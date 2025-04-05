# test_database_integration.py
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from database import DatabaseManager
from psycopg2 import OperationalError

# Add these imports at the top of tests/test_database_integration_ok.py
import itertools  # For mock_time fixture
from concurrent.futures import ThreadPoolExecutor  # For concurrent access test
from psycopg2 import pool


@pytest.fixture
def mock_db_env(monkeypatch):
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_USUARIO", "test")
    monkeypatch.setenv("DB_SENHA", "test")
    monkeypatch.setenv("DB_NOME", "testdb")
    monkeypatch.setenv("DB_SCHEMA", "jec")
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "true")  # Evita singleton


# Add to fixtures if needed
@pytest.fixture
def mock_time():
    with patch("time.time", side_effect=itertools.count(start=1000, step=1)):
        yield


# In test_database_integration.py
@pytest.fixture
def db_manager(mock_db_env):
    with patch("database.pool.SimpleConnectionPool") as mock_pool_class:
        # Create the mock pool instance
        mock_pool_instance = MagicMock()
        mock_pool_class.return_value = mock_pool_instance

        # Setup mock connection chain
        mock_conn = MagicMock()
        mock_pool_instance.getconn.return_value = mock_conn

        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Create the manager instance
        manager = DatabaseManager()

        # Store the mock pool class for assertions
        manager._mock_pool_class = mock_pool_class

        yield manager


def test_connection_pool_initialization(db_manager):
    """Test if pool is initialized with correct params"""
    # Verify the mock pool class was called with correct parameters
    db_manager._mock_pool_class.assert_called_once_with(
        minconn=1,
        maxconn=5,
        host="localhost",
        port="5432",
        user="test",
        password="test",
        database="testdb",
        options="-c search_path=jec",
    )


def test_schema_enforcement(db_manager):
    """Test if schema is enforced on connection checkout"""
    # Create fresh mocks for this test
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    db_manager._connection_pool.getconn.return_value = mock_conn

    # Call the method
    db_manager._get_connection()

    # Verify schema was set
    mock_cursor.execute.assert_called_with("SET search_path TO jec")
    mock_conn.commit.assert_called_once()


def test_execute_query_success(db_manager):
    # Setup mock data
    mock_cursor = (
        db_manager._connection_pool.getconn.return_value.cursor.return_value.__enter__.return_value
    )
    mock_cursor.description = [("id",), ("name",)]
    mock_cursor.fetchall.return_value = [(1, "Test")]

    results = db_manager.execute_query("SELECT...", return_results=True)
    assert results == [{"id": 1, "name": "Test"}]


# In test_database_integration.py
def test_execute_query_error(db_manager):
    """Test error handling and logging"""
    # Setup mock to fail on execute
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = OperationalError("Query failed")

    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    with patch.object(db_manager, "_get_connection", return_value=mock_conn):
        with pytest.raises(OperationalError):
            db_manager.execute_query("INVALID QUERY")


def test_logger_integration(db_manager):
    """Verify all logger methods are properly called"""
    with patch.object(db_manager.logger, "log_conexao") as mock_log:
        try:
            db_manager.execute_query("SELECT id FROM jec.audit_log LIMIT 1")
        except:
            pass

        assert mock_log.called
        assert any("QUERY_" in args[0] for args, _ in mock_log.call_args_list)


def test_metrics_tracking(db_manager):
    """Test if metrics are properly updated"""
    initial_metrics = db_manager.get_metrics()

    # Mock a successful query
    with patch.object(db_manager, "_get_connection"):
        db_manager.execute_query("SELECT id FROM jec.categorias_causas LIMIT 1")

    updated_metrics = db_manager.get_metrics()
    assert updated_metrics["total_queries"] == initial_metrics["total_queries"] + 1
    assert updated_metrics["failed_queries"] == initial_metrics["failed_queries"]


def test_connection_retry(db_manager):
    """Test connection retry logic"""
    db_manager._connection_pool.getconn.side_effect = [
        OperationalError("First fail"),
        MagicMock(),  # Second attempt succeeds
    ]

    with patch.object(db_manager.logger, "log_conexao") as mock_log:
        db_manager._get_connection()

        # Verify retry was logged
        assert any("CONN_RETRY" in args[0] for args, _ in mock_log.call_args_list)
        assert any("CONN_ACQUIRED" in args[0] for args, _ in mock_log.call_args_list)


def test_pool_closure(db_manager):
    """Test connection pool closing with logging"""
    with patch.object(db_manager.logger, "log_conexao") as mock_log:
        db_manager.close_all_connections()
        db_manager._connection_pool.closeall.assert_called_once()
        mock_log.assert_called_with(
            "POOL_CLOSED",
            "All database connections closed",
            metadata={"total_queries": 0, "failed_queries": 0},
        )


# 1. Connection Pool Exhaustion Test
# python
# Copy
def test_connection_pool_exhaustion(db_manager):
    """Test behavior when connection pool is exhausted"""
    # Setup mock to simulate pool exhaustion
    db_manager._connection_pool.getconn.side_effect = pool.PoolError(
        "Connection pool exhausted"
    )

    with patch.object(db_manager.logger, "log_conexao") as mock_log:
        with pytest.raises(pool.PoolError):
            db_manager._get_connection()

        # Verify proper logging occurred
        mock_log.assert_any_call(
            "CONN_FAILED",
            "All connection attempts failed: Connection pool exhausted",
            level="error",
        )
        assert db_manager.metrics["connection_issues"] > 0


# 2. Query Execution Time Logging Test
# python
def test_query_execution_time_logging(db_manager):
    """Test that query execution times are properly logged"""
    test_query = "SELECT * FROM jec.processos"

    # Setup mock chain
    mock_cursor = MagicMock()
    mock_cursor.description = [("id",), ("title",)]
    mock_cursor.fetchall.return_value = [(1, "Test Case")]

    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    db_manager._connection_pool.getconn.return_value = mock_conn

    with patch.object(db_manager, "_log_query_execution") as mock_log, patch(
        "database.perf_counter"  # Changed from "time.perf_counter"
    ) as mock_time:
        # Control time precisely
        mock_time.side_effect = [1000.0, 1000.357]  # Fixed start/end times

        db_manager.execute_query(test_query, return_results=True)

        # Verify logging with exact expected duration
        expected_duration = 0.357  # 357ms exactly
        mock_log.assert_called_once_with(
            test_query,
            None,
            pytest.approx(expected_duration, abs=0.001),  # Absolute tolerance
        )


# 3. Connection Recycling Test
# python
# Copy
def test_connection_recycling(db_manager):
    """Test connections are properly returned to pool"""
    mock_conn = MagicMock()
    db_manager._connection_pool.getconn.return_value = mock_conn

    # Simulate query execution
    db_manager.execute_query("SELECT 1")

    # Verify connection was returned to pool
    db_manager._connection_pool.putconn.assert_called_once_with(mock_conn)


# 4. Concurrent Access Test
# python
# Copy
def test_concurrent_access(db_manager):
    """Test basic thread safety"""
    mock_conn = MagicMock()
    db_manager._connection_pool.getconn.return_value = mock_conn

    def worker(query):
        return db_manager.execute_query(query)

    # Simulate concurrent access
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(worker, f"SELECT {i}") for i in range(3)]
        results = [f.result() for f in futures]

    # Verify proper connection handling
    assert db_manager._connection_pool.getconn.call_count == 3
    assert db_manager._connection_pool.putconn.call_count == 3


# 5. Transaction Rollback Test
def test_transaction_rollback(db_manager):
    """Test failed transactions are properly rolled back"""
    # Setup mock connection chain
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    db_manager._connection_pool.getconn.return_value = mock_conn

    # Make execute fail after first call (for schema setup)
    def execute_side_effect(query, params=None):
        if "SET search_path" not in query:
            raise OperationalError("Failed query")

    mock_cursor.execute.side_effect = execute_side_effect

    with pytest.raises(OperationalError):
        db_manager.execute_query("INSERT INTO invalid_table VALUES (1)")

    mock_conn.rollback.assert_called_once()


@pytest.fixture(autouse=True)
def reset_singleton():
    if hasattr(DatabaseManager, "_instance"):
        del DatabaseManager._instance
