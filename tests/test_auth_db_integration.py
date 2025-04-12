from auth import auth_manager
import pytest


def test_password_hashing_flow(test_db):
    # Insert test user directly
    test_db.execute(
        "INSERT INTO usuarios (email, senha) VALUES (?, ?)",
        ("test@jec.com", "plaintext"),
    )

    # Test login with legacy password
    assert auth_manager.login("test@jec.com", "plaintext") is True

    # Verify password was upgraded
    row = test_db.execute(
        "SELECT senha FROM usuarios WHERE email = ?", ("test@jec.com",)
    ).fetchone()
    assert row[0].startswith("pbkdf2:sha256")


def test_rbac_enforcement(test_db):
    # Insert test users
    test_db.executemany(
        "INSERT INTO usuarios (email, senha, tipo) VALUES (?, ?, ?)",
        [
            ("admin@jec.com", "hash1", "juiz"),
            ("clerk@jec.com", "hash2", "servidor"),
            ("visitor@jec.com", "hash3", "visitante"),
        ],
    )

    # Mock current user
    auth_manager.current_user = {"email": "visitor@jec.com", "tipo": "visitante"}

    # Verify permission denied
    with pytest.raises(PermissionError):
        # This would call the patched database.py
        auth_manager.create_user(...)  # Your RBAC-protected method
