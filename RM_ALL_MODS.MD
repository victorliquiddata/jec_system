
### Estrutura do Diretório E Código Contextual
```json
  "codebase": {

dir = [

__pycache__
.pytest_cache
.venv
archive
data
docs
exports
logs
logs\conexoes.log
logs\interface.log
logs\logica.log
temp
tests
UIs
__init__.py
.coverage
.env
.gitignore
.pylintrc
auth.py
config.py
database.py
logger.py
requirements.txt
rich_cli.py
],

database = [

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


],



auth = [

# auth.py >> version 2

import re

import secrets
import hashlib
from typing import Optional, Dict


from database import get_db_instance
from logger import JCELogger
from config import AppConfig


class AuthManager:
    """Handles user authentication, password hashing, and session management"""

    def __init__(self):
        self.current_user: Optional[Dict] = None
        self.logger = JCELogger()  # Add this line to use your custom logger
        self.config = AppConfig()
        # Log initialization of auth manager
        self.logger.log_negocio("auth", "manager_initialized", level="info")

    def login(self, email: str, senha: str) -> bool:
        """Authenticate user and establish session, upgrading legacy passwords if needed."""
        try:
            self.logger.log_negocio("auth", "login_attempt", {"email": email}, "info")

            db = get_db_instance()
            user = db.execute_query(
                "SELECT * FROM usuarios WHERE email = %s", (email,), return_results=True
            )

            if not user:
                self.logger.log_negocio(
                    "auth",
                    "login_failed",
                    {"email": email, "reason": "user_not_found"},
                    "warning",
                )
                self.current_user = None
                return False

            user_data = user[0]
            stored_password = user_data["senha"]

            # Detect legacy hash by prefix
            SUPPORTED_HASH_PREFIXES = ("pbkdf2:sha256:",)
            is_legacy = not stored_password.startswith(SUPPORTED_HASH_PREFIXES)

            # Validate password (legacy or modern)
            password_valid = self.verify_password(stored_password, senha)

            if not password_valid:
                self.logger.log_negocio(
                    "auth",
                    "login_failed",
                    {
                        "email": email,
                        "user_id": user_data["id"],
                        "reason": "invalid_password",
                    },
                    "warning",
                )
                self.current_user = None
                return False

            # Upgrade legacy password hash
            if is_legacy:
                new_hash = self.hash_password(senha)
                db.execute_query(
                    "UPDATE usuarios SET senha = %s WHERE id = %s",
                    (new_hash, user_data["id"]),
                )
                self.logger.log_negocio(
                    "auth",
                    "password_upgraded",
                    {"user_id": user_data["id"], "email": email},
                    "info",
                )

            self.current_user = user_data
            self.logger.log_negocio(
                "auth",
                "login_success",
                {
                    "user_id": user_data["id"],
                    "email": email,
                    "profile": user_data.get("perfil", "unknown"),
                },
                "info",
            )
            return True

        except Exception as e:
            self.logger.log_negocio(
                "auth",
                "login_error",
                {"email": email, "error": str(e), "error_type": type(e).__name__},
                "error",
            )
            self.current_user = None
        return False

    def logout(self):
        """Terminate current session"""
        if self.current_user:
            # Use your custom logger here
            self.logger.log_negocio(
                "auth", "logout", {"user_email": self.current_user["email"]}, "info"
            )
            self.current_user = None

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
        """Verify a password against stored hash (supports legacy plaintext)"""
        # Add this before each return False in the verify_password method
        self.logger.log_negocio(
            "auth",
            "password_verification_failed",
            {"reason": "invalid_format"},
            "debug",
        )

        if not isinstance(stored_hash, str) or not isinstance(provided_password, str):
            return False

        # Legacy plaintext password (for migration or fallback)
        if not stored_hash.startswith("pbkdf2:sha256:"):
            return stored_hash.strip() == provided_password.strip()

        try:
            parts = stored_hash.split("$")
            if len(parts) != 3:
                return False

            # Format: pbkdf2:sha256:600000$salt$hash
            algorithm_parts = parts[0].split(":")
            if len(algorithm_parts) != 3:
                return False

            method = algorithm_parts[1]
            iterations = int(algorithm_parts[2])
            salt = parts[1]
            stored_key = parts[2]

            new_hash = hashlib.pbkdf2_hmac(
                method,
                provided_password.encode("utf-8"),
                salt.encode("utf-8"),
                iterations,
            )
            return secrets.compare_digest(new_hash.hex(), stored_key)

        except (ValueError, AttributeError, IndexError):
            return False

    def validate_password_complexity(self, password: str) -> tuple[bool, str]:
        """Enforce password complexity rules"""
        if len(password) < 8:
            reason = "Password must be at least 8 characters long"
            self.logger.log_negocio(
                "auth",
                "password_complexity_check",
                {"passed": False, "reason": reason},
                "debug",
            )
            return False, reason
        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter"
        self.logger.log_negocio(
            "auth",
            "password_complexity_check",
            {"passed": False, "reason": "reason_message_here"},
            "debug",
        )
        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter"
        self.logger.log_negocio(
            "auth",
            "password_complexity_check",
            {"passed": False, "reason": "reason_message_here"},
            "debug",
        )
        if not re.search(r"[0-9]", password):
            return False, "Password must contain at least one digit"
        self.logger.log_negocio(
            "auth",
            "password_complexity_check",
            {"passed": False, "reason": "reason_message_here"},
            "debug",
        )
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            reason = "Password must contain at least one special character"
            self.logger.log_negocio(
                "auth",
                "password_complexity_check",
                {"passed": False, "reason": reason},
                "debug",
            )
            return False, reason

        # Success case - all checks passed
        self.logger.log_negocio(
            "auth", "password_complexity_check", {"passed": True}, "debug"
        )
        return True, ""

    def get_current_user(self) -> Optional[Dict]:
        """Get currently authenticated user"""
        return self.current_user


# Singleton instance
auth_manager = AuthManager()


],

config = [

# config.py
import os
import logging

from typing import Dict, Any
from dotenv import load_dotenv
from enum import Enum
from logger import JCELogger


# Carrega variáveis de ambiente
load_dotenv()


class Theme(str, Enum):
    """Esquemas de cores disponíveis"""

    PADRAO = "padrao"
    ESCURO = "escuro"


class AppConfig:
    """Configurações centrais da aplicação"""

    # Versão do sistema
    VERSION = "1.3"

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

    LOG_LEVEL = logging.DEBUG  # Nível padrão
    LOG_ROTATION = "midnight"  # Rotação diária
    LOG_RETENTION = 30  # Dias de retenção

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


],


rich_cli = [

# rich_cli.py version 3!!!!!!! integrating logger.py

from datetime import datetime
from typing import Dict, List

from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.prompt import Prompt
from config import AppConfig
from logger import JCELogger


class JECCLI:
    """Interface de usuário unificada para o Sistema JEC usando Rich"""

    _instance = None
    _initialized = False  # Define at class level to avoid Pylint warning

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False  # Initialize instance flag
        return cls._instance

    def __init__(self):
        if self._initialized:  # Now this is safe to check
            return

        self.console = Console(width=80, highlight=False)
        self.theme = AppConfig.load_theme()

        if self.theme not in ["dark", "light"]:
            self.theme = "dark"

        self.user_context = None
        self.system_status = {
            "database": "offline",
            "auth": "inactive",
            "last_update": datetime.now().isoformat(),
        }
        self._initialized = True  # Mark as initialized
        self.logger = JCELogger()

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

logger = [

# logger.py - version 5 (Final Integration)
import logging
from pathlib import Path
from typing import Dict, Optional, Literal, Any, Union

LogLevel = Literal["info", "warning", "error", "debug"]


class JCELogger:
    """Enhanced centralized logger for JEC system with rich_cli integration"""

    def __init__(self):
        self.log_dir = Path("logs")
        self._setup_logging_env()
        self.loggers = {
            "conexoes": self._create_logger("conexoes"),
            "logica": self._create_logger("logica"),
            "interface": self._create_interface_logger(),  # Special format for UI
        }
        self._valid_levels = {"debug", "info", "warning", "error"}

    def _create_interface_logger(self) -> logging.Logger:
        """Special logger for UI events with enhanced formatting"""
        logger = logging.getLogger("jec.interface")
        logger.handlers.clear()

        handler = logging.FileHandler(self.log_dir / "interface.log", encoding="utf-8")
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | UI:%(message)s | %(extra)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        return logger

    def _setup_logging_env(self):
        """Ensure log directory exists"""
        self.log_dir.mkdir(exist_ok=True, parents=True)

    def _create_logger(self, name: str) -> logging.Logger:
        """Standard logger creator"""
        logger = logging.getLogger(f"jec.{name}")
        logger.handlers.clear()

        handler = logging.FileHandler(self.log_dir / f"{name}.log", encoding="utf-8")
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | %(module)s:%(funcName)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        return logger

    def _safe_get_level(self, level: str) -> str:
        """Validate log level with fallback to debug"""
        return level if level in self._valid_levels else "debug"

    def log_conexao(
        self,
        event_type: str,
        message: str,
        level: LogLevel = "info",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log database connections and operations"""
        log_method = getattr(self.loggers["conexoes"], self._safe_get_level(level))
        log_method(
            f"[{event_type}] {message}",
            extra={"metadata": metadata} if metadata else {},
        )

    def log_negocio(
        self,
        module: str,
        action: str,
        metadata: Optional[Dict[str, Any]] = None,
        level: LogLevel = "debug",
    ) -> None:
        """Log business logic events"""
        log_method = getattr(self.loggers["logica"], self._safe_get_level(level))
        log_method(
            f"{module}.{action}", extra={"metadata": metadata} if metadata else {}
        )

    def log_interface(
        self,
        component: str,
        event: str,
        user_ctx: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        level: LogLevel = "info",
    ) -> None:
        """Enhanced UI event logging for rich_cli integration"""
        log_method = getattr(self.loggers["interface"], self._safe_get_level(level))

        # Prepare structured log data
        log_data = {
            "component": component,
            "event": event,
            **({"user": user_ctx} if user_ctx else {}),
            **({"meta": metadata} if metadata else {}),
        }

        log_method(f"{component}.{event}", extra={"extra": log_data})

]

  
  }