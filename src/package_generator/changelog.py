"""Debian changelog ledger parsing engine.

Provides capabilities to read, split, and extract structured metadata properties
from traditional multi-block Debian changelog text streams using regex patterns.
"""

import re

from .logger import Logger
from .models import ChangelogEntry


class Changelog:
    """Parses and manages historical collection records of a Debian changelog."""

    def __init__(self, raw_text: str, logger: Logger) -> None:
        """Initializes the parser and extracts historical entry records.

        Args:
            raw_text: Raw unparsed multiline string block of a changelog file.
            logger: An injected PSR-3 compliant diagnostic logging service.
        """
        self._logger = logger
        self.entries: list[ChangelogEntry] = []

        self._parse_ledger(raw_text)

        # Expose a direct convenience pointer targeting the newest release block
        self.latest_entry = self.entries[0] if self.entries else None

    def _parse_ledger(self, raw_text: str) -> None:
        """Scans the raw text string to split and extract individual release blocks."""
        self._logger.debug("Initializing regex scanning loop across changelog file tracks...")

        # Pattern targeting the mandatory Debian release entry header line
        header_pattern = re.compile(
            r"^([a-z0-9\-\+\.]+)\s+\(([^\)]+)\)\s+([^;]+);\s+urgency=([a-z]+)",
            re.MULTILINE
        )

        # Pattern targeting the maintainer and timestamp footer signature line
        footer_pattern = re.compile(
            r"^ -- .+\s{2}(.+)$",
            re.MULTILINE
        )

        # Locate all header matching boundaries inside the string payload
        headers = list(header_pattern.finditer(raw_text))
        if not headers:
            self._logger.debug("No valid historical changelog records discovered.")
            return

        # Loop through headers to isolate individual physical text block spans
        for i, header_match in enumerate(headers):
            start_pos = header_match.start()
            # If a lower block exists, end right before it, otherwise read to the file end
            end_pos = headers[i + 1].start() if i + 1 < len(headers) else len(raw_text)

            block_text = raw_text[start_pos:end_pos].strip()

            # Locate the mandatory footer signature line inside this specific block span
            footer_match = footer_pattern.search(block_text)
            timestamp = footer_match.group(1).strip() if footer_match else ""

            # Extract the raw bullet changes by stripping the top header and bottom footer lines
            lines = block_text.splitlines()
            change_lines = [ln for ln in lines[1:] if not ln.startswith(" -- ")]
            changes_content = "\n".join(change_lines).strip()

            # Construct our frozen data value object
            entry = ChangelogEntry(
                package_name=header_match.group(1).strip(),
                version=header_match.group(2).strip(),
                suite=header_match.group(3).strip(),
                urgency=header_match.group(4).strip(),
                changes=changes_content,
                timestamp=timestamp
            )

            self.entries.append(entry)
            self._logger.debug(f"Successfully cataloged changelog release index: {entry.version}")
