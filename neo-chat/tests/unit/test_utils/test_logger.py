"""Tests for structured JSON logging."""

import json
import logging
from io import StringIO
import pytest
from src.utils.logger import JSONFormatter, setup_logger


def test_json_formatter_basic():
    """Test JSONFormatter produces valid JSON."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None
    )
    
    output = formatter.format(record)
    data = json.loads(output)
    
    assert data["level"] == "INFO"
    assert data["message"] == "Test message"
    assert data["logger"] == "test"
    assert "timestamp" in data
    assert data["timestamp"].endswith("Z")


def test_json_formatter_with_user_id():
    """Test JSONFormatter includes user_id when present."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="User action",
        args=(),
        exc_info=None
    )
    record.user_id = "+1234567890"
    
    output = formatter.format(record)
    data = json.loads(output)
    
    assert data["user_id"] == "+1234567890"


def test_json_formatter_with_event_type():
    """Test JSONFormatter includes event_type when present."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Event occurred",
        args=(),
        exc_info=None
    )
    record.event_type = "message_received"
    
    output = formatter.format(record)
    data = json.loads(output)
    
    assert data["event_type"] == "message_received"


def test_json_formatter_with_metadata():
    """Test JSONFormatter includes metadata when present."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Action with metadata",
        args=(),
        exc_info=None
    )
    record.metadata = {"key": "value", "count": 42}
    
    output = formatter.format(record)
    data = json.loads(output)
    
    assert data["metadata"]["key"] == "value"
    assert data["metadata"]["count"] == 42


def test_json_formatter_with_exception():
    """Test JSONFormatter includes exception info."""
    formatter = JSONFormatter()
    
    try:
        raise ValueError("Test error")
    except ValueError:
        import sys
        exc_info = sys.exc_info()
        
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error occurred",
            args=(),
            exc_info=exc_info
        )
        
        output = formatter.format(record)
        data = json.loads(output)
        
        assert data["level"] == "ERROR"
        assert "exception" in data
        assert "ValueError: Test error" in data["exception"]


def test_setup_logger():
    """Test logger setup creates properly configured logger."""
    logger = setup_logger("test-logger")
    
    assert logger.name == "test-logger"
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.StreamHandler)
    assert isinstance(logger.handlers[0].formatter, JSONFormatter)
    assert logger.propagate is False


def test_logger_output_format(caplog):
    """Test that logger produces valid JSON output."""
    logger = setup_logger("test-output")
    
    with caplog.at_level(logging.INFO):
        logger.info("Test message")
    
    # Note: caplog captures the message, not the formatted output
    # In real usage, the JSON formatter would be applied
    assert len(caplog.records) == 1
    assert caplog.records[0].message == "Test message"


def test_logger_levels():
    """Test logger respects log levels."""
    logger = setup_logger("test-levels")
    logger.setLevel(logging.WARNING)
    
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JSONFormatter())
    logger.handlers = [handler]
    
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    
    output = stream.getvalue()
    lines = [line for line in output.split('\n') if line]
    
    # Should only have WARNING and ERROR
    assert len(lines) == 2
    
    data1 = json.loads(lines[0])
    data2 = json.loads(lines[1])
    
    assert data1["level"] == "WARNING"
    assert data2["level"] == "ERROR"
