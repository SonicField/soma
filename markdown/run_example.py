#!/usr/bin/env python3
"""
SOMA Markdown Extension Example Runner

This script executes the SOMA markdown example files:
- markdown-examples.soma -> markdown-examples.md
- markdown-user-guide.soma -> markdown-user-guide.md

The SOMA files demonstrate all features of the SOMA markdown extension
and render themselves as markdown documents.
"""

import sys
import os
from pathlib import Path

# Add soma to path
soma_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(soma_root))

from soma.vm import run_soma_program


def run_soma_file(soma_file: Path, expected_output: Path) -> bool:
    """Run a SOMA file and verify output was created."""
    print(f"\nProcessing: {soma_file.name}")
    print(f"  Input:  {soma_file}")
    print(f"  Output: {expected_output}")

    # Read the SOMA file
    with open(soma_file, 'r') as f:
        code = f.read()

    # Execute it (change to example directory so output goes to the right place)
    try:
        # Save current directory and change to example directory
        original_dir = os.getcwd()
        os.chdir(soma_file.parent)

        try:
            run_soma_program(code)
        finally:
            # Restore original directory
            os.chdir(original_dir)

        # Check if output was created
        if expected_output.exists():
            size = expected_output.stat().st_size
            lines = len(expected_output.read_text().splitlines())
            print(f"  ✓ Generated: {size:,} bytes, {lines:,} lines")
            return True
        else:
            print(f"  ✗ Output file not created")
            return False

    except Exception as e:
        print(f"  ✗ Error: {type(e).__name__}: {e}")
        return False


def main():
    """Run both markdown example files."""
    example_dir = Path(__file__).parent

    print("=" * 70)
    print("SOMA Markdown Extension Examples")
    print("=" * 70)

    files_to_run = [
        ("markdown-examples.soma", "markdown-examples.md"),
        ("markdown-user-guide.soma", "markdown-user-guide.md"),
    ]

    results = []
    for soma_name, md_name in files_to_run:
        soma_file = example_dir / soma_name
        output_file = example_dir / md_name

        if not soma_file.exists():
            print(f"\n✗ {soma_name} not found")
            results.append(False)
            continue

        success = run_soma_file(soma_file, output_file)
        results.append(success)

    # Summary
    print()
    print("=" * 70)
    successful = sum(results)
    total = len(results)

    if successful == total:
        print(f"✓ All {total} files processed successfully!")
    else:
        print(f"✗ {successful}/{total} files processed successfully")
        return 1

    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
