#!/usr/bin/env python3
"""
SOMA Runner - Execute SOMA code from stdin, output to stdout.

This script provides a clean interface for running SOMA programs:
- Reads UTF-8 SOMA code from stdin
- Executes the code
- Outputs only the result to stdout (UTF-8)
- Errors go to stderr

Usage:
    cat document.soma | python3 soma.py > output.md
    echo "(Hello World) >print" | python3 soma.py
"""

import sys
import os
from pathlib import Path

# Add soma to path
soma_root = Path(__file__).parent.parent
sys.path.insert(0, str(soma_root))

from soma.vm import run_soma_program


def main():
    """Read SOMA code from stdin and execute it."""
    try:
        # Read UTF-8 encoded SOMA code from stdin
        code = sys.stdin.read()

        # Execute SOMA program
        # All output from SOMA (via >print, etc.) goes to stdout automatically
        # We just need to execute silently
        run_soma_program(code)

        # Return success
        return 0

    except Exception as e:
        # Errors go to stderr, not stdout
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
