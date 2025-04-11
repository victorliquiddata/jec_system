# test_config.py
import pytest
from config import AppConfig, Theme
from unittest.mock import patch
import os


class TestAppConfig:
    """Testes unitários para a classe AppConfig"""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Fixture para salvar e restaurar configurações originais"""
        original_db_config = AppConfig.DB_CONFIG.copy()
        yield
        # Restaura configurações após cada teste
        AppConfig.DB_CONFIG = original_db_config

    def test_version_constant(self):
        """Verifica se a versão está definida corretamente"""
        assert hasattr(AppConfig, "VERSION")
        assert isinstance(AppConfig.VERSION, str)
        assert len(AppConfig.VERSION.split(".")) >= 2

    def test_db_config_structure(self):
        """Verifica a estrutura da configuração de banco de dados"""
        db_config = AppConfig.DB_CONFIG
        assert isinstance(db_config, dict)
        required_keys = ["host", "port", "user", "password", "database", "schema"]
        assert all(key in db_config for key in required_keys)

    def test_auth_config(self):
        """Verifica parâmetros de autenticação"""
        auth = AppConfig.AUTH
        assert auth["hashing_algorithm"] == "pbkdf2:sha256"
        assert auth["iterations"] == 600000
        assert isinstance(auth["password_rules"], dict)

    def test_theme_enum_values(self):
        """Verifica valores do enum Theme"""
        assert Theme.ESCURO.value == "escuro"
        assert Theme.CLARO.value == "claro"
        assert Theme.PADRAO.value == "padrao"
        assert len(Theme) == 3  # Now includes PADRAO, ESCURO and CLARO

    def test_theme_configurations(self):
        """Verifica se todos os temas têm a estrutura correta"""
        for theme in Theme:
            theme_config = AppConfig.THEMES[theme]
            assert isinstance(theme_config, dict)
            assert "header" in theme_config
            assert "body" in theme_config
            assert "status" in theme_config

            # Verify specific color values
            if theme == Theme.ESCURO:
                assert theme_config["header"]["color"] == "#E0E0E0"
            elif theme == Theme.CLARO:
                assert theme_config["header"]["color"] == "#333333"
            elif theme == Theme.PADRAO:
                assert theme_config["header"]["color"] == "#005F87"

    def test_load_theme_method(self):
        """Testa o método load_theme"""
        # Test with enum values
        assert AppConfig.load_theme(Theme.ESCURO) == Theme.ESCURO
        assert AppConfig.load_theme(Theme.CLARO) == Theme.CLARO
        assert AppConfig.load_theme(Theme.PADRAO) == Theme.PADRAO

        # Test with string values
        assert AppConfig.load_theme("escuro") == Theme.ESCURO
        assert AppConfig.load_theme("claro") == Theme.CLARO
        assert AppConfig.load_theme("padrao") == Theme.PADRAO

        # Test case insensitivity
        assert AppConfig.load_theme("ESCURO") == Theme.ESCURO
        assert AppConfig.load_theme("CLARO") == Theme.CLARO

        # Test fallback to ESCURO for invalid theme
        assert AppConfig.load_theme("invalid") == Theme.ESCURO

    def test_get_db_dsn(self):
        """Verifica geração correta do DSN"""
        # Configuração de teste isolada
        test_config = {
            "host": "testhost",
            "port": "9999",
            "user": "testuser",
            "password": "testpass",
            "database": "testdb",
            "schema": "testschema",
        }

        # Substitui temporariamente a configuração
        original_config = AppConfig.DB_CONFIG
        AppConfig.DB_CONFIG = test_config

        try:
            dsn = AppConfig.get_db_dsn()
            assert "host=testhost" in dsn
            assert "port=9999" in dsn
            assert "user=testuser" in dsn
            assert "password=testpass" in dsn
            assert "dbname=testdb" in dsn
            assert "options='-c search_path=testschema'" in dsn
        finally:
            # Restaura configuração original
            AppConfig.DB_CONFIG = original_config


if __name__ == "__main__":
    pytest.main(["-v", __file__])
