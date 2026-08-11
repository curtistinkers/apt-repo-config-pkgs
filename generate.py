#!/usr/bin/env python3
"""
generate.py
===========
The main executable entrypoint for the repository configuration engine.
Bootstraps the application package runtime environment from the src directory.
"""

import sys
from pathlib import Path

# Explicitly ensure the entrypoint can locate the local 'src' directory
src_path = str(Path(__file__).parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)


if __name__ == "__main__":
    # Import our completed Click interface group object from the package
    from package_generator.cli import main_cli

    # Hand control over to the Click execution framework natively
    main_cli()
