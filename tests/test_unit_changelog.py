# tests/test_unit_changelog.py
"""Changelog unit tests.

Discrete unit specifications validating the Debian changelog lifecycle generation,
state-driven diff calculations, and version history stacking.
"""

from pathlib import Path

import pytest
import yaml

from package_generator import Changelog, Logger, ProjectManifest, RepositoryManifest


def test_changelog_parses_genesis_release_metadata(changelog_v1: str) -> None:
    """Verifies that the changelog engine cleanly parses a baseline v1 text block.

    Args:
        changelog_v1: A test fixture providing a raw initial changelog text string.
    """
    silent_logger = Logger(min_terminal_level="emergency")
    manifest = Changelog(raw_text=changelog_v1, logger=silent_logger)

    assert manifest.latest_entry is not None

    assert manifest.latest_entry.package_name == "test-repo"
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
    silent_logger = Logger(min_terminal_level="emergency")
    manifest = Changelog(raw_text=changelog_v3, logger=silent_logger)

    assert len(manifest.entries) == 3
    assert manifest.entries[0].version == "1.0.2"
    assert manifest.entries[1].version == "1.0.1"
    assert manifest.entries[2].version == "1.0.0"

def test_changelog_handles_empty_or_invalid_text_gracefully() -> None:
    """Verifies that the engine handles unparseable text without crashing."""
    silent_logger = Logger(min_terminal_level="emergency")

    # Ingest a completely invalid string text layout
    manifest = Changelog(
        raw_text="This is random junk text, not a changelog.", logger=silent_logger
    )

    # Assert that the engine exited safely with an empty list and no latest entry
    assert len(manifest.entries) == 0
    assert manifest.latest_entry is None

def test_changelog_generates_genesis_release_from_v1_manifest(
    manifest_v1: str,
    project_config: str,
    changelog_v1: str,
) -> None:
    """Verifies that compiling a blank history with manifest v1 outputs changelog v1.

    Args:
        manifest_v1: A test fixture providing the initial repository configuration.
        project_config: A test fixture providing global project configuration fields.
        changelog_v1: The expected initial genesis changelog file text block.
    """
    silent_logger = Logger(min_terminal_level="emergency")

    # Ingest primitive text fixtures into type-safe configuration DVO assets
    raw_manifest = yaml.safe_load(manifest_v1)
    config = RepositoryManifest(raw_data=raw_manifest, logger=silent_logger).config

    raw_project = yaml.safe_load(project_config)
    project_config_dvo = ProjectManifest(raw_data=raw_project, logger=silent_logger).config

    # EXECUTION: Instantiate the tool as a clean slate (blank text string)
    # and request a new version ledger compilation pass entry block
    changelog_engine = Changelog(raw_text="", logger=silent_logger)

    # 1. Inside test_changelog_generates_genesis_release_from_v1_manifest:
    compiled_output = changelog_engine.generate_next_version(
        config=config,
        project_config=project_config_dvo,
        current_time="Mon, 10 Aug 2026 12:00:00 +0000"  # Pass fixed test timestamp
    )

    # Recreated text must match origin text exactly row-for-row
    assert compiled_output.strip() == changelog_v1.strip()


def test_changelog_appends_delta_changes_from_v2_manifest(
    manifest_v1: str,
    manifest_v2: str,
    project_config: str,
    changelog_v2: str,
) -> None:
    """Verifies that appending a version bump from manifest v2 outputs changelog v2.

    Args:
        manifest_v1: A test fixture providing the baseline v1 configuration state.
        manifest_v2: A test fixture providing the bumped v2 configuration state.
        project_config: A test fixture providing global project configuration fields.
        changelog_v2: The expected accumulated history changelog file text block.
    """
    silent_logger = Logger(min_terminal_level="emergency")

    # Set up our baseline historical config and our targeted bumped configuration
    config_v1 = RepositoryManifest(
        raw_data=yaml.safe_load(manifest_v1),
        logger=silent_logger
    ).config
    config_v2 = RepositoryManifest(
        raw_data=yaml.safe_load(manifest_v2),
        logger=silent_logger
    ).config
    project_config_dvo = ProjectManifest(
        raw_data=yaml.safe_load(project_config),
        logger=silent_logger
    ).config

    # EXECUTION: Ingest the clean v1 changelog history, then request a version bump
    # to evaluate changes introduced by manifest_v2 dynamically
    changelog_engine = Changelog(raw_text="", logger=silent_logger)

    # 2. Inside test_changelog_appends_delta_changes_from_v2_manifest:
    history_track = changelog_engine.generate_next_version(
        config=config_v1,
        project_config=project_config_dvo,
        current_time="Mon, 10 Aug 2026 12:00:00 +0000"
    )

    bump_engine = Changelog(raw_text=history_track, logger=silent_logger)
    compiled_output = bump_engine.generate_next_version(
        config=config_v2,
        project_config=project_config_dvo,
        current_time="Mon, 10 Aug 2026 13:00:00 +0000"  # Pass fixed test timestamp
    )

    assert compiled_output.strip() == changelog_v2.strip()


def test_changelog_compiles_cumulative_history_from_v3_manifest(
    manifest_v1: str,
    manifest_v2: str,
    manifest_v3: str,
    project_config: str,
    changelog_v3: str,
) -> None:
    """Verifies that appending an array removal from manifest v3 outputs changelog v3.

    Args:
        manifest_v1: A test fixture providing the baseline v1 configuration state.
        manifest_v2: A test fixture providing the bumped v2 configuration state.
        manifest_v3: A test fixture providing the final v3 configuration state.
        project_config: A test fixture providing global project configuration fields.
        changelog_v3: The expected cumulative final master changelog file text block.
    """
    silent_logger = Logger(min_terminal_level="emergency")

    config_v1 = RepositoryManifest(
        raw_data=yaml.safe_load(manifest_v1),
        logger=silent_logger
    ).config
    config_v2 = RepositoryManifest(
        raw_data=yaml.safe_load(manifest_v2),
        logger=silent_logger
    ).config
    config_v3 = RepositoryManifest(
        raw_data=yaml.safe_load(manifest_v3),
        logger=silent_logger
    ).config
    project_config_dvo = ProjectManifest(
        raw_data=yaml.safe_load(project_config),
        logger=silent_logger
    ).config

    # Chain generations sequentially to form a continuous three-entry timeline record ledger row
    changelog_engine = Changelog(raw_text="", logger=silent_logger)

    # 3. Inside test_changelog_compiles_cumulative_history_from_v3_manifest:
    history_v1 = changelog_engine.generate_next_version(
        config=config_v1,
        project_config=project_config_dvo,
        current_time="Mon, 10 Aug 2026 12:00:00 +0000"
    )

    engine_v2 = Changelog(raw_text=history_v1, logger=silent_logger)
    history_v2 = engine_v2.generate_next_version(
        config=config_v2,
        project_config=project_config_dvo,
        current_time="Mon, 10 Aug 2026 13:00:00 +0000"
    )

    engine_v3 = Changelog(raw_text=history_v2, logger=silent_logger)
    compiled_output = engine_v3.generate_next_version(
        config=config_v3,
        project_config=project_config_dvo,
        current_time="Mon, 10 Aug 2026 14:00:00 +0000"  # Pass fixed test timestamp
    )

    assert compiled_output.strip() == changelog_v3.strip()

def test_changelog_can_reconstruct_exact_manifest_v1_file(
    tmp_path: Path,
    changelog_v1: str,
    manifest_v1: str,
    mock_manifest_template: str,
) -> None:
    """Verifies that parsing changelog v1 reproduces manifest v1 exactly via template.

    Args:
        tmp_path: A built-in pytest fixture providing a temporary directory path.
        changelog_v1: A test fixture providing the initial changelog text string.
        manifest_v1: A test fixture providing the expected target YAML string.
        mock_manifest_template: Blueprint layout matching manifest_v1 format.
    """
    silent_logger = Logger(min_terminal_level="emergency")
    changelog_engine = Changelog(raw_text=changelog_v1, logger=silent_logger)

    # 1. Reverse-engineer the ledger back into a compiled PackageConfig DVO
    reconstructed_config = changelog_engine.to_package_config()

    # 2. Write our mock blueprint to a temporary sandbox directory layout path
    sandbox_dir = tmp_path / "templates_v1"
    sandbox_dir.mkdir()
    template_file = sandbox_dir / "manifest_mock"
    template_file.write_text(mock_manifest_template, encoding="utf-8")

    # 3. Use our compiler to render the reconstructed DVO back into text layout rows
    from package_generator.compiler import DebianTemplateCompiler
    compiler = DebianTemplateCompiler(templates_dir=sandbox_dir, logger=silent_logger)

    # Pass an empty ProjectConfig since this matching template only requests package attributes
    from package_generator.models import ProjectConfig
    dummy_proj = ProjectConfig(
        maintainer_name="", maintainer_email="", copyright_holder="", repository_url=""
    )

    rendered_manifest = compiler.render_template(
        template_name="manifest_mock",
        package_config=reconstructed_config,
        project_config=dummy_proj,
    )

    # 4. CLOSED-LOOP INVARIANT ASSERTION: Reconstructed YAML string must match origin exactly
    assert rendered_manifest.strip() == manifest_v1.strip()


def test_changelog_can_reconstruct_exact_manifest_v2_file(
    tmp_path: Path,
    changelog_v2: str,
    manifest_v2: str,
    mock_manifest_template: str,
) -> None:
    """Verifies that parsing changelog v2 reproduces manifest v2 exactly via template.

    Args:
        tmp_path: A built-in pytest fixture providing a temporary directory path.
        changelog_v2: A test fixture providing the v2 delta changelog text string.
        manifest_v2: A test fixture providing the expected target YAML string.
        mock_manifest_template: Blueprint layout matching manifest_v1 format.
    """
    silent_logger = Logger(min_terminal_level="emergency")
    changelog_engine = Changelog(raw_text=changelog_v2, logger=silent_logger)

    reconstructed_config = changelog_engine.to_package_config()

    sandbox_dir = tmp_path / "templates_v2"
    sandbox_dir.mkdir()
    template_file = sandbox_dir / "manifest_mock"
    template_file.write_text(mock_manifest_template, encoding="utf-8")

    from package_generator.compiler import DebianTemplateCompiler
    compiler = DebianTemplateCompiler(templates_dir=sandbox_dir, logger=silent_logger)

    from package_generator.models import ProjectConfig
    dummy_proj = ProjectConfig(
        maintainer_name="", maintainer_email="", copyright_holder="", repository_url=""
    )

    rendered_manifest = compiler.render_template(
        template_name="manifest_mock",
        package_config=reconstructed_config,
        project_config=dummy_proj,
    )

    assert rendered_manifest.strip() == manifest_v2.strip()


def test_changelog_can_reconstruct_exact_manifest_v3_file(
    tmp_path: Path,
    changelog_v3: str,
    manifest_v3: str,
    mock_manifest_template: str,
) -> None:
    """Verifies that parsing changelog v3 reproduces manifest v3 exactly via template.

    Args:
        tmp_path: A built-in pytest fixture providing a temporary directory path.
        changelog_v3: A test fixture providing the cumulative v3 changelog text string.
        manifest_v3: A test fixture providing the expected target YAML string.
        mock_manifest_template: Blueprint layout matching manifest_v1 format.
    """
    silent_logger = Logger(min_terminal_level="emergency")
    changelog_engine = Changelog(raw_text=changelog_v3, logger=silent_logger)

    reconstructed_config = changelog_engine.to_package_config()

    sandbox_dir = tmp_path / "templates_v3"
    sandbox_dir.mkdir()
    template_file = sandbox_dir / "manifest_mock"
    template_file.write_text(mock_manifest_template, encoding="utf-8")

    from package_generator.compiler import DebianTemplateCompiler
    compiler = DebianTemplateCompiler(templates_dir=sandbox_dir, logger=silent_logger)

    from package_generator.models import ProjectConfig
    dummy_proj = ProjectConfig(
        maintainer_name="", maintainer_email="", copyright_holder="", repository_url=""
    )

    rendered_manifest = compiler.render_template(
        template_name="manifest_mock",
        package_config=reconstructed_config,
        project_config=dummy_proj,
    )

    assert rendered_manifest.strip() == manifest_v3.strip()

def test_changelog_returns_raw_text_unchanged_if_no_changes_detected(
    manifest_v1: str,
    project_config: str,
    changelog_v1: str,
) -> None:
    """Verifies that the engine returns the existing text if no data fields changed.

    Args:
        manifest_v1: A test fixture providing the baseline configuration state.
        project_config: A test fixture providing global project configuration fields.
        changelog_v1: A pre-existing changelog file text block.
    """
    silent_logger = Logger(min_terminal_level="emergency")

    # SETUP: Ingest changelog_v1 as our active history pool
    changelog_engine = Changelog(raw_text=changelog_v1, logger=silent_logger)

    # Process manifest_v1 again (which has an identical version 1.0.0 and same fields)
    config_v1 = RepositoryManifest(
        raw_data=yaml.safe_load(manifest_v1), logger=silent_logger
    ).config
    project_config_dvo = ProjectManifest(
        raw_data=yaml.safe_load(project_config), logger=silent_logger
    ).config

    # EXECUTION: Attempt to compile a new version entry block
    compiled_output = changelog_engine.generate_next_version(
        config=config_v1,
        project_config=project_config_dvo,
        current_time="Mon, 10 Aug 2026 12:00:00 +0000"
    )

    # ASSERTION: The output text stream must match changelog_v1 precisely without duplicates
    assert compiled_output.strip() == changelog_v1.strip()


def test_changelog_raises_value_error_on_version_downgrade(
    manifest_v1: str,
    project_config: str,
    changelog_v2: str,
) -> None:
    """Verifies that attempting a backward version downgrade raises a ValueError.

    Args:
        manifest_v1: A test fixture providing a v1 (version 1.0.0) config state.
        project_config: A test fixture providing global project configuration fields.
        changelog_v2: Pre-existing history that is already ahead at version 1.0.1.
    """
    silent_logger = Logger(min_terminal_level="emergency")

    # SETUP: Ingest changelog_v2 history (which has already progressed to version 1.0.1)
    changelog_engine = Changelog(raw_text=changelog_v2, logger=silent_logger)

    # Feed manifest_v1 (version 1.0.0) which attempts an illegal downgrade track
    config_v1 = RepositoryManifest(
        raw_data=yaml.safe_load(manifest_v1), logger=silent_logger
    ).config
    project_config_dvo = ProjectManifest(
        raw_data=yaml.safe_load(project_config), logger=silent_logger
    ).config

    # ASSERTION: The generation loop must raise a ValueError and halt that path immediately
    with pytest.raises(ValueError, match="Version downgrade rejected"):
        changelog_engine.generate_next_version(
            config=config_v1,
            project_config=project_config_dvo
        )

def test_changelog_raises_value_error_when_manifest_modified_without_version_bump(
    manifest_v2: str,
    project_config: str,
    changelog_v2: str,
) -> None:
    """Raises ValueError when manifest data changes but the version does not.

    Verifies that the engine raises a ValueError if modifications are made
    to a manifest without changing the version string identifier.

    Args:
        manifest_v2: A test fixture providing a baseline v2 (1.0.1) config state.
        project_config: A test fixture providing global project configuration fields.
        changelog_v2: Pre-existing history that is already at version 1.0.1.
    """
    silent_logger = Logger(min_terminal_level="emergency")
    changelog_engine = Changelog(raw_text=changelog_v2, logger=silent_logger)

    # SETUP: Load manifest_v2 (1.0.1) but alter a field to simulate a modification
    # without changing the version string away from 1.0.1
    raw_manifest_data = yaml.safe_load(manifest_v2)
    raw_manifest_data["description"] = "A brand new modified description text rule."

    config_modified = RepositoryManifest(raw_data=raw_manifest_data, logger=silent_logger).config
    project_config_dvo = ProjectManifest(
        raw_data=yaml.safe_load(project_config), logger=silent_logger
    ).config

    # ASSERTION: The loop must throw an exception to protect against duplicate headers
    with pytest.raises(ValueError, match="Manifest modified without version bump"):
        changelog_engine.generate_next_version(
            config=config_modified,
            project_config=project_config_dvo
        )


def test_changelog_calculates_modified_os_mapping_property_deltas(
    manifest_v1: str,
    project_config: str,
    changelog_v1: str,
) -> None:
    """Verifies that the engine detects and documents altered fields inside os_mappings.

    Args:
        manifest_v1: A test fixture providing a baseline configuration state.
        project_config: A test fixture providing global project configuration fields.
        changelog_v1: An existing history that has progressed forward to v1.0.0.
    """
    silent_logger = Logger(min_terminal_level="emergency")
    changelog_engine = Changelog(raw_text=changelog_v1, logger=silent_logger)

    # SETUP: Alter 'set_codename' for index 0 and bump version to pass downgrade checks
    raw_manifest_data = yaml.safe_load(manifest_v1)
    raw_manifest_data["os_mappings"]["pop|linuxmint"]["codename"] = "noble"
    raw_manifest_data["version"] = "1.0.1"

    config_v2 = RepositoryManifest(raw_data=raw_manifest_data, logger=silent_logger).config
    project_config_dvo = ProjectManifest(
        raw_data=yaml.safe_load(project_config), logger=silent_logger
    ).config

    # EXECUTION: Run the dynamic diff generation loop pass
    compiled_output = changelog_engine.generate_next_version(
        config=config_v2,
        project_config=project_config_dvo,
        current_time="Mon, 10 Aug 2026 13:00:00 +0000"
    )

    # ASSERTION: Engine must compute the internal rule change bullet lines successfully
    assert "Modified os_mappings rule matching pop|linuxmint" in compiled_output
    assert "codename=noble" in compiled_output

def test_changelog_reconstructs_static_keyring_toggle_from_text() -> None:
    """Verifies that the engine extracts static keyring toggles from text."""
    silent_logger = Logger(min_terminal_level="emergency")

    mock_history = (
        "test-repo (1.0.1) stable; urgency=medium\n\n"
        "  * Updated version to 1.0.1\n"
        "  * Toggled repository keyring strategy to: static\n\n"
        " -- Alice <alice@example.com>  Mon, 10 Aug 2026 13:00:00 +0000"
    )

    engine = Changelog(raw_text=mock_history, logger=silent_logger)
    config = engine.to_package_config()
    assert config.dynamic_keyring is False

def test_changelog_calculates_modified_os_mapping_distro_property_deltas(
    manifest_v1: str,
    project_config: str,
    changelog_v1: str,
) -> None:
    """Verifies that the engine detects altered distro fields in os_mappings."""
    silent_logger = Logger(min_terminal_level="emergency")
    changelog_engine = Changelog(raw_text=changelog_v1, logger=silent_logger)

    raw_manifest_data = yaml.safe_load(manifest_v1)
    # Alter distro instead of codename to hit the missing line branch path
    raw_manifest_data["os_mappings"]["pop|linuxmint"]["distro"] = "debian-custom"
    raw_manifest_data["version"] = "1.0.1"


    config_v2 = RepositoryManifest(raw_data=raw_manifest_data, logger=silent_logger).config
    project_config_dvo = ProjectManifest(
        raw_data=yaml.safe_load(project_config), logger=silent_logger
    ).config

    compiled_output = changelog_engine.generate_next_version(
        config=config_v2,
        project_config=project_config_dvo,
        current_time="Mon, 10 Aug 2026 13:00:00 +0000"
    )

    assert "Modified os_mappings rule matching pop|linuxmint" in compiled_output
    assert "distro=debian-custom" in compiled_output
