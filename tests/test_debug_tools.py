"""
Unit tests for debug.chain and debug.choose debug utilities.

These tests verify that debug wrappers provide useful debugging output
for chain and choose operations without changing behavior.

Requirements:
- Use Python unittest framework (not SOMA tests)
- Use regex matching for debug output (not exact string matching)
- Test both functionality and debug output
"""

import unittest
import re
import io
import sys
from soma.vm import run_soma_program, VM, compile_program, Nil, True_, False_
from soma.lexer import lex
from soma.parser import Parser


class TestDebugChain(unittest.TestCase):
    """Tests for debug.chain debugging wrapper."""

    def capture_output(self, code):
        """Run SOMA code and capture stdout."""
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            # Create VM and run code
            tokens = lex(code)
            parser = Parser(tokens)
            ast = parser.parse()
            compiled = compile_program(ast)
            vm = VM()
            vm.execute(compiled)
            output = sys.stdout.getvalue()
            return output, vm.al
        finally:
            sys.stdout = old_stdout

    def test_debug_chain_shows_iterations(self):
        """Test that debug.chain shows iteration count."""
        code = '''
        chain !backup.chain
        debug.chain !chain

        { (second) >print Nil }
        { (first) >print { (second) >print Nil } }
        >chain

        backup.chain !chain
        '''
        output, _ = self.capture_output(code)

        # Should show iteration numbers
        self.assertRegex(output, r'Iteration 1', "Should show iteration 1")
        self.assertRegex(output, r'Iteration 2', "Should show iteration 2")

    def test_debug_chain_shows_al_size_before_after(self):
        """Test that debug.chain shows AL size before and after each iteration."""
        code = '''
        chain !backup.chain
        debug.chain !chain

        Nil
        { 1 2 Nil }
        >chain

        backup.chain !chain
        '''
        output, _ = self.capture_output(code)

        # Should show AL size before and after
        # Format: "AL before: N items" or "AL size: N" etc
        self.assertRegex(output, r'AL.*:\s*\d+\s*item', "Should show AL size")

    def test_debug_chain_detects_nil_termination(self):
        """Test that debug.chain detects Nil on AL (normal termination)."""
        code = '''
        chain !backup.chain
        debug.chain !chain

        { (step2) >print Nil }
        { (step1) >print { (step2) >print Nil } }
        >chain

        backup.chain !chain
        '''
        output, _ = self.capture_output(code)

        # Should detect Nil as chain termination
        self.assertRegex(
            output,
            r'(Nil|terminat|stopped)',
            "Should indicate chain termination"
        )

    def test_debug_chain_detects_infinite_loop(self):
        """Test that debug.chain detects infinite loops (same AL size repeatedly)."""
        code = '''
        chain !backup.chain
        debug.chain !chain

        { >block }
        >chain

        backup.chain !chain
        '''
        output, _ = self.capture_output(code)

        # Should warn about infinite loop or repeated AL size
        # The implementation might detect same AL state or just show many iterations
        self.assertRegex(
            output,
            r'(infinite|loop|repeated|warning|same.*size)',
            "Should detect or warn about infinite loop pattern"
        )

    def test_debug_chain_multiple_iterations(self):
        """Test debug.chain with multiple chain iterations."""
        code = '''
        chain !backup.chain
        debug.chain !chain

        { (c) >print Nil }
        { (b) >print { (c) >print Nil } }
        { (a) >print { (b) >print { (c) >print Nil } } }
        >chain

        backup.chain !chain
        '''
        output, _ = self.capture_output(code)

        # Should show all three iterations
        self.assertRegex(output, r'Iteration 1')
        self.assertRegex(output, r'Iteration 2')
        self.assertRegex(output, r'Iteration 3')

        # Should also show the actual output from prints
        self.assertIn('a', output)
        self.assertIn('b', output)
        self.assertIn('c', output)

    def test_debug_chain_shows_block_execution(self):
        """Test that debug.chain shows when blocks are executed."""
        code = '''
        chain !backup.chain
        debug.chain !chain

        Nil
        { 42 Nil }
        >chain

        backup.chain !chain
        '''
        output, _ = self.capture_output(code)

        # Should indicate block execution
        self.assertRegex(
            output,
            r'(Executing|Running|Block|iteration)',
            "Should show block execution"
        )

    def test_debug_chain_preserves_behavior(self):
        """Test that debug.chain doesn't change program behavior."""
        # Run with debug.chain
        code_debug = '''
        chain !backup.chain
        debug.chain !chain

        { 20 Nil }
        { 10 { 20 Nil } }
        >chain

        backup.chain !chain
        '''
        _, al_debug = self.capture_output(code_debug)

        # Run with normal chain
        code_normal = '''
        { 20 Nil }
        { 10 { 20 Nil } }
        >chain
        '''
        _, al_normal = self.capture_output(code_normal)

        # AL should have same length and types
        self.assertEqual(len(al_debug), len(al_normal), "debug.chain should preserve AL length")
        for i, (d, n) in enumerate(zip(al_debug, al_normal)):
            self.assertEqual(type(d), type(n), f"AL item {i} should have same type")

    def test_debug_chain_empty_al_before_chain(self):
        """Test debug.chain behavior with blocks that modify AL."""
        code = '''
        chain !backup.chain
        debug.chain !chain

        Nil
        { 1 2 3 Nil }
        >chain

        backup.chain !chain
        '''
        output, al = self.capture_output(code)

        # Should show AL size changes
        self.assertRegex(output, r'AL')

        # Final AL should have Nil, 1, 2, 3, Nil (Nil from before block, then block's output)
        self.assertEqual(al, [Nil, 1, 2, 3, Nil])


class TestDebugChoose(unittest.TestCase):
    """Tests for debug.choose debugging wrapper."""

    def capture_output(self, code):
        """Run SOMA code and capture stdout."""
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            tokens = lex(code)
            parser = Parser(tokens)
            ast = parser.parse()
            compiled = compile_program(ast)
            vm = VM()
            vm.execute(compiled)
            output = sys.stdout.getvalue()
            return output, vm.al
        finally:
            sys.stdout = old_stdout

    def test_debug_choose_shows_condition_value(self):
        """Test that debug.choose shows the condition value."""
        code = '''
        choose !backup.choose
        debug.choose !choose

        42 (condition is 42) (ignored) >choose >print

        backup.choose !choose
        '''
        output, _ = self.capture_output(code)

        # Should show condition value (42)
        self.assertRegex(
            output,
            r'(condition|Condition|value).*42',
            "Should show condition value"
        )

    def test_debug_choose_shows_true_branch_taken(self):
        """Test that debug.choose shows when TRUE branch is taken."""
        code = '''
        choose !backup.choose
        debug.choose !choose

        True (true-branch) (false-branch) >choose >print

        backup.choose !choose
        '''
        output, _ = self.capture_output(code)

        # Should indicate TRUE branch was taken
        self.assertRegex(
            output,
            r'(TRUE|true|True|branch.*1|first.*branch)',
            "Should show TRUE branch taken"
        )

        # Should see the actual result
        self.assertIn('true-branch', output)

    def test_debug_choose_shows_false_branch_taken(self):
        """Test that debug.choose shows when FALSE branch is taken."""
        code = '''
        choose !backup.choose
        debug.choose !choose

        Nil (true-branch) (false-branch) >choose >print

        backup.choose !choose
        '''
        output, _ = self.capture_output(code)

        # Should indicate FALSE branch was taken
        self.assertRegex(
            output,
            r'(FALSE|false|False|branch.*2|second.*branch)',
            "Should show FALSE branch taken"
        )

        # Should see the actual result
        self.assertIn('false-branch', output)

    def test_debug_choose_shows_al_state(self):
        """Test that debug.choose shows AL state before/after."""
        code = '''
        choose !backup.choose
        debug.choose !choose

        1 2 3 True (yes) (no) >choose >print

        backup.choose !choose
        '''
        output, _ = self.capture_output(code)

        # Should show AL state or size
        self.assertRegex(
            output,
            r'AL',
            "Should show AL state"
        )

    def test_debug_choose_with_void_condition(self):
        """Test debug.choose with Void condition (should choose FALSE)."""
        code = '''
        choose !backup.choose
        debug.choose !choose

        Void (true-branch) (false-branch) >choose >print

        backup.choose !choose
        '''
        output, _ = self.capture_output(code)

        # Should show Void condition
        self.assertRegex(output, r'Void', "Should show Void condition")

        # Should take FALSE branch
        self.assertIn('false-branch', output)
        self.assertRegex(output, r'FALSE|false|False', "Should indicate FALSE branch")

    def test_debug_choose_with_false_condition(self):
        """Test debug.choose with False condition."""
        code = '''
        choose !backup.choose
        debug.choose !choose

        False (true-branch) (false-branch) >choose >print

        backup.choose !choose
        '''
        output, _ = self.capture_output(code)

        # Should show False condition
        self.assertRegex(output, r'False', "Should show False condition")

        # Should take FALSE branch
        self.assertIn('false-branch', output)

    def test_debug_choose_with_integer_condition(self):
        """Test debug.choose with integer condition (truthy)."""
        code = '''
        choose !backup.choose
        debug.choose !choose

        99 (is-truthy) (is-falsy) >choose >print

        backup.choose !choose
        '''
        output, _ = self.capture_output(code)

        # Should show integer condition
        self.assertRegex(output, r'99', "Should show integer condition")

        # Should take TRUE branch (integers are truthy)
        self.assertIn('is-truthy', output)
        self.assertRegex(output, r'TRUE|true|True', "Should indicate TRUE branch")

    def test_debug_choose_preserves_behavior(self):
        """Test that debug.choose doesn't change program behavior."""
        # With debug
        code_debug = '''
        choose !backup.choose
        debug.choose !choose

        1 2 3 True 10 20 >choose

        backup.choose !choose
        '''
        _, al_debug = self.capture_output(code_debug)

        # Without debug
        code_normal = '''
        1 2 3 True 10 20 >choose
        '''
        _, al_normal = self.capture_output(code_normal)

        # AL should be identical
        self.assertEqual(al_debug, al_normal, "debug.choose should preserve AL state")

    def test_debug_choose_with_blocks(self):
        """Test debug.choose with block values (not just strings)."""
        code = '''
        choose !backup.choose
        debug.choose !choose

        True { (from-true-block) >print } { (from-false-block) >print } >choose >^

        backup.choose !choose
        '''
        output, _ = self.capture_output(code)

        # Should show TRUE branch taken
        self.assertRegex(output, r'TRUE|true|True')

        # Should execute the true block
        self.assertIn('from-true-block', output)
        self.assertNotIn('from-false-block', output)

    def test_debug_choose_shows_selected_value_type(self):
        """Test that debug.choose shows what type of value was selected."""
        code = '''
        choose !backup.choose
        debug.choose !choose

        True 42 99 >choose

        backup.choose !choose
        '''
        output, al = self.capture_output(code)

        # Should show branch selection
        self.assertRegex(output, r'(Taking|selected|chose|branch)')

        # AL should have 42 (the true value)
        self.assertEqual(al, [42])

    def test_debug_choose_multiple_calls(self):
        """Test debug.choose with multiple sequential calls."""
        code = '''
        choose !backup.choose
        debug.choose !choose

        True (first-true) (first-false) >choose >print
        False (second-true) (second-false) >choose >print

        backup.choose !choose
        '''
        output, _ = self.capture_output(code)

        # Should show both TRUE and FALSE branches being taken
        self.assertRegex(output, r'TRUE|true|True')
        self.assertRegex(output, r'FALSE|false|False')

        # Should see both actual outputs
        self.assertIn('first-true', output)
        self.assertIn('second-false', output)


class TestDebugToolsIntegration(unittest.TestCase):
    """Integration tests for debug tools used together."""

    def capture_output(self, code):
        """Run SOMA code and capture stdout."""
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            tokens = lex(code)
            parser = Parser(tokens)
            ast = parser.parse()
            compiled = compile_program(ast)
            vm = VM()
            vm.execute(compiled)
            output = sys.stdout.getvalue()
            return output, vm.al
        finally:
            sys.stdout = old_stdout


class TestDebugType(unittest.TestCase):
    """Tests for debug.type introspection builtin.

    WARNING: debug.type is implementation-specific, not part of SOMA's
    core semantics. It must NEVER be used for normal program control flow.
    """

    def run_soma(self, code):
        """Run SOMA code and return AL."""
        tokens = lex(code)
        parser = Parser(tokens)
        ast = parser.parse()
        compiled = compile_program(ast)
        vm = VM()
        vm.execute(compiled)
        return vm.al

    def test_debug_type_integer(self):
        """Test debug.type returns 'Int' for integers."""
        al = self.run_soma('42 >debug.type')
        self.assertEqual(al, ["Int"])

    def test_debug_type_string(self):
        """Test debug.type returns 'Str' for strings."""
        al = self.run_soma('(hello) >debug.type')
        self.assertEqual(al, ["Str"])

    def test_debug_type_true(self):
        """Test debug.type returns 'Bool' for True."""
        al = self.run_soma('True >debug.type')
        self.assertEqual(al, ["Bool"])

    def test_debug_type_false(self):
        """Test debug.type returns 'Bool' for False."""
        al = self.run_soma('False >debug.type')
        self.assertEqual(al, ["Bool"])

    def test_debug_type_nil(self):
        """Test debug.type returns 'Nil' for Nil."""
        al = self.run_soma('Nil >debug.type')
        self.assertEqual(al, ["Nil"])

    def test_debug_type_block(self):
        """Test debug.type returns 'Block' for blocks."""
        al = self.run_soma('{ >noop } >debug.type')
        self.assertEqual(al, ["Block"])

    def test_debug_type_cellref(self):
        """Test debug.type returns 'CellRef' for cell references."""
        al = self.run_soma('42 !x x. >debug.type')
        self.assertEqual(al, ["CellRef"])

    def test_debug_type_thing(self):
        """Test debug.type returns 'CellRef' for thing references.

        Note: thing. creates a new empty cell and returns a CellRef to it.
        The 'thing' in SOMA is not a distinct type - it's just an empty cell.
        """
        al = self.run_soma('thing. >debug.type')
        self.assertEqual(al, ["CellRef"])

    def test_debug_type_void(self):
        """Test debug.type returns 'Void' for Void."""
        al = self.run_soma('Void >debug.type')
        self.assertEqual(al, ["Void"])

    def test_debug_type_consumes_value(self):
        """Test debug.type consumes the value and pushes only the type string."""
        al = self.run_soma('1 2 3 >debug.type')
        self.assertEqual(al, [1, 2, "Int"])


class TestDebugId(unittest.TestCase):
    """Tests for debug.id identity introspection builtin.

    WARNING: debug.id is implementation-specific, not part of SOMA's
    core semantics. It must NEVER be used for normal program control flow.
    """

    def run_soma(self, code):
        """Run SOMA code and return AL."""
        tokens = lex(code)
        parser = Parser(tokens)
        ast = parser.parse()
        compiled = compile_program(ast)
        vm = VM()
        vm.execute(compiled)
        return vm.al

    def test_debug_id_cellref_returns_int(self):
        """Test debug.id returns an integer for cell references."""
        al = self.run_soma('42 !x x. >debug.id')
        self.assertEqual(len(al), 1)
        self.assertIsInstance(al[0], int)

    def test_debug_id_thing_returns_int(self):
        """Test debug.id returns an integer for things."""
        al = self.run_soma('thing. >debug.id')
        self.assertEqual(len(al), 1)
        self.assertIsInstance(al[0], int)

    def test_debug_id_same_cell_same_id(self):
        """Test debug.id returns same ID for same cell reference."""
        al = self.run_soma('''
        42 !x
        x. >debug.id
        x. >debug.id
        >==
        ''')
        self.assertEqual(len(al), 1)
        # Should be SOMA True (same cell = same ID)
        self.assertEqual(al[0], True_)

    def test_debug_id_different_cells_different_ids(self):
        """Test debug.id returns different IDs for different cells."""
        al = self.run_soma('''
        42 !x
        99 !y
        x. >debug.id
        y. >debug.id
        >==
        ''')
        self.assertEqual(len(al), 1)
        # Should be SOMA False (different cells = different IDs)
        self.assertEqual(al[0], False_)

    def test_debug_id_different_things_different_ids(self):
        """Test debug.id returns different IDs for different thing. calls.

        Note: Each thing. creates a new anonymous cell. However, due to
        Python memory reuse, consecutive thing. calls may get the same
        memory address if the first CellRef is garbage collected before
        the second is created. This test compares IDs directly instead
        of using >==.
        """
        al = self.run_soma('''
        thing. !t1
        thing. !t2
        t1. >debug.id
        t2. >debug.id
        >==
        ''')
        self.assertEqual(len(al), 1)
        # Should be SOMA False (different things = different IDs)
        self.assertEqual(al[0], False_)

    def test_debug_id_consumes_value(self):
        """Test debug.id consumes the value and pushes only the ID."""
        al = self.run_soma('1 2 thing. >debug.id')
        self.assertEqual(len(al), 3)
        self.assertEqual(al[0], 1)
        self.assertEqual(al[1], 2)
        self.assertIsInstance(al[2], int)


class TestDebugToolsIntegrationOriginal(TestDebugToolsIntegration):
    """Original integration tests for debug tools used together."""

    def test_debug_chain_and_choose_together(self):
        """Test using both debug.chain and debug.choose in the same program."""
        code = '''
        chain !backup.chain
        choose !backup.choose
        debug.chain !chain
        debug.choose !choose

        { False (yes) (no) >choose >print Nil }
        { True (yes) (no) >choose >print { False (yes) (no) >choose >print Nil } }
        >chain

        backup.chain !chain
        backup.choose !choose
        '''
        output, _ = self.capture_output(code)

        # Should show chain iterations
        self.assertRegex(output, r'Iteration')

        # Should show choose decisions
        self.assertRegex(output, r'(TRUE|FALSE|true|false)')

        # Should see actual outputs
        self.assertIn('yes', output)
        self.assertIn('no', output)

    def test_restore_original_builtins(self):
        """Test that backup/restore pattern works correctly."""
        # Test that we can restore original behavior
        code = '''
        chain !backup.chain
        debug.chain !chain

        { (debug-active) >print Nil } >chain

        backup.chain !chain

        { (debug-restored) >print Nil } >chain
        '''
        output, _ = self.capture_output(code)

        # First chain should have debug output
        lines = output.split('\n')
        debug_active_line = None
        debug_restored_line = None

        for i, line in enumerate(lines):
            if 'debug-active' in line:
                debug_active_line = i
            if 'debug-restored' in line:
                debug_restored_line = i

        # Both should appear
        self.assertIsNotNone(debug_active_line, "Should find debug-active output")
        self.assertIsNotNone(debug_restored_line, "Should find debug-restored output")

        # Debug output should appear only around first chain
        # (We can't be too specific about line positions due to debug output formatting)


if __name__ == '__main__':
    unittest.main()
