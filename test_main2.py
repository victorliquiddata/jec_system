# test_main2.py
import pytest
import time
from unittest import mock
from datetime import datetime, timedelta

import main


@pytest.fixture
def setup_mocks(monkeypatch):
    """Patch key components: auth_manager, cli, db, logger, and time.sleep."""

    # --- 1. Fake DB ---
    class FakeDB:
        def __init__(self):
            self.usuarios = [
                {"id": 1, "email": "admin@jec.com", "perfil": "juiz", "senha": "hashed"}
            ]

        def execute_query(self, query, params=None, return_results=False):
            if "SELECT" in query:
                return self.usuarios
            if "INSERT" in query:
                self.usuarios.append(
                    {
                        "id": len(self.usuarios) + 1,
                        "email": params[0],
                        "senha": params[1],
                        "perfil": params[2],
                    }
                )
                return
            if "UPDATE" in query:
                # params: (email, perfil, id)
                for u in self.usuarios:
                    if u["id"] == params[2]:
                        u["email"], u["perfil"] = params[0], params[1]
                return
            if "DELETE" in query:
                # params: (id,)
                self.usuarios = [u for u in self.usuarios if u["id"] != params[0]]
                return

    # --- 2. Auth Manager Mock ---
    fake_user = {"id": 1, "email": "admin@jec.com", "perfil": "juiz", "senha": "hashed"}
    auth_manager_mock = mock.MagicMock()
    # Keep track of current_user on the mock
    auth_manager_mock.current_user = None

    # login() should set current_user to fake_user
    def login_side_effect(email, senha):
        auth_manager_mock.current_user = fake_user
        return True

    auth_manager_mock.login.side_effect = login_side_effect
    # get_current_user() just returns the attribute
    auth_manager_mock.get_current_user.side_effect = (
        lambda: auth_manager_mock.current_user
    )

    # logout() should clear current_user
    def logout_side_effect():
        auth_manager_mock.current_user = None

    auth_manager_mock.logout.side_effect = logout_side_effect

    # Complexity, verify, hash all just stubbed
    auth_manager_mock.validate_password_complexity.return_value = (True, "")
    auth_manager_mock.verify_password.return_value = True
    auth_manager_mock.hash_password.return_value = "hashed"

    # --- 3. CLI Mock ---
    cli_mock = mock.MagicMock()
    # Prepare exactly 6 inputs:
    # 1: guest choice=1 (login)
    # 2: email
    # 3: password
    # 4: auth choice=1 (list users)
    # 5: auth choice=6 (logout)
    # 6: guest choice=2 (exit)
    inputs = iter(
        [
            "1",  # guest -> login
            "admin@jec.com",  # email
            "password",  # password
            "1",  # auth -> list users
            "6",  # auth -> logout
            "2",  # guest -> exit
        ]
    )

    def prompt_input_side_effect(label, *args, **kwargs):
        raw = next(inputs)
        # if input_type=int was passed
        if args and args[0] is int:
            return int(raw)
        return raw

    cli_mock.prompt_input.side_effect = prompt_input_side_effect
    # no-ops for other methods
    for method in (
        "display_status",
        "display_main_menu",
        "display_data_table",
        "clear_screen",
        "display_header",
    ):
        setattr(cli_mock, method, lambda *a, **k: None)

    # --- 4. Logger Mock ---
    logger_mock = mock.MagicMock()

    # --- 5. time.sleep no-op ---
    monkeypatch.setattr(main.time, "sleep", lambda s: None)

    # --- 6. Apply all monkeypatches ---
    monkeypatch.setattr(main, "get_db_instance", lambda: FakeDB())
    monkeypatch.setattr(main, "auth_manager", auth_manager_mock)
    monkeypatch.setattr(main, "cli", cli_mock)
    monkeypatch.setattr(main, "JCELogger", lambda *args, **kwargs: logger_mock)


def test_main_full_flow(setup_mocks):
    """Run the entire main() loop through login → list → logout → exit."""
    # Should complete without errors
    main.main()


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main(["-v", __file__]))
