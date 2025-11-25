#!/usr/bin/env python3
"""
SOMA Test Runner

Runs .soma test files and verifies expected behavior.

Test file format:
  ) TEST: Description of test
  ) EXPECT_AL: [expected, AL, values]
  ) EXPECT_OUTPUT: expected output (optional)

  ... SOMA code ...

Multiple tests can be in one file using the TEST: marker.
"""

import sys
import os
import re
from pathlib import Path
from io import StringIO
from contextlib import redirect_stdout

# Add parent directory to path to import soma modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from soma.vm import run_soma_program


class TestCase:
    def __init__(self, name, source, expect_al=None, expect_output=None, expect_error=None):
        self.name = name
        self.source = source
        self.expect_al = expect_al
        self.expect_output = expect_output if expect_output else []
        self.expect_error = expect_error


def parse_test_file(filepath):
    """Parse a .soma test file into TestCase objects."""
    with open(filepath, 'r') as f:
        content = f.read()

    tests = []
    current_test = None
    current_source = []

    for line in content.split('\n'):
        # Check for test markers
        if line.strip().startswith(') TEST:'):
            # Save previous test
            if current_test:
                current_test.source = '\n'.join(current_source)
                tests.append(current_test)

            # Start new test
            test_name = line.split('TEST:', 1)[1].strip()
            current_test = TestCase(test_name, '', None, None)
            current_source = []

        elif line.strip().startswith(') EXPECT_AL:'):
            if current_test:
                al_str = line.split('EXPECT_AL:', 1)[1].strip()
                current_test.expect_al = al_str

        elif line.strip().startswith(') EXPECT_OUTPUT:'):
            if current_test:
                output = line.split('EXPECT_OUTPUT:', 1)[1].strip()
                # Split on literal \n to get individual lines
                lines = output.split('\\n')
                current_test.expect_output.extend(lines)

        elif line.strip().startswith(') EXPECT_ERROR:'):
            if current_test:
                error_type = line.split('EXPECT_ERROR:', 1)[1].strip()
                current_test.expect_error = error_type

        else:
            # Regular source line
            current_source.append(line)

    # Save final test
    if current_test:
        current_test.source = '\n'.join(current_source)
        tests.append(current_test)

    return tests


def repr_al(al):
    """Convert AL to readable string representation."""
    items = []
    for item in al:
        type_name = type(item).__name__
        if type_name == 'int':
            items.append(str(item))
        elif type_name == 'str':
            items.append(f'"{item}"')
        elif type_name in ['TrueSingleton', 'FalseSingleton', 'NilSingleton', 'VoidSingleton']:
            items.append(type_name.replace('Singleton', ''))
        elif type_name == 'Block':
            items.append('Block')
        else:
            items.append(type_name)
    return '[' + ', '.join(items) + ']'


def run_test(test, verbose=False, load_stdlib=True):
    """Run a single test case and return (passed, message)."""
    # If test expects an error, verify it raises the right error
    if test.expect_error:
        try:
            from soma.vm import VM
            from soma.lexer import lex
            from soma.parser import Parser, ParseError
            from soma.vm import compile_program

            # Try to parse and run - should fail
            tokens = lex(test.source)
            parser = Parser(tokens)
            ast = parser.parse()
            compiled = compile_program(ast)

            vm = VM(load_stdlib=load_stdlib)
            vm.execute(compiled)

            # If we get here, test failed - no error was raised
            return False, f"Expected {test.expect_error} but code executed successfully"

        except Exception as e:
            error_type = type(e).__name__
            # Check if error type matches expectation
            if test.expect_error in error_type or error_type in test.expect_error:
                return True, "OK"
            else:
                return False, f"Expected {test.expect_error} but got {error_type}: {e}"

    # Normal test (expects AL/output)
    try:
        # Create VM with appropriate stdlib setting
        from soma.vm import VM
        from soma.lexer import lex
        from soma.parser import Parser
        from soma.vm import compile_program

        # Capture stdout
        captured_output = StringIO()
        with redirect_stdout(captured_output):
            # Create VM with appropriate stdlib flag
            vm = VM(load_stdlib=load_stdlib)

            # Compile and execute test code
            tokens = lex(test.source)
            parser = Parser(tokens)
            ast = parser.parse()
            compiled = compile_program(ast)
            vm.execute(compiled)

            al = vm.al

        output = captured_output.getvalue()

        # Check AL expectation
        if test.expect_al is not None:
            actual_al = repr_al(al)
            if actual_al != test.expect_al:
                return False, f"AL mismatch: expected {test.expect_al}, got {actual_al}"

        # Check output expectation
        if test.expect_output:
            actual_lines = [line for line in output.strip().split('\n') if line]
            expected_lines = test.expect_output

            if len(actual_lines) != len(expected_lines):
                return False, f"Output line count mismatch: expected {len(expected_lines)} lines, got {len(actual_lines)} lines"

            for i, (expected, actual) in enumerate(zip(expected_lines, actual_lines)):
                if expected.strip() != actual.strip():
                    return False, f"Output mismatch at line {i+1}:\n  Expected: {repr(expected)}\n  Got: {repr(actual)}"

        return True, "OK"

    except Exception as e:
        return False, f"Exception: {e}"


def run_test_file(filepath, verbose=False):
    """Run all tests in a file and return (total, passed)."""
    tests = parse_test_file(filepath)

    if not tests:
        print(f"⚠️  {filepath.name}: No tests found")
        return 0, 0

    # Determine if stdlib should be loaded based on filename
    # 01_* files: FFI-only tests, no stdlib
    # 02+_* files: Tests that use stdlib
    load_stdlib = not filepath.name.startswith('01_')

    print(f"\n{'='*60}")
    print(f"📄 {filepath.name}")
    if load_stdlib:
        print(f"   (with stdlib)")
    print(f"{'='*60}")

    passed = 0
    total = len(tests)

    for test in tests:
        success, message = run_test(test, verbose, load_stdlib)

        if success:
            print(f"  ✓ {test.name}")
            passed += 1
        else:
            print(f"  ✗ {test.name}")
            print(f"     {message}")
            if verbose:
                print(f"     Source:\n{test.source}")

    return total, passed


def main():
    """Run all SOMA tests."""
    test_dir = Path(__file__).parent / 'soma'

    if not test_dir.exists():
        print(f"Error: Test directory not found: {test_dir}")
        return 1

    test_files = sorted(test_dir.glob('*.soma'))

    if not test_files:
        print(f"Error: No .soma test files found in {test_dir}")
        return 1

    print("=" * 60)
    print("SOMA Test Suite")
    print("=" * 60)

    total_tests = 0
    total_passed = 0

    for filepath in test_files:
        tests, passed = run_test_file(filepath, verbose=('-v' in sys.argv))
        total_tests += tests
        total_passed += passed

    # Summary
    print(f"\n{'='*60}")
    print(f"Summary: {total_passed}/{total_tests} tests passed")
    print(f"{'='*60}")

    if total_passed == total_tests:
        print("✓ All tests passed!")
        return 0
    else:
        print(f"✗ {total_tests - total_passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
