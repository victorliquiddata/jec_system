from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.align import Align

# Create console with consistent width
console = Console(width=80, highlight=False)


def display_cli_interface():
    # Header with fixed alignment
    header_text = Text("🖥️  MinimalCLI - Monochrome Mode", style="bold #E0E0E0")
    console.print(
        Panel(
            Align.center(header_text),
            border_style="#7A7A7A",
            padding=(1, 2),
            title="v1.0.1",
            title_align="right",
        )
    )

    # Fixed message styles table
    console.print("\n[bold #E0E0E0]MESSAGE STYLES[/]")
    styles_table = Table(show_header=False, box=None, expand=False)
    styles_table.add_column("Icon", style="#E0E0E0", width=4)
    styles_table.add_column("Type", style="#E0E0E0", width=12)
    styles_table.add_column("Description", style="#E0E0E0")

    styles_table.add_row(
        "📜", "Primary:", Text("Standard output message.", style="bold #E0E0E0")
    )
    styles_table.add_row(
        "🗒️", "Secondary:", Text("Less important details like logs.", style="#7A7A7A")
    )
    styles_table.add_row(
        "🔍",
        "Accent:",
        Text("A subtle highlight, used sparingly.", style="underline #BDBDBD"),
    )

    console.print(styles_table)

    # Clean separator
    console.print(Rule(style="#7A7A7A"))

    # Fixed status indicators table
    console.print("\n[bold #E0E0E0]STATUS INDICATORS[/]")
    status_table = Table(show_header=False, box=None, expand=False)
    status_table.add_column("Icon", style="#E0E0E0", width=4)
    status_table.add_column("Type", style="#E0E0E0", width=12)
    status_table.add_column("Description", style="#E0E0E0")

    status_table.add_row(
        "✔", "Success:", Text("Operation completed successfully.", style="bold #66BB6A")
    )
    status_table.add_row(
        "⚠", "Warning:", Text("Check your input parameters.", style="bold #E6A23C")
    )
    status_table.add_row(
        "❌", "Error:", Text("Something went wrong!", style="bold #D32F2F")
    )
    status_table.add_row(
        "ℹ️", "Info:", Text("Helpful information for users.", style="bold #2196F3")
    )

    console.print(status_table)

    # Fixed command examples table
    console.print("\n[bold #E0E0E0]COMMON COMMANDS[/]")
    commands_table = Table(show_header=False, box=None, expand=False)
    commands_table.add_column("Command", style="#BDBDBD", width=16, justify="right")
    commands_table.add_column("Description", style="#7A7A7A")

    commands_table.add_row("help", "Display this help screen")
    commands_table.add_row("status", "Show system status")
    commands_table.add_row("clear", "Clear the console")
    commands_table.add_row("exit", "Exit the application")

    console.print(commands_table)

    # Cleaner footer
    footer_text = Text.assemble(
        ("Status: Running", "italic #7A7A7A"),
        ("   |   ", "#BDBDBD"),
        ("Mode: Monochrome", "italic #7A7A7A"),
        ("   |   ", "#BDBDBD"),
        ("Time: 12:34:56", "italic #7A7A7A"),
    )

    console.print("\n")
    console.print(
        Panel(
            Align.center(footer_text),
            border_style="#BDBDBD",
            padding=(0, 2),
            expand=False,
        )
    )

    # Command prompt
    console.print("\n[bold #E0E0E0]> [/]", end="")


# Display the interface
display_cli_interface()
