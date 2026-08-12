# tests/test_functional_cli.py
"""Functional command-line interface tests.

End-to-end functional integration specifications verifying CLI command
orchestration, argument parsing, and system directory compilation.
"""

from pathlib import Path

from click.testing import CliRunner

from package_generator.cli import main_cli


def test_cli_build_subcommand_orchestrates_directories_end_to_end(
    tmp_path: Path,
    manifest_v1: str,
    project_config: str,
) -> None:
    """Verifies that executing the build subcommand creates directories on disk.

    Ensures that argument parsing, schema verification, and directory
    orchestration layers function collectively during a system build pass.

    Args:
        tmp_path: A built-in pytest fixture providing a temporary directory path.
        manifest_v1: A test fixture providing a valid raw manifest YAML string.
        project_config: A test fixture providing a valid raw project YAML string.
    """
    # Establish physical input and output directory structures in our sandbox
    manifests_dir = tmp_path / "manifests"
    sources_dir = tmp_path / "sources"
    manifests_dir.mkdir(parents=True)

    # Define and write your global project configuration file to the sandbox
    project_file = tmp_path / "project.yaml"
    project_file.write_text(project_config, encoding="utf-8")

    # Write our perfect manifest fixture directly onto the disk platter
    manifest_file = manifests_dir / "test-repo.yaml"
    manifest_file.write_text(manifest_v1, encoding="utf-8")

    # Import our CLI entrypoint and trigger the runner invocation
    runner = CliRunner()

    # Locate our real repository template directories root safely
    real_templates_root = Path(__file__).parents[1] / "templates"

    result = runner.invoke(main_cli, [
        "build",
        "--project-config", str(project_file),
        "--manifests-dir", str(manifests_dir),
        "--templates-dir", str(real_templates_root),
        "--sources-dir", str(sources_dir),
        "--debug"
    ])

    # 3. CONSOLE OUTPUT ASSERTIONS
    assert result.exit_code == 0, f"CLI pipeline crashed with logs: {result.output}"
    assert "DEBUG: Initializing execution environment" in result.output
    assert "INFO: Successfully orchestrated debian/" in result.output

    # 4. FILESYSTEM ARCHITECTURE ASSERTIONS
    expected_debian_dir = sources_dir / "test-repo" / "debian"
    assert expected_debian_dir.exists(), "The build run failed to create directories."
    assert expected_debian_dir.is_dir(), "The target destination path is not a valid directory."


def test_cli_builds_static_keyring_packages(
    tmp_path: Path,
    manifest_v1: str,
    project_config: str,
) -> None:
    """Verifies that the build command creates static keyring files.

    Args:
        tmp_path: A built-in pytest fixture providing a temporary directory path.
        manifest_v1: A test fixture providing a static keyring manifest.
        project_config: A test fixture providing a valid raw project YAML string.
    """
    # Set up sandbox inputs and outputs
    manifests_dir = tmp_path / "manifests"
    sources_dir = tmp_path / "sources"
    manifests_dir.mkdir(parents=True)

    project_file = tmp_path / "project.yaml"
    project_file.write_text(project_config, encoding="utf-8")

    manifest_file = manifests_dir / "test-repo.yaml"
    manifest_file.write_text(manifest_v1, encoding="utf-8")

    runner = CliRunner()
    real_templates_root = Path(__file__).parents[1] / "templates"

    # Run the build command
    result = runner.invoke(main_cli, [
        "build",
        "--project-config", str(project_file),
        "--manifests-dir", str(manifests_dir),
        "--templates-dir", str(real_templates_root),
        "--sources-dir", str(sources_dir),
        "--debug"
    ])

    assert result.exit_code == 0, f"Static build failed: {result.output}"

    expected_debian_dir = sources_dir / "test-repo" / "debian"
    assert expected_debian_dir.exists()

    # Assert against the generated postint file content text
    postinst_file = expected_debian_dir / "postinst"
    assert postinst_file.exists()

    # Static builds should not mention fetch_dynamic_keyring
    postinst_content = postinst_file.read_text(encoding="utf-8")
    assert "fetch_dynamic_keyring" not in postinst_content

    # Assert against the generated postrm file content text
    postrm_file = expected_debian_dir / "postrm"
    assert postrm_file.exists()

    # Static builds should not mention purge_dynamic_keyring
    postrm_content = postrm_file.read_text(encoding="utf-8")
    assert "purge_dynamic_keyring" not in postrm_content

    # Assert against the generated install file content text
    install_file = expected_debian_dir / "install"
    assert install_file.exists()

    # Static builds should mention the static key paths inside the install map
    install_content = install_file.read_text(encoding="utf-8")
    assert "/usr/share/keyrings/test-repo-archive-keyring.gpg" in install_content


def test_cli_builds_dynamic_keyring_packages(
    tmp_path: Path,
    manifest_v3: str,
    project_config: str,
) -> None:
    """Verifies that the build command creates dynamic keyring files.

    Args:
        tmp_path: A built-in pytest fixture providing a temporary directory path.
        manifest_v3: A test fixture providing a dynamic keyring manifest.
        project_config: A test fixture providing a valid raw project YAML string.
    """
    # Set up sandbox inputs and outputs
    manifests_dir = tmp_path / "manifests_dynamic"
    sources_dir = tmp_path / "sources_dynamic"
    manifests_dir.mkdir(parents=True)

    project_file = tmp_path / "project.yaml"
    project_file.write_text(project_config, encoding="utf-8")

    manifest_file = manifests_dir / "test-repo-dynamic.yaml"
    manifest_file.write_text(manifest_v3, encoding="utf-8")

    runner = CliRunner()
    real_templates_root = Path(__file__).parents[1] / "templates"

    # Run the build command
    result = runner.invoke(main_cli, [
        "build",
        "--project-config", str(project_file),
        "--manifests-dir", str(manifests_dir),
        "--templates-dir", str(real_templates_root),
        "--sources-dir", str(sources_dir),
        "--debug"
    ])

    assert result.exit_code == 0, f"Dynamic build failed: {result.output}"

    expected_debian_dir = sources_dir / "test-repo" / "debian"
    assert expected_debian_dir.exists()

    # Assert against the generated postint file content text
    postinst_file = expected_debian_dir / "postinst"
    assert postinst_file.exists()

    # Dynamic builds should mention fetch_dynamic_keyring
    postinst_content = postinst_file.read_text(encoding="utf-8")
    assert "fetch_dynamic_keyring" in postinst_content

    # Ensure our wget default command layout exists instead of curl
    assert "wget" in postinst_content

    # Assert against the generated postrm file content text
    postrm_file = expected_debian_dir / "postrm"
    assert postrm_file.exists()

    # Dynamic builds should mention purge_dynamic_keyring
    postrm_content = postrm_file.read_text(encoding="utf-8")
    assert "purge_dynamic_keyring" in postrm_content

    # Assert against the generated install file content text
    install_file = expected_debian_dir / "install"
    assert install_file.exists()

    # Dynamic builds should not mention the static key paths inside the install map
    install_content = install_file.read_text(encoding="utf-8")
    assert "test-repo-archive-keyring.gpg" not in install_content
