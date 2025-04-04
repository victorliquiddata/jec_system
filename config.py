# version 2

"""
Configuration management for JEC System

This module handles all system configuration including:
- Environment variable loading and validation
- Default value management
- Configuration state management
"""

import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from pathlib import Path


class ConfigManager:
    """Centralized configuration management for the application"""

    _instance = None
    _config: Dict[str, Any] = {}
    _initialized = False  # Move this to class level

    def __new__(cls):
        """Implement singleton pattern"""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            # Remove _initialized assignment here
        return cls._instance

    def __init__(self):
        """Initialize configuration - only happens once due to singleton"""
        if self.__class__._initialized:  # Access class-level attribute
            return

        self.__class__._initialized = True  # Set class-level attribute
        self._load_configuration()
        self._validate_configuration()

    def _load_configuration(self):
        """Load configuration from environment variables"""
        # Try to load from .env file in project root
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        else:
            load_dotenv()

        # Database configuration
        self._config.update(
            {
                "DB_HOST": os.getenv("DB_HOST", "localhost"),
                "DB_PORT": os.getenv("DB_PORT", "5432"),
                "DB_USUARIO": os.getenv("DB_USUARIO"),
                "DB_SENHA": os.getenv("DB_SENHA"),
                "DB_NOME": os.getenv("DB_NOME", "jec_system"),
                "DB_SCHEMA": os.getenv("DB_SCHEMA", "jec"),
                "DB_MIN_CONNECTIONS": int(os.getenv("DB_MIN_CONNECTIONS", "1")),
                "DB_MAX_CONNECTIONS": int(os.getenv("DB_MAX_CONNECTIONS", "5")),
                # Application configuration
                "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
                "LOG_FILE": os.getenv("LOG_FILE", "jec_system.log"),
                "MAX_LOG_SIZE": int(os.getenv("MAX_LOG_SIZE", "1048576")),  # 1MB
                "LOG_BACKUP_COUNT": int(os.getenv("LOG_BACKUP_COUNT", "3")),
                # Security configuration
                "SESSION_TIMEOUT": int(
                    os.getenv("SESSION_TIMEOUT", "1800")
                ),  # 30 minutes
                "PASSWORD_RESET_TIMEOUT": int(
                    os.getenv("PASSWORD_RESET_TIMEOUT", "3600")
                ),  # 1 hour
            }
        )

    def _validate_configuration(self):
        """Validate required configuration values"""
        required = ["DB_USUARIO", "DB_SENHA", "DB_NOME"]
        missing = [var for var in required if not self._config.get(var)]

        if missing:
            error_msg = (
                f"Missing required configuration variables: {', '.join(missing)}"
            )
            logging.critical(error_msg)
            raise ValueError(error_msg)

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get configuration value by key"""
        return self._config.get(key, default)

    def set(self, key: str, value: Any):
        """Set configuration value (for testing purposes)"""
        self._config[key] = value

    def reload(self):
        """Reload configuration from environment"""
        self._config.clear()
        self._load_configuration()
        self._validate_configuration()


# Singleton instance
config = ConfigManager()
