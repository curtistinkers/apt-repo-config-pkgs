"""Network resource retrieval coordinator.

Handles light socket requests to fetch remote content profiles cleanly
from external web repositories using standard library tooling.
"""

import urllib.request

from .logger import Logger


class Downloader:
    """Manages clean network stream acquisition from external URLs."""

    def __init__(self, logger: Logger) -> None:
        """Initializes the network downloader service layer.

        Args:
            logger: An injected PSR-3 compliant diagnostic logging service.
        """
        self._logger = logger

    def download_bytes(self, url: str) -> bytes:
        """Fetches remote file payloads cleanly over a network stream socket.

        Args:
            url: The absolute target URL address path to download from.

        Returns:
            The raw octet binary byte stream downloaded from the endpoint.
        """
        self._logger.info(f"Initiating remote data stream fetch from URL: {url}")

        req = urllib.request.Request(
            url,
            headers={"User-Agent": "DebianPackageBuilder/1.0.0"}
        )

        with urllib.request.urlopen(req) as response:
            payload_bytes = response.read()

        self._logger.debug(f"Successfully retrieved {len(payload_bytes)} raw octet payload bytes.")
        return payload_bytes
