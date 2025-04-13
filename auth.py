# auth.py

import re
import time
import traceback
import secrets
import hashlib
from typing import Dict, List, Optional

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
        self.login_attempts: dict[str, tuple[int, float]] = (
            {}
        )  # email: (count, timestamp)
        self.lockouts: dict[str, float] = {}  # email: unlock_time

    def login(
        self, email: str, password: str, correlation_id: Optional[str] = None
    ) -> bool:
        """Authenticate user and establish session with correlation support"""
        try:
            # Initialize lockout tracking if not exists
            if not hasattr(self, "login_attempts"):
                self.login_attempts = {}
            if not hasattr(self, "lockouts"):
                self.lockouts = {}

            # Check if account is locked
            current_time = time.time()
            if email in self.lockouts:
                if current_time < self.lockouts[email]:
                    remaining = int(self.lockouts[email] - current_time)
                    self.logger.log_negocio(
                        "auth",
                        "login_locked",
                        {
                            "email": email,
                            "remaining_lockout": remaining,
                            "correlation_id": correlation_id,
                        },
                        "warning",
                    )
                    return False
                # Lockout expired
                del self.lockouts[email]

            # Log login attempt
            self.logger.log_negocio(
                "auth",
                "login_attempt",
                {
                    "email": email,
                    "correlation_id": correlation_id,
                    "attempt_count": self.login_attempts.get(email, (0, current_time))[
                        0
                    ]
                    + 1,
                },
                "info",
            )

            db = get_db_instance()
            user = db.execute_query(
                "SELECT * FROM usuarios WHERE email = %s",
                (email,),
                return_results=True,
                correlation_id=correlation_id,
                query_name="user_login",
            )

            if not user:
                self.logger.log_negocio(
                    "auth",
                    "login_failed",
                    {
                        "email": email,
                        "reason": "user_not_found",
                        "correlation_id": correlation_id,
                    },
                    "warning",
                )
                self._track_failed_attempt(email, current_time)
                self.current_user = None
                return False

            user_data = user[0]
            stored_password = user_data["senha"]

            # Detect legacy hash by prefix
            SUPPORTED_HASH_PREFIXES = ("pbkdf2:sha256:",)
            is_legacy = not stored_password.startswith(SUPPORTED_HASH_PREFIXES)

            # Validate password (legacy or modern)
            password_valid = self.verify_password(stored_password, password)

            if not password_valid:
                self.logger.log_negocio(
                    "auth",
                    "login_failed",
                    {
                        "email": email,
                        "user_id": user_data["id"],
                        "reason": "invalid_password",
                        "correlation_id": correlation_id,
                    },
                    "warning",
                )
                self._track_failed_attempt(email, current_time)
                self.current_user = None
                return False

            # Successful login - reset attempts
            if email in self.login_attempts:
                del self.login_attempts[email]

            # Update last login timestamp
            db.execute_query(
                "UPDATE usuarios SET ultimo_login = CURRENT_TIMESTAMP WHERE id = %s",
                (user_data["id"],),
                correlation_id=correlation_id,
                query_name="update_last_login",
            )

            # Upgrade legacy password hash
            if is_legacy:
                new_hash = self.hash_password(password)
                db.execute_query(
                    "UPDATE usuarios SET senha = %s WHERE id = %s",
                    (new_hash, user_data["id"]),
                    correlation_id=correlation_id,
                    query_name="password_upgrade",
                )

                # Refresh user data from database
                updated_user = db.execute_query(
                    "SELECT * FROM usuarios WHERE id = %s",
                    (user_data["id"],),
                    return_results=True,
                    correlation_id=correlation_id,
                )
                user_data = updated_user[0]  # Get fresh data
                self.logger.log_negocio(
                    "auth",
                    "password_upgraded",
                    {
                        "user_id": user_data["id"],
                        "email": email,
                        "correlation_id": correlation_id,
                    },
                    "info",
                )

            self.current_user = user_data
            self.logger.log_negocio(
                "auth",
                "login_success",
                {
                    "user_id": user_data["id"],
                    "email": email,
                    "profile": user_data.get("tipo", "unknown"),
                    "correlation_id": correlation_id,
                },
                "info",
            )
            return True

        except (psycopg2.DatabaseError, ValueError, AttributeError, IndexError) as e:
            self.logger.log_negocio(
                "auth",
                "login_error",
                {
                    "email": email,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "correlation_id": correlation_id,
                    "stack_trace": traceback.format_exc(),
                },
                "error",
            )
            self.current_user = None
            return False

    def _track_failed_attempt(self, email: str, timestamp: float) -> None:
        """Track failed login attempts and implement lockout policy"""
        MAX_ATTEMPTS = 3
        LOCKOUT_DURATION = 300  # 5 minutes in seconds

        attempts, first_attempt = self.login_attempts.get(email, (0, timestamp))
        attempts += 1

        # Reset if last attempt was long ago
        if timestamp - first_attempt > LOCKOUT_DURATION:
            attempts = 1
            first_attempt = timestamp

        self.login_attempts[email] = (attempts, first_attempt)

        # Lock account if threshold reached
        if attempts >= MAX_ATTEMPTS:
            self.lockouts[email] = timestamp + LOCKOUT_DURATION
            self.logger.log_negocio(
                "auth",
                "account_locked",
                {
                    "email": email,
                    "lockout_until": self.lockouts[email],
                    "attempt_count": attempts,
                },
                "warning",
            )

    def logout(self, correlation_id: Optional[str] = None) -> None:
        """Terminate current session with correlation support"""
        if self.current_user:
            self.logger.log_negocio(
                "auth",
                "logout",
                {
                    "user_email": self.current_user["email"],
                    "user_id": self.current_user.get("id"),
                    "correlation_id": correlation_id,
                },
                "info",
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

    def check_permission(self, permission_name: str) -> bool:
        # Add special handling for database permissions
        if permission_name.startswith("db_"):
            required = self.config.AUTH["database_permissions"].get(
                permission_name[3:], []
            )
            return self.current_user["tipo"].lower() in required
        try:
            user_profile = self.current_user.get("tipo", "").lower()
            permissions = self.config.AUTH.get("permissions", {})
            allowed_profiles = permissions.get(permission_name, [])

            # Debug logging
            self.logger.log_negocio(
                "auth",
                "permission_check",
                {
                    "permission": permission_name,
                    "user_profile": user_profile,
                    "allowed_profiles": allowed_profiles,
                    "config_loaded": bool(permissions),
                },
                "debug",
            )

            return user_profile in allowed_profiles

        except Exception as e:
            self.logger.log_negocio(
                "auth",
                "permission_error",
                {"error": str(e), "permission": permission_name},
                "error",
            )
            return False


# Singleton instance
auth_manager = AuthManager()
