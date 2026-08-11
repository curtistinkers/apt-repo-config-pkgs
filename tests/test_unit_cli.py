# tests/test_unit_cli.py
"""CLI unit tests.

Discrete unit specifications validating the argument parsing boundaries,
command routing, and option validations managed by the CLI interface group.
"""

from click.testing import CliRunner


def test_unit_cli_build_subcommand_routes_correctly() -> None:
    """Validate build subcommand.

    Verifies that the CLI 'build' subcommand exists under our main interface
    group and executes with a successful exit status code 0.
    """
    # 1. SETUP: Import the primary CLI group component block
    from package_generator.cli import main_cli

    # Initialize an isolated Click command test runner
    runner = CliRunner()

    # 2. EXECUTION: Run the clean command
    result = runner.invoke(main_cli, ["build"])

    # 3. SPECIFICATION ASSERTION: The command must route successfully
    assert result.exit_code == 0

def test_unit_cli_clean_subcommand_routes_correctly() -> None:
    """Validate clean subcommand.

    Verifies that the CLI 'clean' subcommand exists under our main interface
    group and executes with a successful exit status code 0.
    """
    # 1. SETUP: Import the primary CLI group component block
    from package_generator.cli import main_cli

    # Initialize an isolated Click command test runner
    runner = CliRunner()

    # 2. EXECUTION: Run the clean command
    result = runner.invoke(main_cli, ["clean"])

    # 3. SPECIFICATION ASSERTION: The command must route successfully
    assert result.exit_code == 0
