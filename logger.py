# logger.py - version 5 (Final Integration)
import logging
from pathlib import Path
from typing import Dict, Optional, Literal, Any, Union

LogLevel = Literal["info", "warning", "error", "debug"]


class JCELogger:
    """Enhanced centralized logger for JEC system with rich_cli integration"""

    def __init__(self):
        self.log_dir = Path("logs")
        self._setup_logging_env()
        self.loggers = {
            "conexoes": self._create_logger("conexoes"),
            "logica": self._create_logger("logica"),
            "interface": self._create_interface_logger(),  # Special format for UI
        }
        self._valid_levels = {"debug", "info", "warning", "error"}

    def _create_interface_logger(self) -> logging.Logger:
        """Special logger for UI events with enhanced formatting"""
        logger = logging.getLogger("jec.interface")
        logger.handlers.clear()

        handler = logging.FileHandler(self.log_dir / "interface.log", encoding="utf-8")
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | UI:%(message)s | %(extra)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        return logger

    def _setup_logging_env(self):
        """Ensure log directory exists"""
        self.log_dir.mkdir(exist_ok=True, parents=True)

    def _create_logger(self, name: str) -> logging.Logger:
        """Standard logger creator"""
        logger = logging.getLogger(f"jec.{name}")
        logger.handlers.clear()

        handler = logging.FileHandler(self.log_dir / f"{name}.log", encoding="utf-8")
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | %(module)s:%(funcName)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        return logger

    def _safe_get_level(self, level: str) -> str:
        """Validate log level with fallback to debug"""
        return level if level in self._valid_levels else "debug"

    def log_conexao(
        self,
        event_type: str,
        message: str,
        level: LogLevel = "info",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log database connections and operations"""
        log_method = getattr(self.loggers["conexoes"], self._safe_get_level(level))
        log_method(
            f"[{event_type}] {message}",
            extra={"metadata": metadata} if metadata else {},
        )

    def log_negocio(
        self,
        module: str,
        action: str,
        metadata: Optional[Dict[str, Any]] = None,
        level: LogLevel = "debug",
    ) -> None:
        """Log business logic events"""
        log_method = getattr(self.loggers["logica"], self._safe_get_level(level))
        log_method(
            f"{module}.{action}", extra={"metadata": metadata} if metadata else {}
        )

    def log_interface(
        self,
        component: str,
        event: str,
        user_ctx: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        level: LogLevel = "info",
    ) -> None:
        """Enhanced UI event logging for rich_cli integration"""
        log_method = getattr(self.loggers["interface"], self._safe_get_level(level))

        # Prepare structured log data
        log_data = {
            "component": component,
            "event": event,
            **({"user": user_ctx} if user_ctx else {}),
            **({"meta": metadata} if metadata else {}),
        }

        log_method(f"{component}.{event}", extra={"extra": log_data})
