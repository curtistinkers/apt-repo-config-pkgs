# tests/test_unit_crypto.py
"""Unit tests isolating our network downloader and cryptographic GPG engine."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from package_generator.downloader import Downloader
from package_generator.gpg import GpgEngine
from package_generator.logger import Logger


def test_downloader_retrieves_raw_text_stream_from_remote_url() -> None:
    """Verifies that the Downloader service fetches string payloads from a URL."""
    silent_logger = Logger(min_terminal_level="emergency")
    fetcher = Downloader(logger=silent_logger)

    target_url = "https://example.com"
    mock_payload = "RAW_ASCII_KEY_DATA"

    # Intercept standard library network calls natively
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        mock_response.read.return_value = mock_payload.encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        retrieved_text = fetcher.download_text(url=target_url)

    assert mock_urlopen.called
    assert retrieved_text == "RAW_ASCII_KEY_DATA"


def test_gpg_engine_dearmors_ascii_key_into_binary_bytes() -> None:
    """Verifies that the GpgEngine filters out ASCII armor into binary bytes."""
    silent_logger = Logger(min_terminal_level="emergency")
    crypto = GpgEngine(logger=silent_logger)

    # A standard base64 chunk representing a valid PGP payload stream block
    mock_ascii_armor = (
        "-----BEGIN PGP PUBLIC KEY BLOCK-----\n\n"
        "mQENBFmK\n"
        "-----END PGP PUBLIC KEY BLOCK-----"
    )

    # Translate the ASCII block down to its true binary representation
    binary_bytes = crypto.dearmor(ascii_text=mock_ascii_armor)

    # Assert that it physically stripped the headers and decoded the base64 characters
    assert isinstance(binary_bytes, bytes)
    assert b"-----BEGIN PGP" not in binary_bytes
    assert len(binary_bytes) > 0
