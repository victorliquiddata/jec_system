import pytest
import auth
from auth import AuthManager


class FakeDB:
    """
    Fake database to simulate user lookup and password upgrade.
    """

    def __init__(self):
        self.updated = False

    def execute_query(self, query, params=None, return_results=False):
        # Simulate fetching user record with plaintext password
        if query.strip().upper().startswith("SELECT * FROM USUARIOS"):
            return [
                {
                    "id": "test-id-123",
                    "email": "dddddd.ddddd@gggg.cccc",
                    "senha": "Ulala1234!",  # legacy plaintext
                    "tipo": "juiz",
                }
            ]
        # Simulate updating the password hash
        if query.strip().upper().startswith("UPDATE USUARIOS SET SENHA"):
            new_hash, user_id = params
            # Verify new hash uses PBKDF2-SHA256
            assert new_hash.startswith("pbkdf2:sha256:"), "Password was not re-hashed"
            assert user_id == "test-id-123"
            self.updated = True
            return 1
        return []


def test_login_success(monkeypatch):
    # Monkeypatch get_db_instance in auth module to use our FakeDB
    fake_db = FakeDB()
    monkeypatch.setattr(auth, "get_db_instance", lambda: fake_db)

    am = AuthManager()
    success = am.login("dddddd.ddddd@gggg.cccc", "Ulala1234!")

    assert success is True, "Login should succeed with correct credentials"
    assert (
        am.current_user is not None
    ), "Current user should be set after successful login"
    assert am.current_user["email"] == "dddddd.ddddd@gggg.cccc"
    assert fake_db.updated, "Legacy password should be upgraded to a secure hash"


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main(["-v", __file__]))
