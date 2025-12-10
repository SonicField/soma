#!/usr/bin/env python3
"""
Split a markdown file into sections based on headings.

Usage:
    python3 split_markdown.py input.md output_dir/

Sections are split on lines starting with # that are NOT inside code blocks.
Code blocks are detected by ``` - only a line that is exactly ``` (with optional
whitespace) closes a code block, not ```lang.

Output files are named section_00.md, section_01.md, etc.
"""

import sys
import os
from pathlib import Path


def parse_sections(filepath):
    """Parse markdown file into sections, splitting on headings outside code blocks."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    in_code_block = False
    sections = []
    current_section = []

    for line in lines:
        stripped = line.strip()

        # Track code block state
        if stripped.startswith('```'):
            if in_code_block:
                # Only close on ``` alone (not ```lang)
                if stripped == '```':
                    in_code_block = False
            else:
                in_code_block = True

        # Split on headings outside code blocks
        if not in_code_block and line.startswith('#'):
            if current_section:
                sections.append(current_section)
            current_section = [line]
        else:
            current_section.append(line)

    # Don't forget the last section
    if current_section:
        sections.append(current_section)

    return sections


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} input.md output_dir/", file=sys.stderr)
        sys.exit(1)

    input_file = sys.argv[1]
    output_dir = sys.argv[2]

    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found", file=sys.stderr)
        sys.exit(1)

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Parse and write sections
    sections = parse_sections(input_file)

    for i, section in enumerate(sections):
        output_path = os.path.join(output_dir, f"section_{i:02d}.md")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(section)

        # Show first line (usually heading) for reference
        first_line = section[0].strip() if section else "(empty)"
        print(f"section_{i:02d}.md: {len(section)} lines - {first_line[:60]}")

    print(f"\nTotal: {len(sections)} sections written to {output_dir}/")


if __name__ == "__main__":
    main()
