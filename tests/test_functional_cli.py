"""
tests/test_functional_cli.py
============================
End-to-end functional integration specifications verifying CLI command
orchestration, argument parsing, and system directory compilation.
"""

import os
from pathlib import Path
from click.testing import CliRunner
import pytest

def test_cli_build_subcommand_orchestrates_directories_end_to_end(
    tmp_path: Path,
    manifest_v1: str
) -> None:
    """
    Verifies that executing the 'build' subcommand via the CLI runner:
    1. Successfully parses directory arguments and the --debug flag.
    2. Validates and compiles raw manifest data models.
    3. Physically orchestrates the target package directory tree on disk.
    """
    # 1. SETUP: Establish physical input and output directory structures in our sandbox
    manifests_dir = tmp_path / "manifests"
    sources_dir = tmp_path / "sources"

    manifests_dir.mkdir(parents=True)

    # Write our perfect manifest fixture directly onto the disk platter
    sample_manifest_file = manifests_dir / "test-repo.yaml"
    sample_manifest_file.write_text(manifest_v1, encoding="utf-8")

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
    assert result.exit_code == 0, f"CLI pipeline crashed with console logs: {result.output}"
    assert "DEBUG: Initializing execution environment" in result.output
    assert "Successfully processed package manifest: test-repo" in result.output

    # 4. FILESYSTEM ARCHITECTURE ASSERTIONS: Prove the objects collaborated to write disk paths
    expected_debian_dir = sources_dir / "test-repo" / "debian"
    assert expected_debian_dir.exists(), "The end-to-end CLI run failed to create the target directories."
    assert expected_debian_dir.is_dir()
