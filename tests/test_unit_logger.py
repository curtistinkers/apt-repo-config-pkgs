"""
tests/test_unit_logger.py
=========================
Discrete unit specifications validating the PSR-3 level thresholds, color
routing, and file-mirroring mechanisms managed by the Logger service.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from package_generator.logger import Logger, LogLevel


def test_unit_log_level_model_enforces_mathematical_hierarchy() -> None:
    """Verifies that the LogLevel Enum constants compare accurately by severity weight."""
    # 1. ASSERTIONS: Higher severity tiers must be mathematically greater than lower tiers
    assert LogLevel.EMERGENCY > LogLevel.DEBUG
    assert LogLevel.ERROR >= LogLevel.WARNING
    assert LogLevel.INFO < LogLevel.CRITICAL

    # 2. String evaluation check to ensure clean property translations
    assert LogLevel.DEBUG.name == "DEBUG"
    assert LogLevel.DEBUG.value == 1


@pytest.mark.parametrize(
    "method_name,message,should_print_to_console",
    [
        ("debug", "Low-level background details.", False),
        ("info", "General confirmation note.", False),
        ("notice", "Significant workspace event.", False),
        ("warning", "Non-fatal operational anomaly.", True),
        ("error", "Severe runtime execution fault.", True),
        ("critical", "Severe component breakdown.", True),
        ("alert", "Immediate action required.", True),
        ("emergency", "System completely unusable.", True),
    ]
)
def test_logger_psr3_methods_respect_terminal_thresholds(
    capsys: pytest.CaptureFixture,
    method_name: str,
    message: str,
    should_print_to_console: bool
) -> None:
    """
    Verifies that all 8 standard PSR-3 interface methods exist and are
    correctly filtered or displayed based on the terminal threshold settings.
    """
    # 1. SETUP: Initialize a logger with a 'warning' minimum threshold level.
    # This means debug, info, and notice must be skipped, while warning and above print.
    logger = Logger(min_terminal_level="warning")

    # 2. EXECUTION: Dynamically call the target method name using Python's native getattr()
    # getattr(logger, "info")("msg") is equivalent to typing logger.info("msg")
    log_method = getattr(logger, method_name)
    log_method(message)

    # Capture both stdout and stderr terminal output streams
    captured = capsys.readouterr()
    combined_output = captured.out + captured.err

    # 3. SPECIFICATION ASSERTIONS
    expected_string = f"{method_name.upper()}: {message}"

    if should_print_to_console:
        assert expected_string in combined_output, (
            f"Method {method_name} failed to log to console."
        )
    else:
        assert expected_string not in combined_output, (
            f"Method {method_name} incorrectly logged to console."
        )

def test_logger_silently_drops_filesystem_write_exceptions(tmp_path: Path) -> None:
    """
    Verifies that the Logger service catches and silently handles filesystem
    write exceptions without crashing the primary execution sequence thread.
    """
    target_log_file = tmp_path / "faulty_device.log"

    # Initialize a file logger pointing directly to our sandbox target path
    faulty_logger = Logger(
        min_terminal_level="emergency",
        log_file=target_log_file,
        min_file_level="debug"
    )

    # Use python patch context to intercept builtins.open and force it to raise an error
    with patch("builtins.open", side_effect=OSError("Disk partition mounted read-only.")):
        # This trace call tries to write to the file, encounters the patch error,
        # and drives execution directly down into your 'except Exception:' block.
        faulty_logger.debug("Attempting to write build log data to a broken platter asset.")

    # If we reached this line without the test function crashing, the except block
    # successfully caught the error and protected our runtime engine pipeline.
    assert True

def test_logger_successfully_writes_uncolored_psr3_entries_to_healthy_file(
    tmp_path: Path
) -> None:
    """
    Verifies that the Logger successfully executes the write command line path
    when routed to a healthy, writable destination on the filesystem platter.
    """
    # 1. SETUP: Create a real log file path in our temporary test sandbox folder
    healthy_log_file = tmp_path / "healthy_build_run.log"

    # Initialize the logger with a quiet terminal threshold, but verbose file logging
    logger = Logger(
        min_terminal_level="emergency",
        log_file=healthy_log_file,
        min_file_level="debug"
    )

    # 2. EXECUTION: Call a standard logging method to drive execution down line 78
    logger.info("Executing standard package folder layout extraction processes.")

    # 3. ASSERTIONS: Confirm the file was physically created and populated
    assert healthy_log_file.exists(), "The logger failed to create the physical file layout."

    file_content_ledger = healthy_log_file.read_text(encoding="utf-8")
    assert (
        "INFO: Executing standard package folder layout extraction processes."
        in file_content_ledger
    )
