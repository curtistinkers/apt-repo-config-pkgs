# src/package_generator/gpg.py
"""Cryptographic OpenPGP format normalization engine.

Provides translation operations to strip text headers, clean padding spaces,
and dearmor cleartext public keys down to binary format layouts.
"""

import base64
import re

from .logger import Logger


class GpgEngine:
    """Manages raw translation operations across armored key structures."""

    def __init__(self, logger: Logger) -> None:
        """Initializes the cryptographic processing layout service.

        Args:
            logger: An injected PSR-3 compliant diagnostic logging service.
        """
        self._logger = logger

    def dearmor(self, ascii_text: str) -> bytes:
        """Unpacks ASCII-armored cleartext keys into raw binary octet data streams.

        Args:
            ascii_text: The complete raw multi-line text block representing an
                ASCII-armored PGP public key structure.

        Returns:
            Pure decoded binary bytes corresponding to the underlying key token data.

        Raises:
            ValueError: If the text stream block lacks valid OpenPGP body markers
                or possesses corrupt base64 string records.
        """
        self._logger.info("Initializing binary dearmoring conversion on ASCII public key blocks...")

        # Locate the core inner base64 block wrapped inside standard boundary marks
        body_match = re.search(
            r"-----BEGIN PGP PUBLIC KEY BLOCK-----(.*?)-----END PGP PUBLIC KEY BLOCK-----",
            ascii_text,
            re.DOTALL
        )

        if not body_match:
            err_msg = "Cryptographic parse error: Provided text lacks valid PGP armor boundaries."
            self._logger.error(err_msg)
            raise ValueError(err_msg)

        raw_body_content = body_match.group(1).strip()

        # Filter out optional RFC-4880 cleartext armor block header lines (e.g. Version:, Comment:)
        cleaned_rows = []
        for line in raw_body_content.splitlines():
            line_strip = line.strip()
            if not line_strip:
                continue
            if ":" in line_strip and not line_strip.startswith("=") and len(cleaned_rows) == 0:
                # Skip leading metadata properties header rows entirely
                continue
            cleaned_rows.append(line_strip)

        if not cleaned_rows:
            err_msg = "Cryptographic parse error: OpenPGP key payload container is blank."
            self._logger.error(err_msg)
            raise ValueError(err_msg)

        # Check for and pop the standard OpenPGP 24-bit CRC checksum line starting with an '=' sign
        if cleaned_rows[-1].startswith("="):
            cleaned_rows.pop()

        # Combine lines and decode the raw base64 string block back to native binary format bytes
        compiled_base64_str = "".join(cleaned_rows)

        try:
            binary_bytes = base64.b64decode(compiled_base64_str, validate=True)
            self._logger.info(
                f"Successfully converted ASCII block into {len(binary_bytes)} binary bytes."
            )
            return binary_bytes
        except Exception as decode_error:
            err_msg = (
                f"Cryptographic parse error: Base64 stream content is corrupted: {decode_error}"
            )
            self._logger.error(err_msg)
            raise ValueError(err_msg) from decode_error
