import pytest
from unittest.mock import patch, MagicMock
import psycopg2
from psycopg2 import OperationalError
from database import DatabaseManager


@pytest.fixture(autouse=True)
def mock_environment(monkeypatch):
    """Mock environment variables for database connection"""
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_USUARIO", "test_user")
    monkeypatch.setenv("DB_SENHA", "test_pass")
    monkeypatch.setenv("DB_NOME", "test_db")
    monkeypatch.setenv("DB_SCHEMA", "test_schema")


@pytest.fixture
def mock_connection_pool():
    """Mock PostgreSQL connection pool"""
    with patch("psycopg2.pool.SimpleConnectionPool") as mock_pool:
        mock_pool.return_value = MagicMock()
        yield mock_pool


def test_connection_pool_initialization(mock_connection_pool):
    """Test database connection pool initialization"""
    db = DatabaseManager()
    mock_connection_pool.assert_called_once_with(
        minconn=1,
        maxconn=5,
        host="localhost",
        port="5432",
        user="test_user",
        password="test_pass",
        database="test_db",
        options="-c search_path=test_schema",
    )
    assert db._connection_pool is not None


def test_execute_query_success(mock_connection_pool):
    """Test successful query execution with mocked results"""
    # Setup mocks
    mock_conn = MagicMock()
    mock_cursor = MagicMock(__enter__=MagicMock(), __exit__=MagicMock())
    mock_connection_pool.return_value.getconn.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    # Configure cursor mock to properly simulate the context manager
    cursor_context = mock_cursor.__enter__.return_value
    cursor_context.description = [("id",), ("name",)]
    cursor_context.fetchall.return_value = [(1, "Test"), (2, "Data")]

    # Initialize DB and run test
    db = DatabaseManager()
    result = db.execute_query("SELECT * FROM test_table", return_results=True)

    # Verify results
    assert result == [{"id": 1, "name": "Test"}, {"id": 2, "name": "Data"}]
    cursor_context.execute.assert_called_once_with("SELECT * FROM test_table", None)


def test_execute_query_error_handling(mock_connection_pool):
    """Test proper error handling during query execution"""
    mock_conn = MagicMock()
    mock_connection_pool.return_value.getconn.return_value = mock_conn
    mock_conn.cursor.side_effect = OperationalError("Connection failed")

    db = DatabaseManager()

    with pytest.raises(OperationalError):
        db.execute_query("INVALID SQL")

    mock_conn.rollback.assert_called_once()


def test_connection_retry_logic(mock_connection_pool):
    """Test connection retry mechanism"""
    mock_connection_pool.return_value.getconn.side_effect = [
        OperationalError("First attempt failed"),
        OperationalError("Second attempt failed"),
        MagicMock(),  # Third attempt succeeds
    ]

    db = DatabaseManager()
    # Should succeed after 3 attempts
    conn = db._get_connection()
    assert conn is not None
    assert mock_connection_pool.return_value.getconn.call_count == 3


def test_close_all_connections(mock_connection_pool):
    """Test closing all database connections"""
    db = DatabaseManager()
    db.close_all_connections()
    mock_connection_pool.return_value.closeall.assert_called_once()


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
