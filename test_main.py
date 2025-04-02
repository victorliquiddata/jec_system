import pytest
from unittest.mock import patch, MagicMock
from main import JECCLI
from auth import auth_manager
from database import db_manager


@pytest.fixture
def cli():
    return JECCLI()


@pytest.fixture
def mock_console():
    with patch("main.console") as mock:
        yield mock


@pytest.fixture
def mock_auth():
    with patch("main.auth_manager") as mock:
        yield mock


@pytest.fixture
def mock_db():
    with patch("main.db_manager") as mock:
        yield mock


def test_display_header(cli, mock_console):
    cli.display_header("Test Title")
    mock_console.print.assert_any_call(
        "\n[bold blue]JEC System - Test Title[/bold blue]"
    )
    mock_console.print.assert_any_call("=" * 50)


def test_clear_screen(cli, mock_console):
    cli.clear_screen()
    mock_console.print.assert_called_with("\n" * 100)


def test_main_menu_unauthenticated(cli, mock_auth, mock_console):
    mock_auth.get_current_user.return_value = None
    with patch.object(cli, "login") as mock_login:
        with patch.object(cli, "exit_app") as mock_exit:
            # Simulate user choosing option 1 (Login)
            with patch("main.Prompt.ask", return_value="1"):
                cli.main_menu()
                mock_login.assert_called_once()


def test_main_menu_authenticated(cli, mock_auth, mock_console):
    mock_auth.get_current_user.return_value = {"tipo": "advogado"}
    with patch.object(cli, "list_processes") as mock_list:
        # Simulate user choosing option 1 (View Processes)
        with patch("main.Prompt.ask", return_value="1"):
            cli.main_menu()
            mock_list.assert_called_once()


def test_main_menu_admin(cli, mock_auth, mock_console):
    mock_auth.get_current_user.return_value = {"tipo": "admin"}
    with patch.object(cli, "user_management") as mock_manage:
        # Simulate admin choosing option 5 (User Management)
        with patch("main.Prompt.ask", return_value="5"):
            cli.main_menu()
            mock_manage.assert_called_once()


def test_login_success(cli, mock_auth, mock_console):
    mock_auth.login.return_value = True
    with patch("main.Prompt.ask", side_effect=["test@example.com", "password"]):
        cli.login()
        mock_console.print.assert_any_call(
            "\n[bold green]Login successful![/bold green]"
        )


def test_login_failure(cli, mock_auth, mock_console):
    mock_auth.login.return_value = False
    with patch("main.Prompt.ask", side_effect=["test@example.com", "wrongpass"]):
        cli.login()
        mock_console.print.assert_any_call("\n[bold red]Invalid credentials[/bold red]")


def test_logout(cli, mock_auth, mock_console):
    cli.logout()
    mock_auth.logout.assert_called_once()
    mock_console.print.assert_called_with(
        "\n[bold green]Logged out successfully[/bold green]"
    )


def test_search_cases(cli, mock_db, mock_console):
    mock_db.execute_query.return_value = [
        {
            "numero_processo": "123",
            "titulo": "Test Case",
            "status": "Active",
            "data_distribuicao": "2023-01-01",
        }
    ]
    with patch("main.Prompt.ask", return_value="test"):
        cli.search_cases()
        mock_console.print.assert_any_call(
            "[cyan]Case #[/cyan]", "[magenta]Title[/magenta]", "Status", "Filed On"
        )


def test_search_cases_empty(cli, mock_db, mock_console):
    mock_db.execute_query.return_value = []
    with patch("main.Prompt.ask", return_value="test"):
        cli.search_cases()
        mock_console.print.assert_any_call("\n[italic]No matching cases found[/italic]")


def test_user_profile(cli, mock_auth, mock_console):
    mock_auth.get_current_user.return_value = {
        "nome_completo": "Test User",
        "email": "test@example.com",
        "tipo": "advogado",
        "ultimo_login": "2023-01-01",
    }
    with patch("main.Confirm.ask", return_value=False):
        cli.user_profile()
        mock_console.print.assert_any_call("Name", "Test User")


def test_change_password_success(cli, mock_auth, mock_db, mock_console):
    mock_auth.current_user = {"id": 1, "senha": "hashed"}
    mock_auth.verify_password.return_value = True
    mock_auth.validate_password_complexity.return_value = (True, "")
    with patch("main.Prompt.ask", side_effect=["oldpass", "newpass", "newpass"]):
        cli.change_password()
        mock_db.execute_query.assert_called_once()
        mock_console.print.assert_any_call(
            "\n[bold green]Password changed successfully![/bold green]"
        )


def test_list_processes(cli, mock_db, mock_console):
    mock_db.execute_query.return_value = [
        {
            "numero_processo": "123",
            "titulo": "Test Case",
            "categoria": "Civil",
            "status": "Active",
            "data_distribuicao": "2023-01-01",
        }
    ]
    cli.list_processes()
    mock_console.print.assert_any_call(
        "[cyan]Case #[/cyan]",
        "[magenta]Title[/magenta]",
        "Category",
        "Status",
        "Filed On",
    )


def test_exit_app(cli, mock_db, mock_console):
    cli.running = True
    cli.exit_app()
    assert cli.running is False
    mock_db.close_all_connections.assert_called_once()
    mock_console.print.assert_called_with(
        "\n[bold blue]Closing JEC System...[/bold blue]"
    )


def test_run_keyboard_interrupt(cli, mock_console):
    with patch.object(cli, "current_menu", side_effect=KeyboardInterrupt):
        cli.run()
        mock_console.print.assert_called_with(
            "\n[bold blue]Closing JEC System...[/bold blue]"
        )


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
