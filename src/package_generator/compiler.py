# src/package_generator/compiler.py
"""Debian template compilation engine.

Provides infrastructure capabilities to read raw Jinja2 text templates from disk,
inject strongly typed configuration properties, and compile them into finished
Debian repository system configuration layout text streams.
"""

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from .logger import Logger
from .models import PackageConfig, ProjectConfig


class DebianTemplateCompiler:
    """Manages file loading and variable rendering for Debian package templates."""

    def __init__(self, templates_dir: Path, logger: Logger) -> None:
        """Initializes the compiler with a template environment and logging hooks.

        Args:
            templates_dir: Physical directory path where real Jinja2 template
                source files reside on the disk platter.
            logger: An injected PSR-3 compliant diagnostic logging service.
        """
        self._logger = logger
        self._templates_dir = templates_dir
        self._env = Environment(
            loader=FileSystemLoader(str(self._templates_dir)),
            autoescape=False
        )

    def render_template(
        self,
        template_name: str,
        package_config: PackageConfig,
        project_config: ProjectConfig,
        **kwargs: Any,
    ) -> str:
        """Loads a target template file from disk and renders its variable tokens.

        Args:
            template_name: The file name string of the target template block.
            package_config: Strongly typed package parameters (e.g. name, version).
            project_config: Global project parameters (e.g. maintainer data).
            **kwargs: Dynamic contextual tokens merged directly into the rendering loop.

        Returns:
            The compiled uncolored text block stream containing injected values.
        """
        self._logger.debug(f"Loading template file asset track: {template_name}")
        template = self._env.get_template(template_name)

        # 1. Delegate the shell script loop generation out to an isolated sub-helper
        os_normalization_rules = self._compile_os_normalization_rules(package_config)

        # 2. Delegate context assembly out to a helper, passing kwargs forward cleanly
        render_context = self._build_render_context(
            package_config=package_config,
            project_config=project_config,
            os_normalization_rules=os_normalization_rules,
            extra_context=kwargs
        )

        # Pass the fully combined context map straight into the template natively
        compiled_output = template.render(**render_context)

        self._logger.debug(f"Successfully compiled template configuration layout: {template_name}")
        return compiled_output

    def _compile_os_normalization_rules(self, package_config: PackageConfig) -> str:
        """Assembles raw Bash case statement strings from the package OS mappings data model.

        Args:
            package_config: Validated, strongly typed package configuration parameters.

        Returns:
            A combined multi-line string containing the formatted shell script blocks.
        """
        self._logger.debug("Mapping strongly typed fields into flat template context variables...")
        compiled_rules = []

        for match_key, mapping in package_config.os_mappings.items():
            self._logger.debug(
                f"Compiling normalization case mapping rule for flavor: [{match_key}] "
                f"-> target dist: '{mapping.distro}', codename: '{mapping.codename}'"
            )

            rule_block = (
                f"        {match_key})\n"
                f'            TARGET_DIST="{mapping.distro}"\n'
                f'            TARGET_CODENAME="{mapping.codename}"\n'
                "            ;;"
            )
            compiled_rules.append(rule_block)

        return "\n".join(compiled_rules)

    def _build_render_context(
        self,
        package_config: PackageConfig,
        project_config: ProjectConfig,
        os_normalization_rules: str,
        extra_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Assembles the complete, unified template variables map supporting all engine lanes.

        Args:
            package_config: Validated, strongly typed package configuration parameters.
            project_config: Validated, strongly typed global project parameters.
            os_normalization_rules: Pre-compiled multiline bash rules normalization script string.
            extra_context: A dictionary of additional dynamic attributes to inject.

        Returns:
            A flat combined dictionary mapping variable names straight to primitives.
        """
        context: dict[str, Any] = {
            "package_name": package_config.name,
            "short_description": package_config.description,
            "version": package_config.version,
            "copyright_year": package_config.copyright_year,
            "dynamic_keyring": package_config.dynamic_keyring,
            "repo_url": package_config.repo.url if package_config.repo else "",
            "repo_suites": package_config.repo.suites if package_config.repo else "",
            "repo_components": package_config.repo.components if package_config.repo else "",
            "repo_key_url": package_config.repo.key_url if package_config.repo else "",
            "os_mappings": package_config.os_mappings,

            "maintainer_name": project_config.maintainer_name,
            "maintainer_email": project_config.maintainer_email,
            "copyright_holder": project_config.copyright_holder,
            "repository_url": project_config.repository_url,
            "package_suffix": project_config.package_suffix,

            "os_normalization_rules": os_normalization_rules,
        }

        # Safely merge any dynamic tokens passed from separate services (like Changelog bullets)
        context.update(extra_context)
        return context
