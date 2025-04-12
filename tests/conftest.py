import pytest
import sqlite3
from unittest.mock import patch
from database import DatabaseManager


@pytest.fixture
def sqlite_db():
    """In-memory SQLite database with PostgreSQL compatibility"""
    conn = sqlite3.connect(":memory:")

    # PostgreSQL compatibility layer
    conn.execute("PRAGMA foreign_keys = ON")

    # Create tables matching your PostgreSQL schema
    conn.executescript(
        """
    CREATE TABLE usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        senha TEXT,
        tipo TEXT
    );
    
    CREATE TABLE audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT,
        FOREIGN KEY(user_id) REFERENCES usuarios(id)
    );
    """
    )

    yield conn
    conn.close()


@pytest.fixture
def test_db(sqlite_db):
    """Patch the production database to use SQLite"""

    def mock_execute(query, params=None, **kwargs):
        # Convert PostgreSQL syntax to SQLite
        query = query.replace("::uuid", "")
        query = query.replace("%s", "?")
        cursor = sqlite_db.cursor()
        try:
            cursor.execute(query, params or ())
            if "return_results" in kwargs:
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
            return cursor.rowcount
        finally:
            sqlite_db.commit()
            cursor.close()

    with patch.object(DatabaseManager, "execute_query", mock_execute):
        yield sqlite_db
