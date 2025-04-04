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
from rich.live import Live
from rich import box
from time import sleep
from datetime import datetime
import random
import sys
import os
import argparse
from typing import Dict, List, Optional, Any, Tuple, Union


class RichDashboard:
    """
    A comprehensive dashboard for terminal applications built with Rich.
    Provides various visualization components and layout options.
    """

    def __init__(
        self,
        title: str = "🚀 Ultimate Rich CLI Dashboard",
        theme: Optional[Dict[str, str]] = None,
        console: Optional[Console] = None,
    ):
        """
        Initialize the dashboard with custom title and theme.

        Args:
            title: Dashboard title text
            theme: Dictionary of color styles for different elements
            console: Optional pre-configured console instance
        """
        self.console = console or Console()
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

        # Initialize cache for tables and other data
        self._cache = {}

    def _gradient_text(self, text: str, start: str, end: str) -> Text:
        """
        Create gradient-colored text using Rich's color interpolation.

        Args:
            text: The text to apply gradient to
            start: Starting color name
            end: Ending color name

        Returns:
            Rich Text object with gradient styling
        """
        gradient = Text()
        if not text:
            return gradient

        for i, char in enumerate(text):
            gradient.append(char, style=f"color({start}->{end})[{i}/{len(text)}]")
        return gradient

    def show_header(self, subtitle: Optional[str] = None) -> Panel:
        """
        Display a compact styled header panel with gradient title.

        Args:
            subtitle: Optional subtitle to display under the main title

        Returns:
            Rich Panel containing the header
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        left_column = [self._gradient_text(self.title, "dark_cyan", "medium_purple1")]
        if subtitle:
            left_column.append(Text(f"\n{subtitle}", style=self.theme["secondary"]))

        header_content = Columns(
            [
                Group(*left_column),
                Align.right(Text(now, style=self.theme["neutral"])),
            ],
            expand=True,
        )

        return Panel(
            header_content,
            box=MINIMAL,
            style=Style(color=self.theme["border"], bgcolor=self.theme["background"]),
            padding=(0, 1),
        )

    def show_table(
        self,
        data: Optional[List[Dict[str, Any]]] = None,
        title: str = "📊 System Overview",
        box_style: box = ROUNDED,
        cache_key: Optional[str] = None,
    ) -> Panel:
        """
        Display a compact table with optimized column widths.

        Args:
            data: List of dictionaries containing row data
            title: Table panel title
            box_style: Rich box style for the table panel
            cache_key: Optional key to cache and reuse table data

        Returns:
            Rich Panel containing the table
        """
        # Use cached data if available and requested
        if cache_key and cache_key in self._cache:
            data = self._cache[cache_key]
        else:
            data = data or [
                {"Component": "Tables", "Status": "Active", "Version": "1.0"},
                {"Component": "Panels", "Status": "Active", "Version": "1.2"},
                {"Component": "Progress", "Status": "Active", "Version": "1.1"},
                {"Component": "Charts", "Status": "Coming Soon", "Version": "2.0"},
            ]

            # Cache data if requested
            if cache_key:
                self._cache[cache_key] = data

        # Calculate optimal column widths
        col_widths = {}
        for column in data[0].keys():
            col_widths[column] = (
                max(len(column), max(len(str(row.get(column, ""))) for row in data)) + 2
            )

        table = Table(
            box=MINIMAL,
            highlight=True,
            header_style=f"bold {self.theme['primary']}",
            row_styles=[self.theme["text"], f"dim {self.theme['text']}"],
            padding=(0, 1),
            show_edge=False,
            expand=False,
        )

        for column in data[0].keys():
            table.add_column(
                self._gradient_text(column, "dodger_blue2", "dark_orange3"),
                header_style="bold",
                width=col_widths[column],
                justify="left",
            )

        for row in data:
            # Determine status style based on content
            styled_row = []
            for col in data[0].keys():
                value = str(row.get(col, ""))

                if col == "Status":
                    if "Active" in value:
                        style = self.theme["success"]
                    elif "Coming Soon" in value:
                        style = self.theme["warning"]
                    elif "Error" in value or "Failed" in value:
                        style = self.theme["error"]
                    else:
                        style = self.theme["neutral"]
                else:
                    style = None

                styled_row.append(Text(value, style=style))

            table.add_row(*styled_row)

        return Panel(
            table,
            title=title,
            box=box_style,
            border_style=self.theme["border"],
            title_align="left",
            padding=(1, 1),
        )

    def show_panels(
        self,
        panels: Optional[List[Dict[str, Any]]] = None,
        title: str = "📌 Status Summary",
    ) -> Panel:
        """
        Display compact panels with custom icons arranged in a grid.

        Args:
            panels: List of panel configurations
            title: Main panel group title

        Returns:
            Rich Panel containing the panel group
        """
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
        for panel_config in panels:
            title_text = Text()
            title_text.append(panel_config.get("icon", "") + " ", style="bold")
            title_text.append(
                panel_config["title"], style=f"bold {self.theme[panel_config['type']]}"
            )

            # Support for rich Text objects or plain strings
            content = panel_config["content"]
            if not isinstance(content, Text):
                content = Text(content, justify="left")

            panel_group.append(
                Panel(
                    content,
                    title=title_text,
                    border_style=self.theme[panel_config["type"]],
                    box=SIMPLE_HEAVY,
                    padding=(0, 1),
                )
            )

        return Panel(
            Columns(panel_group, equal=True, expand=True),
            title=title,
            box=ROUNDED,
            border_style=self.theme["border"],
            padding=(0, 0),
        )

    def show_stats(
        self,
        stats: Optional[Dict[str, str]] = None,
        title: str = "📈 Performance Metrics",
        dynamic: bool = False,
    ) -> Panel:
        """
        Display statistics in a compact card layout.

        Args:
            stats: Dictionary of stat name to value mappings
            title: Stats panel title
            dynamic: If True, will return random values when None provided

        Returns:
            Rich Panel containing the stats
        """
        if stats is None and dynamic:
            stats = {
                "CPU Usage": f"{random.randint(1, 100)}%",
                "Memory": f"{random.randint(1, 128)}GB",
                "Tasks": str(random.randint(1, 50)),
                "Uptime": f"{random.randint(1, 30)}d",
            }
        else:
            stats = stats or {
                "CPU Usage": "35%",
                "Memory": "64GB",
                "Tasks": "28",
                "Uptime": "12d",
            }

        stat_items = []
        for key, value in stats.items():
            stat_text = Text()
            stat_text.append(f"{value}\n", style=f"bold {self.theme['text_highlight']}")
            stat_text.append(key, style=f"dim {self.theme['text']}")
            stat_items.append(stat_text)

        grid = Columns(
            stat_items,
            equal=True,
            expand=True,
            padding=(0, 2),
        )

        return Panel(
            grid,
            title=title,
            box=ROUNDED,
            border_style=self.theme["border"],
            style=f"dim {self.theme['secondary']}",
            padding=(1, 1),
        )

    def show_live_dashboard(
        self,
        layout: Optional[Layout] = None,
        update_interval: float = 1.0,
        max_iterations: int = 10,
    ) -> None:
        """
        Display a live-updating dashboard with automatic refreshing of content.

        Args:
            layout: Pre-configured Rich Layout object
            update_interval: Seconds between updates
            max_iterations: Number of updates before stopping
        """
        if layout is None:
            layout = Layout()
            layout.split(
                Layout(name="header", size=3),
                Layout(name="main"),
                Layout(name="footer", size=1),
            )
            layout["main"].split_row(
                Layout(name="left"),
                Layout(name="right"),
            )
            layout["left"].split(
                Layout(name="top"),
                Layout(name="bottom"),
            )

        # Initial setup
        layout["header"].update(self.show_header())
        layout["footer"].update(
            Panel(Text("Press Ctrl+C to exit", justify="center"), box=MINIMAL)
        )

        try:
            with Live(layout, refresh_per_second=4, screen=True):
                for i in range(max_iterations):
                    # Update changing elements
                    layout["header"].update(self.show_header(f"Iteration: {i+1}"))
                    layout["top"].update(
                        self.show_table(dynamic_data(i), title="📊 Live Data")
                    )
                    layout["bottom"].update(self.show_stats(dynamic=True))
                    layout["right"].update(self.show_panels(dynamic_panels(i)))

                    sleep(update_interval)
        except KeyboardInterrupt:
            self.console.print("[bold green]Dashboard stopped by user.[/]")


class RichProgress:
    """
    Enhanced progress visualization tools using Rich.
    """

    def __init__(
        self, console: Optional[Console] = None, theme: Optional[Dict[str, str]] = None
    ):
        """
        Initialize progress visualization tools.

        Args:
            console: Rich Console instance
            theme: Dictionary of color styles
        """
        self.console = console or Console()
        self.theme = theme or {
            "primary": "steel_blue",
            "success": "sea_green3",
            "text": "grey89",
            "text_highlight": "white",
        }

    def show_spinner(
        self,
        message: str = "Loading",
        spinner_type: str = "dots",
        wait_time: float = 2.0,
        show_done: bool = True,
    ) -> None:
        """
        Show an animated spinner with message.

        Args:
            message: Text to display next to spinner
            spinner_type: Rich spinner animation type
            wait_time: How long to display the spinner
            show_done: Whether to show completion message
        """
        with self.console.status(
            f"[{self.theme['primary']} dim]{message}...",
            spinner=spinner_type,
            spinner_style=self.theme["primary"],
        ):
            sleep(wait_time)

        if show_done:
            self.console.print(f"[{self.theme['success']} dim]✔ {message} Complete!")

    def show_progress(
        self, tasks: Optional[List[Dict[str, Any]]] = None, transient: bool = True
    ) -> None:
        """
        Show enhanced progress bars with gradient styling.

        Args:
            tasks: List of task configurations
            transient: Whether to remove progress bars after completion
        """
        tasks = tasks or [
            {"description": "Processing data", "total": 100},
            {"description": "Downloading files", "total": 50},
            {"description": "Analyzing results", "total": 75},
        ]

        with Progress(
            SpinnerColumn("dots", style=self.theme["primary"]),
            TextColumn(
                "[progress.description]{task.description:<20}",
                style=self.theme["text"],
            ),
            BarColumn(
                bar_width=30,
                complete_style=self.theme["primary"],
                finished_style=self.theme["success"],
            ),
            TextColumn(
                "[progress.percentage]{task.percentage:>3.0f}%",
                style=self.theme["text_highlight"],
            ),
            TextColumn(
                "• {task.completed}/{task.total}", style=f"dim {self.theme['text']}"
            ),
            console=self.console,
            expand=False,
            transient=transient,
        ) as progress:
            task_ids = [
                progress.add_task(
                    f"[{self.theme['text']}]{task['description']}", total=task["total"]
                )
                for task in tasks
            ]

            while any(task.completed < task.total for task in progress.tasks):

                for task_id in task_ids:
                    if not progress.tasks[task_ids.index(task_id)].finished:

                        # Variable speed for more realistic progress
                        speed = random.uniform(0.5, 3)
                        remaining = (
                            progress.tasks[task_ids.index(task_id)].total
                            - progress.tasks[task_ids.index(task_id)].completed
                        )

                        # Slow down as we get closer to completion
                        if remaining < 10:
                            speed = speed * 0.5

                        progress.update(task_id, advance=speed)
                sleep(0.05)

            self.console.print(
                f"[{self.theme['success']} bold]✔ All tasks completed!",
                justify="center",
            )


def wait_for_user(
    console: Console, message: str = "Press Enter to continue..."
) -> None:
    """
    Display a message and wait for user input.

    Args:
        console: Rich Console instance
        message: Message to display
    """
    console.print(
        Panel(
            Align.center(
                Text(message, style="italic"),
            ),
            box=MINIMAL,
            style="dim",
            padding=(1, 1),
        )
    )
    input()
    console.clear()


def dynamic_data(iteration: int) -> List[Dict[str, str]]:
    """
    Generate dynamic table data that changes over time.

    Args:
        iteration: Current iteration number

    Returns:
        List of data dictionaries
    """
    statuses = ["Active", "Updating", "Active", "Coming Soon"]
    if iteration % 3 == 0:
        statuses[1] = "Error"

    return [
        {"Component": "Tables", "Status": statuses[0], "Version": f"1.{iteration % 5}"},
        {
            "Component": "Panels",
            "Status": statuses[1],
            "Version": f"1.{(iteration + 2) % 10}",
        },
        {
            "Component": "Progress",
            "Status": statuses[2],
            "Version": f"1.{(iteration + 1) % 7}",
        },
        {"Component": "Charts", "Status": statuses[3], "Version": f"2.{iteration % 3}"},
    ]


def dynamic_panels(iteration: int) -> List[Dict[str, Any]]:
    """
    Generate dynamic panel data that changes over time.

    Args:
        iteration: Current iteration number

    Returns:
        List of panel configuration dictionaries
    """
    cpu = random.randint(5, 95)
    memory = random.randint(20, 85)
    alerts = random.randint(0, 5)

    panels = [
        {
            "title": "System Health",
            "content": f"▶ CPU: {cpu}% utilized\n▶ {42 + iteration % 20} processes running",
            "type": "success" if cpu < 80 else "warning",
            "icon": "🛡️",
        },
        {
            "title": "Network Status",
            "content": f"▶ {85 + iteration % 30} Mbps incoming\n▶ {23 + iteration % 15} Mbps outgoing",
            "type": "info",
            "icon": "🌐",
        },
        {
            "title": "Memory Usage",
            "content": f"▶ {memory}% utilized\n▶ {8 - iteration % 3}GB free",
            "type": "success" if memory < 75 else "warning",
            "icon": "💾",
        },
        {
            "title": "Alerts",
            "content": f"▶ {'No' if alerts == 0 else alerts} critical issues\n▶ {3 + iteration % 5} warnings",
            "type": "success" if alerts == 0 else "error",
            "icon": "🚨",
        },
    ]

    return panels


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        Parsed argument namespace
    """
    parser = argparse.ArgumentParser(description="Rich CLI Dashboard")
    parser.add_argument(
        "--live", action="store_true", help="Run in live mode with automatic updates"
    )
    parser.add_argument(
        "--theme",
        choices=["default", "dark", "light", "neon"],
        default="default",
        help="Color theme to use",
    )
    parser.add_argument(
        "--duration", type=int, default=30, help="Duration in seconds for live mode"
    )
    return parser.parse_args()


def get_theme(theme_name: str) -> Dict[str, str]:
    """
    Get predefined color theme.

    Args:
        theme_name: Name of the theme

    Returns:
        Theme color dictionary
    """
    themes = {
        "default": {
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
        },
        "dark": {
            "primary": "steel_blue",
            "secondary": "slate_blue3",
            "success": "green4",
            "error": "dark_red",
            "warning": "dark_goldenrod",
            "info": "royal_blue1",
            "highlight": "purple4",
            "neutral": "grey50",
            "border": "grey23",
            "text": "grey74",
            "text_highlight": "grey93",
            "background": "grey7",
        },
        "light": {
            "primary": "blue",
            "secondary": "dark_green",
            "success": "green",
            "error": "red",
            "warning": "dark_orange",
            "info": "cyan3",
            "highlight": "magenta",
            "neutral": "grey58",
            "border": "grey70",
            "text": "grey19",
            "text_highlight": "black",
            "background": "grey93",
        },
        "neon": {
            "primary": "bright_cyan",
            "secondary": "bright_green",
            "success": "bright_green",
            "error": "bright_red",
            "warning": "bright_yellow",
            "info": "bright_blue",
            "highlight": "bright_magenta",
            "neutral": "bright_white",
            "border": "bright_black",
            "text": "bright_white",
            "text_highlight": "white",
            "background": "black",
        },
    }

    return themes.get(theme_name, themes["default"])


def main() -> None:
    """Main application entry point."""
    args = parse_arguments()
    console = Console()
    theme = get_theme(args.theme)

    dashboard = RichDashboard(theme=theme, console=console)
    progress = RichProgress(console, theme=theme)

    # Welcome screen with gradient title
    console.clear()
    console.print(
        Panel(
            Align.center(
                Group(
                    Text("Welcome to", style=f"dim {theme['neutral']}"),
                    dashboard._gradient_text(
                        "ULTIMATE RICH CLI DASHBOARD", "steel_blue", "medium_purple1"
                    ),
                    Text("\n"),
                    Text(
                        "A modern terminal interface solution",
                        style=theme["secondary"],
                    ),
                    Text("\n"),
                    Text(
                        f"Theme: {args.theme.capitalize()}",
                        style=f"italic {theme['info']}",
                    ),
                )
            ),
            box=ROUNDED,
            padding=(2, 4),
            border_style=theme["border"],
        ),
        justify="center",
    )

    if args.live:
        # Run in live mode
        wait_for_user(console, "Press Enter to start Live Dashboard...")
        dashboard.show_live_dashboard(
            update_interval=args.duration / 10, max_iterations=10
        )
        return

    wait_for_user(console)

    # Responsive layout system
    term_width = console.width or 100
    layout = Layout()

    if term_width < 100:
        layout.split(
            Layout(name="header", size=3),
            Layout(name="top"),
            Layout(name="middle"),
            Layout(name="bottom"),
            Layout(name="footer", size=1),
        )
    else:
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=1),
        )
        layout["main"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=1),
        )
        layout["left"].split(
            Layout(name="top"),
            Layout(name="bottom", size=8),
        )
        layout["right"].split(
            Layout(name="stats"),
            Layout(name="middle"),
            Layout(name="panels"),
        )

    layout["footer"].update(
        Panel(Text("Press Enter to continue...", justify="center"), box=MINIMAL)
    )

    # Build the dashboard
    layout["header"].update(dashboard.show_header())

    if term_width < 100:
        console.clear()
        console.print(layout["header"])
        console.print(dashboard.show_table())
        wait_for_user(console)

        console.print(layout["header"])
        console.print(dashboard.show_stats())
        wait_for_user(console)

        console.print(layout["header"])
        # Add more panels to showcase layout capabilities
        enhanced_panels = [
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
                "title": "Memory Usage",
                "content": "▶ 63% utilized\n▶ 3.2GB free",
                "type": "warning",
                "icon": "💾",
            },
            {
                "title": "Alerts",
                "content": "▶ No critical issues\n▶ 3 warnings",
                "type": "warning",
                "icon": "🚨",
            },
        ]
        console.print(dashboard.show_panels(enhanced_panels))
        wait_for_user(console)
    else:
        layout["top"].update(dashboard.show_table())
        console.print(layout)
        wait_for_user(console)

        layout["stats"].update(dashboard.show_stats())
        console.clear()
        console.print(layout)
        wait_for_user(console)

        # Add more grid items
        more_stats = {
            "CPU Usage": "42%",
            "Memory": "64GB",
            "Tasks": "28",
            "Uptime": "12d",
            "Threads": "86",
            "Disk I/O": "4.2MB/s",
        }
        layout["stats"].update(dashboard.show_stats(more_stats))

        layout["middle"].update(
            Panel(
                Align.center(Text("Custom Panel Content", style=theme["highlight"])),
                title="🧩 Extra Section",
                border_style=theme["border"],
                box=DOUBLE,
            )
        )

        enhanced_panels = [
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
                "title": "Memory Usage",
                "content": "▶ 63% utilized\n▶ 3.2GB free",
                "type": "warning",
                "icon": "💾",
            },
            {
                "title": "Alerts",
                "content": "▶ No critical issues\n▶ 3 warnings",
                "type": "warning",
                "icon": "🚨",
            },
        ]
        layout["panels"].update(dashboard.show_panels(enhanced_panels))
        console.clear()
        console.print(layout)
        wait_for_user(console)

    # Progress demonstrations
    console.clear()
    console.print(layout["header"])
    console.print(
        Panel(
            Text("Initializing system components...", style=theme["text"]),
            title="⚙️ System Initialization",
            border_style=theme["border"],
            box=ROUNDED,
        )
    )
    progress.show_spinner("System Boot")

    wait_for_user(console)

    console.print(layout["header"])
    console.print(
        Panel(
            Text("Executing background tasks...", style=theme["text"]),
            title="⚡ Task Processing",
            border_style=theme["border"],
            box=ROUNDED,
        )
    )
    # More realistic tasks with varying lengths
    tasks = [
        {"description": "Processing data", "total": 100},
        {"description": "Downloading files", "total": 50},
        {"description": "Analyzing results", "total": 75},
        {"description": "Generating reports", "total": 30},
        {"description": "Optimizing assets", "total": 120},
    ]
    progress.show_progress(tasks)

    # Final screen
    console.clear()
    console.print(
        Panel(
            Align.center(
                Group(
                    dashboard._gradient_text(
                        "Session Complete!", "spring_green3", "deep_sky_blue4"
                    ),
                    Text("\n"),
                    Text(
                        "Thank you for using the dashboard",
                        style=theme["text"],
                    ),
                    Text("\n"),
                    Text(
                        "Run with --live flag for continuous updates",
                        style=f"dim {theme['info']}",
                    ),
                )
            ),
            box=ROUNDED,
            padding=(2, 4),
            border_style=theme["border"],
        ),
        justify="center",
    )


if __name__ == "__main__":
    main()
