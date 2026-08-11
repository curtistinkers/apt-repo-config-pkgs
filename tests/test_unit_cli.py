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
    """
    # 1. SETUP: Create input paths and write un-parseable file text directly to disk
    manifests_dir = tmp_path / "manifests"
    sources_dir = tmp_path / "sources"
    manifests_dir.mkdir(parents=True)

    bad_file = manifests_dir / "corrupted.yaml"
    bad_file.write_text(manifest_corrupted_garbage_syntax, encoding="utf-8")

    from package_generator.cli import main_cli
    runner = CliRunner()

    # 2. EXECUTION: Fire the build subcommand across our corrupted sandbox path
    result = runner.invoke(main_cli, [
        "build",
        "--manifests-dir", str(manifests_dir),
        "--sources-dir", str(sources_dir)
    ])

    # 3. SPECIFICATION ASSERTIONS: It must report an emergency and exit code 1
    assert result.exit_code == 1
    assert "EMERGENCY: Execution Error processing corrupted.yaml" in result.output
