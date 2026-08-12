# tests/test_unit_cli.py
"""CLI unit tests.

Discrete unit specifications validating the argument parsing boundaries,
command routing, and option validations managed by the CLI interface group.
"""

from pathlib import Path

from click.testing import CliRunner

from package_generator.cli import main_cli


def test_unit_cli_build_subcommand_routes_correctly(
    tmp_path: Path,
    project_config: str
) -> None:
    """Validate build subcommand.

    Verifies that the CLI 'build' subcommand exists under our main interface
    group and executes with a successful exit status code 0.

    Args:
        tmp_path: A built-in pytest fixture providing a temporary directory path.
        project_config: A test fixture providing a valid raw project YAML string.
    """
    # Initialize an isolated Click command test runner
    runner = CliRunner()

    # Create safe sandbox folders
    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir()
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    sources_dir = tmp_path / "dpkg-sources"

    # Write out a project file
    project_file = tmp_path / "project.yaml"
    project_file.write_text(project_config, encoding="utf-8")

    # Pass the temporary project file path explicitly to clear the Click gate
    result = runner.invoke(main_cli, [
        "build",
        "--project-config", str(project_file),
        "--manifests-dir", str(manifests_dir),
        "--templates-dir", str(templates_dir),
        "--sources-dir", str(sources_dir)
    ])

    # ASSERTION: The command must route successfully
    assert result.exit_code == 0

def test_unit_cli_clean_subcommand_routes_correctly(tmp_path: Path) -> None:
    """Validate clean subcommand.

    Verifies that the CLI 'clean' subcommand exists under our main interface
    group and executes with a successful exit status code 0.

    Args:
        tmp_path: A built-in pytest fixture providing a temporary directory path.
    """
    # Initialize an isolated Click command test runner
    runner = CliRunner()

    # Create a safe sandbox directory for the clean command to target
    sandbox_dir = tmp_path / "dpkg-sources"
    sandbox_dir.mkdir()

    # Run the clean command targeting our isolated sandbox path container
    result = runner.invoke(main_cli, [
        "clean",
        "--sources-dir", str(sandbox_dir)
    ])

    # ASSERTION: The command must route successfully
    assert result.exit_code == 0

def test_unit_cli_build_subcommand_gracefully_handles_corrupted_syntax_files(
    tmp_path: Path,
    manifest_corrupted_garbage_syntax: str,
    project_config: str
) -> None:
    """Verifies CLI behavior when processing unparseable manifest files.

    Ensures that encountering a completely corrupted file results in an
    emergency error trace and an exit code 1 status response.

    Args:
        tmp_path: A built-in pytest fixture providing a temporary directory path.
        manifest_corrupted_garbage_syntax: Test fixture containing invalid YAML syntax text.
        project_config: A test fixture providing a valid raw project YAML string.
    """
    # Initialize an isolated Click command test runner
    runner = CliRunner()

    # Create safe sandbox folders
    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir()
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    sources_dir = tmp_path / "dpkg-sources"

    # Write out a corrupted manifest file
    bad_manifest_file = manifests_dir / "corrupted.yaml"
    bad_manifest_file.write_text(manifest_corrupted_garbage_syntax, encoding="utf-8")

    # Write out a project file
    project_file = tmp_path / "project.yaml"
    project_file.write_text(project_config, encoding="utf-8")

    # Run the build command
    result = runner.invoke(main_cli, [
        "build",
        "--project-config", str(project_file),
        "--manifests-dir", str(manifests_dir),
        "--templates-dir", str(templates_dir),
        "--sources-dir", str(sources_dir)
    ])

    # ASSERTIONS: It must flag a fatal failure and exit with 1
    assert result.exit_code == 1
    assert "EMERGENCY: Execution Error processing corrupted.yaml" in result.output

def test_unit_cli_build_subcommand_gracefully_handles_corrupted_project_config(
    tmp_path: Path,
    project_config_multiple_missing: str,
    manifest_v1: str
) -> None:
    """Verifies CLI behavior when processing an unparseable global project config.

    Ensures that encountering a completely corrupted project configuration file
    results in a fatal emergency error trace and an exit status code 1.

    Args:
        tmp_path: A built-in pytest fixture providing a temporary directory path.
        project_config_multiple_missing: Test fixture containing invalid syntax text.
        manifest_v1: A test fixture providing a valid raw manifest YAML string.
    """
    # Initialize an isolated Click command test runner
    runner = CliRunner()

    # Create safe sandbox folders
    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir()
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    sources_dir = tmp_path / "dpkg-sources"

    # Write out a manifest file
    manifest_file = manifests_dir / "test-repo.yaml"
    manifest_file.write_text(manifest_v1, encoding="utf-8")

    # Write out a bad project file
    bad_project_file = tmp_path / "project.yaml"
    bad_project_file.write_text(project_config_multiple_missing, encoding="utf-8")

    # Run the build command
    result = runner.invoke(main_cli, [
        "build",
        "--project-config", str(bad_project_file),
        "--manifests-dir", str(manifests_dir),
        "--templates-dir", str(templates_dir),
        "--sources-dir", str(sources_dir)
    ])

    # ASSERTIONS: It must flag a fatal failure and exit with 1
    assert result.exit_code == 1
    assert "EMERGENCY: Fatal validation failure inside global project config" in result.output
