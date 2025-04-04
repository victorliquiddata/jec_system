import logging
from typing import Optional
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich import box
from auth import auth_manager
from database import db_manager
from commands import (
    CommandContext,
    ListProcessesCommand,
    LoginCommand,
    ExitCommand,
    SearchCasesCommand,
    UserProfileCommand,
)

console = Console()


class JECCLI:
    def __init__(self):
        self.context = CommandContext()
        self.commands = {}  # Inicialize vazio
        self.running = True

    def display_header(self, title: str):
        """Display consistent header for all screens"""
        console.print(f"\n[bold blue]JEC System - {title}[/bold blue]")
        console.print("=" * 50)

    def clear_screen(self):
        """Clear terminal screen"""
        console.print("\n" * 100)  # Simple clear for cross-platform

    def main_menu(self):
        """Display main menu based on user role"""
        self.clear_screen()
        self.display_header("Main Menu")

        user = auth_manager.get_current_user()
        if not user:
            # Atualize os comandos para usuários não autenticados
            self.commands = {
                "1": ("Login", LoginCommand()),
                "2": ("List Processes", ListProcessesCommand()),
                "3": ("Search Cases", SearchCasesCommand()),
                "4": ("Profile", UserProfileCommand()),
                "5": ("Exit", ExitCommand()),
            }

        else:
            # Comandos para usuários autenticados (existente)
            pass

        # Renderização do menu (mantenha o resto igual)
        for key, (desc, _) in self.commands.items():
            console.print(f"[green]{key}[/green]. {desc}")

        choice = Prompt.ask("\nSelect an option", choices=list(self.commands.keys()))
        self.commands[choice][1].execute(self.context)

    def login(self):
        """Handle user login"""
        self.clear_screen()
        self.display_header("Login")

        email = Prompt.ask("Email")
        password = Prompt.ask("Password", password=True)

        if auth_manager.login(email, password):
            console.print("\n[bold green]Login successful![/bold green]")
        else:
            console.print("\n[bold red]Invalid credentials[/bold red]")

        self.press_enter_to_continue()

    def logout(self):
        """Handle user logout"""
        auth_manager.logout()
        console.print("\n[bold green]Logged out successfully[/bold green]")
        self.press_enter_to_continue()

    def search_cases(self):
        """Search for legal cases"""
        self.clear_screen()
        self.display_header("Case Search")

        search_term = Prompt.ask("Enter case number, title or party name")

        try:
            results = db_manager.execute_query(
                """SELECT p.* FROM processos p
                LEFT JOIN partes_processo pp ON p.id = pp.processo_id
                LEFT JOIN partes pa ON pp.parte_id = pa.id
                WHERE p.numero_processo ILIKE %s
                OR p.titulo ILIKE %s
                OR pa.nome ILIKE %s
                ORDER BY p.data_distribuicao DESC""",
                (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"),
                return_results=True,
            )

            if not results:
                console.print("\n[italic]No matching cases found[/italic]")
                self.press_enter_to_continue()
                return

            table = Table(box=box.ROUNDED)
            table.add_column("Case #", style="cyan")
            table.add_column("Title", style="magenta")
            table.add_column("Status")
            table.add_column("Filed On")

            for case in results:
                table.add_row(
                    case["numero_processo"],
                    case["titulo"],
                    case["status"],
                    str(case["data_distribuicao"]),
                )

            console.print(table)
        except Exception as error:
            logging.error("Error searching cases: %s", str(error))
            console.print("\n[bold red]Error searching cases[/bold red]")
        finally:
            self.press_enter_to_continue()

    def user_profile(self):
        """Display and manage user profile"""
        self.clear_screen()
        self.display_header("User Profile")

        user = auth_manager.get_current_user()
        if not user:
            console.print("\n[bold red]Not authenticated[/bold red]")
            self.press_enter_to_continue()
            return

        table = Table(box=box.SIMPLE)
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="magenta")

        table.add_row("Name", user["nome_completo"])
        table.add_row("Email", user["email"])
        table.add_row("User Type", user["tipo"].capitalize())
        table.add_row("Last Login", str(user["ultimo_login"]))

        console.print(table)

        if Confirm.ask("\nDo you want to change your password?"):
            self.change_password()
        else:
            self.press_enter_to_continue()

    def change_password(self):
        """Handle password change"""
        current_pass = Prompt.ask("Current password", password=True)
        if not auth_manager.verify_password(
            auth_manager.current_user["senha"], current_pass
        ):
            console.print("\n[bold red]Incorrect current password[/bold red]")
            self.press_enter_to_continue()
            return

        new_pass = Prompt.ask("New password", password=True)
        confirm_pass = Prompt.ask("Confirm new password", password=True)

        if new_pass != confirm_pass:
            console.print("\n[bold red]Passwords don't match[/bold red]")
            self.press_enter_to_continue()
            return

        valid, msg = auth_manager.validate_password_complexity(new_pass)
        if not valid:
            console.print(f"\n[bold red]{msg}[/bold red]")
            self.press_enter_to_continue()
            return

        try:
            new_hash = auth_manager.hash_password(new_pass)
            db_manager.execute_query(
                "UPDATE usuarios SET senha = %s WHERE id = %s",
                (new_hash, auth_manager.current_user["id"]),
            )
            console.print("\n[bold green]Password changed successfully![/bold green]")
        except Exception as error:
            logging.error("Password change failed: %s", str(error))
            console.print("\n[bold red]Failed to change password[/bold red]")

        self.press_enter_to_continue()

    def user_management(self):
        """Admin interface for user management"""
        if auth_manager.get_current_user()["tipo"] != "admin":
            console.print("\n[bold red]Unauthorized access[/bold red]")
            self.press_enter_to_continue()
            return

        self.clear_screen()
        self.display_header("User Management")

        try:
            users = db_manager.execute_query(
                "SELECT id, nome_completo, email, tipo, data_cadastro FROM usuarios",
                return_results=True,
            )

            table = Table(box=box.ROUNDED)
            table.add_column("ID", style="dim")
            table.add_column("Name", style="cyan")
            table.add_column("Email")
            table.add_column("Type")
            table.add_column("Registered On")

            for user in users:
                table.add_row(
                    str(user["id"]),
                    user["nome_completo"],
                    user["email"],
                    user["tipo"].capitalize(),
                    str(user["data_cadastro"]),
                )

            console.print(table)
        except Exception as error:
            logging.error("Error fetching users: %s", str(error))
            console.print("\n[bold red]Error loading users[/bold red]")
        finally:
            self.press_enter_to_continue()

    def list_processes(self):
        """List legal processes"""
        self.clear_screen()
        self.display_header("Active Processes")

        try:
            processes = db_manager.execute_query(
                "SELECT * FROM processos_ativos ORDER BY data_distribuicao DESC",
                return_results=True,
            )

            if not processes:
                console.print("\n[italic]No processes found[/italic]")
                self.press_enter_to_continue()
                return

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
            self.press_enter_to_continue()

    def press_enter_to_continue(self):
        """Utility method for consistent pause"""
        Prompt.ask("\n[dim]Press Enter to continue...[/dim]")
        self.current_menu = self.main_menu

    def exit_app(self):
        """Cleanly exit application"""
        console.print("\n[bold blue]Closing JEC System...[/bold blue]")
        db_manager.close_all_connections()
        self.running = False

    def run(self):
        """Main application loop"""
        while self.running:
            try:
                self.current_menu()
            except KeyboardInterrupt:
                self.exit_app()
            except Exception as error:
                logging.error("Unexpected error: %s", str(error))
                console.print("\n[bold red]An unexpected error occurred[/bold red]")
                self.press_enter_to_continue()


if __name__ == "__main__":
    try:
        cli = JECCLI()
        cli.run()
    except Exception as error:
        logging.critical("Application crash: %s", str(error))
        console.print("\n[bold red]Fatal error - application terminated[/bold red]")
        db_manager.close_all_connections()
