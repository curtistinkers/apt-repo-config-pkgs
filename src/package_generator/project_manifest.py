"""Project manifest translation engine.

Provides capabilities to read, thoroughly validate, and compile global
project-level configurations into a type-safe immutable domain data
value object wrapper.
"""

from .logger import Logger
from .models import ProjectConfig


class ProjectManifest:
    """Validates raw global project manifest inputs and builds a ProjectConfig."""

    def __init__(self, raw_data: dict, logger: Logger) -> None:
        """Initializes and verifies the global project configuration input.

        Args:
            raw_data: Unverified primitive dictionary configuration layout tree.
            logger: An injected PSR-3 compliant diagnostic logging service.
        """
        self._raw_data = raw_data
        self._logger = logger

        self._validate_schema()
        self.config = self._compile_config()

    def _validate_schema(self) -> None:
        """Raises a ValueError containing all schema violations found in the input.

        Raises:
            ValueError: If any top-level project global keys are missing or empty.
        """
        self._logger.debug("Executing input validation checks across project global maps...")

        required_keys = [
            "maintainer_name",
            "maintainer_email",
            "copyright_holder",
            "repository_url",
        ]

        collected_errors = []

        for key in required_keys:
            val = self._raw_data.get(key)
            if val is None or str(val).strip() == "":
                err_msg = f"Mandatory global key '{key}' is missing"
                collected_errors.append(err_msg)

        # Ensure the list check triggers out HERE, completely separate from the for loop block
        if collected_errors:
            combined_report = "\n- ".join(collected_errors)
            full_exception_msg = f"Project manifest schema violations found:\n- {combined_report}"

            self._logger.error(full_exception_msg)
            raise ValueError(full_exception_msg)

    def _compile_config(self) -> ProjectConfig:
        """Transforms validated primitives cleanly into a ProjectConfig DVO asset.

        Returns:
            A fully constructed, type-safe immutable ProjectConfig data structure.
        """
        self._logger.debug("Compiling validated primitive global keys into ProjectConfig DVO...")

        compiled_config = ProjectConfig(
            maintainer_name=str(self._raw_data["maintainer_name"]).strip(),
            maintainer_email=str(self._raw_data["maintainer_email"]).strip(),
            copyright_holder=str(self._raw_data["copyright_holder"]).strip(),
            repository_url=str(self._raw_data["repository_url"]).strip(),
        )

        self._logger.info("Successfully validated and compiled global project manifest.")
        return compiled_config
