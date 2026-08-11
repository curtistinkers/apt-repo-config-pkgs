# src/package_generator/cli.py
"""Command-line interface.

Command-line interface specification layer. Maps incoming terminal arguments,
subcommands, and debug flags to core business logic orchestration layers.
"""

import sys
from pathlib import Path

import click
import yaml

from .builder import DebianPackageBuilder
from .logger import Logger
from .manifest import RepositoryManifest


@click.group()
def main_cli() -> None:
    """A clean, object-oriented Debian package repository generation engine."""
    pass


@main_cli.command(name="build")
@click.option(
    "--manifests-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=Path("manifests"),
    help="Directory containing your input YAML manifest files."
)
@click.option(
    "--sources-dir",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=Path("dpkg-sources"),
    help="Target directory where package source layouts will be constructed."
)
@click.option(
    "--debug",
    is_flag=True,
    default=False,
    help="Enables verbose debugging console outputs."
)
def build_packages_command(manifests_dir: Path, sources_dir: Path, debug: bool) -> None:
    """Scans your manifests directory and orchestrates Debian package folders."""
    # Initialize the Logger service dynamically based on the debug flag
    log_level = "debug" if debug else "info"
    logger = Logger(min_terminal_level=log_level)

    logger.debug("Initializing execution environment pipeline tracks...")
    logger.debug(f"Reading inputs from directory: {manifests_dir}")
    logger.debug(f"Targeting outputs to directory: {sources_dir}")

    # Inject the logger instance straight into the builder constructor
    builder = DebianPackageBuilder(sources_dir=sources_dir, logger=logger)
    processed_count = 0

    for item in sorted(manifests_dir.iterdir()):
        if item.is_file() and item.suffix in [".yaml", ".yml"]:
            logger.debug(f"Loading file stream: {item.name}")

            try:
                with open(item, encoding="utf-8") as file_stream:
                    raw_yaml_data = yaml.safe_load(file_stream)

                manifest = RepositoryManifest(raw_data=raw_yaml_data, logger=logger)

                # The builder uses the injected logger internally to report success notes
                builder.create_package_tree(manifest.config)
                processed_count += 1

            except Exception as error:
                logger.emergency(f"Execution Error processing {item.name}: {error}")
                sys.exit(1)

    logger.info(f"Package folder orchestration completed. Total built: {processed_count}")


@main_cli.command(name="clean")
@click.option(
    "--sources-dir",
    type=click.Path(path_type=Path),
    default=Path("dpkg-sources"),
    help="Target directory to be cleaned and removed from the workspace."
)
def clean_workspace_command(sources_dir: Path) -> None:
    """Removes the generated package sources directory from your workspace."""
    # The clean subcommand runs with standard info tracking by default
    logger = Logger(min_terminal_level="info")
    logger.info(f"Cleaning workspace directory: {sources_dir}")

    # Inject the logger instance into the workspace removal tracker
    builder = DebianPackageBuilder(sources_dir=sources_dir, logger=logger)
    builder.remove_package_tree()
