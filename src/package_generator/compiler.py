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
    ) -> str:
        """Loads a target template file from disk and renders its variable tokens.

        Args:
            template_name: The file name string of the target template block.
            package_config: Strongly typed package parameters (e.g. name, version).
            project_config: Global project parameters (e.g. maintainer data).

        Returns:
            The compiled uncolored text block stream containing injected values.
        """
        self._logger.debug(f"Loading template file asset track: {template_name}")
        template = self._env.get_template(template_name)

        self._logger.debug("Mapping strongly typed fields into flat template context variables...")

        # Dynamically build out the raw bash case statement rows from our DVO dictionary map
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

        os_normalization_rules_str = "\n".join(compiled_rules)

        os_normalization_rules_str = "\n".join(compiled_rules)

        # translate DVO structures into flat tokens matching the control template
        render_context: dict[str, Any] = {
            "package_name": package_config.name,
            "short_description": package_config.description,
            "version": package_config.version,
            "copyright_year": package_config.copyright_year,
            "dynamic_keyring": package_config.dynamic_keyring,
            "repo_url": package_config.repo.url,
            "repo_suites": package_config.repo.suites,
            "repo_components": package_config.repo.components,
            "repo_key_url": package_config.repo.key_url,
            "os_mappings": package_config.os_mappings,

            "maintainer_name": project_config.maintainer_name,
            "maintainer_email": project_config.maintainer_email,
            "copyright_holder": project_config.copyright_holder,
            "repository_url": project_config.repository_url,

            "os_normalization_rules": os_normalization_rules_str,
        }

        # Pass the context map straight into the template context natively
        compiled_output = template.render(**render_context)

        self._logger.info(f"Successfully compiled template configuration layout: {template_name}")
        return compiled_output
