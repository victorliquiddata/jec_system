import re

import secrets
import hashlib
from typing import Optional, Dict


from database import get_db_instance
from logger import JCELogger
from config import AppConfig


class AuthManager:
    """Handles user authentication, password hashing, and session management"""

    def __init__(self):
        self.current_user: Optional[Dict] = None
        self.logger = JCELogger()  # Add this line to use your custom logger

    # Other methods remain the same

    def login(self, email: str, senha: str) -> bool:
        """Authenticate user and establish session, upgrading legacy passwords if needed."""
        try:
            db = get_db_instance()
            user = db.execute_query(
                "SELECT * FROM usuarios WHERE email = %s", (email,), return_results=True
            )

            if not user:
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
                "auth", "login_success", {"user_email": email}, "info"
            )
            return True

        except Exception as e:
            self.logger.log_negocio("auth", "login_failed", {"error": str(e)}, "error")
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
            return False

        # Legacy plaintext password (for migration or fallback)
        if not stored_hash.startswith("pbkdf2:sha256:"):
            return stored_hash.strip() == provided_password.strip()

        try:
            parts = stored_hash.split("$")
            if len(parts) != 3:
                return False

            # Format: pbkdf2:sha256:600000$salt$hash
            algorithm_parts = parts[0].split(":")
            if len(algorithm_parts) != 3:
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
            return secrets.compare_digest(new_hash.hex(), stored_key)

        except (ValueError, AttributeError, IndexError):
            return False

    def validate_password_complexity(self, password: str) -> tuple[bool, str]:
        """Enforce password complexity rules"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter"
        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter"
        if not re.search(r"[0-9]", password):
            return False, "Password must contain at least one digit"
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return False, "Password must contain at least one special character"
        return True, ""

    def get_current_user(self) -> Optional[Dict]:
        """Get currently authenticated user"""
        return self.current_user


# Singleton instance
auth_manager = AuthManager()
