# tests/test_unit_compiler.py
"""DebianTemplateCompiler unit tests.

Discrete unit specifications validating the Jinja2 text compilation, variable
injection, and rendering boundaries managed by the DebianTemplateCompiler class.
"""

from pathlib import Path

import yaml

from package_generator import (
    DebianTemplateCompiler,
    Logger,
    ProjectManifest,
    RepositoryManifest,
)


def test_compiler_successfully_recreates_exact_project_configuration_file(
    tmp_path: Path,
    manifest_v1: str,
    project_config: str,
    mock_project_config_template: str,
) -> None:
    """Verifies Jinja2 compilation by recreating the exact project input file.

    Args:
        tmp_path: A built-in pytest fixture providing a temporary directory path.
        manifest_v1: A test fixture providing a valid raw manifest YAML string.
        project_config: A test fixture providing raw project YAML text.
        mock_project_config_template: Blueprint layout matching project_config.
    """
    silent_logger = Logger(min_terminal_level="emergency")

    # 1. Translate primitive text inputs into true object DVO values
    raw_project_data = yaml.safe_load(project_config)
    project_manifest = ProjectManifest(raw_data=raw_project_data, logger=silent_logger)

    raw_manifest_data = yaml.safe_load(manifest_v1)
    manifest = RepositoryManifest(raw_data=raw_manifest_data, logger=silent_logger)

    # 2. Write the template to a temporary sandbox directory layout path
    sandbox_dir = tmp_path / "templates"
    sandbox_dir.mkdir()

    template_file = sandbox_dir / "project_config_mock"
    template_file.write_text(mock_project_config_template, encoding="utf-8")

    # 3. Compile the values back out into a text stream using the real DVOs
    compiler = DebianTemplateCompiler(templates_dir=sandbox_dir, logger=silent_logger)

    rendered_output = compiler.render_template(
        template_name="project_config_mock",
        package_config=manifest.config,
        project_config=project_manifest.config,
    )

    # 4. SYMMETRICAL LOOP ASSERTION: Recreated text must match origin text exactly
    assert rendered_output == project_config


def test_compiler_successfully_recreates_exact_repository_manifest_file(
    tmp_path: Path,
    manifest_v1: str,
    project_config: str,
    mock_manifest_template: str,
) -> None:
    """Verifies Jinja2 compilation by recreating the exact manifest input file.

    Args:
        tmp_path: A built-in pytest fixture providing a temporary directory path.
        manifest_v1: A test fixture providing a valid raw manifest YAML string.
        project_config: A test fixture providing raw project YAML text.
        mock_manifest_template: Blueprint layout matching manifest_v1.
    """
    silent_logger = Logger(min_terminal_level="emergency")

    # 1. Translate primitive text inputs into true object DVO values
    raw_manifest_data = yaml.safe_load(manifest_v1)
    manifest = RepositoryManifest(raw_data=raw_manifest_data, logger=silent_logger)

    raw_project_data = yaml.safe_load(project_config)
    project_manifest = ProjectManifest(raw_data=raw_project_data, logger=silent_logger)

    # 2. Write the template to a temporary sandbox directory layout path
    sandbox_dir = tmp_path / "templates"
    sandbox_dir.mkdir()

    template_file = sandbox_dir / "manifest_mock"
    template_file.write_text(mock_manifest_template, encoding="utf-8")

    # 3. Compile the values back out into a text stream using the real DVOs
    compiler = DebianTemplateCompiler(templates_dir=sandbox_dir, logger=silent_logger)

    rendered_output = compiler.render_template(
        template_name="manifest_mock",
        package_config=manifest.config,
        project_config=project_manifest.config,
    )

    # 4. SYMMETRICAL LOOP ASSERTION: Recreated text must match origin text exactly
    assert rendered_output == manifest_v1


def test_compiler_context_includes_suite_aliases(
    tmp_path: Path,
    manifest_suites_alias: str,
    project_config: str,
) -> None:
    """Verifies that the compiler incorporates suite_aliases into the render context.

    Args:
        tmp_path: A built-in pytest fixture providing a temporary directory path.
        project_config: A test fixture providing raw project YAML text.
        manifest_v1: A test fixture providing a valid raw manifest YAML string.
    """
    logger = Logger(min_terminal_level="emergency")

    # 1. SETUP: Establish temporary files and directories
    sandbox_dir = tmp_path / "templates"
    sandbox_dir.mkdir()

    # Write a mock template file that renders the raw keys from suite_aliases
    template_file = sandbox_dir / "mock_postinst"
    template_file.write_text(
        "{% for k, v in suite_aliases.items() %}{{ k }}: {{ v }}\n{% endfor %}",
        encoding="utf-8"
    )

    # 2. MODELS: Load manifest data and manually inject sample suite aliases
    raw_project_data = yaml.safe_load(project_config)
    project_manifest = ProjectManifest(raw_data=raw_project_data, logger=logger)

    raw_manifest_data = yaml.safe_load(manifest_suites_alias)
    manifest = RepositoryManifest(raw_data=raw_manifest_data, logger=logger)

    # 3. EXECUTION: Run the template compiler
    compiler = DebianTemplateCompiler(templates_dir=sandbox_dir, logger=logger)
    rendered_output = compiler.render_template(
        template_name="mock_postinst",
        package_config=manifest.config,
        project_config=project_manifest.config,
    )

    # 4. ASSERTION: Verify that the variables were successfully processed by Jinja
    assert "bookworm: sandworm" in rendered_output
    assert "trixie: synchrony" in rendered_output
