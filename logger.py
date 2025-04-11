# logger.py - version 5
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Literal, Any

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
        """Specialized logger for UI events with structured JSON formatting"""
        logger = logging.getLogger("jec.interface")
        logger.handlers.clear()

        handler = logging.FileHandler(self.log_dir / "interface.log", encoding="utf-8")

        class UIFormatter(logging.Formatter):
            """Custom formatter for Rich CLI events"""

            def format(self, record):
                # Base log entry
                log_entry = {
                    "timestamp": self.formatTime(record),
                    "level": record.levelname,
                    "component": getattr(record, "component", "unknown"),
                    "event": getattr(record, "event", "unknown"),
                    "user": getattr(record, "user_id", None),
                    "session": getattr(record, "session_id", None),
                    "metadata": getattr(record, "metadata", {}),
                }

                # Add execution context if available
                if hasattr(record, "execution_context"):
                    log_entry.update(
                        {
                            "render_time_ms": getattr(record, "render_time", 0),
                            "ui_element": getattr(record, "ui_element", "generic"),
                        }
                    )

                return json.dumps(log_entry, ensure_ascii=False)

        handler.setFormatter(UIFormatter())
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

    # Update JCELogger.log_interface() in logger.py
    def log_interface(
        self,
        component: str,
        event: str,
        user_ctx: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
        level: LogLevel = "info",
    ) -> None:
        """Enhanced logging with direct rich_cli context mapping"""
        log_method = getattr(self.loggers["interface"], self._safe_get_level(level))

        # Standardized context format
        record_attrs = {
            "component": component,
            "event": event,
            "user_id": user_ctx.get("email") if user_ctx else None,
            "session_id": user_ctx.get("session_id") if user_ctx else None,
            "metadata": metadata or {},
            "ui_element": component,  # Auto-map component to UI element
        }

        # Add timing if available in metadata
        if metadata and "render_time" in metadata:
            record_attrs["render_time_ms"] = (
                float(metadata["render_time"].replace("s", "")) * 1000
            )

        log_method(event, extra=record_attrs)
