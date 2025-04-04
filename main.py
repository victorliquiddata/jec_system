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
        self.commands = {}  # Will be initialized in main_menu
        self.running = True
        self.current_menu = self.main_menu

    def display_header(self, title: str):
        """Display consistent header for all screens"""
        console.print(f"\n[bold blue]JEC System - {title}[/bold blue]")
        console.print("=" * 50)

    def clear_screen(self):
        """Clear terminal screen"""
        console.print("\n" * 100)  # Simple clear for cross-platform

    def main_menu(self):
        self.clear_screen()
        self.display_header("Main Menu")

        user = auth_manager.get_current_user()
        if not user:
            self.commands = {
                "1": ("Login", LoginCommand()),
                "2": ("List Processes", ListProcessesCommand()),
                "3": ("Search Cases", SearchCasesCommand()),
                "4": ("Profile", UserProfileCommand()),
                "5": ("Exit", ExitCommand()),
            }
        else:
            self.commands = {
                "1": ("List Processes", ListProcessesCommand()),
                "2": ("Search Cases", SearchCasesCommand()),
                "3": ("Profile", UserProfileCommand()),
                "4": ("Logout", LoginCommand()),
                "5": ("Exit", ExitCommand()),
            }

        for key, (desc, _) in self.commands.items():
            console.print(f"[green]{key}[/green]. {desc}")

        choice = Prompt.ask("\nSelect an option", choices=list(self.commands.keys()))

        # Execute command
        self.commands[choice][1].execute(self.context)

        # Sync the running state between context and CLI
        self.running = self.context.running

        # Only show continue prompt if not exiting
        if self.running:
            self.press_enter_to_continue()

    def press_enter_to_continue(self):
        """Utility method for consistent pause"""
        Prompt.ask("\n[dim]Press Enter to continue...[/dim]")

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
                self.exit_app()


if __name__ == "__main__":
    try:
        cli = JECCLI()
        cli.run()
    except Exception as error:
        logging.critical("Application crash: %s", str(error))
        console.print("\n[bold red]Fatal error - application terminated[/bold red]")
        db_manager.close_all_connections()
