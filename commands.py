# commands.py (updated)
import logging
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import box
from database import db_manager
import auth

console = Console()


class CommandContext:
    def __init__(self):
        self.running = True
        self.current_user = None
        self.current_menu = "main"

    def refresh_user(self):
        """Update user data from auth system"""
        from auth import auth_manager

        self.current_user = auth_manager.get_current_user()


class BaseCommand:
    """Base class with common utilities"""

    @staticmethod
    def display_header(title: str):
        console.print(f"\n[bold blue]JEC System - {title}[/bold blue]")
        console.print("=" * 50)

    @staticmethod
    def build_table(*columns) -> Table:
        table = Table(box=box.ROUNDED)
        for col in columns:
            table.add_column(col[0], style=col[1])
        return table


class LoginCommand(BaseCommand):
    def execute(self, context):
        email = Prompt.ask("Email")
        password = Prompt.ask("Password", password=True)

        if auth.auth_manager.login(email, password):
            context.current_user = auth.auth_manager.get_current_user()
            console.print("\n[bold green]Login successful![/bold green]")
        else:
            console.print("\n[bold red]Invalid credentials[/bold red]")


class ExitCommand(BaseCommand):
    def execute(self, context):
        context.running = False
        # Add any cleanup logic here if needed
        console.print("\n[bold blue]Closing JEC System...[/bold blue]")


class ListProcessesCommand(BaseCommand):
    def execute(self, context):
        try:
            processes = db_manager.execute_query(
                "SELECT * FROM processos_ativos ORDER BY data_distribuicao DESC",
                return_results=True,
            )

            if not processes:
                console.print("\n[italic]No processes found[/italic]")
                return

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
            logging.error("Process list error: %s", str(e))  # Fixed logging
            console.print("\n[bold red]Error loading processes[/bold red]")


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
                return

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
            logging.error("Search error: %s", str(e))  # Fixed logging
            console.print("\n[bold red]Search failed[/bold red]")


class UserProfileCommand(BaseCommand):
    def execute(self, context):
        user = auth.auth_manager.get_current_user()
        if not user:
            console.print("\n[bold red]Not authenticated[/bold red]")
            return

        table = self.build_table(("Field", "cyan"), ("Value", "magenta"))

        table.add_row("Name", user["nome_completo"])
        table.add_row("Email", user["email"])
        table.add_row("User Type", user["tipo"].capitalize())
        table.add_row("Last Login", str(user["ultimo_login"]))

        console.print(table)

        if Confirm.ask("\nDo you want to change your password?"):
            self.change_password(user)

    def change_password(self, user):
        current_pass = Prompt.ask("Current password", password=True)
        if not auth.auth_manager.verify_password(user["senha"], current_pass):
            console.print("\n[bold red]Incorrect current password[/bold red]")
            return

        new_pass = Prompt.ask("New password", password=True)
        confirm_pass = Prompt.ask("Confirm new password", password=True)

        if new_pass != confirm_pass:
            console.print("\n[bold red]Passwords don't match[/bold red]")
            return

        valid, msg = auth.auth_manager.validate_password_complexity(new_pass)
        if not valid:
            console.print(f"\n[bold red]{msg}[/bold red]")
            return

        try:
            new_hash = auth.auth_manager.hash_password(new_pass)
            db_manager.execute_query(
                "UPDATE usuarios SET senha = %s WHERE id = %s",
                (new_hash, user["id"]),
            )
            console.print("\n[bold green]Password changed successfully![/bold green]")
        except Exception as error:
            logging.error("Password change failed: %s", str(error))
            console.print("\n[bold red]Failed to change password[/bold red]")
