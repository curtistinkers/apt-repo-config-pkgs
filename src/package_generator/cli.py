# src/package_generator/cli.py
"""Command-line interface specification layer.

Maps incoming terminal arguments, subcommands, and debug flags to core business
logic orchestration layers.
"""

import shutil
import sys
from pathlib import Path

import click
import yaml

from .builder import DebianPackageBuilder
from .compiler import DebianTemplateCompiler
from .downloader import Downloader
from .gpg import GpgEngine
from .logger import Logger
from .project_manifest import ProjectManifest
from .repository_manifest import RepositoryManifest


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
@click.option(
    "--bump-version",
    is_flag=True,
    default=False,
    help=(
        "Automatically bumps version parameters and rewrites manifests "
        "without interactive prompts if configuration changes are detected."
    )
)
def build_packages_command(
    project_config: Path,
    manifests_dir: Path,
    templates_dir: Path,
    sources_dir: Path,
    debug: bool,
    bump_version: bool,
) -> None:
    """Scans your manifests directory and orchestrates Debian package folders.

    Iterates chronologically through all YAML configuration files inside the
    manifests target workspace. For each manifest discovered, it resolves the
    underlying state timeline via the changelog engine, monitors for illegal
    version downgrades, and intercepts un-bumped configuration modifications. If
    a modified layout lacks a version bump, it either triggers an interactive
    user-confirmation prompt to auto-increment the file or uses the automatic
    version parameter flag to accept the update seamlessly.

    Args:
        project_config: Resolved physical filesystem Path targeting the global
            project.yaml maintainer parameter workspace.
        manifests_dir: Resolved physical filesystem Path targeting the folder
            container where repository manifest YAML files are stored.
        templates_dir: Resolved physical filesystem Path targeting the root
            directory where core raw debian template blocks reside.
        sources_dir: Resolved physical filesystem Path targeting the output
            workspace folder where source code trees are built.
        debug: Boolean option flag used to increase logging detail verbosity
            and toggle downstream execution diagnostic traces.
        bump_version: Boolean option flag used to auto-accept version changes
            and automatically increment modified manifest file versions.

    Raises:
        ValueError: If a fatal architecture violation occurs, such as a static
            changelog template file colliding with the state-diff engine.
        SystemExit: Terminates execution flow with code 1 if a lower-level
            unhandled parsing exception or filesystem lock-down occurs.
    """
    log_level = "debug" if debug else "info"
    logger = Logger(min_terminal_level=log_level)

    logger.debug("Initializing execution environment pipeline tracks...")
    logger.debug(f"Reading global configurations from: {project_config}")
    logger.debug(f"Reading inputs from directory: {manifests_dir}")
    logger.debug(f"Reading templates from directory: {templates_dir}")
    logger.debug(f"Targeting outputs to directory: {sources_dir}")

    try:
        with open(project_config, encoding="utf-8") as project_stream:
            raw_project_data = yaml.safe_load(project_stream)

        proj_manifest = ProjectManifest(raw_data=raw_project_data, logger=logger)

    except Exception as project_error:
        logger.emergency(f"Fatal validation failure inside global project config: {project_error}")
        sys.exit(1)

    # Use the user-supplied templates directory path dynamically
    templates_path = templates_dir / "debian"
    compiler = DebianTemplateCompiler(templates_dir=templates_path, logger=logger)



    downloader_service = Downloader(logger=logger)
    gpg_service = GpgEngine(logger=logger)

    # Inject the services down to the package directory builder coordinator
    builder = DebianPackageBuilder(
        sources_dir=sources_dir,
        templates_dir=templates_dir,
        logger=logger,
        compiler=compiler,
        downloader=downloader_service,
        gpg_engine=gpg_service,
    )

    processed_count = 0

    for item in sorted(manifests_dir.iterdir()):
        if item.is_file() and item.suffix in [".yaml", ".yml"]:
            logger.debug(f"Loading file stream: {item.name}")

            try:
                with open(item, encoding="utf-8") as file_stream:
                    raw_yaml_data = yaml.safe_load(file_stream)

                manifest = RepositoryManifest(raw_data=raw_yaml_data, logger=logger)

                # FIX 2: Execute an active loop block to handle interactive auto-bumps
                compiled_successfully = False
                while not compiled_successfully:
                    try:
                        builder.create_package_tree(
                            config=manifest.config,
                            project_config=proj_manifest.config
                        )
                        processed_count += 1
                        compiled_successfully = True
                    except ValueError as validation_error:
                        # Catch the unique string exception raised by our changelog engine
                        if "Manifest modified without version bump" in str(validation_error):

                            # Calculate the next logical micro version string value automatically
                            from packaging.version import Version
                            current_ver = Version(manifest.config.version)
                            next_version_str = (
                                f"{current_ver.major}.{current_ver.minor}.{current_ver.micro + 1}"
                            )

                            # Intercept flag state or launch an interactive click
                            # confirmation prompt block
                            prompt_msg = (
                                f"Manifest modified without version bump "
                                f"for '{manifest.config.name}'. Auto-bump version "
                                f"identifier to {next_version_str}?"
                            )

                            if bump_version or click.confirm(prompt_msg, default=False):
                                logger.info(
                                    f"Auto-bumping manifest file {item.name} "
                                    f"forward to v{next_version_str}..."
                                    )

                                # Rewrite the physical YAML manifest file directly on
                                # disk platter tracks
                                raw_yaml_data["version"] = next_version_str
                                with open(item, "w", encoding="utf-8") as yaml_out_stream:
                                    yaml.safe_dump(
                                        raw_yaml_data, yaml_out_stream, default_flow_style=False
                                    )

                                # Reload the manifest file instance state values into memory
                                # and cycle loop to re-try build
                                manifest = RepositoryManifest(raw_data=raw_yaml_data, logger=logger)
                                continue
                            else:
                                # User selected "No": Log an alert message, break loop,
                                # and skip file gracefully
                                logger.alert(
                                    f"Skipping package file {item.name} due to "
                                    f"state version mismatch."
                                )
                                break
                        raise  # Re-raise alternative genuine errors like rogue changelog templates

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

    if sources_dir.exists():
        try:
            shutil.rmtree(sources_dir)
            logger.info(f"Successfully removed workspace target tree layout: {sources_dir}")
        except Exception as error:
            logger.error(f"Failed to remove directory tree structure: {error}")
