import pytest
import time

import main
import auth
from auth import auth_manager
from rich_cli import cli


# FakeDB to simulate all database interactions
class FakeDB:
    def __init__(self):
        self.senha_calls = 0
        self.updated_legacy = False
        self.created = False
        self.updated_user = False
        self.deleted_user = False
        self.password_changed = False

    def execute_query(
        self,
        query,
        params=None,
        return_results=False,
        correlation_id=None,
        query_name=None,
    ):
        q = query.strip().upper()
        # 1) Login fetch
        if q.startswith("SELECT * FROM USUARIOS"):
            return [
                {
                    "id": "test-id-123",
                    "email": "dddddd.ddddd@gggg.cccc",
                    "senha": "Ulala1234!",  # legacy plaintext
                    "tipo": "juiz",
                }
            ]
        # 2) Legacy password upgrade or self-service password change
        if q.startswith("UPDATE USUARIOS SET SENHA"):
            self.senha_calls += 1
            if self.senha_calls == 1:
                self.updated_legacy = True
            elif self.senha_calls == 2:
                self.password_changed = True
            return 1
        # 3) List users
        if q.startswith("SELECT ID, EMAIL, TIPO FROM USUARIOS"):
            return [
                {"id": "u1", "email": "user1@test.com", "tipo": "advogado"},
                {"id": "u2", "email": "user2@test.com", "tipo": "juiz"},
            ]
        # 4) Create user
        if q.startswith("INSERT INTO USUARIOS"):
            self.created = True
            return 1
        # 5) Check existence for update/delete
        if q.startswith("SELECT ID FROM USUARIOS"):
            return [{"id": params[0]}]
        # 6) Update user
        if q.startswith("UPDATE USUARIOS SET EMAIL"):
            self.updated_user = True
            return 1
        # 7) Delete audit log
        if q.startswith("DELETE FROM AUDIT_LOG"):
            return 1
        # 8) Delete user
        if q.startswith("DELETE FROM USUARIOS"):
            self.deleted_user = True
            return 1
        return []


@pytest.fixture(autouse=True)
def patch_environment(monkeypatch):
    # Patch DB instance for auth and main modules
    fake_db = FakeDB()
    monkeypatch.setattr(auth, "get_db_instance", lambda: fake_db)
    monkeypatch.setattr(main, "get_db_instance", lambda: fake_db)

    # Speed up sleeps
    monkeypatch.setattr(time, "sleep", lambda s: None)

    # Ensure clean auth state
    auth_manager.logout()

    # Stub CLI display methods
    monkeypatch.setattr(cli, "clear_screen", lambda: None)
    monkeypatch.setattr(cli, "display_header", lambda title: None)
    monkeypatch.setattr(cli, "display_main_menu", lambda opts: None)

    # Capture statuses and tables
    statuses = []
    monkeypatch.setattr(
        cli, "display_status", lambda msg, status: statuses.append((msg, status))
    )
    data_tables = []
    monkeypatch.setattr(
        cli,
        "display_data_table",
        lambda data, title=None: data_tables.append((data, title)),
    )

    return {"fake_db": fake_db, "statuses": statuses, "data_tables": data_tables}


def test_main_full_flow(patch_environment, monkeypatch):
    env = patch_environment
    # Sequence of menu interactions:
    # 1: Login
    # 1: List users, '' to return
    # 2: Create user (CPF, name, email, password, perfil, skip phone)
    # 3: Update user (id 'u1')
    # 4: Delete user (id 'u2', confirm YES)
    # 5: Change password (current legacy, new)
    # 6: Logout
    # 2: Exit from guest
    inputs = iter(
        [
            1,
            "dddddd.ddddd@gggg.cccc",
            "Ulala1234!",
            1,
            "",
            2,
            "12345678901",
            "Test User",
            "testuser@test.com",
            "TestPass1!",
            "servidor",
            "",
            3,
            "u1",
            "updated@test.com",
            "advogado",
            4,
            "u2",
            "YES",
            5,
            "Ulala1234!",
            "NewPass1!",
            6,
            2,
        ]
    )
    monkeypatch.setattr(
        cli, "prompt_input", lambda prompt, input_type=str, password=False: next(inputs)
    )

    main.main()

    # Verify all DB operations occurred
    assert env["fake_db"].updated_legacy, "Legacy password should be upgraded"
    assert env["fake_db"].created, "User creation should be invoked"
    assert env["fake_db"].updated_user, "User update should be invoked"
    assert env["fake_db"].deleted_user, "User deletion should be invoked"
    assert env["fake_db"].password_changed, "Password change should be invoked"

    # Verify status messages
    msgs = [m for m, _ in env["statuses"]]
    assert "Login successful" in msgs
    assert "User created successfully" in msgs
    assert "User updated" in msgs
    assert "User deleted" in msgs
    assert "Password changed" in msgs
    assert "Logged out" in msgs
    assert "Exiting..." in msgs


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main(["-v", __file__]))
