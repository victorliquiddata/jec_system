import time
import os
import sqlite3
import shutil
from datetime import datetime, timedelta
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.layout import Layout
from rich.text import Text
from rich.prompt import Prompt
from rich.console import Group
from rich.align import Align
from rich.columns import Columns
from rich import box
import random


# Initialize Rich console with dynamic width based on terminal size
def get_terminal_size():
    """Get the current terminal size"""
    terminal_size = shutil.get_terminal_size((80, 24))  # Default fallback is 80x24
    return terminal_size.columns, terminal_size.lines


# Get current terminal width and height
terminal_width, terminal_height = get_terminal_size()

# Initialize the console with dynamic width
console = Console(width=terminal_width, highlight=False)


# Function to update console width when needed
def update_console_width():
    """Update console width based on current terminal size"""
    global console, terminal_width, terminal_height
    new_width, new_height = get_terminal_size()

    # Only update if dimensions changed
    if new_width != terminal_width or new_height != terminal_height:
        terminal_width, terminal_height = new_width, new_height
        console = Console(width=terminal_width, highlight=False)

    return terminal_width, terminal_height


def create_database():
    """Initialize the SQLite database and create necessary tables if they don't exist."""
    conn = sqlite3.connect("finance_manager.db")
    cursor = conn.cursor()

    # Create transactions table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            category TEXT,
            description TEXT,
            amount REAL,
            type TEXT
        )
    """
    )

    # Create budget table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS budget (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT UNIQUE,
            monthly_limit REAL
        )
    """
    )

    # Create goals table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            target_amount REAL,
            current_amount REAL,
            target_date TEXT
        )
    """
    )

    # Insert some default categories if none exist
    cursor.execute("SELECT COUNT(*) FROM budget")
    if cursor.fetchone()[0] == 0:
        default_categories = [
            ("Food", 400.0),
            ("Transportation", 200.0),
            ("Entertainment", 150.0),
            ("Housing", 800.0),
            ("Utilities", 250.0),
            ("Healthcare", 100.0),
            ("Shopping", 200.0),
            ("Personal", 150.0),
        ]
        cursor.executemany(
            "INSERT INTO budget (category, monthly_limit) VALUES (?, ?)",
            default_categories,
        )

    conn.commit()
    conn.close()


def add_sample_data():
    """Add sample transaction data if the database is empty."""
    conn = sqlite3.connect("finance_manager.db")
    cursor = conn.cursor()

    # Check if there are any transactions
    cursor.execute("SELECT COUNT(*) FROM transactions")
    if cursor.fetchone()[0] == 0:
        # Generate random transactions for the last 30 days
        categories = [
            "Food",
            "Transportation",
            "Entertainment",
            "Housing",
            "Utilities",
            "Healthcare",
            "Shopping",
            "Personal",
        ]
        types = ["expense", "income"]
        descriptions = {
            "Food": [
                "Grocery store",
                "Restaurant",
                "Coffee shop",
                "Fast food",
                "Delivery",
                "Bakery",
            ],
            "Transportation": [
                "Gas",
                "Public transit",
                "Uber",
                "Car maintenance",
                "Parking",
                "Toll",
            ],
            "Entertainment": [
                "Movies",
                "Concert",
                "Streaming service",
                "Books",
                "Games",
                "Subscription",
            ],
            "Housing": [
                "Rent",
                "Mortgage",
                "Repairs",
                "Furniture",
                "Decoration",
                "Insurance",
            ],
            "Utilities": [
                "Electricity",
                "Water",
                "Internet",
                "Phone",
                "Gas",
                "Garbage",
            ],
            "Healthcare": [
                "Doctor visit",
                "Pharmacy",
                "Insurance",
                "Therapy",
                "Gym",
                "Supplements",
            ],
            "Shopping": [
                "Clothing",
                "Electronics",
                "Home goods",
                "Gifts",
                "Online shopping",
                "Department store",
            ],
            "Personal": [
                "Haircut",
                "Toiletries",
                "Education",
                "Charity",
                "Hobbies",
                "Miscellaneous",
            ],
        }

        # Generate income entries
        today = datetime.now()
        income_entries = []
        for i in range(2):
            date = (today - timedelta(days=i * 15)).strftime("%Y-%m-%d")
            income_entries.append(
                (date, "Income", "Salary", random.uniform(2000, 3000), "income")
            )

        # Generate expense entries
        expense_entries = []
        for i in range(30):
            date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            for _ in range(random.randint(1, 3)):
                category = random.choice(categories)
                description = random.choice(descriptions[category])
                amount = (
                    random.uniform(5, 150)
                    if category != "Housing"
                    else random.uniform(500, 1200)
                )
                expense_entries.append((date, category, description, amount, "expense"))

        # Insert all sample data
        cursor.executemany(
            "INSERT INTO transactions (date, category, description, amount, type) VALUES (?, ?, ?, ?, ?)",
            income_entries + expense_entries,
        )

        # Add sample goals
        sample_goals = [
            (
                "Emergency Fund",
                5000.0,
                2000.0,
                (today + timedelta(days=180)).strftime("%Y-%m-%d"),
            ),
            (
                "Vacation",
                1500.0,
                500.0,
                (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            ),
            (
                "New Laptop",
                1200.0,
                300.0,
                (today + timedelta(days=120)).strftime("%Y-%m-%d"),
            ),
        ]
        cursor.executemany(
            "INSERT INTO goals (name, target_amount, current_amount, target_date) VALUES (?, ?, ?, ?)",
            sample_goals,
        )

        conn.commit()
    conn.close()


def display_splash_screen():
    """Display an enhanced splash screen with ASCII art and animations."""
    os.system("cls" if os.name == "nt" else "clear")  # Clear the screen

    # ASCII art logo
    splash = """
        ███████╗██╗███╗   ██╗ █████╗ ███╗   ██╗ ██████╗███████╗
        ██╔════╝██║████╗  ██║██╔══██╗████╗  ██║██╔════╝██╔════╝
        █████╗  ██║██╔██╗ ██║███████║██╔██╗ ██║██║     █████╗  
        ██╔══╝  ██║██║╚██╗██║██╔══██║██║╚██╗██║██║     ██╔══╝  
        ██║     ██║██║ ╚████║██║  ██║██║ ╚████║╚██████╗███████╗
        ╚═╝     ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝╚══════╝
                 ████████╗██████╗  █████╗  ██████╗██╗  ██╗███████╗██████╗ 
                 ╚══██╔══╝██╔══██╗██╔══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗
                    ██║   ██████╔╝███████║██║     █████╔╝ █████╗  ██████╔╝
                    ██║   ██╔══██╗██╔══██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗
                    ██║   ██║  ██║██║  ██║╚██████╗██║  ██╗███████╗██║  ██║
                    ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
    """

    # Create a gradient effect for the ASCII art
    lines = splash.split("\n")
    total_lines = len(lines)
    styled_text = Text()

    for i, line in enumerate(lines):
        if not line.strip():
            styled_text.append("\n")
            continue

        # Calculate gradient position (0.0 to 1.0)
        position = i / (total_lines - 1) if total_lines > 1 else 0

        # Create a gradient from cyan to purple
        if position < 0.5:
            # First half: bright cyan to medium blue
            t = position * 2  # Scale to 0-1 range
            r = int(0 + (64 * t))  # 0 to 64
            g = int(255 - (100 * t))  # 255 to 155
            b = int(255 - (20 * t))  # 255 to 235
        else:
            # Second half: medium blue to purple
            t = (position - 0.5) * 2  # Scale to 0-1 range
            r = int(64 + (191 * t))  # 64 to 255
            g = int(155 - (95 * t))  # 155 to 60
            b = int(235 - (15 * t))  # 235 to 220

        # Convert RGB to hex color code
        color = f"#{r:02x}{g:02x}{b:02x}"

        # Add the line with the calculated color
        styled_text.append(line, style=color)
        styled_text.append("\n")

    # Center the styled text directly without a panel
    console.print(Align.center(styled_text))

    # Centered text below splash
    console.print(
        "Your Digital Finance Tracker",
        style="bold cyan",
        justify="center",
    )
    console.print(
        "Version 1.0.1 By Your Name 🤓",
        style="cyan",
        justify="center",
    )

    # Add some space
    console.print("")

    # Create a simple loading message
    console.print(
        "Loading your financial data...",
        style="bold cyan",
        justify="center",
    )

    # Create a gradient progress bar
    console_width = console.width
    bar_width = min(60, console_width - 10)  # Max 60 chars or fit console

    # Function to get color at position
    def get_gradient_color(position):
        # Use the same gradient logic as for the splash text
        if position < 0.5:
            # First half: bright cyan to medium blue
            t = position * 2  # Scale to 0-1 range
            r = int(0 + (64 * t))  # 0 to 64
            g = int(255 - (100 * t))  # 255 to 155
            b = int(255 - (20 * t))  # 255 to 235
        else:
            # Second half: medium blue to purple
            t = (position - 0.5) * 2  # Scale to 0-1 range
            r = int(64 + (191 * t))  # 64 to 255
            g = int(155 - (95 * t))  # 155 to 60
            b = int(235 - (15 * t))  # 235 to 220
        return f"#{r:02x}{g:02x}{b:02x}"

    # Prepare an empty line for the progress bar (centered)
    empty_progress = " " * console_width
    console.print(Align.center(empty_progress), end="")

    # Save cursor position for progress bar updates
    # Use ANSI escape sequence to save cursor position
    print("\033[s", end="", flush=True)

    for i in range(101):
        # Create a styled progress bar text
        progress_bar = Text()

        filled_width = int(bar_width * (i / 100))
        empty_width = bar_width - filled_width

        # Add colored filled part with gradient
        for j in range(filled_width):
            # Calculate position in the gradient
            position = j / bar_width if bar_width > 0 else 0
            color = get_gradient_color(position)
            progress_bar.append("█", style=color)

        # Add empty part
        progress_bar.append("░" * empty_width, style="dim")

        # Create percentage text
        percentage = Text(f" {i:3d}%", style="bold cyan")

        # Combine into a full progress line
        full_line = Text("")
        full_line.append(progress_bar)
        full_line.append("")
        full_line.append(percentage)

        # Use ANSI escape sequence to restore cursor position
        print("\033[u", end="", flush=True)

        # Print centered progress bar (overwriting previous bar)
        console.print(Align.center(full_line), end="")

        time.sleep(0.02)

    # Add a new line after progress is complete
    console.print()

    # Press Enter prompt with style - without panel
    console.print("")  # Add some space
    console.print(
        "[bold]Press ENTER to continue[/bold]",
        style="bold cyan",
        justify="center",
    )
    input()


def get_monthly_summary():
    """Get monthly summary data from the database."""
    conn = sqlite3.connect("finance_manager.db")
    cursor = conn.cursor()

    # Get current month's data
    current_month = datetime.now().strftime("%Y-%m")

    # Get income
    cursor.execute(
        "SELECT SUM(amount) FROM transactions WHERE date LIKE ? AND type='income'",
        (f"{current_month}%",),
    )
    income = cursor.fetchone()[0] or 0

    # Get expenses
    cursor.execute(
        "SELECT SUM(amount) FROM transactions WHERE date LIKE ? AND type='expense'",
        (f"{current_month}%",),
    )
    expenses = cursor.fetchone()[0] or 0

    # Get balance
    balance = income - expenses

    # Get category breakdown
    cursor.execute(
        """
        SELECT category, SUM(amount) FROM transactions 
        WHERE date LIKE ? AND type='expense'
        GROUP BY category
        ORDER BY SUM(amount) DESC
    """,
        (f"{current_month}%",),
    )
    categories = cursor.fetchall()

    # Get budget vs actual
    cursor.execute(
        """
        SELECT b.category, b.monthly_limit, IFNULL(SUM(t.amount), 0) as spent
        FROM budget b
        LEFT JOIN transactions t ON b.category = t.category AND t.date LIKE ? AND t.type='expense'
        GROUP BY b.category
        ORDER BY (spent/b.monthly_limit) DESC
    """,
        (f"{current_month}%",),
    )
    budget_vs_actual = cursor.fetchall()

    conn.close()

    return {
        "income": income,
        "expenses": expenses,
        "balance": balance,
        "categories": categories,
        "budget_vs_actual": budget_vs_actual,
    }


def get_recent_transactions(limit=5):
    """Get the most recent transactions."""
    conn = sqlite3.connect("finance_manager.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT date, category, description, amount, type
        FROM transactions
        ORDER BY date DESC, id DESC
        LIMIT ?
    """,
        (limit,),
    )

    transactions = cursor.fetchall()
    conn.close()

    return transactions


def get_savings_goals():
    """Get the current savings goals and progress."""
    conn = sqlite3.connect("finance_manager.db")
    cursor = conn.cursor()

    cursor.execute("SELECT name, target_amount, current_amount, target_date FROM goals")
    goals = cursor.fetchall()

    conn.close()
    return goals


def format_currency(amount):
    """Format a number as currency with commas and two decimal places."""
    return f"${amount:,.2f}"


def display_dashboard():
    """Display the main dashboard with financial overview in monochrome style."""
    os.system("cls" if os.name == "nt" else "clear")

    # Update console width before displaying dashboard
    terminal_width, terminal_height = update_console_width()

    # Get data for dashboard
    monthly_data = get_monthly_summary()
    recent_transactions = get_recent_transactions()
    savings_goals = get_savings_goals()

    # Create layout
    layout = Layout()

    # Split screen into sections
    layout.split(Layout(name="header", size=3), Layout(name="main", ratio=1))

    # Split main area into columns
    # Adjust ratio based on terminal width
    # For narrower terminals, use a more vertical layout
    if terminal_width < 100:
        # More vertical layout for narrow terminals
        layout["main"].split(
            Layout(name="top", ratio=3), Layout(name="bottom", ratio=2)
        )

        # Split top into monthly summary and budget
        layout["top"].split(
            Layout(name="monthly_summary", ratio=1),
            Layout(name="budget_vs_actual", ratio=3),
        )

        # Split bottom into transactions and goals
        layout["bottom"].split(
            Layout(name="recent_transactions", ratio=1),
            Layout(name="savings_goals", ratio=1),
        )
    else:
        # Standard layout for wider terminals
        layout["main"].split_row(
            Layout(name="left", ratio=2), Layout(name="right", ratio=1)
        )

        # Split left column into top and bottom
        layout["left"].split(
            Layout(name="monthly_summary", ratio=1),
            Layout(name="budget_vs_actual", ratio=2),
        )

        # Split right column into top and bottom
        layout["right"].split(
            Layout(name="recent_transactions", ratio=1),
            Layout(name="savings_goals", ratio=1),
        )

    # Create header with current month and year - monochrome style
    current_month_year = datetime.now().strftime("%B %Y")
    current_date = datetime.now().strftime("%B %d, %Y")
    header_text = f"[bold #E0E0E0]🖥️  FINANCE TRACKER[/bold #E0E0E0] | [#BDBDBD]{current_date}[/#BDBDBD] | [#E0E0E0]Viewing: {current_month_year}[/#E0E0E0]"
    layout["header"].update(
        Panel(header_text, style="bold", box=box.ROUNDED, border_style="#7A7A7A")
    )

    # Using monochrome colors with semantic indicators
    income_color = "#66BB6A"  # Success green
    expenses_color = "#D32F2F"  # Error red
    balance_color = "#66BB6A" if monthly_data["balance"] >= 0 else "#D32F2F"

    income_formatted = format_currency(monthly_data["income"])
    expenses_formatted = format_currency(monthly_data["expenses"])
    balance_formatted = format_currency(monthly_data["balance"])

    savings_rate = 0
    if monthly_data["income"] > 0:
        savings_rate = (monthly_data["balance"] / monthly_data["income"]) * 100

    monthly_summary = Panel(
        Group(
            Text("📜 MONTHLY SUMMARY", style="bold #E0E0E0", justify="center"),
            Text(
                f"Income: {income_formatted}",
                style=f"bold {income_color}",
                justify="center",
            ),
            Text(
                f"Expenses: {expenses_formatted}",
                style=f"bold {expenses_color}",
                justify="center",
            ),
            Text(
                f"Balance: {balance_formatted}",
                style=f"bold {balance_color}",
                justify="center",
            ),
            Text(
                f"Savings Rate: {savings_rate:.1f}%",
                style=f"bold {'#66BB6A' if savings_rate > 20 else '#E6A23C' if savings_rate > 0 else '#D32F2F'}",
                justify="center",
            ),
        ),
        title="[bold #E0E0E0]Monthly Overview[/bold #E0E0E0]",
        border_style="#7A7A7A",
        box=box.ROUNDED,
    )
    layout["monthly_summary"].update(monthly_summary)

    # Create budget vs actual section with monochrome visuals
    budget_table = Table(
        show_header=True,
        header_style="bold #E0E0E0",
        title="🗒️ Budget vs. Actual",
        title_style="bold #E0E0E0",
        box=box.ROUNDED,
        expand=True,
        border_style="#7A7A7A",
    )
    budget_table.add_column("Category", style="#BDBDBD", overflow="fold")
    budget_table.add_column("Budget", justify="right", style="#E0E0E0")
    budget_table.add_column("Spent", justify="right", style="#E0E0E0")
    budget_table.add_column("Remaining", justify="right", style="#E0E0E0")

    # For narrow terminals, make progress bar narrower
    progress_width = 12 if terminal_width < 100 else 20
    budget_table.add_column(
        "Progress", justify="left", width=progress_width + 7
    )  # +7 for percentage

    for category, budget, spent in monthly_data["budget_vs_actual"]:
        remaining = budget - spent
        percentage = (spent / budget) * 100 if budget > 0 else 0

        # Monochrome progress indicators with semantic colors
        if percentage >= 100:
            progress_color = "#D32F2F"  # Error red
        elif percentage >= 90:
            progress_color = "#E6A23C"  # Warning yellow
        elif percentage >= 75:
            progress_color = "#BDBDBD"  # Neutral
        else:
            progress_color = "#66BB6A"  # Success green

        # Simplified progress bar with dynamic width
        filled_blocks = min(int(percentage / (100 / progress_width)), progress_width)
        progress_bar = "█" * filled_blocks + "░" * (progress_width - filled_blocks)

        budget_table.add_row(
            category,
            format_currency(budget),
            format_currency(spent),
            f"[{'#66BB6A' if remaining >= 0 else '#D32F2F'}]{format_currency(remaining)}[/{'#66BB6A' if remaining >= 0 else '#D32F2F'}]",
            f"[{progress_color}]{progress_bar}[/{progress_color}] {percentage:.1f}%\n ",  # Added newline and space for vertical padding
        )

    layout["budget_vs_actual"].update(
        Panel(budget_table, border_style="#7A7A7A", box=box.ROUNDED)
    )

    # Create recent transactions section with monochrome visuals
    transactions_table = Table(
        show_header=True,
        header_style="bold #E0E0E0",
        title_style="bold #E0E0E0",
        box=box.ROUNDED,
        expand=True,
        border_style="#7A7A7A",
    )
    transactions_table.add_column("Date", style="#7A7A7A", width=10)

    # For narrow terminals, optimize column widths
    if terminal_width < 100:
        transactions_table.add_column("Category", style="#BDBDBD", width=12)
        transactions_table.add_column("Description", style="#E0E0E0", width=15)
    else:
        transactions_table.add_column("Category", style="#BDBDBD")
        transactions_table.add_column("Description", style="#E0E0E0")

    transactions_table.add_column("Amount", justify="right")

    for date, category, description, amount, type_ in recent_transactions:
        amount_formatted = format_currency(amount)
        amount_color = "#66BB6A" if type_ == "income" else "#D32F2F"
        # Convert date to more readable format
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        friendly_date = date_obj.strftime("%b %d")

        # Adjust description length based on terminal width
        description_max_length = 12 if terminal_width < 100 else 20
        short_description = (
            description[:description_max_length] + "..."
            if len(description) > description_max_length
            else description
        )

        transactions_table.add_row(
            friendly_date,
            category,
            short_description,
            f"[{amount_color}]{amount_formatted}[/{amount_color}]",
        )

    layout["recent_transactions"].update(
        Panel(
            Group(
                transactions_table,
                Text(
                    "\n[#7A7A7A]Showing 5 most recent transactions[/#7A7A7A]",
                    justify="center",
                ),
            ),
            title="[bold #E0E0E0]🔍 Recent Transactions[/bold #E0E0E0]",
            border_style="#7A7A7A",
            box=box.ROUNDED,
        )
    )

    # Create savings goals section with monochrome visuals
    goals_table = Table(
        show_header=True,
        header_style="bold #E0E0E0",
        title_style="bold #E0E0E0",
        box=box.ROUNDED,
        expand=True,
        border_style="#7A7A7A",
    )
    goals_table.add_column("Goal", style="#BDBDBD")

    # Adjust progress bar width based on terminal width
    progress_width = 12 if terminal_width < 100 else 20
    goals_table.add_column("Progress", justify="center", style="#E0E0E0")
    goals_table.add_column("Due", style="#7A7A7A")

    for name, target, current, date in savings_goals:
        percentage = (current / target) * 100 if target > 0 else 0

        # Simplified progress bar in monochrome with dynamic width
        filled_blocks = min(int(percentage / (100 / progress_width)), progress_width)
        progress_bar = "█" * filled_blocks + "░" * (progress_width - filled_blocks)

        # Calculate days remaining
        target_date = datetime.strptime(date, "%Y-%m-%d")
        days_remaining = (target_date - datetime.now()).days

        # Friendly date format
        friendly_date = target_date.strftime("%b %d")

        # Color code based on progress
        if percentage >= 80:
            color = "#66BB6A"  # Success green
        elif percentage >= 50:
            color = "#BDBDBD"  # Neutral
        elif days_remaining < 30:
            color = "#D32F2F"  # Error red
        else:
            color = "#E6A23C"  # Warning yellow

        # For narrower terminals, adjust the display format
        if terminal_width < 100:
            goals_table.add_row(
                name,
                f"[{color}]{progress_bar}[/{color}] {percentage:.1f}%",
                f"{friendly_date}\n{days_remaining}d left",
            )
        else:
            goals_table.add_row(
                name,
                f"[{color}]{progress_bar}[/{color}] {percentage:.1f}%\n{format_currency(current)} of {format_currency(target)}",
                f"{friendly_date}\n[{'#66BB6A' if days_remaining > 30 else '#E6A23C' if days_remaining > 14 else '#D32F2F'}]{days_remaining} days left[/{'#66BB6A' if days_remaining > 30 else '#E6A23C' if days_remaining > 14 else '#D32F2F'}]",
            )

    layout["savings_goals"].update(
        Panel(
            goals_table,
            title="[bold #E0E0E0]ℹ️ Savings Goals[/bold #E0E0E0]",
            border_style="#7A7A7A",
            box=box.ROUNDED,
        )
    )

    # Render layout
    console.print(layout)

    # Show menu with monochrome layout
    console.print("\n")

    # For narrow terminals, display menu as a list
    if terminal_width < 100:
        menu_items = [
            "[1] [bold #E0E0E0]✏️ Add Transaction[/bold #E0E0E0]",
            "[2] [bold #E0E0E0]📊 View Reports[/bold #E0E0E0]",
            "[3] [bold #E0E0E0]💰 Manage Budget[/bold #E0E0E0]",
            "[4] [bold #E0E0E0]🎯 Manage Goals[/bold #E0E0E0]",
            "[5] [bold #E0E0E0]❌ Exit[/bold #E0E0E0]",
        ]
        menu_panel = Panel(
            "\n".join(menu_items),
            title="[bold #E0E0E0]Menu Options[/bold #E0E0E0]",
            border_style="#7A7A7A",
            box=box.ROUNDED,
        )
    else:
        # For wider terminals, display menu as columns
        menu_items = [
            "[1] [bold #E0E0E0]✏️ Add Transaction[/bold #E0E0E0]",
            "[2] [bold #E0E0E0]📊 View Reports[/bold #E0E0E0]",
            "[3] [bold #E0E0E0]💰 Manage Budget[/bold #E0E0E0]",
            "[4] [bold #E0E0E0]🎯 Manage Goals[/bold #E0E0E0]",
            "[5] [bold #E0E0E0]❌ Exit[/bold #E0E0E0]",
        ]
        menu_panel = Panel(
            Columns(menu_items, equal=True, expand=True),
            title="[bold #E0E0E0]Menu Options[/bold #E0E0E0]",
            border_style="#7A7A7A",
            box=box.ROUNDED,
        )

    console.print(menu_panel)

    # Clean footer with system status
    footer_text = Text.assemble(
        ("Status: Running", "italic #7A7A7A"),
        ("   |   ", "#BDBDBD"),
        ("Mode: Monochrome", "italic #7A7A7A"),
        ("   |   ", "#BDBDBD"),
        (
            "Terminal: " + str(terminal_width) + "x" + str(terminal_height),
            "italic #7A7A7A",
        ),
        ("   |   ", "#BDBDBD"),
        (datetime.now().strftime("%H:%M:%S"), "italic #7A7A7A"),
    )

    console.print(
        Panel(
            Align.center(footer_text),
            border_style="#7A7A7A",
            padding=(0, 2),
            expand=False,
        )
    )

    # Get user choice with monochrome prompt
    choice = Prompt.ask(
        "[bold #E0E0E0]> Select an option[/bold #E0E0E0]",
        choices=["1", "2", "3", "4", "5"],
        default="1",
    )
    handle_menu_choice(choice)


def handle_menu_choice(choice):
    """Handle the user's menu selection with monochrome styling."""
    # Update console width before menu handling
    update_console_width()

    if choice == "1":
        # Add transaction functionality
        with Progress(
            SpinnerColumn(),
            TextColumn(
                "[bold #E0E0E0]Loading Add Transaction screen...[/bold #E0E0E0]"
            ),
            console=console,
        ) as progress:
            task = progress.add_task("", total=100)
            for i in range(101):
                time.sleep(0.01)
                progress.update(task, completed=i)

        console.print(
            Panel(
                "[bold #E0E0E0]✏️ Add Transaction[/bold #E0E0E0] feature would be implemented here.",
                border_style="#7A7A7A",
                box=box.ROUNDED,
            )
        )
        time.sleep(1.5)
        display_dashboard()
    elif choice == "2":
        # View reports functionality
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold #E0E0E0]Loading Reports screen...[/bold #E0E0E0]"),
            console=console,
        ) as progress:
            task = progress.add_task("", total=100)
            for i in range(101):
                time.sleep(0.01)
                progress.update(task, completed=i)

        console.print(
            Panel(
                "[bold #E0E0E0]📊 View Reports[/bold #E0E0E0] feature would be implemented here.",
                border_style="#7A7A7A",
                box=box.ROUNDED,
            )
        )
        time.sleep(1.5)
        display_dashboard()
    elif choice == "3":
        # Manage budget functionality
        with Progress(
            SpinnerColumn(),
            TextColumn(
                "[bold #E0E0E0]Loading Budget Management screen...[/bold #E0E0E0]"
            ),
            console=console,
        ) as progress:
            task = progress.add_task("", total=100)
            for i in range(101):
                time.sleep(0.01)
                progress.update(task, completed=i)

        console.print(
            Panel(
                "[bold #E0E0E0]💰 Manage Budget[/bold #E0E0E0] feature would be implemented here.",
                border_style="#7A7A7A",
                box=box.ROUNDED,
            )
        )
        time.sleep(1.5)
        display_dashboard()
    elif choice == "4":
        # Manage goals functionality
        with Progress(
            SpinnerColumn(),
            TextColumn(
                "[bold #E0E0E0]Loading Goals Management screen...[/bold #E0E0E0]"
            ),
            console=console,
        ) as progress:
            task = progress.add_task("", total=100)
            for i in range(101):
                time.sleep(0.01)
                progress.update(task, completed=i)

        console.print(
            Panel(
                "[bold #E0E0E0]🎯 Manage Goals[/bold #E0E0E0] feature would be implemented here.",
                border_style="#7A7A7A",
                box=box.ROUNDED,
            )
        )
        time.sleep(1.5)
        display_dashboard()
    elif choice == "5":
        # Exit with animation
        os.system("cls" if os.name == "nt" else "clear")
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold #E0E0E0]Saving your financial data...[/bold #E0E0E0]"),
            console=console,
        ) as progress:
            task = progress.add_task("", total=100)
            for i in range(101):
                time.sleep(0.02)
                progress.update(task, completed=i)

        # Goodbye message with monochrome style
        os.system("cls" if os.name == "nt" else "clear")
        console.print("\n\n")
        console.print(
            Align.center(
                Panel(
                    Group(
                        Text(
                            "✔ THANK YOU FOR USING",
                            style="bold #E0E0E0",
                            justify="center",
                        ),
                        Text("Finance Tracker", style="bold #BDBDBD", justify="center"),
                        Text("\n", justify="center"),
                        Text(
                            "Your financial future is in good hands.",
                            style="italic #7A7A7A",
                            justify="center",
                        ),
                        Text("\n", justify="center"),
                        Text("See you soon!", style="bold #E0E0E0", justify="center"),
                    ),
                    border_style="#7A7A7A",
                    box=box.ROUNDED,
                    width=60,
                    padding=(1, 2),
                )
            )
        )
        return


def main():
    """Main function to run the application."""
    # Initialize the database
    create_database()

    # Add sample data for demonstration
    add_sample_data()

    # Display splash screen
    display_splash_screen()

    # Display main dashboard
    display_dashboard()


if __name__ == "__main__":
    main()
