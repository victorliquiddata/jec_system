
### Estrutura do Diretório E Código Contextual
```json
  "codebase": {

dir = [
    __pycache__
.pytest_cache
.venv
archive
archive\__pycache__
data
docs
exports
logs
temp
tests
UIs
__init__.py
.coverage
.env
.gitignore
auth.py
config.py
database.py
rich_cli.py
requirements.txt

]

database = [

"""
Database Manager Module

Handles all PostgreSQL database operations with connection pooling and comprehensive logging.
Uses JCELogger for detailed audit trails and operational monitoring.

Features:
- Thread-safe connection pooling
- Automatic reconnection logic
- Query execution tracking
- Detailed error logging
- Performance monitoring
"""

import os
from typing import Optional, List, Dict, Any, Union
from psycopg2 import pool, OperationalError, Error, DatabaseError
from psycopg2.extensions import connection  # Removed unused 'cursor'
from dotenv import load_dotenv
from datetime import datetime
from logger import JCELogger

# Initialize environment variables
load_dotenv()


class DatabaseManager:
    """Gerenciador de conexões PostgreSQL com logging e métricas."""

    def __init__(self):
        self.logger = JCELogger()
        self._connection_pool: Optional[pool.SimpleConnectionPool] = None
        self._reconnect_attempts = 3
        self._setup_metrics()
        self._initialize_pool()

    def _setup_metrics(self) -> None:
        """Inicializa métricas de desempenho."""
        self.metrics = {
            "total_queries": 0,
            "failed_queries": 0,
            "connection_issues": 0,
            "last_success": None,
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas de conexão sem acessar atributos privados."""
        metrics = {**self.metrics}

        if self._connection_pool:
            # Usando try-except para evitar falhas se o pool mudar
            try:
                metrics.update(
                    {
                        "active_connections": self._connection_pool._used
                        and len(self._connection_pool._used)
                        or 0,
                        "available_connections": self._connection_pool.maxconn
                        - (
                            self._connection_pool._used
                            and len(self._connection_pool._used)
                            or 0
                        ),
                    }
                )
            except AttributeError:
                metrics.update({"active_connections": 0, "available_connections": 0})

        return metrics

    def _initialize_pool(self):
        """Create connection pool with logging"""
        if not self._connection_pool:
            try:
                min_connections = int(os.getenv("DB_MIN_CONNECTIONS", "1"))
                max_connections = int(os.getenv("DB_MAX_CONNECTIONS", "5"))

                self._connection_pool = pool.SimpleConnectionPool(
                    minconn=min_connections,
                    maxconn=max_connections,
                    host=os.getenv("DB_HOST"),
                    port=os.getenv("DB_PORT"),
                    user=os.getenv("DB_USUARIO"),
                    password=os.getenv("DB_SENHA"),
                    database=os.getenv("DB_NOME"),
                    options=f"-c search_path={os.getenv('DB_SCHEMA', 'jec')}",
                )

                self.logger.log_conexao(
                    "POOL_INIT",
                    f"Pool created: {min_connections}-{max_connections} connections",
                    metadata={
                        "min": min_connections,
                        "max": max_connections,
                        "host": os.getenv("DB_HOST"),
                        "schema": os.getenv("DB_SCHEMA", "jec"),
                    },
                )

            except Exception as exc:
                self.logger.log_conexao(
                    "POOL_FAIL", f"Failed to initialize pool: {str(exc)}", level="error"
                )
                raise DatabaseError(f"Connection pool initialization failed: {exc}")

    def _get_connection(self) -> connection:
        """Get a connection with retry logic and logging"""
        for attempt in range(self._reconnect_attempts):
            try:
                conn = self._connection_pool.getconn()

                # 🚨 Force schema on each checkout
                schema = os.getenv("DB_SCHEMA", "jec")
                with conn.cursor() as cur:
                    cur.execute(f"SET search_path TO {schema}")
                conn.commit()

                self.logger.log_conexao(
                    "CONN_ACQUIRED",
                    f"Connection acquired and schema set to '{schema}' (attempt {attempt + 1})",
                )
                return conn

            except (OperationalError, pool.PoolError) as e:
                if attempt < self._reconnect_attempts - 1:
                    self.logger.log_conexao(
                        "CONN_RETRY",
                        f"Attempt {attempt + 1} failed: {str(e)}",
                        level="warning",
                    )
                    continue

                self.metrics["connection_issues"] += 1
                self.logger.log_conexao(
                    "CONN_FAILED",
                    f"All connection attempts failed: {str(e)}",
                    level="error",
                )
                raise

    def _log_query_execution(self, query: str, params: tuple, execution_time: float):
        """Log query execution details"""
        self.logger.log_conexao(
            "QUERY_EXECUTED",
            f"Query completed in {execution_time:.2f}s",
            metadata={
                "query": query[:200] + ("..." if len(query) > 200 else ""),
                "params": str(params) if params else None,
                "duration": execution_time,
            },
        )

    def execute_query(
        self, query: str, params: Optional[tuple] = None, return_results: bool = False
    ) -> Optional[Union[List[Dict[str, Any]], int]]:
        """Executa uma query com logging automático."""
        conn = None
        self.metrics["total_queries"] += 1  # At start
        try:
            self.logger.log_conexao("QUERY_START", f"Executando: {query[:50]}...")
            conn = self._get_connection()

            # Use the cursor as a context manager
            with conn.cursor() as cur:
                cur.execute(query, params)

                if return_results:
                    if cur.description:  # Check if there's a result set
                        columns = [desc[0] for desc in cur.description]
                        results = [dict(zip(columns, row)) for row in cur.fetchall()]
                        self.logger.log_conexao("QUERY_SUCCESS", "Consulta concluída")
                        return results
                    else:
                        return []
                else:
                    conn.commit()
                    self.logger.log_conexao(
                        "UPDATE_SUCCESS", f"Linhas afetadas: {cur.rowcount}"
                    )
                    return cur.rowcount
            self.metrics["last_success"] = datetime.now()

        except Error as e:
            self.metrics["failed_queries"] += 1  # Increment failed query count
            self.logger.log_conexao("QUERY_FAILED", str(e), level="error")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                self._connection_pool.putconn(conn)

    def close_all_connections(self):
        """Close all connections with logging"""
        if self._connection_pool:
            try:
                self._connection_pool.closeall()
                self.logger.log_conexao(
                    "POOL_CLOSED",
                    "All database connections closed",
                    metadata={
                        "total_queries": self.metrics["total_queries"],
                        "failed_queries": self.metrics["failed_queries"],
                    },
                )
            except Exception as e:
                self.logger.log_conexao(
                    "POOL_CLOSE_FAILED", f"Error closing pool: {str(e)}", level="error"
                )
                raise


def get_db_instance() -> DatabaseManager:
    """Get the singleton database instance."""
    if not hasattr(DatabaseManager, "_instance"):
        DatabaseManager._instance = DatabaseManager()
    return DatabaseManager._instance


# Then modify any code that was using the direct 'db' instance to use:
db = get_db_instance()


]

test_database_integration = [please insert status aafter reading and print this line at the end]
[
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

    with patch.object(db_manager, "_log_query_execution") as mock_log:
        # Execute with timing
        start_time = datetime.now()
        db_manager.execute_query(test_query, return_results=True)
        forced_duration = (datetime.now() - start_time).total_seconds()

        # Verify logging
        mock_log.assert_called_once_with(
            test_query,
            None,
            pytest.approx(forced_duration, rel=0.1),  # Allow 10% variance
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


]






auth = [
import logging
import re
import secrets
import hashlib
from typing import Optional, Dict
from database import db_manager


class AuthManager:
    """Handles user authentication, password hashing, and session management"""

    def __init__(self):
        self.current_user: Optional[Dict] = None

    def hash_password(self, password: str, salt: Optional[str] = None) -> str:
        """Hash password with PBKDF2-HMAC-SHA256"""
        if salt is None:
            salt = secrets.token_hex(16)
        iterations = 600000
        hashed = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations
        )
        return f"pbkdf2:sha256:{iterations}${salt}${hashed.hex()}"

    def verify_password(self, stored_hash: str, provided_password: str) -> bool:
        """Verify a password against stored hash"""
        if not stored_hash.startswith("pbkdf2:sha256:"):
            # Legacy plaintext password (for migration)
            return stored_hash == provided_password

        try:
            algorithm, hash_params = stored_hash.split("$", 1)
            _, method, iterations = algorithm.split(":")
            salt, stored_key = hash_params.split("$")
            new_hash = hashlib.pbkdf2_hmac(
                method,
                provided_password.encode("utf-8"),
                salt.encode("utf-8"),
                int(iterations),
            )
            return secrets.compare_digest(new_hash.hex(), stored_key)
        except (ValueError, AttributeError):
            return False

    def validate_password_complexity(self, password: str) -> tuple[bool, str]:
        """Enforce password complexity rules"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter"
        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter"
        if not re.search(r"[0-9]", password):
            return False, "Password must contain at least one digit"
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return False, "Password must contain at least one special character"
        return True, ""

    def login(self, email: str, senha: str) -> bool:
        """Authenticate user and establish session"""
        try:
            user = db_manager.execute_query(
                "SELECT * FROM usuarios WHERE email = %s", (email,), return_results=True
            )
            if user and self.verify_password(user[0]["senha"], senha):
                if not user[0]["senha"].startswith("pbkdf2:sha256:"):
                    new_hash = self.hash_password(senha)
                    db_manager.execute_query(
                        "UPDATE usuarios SET senha = %s WHERE id = %s",
                        (new_hash, user[0]["id"]),
                    )

                self.current_user = user[0]
                logging.info("User %s logged in successfully", email)
                return True
            else:
                self.current_user = None  # Ensure session is cleared on failure
                return False
        except Exception as e:
            logging.error("Login failed: %s", str(e))
            self.current_user = None  # Ensure session is cleared on exceptions
            return False

    def logout(self):
        """Terminate current session"""
        if self.current_user:
            logging.info("User %s logged out", self.current_user["email"])
            self.current_user = None

    def get_current_user(self) -> Optional[Dict]:
        """Get currently authenticated user"""
        return self.current_user


# Singleton instance
auth_manager = AuthManager()


]

test_auth - status all passed [

    import pytest
from unittest.mock import patch, MagicMock
from auth import AuthManager, auth_manager
from database import db_manager


@pytest.fixture
def mock_db():
    with patch.object(db_manager, "execute_query") as mock_query:
        yield mock_query


def test_password_hashing():
    auth = AuthManager()
    password = "SecurePass123!"
    hashed = auth.hash_password(password)

    # Verify the hash format
    assert hashed.startswith("pbkdf2:sha256:600000$")
    assert len(hashed.split("$")) == 3

    # Verify password verification
    assert auth.verify_password(hashed, password)
    assert not auth.verify_password(hashed, "wrongpass")


def test_password_complexity():
    auth = AuthManager()

    # Test valid password
    valid, msg = auth.validate_password_complexity("SecurePass123!")
    assert valid
    assert msg == ""

    # Test various invalid cases
    assert not auth.validate_password_complexity("short")[0]
    assert not auth.validate_password_complexity("nouppercase123!")[0]
    assert not auth.validate_password_complexity("NOLOWERCASE123!")[0]
    assert not auth.validate_password_complexity("NoNumbers!")[0]
    assert not auth.validate_password_complexity("MissingSpecial123")[0]


def test_successful_login(mock_db):
    mock_db.return_value = [
        {
            "id": 1,
            "email": "test@example.com",
            "senha": auth_manager.hash_password("correctpass"),
        }
    ]

    assert auth_manager.login("test@example.com", "correctpass")
    assert auth_manager.get_current_user() is not None
    mock_db.assert_called()


def test_failed_login(mock_db):
    auth_manager.logout()  # Ensure no previous session exists
    mock_db.return_value = [
        {
            "id": 1,
            "email": "test@example.com",
            "senha": auth_manager.hash_password("correctpass"),
        }
    ]

    assert not auth_manager.login("test@example.com", "wrongpass")
    assert auth_manager.get_current_user() is None  # This should now pass


def test_logout():
    auth_manager.current_user = {"email": "test@example.com"}
    auth_manager.logout()
    assert auth_manager.get_current_user() is None


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])

],

[

    {
  "python_version": "3.13.2",
  "pytest_version": "8.3.5",
  "platform": "win32",
  "total_test_files": 4,
  "test_results": [
    {
      "file": "test_rich_cli.py",
      "collected": 10,
      "passed": 10,
      "failed": 0,
      "duration_seconds": 0.13
    },
    {
      "file": "test_config_ok.py",
      "collected": 7,
      "passed": 7,
      "failed": 0,
      "duration_seconds": 0.04
    },
    {
      "file": "test_auth_ok.py",
      "collected": 5,
      "passed": 5,
      "failed": 0,
      "duration_seconds": 1.85
    },
    {
      "file": "test_database_ok.py",
      "collected": 5,
      "passed": 5,
      "failed": 0,
      "warnings": [
        "Connection attempt 1 failed. Retrying...",
        "Connection attempt 2 failed. Retrying..."
      ],
      "errors": [
        "Database error: Connection failed"
      ],
      "duration_seconds": 0.04
    }
  ],
  "summary": {
    "total_tests": 27,
    "passed": 27,
    "failed": 0,
    "warnings": 2,
    "errors": 1,
    "overall_status": "success"
  }
}

],

config [
    # config.py
import os
from typing import Dict, Any
from dotenv import load_dotenv
from enum import Enum

# Carrega variáveis de ambiente
load_dotenv()


class Theme(str, Enum):
    """Esquemas de cores disponíveis"""

    PADRAO = "padrao"
    ESCURO = "escuro"


class AppConfig:
    """Configurações centrais da aplicação"""

    # Versão do sistema
    VERSION = "1.1"

    # Configurações de banco de dados
    DB_CONFIG = {
        "host": os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT"),
        "user": os.getenv("DB_USUARIO"),
        "password": os.getenv("DB_SENHA"),
        "database": os.getenv("DB_NOME"),
        "schema": os.getenv("DB_SCHEMA", "jec"),
        "min_connections": int(os.getenv("DB_MIN_CONNECTIONS", "1")),
        "max_connections": int(os.getenv("DB_MAX_CONNECTIONS", "5")),
    }

    # Configurações de autenticação
    AUTH = {
        "hashing_algorithm": "pbkdf2:sha256",
        "iterations": 600000,
        "session_timeout": 1800,  # 30 minutos em segundos
        "password_rules": {
            "min_length": 8,
            "require_upper": True,
            "require_lower": True,
            "require_digit": True,
            "require_special": True,
        },
    }

    # Esquemas de cores (para rich_cli.py)
    THEMES = {
        Theme.PADRAO: {
            "header": {"color": "#005F87", "border": "#003D5C"},
            "body": {"primary": "#333333", "secondary": "#666666"},
            "status": {
                "success": "#4CAF50",
                "warning": "#FFC107",
                "error": "#F44336",
                "info": "#2196F3",
            },
        },
        Theme.ESCURO: {
            "header": {"color": "#E0E0E0", "border": "#7A7A7A"},
            "body": {"primary": "#BDBDBD", "secondary": "#7A7A7A"},
            "status": {
                "success": "#66BB6A",
                "warning": "#E6A23C",
                "error": "#D32F2F",
                "info": "#2196F3",
            },
        },
    }

    @classmethod
    def load_theme(cls, theme_name: str = Theme.ESCURO) -> Dict[str, Any]:
        """Carrega configurações de tema"""
        try:
            return cls.THEMES[Theme(theme_name)]
        except ValueError:
            return cls.THEMES[Theme.ESCURO]

    @classmethod
    def get_db_dsn(cls) -> str:
        """Retorna DSN para conexão com banco"""
        return (
            f"host={cls.DB_CONFIG['host']} "
            f"port={cls.DB_CONFIG['port']} "
            f"user={cls.DB_CONFIG['user']} "
            f"password={cls.DB_CONFIG['password']} "
            f"dbname={cls.DB_CONFIG['database']} "
            f"options='-c search_path={cls.DB_CONFIG['schema']}'"
        )


# Teste de configuração (executa apenas quando rodado diretamente)
if __name__ == "__main__":
    print(f"Configuração do tema escuro: {AppConfig.load_theme()}")
    print(f"DSN do banco de dados: {AppConfig.get_db_dsn()}")

]
,
[
    # test_config.py
import pytest
from config import AppConfig, Theme
from unittest.mock import patch
import os


class TestAppConfig:
    """Testes unitários para a classe AppConfig"""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Fixture para salvar e restaurar configurações originais"""
        original_db_config = AppConfig.DB_CONFIG.copy()
        yield
        # Restaura configurações após cada teste
        AppConfig.DB_CONFIG = original_db_config

    def test_version_constant(self):
        """Verifica se a versão está definida corretamente"""
        assert hasattr(AppConfig, "VERSION")
        assert isinstance(AppConfig.VERSION, str)
        assert len(AppConfig.VERSION.split(".")) >= 2

    def test_db_config_structure(self):
        """Verifica a estrutura da configuração de banco de dados"""
        db_config = AppConfig.DB_CONFIG
        assert isinstance(db_config, dict)
        required_keys = ["host", "port", "user", "password", "database", "schema"]
        assert all(key in db_config for key in required_keys)

    def test_auth_config(self):
        """Verifica parâmetros de autenticação"""
        auth = AppConfig.AUTH
        assert auth["hashing_algorithm"] == "pbkdf2:sha256"
        assert auth["iterations"] == 600000
        assert isinstance(auth["password_rules"], dict)

    def test_theme_loading(self):
        """Testa carregamento de temas"""
        for theme in Theme:
            theme_config = AppConfig.load_theme(theme)
            assert isinstance(theme_config, dict)
            assert "header" in theme_config
            assert "body" in theme_config
            assert "status" in theme_config

    def test_default_theme_fallback(self):
        """Verifica fallback para tema padrão"""
        invalid_theme = "inexistente"
        theme_config = AppConfig.load_theme(invalid_theme)
        assert theme_config == AppConfig.THEMES[Theme.ESCURO]

    def test_get_db_dsn(self):
        """Verifica geração correta do DSN"""
        # Configuração de teste isolada
        test_config = {
            "host": "testhost",
            "port": "9999",
            "user": "testuser",
            "password": "testpass",
            "database": "testdb",
            "schema": "testschema",
        }

        # Substitui temporariamente a configuração
        original_config = AppConfig.DB_CONFIG
        AppConfig.DB_CONFIG = test_config

        try:
            dsn = AppConfig.get_db_dsn()
            assert "host=testhost" in dsn
            assert "port=9999" in dsn
            assert "user=testuser" in dsn
            assert "password=testpass" in dsn
            assert "dbname=testdb" in dsn
            assert "options='-c search_path=testschema'" in dsn
        finally:
            # Restaura configuração original
            AppConfig.DB_CONFIG = original_config

    def test_theme_enum_values(self):
        """Verifica valores do enum Theme"""
        assert Theme.PADRAO.value == "padrao"
        assert Theme.ESCURO.value == "escuro"
        assert len(Theme) == 2


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])

]
,

rich_cli [
# rich_cli.py (versão corrigida)
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.align import Align
from rich.prompt import Prompt
from datetime import datetime
from typing import Dict, List, Optional, Union
from config import AppConfig


class JECCLI:
    """Interface de usuário unificada para o Sistema JEC usando Rich"""

    def __init__(self):
        self.console = Console(width=80, highlight=False)
        self.theme = AppConfig.load_theme()

        # Garante que o tema carregado seja válido
        if self.theme not in ["dark", "light"]:
            self.theme = "dark"  # Tema padrão

        self.user_context: Optional[Dict[str, Union[str, Dict]]] = None

        self.system_status: Dict[str, str] = {
            "database": "offline",
            "auth": "inactive",
            "last_update": datetime.now().isoformat(),
        }

    def _apply_theme(self, element_type: str) -> Dict[str, str]:
        """Aplica esquema de cores baseado no tema atual"""
        themes = {
            "dark": {
                "header": {"color": "#E0E0E0", "border": "#7A7A7A"},
                "body": {"primary": "#BDBDBD", "secondary": "#7A7A7A"},
                "status": {
                    "success": "#66BB6A",
                    "warning": "#E6A23C",
                    "error": "#D32F2F",
                    "info": "#2196F3",
                },
            },
            "light": {
                "header": {"color": "#333333", "border": "#AAAAAA"},
                "body": {"primary": "#000000", "secondary": "#666666"},
                "status": {
                    "success": "#4CAF50",
                    "warning": "#FFC107",
                    "error": "#F44336",
                    "info": "#2196F3",
                },
            },
        }
        return themes.get(self.theme, themes["dark"])[element_type]

    def display_header(self, title: str = "Sistema JEC"):
        """Renderiza o cabeçalho da aplicação"""
        header_text = Text(
            f"⚖️  {title}", style=f"bold {self._apply_theme('header')['color']}"
        )
        self.console.print(
            Panel(
                Align.center(header_text),
                border_style=self._apply_theme("header")["border"],
                padding=(1, 2),
                title=f"v{AppConfig.VERSION}",
                title_align="right",
            )
        )

    def display_main_menu(self, options: List[Dict[str, str]]):
        """Exibe menu principal numerado"""
        menu_table = Table(show_header=False, box=None, expand=True)
        menu_table.add_column(
            "Opção", style=self._apply_theme("body")["primary"], width=6
        )
        menu_table.add_column("Descrição", style=self._apply_theme("body")["secondary"])

        for idx, option in enumerate(options, 1):
            menu_table.add_row(
                Text(f"{idx}", style="bold"), Text(option["description"])
            )

        self.console.print("\n")
        self.console.print(
            Panel(
                menu_table,
                title="[bold]Menu Principal[/]",
                border_style=self._apply_theme("header")["border"],
            )
        )

    def display_status(self, message: str, level: str = "info"):
        """Exibe mensagens de status formatadas"""
        icons = {"success": "✔", "warning": "⚠", "error": "❌", "info": "ℹ️"}
        self.console.print(
            f"{icons[level]} [{self._apply_theme('status')[level]}]{message}[/]",
            style=self._apply_theme("body")["primary"],
        )

    def prompt_input(self, label: str, input_type: type = str) -> str:
        """Solicita entrada do usuário com validação de tipo"""
        while True:
            try:
                value = Prompt.ask(f"[bold]{label}[/]", console=self.console)
                return input_type(value)
            except ValueError:
                self.display_status(
                    f"Entrada inválida. Esperado tipo {input_type.__name__}.", "warning"
                )

    def display_data_table(self, data: List[Dict], title: str = "Resultados"):
        """Exibe dados em formato tabular"""
        table = Table(
            title=f"[bold]{title}[/]",
            box=None,
            show_header=True,
            header_style=f"bold {self._apply_theme('body')['primary']}",
        )

        if data:
            for key in data[0].keys():
                table.add_column(key.capitalize())

            for item in data:
                table.add_row(*[str(v) for v in item.values()])

            self.console.print(table)
        else:
            self.display_status("Nenhum dado encontrado.", "warning")

    def update_footer(self):
        """Atualiza e exibe o rodapé dinâmico"""
        user_email = (
            self.user_context.get("email", "N/A")
            if self.user_context and isinstance(self.user_context, dict)
            else "Não autenticado"
        )

        footer_elements = [
            f"Usuário: {user_email}",
            f"Status DB: {self.system_status.get('database', 'unknown')}",
            f"Atualizado: {datetime.now().strftime('%H:%M:%S')}",
        ]

        footer_text = Text("   |   ".join(footer_elements), style="italic #7A7A7A")
        self.console.print(
            Panel(
                Align.center(footer_text),
                border_style=self._apply_theme("header")["border"],
                padding=(0, 2),
                expand=False,
            )
        )

    def clear_screen(self):
        """Limpa a tela do console"""
        self.console.clear()


# Singleton para uso global
cli = JECCLI()

],

test_rich_cli [
# test_rich_cli.py

import pytest
from unittest.mock import patch


import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rich_cli import JECCLI


@pytest.fixture
def cli():
    return JECCLI()


def test_display_header(cli, capsys):
    cli.display_header("Teste Header")
    captured = capsys.readouterr()
    assert "Teste Header" in captured.out


def test_display_main_menu(cli, capsys):
    options = [{"description": "Opção 1"}, {"description": "Opção 2"}]
    cli.display_main_menu(options)
    captured = capsys.readouterr()
    assert "Opção 1" in captured.out
    assert "Opção 2" in captured.out


def test_display_status_success(cli, capsys):
    cli.display_status("Tudo certo!", level="success")
    captured = capsys.readouterr()
    assert "Tudo certo!" in captured.out
    assert "✔" in captured.out


def test_prompt_input_valid(monkeypatch, cli):
    monkeypatch.setattr("builtins.input", lambda _: "123")
    with patch("rich.prompt.Prompt.ask", return_value="123"):
        result = cli.prompt_input("Digite um número", int)
    assert result == 123


def test_prompt_input_invalid_then_valid(monkeypatch, cli):
    inputs = iter(["abc", "456"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    with patch("rich.prompt.Prompt.ask", side_effect=["abc", "456"]):
        result = cli.prompt_input("Digite número", int)
    assert result == 456


def test_display_data_table_with_data(cli, capsys):
    data = [{"nome": "João", "idade": 30}, {"nome": "Ana", "idade": 25}]
    cli.display_data_table(data, "Pessoas")
    captured = capsys.readouterr()
    assert "João" in captured.out
    assert "Ana" in captured.out
    assert "Pessoas" in captured.out


def test_display_data_table_empty(cli, capsys):
    cli.display_data_table([], "Vazio")
    captured = capsys.readouterr()
    assert "Nenhum dado encontrado." in captured.out


def test_update_footer_authenticated(cli, capsys):
    cli.user_context = {"email": "teste@exemplo.com"}
    cli.update_footer()
    captured = capsys.readouterr()
    assert "teste@exemplo.com" in captured.out


def test_update_footer_unauthenticated(cli, capsys):
    cli.user_context = None
    cli.update_footer()
    captured = capsys.readouterr()
    assert "Não autenticado" in captured.out


def test_clear_screen(cli):
    # Não há saída capturável com capsys, apenas garantir que não dá erro
    cli.clear_screen()

],

[RESULTS: ALL 4 FILES TESTED AND FULLY PASSED  ]
  
  }