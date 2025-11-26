#!/usr/bin/env python3
"""
Tests for the pure SOMA load extension.

Tests loading files from pwd and $SOMA_LIB with path searching.
"""

import unittest
import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from soma.vm import VM, run_soma_program


class TestLoadExtension(unittest.TestCase):
    """Test the load extension."""

    def setUp(self):
        """Set up test directories and files."""
        # Create temp directories
        self.test_dir = tempfile.mkdtemp()
        self.soma_lib_dir = tempfile.mkdtemp()

        # Create test SOMA files
        self.pwd_file = Path(self.test_dir) / "test_pwd.soma"
        self.pwd_file.write_text("42 !loaded_from_pwd")

        self.lib_file = Path(self.soma_lib_dir) / "test_lib.soma"
        self.lib_file.write_text("99 !loaded_from_lib")

        # Save original directory and SOMA_LIB
        self.orig_dir = os.getcwd()
        self.orig_soma_lib = os.environ.get('SOMA_LIB')

    def tearDown(self):
        """Clean up test directories."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
        shutil.rmtree(self.soma_lib_dir, ignore_errors=True)

        # Restore original directory and env var
        os.chdir(self.orig_dir)
        if self.orig_soma_lib is not None:
            os.environ['SOMA_LIB'] = self.orig_soma_lib
        elif 'SOMA_LIB' in os.environ:
            del os.environ['SOMA_LIB']

    def test_load_extension_available(self):
        """Test that load extension can be loaded."""
        code = """
        (python) >use
        (load) >use
        """
        vm = VM()
        from soma.lexer import lex
        from soma.parser import Parser
        from soma.vm import compile_program

        tokens = lex(code)
        parser = Parser(tokens)
        ast = parser.parse()
        compiled = compile_program(ast)
        vm.execute(compiled)

        # Check that load function exists
        from soma.vm import Void
        self.assertIsNot(vm.store.read_value(['load']), Void)

    def test_load_from_pwd(self):
        """Test loading a file from current directory."""
        os.chdir(self.test_dir)

        code = """
        (python) >use
        (load) >use

        (test_pwd.soma) >load

        ) Check that variable was set
        loaded_from_pwd
        """

        al = run_soma_program(code)
        self.assertEqual(al, [42])

    def test_load_from_soma_lib(self):
        """Test loading a file from $SOMA_LIB."""
        # Set SOMA_LIB and change to different directory
        os.environ['SOMA_LIB'] = str(self.soma_lib_dir)
        os.chdir(self.test_dir)  # Different from SOMA_LIB

        code = """
        (python) >use
        (load) >use

        (test_lib.soma) >load

        ) Check that variable was set
        loaded_from_lib
        """

        al = run_soma_program(code)
        self.assertEqual(al, [99])

    def test_pwd_takes_precedence(self):
        """Test that pwd is checked before $SOMA_LIB."""
        # Create same filename in both locations with different values
        pwd_override = Path(self.test_dir) / "shared.soma"
        pwd_override.write_text("1 !source")

        lib_file = Path(self.soma_lib_dir) / "shared.soma"
        lib_file.write_text("2 !source")

        os.environ['SOMA_LIB'] = str(self.soma_lib_dir)
        os.chdir(self.test_dir)

        code = """
        (python) >use
        (load) >use

        (shared.soma) >load
        source
        """

        al = run_soma_program(code)
        self.assertEqual(al, [1], "Should load from pwd, not SOMA_LIB")

    def test_loads_into_current_context(self):
        """Test that loaded file executes in current context."""
        # Create file that uses variables from calling context
        context_file = Path(self.test_dir) / "use_context.soma"
        context_file.write_text("existing_var 10 >+")

        os.chdir(self.test_dir)

        code = """
        (python) >use
        (load) >use

        5 !existing_var
        (use_context.soma) >load
        """

        al = run_soma_program(code)
        self.assertEqual(al, [15], "Loaded file should see existing_var")


if __name__ == '__main__':
    unittest.main(verbosity=2)
