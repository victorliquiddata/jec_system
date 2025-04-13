# logger.py

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Literal, Any
from config import AppConfig


from logging.handlers import TimedRotatingFileHandler

LogLevel = Literal["info", "warning", "error", "debug"]


class JCELogger:
    """Enhanced centralized logger for JEC system with rich_cli integration"""

    def __init__(self):
        config = AppConfig.get_log_config()
        self.log_dir = Path(config["dir"])
        self.rotation = config["rotation"]
        self.retention_days = config["retention"]
        self.correlation_enabled = config["enable_correlation"]

        self._setup_logging_env()
        self.loggers = {
            "conexoes": self._create_logger("conexoes"),
            "logica": self._create_logger("logica"),
            "interface": self._create_interface_logger(),  # Special format for UI
        }
        self._valid_levels = {"debug", "info", "warning", "error"}

    def _create_logger(self, name: str) -> logging.Logger:
        logger = logging.getLogger(f"jec.{name}")
        logger.handlers.clear()

        handler = TimedRotatingFileHandler(
            filename=self.log_dir / f"{name}.log",
            when=self.rotation,
            backupCount=self.retention_days,
            encoding="utf-8",
        )

    def _create_interface_logger(self) -> logging.Logger:
        """Specialized logger for UI events with structured JSON formatting"""
        logger = logging.getLogger("jec.interface")
        logger.handlers.clear()

        # Write interface logs to the root log directory, no nested ui folder
        interface_log_path = self.log_dir / "interface.log"

        handler = TimedRotatingFileHandler(
            filename=interface_log_path,
            when=self.rotation,
            backupCount=self.retention_days,
            encoding="utf-8",
        )

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
        """Create log directory from config"""
        try:
            self.log_dir.mkdir(exist_ok=True, parents=True)
            (self.log_dir / "archive").mkdir(exist_ok=True)  # For rotated logs
        except PermissionError as pe:
            logging.error(f"Log directory permission error: {str(pe)}")
            raise

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
        correlation_id: Optional[str] = None,
    ) -> None:
        """Log database connections and operations"""

        metadata = metadata or {}
        if self.correlation_enabled and correlation_id:
            metadata["correlation_id"] = correlation_id
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

    def log_db_error(
        self,
        module: str,
        action: str,
        table: str,
        error: Exception,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ):
        """Standardized database error logging"""
        self.log_negocio(
            module=module,
            action=action,
            metadata={
                "table": table,
                "error": str(error),
                "error_type": type(error).__name__,
                "user_id": user_id,
                "correlation_id": correlation_id,
            },
            level="error",
        )

    def log_data_access(self, action: str, metadata: dict):
        self.log_negocio(
            "data_access",
            action,
            metadata={**metadata, "access_type": "preview", "sensitive": False},
            level="info",
        )
