# src/package_generator/manifest.py
"""Repository manifest translation engine.

Provides capabilities to read, thoroughly validate, and compile unstructured
primitive configuration structures down into type-safe immutable domain data
value objects.
"""

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
                individual operating system rules violate the schema model structural requirements.
        """
        # Enforce mandatory top-level root configuration keys
        required_root_keys = ["name", "version", "description", "copyright_year"]
        for key in required_root_keys:
            val = self._raw_data.get(key)
            if val is None or str(val).strip() == "":
                err_msg = (
                    f"Manifest schema violation: Mandatory root key '{key}' is missing or empty."
                )
                self._logger.error(err_msg)
                raise ValueError(err_msg)

        # Enforce structural presence of the nested 'repo' sub-dictionary block
        if "repo" not in self._raw_data or not isinstance(self._raw_data["repo"], dict):
            err_msg = (
                "Manifest schema violation: Mandatory child block 'repo' is missing or invalid."
            )
            self._logger.error(err_msg)
            raise ValueError(err_msg)

        repo_block = self._raw_data["repo"]
        required_repo_keys = ["url", "suites", "components", "key_url"]
        for r_key in required_repo_keys:
            r_val = repo_block.get(r_key)
            if r_val is None or str(r_val).strip() == "":
                err_msg = (
                    f"Manifest schema violation: Mandatory repo child key '{r_key}' "
                    "is missing or empty."
                )
                self._logger.error(err_msg)
                raise ValueError(err_msg)

        # Enforce strict conditional validations on the 'os_mappings' collection array
        if "os_mappings" in self._raw_data and self._raw_data["os_mappings"] is not None:
            raw_mappings = self._raw_data["os_mappings"]
            if not isinstance(raw_mappings, list):
                err_msg = (
                    "Manifest schema violation: 'os_mappings' must be a valid array list structure."
                )
                self._logger.error(err_msg)
                raise ValueError(err_msg)

            required_mapping_keys = ["match", "set_dist", "set_codename"]
            for index, item in enumerate(raw_mappings):
                if not isinstance(item, dict):
                    err_msg = (
                        f"Manifest schema violation: os_mappings item at index {index} "
                        "must be a dictionary."
                    )
                    self._logger.error(err_msg)
                    raise ValueError(err_msg)

                for m_key in required_mapping_keys:
                    m_val = item.get(m_key)
                    if m_val is None or str(m_val).strip() == "":
                        err_msg = (
                            f"Manifest schema violation: Mandatory mapping child key '{m_key}' "
                            f"is missing or empty inside os_mappings index {index}."
                        )
                        self._logger.error(err_msg)
                        raise ValueError(err_msg)

    def _compile_config(self) -> PackageConfig:
        """Transforms validated primitives cleanly into nested DVO assets.

        Returns:
            A fully constructed, type-safe immutable PackageConfig data structure.
        """
        self._logger.debug("Compiling valid primitive schema keys into PackageConfig DVO...")
        repo_block = self._raw_data["repo"]

        repo_dvo = PackageRepoConfig(
            url=str(repo_block["url"]).strip(),
            suites=str(repo_block["suites"]).strip(),
            components=str(repo_block["components"]).strip(),
            key_url=str(repo_block["key_url"]).strip()
        )

        mapping_dvos = []
        raw_mappings = self._raw_data.get("os_mappings", [])
        if isinstance(raw_mappings, list):
            for item in raw_mappings:
                if isinstance(item, dict):
                    mapping_dvos.append(
                        PackageOSMappingConfig(
                            match=str(item.get("match", "")).strip(),
                            set_dist=str(item.get("set_dist", "")).strip(),
                            set_codename=str(item.get("set_codename", "")).strip()
                        )
                    )

        compiled_config = PackageConfig(
            name=str(self._raw_data["name"]).strip(),
            version=str(self._raw_data["version"]).strip(),
            description=str(self._raw_data["description"]).strip(),
            copyright_year=int(self._raw_data["copyright_year"]),
            dynamic_keyring=bool(self._raw_data.get("dynamic_keyring", False)),
            repo=repo_dvo,
            os_mappings=mapping_dvos
        )

        self._logger.info(f"Successfully validated and compiled manifest: {compiled_config.name}")
        return compiled_config
