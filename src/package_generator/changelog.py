"""Debian changelog parsing and generation engine.

Decoupled into single-purpose methods for text parsing, history state
reconstruction, and dynamic delta diff calculations.
"""

import re
from email.utils import formatdate

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

        Iterates backwards through the collection list of parsed changelog entries,
        from the oldest record to the most recent, accumulating explicit assignments
        and text delta modifications into a unified final state snapshot dictionary.

        Returns:
            A tuple containing a dictionary of scalar properties mapping configuration keys
            to their values, and a set of active historical OS mapping match strings.
        """
        # Signal the initialization of the historical accumulator loop
        self._logger.debug(
            "Reconstructing absolute state timeline by compiling history backwards..."
        )

        history_map: dict[str, str] = {}
        historical_matches: set[str] = set()

        for entry in reversed(self.entries):
            # Record exactly which historical block version is being collated
            self._logger.debug(f"Collating change bullets from version block: {entry.version}")

            # Parse traditional key=value declarations
            for row in entry.changes.splitlines():
                clean_row = row.strip().lstrip("*").strip()
                if "=" in clean_row:
                    h_key, h_val = clean_row.split("=", 1)
                    history_map[h_key.strip()] = h_val.strip()

                if "os_mappings." in clean_row and ".match=" in clean_row:
                    match_val = clean_row.split(".match=", 1)[1]
                    historical_matches.add(match_val.strip())

            # Accumulate historical macro state updates from human-readable logs
            if "Toggled repository keyring strategy to: dynamic" in entry.changes:
                # Track a dynamic keyring toggle found in the raw text logs
                self._logger.debug(
                    f"Tracking state transition: dynamic_keyring=true found at v{entry.version}"
                )
                history_map["dynamic_keyring"] = "true"
            elif "Toggled repository keyring strategy to: static" in entry.changes:
                # Track a static keyring toggle found in the raw text logs
                self._logger.debug(
                    f"Tracking state transition: dynamic_keyring=false found at v{entry.version}"
                )
                history_map["dynamic_keyring"] = "false"

            if "Modified description:" in entry.changes:
                desc_val = entry.changes.split("Modified description:", 1)[1].splitlines()[0]
                history_map["description"] = desc_val.strip()

            if "Modified repo.url:" in entry.changes:
                url_val = entry.changes.split("Modified repo.url:", 1)[1].splitlines()[0]
                history_map["repo.url"] = url_val.strip()

            if "Modified repo.key_url:" in entry.changes:
                key_val = entry.changes.split("Modified repo.key_url:", 1)[1].splitlines()[0]
                history_map["repo.key_url"] = key_val.strip()

            pruned_match = re.search(
                r"Removed os_mappings rule matching ([^\.\s\n]+)", entry.changes
            )
            if pruned_match:
                matched_flavor = pruned_match.group(1).strip()
                # Record when an array rule exclusion is successfully tracked
                self._logger.debug(
                    f"Tracking state removal: os_mapping '{matched_flavor}' "
                    f"discarded at v{entry.version}"
                )
                historical_matches.discard(matched_flavor)

        return history_map, historical_matches


    def _calculate_diff_bullets(self, config: PackageConfig) -> list[str]:
        """Compares incoming config against historical state to generate bullet lines.

        Inspects the current configuration parameters against the compiled
        historical baseline state map, determining if changes exist to append
        descriptive release bullets dynamically.

        Args:
            config: Incoming type-safe PackageConfig domain value object state
                to evaluate against historical release milestones.

        Returns:
            A list of formatted text bullet strings representing structural modifications.
        """
        bullet_lines: list[str] = []

        # Case A: Genesis Slate (No historical logs exist)
        if not self.latest_entry:
            # Track initialization of a blank baseline slate
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
            for index, mapping in enumerate(config.os_mappings):
                bullet_lines.append(f"  * os_mappings.{index}.match={mapping.match}")
                bullet_lines.append(f"  * os_mappings.{index}.set_dist={mapping.set_dist}")
                bullet_lines.append(f"  * os_mappings.{index}.set_codename={mapping.set_codename}")
            return bullet_lines

        # Case B: Incremental Delta Calculation (Building on top of history logs)
        # Confirm the initialization of a version increment sweep pass
        self._logger.info(
                f"Calculating delta differences for version upgrade: "
                f"{self.latest_entry.version} -> {config.version}"
            )
        bullet_lines.append(f"  * Updated version to {config.version}")
        history_map, historical_matches = self._reconstruct_historical_state()

        if "description" in history_map and history_map["description"] != config.description:
            # Record a parameter shift for description text strings
            self._logger.debug("Change detected: Package 'description' field updated.")
            bullet_lines.append(f"  * Modified description: {config.description}")

        if "repo.url" in history_map and history_map["repo.url"] != config.repo.url:
            # Record a parameter shift for repository target URLs
            self._logger.debug("Change detected: Package 'repo.url' field updated.")
            bullet_lines.append(f"  * Modified repo.url: {config.repo.url}")
            bullet_lines.append(f"  * Modified repo.key_url: {config.repo.key_url}")

        prev_dynamic = history_map.get("dynamic_keyring") == "true"
        if config.dynamic_keyring != prev_dynamic:
            # Record a keyring operational strategy toggle branch shift
            self._logger.debug("Change detected: Keyring operational strategy toggled.")
            strategy_name = "dynamic" if config.dynamic_keyring else "static"
            bullet_lines.append(f"  * Toggled repository keyring strategy to: {strategy_name}")

        current_matches = {m.match for m in config.os_mappings}
        for old_match in sorted(historical_matches):
            if old_match not in current_matches:
                # Record when a single operating system mapping rule flavor vanishes
                self._logger.debug(f"Change detected: OS mapping rule flavor '{old_match}' pruned.")
                bullet_lines.append(f"  * Removed os_mappings rule matching {old_match}.")

        return bullet_lines


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

        timestamp = current_time if current_time is not None else formatdate(localtime=True)
        bullet_lines = self._calculate_diff_bullets(config)

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


    def to_package_config(self) -> PackageConfig:
        """Recreate the package manifest by working backwards.

        Reverse-engineers the historical ledger entries chronologically back into
        a type-safe, frozen PackageConfig state.

        Returns:
            A fully constructed PackageConfig reflecting the snapshot properties
            of this changelog configuration timeline.
        """
        # Record inception of the reversal mapping pipeline
        self._logger.info(
            "Reverse-engineering changelog text blocks back to a PackageConfig model..."
        )

        # Harvest our complete historical state tracking maps compiled chronologically
        history_map, historical_matches = self._reconstruct_historical_state()

        # Extract standard package parameters
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

        # Dynamically rebuild the array list structures from our compiled mappings
        os_mappings: list[PackageOSMappingConfig] = []

        # Scan history_map keys to find every registered structural sub-index mapping item
        index_pattern = re.compile(r"^os_mappings\.(\d+)\.match$")
        discovered_indices = set()

        for key in history_map:
            match_index = index_pattern.match(key)
            if match_index:
                discovered_indices.add(int(match_index.group(1)))

        # Loop through sorted index numbers to reconstruct individual structural dictionary rows
        for index in sorted(discovered_indices):
            match_val = history_map.get(f"os_mappings.{index}.match", "")

            # Ensure we only append the rule layer if it hasn't been explicitly pruned from history
            if match_val in historical_matches:
                mapping_item = PackageOSMappingConfig(
                    match=match_val,
                    set_dist=history_map.get(f"os_mappings.{index}.set_dist", ""),
                    set_codename=history_map.get(f"os_mappings.{index}.set_codename", ""),
                )
                os_mappings.append(mapping_item)

        # Confirm the successful finalization of the frozen data layout
        self._logger.info(f"Successfully reverse-engineered model snapshot for version: {version}")

        # Compile all sub-components natively straight into your type-safe model container
        return PackageConfig(
            name=package_name,
            version=version,
            description=description,
            copyright_year=copyright_year,
            dynamic_keyring=dynamic_keyring,
            repo=repo_config,
            os_mappings=os_mappings,
        )
