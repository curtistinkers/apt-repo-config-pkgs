# package_generator/manifest.py
"""
package_generator.manifest
==========================
Input validator layer parsing raw dictionary inputs into strongly typed DVOs.
"""

from .models import PackageConfig, PackageOSMappingConfig, PackageRepoConfig


class RepositoryManifest:
    """Responsible for validating raw user inputs and building a PackageConfig."""

    def __init__(self, raw_data: dict) -> None:
        """Initializes and verifies the repository manifest input."""
        self._raw_data = raw_data
        self._validate_schema()
        self.config = self._compile_config()

    def _validate_schema(self) -> None:
        """Raises a ValueError if mandatory elements are missing or empty."""
        # 1. Enforce mandatory top-level root configuration keys
        required_root_keys = ["name", "version", "description", "copyright_year"]
        for key in required_root_keys:
            if key not in self._raw_data or self._raw_data[key] is None or str(self._raw_data[key]).strip() == "":
                raise ValueError(f"Manifest schema violation: Mandatory root key '{key}' is missing or empty.")

        # 2. Enforce structural presence of the nested 'repo' sub-dictionary block
        if "repo" not in self._raw_data or not isinstance(self._raw_data["repo"], dict):
            raise ValueError("Manifest schema violation: Mandatory child block 'repo' is missing or invalid.")

        repo_block = self._raw_data["repo"]
        required_repo_keys = ["url", "suites", "components", "key_url"]
        for r_key in required_repo_keys:
            if r_key not in repo_block or repo_block[r_key] is None or str(repo_block[r_key]).strip() == "":
                raise ValueError(f"Manifest schema violation: Mandatory repo child key '{r_key}' is missing or empty.")

        # 3. FIX: Enforce strict conditional validations on the 'os_mappings' collection array
        # If the key is present in the document layout, inspect every child dictionary row
        if "os_mappings" in self._raw_data and self._raw_data["os_mappings"] is not None:
            raw_mappings = self._raw_data["os_mappings"]
            if not isinstance(raw_mappings, list):
                raise ValueError("Manifest schema violation: 'os_mappings' must be a valid array list structure.")

            required_mapping_keys = ["match", "set_dist", "set_codename"]
            for index, item in enumerate(raw_mappings):
                if not isinstance(item, dict):
                    raise ValueError(f"Manifest schema violation: os_mappings item at index {index} must be a dictionary.")

                for m_key in required_mapping_keys:
                    if m_key not in item or item[m_key] is None or str(item[m_key]).strip() == "":
                        raise ValueError(
                            f"Manifest schema violation: Mandatory mapping child key '{m_key}' "
                            f"is missing or empty inside os_mappings index {index}."
                        )

    def _compile_config(self) -> PackageConfig:
        """Transforms validated primitives cleanly into nested DVO assets."""
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

        return PackageConfig(
            name=str(self._raw_data["name"]).strip(),
            version=str(self._raw_data["version"]).strip(),
            description=str(self._raw_data["description"]).strip(),
            copyright_year=int(self._raw_data["copyright_year"]),
            dynamic_keyring=bool(self._raw_data.get("dynamic_keyring", False)),
            repo=repo_dvo,
            os_mappings=mapping_dvos
        )
