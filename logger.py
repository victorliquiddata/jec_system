# logger.py
import logging
from pathlib import Path
from typing import Dict, Optional, Literal

LogLevel = Literal["info", "warning", "error", "debug"]


class JCELogger:
    """Logger centralizado para o sistema JEC com métodos tipados."""

    def __init__(self):
        self.log_dir = Path("logs")
        self._setup_logging_env()
        self.loggers: Dict[str, logging.Logger] = {
            "conexoes": self._create_logger("conexoes"),
            "logica": self._create_logger("logica"),
            "interface": self._create_logger("interface"),
        }

    def _setup_logging_env(self):
        """Cria diretório de logs (se não existir)."""
        self.log_dir.mkdir(exist_ok=True, parents=True)

    def _create_logger(self, name: str) -> logging.Logger:
        """Configura um logger individual com formatação padrão."""
        logger = logging.getLogger(f"jec.{name}")
        logger.handlers.clear()  # Evita duplicação de handlers

        file_handler = logging.FileHandler(
            self.log_dir / f"{name}.log", encoding="utf-8"
        )
        file_handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | %(module)s:%(funcName)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(file_handler)
        logger.setLevel(logging.DEBUG)
        return logger

    # Final logger fix
    def log_conexao(self, event_type, message, level="info", metadata=None):
        logger = self.loggers["conexoes"]
        getattr(logger, level)(
            f"[{event_type}] {message}",
            extra={"metadata": metadata} if metadata else {},
        )

    def log_negocio(
        self,
        module: str,
        action: str,
        metadata: Optional[Dict] = None,
        level: LogLevel = "debug",
    ) -> None:
        """Logs de lógica de negócio."""
        log_method = getattr(self.loggers["logica"], level)
        log_method(
            "{module}.{action}", extra={"metadata": metadata} if metadata else {}
        )

    def log_interface(
        self,
        component: str,
        event: str,
        user_ctx: Optional[Dict] = None,
        level: LogLevel = "info",
    ) -> None:
        """Logs de interação com a interface."""
        log_method = getattr(self.loggers["interface"], level)
        log_method(
            "UI:{component}.{event}", extra={"user": user_ctx} if user_ctx else {}
        )
