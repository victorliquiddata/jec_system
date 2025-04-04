import pytest
from unittest.mock import patch, MagicMock, call
from commands import ListProcessesCommand, BaseCommand
from database import db_manager
import sys
from pathlib import Path

# Fix imports
sys.path.append(str(Path(__file__).parent.parent))


class TestBaseCommand(BaseCommand):
    """Implementação concreta para testar BaseCommand"""

    def execute(self, context):
        pass


@pytest.fixture
def mock_db():
    with patch("commands.db_manager") as mock:
        yield mock


@pytest.fixture
def mock_prompt():
    with patch("commands.Prompt.ask", return_value=""):
        yield


def test_base_command_abstract():
    """Testa se BaseCommand é abstrata"""
    with pytest.raises(TypeError):  # Agora esperando TypeError
        BaseCommand().execute(MagicMock())

    # Teste com implementação concreta
    TestBaseCommand().execute(MagicMock())  # Não deve levantar exceção


def test_list_processes_command(mock_db, mock_prompt):
    context = MagicMock()
    cmd = ListProcessesCommand()

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

    cmd.execute(context)

    mock_db.execute_query.assert_called_once()
    assert context.current_menu == "main_menu"


def test_list_processes_empty(mock_db, mock_prompt):
    context = MagicMock()
    cmd = ListProcessesCommand()
    mock_db.execute_query.return_value = []

    # Mock específico para console.print
    with patch("commands.console.print") as mock_print:
        cmd.execute(context)
        # Verifica se a mensagem foi impressa
        mock_print.assert_any_call("\n[italic]No processes found[/italic]")


def test_list_processes_error(mock_db, mock_prompt):
    context = MagicMock()
    cmd = ListProcessesCommand()
    mock_db.execute_query.side_effect = Exception("DB Error")

    with patch("commands.console.print") as mock_print:
        cmd.execute(context)
        mock_print.assert_called_with("\n[bold red]Error loading processes[/bold red]")
