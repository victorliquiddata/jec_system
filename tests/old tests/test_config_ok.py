#####version 6 >> update if new vresion please

import pytest
from unittest.mock import patch, MagicMock
import os
from pathlib import Path
from config import ConfigManager, config
import dotenv
import sys


@pytest.fixture(autouse=True)
def reset_config_singleton():
    """Completely reset the ConfigManager between tests"""
    # Backup original state
    original_instance = ConfigManager._instance
    original_initialized = ConfigManager._initialized
    original_config = ConfigManager._config.copy()

    # Reset for test
    ConfigManager._instance = None
    ConfigManager._initialized = False
    ConfigManager._config = {}

    # Also reset the module-level config variable
    if "config" in sys.modules[__name__].__dict__:
        sys.modules[__name__].__dict__["config"] = None

    yield

    # Restore original state
    ConfigManager._instance = original_instance
    ConfigManager._initialized = original_initialized
    ConfigManager._config = original_config
    if "config" in sys.modules[__name__].__dict__:
        sys.modules[__name__].__dict__["config"] = original_instance


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing"""
    # Clear all existing env vars that might interfere
    for key in ["DB_HOST", "DB_PORT", "DB_USUARIO", "DB_SENHA", "DB_NOME", "LOG_LEVEL"]:
        monkeypatch.delenv(key, raising=False)

    # Set required minimum config
    monkeypatch.setenv("DB_USUARIO", "test_user")
    monkeypatch.setenv("DB_SENHA", "test_pass")
    monkeypatch.setenv("DB_NOME", "test_db")


@pytest.fixture
def mock_env_file(tmp_path, monkeypatch):
    """Create a mock .env file and ensure it's loaded"""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DB_HOST=file_host\n"
        "DB_PORT=4321\n"
        "DB_USUARIO=envfile_user\n"
        "DB_SENHA=envfile_pass\n"
        "DB_NOME=envfile_db\n"
    )

    # Mock Path.exists to only return True for our test file
    def mock_exists(path):
        return str(path) == str(env_file)

    monkeypatch.setattr(Path, "exists", mock_exists)

    # Create a proper mock for load_dotenv
    original_load = dotenv.load_dotenv

    def mock_load_dotenv(path=None, **kwargs):
        if path is None:
            path = env_file
        # Actually load from our test file
        return original_load(path, **kwargs)

    monkeypatch.setattr(dotenv, "load_dotenv", mock_load_dotenv)
    monkeypatch.setattr("config.load_dotenv", mock_load_dotenv)

    return env_file


def test_singleton_pattern():
    """Test that ConfigManager is a proper singleton"""
    instance1 = ConfigManager()
    instance2 = ConfigManager()
    assert instance1 is instance2


def test_config_initialization(mock_env_vars):
    """Test basic config initialization with environment variables"""
    cfg = ConfigManager()
    assert cfg.get("DB_USUARIO") == "test_user"
    assert cfg.get("DB_SENHA") == "test_pass"
    assert cfg.get("DB_NOME") == "test_db"
    assert cfg.get("DB_MAX_CONNECTIONS") == 5  # Default value


def test_env_file_loading(mock_env_file, monkeypatch):
    """Test that config loads from .env file when present"""
    # Ensure environment doesn't have these vars
    monkeypatch.delenv("DB_HOST", raising=False)
    monkeypatch.delenv("DB_PORT", raising=False)
    monkeypatch.delenv("DB_USUARIO", raising=False)
    monkeypatch.delenv("DB_SENHA", raising=False)
    monkeypatch.delenv("DB_NOME", raising=False)

    # Create a fresh ConfigManager which should load from our mock .env file
    cfg = ConfigManager()
    assert cfg.get("DB_HOST") == "file_host"
    assert cfg.get("DB_PORT") == "4321"
    assert cfg.get("DB_USUARIO") == "envfile_user"


def test_missing_required_config(monkeypatch):
    """Test that missing required config raises ValueError"""
    # Clear all required vars
    for key in ["DB_USUARIO", "DB_SENHA", "DB_NOME"]:
        monkeypatch.delenv(key, raising=False)

    # Ensure no .env file is loaded
    monkeypatch.setattr(Path, "exists", lambda *args: False)
    monkeypatch.setattr("config.load_dotenv", lambda *args, **kwargs: False)

    with pytest.raises(ValueError) as excinfo:
        ConfigManager()
    assert "Missing required configuration variables" in str(excinfo.value)


def test_config_reload(mock_env_vars, monkeypatch):
    """Test that reload() refreshes configuration"""
    cfg = ConfigManager()
    monkeypatch.setenv("DB_USUARIO", "new_user")
    cfg.reload()
    assert cfg.get("DB_USUARIO") == "new_user"


def test_config_get_with_default(mock_env_vars):
    """Test get() with default values"""
    cfg = ConfigManager()
    assert cfg.get("NON_EXISTENT_KEY", "default") == "default"
    assert cfg.get("NON_EXISTENT_KEY") is None


def test_config_set_method(mock_env_vars):
    """Test that set() method works for testing purposes"""
    cfg = ConfigManager()
    cfg.set("TEST_KEY", "test_value")
    assert cfg.get("TEST_KEY") == "test_value"


def test_no_env_file(monkeypatch):
    """Test behavior when no .env file exists"""
    monkeypatch.setattr(Path, "exists", lambda *args: False)
    monkeypatch.setattr("config.load_dotenv", lambda *args, **kwargs: False)

    # Set required vars directly in environment
    monkeypatch.setenv("DB_USUARIO", "test_user")
    monkeypatch.setenv("DB_SENHA", "test_pass")
    monkeypatch.setenv("DB_NOME", "test_db")

    cfg = ConfigManager()
    assert cfg.get("DB_USUARIO") == "test_user"


def test_singleton_instance_access():
    """Test that the singleton instance can be accessed via config variable"""
    # Import and reload the module to reset state
    import importlib
    import config

    # Reset class-level attributes through the module
    config.ConfigManager._instance = None
    config.ConfigManager._initialized = False
    config.ConfigManager._config = {}

    # Reload the module to reset the config variable
    importlib.reload(config)

    # Create new instance
    cfg = config.ConfigManager()

    # Verify module-level config matches
    assert config.config is cfg
    assert isinstance(config.config, config.ConfigManager)


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
