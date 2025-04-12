import pytest
import auth
from auth import AuthManager
from typing import Optional, Dict, List, Any, Union


class FakeDB:
    """Enhanced test database with correlation ID support"""

    def __init__(self):
        self.updated = False
        self.last_correlation_id = None
        self.last_query_name = None
        self.query_names = []  # <-- Track all query names

    def execute_query(
        self,
        query: str,
        params: Optional[tuple] = None,
        return_results: bool = False,
        correlation_id: Optional[str] = None,
        query_name: Optional[str] = None,
    ) -> Optional[Union[List[Dict[str, Any]], int]]:
        self.last_correlation_id = correlation_id
        self.last_query_name = query_name
        self.query_names.append(query_name)  # <-- Store each call

        # Simulate user lookup
        if query.strip().upper().startswith("SELECT * FROM USUARIOS"):
            return [
                {
                    "id": "test-id-123",
                    "email": "test@example.com",
                    "senha": "Ulala1234!",  # legacy plaintext
                    "tipo": "juiz",
                }
            ]

        # Simulate password update
        if query.strip().upper().startswith("UPDATE USUARIOS SET SENHA"):
            new_hash, user_id = params
            assert new_hash.startswith("pbkdf2:sha256:"), "Password not re-hashed"
            assert user_id == "test-id-123"
            self.updated = True
            return 1

        return []


@pytest.fixture
def auth_manager(monkeypatch):
    """Fixture providing configured AuthManager with mock DB"""
    fake_db = FakeDB()
    monkeypatch.setattr(auth, "get_db_instance", lambda: fake_db)
    am = AuthManager()
    am.logger = MockLogger()  # Using a mock logger
    return am, fake_db


class MockLogger:
    """Mock logger for verification"""

    def __init__(self):
        self.logs = []

    def log_negocio(
        self,
        module: str,
        action: str,
        metadata: Optional[Dict] = None,
        level: str = "info",
    ):
        self.logs.append(
            {
                "module": module,
                "action": action,
                "metadata": metadata or {},
                "level": level,
            }
        )


def test_login_success(auth_manager):
    """Test successful login with correlation ID"""
    am, fake_db = auth_manager
    test_correlation_id = "test-corr-123"

    success = am.login(
        email="test@example.com",
        password="Ulala1234!",
        correlation_id=test_correlation_id,
    )

    assert success is True
    assert am.current_user is not None
    assert fake_db.updated is True
    assert fake_db.last_correlation_id == test_correlation_id
    assert "user_login" in fake_db.query_names

    # Verify password upgrade was logged
    upgrade_logs = [
        log for log in am.logger.logs if log["action"] == "password_upgraded"
    ]
    assert len(upgrade_logs) == 1
    assert upgrade_logs[0]["metadata"]["correlation_id"] == test_correlation_id


def test_login_failure(auth_manager):
    """Test failed login attempt"""
    am, fake_db = auth_manager

    success = am.login(
        email="test@example.com",
        password="wrongpassword",
        correlation_id="test-corr-456",
    )

    assert success is False
    assert am.current_user is None

    # Verify failed attempt was logged
    failure_logs = [log for log in am.logger.logs if log["action"] == "login_failed"]
    assert len(failure_logs) == 1
    assert failure_logs[0]["metadata"]["reason"] == "invalid_password"


def test_logout(auth_manager):
    """Test logout with correlation tracking"""
    am, fake_db = auth_manager
    test_correlation_id = "test-corr-789"

    # First login to set current user
    am.login("test@example.com", "Ulala1234!")
    assert am.current_user is not None

    # Then logout
    am.logout(correlation_id=test_correlation_id)
    assert am.current_user is None

    # Verify logout was logged
    logout_logs = [log for log in am.logger.logs if log["action"] == "logout"]
    assert len(logout_logs) == 1
    assert logout_logs[0]["metadata"]["correlation_id"] == test_correlation_id


def test_password_complexity(auth_manager):
    """Test password validation rules"""
    am, _ = auth_manager

    # Test weak password
    valid, reason = am.validate_password_complexity("weak")
    assert valid is False
    assert "at least 8 characters" in reason

    # Test valid password
    valid, _ = am.validate_password_complexity("StrongPass123!")
    assert valid is True


if __name__ == "__main__":
    pytest.main(["-v", __file__])
