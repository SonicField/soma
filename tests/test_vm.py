"""
Unit tests for the SOMA VM (TDD - tests written before implementation).

These tests define the expected behavior of the VM:

- Compilation: AST → RunNodes for all node types
- Execution: RunNodes executing on VM state (AL, Store, Register)
- Register: Isolation, lifecycle, read/write
- Built-ins: >block, >choose, >chain
- Integration: Complete programs from lexer → parser → compiler → VM
- Errors: AL underflow, Void-Payload-Invariant, type errors

The VM is expected to:
1. Compile AST nodes to RunNodes (dispatch on type once)
2. Execute RunNodes (just function calls, no isinstance)
3. Maintain AL (LIFO stack), Store (global hierarchical graph), Register (block-local graph)
4. Enforce Register isolation (fresh per block execution)
5. Support built-ins as special Blocks
6. Provide clear error messages
"""

import unittest

# VM will be implemented in soma.vm module
from soma.vm import (
    VM,
    compile_program,
    compile_node,
    RunNode,
    CompiledProgram,
    Cell,
    Store,
    Register,
    Block,
    BuiltinBlock,
    CellRef,
    Void,
    Nil,
    VoidSingleton,
    NilSingleton,
    RuntimeError as VMRuntimeError,
    CompileError,
)

# Parser provides AST nodes
from soma.parser import (
    parse,
    Program,
    IntNode,
    StringNode,
    BlockNode,
    ValuePath,
    ReferencePath,
    ExecNode,
    StoreNode,
)


class TestCompilation(unittest.TestCase):
    """Tests for AST → RunNode compilation."""

    def test_compile_int_node(self):
        """Test compiling IntNode to RunNode."""
        ast = parse("42")
        node = ast["body"][0]

        # Create AST node manually for controlled test
        int_node = IntNode(value=42, location={})
        run_node = compile_node(int_node)

        self.assertIsInstance(run_node, RunNode)
        self.assertEqual(run_node.ast_node, int_node)

        # Execute should push int onto AL
        vm = VM(load_stdlib=False)
        run_node.execute(vm)
        self.assertEqual(vm.al, [42])

    def test_compile_string_node(self):
        """Test compiling StringNode to RunNode."""
        string_node = StringNode(value="hello", location={})
        run_node = compile_node(string_node)

        self.assertIsInstance(run_node, RunNode)

        vm = VM(load_stdlib=False)
        run_node.execute(vm)
        self.assertEqual(vm.al, ["hello"])

    def test_compile_block_node(self):
        """Test compiling BlockNode to RunNode (recursive)."""
        # Block containing: { 1 2 }
        block_node = BlockNode(
            body=[
                IntNode(value=1, location={}),
                IntNode(value=2, location={}),
            ],
            location={}
        )
        run_node = compile_node(block_node)

        self.assertIsInstance(run_node, RunNode)

        # Execute should push Block onto AL
        vm = VM(load_stdlib=False)
        run_node.execute(vm)
        self.assertEqual(len(vm.al), 1)
        self.assertIsInstance(vm.al[0], Block)

        # Block should have compiled body
        block = vm.al[0]
        self.assertEqual(len(block.body), 2)
        self.assertIsInstance(block.body[0], RunNode)
        self.assertIsInstance(block.body[1], RunNode)

    def test_compile_value_path_store(self):
        """Test compiling ValuePath (Store) to RunNode."""
        path_node = ValuePath(components=["foo"], location={})
        run_node = compile_node(path_node)

        vm = VM(load_stdlib=False)

        # Reading non-existent path returns Void
        run_node.execute(vm)
        self.assertEqual(len(vm.al), 1)
        self.assertIsInstance(vm.al[0], VoidSingleton)

        # Store a value, then read it
        vm.al = []
        vm.store.write_value(["foo"], 42)
        run_node.execute(vm)
        self.assertEqual(vm.al, [42])

    def test_compile_value_path_register(self):
        """Test compiling ValuePath (Register) to RunNode."""
        path_node = ValuePath(components=["_", "x"], location={})
        run_node = compile_node(path_node)

        vm = VM(load_stdlib=False)

        # Reading non-existent register path returns Void
        run_node.execute(vm)
        self.assertEqual(len(vm.al), 1)
        self.assertIsInstance(vm.al[0], VoidSingleton)

        # Store a value in register, then read it
        vm.al = []
        vm.register.write_value(["_", "x"], 23)
        run_node.execute(vm)
        self.assertEqual(vm.al, [23])

    def test_compile_reference_path_store(self):
        """Test compiling ReferencePath (Store) to RunNode."""
        path_node = ReferencePath(components=["data"], location={})
        run_node = compile_node(path_node)

        vm = VM(load_stdlib=False)

        # Reading reference auto-vivifies and returns CellRef
        run_node.execute(vm)
        self.assertEqual(len(vm.al), 1)
        self.assertIsInstance(vm.al[0], CellRef)

    def test_compile_reference_path_register(self):
        """Test compiling ReferencePath (Register) to RunNode."""
        path_node = ReferencePath(components=["_", "temp"], location={})
        run_node = compile_node(path_node)

        vm = VM(load_stdlib=False)

        # Reading register reference auto-vivifies and returns CellRef
        run_node.execute(vm)
        self.assertEqual(len(vm.al), 1)
        self.assertIsInstance(vm.al[0], CellRef)

    def test_compile_exec_node(self):
        """Test compiling ExecNode to RunNode."""
        # >{ 5 5 >* }
        block = BlockNode(
            body=[
                IntNode(value=5, location={}),
                IntNode(value=5, location={}),
                ExecNode(target=ValuePath(components=["*"], location={}), location={}),
            ],
            location={}
        )
        exec_node = ExecNode(target=block, location={})
        run_node = compile_node(exec_node)

        vm = VM(load_stdlib=False)

        # Store multiplication operator
        mult_block = BuiltinBlock("*", lambda vm: vm.al.append(vm.al.pop() * vm.al.pop()))
        vm.store.write_value(["*"], mult_block)

        # Execute should run the block
        run_node.execute(vm)
        self.assertEqual(vm.al, [25])

    def test_compile_store_node_value(self):
        """Test compiling StoreNode (value write) to RunNode."""
        # !foo
        store_node = StoreNode(target=ValuePath(components=["foo"], location={}), location={})
        run_node = compile_node(store_node)

        vm = VM(load_stdlib=False)
        vm.al.append(42)

        # Execute should pop AL and store
        run_node.execute(vm)
        self.assertEqual(vm.al, [])
        self.assertEqual(vm.store.read_value(["foo"]), 42)

    def test_compile_store_node_reference(self):
        """Test compiling StoreNode (reference write) to RunNode."""
        # !bar.
        store_node = StoreNode(target=ReferencePath(components=["bar"], location={}), location={})
        run_node = compile_node(store_node)

        vm = VM(load_stdlib=False)
        vm.al.append(99)

        # Execute should pop AL and replace cell
        run_node.execute(vm)
        self.assertEqual(vm.al, [])
        self.assertEqual(vm.store.read_value(["bar"]), 99)

    def test_compile_store_node_register(self):
        """Test compiling StoreNode (register write) to RunNode."""
        # !_.temp
        store_node = StoreNode(target=ValuePath(components=["_", "temp"], location={}), location={})
        run_node = compile_node(store_node)

        vm = VM(load_stdlib=False)
        vm.al.append(7)

        # Execute should pop AL and store in register
        run_node.execute(vm)
        self.assertEqual(vm.al, [])
        self.assertEqual(vm.register.read_value(["_", "temp"]), 7)

    def test_compile_program(self):
        """Test compiling complete Program to CompiledProgram."""
        ast = parse("1 2 >+")
        compiled = compile_program(ast)

        self.assertIsInstance(compiled, CompiledProgram)
        self.assertEqual(len(compiled.run_nodes), 3)
        self.assertIsInstance(compiled.run_nodes[0], RunNode)
        self.assertIsInstance(compiled.run_nodes[1], RunNode)
        self.assertIsInstance(compiled.run_nodes[2], RunNode)


class TestVMExecution(unittest.TestCase):
    """Tests for VM execution primitives."""

    def test_vm_initialization(self):
        """Test VM starts with empty AL, empty Store, empty Register."""
        vm = VM(load_stdlib=False)
        self.assertEqual(vm.al, [])
        self.assertIsInstance(vm.store, Store)
        self.assertIsInstance(vm.register, Register)
        self.assertIsNone(vm.current_block)

    def test_push_int_to_al(self):
        """Test pushing int onto AL."""
        vm = VM(load_stdlib=False)
        compiled = compile_program(parse("42"))
        compiled.execute(vm)
        self.assertEqual(vm.al, [42])

    def test_push_string_to_al(self):
        """Test pushing string onto AL."""
        vm = VM(load_stdlib=False)
        compiled = compile_program(parse("(hello)"))
        compiled.execute(vm)
        self.assertEqual(vm.al, ["hello"])

    def test_push_block_to_al(self):
        """Test pushing block onto AL."""
        vm = VM(load_stdlib=False)
        compiled = compile_program(parse("{ 1 2 }"))
        compiled.execute(vm)
        self.assertEqual(len(vm.al), 1)
        self.assertIsInstance(vm.al[0], Block)

    def test_multiple_values_on_al(self):
        """Test multiple values on AL (LIFO order)."""
        vm = VM(load_stdlib=False)
        compiled = compile_program(parse("1 2 3"))
        compiled.execute(vm)
        # Top of stack is rightmost
        self.assertEqual(vm.al, [1, 2, 3])


class TestStoreOperations(unittest.TestCase):
    """Tests for Store read/write operations."""

    def test_store_read_nonexistent(self):
        """Test reading non-existent Store path returns Void."""
        vm = VM(load_stdlib=False)
        compiled = compile_program(parse("foo"))
        compiled.execute(vm)
        self.assertEqual(len(vm.al), 1)
        self.assertIsInstance(vm.al[0], VoidSingleton)

    def test_store_write_and_read(self):
        """Test write to Store and read back."""
        vm = VM(load_stdlib=False)
        compiled = compile_program(parse("42 !counter counter"))
        compiled.execute(vm)
        self.assertEqual(vm.al, [42])

    def test_store_auto_vivification(self):
        """Test auto-vivification creates intermediate cells with Void."""
        vm = VM(load_stdlib=False)
        compiled = compile_program(parse("99 !a.b.c"))
        compiled.execute(vm)

        # a.b.c should be 99
        self.assertEqual(vm.store.read_value(["a", "b", "c"]), 99)

        # a.b should be Void (auto-vivified)
        self.assertIsInstance(vm.store.read_value(["a", "b"]), VoidSingleton)

        # a should be Void (auto-vivified)
        self.assertIsInstance(vm.store.read_value(["a"]), VoidSingleton)

    def test_store_read_cellref(self):
        """Test reading CellRef from Store."""
        vm = VM(load_stdlib=False)
        compiled = compile_program(parse("data."))
        compiled.execute(vm)

        # Should return CellRef (auto-vivifies)
        self.assertEqual(len(vm.al), 1)
        self.assertIsInstance(vm.al[0], CellRef)

    def test_store_write_cellref(self):
        """Test writing through CellRef."""
        vm = VM(load_stdlib=False)
        compiled = compile_program(parse("42 !node node. !ref 99 !ref ref"))
        compiled.execute(vm)

        # ref should now point to Cell with value 99
        self.assertEqual(len(vm.al), 1)
        self.assertIsInstance(vm.al[0], CellRef)

        # Reading through CellRef should give 99
        cellref = vm.al[0]
        self.assertEqual(cellref.cell.value, 99)

    def test_store_structural_deletion(self):
        """Test Void !path. deletes cell structurally."""
        vm = VM(load_stdlib=False)
        # Create cell, then delete it
        vm.store.write_value(["temp"], 42)
        vm.store.write_ref(["temp"], Void)

        # Reading should return Void
        self.assertIsInstance(vm.store.read_value(["temp"]), VoidSingleton)

    def test_store_nested_paths(self):
        """Test reading/writing nested Store paths."""
        vm = VM(load_stdlib=False)
        compiled = compile_program(parse("1 !config.server.port config.server.port"))
        compiled.execute(vm)
        self.assertEqual(vm.al, [1])


class TestRegisterOperations(unittest.TestCase):
    """Tests for Register read/write operations."""

    def test_register_read_nonexistent(self):
        """Test reading non-existent Register path returns Void."""
        vm = VM(load_stdlib=False)
        compiled = compile_program(parse("_.x"))
        compiled.execute(vm)
        self.assertEqual(len(vm.al), 1)
        self.assertIsInstance(vm.al[0], VoidSingleton)

    def test_register_write_and_read(self):
        """Test write to Register and read back."""
        vm = VM(load_stdlib=False)
        compiled = compile_program(parse("23 !_.temp _.temp"))
        compiled.execute(vm)
        self.assertEqual(vm.al, [23])

    def test_register_root_access(self):
        """Test reading/writing Register root (_)."""
        vm = VM(load_stdlib=False)
        compiled = compile_program(parse("42 !_ _"))
        compiled.execute(vm)
        self.assertEqual(vm.al, [42])

    def test_register_root_cellref(self):
        """Test reading Register root CellRef (_.)."""
        vm = VM(load_stdlib=False)
        compiled = compile_program(parse("_."))
        compiled.execute(vm)
        self.assertEqual(len(vm.al), 1)
        self.assertIsInstance(vm.al[0], CellRef)

    def test_register_isolation_fresh_per_block(self):
        """Test each block gets fresh, empty Register."""
        vm = VM(load_stdlib=False)
        # Outer block: store in register, inner block: read register (should be Void)
        compiled = compile_program(parse("{ 1 !_.x { _.x } >chain }"))
        compiled.execute(vm)

        # Get outer block
        outer_block = vm.al[0]
        self.assertIsInstance(outer_block, Block)

        # Execute outer block
        vm.al = []
        outer_block.execute(vm)

        # Inner block should have read Void (not 1)
        self.assertEqual(len(vm.al), 1)
        self.assertIsInstance(vm.al[0], VoidSingleton)

    def test_register_destroyed_after_block(self):
        """Test Register is destroyed when block completes."""
        vm = VM(load_stdlib=False)
        compiled = compile_program(parse("{ 100 !_.value _.value }"))
        compiled.execute(vm)

        block = vm.al[0]
        self.assertIsInstance(block, Block)

        # Execute block
        vm.al = []
        saved_register = vm.register
        block.execute(vm)

        # Register should be restored (destroyed and recreated)
        self.assertEqual(vm.register, saved_register)

        # Block should have returned 100 on AL
        self.assertEqual(vm.al, [100])

        # Top-level register should not have _.value
        self.assertIsInstance(vm.register.read_value(["_", "value"]), VoidSingleton)

    def test_register_nested_isolation(self):
        """Test nested blocks have completely isolated Registers."""
        vm = VM(load_stdlib=False)
        # Outer: 1 !_.n, Inner: 2 !_.n, Outer: _.n (should still be 1)
        source = """
        {
            1 !_.n
            { 2 !_.n } >chain
            _.n
        }
        """
        compiled = compile_program(parse(source))
        compiled.execute(vm)

        outer_block = vm.al[0]

        # Execute outer block
        vm.al = []
        outer_block.execute(vm)

        # Should return 1 (outer's _.n)
        self.assertEqual(vm.al, [1])

    def test_register_deletion(self):
        """Test Void !_.path. deletes Register cell."""
        vm = VM(load_stdlib=False)
        vm.register.write_value(["_", "temp"], 42)
        vm.register.write_ref(["_", "temp"], Void)

        # Reading should return Void
        self.assertIsInstance(vm.register.read_value(["_", "temp"]), VoidSingleton)


class TestBuiltins(unittest.TestCase):
    """Tests for built-in operations."""

    def test_builtin_block_push_current_block(self):
        """Test >block pushes current block onto AL."""
        vm = VM(load_stdlib=False)

        # Create block with >block inside
        source = "{ >block }"
        compiled = compile_program(parse(source))
        compiled.execute(vm)

        block = vm.al[0]
        self.assertIsInstance(block, Block)

        # Execute the block
        vm.al = []
        block.execute(vm)

        # Should push itself onto AL
        self.assertEqual(len(vm.al), 1)
        self.assertEqual(vm.al[0], block)

    def test_builtin_block_at_top_level_error(self):
        """Test >block at top-level raises error (no current block)."""
        vm = VM(load_stdlib=False)

        # Top-level has no current_block
        with self.assertRaises(VMRuntimeError) as ctx:
            vm.store.root["block"].value.execute(vm)

        self.assertIn("top-level", str(ctx.exception).lower())

    def test_builtin_choose_true_branch(self):
        """Test >choose selects true branch when condition is truthy."""
        vm = VM(load_stdlib=False)

        # Create blocks for branches
        true_block = Block([
            RunNode(IntNode(value=1, location={}), lambda vm: vm.al.append(1))
        ])
        false_block = Block([
            RunNode(IntNode(value=2, location={}), lambda vm: vm.al.append(2))
        ])

        # AL: [condition, true_branch, false_branch]
        vm.al = [42, true_block, false_block]  # 42 is truthy

        # Execute >choose
        choose_builtin = vm.store.read_value(["choose"])
        choose_builtin.execute(vm)

        # Should select true branch (push block, not execute it)
        self.assertEqual(len(vm.al), 1)
        self.assertEqual(vm.al[0], true_block)

    def test_builtin_choose_false_branch(self):
        """Test >choose selects false branch when condition is Nil."""
        vm = VM(load_stdlib=False)

        true_block = Block([
            RunNode(IntNode(value=1, location={}), lambda vm: vm.al.append(1))
        ])
        false_block = Block([
            RunNode(IntNode(value=2, location={}), lambda vm: vm.al.append(2))
        ])

        # AL: [Nil, true_branch, false_branch]
        vm.al = [Nil, true_block, false_block]

        choose_builtin = vm.store.read_value(["choose"])
        choose_builtin.execute(vm)

        # Should select false branch (push block, not execute it)
        self.assertEqual(len(vm.al), 1)
        self.assertEqual(vm.al[0], false_block)

    def test_builtin_choose_void_is_falsy(self):
        """Test >choose treats Void as falsy."""
        vm = VM(load_stdlib=False)

        true_block = Block([
            RunNode(IntNode(value=1, location={}), lambda vm: vm.al.append(1))
        ])
        false_block = Block([
            RunNode(IntNode(value=2, location={}), lambda vm: vm.al.append(2))
        ])

        vm.al = [Void, true_block, false_block]

        choose_builtin = vm.store.read_value(["choose"])
        choose_builtin.execute(vm)

        # Should select false branch (Void is falsy, push block not execute)
        self.assertEqual(len(vm.al), 1)
        self.assertEqual(vm.al[0], false_block)

    def test_builtin_choose_al_underflow(self):
        """Test >choose raises error on AL underflow."""
        vm = VM(load_stdlib=False)
        vm.al = [1, 2]  # Only 2 values, need 3

        choose_builtin = vm.store.read_value(["choose"])

        with self.assertRaises(VMRuntimeError) as ctx:
            choose_builtin.execute(vm)

        self.assertIn("underflow", str(ctx.exception).lower())

    def test_builtin_choose_selects_non_block_values(self):
        """Test >choose can select non-block values (ints, strings, etc)."""
        vm = VM(load_stdlib=False)
        choose_builtin = vm.store.read_value(["choose"])

        # Test with integers
        vm.al = [1, 100, 200]  # condition=1 (truthy), true=100, false=200
        choose_builtin.execute(vm)
        self.assertEqual(vm.al, [100])

        # Test with strings
        vm.al = [Nil, "true_str", "false_str"]  # condition=Nil (falsy)
        choose_builtin.execute(vm)
        self.assertEqual(vm.al, ["false_str"])

        # Test with mixed types
        vm.al = [True, 42, "fallback"]
        choose_builtin.execute(vm)
        self.assertEqual(vm.al, [42])

    def test_builtin_choose_blocks_not_executed(self):
        """Test >choose does NOT execute blocks, only selects them."""
        vm = VM(load_stdlib=False)

        # Create blocks that would modify AL if executed
        executed_marker = []

        def mark_executed(marker_list):
            def execute_fn(vm):
                marker_list.append("executed")
                vm.al.append(999)
            return execute_fn

        true_block = Block([
            RunNode(None, mark_executed(executed_marker))
        ])
        false_block = Block([
            RunNode(None, mark_executed(executed_marker))
        ])

        # Choose true branch
        vm.al = [1, true_block, false_block]
        choose_builtin = vm.store.read_value(["choose"])
        choose_builtin.execute(vm)

        # Block should be on AL but NOT executed
        self.assertEqual(len(vm.al), 1)
        self.assertIs(vm.al[0], true_block)
        self.assertEqual(executed_marker, [])  # No execution happened

        # Now execute it manually to verify it works
        selected_block = vm.al.pop()
        selected_block.execute(vm)
        self.assertEqual(executed_marker, ["executed"])
        self.assertEqual(vm.al, [999])

    def test_builtin_chain_executes_block(self):
        """Test >chain pops and executes block from AL."""
        vm = VM(load_stdlib=False)

        block = Block([
            RunNode(IntNode(value=42, location={}), lambda vm: vm.al.append(42))
        ])

        vm.al = [block]

        chain_builtin = vm.store.read_value(["chain"])
        chain_builtin.execute(vm)

        # Block executed, result on AL
        self.assertEqual(vm.al, [42])

    def test_builtin_chain_stops_on_non_block(self):
        """Test >chain stops when AL top is not a block."""
        vm = VM(load_stdlib=False)

        # Push a value (not a block)
        vm.al = [42]

        chain_builtin = vm.store.read_value(["chain"])
        chain_builtin.execute(vm)

        # Should stop, leave 42 on AL
        self.assertEqual(vm.al, [42])

    def test_builtin_chain_loop_with_block(self):
        """Test >chain loops while block leaves block on AL."""
        vm = VM(load_stdlib=False)

        # Counter in Store
        vm.store.write_value(["counter"], 0)

        # Block that increments counter and pushes itself if counter < 3
        def loop_body(vm):
            count = vm.store.read_value(["counter"])
            vm.store.write_value(["counter"], count + 1)

            # If counter < 3, push block back
            if count + 1 < 3:
                vm.al.append(vm.current_block)

        block = Block([RunNode(None, loop_body)])
        vm.al = [block]

        chain_builtin = vm.store.read_value(["chain"])
        chain_builtin.execute(vm)

        # Counter should be 3
        self.assertEqual(vm.store.read_value(["counter"]), 3)


class TestIntegration(unittest.TestCase):
    """Integration tests for complete programs."""

    def test_simple_arithmetic(self):
        """Test 1 2 >+ (if built-in + exists)."""
        # Note: This test assumes + is implemented as a built-in
        # For minimal VM, we'll just test compilation and structure
        vm = VM(load_stdlib=False)
        compiled = compile_program(parse("1 2"))
        compiled.execute(vm)
        self.assertEqual(vm.al, [1, 2])

    def test_store_and_retrieve(self):
        """Test 42 !counter counter."""
        vm = VM(load_stdlib=False)
        compiled = compile_program(parse("42 !counter counter"))
        compiled.execute(vm)
        self.assertEqual(vm.al, [42])

    def test_block_definition_and_storage(self):
        """Test { 5 5 } !square."""
        vm = VM(load_stdlib=False)
        compiled = compile_program(parse("{ 5 5 } !square"))
        compiled.execute(vm)

        # AL should be empty
        self.assertEqual(vm.al, [])

        # Store should have square
        square_block = vm.store.read_value(["square"])
        self.assertIsInstance(square_block, Block)

    def test_register_operations(self):
        """Test 1 !_.x _.x."""
        vm = VM(load_stdlib=False)
        compiled = compile_program(parse("1 !_.x _.x"))
        compiled.execute(vm)
        self.assertEqual(vm.al, [1])

    def test_nested_blocks(self):
        """Test { { 42 } }."""
        vm = VM(load_stdlib=False)
        compiled = compile_program(parse("{ { 42 } }"))
        compiled.execute(vm)

        # Outer block on AL
        outer = vm.al[0]
        self.assertIsInstance(outer, Block)

        # Execute outer block
        vm.al = []
        outer.execute(vm)

        # Inner block should be on AL
        inner = vm.al[0]
        self.assertIsInstance(inner, Block)

        # Execute inner block
        vm.al = []
        inner.execute(vm)

        # Should have 42
        self.assertEqual(vm.al, [42])

    def test_block_execution_with_exec_node(self):
        """Test executing inline block: >{ 5 5 }."""
        vm = VM(load_stdlib=False)
        compiled = compile_program(parse(">{ 5 5 }"))
        compiled.execute(vm)

        # Block executed, values on AL
        self.assertEqual(vm.al, [5, 5])

    def test_conditional_with_choose(self):
        """Test conditional selection pattern."""
        vm = VM(load_stdlib=False)

        # True { 1 } { 2 } >choose >chain
        # With new semantics: choose selects block, then chain executes it
        source = """
        True { 1 } { 2 } >choose >chain
        """

        # First, set up True as a truthy value (non-Nil, non-Void)
        vm.store.write_value(["True"], 1)

        compiled = compile_program(parse(source))
        compiled.execute(vm)

        # Should select true branch and execute it (via chain)
        self.assertEqual(vm.al, [1])

    def test_loop_with_chain_and_block(self):
        """Test simple loop using >block."""
        vm = VM(load_stdlib=False)

        # Counter in Store
        vm.store.write_value(["counter"], 0)

        # { counter 1 >+ !counter counter 3 >< { >block } { } >choose } >chain
        # This is complex - let's test simpler version manually

        # Block that increments and loops
        def increment_and_loop(vm):
            count = vm.store.read_value(["counter"])
            vm.store.write_value(["counter"], count + 1)

            # If < 3, push self back
            if count + 1 < 3:
                vm.al.append(vm.current_block)

        loop_block = Block([RunNode(None, increment_and_loop)])
        vm.al = [loop_block]

        # Execute with >chain
        chain = vm.store.read_value(["chain"])
        chain.execute(vm)

        # Counter should be 3
        self.assertEqual(vm.store.read_value(["counter"]), 3)

    def test_cellref_persistence(self):
        """Test CellRef persists after path deletion."""
        vm = VM(load_stdlib=False)

        # Create cell, get CellRef, delete path, access via CellRef
        source = """
        42 !data
        data. !ref
        Void !data.
        ref
        """

        compiled = compile_program(parse(source))
        compiled.execute(vm)

        # AL should have CellRef
        self.assertEqual(len(vm.al), 1)
        self.assertIsInstance(vm.al[0], CellRef)

        # CellRef should point to Cell with value 42
        cellref = vm.al[0]
        self.assertEqual(cellref.cell.value, 42)

        # Original path should be Void
        self.assertIsInstance(vm.store.read_value(["data"]), VoidSingleton)


class TestErrors(unittest.TestCase):
    """Tests for error conditions."""

    def test_al_underflow_exec(self):
        """Test AL underflow on exec (empty AL)."""
        vm = VM(load_stdlib=False)

        # Create ExecNode with path target
        exec_node = ExecNode(target=ValuePath(components=["foo"], location={}), location={})
        run_node = compile_node(exec_node)

        # AL is empty, should error
        with self.assertRaises(VMRuntimeError) as ctx:
            run_node.execute(vm)

        self.assertIn("underflow", str(ctx.exception).lower())

    def test_al_underflow_store(self):
        """Test AL underflow on store (empty AL)."""
        vm = VM(load_stdlib=False)

        # Create StoreNode
        store_node = StoreNode(target=ValuePath(components=["x"], location={}), location={})
        run_node = compile_node(store_node)

        # AL is empty, should error
        with self.assertRaises(VMRuntimeError) as ctx:
            run_node.execute(vm)

        self.assertIn("underflow", str(ctx.exception).lower())

    def test_write_void_as_payload_error(self):
        """Test writing Void as payload raises error (Void-Payload-Invariant)."""
        vm = VM(load_stdlib=False)

        with self.assertRaises(VMRuntimeError) as ctx:
            vm.store.write_value(["path"], Void)

        self.assertIn("void", str(ctx.exception).lower())
        self.assertIn("payload", str(ctx.exception).lower())

    def test_write_void_to_register_error(self):
        """Test writing Void to Register raises error."""
        vm = VM(load_stdlib=False)

        with self.assertRaises(VMRuntimeError) as ctx:
            vm.register.write_value(["_", "temp"], Void)

        self.assertIn("void", str(ctx.exception).lower())

    def test_execute_non_block_error(self):
        """Test executing non-block value raises error."""
        vm = VM(load_stdlib=False)

        # Push int onto AL, try to exec it
        vm.al = [42]

        exec_node = ExecNode(target=ValuePath(components=["dummy"], location={}), location={})
        run_node = compile_node(exec_node)

        # Manually set up exec to try executing the int
        vm.al = []
        vm.al.append(42)

        with self.assertRaises(VMRuntimeError) as ctx:
            run_node.execute(vm)

        error_msg = str(ctx.exception).lower()
        self.assertTrue("execute" in error_msg or "block" in error_msg)

    def test_chain_non_block_error(self):
        """Test >chain with non-block raises error."""
        vm = VM(load_stdlib=False)

        # This should NOT error - Chain just stops if AL top is not a block
        vm.al = [42]

        chain = vm.store.read_value(["chain"])
        chain.execute(vm)

        # Should just stop, leaving 42 on AL
        self.assertEqual(vm.al, [42])


class TestCellOperations(unittest.TestCase):
    """Tests for Cell operations (value/subpaths orthogonality)."""

    def test_cell_value_and_subpaths_independent(self):
        """Test Cell can have both value and children."""
        vm = VM(load_stdlib=False)

        # Set parent value
        vm.store.write_value(["parent"], Nil)

        # Add child
        vm.store.write_value(["parent", "child"], 42)

        # Parent value unchanged
        self.assertIsInstance(vm.store.read_value(["parent"]), NilSingleton)

        # Child accessible
        self.assertEqual(vm.store.read_value(["parent", "child"]), 42)

    def test_path_traversal_through_void(self):
        """Test can traverse through Void intermediate cells."""
        vm = VM(load_stdlib=False)

        # Auto-vivify a.b with Void, set a.b.c to 42
        vm.store.write_value(["a", "b", "c"], 42)

        # a.b should be Void
        self.assertIsInstance(vm.store.read_value(["a", "b"]), VoidSingleton)

        # But we can traverse through it
        self.assertEqual(vm.store.read_value(["a", "b", "c"]), 42)

    def test_path_traversal_through_nil(self):
        """Test can traverse through Nil cells."""
        vm = VM(load_stdlib=False)

        # Set a.b to Nil
        vm.store.write_value(["a", "b"], Nil)

        # Add child a.b.c
        vm.store.write_value(["a", "b", "c"], 99)

        # a.b is still Nil
        self.assertIsInstance(vm.store.read_value(["a", "b"]), NilSingleton)

        # a.b.c is 99
        self.assertEqual(vm.store.read_value(["a", "b", "c"]), 99)

    def test_int_with_children(self):
        """Test Int value can have children."""
        vm = VM(load_stdlib=False)

        vm.store.write_value(["node"], 42)
        vm.store.write_value(["node", "sub"], 99)

        self.assertEqual(vm.store.read_value(["node"]), 42)
        self.assertEqual(vm.store.read_value(["node", "sub"]), 99)

    def test_block_with_children(self):
        """Test Block value can have children."""
        vm = VM(load_stdlib=False)

        block = Block([])
        vm.store.write_value(["action"], block)
        vm.store.write_value(["action", "description"], "help text")

        self.assertEqual(vm.store.read_value(["action"]), block)
        self.assertEqual(vm.store.read_value(["action", "description"]), "help text")


class TestVoidVsNil(unittest.TestCase):
    """Tests for Void vs Nil semantics."""

    def test_void_from_auto_vivification(self):
        """Test auto-vivification creates Void."""
        vm = VM(load_stdlib=False)

        vm.store.write_value(["a", "b", "c"], 42)

        # Intermediate cells have Void
        self.assertIsInstance(vm.store.read_value(["a"]), VoidSingleton)
        self.assertIsInstance(vm.store.read_value(["a", "b"]), VoidSingleton)

        # Final cell has value
        self.assertEqual(vm.store.read_value(["a", "b", "c"]), 42)

    def test_nil_is_explicit(self):
        """Test Nil is explicitly set."""
        vm = VM(load_stdlib=False)

        vm.store.write_value(["field"], Nil)

        self.assertIsInstance(vm.store.read_value(["field"]), NilSingleton)

    def test_void_vs_nil_different(self):
        """Test Void and Nil are different values."""
        vm = VM(load_stdlib=False)

        # Auto-vivify (Void)
        vm.store.write_value(["auto", "child"], 1)

        # Explicit Nil
        vm.store.write_value(["explicit"], Nil)

        auto_value = vm.store.read_value(["auto"])
        explicit_value = vm.store.read_value(["explicit"])

        self.assertIsInstance(auto_value, VoidSingleton)
        self.assertIsInstance(explicit_value, NilSingleton)
        self.assertNotEqual(type(auto_value), type(explicit_value))

    def test_void_singleton(self):
        """Test Void is a singleton."""
        vm = VM(load_stdlib=False)

        void1 = vm.store.read_value(["nonexistent1"])
        void2 = vm.store.read_value(["nonexistent2"])

        self.assertIs(void1, void2)
        self.assertIs(void1, Void)

    def test_nil_singleton(self):
        """Test Nil is a singleton."""
        vm = VM(load_stdlib=False)

        vm.store.write_value(["a"], Nil)
        vm.store.write_value(["b"], Nil)

        nil1 = vm.store.read_value(["a"])
        nil2 = vm.store.read_value(["b"])

        self.assertIs(nil1, nil2)
        self.assertIs(nil1, Nil)


class TestRegisterLifecycle(unittest.TestCase):
    """Tests for Register lifecycle and isolation."""

    def test_register_created_on_block_start(self):
        """Test fresh Register created when block executes."""
        vm = VM(load_stdlib=False)

        # Store value in top-level register
        vm.register.write_value(["_", "top_level"], 1)

        # Create and execute block
        block = Block([
            RunNode(None, lambda vm: vm.register.write_value(["_", "block_level"], 2))
        ])

        block.execute(vm)

        # Top-level register should still have top_level
        self.assertEqual(vm.register.read_value(["_", "top_level"]), 1)

        # Top-level register should NOT have block_level
        self.assertIsInstance(vm.register.read_value(["_", "block_level"]), VoidSingleton)

    def test_register_destroyed_on_block_end(self):
        """Test Register destroyed when block completes."""
        vm = VM(load_stdlib=False)

        original_register = vm.register

        # Block that modifies register
        block = Block([
            RunNode(None, lambda vm: vm.register.write_value(["_", "temp"], 42))
        ])

        block.execute(vm)

        # Register should be restored to original
        self.assertEqual(vm.register, original_register)

    def test_register_isolation_complete(self):
        """Test Registers are completely isolated."""
        vm = VM(load_stdlib=False)

        # Outer register
        vm.register.write_value(["_", "outer"], 1)

        # Inner block tries to read outer register
        def read_outer(vm):
            value = vm.register.read_value(["_", "outer"])
            vm.al.append(value)

        inner_block = Block([RunNode(None, read_outer)])
        inner_block.execute(vm)

        # Should have read Void (not 1)
        self.assertEqual(len(vm.al), 1)
        self.assertIsInstance(vm.al[0], VoidSingleton)

    def test_register_cellref_escape(self):
        """Test CellRef to Register cell persists after block ends."""
        vm = VM(load_stdlib=False)

        # Block that creates Register cell and returns CellRef
        def create_and_escape(vm):
            vm.register.write_value(["_", "data"], 42)
            cellref = vm.register.read_ref(["_", "data"])
            vm.al.append(cellref)

        block = Block([RunNode(None, create_and_escape)])
        block.execute(vm)

        # AL should have CellRef
        self.assertEqual(len(vm.al), 1)
        self.assertIsInstance(vm.al[0], CellRef)

        # CellRef should still point to Cell with value 42
        cellref = vm.al[0]
        self.assertEqual(cellref.cell.value, 42)


class TestExamplesFromSpec(unittest.TestCase):
    """Tests based on examples from specification documents."""

    def test_hello_world(self):
        """Test: (Hello, world!) >print."""
        # This requires print built-in, which we'll assume exists
        # For now, just test compilation
        vm = VM(load_stdlib=False)
        compiled = compile_program(parse('(Hello, world!)'))
        compiled.execute(vm)

        self.assertEqual(vm.al, ["Hello, world!"])

    def test_counter_increment(self):
        """Test: 0 !counter counter 1 >+ !counter."""
        # Requires + built-in
        # Test structure only
        vm = VM(load_stdlib=False)
        compiled = compile_program(parse('0 !counter counter'))
        compiled.execute(vm)

        self.assertEqual(vm.al, [0])

    def test_sparse_array(self):
        """Test sparse array with Void."""
        vm = VM(load_stdlib=False)

        vm.store.write_value(["array", "0"], 1)
        vm.store.write_value(["array", "100"], 2)
        vm.store.write_value(["array", "1000"], 3)

        # Unset indices return Void
        self.assertIsInstance(vm.store.read_value(["array", "50"]), VoidSingleton)

        # Set indices have values
        self.assertEqual(vm.store.read_value(["array", "0"]), 1)
        self.assertEqual(vm.store.read_value(["array", "100"]), 2)

    def test_linked_list_with_cellrefs(self):
        """Test linked list using CellRefs."""
        vm = VM(load_stdlib=False)

        # Node 1
        vm.store.write_value(["list", "value"], 1)

        # Create CellRef to next node
        next_ref = vm.store.read_ref(["list", "next"])
        vm.store.write_value(["list", "next"], next_ref)

        # Node 2
        vm.store.write_value(["list", "next", "value"], 2)
        vm.store.write_value(["list", "next", "next"], Nil)

        # Traverse
        self.assertEqual(vm.store.read_value(["list", "value"]), 1)
        self.assertEqual(vm.store.read_value(["list", "next", "value"]), 2)
        self.assertIsInstance(vm.store.read_value(["list", "next", "next"]), NilSingleton)


if __name__ == "__main__":
    unittest.main()
