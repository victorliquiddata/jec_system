# test_rich_cli.py
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import io
import sys

from rich_cli import JECCLI, cli
from config import AppConfig


class TestJECCLI:
    """Test suite for JECCLI class"""

    def setup_method(self):
        """Set up test environment before each test"""
        # Reset singleton instance for each test
        with patch("config.AppConfig.load_theme", return_value="dark"):
            self.cli = JECCLI()

    def test_initialization(self):
        """Test proper initialization of JECCLI instance"""
        assert self.cli.console is not None
        assert self.cli.theme in ["dark", "light"]
        assert self.cli.user_context is None
        assert "database" in self.cli.system_status
        assert "auth" in self.cli.system_status
        assert "last_update" in self.cli.system_status

    @patch("config.AppConfig.load_theme", return_value="invalid_theme")
    def test_invalid_theme_defaults_to_dark(self, mock_load_theme):
        """Test that invalid theme defaults to dark theme"""
        test_cli = JECCLI()
        assert test_cli.theme == "dark"

    def test_apply_theme(self):
        """Test theme application for different elements"""
        # Test dark theme (default)
        self.cli.theme = "dark"
        assert self.cli._apply_theme("header")["color"] == "#E0E0E0"
        assert self.cli._apply_theme("status")["success"] == "#66BB6A"

        # Test light theme
        self.cli.theme = "light"
        assert self.cli._apply_theme("header")["color"] == "#333333"
        assert self.cli._apply_theme("status")["success"] == "#4CAF50"

    @patch("rich.console.Console.print")
    def test_display_header(self, mock_print):
        """Test header display with default and custom title"""
        # Test default title
        self.cli.display_header()
        mock_print.assert_called()

        # Test custom title
        self.cli.display_header("Custom Title")
        assert mock_print.call_count == 2

    @patch("rich.console.Console.print")
    def test_display_main_menu(self, mock_print):
        """Test main menu display with options"""
        options = [{"description": "Option 1"}, {"description": "Option 2"}]
        self.cli.display_main_menu(options)
        mock_print.assert_called()

    @patch("rich.console.Console.print")
    def test_display_status(self, mock_print):
        """Test status display with different levels"""
        for level in ["success", "warning", "error", "info"]:
            self.cli.display_status(f"Test {level} message", level)
        assert mock_print.call_count == 4

    @patch("rich.prompt.Prompt.ask", return_value="test_input")
    def test_prompt_input_string(self, mock_ask):
        """Test string input prompt"""
        result = self.cli.prompt_input("Test prompt")
        assert result == "test_input"
        mock_ask.assert_called_once()

    @patch("rich.prompt.Prompt.ask", return_value="42")
    def test_prompt_input_int(self, mock_ask):
        """Test integer input prompt"""
        result = self.cli.prompt_input("Test prompt", int)
        assert result == 42
        mock_ask.assert_called_once()

    @patch("rich.prompt.Prompt.ask", side_effect=["invalid", "42"])
    @patch("rich_cli.JECCLI.display_status")
    def test_prompt_input_validation(self, mock_display, mock_ask):
        """Test input validation with invalid then valid input"""
        result = self.cli.prompt_input("Test prompt", int)
        assert result == 42
        assert mock_ask.call_count == 2
        mock_display.assert_called_once()

    @patch("rich.console.Console.print")
    def test_display_data_table_with_data(self, mock_print):
        """Test data table display with sample data"""
        data = [{"id": 1, "name": "Test1"}, {"id": 2, "name": "Test2"}]
        self.cli.display_data_table(data, "Test Table")
        mock_print.assert_called_once()

    @patch("rich.console.Console.print")
    @patch("rich_cli.JECCLI.display_status")
    def test_display_data_table_empty(self, mock_display, mock_print):
        """Test data table display with empty data"""
        self.cli.display_data_table([], "Empty Table")
        mock_display.assert_called_once_with("Nenhum dado encontrado.", "warning")

    @patch("rich.console.Console.print")
    def test_update_footer_no_user(self, mock_print):
        """Test footer update with no user context"""
        self.cli.update_footer()
        mock_print.assert_called_once()

    @patch("rich.console.Console.print")
    def test_update_footer_with_user(self, mock_print):
        """Test footer update with user context"""
        self.cli.user_context = {"email": "test@example.com"}
        self.cli.update_footer()
        mock_print.assert_called_once()

    @patch("rich.console.Console.clear")
    def test_clear_screen(self, mock_clear):
        """Test screen clearing functionality"""
        self.cli.clear_screen()
        mock_clear.assert_called_once()

    def test_singleton_instance(self):
        """Test that cli is a singleton instance of JECCLI"""
        assert isinstance(cli, JECCLI)
        # Test modifying singleton affects future access
        cli.theme = "light"
        with patch("config.AppConfig.load_theme", return_value="dark"):
            new_ref = JECCLI()
            assert new_ref.theme == "light"


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main(["-v", __file__]))
