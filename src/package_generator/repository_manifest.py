# src/package_generator/manifest.py
"""Repository manifest translation engine.

Provides capabilities to read, thoroughly validate, and compile unstructured
primitive configuration structures down into type-safe immutable domain data
value objects.
"""

from typing import Any

from .logger import Logger
from .models import PackageConfig, PackageOSMappingConfig, PackageRepoConfig


class RepositoryManifest:
    """Validates raw user manifest inputs and builds a PackageConfig."""

    def __init__(self, raw_data: dict, logger: Logger) -> None:
        """Initializes and verifies the repository manifest input.

        Args:
            raw_data: Unverified primitive dictionary configuration layout tree.
            logger: An injected PSR-3 compliant diagnostic logging service.
        """
        self._raw_data = raw_data
        self._logger = logger

        self._validate_schema()
        self.config = self._compile_config()

    def _validate_schema(self) -> None:
        """Raises a ValueError if mandatory elements are missing or empty.

        Raises:
            ValueError: If any top-level keys, nested repository parameters, or
                individual operating system rules violate structural requirements.
        """
        # Enforce mandatory top-level root configuration keys
        required_root_keys = ["name", "version", "description", "copyright_year"]
        for key in required_root_keys:
            val = self._raw_data.get(key)
            if val is None or str(val).strip() == "":
                err_msg = f"Manifest schema violation: Mandatory root key '{key}' is missing."
                self._logger.error(err_msg)
                raise ValueError(err_msg)

        # Enforce structural presence of the nested 'repo' sub-dictionary block
        if "repo" not in self._raw_data or not isinstance(self._raw_data["repo"], dict):
            err_msg = "Manifest schema violation: Mandatory child block 'repo' is missing."
            self._logger.error(err_msg)
            raise ValueError(err_msg)

        repo_block = self._raw_data["repo"]
        required_repo_keys = ["url", "suites", "components", "key_url"]
        for r_key in required_repo_keys:
            r_val = repo_block.get(r_key)
            if r_val is None or str(r_val).strip() == "":
                err_msg = (
                    f"Manifest schema violation: Mandatory repo child key '{r_key}' is missing."
                )
                self._logger.error(err_msg)
                raise ValueError(err_msg)

        # FIX: Enforce validation constraints against our new YAML Mapping dictionary format
        if "os_mappings" in self._raw_data and self._raw_data["os_mappings"] is not None:
            raw_mappings = self._raw_data["os_mappings"]
            if not isinstance(raw_mappings, dict):
                err_msg = "Manifest schema violation: 'os_mappings' must be a valid key-value map."
                self._logger.error(err_msg)
                raise ValueError(err_msg)

            required_mapping_keys = ["distro", "codename"]
            for match_key, inner_properties in raw_mappings.items():
                if not isinstance(inner_properties, dict):
                    err_msg = (
                        f"Manifest schema violation: Rule content for '{match_key}' must be a map."
                    )
                    self._logger.error(err_msg)
                    raise ValueError(err_msg)

                for m_key in required_mapping_keys:
                    m_val = inner_properties.get(m_key)
                    if m_val is None or str(m_val).strip() == "":
                        err_msg = (
                            f"Manifest schema violation: Mandatory child property '{m_key}' "
                            f"is missing or empty inside the 'os_mappings.{match_key}' block."
                        )
                        self._logger.error(err_msg)
                        raise ValueError(err_msg)

    def _parse_repo(self, repo_block: dict[str, Any]) -> PackageRepoConfig:
        """Translates raw repository map primitives into a type-safe DVO node."""
        return PackageRepoConfig(
            url=str(repo_block["url"]).strip(),
            suites=str(repo_block["suites"]).strip(),
            components=str(repo_block["components"]).strip(),
            key_url=str(repo_block["key_url"]).strip(),
        )

    def _parse_os_mappings(self, raw_mappings: dict[str, Any]) -> dict[str, PackageOSMappingConfig]:
        """Translates raw manifest mapping properties into a strongly typed DVO dictionary."""
        parsed_mappings: dict[str, PackageOSMappingConfig] = {}

        for match_key, inner_properties in raw_mappings.items():
            mapping_node = PackageOSMappingConfig(
                distro=str(inner_properties.get("distro", "")).strip(),
                codename=str(inner_properties.get("codename", "")).strip(),
            )
            parsed_mappings[match_key.strip()] = mapping_node

        return parsed_mappings

    def _compile_config(self) -> PackageConfig:
        """Transforms validated primitives cleanly into nested DVO assets.

        Returns:
            A fully constructed, type-safe immutable PackageConfig data structure.
        """
        self._logger.debug("Compiling valid primitive schema keys into PackageConfig DVO...")

        repo_dvo = self._parse_repo(self._raw_data["repo"])

        raw_mappings = self._raw_data.get("os_mappings", {})
        mapping_dvos = self._parse_os_mappings(raw_mappings)

        compiled_config = PackageConfig(
            name=str(self._raw_data["name"]).strip(),
            version=str(self._raw_data["version"]).strip(),
            description=str(self._raw_data["description"]).strip(),
            copyright_year=int(self._raw_data["copyright_year"]),
            dynamic_keyring=bool(self._raw_data.get("dynamic_keyring", False)),
            repo=repo_dvo,
            os_mappings=mapping_dvos,
        )

        self._logger.info(f"Successfully validated and compiled manifest: {compiled_config.name}")
        return compiled_config
