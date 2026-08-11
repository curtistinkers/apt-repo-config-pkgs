"""
tests/test_unit_builder.py
==========================
Discrete unit specifications validating the folder orchestration and file
generation layer managed by the DebianPackageBuilder class.
"""

from pathlib import Path
import yaml
import pytest
from package_generator import RepositoryManifest, DebianPackageBuilder

def test_builder_orchestrates_clean_package_directory_tree(
    tmp_path: Path,
    manifest_v1: str
) -> None:
    """
    Verifies that DebianPackageBuilder uses a compiled PackageConfig DVO
    to orchestrate the required debian/ source directories on disk.
    """
    # 1. SETUP: Prepare our inputs and output paths in our sandbox
    raw_data = yaml.safe_load(manifest_v1)
    manifest = RepositoryManifest(raw_data=raw_data)

    # Define our temporary sources sandbox output folder
    sources_dir = tmp_path / "dpkg-sources"

    # Instantiate our new infrastructure builder class
    builder = DebianPackageBuilder(sources_dir=sources_dir)

    # 2. EXECUTION: Run the target folder orchestration method
    target_debian_dir = builder.create_package_tree(manifest.config)

    # 3. ASSERTIONS: Verify the physical directory path exists matching the schema
    expected_path = sources_dir / "test-repo" / "debian"

    assert target_debian_dir == expected_path
    assert target_debian_dir.exists(), "The builder failed to physically create the directory tree."
    assert target_debian_dir.is_dir(), "The target destination path is not a valid directory."

def test_builder_successfully_removes_sources_directory_tree(tmp_path: Path) -> None:
    """
    Verifies that the package builder can safely delete an entire
    generated directory tree structure from the filesystem.
    """
    # 1. SETUP: Create a real temporary folder structure to be deleted
    mock_sources_dir = tmp_path / "dpkg-sources"
    mock_package_dir = mock_sources_dir / "test-repo" / "debian"
    mock_package_dir.mkdir(parents=True)

    # Write a dummy file inside it to ensure the builder handles non-empty folders
    (mock_package_dir / "dummy_file.txt").write_text("hello", encoding="utf-8")

    # Instantiate our infrastructure builder targeting this sandbox folder
    builder = DebianPackageBuilder(sources_dir=mock_sources_dir)

    # Double-check that our setup worked and the path physically exists before cleaning
    assert mock_sources_dir.exists()

    # 2. EXECUTION: Run the upcoming cleanup method
    builder.remove_package_tree()

    # 3. ASSERTION: The entire directory tree must be completely purged from disk
    assert not mock_sources_dir.exists(), "The builder failed to delete the target directory tree."
