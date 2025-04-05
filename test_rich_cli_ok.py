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
