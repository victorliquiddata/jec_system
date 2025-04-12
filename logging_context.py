import threading
from contextvars import ContextVar
from typing import Optional


class LoggingContext:
    _correlation_id = ContextVar("correlation_id", default=None)
    _local = threading.local()

    @classmethod
    def set_correlation_id(cls, cid: str):
        cls._correlation_id.set(cid)
        cls._local.correlation_id = cid

    @classmethod
    def get_correlation_id(cls) -> Optional[str]:
        return cls._correlation_id.get() or getattr(cls._local, "correlation_id", None)
