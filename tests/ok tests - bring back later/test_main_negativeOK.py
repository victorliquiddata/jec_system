import pytest
import time

import main
import auth
from auth import auth_manager
from rich_cli import cli


# FakeDB stub that matches current main.py expectations
class FakeDB:
    def __init__(self):
        self.queries = []

    def execute_query(
        self,
        query,
        params=(),
        return_results=False,
        correlation_id=None,
        query_name=None,
    ):
        self.queries.append((query, params, correlation_id, query_name))
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

    # Mock AppConfig.generate_correlation_id to return a consistent value
    monkeypatch.setattr(
        main.AppConfig, "generate_correlation_id", lambda: "test-correlation-id"
    )

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

    return {"statuses": statuses, "fake_db": fake_db}


def fake_prompt_factory(inputs):
    def fake_prompt(prompt, input_type=str, password=False, **kwargs):
        try:
            val = next(inputs)
            print(f"Prompted: {prompt} -> {val}")
            return input_type(val)
        except StopIteration:
            print(f"[TEST] Ran out of inputs at prompt: {prompt}")
            raise
        except Exception:
            return str(val)

    return fake_prompt


def test_create_cpf_validation_loop(patch_environment, monkeypatch):
    env = patch_environment

    # Simulate login then create user with 3 invalid CPF attempts, then a valid one
    inputs = iter(
        [
            "1",  # Choose Login
            "dddddd.ddddd@gggg.cccc",
            "Ulala1234!",  # Login credentials
            "2",  # Choose Create user
            "abc",  # Invalid CPF (not digits)
            "123",  # Invalid CPF (too short)
            "12345",  # Invalid CPF (too short)
            "12345678901",  # Valid CPF (11 digits)
            "Test User",  # Full name
            "testuser@test.com",  # Email
            "TestPass1!",  # Password
            "juiz",  # Profile type
            "",  # Phone (skip)
            "7",  # Exit
        ]
    )

    monkeypatch.setattr(cli, "prompt_input", fake_prompt_factory(inputs))

    # Run the main function
    main.main()

    # Extract just messages
    msgs = [m for m, s in env["statuses"]]

    # Should warn three times about CPF length
    assert msgs.count("CPF must be 11 digits") == 3

    # Verify login successful status was shown
    assert "Login successful" in msgs


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main(["-v", __file__]))
