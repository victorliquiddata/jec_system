# main.py

import time
from datetime import datetime, timedelta
import traceback
import json
import re
from database import get_db_instance
from auth import auth_manager
from rich_cli import cli
from config import AppConfig
from logger import JCELogger

from typing import Dict, List, Optional
from logging_context import LoggingContext  # Add this import

# Add to existing imports
from db_mgmt.data_preview import DataPreviewService
from db_mgmt.services.validation import DBMgmtValidator

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
    current_correlation_id: Optional[str] = None  # Track active correlation ID

    try:
        while True:
            cli.clear_screen()
            cli.display_header("Sistema JEC")

            # Generate new correlation ID for guest actions
            if not auth_manager.get_current_user():
                current_correlation_id = (
                    AppConfig.generate_correlation_id()
                    if AppConfig.LOGGING["enable_correlation"]
                    else None
                )
                LoggingContext.set_correlation_id(current_correlation_id)

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

                    # Pass correlation ID to auth system
                    success = auth_manager.login(
                        email, password, correlation_id=current_correlation_id
                    )

                    if success:
                        user = auth_manager.get_current_user()
                        # Store correlation ID in user context
                        cli.user_context = {
                            **user,
                            "correlation_id": current_correlation_id,
                        }
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
                # Get correlation ID from user context
                current_correlation_id = cli.user_context.get("correlation_id")

                # Session timeout check with correlation context
                if datetime.now() - last_activity > timedelta(seconds=SESSION_TIMEOUT):
                    cli.display_status("Session expired due to inactivity", "warning")
                    auth_manager.logout(correlation_id=current_correlation_id)
                    cli.user_context = None
                    continue

                # In the authenticated flow section (else block):
                options = [
                    {"description": "List users"},
                    {"description": "Create user"},
                    {"description": "Update user"},
                    {"description": "Delete user"},
                    {"description": "Change password"},
                    {"description": "Database Management"},  # New option
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
                        # Execute query with proper error handling
                        result = db.execute_query(
                            "SELECT id, email, tipo FROM usuarios ORDER BY email",
                            return_results=True,
                            correlation_id=current_correlation_id,
                            query_name="list_users",
                        )

                        if not result:
                            cli.display_status("No users found", "info")
                            logger.log_negocio(
                                "user",
                                "list_empty",
                                {"correlation_id": current_correlation_id},
                                level="info",
                            )
                        else:
                            # Transform results for display
                            users = [
                                {
                                    "ID": str(user["id"]),
                                    "Email": user["email"],
                                    "Tipo": user["tipo"],
                                }
                                for user in result
                            ]

                            cli.display_data_table(
                                users,
                                title="Usuários",
                                metadata={
                                    "correlation_id": current_correlation_id,
                                    "count": len(users),
                                },
                            )

                        cli.prompt_input("\nPress Enter to continue...")

                    except Exception as e:
                        error_msg = f"Database error: {str(e)}"
                        cli.display_status(error_msg, "error")
                        logger.log_negocio(
                            "user",
                            "list_failed",
                            {
                                "error": str(e),
                                "correlation_id": current_correlation_id,
                                "traceback": traceback.format_exc(),
                            },
                            level="error",
                        )
                        time.sleep(2)  # Give user time to read error

                # 2. Create user
                elif choice == 2:  # Create user
                    if not auth_manager.check_permission("user_management"):
                        cli.display_status("Permission denied", "error")
                        logger.log_negocio(
                            "auth",
                            "permission_denied",
                            {
                                "action": "create_user",
                                "user_perfil": perfil,
                                "correlation_id": current_correlation_id,
                            },
                            level="warning",
                        )
                        continue

                    # Enhanced profile selection
                    profile_options = [
                        {
                            "id": 1,
                            "code": "juiz",
                            "name": "Juiz",
                            "description": "Full system access including user management",
                        },
                        {
                            "id": 2,
                            "code": "servidor",
                            "name": "Servidor",
                            "description": "Manage cases and documents",
                        },
                        {
                            "id": 3,
                            "code": "advogado",
                            "name": "Advogado",
                            "description": "Submit and track cases",
                        },
                        {
                            "id": 4,
                            "code": "parte",
                            "name": "Parte",
                            "description": "View case status",
                        },
                    ]

                    cli.display_data_table(
                        [
                            {
                                "#": opt["id"],
                                "Profile": opt["name"],
                                "Access Level": opt["description"],
                            }
                            for opt in profile_options
                        ],
                        title="Available User Profiles",
                    )

                    # Collect user data with validation
                    while True:
                        new_cpf = cli.prompt_input("CPF (11 digits, numbers only)")
                        if new_cpf.isdigit() and len(new_cpf) == 11:
                            exists = db.execute_query(
                                "SELECT 1 FROM usuarios WHERE cpf = %s",
                                (new_cpf,),
                                return_results=True,
                                correlation_id=current_correlation_id,
                                query_name="check_cpf_exists",
                            )
                            if not exists:
                                break
                            cli.display_status("CPF already registered", "warning")
                        else:
                            cli.display_status("CPF must be 11 digits", "warning")

                    new_nome = cli.prompt_input("Full name")

                    while True:
                        new_email = cli.prompt_input("Email")
                        if "@" in new_email and "." in new_email.split("@")[-1]:
                            break
                        cli.display_status("Invalid email format", "warning")

                    while True:
                        new_password = cli.prompt_input("Password", password=True)
                        valid, reason = auth_manager.validate_password_complexity(
                            new_password
                        )
                        if valid:
                            break
                        cli.display_status(
                            f"Password requirements: {reason}", "warning"
                        )

                    # Profile selection with validation
                    while True:
                        profile_choice = cli.prompt_input(
                            "Select profile number (1-4)", int
                        )
                        selected_profile = next(
                            (p for p in profile_options if p["id"] == profile_choice),
                            None,
                        )

                        if selected_profile:
                            new_perfil = selected_profile["code"]
                            cli.display_status(
                                f"Selected: {selected_profile['name']} - {selected_profile['description']}",
                                "info",
                            )
                            break
                        cli.display_status("Invalid profile selection", "warning")

                    # Profile-specific validation (without storage)
                    if new_perfil == "advogado":
                        while True:
                            oab = cli.prompt_input(
                                "OAB Number (format: XX/YYYYYY) [validation only]"
                            )
                            if re.match(r"^\w{2}/\d{6}$", oab):
                                break
                            cli.display_status(
                                "Invalid OAB format (use XX/YYYYYY)", "warning"
                            )
                    elif new_perfil == "parte":
                        while True:
                            parte_type = cli.prompt_input(
                                "Party type (autor/réu/testemunha) [validation only]"
                            )
                            if parte_type.lower() in {"autor", "réu", "testemunha"}:
                                break
                            cli.display_status("Invalid party type", "warning")

                    # Phone number handling
                    cli.display_status(
                        "Phone number (optional, format: XX XXXX-XXXX)", "info"
                    )
                    while True:
                        new_telefone = cli.prompt_input(
                            "Phone number (press Enter to skip)"
                        )
                        if not new_telefone:
                            new_telefone = None
                            break
                        if re.match(r"^(\d{2} \d{4,5}-\d{4})$", new_telefone):
                            break
                        cli.display_status(
                            "Invalid phone format (use XX XXXX-XXXX or XX XXXXX-XXXX)",
                            "warning",
                        )

                    # Create user with existing schema
                    try:
                        db.execute_query(
                            """INSERT INTO usuarios 
                            (cpf, nome_completo, email, senha, tipo, telefone) 
                            VALUES (%s, %s, %s, %s, %s, %s)""",
                            (
                                new_cpf,
                                new_nome,
                                new_email,
                                auth_manager.hash_password(new_password),
                                new_perfil,
                                new_telefone,
                            ),
                            correlation_id=current_correlation_id,
                            query_name="create_user",
                        )

                        cli.display_status(
                            f"{selected_profile['name']} created successfully",
                            "success",
                        )
                        logger.log_negocio(
                            "auth",
                            "user_create",
                            {
                                "email": new_email,
                                "perfil": new_perfil,
                                "cpf_masked": new_cpf[:3] + "***",
                                "correlation_id": current_correlation_id,
                            },
                            level="info",
                        )
                    except Exception as e:
                        cli.display_status(f"Error creating user: {str(e)}", "error")
                        logger.log_negocio(
                            "auth",
                            "user_create_failed",
                            {
                                "error": str(e),
                                "correlation_id": current_correlation_id,
                                "attempted_data": {
                                    "email": new_email,
                                    "perfil": new_perfil,
                                },
                            },
                            level="error",
                        )
                        cli.prompt_input("\nPress Enter to continue...")

                # 3. Update user
                elif choice == 3:
                    if not auth_manager.check_permission("user_management"):
                        cli.display_status("Permission denied", "error")
                        logger.log_negocio(
                            "auth",
                            "permission_denied",
                            {
                                "action": "update_user",
                                "user_perfil": perfil,
                                "correlation_id": current_correlation_id,
                            },
                            level="warning",
                        )
                    else:
                        user_id = cli.prompt_input("User ID to update")
                        exists = db.execute_query(
                            "SELECT id FROM usuarios WHERE id=%s::uuid",
                            (user_id,),
                            return_results=True,
                            correlation_id=current_correlation_id,
                            query_name="verify_user_exists",
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
                                    correlation_id=current_correlation_id,
                                    query_name="update_user",
                                )
                                cli.display_status("User updated", "success")
                                logger.log_negocio(
                                    "auth",
                                    "user_update",
                                    {
                                        "user_id": user_id,
                                        "email": new_email,
                                        "perfil": new_perfil,
                                        "correlation_id": current_correlation_id,
                                    },
                                    "info",
                                )
                            except Exception as e:
                                cli.display_status(
                                    f"Error updating user: {str(e)}", "error"
                                )
                                logger.log_negocio(
                                    "auth",
                                    "user_update_failed",
                                    {
                                        "user_id": user_id,
                                        "error": str(e),
                                        "correlation_id": current_correlation_id,
                                    },
                                    level="error",
                                )

                # 4. Delete user
                elif choice == 4:
                    if not auth_manager.check_permission("user_management"):
                        cli.display_status("Permission denied", "error")
                    else:
                        user_id = cli.prompt_input("User ID to delete (UUID)")
                        exists = db.execute_query(
                            "SELECT id FROM usuarios WHERE id=%s::uuid",
                            (user_id,),
                            return_results=True,
                            correlation_id=current_correlation_id,
                            query_name="verify_user_exists",
                        )
                        if not exists:
                            cli.display_status("User not found", "warning")
                        else:
                            confirm = cli.prompt_input(
                                f"Type 'YES' to confirm deletion of user {user_id}"
                            )
                            if confirm.upper() == "YES":
                                try:
                                    db.execute_query(
                                        "DELETE FROM audit_log WHERE user_id = %s::uuid",
                                        (user_id,),
                                        correlation_id=current_correlation_id,
                                        query_name="delete_audit_logs",
                                    )
                                    db.execute_query(
                                        "DELETE FROM usuarios WHERE id = %s::uuid",
                                        (user_id,),
                                        correlation_id=current_correlation_id,
                                        query_name="delete_user",
                                    )
                                    cli.display_status("User deleted", "success")
                                    logger.log_negocio(
                                        "auth",
                                        "user_delete",
                                        {
                                            "user_id": user_id,
                                            "correlation_id": current_correlation_id,
                                        },
                                        "info",
                                    )
                                except Exception as e:
                                    cli.display_status(
                                        f"Error deleting user: {str(e)}", "error"
                                    )
                                    logger.log_negocio(
                                        "auth",
                                        "user_delete_failed",
                                        {
                                            "user_id": user_id,
                                            "error": str(e),
                                            "correlation_id": current_correlation_id,
                                        },
                                        level="error",
                                    )
                            else:
                                cli.display_status("Deletion cancelled", "info")

                # 5. Change password
                elif choice == 5:
                    old = cli.prompt_input("Current password", password=True)
                    if not auth_manager.verify_password(user["senha"], old):
                        cli.display_status("Incorrect current password", "error")
                        logger.log_negocio(
                            "auth",
                            "password_change_failed",
                            {
                                "reason": "incorrect_current_password",
                                "user_id": user["id"],
                                "correlation_id": current_correlation_id,
                            },
                            level="warning",
                        )
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
                                correlation_id=current_correlation_id,
                                query_name="change_password",
                            )
                            cli.display_status("Password changed", "success")
                            logger.log_negocio(
                                "auth",
                                "password_change",
                                {
                                    "user_id": user["id"],
                                    "correlation_id": current_correlation_id,
                                },
                                "info",
                            )
                        except Exception as e:
                            cli.display_status(
                                f"Error changing password: {str(e)}", "error"
                            )

                elif choice == 6:  # Database Management
                    if not auth_manager.check_permission("database_management"):
                        cli.display_status("Permission denied", "error")
                        logger.log_negocio(
                            "auth",
                            "permission_denied",
                            {
                                "action": "database_management",
                                "user_perfil": perfil,
                                "correlation_id": current_correlation_id,
                            },
                            level="warning",
                        )
                        time.sleep(1)
                        continue
                    else:
                        handle_database_management(
                            db, logger, current_correlation_id, user
                        )

                # 7. Logout
                elif choice == 7:
                    auth_manager.logout(correlation_id=current_correlation_id)
                    cli.user_context = None
                    current_correlation_id = None
                    cli.display_status("Logged out", "info")
                    time.sleep(1)

                # 8. Exit
                elif choice == 8:
                    cli.display_status("Exiting...", "info")
                    break

                else:
                    cli.display_status("Invalid option", "warning")
                    logger.log_interface(
                        "menu",
                        "invalid_option",
                        user_ctx=cli.user_context,
                        metadata={"choice": choice},
                        level="warning",
                    )

                time.sleep(1)

        cli.clear_screen()
        cli.display_status("Goodbye!", "info")

    except KeyboardInterrupt:
        cli.clear_screen()
        cli.display_status("Interrupted. Goodbye!", "warning")


def handle_database_management(db, logger, correlation_id, user):
    """Handles database management submenu"""
    from db_mgmt.table_structure import TableStructureService
    from db_mgmt.services.validation import DBMgmtValidator

    service = TableStructureService(db)

    while True:
        cli.clear_screen()
        cli.display_header("Database Management")

        sub_options = [
            {"description": "View Table Structure"},
            {"description": "Preview Table Data"},
            {"description": "Run Custom Query"},
            {"description": "Export Table"},
            {"description": "View Database Info"},
            {"description": "Manage Users"},
            {"description": "Manage Legal Cases"},
            {"description": "Track Case Progress"},
            {"description": "Back to Main Menu"},
        ]

        cli.display_main_menu(sub_options)
        sub_choice = cli.prompt_input("Choose an option", int)

        if sub_choice == 1:  # View Table Structure
            try:
                table_name = cli.prompt_input("Enter table name")

                if not DBMgmtValidator.validate_table_name(table_name):
                    cli.display_status("Invalid table name", "error")
                    time.sleep(1)
                    continue

                # Get and display structure
                columns = service.get_table_columns(table_name, correlation_id)
                constraints = service.get_constraints(table_name, correlation_id)

                # Add type checking
                if not isinstance(columns, list) or not columns:
                    cli.display_status("Failed to retrieve table structure", "error")
                    logger.log_negocio(  # Changed from log_db_error to log_negocio to match your actual logger
                        module="database_mgmt",
                        action="get_structure_failed",
                        metadata={  # Changed to use metadata parameter
                            "table": table_name,
                            "error": "Expected list, got " + str(type(columns)),
                            "error_type": "TypeError",
                            "user_id": user.get("id") if user else None,
                            "correlation_id": correlation_id,  # Use the parameter
                        },
                        level="error",
                    )
                    continue

                if not columns:
                    cli.display_status(
                        "No columns found or table doesn't exist", "warning"
                    )
                else:
                    # Transform for display
                    display_data = [
                        {
                            "Column": col["column_name"],
                            "Type": col["data_type"],
                            "Nullable": col["is_nullable"],
                            "Default": str(col["column_default"] or ""),
                        }
                        for col in columns
                    ]

                    cli.display_data_table(
                        display_data,
                        title=f"Structure of {table_name}",
                        metadata={
                            "constraints": constraints,
                            "correlation_id": correlation_id,
                        },
                    )

                logger.log_negocio(
                    "database_mgmt",
                    "structure_viewed",
                    {
                        "table": table_name,
                        "user": user["id"],
                        "columns": len(columns),
                        "correlation_id": correlation_id,
                    },
                    level="info",
                )

            except Exception as e:
                cli.display_status(f"Error: {str(e)}", "error")
                logger.log_negocio(
                    "database_mgmt",
                    "structure_view_failed",
                    {
                        "error": str(e),
                        "traceback": traceback.format_exc(),
                        "correlation_id": correlation_id,
                    },
                    level="error",
                )

            cli.prompt_input("\nPress Enter to continue...")

        # Add to sub_choice handling
        elif sub_choice == 2:  # Preview Table Data
            try:
                table_name = cli.prompt_input("Enter table name")
                if not DBMgmtValidator.validate_table_name(table_name):
                    cli.display_status("Invalid table name", "error")
                    time.sleep(1)
                    continue

                preview_service = DataPreviewService(db)
                total_rows = preview_service.get_row_count(table_name, correlation_id)

                if total_rows == 0:
                    cli.display_status("Table is empty", "info")
                    continue

                # Pagination control
                page_size = cli.prompt_input("Rows per page (10-100)", int, default=20)
                page_size = DBMgmtValidator.sanitize_limit(page_size)
                total_pages = (total_rows + page_size - 1) // page_size

                current_page = 1
                while True:
                    offset = (current_page - 1) * page_size
                    data = preview_service.preview_data(
                        table_name, page_size, offset, correlation_id
                    )

                    cli.display_data_table(
                        data,
                        title=f"{table_name} (Page {current_page}/{total_pages})",
                        metadata={
                            "total_rows": total_rows,
                            "correlation_id": correlation_id,
                        },
                    )

                    nav_choice = cli.prompt_input(
                        "[N]ext/[P]revious/[B]ack", options=["n", "p", "b"]
                    )

                    if nav_choice == "n" and current_page < total_pages:
                        current_page += 1
                    elif nav_choice == "p" and current_page > 1:
                        current_page -= 1
                    else:
                        break

            except Exception as e:
                cli.display_status(f"Preview error: {str(e)}", "error")
                logger.log_negocio(
                    "database_mgmt",
                    "data_preview_failed",
                    {
                        "table": table_name,
                        "error": str(e),
                        "correlation_id": correlation_id,
                        "traceback": traceback.format_exc(),
                    },
                    level="error",
                )

        if sub_choice == 9:  # Back to main menu
            break

        time.sleep(1.5)

        # Log the access attempt
        logger.log_negocio(
            "database_mgmt",
            "submenu_access",
            {
                "option": sub_options[sub_choice - 1]["description"],
                "user_id": user["id"],
                "correlation_id": correlation_id,
            },
            level="info",
        )


if __name__ == "__main__":
    main()
