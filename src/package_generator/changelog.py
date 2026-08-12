# src/package_generator/changelog.py
"""Debian changelog parsing and generation engine.

Decoupled into single-purpose methods for text parsing, history state
reconstruction, and dynamic delta diff calculations.
"""

import re
from email.utils import formatdate

from packaging.version import Version

from .logger import Logger
from .models import (
    ChangelogEntry,
    PackageConfig,
    PackageOSMappingConfig,
    PackageRepoConfig,
    ProjectConfig,
)


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
        """Scans raw text to split and extract individual release blocks.

        Uses traditional Debian regex metadata formatting rules to find release
        headers, bullet lists of differences, and maintainer signatures,
        building an in-memory sequential array list tracker of versions.

        Args:
            raw_text: Raw multiline text content stream read from an existing
                debian/changelog tracking file platter on the disk.
        """
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

        self._logger.debug(f"Discovered {len(headers)} historical release blocks to catalog.")

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

            self._logger.debug(
                f"Cataloged historical block: {entry.package_name} ({entry.version})"
            )


    def _reconstruct_historical_state(self) -> tuple[dict[str, str], set[str]]:
        """Compiles historical entry strings chronologically into a clean state map.

        Returns:
            A tuple containing a dictionary of scalar properties and a set of
            historical OS mapping match strings.
        """
        self._logger.debug(
            "Reconstructing absolute state timeline by compiling history backwards..."
        )
        history_map: dict[str, str] = {}
        historical_matches: set[str] = set()

        for entry in reversed(self.entries):
            self._logger.debug(f"Collating change bullets from version block: {entry.version}")

            for row in entry.changes.splitlines():
                clean_row = row.strip().lstrip("*").strip()
                if "=" in clean_row:
                    h_key, h_val = clean_row.split("=", 1)
                    history_map[h_key.strip()] = h_val.strip()

                    # Dynamically capture historical active match keys from log parameters
                    if h_key.startswith("os_mappings."):
                        parts = h_key.split(".")
                        if len(parts) >= 2:
                            historical_matches.add(parts[1].strip())

            # Accumulate historical macro state updates from human-readable logs
            if "Toggled repository keyring strategy to: dynamic" in entry.changes:
                self._logger.debug(
                    f"Tracking state transition: dynamic_keyring=true found at v{entry.version}"
                )
                history_map["dynamic_keyring"] = "true"
            elif "Toggled repository keyring strategy to: static" in entry.changes:
                self._logger.debug(
                    f"Tracking state transition: dynamic_keyring=false found at v{entry.version}"
                )
                history_map["dynamic_keyring"] = "false"

            if "Modified description:" in entry.changes:
                desc_val = entry.changes.split("Modified description:", 1)[1].splitlines()
                history_map["description"] = desc_val[0].strip()

            if "Modified repo.url:" in entry.changes:
                url_val = entry.changes.split("Modified repo.url:", 1)[1].splitlines()
                history_map["repo.url"] = url_val[0].strip()

            if "Modified repo.key_url:" in entry.changes:
                key_val = entry.changes.split("Modified repo.key_url:", 1)[1].splitlines()
                history_map["repo.key_url"] = key_val[0].strip()

            # Parse structural removal bullets matching: Removed os_mappings.<match_key>.
            pruned_match = re.search(r"Removed os_mappings\.([^\s\n\.]+)\.", entry.changes)
            if pruned_match:
                matched_flavor = pruned_match.group(1).strip()
                self._logger.debug(
                    f"Tracking state removal: os_mapping '{matched_flavor}' "
                    f"discarded at v{entry.version}"
                )
                historical_matches.discard(matched_flavor)

        return history_map, historical_matches

    def _calculate_diff_bullets(self, config: PackageConfig) -> list[str]:
        """Compares incoming config against historical state to generate bullet lines."""
        bullet_lines: list[str] = []

        # Case A: Genesis Slate
        if not self.latest_entry:
            self._logger.info(
                f"Generating genesis release changelog block for: {config.name} ({config.version})"
            )
            bullet_lines.append("  * Initial package definition established.")
            bullet_lines.append(f"  * description={config.description}")
            bullet_lines.append(f"  * copyright_year={config.copyright_year}")
            bullet_lines.append(f"  * dynamic_keyring={str(config.dynamic_keyring).lower()}")
            bullet_lines.append(f"  * repo.url={config.repo.url}")
            bullet_lines.append(f"  * repo.suites={config.repo.suites}")
            bullet_lines.append(f"  * repo.components={config.repo.components}")
            bullet_lines.append(f"  * repo.key_url={config.repo.key_url}")
            for match_key, mapping in config.os_mappings.items():
                bullet_lines.append(f"  * os_mappings.{match_key}.distro={mapping.distro}")
                bullet_lines.append(f"  * os_mappings.{match_key}.codename={mapping.codename}")
            return bullet_lines

        # Case B: Incremental Delta Calculation
        self._logger.info(
            f"Calculating delta differences for version upgrade: "
            f"{self.latest_entry.version} -> {config.version}"
        )
        bullet_lines.append(f"  * Updated version to {config.version}")
        history_map, historical_matches = self._reconstruct_historical_state()

        if "description" in history_map and history_map["description"] != config.description:
            self._logger.debug("Change detected: Package 'description' field updated.")
            bullet_lines.append(f"  * Modified description: {config.description}")

        if "repo.url" in history_map and history_map["repo.url"] != config.repo.url:
            self._logger.debug("Change detected: Package 'repo.url' field updated.")
            bullet_lines.append(f"  * Modified repo.url: {config.repo.url}")
            bullet_lines.append(f"  * Modified repo.key_url: {config.repo.key_url}")

        prev_dynamic = history_map.get("dynamic_keyring") == "true"
        if config.dynamic_keyring != prev_dynamic:
            self._logger.debug("Change detected: Keyring operational strategy toggled.")
            strategy_name = "dynamic" if config.dynamic_keyring else "static"
            bullet_lines.append(f"  * Toggled repository keyring strategy to: {strategy_name}")

        # Track internal updates to properties within active OS mappings
        current_matches = set(config.os_mappings.keys())
        for match_key, mapping in config.os_mappings.items():
            if match_key in historical_matches:
                hist_dist = history_map.get(f"os_mappings.{match_key}.distro")
                hist_codename = history_map.get(f"os_mappings.{match_key}.codename")

                if (hist_dist and hist_dist != mapping.distro) or \
                   (hist_codename and hist_codename != mapping.codename):

                    self._logger.debug(
                        f"Change detected: Properties modified inside rule '{match_key}'."
                    )
                    bullet_lines.append(f"  * Modified os_mappings rule matching {match_key}")
                    if hist_dist != mapping.distro:
                        bullet_lines.append(f"  * os_mappings.{match_key}.distro={mapping.distro}")
                    if hist_codename != mapping.codename:
                        bullet_lines.append(
                            f"  * os_mappings.{match_key}.codename={mapping.codename}"
                        )

        for old_match in sorted(historical_matches):
            if old_match not in current_matches:
                self._logger.debug(f"Change detected: OS mapping rule flavor '{old_match}' pruned.")
                bullet_lines.append(f"  * Removed os_mappings.{old_match}.")

        return bullet_lines

    def to_package_config(self) -> PackageConfig:
        """Reverse-engineers historical changelog records back into a PackageConfig."""
        self._logger.info(
            "Reverse-engineering changelog text blocks back to a PackageConfig model..."
        )
        history_map, historical_matches = self._reconstruct_historical_state()

        package_name = self.entries[-1].package_name if self.entries else ""
        version = self.entries[0].version if self.entries else "1.0.0"
        description = history_map.get("description", "")
        copyright_year = int(history_map.get("copyright_year", 0))
        dynamic_keyring = history_map.get("dynamic_keyring") == "true"



        repo_config = PackageRepoConfig(
            url=history_map.get("repo.url", ""),
            suites=history_map.get("repo.suites", ""),
            components=history_map.get("repo.components", ""),
            key_url=history_map.get("repo.key_url", ""),
        )

        os_mappings: dict[str, PackageOSMappingConfig] = {}
        for match_key in sorted(historical_matches):
            os_mappings[match_key] = PackageOSMappingConfig(
                distro=history_map.get(f"os_mappings.{match_key}.distro", ""),
                codename=history_map.get(f"os_mappings.{match_key}.codename", ""),
            )

        self._logger.info(f"Successfully reverse-engineered model snapshot for version: {version}")
        return PackageConfig(
            name=package_name,
            version=version,
            description=description,
            copyright_year=copyright_year,
            dynamic_keyring=dynamic_keyring,
            repo=repo_config,
            os_mappings=os_mappings,
        )


    def generate_next_version(
        self,
        config: PackageConfig,
        project_config: ProjectConfig,
        current_time: str | None = None,
    ) -> str:
        """Calculates version differences and compiles an updated changelog text stream.

        Orchestrates the entire changelog assembly pipeline by converting a
        strongly typed configuration profile and a global project profile into
        a standard, multi-block Debian changelog text stream container.

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

        if self.latest_entry:
            current_ver_obj = Version(config.version)
            previous_ver_obj = Version(self.latest_entry.version)

            if current_ver_obj < previous_ver_obj:
                raise ValueError(
                    f"Version downgrade rejected for {config.name}. "
                    f"Attempted to compile v{config.version} "
                    f"but history has already progressed forward to v{self.latest_entry.version}."
                )

        timestamp = current_time if current_time is not None else formatdate(localtime=True)
        bullet_lines = self._calculate_diff_bullets(config)

        # Raise a ValueError if the manifest was modified but version string remained identical
        if self.latest_entry and config.version == self.latest_entry.version:
            # Contains actual detected field differences beyond the version tag row
            if len(bullet_lines) > 1:
                raise ValueError(
                    f"Manifest modified without version bump for package '{config.name}'. "
                    f"Changes detected at version {config.version} must be accompanied "
                    f"by an incremented version."
                )
            # Safe duplicate no-op fallback run path
            self._logger.info(
                f"No changes detected for package '{config.name}' at version {config.version}. "
                f"Preserving changelog."
            )
            return self._raw_text

        changes_block = "\n".join(bullet_lines)
        new_block = (
            f"{config.name} ({config.version}) stable; urgency=medium\n\n"
            f"{changes_block}\n\n"
            f" -- {project_config.maintainer_name} <{project_config.maintainer_email}>  {timestamp}"
        )

        if self._raw_text:
            # Record a successful text stacking merge pass
            self._logger.debug(
                "Successfully appended new release block on top of historical text ledger lines."
            )
            return f"{new_block}\n\n{self._raw_text.strip()}\n"

        # Record a successful single-entry compilation pass
        self._logger.debug("Successfully generated isolated baseline release text entry block.")
        return f"{new_block}\n"
