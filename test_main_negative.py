import pytest
import time

import main
import auth
from auth import auth_manager
from rich_cli import cli


# FakeDB stub for CPF validation test
class FakeDB:
    def execute_query(self, query, params=None, return_results=False):
        q = query.strip().upper()
        # Return a valid user record on login
        if q.startswith("SELECT * FROM USUARIOS"):
            return [
                {
                    "id": "test-id-123",
                    "email": "dddddd.ddddd@gggg.cccc",
                    "senha": "Ulala1234!",  # legacy plaintext
                    "tipo": "servidor",
                }
            ]
        if return_results:
            return []
        return 1


@pytest.fixture(autouse=True)
def patch_environment(monkeypatch):
    # Patch DB instance for auth and main modules
    fake_db = FakeDB()
    monkeypatch.setattr(auth, "get_db_instance", lambda: fake_db)
    monkeypatch.setattr(main, "get_db_instance", lambda: fake_db)
    # Speed up sleep calls
    monkeypatch.setattr(time, "sleep", lambda s: None)
    # Ensure clean auth state
    auth_manager.logout()
    # Stub CLI display methods
    monkeypatch.setattr(cli, "clear_screen", lambda: None)
    monkeypatch.setattr(cli, "display_header", lambda title: None)
    monkeypatch.setattr(cli, "display_main_menu", lambda opts: None)
    # Capture status messages
    statuses = []
    monkeypatch.setattr(
        cli, "display_status", lambda msg, status: statuses.append((msg, status))
    )
    return {"statuses": statuses}


def fake_prompt_factory(inputs):
    def fake_prompt(prompt, input_type=str, password=False):
        val = next(inputs)
        print(f"Prompted: {prompt} -> {val}")
        try:
            return input_type(val)
        except Exception:
            return str(val)

    return fake_prompt


def test_create_cpf_validation_loop(patch_environment, monkeypatch):
    env = patch_environment
    # Simulate login then create user with 3 invalid CPF attempts, then a valid one
    inputs = iter(
        [
            1,
            "dddddd.ddddd@gggg.cccc",
            "Ulala1234!",  # login
            2,  # choose Create user
            "abc",
            "123",
            "12345",
            "12345678901",  # CPF attempts (3 invalid + 1 valid)
            "Test User",
            "testuser@test.com",
            "TestPass1!",  # rest fields
            "juiz",
            "",  # perfil and skip phone
            7,  # exit authenticated
        ]
    )
    monkeypatch.setattr(cli, "prompt_input", fake_prompt_factory(inputs))

    main.main()

    # Extract just messages
    msgs = [m for m, _ in env["statuses"]]
    # Should warn three times about CPF length
    assert msgs.count("CPF must be 11 digits") == 3


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main(["-v", __file__]))
