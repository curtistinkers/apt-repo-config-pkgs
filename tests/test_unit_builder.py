# tests/test_unit_builder.py
"""DebianProjectBuilder unit tests.

Discrete unit specifications validating the folder orchestration and file
generation layer managed by the DebianPackageBuilder class.
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml

from package_generator import (
    DebianPackageBuilder,
    DebianTemplateCompiler,
    Logger,
    ProjectManifest,
    RepositoryManifest,
)


@pytest.fixture
def mock_builder_ctx(tmp_path: Path) -> tuple[DebianPackageBuilder, MagicMock, MagicMock, Path]:
    """Provides a fully mocked builder instance with pre-configured services.

    Acts exactly like a PHPUnit setUp() method, isolating network and
    cryptographic layers across all package tree unit tests.
    """
    logger = Logger(min_terminal_level="emergency")

    # Setup mock templates footprint so compiler can run
    templates_dir = tmp_path / "templates" / "debian"
    templates_dir.mkdir(parents=True, exist_ok=True)

    (templates_dir / "control").write_text("Package: {{ package_name }}", encoding="utf-8")
    (templates_dir / "rules").write_text("#!/usr/bin/make", encoding="utf-8")

    compiler = DebianTemplateCompiler(templates_dir=templates_dir, logger=logger)
    sources_dir = tmp_path / "dpkg-sources"

    # Configure our uniform network and crypto mocks
    downloader = MagicMock()

    # We prefix with ASCII headers so default fixture runs go down the dearmor track cleanly
    downloader.download_bytes.return_value = b"-----BEGIN PGP PUBLIC KEY BLOCK-----\nMOCK_ASCII_KEY"

    gpg_engine = MagicMock()
    gpg_engine.dearmor.return_value = b"MOCK_BINARY_BYTES"


    builder = DebianPackageBuilder(
        sources_dir=sources_dir,
        logger=logger,
        compiler=compiler,
        downloader=downloader,
        gpg_engine=gpg_engine,
    )

    return builder, downloader, gpg_engine, sources_dir


def test_builder_build_clean_package_directory_tree(
    mock_builder_ctx: tuple[DebianPackageBuilder, MagicMock, MagicMock, Path],
    manifest_v1: str,
    project_config: str,
) -> None:
    """Verifies source tree directory and file compilation orchestration.

    Ensures that DebianPackageBuilder scans the templates directory, uses a
    PackageConfig and ProjectConfig to create debian/ source structures, and
    physically writes out all compiled configuration files onto disk.

    Args:
        mock_builder_ctx: A shared setup fixture providing a mocked builder context.
        manifest_v1: A test fixture providing a valid raw manifest YAML string.
        project_config: A test fixture providing a valid raw project YAML string.
    """
    # Extract pre-configured builder and dependencies from our shared setup fixture
    builder, _, _, sources_dir = mock_builder_ctx
    logger = Logger(min_terminal_level="emergency")

    raw_manifest_data = yaml.safe_load(manifest_v1)
    manifest = RepositoryManifest(raw_data=raw_manifest_data, logger=logger)

    raw_project_data = yaml.safe_load(project_config)
    project_manifest = ProjectManifest(raw_data=raw_project_data, logger=logger)

    # Pass both configuration DVOs to drive the compilation loop pass
    target_debian_dir = builder.create_package_tree(
        config=manifest.config,
        project_config=project_manifest.config,
    )

    # Verify the physical directory path exists matching the schema
    expected_path = sources_dir / "test-repo" / "debian"
    assert target_debian_dir == expected_path
    assert target_debian_dir.exists()

    # Assert that the modern static binary archive-keyring was saved perfectly
    expected_keyring = (
        target_debian_dir / "usr" / "share" / "keyrings" / "test-repo-archive-keyring.gpg"
    )
    assert expected_keyring.exists()
    assert expected_keyring.read_bytes() == b"MOCK_BINARY_BYTES"

    # Verify that the builder dynamically looped through the template folder
    # and generated all target configuration files onto the platter
    mandatory_files = ["control", "rules"]
    for filename in mandatory_files:
        expected_file = target_debian_dir / filename
        assert expected_file.exists(), f"The builder failed to generate file: {filename}"
        assert expected_file.read_text(encoding="utf-8").strip() != ""


def test_builder_successfully_removes_sources_directory_tree(
    mock_builder_ctx: tuple[DebianPackageBuilder, MagicMock, MagicMock, Path],
) -> None:
    """Verifies source tree directory removal.

    Ensures that the package builder can safely delete an entire generated
    directory tree structure from the filesystem.

    Args:
        mock_builder_ctx: A shared setup fixture providing a mocked builder context.
    """
    builder, _, _, sources_dir = mock_builder_ctx

    # Create the folder
    sources_dir.mkdir(parents=True, exist_ok=True)

    # Double-check that our setup worked and the path physically exists before cleaning
    assert sources_dir.exists()

    # Run the upcoming cleanup method
    builder.remove_package_tree()

    # The entire directory tree must be completely purged from disk
    assert not sources_dir.exists(), "The builder failed to delete the target directory tree."

def test_builder_persists_and_increments_existing_changelog_on_disk(
    mock_builder_ctx: tuple[DebianPackageBuilder, MagicMock, MagicMock, Path],
    manifest_v2: str,
    project_config: str,
    changelog_v1: str,
    changelog_v2: str,
) -> None:
    """Verifies that the builder reads an existing changelog to calculate deltas.

    Ensures that if a changelog file already exists in the target debian/ folder,
    the builder reverse-engineers its historical state, appends the new version
    delta entries, and overwrites the file non-destructively.

    Args:
        mock_builder_ctx: A shared setup fixture providing a mocked builder context.
        manifest_v2: A test fixture providing a bumped v2 manifest string.
        project_config: A test fixture providing a valid raw project YAML string.
        changelog_v1: The pre-existing historical changelog on the platter.
        changelog_v2: The expected cumulative final changelog output text stream.
    """
    # Extract pre-configured builder and workspace from our shared setup fixture
    builder, _, _, sources_dir = mock_builder_ctx
    logger = Logger(min_terminal_level="emergency")

    raw_manifest = yaml.safe_load(manifest_v2)
    manifest = RepositoryManifest(raw_data=raw_manifest, logger=logger)

    raw_project = yaml.safe_load(project_config)
    project_manifest = ProjectManifest(raw_data=raw_project, logger=logger)

    # Pre-seed the target debian/ tree with a real historical changelog file using fixture paths
    target_debian_dir = sources_dir / "test-repo" / "debian"
    target_debian_dir.mkdir(parents=True, exist_ok=True)
    existing_changelog_file = target_debian_dir / "changelog"
    existing_changelog_file.write_text(changelog_v1, encoding="utf-8")

    # Run the package directory tree compilation pass
    # We pass a fixed test timestamp override matching our changelog fixture requirements
    builder.create_package_tree(
        config=manifest.config,
        project_config=project_manifest.config,
        current_time="Mon, 10 Aug 2026 13:00:00 +0000",
    )

    # 3. ASSERTIONS: Verify the file on disk was incremented to v2 perfectly
    assert existing_changelog_file.exists()
    assert existing_changelog_file.read_text(encoding="utf-8").strip() == changelog_v2.strip()


def test_builder_throws_emergency_error_if_changelog_template_exists(
    mock_builder_ctx: tuple[DebianPackageBuilder, MagicMock, MagicMock, Path],
    tmp_path: Path,  # FIX 1: Request tmp_path directly to get type-safe access
    manifest_v1: str,
    project_config: str,
) -> None:
    """Verifies that the builder panics if a changelog file exists in templates.

    Args:
        mock_builder_ctx: A shared setup fixture providing a mocked builder context.
        tmp_path: A built-in pytest fixture providing a temporary directory path.
        manifest_v1: A test fixture providing a baseline manifest string.
        project_config: A test fixture providing a valid raw project YAML string.
    """
    builder, _, _, _ = mock_builder_ctx
    silent_logger = Logger(min_terminal_level="emergency")

    raw_manifest = yaml.safe_load(manifest_v1)
    manifest = RepositoryManifest(raw_data=raw_manifest, logger=silent_logger)

    raw_project = yaml.safe_load(project_config)
    project_manifest = ProjectManifest(raw_data=raw_project, logger=silent_logger)

    # FIX 2: Locate the templates directory natively using tmp_path coordinates
    sandbox_root = tmp_path / "templates" / "debian"
    (sandbox_root / "changelog").write_text("", encoding="utf-8")

    # FIX 3: Override template list with a type-safe lamda method execution track
    # We cast to Any to bypass Jinja's abstract base class property constraints quietly
    from typing import Any
    env_instance: Any = builder._compiler._env
    env_instance.list_templates = lambda: ["control", "rules", "changelog"]

    # ASSERTION: The builder must raise a ValueError and refuse to compile the tree
    with pytest.raises(ValueError, match="A template named 'changelog' was discovered"):
        builder.create_package_tree(
            config=manifest.config,
            project_config=project_manifest.config,
        )


def test_builder_uses_downloader_and_gpg_services_when_dynamic_keyring_is_false(
    mock_builder_ctx: tuple[DebianPackageBuilder, MagicMock, MagicMock, Path],
    manifest_v1: str,
    project_config: str,
) -> None:
    """Verifies builder invokes downloader and gpg engines for static keyrings.

    Args:
        mock_builder_ctx: A shared setup fixture providing a mocked builder context.
        manifest_v1: A test fixture providing a static baseline config manifest string.
    """
    # 1. SETUP: Extract pre-configured components directly from our shared setup fixture
    builder, mock_downloader, mock_gpg, _ = mock_builder_ctx
    logger = Logger(min_terminal_level="emergency")

    # FIX 1: Do NOT overwrite with MagicMock(). Configure the fixture's mocks directly:
    mock_downloader.download_bytes.return_value = b"-----BEGIN PGP PUBLIC KEY BLOCK-----\nMOCK_ASCII_KEY_CONTENT"
    mock_gpg.dearmor.return_value = b"MOCK_BINARY_DEARMORED_BYTES"

    raw_manifest = yaml.safe_load(manifest_v1)
    manifest = RepositoryManifest(raw_data=raw_manifest, logger=logger)

    # Ground the test: verify our v1 fixture has dynamic_keyring set to False
    assert manifest.config.dynamic_keyring is False

    raw_project = yaml.safe_load(project_config)
    project_manifest = ProjectManifest(raw_data=raw_project, logger=logger)

    # 3. EXECUTION: Run the folder structure tree compilation pass
    target_debian_dir = builder.create_package_tree(
        config=manifest.config,
        project_config=project_manifest.config,
    )

    # 4. DECOUPLED INVARIANT ASSERTIONS: Verify coordination behavior
    expected_key_file = (
        target_debian_dir / "usr" / "share" / "keyrings" / "test-repo-archive-keyring.gpg"
    )

    # FIX 2: Sync the exact endpoint file path URL string matching manifest_v1
    mock_downloader.download_bytes.assert_called_once_with(url="https://example.com/signing.gpg")

    # Verify that the builder fed that raw text straight into the GPG dearmor engine
    # Note: We slice off headers if your production code decodes it first
    mock_gpg.dearmor.assert_called_once_with(ascii_text="-----BEGIN PGP PUBLIC KEY BLOCK-----\nMOCK_ASCII_KEY_CONTENT")

    # Verify that the resulting binary bytes were physically written to the expected path
    assert expected_key_file.exists()
    assert expected_key_file.read_bytes() == b"MOCK_BINARY_DEARMORED_BYTES"



def test_builder_invokes_dearmor_when_key_payload_starts_with_ascii_headers(
    mock_builder_ctx: tuple[DebianPackageBuilder, MagicMock, MagicMock, Path],
    manifest_v1: str,
    project_config: str,
) -> None:
    """Verifies that the builder sends payloads to GpgEngine if armor headers match.

    Ensures that when download_bytes returns a stream beginning with ASCII text
    headers, the orchestrator routes it to the cryptographic dearmoring filter.
    """
    builder, mock_downloader, mock_gpg, _ = mock_builder_ctx
    silent_logger = Logger(min_terminal_level="emergency")

    # 1. SETUP: Configure the network downloader mock to return text armor bytes
    mock_downloader.download_bytes.return_value = b"-----BEGIN PGP PUBLIC KEY BLOCK-----\nmQEN..."
    mock_gpg.dearmor.return_value = b"MOCK_FILTERED_BINARY_BYTES"

    raw_manifest = yaml.safe_load(manifest_v1)
    manifest = RepositoryManifest(raw_data=raw_manifest, logger=silent_logger)
    project_manifest = ProjectManifest(
        raw_data=yaml.safe_load(project_config),
        logger=silent_logger
    )

    # 2. EXECUTION: Drive the compilation loop pass
    target_debian_dir = builder.create_package_tree(
        config=manifest.config,
        project_config=project_manifest.config,
    )

    # 3. ASSERTIONS: Verify the crypto engine was called and the result was saved
    mock_gpg.dearmor.assert_called_once_with(
        ascii_text="-----BEGIN PGP PUBLIC KEY BLOCK-----\nmQEN..."
    )

    expected_file = (
        target_debian_dir / "usr" / "share" / "keyrings" / "test-repo-archive-keyring.gpg"
    )
    assert expected_file.read_bytes() == b"MOCK_FILTERED_BINARY_BYTES"


def test_builder_bypasses_dearmor_when_key_payload_is_already_raw_binary(
    mock_builder_ctx: tuple[DebianPackageBuilder, MagicMock, MagicMock, Path],
    manifest_v1: str,
    project_config: str,
) -> None:
    """Verifies that the builder writes binary public keys straight to disk.

    Ensures that when download_bytes returns a raw pre-compiled binary stream,
    the orchestrator skips GpgEngine entirely and saves the raw payload bytes.
    """
    builder, mock_downloader, mock_gpg, _ = mock_builder_ctx
    silent_logger = Logger(min_terminal_level="emergency")

    # 1. SETUP: Configure the network downloader mock to return non-armored binary bytes
    mock_raw_binary_payload = b"\x99\x01\x00_RAW_UNARMORED_BINARY_STREAM"
    mock_downloader.download_bytes.return_value = mock_raw_binary_payload

    raw_manifest = yaml.safe_load(manifest_v1)
    manifest = RepositoryManifest(raw_data=raw_manifest, logger=silent_logger)
    project_manifest = ProjectManifest(
        raw_data=yaml.safe_load(project_config),
        logger=silent_logger
    )

    # 2. EXECUTION: Drive the compilation loop pass
    target_debian_dir = builder.create_package_tree(
        config=manifest.config,
        project_config=project_manifest.config,
    )

    # 3. ASSERTIONS: Verify the crypto engine was completely bypassed
    assert not mock_gpg.dearmor.called

    expected_file = (
        target_debian_dir / "usr" / "share" / "keyrings" / "test-repo-archive-keyring.gpg"
    )
    assert expected_file.read_bytes() == mock_raw_binary_payload
