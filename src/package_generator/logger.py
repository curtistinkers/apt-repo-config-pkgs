"""
package_generator.logger
========================
An object-oriented diagnostic logger implementing a clean PSR-3 interface contract.
Handles rich color console filtering and explicit uncolored file routing.
"""

from enum import Enum
from pathlib import Path
from typing import Optional, Dict
import click


class LogLevel(int, Enum):
    """
    An explicit, typed model representing PSR-3 severity thresholds.
    """
    DEBUG = 1
    INFO = 2
    NOTICE = 3
    WARNING = 4
    ERROR = 5
    CRITICAL = 6
    ALERT = 7
    EMERGENCY = 8


class Logger:
    """
    Responsible for evaluating, formatting, and routing operational system messages
    to terminal screens and file systems based on PSR-3 severity tiers.
    """

    # Internal translation look-up map converting user strings to LogLevel Enum models
    _STRING_TO_LEVEL: Dict[str, LogLevel] = {
        "debug": LogLevel.DEBUG,
        "info": LogLevel.INFO,
        "notice": LogLevel.NOTICE,
        "warning": LogLevel.WARNING,
        "error": LogLevel.ERROR,
        "critical": LogLevel.CRITICAL,
        "alert": LogLevel.ALERT,
        "emergency": LogLevel.EMERGENCY,
    }

    def __init__(
        self,
        min_terminal_level: str = "info",
        log_file: Optional[Path] = None,
        min_file_level: str = "debug",
    ) -> None:
        """
        Initializes the diagnostic logging service engine.

        Args:
            min_terminal_level (str): Minimum PSR-3 level required to display on console.
            log_file (Optional[Path]): Optional file path target to mirror text records.
            min_file_level (str): Minimum PSR-3 level required to save inside the file.
        """
        self._min_term_level = self._STRING_TO_LEVEL.get(min_terminal_level.lower(), LogLevel.INFO)
        self._log_file = log_file
        self._min_file_level = self._STRING_TO_LEVEL.get(min_file_level.lower(), LogLevel.DEBUG)

    def _log_message(self, level_enum: LogLevel, message: str, color: str, use_stderr: bool) -> None:
        """Core internal routing mechanism parsing line statements across active targets."""
        formatted_payload = f"{level_enum.name}: {message}"

        # 1. THE CONSOLE GATE: Math comparisons work natively on int-backed Enum constants
        if level_enum >= self._min_term_level:
            click.secho(formatted_payload, fg=color, err=use_stderr)

        # 2. THE FILE GATE: Independently evaluate and append plain text to the disk ledger
        if self._log_file and level_enum >= self._min_file_level:
            try:
                # Ensure parent directory layers exist before appending to file
                self._log_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self._log_file, "a", encoding="utf-8") as file_stream:
                    file_stream.write(f"{formatted_payload}\n")
            except Exception:
                # Silently drop filesystem telemetry issues to protect the build run loop
                pass

    # ==============================================================================
    # EXPLICIT PSR-3 STRUCTURAL CONTRACT METHODS
    # ==============================================================================

    def debug(self, message: str) -> None:
        """Logs low-level developer background context data blocks."""
        self._log_message(LogLevel.DEBUG, message, "cyan", use_stderr=False)

    def info(self, message: str) -> None:
        """Logs general informational workspace execution events confirmation."""
        self._log_message(LogLevel.INFO, message, "green", use_stderr=False)

    def notice(self, message: str) -> None:
        """Logs normal but highly significant operational system event gates."""
        self._log_message(LogLevel.NOTICE, message, "blue", use_stderr=False)

    def warning(self, message: str) -> None:
        """Logs non-fatal anomalies or fallback paths configuration alerts."""
        self._log_message(LogLevel.WARNING, message, "yellow", use_stderr=False)

    def error(self, message: str) -> None:
        """Logs severe execution bugs or standard template compilation faults."""
        self._log_message(LogLevel.ERROR, message, "red", use_stderr=True)

    def critical(self, message: str) -> None:
        """Logs extreme operational breakdowns or core tracking connection losses."""
        self._log_message(LogLevel.CRITICAL, message, "red", use_stderr=True)

    def alert(self, message: str) -> None:
        """Logs urgent situations demanding immediate code workspace intervention."""
        self._log_message(LogLevel.ALERT, message, "magenta", use_stderr=True)

    def emergency(self, message: str) -> None:
        """Logs a completely broken workspace state rendering components unusable."""
        self._log_message(LogLevel.EMERGENCY, message, "red", use_stderr=True)
