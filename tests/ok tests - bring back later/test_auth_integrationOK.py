import pytest
from unittest.mock import patch, MagicMock
from auth import AuthManager


@pytest.fixture
def mock_db():
    mock_instance = MagicMock()
    # Patch where get_db_instance is *used*, not where it's *defined*
    with patch("auth.get_db_instance", return_value=mock_instance):
        yield mock_instance


class TestAuthManager:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.auth = AuthManager()
        self.auth.current_user = None  # Reset session between tests

    def test_password_hashing(self):
        """Test PBKDF2 password hashing with salt generation"""
        password = "securePassword123!"
        hashed = self.auth.hash_password(password)

        assert hashed.startswith("pbkdf2:sha256:600000$")
        # Expect 3 parts: algorithm, salt, and hash
        assert len(hashed.split("$")) == 3
        assert self.auth.verify_password(hashed, password)

    @pytest.mark.parametrize(
        "password, expected, message",
        [
            ("Short1!", False, "Minimum length"),
            ("nouppercase123!", False, "Missing uppercase"),
            ("NOLOWERCASE123!", False, "Missing lowercase"),
            ("NoDigits!", False, "Missing digits"),
            ("ValidPass123!", True, "Valid password"),
            ("Another$Valid1", True, "Valid complex password"),
        ],
    )
    def test_password_complexity(self, password, expected, message):
        """Test password complexity rules enforcement"""
        valid, msg = self.auth.validate_password_complexity(password)
        assert valid == expected, message

    @patch("auth.get_db_instance")  # Patch where it's USED, not where it's defined
    def test_successful_login(self, mock_get_db_instance):
        """Test successful authentication with legacy password migration"""

        # Create a mock DB instance
        mock_db = MagicMock()

        # Return it when get_db_instance() is called
        mock_get_db_instance.return_value = mock_db

        # Prepare a legacy user (plaintext password)
        mock_user = {
            "id": "test-uuid",
            "email": "test@example.com",
            "senha": "legacy_plain_password",  # legacy plaintext
            "perfil": "advogado",
        }

        # First call returns the SELECT query result
        mock_db.execute_query.return_value = [mock_user]

        # Initialize auth using the patched DB
        auth = AuthManager()

        # Test login with correct credentials
        assert auth.login("test@example.com", "legacy_plain_password") is True

        # There should be at least two calls:
        # 1. SELECT to check credentials
        # 2. UPDATE to hash+save the password
        assert mock_db.execute_query.call_count >= 2

        # Verify the second call is the UPDATE query
        update_call = mock_db.execute_query.call_args_list[1]
        query_executed = update_call[0][0]
        update_params = update_call[0][1]

        assert query_executed.startswith("UPDATE usuarios SET senha = %s")

        # Check the hash starts with expected secure prefix
        new_hash = update_params[0]
        assert new_hash.startswith("pbkdf2:sha256:600000$")

        # Also confirm the user was set
        assert auth.current_user["email"] == "test@example.com"

    def test_failed_login(self, mock_db):
        """Test failed authentication scenarios"""
        # Case 1: No user found
        mock_db.return_value = [
            {
                "id": 1,
                "email": "legacy@example.com",
                "senha": "plain_legacy_password",  # stored as plaintext
            }
        ]
        assert self.auth.login("wrong@example.com", "wrongpass") is False
        assert self.auth.current_user is None

        # Case 2: User found but password incorrect
        mock_user = {
            "id": "valid-uuid",
            "email": "valid@example.com",
            "senha": self.auth.hash_password("correctPassword123!"),
            "perfil": "servidor",
        }
        mock_db.execute_query.return_value = [mock_user]
        assert self.auth.login("valid@example.com", "wrongPassword") is False
        assert self.auth.current_user is None

    def test_logout(self):
        """Test session termination"""
        self.auth.current_user = {"email": "test@example.com"}
        self.auth.logout()
        assert self.auth.current_user is None

    def test_legacy_password_migration(self, mock_db):
        """Test automatic migration of legacy plaintext passwords"""
        # Prepare a legacy user (plaintext password)
        mock_user = {
            "id": "legacy-uuid",
            "email": "legacy@example.com",
            "senha": "old_plain_password",
            "perfil": "juiz",
        }
        mock_db.execute_query.return_value = [mock_user]

        # Login should succeed and trigger migration
        assert self.auth.login("legacy@example.com", "old_plain_password") is True

        # There should be at least two execute_query calls:
        # 1. SELECT and 2. UPDATE migration
        assert mock_db.execute_query.call_count >= 2

        update_call = mock_db.execute_query.call_args_list[1]
        query_executed = update_call[0][0]
        update_params = update_call[0][1]
        assert "UPDATE usuarios SET senha = %s" in query_executed
        new_hash = update_params[0]
        assert new_hash.startswith("pbkdf2:sha256:600000$")
        # Verify the new hash matches the provided password
        assert self.auth.verify_password(new_hash, "old_plain_password")


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main(["-v", __file__]))
