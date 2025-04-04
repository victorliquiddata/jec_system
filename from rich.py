from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.columns import Columns
from rich.box import ROUNDED, DOUBLE, HEAVY
from rich.layout import Layout
from rich.text import Text
from rich.align import Align
from rich.style import Style
from time import sleep
from datetime import datetime
import random
from typing import Dict, List, Optional, Any


class RichDashboard:
    def __init__(
        self,
        title: str = "🚀 Ultimate Rich CLI Dashboard",
        theme: Dict[str, str] = None,
    ):
        self.console = Console()
        self.title = title
        self.theme = theme or {
            # Primary colors
            "primary": "steel_blue",  # Softer than cyan
            "secondary": "dark_sea_green",  # Muted green
            # Status colors
            "success": "sea_green3",  # Soft green
            "error": "indian_red",  # Muted red
            "warning": "light_goldenrod2",  # Soft yellow
            "info": "sky_blue3",  # Muted blue
            "highlight": "medium_orchid",  # Soft purple
            # Neutral colors
            "neutral": "grey62",
            "border": "grey42",
            # Text colors
            "text": "grey89",
            "text_highlight": "grey100",
        }

    def _apply_theme(self, element: Any, style: str) -> Any:
        """Apply theme style to rich element"""
        if hasattr(element, "style"):
            element.style = self.theme.get(style, style)
        return element

    def show_header(self) -> Panel:
        """Display a styled header panel"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header_text = Text()
        header_text.append(self.title, style=f"bold {self.theme['primary']}")
        header_text.append("\n")
        header_text.append(now, style=self.theme["neutral"])

        return Panel(
            Align.center(header_text),
            style=f"bold {self.theme['primary']}",
            box=DOUBLE,
            border_style=self.theme["border"],
        )

    def show_table(self, data: Optional[List[Dict]] = None) -> Table:
        """Display a customizable table with data"""
        data = data or [
            {"Feature": "Tables", "Status": "Ready", "Version": "1.0"},
            {"Feature": "Panels", "Status": "Ready", "Version": "1.2"},
            {"Feature": "Spinners", "Status": "Ready", "Version": "1.1"},
            {"Feature": "Progress Bars", "Status": "Ready", "Version": "1.3"},
            {"Feature": "Charts", "Status": "Coming Soon", "Version": "2.0"},
        ]

        table = Table(
            title="📊 System Features",
            box=ROUNDED,
            highlight=True,
            border_style=self.theme["border"],
            header_style=f"bold {self.theme['text_highlight']}",
            title_style=f"bold {self.theme['primary']}",
        )

        # Add columns dynamically based on data keys
        for column in data[0].keys():
            table.add_column(
                column,
                style=self.theme["text"],
                header_style=f"bold {self.theme['highlight']}",
            )

        # Add rows
        for row in data:
            status_style = (
                self.theme["success"]
                if "Ready" in row["Status"]
                else self.theme["warning"]
            )
            table.add_row(
                *[str(row[col]) for col in row.keys()], style=f"{status_style} dim"
            )

        return table

    def show_panels(self, panels: Optional[List[Dict]] = None) -> Columns:
        """Display multiple panels in columns"""
        panels = panels or [
            {
                "title": "✅ Success",
                "content": "All systems operational",
                "type": "success",
            },
            {"title": "❌ Error", "content": "No issues detected", "type": "error"},
            {
                "title": "⚠️ Warning",
                "content": "Maintenance scheduled",
                "type": "warning",
            },
            {"title": "ℹ️ Info", "content": "v2.0 coming soon", "type": "info"},
        ]

        rendered_panels = []
        for panel in panels:
            panel_type = panel["type"]
            rendered_panels.append(
                Panel(
                    panel["content"],
                    title=panel["title"],
                    border_style=self.theme["border"],
                    box=HEAVY if panel_type == "info" else ROUNDED,
                    style=f"dim {self.theme[panel_type]}",  # Apply the panel style here
                )
            )

        return Columns(rendered_panels, equal=True, expand=True)

    def show_stats(self, stats: Optional[Dict] = None) -> Panel:
        """Display key statistics in a panel"""
        stats = stats or {
            "CPU Usage": f"{random.randint(1, 100)}%",
            "Memory": f"{random.randint(1, 128)}GB used",
            "Tasks": str(random.randint(1, 50)),
            "Uptime": f"{random.randint(1, 30)} days",
        }

        content = "\n".join(
            f"[{self.theme['text']}]{key}:[/] [{self.theme['text_highlight']}]{value}[/]"
            for key, value in stats.items()
        )

        return Panel(
            content,
            title="📈 System Stats",
            border_style=self.theme["border"],
            box=ROUNDED,
            style=f"bold {self.theme['primary']}",  # Apply title style here
        )


class RichProgress:
    def __init__(self, console: Console, theme: Dict[str, str] = None):
        self.console = console
        self.theme = theme or {
            "primary": "steel_blue",
            "success": "sea_green3",
            "text": "grey89",
        }

    def show_spinner(
        self, message: str = "Loading data", spinner_type: str = "dots"
    ) -> None:
        """Show an animated spinner with message"""
        with self.console.status(
            f"[{self.theme['primary']} dim]{message}...",
            spinner=spinner_type,
            spinner_style=self.theme["primary"],
        ):
            sleep(2)
        self.console.print(f"[{self.theme['success']} dim]✔ {message} Complete!")

    def show_progress(self, tasks: Optional[List[Dict]] = None) -> None:
        """Show multiple progress bars for different tasks"""
        tasks = tasks or [
            {"description": "Processing data", "total": 100},
            {"description": "Downloading files", "total": 50},
            {"description": "Analyzing results", "total": 75},
        ]

        with Progress(
            SpinnerColumn(style=self.theme["primary"]),
            TextColumn(
                "[progress.description]{task.description}", style=self.theme["text"]
            ),
            BarColumn(
                bar_width=None,
                complete_style=self.theme["primary"],
                pulse_style=self.theme["highlight"],
            ),
            TextColumn(
                "[progress.percentage]{task.percentage:>3.0f}%",
                style=self.theme["text"],
            ),
            console=self.console,
            expand=True,
            transient=True,
        ) as progress:
            progress_tasks = [
                progress.add_task(
                    f"[{self.theme['text']}]{task['description']}...",
                    total=task["total"],
                )
                for task in tasks
            ]

            while not all(progress.tasks[task].completed for task in progress_tasks):
                for task in progress_tasks:
                    if not progress.finished:
                        progress.update(task, advance=random.uniform(0.5, 5))
                sleep(0.1)

        self.console.print(f"[{self.theme['success']} dim]✔ All tasks completed!")


def dashboard():
    console = Console()

    # Enhanced minimalistic theme
    custom_theme = {
        # Primary colors
        "primary": "steel_blue",
        "secondary": "dark_sea_green",
        # Status colors
        "success": "sea_green3",
        "error": "indian_red",
        "warning": "light_goldenrod2",
        "info": "sky_blue3",
        "highlight": "medium_orchid",
        # Neutral colors
        "neutral": "grey62",
        "border": "grey42",
        # Text colors
        "text": "grey89",
        "text_highlight": "grey100",
    }

    dashboard = RichDashboard(theme=custom_theme)
    progress = RichProgress(console, theme=custom_theme)

    # Create a layout
    layout = Layout(name="root")
    layout.split(
        Layout(name="header", size=3),
        Layout(name="main", ratio=1),
        Layout(name="footer", size=3),
    )

    layout["main"].split_row(
        Layout(name="left", ratio=2), Layout(name="right", ratio=1)
    )

    layout["left"].split(Layout(name="features"), Layout(name="progress"))

    # Update layout with content
    layout["header"].update(dashboard.show_header())
    layout["features"].update(dashboard.show_table())
    layout["right"].update(Group(dashboard.show_stats(), dashboard.show_panels()))

    # Clear and render
    console.clear()
    console.print(layout)

    # Show progress in the designated area
    with console.capture() as capture:
        progress.show_progress()
    layout["progress"].update(
        Panel(
            capture.get(),
            title="Progress",
            border_style=custom_theme["border"],
            box=ROUNDED,
        )
    )

    console.print(layout)

    # Final spinner
    progress.show_spinner("Finalizing dashboard")


if __name__ == "__main__":
    dashboard()
