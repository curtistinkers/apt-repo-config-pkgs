# tests/test_unit_compiler.py
"""DebianTemplateCompiler unit tests.

Discrete unit specifications validating the Jinja2 text compilation, variable
injection, and rendering boundaries managed by the DebianTemplateCompiler class.
"""

from pathlib import Path

import yaml

from package_generator import Logger, ProjectManifest, RepositoryManifest


def test_compiler_successfully_renders_template_variables(
    manifest_v1: str,
    project_config: str
) -> None:
    """Verifies Jinja2 data template rendering boundaries.

    Ensures that the compiler accepts strongly typed configuration inputs
    and compiles their properties cleanly into a text template string.

    Args:
        manifest_v1: A test fixture providing a valid raw manifest YAML string.
        project_config: A test fixture providing raw project YAML text.
    """
    # Instantiate a a silent logger
    silent_logger = Logger(min_terminal_level="emergency")

    # Pass the fixture through the manifest block to compile the type-safe DVO
    raw_input_data = yaml.safe_load(manifest_v1)
    manifest = RepositoryManifest(raw_data=raw_input_data, logger=silent_logger)

    # FIX: Parse your new project YAML fixture cleanly into our type-safe DVO block
    raw_project_data = yaml.safe_load(project_config)
    project_manifest = ProjectManifest(raw_data=raw_project_data, logger=silent_logger)

    # Define the path where template files live at the repository root
    # Path(__file__).parents[2] navigates up from tests/ to the root folder
    templates_dir = Path(__file__).parents[1] / "templates" / "debian"

    # Lazy-load compiler class to test the path contract
    from package_generator.compiler import DebianTemplateCompiler

    # Pass the templates folder location straight to the compiler constructor
    compiler = DebianTemplateCompiler(templates_dir=templates_dir, logger=silent_logger)

    # Instruct the compiler to load and render the 'control' template file
    rendered_output = compiler.render_template(
        template_name="control",
        package_config=manifest.config,
        project_config=project_manifest.config
    )

    # ASSERTIONS: Verify that Jinja2 successfully compiled the text fields
    expected_text = (
        "Source: test-repo-repo-config\n"
        "Section: utils\n"
        "Priority: optional\n"
        "Maintainer: Alice <alice@example.com>\n"
        "Build-Depends: debhelper-compat (= 13)\n"
        "Standards-Version: 4.6.2\n"
        "\n"
        "Package: test-repo-repo-config\n"
        "Architecture: all\n"
        "Depends: ${misc:Depends}, curl, ca-certificates, gnupg\n"
        "Description: Test repository package layout configuration.\n"
        " This package automatically manages the APT repository configuration and\n"
        " secure cryptographic keyrings for test-repo."
    )
    assert rendered_output == expected_text
