##version


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
from time import time  # Adicionar import
from time import perf_counter  # Add this import
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
        self.metrics.setdefault("query_times", []).append(
            execution_time
        )  # Histórico de tempos
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
        start_time = perf_counter()  # More precise timing
        self.metrics["total_queries"] += 1

        try:
            self.logger.log_conexao("QUERY_START", f"Executando: {query[:50]}...")
            conn = self._get_connection()

            with conn.cursor() as cur:
                cur.execute(query, params)
                execution_time = perf_counter() - start_time  # Precise measurement

                self._log_query_execution(query, params, execution_time)

                if return_results:
                    if cur.description:
                        columns = [desc[0] for desc in cur.description]
                        results = [dict(zip(columns, row)) for row in cur.fetchall()]
                        self.logger.log_conexao("QUERY_SUCCESS", "Consulta concluída")
                        return results
                    return []
                else:
                    conn.commit()
                    self.logger.log_conexao(
                        "UPDATE_SUCCESS", f"Linhas afetadas: {cur.rowcount}"
                    )
                    return cur.rowcount

            self.metrics["last_success"] = datetime.now()

        except Error as e:
            self.metrics["failed_queries"] += 1
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
