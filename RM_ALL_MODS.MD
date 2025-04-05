
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
test_auth_ok.py
test_database_ok.py
test_config_ok.py
test_rich_cli_ok.py
]

database = [

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

]

test_database = status: all passed [
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