# tests/test_unit_project_manifest.py
"""ProjectManifest unit tests."""

import pytest
import yaml

from package_generator import Logger, ProjectManifest


@pytest.fixture
def project_config_v1() -> str:
    """Provides a valid raw global project configuration YAML text string."""
    return """maintainer_name: "Alice"
maintainer_email: "alice@example.com"
copyright_holder: "Alice"
repository_url: "https://example.com"
"""


@pytest.fixture
def project_config_invalid() -> str:
    """Provides an invalid raw project configuration missing the maintainer name."""
    return """maintainer_email: "alice@example.com"
copyright_holder: "Alice"
repository_url: "https://example.com"
"""


def test_project_manifest_compiles_valid_dvo_hierarchy(project_config: str) -> None:
    """Verifies that a valid project configuration compiles cleanly into a DVO tree.

    Args:
        project_config: Test fixture providing a valid raw project YAML string.
    """
    raw_input_data = yaml.safe_load(project_config)
    silent_logger = Logger(min_terminal_level="emergency")

    # Instantiate our upcoming validator and translation class
    manifest = ProjectManifest(raw_data=raw_input_data, logger=silent_logger)

    # Verify that data properties mapped cleanly onto our frozen ProjectConfig DVO
    assert manifest.config.maintainer_name == "Alice"
    assert manifest.config.maintainer_email == "alice@example.com"
    assert manifest.config.copyright_holder == "Alice"
    assert manifest.config.repository_url == "https://git.example.com/alice/deb-repo-config-packages"


def test_project_manifest_rejects_missing_mandatory_keys(
    project_config_multiple_missing: str
) -> None:
    """Verifies that the validator catches missing required global configuration fields.

    Args:
        project_config_multiple_missing: Test fixture providing an invalid raw project YAML string.
    """
    raw_input_data = yaml.safe_load(project_config_multiple_missing)

    silent_logger = Logger(min_terminal_level="emergency")

    with pytest.raises(ValueError) as error_context:
        ProjectManifest(raw_data=raw_input_data, logger=silent_logger)

    assert "Mandatory global key 'maintainer_name' is missing" in str(error_context.value)
    assert "Mandatory global key 'repository_url' is missing" in str(error_context.value)
