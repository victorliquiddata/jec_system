"""
run by using:
python -m pytest test_commands2.py -v -s
"""

import pytest
from unittest.mock import patch, MagicMock
from commands import (
    BaseCommand,
    LoginCommand,
    ExitCommand,
    ListProcessesCommand,
    SearchCasesCommand,
    UserProfileCommand,
    CommandContext,
)
from database import db_manager
from rich.table import Table
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))


@pytest.fixture
def mock_db():
    with patch("commands.db_manager") as mock:
        yield mock


@pytest.fixture
def mock_prompt():
    with patch("commands.Prompt.ask", return_value=""):
        yield


@pytest.fixture
def mock_auth():
    with patch("auth.auth_manager") as mock:  # Corrected path
        yield mock


@pytest.fixture
def mock_cli():
    with patch("main.JECCLI") as mock:
        yield mock


# --- BaseCommand Tests ---
def test_base_command_utilities():
    cmd = BaseCommand()
    with patch("commands.console.print") as mock_print:
        cmd.display_header("Test")
        mock_print.assert_any_call("\n[bold blue]JEC System - Test[/bold blue]")

    with patch("commands.Prompt.ask") as mock_ask:
        cmd.press_enter_to_continue()
        mock_ask.assert_called_once()

    table = cmd.build_table(("Test", "red"))
    assert len(table.columns) == 1


# --- ListProcessesCommand Tests ---
def test_list_processes_success(mock_db, mock_prompt):  # Added mock_prompt
    test_data = [
        {
            "numero_processo": "123",
            "titulo": "Test Case",
            "categoria": "Civil",
            "status": "Active",
            "data_distribuicao": "2023-01-01",
        }
    ]
    mock_db.execute_query.return_value = test_data

    cmd = ListProcessesCommand()
    context = CommandContext()

    with patch("commands.console.print") as mock_print:
        cmd.execute(context)
        assert any(isinstance(args[0], Table) for args, _ in mock_print.call_args_list)


def test_list_processes_empty(mock_db, mock_prompt):  # Added mock_prompt
    mock_db.execute_query.return_value = []

    cmd = ListProcessesCommand()

    with patch("commands.console.print") as mock_print:
        cmd.execute(CommandContext())
        mock_print.assert_any_call("\n[italic]No processes found[/italic]")


# --- LoginCommand Tests ---
def test_login_success(mock_auth, mock_prompt):
    mock_auth.login.return_value = True
    mock_auth.get_current_user.return_value = {"name": "Test User"}

    cmd = LoginCommand()
    context = CommandContext()

    with patch("commands.Prompt.ask", side_effect=["test@test.com", "password", ""]):
        cmd.execute(context)

    mock_auth.login.assert_called_with("test@test.com", "password")
    assert context.current_user == {"name": "Test User"}


def test_login_failure(mock_auth, mock_prompt):
    mock_auth.login.return_value = False
    mock_auth.get_current_user.return_value = None  # Explicitly set

    cmd = LoginCommand()
    context = CommandContext()

    with patch("commands.Prompt.ask", side_effect=["bad@test.com", "wrongpass", ""]):
        with patch("commands.console.print") as mock_print:
            cmd.execute(context)

            # Verify error message
            mock_print.assert_any_call("\n[bold red]Invalid credentials[/bold red]")
            # Verify user remains unset
            assert context.current_user is None


# --- SearchCasesCommand Tests ---
def test_search_cases(mock_db):
    test_data = [
        {
            "numero_processo": "456",
            "titulo": "Search Test",
            "status": "Pending",
            "data_distribuicao": "2023-02-01",
        }
    ]
    mock_db.execute_query.return_value = test_data

    cmd = SearchCasesCommand()

    with patch("commands.Prompt.ask", return_value="test"):
        cmd.execute(CommandContext())

        # Get actual query and normalize whitespace
        called_args, _ = mock_db.execute_query.call_args
        actual_query = " ".join(called_args[0].split())

        # Define expected query pattern
        expected = (
            "SELECT p.* FROM processos p LEFT JOIN partes_processo pp ON p.id = pp.processo_id "
            "LEFT JOIN partes pa ON pp.parte_id = pa.id WHERE p.numero_processo ILIKE %s "
            "OR p.titulo ILIKE %s OR pa.nome ILIKE %s ORDER BY p.data_distribuicao DESC"
        )
        assert actual_query == expected


# --- CommandContext Tests ---
def test_command_context_refresh():
    with patch("auth.auth_manager") as mock_auth:
        test_user = {"name": "Test User"}
        mock_auth.get_current_user.return_value = test_user

        context = CommandContext()
        context.refresh_user()

        assert context.current_user == test_user
