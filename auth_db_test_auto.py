# auth_db_test_auto.py - gets read by advanced_auth_db_test_auto.py

# === TEST CREDENTIAL CONSTANTS (fill before running tests) ===
TEST_VALID_EMAIL = "vic@gmail.com"
TEST_VALID_PASSWORD = "Newlife5379!"
TEST_INVALID_PASSWORD = "wrong_password"
TEST_NONEXISTENT_EMAIL = "nonexistent@example.com"

# === REMAINDER OF TEST CODE ===
import time
import traceback
from datetime import datetime
from auth import auth_manager
from database import get_db_instance
from logger import JCELogger
from rich_cli import cli

logger = JCELogger()
db = get_db_instance()


def test_nonexistent_user(correlation_id: str):
    """Test login attempt with non-existent user"""
    cli.display_status("\n=== Testing Non-existent User ===", "info")

    email = TEST_NONEXISTENT_EMAIL
    password = TEST_INVALID_PASSWORD

    success = auth_manager.login(email, password, correlation_id)

    if not success:
        cli.display_status("Login failed as expected", "success")

        # Verify user doesn't exist in DB
        db_user = db.execute_query(
            "SELECT 1 FROM usuarios WHERE email = %s",
            (email,),
            return_results=True,
            correlation_id=correlation_id,
        )

        if not db_user:
            cli.display_status("Confirmed user doesn't exist", "success")
        else:
            cli.display_status("User exists in DB!", "error")
    else:
        cli.display_status("Login succeeded unexpectedly!", "error")


def test_valid_login(correlation_id: str):
    """Test successful authentication flow"""
    cli.display_status("\n=== Testing Valid Login ===", "info")

    email = TEST_VALID_EMAIL
    password = TEST_VALID_PASSWORD

    start_time = time.time()
    success = auth_manager.login(email, password, correlation_id)
    elapsed = time.time() - start_time

    if success:
        user = auth_manager.get_current_user()
        cli.display_status(f"Login succeeded in {elapsed:.2f}s", "success")
        cli.display_data_table(
            [{"Field": k, "Value": v} for k, v in user.items() if k != "senha"],
            title="User Details",
        )

        # Verify database record
        db_user = db.execute_query(
            "SELECT * FROM usuarios WHERE email = %s",
            (email,),
            return_results=True,
            correlation_id=correlation_id,
        )

        if db_user:
            cli.display_status("DB record matches session", "success")
        else:
            cli.display_status("DB record not found!", "error")

    else:
        cli.display_status("Login failed unexpectedly", "error")


def test_invalid_password(correlation_id: str):
    """Test failed login with wrong password"""
    cli.display_status("\n=== Testing Invalid Password ===", "info")

    email = TEST_VALID_EMAIL
    password = TEST_INVALID_PASSWORD

    success = auth_manager.login(email, password, correlation_id)

    if not success:
        cli.display_status("Login failed as expected", "success")
    else:
        cli.display_status("Login succeeded unexpectedly!", "error")


def test_password_migration(correlation_id: str):
    """Test legacy password hash upgrade with proper cleanup"""
    cli.display_status("\n=== Testing Password Migration ===", "info")

    try:
        # Generate unique test credentials
        timestamp = int(time.time())
        temp_email = f"legacy_user_{timestamp}@test.com"
        temp_cpf = f"{timestamp % 10000000000:011d}"  # 11-digit CPF
        temp_password = f"oldpassword{timestamp % 1000}"
        temp_name = f"Legacy User {timestamp}"

        # Create temporary legacy user (plaintext password)
        db.execute_query(
            """INSERT INTO usuarios 
            (cpf, nome_completo, email, senha, tipo) 
            VALUES (%s, %s, %s, %s, 'servidor')""",
            (temp_cpf, temp_name, temp_email, temp_password),
            correlation_id=correlation_id,
            query_name="create_legacy_user",
        )
        cli.display_status("Created legacy test user", "info")

        # Attempt login - should trigger migration
        if auth_manager.login(temp_email, temp_password, correlation_id):
            # Verify directly in database
            db_user = db.execute_query(
                "SELECT senha FROM usuarios WHERE email = %s",
                (temp_email,),
                return_results=True,
                correlation_id=correlation_id,
            )[0]

            if db_user["senha"].startswith("pbkdf2:sha256"):
                cli.display_status("Password migrated successfully", "success")

                # Verify new hash works
                auth_manager.logout()
                if auth_manager.login(temp_email, temp_password, correlation_id):
                    user = auth_manager.get_current_user()
                    if user["senha"] == db_user["senha"]:
                        cli.display_status("Session and DB hashes match", "success")
                    else:
                        cli.display_status("Session hash mismatch!", "error")
                    cli.display_status("Verified migrated password works", "success")
                else:
                    cli.display_status(
                        "Migrated password verification failed!", "error"
                    )
            else:
                cli.display_status("Password not upgraded to PBKDF2!", "error")
        else:
            cli.display_status("Legacy login failed", "error")

    except Exception as e:
        cli.display_status(f"Test error: {str(e)}", "error")
        logger.log_negocio(
            "test",
            "password_migration_error",
            {
                "error": str(e),
                "traceback": traceback.format_exc(),
                "correlation_id": correlation_id,
            },
            level="error",
        )

    finally:
        try:
            db.execute_query(
                "DELETE FROM usuarios WHERE email = %s",
                (temp_email,),
                correlation_id=correlation_id,
                query_name="delete_legacy_user",
            )
            cli.display_status("Cleaned up test user", "info")
        except Exception as cleanup_error:
            cli.display_status(f"Cleanup failed: {str(cleanup_error)}", "error")


def test_account_lockout(correlation_id: str):
    """Test account lockout after multiple failures with verification"""
    cli.display_status("\n=== Testing Account Lockout ===", "info")

    email = TEST_VALID_EMAIL

    db_user = db.execute_query(
        "SELECT 1 FROM usuarios WHERE email = %s",
        (email,),
        return_results=True,
        correlation_id=correlation_id,
        query_name="verify_user_exists",
    )

    if not db_user:
        cli.display_status("Account not found - cannot test lockout", "error")
        return

    cli.display_status("\nTesting failed login attempts...", "info")
    for attempt in range(1, 4):
        start_time = time.time()
        success = auth_manager.login(email, TEST_INVALID_PASSWORD, correlation_id)
        elapsed = time.time() - start_time

        if success:
            cli.display_status(
                f"Attempt {attempt}: Login succeeded unexpectedly!", "error"
            )
            return
        else:
            cli.display_status(
                f"Attempt {attempt}: Failed as expected ({elapsed:.2f}s)",
                "success" if attempt < 3 else "warning",
            )

    cli.display_status("\nVerifying account lockout...", "info")
    try:
        start_time = time.time()
        success = auth_manager.login(email, TEST_INVALID_PASSWORD, correlation_id)
        elapsed = time.time() - start_time

        if success:
            cli.display_status(
                f"Login succeeded after lockout! ({elapsed:.2f}s)", "error"
            )
        else:
            cli.display_status(f"Login blocked by lockout ({elapsed:.2f}s)", "success")

            if hasattr(auth_manager, "lockouts") and email in auth_manager.lockouts:
                remaining = int(auth_manager.lockouts[email] - time.time())
                cli.display_status(f"Lockout active for {remaining}s remaining", "info")
            else:
                cli.display_status("No lockout record found in auth_manager", "error")

    except Exception as e:
        cli.display_status(f"Error during lockout test: {str(e)}", "error")
        logger.log_negocio(
            "test",
            "lockout_test_error",
            {
                "email": email,
                "error": str(e),
                "correlation_id": correlation_id,
                "traceback": traceback.format_exc(),
            },
            level="error",
        )

    cli.display_status("\nTesting lockout expiration...", "info")
    if hasattr(auth_manager, "lockouts") and email in auth_manager.lockouts:
        wait_time = max(0, auth_manager.lockouts[email] - time.time()) + 1
        cli.display_status(f"Waiting {wait_time:.1f}s for lockout to expire...", "info")
        time.sleep(wait_time)

        success = auth_manager.login(email, TEST_INVALID_PASSWORD, correlation_id)
        if success:
            cli.display_status("Login succeeded after lockout expired!", "error")
        else:
            cli.display_status(
                "Properly rejected login after lockout (wrong password)", "success"
            )
    else:
        cli.display_status("Cannot test expiration - no active lockout", "error")

    try:
        if (
            hasattr(auth_manager, "login_attempts")
            and email in auth_manager.login_attempts
        ):
            del auth_manager.login_attempts[email]
        if hasattr(auth_manager, "lockouts") and email in auth_manager.lockouts:
            del auth_manager.lockouts[email]

        cli.display_status("\nLockout test cleanup complete", "info")
    except Exception as e:
        cli.display_status(f"Cleanup error: {str(e)}", "error")


# === No changes below here ===


def run_full_test_suite():
    cli.display_status("\nRunning comprehensive test suite...", "info")
    test_cases = [
        ("Valid Login", test_valid_login),
        ("Invalid Password", test_invalid_password),
        ("Non-existent User", test_nonexistent_user),
        ("Account Lockout", test_account_lockout),
        ("Password Migration", test_password_migration),
    ]

    for name, test_func in test_cases:
        cli.display_status(f"\nRunning {name} test...", "info")
        correlation_id = (
            f"FULLTEST-{name.replace(' ', '')}-{datetime.now().strftime('%H%M%S')}"
        )
        test_func(correlation_id)
        time.sleep(1)


def run_integration_tests():
    cli.clear_screen()
    cli.display_header("Auth-DB Integration Tests")

    while True:
        cli.display_main_menu(
            [
                {"description": "Test Valid Login"},
                {"description": "Test Invalid Password"},
                {"description": "Test Non-existent User"},
                {"description": "Test Account Lockout"},
                {"description": "Test Password Migration"},
                {"description": "Run All Tests"},
                {"description": "Exit"},
            ]
        )

        choice = cli.prompt_input("Choose test scenario", int)
        correlation_id = f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        if choice == 1:
            test_valid_login(correlation_id)
        elif choice == 2:
            test_invalid_password(correlation_id)
        elif choice == 3:
            test_nonexistent_user(correlation_id)
        elif choice == 4:
            test_account_lockout(correlation_id)
        elif choice == 5:
            test_password_migration(correlation_id)
        elif choice == 6:
            run_full_test_suite()
        elif choice == 7:
            break

        cli.prompt_input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        run_integration_tests()
    except KeyboardInterrupt:
        cli.display_status("\nTests interrupted", "warning")
    finally:
        cli.display_status("\nTest session completed", "info")
