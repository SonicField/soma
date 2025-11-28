"""
Tests for SOMA extension system.

These tests are written FIRST (TDD) and will initially FAIL.
Implementation should make these tests pass.
"""
import unittest
from soma.vm import VM, run_soma_program, Void, RuntimeError as SomaRuntimeError


def path_exists(store, path):
    """Helper: Check if a Store path exists (strict semantics)."""
    try:
        value = store.read_value(path)
        # Path exists if we can read it (even if value is Void from auto-vivification)
        return True
    except SomaRuntimeError:
        # Undefined path raises RuntimeError under strict semantics
        return False


class TestStdlibAutoLoad(unittest.TestCase):
    """Test stdlib auto-loading functionality."""

    def test_stdlib_loads_by_default(self):
        """Test VM() auto-loads stdlib operations."""
        vm = VM()
        # Stdlib operations should exist
        self.assertTrue(path_exists(vm.store, ['dup']))
        self.assertTrue(path_exists(vm.store, ['drop']))
        self.assertTrue(path_exists(vm.store, ['swap']))
        self.assertTrue(path_exists(vm.store, ['if']))
        self.assertTrue(path_exists(vm.store, ['while']))
        self.assertTrue(path_exists(vm.store, ['not']))

    def test_stdlib_can_be_disabled(self):
        """Test VM(load_stdlib=False) doesn't load stdlib."""
        vm = VM(load_stdlib=False)
        # Stdlib should NOT exist
        self.assertFalse(path_exists(vm.store, ['dup']))
        self.assertFalse(path_exists(vm.store, ['if']))

    def test_ffi_builtins_always_available(self):
        """Test FFI builtins exist even without stdlib."""
        vm = VM(load_stdlib=False)
        # FFI builtins should still exist
        self.assertTrue(path_exists(vm.store, ['block']))
        self.assertTrue(path_exists(vm.store, ['+']))
        self.assertTrue(path_exists(vm.store, ['-']))
        self.assertTrue(path_exists(vm.store, ['print']))
        self.assertTrue(path_exists(vm.store, ['<']))

    def test_stdlib_operations_execute(self):
        """Test stdlib operations work correctly."""
        code = "5 >dup >+"
        al = run_soma_program(code)
        self.assertEqual(len(al), 1)
        self.assertEqual(al[0], 10)

    def test_stdlib_only_loads_once(self):
        """Test calling _load_stdlib twice is safe."""
        vm = VM(load_stdlib=False)
        vm._load_stdlib()
        vm._load_stdlib()  # Should not error
        self.assertTrue(path_exists(vm.store, ['dup']))


class TestUseBuiltin(unittest.TestCase):
    """Test >use builtin for loading extensions."""

    def test_use_builtin_exists(self):
        """Test >use is registered as a builtin."""
        vm = VM(load_stdlib=False)
        self.assertTrue(path_exists(vm.store, ['use']))

    def test_use_with_string(self):
        """Test >use loads extension by name."""
        code = "(python) >use"
        vm = VM(load_stdlib=False)
        vm.execute_code(code)
        self.assertIn('python', vm.loaded_extensions)

    def test_use_requires_string(self):
        """Test >use rejects non-string argument."""
        vm = VM(load_stdlib=False)
        vm.al.append(42)  # Not a string
        with self.assertRaises(SomaRuntimeError):
            vm.store.read_value(['use']).fn(vm)

    def test_use_al_underflow(self):
        """Test >use with empty AL errors."""
        vm = VM(load_stdlib=False)
        with self.assertRaises(SomaRuntimeError):
            vm.store.read_value(['use']).fn(vm)

    def test_use_idempotent(self):
        """Test loading same extension twice is safe."""
        code = "(python) >use (python) >use"
        vm = VM(load_stdlib=False)
        vm.execute_code(code)
        # Should not error - verified by no exception

    def test_use_nonexistent_extension(self):
        """Test >use with invalid extension name errors."""
        code = "(nonexistent_extension_xyz) >use"
        with self.assertRaises(SomaRuntimeError):
            run_soma_program(code)


class TestExtensionRegistration(unittest.TestCase):
    """Test extension builtin registration."""

    def test_register_valid_name(self):
        """Test registering builtin with valid use.* name."""
        vm = VM(load_stdlib=False)

        def my_builtin(vm):
            vm.al.append(42)

        vm.register_extension_builtin('use.myext.answer', my_builtin)
        self.assertTrue(path_exists(vm.store, ['use', 'myext', 'answer']))

    def test_register_rejects_invalid_name(self):
        """Test registration rejects non-namespaced names."""
        vm = VM(load_stdlib=False)

        def bad_builtin(vm):
            pass

        with self.assertRaises(ValueError):
            vm.register_extension_builtin('badname', bad_builtin)

    def test_registered_builtin_callable(self):
        """Test registered builtin can be called from SOMA."""
        vm = VM(load_stdlib=False)

        def answer_builtin(vm):
            vm.al.append(42)

        vm.register_extension_builtin('use.test.answer', answer_builtin)

        code = ">use.test.answer"
        vm.execute_code(code)
        self.assertEqual(vm.al[-1], 42)

    def test_extension_has_loaded_set(self):
        """Test VM tracks loaded extensions."""
        vm = VM(load_stdlib=False)
        self.assertTrue(hasattr(vm, 'loaded_extensions'))
        self.assertIsInstance(vm.loaded_extensions, set)


if __name__ == '__main__':
    unittest.main()
