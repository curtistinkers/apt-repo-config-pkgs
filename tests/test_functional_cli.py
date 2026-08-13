# tests/test_functional_cli.py
"""Functional command-line interface tests.

End-to-end functional integration specifications verifying CLI command
orchestration, argument parsing, and system directory compilation.
"""

from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from click.testing import CliRunner

from package_generator.cli import main_cli


@pytest.fixture
def cli_sandbox(
    tmp_path: Path,
    project_config: str
) -> Generator[tuple[CliRunner, Path, Path, Path, Path], None, None]:
    """Sets up a complete physical sandbox workspace with global network mocks.

    Provides a clean, uniform environment for functional CLI build tests, isolating
    the downloader and gpg layers while preserving template execution maps.
    """
    runner = CliRunner()

    # Establish sandbox filesystem paths
    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir(parents=True, exist_ok=True)
    sources_dir = tmp_path / "dpkg-sources"
    sources_dir.mkdir(parents=True, exist_ok=True)

    # Persist the global project configuration
    project_file = tmp_path / "project.yaml"
    project_file.write_text(project_config, encoding="utf-8")

    # Locate the real production templates folder track layout
    templates_dir = Path(__file__).parents[1] / "templates"

    # FIX: Update the patcher target to use our new binary method contract name
    mock_download_patcher = patch(
        "package_generator.downloader.Downloader.download_bytes",
        return_value=b"-----BEGIN PGP PUBLIC KEY BLOCK-----\nMOCK_ASCII_KEY"
    )
    mock_dearmor_patcher = patch(
        "package_generator.gpg.GpgEngine.dearmor",
        return_value=b"MOCK_BINARY_BYTES"
    )

    mock_download_patcher.start()
    mock_dearmor_patcher.start()

    yield runner, project_file, manifests_dir, templates_dir, sources_dir

    # Clean up the global patchers when the test function completes execution
    mock_download_patcher.stop()
    mock_dearmor_patcher.stop()


def test_cli_build_subcommand_creates_directories(
    cli_sandbox: tuple[CliRunner, Path, Path, Path, Path],
    manifest_v1: str,
) -> None:
    """Verifies that executing the build subcommand creates directories on disk.

    Ensures that argument parsing, schema verification, and directory
    orchestration layers function collectively during a system build pass.

    Args:
        cli_sandbox: A shared setup fixture providing an isolated CLI environment.
        manifest_v1: A test fixture providing a valid raw manifest YAML string.
    """
    # 1. SETUP: Extract pre-configured infrastructure components from our sandbox fixture
    runner, project_file, manifests_dir, templates_dir, sources_dir = cli_sandbox

    # Write out the target repository manifest file for this test instance
    manifest_file = manifests_dir / "test-repo.yaml"
    manifest_file.write_text(manifest_v1, encoding="utf-8")

    # 2. EXECUTION: Run the build subcommand pass with debug verbosity active
    result = runner.invoke(main_cli, [
        "build",
        "--project-config", str(project_file),
        "--manifests-dir", str(manifests_dir),
        "--templates-dir", str(templates_dir),
        "--sources-dir", str(sources_dir),
        "--debug"
    ])

    # 3. CONSOLE OUTPUT ASSERTIONS
    assert result.exit_code == 0, f"CLI pipeline crashed with logs: {result.output}"
    assert "DEBUG: Initializing execution environment" in result.output
    assert "INFO: Successfully finalized debian/" in result.output

    # 4. FILESYSTEM ARCHITECTURE ASSERTIONS
    expected_debian_dir = sources_dir / "test-repo" / "debian"
    assert expected_debian_dir.exists(), "The build run failed to create directories."
    assert expected_debian_dir.is_dir(), "The target destination path is not a valid directory."


def test_cli_builds_control_file(
    cli_sandbox: tuple[CliRunner, Path, Path, Path, Path],
    manifest_v1: str,
) -> None:
    """Verifies that the build command compiles a valid control file.

    Args:
        cli_sandbox: A shared setup fixture providing an isolated CLI environment.
        manifest_v1: A test fixture providing a static keyring manifest string.
    """
    # 1. SETUP: Extract pre-configured infrastructure components from our sandbox fixture
    runner, project_file, manifests_dir, templates_dir, sources_dir = cli_sandbox

    # Write out the target repository manifest file for this test instance
    manifest_file = manifests_dir / "test-repo.yaml"
    manifest_file.write_text(manifest_v1, encoding="utf-8")

    # 2. EXECUTION: Run the build subcommand to compile the output tree
    result = runner.invoke(main_cli, [
        "build",
        "--project-config", str(project_file),
        "--manifests-dir", str(manifests_dir),
        "--templates-dir", str(templates_dir),
        "--sources-dir", str(sources_dir)
    ])

    assert result.exit_code == 0, f"Control build run failed: {result.output}"

    # 3. ASSERTIONS: Verify that the control file matches our exact literal layout
    expected_debian_dir = sources_dir / "test-repo" / "debian"
    control_file = expected_debian_dir / "control"

    assert control_file.exists(), "The builder failed to generate the debian/control file."

    control_content = control_file.read_text(encoding="utf-8")

    expected_text = (
        "Source: test-repo-repo-config\n"
        "Section: utils\n"
        "Priority: optional\n"
        "Maintainer: Alice <alice@example.com>\n"
        "Build-Depends: debhelper-compat (= 13)\n"
        "Standards-Version: 4.6.2\n"
        "\n"
        "Package: test-repo-repo-config\n"
        "Architecture: all\n"
        "Depends: ${misc:Depends}\n"
        "Description: Test repository package layout configuration.\n"
        " This package automatically manages the APT repository configuration and\n"
        " secure cryptographic keyrings for test-repo."
    )

    assert control_content == expected_text


def test_cli_builds_copyright_file(
    cli_sandbox: tuple[CliRunner, Path, Path, Path, Path],
    manifest_v1: str,
) -> None:
    """Verifies that the build command compiles a valid copyright file.

    Args:
        cli_sandbox: A shared setup fixture providing an isolated CLI environment.
        manifest_v1: A test fixture providing a static keyring manifest string.
    """
    # 1. SETUP: Extract pre-configured infrastructure components from our sandbox fixture
    runner, project_file, manifests_dir, templates_dir, sources_dir = cli_sandbox

    # Write out the target repository manifest file for this test instance
    manifest_file = manifests_dir / "test-repo.yaml"
    manifest_file.write_text(manifest_v1, encoding="utf-8")

    # 2. EXECUTION: Run the build subcommand to compile the output tree
    result = runner.invoke(main_cli, [
        "build",
        "--project-config", str(project_file),
        "--manifests-dir", str(manifests_dir),
        "--templates-dir", str(templates_dir),
        "--sources-dir", str(sources_dir)
    ])

    assert result.exit_code == 0, f"Control build run failed: {result.output}"

    # 3. ASSERTIONS: Verify that the copyright file contains our structural content
    expected_debian_dir = sources_dir / "test-repo" / "debian"
    copyright_file = expected_debian_dir / "copyright"

    assert copyright_file.exists(), "The builder failed to generate the debian/copyright file."

    copyright_content = copyright_file.read_text(encoding="utf-8")

    expected_text = (
        "Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/\n"
        "Source: https://git.example.com/alice/deb-repo-config-packages/dpkg-sources/test-repo\n"
        "Upstream-Name: test-repo-repo-config\n"
        "Upstream-Contact: Alice <alice@example.com>\n"
        "\n"
        "Files: *\n"
        "Copyright: 2024 Alice <alice@example.com>"
    )

    assert expected_text in copyright_content


def test_cli_builds_rules_file(
    cli_sandbox: tuple[CliRunner, Path, Path, Path, Path],
    manifest_v1: str,
) -> None:
    """Verifies that the build command compiles a valid rules file.

    Args:
        cli_sandbox: A shared setup fixture providing an isolated CLI environment.
        manifest_v1: A test fixture providing a static keyring manifest string.
    """
    # 1. SETUP: Extract pre-configured infrastructure components from our sandbox fixture
    runner, project_file, manifests_dir, templates_dir, sources_dir = cli_sandbox

    # Write out the target repository manifest file for this test instance
    manifest_file = manifests_dir / "test-repo.yaml"
    manifest_file.write_text(manifest_v1, encoding="utf-8")

    # 2. EXECUTION: Run the build subcommand to compile the output tree
    result = runner.invoke(main_cli, [
        "build",
        "--project-config", str(project_file),
        "--manifests-dir", str(manifests_dir),
        "--templates-dir", str(templates_dir),
        "--sources-dir", str(sources_dir)
    ])

    assert result.exit_code == 0, f"Control build run failed: {result.output}"

    # 3. ASSERTIONS: Verify that the rules file matches our exact literal layout
    expected_debian_dir = sources_dir / "test-repo" / "debian"
    rules_file = expected_debian_dir / "rules"

    assert rules_file.exists(), "The builder failed to generate the debian/rules file."

    rules_content = rules_file.read_text(encoding="utf-8")

    expected_text = (
        "#!/usr/bin/make -f\n"
        "\n"
        "# The '%' symbol acts as a wildcard catching all build stages.\n"
        "# 'dh $@' passes execution to Debhelper, automating the entire Debian lifecycle.\n"
        "%:\n"
        "\tdh $@"
    )

    assert rules_content == expected_text


def test_cli_builds_static_keyring_packages(
    cli_sandbox: tuple[CliRunner, Path, Path, Path, Path],
    manifest_v1: str,
) -> None:
    """Verifies that the build command creates static keyring files.

    Args:
        cli_sandbox: A shared setup fixture providing an isolated CLI environment.
        manifest_v1: A test fixture providing a static keyring manifest string.
    """
    # 1. SETUP: Extract pre-configured infrastructure components from our sandbox fixture
    runner, project_file, manifests_dir, templates_dir, sources_dir = cli_sandbox

    # Write out the target repository manifest file for this test instance
    manifest_file = manifests_dir / "test-repo.yaml"
    manifest_file.write_text(manifest_v1, encoding="utf-8")

    # 2. EXECUTION: Run the build subcommand to compile the output tree
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

    # 3. ASSERTIONS: Verify that static files omit dynamic commands but map keyrings
    postinst_file = expected_debian_dir / "postinst"
    assert postinst_file.exists()
    postinst_content = postinst_file.read_text(encoding="utf-8")
    assert "fetch_dynamic_keyring" not in postinst_content

    postrm_file = expected_debian_dir / "postrm"
    assert postrm_file.exists()
    postrm_content = postrm_file.read_text(encoding="utf-8")
    assert "purge_dynamic_keyring" not in postrm_content

    install_file = expected_debian_dir / "install"
    assert install_file.exists()
    install_content = install_file.read_text(encoding="utf-8")
    assert "usr/share/keyrings/test-repo-archive-keyring.gpg" in install_content


def test_cli_builds_dynamic_keyring_packages(
    cli_sandbox: tuple[CliRunner, Path, Path, Path, Path],
    manifest_v3: str,
) -> None:
    """Verifies that the build command creates dynamic keyring files.

    Args:
        cli_sandbox: A shared setup fixture providing an isolated CLI environment.
        manifest_v3: A test fixture providing a dynamic keyring manifest string.
    """
    # 1. SETUP: Extract pre-configured infrastructure components from our sandbox fixture
    runner, project_file, manifests_dir, templates_dir, sources_dir = cli_sandbox

    # Write out the target repository manifest file for this test instance
    manifest_file = manifests_dir / "test-repo.yaml"
    manifest_file.write_text(manifest_v3, encoding="utf-8")

    # 2. EXECUTION: Run the build subcommand to compile the output tree
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

    # 3. ASSERTIONS: Verify that dynamic files include setup scripts but omit static keyrings
    postinst_file = expected_debian_dir / "postinst"
    assert postinst_file.exists()
    postinst_content = postinst_file.read_text(encoding="utf-8")
    assert "fetch_dynamic_keyring" in postinst_content
    assert "wget" in postinst_content

    # Assert against the generated postrm file content text
    postrm_file = expected_debian_dir / "postrm"
    assert postrm_file.exists()
    postrm_content = postrm_file.read_text(encoding="utf-8")
    assert "purge_dynamic_keyring" in postrm_content

    # Assert against the generated install file content text
    install_file = expected_debian_dir / "install"
    assert install_file.exists()
    install_content = install_file.read_text(encoding="utf-8")
    assert "test-repo-archive-keyring.gpg" not in install_content


def test_cli_builds_os_normalization_rules(
    cli_sandbox: tuple[CliRunner, Path, Path, Path, Path],
    manifest_v1: str,
) -> None:
    """Verifies that the build command compiles valid OS normalization case rules.

    Args:
        cli_sandbox: A shared setup fixture providing an isolated CLI environment.
        manifest_v1: A test fixture providing a standard repository manifest string.
    """
    # 1. SETUP: Extract pre-configured infrastructure components from our sandbox fixture
    runner, project_file, manifests_dir, templates_dir, sources_dir = cli_sandbox

    # Write out the target repository manifest file for this test instance
    manifest_file = manifests_dir / "test-repo.yaml"
    manifest_file.write_text(manifest_v1, encoding="utf-8")

    # 2. EXECUTION: Run the build subcommand to compile the output tree with debug logs active
    result = runner.invoke(main_cli, [
        "build",
        "--project-config", str(project_file),
        "--manifests-dir", str(manifests_dir),
        "--templates-dir", str(templates_dir),
        "--sources-dir", str(sources_dir),
        "--debug"
    ])

    assert result.exit_code == 0, f"Normalization build run failed: {result.output}"

    # 3. ASSERTIONS: Verify that the postinst file contains our exact case rule mappings
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
    cli_sandbox: tuple[CliRunner, Path, Path, Path, Path],
    manifest_v2: str,
    changelog_v2: str,
) -> None:
    """Verifies that selecting 'No' at the interactive prompt skips the package.

    Args:
        cli_sandbox: A shared setup fixture providing an isolated CLI environment.
        manifest_v2: A test fixture providing a baseline manifest version 1.0.1 string.
        changelog_v2: The historical changelog tracking version 1.0.1 on disk.
    """
    # 1. SETUP: Extract pre-configured infrastructure components from our sandbox fixture
    runner, project_file, manifests_dir, templates_dir, sources_dir = cli_sandbox

    # Seed the history tracking file so that version 1.0.1 is already written on disk tracks
    pkg_debian_dir = sources_dir / "test-repo" / "debian"
    pkg_debian_dir.mkdir(parents=True, exist_ok=True)
    (pkg_debian_dir / "changelog").write_text(changelog_v2, encoding="utf-8")

    # Create an identical manifest version 1.0.1 file block, but modify its description
    raw_manifest_data = yaml.safe_load(manifest_v2)
    raw_manifest_data["description"] = "A brand new modified description text rule."

    modified_manifest_file = manifests_dir / "test-repo.yaml"
    modified_manifest_file.write_text(yaml.safe_dump(raw_manifest_data), encoding="utf-8")

    # 2. EXECUTION: Trigger the build subcommand pass while feeding 'n' (No) into stdin
    result = runner.invoke(
        main_cli,
        [
            "build",
            "--project-config", str(project_file),
            "--manifests-dir", str(manifests_dir),
            "--templates-dir", str(templates_dir),
            "--sources-dir", str(sources_dir),
            "--debug"
        ],
        input="n\n"  # Simulate pressing No
    )

    # 3. ASSERTIONS: The file must be skipped gracefully with a dedicated alert log message
    assert result.exit_code == 0
    assert "Manifest modified without version bump" in result.output
    assert "ALERT: Skipping package file test-repo.yaml" in result.output


def test_cli_auto_bumps_and_rewrites_manifest_on_yes_response(
    cli_sandbox: tuple[CliRunner, Path, Path, Path, Path],
    manifest_v2: str,
    changelog_v2: str,
) -> None:
    """Verifies that selecting 'Yes' at the prompt auto-bumps and rewrites the yaml.

    Args:
        cli_sandbox: A shared setup fixture providing an isolated CLI environment.
        manifest_v2: A test fixture providing a baseline manifest version 1.0.1 string.
        changelog_v2: The historical changelog tracking version 1.0.1 on disk.
    """
    # 1. SETUP: Extract pre-configured infrastructure components from our sandbox fixture
    runner, project_file, manifests_dir, templates_dir, sources_dir = cli_sandbox

    # Seed the history tracking file so that version 1.0.1 is already written on disk tracks
    pkg_debian_dir = sources_dir / "test-repo" / "debian"
    pkg_debian_dir.mkdir(parents=True, exist_ok=True)
    (pkg_debian_dir / "changelog").write_text(changelog_v2, encoding="utf-8")

    # Create an identical manifest version 1.0.1 file block, but modify its description
    raw_manifest_data = yaml.safe_load(manifest_v2)
    raw_manifest_data["description"] = "A brand new modified description text rule."

    modified_manifest_file = manifests_dir / "test-repo.yaml"
    modified_manifest_file.write_text(yaml.safe_dump(raw_manifest_data), encoding="utf-8")

    # 2. EXECUTION: Trigger the build subcommand pass while feeding 'y' (Yes) into stdin
    result = runner.invoke(
        main_cli,
        [
            "build",
            "--project-config", str(project_file),
            "--manifests-dir", str(manifests_dir),
            "--templates-dir", str(templates_dir),
            "--sources-dir", str(sources_dir),
            "--debug"
        ],
        input="y\n"  # Simulate pressing Yes
    )

    # 3. ASSERTIONS: Verify the console logged the confirmation bump state successfully
    assert result.exit_code == 0
    assert "Auto-bumping manifest file test-repo.yaml forward to v1.0.2" in result.output

    # 4. VERIFY DISK PERSISTENCE: Confirm the physical manifest file on disk was rewritten
    updated_yaml_content = modified_manifest_file.read_text(encoding="utf-8")
    assert "version: 1.0.2" in updated_yaml_content


def test_cli_auto_bumps_natively_via_flag_option(
    cli_sandbox: tuple[CliRunner, Path, Path, Path, Path],
    manifest_v2: str,
    changelog_v2: str,
) -> None:
    """Verifies that the --bump-version flag option auto-accepts without prompts.

    Args:
        cli_sandbox: A shared setup fixture providing an isolated CLI environment.
        manifest_v2: A test fixture providing a baseline manifest version 1.0.1 string.
        changelog_v2: The historical changelog tracking version 1.0.1 on disk.
    """
    # 1. SETUP: Extract pre-configured infrastructure components from our sandbox fixture
    runner, project_file, manifests_dir, templates_dir, sources_dir = cli_sandbox

    # Seed the history tracking file so that version 1.0.1 is already written on disk tracks
    pkg_debian_dir = sources_dir / "test-repo" / "debian"
    pkg_debian_dir.mkdir(parents=True, exist_ok=True)
    (pkg_debian_dir / "changelog").write_text(changelog_v2, encoding="utf-8")

    # Create an identical manifest version 1.0.1 file block, but modify its description
    raw_manifest_data = yaml.safe_load(manifest_v2)
    raw_manifest_data["description"] = "A brand new modified description text rule."

    modified_manifest_file = manifests_dir / "test-repo.yaml"
    modified_manifest_file.write_text(yaml.safe_dump(raw_manifest_data), encoding="utf-8")

    # 2. EXECUTION: Trigger build with the explicit --bump-version flag option parameter active
    result = runner.invoke(
        main_cli,
        [
            "build",
            "--project-config", str(project_file),
            "--manifests-dir", str(manifests_dir),
            "--templates-dir", str(templates_dir),
            "--sources-dir", str(sources_dir),
            "--bump-version",  # Bypass prompts natively
            "--debug"
        ]
    )

    # 3. ASSERTIONS: Verify the console logged the confirmation bump state successfully
    assert result.exit_code == 0
    assert "Auto-bumping manifest file test-repo.yaml forward to v1.0.2" in result.output

    # 4. VERIFY DISK PERSISTENCE: Confirm the physical manifest file on disk was rewritten
    updated_yaml_content = modified_manifest_file.read_text(encoding="utf-8")
    assert "version: 1.0.2" in updated_yaml_content


def test_cli_re_raises_genuine_value_errors_like_rogue_templates(
    cli_sandbox: tuple[CliRunner, Path, Path, Path, Path],
    tmp_path: Path,
    manifest_v1: str,
) -> None:
    """Verifies that the CLI re-raises true architectural template panics.

    Args:
        cli_sandbox: A shared setup fixture providing an isolated CLI environment.
        tmp_path: A built-in pytest fixture providing a temporary directory path.
        manifest_v1: A test fixture providing a baseline manifest string.
    """
    # 1. SETUP: Extract pre-configured infrastructure components from our sandbox fixture
    runner, project_file, manifests_dir, _, sources_dir = cli_sandbox

    # Write out the repository manifest into the fixture's manifests folder
    manifest_file = manifests_dir / "test-repo.yaml"
    manifest_file.write_text(manifest_v1, encoding="utf-8")

    # SETUP: Violate the template contract by placing a rogue changelog file into a target folder
    rogue_templates_root = tmp_path / "templates_rogue" / "debian"
    rogue_templates_root.mkdir(parents=True, exist_ok=True)
    (rogue_templates_root / "changelog").write_text("", encoding="utf-8")

    # 2. EXECUTION: This must abort with exit code 1 because the architectural error is re-raised
    result = runner.invoke(main_cli, [
        "build",
        "--project-config", str(project_file),
        "--manifests-dir", str(manifests_dir),
        "--templates-dir", str(tmp_path / "templates_rogue"),
        "--sources-dir", str(sources_dir),
        "--debug"
    ])

    # 3. ASSERTIONS: Verify that the pipeline correctly crashed out on the re-raised panic
    assert result.exit_code != 0
    assert "Required layout file 'changelog.jinja2' is missing" in result.output
