# src/package_generator/changelog.py
"""Debian changelog parsing and generation engine.

Decoupled into single-purpose methods for text parsing, history state
reconstruction, and dynamic delta diff calculations.
"""

import re
from email.utils import formatdate
from pathlib import Path

import jinja2
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

    def _compare_versions(self, incoming_version_str: str) -> None:
        """Compares incoming version with history to prevent semantic regressions.

        Args:
            incoming_version_str: The version string from the active manifest configuration.

        Raises:
            ValueError: If the incoming version is sequentially lower than history,
                or if it matches history but configuration states differ.
        """
        if not self.latest_entry:
            return

        current_ver = Version(self.latest_entry.version)
        target_ver = Version(incoming_version_str)

        if target_ver < current_ver:
            self._logger.error(
                f"Semantic regression blocked: v{target_ver} is lower than v{current_ver}"
            )
            raise ValueError(
                f"Version downgrade violation: Proposed version '{incoming_version_str}' "
                f"is sequentially lower than latest ledger release '{self.latest_entry.version}'."
            )


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


    def _reconstruct_historical_state(self) -> tuple[dict[str, str], list[str]]:
        """Compiles historical entry strings chronologically into a clean state map.

        Returns:
            A tuple containing a dictionary of scalar properties and an ordered list of
            historical OS mapping match strings tracking original insertion layout.
        """
        self._logger.debug(
            "Reconstructing absolute state timeline by compiling history..."
        )
        history_map: dict[str, str] = {}

        # Extract original sequence layout using a clean forward-pass scanner
        ordered_historical_flavors = self._extract_original_layout_order()

        # Compile state overrides by reading entries in reverse chronological order
        for entry in reversed(self.entries):
            self._logger.debug(f"Collating change bullets from version block: {entry.version}")

            for row in entry.changes.splitlines():
                self._parse_historical_state_row(row, history_map, ordered_historical_flavors)

            self._parse_human_readable_log_mutations(entry, history_map, ordered_historical_flavors)

        return history_map, ordered_historical_flavors

    def _extract_original_layout_order(self) -> list[str]:
        """Scans entries chronologically to lock in original insertion layout order."""
        ordered_flavors: list[str] = []

        for entry in self.entries:
            for row in entry.changes.splitlines():
                clean_row = row.strip().lstrip("*").strip()
                if "=" in clean_row:
                    h_key, _ = clean_row.split("=", 1)
                    if h_key.startswith("os_mappings."):
                        parts = h_key.split(".")
                        if len(parts) >= 2:
                            flavor = parts[1].strip()
                            if flavor not in ordered_flavors:
                                ordered_flavors.append(flavor)

        return ordered_flavors

    def _parse_historical_state_row(
        self, row: str, history_map: dict[str, str], ordered_flavors: list[str]
    ) -> None:
        """Parses a single row from a change log block into primitive state properties."""
        clean_row = row.strip().lstrip("*").strip()
        if "=" in clean_row:
            h_key, h_val = clean_row.split("=", 1)
            history_map[h_key.strip()] = h_val.strip()

    def _parse_human_readable_log_mutations(
        self, entry: ChangelogEntry, history_map: dict[str, str], ordered_flavors: list[str]
    ) -> None:
        """Extracts macro status updates and structural pruning alerts from human logs."""
        if "Toggled repository keyring strategy to: dynamic" in entry.changes:
            history_map["dynamic_keyring"] = "true"
        elif "Toggled repository keyring strategy to: static" in entry.changes:
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

        pruned_match = re.search(r"Removed os_mappings\.([^\s\n\.]+)\.", entry.changes)
        if pruned_match:
            matched_flavor = pruned_match.group(1).strip()
            if matched_flavor in ordered_flavors:
                ordered_flavors.remove(matched_flavor)


    def _calculate_diff_bullets(self, config: PackageConfig) -> list[str]:
        """Compares incoming config against historical state to generate bullet lines.

        Args:
            config: Strongly typed, validated package configuration properties.

        Returns:
            A list of formatted text bullet strings representing structural modifications.
        """
        if not self.latest_entry:
            return self._generate_genesis_bullets(config)

        return self._calculate_incremental_deltas(config)


    def _generate_genesis_bullets(self, config: PackageConfig) -> list[str]:
        """Assembles baseline initial entry blocks for unreleased packages.

        Args:
            config: Strongly typed, validated package configuration properties.

        Returns:
            A list of scalar key assignments mapping out the initial file state tracks.
        """
        self._logger.info(
            f"Generating genesis release changelog block for: {config.name} ({config.version})"
        )
        bullet_lines: list[str] = [
            "  * Initial package definition established.",
            f"  * description={config.description}",
            f"  * copyright_year={config.copyright_year}",
            f"  * dynamic_keyring={str(config.dynamic_keyring).lower()}",
            f"  * repo.url={config.repo.url}",
            f"  * repo.suites={config.repo.suites}",
            f"  * repo.components={config.repo.components}",
            f"  * repo.key_url={config.repo.key_url}"
        ]

        for match_key, mapping in config.os_mappings.items():
            bullet_lines.append(f"  * os_mappings.{match_key}.distro={mapping.distro}")
            bullet_lines.append(f"  * os_mappings.{match_key}.codename={mapping.codename}")

        return bullet_lines


    def _calculate_incremental_deltas(self, config: PackageConfig) -> list[str]:
        """Calculates precise field differentials against reconstructed historical maps.

        Args:
            config: Strongly typed, validated package configuration properties.

        Returns:
            A list of structural alteration descriptions and scalar modifications.
        """
        if not self.latest_entry:
            self._logger.error("Incremental delta check aborted: No valid historical ledger entries discovered.")
            return []

        # Initialize as a pure empty list slate. Do not pre-seed the version line yet!
        bullet_lines: list[str] = []

        history_map, historical_matches = self._reconstruct_historical_state()

        # Execute lean sub-helpers to accumulate distinct delta changes if they exist
        self._check_scalar_property_changes(bullet_lines, history_map, config)
        self._check_keyring_strategy_toggle(bullet_lines, history_map, config)
        self._check_granular_os_mapping_changes(
            bullet_lines, history_map, historical_matches, config
        )
        self._check_os_mapping_pruning(bullet_lines, historical_matches, config)

        # FIX 2: Only inject the version upgrade header bullet if field mutations were discovered!
        if bullet_lines:
            self._logger.info(
                f"Calculating delta differences for version upgrade: "
                f"{self.latest_entry.version} -> {config.version}"
            )
            bullet_lines.insert(0, f"  * Updated version to {config.version}")

        return bullet_lines



    def _check_scalar_property_changes(
        self, bullet_lines: list[str], history_map: dict[str, str], config: PackageConfig
    ) -> None:
        """Appends bullet entries if standard configuration or repo properties changed."""
        if "description" in history_map and history_map["description"] != config.description:
            self._logger.debug("Change detected: Package 'description' field updated.")
            bullet_lines.append(f"  * Modified description: {config.description}")

        if "repo.url" in history_map and history_map["repo.url"] != config.repo.url:
            self._logger.debug("Change detected: Package 'repo.url' field updated.")
            bullet_lines.append(f"  * Modified repo.url: {config.repo.url}")

        if "repo.suites" in history_map and history_map["repo.suites"] != config.repo.suites:
            self._logger.debug("Change detected: Package 'repo.suites' field updated.")
            bullet_lines.append(f"  * Modified repo.suites: {config.repo.suites}")

        if "repo.components" in history_map and history_map["repo.components"] != config.repo.components:
            self._logger.debug("Change detected: Package 'repo.components' field updated.")
            bullet_lines.append(f"  * Modified repo.components: {config.repo.components}")

        if "repo.key_url" in history_map and history_map["repo.key_url"] != config.repo.key_url:
            self._logger.debug("Change detected: Package 'repo.key_url' field updated.")
            bullet_lines.append(f"  * Modified repo.key_url: {config.repo.key_url}")


    def _check_keyring_strategy_toggle(
        self, bullet_lines: list[str], history_map: dict[str, str], config: PackageConfig
    ) -> None:
        """Appends bullet entry if operational keyring strategies were toggled."""
        prev_dynamic = history_map.get("dynamic_keyring") == "true"
        if config.dynamic_keyring != prev_dynamic:
            self._logger.debug("Change detected: Keyring operational strategy toggled.")
            strategy_name = "dynamic" if config.dynamic_keyring else "static"
            bullet_lines.append(f"  * Toggled repository keyring strategy to: {strategy_name}")


    def _check_granular_os_mapping_changes(
        self,
        bullet_lines: list[str],
        history_map: dict[str, str],
        historical_matches: list[str],
        config: PackageConfig,
    ) -> None:
        """Appends modifications located inside active, matching OS rule subsets."""
        for match_key, mapping in config.os_mappings.items():
            if match_key in historical_matches:
                hist_dist = history_map.get(f"os_mappings.{match_key}.distro")
                hist_codename = history_map.get(f"os_mappings.{match_key}.codename")

                if (hist_dist and hist_dist != mapping.distro) or \
                   (hist_codename and hist_codename != mapping.codename):

                    self._logger.debug(
                        f"Change detected: Properties modified "
                        f"inside os_mappings rule '{match_key}'."
                    )
                    bullet_lines.append(f"  * Modified os_mappings rule matching {match_key}")
                    if hist_dist != mapping.distro:
                        bullet_lines.append(f"  * os_mappings.{match_key}.distro={mapping.distro}")
                    if hist_codename != mapping.codename:
                        bullet_lines.append(
                            f"  * os_mappings.{match_key}.codename={mapping.codename}"
                        )


    def _check_os_mapping_pruning(
        self, bullet_lines: list[str], historical_matches: list[str], config: PackageConfig
    ) -> None:
        """Appends entries for historical mapping targets dropped from configuration."""
        current_matches = set(config.os_mappings.keys())
        for old_match in sorted(historical_matches):
            if old_match not in current_matches:
                self._logger.debug(f"Change detected: OS mapping rule flavor '{old_match}' pruned.")
                bullet_lines.append(f"  * Removed os_mappings.{old_match}.")


    def to_package_config(self) -> PackageConfig:
        """Reverse-engineers the current parsed historical state back into a PackageConfig DVO."""
        self._logger.debug("Reconstructing config structures from parsed historical metrics...")

        # Unpack ordered_historical_flavors as a sequence list instead of historical_matches set
        history_map, ordered_historical_flavors = self._reconstruct_historical_state()

        raw_extracted_name = (
            self.latest_entry.package_name if self.latest_entry else "unknown-package"
        )
        version = self.latest_entry.version if self.latest_entry else "1.0.0"

        package_name = raw_extracted_name.strip()
        for suffix in ["-repo-config", "-archive-keyring"]:
            if package_name.endswith(suffix):
                package_name = package_name[:-len(suffix)].strip()

        description = history_map.get("description", "")
        copyright_year = int(history_map.get("copyright_year", "2026"))
        dynamic_keyring = history_map.get("dynamic_keyring", "false") == "true"

        repo_config = PackageRepoConfig(
            url=history_map.get("repo.url", ""),
            suites=history_map.get("repo.suites", ""),
            components=history_map.get("repo.components", ""),
            key_url=history_map.get("repo.key_url", ""),
        )

        # FIX 3: Iterate straight through the chronological list layout. No sorting!
        # This completely preserves the user's exact original dictionary entry placement order.
        os_mappings = {}
        for flavor in ordered_historical_flavors:
            os_mappings[flavor] = PackageOSMappingConfig(
                distro=history_map.get(f"os_mappings.{flavor}.distro", ""),
                codename=history_map.get(f"os_mappings.{flavor}.codename", ""),
            )

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
        templates_dir: Path,
        current_time: str | None = None,
    ) -> str:
        """Calculates differences and generates an updated changelog ledger using templates.

        Args:
            config: Strongly typed, validated package configuration properties.
            project_config: Strongly typed global project baseline metadata definitions.
            templates_dir: Explicit filesystem Path to locate the required templates pool.
            current_time: An optional exact timestamp override string for deterministic testing.

        Returns:
            The complete multi-release changelog text payload.

        Raises:
            FileNotFoundError: If the mandatory 'changelog.jinja2' file layout asset
                is missing from the specified templates directory tracking paths.
        """
        # Run our modular, decoupled version validation loop
        self._compare_versions(config.version)

        self._logger.debug(f"Calculating configuration delta checks for package: {config.name}")

        target_template = templates_dir / "changelog.jinja2"
        if not target_template.exists():
            err_msg = (
                f"Fatal architecture breach: Required layout file "
                f"'changelog.jinja2' is missing from: {templates_dir}"
                )
            self._logger.emergency(err_msg)
            raise FileNotFoundError(err_msg)

        resolved_time = current_time if current_time is not None else formatdate(localtime=True)
        # Inside generate_next_version, right after calculating bullets:
                # 1. Calculate out your bullet metrics arrays
        bullet_lines = self._calculate_diff_bullets(config)

        # Short-circuit optimization: If no fields changed, preserve exact idempotency
        if not bullet_lines:
            self._logger.info("Idempotent state verified: No structural parameters or configurations changed.")
            return self._raw_text

        # Validate version bumps. If the manifest has structural modifications
        # but the version matches the latest ledger entry on disk, block the build!
        if self.latest_entry and config.version == self.latest_entry.version:
            err_msg = (
                f"Validation error: Manifest modified without version bump. "
                f"Version '{config.version}' is already recorded in history logs. "
                f"Increment your version configuration to register these changes."
            )
            self._logger.error(err_msg)
            raise ValueError("Manifest modified without version bump")

        # Turn the soft check into a mandatory, non-negotiable architectural gate rail
        target_template = templates_dir / "changelog.jinja2"
        if not target_template.exists():
            err_msg = (
                f"Fatal architecture breach: Required layout file 'changelog.jinja2' "
                f"is missing from specified directory track: {templates_dir}"
            )
            self._logger.emergency(err_msg)
            raise FileNotFoundError(err_msg)

        # Once validated, proceed directly with compile and render operations
        self._logger.info("Initializing external changelog layout compilation pass...")
        jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(templates_dir)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True
        )
        template = jinja_env.get_template("changelog.jinja2")

        # Clean structural prefixes (* ) off the lines for clean template rendering loops
        clean_bullets = [line.lstrip(" ").lstrip("*").strip() for line in bullet_lines]

        rendered_block = template.render(
            package_name=config.name,
            package_suffix=project_config.package_suffix,
            version=config.version,
            changelog_bullets=clean_bullets,
            maintainer_name=project_config.maintainer_name,
            maintainer_email=project_config.maintainer_email,
            current_date=resolved_time
        )

        return f"{rendered_block.strip()}\n\n{self._raw_text}".strip() + "\n"

