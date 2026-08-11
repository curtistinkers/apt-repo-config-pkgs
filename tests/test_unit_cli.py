# tests/test_unit_cli.py
"""CLI unit tests.

Discrete unit specifications validating the argument parsing boundaries,
command routing, and option validations managed by the CLI interface group.
"""

from pathlib import Path

from click.testing import CliRunner


def test_unit_cli_build_subcommand_routes_correctly() -> None:
    """Validate build subcommand.

    Verifies that the CLI 'build' subcommand exists under our main interface
    group and executes with a successful exit status code 0.
    """
    # 1. SETUP: Import the primary CLI group component block
    from package_generator.cli import main_cli

    # Initialize an isolated Click command test runner
    runner = CliRunner()

    # 2. EXECUTION: Run the clean command
    result = runner.invoke(main_cli, ["build"])

    # 3. SPECIFICATION ASSERTION: The command must route successfully
    assert result.exit_code == 0

def test_unit_cli_clean_subcommand_routes_correctly() -> None:
    """Validate clean subcommand.

    Verifies that the CLI 'clean' subcommand exists under our main interface
    group and executes with a successful exit status code 0.
    """
    # 1. SETUP: Import the primary CLI group component block
    from package_generator.cli import main_cli

    # Initialize an isolated Click command test runner
    runner = CliRunner()

    # 2. EXECUTION: Run the clean command
    result = runner.invoke(main_cli, ["clean"])

    # 3. SPECIFICATION ASSERTION: The command must route successfully
    assert result.exit_code == 0

def test_unit_cli_build_subcommand_gracefully_handles_corrupted_syntax_files(
    tmp_path: Path,
    manifest_corrupted_garbage_syntax: str
) -> None:
    """Verifies CLI behavior when processing unparseable manifest files.

    Ensures that encountering a completely corrupted file results in an
    emergency error trace and an exit code 1 status response.

    Args:
        tmp_path: A built-in pytest fixture providing a temporary directory path.
        manifest_corrupted_garbage_syntax: Test fixture containing invalid YAML syntax text.
    """
    # Create input paths and write un-parseable file text directly to disk
    manifests_dir = tmp_path / "manifests"
    sources_dir = tmp_path / "sources"
    manifests_dir.mkdir(parents=True)

    bad_file = manifests_dir / "corrupted.yaml"
    bad_file.write_text(manifest_corrupted_garbage_syntax, encoding="utf-8")

    from package_generator.cli import main_cli
    runner = CliRunner()

    # Locate our real repository template directories root safely
    real_templates_root = Path(__file__).parents[1] / "templates"

    # Fire the build subcommand across our corrupted sandbox path
    result = runner.invoke(main_cli, [
        "build",
        "--manifests-dir", str(manifests_dir),
        "--templates-dir", str(real_templates_root), # NEW: Pass the option explicitly
        "--sources-dir", str(sources_dir)
    ])

    # ASSERTIONS: It must report an emergency and exit code 1
    assert result.exit_code == 1
    assert "EMERGENCY: Execution Error processing corrupted.yaml" in result.output

def test_unit_cli_build_subcommand_gracefully_handles_corrupted_project_config(
    tmp_path: Path,
    manifest_corrupted_garbage_syntax: str,
    manifest_v1: str
) -> None:
    """Verifies CLI behavior when processing an unparseable global project config.

    Ensures that encountering a completely corrupted project configuration file
    results in a fatal emergency error trace and an exit status code 1.

    Args:
        tmp_path: A built-in pytest fixture providing a temporary directory path.
        manifest_corrupted_garbage_syntax: Test fixture containing invalid syntax text.
        manifest_v1: A test fixture providing a valid raw manifest YAML string.
    """
    # 1. SETUP: Create paths and write our corrupted text directly to the project file
    manifests_dir = tmp_path / "manifests"
    sources_dir = tmp_path / "sources"
    manifests_dir.mkdir(parents=True)

    bad_project_file = tmp_path / "project.yaml"
    bad_project_file.write_text(manifest_corrupted_garbage_syntax, encoding="utf-8")

    # Supply a valid package manifest to isolate the error strictly to the project config
    good_manifest_file = manifests_dir / "test-repo.yaml"
    good_manifest_file.write_text(manifest_v1, encoding="utf-8")

    real_templates_root = Path(__file__).parents[1] / "templates"

    from package_generator.cli import main_cli
    runner = CliRunner()

    # 2. EXECUTION: Run the build command targeting our unparseable global project file
    result = runner.invoke(main_cli, [
        "build",
        "--project-config", str(bad_project_file),
        "--manifests-dir", str(manifests_dir),
        "--templates-dir", str(real_templates_root),
        "--sources-dir", str(sources_dir)
    ])

    # 3. SPECIFICATION ASSERTIONS: It must flag a fatal failure and exit with 1
    assert result.exit_code == 1
    assert "EMERGENCY: Fatal validation failure inside global project config" in result.output
