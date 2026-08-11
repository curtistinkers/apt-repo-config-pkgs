# src/package_generator/builder.py
"""Builds and cleans the package files.

Infrastructure coordination layer managing filesystem writes, directory tree
orchestration, and package building workflows.
"""

import shutil
from pathlib import Path

from .models import PackageConfig


class DebianPackageBuilder:
    """Facilitates the construction of repository packages.

    Coordinates filesystem actions, template compilation, and directory layout preparation for
    individual packages.
    """
    def __init__(self, sources_dir: Path) -> None:
        """Initializes the package builder with standard target directory context.

        Args:
            sources_dir (Path): The root workspace container folder where package
                                source trees are extracted and managed.
        """
        self._sources_dir = sources_dir

    def create_package_tree(self, config: PackageConfig) -> Path:
        """Builds the package tree.

        Creates a clean, isolated source workspace matching the package name schema
        and ensures the critical 'debian/' directory container exists.

        Args:
            config (PackageConfig): Validated, strongly typed package configuration parameters.

        Returns:
            Path: The resolved physical Path object targeting the package's internal debian folder.
        """
        # Build out standard Debian layout: sources/<package_name>/debian
        package_root_dir = self._sources_dir / config.name
        target_debian_dir = package_root_dir / "debian"

        # Physically create the directory paths on disk safely.
        # parents=True acts like 'mkdir -p' in bash, creating missing parent folders automatically.
        target_debian_dir.mkdir(parents=True, exist_ok=True)

        return target_debian_dir

    def remove_package_tree(self) -> None:
        """Cleans the package tree.

        Safely removes the targeted sources directory tree from the filesystem platter
        if it exists. Handles directories containing files and nested sub-folders.
        """
        if self._sources_dir.exists():
            # rmtree deletes the folder and everything inside it, matching 'rm -rf' in bash
            shutil.rmtree(self._sources_dir)
