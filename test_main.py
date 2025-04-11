# test_main.py
import pytest
import time
from main import main
from auth import auth_manager
from rich_cli import cli


# Disable actual sleeping to speed up tests
@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda x: None)


class DummyCLI:
    """A dummy CLI to capture inputs and status messages."""

    def __init__(self):
        self.inputs = []
        self.statuses = []

    def clear_screen(self):
        pass

    def display_header(self, title):
        pass

    def display_main_menu(self, options):
        pass

    def prompt_input(self, label, *args, **kwargs):
        # Return the next preloaded input
        return self.inputs.pop(0)

    def display_status(self, message, level="info"):
        # Capture status messages for assertions
        self.statuses.append((message, level))


def setup_dummy_cli(monkeypatch, dummy: DummyCLI):
    """Monkeypatch the real CLI methods to use our dummy."""
    monkeypatch.setattr(cli, "clear_screen", dummy.clear_screen)
    monkeypatch.setattr(cli, "display_header", dummy.display_header)
    monkeypatch.setattr(cli, "display_main_menu", dummy.display_main_menu)
    monkeypatch.setattr(cli, "prompt_input", dummy.prompt_input)
    monkeypatch.setattr(cli, "display_status", dummy.display_status)


def test_guest_exit(monkeypatch):
    """Guest chooses 'Exit' and the application should terminate cleanly."""
    dummy = DummyCLI()
    dummy.inputs = [2]  # Guest menu: 1=Login, 2=Exit
    setup_dummy_cli(monkeypatch, dummy)

    main()

    # Should have displayed 'Exiting...' and then 'Goodbye!'
    assert ("Exiting...", "info") in dummy.statuses
    assert ("Goodbye!", "info") in dummy.statuses


def test_authenticated_exit(monkeypatch):
    """Authenticated user chooses 'Exit' and the application should terminate."""
    # Simulate a logged-in user
    user = {"id": 1, "email": "user@test.com", "perfil": "servidor"}
    monkeypatch.setattr(auth_manager, "get_current_user", lambda: user)
    cli.user_context = user

    dummy = DummyCLI()
    dummy.inputs = [7]  # Authenticated menu: 7=Exit
    setup_dummy_cli(monkeypatch, dummy)

    main()

    assert ("Exiting...", "info") in dummy.statuses
    assert ("Goodbye!", "info") in dummy.statuses


def test_login_lockout(monkeypatch):
    """After 3 failed login attempts, the account should be locked."""
    dummy = DummyCLI()
    email = "fail@test.com"

    # Sequence: three login attempts (choice=1,email,password), then exit (choice=2)
    dummy.inputs = [
        1,
        email,
        "wrong",  # Attempt 1
        1,
        email,
        "wrong",  # Attempt 2
        1,
        email,
        "wrong",  # Attempt 3 -> lockout
        2,  # Then choose Exit
    ]
    setup_dummy_cli(monkeypatch, dummy)

    # Force all login attempts to fail
    monkeypatch.setattr(auth_manager, "login", lambda e, p: False)

    main()

    # Expect a lockout message after 3 failures
    assert any("Locked for" in msg for msg, lvl in dummy.statuses)


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main(["-v", __file__]))
