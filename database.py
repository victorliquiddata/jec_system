"mod docstring to be impl"

import os
import logging
from typing import Optional, List, Dict, Any
from psycopg2 import pool
from psycopg2 import OperationalError, Error
from dotenv import load_dotenv


# Initialize environment variables
load_dotenv()


class DatabaseManager:
    """Manage PostgreSQL database connections and operations with connection pooling"""

    _connection_pool: pool.SimpleConnectionPool = None
    _reconnect_attempts = 3

    def __init__(self):
        self._initialize_pool()

    def _initialize_pool(self):
        """Create connection pool using environment variables"""
        if not self._connection_pool:
            try:
                # Convert string env vars to int for connection settings
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
                logging.info("Database connection pool initialized successfully")
            except Exception as exc:
                logging.critical("Database connection failed: %s", str(exc))
                raise

    def _get_connection(self):
        """Get a connection from the pool with retry logic"""
        for attempt in range(self._reconnect_attempts):
            try:
                return self._connection_pool.getconn()
            except (OperationalError, pool.PoolError):  # Removed unused exc variable
                if attempt < self._reconnect_attempts - 1:
                    logging.warning(
                        "Connection attempt %d failed. Retrying...", attempt + 1
                    )
                    continue
                logging.error("Maximum connection attempts reached")
                raise

    def execute_query(
        self, query: str, params: Optional[tuple] = None, return_results: bool = False
    ) -> Optional[List[Dict[str, Any]]]:
        """Execute SQL query with parameters and optional result return"""
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute(query, params)

                if return_results:
                    columns = [desc[0] for desc in cur.description]
                    return [dict(zip(columns, row)) for row in cur.fetchall()]

                conn.commit()
                return None

        except Error as exc:
            logging.error("Database error: %s", str(exc))
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                self._connection_pool.putconn(conn)

    def close_all_connections(self):
        """Close all connections in the pool"""
        if self._connection_pool:
            self._connection_pool.closeall()
            logging.info("All database connections closed")


# Singleton instance for easy access
db_manager = DatabaseManager()
