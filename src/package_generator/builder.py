# src/package_generator/builder.py
"""Debian package layout builder service.

Infrastructure coordination layer managing filesystem directory tree layouts,
template file resource loading compilation tracks, and workspace purges.
"""

import shutil
from pathlib import Path

from .changelog import Changelog
from .compiler import DebianTemplateCompiler
from .downloader import Downloader
from .gpg import GpgEngine
from .logger import Logger
from .models import PackageConfig, ProjectConfig


class DebianPackageBuilder:
    """Coordinating infrastructure layer managing physical file generation tasks."""

    def __init__(
        self,
        sources_dir: Path,
        templates_dir: Path,
        logger: "Logger",  # Prevent circular import layout paths
        compiler: DebianTemplateCompiler,
        downloader: Downloader | None = None,
        gpg_engine: GpgEngine | None = None,
    ) -> None:
        """Initializes the package builder service coordinator.

        Args:
            sources_dir: Directory where package source trees are compiled.
            templates_dir: Directory where template files are stored.
            logger: An injected PSR-3 compliant diagnostic logging service.
            compiler: An injected template compilation engine service instance.
            downloader: Optional custom network resource downloader engine service.
            gpg_engine: Optional custom cryptographic PPG dearmoring engine service.
        """
        self._sources_dir = sources_dir
        self._templates_dir = templates_dir
        self._logger = logger
        self._compiler = compiler
        self._downloader = downloader if downloader is not None else Downloader(logger=logger)
        self._gpg_engine = gpg_engine if gpg_engine is not None else GpgEngine(logger=logger)

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
        """
        self._logger.debug(f"Initializing directory layout compilation for package: {config.name}")

        package_root_dir = self._sources_dir / config.name
        target_debian_dir = package_root_dir / "debian"

        # Check for pre-existing history tracking files BEFORE creating directories
        changelog_file_path = target_debian_dir / "changelog"
        existing_history_text = ""

        if changelog_file_path.exists():
            self._logger.info(f"Discovered pre-existing changelog file at: {changelog_file_path}")
            existing_history_text = changelog_file_path.read_text(encoding="utf-8")

        # Physically create the directory structures safely on the platter
        target_debian_dir.mkdir(parents=True, exist_ok=True)

        # Execute broken-down sub-orchestration helper functions
        self._orchestrate_changelog(
            changelog_file_path=changelog_file_path,
            existing_history_text=existing_history_text,
            config=config,
            project_config=project_config,
            current_time=current_time,
        )

        self._process_signing_key(
            target_debian_dir=target_debian_dir,
            config=config,
        )

        self._compile_templates(
            target_debian_dir=target_debian_dir,
            config=config,
            project_config=project_config,
        )

        self._logger.debug(
            "Applying flat 644 permission pass across all generated package files..."
        )

        # Force absolutely every file inside the directory to 0o644
        for generated_file in target_debian_dir.iterdir():
            if generated_file.is_file():
                generated_file.chmod(0o644)
                self._logger.debug(
                    f"Forced read-write permissions (644) for file: {generated_file.name}"
                )

        self._logger.info(f"Successfully finalized debian/ container at: {target_debian_dir}")
        return target_debian_dir

    def _orchestrate_changelog(
        self,
        changelog_file_path: Path,
        existing_history_text: str,
        config: PackageConfig,
        project_config: ProjectConfig,
        current_time: str | None,
    ) -> None:
        """Handles reading, calculating, and saving the dynamic version changelog ledger."""
        changelog_handler = Changelog(raw_text=existing_history_text, logger=self._logger)

        # FIX 2: Pass our clean, type-safe instance path directly
        updated_changelog_content = changelog_handler.generate_next_version(
            config=config,
            project_config=project_config,
            templates_dir=self._templates_dir,
            current_time=current_time,
        )

        with open(changelog_file_path, "w", encoding="utf-8", newline="\n") as file_stream:
            file_stream.write(updated_changelog_content)


    def _process_signing_key(self, target_debian_dir: Path, config: PackageConfig) -> None:
        """Downloads, checks armor status, and persists the security keyring to disk."""
        if config.dynamic_keyring:
            return

        self._logger.info(
            f"Static keyring strategy verified for '{config.name}'. Extracting signing assets..."
        )

        # 1. Download raw bytes directly from the network wire
        raw_bytes = self._downloader.download_bytes(url=config.repo.key_url)

        # 2. Check the signature prefix directly within this orchestration routine
        if raw_bytes.startswith(b"-----BEGIN PGP"):
            self._logger.debug("Payload is ASCII armored text. Invoking GpgEngine dearmor filter.")
            binary_key_bytes = self._gpg_engine.dearmor(ascii_text=raw_bytes.decode("utf-8"))
        else:
            self._logger.debug("Payload is already raw binary data. Bypassing dearmor filter.")
            binary_key_bytes = raw_bytes

        # 3. Commit the verified binary keyring to disk
        keyrings_dir = target_debian_dir.parent / "usr" / "share" / "keyrings"
        keyrings_dir.mkdir(parents=True, exist_ok=True)

        output_key_file = keyrings_dir / f"{config.name}-archive-keyring.gpg"
        output_key_file.write_bytes(binary_key_bytes)
        self._logger.debug(
            f"Successfully recorded static binary signing asset on disk path: {output_key_file}"
        )

    def _compile_templates(
        self,
        target_debian_dir: Path,
        config: PackageConfig,
        project_config: ProjectConfig,
    ) -> None:
        """Iterates over available templates and renders them to the workspace container."""
        self._logger.debug("Dynamically discovering available system template assets...")
        available_templates = self._compiler._env.list_templates()

        for template_name in available_templates:
            if template_name == "changelog":
                self._logger.emergency(
                    "Fatal architecture violation: A static template named 'changelog' "
                    "was discovered inside the templates pool directory. Changelog generation "
                    "must be handled exclusively by the object-oriented state ledger engine."
                )
                raise ValueError(
                    "A template named 'changelog' was discovered inside your debian package "
                    "templates directory. You must remove this file to continue."
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

    def remove_package_tree(self, target_dir: Path | None = None) -> None:
        """Safely removes a targeted sources directory tree from the filesystem.

        Args:
            target_dir: Optional explicit Path container to purge. If omitted,
                defaults to the builder instance's assigned sources directory path.
        """
        # Resolve which directory track target to target for the purge pass
        dir_to_remove = target_dir if target_dir is not None else self._sources_dir

        self._logger.debug(
            f"Initializing complete directory tree purge at path: {dir_to_remove}"
        )

        if dir_to_remove.exists():
            shutil.rmtree(dir_to_remove)
            self._logger.info(
                f"Successfully removed workspace target tree layout: {dir_to_remove}"
            )
