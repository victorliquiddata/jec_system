# advanced_auth_db_test.py
import time
import traceback
from datetime import datetime, timedelta
from auth import auth_manager
from database import get_db_instance
from logger import JCELogger
from rich_cli import cli
from config import AppConfig
from logging_context import LoggingContext

# Import previous test functions
from auth_db_test import (
    test_nonexistent_user,
    test_valid_login,
    test_invalid_password,
    test_password_migration,
    test_account_lockout,
)


logger = JCELogger()
db = get_db_instance()

# ----------------------------
# New Integration Test Cases
# ----------------------------


def test_role_based_access(correlation_id: str):
    """Verify role-based permission system"""
    cli.display_status("\n=== Testing Role-Based Access ===", "info")

    # Get test credentials
    email = cli.prompt_input("Enter user email to test permissions")
    password = cli.prompt_input("Enter password", password=True)

    if auth_manager.login(email, password, correlation_id):
        user = auth_manager.get_current_user()
        cli.display_data_table(
            [
                {
                    "Permission": "User Management",
                    "Expected": "❌" if user["tipo"] in ["advogado", "parte"] else "✅",
                }
            ],
            title=f"Access Checks for {user['tipo']}",
        )

        # Verify database permissions
        db_access = auth_manager.check_permission("db_query_execution")
        cli.display_status(
            f"Database access {'granted' if db_access else 'denied'} as expected",
            (
                "success"
                if db_access == (user["tipo"] in ["servidor", "juiz"])
                else "error"
            ),
        )
    else:
        cli.display_status("Login failed - cannot test permissions", "error")


def test_session_timeout(correlation_id: str):
    """Test session expiration after inactivity (debug version)"""
    cli.display_status("\n=== Testing Session Timeout ===", "info")

    email = cli.prompt_input("Enter email for session test")
    password = cli.prompt_input("Enter password", password=True)

    if auth_manager.login(email, password, correlation_id):
        # Debug 1: Print initial session state
        user = auth_manager.get_current_user()
        cli.display_status(f"Initial session: {user['email']}", "debug")

        # Force expiration
        auth_manager.current_user = None
        cli.user_context = None
        cli.display_status("Session manually expired", "debug")

        # Debug 2: Verify auth state
        cli.display_status(
            f"Post-clear auth state: {auth_manager.current_user is None}", "debug"
        )

        # Debug 3: Check permissions directly
        try:
            can_list = auth_manager.check_permission("user_management")
            cli.display_status(f"Permission check: {can_list}", "debug")
        except Exception as e:
            cli.display_status(f"Permission check failed: {str(e)}", "debug")

        # Debug 4: Database connection info
        db_metrics = db.get_metrics()
        cli.display_status(
            f"DB connections: {db_metrics['active_connections']} active", "debug"
        )

        # Attempt protected action
        try:
            cli.display_status("Attempting query...", "debug")
            result = db.execute_query(
                "SELECT id, email FROM usuarios",
                return_results=True,
                correlation_id=correlation_id,
            )
            cli.display_status(f"Query returned {len(result)} rows", "debug")
            cli.display_status("Session remained active!", "error")

        except Exception as e:
            cli.display_status(f"Query error: {str(e)}", "debug")
            if "permission" in str(e).lower():
                cli.display_status("Session properly expired", "success")
            else:
                cli.display_status(f"Unexpected error: {str(e)}", "error")
    else:
        cli.display_status("Initial login failed", "error")


def test_password_complexity(correlation_id: str):
    """Validate password policy enforcement"""
    cli.display_status("\n=== Testing Password Complexity ===", "info")

    test_cases = [
        ("Short", "A1!a", False),
        ("No upper", "a1!aaaaa", False),
        ("Valid", "A1!aaaaa", True),
    ]

    for name, password, expected in test_cases:
        valid, reason = auth_manager.validate_password_complexity(password)
        result = "✅" if valid == expected else "❌"
        cli.display_data_table(
            [{"Case": name, "Password": password, "Result": result}],
            title="Complexity Check Results",
        )


def test_full_user_lifecycle(correlation_id: str):
    """Test complete user creation/update/deletion cycle"""
    cli.display_status("\n=== Testing User Lifecycle ===", "info")

    try:
        # Create
        test_email = f"testuser_{int(time.time())}@example.com"
        db.execute_query(
            """INSERT INTO usuarios (cpf, nome_completo, email, senha, tipo)
            VALUES (%s, %s, %s, %s, %s)""",
            ("00000000001", "Test User", test_email, "TempPass123!", "servidor"),
            correlation_id=correlation_id,
        )
        cli.display_status("User created", "success")

        # Update
        new_name = "Updated Test User"
        db.execute_query(
            "UPDATE usuarios SET nome_completo = %s WHERE email = %s",
            (new_name, test_email),
            correlation_id=correlation_id,
        )
        cli.display_status("User updated", "success")

        # Delete
        db.execute_query(
            "DELETE FROM usuarios WHERE email = %s",
            (test_email,),
            correlation_id=correlation_id,
        )
        cli.display_status("User deleted", "success")

    except Exception as e:
        cli.display_status(f"Lifecycle test failed: {str(e)}", "error")
        logger.log_negocio(
            "test",
            "user_lifecycle_failure",
            {"error": str(e), "traceback": traceback.format_exc()},
            level="error",
        )


# ----------------------------
# Test Orchestration
# ----------------------------


def run_full_test_suite():
    """Execute all tests with predefined credentials"""
    cli.display_status("\nRunning Comprehensive Test Suite...", "info")
    test_cases = [
        ("Role-Based Access", test_role_based_access),
        ("Session Timeout", test_session_timeout),
        ("Password Complexity", test_password_complexity),
        ("User Lifecycle", test_full_user_lifecycle),
        # Include previous tests
        ("Valid Login", test_valid_login),
        ("Invalid Password", test_invalid_password),
        ("Non-existent User", test_nonexistent_user),
        ("Account Lockout", test_account_lockout),
        ("Password Migration", test_password_migration),
    ]

    for name, test_func in test_cases:
        cli.display_status(f"\nRunning {name} Test...", "info")
        correlation_id = (
            f"FULLTEST-{name.replace(' ', '')}-{datetime.now().strftime('%H%M%S')}"
        )
        test_func(correlation_id)
        time.sleep(1)


def run_integration_tests():
    """Main test runner with user interaction"""
    cli.clear_screen()
    cli.display_header("Advanced Auth-DB Integration Tests")

    while True:
        cli.display_main_menu(
            [
                {"description": "Test Role-Based Access"},
                {"description": "Test Session Timeout"},
                {"description": "Test Password Complexity"},
                {"description": "Test User Lifecycle"},
                {"description": "Run All Tests"},
                {"description": "Exit"},
            ]
        )

        choice = cli.prompt_input("Choose test scenario", int)
        correlation_id = f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        test_map = {
            1: test_role_based_access,
            2: test_session_timeout,
            3: test_password_complexity,
            4: test_full_user_lifecycle,
            5: run_full_test_suite,
            6: lambda _: None,
        }

        if choice == 6:
            break

        if choice in test_map:
            if choice == 5:
                test_map[choice]()
            else:
                test_map[choice](correlation_id)

        cli.prompt_input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        run_integration_tests()
    except KeyboardInterrupt:
        cli.display_status("\nTests interrupted", "warning")
    finally:
        cli.display_status("\nAdvanced test session completed", "info")
