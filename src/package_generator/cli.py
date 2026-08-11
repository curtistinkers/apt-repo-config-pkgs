"""Command-line interface specification layer.

Maps incoming terminal arguments, subcommands, and debug flags to core business
logic orchestration layers.
"""

import sys
from pathlib import Path

import click
import yaml

from .builder import DebianPackageBuilder
from .compiler import DebianTemplateCompiler
from .logger import Logger
from .manifest import RepositoryManifest
from .project_manifest import ProjectManifest


@click.group()
def main_cli() -> None:
    """A clean, object-oriented Debian package repository generation engine."""
    pass


@main_cli.command(name="build")
@click.option(
    "--project-config",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    default=Path("config.yaml"),
    help="Path to your global project configuration YAML file."
)
@click.option(
    "--manifests-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=Path("manifests"),
    help="Directory containing your input YAML manifest files."
)
@click.option(
    "--templates-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=Path("templates"),
    help="Directory containing your Debian configuration template files."
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
def build_packages_command(
    project_config: Path,
    manifests_dir: Path,
    templates_dir: Path,
    sources_dir: Path,
    debug: bool
) -> None:
    """Scans your manifests directory and orchestrates Debian package folders."""
    log_level = "debug" if debug else "info"
    logger = Logger(min_terminal_level=log_level)

    logger.debug("Initializing execution environment pipeline tracks...")
    logger.debug(f"Reading global configurations from: {project_config}")
    logger.debug(f"Reading inputs from directory: {manifests_dir}")
    logger.debug(f"Reading templates from directory: {templates_dir}")
    logger.debug(f"Targeting outputs to directory: {sources_dir}")

    try:
        with open(project_config, "r", encoding="utf-8") as project_stream:
            raw_project_data = yaml.safe_load(project_stream)

        proj_manifest = ProjectManifest(raw_data=raw_project_data, logger=logger)

    except Exception as project_error:
        logger.emergency(f"Fatal validation failure inside global project config: {project_error}")
        sys.exit(1)

    # FIX: Use the user-supplied templates directory path dynamically
    resolved_templates_path = templates_dir / "debian"
    compiler = DebianTemplateCompiler(templates_dir=resolved_templates_path, logger=logger)

    builder = DebianPackageBuilder(
        sources_dir=sources_dir,
        logger=logger,
        compiler=compiler
    )

    processed_count = 0

    for item in sorted(manifests_dir.iterdir()):
        if item.is_file() and item.suffix in [".yaml", ".yml"]:
            logger.debug(f"Loading file stream: {item.name}")

            try:
                with open(item, "r", encoding="utf-8") as file_stream:
                    raw_yaml_data = yaml.safe_load(file_stream)

                manifest = RepositoryManifest(raw_data=raw_yaml_data, logger=logger)

                builder.create_package_tree(
                    config=manifest.config,
                    project_config=proj_manifest.config
                )
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
    logger = Logger(min_terminal_level="info")
    logger.info(f"Cleaning workspace directory: {sources_dir}")

    # FIX: Maintain a synchronized constructor setup layout signature contract
    dummy_templates_dir = Path("templates") / "debian"
    compiler = DebianTemplateCompiler(templates_dir=dummy_templates_dir, logger=logger)

    builder = DebianPackageBuilder(
        sources_dir=sources_dir,
        logger=logger,
        compiler=compiler
    )
    builder.remove_package_tree()
