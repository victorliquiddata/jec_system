import os
import logging
from dotenv import load_dotenv
import psycopg2
from psycopg2 import pool
from psycopg2 import OperationalError, Error  # Correct import location
from typing import Optional, List, Dict, Any

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
                self._connection_pool = pool.SimpleConnectionPool(
                    minconn=int(os.getenv("DB_MIN_CONNECTIONS", 1)),
                    maxconn=int(os.getenv("DB_MAX_CONNECTIONS", 5)),
                    host=os.getenv("DB_HOST"),
                    port=os.getenv("DB_PORT"),
                    user=os.getenv("DB_USUARIO"),
                    password=os.getenv("DB_SENHA"),
                    database=os.getenv("DB_NOME"),
                    options=f"-c search_path={os.getenv('DB_SCHEMA', 'jec')}",
                )
                logging.info("Database connection pool initialized successfully")
            except Exception as e:
                logging.critical(f"Database connection failed: {str(e)}")
                raise

    def _get_connection(self):
        """Get a connection from the pool with retry logic"""
        for attempt in range(self._reconnect_attempts):
            try:
                return self._connection_pool.getconn()
            except (OperationalError, pool.PoolError) as e:  # Now correctly referenced
                if attempt < self._reconnect_attempts - 1:
                    logging.warning(
                        f"Connection attempt {attempt + 1} failed. Retrying..."
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

        except Error as e:  # Now correctly referenced
            logging.error(f"Database error: {str(e)}")
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
