# config.py
import os
import logging

from typing import Dict, Any
from dotenv import load_dotenv
from enum import Enum
from logger import JCELogger


# Carrega variáveis de ambiente
load_dotenv()


class Theme(str, Enum):
    """Esquemas de cores disponíveis"""

    PADRAO = "padrao"
    ESCURO = "escuro"


class AppConfig:
    """Configurações centrais da aplicação"""

    # Versão do sistema
    VERSION = "1.3"

    # Configurações de banco de dados
    DB_CONFIG = {
        "host": os.getenv("DB_HOST"),
        "port": os.getenv("DB_PORT"),
        "user": os.getenv("DB_USUARIO"),
        "password": os.getenv("DB_SENHA"),
        "database": os.getenv("DB_NOME"),
        "schema": os.getenv("DB_SCHEMA", "jec"),
        "min_connections": int(os.getenv("DB_MIN_CONNECTIONS", "1")),
        "max_connections": int(os.getenv("DB_MAX_CONNECTIONS", "5")),
    }

    # Configurações de autenticação
    AUTH = {
        "hashing_algorithm": "pbkdf2:sha256",
        "iterations": 600000,
        "session_timeout": 1800,  # 30 minutos em segundos
        "password_rules": {
            "min_length": 8,
            "require_upper": True,
            "require_lower": True,
            "require_digit": True,
            "require_special": True,
        },
    }

    LOG_LEVEL = logging.DEBUG  # Nível padrão
    LOG_ROTATION = "midnight"  # Rotação diária
    LOG_RETENTION = 30  # Dias de retenção

    # Esquemas de cores (para rich_cli.py)
    THEMES = {
        Theme.PADRAO: {
            "header": {"color": "#005F87", "border": "#003D5C"},
            "body": {"primary": "#333333", "secondary": "#666666"},
            "status": {
                "success": "#4CAF50",
                "warning": "#FFC107",
                "error": "#F44336",
                "info": "#2196F3",
            },
        },
        Theme.ESCURO: {
            "header": {"color": "#E0E0E0", "border": "#7A7A7A"},
            "body": {"primary": "#BDBDBD", "secondary": "#7A7A7A"},
            "status": {
                "success": "#66BB6A",
                "warning": "#E6A23C",
                "error": "#D32F2F",
                "info": "#2196F3",
            },
        },
    }

    @classmethod
    def load_theme(cls, theme_name: str = Theme.ESCURO) -> Dict[str, Any]:
        """Carrega configurações de tema"""
        try:
            return cls.THEMES[Theme(theme_name)]
        except ValueError:
            return cls.THEMES[Theme.ESCURO]

    @classmethod
    def get_db_dsn(cls) -> str:
        """Retorna DSN para conexão com banco"""
        return (
            f"host={cls.DB_CONFIG['host']} "
            f"port={cls.DB_CONFIG['port']} "
            f"user={cls.DB_CONFIG['user']} "
            f"password={cls.DB_CONFIG['password']} "
            f"dbname={cls.DB_CONFIG['database']} "
            f"options='-c search_path={cls.DB_CONFIG['schema']}'"
        )


# Teste de configuração (executa apenas quando rodado diretamente)
if __name__ == "__main__":
    print(f"Configuração do tema escuro: {AppConfig.load_theme()}")
    print(f"DSN do banco de dados: {AppConfig.get_db_dsn()}")
