# test_logger.py - Final Robust Version
import pytest
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock
import os
import time

from logger import JCELogger


# Helper function to safely close logging handlers
def reset_logging():
    """Clean up logging handlers to prevent file locks"""
    for handler in logging.root.handlers[:]:
        handler.close()
        logging.root.removeHandler(handler)
    logging.shutdown()


@pytest.fixture
def logger(tmp_path):
    """Fixture with isolated temp directory and proper cleanup"""
    # Patch the log directory to use pytest's tmp_path
    with patch("logger.Path", return_value=tmp_path):
        test_logger = JCELogger()
        yield test_logger

    # Force cleanup of logging handlers
    reset_logging()


def test_logger_initialization(logger, tmp_path):
    """Test logger creates required log channels"""
    assert set(logger.loggers.keys()) == {"conexoes", "logica", "interface"}
    for log_name in logger.loggers:
        assert (tmp_path / f"{log_name}.log").exists()


def test_log_conexao_formatting(logger):
    """Test log format structure"""
    with patch.object(logger.loggers["conexoes"], "info") as mock_log:
        logger.log_conexao("TEST_EVENT", "test message", level="info")
        args, _ = mock_log.call_args
        assert "[TEST_EVENT] test message" in args[0]


def test_log_negocio_metadata(logger):
    """Test metadata inclusion"""
    with patch.object(logger.loggers["logica"], "debug") as mock_log:
        test_meta = {"user_id": 123, "action": "login"}
        logger.log_negocio("auth", "login", test_meta, "debug")
        assert mock_log.call_args[1]["extra"]["metadata"] == test_meta


def test_log_interface_user_context(logger):
    """Test user context logging"""
    with patch.object(logger.loggers["interface"], "info") as mock_log:
        test_user = {"id": 456, "email": "test@example.com"}
        logger.log_interface("login", "attempt", test_user, "info")
        assert mock_log.call_args[1]["extra"]["user"] == test_user


def test_actual_file_writing(tmp_path):
    """Single test that verifies actual file output"""
    log_file = tmp_path / "conexoes.log"

    # Create fresh logger instance for this test
    with patch("logger.Path", return_value=tmp_path):
        test_logger = JCELogger()
        test_logger.log_conexao("FILE_TEST", "file content", level="info")

    # Verify file content
    assert "FILE_TEST" in log_file.read_text()

    # Explicit cleanup
    reset_logging()


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main(["-v", __file__]))
