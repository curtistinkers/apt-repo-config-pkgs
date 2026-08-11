# tests/test_unit_manifest.py
"""RepositoryManifest unit tests."""

import pytest
import yaml

from package_generator import Logger, RepositoryManifest


@pytest.mark.parametrize(
    "missing_key,expected_error",
    [
        ("description", "Mandatory root key 'description' is missing"),
        ("copyright_year", "Mandatory root key 'copyright_year' is missing"),
        ("suites", "Mandatory repo child key 'suites' is missing"),
        ("set_codename", "Mandatory mapping child key 'set_codename' is missing"),
    ]
)
def test_manifest_invalid_schema_fixture_fails_validation(
    manifest_invalid_schema: str,
    missing_key: str,
    expected_error: str
) -> None:
    """Verifies manifest schema failures using the invalid layout fixture.

    Verifies that the RepositoryManifest validator catches every missing
    mandatory field inside the manifest_invalid_schema fixture.

    TODO: Add Args
    """
    raw_data = yaml.safe_load(manifest_invalid_schema)

    # Progressively patch required variables *forward* to isolate the next guard rail
    if missing_key != "description":
        raw_data["description"] = "Valid description."
    if missing_key not in ["description", "copyright_year"]:
        raw_data["copyright_year"] = 2026
    if missing_key not in ["description", "copyright_year", "suites"]:
        raw_data["repo"]["suites"] = "stable"
        raw_data["repo"]["components"] = "main"
        raw_data["repo"]["key_url"] = "https://example.com"

    # Initialize a real, quiet logger dependency
    silent_logger = Logger(min_terminal_level="emergency")

    with pytest.raises(ValueError) as error_context:
        RepositoryManifest(raw_data=raw_data, logger=silent_logger)

    assert expected_error in str(error_context.value)


def test_repository_manifest_compiles_valid_dvo_hierarchy(manifest_v1: str) -> None:
    """TODO: Needs a single-line description.

    Verifies that the RepositoryManifest validator accepts a complete configuration,
    executes all schema checks, and compiles a nested, type-safe PackageConfig DVO.

    Args:
        manifest_v1 (str): A test fixture providing a valid raw manifest YAML string.
    """
    # Safely parse our raw YAML string fixture into a primitive dictionary
    raw_input_data = yaml.safe_load(manifest_v1)

    # Initialize a real, quiet logger dependency
    silent_logger = Logger(min_terminal_level="emergency")

    # Instantiating the manifest drives coverage down the compilation loops
    manifest = RepositoryManifest(raw_data=raw_input_data, logger=silent_logger)

    # 3. COMPREHENSIVE VALUATION ASSERTIONS: Verify all data fields mapped cleanly
    assert manifest.config.name == "test-repo"
    assert manifest.config.version == "1.0.0"
    assert manifest.config.copyright_year == 2024
    assert manifest.config.dynamic_keyring is False

    # Check that nested child repository hosting fields are perfectly preserved
    assert manifest.config.repo.url == "https://example.com"
    assert manifest.config.repo.suites == "${TARGET_CODENAME}"
    assert manifest.config.repo.components == "main"
    assert manifest.config.repo.key_url == "https://example.com/signing.gpg"

    # Check that individual operating system collection mapping DVOs track accurately
    assert len(manifest.config.os_mappings) == 2
    assert manifest.config.os_mappings[0].match == "pop|linuxmint"
    assert manifest.config.os_mappings[0].set_dist == "ubuntu"
    assert manifest.config.os_mappings[0].set_codename == "${UBUNTU_CODENAME}"
    assert manifest.config.os_mappings[1].match == "raspbian"
    assert manifest.config.os_mappings[1].set_dist == "debian"
    assert manifest.config.os_mappings[1].set_codename == "${VERSION_CODENAME}"

    assert not manifest.config.os_mappings[0].match == "fake_flavor"
    assert not manifest.config.os_mappings[0].set_dist == "fake_distro"
    assert not manifest.config.os_mappings[0].set_codename == "${FAKE_VARIABLE}"


def test_manifest_rejects_non_dictionary_repo_block(manifest_invalid_repo_type: str) -> None:
    """Verifies the validator catches a 'repo' key declared as a flat string type.

    Args:
        manifest_invalid_repo_type (str): A test fixture providing an invalid manifest YAML string.
    """
    raw_data = yaml.safe_load(manifest_invalid_repo_type)

    # Initialize a real, quiet logger dependency
    silent_logger = Logger(min_terminal_level="emergency")

    with pytest.raises(ValueError) as error_context:
        RepositoryManifest(raw_data=raw_data, logger=silent_logger)

    assert "Mandatory child block 'repo' is missing or invalid" in str(error_context.value)


def test_manifest_rejects_non_list_os_mappings_block(manifest_invalid_mappings_type: str) -> None:
    """Verifies the validator catches an 'os_mappings' key declared as a flat string type.

    Args:
        manifest_invalid_mappings_type (str): A test fixture providing an invalid manifest
            YAML string.
    """
    raw_data = yaml.safe_load(manifest_invalid_mappings_type)

    # Initialize a real, quiet logger dependency
    silent_logger = Logger(min_terminal_level="emergency")

    with pytest.raises(ValueError) as error_context:
        RepositoryManifest(raw_data=raw_data, logger=silent_logger)

    assert "'os_mappings' must be a valid array list structure" in str(error_context.value)


def test_manifest_rejects_non_dictionary_os_mapping_item(
    manifest_invalid_mapping_item_type: str
) -> None:
    """Verifies the validator catches an individual os_mappings item formatted as a flat string.

    Args:
        manifest_invalid_mapping_item_type (str): A test fixture providing an invalid manifest
            YAML string.
    """
    raw_data = yaml.safe_load(manifest_invalid_mapping_item_type)

    # Initialize a real, quiet logger dependency
    silent_logger = Logger(min_terminal_level="emergency")

    with pytest.raises(ValueError) as error_context:
        RepositoryManifest(raw_data=raw_data, logger=silent_logger)

    assert "must be a dictionary" in str(error_context.value)

