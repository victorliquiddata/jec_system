# commands.py >> versao 4
# commands.py (versão corrigida)
import logging
from typing import Optional, Dict, List
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich import box
from database import db_manager

console = Console()


class CommandContext:
    """Container para compartilhar estado entre comandos"""

    def __init__(self):
        self.current_menu = None
        self.running = True


class BaseCommand:
    def execute(self, context):
        """Método abstrato - deve ser implementado por subclasses"""
        raise TypeError(
            "Método execute() deve ser implementado por subclasses"
        )  # Alterado para TypeError

    @staticmethod
    def press_enter_to_continue(context):
        """Versão testável do método"""
        try:
            Prompt.ask("\n[dim]Press Enter to continue...[/dim]")
        except Exception:  # Captura erro durante testes
            pass
        finally:
            context.current_menu = "main_menu"


class ListProcessesCommand(BaseCommand):
    def execute(self, context):
        try:
            processes = db_manager.execute_query(
                "SELECT * FROM processos_ativos ORDER BY data_distribuicao DESC",
                return_results=True,
            )

            if not processes:
                console.print(
                    "\n[italic]No processes found[/italic]"
                )  # Garantir que esta linha existe
                return self.press_enter_to_continue(context)

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
            self.press_enter_to_continue(context)
