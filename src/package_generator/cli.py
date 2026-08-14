# src/package_generator/cli.py
"""Command-line interface specification layer.

Maps incoming terminal arguments, subcommands, and debug flags to core business
logic orchestration layers.
"""

import dataclasses
import shutil
import sys
from pathlib import Path

import click
import yaml
from jinja2 import Environment, FileSystemLoader
from packaging.version import Version

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
    "--package",
    type=str,
    default=None,
    help="Targets a single specific package manifest name to build, skipping all others."
)
@click.option(
    "--no-download-keys",
    is_flag=True,
    default=False,
    help="Skips the network download and dearmor phase for static keyrings entirely."
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
    no_download_keys: bool,
    package: str | None,
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
        project_config: The global `config.yaml` package parameter file.
        manifests_dir: the directory where repository manifest YAML files are stored.
        templates_dir: The directory where template blocks reside.
        sources_dir: The output folder where source code trees are built.
        debug: ncrease logging detail and toggle downstream diagnostic traces.
        bump_version:Auto-accept version changes and increment manifest file versions.
        no_download_keys: Indicates whether the package builder should download signing keys.
        package: Name of the specific package to build.

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

    proj_manifest = _initialize_project_context(project_config, logger)

    compiler = DebianTemplateCompiler(templates_dir=templates_dir / "debian", logger=logger)
    builder = DebianPackageBuilder(
        sources_dir=sources_dir,
        templates_dir=templates_dir,
        logger=logger,
        compiler=compiler,
        downloader=Downloader(logger=logger),
        gpg_engine=GpgEngine(logger=logger),
    )

    _orchestrate_manifest_build_loop(
        manifests_dir=manifests_dir,
        project_config=proj_manifest,
        builder=builder,
        bump_version=bump_version,
        logger=logger,
        no_download_keys=no_download_keys,
        target_package=package
    )


def _initialize_project_context(project_config: Path, logger: Logger) -> ProjectManifest:
    """Loads and compiles the global project configuration manifest."""
    try:
        with open(project_config, encoding="utf-8") as project_stream:
            raw_project_data = yaml.safe_load(project_stream)
        return ProjectManifest(raw_data=raw_project_data, logger=logger)
    except Exception as project_error:
        logger.emergency(f"Fatal validation failure inside global project config: {project_error}")
        sys.exit(1)


def _orchestrate_manifest_build_loop(
    manifests_dir: Path,
    project_config: ProjectManifest,
    builder: DebianPackageBuilder,
    bump_version: bool,
    logger: Logger,
    no_download_keys: bool,
    target_package: str | None,
) -> None:
    """Iterates chronologically through directory contents to build manifest records."""
    processed_count = 0

    for item in sorted(manifests_dir.iterdir()):
        if item.is_file() and item.suffix in [".yaml", ".yml"]:
            logger.debug(f"Loading file stream: {item.name}")

            try:
                with open(item, encoding="utf-8") as file_stream:
                    raw_yaml_data = yaml.safe_load(file_stream)

                manifest = RepositoryManifest(raw_data=raw_yaml_data, logger=logger)

                # If a target package was requested, skip any file that doesn't match its name!
                if target_package is not None and manifest.config.name != target_package:
                    logger.debug(
                        f"Skipping package '{manifest.config.name}' (targeting '{target_package}')."
                    )
                    continue

                logger.debug(f"Loading file stream: {item.name}")
                compiled_successfully = False

                while not compiled_successfully:
                    try:
                        builder.create_package_tree(
                            config=manifest.config,
                            project_config=project_config.config,
                            no_download_keys=no_download_keys
                        )
                        processed_count += 1
                        compiled_successfully = True
                    except ValueError as validation_error:
                        manifest, compiled_successfully = _handle_version_bump_prompt(
                            item=item,
                            manifest=manifest,
                            validation_error=validation_error,
                            bump_version=bump_version,
                            logger=logger,
                            templates_dir=builder._templates_dir
                        )

            except Exception as error:
                logger.emergency(f"Execution Error processing {item.name}: {error}")
                sys.exit(1)

    logger.info(f"Package folder orchestration completed. Total built: {processed_count}")


def _handle_version_bump_prompt(
    item: Path,
    manifest: RepositoryManifest,
    validation_error: ValueError,
    bump_version: bool,
    logger: Logger,
    templates_dir: Path,
) -> tuple[RepositoryManifest, bool]:
    """Evaluates version bumps via prompts or re-raises generic ValueErrors."""
    if "Manifest modified without version bump" in str(validation_error):
        current_ver = Version(manifest.config.version)
        next_version_str = f"{current_ver.major}.{current_ver.minor}.{current_ver.micro + 1}"

        prompt_msg = (
            f"Manifest modified without version bump for '{manifest.config.name}'. "
            f"Auto-bump version identifier to {next_version_str}?"
        )

        if bump_version or click.confirm(prompt_msg, default=False):
            logger.info(f"Auto-bumping manifest file {item.name} forward to v{next_version_str}...")

            # FIX 1: Safely update our immutable frozen dataclass object using replace()
            updated_config = dataclasses.replace(manifest.config, version=next_version_str)


            native_env = Environment(
                loader=FileSystemLoader(str(templates_dir)),
                autoescape=False
            )

            # FIX 2: Map flat keys to perfectly match your mock_manifest_template variables pool
            manifest_template = native_env.get_template("manifest.jinja2")
            compiled_manifest_text = manifest_template.render(
                package_name=updated_config.name,
                version=updated_config.version,
                short_description=updated_config.description,
                copyright_year=updated_config.copyright_year,
                dynamic_keyring=updated_config.dynamic_keyring,
                repo_url=updated_config.repo.url if updated_config.repo else "",
                repo_suites=updated_config.repo.suites if updated_config.repo else "",
                repo_components=updated_config.repo.components if updated_config.repo else "",
                repo_key_url=updated_config.repo.key_url if updated_config.repo else "",
                repo_key_fingerprint=updated_config.repo.key_fingerprint if updated_config.repo else "", # noqa
                os_mappings=updated_config.os_mappings,
            )

            # Flush content to disk platter
            with open(item, "w", encoding="utf-8", newline="\n") as manifest_out:
                manifest_out.write(compiled_manifest_text)

            # FIX 3: Update our wrapper reference tracker so the next loop has the correct version
            manifest.config = updated_config
            return manifest, False

        else:
            logger.alert(f"Skipping package file {item.name} due to state version mismatch.")
            return manifest, True

    raise validation_error



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
