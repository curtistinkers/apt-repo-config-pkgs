# tests/test_unit_cli.py
"""CLI unit tests.

Discrete unit specifications validating the argument parsing boundaries,
command routing, and option validations managed by the CLI interface group.
"""

from pathlib import Path
from unittest.mock import patch

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


def test_cli_build_re_raises_genuine_alternative_exceptions(
    tmp_path: Path,
    project_config: str,
    manifest_v1: str,
    mock_changelog_template: str,
) -> None:
    """Verifies that the build command bubbles up unexpected runtime exceptions.

    Args:
        tmp_path: A built-in pytest fixture providing a temporary directory path.
        project_config: A test fixture providing raw project YAML text.
        manifest_v1: A test fixture providing a valid raw manifest YAML string.
        mock_changelog_template: A test fixture providing the mock changelog template layout.
    """
    runner = CliRunner()

    # 1. Setup isolated directories matching the default expectations
    config_file = tmp_path / "config.yaml"
    config_file.write_text(project_config, encoding="utf-8")

    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir()
    (manifests_dir / "omv.yaml").write_text(manifest_v1, encoding="utf-8")

    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    (templates_dir / "changelog.jinja2").write_text(mock_changelog_template, encoding="utf-8")

    sources_dir = tmp_path / "dpkg-sources"

    # 2. Force the builder orchestrator to throw an unexpected RuntimeError exception
    with patch("package_generator.cli.DebianPackageBuilder.create_package_tree") as mock_tree:
        mock_tree.side_effect = RuntimeError("Genuine unexpected layout execution failure.")

        result = runner.invoke(main_cli, [
            "build",
            "--project-config", str(config_file),
            "--manifests-dir", str(manifests_dir),
            "--templates-dir", str(templates_dir),
            "--sources-dir", str(sources_dir),
        ])

    assert result.exit_code == 1
    assert "Genuine unexpected layout execution failure." in result.output


def test_cli_clean_logs_error_when_directory_removal_fails(
    tmp_path: Path,
) -> None:
    """Verifies that the clean command handles and logs directory purge exceptions.

    Args:
        tmp_path: A built-in pytest fixture providing a temporary directory path.
    """
    runner = CliRunner()
    sources_dir = tmp_path / "dpkg-sources"
    sources_dir.mkdir(parents=True, exist_ok=True)

    # Mock shutil.rmtree to simulate a permission error or file lock crash on Windows
    with patch("shutil.rmtree") as mock_rmtree:
        mock_rmtree.side_effect = OSError("Access denied or storage platter file lock.")

        result = runner.invoke(main_cli, [
            "clean",
            "--sources-dir", str(sources_dir),
        ])

    assert result.exit_code == 0
    assert "ERROR: Failed to remove directory tree structure" in result.output

def test_cli_build_re_raises_alternative_value_errors(
    tmp_path: Path,
    project_config: str,
    manifest_v1: str,
) -> None:
    """Verifies that the build command re-raises non-bump related ValueErrors."""
    runner = CliRunner()

    config_file = tmp_path / "config.yaml"
    config_file.write_text(project_config, encoding="utf-8")

    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir()
    (manifests_dir / "omv.yaml").write_text(manifest_v1, encoding="utf-8")

    # We can use flat paths here since we aren't testing changelog.py in this unit block
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    (templates_dir / "debian").mkdir()
    sources_dir = tmp_path / "dpkg-sources"

        # Force a ValueError that does NOT contain the version bump string parameter
    with patch("package_generator.cli.DebianPackageBuilder.create_package_tree") as mock_tree:
        mock_tree.side_effect = ValueError(
            "Fatal architecture violation: rogue template collision."
            )

        result = runner.invoke(main_cli, [
            "build",
            "--project-config", str(config_file),
            "--manifests-dir", str(manifests_dir),
            "--templates-dir", str(templates_dir),
            "--sources-dir", str(sources_dir),
        ])

    # FIX: Verify that the outer loop handles the re-raised ValueError, logs it, and exits cleanly
    assert result.exit_code == 1
    assert "Fatal architecture violation: rogue template collision." in result.output


def test_cli_build_terminates_on_invalid_project_yaml_file(
    tmp_path: Path,
) -> None:
    """Verifies that build terminates with code 1 if project config is corrupted."""
    runner = CliRunner()

    # Write structural garbage to the file to force yaml parsing errors
    corrupted_config = tmp_path / "config.yaml"
    corrupted_config.write_text("::: global_keys: [missing_indentation_garbage", encoding="utf-8")

    result = runner.invoke(main_cli, [
        "build",
        "--project-config", str(corrupted_config),
        "--manifests-dir", str(tmp_path)
    ])

    assert result.exit_code == 1
    assert "Fatal validation failure inside global project config" in result.output


def test_cli_build_skips_manifest_when_user_rejects_auto_bump_prompt(
    tmp_path: Path,
    project_config: str,
    manifest_v1: str,
) -> None:
    """Verifies skipping a manifest file when user selects 'No' to auto-bump."""
    runner = CliRunner()

    config_file = tmp_path / "config.yaml"
    config_file.write_text(project_config, encoding="utf-8")

    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir()
    (manifests_dir / "omv.yaml").write_text(manifest_v1, encoding="utf-8")

    # Force an un-bumped version collision by mocking the builder tree pass
    with patch("package_generator.cli.DebianPackageBuilder.create_package_tree") as mock_tree:
        mock_tree.side_effect = ValueError(
            "Manifest modified without version bump for 'test-repo'."
            )

        # Simulate typing 'n' (No) directly into the interactive terminal click prompt channel
        result = runner.invoke(main_cli, [
            "build",
            "--project-config", str(config_file),
            "--manifests-dir", str(manifests_dir),
            "--sources-dir", str(tmp_path / "dpkg-sources")
        ], input="n\n")

    assert result.exit_code == 0
    assert "Skipping package file omv.yaml due to state version mismatch" in result.output

def test_cli_build_successfully_processes_valid_manifests(
    tmp_path: Path,
    project_config: str,
    manifest_v1: str,
) -> None:
    """Verifies that the build command completes successfully on clean runs.

    Args:
        tmp_path: A built-in pytest fixture providing a temporary directory path.
        project_config: A test fixture providing raw project YAML text.
        manifest_v1: A test fixture providing a valid raw manifest YAML string.
    """
    runner = CliRunner()

    config_file = tmp_path / "config.yaml"
    config_file.write_text(project_config, encoding="utf-8")

    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir()
    (manifests_dir / "omv.yaml").write_text(manifest_v1, encoding="utf-8")

    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    (templates_dir / "debian").mkdir()
    sources_dir = tmp_path / "dpkg-sources"

    # Mock create_package_tree to do absolutely nothing (simulate a perfect clean pass)
    with patch("package_generator.cli.DebianPackageBuilder.create_package_tree"):
        result = runner.invoke(main_cli, [
            "build",
            "--project-config", str(config_file),
            "--manifests-dir", str(manifests_dir),
            "--templates-dir", str(templates_dir),
            "--sources-dir", str(sources_dir),
        ])

    # This pass forces the loop to hit processed_count += 1 and compiled_successfully = True
    assert result.exit_code == 0
    assert "Total built: 1" in result.output


def test_cli_build_performs_auto_bump_when_user_accepts_prompt(
    tmp_path: Path,
    project_config: str,
    manifest_v1: str,
    mock_manifest_template: str,
) -> None:
    """Verifies rewriting a manifest file on disk when a user inputs 'Yes' to an auto-bump.

    Args:
        tmp_path: A built-in pytest fixture providing a temporary directory path.
        project_config: A test fixture providing raw project YAML text.
        manifest_v1: A test fixture providing a valid raw manifest YAML string.
        mock_manifest_template: Blueprint layout matching manifest_v1 format.
    """
    runner = CliRunner()

    config_file = tmp_path / "config.yaml"
    config_file.write_text(project_config, encoding="utf-8")

    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir()
    manifest_file = manifests_dir / "test-repo.yaml"
    manifest_file.write_text(manifest_v1, encoding="utf-8")

    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    (templates_dir / "debian").mkdir()
    sources_dir = tmp_path / "dpkg-sources"

    # Seed the mandatory manifest template layout to verify the clean rewrite path
    (templates_dir / "manifest.jinja2").write_text(mock_manifest_template, encoding="utf-8")

    # Side effect sequence: throw a version collision error on pass 1, then pass natively on pass 2
    with patch("package_generator.cli.DebianPackageBuilder.create_package_tree") as mock_tree:
        mock_tree.side_effect = [
            ValueError("Manifest modified without version bump for 'test-repo'."),
            None
        ]

        # Simulate typing 'y' (Yes) directly into the interactive Click terminal prompt
        result = runner.invoke(main_cli, [
            "build",
            "--project-config", str(config_file),
            "--manifests-dir", str(manifests_dir),
            "--templates-dir", str(templates_dir),
            "--sources-dir", str(sources_dir),
        ], input="y\n")

    # Verify that the true-evaluation branch executed the rewrite, reloaded, and finalized the build
    assert result.exit_code == 0
    assert "Auto-bumping manifest file test-repo.yaml forward to v1.0.1" in result.output
    assert "Total built: 1" in result.output

    # Confirm that the file stream on the disk platter was physically modified to v1.0.1
    updated_manifest_text = manifest_file.read_text(encoding="utf-8")
    assert "version: 1.0.1" in updated_manifest_text


def test_cli_build_filters_by_specific_package_name(
    tmp_path: Path,
    project_config: str,
    manifest_v1: str,
) -> None:
    """Verifies that the build command only processes the manifest matching the package flag.

    Args:
        tmp_path: A built-in pytest fixture providing a temporary directory path.
        project_config: A test fixture providing raw project YAML text.
        manifest_v1: A test fixture providing a valid raw manifest YAML string.
    """
    runner = CliRunner()

    config_file = tmp_path / "config.yaml"
    config_file.write_text(project_config, encoding="utf-8")

    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir()

    # Write the target manifest (name is 'test-repo')
    (manifests_dir / "target.yaml").write_text(manifest_v1, encoding="utf-8")

    # Write a second manifest with a different name that should be skipped
    skipped_manifest = manifest_v1.replace("name: test-repo", "name: skipped-repo")
    (manifests_dir / "skipped.yaml").write_text(skipped_manifest, encoding="utf-8")

    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    (templates_dir / "debian").mkdir()
    sources_dir = tmp_path / "dpkg-sources"

    with patch("package_generator.cli.DebianPackageBuilder.create_package_tree") as mock_tree:
        result = runner.invoke(main_cli, [
            "build",
            "--project-config", str(config_file),
            "--manifests-dir", str(manifests_dir),
            "--templates-dir", str(templates_dir),
            "--sources-dir", str(sources_dir),
            "--package", "test-repo"
        ])

    assert result.exit_code == 0
    # Verify that the builder tree creation was called exactly once (only for the targeted package)
    assert mock_tree.call_count == 1
