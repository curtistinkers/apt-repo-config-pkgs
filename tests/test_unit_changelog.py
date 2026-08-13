# tests/test_unit_changelog.py
"""Changelog unit tests.

Discrete unit specifications validating the Debian changelog lifecycle generation,
state-driven diff calculations, and version history stacking.
"""

from pathlib import Path

import pytest
import yaml

from package_generator import (
    Changelog,
    DebianTemplateCompiler,
    Logger,
    PackageConfig,
    ProjectConfig,
    ProjectManifest,
    RepositoryManifest,
)


@pytest.fixture
def changelog_sandbox(
    tmp_path: Path,
    project_config: str,
    mock_changelog_template: str,
) -> tuple[Logger, Path, ProjectConfig]:
    """Establishes a unified, type-safe sandbox environment for changelog unit tests.

    Automates structural configuration DVO parsing and seeds the required external
    Jinja2 changelog template layout directly inside a temporary workspace container.

    Returns:
        A tuple tracking (template_directory_path, package_config_dvo, project_config_dvo).
    """
    logger = Logger(min_terminal_level="emergency")

    raw_project = yaml.safe_load(project_config)
    project = ProjectManifest(raw_data=raw_project, logger=logger).config

    # 2. Automatically establish the required templates layout footprint on disk
    template_dir = tmp_path / "templates"
    template_dir.mkdir(parents=True, exist_ok=True)

    changelog_template = template_dir / "changelog.jinja2"
    changelog_template.write_text(mock_changelog_template, encoding="utf-8")

    return logger, template_dir, project


@pytest.fixture
def config_v1(manifest_v1: str) -> PackageConfig:
    """Compiles the raw version 1.0.0 manifest string into a type-safe object.

    Args:
        manifest_v1: A shared test fixture providing the baseline manifest YAML string.

    Returns:
        A strongly typed PackageConfig domain value object instance.
    """
    logger = Logger(min_terminal_level="emergency")
    raw_manifest = yaml.safe_load(manifest_v1)
    return RepositoryManifest(raw_data=raw_manifest, logger=logger).config


@pytest.fixture
def config_v2(manifest_v2: str) -> PackageConfig:
    """Compiles the raw version 1.0.0 manifest string into a type-safe object.

    Args:
        manifest_v2: A shared test fixture providing the baseline manifest YAML string.

    Returns:
        A strongly typed PackageConfig domain value object instance.
    """
    logger = Logger(min_terminal_level="emergency")
    raw_manifest = yaml.safe_load(manifest_v2)
    return RepositoryManifest(raw_data=raw_manifest, logger=logger).config


@pytest.fixture
def config_v3(manifest_v3: str) -> PackageConfig:
    """Compiles the raw version 1.0.0 manifest string into a type-safe object.

    Args:
        manifest_v3: A shared test fixture providing the baseline manifest YAML string.

    Returns:
        A strongly typed PackageConfig domain value object instance.
    """
    logger = Logger(min_terminal_level="emergency")
    raw_manifest = yaml.safe_load(manifest_v3)
    return RepositoryManifest(raw_data=raw_manifest, logger=logger).config


def test_changelog_parses_genesis_release_metadata(changelog_v1: str) -> None:
    """Verifies that the changelog engine cleanly parses a baseline v1 text block.

    Args:
        changelog_v1: A test fixture providing a raw initial changelog text string.
    """
    logger = Logger(min_terminal_level="emergency")
    manifest = Changelog(raw_text=changelog_v1, logger=logger)

    assert manifest.latest_entry is not None

    assert manifest.latest_entry.package_name == "test-repo-repo-config"
    assert manifest.latest_entry.version == "1.0.0"
    assert manifest.latest_entry.suite == "stable"
    assert manifest.latest_entry.urgency == "medium"
    assert "Initial package definition established." in manifest.latest_entry.changes
    assert manifest.latest_entry.timestamp == "Mon, 10 Aug 2026 12:00:00 +0000"


def test_changelog_tracks_multiple_historical_blocks(changelog_v3: str) -> None:
    """Verifies that the engine handles and orders multi-block release chains.

    Args:
        changelog_v3: A test fixture providing a master three-entry changelog text.
    """
    logger = Logger(min_terminal_level="emergency")
    manifest = Changelog(raw_text=changelog_v3, logger=logger)

    assert len(manifest.entries) == 3
    assert manifest.entries[0].version == "1.0.2"
    assert manifest.entries[1].version == "1.0.1"
    assert manifest.entries[2].version == "1.0.0"

def test_changelog_handles_empty_or_invalid_text_gracefully() -> None:
    """Verifies that the engine handles unparseable text without crashing."""
    logger = Logger(min_terminal_level="emergency")

    # Ingest a completely invalid string text layout
    manifest = Changelog(
        raw_text="This is random junk text, not a changelog.", logger=logger
    )

    # Assert that the engine exited safely with an empty list and no latest entry
    assert len(manifest.entries) == 0
    assert manifest.latest_entry is None

def test_changelog_generates_genesis_release_from_v1_manifest(
    changelog_sandbox: tuple[Logger, Path, ProjectConfig],
    config_v1: PackageConfig,
    changelog_v1: str,
) -> None:
    """Verifies that compiling a blank history with manifest v1 outputs changelog v1.

    Args:
        changelog_sandbox: Shared setup fixture providing the template directory and project object.
        config_v1: Shared setup fixture providing the initial repository object.
        changelog_v1: The expected initial genesis changelog file text block.
    """
    # Extract the shared infrastructure assets from fixtures
    logger, template_dir, project = changelog_sandbox
    # Instantiate the engine with a clean slate
    changelog_engine = Changelog(raw_text="", logger=logger)
    # Compile changelog entry
    compiled_output = changelog_engine.generate_next_version(
        config=config_v1,
        project_config=project,
        templates_dir=template_dir,
        current_time="Mon, 10 Aug 2026 12:00:00 +0000"
    )
    # Check that the final compiled layout matches our target fixture perfectly
    assert compiled_output.strip() == changelog_v1.strip()


def test_changelog_appends_delta_changes_from_v2_manifest(
    changelog_sandbox: tuple[Logger, Path, ProjectConfig],
    config_v1: PackageConfig,
    config_v2: PackageConfig,
    changelog_v2: str,
) -> None:
    """Verifies that appending a version bump from manifest v2 outputs changelog v2.

    Args:
        changelog_sandbox: Shared setup fixture providing the template directory and project object.
        config_v1: Shared setup fixture providing the baseline repository object.
        config_v2: Shared setup fixture providing the bumped v2 repository object.
        changelog_v2: The expected accumulated history changelog file text block.
    """
    # Extract the shared infrastructure assets from fixtures
    logger, template_dir, project = changelog_sandbox
    # Instantiate the changelog engine with a clean slate
    changelog_engine = Changelog(raw_text="", logger=logger)
    # Compile changelog entry for config_v1
    history_track = changelog_engine.generate_next_version(
        config=config_v1,
        project_config=project,
        templates_dir=template_dir,
        current_time="Mon, 10 Aug 2026 12:00:00 +0000"
    )
    # Instantiate the changelog engine with the generated manifest from config_v1
    bump_engine = Changelog(raw_text=history_track, logger=logger)
    # Compile changelog entry for config_v2
    compiled_output = bump_engine.generate_next_version(
        config=config_v2,
        project_config=project,
        templates_dir=template_dir,
        current_time="Mon, 10 Aug 2026 13:00:00 +0000"  # Pass fixed test timestamp
    )
    # Check that the final compiled layout matches our target fixture perfectly
    assert compiled_output.strip() == changelog_v2.strip()


def test_changelog_compiles_cumulative_history_from_v3_manifest(
    changelog_sandbox: tuple[Logger, Path, ProjectConfig],
    config_v1: PackageConfig,
    config_v2: PackageConfig,
    config_v3: PackageConfig,
    changelog_v3: str,
) -> None:
    """Verifies that appending an array removal from manifest v3 outputs changelog v3.

    Args:
        changelog_sandbox: Shared setup fixture providing the template directory and project object.
        config_v1: Shared setup fixture providing the baseline repository object.
        config_v2: Shared setup fixture providing the bumped v2 repository object.
        config_v3: Shared setup fixture providing the bumped v2 repository object.
        changelog_v3: The expected cumulative final master changelog file text block.
    """
    # Extract the shared infrastructure assets from fixtures
    logger, template_dir, project = changelog_sandbox
    # Instantiate the changelog engine with a clean slate
    changelog_engine = Changelog(raw_text="", logger=logger)
    # Compile each changelog fixture one after the other
    history_v1 = changelog_engine.generate_next_version(
        config=config_v1,
        project_config=project,
        templates_dir=template_dir,
        current_time="Mon, 10 Aug 2026 12:00:00 +0000"
    )
    engine_v2 = Changelog(raw_text=history_v1, logger=logger)
    history_v2 = engine_v2.generate_next_version(
        config=config_v2,
        project_config=project,
        templates_dir=template_dir,
        current_time="Mon, 10 Aug 2026 13:00:00 +0000"
    )
    engine_v3 = Changelog(raw_text=history_v2, logger=logger)
    compiled_output = engine_v3.generate_next_version(
        config=config_v3,
        project_config=project,
        templates_dir=template_dir,
        current_time="Mon, 10 Aug 2026 14:00:00 +0000"  # Pass fixed test timestamp
    )
    # Check that the final compiled layout matches our target fixture perfectly
    assert compiled_output.strip() == changelog_v3.strip()

def test_changelog_can_reconstruct_exact_manifest_v1_file(
    changelog_sandbox: tuple[Logger, Path, ProjectConfig],
    manifest_v1: str,
    changelog_v1: str,
    mock_manifest_template: str,
) -> None:
    """Verifies that parsing changelog v1 reproduces manifest v1 exactly via template.

    Args:
        changelog_sandbox: Shared setup fixture providing the template directory and project object.
        manifest_v1: A test fixture providing the expected target YAML string.
        changelog_v1: A test fixture providing the initial changelog text string.
        mock_manifest_template: Blueprint layout matching manifest_v1 format.
    """
    # Extract the shared infrastructure assets from fixtures
    logger, template_dir, project = changelog_sandbox
    # Instantiate the changelog engine with the changelog_v1 fixture
    changelog_engine = Changelog(raw_text=changelog_v1, logger=logger)
    # Reverse-engineer the ledger back into a PackageConfig object
    rebuilt_config = changelog_engine.to_package_config()
    # Write our mock manifest template to a temporary directory
    template_file = template_dir / "manifest.jinja2"
    template_file.write_text(mock_manifest_template, encoding="utf-8")
    # Render the rebuilt manifest file back into text layout rows
    compiler = DebianTemplateCompiler(templates_dir=template_dir, logger=logger)
    rendered_manifest = compiler.render_template(
        template_name="manifest.jinja2",
        package_config=rebuilt_config,
        project_config=project,  # Pass the real type-safe config object
    )
    # Reconstructed YAML string must match origin exactly
    assert rendered_manifest.strip() == manifest_v1.strip()


def test_changelog_can_reconstruct_exact_manifest_v2_file(
    changelog_sandbox: tuple[Logger, Path, ProjectConfig],
    manifest_v2: str,
    changelog_v2: str,
    mock_manifest_template: str,
) -> None:
    """Verifies that parsing changelog v2 reproduces manifest v2 exactly via template.

    Args:
        changelog_sandbox: Shared setup fixture providing the template directory and project object.
        manifest_v2: A test fixture providing the expected target YAML string.
        changelog_v2: A test fixture providing the changelog text string.
        mock_manifest_template: Blueprint layout matching manifest_v1 format.
    """
    # Extract the shared infrastructure assets from fixtures
    logger, template_dir, project = changelog_sandbox
    # Instantiate the changelog engine with the changelog_v1 fixture
    changelog_engine = Changelog(raw_text=changelog_v2, logger=logger)
    # Reverse-engineer the ledger back into a PackageConfig object
    rebuilt_config = changelog_engine.to_package_config()
    # Write our mock manifest template to a temporary directory
    template_file = template_dir / "manifest.jinja2"
    template_file.write_text(mock_manifest_template, encoding="utf-8")
    # Render the rebuilt manifest file back into text layout rows
    compiler = DebianTemplateCompiler(templates_dir=template_dir, logger=logger)
    rendered_manifest = compiler.render_template(
        template_name="manifest.jinja2",
        package_config=rebuilt_config,
        project_config=project,  # Pass the real type-safe config object
    )
    # Reconstructed YAML string must match origin exactly
    assert rendered_manifest.strip() == manifest_v2.strip()


def test_changelog_can_reconstruct_exact_manifest_v3_file(
    changelog_sandbox: tuple[Logger, Path, ProjectConfig],
    changelog_v3: str,
    manifest_v3: str,
    mock_manifest_template: str,
) -> None:
    """Verifies that parsing changelog v3 reproduces manifest v3 exactly via template.

    Args:
        changelog_sandbox: Shared setup fixture providing the template directory and project object.
        changelog_v3: A test fixture providing the cumulative v3 changelog text string.
        manifest_v3: A test fixture providing the expected target YAML string.
        mock_manifest_template: Blueprint layout matching manifest_v1 format.
    """
    # Extract the shared infrastructure assets from fixtures
    logger, template_dir, project = changelog_sandbox

    changelog_engine = Changelog(raw_text=changelog_v3, logger=logger)

    reconstructed_config = changelog_engine.to_package_config()

    template_file = template_dir / "manifest.jinja2"
    template_file.write_text(mock_manifest_template, encoding="utf-8")

    compiler = DebianTemplateCompiler(templates_dir=template_dir, logger=logger)

    rendered_manifest = compiler.render_template(
        template_name="manifest.jinja2",
        package_config=reconstructed_config,
        project_config=project,
    )

    assert rendered_manifest.strip() == manifest_v3.strip()

def test_changelog_returns_raw_text_unchanged_if_no_changes_detected(
    changelog_sandbox: tuple[Logger, Path, ProjectConfig],
    config_v1: PackageConfig,
    changelog_v1: str,
) -> None:
    """Verifies that the engine returns the existing text if no data fields changed.

    Args:
        changelog_sandbox: Shared setup fixture providing the template directory and project object.
        config_v1: A test fixture providing the baseline configuration state.
        changelog_v1: A pre-existing changelog file text block.
    """
    # Extract the shared infrastructure assets from fixtures
    logger, template_dir, project = changelog_sandbox

    # Ingest changelog_v1 as our active history pool
    changelog_engine = Changelog(raw_text=changelog_v1, logger=logger)

    # Attempt to compile a new version entry block
    compiled_output = changelog_engine.generate_next_version(
        config=config_v1,
        project_config=project,
        templates_dir=template_dir,
        current_time="Mon, 10 Aug 2026 12:00:00 +0000",
    )

    # The output text stream must match changelog_v1 precisely without duplicates
    assert compiled_output.strip() == changelog_v1.strip()


def test_changelog_raises_value_error_on_version_downgrade(
    changelog_sandbox: tuple[Logger, Path, ProjectConfig],
    config_v1: PackageConfig,
    changelog_v2: str,
) -> None:
    """Verifies that attempting a backward version downgrade raises a ValueError.

    Args:
        changelog_sandbox: Shared setup fixture providing the template directory and project object.
        config_v1: A test fixture providing the baseline configuration state.
        changelog_v2: Pre-existing history that is already ahead at version 1.0.1.
    """
    # Extract the shared infrastructure assets from fixtures
    logger, template_dir, project = changelog_sandbox

    # Ingest changelog_v2 history (which has already progressed to version 1.0.1)
    changelog_engine = Changelog(raw_text=changelog_v2, logger=logger)

    # ASSERTION: The generation loop must raise a ValueError and halt that path immediately
    with pytest.raises(
        ValueError,
        match="Version downgrade violation: Proposed version '1.0.0' is sequentially lower "
            "than latest ledger release '1.0.1'."
    ):
        changelog_engine.generate_next_version(
            config=config_v1,
            project_config=project,
            templates_dir=template_dir
        )

def test_changelog_raises_value_error_when_manifest_modified_without_version_bump(
    changelog_sandbox: tuple[Logger, Path, ProjectConfig],
    manifest_v2: str,
    changelog_v2: str,
) -> None:
    """Raises ValueError when manifest data changes but the version does not.

    Verifies that the engine raises a ValueError if modifications are made
    to a manifest without changing the version string identifier.

    Args:
        changelog_sandbox: Shared setup fixture providing the template directory and project object.
        manifest_v2: A test fixture providing a baseline v2 (1.0.1) config state.
        changelog_v2: Pre-existing history that is already at version 1.0.1.
    """
    # Extract the shared infrastructure assets from fixtures
    logger, template_dir, project = changelog_sandbox
    changelog_engine = Changelog(raw_text=changelog_v2, logger=logger)

    # Load manifest_v2 (1.0.1) but alter a field to simulate a modification
    # without changing the version string away from 1.0.1
    raw_manifest_data = yaml.safe_load(manifest_v2)
    raw_manifest_data["description"] = "A brand new modified description text rule."

    config_modified = RepositoryManifest(raw_data=raw_manifest_data, logger=logger).config

    # ASSERTION: The loop must throw an exception to protect against duplicate headers
    with pytest.raises(ValueError, match="Manifest modified without version bump"):
        changelog_engine.generate_next_version(
            config=config_modified,
            project_config=project,
            templates_dir=template_dir
        )


def test_changelog_calculates_modified_os_mapping_property_deltas(
    changelog_sandbox: tuple[Logger, Path, ProjectConfig],
    manifest_v1: str,
    changelog_v1: str,
) -> None:
    """Verifies that the engine detects and documents altered fields inside os_mappings.

    Args:
        changelog_sandbox: Shared setup fixture providing the template directory and project object.
        manifest_v1: A test fixture providing a baseline configuration state.
        changelog_v1: An existing history that has progressed forward to v1.0.0.
    """
    # Extract the shared infrastructure assets from fixtures
    logger, template_dir, project = changelog_sandbox

    changelog_engine = Changelog(raw_text=changelog_v1, logger=logger)

    # Alter 'codename' for index pop|linux and bump version to pass downgrade checks
    raw_manifest_data = yaml.safe_load(manifest_v1)
    raw_manifest_data["os_mappings"]["pop|linuxmint"]["codename"] = "noble"
    raw_manifest_data["version"] = "1.0.1"

    config_v2 = RepositoryManifest(raw_data=raw_manifest_data, logger=logger).config

    # EXECUTION: Run the dynamic diff generation loop pass
    compiled_output = changelog_engine.generate_next_version(
        config=config_v2,
        project_config=project,
        templates_dir=template_dir,
        current_time="Mon, 10 Aug 2026 13:00:00 +0000",
    )

    # ASSERTION: Engine must compute the internal rule change bullet lines successfully
    assert "Modified os_mappings rule matching pop|linuxmint" in compiled_output
    assert "codename=noble" in compiled_output

def test_changelog_reconstructs_static_keyring_toggle_from_text() -> None:
    """Verifies that the engine extracts static keyring toggles from text."""
    logger = Logger(min_terminal_level="emergency")

    mock_history = (
        "test-repo (1.0.1) stable; urgency=medium\n\n"
        "  * Updated version to 1.0.1\n"
        "  * Toggled repository keyring strategy to: static\n\n"
        " -- Alice <alice@example.com>  Mon, 10 Aug 2026 13:00:00 +0000"
    )

    engine = Changelog(raw_text=mock_history, logger=logger)
    config = engine.to_package_config()
    assert config.dynamic_keyring is False

def test_changelog_calculates_modified_os_mapping_distro_property_deltas(
    changelog_sandbox: tuple[Logger, Path, ProjectConfig],
    manifest_v1: str,
    changelog_v1: str,
) -> None:
    """Verifies that the engine detects altered distro fields in os_mappings."""
    # Extract the shared infrastructure assets from fixtures
    logger, template_dir, project = changelog_sandbox

    changelog_engine = Changelog(raw_text=changelog_v1, logger=logger)

    raw_manifest_data = yaml.safe_load(manifest_v1)
    # Alter distro instead of codename to hit the missing line branch path
    raw_manifest_data["os_mappings"]["pop|linuxmint"]["distro"] = "debian-custom"
    raw_manifest_data["version"] = "1.0.1"

    config_v2 = RepositoryManifest(raw_data=raw_manifest_data, logger=logger).config

    compiled_output = changelog_engine.generate_next_version(
        config=config_v2,
        project_config=project,
        templates_dir=template_dir,
        current_time="Mon, 10 Aug 2026 13:00:00 +0000",
    )

    assert "Modified os_mappings rule matching pop|linuxmint" in compiled_output
    assert "distro=debian-custom" in compiled_output

def test_changelog_isolates_repo_url_and_key_url_deltas_precisely(
    changelog_sandbox: tuple[Logger, Path, ProjectConfig],
    manifest_v1: str,
    changelog_v1: str,
) -> None:
    """Verifies modifying only repo.url does not falsely claim a key_url delta."""
    # Extract the shared infrastructure assets from fixtures
    logger, template_dir, project = changelog_sandbox

    changelog_engine = Changelog(raw_text=changelog_v1, logger=logger)

    raw_manifest_data = yaml.safe_load(manifest_v1)
    # Modify ONLY the url parameter to match your real-world scenario bug
    raw_manifest_data["repo"]["url"] = "http://packages2.openmediavault.org"
    raw_manifest_data["version"] = "1.0.1"

    config_v2 = RepositoryManifest(raw_data=raw_manifest_data, logger=logger).config

    compiled_output = changelog_engine.generate_next_version(
        config=config_v2,
        project_config=project,
        templates_dir=template_dir,
    )

    assert "repo.url=" in compiled_output
    # CRITICAL INVARIANT: It must NOT claim that repo.key_url was modified
    assert "Modified repo.key_url" not in compiled_output


def test_changelog_calculates_and_persists_repo_components_and_suites_deltas(
    changelog_sandbox: tuple[Logger, Path, ProjectConfig],
    manifest_v1: str,
    changelog_v1: str,
) -> None:
    """Verifies that changes to repo components and suites calculate deltas."""
    # Extract the shared infrastructure assets from fixtures
    logger, template_dir, project = changelog_sandbox

    changelog_engine = Changelog(raw_text=changelog_v1, logger=logger)

    raw_manifest_data = yaml.safe_load(manifest_v1)
    # Modify the parameters to match your real-world OpenMediaVault values
    raw_manifest_data["repo"]["components"] = "stable"
    raw_manifest_data["repo"]["suites"] = "synchrony"
    raw_manifest_data["version"] = "1.0.1"

    config_v2 = RepositoryManifest(raw_data=raw_manifest_data, logger=logger).config

    compiled_output = changelog_engine.generate_next_version(
        config=config_v2,
        project_config=project,
        templates_dir=template_dir,
    )

    assert "repo.components=" in compiled_output
    assert "repo.suites=" in compiled_output


def test_changelog_reverse_parser_successfully_reconstructs_components_and_suites(
    changelog_v1: str,
) -> None:
    """Verifies that to_package_config reverse-engineers components and suites."""
    logger = Logger(min_terminal_level="emergency")

    changelog_engine = Changelog(raw_text=changelog_v1, logger=logger)

    reconstructed_config = changelog_engine.to_package_config()

    # CRITICAL INVARIANT: The reverse-parsed object must capture the nested data
    assert reconstructed_config.repo.components == "main"
    assert reconstructed_config.repo.suites == "${TARGET_CODENAME}"

def test_changelog_engine_renders_next_version_using_external_jinja_template(
    changelog_sandbox: tuple[Logger, Path, ProjectConfig],
    config_v1: PackageConfig,
    changelog_v1: str,
    mock_changelog_template: str,
) -> None:
    """Verifies that Changelog uses an external Jinja template to format records.

    Ensures that instead of manual string compilation, the engine uses the
    provided template layout structure to output the final changelog text.

    Args:
        changelog_sandbox: Shared setup fixture providing the template directory and project object.
        config_v1: Shared setup fixture providing the initial repository object.
        changelog_v1: The expected initial genesis changelog file text block.
        mock_changelog_template: Blueprint layout matching changelog_v1 format.
    """
    # Extract the shared infrastructure assets from fixtures
    logger, template_dir, project = changelog_sandbox

    changelog_template = template_dir / "changelog.jinja2"
    changelog_template.write_text(mock_changelog_template, encoding="utf-8")

    # Initialize our changelog slate tracker pre-seeded with our existing history string fixture
    changelog = Changelog(raw_text=changelog_v1, logger=logger)

    # Pass the custom templates path straight to the generator routine
    compiled_output = changelog.generate_next_version(
        config=config_v1,
        project_config=project,
        current_time="Mon, 10 Aug 2026 12:00:00 +0000",
        templates_dir=template_dir,
    )

    # Verify the template structure applied the suffix and formatted lines perfectly
    assert compiled_output.strip() == changelog_v1.strip()

def test_changelog_incremental_deltas_returns_empty_when_no_latest_entry(
    changelog_sandbox: tuple[Logger, Path, ProjectConfig],
    config_v1: PackageConfig,
) -> None:
    """Verifies that the delta engine returns an empty list if no historical ledger entries exist.

    Args:
        changelog_sandbox: Shared setup fixture providing the template directory and project object.
        config_v1: A test fixture providing a baseline static keyring package configuration.
    """
    # Extract the shared infrastructure assets from fixtures
    logger, _, _ = changelog_sandbox

    # Initialize a baseline engine with an absolute blank text history string
    changelog_engine = Changelog(raw_text="", logger=logger)

    # Directly invoke the internal private delta compiler method to cover the guard rail branch
    result = changelog_engine._calculate_incremental_deltas(config=config_v1)
    assert result == []


def test_changelog_engine_fails_when_no_changelog_template(
    changelog_sandbox: tuple[Logger, Path, ProjectConfig],
    tmp_path: Path,
    config_v1: PackageConfig,
    changelog_v1: str,
) -> None:
    """Verifies that the generator raises a FileNotFoundError if the changelog template file is missing.

    Args:
        changelog_sandbox: Shared setup fixture providing the template directory and project object.
        tmp_path: A built-in pytest fixture providing a temporary directory path.
        config_v1: Shared setup fixture providing the initial repository object.
        changelog_v1: The expected initial genesis changelog file text block.
    """
    # Extract the shared infrastructure assets from fixtures
    logger, _, project = changelog_sandbox

    template_dir = tmp_path

    assert not (template_dir / "changelog.jinja2 ").exists()

    # Initialize our changelog slate tracker pre-seeded with our existing history string fixture
    changelog = Changelog(raw_text=changelog_v1, logger=logger)

    with pytest.raises(FileNotFoundError):
        changelog.generate_next_version(
            config=config_v1,
            project_config=project,
            current_time="Mon, 10 Aug 2026 12:00:00 +0000",
            templates_dir=template_dir,
        )
