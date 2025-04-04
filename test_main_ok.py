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
