import pytest
from unittest.mock import MagicMock, patch
from auth import AuthManager
from database import get_db_instance
from config import AppConfig


@pytest.fixture
def mock_env():
    with patch("auth.get_db_instance") as mock_db_instance, patch(
        "auth.AppConfig"
    ) as mock_config, patch("auth.JCELogger") as mock_logger:

        # Set up logger
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance

        # Set up config
        mock_config_instance = MagicMock()
        mock_config.return_value = mock_config_instance

        # Set up DB instance
        mock_db = MagicMock()
        mock_db_instance.return_value = mock_db

        yield {
            "db": mock_db,
            "config": mock_config_instance,
            "logger": mock_logger_instance,
        }


@pytest.fixture
def mock_db():
    """Mock the DB layer"""
    mock = MagicMock()
    with patch("auth.get_db_instance", return_value=mock):
        yield mock


@pytest.fixture
def mock_config():
    """Mock the AppConfig"""
    with patch("auth.AppConfig") as mock_cfg_class:
        mock_cfg = MagicMock()
        mock_cfg_class.return_value = mock_cfg
        yield mock_cfg


@pytest.fixture
def auth_manager(mock_db, mock_config):
    """Return a fresh AuthManager instance with mocked deps"""
    return AuthManager()


def test_successful_login_with_modern_hash(auth_manager, mock_db):
    plain_password = "SecurePass1!"
    hashed_password = auth_manager.hash_password(plain_password)

    mock_db.execute_query.return_value = [
        {
            "id": 1,
            "email": "test@example.com",
            "senha": hashed_password,
            "perfil": "admin",
        }
    ]

    success = auth_manager.login("test@example.com", plain_password)

    assert success is True
    assert auth_manager.get_current_user()["email"] == "test@example.com"
    mock_db.execute_query.assert_called()


def test_successful_login_and_legacy_password_upgrade(mock_env):
    mock_db = mock_env["db"]
    mock_logger = mock_env["logger"]

    email = "legacy@example.com"
    password = "LegacyPass123!"
    user_id = 42

    # Legacy password (plaintext stored in DB)
    legacy_password = password  # no hashing

    # Mock execute_query with conditional return values
    def mock_execute_query(query, params=None, return_results=False):
        if "SELECT" in query:
            return [
                {
                    "id": user_id,
                    "email": email,
                    "senha": legacy_password,
                    "perfil": "user",
                }
            ]
        elif "UPDATE" in query:
            return []  # simulate update success
        return []

    mock_db.execute_query.side_effect = mock_execute_query

    auth = AuthManager()
    success = auth.login(email, password)

    assert success is True
    assert auth.get_current_user()["email"] == email

    # Check that password upgrade was triggered
    mock_logger.log_negocio.assert_any_call(
        "auth", "password_upgraded", {"user_id": user_id, "email": email}, "info"
    )

    # Check login success was logged
    mock_logger.log_negocio.assert_any_call(
        "auth",
        "login_success",
        {"user_id": user_id, "email": email, "profile": "user"},
        "info",
    )


def test_login_failure_wrong_password(auth_manager, mock_db):
    password = "WrongPass123!"
    stored_password = auth_manager.hash_password("CorrectPass1!")

    mock_db.execute_query.return_value = [
        {
            "id": 3,
            "email": "fail@example.com",
            "senha": stored_password,
            "perfil": "user",
        }
    ]

    success = auth_manager.login("fail@example.com", password)

    assert success is False
    assert auth_manager.get_current_user() is None


def test_logout_clears_session(auth_manager, mock_db):
    email = "out@example.com"
    password = "LogMeOut123!"
    stored = auth_manager.hash_password(password)

    mock_db.execute_query.return_value = [
        {
            "id": 4,
            "email": email,
            "senha": stored,
            "perfil": "user",
        }
    ]

    assert auth_manager.login(email, password) is True
    assert auth_manager.get_current_user() is not None

    auth_manager.logout()
    assert auth_manager.get_current_user() is None


def test_legacy_password_fails_if_incorrect(auth_manager, mock_env):
    mock_db = mock_env["db"]
    email = "legacyfail@example.com"
    wrong_password = "WrongPass123!"
    correct_legacy = "CorrectLegacy1!"

    mock_db.execute_query.return_value = [
        {
            "id": 99,
            "email": email,
            "senha": correct_legacy,  # legacy plaintext
            "perfil": "user",
        }
    ]

    assert not auth_manager.login(email, wrong_password)
    assert auth_manager.get_current_user() is None


def test_legacy_password_triggers_upgrade(auth_manager, mock_env):
    mock_db = mock_env["db"]
    email = "upgrade@example.com"
    plain_password = "Plain123!"
    user_id = 88

    def upgrade_side_effect(query, params=None, return_results=False):
        if "SELECT" in query:
            return [
                {
                    "id": user_id,
                    "email": email,
                    "senha": plain_password,  # legacy stored
                    "perfil": "user",
                }
            ]
        elif "UPDATE" in query:
            assert params[0] != plain_password  # should be hashed
            assert params[1] == user_id
        return []

    mock_db.execute_query.side_effect = upgrade_side_effect

    assert AuthManager().login(email, plain_password)


def test_login_blocked_in_strict_mode(mock_env):
    mock_db = mock_env["db"]
    mock_config = mock_env["config"]
    mock_config.get.return_value = True  # strict mode ON
    mock_db.execute_query.return_value = []

    auth = AuthManager()
    assert not auth.login("blocked@example.com", "AnyPass123!")


def test_failed_login_logs_attempt(mock_env):
    mock_db = mock_env["db"]
    mock_logger = mock_env["logger"]
    email = "ghost@example.com"

    mock_db.execute_query.return_value = []

    auth = AuthManager()
    assert not auth.login(email, "Nope123!")

    mock_logger.log_negocio.assert_any_call(
        "auth", "login_attempt", {"email": email}, "info"
    )


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main(["-v", __file__]))
