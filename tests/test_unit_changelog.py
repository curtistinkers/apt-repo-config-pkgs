# tests/test_unit_changelog.py
"""Changelog unit tests.

Discrete unit specifications validating the Debian changelog Ingestion, regex
parsing, block structure extraction, and chronological history tracking.
"""

from package_generator import Changelog, Logger


def test_changelog_parses_genesis_release_metadata(changelog_v1: str) -> None:
    """Verifies that the changelog engine cleanly parses a baseline v1 text block.

    Args:
        changelog_v1: A test fixture providing a raw initial changelog text string.
    """
    silent_logger = Logger(min_terminal_level="emergency")
    manifest = Changelog(raw_text=changelog_v1, logger=silent_logger)

    assert manifest.latest_entry.package_name == "test-repo"
    assert manifest.latest_entry.version == "1.0.0"
    assert manifest.latest_entry.suite == "stable"
    assert manifest.latest_entry.urgency == "medium"
    assert "Initial package definition established." in manifest.latest_entry.changes
    assert manifest.latest_entry.timestamp == "Mon, 10 Aug 2026 12:00:00 +0000"


def test_changelog_tracks_multiple_historical_blocks(changelog_v3: str) -> None:
    """Verifies that the engine handles and orders multi-block release chains.

    Args:
        changelog_v3: A test fixture providing a master three-entry changelog text.
    """
    silent_logger = Logger(min_terminal_level="emergency")
    manifest = Changelog(raw_text=changelog_v3, logger=silent_logger)

    assert len(manifest.entries) == 3
    assert manifest.entries[0].version == "1.0.2"
    assert manifest.entries[1].version == "1.0.1"
    assert manifest.entries[2].version == "1.0.0"

def test_changelog_handles_empty_or_invalid_text_gracefully() -> None:
    """Verifies that the engine handles unparseable text without crashing."""
    silent_logger = Logger(min_terminal_level="emergency")

    # Ingest a completely invalid string text layout
    manifest = Changelog(raw_text="This is random junk text, not a changelog.", logger=silent_logger)

    # Assert that the engine exited safely with an empty list and no latest entry
    assert len(manifest.entries) == 0
    assert manifest.latest_entry is None
