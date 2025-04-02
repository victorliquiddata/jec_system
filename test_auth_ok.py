import pytest
from unittest.mock import patch, MagicMock
from auth import AuthManager, auth_manager
from database import db_manager


@pytest.fixture
def mock_db():
    with patch.object(db_manager, "execute_query") as mock_query:
        yield mock_query


def test_password_hashing():
    auth = AuthManager()
    password = "SecurePass123!"
    hashed = auth.hash_password(password)

    # Verify the hash format
    assert hashed.startswith("pbkdf2:sha256:600000$")
    assert len(hashed.split("$")) == 3

    # Verify password verification
    assert auth.verify_password(hashed, password)
    assert not auth.verify_password(hashed, "wrongpass")


def test_password_complexity():
    auth = AuthManager()

    # Test valid password
    valid, msg = auth.validate_password_complexity("SecurePass123!")
    assert valid
    assert msg == ""

    # Test various invalid cases
    assert not auth.validate_password_complexity("short")[0]
    assert not auth.validate_password_complexity("nouppercase123!")[0]
    assert not auth.validate_password_complexity("NOLOWERCASE123!")[0]
    assert not auth.validate_password_complexity("NoNumbers!")[0]
    assert not auth.validate_password_complexity("MissingSpecial123")[0]


def test_successful_login(mock_db):
    mock_db.return_value = [
        {
            "id": 1,
            "email": "test@example.com",
            "senha": auth_manager.hash_password("correctpass"),
        }
    ]

    assert auth_manager.login("test@example.com", "correctpass")
    assert auth_manager.get_current_user() is not None
    mock_db.assert_called()


def test_failed_login(mock_db):
    auth_manager.logout()  # Ensure no previous session exists
    mock_db.return_value = [
        {
            "id": 1,
            "email": "test@example.com",
            "senha": auth_manager.hash_password("correctpass"),
        }
    ]

    assert not auth_manager.login("test@example.com", "wrongpass")
    assert auth_manager.get_current_user() is None  # This should now pass


def test_logout():
    auth_manager.current_user = {"email": "test@example.com"}
    auth_manager.logout()
    assert auth_manager.get_current_user() is None


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
