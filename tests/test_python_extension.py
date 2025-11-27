"""
Tests for Python FFI extension.

Written FIRST following TDD. Will fail until implementation complete.
"""
import unittest
import tempfile
import os
from soma.vm import VM, run_soma_program, RuntimeError as SomaRuntimeError


class TestPythonExtensionLoading(unittest.TestCase):
    """Test loading the Python extension."""

    def test_python_extension_loads(self):
        """Test (python) >use loads extension."""
        code = "(python) >use"
        vm = VM(load_stdlib=False)
        vm.execute_code(code)
        self.assertIn('python', vm.loaded_extensions)

    def test_python_builtins_registered(self):
        """Test Python extension registers expected builtins."""
        vm = VM(load_stdlib=False)
        vm.load_extension('python')

        self.assertTrue(vm.store.read_value(['use', 'python', 'call']) is not None)
        self.assertTrue(vm.store.read_value(['use', 'python', 'load']) is not None)
        self.assertTrue(vm.store.read_value(['use', 'python', 'import']) is not None)

    def test_python_macros_created(self):
        """Test setup code creates Store macros."""
        vm = VM(load_stdlib=False)
        vm.load_extension('python')

        # Check wrapper macros exist (after implementing get_soma_setup)
        # For now, just verify extension loads
        self.assertIn('python', vm.loaded_extensions)


class TestPythonCall(unittest.TestCase):
    """Test >use.python.call FFI primitive."""

    def test_simple_builtin_call(self):
        """Test calling Python int('42')."""
        code = """
        (python) >use
        Void (42) (int) >use.python.call
        """
        al = run_soma_program(code)

        # AL: [result, exception]
        exception = al[-1]
        result = al[-2]

        self.assertEqual(result, 42)
        self.assertTrue(isinstance(exception, type(VM().store.read_value(['Void']))))

    def test_multiple_arguments(self):
        """Test calling pow(2, 10) with correct argument order."""
        code = """
        (python) >use
        Void 2 10 (pow) >use.python.call
        """
        al = run_soma_program(code)

        exception = al[-1]
        result = al[-2]

        self.assertEqual(result, 1024)  # pow(2, 10), not pow(10, 2)

    def test_zero_arguments(self):
        """Test calling function with no arguments."""
        code = """
        (python) >use
        Void (list) >use.python.call
        """
        al = run_soma_program(code)

        exception = al[-1]
        result = al[-2]

        # list() returns []
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_exception_on_failure(self):
        """Test exception handling when Python call fails."""
        code = """
        (python) >use
        Void (not_a_number) (int) >use.python.call
        """
        al = run_soma_program(code)

        exception = al[-1]
        result = al[-2]

        # Failure: result is Void, exception is Thing
        from soma.vm import Void, VoidSingleton
        self.assertIsInstance(result, VoidSingleton)
        self.assertNotIsInstance(exception, VoidSingleton)

    def test_none_to_void_conversion(self):
        """Test Python None converts to SOMA Void."""
        code = """
        (python) >use
        Void (Hello World) (print) >use.python.call
        """
        al = run_soma_program(code)

        exception = al[-1]
        result = al[-2]

        # print() returns None → Void
        from soma.vm import VoidSingleton
        self.assertIsInstance(result, VoidSingleton)
        self.assertIsInstance(exception, VoidSingleton)

    def test_module_function_call(self):
        """Test calling module.function (e.g., math.sqrt)."""
        code = """
        (python) >use
        Void 16 (math.sqrt) >use.python.call
        """
        al = run_soma_program(code)

        exception = al[-1]
        result = al[-2]

        self.assertEqual(result, 4.0)

    def test_al_underflow_error(self):
        """Test >use.python.call with insufficient values."""
        code = """
        (python) >use
        >use.python.call
        """
        with self.assertRaises(SomaRuntimeError):
            run_soma_program(code)


class TestPythonLoad(unittest.TestCase):
    """Test >use.python.load file loading."""

    def test_load_soma_file(self):
        """Test loading and executing SOMA file."""
        # Create temp SOMA file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.soma', delete=False) as f:
            f.write('42 !loaded.value\n99 !loaded.other')
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            ({temp_path}) >use.python.load
            loaded.value loaded.other
            """
            al = run_soma_program(code)

            self.assertEqual(al[-2], 42)
            self.assertEqual(al[-1], 99)
        finally:
            os.unlink(temp_path)

    def test_load_nonexistent_file(self):
        """Test loading non-existent file errors."""
        code = """
        (python) >use
        (/nonexistent/path/file.soma) >use.python.load
        """
        with self.assertRaises(SomaRuntimeError):
            run_soma_program(code)

    def test_load_executes_in_current_context(self):
        """Test loaded code shares VM context."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.soma', delete=False) as f:
            f.write('shared.value 10 >+')
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            32 !shared.value
            ({temp_path}) >use.python.load
            """
            al = run_soma_program(code)

            self.assertEqual(al[-1], 42)  # 32 + 10
        finally:
            os.unlink(temp_path)


class TestPythonImport(unittest.TestCase):
    """Test >use.python.import module importing."""

    def test_import_standard_module(self):
        """Test importing Python standard library."""
        code = """
        (python) >use
        (math) >use.python.import
        """
        al = run_soma_program(code)

        # Should push True for success
        from soma.vm import True_
        self.assertEqual(al[-1], True_)

    def test_import_nonexistent_module(self):
        """Test importing non-existent module returns False."""
        code = """
        (python) >use
        (nonexistent_module_xyz) >use.python.import
        """
        al = run_soma_program(code)

        # Should push False for failure
        from soma.vm import False_
        self.assertEqual(al[-1], False_)

    def test_imported_module_callable(self):
        """Test imported module functions are callable."""
        code = """
        (python) >use
        (json) >use.python.import >drop
        Void (test) (str.upper) >use.python.call
        """
        al = run_soma_program(code)

        exception = al[-1]
        result = al[-2]

        self.assertEqual(result, "TEST")


class TestTypeConversions(unittest.TestCase):
    """Test type conversions between Python and SOMA."""

    def test_python_none_to_void(self):
        """Test Python None → SOMA Void."""
        code = """
        (python) >use
        Void (None) (eval) >use.python.call
        """
        al = run_soma_program(code)
        result = al[-2]
        from soma.vm import VoidSingleton
        self.assertIsInstance(result, VoidSingleton)

    def test_python_bool_to_soma(self):
        """Test Python bool → SOMA boolean."""
        code = """
        (python) >use
        Void (True) (eval) >use.python.call
        """
        al = run_soma_program(code)
        result = al[-2]
        from soma.vm import True_
        self.assertIs(result, True_)  # SOMA True

    def test_python_int_to_soma(self):
        """Test Python int → SOMA integer."""
        code = """
        (python) >use
        Void (42) (int) >use.python.call
        """
        al = run_soma_program(code)
        result = al[-2]
        self.assertEqual(result, 42)

    def test_python_str_to_soma(self):
        """Test Python str → SOMA string."""
        code = """
        (python) >use
        Void (42) (str) >use.python.call
        """
        al = run_soma_program(code)
        result = al[-2]
        self.assertIsInstance(result, str)
        self.assertEqual(result, "42")


if __name__ == '__main__':
    unittest.main()
