# tests/test_functional_cli.py
"""Functional command-line interface tests.

End-to-end functional integration specifications verifying CLI command
orchestration, argument parsing, and system directory compilation.
"""

from pathlib import Path

import yaml
from click.testing import CliRunner

from package_generator.cli import main_cli


def test_cli_build_subcommand_creates_directories(
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
    # Initialize an isolated Click command test runner
    runner = CliRunner()

    # Create safe sandbox folders
    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir()
    sources_dir = tmp_path / "dpkg-sources"

    # Create a project manifest file
    project_file = tmp_path / "project.yaml"
    project_file.write_text(project_config, encoding="utf-8")

    # Write out a repository manifest file
    manifest_file = manifests_dir / "test-repo.yaml"
    manifest_file.write_text(manifest_v1, encoding="utf-8")

    # Get the real templates directory
    templates_dir = Path(__file__).parents[1] / "templates"

    # Run the build command
    result = runner.invoke(main_cli, [
        "build",
        "--project-config", str(project_file),
        "--manifests-dir", str(manifests_dir),
        "--templates-dir", str(templates_dir),
        "--sources-dir", str(sources_dir),
        "--debug"
    ])

    # 3. CONSOLE OUTPUT ASSERTIONS
        # 3. CONSOLE OUTPUT ASSERTIONS
    assert result.exit_code == 0, f"CLI pipeline crashed with logs: {result.output}"
    assert "DEBUG: Initializing execution environment" in result.output
    # FIX: Swapped out 'orchestrated' for 'finalized' to match our simple production log text
    assert "INFO: Successfully finalized debian/" in result.output


    # 4. FILESYSTEM ARCHITECTURE ASSERTIONS
    expected_debian_dir = sources_dir / "test-repo" / "debian"
    assert expected_debian_dir.exists(), "The build run failed to create directories."
    assert expected_debian_dir.is_dir(), "The target destination path is not a valid directory."

def test_cli_builds_control_file(
    tmp_path: Path,
    manifest_v1: str,
    project_config: str,
) -> None:
    """Verifies that the build command compiles a valid control file.

    Args:
        tmp_path: A built-in pytest fixture providing a temporary directory path.
        manifest_v1: A test fixture providing a static keyring manifest.
        project_config: A test fixture providing a valid raw project YAML string.
    """
    # Initialize an isolated Click command test runner
    runner = CliRunner()

    # Create safe sandbox folders
    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir()
    sources_dir = tmp_path / "dpkg-sources"

    # Create a project manifest file
    project_file = tmp_path / "project.yaml"
    project_file.write_text(project_config, encoding="utf-8")

    # Write out a repository manifest file
    manifest_file = manifests_dir / "test-repo.yaml"
    manifest_file.write_text(manifest_v1, encoding="utf-8")

    # Get the real templates directory
    templates_dir = Path(__file__).parents[1] / "templates"

    # Run the build command
    result = runner.invoke(main_cli, [
        "build",
        "--project-config", str(project_file),
        "--manifests-dir", str(manifests_dir),
        "--templates-dir", str(templates_dir),
        "--sources-dir", str(sources_dir)
    ])

    assert result.exit_code == 0, f"Control build run failed: {result.output}"

    expected_debian_dir = sources_dir / "test-repo" / "debian"
    control_file = expected_debian_dir / "control"

    # Verify the physical file asset exists on the disk platter
    assert control_file.exists(), "The builder failed to generate the debian/copyright file."

    # Capture your actual generated output text block
    control_content = control_file.read_text(encoding="utf-8")

    # 2. Define the exact, literal multiline expectation layout
    expected_text1 = (
        "Source: test-repo-repo-config\n"
        "Section: utils\n"
        "Priority: optional\n"
        "Maintainer: Alice <alice@example.com>\n"
        "Build-Depends: debhelper-compat (= 13)\n"
        "Standards-Version: 4.6.2\n"
        "\n"
        "Package: test-repo-repo-config\n"
        "Architecture: all\n"
        "Depends: ${misc:Depends}, wget, gnupg\n"
        "Description: Test repository package layout configuration.\n"
        " This package automatically manages the APT repository configuration and\n"
        " secure cryptographic keyrings for test-repo."
    )

    # 3. Assert the exact match natively
    assert control_content == expected_text1


def test_cli_builds_copyright_file(
    tmp_path: Path,
    manifest_v1: str,
    project_config: str,
) -> None:
    """Verifies that the build command compiles a valid copyright file.

    Args:
        tmp_path: A built-in pytest fixture providing a temporary directory path.
        manifest_v1: A test fixture providing a static keyring manifest.
        project_config: A test fixture providing a valid raw project YAML string.
    """
    # Initialize an isolated Click command test runner
    runner = CliRunner()

    # Create safe sandbox folders
    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir()
    sources_dir = tmp_path / "dpkg-sources"

    # Create a project manifest file
    project_file = tmp_path / "project.yaml"
    project_file.write_text(project_config, encoding="utf-8")

    # Write out a repository manifest file
    manifest_file = manifests_dir / "test-repo.yaml"
    manifest_file.write_text(manifest_v1, encoding="utf-8")

    # Get the real templates directory
    templates_dir = Path(__file__).parents[1] / "templates"

    # Run the build command
    result = runner.invoke(main_cli, [
        "build",
        "--project-config", str(project_file),
        "--manifests-dir", str(manifests_dir),
        "--templates-dir", str(templates_dir),
        "--sources-dir", str(sources_dir)
    ])

    assert result.exit_code == 0, f"Control build run failed: {result.output}"

    expected_debian_dir = sources_dir / "test-repo" / "debian"
    copyright_file = expected_debian_dir / "copyright"

    # Verify the physical file asset exists on the disk platter
    assert copyright_file.exists(), "The builder failed to generate the debian/copyright file."

    # Capture your actual generated output text block
    copyright_content = copyright_file.read_text(encoding="utf-8")

    # Define the exact, literal multiline expectation layout
    expected_text = (
        "Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/\n"
        "Source: https://git.example.com/alice/deb-repo-config-packages/dpkg-sources/test-repo\n"
        "Upstream-Name: test-repo-repo-config\n"
        "Upstream-Contact: Alice <alice@example.com>\n"
        "\n"
        "Files: *\n"
        "Copyright: 2024 Alice <alice@example.com>"
    )

    # Check that your short snippet exists inside the large generated text block
    assert expected_text in copyright_content


def test_cli_builds_rules_file(
    tmp_path: Path,
    manifest_v1: str,
    project_config: str,
) -> None:
    """Verifies that the build command compiles a valid rules file.

    Args:
        tmp_path: A built-in pytest fixture providing a temporary directory path.
        manifest_v1: A test fixture providing a static keyring manifest.
        project_config: A test fixture providing a valid raw project YAML string.
    """
    # Initialize an isolated Click command test runner
    runner = CliRunner()

    # Create safe sandbox folders
    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir()
    sources_dir = tmp_path / "dpkg-sources"

    # Create a project manifest file
    project_file = tmp_path / "project.yaml"
    project_file.write_text(project_config, encoding="utf-8")

    # Write out a repository manifest file
    manifest_file = manifests_dir / "test-repo.yaml"
    manifest_file.write_text(manifest_v1, encoding="utf-8")

    # Get the real templates directory
    templates_dir = Path(__file__).parents[1] / "templates"

    # Run the build command
    result = runner.invoke(main_cli, [
        "build",
        "--project-config", str(project_file),
        "--manifests-dir", str(manifests_dir),
        "--templates-dir", str(templates_dir),
        "--sources-dir", str(sources_dir)
    ])

    assert result.exit_code == 0, f"Control build run failed: {result.output}"

    expected_debian_dir = sources_dir / "test-repo" / "debian"
    rules_file = expected_debian_dir / "rules"

    # Verify the physical file asset exists on the disk platter
    assert rules_file.exists(), "The builder failed to generate the debian/rules file."

    # Capture your actual generated output text block
    rules_content = rules_file.read_text(encoding="utf-8")

    # Define the exact, literal multiline expectation layout
    expected_text = (
        "#!/usr/bin/make -f\n"
        "\n"
        "# The '%' symbol acts as a wildcard catching all build stages.\n"
        "# 'dh $@' passes execution to Debhelper, automating the entire Debian lifecycle.\n"
        "%:\n"
        "\tdh $@"
    )

    # Check that your short snippet exists inside the large generated text block
    assert rules_content == expected_text


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
    # Initialize an isolated Click command test runner
    runner = CliRunner()

    # Create safe sandbox folders
    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir()
    sources_dir = tmp_path / "dpkg-sources"

    # Create a project manifest file
    project_file = tmp_path / "project.yaml"
    project_file.write_text(project_config, encoding="utf-8")

    # Write out a repository manifest file
    manifest_file = manifests_dir / "test-repo.yaml"
    manifest_file.write_text(manifest_v1, encoding="utf-8")

    # Get the real templates directory
    templates_dir = Path(__file__).parents[1] / "templates"

    # Run the build command
    result = runner.invoke(main_cli, [
        "build",
        "--project-config", str(project_file),
        "--manifests-dir", str(manifests_dir),
        "--templates-dir", str(templates_dir),
        "--sources-dir", str(sources_dir)
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
    # Initialize an isolated Click command test runner
    runner = CliRunner()

    # Create safe sandbox folders
    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir()
    sources_dir = tmp_path / "dpkg-sources"

    # Create a project manifest file
    project_file = tmp_path / "project.yaml"
    project_file.write_text(project_config, encoding="utf-8")

    # Write out a repository manifest file
    manifest_file = manifests_dir / "test-repo.yaml"
    manifest_file.write_text(manifest_v3, encoding="utf-8")

    # Get the real templates directory
    templates_dir = Path(__file__).parents[1] / "templates"

    # Run the build command
    result = runner.invoke(main_cli, [
        "build",
        "--project-config", str(project_file),
        "--manifests-dir", str(manifests_dir),
        "--templates-dir", str(templates_dir),
        "--sources-dir", str(sources_dir)
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

def test_cli_builds_os_normalization_rules(
    tmp_path: Path,
    manifest_v1: str,
    project_config: str,
) -> None:
    """Verifies that the build command compiles valid OS normalization case rules.

    Args:
        tmp_path: A built-in pytest fixture providing a temporary directory path.
        manifest_v1: A test fixture providing a standard repository manifest.
        project_config: A test fixture providing a valid raw project YAML string.
    """
    manifests_dir = tmp_path / "manifests_normalization"
    sources_dir = tmp_path / "sources_normalization"
    manifests_dir.mkdir(parents=True)

    project_file = tmp_path / "project.yaml"
    project_file.write_text(project_config, encoding="utf-8")

    manifest_file = manifests_dir / "test-repo.yaml"
    manifest_file.write_text(manifest_v1, encoding="utf-8")

    runner = CliRunner()
    real_templates_root = Path(__file__).parents[1] / "templates"

    result = runner.invoke(main_cli, [
        "build",
        "--project-config", str(project_file),
        "--manifests-dir", str(manifests_dir),
        "--templates-dir", str(real_templates_root),
        "--sources-dir", str(sources_dir),
        "--debug"
    ])

    assert result.exit_code == 0, f"Normalization build run failed: {result.output}"

    expected_debian_dir = sources_dir / "test-repo" / "debian"
    postinst_file = expected_debian_dir / "postinst"

    assert postinst_file.exists()

    postinst_content = postinst_file.read_text(encoding="utf-8")

    # Assert that the exact case blocks we expect from manifest_v1 are present
    assert "pop|linuxmint)" in postinst_content
    assert 'TARGET_DIST="ubuntu"' in postinst_content
    assert 'TARGET_CODENAME="${UBUNTU_CODENAME}"' in postinst_content

    assert "raspbian)" in postinst_content
    assert 'TARGET_DIST="debian"' in postinst_content
    assert 'TARGET_CODENAME="${VERSION_CODENAME}"' in postinst_content


def test_cli_prompts_and_skips_on_no_response(
    tmp_path: Path,
    manifest_v2: str,
    project_config: str,
    changelog_v2: str,
) -> None:
    """Verifies that selecting 'No' at the interactive prompt skips the package."""
    runner = CliRunner()
    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir()
    sources_dir = tmp_path / "dpkg-sources"

    # Write out a global project configuration file
    project_file = tmp_path / "project.yaml"
    project_file.write_text(project_config, encoding="utf-8")

    # Seed the history tracking file so that version 1.0.1 is already written on disk
    pkg_debian_dir = sources_dir / "test-repo" / "debian"
    pkg_debian_dir.mkdir(parents=True)
    (pkg_debian_dir / "changelog").write_text(changelog_v2, encoding="utf-8")

    # Create an identical manifest version 1.0.1 file block, but modify its description
    raw_manifest_data = yaml.safe_load(manifest_v2)
    raw_manifest_data["description"] = "A brand new modified description text rule."

    modified_manifest_file = manifests_dir / "test-repo.yaml"
    modified_manifest_file.write_text(yaml.safe_dump(raw_manifest_data), encoding="utf-8")

    real_templates_root = Path(__file__).parents[1] / "templates"

    # EXECUTION: Trigger the build subcommand pass while feeding 'n' (No) into stdin
    result = runner.invoke(
        main_cli,
        [
            "build",
            "--project-config", str(project_file),
            "--manifests-dir", str(manifests_dir),
            "--templates-dir", str(real_templates_root),
            "--sources-dir", str(sources_dir),
            "--debug"
        ],
        input="n\n"  # Simulate pressing No
    )

    # ASSERTIONS: The file must be skipped gracefully with a dedicated alert log message
    assert result.exit_code == 0
    assert "Manifest modified without version bump" in result.output
    assert "ALERT: Skipping package file test-repo.yaml" in result.output


def test_cli_auto_bumps_and_rewrites_manifest_on_yes_response(
    tmp_path: Path,
    manifest_v2: str,
    project_config: str,
    changelog_v2: str,
) -> None:
    """Verifies that selecting 'Yes' at the prompt auto-bumps and rewrites the yaml."""
    runner = CliRunner()
    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir()
    sources_dir = tmp_path / "dpkg-sources"

    project_file = tmp_path / "project.yaml"
    project_file.write_text(project_config, encoding="utf-8")

    pkg_debian_dir = sources_dir / "test-repo" / "debian"
    pkg_debian_dir.mkdir(parents=True)
    (pkg_debian_dir / "changelog").write_text(changelog_v2, encoding="utf-8")

    raw_manifest_data = yaml.safe_load(manifest_v2)
    raw_manifest_data["description"] = "A brand new modified description text rule."

    modified_manifest_file = manifests_dir / "test-repo.yaml"
    modified_manifest_file.write_text(yaml.safe_dump(raw_manifest_data), encoding="utf-8")

    real_templates_root = Path(__file__).parents[1] / "templates"

    # EXECUTION: Trigger the build subcommand pass while feeding 'y' (Yes) into stdin
    result = runner.invoke(
        main_cli,
        [
            "build",
            "--project-config", str(project_file),
            "--manifests-dir", str(manifests_dir),
            "--templates-dir", str(real_templates_root),
            "--sources-dir", str(sources_dir),
            "--debug"
        ],
        input="y\n"  # Simulate pressing Yes
    )

    assert result.exit_code == 0
    assert "Auto-bumping manifest file test-repo.yaml forward to v1.0.2" in result.output

    # VERIFY DISK PERSISTENCE: Confirm the physical manifest file on disk was rewritten
    updated_yaml_content = modified_manifest_file.read_text(encoding="utf-8")
    assert "version: 1.0.2" in updated_yaml_content


def test_cli_auto_bumps_natively_via_flag_option(
    tmp_path: Path,
    manifest_v2: str,
    project_config: str,
    changelog_v2: str,
) -> None:
    """Verifies that the --bump-version flag option auto-accepts without prompts."""
    runner = CliRunner()
    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir()
    sources_dir = tmp_path / "dpkg-sources"

    project_file = tmp_path / "project.yaml"
    project_file.write_text(project_config, encoding="utf-8")

    pkg_debian_dir = sources_dir / "test-repo" / "debian"
    pkg_debian_dir.mkdir(parents=True)
    (pkg_debian_dir / "changelog").write_text(changelog_v2, encoding="utf-8")

    raw_manifest_data = yaml.safe_load(manifest_v2)
    raw_manifest_data["description"] = "A brand new modified description text rule."

    modified_manifest_file = manifests_dir / "test-repo.yaml"
    modified_manifest_file.write_text(yaml.safe_dump(raw_manifest_data), encoding="utf-8")

    real_templates_root = Path(__file__).parents[1] / "templates"

    # EXECUTION: Trigger build with the explicit --bump-version flag option parameter active
    result = runner.invoke(
        main_cli,
        [
            "build",
            "--project-config", str(project_file),
            "--manifests-dir", str(manifests_dir),
            "--templates-dir", str(real_templates_root),
            "--sources-dir", str(sources_dir),
            "--bump-version",  # Bypass prompts natively
            "--debug"
        ]
    )

    assert result.exit_code == 0
    assert "Auto-bumping manifest file test-repo.yaml forward to v1.0.2" in result.output

    updated_yaml_content = modified_manifest_file.read_text(encoding="utf-8")
    assert "version: 1.0.2" in updated_yaml_content
