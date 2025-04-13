"""
advanced_auth_db_test_auto.py
------------------------

Advanced integration tests for the authentication and database layers of the Sistema JEC.

This suite expands on core authentication scenarios with tests for permission handling,
session management, password policies, and end-to-end user lifecycle validation.

Modules Used:
- auth.auth_manager: Handles login, user sessions, and permission checks.
- database: Database interface for executing queries.
- logger: Custom logger for structured event logging.
- config: Application configuration including session timeout settings.
- rich_cli: CLI interface using Rich for enhanced UX.
- logging_context: Adds contextual info for traceability.

Imported Test Cases (from auth_db_test.py):
- test_valid_login
- test_invalid_password
- test_nonexistent_user
- test_password_migration
- test_account_lockout

New Integration Test Cases:
- test_role_based_access: Validates permission access based on user role (advogado, servidor, juiz, etc.).
- test_session_timeout: Ensures session expires after configured inactivity period.
- test_password_complexity: Checks password policy enforcement (length, character types).
- test_full_user_lifecycle: Verifies full cycle of creating, updating, and deleting a user.

To execute interactively, run this file directly:
$ python advanced_auth_db_test.py
"""

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
from auth_db_test_auto import (
    test_valid_login,
    test_invalid_password,
    test_nonexistent_user,
    test_account_lockout,
    test_password_migration,
)

# ----------------------------
# Test Constants (for automation)
# ----------------------------

TEST_EMAIL = "vic@gmail.com"
TEST_PASSWORD = "Newlife5379!"
SESSION_TEST_EMAIL = "vic@gmail.com"
SESSION_TEST_PASSWORD = "Newlife5379!"
SESSION_TEST_TIMEOUT = 60  # seconds


logger = JCELogger()
db = get_db_instance()

# ----------------------------
# New Integration Test Cases
# ----------------------------


def test_role_based_access(correlation_id: str):
    """Verify role-based permission system"""
    cli.display_status("\n=== Testing Role-Based Access ===", "info")

    if auth_manager.login(TEST_EMAIL, TEST_PASSWORD, correlation_id):
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
    """Test session expiration after inactivity"""
    cli.display_status("\n=== Testing Session Timeout ===", "info")

    try:
        original_timeout = AppConfig.AUTH["session_timeout"]
        AppConfig.AUTH["session_timeout"] = SESSION_TEST_TIMEOUT

        if auth_manager.login(
            SESSION_TEST_EMAIL, SESSION_TEST_PASSWORD, correlation_id
        ):
            cli.display_status("Session active, waiting for timeout...", "info")

            for i in range(SESSION_TEST_TIMEOUT + 5):
                time.sleep(1)
                cli.display_progress(
                    f"⏳ Timeout in: {SESSION_TEST_TIMEOUT + 5 - i}s remaining",
                    "yellow",
                )

            cli.display_progress(" " * 50)  # Clear line

            if auth_manager.get_current_user():
                cli.display_status("Session remained active!", "error")
            else:
                cli.display_status("Session expired correctly", "success")

            AppConfig.AUTH["session_timeout"] = original_timeout
        else:
            cli.display_status("Initial login failed", "error")

    except Exception as e:
        cli.display_status(f"Test error: {str(e)}", "error")
        logger.log_negocio(
            "test",
            "session_timeout_error",
            {
                "error": str(e),
                "traceback": traceback.format_exc(),
                "correlation_id": correlation_id,
            },
            level="error",
        )


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
        test_email = f"testuser_{int(time.time())}@example.com"
        db.execute_query(
            """INSERT INTO usuarios (cpf, nome_completo, email, senha, tipo)
            VALUES (%s, %s, %s, %s, %s)""",
            ("00000000001", "Test User", test_email, "TempPass123!", "servidor"),
            correlation_id=correlation_id,
        )
        cli.display_status("User created", "success")

        new_name = "Updated Test User"
        db.execute_query(
            "UPDATE usuarios SET nome_completo = %s WHERE email = %s",
            (new_name, test_email),
            correlation_id=correlation_id,
        )
        cli.display_status("User updated", "success")

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
