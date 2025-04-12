# test_main.py

import pytest
import time

import main
import auth
from auth import auth_manager
from rich_cli import cli


class FakeDB:
    def __init__(self):
        self.updated = False

    def execute_query(self, query, params=(), **kwargs):
        q = query.strip().upper()
        if q.startswith("SELECT * FROM USUARIOS"):
            return [
                {
                    "id": "test-id-123",
                    "email": "dddddd.ddddd@gggg.cccc",
                    "senha": "Ulala1234!",  # plaintext legacy password
                    "tipo": "juiz",
                }
            ]
        if q.startswith("SELECT ID, EMAIL, TIPO FROM USUARIOS"):
            return [
                {"id": "u1", "email": "user1@test.com", "tipo": "advogado"},
                {"id": "u2", "email": "user2@test.com", "tipo": "juiz"},
            ]
        if q.startswith("UPDATE USUARIOS SET SENHA"):
            self.updated = True
            return 1
        return []


@pytest.fixture(autouse=True)
def patch_environment(monkeypatch):
    fake_db = FakeDB()
    monkeypatch.setattr(auth, "get_db_instance", lambda: fake_db)
    monkeypatch.setattr(main, "get_db_instance", lambda: fake_db)

    monkeypatch.setattr(time, "sleep", lambda s: None)
    auth_manager.logout()

    monkeypatch.setattr(cli, "clear_screen", lambda: None)
    monkeypatch.setattr(cli, "display_header", lambda title: None)
    monkeypatch.setattr(cli, "display_main_menu", lambda options: None)

    statuses = []
    monkeypatch.setattr(
        cli, "display_status", lambda msg, status: statuses.append((msg, status))
    )

    data_tables = []
    monkeypatch.setattr(
        cli,
        "display_data_table",
        lambda data, title=None, **kwargs: data_tables.append((data, title)),
    )

    return {"statuses": statuses, "fake_db": fake_db, "data_tables": data_tables}


def test_main_login_success(patch_environment, monkeypatch):
    env = patch_environment

    inputs = iter(["1", "dddddd.ddddd@gggg.cccc", "Ulala1234!", "7"])  # login  # exit

    def safe_prompt(prompt, input_type=str, password=False, **kwargs):
        try:
            return input_type(next(inputs))
        except StopIteration:
            print(f"[TEST] Ran out of inputs at prompt: {prompt}")
            raise

    monkeypatch.setattr(cli, "prompt_input", safe_prompt)

    main.main()

    assert any("Login successful" in msg for msg, st in env["statuses"])
    assert env["fake_db"].updated


def test_main_list_users(patch_environment, monkeypatch):
    env = patch_environment

    inputs = iter(
        [
            "1",  # login
            "dddddd.ddddd@gggg.cccc",
            "Ulala1234!",
            "1",  # list users (changed from 2 -> 1)
            "",  # press Enter to continue
            "7",  # exit (changed from 0 -> 7)
        ]
    )

    def safe_prompt(prompt, input_type=str, password=False, **kwargs):
        try:
            return input_type(next(inputs))
        except StopIteration:
            print(f"[TEST] Ran out of inputs at prompt: {prompt}")
            raise

    monkeypatch.setattr(cli, "prompt_input", safe_prompt)

    main.main()

    assert env["data_tables"]
    data, title = env["data_tables"][0]
    assert title == "Usuários"
    assert len(data) == 2


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main(["-v", __file__]))
