# src/package_generator/builder.py
"""Debian package layout builder service.

Infrastructure coordination layer managing filesystem directory tree layouts,
template file resource loading compilation tracks, and workspace purges.
"""

import shutil
from pathlib import Path

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
    ) -> Path:
        """Creates a clean source tree and compiles all available Debian layout files.

        Args:
            config: Validated, strongly typed package configuration parameters.
            project_config: Validated, strongly typed global project parameters.

        Returns:
            The resolved physical Path object targeting the package's internal
            debian/ directory container.
        """
        self._logger.debug(f"Initializing directory layout compilation for package: {config.name}")

        # Construct standard layout target path: sources/<package_name>/debian
        package_root_dir = self._sources_dir / config.name
        target_debian_dir = package_root_dir / "debian"

        # Physically create the directory structures safely on the platter
        target_debian_dir.mkdir(parents=True, exist_ok=True)

        self._logger.debug("Dynamically discovering available system template assets...")

        # FIX: Query the compiler's Jinja2 environment to find all files in the templates folder
        available_templates = self._compiler._env.list_templates()

        for template_name in available_templates:
            self._logger.debug(f"Processing and compiling workspace template line: {template_name}")

            # Execute the template variable injection pass
            compiled_text_stream = self._compiler.render_template(
                template_name=template_name,
                package_config=config,
                project_config=project_config,
            )

            # Define the exact destination file target location on disk
            output_file_path = target_debian_dir / template_name

            # Safely create parent sub-folders if a multi-nested layout exists
            output_file_path.parent.mkdir(parents=True, exist_ok=True)

            # Physically write out the plain text stream onto your hard drive
            with open(output_file_path, "w", encoding="utf-8", newline="\n") as file_writer:
                file_writer.write(compiled_text_stream)

        self._logger.info(f"Successfully orchestrated debian/ container at: {target_debian_dir}")
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
