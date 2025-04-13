# database.py

import os
import secrets
import hashlib
from typing import Optional, List, Dict, Any, Union
from psycopg2 import pool, OperationalError, Error, DatabaseError
from psycopg2.extensions import connection  # Removed unused 'cursor'
from dotenv import load_dotenv
from time import perf_counter  # Add this import
from datetime import datetime
from logger import JCELogger
from config import AppConfig

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
                        "log_config": AppConfig.get_log_config(),  # Add config snapshot
                    },
                )

            except Exception as exc:
                self.logger.log_conexao(
                    "POOL_FAIL", f"Failed to initialize pool: {str(exc)}", level="error"
                )
                raise DatabaseError(
                    f"Connection pool initialization failed: {exc}"
                ) from exc

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
        self,
        query: str,
        params: Optional[tuple] = None,
        return_results: bool = False,
        correlation_id: Optional[str] = None,
        query_name: Optional[str] = None,
    ) -> Union[List[Dict[str, Any]], int]:
        """
        Executes a database query with full observability integration.

        Args:
            query: SQL query string
            params: Query parameters
            return_results: Whether to return results
            correlation_id: Request tracing ID
            query_name: Optional descriptive name for metrics

        Returns:
            Query results or affected row count

        Raises:
            DatabaseError: On query execution failure
        """
        conn = None
        start_time = perf_counter()
        query_id = f"qry-{secrets.token_hex(4)}"  # Unique query identifier
        self.metrics["total_queries"] += 1

        # Build metadata payload
        log_metadata = {
            "query_id": query_id,
            "query_name": query_name or "adhoc",
            "correlation_id": correlation_id,
            "params_hash": (
                hashlib.md5(str(params).encode()).hexdigest()[:8] if params else None
            ),
        }

        try:
            self.logger.log_conexao(
                "QUERY_START",
                f"Executing: {query[:100]}...",
                metadata=log_metadata,
                correlation_id=correlation_id,
            )

            conn = self._get_connection()
            with conn.cursor() as cur:
                # Execute with timing
                cur.execute(query, params)
                execution_time = perf_counter() - start_time

                # Log the query execution time (added for robustness)
                self._log_query_execution(query, params, execution_time)

                # Update metrics
                self._update_query_metrics(
                    query=query,
                    params=params,
                    execution_time=execution_time,
                    metadata=log_metadata,
                )

                # Handle results
                if return_results:
                    results = self._process_query_results(cur)
                    self.logger.log_conexao(
                        "QUERY_SUCCESS",
                        f"Returned {len(results)} rows",
                        metadata={
                            **log_metadata,
                            "row_count": len(results),
                            "execution_time": execution_time,
                        },
                        correlation_id=correlation_id,
                    )
                    return results

                # Handle updates
                conn.commit()
                self.logger.log_conexao(
                    "UPDATE_SUCCESS",
                    f"Rows affected: {cur.rowcount}",
                    metadata={
                        **log_metadata,
                        "row_count": cur.rowcount,
                        "execution_time": execution_time,
                    },
                    correlation_id=correlation_id,
                )
                return cur.rowcount

        except OperationalError as e:
            # Handle OperationalError specifically and re-raise it
            self.metrics["failed_queries"] += 1
            self.logger.log_conexao(
                "QUERY_FAILED",
                str(e),
                level="error",
                metadata={
                    **log_metadata,
                    "error_type": type(e).__name__,
                    "execution_time": perf_counter() - start_time,
                },
                correlation_id=correlation_id,
            )
            if conn:
                conn.rollback()
            raise e  # Re-raise the OperationalError so it can be properly handled in the tests

        except Error as e:
            # Catch all other database errors and log them
            self.metrics["failed_queries"] += 1
            self.logger.log_conexao(
                "QUERY_FAILED",
                str(e),
                level="error",
                metadata={
                    **log_metadata,
                    "error_type": type(e).__name__,
                    "execution_time": perf_counter() - start_time,
                },
                correlation_id=correlation_id,
            )
            if conn:
                conn.rollback()
            raise DatabaseError(f"Query failed [ID:{query_id}] - {str(e)}") from e

        finally:
            if conn:
                try:
                    self._connection_pool.putconn(conn)
                    self.logger.log_conexao(
                        "CONN_RELEASED",
                        f"Connection returned to pool (Query ID: {query_id})",
                        metadata=log_metadata,
                        correlation_id=correlation_id,
                        level="debug",
                    )
                except Exception as pool_error:
                    self.logger.log_conexao(
                        "POOL_ERROR",
                        f"Failed returning connection: {str(pool_error)}",
                        level="critical",
                        metadata=log_metadata,
                        correlation_id=correlation_id,
                    )

    # Helper Methods
    def _update_query_metrics(
        self, query: str, params: tuple, execution_time: float, metadata: dict
    ):
        """Updates metrics and logs query execution"""
        self.metrics.setdefault("query_times", []).append(execution_time)
        self.metrics["last_success"] = datetime.now()

        # Slow query logging
        if execution_time > 1.0:  # 1 second threshold
            self.logger.log_conexao(
                "SLOW_QUERY",
                f"Query took {execution_time:.2f}s",
                level="warning",
                metadata={
                    **metadata,
                    "execution_time": execution_time,
                    "query_sample": query[:200],
                },
            )

    def _process_query_results(self, cursor) -> List[Dict[str, Any]]:
        """Transforms cursor results into dictionaries"""
        if not cursor.description:
            return []

        try:
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.log_conexao(
                "RESULT_PROCESSING_ERROR",
                f"Failed to process results: {str(e)}",
                level="error",
            )
            return []

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
