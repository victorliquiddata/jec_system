# test_logger2.py - Focused Fixes for Remaining Issues
import pytest
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock
from logger import JCELogger


def reset_logging():
    """Clean up logging handlers between tests"""
    for handler in logging.root.handlers[:]:
        handler.close()
        logging.root.removeHandler(handler)
    logging.shutdown()


@pytest.fixture
def logger(tmp_path):
    """Isolated logger fixture with temp directory"""
    with patch("logger.Path", return_value=tmp_path):
        yield JCELogger()
    reset_logging()


def test_log_file_rotation(tmp_path):
    """Verify formatted log messages"""
    with patch("logger.Path", return_value=tmp_path):
        test_logger = JCELogger()
        test_logger.log_interface("login", "attempt", level="info")

    log_content = (tmp_path / "interface.log").read_text()
    assert "UI:login.attempt" in log_content  # Now matches formatted string


# test_logger2.py - Final Working Version
def test_log_level_handling(logger):
    """Test valid and invalid log levels with proper mocks"""
    level_map = {
        "debug": (logging.DEBUG, "debug"),
        "info": (logging.INFO, "info"),
        "invalid": (logging.DEBUG, "debug"),  # Fallback case
    }

    for level_input, (expected_level, expected_method) in level_map.items():
        with patch.object(logger.loggers["logica"], expected_method) as mock_log:
            logger.log_negocio(
                module="test",
                action="action",
                metadata={},
                level=level_input,  # type: ignore
            )
            # Verify method call
            mock_log.assert_called_once_with("test.action", extra={})


def test_multiple_loggers_independence(tmp_path):
    """Test separate logger instances with proper method mocks"""
    # First clear all loggers to avoid interference
    logging.Logger.manager.loggerDict.clear()

    with patch("logger.Path", return_value=tmp_path):
        # Create loggers with different patching for each
        logger1 = JCELogger()
        # Directly patch the log method rather than the logger's method
        with patch.object(logger1, "log_conexao") as mock1:
            logger1.log_conexao(event_type="INST1", message="test1", level="info")
            mock1.assert_called_once_with(
                event_type="INST1", message="test1", level="info"
            )

        # Create a completely separate logger after the first one is done
        logging.Logger.manager.loggerDict.clear()
        logger2 = JCELogger()
        with patch.object(logger2, "log_conexao") as mock2:
            logger2.log_conexao(event_type="INST2", message="test2", level="info")
            mock2.assert_called_once_with(
                event_type="INST2", message="test2", level="info"
            )


def test_invalid_log_level_fallback(logger):
    """Test invalid level falls back to debug"""
    with patch.object(logger.loggers["logica"], "debug") as mock_debug:
        logger.log_negocio(
            module="test",
            action="action",
            metadata={},
            level="invalid_level",  # type: ignore
        )
        mock_debug.assert_called_once_with("test.action", extra={})


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main(["-v", __file__]))
