"""
python -m pytest test_main_ok.py -v -s
"""

import pytest
from unittest.mock import patch, MagicMock, call
from main import JECCLI
from commands import ExitCommand
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
def mock_auth():
    with patch("main.auth_manager") as mock:
        yield mock


@pytest.fixture
def mock_db():
    with patch("main.db_manager") as mock:
        yield mock


@pytest.fixture
def mock_commands():
    with patch("main.LoginCommand"), patch("main.ListProcessesCommand"), patch(
        "main.SearchCasesCommand"
    ), patch("main.UserProfileCommand"), patch("main.ExitCommand"):
        yield


def test_display_header(cli, mock_console_print):
    cli.display_header("Test Title")
    mock_console_print.assert_any_call(
        "\n[bold blue]JEC System - Test Title[/bold blue]"
    )
    mock_console_print.assert_any_call("=" * 50)


def test_clear_screen(cli, mock_console_print):
    cli.clear_screen()
    mock_console_print.assert_called_with("\n" * 100)


def test_press_enter_to_continue(cli, mock_prompt_ask):
    cli.press_enter_to_continue()
    mock_prompt_ask.assert_called_once_with("\n[dim]Press Enter to continue...[/dim]")


def test_main_menu_unauthenticated(cli, mock_prompt_ask, mock_auth, mock_commands):
    mock_auth.get_current_user.return_value = None

    # Create a completely mock command
    mock_command = MagicMock()
    mock_command.execute.return_value = None

    # Replace the real command with our mock
    with patch("main.LoginCommand", return_value=mock_command):
        # Simulate selecting option 1
        mock_prompt_ask.return_value = "1"

        with patch("main.console.print"):
            cli.main_menu()

        mock_command.execute.assert_called_once()


def test_main_menu_authenticated(cli, mock_prompt_ask, mock_auth, mock_commands):
    mock_auth.get_current_user.return_value = {"name": "Test User"}

    # Create a completely mock command
    mock_command = MagicMock()
    mock_command.execute.return_value = None

    # Replace the real command with our mock
    with patch("main.ListProcessesCommand", return_value=mock_command):
        # Simulate selecting option 1
        mock_prompt_ask.return_value = "1"

        with patch("main.console.print"):
            cli.main_menu()

        mock_command.execute.assert_called_once()


def test_main_menu_exit(cli, mock_prompt_ask, mock_auth, mock_commands):
    mock_auth.get_current_user.return_value = None

    # Create a mock exit command that sets running to False
    mock_exit = MagicMock()

    def exit_effect(context):
        context.running = False

    mock_exit.execute.side_effect = exit_effect

    with patch("main.ExitCommand", return_value=mock_exit):
        mock_prompt_ask.return_value = "5"

        with patch("main.console.print"):
            cli.main_menu()

        assert cli.running is False


def test_run_loop(cli, mock_commands):
    # Create a completely separate function that will replace current_menu
    # We want to control exactly what happens in the loop
    call_count = 0

    def mock_menu_function():
        nonlocal call_count
        call_count += 1
        # After 3 calls, set running to False to exit the loop
        if call_count >= 3:
            cli.running = False

    # Replace the current_menu attribute entirely
    # This way, cli.run() will call our mock function instead of main_menu
    cli.current_menu = mock_menu_function

    # Run the application loop
    with patch("main.console.print"):  # Just suppress output
        cli.running = True
        cli.run()

    # Verify our mock was called the expected number of times
    assert call_count == 3


def test_run_keyboard_interrupt(cli, mock_db, mock_console_print, mock_commands):
    # Create a simple function that raises KeyboardInterrupt immediately
    def interrupt_function():
        raise KeyboardInterrupt()

    # Replace current_menu directly
    cli.current_menu = interrupt_function

    # Run the application, which should catch our KeyboardInterrupt and call exit_app
    cli.run()

    # Verify exit behavior was triggered
    mock_console_print.assert_called_with(
        "\n[bold blue]Closing JEC System...[/bold blue]"
    )
    mock_db.close_all_connections.assert_called_once()


def test_run_unexpected_error(cli, mock_console_print, mock_prompt_ask, mock_commands):
    test_error = Exception("Test error")

    # Mock press_enter_to_continue to prevent interactive blocking
    mock_prompt_ask.return_value = ""

    # Custom function to simulate an error and exit immediately
    def error_function():
        raise test_error

    cli.current_menu = error_function

    with patch("main.logging.error") as mock_logging:
        cli.run()

        # Ensure the error was logged
        mock_logging.assert_called_with("Unexpected error: %s", str(test_error))

        # Ensure the console printed the error message
        mock_console_print.assert_any_call(
            "\n[bold red]An unexpected error occurred[/bold red]"
        )

        # Ensure the loop exits after an error
        assert cli.running is False


def test_exit_app(cli, mock_db, mock_console_print):
    cli.exit_app()
    assert cli.running is False
    mock_db.close_all_connections.assert_called_once()
    mock_console_print.assert_called_with(
        "\n[bold blue]Closing JEC System...[/bold blue]"
    )
