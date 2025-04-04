# template Atualização de Proposta

**Data**: `YYYY-MM-DD`  
**Versão**: `X.Y`  

## Mudanças Reconhecidas
✅ `[Módulo]` Descrição sucinta  
⚠️ `[Módulo]` Divergência + justificativa  

## Decisões Técnicas
1. `[Tópico]`:  
   - Antigo: `[Descrição]`  
   - Novo: `[Descrição]`  
   - Motivo: `[Razão técnica/organizacional]`  

## Impactos
- Áreas afetadas: `[Lista]`  
- Migração necessária: `[Sim/Não]`  

## Próximas Ações
- `[Responsável]` `[Tarefa]` `[Prazo]`









context (


revisão 2025-04-04
| Item Proposta original | Implementação Atual | Justificativa/Impacto | Ação Recomendada |
|---------------|---------------------|-----------------------|------------------|
| PassLib       | PBKDF2 customizado  | Solução igualmente segura | Atualizar doc para refletir padrão atual |
| commands.py   | Lógica em main.py   | Acoplamento alto      | Refatorar para módulo separado |
| Temas UI      | Não implementado    | Funcionalidade adiada | Marcar como roadmap futuro |



# JEC System v1.1 (Revisão Técnica)

## 1. Mudanças Principais
- **Autenticação**: Substituição de PassLib por PBKDF2-HMAC-SHA256 customizado (testado)
- **Arquitetura**: Consolidação inicial em 4 módulos principais (lista atual, testado com git repo commit feito para cada etapa >> proceder para (| commands.py   | Lógica em main.py   | Acoplamento alto      | Refatorar para módulo separado |)
)

## 2. Diagrama Atualizado
```plantuml
@startuml
[Main CLI] --> [Auth]
[Main CLI] --> [Database]
[Config] --> .env
@enduml




__pycache__
.pytest_cache
.venv
exports
logs
temp
__init__.py
.env
.gitignore
auth.py
commands.py
config.py
database.py
JEC_System.code-workspace
main.py
requirements.txt
test_auth_ok.py
test_config_ok.py
test_database_ok.py
test_main_ok.py

database (
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

)

test ok (
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

)

auth (
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

)

test ok (
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

)

main (
import logging
from typing import Optional
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich import box
from auth import auth_manager
from database import db_manager

console = Console()


class JECCLI:
    """Main CLI interface for JEC System"""

    def __init__(self):
        self.current_menu = self.main_menu
        self.running = True

    def display_header(self, title: str):
        """Display consistent header for all screens"""
        console.print(f"\n[bold blue]JEC System - {title}[/bold blue]")
        console.print("=" * 50)

    def clear_screen(self):
        """Clear terminal screen"""
        console.print("\n" * 100)  # Simple clear for cross-platform

    def main_menu(self):
        """Display main menu based on user role"""
        self.clear_screen()
        self.display_header("Main Menu")

        user = auth_manager.get_current_user()
        if not user:
            options = {"1": ("Login", self.login), "2": ("Exit", self.exit_app)}
        else:
            role = user["tipo"].capitalize()
            options = {
                "1": ("View Processes", self.list_processes),
                "2": ("Search Cases", self.search_cases),
                "3": ("User Profile", self.user_profile),
                "4": ("Logout", self.logout),
            }
            if role == "Admin":
                options["5"] = ("User Management", self.user_management)

        for key, (desc, _) in options.items():
            console.print(f"[green]{key}[/green]. {desc}")

        choice = Prompt.ask("\nSelect an option", choices=list(options.keys()))
        options[choice][1]()

    def login(self):
        """Handle user login"""
        self.clear_screen()
        self.display_header("Login")

        email = Prompt.ask("Email")
        password = Prompt.ask("Password", password=True)

        if auth_manager.login(email, password):
            console.print("\n[bold green]Login successful![/bold green]")
        else:
            console.print("\n[bold red]Invalid credentials[/bold red]")

        self.press_enter_to_continue()

    def logout(self):
        """Handle user logout"""
        auth_manager.logout()
        console.print("\n[bold green]Logged out successfully[/bold green]")
        self.press_enter_to_continue()

    def search_cases(self):
        """Search for legal cases"""
        self.clear_screen()
        self.display_header("Case Search")

        search_term = Prompt.ask("Enter case number, title or party name")

        try:
            results = db_manager.execute_query(
                """SELECT p.* FROM processos p
                LEFT JOIN partes_processo pp ON p.id = pp.processo_id
                LEFT JOIN partes pa ON pp.parte_id = pa.id
                WHERE p.numero_processo ILIKE %s
                OR p.titulo ILIKE %s
                OR pa.nome ILIKE %s
                ORDER BY p.data_distribuicao DESC""",
                (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"),
                return_results=True,
            )

            if not results:
                console.print("\n[italic]No matching cases found[/italic]")
                self.press_enter_to_continue()
                return

            table = Table(box=box.ROUNDED)
            table.add_column("Case #", style="cyan")
            table.add_column("Title", style="magenta")
            table.add_column("Status")
            table.add_column("Filed On")

            for case in results:
                table.add_row(
                    case["numero_processo"],
                    case["titulo"],
                    case["status"],
                    str(case["data_distribuicao"]),
                )

            console.print(table)
        except Exception as error:
            logging.error("Error searching cases: %s", str(error))
            console.print("\n[bold red]Error searching cases[/bold red]")
        finally:
            self.press_enter_to_continue()

    def user_profile(self):
        """Display and manage user profile"""
        self.clear_screen()
        self.display_header("User Profile")

        user = auth_manager.get_current_user()
        if not user:
            console.print("\n[bold red]Not authenticated[/bold red]")
            self.press_enter_to_continue()
            return

        table = Table(box=box.SIMPLE)
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="magenta")

        table.add_row("Name", user["nome_completo"])
        table.add_row("Email", user["email"])
        table.add_row("User Type", user["tipo"].capitalize())
        table.add_row("Last Login", str(user["ultimo_login"]))

        console.print(table)

        if Confirm.ask("\nDo you want to change your password?"):
            self.change_password()
        else:
            self.press_enter_to_continue()

    def change_password(self):
        """Handle password change"""
        current_pass = Prompt.ask("Current password", password=True)
        if not auth_manager.verify_password(
            auth_manager.current_user["senha"], current_pass
        ):
            console.print("\n[bold red]Incorrect current password[/bold red]")
            self.press_enter_to_continue()
            return

        new_pass = Prompt.ask("New password", password=True)
        confirm_pass = Prompt.ask("Confirm new password", password=True)

        if new_pass != confirm_pass:
            console.print("\n[bold red]Passwords don't match[/bold red]")
            self.press_enter_to_continue()
            return

        valid, msg = auth_manager.validate_password_complexity(new_pass)
        if not valid:
            console.print(f"\n[bold red]{msg}[/bold red]")
            self.press_enter_to_continue()
            return

        try:
            new_hash = auth_manager.hash_password(new_pass)
            db_manager.execute_query(
                "UPDATE usuarios SET senha = %s WHERE id = %s",
                (new_hash, auth_manager.current_user["id"]),
            )
            console.print("\n[bold green]Password changed successfully![/bold green]")
        except Exception as error:
            logging.error("Password change failed: %s", str(error))
            console.print("\n[bold red]Failed to change password[/bold red]")

        self.press_enter_to_continue()

    def user_management(self):
        """Admin interface for user management"""
        if auth_manager.get_current_user()["tipo"] != "admin":
            console.print("\n[bold red]Unauthorized access[/bold red]")
            self.press_enter_to_continue()
            return

        self.clear_screen()
        self.display_header("User Management")

        try:
            users = db_manager.execute_query(
                "SELECT id, nome_completo, email, tipo, data_cadastro FROM usuarios",
                return_results=True,
            )

            table = Table(box=box.ROUNDED)
            table.add_column("ID", style="dim")
            table.add_column("Name", style="cyan")
            table.add_column("Email")
            table.add_column("Type")
            table.add_column("Registered On")

            for user in users:
                table.add_row(
                    str(user["id"]),
                    user["nome_completo"],
                    user["email"],
                    user["tipo"].capitalize(),
                    str(user["data_cadastro"]),
                )

            console.print(table)
        except Exception as error:
            logging.error("Error fetching users: %s", str(error))
            console.print("\n[bold red]Error loading users[/bold red]")
        finally:
            self.press_enter_to_continue()

    def list_processes(self):
        """List legal processes"""
        self.clear_screen()
        self.display_header("Active Processes")

        try:
            processes = db_manager.execute_query(
                "SELECT * FROM processos_ativos ORDER BY data_distribuicao DESC",
                return_results=True,
            )

            if not processes:
                console.print("\n[italic]No processes found[/italic]")
                self.press_enter_to_continue()
                return

            table = Table(box=box.ROUNDED)
            table.add_column("Case #", style="cyan")
            table.add_column("Title", style="magenta")
            table.add_column("Category")
            table.add_column("Status")
            table.add_column("Filed On")

            for process in processes:
                table.add_row(
                    process["numero_processo"],
                    process["titulo"],
                    process["categoria"],
                    process["status"],
                    str(process["data_distribuicao"]),
                )

            console.print(table)
        except Exception as error:
            logging.error("Error fetching processes: %s", str(error))
            console.print("\n[bold red]Error loading processes[/bold red]")
        finally:
            self.press_enter_to_continue()

    def press_enter_to_continue(self):
        """Utility method for consistent pause"""
        Prompt.ask("\n[dim]Press Enter to continue...[/dim]")
        self.current_menu = self.main_menu

    def exit_app(self):
        """Cleanly exit application"""
        console.print("\n[bold blue]Closing JEC System...[/bold blue]")
        db_manager.close_all_connections()
        self.running = False

    def run(self):
        """Main application loop"""
        while self.running:
            try:
                self.current_menu()
            except KeyboardInterrupt:
                self.exit_app()
            except Exception as error:
                logging.error("Unexpected error: %s", str(error))
                console.print("\n[bold red]An unexpected error occurred[/bold red]")
                self.press_enter_to_continue()


if __name__ == "__main__":
    try:
        cli = JECCLI()
        cli.run()
    except Exception as error:
        logging.critical("Application crash: %s", str(error))
        console.print("\n[bold red]Fatal error - application terminated[/bold red]")
        db_manager.close_all_connections()

)

test ok (
import pytest
from unittest.mock import patch, MagicMock, call
from main import JECCLI
from auth import auth_manager
from database import db_manager
from rich.table import Table


@pytest.fixture
def cli():
    return JECCLI()


@pytest.fixture
def mock_console_print():
    with patch("main.console.print") as mock:
        yield mock


@pytest.fixture
def mock_prompt_ask():
    with patch("main.Prompt.ask") as mock:
        yield mock


@pytest.fixture
def mock_confirm_ask():
    with patch("main.Confirm.ask") as mock:
        yield mock


def test_display_header(cli, mock_console_print):
    cli.display_header("Test Title")
    mock_console_print.assert_any_call(
        "\n[bold blue]JEC System - Test Title[/bold blue]"
    )
    mock_console_print.assert_any_call("=" * 50)


def test_clear_screen(cli, mock_console_print):
    cli.clear_screen()
    mock_console_print.assert_called_with("\n" * 100)


def test_main_menu_unauthenticated(cli, mock_prompt_ask):
    with patch("main.auth_manager.get_current_user", return_value=None):
        mock_prompt_ask.return_value = "1"
        with patch.object(cli, "login") as mock_login:
            cli.main_menu()
            mock_login.assert_called_once()


def test_login_success(cli, mock_prompt_ask, mock_console_print):
    with patch("main.auth_manager.login", return_value=True):
        mock_prompt_ask.side_effect = [
            "test@example.com",
            "password",
            "",
        ]  # Added Enter press
        cli.login()
        mock_console_print.assert_any_call(
            "\n[bold green]Login successful![/bold green]"
        )


def test_login_failure(cli, mock_prompt_ask, mock_console_print):
    with patch("main.auth_manager.login", return_value=False):
        mock_prompt_ask.side_effect = [
            "test@example.com",
            "wrongpass",
            "",
        ]  # Added Enter press
        cli.login()
        mock_console_print.assert_any_call("\n[bold red]Invalid credentials[/bold red]")


def test_search_cases(cli, mock_prompt_ask, mock_console_print):
    test_data = [
        {
            "numero_processo": "123",
            "titulo": "Test Case",
            "status": "Active",
            "data_distribuicao": "2023-01-01",
        }
    ]

    with patch("main.db_manager.execute_query", return_value=test_data):
        mock_prompt_ask.side_effect = ["search term", ""]  # Search term + Enter
        cli.search_cases()

        # Verify table structure was created
        assert any(
            isinstance(args[0], Table) for args, _ in mock_console_print.call_args_list
        )


def test_user_profile(cli, mock_confirm_ask, mock_console_print):
    test_user = {
        "nome_completo": "Test User",
        "email": "test@example.com",
        "tipo": "advogado",
        "ultimo_login": "2023-01-01",
    }

    with patch("main.auth_manager.get_current_user", return_value=test_user):
        mock_confirm_ask.return_value = False
        cli.user_profile()

        # Verify the table was printed with user data
        table_calls = [
            args[0]
            for args, _ in mock_console_print.call_args_list
            if isinstance(args[0], Table)
        ]
        assert len(table_calls) == 1

        # Get the table rows
        table = table_calls[0]
        rows = [column._cells for column in table.columns]  # Access table data

        # Verify all user data is present in the table
        assert test_user["nome_completo"] in rows[1]  # Name column values
        assert test_user["email"] in rows[1]  # Value column values
        assert test_user["tipo"].capitalize() in rows[1]
        assert str(test_user["ultimo_login"]) in rows[1]


def test_change_password_success(cli, mock_prompt_ask, mock_console_print):
    with patch("main.auth_manager.current_user", {"id": 1, "senha": "hashed"}):
        with patch("main.auth_manager.verify_password", return_value=True):
            with patch(
                "main.auth_manager.validate_password_complexity",
                return_value=(True, ""),
            ):
                with patch("main.auth_manager.hash_password", return_value="new_hash"):
                    with patch("main.db_manager.execute_query"):
                        mock_prompt_ask.side_effect = [
                            "oldpass",
                            "newpass",
                            "newpass",
                            "",  # Added Enter press
                        ]
                        cli.change_password()
                        mock_console_print.assert_any_call(
                            "\n[bold green]Password changed successfully![/bold green]"
                        )


def test_list_processes(cli, mock_console_print):
    test_data = [
        {
            "numero_processo": "123",
            "titulo": "Test Case",
            "categoria": "Civil",
            "status": "Active",
            "data_distribuicao": "2023-01-01",
        }
    ]

    with patch("main.db_manager.execute_query", return_value=test_data):
        cli.list_processes()

        # Verify table was printed
        assert any(
            isinstance(args[0], Table) for args, _ in mock_console_print.call_args_list
        )


def test_exit_app(cli):
    cli.running = True
    with patch("main.db_manager.close_all_connections") as mock_close:
        cli.exit_app()
        assert cli.running is False
        mock_close.assert_called_once()


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])

)


config (
# version 2

"""
Configuration management for JEC System

This module handles all system configuration including:
- Environment variable loading and validation
- Default value management
- Configuration state management
"""

import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from pathlib import Path


class ConfigManager:
    """Centralized configuration management for the application"""

    _instance = None
    _config: Dict[str, Any] = {}
    _initialized = False  # Move this to class level

    def __new__(cls):
        """Implement singleton pattern"""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            # Remove _initialized assignment here
        return cls._instance

    def __init__(self):
        """Initialize configuration - only happens once due to singleton"""
        if self.__class__._initialized:  # Access class-level attribute
            return

        self.__class__._initialized = True  # Set class-level attribute
        self._load_configuration()
        self._validate_configuration()

    def _load_configuration(self):
        """Load configuration from environment variables"""
        # Try to load from .env file in project root
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        else:
            load_dotenv()

        # Database configuration
        self._config.update(
            {
                "DB_HOST": os.getenv("DB_HOST", "localhost"),
                "DB_PORT": os.getenv("DB_PORT", "5432"),
                "DB_USUARIO": os.getenv("DB_USUARIO"),
                "DB_SENHA": os.getenv("DB_SENHA"),
                "DB_NOME": os.getenv("DB_NOME", "jec_system"),
                "DB_SCHEMA": os.getenv("DB_SCHEMA", "jec"),
                "DB_MIN_CONNECTIONS": int(os.getenv("DB_MIN_CONNECTIONS", "1")),
                "DB_MAX_CONNECTIONS": int(os.getenv("DB_MAX_CONNECTIONS", "5")),
                # Application configuration
                "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
                "LOG_FILE": os.getenv("LOG_FILE", "jec_system.log"),
                "MAX_LOG_SIZE": int(os.getenv("MAX_LOG_SIZE", "1048576")),  # 1MB
                "LOG_BACKUP_COUNT": int(os.getenv("LOG_BACKUP_COUNT", "3")),
                # Security configuration
                "SESSION_TIMEOUT": int(
                    os.getenv("SESSION_TIMEOUT", "1800")
                ),  # 30 minutes
                "PASSWORD_RESET_TIMEOUT": int(
                    os.getenv("PASSWORD_RESET_TIMEOUT", "3600")
                ),  # 1 hour
            }
        )

    def _validate_configuration(self):
        """Validate required configuration values"""
        required = ["DB_USUARIO", "DB_SENHA", "DB_NOME"]
        missing = [var for var in required if not self._config.get(var)]

        if missing:
            error_msg = (
                f"Missing required configuration variables: {', '.join(missing)}"
            )
            logging.critical(error_msg)
            raise ValueError(error_msg)

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get configuration value by key"""
        return self._config.get(key, default)

    def set(self, key: str, value: Any):
        """Set configuration value (for testing purposes)"""
        self._config[key] = value

    def reload(self):
        """Reload configuration from environment"""
        self._config.clear()
        self._load_configuration()
        self._validate_configuration()


# Singleton instance
config = ConfigManager()

)

test ok (
#####version 6 >> update if new vresion please

import pytest
from unittest.mock import patch, MagicMock
import os
from pathlib import Path
from config import ConfigManager, config
import dotenv
import sys


@pytest.fixture(autouse=True)
def reset_config_singleton():
    """Completely reset the ConfigManager between tests"""
    # Backup original state
    original_instance = ConfigManager._instance
    original_initialized = ConfigManager._initialized
    original_config = ConfigManager._config.copy()

    # Reset for test
    ConfigManager._instance = None
    ConfigManager._initialized = False
    ConfigManager._config = {}

    # Also reset the module-level config variable
    if "config" in sys.modules[__name__].__dict__:
        sys.modules[__name__].__dict__["config"] = None

    yield

    # Restore original state
    ConfigManager._instance = original_instance
    ConfigManager._initialized = original_initialized
    ConfigManager._config = original_config
    if "config" in sys.modules[__name__].__dict__:
        sys.modules[__name__].__dict__["config"] = original_instance


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing"""
    # Clear all existing env vars that might interfere
    for key in ["DB_HOST", "DB_PORT", "DB_USUARIO", "DB_SENHA", "DB_NOME", "LOG_LEVEL"]:
        monkeypatch.delenv(key, raising=False)

    # Set required minimum config
    monkeypatch.setenv("DB_USUARIO", "test_user")
    monkeypatch.setenv("DB_SENHA", "test_pass")
    monkeypatch.setenv("DB_NOME", "test_db")


@pytest.fixture
def mock_env_file(tmp_path, monkeypatch):
    """Create a mock .env file and ensure it's loaded"""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DB_HOST=file_host\n"
        "DB_PORT=4321\n"
        "DB_USUARIO=envfile_user\n"
        "DB_SENHA=envfile_pass\n"
        "DB_NOME=envfile_db\n"
    )

    # Mock Path.exists to only return True for our test file
    def mock_exists(path):
        return str(path) == str(env_file)

    monkeypatch.setattr(Path, "exists", mock_exists)

    # Create a proper mock for load_dotenv
    original_load = dotenv.load_dotenv

    def mock_load_dotenv(path=None, **kwargs):
        if path is None:
            path = env_file
        # Actually load from our test file
        return original_load(path, **kwargs)

    monkeypatch.setattr(dotenv, "load_dotenv", mock_load_dotenv)
    monkeypatch.setattr("config.load_dotenv", mock_load_dotenv)

    return env_file


def test_singleton_pattern():
    """Test that ConfigManager is a proper singleton"""
    instance1 = ConfigManager()
    instance2 = ConfigManager()
    assert instance1 is instance2


def test_config_initialization(mock_env_vars):
    """Test basic config initialization with environment variables"""
    cfg = ConfigManager()
    assert cfg.get("DB_USUARIO") == "test_user"
    assert cfg.get("DB_SENHA") == "test_pass"
    assert cfg.get("DB_NOME") == "test_db"
    assert cfg.get("DB_MAX_CONNECTIONS") == 5  # Default value


def test_env_file_loading(mock_env_file, monkeypatch):
    """Test that config loads from .env file when present"""
    # Ensure environment doesn't have these vars
    monkeypatch.delenv("DB_HOST", raising=False)
    monkeypatch.delenv("DB_PORT", raising=False)
    monkeypatch.delenv("DB_USUARIO", raising=False)
    monkeypatch.delenv("DB_SENHA", raising=False)
    monkeypatch.delenv("DB_NOME", raising=False)

    # Create a fresh ConfigManager which should load from our mock .env file
    cfg = ConfigManager()
    assert cfg.get("DB_HOST") == "file_host"
    assert cfg.get("DB_PORT") == "4321"
    assert cfg.get("DB_USUARIO") == "envfile_user"


def test_missing_required_config(monkeypatch):
    """Test that missing required config raises ValueError"""
    # Clear all required vars
    for key in ["DB_USUARIO", "DB_SENHA", "DB_NOME"]:
        monkeypatch.delenv(key, raising=False)

    # Ensure no .env file is loaded
    monkeypatch.setattr(Path, "exists", lambda *args: False)
    monkeypatch.setattr("config.load_dotenv", lambda *args, **kwargs: False)

    with pytest.raises(ValueError) as excinfo:
        ConfigManager()
    assert "Missing required configuration variables" in str(excinfo.value)


def test_config_reload(mock_env_vars, monkeypatch):
    """Test that reload() refreshes configuration"""
    cfg = ConfigManager()
    monkeypatch.setenv("DB_USUARIO", "new_user")
    cfg.reload()
    assert cfg.get("DB_USUARIO") == "new_user"


def test_config_get_with_default(mock_env_vars):
    """Test get() with default values"""
    cfg = ConfigManager()
    assert cfg.get("NON_EXISTENT_KEY", "default") == "default"
    assert cfg.get("NON_EXISTENT_KEY") is None


def test_config_set_method(mock_env_vars):
    """Test that set() method works for testing purposes"""
    cfg = ConfigManager()
    cfg.set("TEST_KEY", "test_value")
    assert cfg.get("TEST_KEY") == "test_value"


def test_no_env_file(monkeypatch):
    """Test behavior when no .env file exists"""
    monkeypatch.setattr(Path, "exists", lambda *args: False)
    monkeypatch.setattr("config.load_dotenv", lambda *args, **kwargs: False)

    # Set required vars directly in environment
    monkeypatch.setenv("DB_USUARIO", "test_user")
    monkeypatch.setenv("DB_SENHA", "test_pass")
    monkeypatch.setenv("DB_NOME", "test_db")

    cfg = ConfigManager()
    assert cfg.get("DB_USUARIO") == "test_user"


def test_singleton_instance_access():
    """Test that the singleton instance can be accessed via config variable"""
    # Import and reload the module to reset state
    import importlib
    import config

    # Reset class-level attributes through the module
    config.ConfigManager._instance = None
    config.ConfigManager._initialized = False
    config.ConfigManager._config = {}

    # Reload the module to reset the config variable
    importlib.reload(config)

    # Create new instance
    cfg = config.ConfigManager()

    # Verify module-level config matches
    assert config.config is cfg
    assert isinstance(config.config, config.ConfigManager)


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])

)
)

db info (
JEC FULL STRUCTURE


SELECT
    table_name,
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
FROM
    information_schema.columns
WHERE
    table_schema = 'jec'
ORDER BY
    table_name,
    ordinal_position;

"audit_log"	"id"	"uuid"		"NO"	"uuid_generate_v4()"
"audit_log"	"user_id"	"uuid"		"YES"	
"audit_log"	"action"	"character varying"	50	"NO"	
"audit_log"	"description"	"text"		"YES"	
"audit_log"	"ip_address"	"character varying"	45	"YES"	
"audit_log"	"timestamp"	"timestamp without time zone"		"YES"	"CURRENT_TIMESTAMP"
"categorias_causas"	"id"	"uuid"		"NO"	"uuid_generate_v4()"
"categorias_causas"	"categoria_pai_id"	"uuid"		"YES"	
"categorias_causas"	"nome"	"character varying"	50	"NO"	
"categorias_causas"	"descricao"	"text"		"YES"	
"categorias_causas"	"valor_maximo"	"numeric"		"YES"	
"documentos"	"id"	"uuid"		"NO"	"uuid_generate_v4()"
"documentos"	"processo_id"	"uuid"		"NO"	
"documentos"	"tipo"	"character varying"	50	"NO"	
"documentos"	"nome_arquivo"	"character varying"	100	"NO"	
"documentos"	"caminho_arquivo"	"character varying"	255	"NO"	
"documentos"	"data_envio"	"timestamp without time zone"		"YES"	"CURRENT_TIMESTAMP"
"documentos"	"descricao"	"text"		"YES"	
"documentos"	"obrigatorio"	"boolean"		"YES"	"true"
"partes"	"id"	"uuid"		"NO"	"uuid_generate_v4()"
"partes"	"tipo"	"character varying"	15	"NO"	
"partes"	"nome"	"character varying"	100	"NO"	
"partes"	"cpf_cnpj"	"character varying"	20	"NO"	
"partes"	"endereco"	"text"		"YES"	
"partes"	"telefone"	"character varying"	20	"YES"	
"partes"	"email"	"character varying"	100	"YES"	
"partes"	"advogado_id"	"uuid"		"YES"	
"partes_processo"	"id"	"uuid"		"NO"	"uuid_generate_v4()"
"partes_processo"	"processo_id"	"uuid"		"NO"	
"partes_processo"	"parte_id"	"uuid"		"NO"	
"partes_processo"	"tipo"	"character varying"	15	"NO"	
"partes_processo"	"principal"	"boolean"		"YES"	"false"
"processos"	"id"	"uuid"		"NO"	"uuid_generate_v4()"
"processos"	"numero_processo"	"character varying"	25	"NO"	
"processos"	"titulo"	"character varying"	100	"NO"	
"processos"	"descricao"	"text"		"YES"	
"processos"	"categoria_id"	"uuid"		"NO"	
"processos"	"subcategoria_id"	"uuid"		"YES"	
"processos"	"valor_causa"	"numeric"		"NO"	
"processos"	"data_distribuicao"	"date"		"NO"	
"processos"	"status"	"character varying"	30	"NO"	
"processos"	"juiz_id"	"uuid"		"YES"	
"processos"	"servidor_id"	"uuid"		"YES"	
"processos"	"data_criacao"	"timestamp without time zone"		"YES"	"CURRENT_TIMESTAMP"
"processos"	"data_atualizacao"	"timestamp without time zone"		"YES"	"CURRENT_TIMESTAMP"
"processos_ativos"	"id"	"uuid"		"YES"	
"processos_ativos"	"numero_processo"	"character varying"	25	"YES"	
"processos_ativos"	"titulo"	"character varying"	100	"YES"	
"processos_ativos"	"categoria"	"character varying"	50	"YES"	
"processos_ativos"	"status"	"character varying"	30	"YES"	
"processos_ativos"	"data_distribuicao"	"date"		"YES"	
"processos_ativos"	"autor"	"character varying"	100	"YES"	
"test_counter"	"id"	"integer"		"NO"	
"test_counter"	"value"	"integer"		"YES"	
"usuarios"	"id"	"uuid"		"NO"	"uuid_generate_v4()"
"usuarios"	"cpf"	"character varying"	14	"NO"	
"usuarios"	"nome_completo"	"character varying"	100	"NO"	
"usuarios"	"email"	"character varying"	100	"NO"	
"usuarios"	"senha"	"character varying"	255	"NO"	
"usuarios"	"tipo"	"character varying"	20	"NO"	
"usuarios"	"telefone"	"character varying"	20	"YES"	
"usuarios"	"data_cadastro"	"timestamp without time zone"		"YES"	"CURRENT_TIMESTAMP"
"usuarios"	"ultimo_login"	"timestamp without time zone"		"YES"	



SELECT * FROM jec.usuarios;

"f7ff954d-dbc5-4ae2-b8f1-9963a8995905"	"67867867867"	"test2"	"test2@asdfas.asdf"	"123456"	"servidor"		"2025-03-28 16:24:48.140317"	
"61588c5f-1613-435d-9f89-16e22edff6b7"	"45645645645"	"dfghsdfh dgsdfg"	"dsfgsdfgsd@asdfa.asdf"	"123123"	"parte"		"2025-03-28 17:21:07.925657"	
"626ff173-1831-4c6e-b8ec-af8aa6c4b60b"	"45678945625"	"fghjfgh rtyuytu"	"rturty@sdfg.sdgf"	"789369"	"advogado"		"2025-03-29 16:57:12.837847"	
"49718dea-865a-4f11-b46c-468f579663ce"	"65465465458"	"bnmvbn"	"vbnmvnb@fghdfgh.dfgh"	"852147"	"parte"		"2025-03-29 19:40:20.125683"	
"fb26bd61-0e03-498a-a389-fa33a78d3de1"	"96396396336"	"asdfasd yuityui ababa"	"tyurtyurtyu@yretyrety.ertyr"	"asdfasdf"	"parte"		"2025-03-30 03:52:49.284764"	
"db70e112-ca4e-4caf-922e-584f5e397e2e"	"05405405454"	"OIYOIYOIYIY"	"oytoyotoyot@oytoyto.oyotoy"	"123123"	"parte"		"2025-03-30 05:08:52.961166"	
"a540dc26-8955-470f-a02e-521af7eca99d"	"78978978978"	"khjkjhk hjkjhk"	"sdfgsdfg@asfasdf.asdfa"	"456789"	"parte"		"2025-03-30 05:24:57.044347"	
"41c2576c-a2dc-4b0c-9415-8fd446dd63d7"	"54354354367"	"VICVIC"	"vicvic@vic.com"	"pbkdf2:sha256:600000$3390a8f9a74160c3d9525c2ec7ece963$cd09980696fbe7440ff478ec2b3eab91fa92ba0fa24286f747dfeed12c75731b"	"advogado"	"243523452345"	"2025-04-01 01:05:31.542927"	"2025-04-01 01:44:26.855411"
"eeb0b1a9-e33f-4cd6-ab8c-6dfde8ba921f"	"45678945645"	"laks qwerqwer"	"lask@qwerq.qwer"	"laskqwer"	"parte"		"2025-03-30 08:31:46.370925"	
"db4db0c1-d50c-410e-bcb5-279e9df97ba7"	"98798767856"	"Victor Oliveira"	"v.oliveira@gmail.com"	"123745"	"parte"		"2025-03-30 15:20:55.636815"	
"352cea81-6236-4e30-89a3-8c4d9834e0d0"	"45678923432"	"asdfasdf qerqwerqwer"	"sadfasdf@waerqwer.qwer"	"pbkdf2:sha256:100000$9b84a0df21456deea678a309f7990256$bfed548042e458e3ae4445258a54ebdc0890ebb94310052d28edb986dd1ae69b"	"servidor"		"2025-03-31 22:53:09.326549"	
"bb54b3e9-d83c-4cf1-940b-1b4ceca99833"	"12312312312"	"sdfgsdfg rtyertyerty"	"kkkkkkkkkkkkkkk@gmai.com"	"pbkdf2:sha256:100000$59f27e27775e603613a854900d9cafa5$439eb83a2ac0b1dda22cc97612d15a7ec7aa0eadd3cdd22e89d4e4f3ab34f528"	"parte"		"2025-03-30 05:03:58.775131"	"2025-03-31 23:11:40.263474"
"fe7c837a-fbcf-4b47-ad63-e6cc26b5cb3b"	"00000000000"	"vvvvvvvvv dddddd"	"dddddd.ddddd@gggg.cccc"	"pbkdf2:sha256:600000$1f3fc30079f12de6f4d1e5d43b286a2c$61f918afa328414eb81e57c7a95aed02632ada52966482f2b9e6617fa87bc226"	"juiz"		"2025-03-28 16:53:44.539278"	"2025-04-01 01:04:24.65046"


)

hashing guidelines:

[
Password Hashing Implementation Details
The code uses a custom implementation of PBKDF2-HMAC-SHA256 password hashing rather than PassLib. Here's how it works:
Password Hashing (Creating a New Hash)
The hash_password method:
pythonCopiardef hash_password(self, password, salt=None):
    """Hash password with PBKDF2-HMAC-SHA256"""
    if salt is None:
        salt = secrets.token_hex(16)  # Generate a random 16-byte salt as hex string
    iterations = 600000  # A high number of iterations increases security
    hashed = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations
    )
    return f"pbkdf2:sha256:{iterations}${salt}${hashed.hex()}"
This method:

Generates a cryptographically secure random salt (32 hex characters) using secrets.token_hex(16) if none is provided
Sets a high iteration count (600,000) to make brute force attacks more difficult
Uses Python's built-in hashlib.pbkdf2_hmac to generate the hash
Returns a formatted string with algorithm information, iterations, salt, and hash in the format: pbkdf2:sha256:600000$<salt>$<hash>

Password Verification
The verify_password method:
pythonCopiardef verify_password(self, stored_hash, provided_password):
    """Verify a password against stored hash"""
    if not stored_hash.startswith("pbkdf2:sha256:"):
        # Legacy plaintext password (for migration purposes)
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
This method:

Checks if the stored hash uses the modern format, if not, falls back to legacy comparison
Parses the hash string to extract the algorithm, method, iterations, salt, and hash
Re-computes the hash using the provided password and extracted parameters
Uses secrets.compare_digest() for a constant-time comparison to prevent timing attacks

Password Migration
The login method includes an automatic password rehashing mechanism:
pythonCopiarif user and self.verify_password(user["senha"], senha):
    # Password rehashing logic
    if not user["senha"].startswith("pbkdf2:sha256:"):
        new_hash = self.hash_password(senha)
        cur.execute(
            sql.SQL("UPDATE usuarios SET senha = %s WHERE id = %s"),
            (new_hash, user["id"]),
        )
This code:

Checks if the password is stored in the legacy format
If so, rehashes it using the modern PBKDF2 format
Updates the database with the new hash

Password Complexity Validation
The validate_password_complexity method:
pythonCopiardef validate_password_complexity(self, password):
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
This enforces the following password complexity rules:

Minimum 8 characters
At least one uppercase letter
At least one lowercase letter
At least one digit
At least one special character

Usage Flow
The whole password handling system is used in several key workflows:

User Creation:

Hash password with hash_password()
Store hash in the database


User Login:

Retrieve stored hash from database
Verify with verify_password()
Automatically upgrade legacy passwords to PBKDF2 format


Password Change:

Verify current password with verify_password()
Validate complexity of new password with validate_password_complexity()
Hash new password with hash_password()
Store new hash in database



This implementation follows industry best practices for password storage, including secure salt generation, high iteration counts, and constant-time comparison, which effectively protects against various attacks like rainbow tables, brute force, and timing attacks.
]

project be implemented:

{
  "projeto": {
    "nome": "JEC System",
    "tipo": "CLI",
    "linguagem": "Python",
    "interface": "Rich",
    "escopo": "gestao_juizado_especial_civel",
    "media_max_usuarios": 15
  },

"versoes": {
  "1.0": "Proposta inicial (2025-01)",
  "1.1": "2025-04-04: Implementação core + autenticação",
  "roadmap": {
    "v1.2": "Modularização de comandos",
    "v2.0": "Sistema de temas UI"
  }
},
"testes": {
  "cobertura": {
    "auth.py": "100%",
    "database.py": "100%",
    "main.py": "100%"
    "config.py": "100%"
  },
  "estrategia": "TDD com pytest - standalone run-from-root pytest files"
},
  "estrutura_arquivos": {
    "localizacao_arquivos": "todos os arquivos em root",
    "arquivos_principais": [
      {
        "name": "main.py",
        "role": "Entry Point",
        "description": "Handles the CLI logic, user interactions, and command execution."
      },
      {
        "name": "database.py",
        "role": "Database Manager",
        "description": "Handles connections and queries to the PostgreSQL database."
      },
      {
        "name": "auth.py",
        "role": "Authentication & Security",
        "description": "Handles user authentication, password hashing ("PBKDF2-HMAC-SHA256 (600k iterações)"
), and session management."
      },
      {
        "name": "config.py",
        "role": "Basic config for ui and other configs",
        "description": "Handles basic configs"
      },      {
        "name": "commands.py",
        "role": "CLI Commands & Business Logic",
        "description": "Defines commands using rich, implementing the core functionalities."
      }
    ],
    "arquivos_suporte_e_venv": [".env", ".gitignore", ".venv"],
    "template_env": {
      "DB_HOST": "",
      "DB_PORT": "",
      "DB_USUARIO": "",
      "DB_SENHA": "",
      "DB_NOME": "",
      "DB_SCHEMA": "jec"
    }
  },
  "modulos_nucleares": {
    "config": {
      "descricao": "Gerenciamento de temas",
      "temas": ["padrao", "escuro"],
      "funcionalidades": ["esquemas_cores"]
    },
    "banco_dados": {
      "tipo": "PostgreSQL",
      "conexao": {
        "pooling": "SimpleConnectionPool (implementado com reconexão automática)",
        "min_conexoes": 1,
        "max_conexoes": 5,
        "timeout": 30,
        "tentativas_reconexao": 3
      },
"implementado": {
  "core": ["auth", "database", "cli_base"],
  "pendente": ["temas_ui", "modularizacao"]
},
    },
    "autenticacao": {
      "seguranca": {
        "hashing": "PBKDF2-HMAC-SHA256",
        "iteracoes": 600000,
        "tempo_expiracao_sessao": "30_minutos"
      },
      "roles_usuarios": ["advogado", "juiz", "servidor", "parte", "visitante"]
    },
    "menus": {
      "estilo": "painel_numerado",
      "funcionalidades": ["atalhos", "contexto_dinamico", "entrada_sql"]
    },
    "servicos": {
      "entidades": ["corresponde_info_db"]
    }
  },
  "especificacoes_tecnicas": {
    "sistema_operacional": "Windows",
    "servidor": {
      "modelo": "Acer 2020",
      "especificacoes": "20GB RAM, Intel Core i5"
    },
    "rede": "Wi-Fi LAN",
    "log": {
      "nivel": "detalhado",
      "requisitos": [
        "psycopg2-binary",
        "python-dotenv",
        "rich",
        "passlib",
        "[ADICIONAR MAIS SE NECESSARIO]"
      ]
    }
  },
  "funcionalidades": {
    "essenciais": {
      "gerenciamento_usuarios": ["CRUD", "autenticacao"],
      "rastreamento_processos": ["status", "prazos"]
    },
    "futuro": {
      "calendario": ["audiencias", "compromissos"],
      "integracoes": ["PJe", "Esaj"],
      "escalabilidade": ["dados_flexiveis", "principios_DRY"]
    }
  },
  "requisitos_ui": {
    "estilo": "DOS-like_com_cores",
    "componentes": [
      "barras_progresso",
      "seletor_tema",
      "tela_login"
    ],
    "navegacao": {
      "restricoes_visitante": true,
      "pre_visualizacoes_rapidas": true
    }
  },
  "entrega": {
    "prazo": "15_dias",
    "prioridade": "gerenciamento_documentos",
    "restricoes": ["uso_interno_somente"]
  },
  "implementacao": {
    "foco_atual": [
      "conexao_banco_dados",
      "CRUD_basico_usuarios"
    ],
    "padroes_codigo": [
      "tratamento_erros",
      "validacao_parametros",
      "robustez_conexao",
      "configuracao_env"
    ]
  }
}




instructions: after reading, follow similar pattern of next most important file and create it, then follow similar testing structure and please provide a standalone run-from-root test_modulename.py pytest file pls