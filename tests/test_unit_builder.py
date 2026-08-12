# tests/test_unit_builder.py
"""DebianProjectBuilder unit tests.

Discrete unit specifications validating the folder orchestration and file
generation layer managed by the DebianPackageBuilder class.
"""

from pathlib import Path

import pytest
import yaml

from package_generator import (
    DebianPackageBuilder,
    DebianTemplateCompiler,
    Logger,
    ProjectManifest,
    RepositoryManifest,
)


def test_builder_orchestrates_clean_package_directory_tree(
    tmp_path: Path,
    manifest_v1: str,
    project_config: str,
) -> None:
    """Verifies source tree directory and file compilation orchestration.

    Ensures that DebianPackageBuilder scans the templates directory, uses a
    PackageConfig and ProjectConfig to create debian/ source structures, and
    physically writes out all compiled configuration files onto disk.

    Args:
        tmp_path: A built-in pytest fixture providing a temporary directory path.
        manifest_v1: A test fixture providing a valid raw manifest YAML string.
        project_config: A test fixture providing a valid raw project YAML string.
    """
    # 1. SETUP: Prepare our compiled domain data configurations and dependencies
    silent_logger = Logger(min_terminal_level="emergency")

    raw_manifest_data = yaml.safe_load(manifest_v1)
    manifest = RepositoryManifest(raw_data=raw_manifest_data, logger=silent_logger)

    # FIX: Use our new ProjectManifest class natively to compile the project DVO
    raw_project_data = yaml.safe_load(project_config)
    project_manifest = ProjectManifest(raw_data=raw_project_data, logger=silent_logger)

    # Locate our real templates directory root
    templates_dir = Path(__file__).parents[1] / "templates" / "debian"
    compiler = DebianTemplateCompiler(templates_dir=templates_dir, logger=silent_logger)

    # Define our temporary sources sandbox output folder
    sources_dir = tmp_path / "dpkg-sources"

    # Inject BOTH the logger and the template compiler into the builder constructor
    builder = DebianPackageBuilder(
        sources_dir=sources_dir,
        logger=silent_logger,
        compiler=compiler,
    )

    # 2. EXECUTION: Pass both configuration DVOs to drive the compilation loop pass
    target_debian_dir = builder.create_package_tree(
        config=manifest.config,
        project_config=project_manifest.config,
    )

    # 3. ASSERTIONS: Verify the physical directory path exists matching the schema
    expected_path = sources_dir / "test-repo" / "debian"
    assert target_debian_dir == expected_path
    assert target_debian_dir.exists()

    # Verify that the builder dynamically looped through the template folder
    # and generated all target configuration files onto the platter
    mandatory_files = ["control", "rules"]
    for filename in mandatory_files:
        expected_file = target_debian_dir / filename
        assert expected_file.exists(), f"The builder failed to generate file: {filename}"
        assert expected_file.read_text(encoding="utf-8").strip() != ""


def test_builder_successfully_removes_sources_directory_tree(tmp_path: Path) -> None:
    """Verifies source tree directory removal.

    Ensures that the package builder can safely delete an entire generated
    directory tree structure from the filesystem.

    Args:
        tmp_path: A built-in pytest fixture providing a temporary directory path.
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

    # Provide a placeholder compiler instance to fulfill the constructor signature contract
    templates_dir = Path(__file__).parents[1] / "templates" / "debian"
    compiler = DebianTemplateCompiler(templates_dir=templates_dir, logger=silent_logger)

    # Instantiate our builder infrastructure class
    builder = DebianPackageBuilder(
        sources_dir=sources_dir,
        logger=silent_logger,
        compiler=compiler,
    )

    # Double-check that our setup worked and the path physically exists before cleaning
    assert sources_dir.exists()

    # 2. EXECUTION: Run the upcoming cleanup method
    builder.remove_package_tree()

    # 3. ASSERTION: The entire directory tree must be completely purged from disk
    assert not sources_dir.exists(), "The builder failed to delete the target directory tree."

def test_builder_persists_and_increments_existing_changelog_on_disk(
    tmp_path: Path,
    manifest_v2: str,
    project_config: str,
    changelog_v1: str,
    changelog_v2: str,
) -> None:
    """Verifies that the builder reads an existing changelog to calculate deltas.

    Ensures that if a changelog file already exists in the target debian/ folder,
    the builder reverse-engineers its historical state, appends the new version
    delta entries, and overwrites the file non-destructively.

    Args:
        tmp_path: A built-in pytest fixture providing a temporary directory path.
        manifest_v2: A test fixture providing a bumped v2 manifest string.
        project_config: A test fixture providing a valid raw project YAML string.
        changelog_v1: The pre-existing historical changelog on the platter.
        changelog_v2: The expected cumulative final changelog output text stream.
    """
    # 1. SETUP: Prepare our sandbox, models, and pre-existing file on disk
    silent_logger = Logger(min_terminal_level="emergency")

    raw_manifest = yaml.safe_load(manifest_v2)
    manifest = RepositoryManifest(raw_data=raw_manifest, logger=silent_logger)

    raw_project = yaml.safe_load(project_config)
    project_manifest = ProjectManifest(raw_data=raw_project, logger=silent_logger)

    templates_dir = tmp_path / "templates" / "debian"
    templates_dir.mkdir(parents=True)
    # Write empty template placeholders so the builder can complete its execution loop
    (templates_dir / "control").write_text("", encoding="utf-8")
    (templates_dir / "rules").write_text("", encoding="utf-8")

    compiler = DebianTemplateCompiler(templates_dir=templates_dir, logger=silent_logger)
    sources_dir = tmp_path / "dpkg-sources"

    # Pre-seed the target debian/ tree with a real historical changelog file
    target_debian_dir = sources_dir / "test-repo" / "debian"
    target_debian_dir.mkdir(parents=True)
    existing_changelog_file = target_debian_dir / "changelog"
    existing_changelog_file.write_text(changelog_v1, encoding="utf-8")

    builder = DebianPackageBuilder(
        sources_dir=sources_dir,
        logger=silent_logger,
        compiler=compiler,
    )

    # 2. EXECUTION: Run the package directory tree compilation pass
    # We pass a fixed test timestamp override matching our changelog fixture requirements
    builder.create_package_tree(
        config=manifest.config,
        project_config=project_manifest.config,
        current_time="Mon, 10 Aug 2026 13:00:00 +0000",
    )

    # 3. ASSERTIONS: Verify the file on disk was incremented to v2 perfectly
    assert existing_changelog_file.exists()
    assert existing_changelog_file.read_text(encoding="utf-8").strip() == changelog_v2.strip()

def test_builder_throws_emergency_error_if_changelog_template_exists(
    tmp_path: Path,
    manifest_v1: str,
    project_config: str,
) -> None:
    """Verifies that the builder panics if a changelog file exists in templates.

    Args:
        tmp_path: A built-in pytest fixture providing a temporary directory path.
        manifest_v1: A test fixture providing a baseline manifest string.
        project_config: A test fixture providing a valid raw project YAML string.
    """
    silent_logger = Logger(min_terminal_level="emergency")

    raw_manifest = yaml.safe_load(manifest_v1)
    manifest = RepositoryManifest(raw_data=raw_manifest, logger=silent_logger)

    raw_project = yaml.safe_load(project_config)
    project_manifest = ProjectManifest(raw_data=raw_project, logger=silent_logger)

    templates_dir = tmp_path / "templates" / "debian"
    templates_dir.mkdir(parents=True)

    # SETUP: Violate the architecture by dropping a rogue changelog file into templates
    (templates_dir / "changelog").write_text("", encoding="utf-8")

    compiler = DebianTemplateCompiler(templates_dir=templates_dir, logger=silent_logger)
    sources_dir = tmp_path / "dpkg-sources"

    builder = DebianPackageBuilder(
        sources_dir=sources_dir,
        logger=silent_logger,
        compiler=compiler,
    )

    # ASSERTION: The builder must raise a ValueError and refuse to compile the tree
    with pytest.raises(ValueError, match="A template named 'changelog' was discovered"):
        builder.create_package_tree(
            config=manifest.config,
            project_config=project_manifest.config,
        )
