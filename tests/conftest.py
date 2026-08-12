# tests/conftest.py
"""Testing fixtures.

Global configuration file and shared test fixtures for the pytest framework.
This file configures environment overrides and cross-platform paths for tests.
"""

import sys

import pytest


# Ensure our Python testing environment can seamlessly see and import modules
# from the root folder where our main generation engine will live.
sys.path.insert(0, ".")


@pytest.fixture
def project_config() -> str:
    """Provides a valid raw global project configuration YAML text string.

    Returns:
        A multiline YAML string representing a project config file.
    """
    return """maintainer_name: Alice
maintainer_email: alice@example.com
copyright_holder: Alice
repository_url: https://git.example.com/alice/deb-repo-config-packages
"""

@pytest.fixture
def project_config_multiple_missing() -> str:
    """Provides an invalid raw project configuration missing maintainer_name and repository_url."""
    return """maintainer_email: "bob@example.com"
copyright_holder: "Bob"
"""


@pytest.fixture
def manifest_v1() -> str:
    """Complete mock YAML configuration.

    A shared fixture providing a standard, mock YAML configuration. This simulates a valid vendor
    configuration file for testing processors.

    Returns:
        A multiline YAML string representing a standard manifest.
    """
    return """name: test-repo
version: 1.0.0
description: Test repository package layout configuration.
copyright_year: 2024
dynamic_keyring: false
repo:
  url: https://example.com
  suites: ${TARGET_CODENAME}
  components: main
  key_url: https://example.com/signing.gpg
os_mappings:
  - match: pop|linuxmint
    set_dist: ubuntu
    set_codename: ${UBUNTU_CODENAME}
  - match: raspbian
    set_dist: debian
    set_codename: ${VERSION_CODENAME}
"""


@pytest.fixture
def changelog_v1() -> str:
    """Lintian-compliant initial Genesis changelog text block.

    Returns:
        str: A multiline string representing a changelog.
    """
    return """test-repo (1.0.0) stable; urgency=medium

  * Initial package definition established.
  * description=Test repository package layout configuration.
  * copyright_year=2024
  * dynamic_keyring=false
  * repo.url=https://example.com
  * repo.suites=${TARGET_CODENAME}
  * repo.components=main
  * repo.key_url=https://example.com/signing.gpg
  * os_mappings.0.match=pop|linuxmint
  * os_mappings.0.set_dist=ubuntu
  * os_mappings.0.set_codename=${UBUNTU_CODENAME}
  * os_mappings.1.match=raspbian
  * os_mappings.1.set_dist=debian
  * os_mappings.1.set_codename=${VERSION_CODENAME}

 -- Alice <alice@example.com>  Mon, 10 Aug 2026 12:00:00 +0000
"""


@pytest.fixture
def manifest_v2() -> str:
    """Complete mock YAML configuration with version bump.

    Provides a mock YAML configuration string representing a version 1.0.1 bump.
    This lifecycle state alters the vendor URL string and description parameters
    while preserving the background background array layouts.

    Returns:
        str: A raw, multiline YAML string representing the v2 repository configuration.
    """
    return """name: test-repo
version: 1.0.1
description: Altered test repository package layout configuration.
copyright_year: 2024
dynamic_keyring: false
repo:
  url: https://v2.example.com
  suites: ${TARGET_CODENAME}
  components: main
  key_url: https://v2.example.com/signing.gpg
os_mappings:
  - match: pop|linuxmint
    set_dist: ubuntu
    set_codename: ${UBUNTU_CODENAME}
  - match: raspbian
    set_dist: debian
    set_codename: ${VERSION_CODENAME}
"""


@pytest.fixture
def changelog_v2(changelog_v1: str) -> str:
    """Cumulative v1 & v2 changleog fixture.

    Assembles a historical cumulative changelog string for version 1.0.1.
    This injects the human-readable parameter modification bullets and
    stacks the previous v1 release text block chronologically at the bottom.

    Args:
        changelog_v1: The initial Genesis version changelog string asset.

    Returns:
        str: A multi-block changelog string tracking versions 1.0.1 and 1.0.0.
    """
    return f"""test-repo (1.0.1) stable; urgency=medium

  * Updated version to 1.0.1
  * Modified description: Altered test repository package layout configuration.
  * Modified repo.url: https://v2.example.com
  * Modified repo.key_url: https://v2.example.com/signing.gpg

 -- Alice <alice@example.com>  Mon, 10 Aug 2026 13:00:00 +0000

{changelog_v1.strip()}
"""

@pytest.fixture
def manifest_v3() -> str:
    """Provides a mock YAML configuration string representing a version 1.0.2 bump.

    This lifecycle state switches the keyring to dynamic installation mode and
    removes the second index rule from the os_mappings array layout.

    Returns:
        str: A raw, multiline YAML string representing the v3 repository configuration.
    """
    return """name: test-repo
version: 1.0.2
description: Altered test repository package layout configuration.
copyright_year: 2024
dynamic_keyring: true
repo:
  url: https://v2.example.com
  suites: ${TARGET_CODENAME}
  components: main
  key_url: https://v2.example.com/signing.gpg
os_mappings:
  - match: pop|linuxmint
    set_dist: ubuntu
    set_codename: ${UBUNTU_CODENAME}
"""


@pytest.fixture
def changelog_v3(changelog_v2: str) -> str:
    """Cumulative v1, v2 & v3 changleog fixture.

    Assembles the final cumulative master changelog text layout for version 1.0.2.
    This tracks a partial array removal by explicitly naming the match value
    of the deleted rule, ensuring index stability across future updates.

    Args:
        changelog_v2: The cumulative historical v2 version changelog string asset.

    Returns:
        A multi-block changelog string tracking versions 1.0.2, 1.0.1, and 1.0.0.
    """
    return f"""test-repo (1.0.2) stable; urgency=medium

  * Updated version to 1.0.2
  * Toggled repository keyring strategy to: dynamic
  * Removed os_mappings rule matching raspbian.

 -- Alice <alice@example.com>  Mon, 10 Aug 2026 14:00:00 +0000

{changelog_v2.strip()}
"""

@pytest.fixture
def manifest_invalid_schema() -> str:
    """Malformed YAML fixture.

    Provides a malformed YAML configuration string missing mandatory parameters
    such as 'description' and most of the 'repo' dictionary structure.

    Returns:
        str: A raw, invalid multiline YAML string for schema verification.
    """
    return """name: broken-repo
version: 1.0.0
repo:
  url: https://invalid.example.com
os_mappings:
  - match: pop
    set_dist: ubuntu
"""


@pytest.fixture
def manifest_invalid_repo_type() -> str:
    """A manifest layout where the repo key is a raw string instead of a dictionary."""
    return """name: broken-repo
version: 1.0.0
description: Testing invalid repo dictionary type guard.
copyright_year: 2026
repo: "this_should_be_a_dictionary_but_is_a_string"
"""


@pytest.fixture
def manifest_invalid_mappings_type() -> str:
    """A manifest layout where os_mappings is a string instead of a bulleted array list."""
    return """name: broken-repo
version: 1.0.0
description: Testing invalid mappings array list type guard.
copyright_year: 2026
repo:
  url: https://bad-fixture.example.com
  suites: stable
  components: main
  key_url: https://bad-fixture.example.com/keyring.gpg
os_mappings: "this_should_be_a_list_but_is_a_string"
"""


@pytest.fixture
def manifest_invalid_mapping_item_type() -> str:
    """A manifest layout where an os_mappings item is a flat string instead of a sub-dictionary."""
    return """name: broken-repo
version: 1.0.0
description: Testing invalid individual mapping item block type guard.
copyright_year: 2026
repo:
  url: https://bad-fixture.example.com
  suites: stable
  components: main
  key_url: https://bad-fixture.example.com/keyring.gpg
os_mappings:
  - "flat_string_bullet_item_instead_of_dictionary"
  - "second_flat_string_bullet_item_instead_of_dictionary"
"""

@pytest.fixture
def manifest_corrupted_garbage_syntax() -> str:
    """Provides a completely corrupted raw string text layout that violates YAML syntax."""
    return """name: unparseable-package
version: 1.0.0
this is invalid un-indented garbage text layout lines that will break the parser structure { [ !!
"""

@pytest.fixture
def mock_project_config_template() -> str:
    """Provides a valid raw global project configuration YAML text string.

    Returns:
        A multiline YAML string representing a project config file.
    """
    return """maintainer_name: {{ maintainer_name }}
maintainer_email: {{ maintainer_email}}
copyright_holder: {{ copyright_holder }}
repository_url: {{ repository_url }}

"""

@pytest.fixture
def mock_manifest_template() -> str:
    """Provides a token-matching template layout mirroring manifest_v1 exactly.

    Returns:
        A multiline YAML string representing a repository configuration file.
    """
    return """name: {{ package_name }}
version: {{ version }}
description: {{ short_description }}
copyright_year: {{ copyright_year }}
dynamic_keyring: {% if dynamic_keyring %}true{% else %}false{% endif %}
repo:
  url: {{ repo_url }}
  suites: {{ repo_suites }}
  components: {{ repo_components }}
  key_url: {{ repo_key_url }}
os_mappings:
{%- for mapping in os_mappings %}
  - match: {{ mapping.match }}
    set_dist: {{ mapping.set_dist }}
    set_codename: {{ mapping.set_codename }}
{%- endfor %}

"""
