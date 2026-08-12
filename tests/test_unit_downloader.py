# tests/test_unit_downloader.py
"""Unit tests isolating our network downloader client operations."""

from unittest.mock import MagicMock, patch

from package_generator.downloader import Downloader
from package_generator.logger import Logger


def test_downloader_retrieves_raw_binary_octet_stream_from_remote_url() -> None:
    """Verifies that the Downloader service fetches byte arrays from a URL.

    Ensures that the response stream is preserved as raw binary bytes and is not
    corrupted or transformed by an implicit text string decoding operation pass.
    """
    silent_logger = Logger(min_terminal_level="emergency")
    fetcher = Downloader(logger=silent_logger)

    target_url = "https://example.com"
    mock_binary_payload = b"\x99\x01\x00_RAW_BINARY_KEY_OCTETS"

    # Intercept standard library network calls natively
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = mock_binary_payload
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # SPECIFICATION CONTRACT: The method must be named download_bytes and return bytes
        retrieved_bytes = fetcher.download_bytes(url=target_url)

    assert mock_urlopen.called
    assert isinstance(retrieved_bytes, bytes)
    assert retrieved_bytes == b"\x99\x01\x00_RAW_BINARY_KEY_OCTETS"
