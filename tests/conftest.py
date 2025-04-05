# tests/conftest.py

import pytest
import itertools
from unittest.mock import patch, MagicMock
from database import DatabaseManager


@pytest.fixture(autouse=True)
def reset_singleton():
    """Ensure DatabaseManager singleton is reset before each test."""
    if hasattr(DatabaseManager, "_instance"):
        del DatabaseManager._instance


@pytest.fixture
def mock_db_env(monkeypatch):
    """Mock environment variables for database connection."""
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_USUARIO", "test")
    monkeypatch.setenv("DB_SENHA", "test")
    monkeypatch.setenv("DB_NOME", "testdb")
    monkeypatch.setenv("DB_SCHEMA", "jec")
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "true")  # Prevent singleton


@pytest.fixture
def mock_time():
    """Mock time.time() to return incrementing integers."""
    with patch("time.time", side_effect=itertools.count(start=1000, step=1)):
        yield


@pytest.fixture
def db_manager(mock_db_env):
    """Provide a DatabaseManager instance with a mocked connection pool."""
    with patch("database.pool.SimpleConnectionPool") as mock_pool_class:
        mock_pool_instance = MagicMock()
        mock_pool_class.return_value = mock_pool_instance

        mock_conn = MagicMock()
        mock_pool_instance.getconn.return_value = mock_conn

        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        manager = DatabaseManager()
        manager._mock_pool_class = mock_pool_class

        yield manager
