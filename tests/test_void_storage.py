#!/usr/bin/env python3
"""
Test Void Storage (TDD for Void-Payload-Invariant Removal)

These tests currently FAIL because Void cannot be stored.
After removing the invariant, they will PASS.
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from soma.vm import VM, Void, RuntimeError as SomaRuntimeError


class TestVoidStorageInStore(unittest.TestCase):
    """Test storing Void values in Store cells."""

    def test_store_void_in_store_cell(self):
        """Test that we can write Void to a Store path."""
        vm = VM(load_stdlib=False)

        # This should work after invariant removal
        vm.store.write_value(["mypath"], Void)

        # Should be able to read it back
        value = vm.store.read_value(["mypath"])
        self.assertIs(value, Void)

    def test_store_void_in_nested_path(self):
        """Test storing Void in nested Store path."""
        vm = VM(load_stdlib=False)

        vm.store.write_value(["a", "b", "c"], Void)
        value = vm.store.read_value(["a", "b", "c"])
        self.assertIs(value, Void)

    def test_overwrite_value_with_void(self):
        """Test overwriting existing value with Void."""
        vm = VM(load_stdlib=False)

        # Write integer first
        vm.store.write_value(["mypath"], 42)
        self.assertEqual(vm.store.read_value(["mypath"]), 42)

        # Overwrite with Void
        vm.store.write_value(["mypath"], Void)
        self.assertIs(vm.store.read_value(["mypath"]), Void)


class TestVoidStorageInRegister(unittest.TestCase):
    """Test storing Void values in Register."""

    def test_store_void_in_register(self):
        """Test that we can write Void to Register."""
        vm = VM(load_stdlib=False)

        # This should work after invariant removal
        vm.register.write_value(["_", "temp"], Void)

        # Should be able to read it back
        value = vm.register.read_value(["_", "temp"])
        self.assertIs(value, Void)

    def test_store_void_at_register_root(self):
        """Test storing Void at Register root _."""
        vm = VM(load_stdlib=False)

        vm.register.write_value(["_"], Void)
        value = vm.register.read_value(["_"])
        self.assertIs(value, Void)


class TestStdlibDropWithVoid(unittest.TestCase):
    """Test that stdlib's {!_} !drop works with Void values."""

    def test_drop_void_value(self):
        """Test dropping Void from AL using stdlib drop."""
        from soma.vm import run_soma_program

        code = """
        Void >drop
        42
        """

        # Should not raise error
        al = run_soma_program(code)
        self.assertEqual(al, [42])

    def test_drop_in_sequence_with_void(self):
        """Test drop works in sequence with Void values."""
        from soma.vm import run_soma_program

        code = """
        1 Void 3 >drop >drop
        """

        # Should drop 3, then drop Void, leaving 1
        al = run_soma_program(code)
        self.assertEqual(al, [1])


class TestPythonFFIWithVoid(unittest.TestCase):
    """Test Python FFI helpers work with Void in dual-return pattern."""

    def test_get_result_discards_void_exception(self):
        """Test getResult helper discards Void exception."""
        from soma.vm import run_soma_program

        code = """
        (python) >use
        Void 2 10 (pow) >use.python.call
        >use.python.getResult
        """

        # Should return just the result (1024), dropping Void exception
        al = run_soma_program(code)
        self.assertEqual(al, [1024])

    def test_get_exception_discards_void_result(self):
        """Test getException helper works when result is Void."""
        from soma.vm import run_soma_program

        code = """
        (python) >use
        Void (invalid) (int) >use.python.call
        >use.python.getException
        """

        # Should return just the exception, dropping Void result
        al = run_soma_program(code)
        self.assertEqual(len(al), 1)
        # Exception should be a Python ValueError object
        self.assertIsInstance(al[0], ValueError)


class TestAutoVivification(unittest.TestCase):
    """Test auto-vivification behavior with strict semantics."""

    def test_read_unwritten_path_raises_error(self):
        """Test reading unwritten path raises RuntimeError (strict semantics)."""
        vm = VM(load_stdlib=False)

        # Reading non-existent path should raise RuntimeError
        with self.assertRaises(SomaRuntimeError) as ctx:
            vm.store.read_value(["never", "written"])
        self.assertIn("Undefined Store path", str(ctx.exception))

    def test_can_distinguish_written_void_from_never_written(self):
        """Test that written Void is distinguishable from never-written.

        With strict semantics:
        - Never-written path: raises RuntimeError
        - Explicitly written Void: returns Void
        - Auto-vivified intermediate: returns Void

        This is an IMPROVEMENT over permissive semantics.
        """
        vm = VM(load_stdlib=False)

        # Path 1: Never written - should error
        with self.assertRaises(SomaRuntimeError):
            vm.store.read_value(["never_written"])

        # Path 2: Explicitly written as Void - should return Void
        vm.store.write_value(["explicit"], Void)
        explicit = vm.store.read_value(["explicit"])
        self.assertIs(explicit, Void)

        # Path 3: Auto-vivified (write to child, read parent) - should return Void
        vm.store.write_value(["auto", "child"], 42)
        autovivified = vm.store.read_value(["auto"])
        self.assertIs(autovivified, Void)

        # Now we CAN distinguish! Never-written errors, others return Void


class TestVoidInSOMACode(unittest.TestCase):
    """Test Void storage through SOMA code execution."""

    def test_store_void_via_soma_store_operator(self):
        """Test !path with Void works."""
        from soma.vm import run_soma_program

        code = """
        Void !mypath
        mypath
        """

        al = run_soma_program(code)
        from soma.vm import Void as VoidSingleton
        self.assertIs(al[0], VoidSingleton)

    def test_store_void_in_register_via_soma(self):
        """Test !_.path with Void works."""
        from soma.vm import run_soma_program

        code = """
        { Void !_.x _.x } >chain
        """

        al = run_soma_program(code)
        from soma.vm import Void as VoidSingleton
        self.assertIs(al[0], VoidSingleton)


if __name__ == '__main__':
    # Run tests and show which ones fail (they should all fail before invariant removal)
    unittest.main(verbosity=2)
