# tests/test_unit_models.py
"""Data models unit tests.

Atomic unit specifications validating the structural contracts and immutability
constraints of each individual Data Value Object (DVO) in the OOP engine.
"""

from dataclasses import FrozenInstanceError

import pytest

from package_generator import (
    PackageConfig,
    PackageOSMappingConfig,
    PackageRepoConfig,
    ProjectConfig,
)


# ==============================================================================
# DISCRETE TESTS FOR: ProjectConfig
# ==============================================================================
def test_project_config_stores_attributes_correctly() -> None:
    """Verifies ProjectConfig successfully maps and holds its core fields."""
    config = ProjectConfig(
        maintainer_name="Alice",
        maintainer_email="alice@example.com",
        copyright_holder="Alice",
        repository_url="https://example.com/alice/deb-repo-config-packages"
    )
    assert config.maintainer_name == "Alice"
    assert config.maintainer_email == "alice@example.com"
    assert config.copyright_holder == "Alice"
    assert config.repository_url == "https://example.com/alice/deb-repo-config-packages"


def test_project_config_is_strictly_immutable() -> None:
    """Guarantees ProjectConfig blocks runtime modifications to its fields."""
    config = ProjectConfig(
        maintainer_name="Alice",
        maintainer_email="alice@example.com",
        copyright_holder="Alice",
        repository_url="https://example.com/alice/deb-repo-config-packages"
    )
    with pytest.raises(FrozenInstanceError):
        config.maintainer_name = "Bob"  # type: ignore
        config.maintainer_email = "bob@example.com"  # type: ignore
        config.maintainer_name = "Bob"  # type: ignore
        config.repository_url = "https://example.com/bob/deb-repo-config-packages"  # type: ignore


# ==============================================================================
# DISCRETE TESTS FOR: PackageRepoConfig
# ==============================================================================
def test_package_repo_config_stores_attributes_correctly() -> None:
    """Verifies PackageRepoConfig successfully maps and holds its hosting fields."""
    repo = PackageRepoConfig(
        url="https://apt.example.com/linux/${TARGET_DIST}",
        suites="trixie",
        components="main",
        key_url="https://apt.example.com/keyring.gpg"
    )

    assert repo.url == "https://apt.example.com/linux/${TARGET_DIST}"
    assert repo.suites == "trixie"
    assert repo.components == "main"
    assert repo.key_url == "https://apt.example.com/keyring.gpg"


def test_package_repo_config_is_strictly_immutable() -> None:
    """Guarantees PackageRepoConfig blocks runtime mutations."""
    repo = PackageRepoConfig(
        url="https://apt.example.com/linux/${TARGET_DIST}",
        suites="trixie",
        components="main",
        key_url="https://apt.example.com/keyring.gpg"
    )

    with pytest.raises(FrozenInstanceError):
        repo.url = "https://mutated.example.com/linux/${TARGET_DIST}"  # type: ignore
        repo.suites = "sid"  # type: ignore
        repo.components = "stable"  # type: ignore
        repo.key_url = "https://mutated.example.com/keyring.gpg"  # type: ignore


# ==============================================================================
# DISCRETE TESTS FOR: PackageOSMappingConfig
# ==============================================================================
def test_package_os_mapping_config_stores_attributes_correctly() -> None:
    """Verifies PackageOSMappingConfig successfully maps normalization items."""
    mapping = PackageOSMappingConfig(
        distro="ubuntu",
        codename="${UBUNTU_CODENAME}"
    )

    assert mapping.distro == "ubuntu"
    assert mapping.codename == "${UBUNTU_CODENAME}"


def test_package_os_mapping_config_is_strictly_immutable() -> None:
    """Guarantees PackageOSMappingConfig blocks runtime mutations."""
    mapping = PackageOSMappingConfig(
        distro="ubuntu",
        codename="${UBUNTU_CODENAME}"
    )

    with pytest.raises(FrozenInstanceError):
        mapping.distro = "debian"  # pyright: ignore[reportAttributeAccessIssue]
        mapping.codename = "${VERSION_CODENAME}"  # pyright: ignore[reportAttributeAccessIssue]


# ==============================================================================
# DISCRETE TESTS FOR: PackageConfig (The Master Composition Tree)
# ==============================================================================

def test_package_config_compiles_nested_tree_structures_correctly() -> None:
    """Verifies PackageConfig cleanly maps nested compound child relationships."""
    repo = PackageRepoConfig(
        url="https://apt.example.com/linux/${TARGET_DIST}",
        suites="trixie",
        components="main",
        key_url="https://apt.example.com/keyring.gpg"
    )

    mapping_dict = {
        "pop|linuxmint": PackageOSMappingConfig(
            distro="ubuntu",
            codename="${UBUNTU_CODENAME}"
        ),
        "raspbian": PackageOSMappingConfig(
            distro="debian",
            codename="${VERSION_CODENAME}"
        )
    }

    pkg = PackageConfig(
        name="test-package",
        version="1.0.0",
        description="A sample package layout.",
        copyright_year=2026,
        dynamic_keyring=False,
        repo=repo,
        os_mappings=mapping_dict
    )

    assert pkg.name == "test-package"
    assert pkg.copyright_year == 2026
    assert pkg.dynamic_keyring is False
    assert pkg.repo.url == "https://apt.example.com/linux/${TARGET_DIST}"
    assert pkg.repo.suites == "trixie"
    assert pkg.repo.components == "main"
    assert pkg.repo.key_url == "https://apt.example.com/keyring.gpg"
    assert not len(pkg.os_mappings) == 1
    assert pkg.os_mappings['pop|linuxmint'].distro == "ubuntu"
    assert pkg.os_mappings['pop|linuxmint'].codename == "${UBUNTU_CODENAME}"
    assert pkg.os_mappings['raspbian'].distro == "debian"
    assert pkg.os_mappings['raspbian'].codename == "${VERSION_CODENAME}"


def test_package_config_tree_is_completely_frozen() -> None:
    """Guarantees the nested PackageConfig structure is locked down."""
    repo = PackageRepoConfig(url="a", suites="b", components="c", key_url="d")
    mapping_dict = {"x": PackageOSMappingConfig(distro="y", codename="z")}
    pkg = PackageConfig(
        name="test-package",
        version="1.0.0",
        description="A sample package layout.",
        copyright_year=2026,
        dynamic_keyring=False,
        repo=repo,
        os_mappings=mapping_dict
    )

    repo_mutated = PackageRepoConfig(url="e", suites="f", components="g", key_url="f")
    mapping_mutated = {"u": PackageOSMappingConfig(distro="v", codename="w")}

    with pytest.raises(FrozenInstanceError):
        pkg.name = "mutated-package"  # type: ignore
        pkg.version = "1.0.1"  # type: ignore
        pkg.description = "A mutated package description."  # type: ignore
        pkg.copyright_year = "2024"  # type: ignore
        pkg.dynamic_keyring = True  # type: ignore
        pkg.repo = repo_mutated  # type: ignore
        pkg.os_mappings = [mapping_mutated]  # type: ignore
