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

    def test_theme_loading(self):
        """Testa carregamento de temas"""
        for theme in Theme:
            theme_config = AppConfig.load_theme(theme)
            assert isinstance(theme_config, dict)
            assert "header" in theme_config
            assert "body" in theme_config
            assert "status" in theme_config

    def test_default_theme_fallback(self):
        """Verifica fallback para tema padrão"""
        invalid_theme = "inexistente"
        theme_config = AppConfig.load_theme(invalid_theme)
        assert theme_config == AppConfig.THEMES[Theme.ESCURO]

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

    def test_theme_enum_values(self):
        """Verifica valores do enum Theme"""
        assert Theme.PADRAO.value == "padrao"
        assert Theme.ESCURO.value == "escuro"
        assert len(Theme) == 2


if __name__ == "__main__":
    pytest.main(["-v", __file__])
