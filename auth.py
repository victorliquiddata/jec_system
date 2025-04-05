import logging
import re
import secrets
import hashlib
from typing import Optional, Dict
from database import DatabaseManager


class AuthManager:
    """Handles user authentication, password hashing, and session management"""

    def __init__(self):
        self.current_user: Optional[Dict] = None

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
        """Verify a password against stored hash"""
        if not stored_hash.startswith("pbkdf2:sha256:"):
            # Legacy plaintext password (for migration)
            return stored_hash == provided_password

        try:
            algorithm, hash_params = stored_hash.split("$", 1)
            _, method, iterations = algorithm.split(":")
            salt, stored_key = hash_params.split("$")
            new_hash = hashlib.pbkdf2_hmac(
                method,
                provided_password.encode("utf-8"),
                salt.encode("utf-8"),
                int(iterations),
            )
            return secrets.compare_digest(new_hash.hex(), stored_key)
        except (ValueError, AttributeError):
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

    def login(self, email: str, senha: str) -> bool:
        """Authenticate user and establish session"""
        try:
            user = get_db_instance.execute_query(
                "SELECT * FROM usuarios WHERE email = %s", (email,), return_results=True
            )
            if user and self.verify_password(user[0]["senha"], senha):
                if not user[0]["senha"].startswith("pbkdf2:sha256:"):
                    new_hash = self.hash_password(senha)
                    db_manager.execute_query(
                        "UPDATE usuarios SET senha = %s WHERE id = %s",
                        (new_hash, user[0]["id"]),
                    )

                self.current_user = user[0]
                logging.info("User %s logged in successfully", email)
                return True
            else:
                self.current_user = None  # Ensure session is cleared on failure
                return False
        except Exception as e:
            logging.error("Login failed: %s", str(e))
            self.current_user = None  # Ensure session is cleared on exceptions
            return False

    def logout(self):
        """Terminate current session"""
        if self.current_user:
            logging.info("User %s logged out", self.current_user["email"])
            self.current_user = None

    def get_current_user(self) -> Optional[Dict]:
        """Get currently authenticated user"""
        return self.current_user


# Singleton instance
auth_manager = AuthManager()
