# tests/test_functional_cli.py
"""Functional command-line interface tests.

End-to-end functional integration specifications verifying CLI command
orchestration, argument parsing, and system directory compilation.
"""

from pathlib import Path

from click.testing import CliRunner


def test_cli_build_subcommand_orchestrates_directories_end_to_end(
    tmp_path: Path,
    manifest_v1: str
) -> None:
    """Verifies that executing the build subcommand creates directories on disk.

    Ensures that argument parsing, schema verification, and directory
    orchestration layers function collectively during a system build pass.

    Args:
        tmp_path (Path): A built-in pytest fixture providing a temporary directory path.
        manifest_v1 (str): A test fixture providing a valid raw manifest YAML string.
    """
    # 1. SETUP: Establish physical input and output directory structures in our sandbox
    manifests_dir = tmp_path / "manifests"
    sources_dir = tmp_path / "sources"
    manifests_dir.mkdir(parents=True)

    # Write our perfect manifest fixture directly onto the disk platter
    manifest_file = manifests_dir / "test-repo.yaml"
    manifest_file.write_text(manifest_v1, encoding="utf-8")

    # 2. EXECUTION: Import our CLI entrypoint and trigger the runner invocation
    from package_generator.cli import main_cli
    runner = CliRunner()

    result = runner.invoke(main_cli, [
        "build",
        "--manifests-dir", str(manifests_dir),
        "--sources-dir", str(sources_dir),
        "--debug"
    ])

    # 3. CONSOLE OUTPUT ASSERTIONS
    assert result.exit_code == 0, f"CLI pipeline crashed with logs: {result.output}"
    assert "DEBUG: Initializing execution environment" in result.output
    # FIX: Synchronize assertion text to look for our new PSR-3 string token formats exactly
    assert "INFO: Successfully orchestrated debian/" in result.output

    # 4. FILESYSTEM ARCHITECTURE ASSERTIONS
    expected_debian_dir = sources_dir / "test-repo" / "debian"
    assert expected_debian_dir.exists(), "The build run failed to create directories."
    assert expected_debian_dir.is_dir(), "The target destination path is not a valid directory."
