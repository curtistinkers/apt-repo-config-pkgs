# src/package_generator/__init__.py
"""Core entry-point exposing public class structures."""

from .builder import DebianPackageBuilder
from .changelog import Changelog
from .compiler import DebianTemplateCompiler
from .downloader import Downloader
from .gpg import GpgEngine
from .logger import Logger
from .models import PackageConfig, PackageOSMappingConfig, PackageRepoConfig, ProjectConfig
from .project_manifest import ProjectManifest
from .repository_manifest import RepositoryManifest


__all__ = [
    "DebianPackageBuilder",
    "Changelog",
    "DebianTemplateCompiler",
    "Downloader",
    "GpgEngine",
    "Logger",
    "RepositoryManifest",
    "PackageConfig",
    "PackageOSMappingConfig",
    "PackageRepoConfig",
    "ProjectConfig",
    "ProjectManifest",
]
