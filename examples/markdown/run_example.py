#!/usr/bin/env python3
"""
SOMA Markdown Extension Example Runner

This script executes the markdown_examples.soma file which demonstrates
all features of the SOMA markdown extension.

The SOMA file will render itself as a markdown document to output.md.
"""

import sys
import os
from pathlib import Path

# Add soma to path
soma_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(soma_root))

from soma.vm import VM, run_soma_program
from soma.parser import Parser
from soma.lexer import lex


def main():
    """Run the markdown example."""
    example_dir = Path(__file__).parent
    soma_file = example_dir / "markdown_examples.soma"
    output_file = example_dir / "output.md"

    print("=" * 70)
    print("SOMA Markdown Extension Example")
    print("=" * 70)
    print(f"Input:  {soma_file}")
    print(f"Output: {output_file}")
    print()

    # Read the SOMA file
    with open(soma_file, 'r') as f:
        code = f.read()

    # Execute it (change to example directory so output.md goes to the right place)
    print("Executing SOMA program...")
    try:
        # Save current directory and change to example directory
        original_dir = os.getcwd()
        os.chdir(example_dir)

        try:
            run_soma_program(code)
        finally:
            # Restore original directory
            os.chdir(original_dir)

        print("✓ Execution complete!")
        print()

        # Check if output was created
        if output_file.exists():
            print(f"✓ Output file created: {output_file}")

            # Show file size
            size = output_file.stat().st_size
            print(f"  Size: {size} bytes")

            # Show first few lines
            print()
            print("Preview (first 20 lines):")
            print("-" * 70)
            with open(output_file, 'r') as f:
                lines = f.readlines()
                for i, line in enumerate(lines[:20], 1):
                    print(f"{i:3d}: {line}", end='')
                if len(lines) > 20:
                    print(f"... ({len(lines) - 20} more lines)")
            print("-" * 70)
            print()
            print(f"Full output available in: {output_file}")
        else:
            print(f"✗ Output file not created")
            return 1

    except Exception as e:
        print(f"✗ Error executing SOMA program:")
        print(f"  {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print()
    print("=" * 70)
    print("Example complete!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
