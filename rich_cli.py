import traceback
from datetime import datetime
from typing import Dict, List, Optional
from time import perf_counter
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.prompt import Prompt
from config import AppConfig, Theme
from logger import JCELogger


class JECCLI:
    """Enhanced Rich CLI with comprehensive logging integration"""

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.console = Console(width=80, highlight=False)
        self.logger = JCELogger()
        self.theme = AppConfig.load_theme()
        self.user_context = None
        self.system_status = {
            "database": "offline",
            "auth": "inactive",
            "last_update": datetime.now().isoformat(),
        }
        self._current_context = {}  # Initialize context storage
        self._initialized = True
        self.logger.log_interface(
            "CLI",
            "initialized",
            metadata={"theme": self.theme, "config_version": AppConfig.VERSION},
        )

    def _apply_theme(self, element_type: str) -> Dict[str, str]:
        """Theme application with fallback"""
        try:
            return AppConfig.THEMES[self.theme][element_type]
        except KeyError:
            self.logger.log_interface(
                "Theme",
                "fallback_used",
                level="warning",
                metadata={
                    "requested_element": element_type,
                    "available_themes": list(AppConfig.THEMES.keys()),
                },
            )
            return AppConfig.THEMES[Theme.ESCURO][element_type]

    def display_header(self, title: str = "Sistema JEC") -> None:
        """Render application header with logging"""
        try:
            start_time = perf_counter()
            header_text = Text(
                f"⚖️  {title}", style=f"bold {self._apply_theme('header')['color']}"
            )

            self.console.print(
                Panel(
                    Align.center(header_text),
                    border_style=self._apply_theme("header")["border"],
                    padding=(1, 2),
                    title=f"v{AppConfig.VERSION}",
                    title_align="right",
                )
            )

            self.logger.log_interface(
                "Header",
                "displayed",
                metadata={
                    "title": title,
                    "render_time": f"{perf_counter() - start_time:.3f}s",
                },
            )
        except Exception as e:
            self._log_ui_error("header_render", e)

    def display_main_menu(self, options: List[Dict[str, str]]) -> None:
        """Show numbered menu with full interaction logging"""
        try:
            start_time = perf_counter()
            menu_table = Table(show_header=False, box=None, expand=True)
            menu_table.add_column(
                "Option", style=self._apply_theme("body")["primary"], width=6
            )
            menu_table.add_column(
                "Description", style=self._apply_theme("body")["secondary"]
            )

            for idx, option in enumerate(options, 1):
                menu_table.add_row(
                    Text(f"{idx}", style="bold"), Text(option["description"])
                )

            self.console.print("\n")
            self.console.print(
                Panel(
                    menu_table,
                    title="[bold]Main Menu[/]",
                    border_style=self._apply_theme("header")["border"],
                )
            )

            self.logger.log_interface(
                "Menu",
                "displayed",
                user_ctx=self.user_context,
                metadata={
                    "options_count": len(options),
                    "render_time": f"{perf_counter() - start_time:.3f}s",
                },
            )
        except Exception as e:
            self._log_ui_error("menu_render", e)

    def display_status(self, message: str, level: str = "info"):
        """Exibe mensagens de status formatadas"""
        icons = {"success": "✔", "warning": "⚠", "error": "❌", "info": "ℹ️"}
        self.console.print(
            f"{icons[level]} [{self._apply_theme('status')[level]}]{message}[/]",
            style=self._apply_theme("body")["primary"],
        )

    def prompt_input(
        self, label: str, input_type: type = str, password: bool = False
    ) -> str:
        """Get user input with type validation and logging"""
        attempt = 0
        max_attempts = 3

        while attempt < max_attempts:
            try:
                attempt += 1
                if password:
                    value = Prompt.ask(
                        f"[bold]{label}[/]", console=self.console, password=True
                    )
                else:
                    value = Prompt.ask(f"[bold]{label}[/]", console=self.console)

                self.logger.log_interface(
                    "Input",
                    "received",
                    user_ctx=self.user_context,
                    metadata={
                        "label": label,
                        "attempt": attempt,
                        "raw_value": value,
                        "expected_type": input_type.__name__,
                    },
                )

                converted = input_type(value)

                self.logger.log_interface(
                    "Input",
                    "validated",
                    metadata={"converted_value": str(converted), "success": True},
                )

                return converted

            except ValueError:
                self.display_status(
                    f"Invalid input. Expected {input_type.__name__}.", "warning"
                )
                self.logger.log_interface(
                    "Input",
                    "validation_failed",
                    level="warning",
                    metadata={"attempt": attempt, "max_attempts": max_attempts},
                )

        raise ValueError(f"Failed after {max_attempts} attempts")

    def display_data_table(
        self, data: List[Dict], title: str, metadata: Optional[Dict] = None
    ) -> None:
        """Display tabular data with optional metadata"""
        try:
            # Ensure context exists
            if not hasattr(self, "_current_context"):
                self._current_context = {}

            # Store metadata in context
            if metadata:
                self._current_context["metadata"] = metadata
                self.logger.log_interface(
                    "Table", "metadata_updated", metadata=metadata
                )

            start_time = perf_counter()
            table = Table(
                title=f"[bold]{title}[/]",
                box=None,
                show_header=True,
                header_style=f"bold {self._apply_theme('body')['primary']}",
            )

            if data and len(data) > 0:
                # Process columns
                columns = list(data[0].keys())
                for col in columns:
                    table.add_column(col.capitalize())

                # Process rows
                rendered_rows = 0
                for item in data:
                    row_values = []
                    for key in columns:
                        value = item.get(key, "N/A")
                        if isinstance(value, str) and len(value) > 50:
                            row_values.append(value[:47] + "...")
                        else:
                            row_values.append(str(value))
                    table.add_row(*row_values)
                    rendered_rows += 1

                self.console.print(table)

                # Log successful render
                self.logger.log_interface(
                    "Table",
                    "rendered",
                    user_ctx=self.user_context,
                    metadata={
                        "title": title,
                        "row_count": len(data),
                        "columns": columns,
                        "render_time": f"{perf_counter() - start_time:.3f}s",
                        **self._current_context.get("metadata", {}),
                    },
                )
            else:
                self.display_status("No data available", "warning")
                self.logger.log_interface(
                    "Table",
                    "empty",
                    level="warning",
                    metadata={
                        "title": title,
                        **self._current_context.get("metadata", {}),
                    },
                )

        except Exception as e:
            error_meta = {
                "title": title,
                "data_type": type(data).__name__,
                "data_length": len(data) if data else 0,
                **self._current_context.get("metadata", {}),
            }
            self._log_ui_error("table_render", e, error_meta)

    def _log_ui_error(
        self, operation: str, error: Exception, additional_meta: Optional[Dict] = None
    ) -> None:
        """Standardized error logging for UI operations with optional metadata"""
        error_meta = {
            "operation": operation,
            "error": str(error),
            "type": type(error).__name__,
            "stack": traceback.format_exc(),
        }

        if additional_meta:
            error_meta.update(additional_meta)

        self.logger.log_interface(
            "CLI", "operation_failed", level="error", metadata=error_meta
        )
        self.display_status(f"UI Error: {str(error)}", "error")

    def update_footer(self) -> None:
        """Dynamic footer with system status"""
        try:
            user_email = (
                self.user_context.get("email", "N/A")
                if self.user_context
                else "Not authenticated"
            )

            footer_elements = [
                f"User: {user_email}",
                f"DB Status: {self.system_status.get('database', 'unknown')}",
                f"Updated: {datetime.now().strftime('%H:%M:%S')}",
            ]

            footer_text = Text(" | ".join(footer_elements), style="italic #7A7A7A")
            self.console.print(
                Panel(
                    Align.center(footer_text),
                    border_style=self._apply_theme("header")["border"],
                    padding=(0, 2),
                    expand=False,
                )
            )

            self.logger.log_interface(
                "Footer",
                "updated",
                metadata={
                    "user": user_email,
                    "db_status": self.system_status.get("database"),
                },
            )
        except Exception as e:
            self._log_ui_error("footer_update", e)

    def clear_screen(self):
        """Limpa a tela do console"""
        self.console.clear()


# Singleton para uso global
cli = JECCLI()
