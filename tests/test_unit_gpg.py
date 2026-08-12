# tests/test_unit_gpg.py
"""Unit tests isolating our cryptographic GPG engine layout formatting."""

import pytest

from package_generator.gpg import GpgEngine
from package_generator.logger import Logger


def test_gpg_engine_dearmors_ascii_text_into_binary_bytes() -> None:
    """Verifies that GpgEngine filters out ASCII armor headers into binary format.

    Ensures that when handed a clean cleartext string, it parses out metadata rows,
    removes the 24-bit CRC checksum line, and decodes the internal base64.
    """
    silent_logger = Logger(min_terminal_level="emergency")
    crypto = GpgEngine(logger=silent_logger)

    # A standard mock representation of a valid RFC-4880 cleartext armor block
    mock_ascii_armor = (
        "-----BEGIN PGP PUBLIC KEY BLOCK-----\n"
        "Version: GnuPG v2\n"
        "\n"
        "mQEN\n"
        "=abcd\n"
        "-----END PGP PUBLIC KEY BLOCK-----"
    )

    # SPECIFICATION CONTRACT: Method must accept an explicit string parameter
    binary_bytes = crypto.dearmor(ascii_text=mock_ascii_armor)

    # Assert that it physically stripped the text markers down to a binary stream
    assert isinstance(binary_bytes, bytes)
    assert b"-----BEGIN PGP" not in binary_bytes
    assert len(binary_bytes) > 0


@pytest.mark.parametrize(
    "malformed_text,expected_error_snippet",
    [
        (
            "INVALID_TEXT_WITHOUT_PGP_BOUNDARIES",
            "Provided text lacks valid PGP armor boundaries"
        ),
        (
            "-----BEGIN PGP PUBLIC KEY BLOCK-----\n-----END PGP PUBLIC KEY BLOCK-----",
            "OpenPGP key payload container is blank"
        ),
        (
            "-----BEGIN PGP PUBLIC KEY BLOCK-----\nVersion: 1.0\n\n"
            "-----END PGP PUBLIC KEY BLOCK-----",
            "OpenPGP key payload container is blank"
        ),
        (
            "-----BEGIN PGP PUBLIC KEY BLOCK-----\n\nCORRUPT_BASE64_STREAM_!!!\n"
            "-----END PGP PUBLIC KEY BLOCK-----",
            "Base64 stream content is corrupted"
        ),
    ]
)
def test_gpg_engine_raises_value_error_on_malformed_input_variants(
    malformed_text: str,
    expected_error_snippet: str,
) -> None:
    """Verifies that GpgEngine catches and rejects malformed openPGP stream data."""
    silent_logger = Logger(min_terminal_level="emergency")
    crypto = GpgEngine(logger=silent_logger)

    with pytest.raises(ValueError) as error_context:
        crypto.dearmor(ascii_text=malformed_text)

    assert expected_error_snippet in str(error_context.value)
