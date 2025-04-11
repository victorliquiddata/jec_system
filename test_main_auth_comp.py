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

    def execute_query(self, query, params=None, return_results=False):
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
    fake_db = FakeDB()
    # Patch DB instance for auth and main
    monkeypatch.setattr(auth, "get_db_instance", lambda: fake_db)
    monkeypatch.setattr(main, "get_db_instance", lambda: fake_db)
    # Speed up sleeps
    monkeypatch.setattr(time, "sleep", lambda s: None)
    # Clean auth state
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


def fake_prompt_factory(inputs):
    """
    Returns a fake prompt_input that casts values to the expected type.
    """

    def fake_prompt(prompt, input_type=str, password=False):
        val = next(inputs)
        try:
            return input_type(val)
        except Exception:
            return val

    return fake_prompt


def test_main_full_flow(patch_environment, monkeypatch):
    env = patch_environment
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


def test_login_lockout(patch_environment, monkeypatch):
    env = patch_environment
    # Force login to always fail
    monkeypatch.setattr(auth_manager, "login", lambda e, p: False)
    auth_manager.logout()
    inputs = iter(
        [
            1,
            "user@test.com",
            "bad",  # 1st
            1,
            "user@test.com",
            "bad",  # 2nd
            1,
            "user@test.com",
            "bad",  # 3rd
            1,
            "user@test.com",
            "bad",  # lockout check
            2,  # exit
        ]
    )
    monkeypatch.setattr(
        cli, "prompt_input", lambda prompt, input_type=str, password=False: next(inputs)
    )
    main.main()
    msgs = [m for m, _ in env["statuses"]]
    assert "Too many attempts. Locked for 300s" in msgs
    assert any("Account locked" in m for m in msgs)


def test_invalid_option_guest(patch_environment, monkeypatch):
    env = patch_environment
    inputs = iter([3, 2])
    monkeypatch.setattr(
        cli, "prompt_input", lambda prompt, input_type=str, password=False: next(inputs)
    )
    main.main()
    msgs = [m for m, _ in env["statuses"]]
    assert "Invalid option" in msgs


def test_invalid_option_auth(patch_environment, monkeypatch):
    env = patch_environment
    monkeypatch.setattr(auth_manager, "login", lambda e, p: True)
    monkeypatch.setattr(
        auth_manager,
        "get_current_user",
        lambda: {"id": "x", "email": "a", "senha": "h", "tipo": "juiz"},
    )
    inputs = iter([1, "a", "b", 9, 7])
    monkeypatch.setattr(
        cli, "prompt_input", lambda prompt, input_type=str, password=False: next(inputs)
    )
    main.main()
    msgs = [m for m, _ in env["statuses"]]
    assert "Invalid option" in msgs


def test_permission_denied_flows(patch_environment, monkeypatch):
    # Start already authenticated as advogado
    auth_manager.current_user = {
        "id": "x",
        "email": "a",
        "senha": "h",
        "tipo": "advogado",
    }
    monkeypatch.setattr(
        auth_manager, "get_current_user", lambda: auth_manager.current_user
    )
    # Sequence: create, update, delete, logout, exit guest
    inputs = iter([2, 3, 4, 6, 2])
    monkeypatch.setattr(cli, "prompt_input", fake_prompt_factory(inputs))

    main.main()
    msgs = [m for m, _ in patch_environment["statuses"]]
    # Should see exactly three 'Permission denied'
    assert msgs.count("Permission denied") == 3


def test_validate_password_complexity():
    am = auth_manager.__class__()
    tests = [
        ("short", False),
        ("alllowercase1!", False),
        ("ALLUPPERCASE1!", False),
        ("NoDigits!!", False),
        ("NoSpecial123", False),
        ("Valid1!", False),  # too short
        ("ValidPass1!", True),
    ]
    for pw, expected in tests:
        valid, _ = am.validate_password_complexity(pw)
        assert valid is expected


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main(["-v", __file__]))
