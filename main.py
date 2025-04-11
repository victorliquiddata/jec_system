#!/usr/bin/env python3
"""
main.py — Entry point for Sistema JEC CLI >> TIME TO TEST THOROUGHLY THIS VERSION 1!!!!

Features:
- Guest menu (Login / Exit)
- Authenticated menu (CRUD usuários, trocar senha, logout, exit)
- Session timeout, login lockout
- Role-based access control for user management
- Audit logging for critical actions
"""

import time
from datetime import datetime, timedelta

from database import get_db_instance
from auth import auth_manager
from rich_cli import cli
from config import AppConfig
from logger import JCELogger


# Security / session settings
MAX_LOGIN_ATTEMPTS = 3
LOCKOUT_DURATION = 300  # seconds
SESSION_TIMEOUT = AppConfig.AUTH["session_timeout"]  # e.g. 1800 seconds


def main():
    logger = JCELogger()
    db = get_db_instance()

    login_attempts: dict[str, tuple[int, float]] = {}
    lockouts: dict[str, float] = {}

    last_activity = datetime.now()

    try:
        while True:
            cli.clear_screen()
            cli.display_header("Sistema JEC")

            user = auth_manager.get_current_user()
            now_ts = time.time()

            # --- Guest flow ---
            if not user:
                options = [{"description": "Login"}, {"description": "Exit"}]
                cli.display_main_menu(options)
                choice = cli.prompt_input("Choose an option", int)

                if choice == 1:
                    email = cli.prompt_input("Email")
                    if email in lockouts and now_ts < lockouts[email]:
                        remaining = int(lockouts[email] - now_ts)
                        cli.display_status(
                            f"Account locked. Try again in {remaining}s", "error"
                        )
                        time.sleep(2)
                        continue

                    password = cli.prompt_input("Password", password=True)
                    success = auth_manager.login(email, password)

                    if success:
                        user = auth_manager.get_current_user()
                        cli.user_context = user
                        last_activity = datetime.now()
                        cli.display_status("Login successful", "success")
                        time.sleep(1)
                    else:
                        count, first_ts = login_attempts.get(email, (0, now_ts))
                        count += 1
                        login_attempts[email] = (count, first_ts)
                        cli.display_status("Login failed", "error")

                        if count >= MAX_LOGIN_ATTEMPTS:
                            lockouts[email] = now_ts + LOCKOUT_DURATION
                            cli.display_status(
                                f"Too many attempts. Locked for {LOCKOUT_DURATION}s",
                                "error",
                            )
                        time.sleep(2)

                elif choice == 2:
                    cli.display_status("Exiting...", "info")
                    break

                else:
                    cli.display_status("Invalid option", "warning")
                    time.sleep(1)

            # --- Authenticated flow ---
            else:
                if datetime.now() - last_activity > timedelta(seconds=SESSION_TIMEOUT):
                    cli.display_status("Session expired due to inactivity", "warning")
                    auth_manager.logout()
                    cli.user_context = None
                    continue

                options = [
                    {"description": "List users"},
                    {"description": "Create user"},
                    {"description": "Update user"},
                    {"description": "Delete user"},
                    {"description": "Change password"},
                    {"description": "Logout"},
                    {"description": "Exit"},
                ]
                cli.display_main_menu(options)
                choice = cli.prompt_input("Choose an option", int)
                last_activity = datetime.now()
                perfil = user.get("tipo", "")

                # 1. List users
                if choice == 1:
                    try:
                        users = db.execute_query(
                            "SELECT id, email, tipo FROM usuarios", return_results=True
                        )
                        cli.display_data_table(users, title="Usuários")
                        cli.prompt_input("\nPress Enter to return to the menu...")
                    except Exception as e:
                        cli.display_status(f"Error fetching users: {str(e)}", "error")

                # 2. Create user
                elif choice == 2:
                    if perfil not in ("servidor", "juiz"):
                        cli.display_status("Permission denied", "error")
                    else:
                        # Collect all required fields
                        new_cpf = cli.prompt_input("CPF (11 digits)")
                        new_nome = cli.prompt_input("Full name")
                        new_email = cli.prompt_input("Email")

                        # Validate CPF format (basic check)
                        while not (new_cpf.isdigit() and len(new_cpf) == 11):
                            cli.display_status("CPF must be 11 digits", "warning")
                            new_cpf = cli.prompt_input("CPF (11 digits)")

                        # Password validation
                        while True:
                            new_password = cli.prompt_input("Password", password=True)
                            valid, reason = auth_manager.validate_password_complexity(
                                new_password
                            )
                            if not valid:
                                cli.display_status(reason, "warning")
                            else:
                                break

                        new_perfil = cli.prompt_input(
                            "Profile type (advogado/servidor/juiz/etc)"
                        )

                        # Handle optional phone number
                        cli.display_status("Phone number (press Enter to skip)", "info")
                        new_telefone = cli.prompt_input("Phone number")
                        new_telefone = new_telefone if new_telefone else None

                        hashed = auth_manager.hash_password(new_password)
                        try:
                            db.execute_query(
                                """INSERT INTO usuarios 
                                (cpf, nome_completo, email, senha, tipo, telefone) 
                                VALUES (%s, %s, %s, %s, %s, %s)""",
                                (
                                    new_cpf,
                                    new_nome,
                                    new_email,
                                    hashed,
                                    new_perfil,
                                    new_telefone,
                                ),
                            )
                            cli.display_status("User created successfully", "success")
                            logger.log_negocio(
                                "auth",
                                "user_create",
                                {
                                    "email": new_email,
                                    "perfil": new_perfil,
                                    "cpf": new_cpf[:3]
                                    + "***",  # Log partial CPF for privacy
                                },
                                "info",
                            )
                        except Exception as e:
                            cli.display_status(
                                f"Error creating user: {str(e)}", "error"
                            )

                # 3. Update user
                elif choice == 3:
                    if perfil not in ("servidor", "juiz"):
                        cli.display_status("Permission denied", "error")
                    else:
                        # Change prompt to accept string instead of int for UUID
                        user_id = cli.prompt_input("User ID to update")
                        exists = db.execute_query(
                            "SELECT id FROM usuarios WHERE id=%s::uuid",
                            (user_id,),
                            return_results=True,
                        )
                        if not exists:
                            cli.display_status("User not found", "warning")
                        else:
                            new_email = cli.prompt_input("New email")
                            new_perfil = cli.prompt_input("New perfil")
                            try:
                                db.execute_query(
                                    "UPDATE usuarios SET email=%s, tipo=%s WHERE id=%s::uuid",
                                    (new_email, new_perfil, user_id),
                                )
                                cli.display_status("User updated", "success")
                                logger.log_negocio(
                                    "auth",
                                    "user_update",
                                    {
                                        "user_id": user_id,
                                        "email": new_email,
                                        "perfil": new_perfil,
                                    },
                                    "info",
                                )
                            except Exception as e:
                                cli.display_status(
                                    f"Error updating user: {str(e)}", "error"
                                )

                # 4. Delete user
                elif choice == 4:
                    if perfil not in ("servidor", "juiz"):
                        cli.display_status("Permission denied", "error")
                    else:
                        # Remove int type constraint since we're using UUIDs
                        user_id = cli.prompt_input("User ID to delete (UUID)")
                        exists = db.execute_query(
                            "SELECT id FROM usuarios WHERE id=%s::uuid",  # Add UUID cast
                            (user_id,),
                            return_results=True,
                        )
                        if not exists:
                            cli.display_status("User not found", "warning")
                        else:
                            confirm = cli.prompt_input(
                                f"Type 'YES' to confirm deletion of user {user_id}"
                            )
                            if confirm.upper() == "YES":
                                try:
                                    # Delete related audit_log entries first to avoid FK constraint
                                    db.execute_query(
                                        "DELETE FROM audit_log WHERE user_id = %s::uuid",
                                        (user_id,),
                                    )
                                    # Then delete the user
                                    db.execute_query(
                                        "DELETE FROM usuarios WHERE id = %s::uuid",
                                        (user_id,),
                                    )
                                    cli.display_status("User deleted", "success")
                                    logger.log_negocio(
                                        "auth",
                                        "user_delete",
                                        {"user_id": user_id},
                                        "info",
                                    )
                                except Exception as e:
                                    cli.display_status(
                                        f"Error deleting user: {str(e)}", "error"
                                    )
                            else:
                                cli.display_status("Deletion cancelled", "info")

                # 5. Change password (self-service)
                elif choice == 5:
                    old = cli.prompt_input("Current password", password=True)
                    if not auth_manager.verify_password(user["senha"], old):
                        cli.display_status("Incorrect current password", "error")
                    else:
                        while True:
                            new_pw = cli.prompt_input("New password", password=True)
                            valid, reason = auth_manager.validate_password_complexity(
                                new_pw
                            )
                            if not valid:
                                cli.display_status(reason, "warning")
                            else:
                                break
                        hashed = auth_manager.hash_password(new_pw)
                        try:
                            db.execute_query(
                                "UPDATE usuarios SET senha=%s WHERE id=%s",
                                (hashed, user["id"]),
                            )
                            cli.display_status("Password changed", "success")
                            logger.log_negocio(
                                "auth",
                                "password_change",
                                {"user_id": user["id"]},
                                "info",
                            )
                        except Exception as e:
                            cli.display_status(
                                f"Error changing password: {str(e)}", "error"
                            )

                # 6. Logout
                elif choice == 6:
                    auth_manager.logout()
                    cli.user_context = None
                    cli.display_status("Logged out", "info")
                    time.sleep(1)

                # 7. Exit
                elif choice == 7:
                    cli.display_status("Exiting...", "info")
                    break

                else:
                    cli.display_status("Invalid option", "warning")

                time.sleep(1)

        cli.clear_screen()
        cli.display_status("Goodbye!", "info")

    except KeyboardInterrupt:
        cli.clear_screen()
        cli.display_status("Interrupted. Goodbye!", "warning")


if __name__ == "__main__":
    main()
