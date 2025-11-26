#!/usr/bin/env python3
"""
Python FFI Demo: Practical Examples

Shows SOMA calling Python with robust error handling.

Run from anywhere:
    python3 examples/ffi/python_ffi_demo.py
"""

import sys
from pathlib import Path

# Add SOMA to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from soma.vm import run_soma_program

print("=" * 70)
print("Python FFI Demonstration")
print("=" * 70)
print()

# Example 1: Math operations
print("Example 1: Mathematical Functions")
print("-" * 70)
code1 = """
(python) >use

(Calculating 2^10 using Python pow function) >print
Void 2 10 (pow) >use.python.call
>drop  ) Drop exception (Void for success)
>toString (Result: ) >swap >concat >print

(Calculating sqrt of 144) >print
Void 144 (math.sqrt) >use.python.call
>drop
) Convert float to string using Python str()
Void >swap (str) >use.python.call >drop
(Result: ) >swap >concat >print
"""
run_soma_program(code1)

print()

# Example 2: String manipulation
print("Example 2: String Operations")
print("-" * 70)
code2 = """
(python) >use

(hello world) (Original: ) >swap >concat >print

(Uppercase: ) (hello world) Void >swap (str.upper) >use.python.call >drop >concat >print

(Title case: ) (hello world) Void >swap (str.title) >use.python.call >drop >concat >print
"""
run_soma_program(code2)

print()

# Example 3: Error handling
print("Example 3: Error Handling with Dual-Return Pattern")
print("-" * 70)
code3 = """
(python) >use

(Attempting: int of not-a-number) >print
Void (not_a_number) (int) >use.python.call

) Dual return gives [result, exception]
) Check if exception is Void (= success)
>isVoid {
  (Unexpected success!) >print
} {
  (✓ Error caught correctly!) >print
  (  Exception object received) >print
} >ifelse
"""
run_soma_program(code3)

print()
print("=" * 70)
print("Key Features Demonstrated:")
print("=" * 70)
print("""
✓ Call any Python function: pow, sqrt, str.upper, json.loads, etc.
✓ Dual-return pattern: [result, exception] for robust error handling
✓ Check success: exception >isVoid (True = success, False = error)
✓ Natural integration with SOMA control flow (>ifelse)
✓ Access to Python's entire standard library + any installed packages

The FFI demonstrates SOMA's philosophy:
  Minimal core language + powerful FFI = maximum flexibility

This lets SOMA leverage Python's rich ecosystem without reinventing wheels!
""")
