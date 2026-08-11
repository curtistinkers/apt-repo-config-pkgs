# package_generator/models.py
"""
package_generator.models
========================
Pure, immutable Data Value Objects representing our package and project parameters.
"""

from dataclasses import dataclass, field
from typing import List

@dataclass(frozen=True)
class ProjectConfig:
    """
    An immutable Data Value Object representing general parameters used amongst
    all packages.
    """
    maintainer_name: str
    maintainer_email: str
    copyright_holder: str
    repository_url: str


@dataclass(frozen=True)
class PackageConfig:
    """
    The master immutable Data Value Object representing the complete
    configuration state of a repository manifest at a single point in time.
    """
    name: str
    version: str
    description: str
    copyright_year: int
    dynamic_keyring: bool
    repo: PackageRepoConfig  # <-- Nested structured value object type-hint
    os_mappings: List[PackageOSMappingConfig] = field(default_factory=list)  # <-- Strongly-typed collection


@dataclass(frozen=True)
class PackageRepoConfig:
    """
    An immutable Data Value Object representing the target repository hosting
    parameter specifications for a package.
    """
    url: str
    suites: str
    components: str
    key_url: str


@dataclass(frozen=True)
class PackageOSMappingConfig:
    """
    An immutable Data Value Object representing an individual operating system
    normalization rule used during installation orchestration.
    """
    match: str
    set_dist: str
    set_codename: str
