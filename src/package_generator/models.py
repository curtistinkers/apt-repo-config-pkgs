# src/package_generator/models.py
"""Pure, immutable Data Value Objects representing our package and project parameters."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProjectConfig:
    """General parameters used amongst all packages."""
    maintainer_name: str
    maintainer_email: str
    copyright_holder: str
    repository_url: str


@dataclass(frozen=True)
class PackageRepoConfig:
    """A target repository hosting parameter specifications for a package."""
    url: str
    suites: str
    components: str
    key_url: str


@dataclass(frozen=True)
class PackageOSMappingConfig:
    """A packages operating system normalization rule used during installation."""
    match: str
    set_dist: str
    set_codename: str


@dataclass(frozen=True)
class PackageConfig:
    """Complete configuration state of a repository manifest."""
    name: str
    version: str
    description: str
    copyright_year: int
    dynamic_keyring: bool
    repo: PackageRepoConfig  # <-- Nested structured value object type-hint
    os_mappings: list[PackageOSMappingConfig] = field(default_factory=list)

@dataclass(frozen=True)
class ChangelogEntry:
    """Represents a single parsed historical Debian changelog release block."""
    package_name: str
    version: str
    suite: str
    urgency: str
    changes: str
    timestamp: str
