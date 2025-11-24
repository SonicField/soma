"""
SOMA Sin Calculator Runner

Usage (from soma repo root): python3 examples/sin_calculator/run_soma_sin.py
"""

import sys
from pathlib import Path

# Get the soma repo root directory (two levels up from this script)
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent.parent

# Add SOMA to Python path
sys.path.insert(0, str(REPO_ROOT))

from soma.vm import run_soma_program

# Load stdlib (relative to repo root)
stdlib_path = REPO_ROOT / 'soma' / 'stdlib.soma'
with open(stdlib_path, 'r') as f:
    stdlib_code = f.read()

# Load sin calculator (in same directory as this script)
sin_calculator_path = SCRIPT_DIR / 'soma_sin_calculator.soma'
with open(sin_calculator_path, 'r') as f:
    sin_code = f.read()

# Execute
full_code = stdlib_code + '\n' + sin_code
print("Running SOMA Sin Calculator...")
print("="*60)
al = run_soma_program(full_code)
print("="*60)
print("Done!")
