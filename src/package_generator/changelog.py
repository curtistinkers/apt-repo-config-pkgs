"""Debian changelog ledger parsing and generation engine.

Provides capabilities to read, split, and parse historical release records,
calculate structural changes between configuration lifecycles, and compile
Lintian-compliant Debian changelog text streams.
"""

import re
from email.utils import formatdate

from .logger import Logger
from .models import ChangelogEntry, PackageConfig, ProjectConfig


class Changelog:
    """Parses and manages historical collection records of a Debian changelog."""

    latest_entry: ChangelogEntry | None
    entries: list[ChangelogEntry]

    def __init__(self, raw_text: str, logger: Logger) -> None:
        """Initializes the parser and extracts historical entry records.

        Args:
            raw_text: Raw unparsed multiline string block of a changelog file.
            logger: An injected PSR-3 compliant diagnostic logging service.
        """
        self._logger = logger
        self.entries = []
        self._raw_text = raw_text

        self._parse_ledger(raw_text)
        self.latest_entry = self.entries[0] if self.entries else None

    def _parse_ledger(self, raw_text: str) -> None:
        """Scans the raw text string to split and extract individual release blocks."""
        self._logger.debug("Initializing regex scanning loop across changelog file tracks...")

        header_pattern = re.compile(
            r"^([a-z0-9\-\+\.]+)\s+\(([^\)]+)\)\s+([^;]+);\s+urgency=([a-z]+)",
            re.MULTILINE
        )
        footer_pattern = re.compile(
            r"^ -- .+\s{2}(.+)$",
            re.MULTILINE
        )

        headers = list(header_pattern.finditer(raw_text))
        if not headers:
            self._logger.debug("No valid historical changelog records discovered.")
            return

        for i, header_match in enumerate(headers):
            start_pos = header_match.start()
            end_pos = headers[i + 1].start() if i + 1 < len(headers) else len(raw_text)
            block_text = raw_text[start_pos:end_pos].strip()

            footer_match = footer_pattern.search(block_text)
            timestamp = footer_match.group(1).strip() if footer_match else ""

            lines = block_text.splitlines()
            change_lines = [ln for ln in lines[1:] if not ln.startswith(" -- ")]
            changes_content = "\n".join(change_lines).strip()

            entry = ChangelogEntry(
                package_name=header_match.group(1).strip(),
                version=header_match.group(2).strip(),
                suite=header_match.group(3).strip(),
                urgency=header_match.group(4).strip(),
                changes=changes_content,
                timestamp=timestamp
            )
            self.entries.append(entry)

    def generate_next_version(
        self,
        config: PackageConfig,
        project_config: ProjectConfig,
        current_time: str | None = None,
    ) -> str:
        """Calculates version differences and compiles an updated changelog text stream.

        Args:
            config: Incoming package layout configuration properties to validate.
            project_config: Global project variables detailing maintainer properties.
            current_time: An optional RFC-2822 string override used strictly to lock
                down deterministic test outcomes. Defaults to None (uses system time).

        Returns:
            A continuous, multi-block Lintian-compliant Debian changelog string.
        """
        self._logger.debug(
            f"Compiling release history for package '{config.name}' "
            f"under maintainer signature: {project_config.maintainer_name}"
        )

        bullet_lines = []

        # 1. Use live system clock or explicit test override formatdate(localtime=True) natively
        # handles the RFC-2822 standard string required by Debian
        timestamp = current_time if current_time is not None else formatdate(localtime=True)

        # LIFECYCLE BRANCH 1: GENESIS SLATE (No historical logs exist)
        if not self.latest_entry:
            bullet_lines.append("  * Initial package definition established.")
            bullet_lines.append(f"  * description={config.description}")
            bullet_lines.append(f"  * copyright_year={config.copyright_year}")
            bullet_lines.append(f"  * dynamic_keyring={str(config.dynamic_keyring).lower()}")
            bullet_lines.append(f"  * repo.url={config.repo.url}")
            bullet_lines.append(f"  * repo.suites={config.repo.suites}")
            bullet_lines.append(f"  * repo.components={config.repo.components}")
            bullet_lines.append(f"  * repo.key_url={config.repo.key_url}")
            for index, mapping in enumerate(config.os_mappings):
                bullet_lines.append(f"  * os_mappings.{index}.match={mapping.match}")
                bullet_lines.append(f"  * os_mappings.{index}.set_dist={mapping.set_dist}")
                bullet_lines.append(f"  * os_mappings.{index}.set_codename={mapping.set_codename}")

        else:
            # LIFECYCLE BRANCH 2 & 3: TRUE HISTORICAL DIFFERENCE ENGINE
            bullet_lines.append(f"  * Updated version to {config.version}")

            history_map = {}
            for entry in reversed(self.entries):
                for row in entry.changes.splitlines():
                    clean_row = row.strip().lstrip("*").strip()
                    if "=" in clean_row:
                        h_key, h_val = clean_row.split("=", 1)
                        history_map[h_key.strip()] = h_val.strip()

            if "description" in history_map and history_map["description"] != config.description:
                bullet_lines.append(f"  * Modified description: {config.description}")

            if "repo.url" in history_map and history_map["repo.url"] != config.repo.url:
                bullet_lines.append(f"  * Modified repo.url: {config.repo.url}")
                bullet_lines.append(f"  * Modified repo.key_url: {config.repo.key_url}")

            prev_dynamic = history_map.get("dynamic_keyring") == "true"
            if config.dynamic_keyring != prev_dynamic:
                strategy_name = "dynamic" if config.dynamic_keyring else "static"
                bullet_lines.append(f"  * Toggled repository keyring strategy to: {strategy_name}")

            current_matches = {m.match for m in config.os_mappings}
            historical_matches = set()
            for k, v in history_map.items():
                if k.startswith("os_mappings.") and k.endswith(".match"):
                    historical_matches.add(v)

            for old_match in sorted(historical_matches):
                if old_match not in current_matches:
                    bullet_lines.append(f"  * Removed os_mappings rule matching {old_match}.")

         # Ensure a clean empty row break consistently decouples headers from bullet points
        header_separator = "\n\n"

        # Assemble the fresh block with standard uniform spacing row breaks
        changes_block = "\n".join(bullet_lines)
        new_block = (
            f"{config.name} ({config.version}) stable; urgency=medium{header_separator}"
            f"{changes_block}\n\n"
            f" -- {project_config.maintainer_name} <{project_config.maintainer_email}>  {timestamp}"
        )

        if self._raw_text:
            return f"{new_block}\n\n{self._raw_text.strip()}\n"

        return f"{new_block}\n"
