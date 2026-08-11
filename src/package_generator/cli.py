"""
package_generator.cli
=====================
Command-line interface specification layer. Maps incoming terminal arguments,
subcommands, and debug flags to core business logic orchestration layers.
"""

import sys
from pathlib import Path

import click
import yaml

from .builder import DebianPackageBuilder
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
    if debug:
        click.echo("DEBUG: Initializing execution environment pipeline tracks...")
        click.echo(f"DEBUG: Reading inputs from directory: {manifests_dir}")
        click.echo(f"DEBUG: Targeting outputs to directory: {sources_dir}")

    # Initialize our infrastructure service coordinator class
    builder = DebianPackageBuilder(sources_dir=sources_dir)
    processed_count = 0

    # Iterate through the manifests directory to find configuration layouts
    for item in sorted(manifests_dir.iterdir()):
        if item.is_file() and item.suffix in [".yaml", ".yml"]:
            if debug:
                click.echo(f"DEBUG: Loading file stream: {item.name}")

            try:
                # 1. READ: Load raw text track from the filesystem platter
                with open(item, "r", encoding="utf-8") as file_stream:
                    raw_yaml_data = yaml.safe_load(file_stream)

                # 2. VALIDATE & COMPILE: Feed primitive dict to our translator domain layer
                manifest = RepositoryManifest(raw_data=raw_yaml_data)

                # 3. ORCHESTRATE: Hand type-safe config object to infrastructure builder layer
                builder.create_package_tree(manifest.config)

                click.echo(f"Successfully processed package manifest: {manifest.config.name}")
                processed_count += 1

            except Exception as error:
                click.echo(f"Execution Error processing {item.name}: {error}", err=True)
                sys.exit(1)

    click.echo(f"Package tree creation completed. Total built: {processed_count}")

@main_cli.command(name="clean")
@click.option(
    "--sources-dir",
    type=click.Path(path_type=Path),
    default=Path("dpkg-sources"),
    help="Target directory to be cleaned and removed from the workspace."
)
def clean_workspace_command(sources_dir: Path) -> None:
    """Removes the generated package sources directory from your workspace."""
    click.echo(f"Cleaning workspace directory: {sources_dir}")

    # 1. Initialize our infrastructure builder targeting the specified path
    builder = DebianPackageBuilder(sources_dir=sources_dir)

    # 2. Trigger your clean, renamed backend removal service method
    builder.remove_package_tree()

    click.echo("Workspace cleanup completed successfully.")
