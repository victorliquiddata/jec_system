# rich_cli.py (versão corrigida)
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.align import Align
from rich.prompt import Prompt
from datetime import datetime
from typing import Dict, List, Optional, Union
from config import AppConfig


class JECCLI:
    """Interface de usuário unificada para o Sistema JEC usando Rich"""

    def __init__(self):
        self.console = Console(width=80, highlight=False)
        self.theme = AppConfig.load_theme()

        # Garante que o tema carregado seja válido
        if self.theme not in ["dark", "light"]:
            self.theme = "dark"  # Tema padrão

        self.user_context: Optional[Dict[str, Union[str, Dict]]] = None

        self.system_status: Dict[str, str] = {
            "database": "offline",
            "auth": "inactive",
            "last_update": datetime.now().isoformat(),
        }

    def _apply_theme(self, element_type: str) -> Dict[str, str]:
        """Aplica esquema de cores baseado no tema atual"""
        themes = {
            "dark": {
                "header": {"color": "#E0E0E0", "border": "#7A7A7A"},
                "body": {"primary": "#BDBDBD", "secondary": "#7A7A7A"},
                "status": {
                    "success": "#66BB6A",
                    "warning": "#E6A23C",
                    "error": "#D32F2F",
                    "info": "#2196F3",
                },
            },
            "light": {
                "header": {"color": "#333333", "border": "#AAAAAA"},
                "body": {"primary": "#000000", "secondary": "#666666"},
                "status": {
                    "success": "#4CAF50",
                    "warning": "#FFC107",
                    "error": "#F44336",
                    "info": "#2196F3",
                },
            },
        }
        return themes.get(self.theme, themes["dark"])[element_type]

    def display_header(self, title: str = "Sistema JEC"):
        """Renderiza o cabeçalho da aplicação"""
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

    def display_main_menu(self, options: List[Dict[str, str]]):
        """Exibe menu principal numerado"""
        menu_table = Table(show_header=False, box=None, expand=True)
        menu_table.add_column(
            "Opção", style=self._apply_theme("body")["primary"], width=6
        )
        menu_table.add_column("Descrição", style=self._apply_theme("body")["secondary"])

        for idx, option in enumerate(options, 1):
            menu_table.add_row(
                Text(f"{idx}", style="bold"), Text(option["description"])
            )

        self.console.print("\n")
        self.console.print(
            Panel(
                menu_table,
                title="[bold]Menu Principal[/]",
                border_style=self._apply_theme("header")["border"],
            )
        )

    def display_status(self, message: str, level: str = "info"):
        """Exibe mensagens de status formatadas"""
        icons = {"success": "✔", "warning": "⚠", "error": "❌", "info": "ℹ️"}
        self.console.print(
            f"{icons[level]} [{self._apply_theme('status')[level]}]{message}[/]",
            style=self._apply_theme("body")["primary"],
        )

    def prompt_input(self, label: str, input_type: type = str) -> str:
        """Solicita entrada do usuário com validação de tipo"""
        while True:
            try:
                value = Prompt.ask(f"[bold]{label}[/]", console=self.console)
                return input_type(value)
            except ValueError:
                self.display_status(
                    f"Entrada inválida. Esperado tipo {input_type.__name__}.", "warning"
                )

    def display_data_table(self, data: List[Dict], title: str = "Resultados"):
        """Exibe dados em formato tabular"""
        table = Table(
            title=f"[bold]{title}[/]",
            box=None,
            show_header=True,
            header_style=f"bold {self._apply_theme('body')['primary']}",
        )

        if data:
            for key in data[0].keys():
                table.add_column(key.capitalize())

            for item in data:
                table.add_row(*[str(v) for v in item.values()])

            self.console.print(table)
        else:
            self.display_status("Nenhum dado encontrado.", "warning")

    def update_footer(self):
        """Atualiza e exibe o rodapé dinâmico"""
        user_email = (
            self.user_context.get("email", "N/A")
            if self.user_context and isinstance(self.user_context, dict)
            else "Não autenticado"
        )

        footer_elements = [
            f"Usuário: {user_email}",
            f"Status DB: {self.system_status.get('database', 'unknown')}",
            f"Atualizado: {datetime.now().strftime('%H:%M:%S')}",
        ]

        footer_text = Text("   |   ".join(footer_elements), style="italic #7A7A7A")
        self.console.print(
            Panel(
                Align.center(footer_text),
                border_style=self._apply_theme("header")["border"],
                padding=(0, 2),
                expand=False,
            )
        )

    def clear_screen(self):
        """Limpa a tela do console"""
        self.console.clear()


# Singleton para uso global
cli = JECCLI()
