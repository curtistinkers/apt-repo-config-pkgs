# tests/test_unit_builder.py
"""DebianProjectBuilder unit tests.

Discrete unit specifications validating the folder orchestration and file
generation layer managed by the DebianPackageBuilder class.
"""

from pathlib import Path

import yaml

from package_generator import DebianPackageBuilder, Logger, RepositoryManifest


def test_builder_orchestrates_clean_package_directory_tree(
    tmp_path: Path,
    manifest_v1: str
) -> None:
    """Verifies source tree directory orchestration.

    Ensures that DebianPackageBuilder uses a PackageConfig to create
    debian/ source directories on disk.

    Args:
        tmp_path (Path): A built-in pytest fixture providing a temporary directory path.
        manifest_v1 (str): A test fixture providing a valid raw manifest YAML string.
    """
    # Prepare our inputs and output paths in our sandbox
    raw_data = yaml.safe_load(manifest_v1)

    # Initialize a real logger, configured to be completely quiet
    silent_logger = Logger(min_terminal_level="emergency")

    # Pass the required silent_logger into the RepositoryManifest constructor
    manifest = RepositoryManifest(raw_data=raw_data, logger=silent_logger)

    # Define our temporary sources sandbox output folder
    sources_dir = tmp_path / "dpkg-sources"

    # Instantiate our new infrastructure builder class
    builder = DebianPackageBuilder(sources_dir=sources_dir, logger=silent_logger)

    # 2. EXECUTION: Run the target folder orchestration method
    target_debian_dir = builder.create_package_tree(manifest.config)

    # 3. ASSERTIONS: Verify the physical directory path exists matching the schema
    expected_path = sources_dir / "test-repo" / "debian"

    assert target_debian_dir == expected_path
    assert target_debian_dir.exists(), "The builder failed to physically create the directory tree."
    assert target_debian_dir.is_dir(), "The target destination path is not a valid directory."

def test_builder_successfully_removes_sources_directory_tree(tmp_path: Path) -> None:
    """Verifies source tree directory removal.

    Ensures that the package builder can safely delete an entire generated
    directory tree structure from the filesystem.

    Args:
        tmp_path (Path): A built-in pytest fixture providing a temporary directory path.
    """
    # Create a real temporary folder structure to be deleted
    sources_dir = tmp_path / "dpkg-sources"
    sources_dir.mkdir(parents=True)
    package_dir = sources_dir / "test-repo" / "debian"
    package_dir.mkdir(parents=True)

    # Write a dummy file inside it to ensure the builder handles non-empty folders
    (package_dir / "dummy_file.txt").write_text("hello", encoding="utf-8")

    # Initialize a real logger, configured to be completely quiet during our test run
    silent_logger = Logger(min_terminal_level="emergency")

    # Instantiate our new infrastructure builder class
    builder = DebianPackageBuilder(sources_dir=sources_dir, logger=silent_logger)

    # Double-check that our setup worked and the path physically exists before cleaning
    assert sources_dir.exists()

    # 2. EXECUTION: Run the upcoming cleanup method
    builder.remove_package_tree()

    # 3. ASSERTION: The entire directory tree must be completely purged from disk
    assert not sources_dir.exists(), "The builder failed to delete the target directory tree."
