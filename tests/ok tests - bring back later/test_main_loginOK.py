import pytest
import time

import main
import auth
from auth import auth_manager
from rich_cli import cli


# FakeDB to simulate user lookup and password upgrade
class FakeDB:
    def __init__(self):
        self.updated = False

    def execute_query(
        self,
        query,
        params=None,
        return_results=False,
        correlation_id=None,
        query_name=None,
    ):
        # Simulate fetching user record
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

    # Provide sequence of inputs: login choice, email, password, then exit choice
    inputs = iter([1, "dddddd.ddddd@gggg.cccc", "Ulala1234!", 7])

    def fake_prompt(prompt, input_type=str, password=False):
        return next(inputs)

    monkeypatch.setattr(cli, "prompt_input", fake_prompt)

    # Expose captured statuses and fake_db to tests
    return {"statuses": statuses, "fake_db": fake_db}


def test_main_login_success(patch_environment):
    env = patch_environment
    # Run main loop (will login then exit)
    main.main()

    # Check that login success was shown
    assert any(
        "Login successful" in msg for msg, st in env["statuses"]
    ), "Expected a 'Login successful' status message"

    # Verify that the legacy password was upgraded
    assert env["fake_db"].updated, "Expected legacy password to be upgraded in DB"


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main(["-v", __file__]))
