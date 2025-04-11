import pytest
import time

import main
import auth
from auth import auth_manager
from rich_cli import cli


# FakeDB to simulate user lookup, password upgrade, and user listing
class FakeDB:
    def __init__(self):
        self.updated = False

    def execute_query(self, query, params=None, return_results=False):
        q = query.strip().upper()
        # Simulate fetching user record for login
        if q.startswith("SELECT * FROM USUARIOS"):
            return [
                {
                    "id": "test-id-123",
                    "email": "dddddd.ddddd@gggg.cccc",
                    "senha": "Ulala1234!",  # legacy plaintext
                    "tipo": "juiz",
                }
            ]
        # Simulate listing users
        if q.startswith("SELECT ID, EMAIL, TIPO FROM USUARIOS"):
            return [
                {"id": "u1", "email": "user1@test.com", "tipo": "advogado"},
                {"id": "u2", "email": "user2@test.com", "tipo": "juiz"},
            ]
        # Simulate updating the password hash
        if q.startswith("UPDATE USUARIOS SET SENHA"):
            self.updated = True
            return 1
        return []


@pytest.fixture(autouse=True)
def patch_environment(monkeypatch):
    # Patch DB instance for auth and main modules
    fake_db = FakeDB()
    monkeypatch.setattr(auth, "get_db_instance", lambda: fake_db)
    monkeypatch.setattr(main, "get_db_instance", lambda: fake_db)

    # Patch time.sleep to speed up test
    monkeypatch.setattr(time, "sleep", lambda s: None)

    # Ensure no prior user is logged in
    auth_manager.logout()

    # Patch CLI I/O methods
    monkeypatch.setattr(cli, "clear_screen", lambda: None)
    monkeypatch.setattr(cli, "display_header", lambda title: None)
    monkeypatch.setattr(cli, "display_main_menu", lambda options: None)

    # Capture statuses
    statuses = []
    monkeypatch.setattr(
        cli, "display_status", lambda msg, status: statuses.append((msg, status))
    )

    # Capture data table output
    data_tables = []
    monkeypatch.setattr(
        cli,
        "display_data_table",
        lambda data, title=None: data_tables.append((data, title)),
    )

    # Default prompt sequence (login then exit)
    inputs = iter([1, "dddddd.ddddd@gggg.cccc", "Ulala1234!", 7])

    def fake_prompt(prompt, input_type=str, password=False):
        return next(inputs)

    monkeypatch.setattr(cli, "prompt_input", fake_prompt)

    return {"statuses": statuses, "fake_db": fake_db, "data_tables": data_tables}


def test_main_login_success(patch_environment):
    env = patch_environment
    main.main()

    # Check that login success was shown
    assert any(
        "Login successful" in msg for msg, st in env["statuses"]
    ), "Expected a 'Login successful' status message"
    # Verify that the legacy password was upgraded
    assert env["fake_db"].updated, "Expected legacy password to be upgraded in DB"


def test_main_list_users(patch_environment, monkeypatch):
    env = patch_environment
    # Override prompt_input to simulate: login, list users, press Enter, then exit
    inputs = iter([1, "dddddd.ddddd@gggg.cccc", "Ulala1234!", 1, "", 7])
    monkeypatch.setattr(
        cli, "prompt_input", lambda prompt, input_type=str, password=False: next(inputs)
    )

    main.main()

    # Verify listing users displayed the expected table
    assert env["data_tables"], "Expected display_data_table to be called"
    data, title = env["data_tables"][0]
    assert title == "Usuários", "Expected table title 'Usuários'"
    assert isinstance(data, list) and len(data) == 2, "Expected two users in the list"
    emails = [row["email"] for row in data]
    assert "user1@test.com" in emails and "user2@test.com" in emails


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main(["-v", __file__]))
