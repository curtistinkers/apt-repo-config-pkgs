# src/package_generator/builder.py
"""Debian package layout builder service.

Infrastructure coordination layer managing filesystem directory tree layouts,
template file resource loading compilation tracks, and workspace purges.
"""

import shutil
from pathlib import Path

from .changelog import Changelog
from .compiler import DebianTemplateCompiler
from .logger import Logger
from .models import PackageConfig, ProjectConfig


class DebianPackageBuilder:
    """Coordinating infrastructure layer managing physical file generation tasks."""

    def __init__(
        self,
        sources_dir: Path,
        logger: "Logger",  # Using standard generic to prevent circular import layout paths
        compiler: DebianTemplateCompiler,
    ) -> None:
        """Initializes the package builder service coordinator.

        Args:
            sources_dir: Root workspace directory container path where package
                source trees are compiled on disk.
            logger: An injected PSR-3 compliant diagnostic logging service.
            compiler: An injected template compilation engine service instance.
        """
        self._sources_dir = sources_dir
        self._logger = logger
        self._compiler = compiler

    def create_package_tree(
        self,
        config: PackageConfig,
        project_config: ProjectConfig,
        current_time: str | None = None,
    ) -> Path:
        """Creates a clean source tree and compiles all available Debian layout files.

        Args:
            config: Validated, strongly typed package configuration parameters.
            project_config: Validated, strongly typed global project parameters.
            current_time: An optional RFC-2822 string override used strictly to lock
                down deterministic test outcomes. Defaults to None (uses system time).

        Returns:
            The resolved physical Path object targeting the package's internal
            debian/ directory container.

        Raises:
            ValueError: If a static template file named 'changelog' is discovered
                inside the templates directory tracks, breaking the dynamic state
                ledger compilation engine boundaries.
        """
        self._logger.debug(f"Initializing directory layout compilation for package: {config.name}")

        package_root_dir = self._sources_dir / config.name
        target_debian_dir = package_root_dir / "debian"

        # Check for pre-existing history tracking files BEFORE wiping or creating directories
        changelog_file_path = target_debian_dir / "changelog"
        existing_history_text = ""

        if changelog_file_path.exists():
            self._logger.info(f"Discovered pre-existing changelog file at: {changelog_file_path}")
            existing_history_text = changelog_file_path.read_text(encoding="utf-8")

        # Physically create the directory structures safely on the platter
        target_debian_dir.mkdir(parents=True, exist_ok=True)

        # 1. ORCHESTRATE CHANGELOG LIFECYCLE TRACKING PERSISTENCE
        # Feed existing history or blank slate into the dynamic diff assembler engine
        changelog_handler = Changelog(raw_text=existing_history_text, logger=self._logger)

        updated_changelog_content = changelog_handler.generate_next_version(
            config=config,
            project_config=project_config,
            current_time=current_time,
        )

        # Write out the persistent, incremented changelog ledger with strict Unix newlines
        with open(changelog_file_path, "w", encoding="utf-8", newline="\n") as file_stream:
            file_stream.write(updated_changelog_content)

                # 2. RENDER THE REST OF THE DEBIAN TEMPLATE PLATES POOL
        self._logger.debug("Dynamically discovering available system template assets...")
        available_templates = self._compiler._env.list_templates()

        for template_name in available_templates:
            # FIX: Convert the silent bypass into a hard architecture guard rail exception
            if template_name == "changelog":
                self._logger.emergency(
                    "Fatal architecture violation: A static template named 'changelog' "
                    "was discovered inside the templates pool directory. Changelog generation "
                    "must be handled exclusively by the object-oriented state ledger engine."
                )
                raise ValueError(
                    "A template named 'changelog' was discovered inside your templates directory. "
                    "Remove this asset to clear the package building gatekeeper."
                )

            self._logger.debug(f"Processing and compiling workspace template line: {template_name}")

            compiled_text_stream = self._compiler.render_template(
                template_name=template_name,
                package_config=config,
                project_config=project_config,
            )

            output_file_path = target_debian_dir / template_name
            output_file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file_path, "w", encoding="utf-8", newline="\n") as file_stream:
                file_stream.write(compiled_text_stream)

        self._logger.info(f"Successfully finalized debian/ container at: {target_debian_dir}")
        return target_debian_dir

    def remove_package_tree(self) -> None:
        """Safely removes the targeted sources directory tree from the filesystem.

        Handles folders containing active build configuration files and nested
        sub-directories layout structures.
        """
        self._logger.debug(
            f"Initializing complete directory tree purge at path: {self._sources_dir}"
        )

        if self._sources_dir.exists():
            shutil.rmtree(self._sources_dir)
            self._logger.info(
                f"Successfully removed workspace target tree layout: {self._sources_dir}"
            )
