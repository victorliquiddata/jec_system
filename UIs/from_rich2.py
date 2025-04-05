from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.columns import Columns
from rich.box import ROUNDED, DOUBLE, HEAVY, MINIMAL, SIMPLE_HEAVY
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
            "primary": "steel_blue",
            "secondary": "dark_sea_green",
            "success": "sea_green3",
            "error": "indian_red",
            "warning": "light_goldenrod2",
            "info": "sky_blue3",
            "highlight": "medium_orchid",
            "neutral": "grey62",
            "border": "grey42",
            "text": "grey89",
            "text_highlight": "grey100",
            "background": "grey19",
        }

    def _gradient_text(self, text: str, start: str, end: str) -> Text:
        """Create gradient-colored text"""
        gradient = Text()
        for i, char in enumerate(text):
            gradient.append(char, style=f"color({start}->{end})[{i}/{len(text)}]")
        return gradient

    def show_header(self) -> Panel:
        """Display a styled header panel with gradient title"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header_content = Columns(
            [
                self._gradient_text(self.title, "dark_cyan", "medium_purple1"),
                Align.right(Text(now, style=self.theme["neutral"])),
            ],
            expand=True,
        )

        return Panel(
            header_content,
            box=HEAVY,
            style=Style(color=self.theme["border"], bgcolor=self.theme["background"]),
            padding=(0, 2),
        )

    def show_table(self, data: Optional[List[Dict]] = None) -> Table:
        """Display an enhanced table with gradient headers"""
        data = data or [
            {"Feature": "Tables", "Status": "Ready", "Version": "1.0"},
            {"Feature": "Panels", "Status": "Ready", "Version": "1.2"},
            {"Feature": "Spinners", "Status": "Ready", "Version": "1.1"},
            {"Feature": "Progress Bars", "Status": "Ready", "Version": "1.3"},
            {"Feature": "Charts", "Status": "Coming Soon", "Version": "2.0"},
        ]

        table = Table(
            box=MINIMAL,
            highlight=True,
            header_style=f"bold {self.theme['primary']}",
            row_styles=[self.theme["text"]],
            padding=(0, 1),
            show_edge=False,
        )

        # Add table columns
        for column in data[0].keys():
            table.add_column(
                self._gradient_text(column, "dodger_blue2", "dark_orange3"),
                header_style="bold",
                width=18,
            )

        # Add rows with styles
        for row in data:
            status_style = (
                self.theme["warning"]
                if "Coming Soon" in row["Status"]
                else self.theme["success"]
            )
            # Ensure that all column names are handled properly here
            styled_row = [
                (
                    Text(str(row.get(col, "")))  # Use .get to avoid KeyError
                    if col in row
                    else Text("")
                )  # Fallback in case column is missing in a row
                for col in row.keys()
            ]
            table.add_row(*styled_row)

        return Panel(
            table,
            title="📊 System Features",
            box=ROUNDED,
            border_style=self.theme["border"],
            title_align="left",
            padding=(1, 2),
        )

    def show_panels(self, panels: Optional[List[Dict]] = None) -> Panel:
        """Display interactive panels with custom icons"""
        panels = panels or [
            {
                "title": "System Health",
                "content": "▶ All systems operational\n▶ 42 processes running",
                "type": "success",
                "icon": "🛡️",
            },
            {
                "title": "Network Status",
                "content": "▶ 85 Mbps incoming\n▶ 23 Mbps outgoing",
                "type": "info",
                "icon": "🌐",
            },
            {
                "title": "Alerts",
                "content": "▶ No critical issues\n▶ 3 warnings",
                "type": "warning",
                "icon": "🚨",
            },
        ]

        panel_group = []
        for panel in panels:
            title_text = Text()
            title_text.append(panel["icon"] + " ", style="bold")
            title_text.append(panel["title"], style=f"bold {self.theme[panel['type']]}")

            content = Panel(
                Text(panel["content"], justify="left"),
                box=SIMPLE_HEAVY,
                style=f"dim {self.theme['text']}",
                padding=(1, 2),
            )

            panel_group.append(
                Panel(
                    content,
                    title=title_text,
                    border_style=self.theme["border"],
                    box=HEAVY,
                    padding=(0, 1),
                )
            )

        return Panel(
            Columns(panel_group, equal=True, expand=True),
            box=ROUNDED,
            border_style=self.theme["border"],
        )

    def show_stats(self, stats: Optional[Dict] = None) -> Panel:
        """Display statistics in a modern card layout"""
        stats = stats or {
            "CPU Usage": f"{random.randint(1, 100)}%",
            "Memory": f"{random.randint(1, 128)}GB",
            "Tasks": str(random.randint(1, 50)),
            "Uptime": f"{random.randint(1, 30)}d",
        }

        grid = Columns(
            [
                Text(
                    f"[b {self.theme['text_highlight']}]{value}\n[dim {self.theme['text']}]{key}"
                )
                for key, value in stats.items()
            ],
            equal=True,
            expand=True,
        )

        return Panel(
            grid,
            title="📈 Performance Metrics",
            box=ROUNDED,
            border_style=self.theme["border"],
            style=f"dim {self.theme['secondary']}",
            padding=(1, 2),
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
        """Show enhanced progress bars"""
        tasks = tasks or [
            {"description": "Processing data", "total": 100},
            {"description": "Downloading files", "total": 50},
            {"description": "Analyzing results", "total": 75},
        ]

        with Progress(
            SpinnerColumn("dots", style=self.theme["primary"]),
            TextColumn(
                "[progress.description]{task.description}", style=self.theme["text"]
            ),
            BarColumn(
                bar_width=40,
                complete_style=self.theme["primary"],
                finished_style=self.theme["success"],
            ),
            TextColumn("•", style=self.theme["neutral"]),
            TextColumn(
                "[progress.percentage]{task.percentage:>3.0f}%",
                style=self.theme["text_highlight"],
            ),
            console=self.console,
            expand=True,
            transient=True,
        ) as progress:
            tasks = [
                progress.add_task(
                    f"[{self.theme['text']}]{task['description']}", total=task["total"]
                )
                for task in tasks
            ]

            while not all(progress.finished for task in tasks):
                for task in tasks:
                    progress.update(task, advance=random.uniform(0.5, 3))
                sleep(0.05)

            self.console.print(
                f"[{self.theme['success']} bold]✔ All tasks completed!",
                justify="center",
            )


def dashboard():
    console = Console()
    custom_theme = {
        "primary": "dodger_blue2",
        "secondary": "dark_sea_green4",
        "success": "spring_green3",
        "error": "red1",
        "warning": "gold1",
        "info": "deep_sky_blue3",
        "highlight": "medium_purple1",
        "neutral": "grey66",
        "border": "grey35",
        "text": "grey89",
        "text_highlight": "white",
        "background": "grey11",
    }

    dashboard = RichDashboard(theme=custom_theme)
    progress = RichProgress(console, theme=custom_theme)

    layout = Layout(name="root")
    layout.split(
        Layout(name="header", size=3),
        Layout(name="main", ratio=1),
        Layout(name="footer", size=3),
    )

    layout["main"].split_row(
        Layout(name="left", ratio=3),
        Layout(name="right", ratio=2),
    )

    layout["left"].split(
        Layout(dashboard.show_table(), name="features"), Layout(name="progress", size=8)
    )

    layout["right"].split(
        Layout(dashboard.show_stats(), name="stats"),
        Layout(dashboard.show_panels(), name="panels"),
    )

    console.clear()
    console.print(layout)

    with console.capture() as capture:
        progress.show_progress()
    layout["progress"].update(
        Panel.fit(
            capture.get(),
            title="Active Processes",
            border_style=custom_theme["border"],
            padding=(1, 2),
        )
    )

    console.print(layout)
    progress.show_spinner("Finalizing dashboard display")


if __name__ == "__main__":
    dashboard()
