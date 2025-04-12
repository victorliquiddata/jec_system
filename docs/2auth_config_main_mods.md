```md
<details>
<summary>INSTRUCTION FOR LLM: READ ONLY THE CONTEXT BELOW, NO FURTHER ACTION REQUIRED YET - auth</summary>

```json
{
  "auth": [

# auth.py >> version 2
"""
auth.py — [insert brief description] >> UPDATE HERE BEFORE ANY CHANGES

Features:
- [insert feat 1]
- [insert feat 2]
- [insert more feats if needed]
"""


import re

import secrets
import hashlib
from typing import Optional, Dict

import psycopg2  # or your actual DB library

from database import get_db_instance
from logger import JCELogger
from config import AppConfig


class AuthManager:
    """Handles user authentication, password hashing, and session management"""

    def __init__(self):
        self.current_user: Optional[Dict] = None
        self.logger = JCELogger()  # Add this line to use your custom logger
        self.config = AppConfig()
        # Log initialization of auth manager
        self.logger.log_negocio("auth", "manager_initialized", level="info")

    def login(self, email: str, senha: str) -> bool:
        """Authenticate user and establish session, upgrading legacy passwords if needed."""
        try:
            self.logger.log_negocio("auth", "login_attempt", {"email": email}, "info")

            db = get_db_instance()
            user = db.execute_query(
                "SELECT * FROM usuarios WHERE email = %s", (email,), return_results=True
            )

            if not user:
                self.logger.log_negocio(
                    "auth",
                    "login_failed",
                    {"email": email, "reason": "user_not_found"},
                    "warning",
                )
                self.current_user = None
                return False

            user_data = user[0]
            stored_password = user_data["senha"]

            # Detect legacy hash by prefix
            SUPPORTED_HASH_PREFIXES = ("pbkdf2:sha256:",)
            is_legacy = not stored_password.startswith(SUPPORTED_HASH_PREFIXES)

            # Validate password (legacy or modern)
            password_valid = self.verify_password(stored_password, senha)

            if not password_valid:
                self.logger.log_negocio(
                    "auth",
                    "login_failed",
                    {
                        "email": email,
                        "user_id": user_data["id"],
                        "reason": "invalid_password",
                    },
                    "warning",
                )
                self.current_user = None
                return False

            # Upgrade legacy password hash
            if is_legacy:
                new_hash = self.hash_password(senha)
                db.execute_query(
                    "UPDATE usuarios SET senha = %s WHERE id = %s",
                    (new_hash, user_data["id"]),
                )
                self.logger.log_negocio(
                    "auth",
                    "password_upgraded",
                    {"user_id": user_data["id"], "email": email},
                    "info",
                )

            self.current_user = user_data
            self.logger.log_negocio(
                "auth",
                "login_success",
                {
                    "user_id": user_data["id"],
                    "email": email,
                    "profile": user_data.get("perfil", "unknown"),
                },
                "info",
            )
            return True

        except (psycopg2.DatabaseError, ValueError, AttributeError, IndexError) as e:
            self.logger.log_negocio(
                "auth",
                "login_error",
                {"email": email, "error": str(e), "error_type": type(e).__name__},
                "error",
            )
            self.current_user = None
            return False

    def logout(self):
        """Terminate current session"""
        if self.current_user:
            # Use your custom logger here
            self.logger.log_negocio(
                "auth", "logout", {"user_email": self.current_user["email"]}, "info"
            )
            self.current_user = None

    def hash_password(self, password: str, salt: Optional[str] = None) -> str:
        """Hash password with PBKDF2-HMAC-SHA256"""
        if salt is None:
            salt = secrets.token_hex(16)
        iterations = 600000
        hashed = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations
        )
        return f"pbkdf2:sha256:{iterations}${salt}${hashed.hex()}"

    def verify_password(self, stored_hash: str, provided_password: str) -> bool:
        """Verify a password against stored hash (supports legacy plaintext)"""

        if not isinstance(stored_hash, str) or not isinstance(provided_password, str):
            self.logger.log_negocio(
                "auth",
                "password_verification_failed",
                {"reason": "non_string_input"},
                "debug",
            )
            return False

        # Legacy plaintext password (for migration or fallback)
        if not stored_hash.startswith("pbkdf2:sha256:"):
            match = stored_hash.strip() == provided_password.strip()
            self.logger.log_negocio(
                "auth",
                "password_verification_legacy",
                {"match": match, "used_legacy": True},
                "debug",
            )
            return match

        try:
            parts = stored_hash.split("$")
            if len(parts) != 3:
                self.logger.log_negocio(
                    "auth",
                    "password_verification_failed",
                    {"reason": "invalid_hash_format", "parts_length": len(parts)},
                    "debug",
                )
                return False

            algorithm_parts = parts[0].split(":")
            if len(algorithm_parts) != 3:
                self.logger.log_negocio(
                    "auth",
                    "password_verification_failed",
                    {"reason": "invalid_algorithm_format", "algorithm": parts[0]},
                    "debug",
                )
                return False

            method = algorithm_parts[1]
            iterations = int(algorithm_parts[2])
            salt = parts[1]
            stored_key = parts[2]

            new_hash = hashlib.pbkdf2_hmac(
                method,
                provided_password.encode("utf-8"),
                salt.encode("utf-8"),
                iterations,
            )

            match = secrets.compare_digest(new_hash.hex(), stored_key)

            if not match:
                self.logger.log_negocio(
                    "auth",
                    "password_verification_failed",
                    {"reason": "hash_mismatch"},
                    "debug",
                )

            return match

        except (ValueError, AttributeError, IndexError) as e:
            self.logger.log_negocio(
                "auth",
                "password_verification_failed",
                {"reason": "exception", "error": str(e)},
                "debug",
            )
            return False

    def validate_password_complexity(self, password: str) -> tuple[bool, str]:
        """Enforce password complexity rules"""

        if len(password) < 8:
            reason = "Password must be at least 8 characters long"
            self.logger.log_negocio(
                "auth",
                "password_complexity_check",
                {"passed": False, "reason": reason},
                "debug",
            )
            return False, reason

        if not re.search(r"[A-Z]", password):
            reason = "Password must contain at least one uppercase letter"
            self.logger.log_negocio(
                "auth",
                "password_complexity_check",
                {"passed": False, "reason": reason},
                "debug",
            )
            return False, reason

        if not re.search(r"[a-z]", password):
            reason = "Password must contain at least one lowercase letter"
            self.logger.log_negocio(
                "auth",
                "password_complexity_check",
                {"passed": False, "reason": reason},
                "debug",
            )
            return False, reason

        if not re.search(r"[0-9]", password):
            reason = "Password must contain at least one digit"
            self.logger.log_negocio(
                "auth",
                "password_complexity_check",
                {"passed": False, "reason": reason},
                "debug",
            )
            return False, reason

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            reason = "Password must contain at least one special character"
            self.logger.log_negocio(
                "auth",
                "password_complexity_check",
                {"passed": False, "reason": reason},
                "debug",
            )
            return False, reason

        # All checks passed
        self.logger.log_negocio(
            "auth",
            "password_complexity_check",
            {"passed": True},
            "debug",
        )
        return True, ""

    def get_current_user(self) -> Optional[Dict]:
        """Get currently authenticated user"""
        return self.current_user


# Singleton instance
auth_manager = AuthManager()


  ]
}














```

</details>

<details>
<summary>INSTRUCTION FOR LLM: READ ONLY THE CONTEXT BELOW, NO FURTHER ACTION REQUIRED YET - config</summary>

```json
{
  "config": [

# config.py
"""
config.py — [insert brief description] >> UPDATE HERE BEFORE ANY CHANGES

Features:
- [insert feat 1]
- [insert feat 2]
- [insert more feats if needed]
"""

import os
import logging
from dotenv import load_dotenv
from enum import Enum

# Carrega variáveis de ambiente
load_dotenv()


class Theme(str, Enum):
    """Esquemas de cores disponíveis"""

    ESCURO = "escuro"  # Dark theme
    CLARO = "claro"  # Light theme (renamed from PADRAO to match tests)
    PADRAO = "padrao"  # Kept for backward compatibility


class AppConfig:
    """Configurações centrais da aplicação"""

    # Versão do sistema
    VERSION = "0.4"

    # Configurações de banco de dados
    DB_CONFIG = {
        "host": os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT"),
        "user": os.getenv("DB_USUARIO"),
        "password": os.getenv("DB_SENHA"),
        "database": os.getenv("DB_NOME"),
        "schema": os.getenv("DB_SCHEMA", "jec"),
        "min_connections": int(os.getenv("DB_MIN_CONNECTIONS", "1")),
        "max_connections": int(os.getenv("DB_MAX_CONNECTIONS", "5")),
    }

    # Configurações de autenticação
    AUTH = {
        "hashing_algorithm": "pbkdf2:sha256",
        "iterations": 600000,
        "session_timeout": 1800,  # 30 minutos em segundos
        "password_rules": {
            "min_length": 8,
            "require_upper": True,
            "require_lower": True,
            "require_digit": True,
            "require_special": True,
        },
    }

    LOG_LEVEL = logging.DEBUG  # Nível padrão
    LOG_ROTATION = "midnight"  # Rotação diária
    LOG_RETENTION = 30  # Dias de retenção

    # Esquemas de cores (para rich_cli.py)
    THEMES = {
        Theme.ESCURO: {
            "header": {"color": "#E0E0E0", "border": "#7A7A7A"},
            "body": {"primary": "#BDBDBD", "secondary": "#7A7A7A"},
            "status": {
                "success": "#66BB6A",
                "warning": "#E6A23C",
                "error": "#D32F2F",
                "info": "#2196F3",
            },
        },
        Theme.CLARO: {  # Changed from PADRAO to CLARO
            "header": {"color": "#333333", "border": "#003D5C"},
            "body": {"primary": "#333333", "secondary": "#666666"},
            "status": {
                "success": "#4CAF50",
                "warning": "#FFC107",
                "error": "#F44336",
                "info": "#2196F3",
            },
        },
        # Keep PADRAO as alias for CLARO if needed for backward compatibility
        Theme.PADRAO: {
            "header": {"color": "#005F87", "border": "#003D5C"},
            "body": {"primary": "#333333", "secondary": "#666666"},
            "status": {
                "success": "#4CAF50",
                "warning": "#FFC107",
                "error": "#F44336",
                "info": "#2196F3",
            },
        },
    }

    @classmethod
    def load_theme(cls, theme_name: str = Theme.ESCURO) -> Theme:
        """Carrega configurações de tema"""
        try:
            if isinstance(theme_name, Theme):
                return theme_name
            return Theme(theme_name.lower())  # Handles case insensitivity
        except ValueError:
            return Theme.ESCURO

    @classmethod
    def get_db_dsn(cls) -> str:
        """Retorna DSN para conexão com banco"""
        return (
            f"host={cls.DB_CONFIG['host']} "
            f"port={cls.DB_CONFIG['port']} "
            f"user={cls.DB_CONFIG['user']} "
            f"password={cls.DB_CONFIG['password']} "
            f"dbname={cls.DB_CONFIG['database']} "
            f"options='-c search_path={cls.DB_CONFIG['schema']}'"
        )


# Teste de configuração (executa apenas quando rodado diretamente)
if __name__ == "__main__":
    print(f"Configuração do tema escuro: {AppConfig.load_theme()}")
    print(f"DSN do banco de dados: {AppConfig.get_db_dsn()}")


  ]
}
```

















</details>

<details>
<summary>INSTRUCTION FOR LLM: READ ONLY THE CONTEXT BELOW, NO FURTHER ACTION REQUIRED YET - main</summary>

```json
{
  "main": [

#!/usr/bin/env python3
"""
main.py — Entry point for Sistema JEC CLI >> UPDATE HERE BEFORE ANY CHANGES

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
                        # Validate CPF format (basic check)
                        while True:
                            new_cpf = cli.prompt_input("CPF (11 digits)")
                            if new_cpf.isdigit() and len(new_cpf) == 11:
                                break
                            cli.display_status("CPF must be 11 digits", "warning")

                        new_nome = cli.prompt_input("Full name")
                        new_email = cli.prompt_input("Email")

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


  ]
}
```

</details>
```