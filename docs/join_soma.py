#!/usr/bin/env python3
"""
Join SOMA section files into a complete .soma document.

Usage:
    python3 join_soma.py input_dir/ output.soma

Reads section_00.soma, section_01.soma, etc. from input_dir.
Strips per-section headers and footers, adds document header/footer.

Per-section patterns stripped:
- Header: (python) >use (markdown) >use, >md.start
- Footer: lines ending with >md.render

Document wrapper added:
- Header: (python) >use (markdown) >use, >md.start
- Footer: >md.print
"""

import sys
import os
import re
from pathlib import Path


def is_header_line(line):
    """Check if line is a per-section header line to strip."""
    stripped = line.strip()
    return stripped in [
        '(python) >use (markdown) >use',
        '(python) >use',
        '(markdown) >use',
        '>md.start',
    ]


def is_footer_line(line):
    """Check if line is a per-section footer line to strip."""
    stripped = line.strip()
    return stripped.endswith('>md.render')


def process_section(filepath):
    """Read a section file and strip header/footer lines."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    result = []
    for line in lines:
        # Skip header lines
        if is_header_line(line):
            continue
        # Skip footer lines
        if is_footer_line(line):
            continue
        result.append(line.rstrip('\n'))

    # Remove leading/trailing blank lines from section
    while result and not result[0].strip():
        result.pop(0)
    while result and not result[-1].strip():
        result.pop()

    return result


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} input_dir/ output.soma", file=sys.stderr)
        sys.exit(1)

    input_dir = sys.argv[1]
    output_file = sys.argv[2]

    if not os.path.isdir(input_dir):
        print(f"Error: {input_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    # Find all section files
    section_files = sorted([
        f for f in os.listdir(input_dir)
        if re.match(r'section_\d+\.soma$', f)
    ])

    if not section_files:
        print(f"Error: No section_*.soma files found in {input_dir}", file=sys.stderr)
        sys.exit(1)

    # Build complete document
    output_lines = [
        '(python) >use (markdown) >use',
        '>md.start',
        '',
    ]

    for section_file in section_files:
        filepath = os.path.join(input_dir, section_file)
        section_lines = process_section(filepath)

        if section_lines:
            output_lines.extend(section_lines)
            output_lines.append('')  # Blank line between sections

        print(f"{section_file}: {len(section_lines)} lines")

    # Add footer
    output_lines.append('>md.print')

    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))

    total_lines = len(output_lines)
    print(f"\nTotal: {len(section_files)} sections -> {total_lines} lines in {output_file}")


if __name__ == "__main__":
    main()
