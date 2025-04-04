# commands.py >> versao 6
# commands.py (versão corrigida)
import logging
from typing import Optional, Dict, List
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import box
from database import db_manager
import auth


console = Console()


# At top of commands.py


class CommandContext:
    def __init__(self):
        self.running = True
        self.current_user = None  # Populated after login
        self.current_menu = "main"

    def refresh_user(self):
        """Update user data from auth system"""
        from auth import auth_manager  # Lazy import

        self.current_user = auth_manager.get_current_user()


class BaseCommand:
    """Enhanced base class with common utilities"""

    @staticmethod
    def display_header(title: str):
        """Reusable header display"""
        console.print(f"\n[bold blue]JEC System - {title}[/bold blue]")
        console.print("=" * 50)

    @staticmethod
    def press_enter_to_continue():
        """Standard pause method"""
        Prompt.ask("\n[dim]Press Enter to continue...[/dim]")

    @staticmethod
    def build_table(*columns) -> Table:
        """Helper for creating consistent tables"""
        table = Table(box=box.ROUNDED)
        for col in columns:
            table.add_column(col[0], style=col[1])
        return table


class LoginCommand(BaseCommand):
    def execute(self, context):
        email = Prompt.ask("Email")
        password = Prompt.ask("Password", password=True)

        if auth.auth_manager.login(email, password):  # Access through module
            context.current_user = auth.auth_manager.get_current_user()
            console.print("\n[bold green]Login successful![/bold green]")
        else:
            console.print("\n[bold red]Invalid credentials[/bold red]")

        self.press_enter_to_continue()


class ExitCommand(BaseCommand):
    def execute(self, context):
        context.running = False


class ListProcessesCommand(BaseCommand):
    def execute(self, context):
        try:
            processes = db_manager.execute_query(
                "SELECT * FROM processos_ativos ORDER BY data_distribuicao DESC",
                return_results=True,
            )

            if not processes:
                console.print("\n[italic]No processes found[/italic]")
                return self.press_enter_to_continue()

            table = self.build_table(
                ("Case #", "cyan"),
                ("Title", "magenta"),
                ("Category", ""),
                ("Status", ""),
                ("Filed On", ""),
            )

            for p in processes:
                table.add_row(
                    p["numero_processo"],
                    p["titulo"],
                    p["categoria"],
                    p["status"],
                    str(p["data_distribuicao"]),
                )

            console.print(table)
        except Exception as e:
            logging.error("Process list error: {str(e)}")
            console.print("\n[bold red]Error loading processes[/bold red]")
        finally:
            self.press_enter_to_continue()


class SearchCasesCommand(BaseCommand):
    def execute(self, context):
        self.display_header("Case Search")
        term = Prompt.ask("Enter case number/title/party")

        try:
            results = db_manager.execute_query(
                """SELECT p.* FROM processos p
                LEFT JOIN partes_processo pp ON p.id = pp.processo_id
                LEFT JOIN partes pa ON pp.parte_id = pa.id
                WHERE p.numero_processo ILIKE %s OR p.titulo ILIKE %s OR pa.nome ILIKE %s
                ORDER BY p.data_distribuicao DESC""",
                (f"%{term}%", f"%{term}%", f"%{term}%"),
                return_results=True,
            )

            if not results:
                console.print("\n[italic]No matches found[/italic]")
                return self.press_enter_to_continue()

            table = self.build_table(
                ("Case #", "cyan"), ("Title", "magenta"), ("Status", ""), ("Filed", "")
            )

            for case in results:
                table.add_row(
                    case["numero_processo"],
                    case["titulo"],
                    case["status"],
                    str(case["data_distribuicao"]),
                )

            console.print(table)
        except Exception as e:
            logging.error("Search error: {str(e)}")
            console.print("\n[bold red]Search failed[/bold red]")
        finally:
            self.press_enter_to_continue()


class UserProfileCommand(BaseCommand):
    def execute(self, context):
        from main import JECCLI  # Lazy import for shared methods

        JECCLI().user_profile()  # Reuse existing UI flow
