"""
SOMA Virtual Machine

Implements the runtime execution engine for SOMA programs using a compile-once,
execute-fast model with RunNodes.

Architecture:
1. Parse source -> AST (handled by parser.py)
2. Compile AST -> RunNodes (compile_program, compile_node)
3. Execute RunNodes (VM.execute)

This separates slow isinstance dispatch (compilation) from fast execution.
"""

from typing import List, Union, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum, auto

from soma.parser import (
    Program, IntNode, StringNode, BlockNode, ValuePath, ReferencePath,
    ExecNode, StoreNode
)


# ==================== Error Classes ====================


class RuntimeError(Exception):
    """Runtime error during VM execution."""
    pass


class CompileError(Exception):
    """Error during AST compilation to RunNodes."""
    pass


# ==================== Value Types ====================


class ThingType(Enum):
    """Value type tags for runtime type checking."""
    INT = auto()
    STRING = auto()
    BLOCK = auto()
    NIL = auto()
    VOID = auto()
    CELLREF = auto()
    FFI = auto()  # Foreign objects from invoke


class VoidSingleton:
    """
    Singleton representing 'never set' (auto-vivified cells).

    Void represents the state of a cell that has been created through
    auto-vivification but has never had a value explicitly written to it.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self):
        return "Void"


class NilSingleton:
    """
    Singleton representing 'explicitly set to empty'.

    Nil represents an explicit empty value, distinct from Void which
    represents 'never set'.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self):
        return "Nil"


class TrueSingleton:
    """
    Singleton representing boolean True.

    FFI built-in for boolean operations. In SOMA, True is used by
    comparison operators and can be tested in >choose.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self):
        return "True"


class FalseSingleton:
    """
    Singleton representing boolean False.

    FFI built-in for boolean operations. In SOMA, False is treated
    the same as Nil in conditional contexts.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self):
        return "False"


# Global singleton instances
Void = VoidSingleton()
Nil = NilSingleton()
True_ = TrueSingleton()
False_ = FalseSingleton()


@dataclass
class Block:
    """
    Executable block (first-class value).

    Contains compiled RunNodes for the block body.
    Blocks are immutable values that can be stored, passed around,
    and executed multiple times.

    Attributes:
        body: List of compiled RunNodes for the block body
    """
    body: List['RunNode']

    def execute(self, vm: 'VM'):
        """
        Execute this block in the given VM context.

        Creates a fresh Register for block-local state, executes all
        statements, then restores the previous register (destroying
        the block-local state).

        Args:
            vm: The VM instance to execute in
        """
        # Save current register and block context
        saved_register = vm.register
        saved_block = vm.current_block

        # Create fresh Register for this block
        vm.register = Register()
        vm.current_block = self

        try:
            # Execute block body
            for rn in self.body:
                rn.execute(vm)
        finally:
            # Restore register (block-local state destroyed)
            vm.register = saved_register
            vm.current_block = saved_block


@dataclass
class CellRef:
    """
    Reference to a Cell (not the value, the Cell itself).

    Immutable value that provides access to a Cell.
    The Cell persists as long as the CellRef exists (or the path exists
    in the Store/Register).

    Attributes:
        cell: The Cell being referenced
    """
    cell: 'Cell'

    def __repr__(self):
        return f"CellRef({id(self.cell)})"


@dataclass
class BuiltinBlock:
    """
    Special Block for built-in operations.

    Instead of RunNode body, has a Python function that operates on the VM.
    Used for built-in operations like >block, >choose, >chain.

    Attributes:
        name: Name of the built-in (for debugging/error messages)
        fn: Python function that takes a VM and performs the operation
    """
    name: str
    fn: Callable[['VM'], None]

    def execute(self, vm: 'VM'):
        """Execute built-in function."""
        self.fn(vm)

    def __repr__(self):
        return f"<builtin {self.name}>"


# Thing type union - any value that can live on the AL or in a Cell
Thing = Union[int, str, Block, VoidSingleton, NilSingleton, CellRef, BuiltinBlock, Any]


# ==================== Cell and Storage ====================


@dataclass
class Cell:
    """
    A Cell in the hierarchical graph.

    Has two orthogonal components:
    - value: The payload (any Thing)
    - children: Dict of sub-paths to child Cells

    A Cell can have both a value and children simultaneously.
    """
    value: Thing
    children: dict[str, 'Cell']

    def __init__(self, value: Thing = None):
        """
        Initialize a Cell with a value.

        Args:
            value: Initial value (defaults to Void if None)
        """
        if value is None:
            value = Void
        self.value = value
        self.children = {}


class Store:
    """
    Global hierarchical Cell graph.

    Persistent across entire program execution.
    Pre-populated with built-in operations.

    Provides value and reference access to the Cell graph with
    auto-vivification for paths.
    """

    def __init__(self):
        """Initialize Store with built-in operations."""
        self.root: dict[str, Cell] = {}
        self._populate_builtins()

    def _populate_builtins(self):
        """Pre-populate Store with built-in operations and constants."""
        # Core control flow built-ins
        block_builtin = BuiltinBlock("block", builtin_block)
        choose_builtin = BuiltinBlock("choose", builtin_choose)
        chain_builtin = BuiltinBlock("chain", builtin_chain)

        self.root["block"] = Cell(value=block_builtin)
        self.root["choose"] = Cell(value=choose_builtin)
        self.root["chain"] = Cell(value=chain_builtin)

        # Boolean constants and special values
        self.root["True"] = Cell(value=True_)
        self.root["False"] = Cell(value=False_)
        self.root["Nil"] = Cell(value=Nil)
        self.root["Void"] = Cell(value=Void)

        # Comparison operators
        self.root["<"] = Cell(value=BuiltinBlock("<", builtin_lt))

        # Arithmetic operators
        self.root["+"] = Cell(value=BuiltinBlock("+", builtin_add))
        self.root["-"] = Cell(value=BuiltinBlock("-", builtin_subtract))
        self.root["*"] = Cell(value=BuiltinBlock("*", builtin_multiply))
        self.root["/"] = Cell(value=BuiltinBlock("/", builtin_divide))
        self.root["%"] = Cell(value=BuiltinBlock("%", builtin_modulo))

        # I/O operations
        self.root["print"] = Cell(value=BuiltinBlock("print", builtin_print))
        self.root["readLine"] = Cell(value=BuiltinBlock("readLine", builtin_read_line))

        # Debug utilities (non-standard)
        if "debug" not in self.root:
            self.root["debug"] = Cell(value=Void)
        if "al" not in self.root["debug"].children:
            self.root["debug"].children["al"] = Cell(value=Void)
        self.root["debug"].children["al"].children["dump"] = Cell(value=BuiltinBlock("debug.al.dump", builtin_debug_al_dump))

        # Debug instrumented control flow primitives
        self.root["debug"].children["chain"] = Cell(value=BuiltinBlock("debug.chain", builtin_debug_chain))
        self.root["debug"].children["choose"] = Cell(value=BuiltinBlock("debug.choose", builtin_debug_choose))

        # String operations
        self.root["concat"] = Cell(value=BuiltinBlock("concat", builtin_concat))

        # Type conversions
        self.root["toString"] = Cell(value=BuiltinBlock("toString", builtin_to_string))
        self.root["toInt"] = Cell(value=BuiltinBlock("toInt", builtin_to_int))

        # Type predicates
        self.root["isVoid"] = Cell(value=BuiltinBlock("isVoid", builtin_is_void))
        self.root["isNil"] = Cell(value=BuiltinBlock("isNil", builtin_is_nil))

        # Extension system
        self.root["use"] = Cell(value=BuiltinBlock("use", builtin_use))

    def read_value(self, components: List[str]) -> Thing:
        """
        Read Cell value at path.

        Raises RuntimeError if path doesn't exist (was never set or auto-vivified).
        Auto-vivified intermediate cells (created during nested writes) can be read
        and return Void.

        Args:
            components: List of path components (e.g., ["a", "b", "c"])

        Returns:
            The value at the path

        Raises:
            RuntimeError: If path doesn't exist
        """
        cell = self._get_cell(components)
        if cell is None:
            path_str = '.'.join(str(c) for c in components)
            raise RuntimeError(
                f"Undefined Store path: '{path_str}'\n"
                f"  Path was never set. Did you mean to:\n"
                f"    - Initialize it first: () !{path_str}\n"
                f"    - Set a nested value: <value> !{path_str}.<child>\n"
                f"    - Check a different path?\n"
                f"  Hint: Auto-vivified intermediate paths can be read after writing to children.\n"
                f"        Example: 42 !a.b.c creates 'a' and 'a.b' with Void, which can be read."
            )
        return cell.value

    def read_ref(self, components: List[str]) -> CellRef:
        """
        Read CellRef at path.

        Auto-vivifies path if it doesn't exist (creates Cells with Void value).

        Args:
            components: List of path components

        Returns:
            CellRef to the Cell at the path
        """
        cell = self._get_or_create_cell(components)
        return CellRef(cell)

    def write_value(self, components: List[str], value: Thing):
        """
        Write value to Cell at path.

        Auto-vivifies intermediate Cells with Void value.
        Void can be written as a normal value.

        If the current value at the path is a CellRef, writes through
        the CellRef to its target Cell.

        Args:
            components: List of path components
            value: Value to write (including Void)
        """
        # Auto-vivify intermediate cells and get target cell
        cell = self._get_or_create_cell(components)

        # Check if current value is a CellRef - if so, write through
        # UNLESS we're writing a new CellRef (replacing the reference itself)
        if isinstance(cell.value, CellRef) and not isinstance(value, CellRef):
            # Write to the Cell that the CellRef points to
            cell.value.cell.value = value
        else:
            # Normal write (or replacing a CellRef with a new CellRef)
            cell.value = value

    def write_ref(self, components: List[str], value: Thing):
        """
        Replace entire Cell at path.

        If value is Void, deletes the Cell (structural deletion).
        Otherwise, replaces the Cell.

        Args:
            components: List of path components
            value: Value to write (Void triggers deletion)
        """
        if isinstance(value, VoidSingleton):
            # Structural deletion
            self._delete_cell(components)
        else:
            # Replace Cell
            cell = self._get_or_create_cell(components)
            cell.value = value
            cell.children.clear()  # Remove all children

    def _get_cell(self, components: List[str]) -> Optional[Cell]:
        """
        Get Cell at path without creating.

        Args:
            components: List of path components

        Returns:
            Cell if it exists, None otherwise
        """
        if len(components) == 0:
            return None

        current = self.root
        for component in components[:-1]:
            if component not in current:
                return None
            cell = current[component]

            # CellRef dereferencing: If a Cell's value is a CellRef, we follow it.
            # This enables transparent reference semantics. For example:
            #   42 !data.x    - Store 42 at data.x
            #   data. !ref    - Store a CellRef to 'data' cell at 'ref'
            #   ref.x         - Should return 42 (follow ref -> data, then access x)
            # Without this check, we'd only look at ref's children, missing the indirection.
            if isinstance(cell.value, CellRef):
                cell = cell.value.cell

            current = cell.children

        final_component = components[-1]
        return current.get(final_component)

    def _get_or_create_cell(self, components: List[str]) -> Cell:
        """
        Get or create Cell at path (auto-vivification).

        Args:
            components: List of path components

        Returns:
            Cell at the path (created if necessary)
        """
        if len(components) == 0:
            # Special case: empty path not allowed
            raise RuntimeError("Cannot get cell with empty path")

        current = self.root

        # Auto-vivify intermediate cells
        for component in components[:-1]:
            if component not in current:
                current[component] = Cell(value=Void)
            cell = current[component]

            # CellRef dereferencing: Follow references during path traversal.
            # This ensures writes through CellRefs work correctly. For example:
            #   data. !ref    - Store CellRef to 'data' at 'ref'
            #   99 !ref.y     - Should write to data.y (follow ref -> data, then write y)
            # Without this, we'd create a child 'y' under 'ref' instead of following the reference.
            if isinstance(cell.value, CellRef):
                cell = cell.value.cell

            current = cell.children

        # Get or create final cell
        final_component = components[-1]
        if final_component not in current:
            current[final_component] = Cell(value=Void)

        return current[final_component]

    def _delete_cell(self, components: List[str]):
        """
        Delete Cell at path (structural deletion).

        Args:
            components: List of path components
        """
        if len(components) == 0:
            return

        # Navigate to parent
        current = self.root
        for component in components[:-1]:
            if component not in current:
                return  # Path doesn't exist, nothing to delete
            current = current[component].children

        # Delete child
        final_component = components[-1]
        if final_component in current:
            del current[final_component]


class Register:
    """
    Block-local hierarchical Cell graph.

    Created fresh for each block execution.
    Destroyed when block completes.
    Completely isolated from parent block's Register.

    Has the same interface as Store (read_value, read_ref, write_value, write_ref).
    """

    def __init__(self):
        """Initialize empty Register."""
        self.root: dict[str, Cell] = {}

    def _validate_register_path(self, components: List[str]):
        """
        Validate Register path syntax.

        Rules:
        - Must have at least one component
        - First component must be exactly "_"
        - Invalid: ["_root"], ["_temp"], ["_x"], etc. (malformed single-component paths)

        Args:
            components: Path components to validate

        Raises:
            RuntimeError: If path is invalid
        """
        if len(components) == 0:
            raise RuntimeError("Empty Register path not allowed")

        # First component must be exactly "_"
        # This rejects ["_root"], ["_temp"], etc. which are malformed single-component paths
        if components[0] != "_":
            # Check if it looks like a malformed register path (starts with underscore)
            if components[0].startswith("_"):
                raise RuntimeError(
                    f"Invalid Register path '{components[0]}': use '_' for root or "
                    f"'_.{components[0][1:]}' for child"
                )
            else:
                raise RuntimeError(
                    f"Register paths must start with '_', got: {'.'.join(components)}"
                )

    def read_value(self, components: List[str]) -> Thing:
        """
        Read Cell value at path.

        Raises RuntimeError if path doesn't exist (was never set or auto-vivified).

        Args:
            components: List of path components

        Returns:
            The value at the path

        Raises:
            RuntimeError: If path doesn't exist
        """
        self._validate_register_path(components)
        cell = self._get_cell(components)
        if cell is None:
            # Format path nicely (skip the "_" root for display)
            if len(components) > 1:
                path_str = '.'.join(components[1:])
            else:
                path_str = ""

            raise RuntimeError(
                f"Undefined Register path: '_.{path_str}'\n"
                f"  Register paths must be written before reading.\n"
                f"  Did you forget: <value> !_.{path_str}?"
            )
        return cell.value

    def read_ref(self, components: List[str]) -> CellRef:
        """
        Read CellRef at path.

        Auto-vivifies path if it doesn't exist.

        Args:
            components: List of path components

        Returns:
            CellRef to the Cell at the path
        """
        self._validate_register_path(components)
        cell = self._get_or_create_cell(components)
        return CellRef(cell)

    def write_value(self, components: List[str], value: Thing):
        """
        Write value to Cell at path.

        Auto-vivifies intermediate Cells.
        Void can be written as a normal value.

        If the current value at the path is a CellRef, writes through
        the CellRef to its target Cell.

        Args:
            components: List of path components
            value: Value to write (including Void)
        """
        self._validate_register_path(components)

        # Auto-vivify intermediate cells and get target cell
        cell = self._get_or_create_cell(components)

        # Check if current value is a CellRef - if so, write through
        # UNLESS we're writing a new CellRef (replacing the reference itself)
        if isinstance(cell.value, CellRef) and not isinstance(value, CellRef):
            # Write to the Cell that the CellRef points to
            cell.value.cell.value = value
        else:
            # Normal write (or replacing a CellRef with a new CellRef)
            cell.value = value

    def write_ref(self, components: List[str], value: Thing):
        """
        Replace entire Cell at path.

        If value is Void, deletes the Cell.
        Otherwise, replaces the Cell.

        Args:
            components: List of path components
            value: Value to write (Void triggers deletion)
        """
        self._validate_register_path(components)

        if isinstance(value, VoidSingleton):
            # Structural deletion
            self._delete_cell(components)
        else:
            # Replace Cell
            cell = self._get_or_create_cell(components)
            cell.value = value
            cell.children.clear()  # Remove all children

    def _resolve_register_root(self, components: List[str], auto_vivify: bool = False) -> Optional[dict]:
        """
        Helper: Resolve the Register root and handle CellRef dereferencing.

        This centralizes the logic for:
        - Validating Register paths start with "_"
        - Getting/creating the root Cell
        - Following CellRef if root has been aliased (context-passing pattern)
        - Returning the dict to start traversal from

        Args:
            components: Full path including "_" prefix
            auto_vivify: If True, create root Cell if it doesn't exist

        Returns:
            Dictionary to start traversal from (root_cell.children after dereferencing)
            or None if root doesn't exist (when auto_vivify=False)
        """
        if len(components) == 0:
            raise RuntimeError("Empty path not allowed")

        # Register paths must start with "_"
        if components[0] != "_":
            raise RuntimeError(f"Register paths must start with '_', got: {components}")

        # Get or create root Cell
        if "_" not in self.root:
            if not auto_vivify:
                return None
            self.root["_"] = Cell(value=Void)

        root_cell = self.root["_"]

        # Context-passing: If root's value is a CellRef, follow it.
        # This enables the idiom where outer Register is passed via `_.` and stored as `!_.`
        # Then all subsequent accesses like `_.x` transparently access the aliased Register.
        if isinstance(root_cell.value, CellRef):
            root_cell = root_cell.value.cell

        return root_cell.children

    def _get_cell(self, components: List[str]) -> Optional[Cell]:
        """
        Get Cell at path without creating.

        Register paths should start with "_" which represents the Register root Cell.
        All Register data lives as children of this root Cell.
        For example: ["_", "x"] means root["_"].children["x"]
        """
        if len(components) == 0:
            return None

        # If just accessing "_" itself, need to follow CellRef if present
        if len(components) == 1:
            root_cell = self.root.get("_")
            if root_cell is None:
                return None
            # Follow CellRef if root has been aliased (context-passing)
            if isinstance(root_cell.value, CellRef):
                return root_cell.value.cell
            return root_cell

        # Resolve root and get starting point for traversal
        current = self._resolve_register_root(components, auto_vivify=False)
        if current is None:
            return None

        # Traverse path (with CellRef dereferencing at each step)
        for component in components[1:-1]:
            if component not in current:
                return None
            cell = current[component]

            # CellRef dereferencing during path traversal
            if isinstance(cell.value, CellRef):
                cell = cell.value.cell

            current = cell.children

        final_component = components[-1]
        return current.get(final_component)

    def _get_or_create_cell(self, components: List[str]) -> Cell:
        """
        Get or create Cell at path (auto-vivification).

        Register paths should start with "_" which represents the Register root Cell.
        All Register data lives as children of this root Cell.
        """
        if len(components) == 0:
            raise RuntimeError("Cannot get cell with empty path")

        # If just accessing "_" itself, need to follow CellRef if present
        if len(components) == 1:
            if "_" not in self.root:
                self.root["_"] = Cell(value=Void)
            root_cell = self.root["_"]
            # Follow CellRef if root has been aliased (context-passing)
            if isinstance(root_cell.value, CellRef):
                return root_cell.value.cell
            return root_cell

        # Resolve root and get starting point for traversal (creates root if needed)
        current = self._resolve_register_root(components, auto_vivify=True)

        # Auto-vivify and traverse path (with CellRef dereferencing)
        for component in components[1:-1]:
            if component not in current:
                current[component] = Cell(value=Void)
            cell = current[component]

            # CellRef dereferencing during path traversal
            if isinstance(cell.value, CellRef):
                cell = cell.value.cell

            current = cell.children

        # Get or create final cell
        final_component = components[-1]
        if final_component not in current:
            current[final_component] = Cell(value=Void)

        return current[final_component]

    def _delete_cell(self, components: List[str]):
        """Delete Cell at path (structural deletion)."""
        if len(components) == 0:
            return

        # Navigate to parent
        current = self.root
        for component in components[:-1]:
            if component not in current:
                return  # Path doesn't exist, nothing to delete
            current = current[component].children

        # Delete child
        final_component = components[-1]
        if final_component in current:
            del current[final_component]


# ==================== RunNode and Compilation ====================


@dataclass
class RunNode:
    """
    Executable wrapper around AST node.

    Combines AST node (for error reporting/debugging) with a compiled
    execution function (for fast dispatch-free execution).

    Attributes:
        ast_node: Original AST node
        execute: Execution function that takes VM and performs the operation
    """
    ast_node: Any  # AST node type
    execute: Callable[['VM'], None]

    def __repr__(self):
        return f"RunNode({self.ast_node.__class__.__name__})"


@dataclass
class CompiledProgram:
    """
    Compiled SOMA program ready for execution.

    Attributes:
        run_nodes: List of compiled RunNodes for top-level statements
    """
    run_nodes: List[RunNode]

    def execute(self, vm: 'VM'):
        """
        Execute all statements in the program.

        Args:
            vm: VM instance to execute in
        """
        for rn in self.run_nodes:
            rn.execute(vm)


def compile_program(program: Union[Program, dict]) -> CompiledProgram:
    """
    Compile AST Program to executable RunNodes.

    This is the one-time compilation phase where we dispatch on AST
    node types and create execution functions. During execution, we
    just call these functions without any type checking.

    Args:
        program: Parsed AST Program (either Program object or dict from parse())

    Returns:
        CompiledProgram ready for execution

    Raises:
        CompileError: If compilation fails
    """
    # Handle dict input from parse()
    if isinstance(program, dict):
        from soma.parser import Parser
        from soma.lexer import lex

        # If it's already a dict, we need to reconstruct the Program
        # Actually, we need to work with the dict structure
        statements = [_dict_to_ast(stmt) for stmt in program["body"]]
        run_nodes = [compile_node(stmt) for stmt in statements]
    else:
        # It's a Program object
        run_nodes = [compile_node(stmt) for stmt in program.statements]

    return CompiledProgram(run_nodes)


def _dict_to_ast(node_dict: dict) -> Any:
    """Convert dictionary AST representation back to AST node objects."""
    kind = node_dict["kind"]

    if kind == "IntNode":
        return IntNode(value=node_dict["value"])
    elif kind == "StringNode":
        return StringNode(value=node_dict["value"])
    elif kind == "BlockNode":
        body = [_dict_to_ast(n) for n in node_dict["body"]]
        return BlockNode(body=body)
    elif kind == "ValuePath":
        return ValuePath(components=node_dict["components"])
    elif kind == "ReferencePath":
        return ReferencePath(components=node_dict["components"])
    elif kind == "ExecNode":
        target = _dict_to_ast(node_dict["target"])
        return ExecNode(target=target)
    elif kind == "StoreNode":
        target = _dict_to_ast(node_dict["target"])
        return StoreNode(target=target)
    else:
        raise CompileError(f"Unknown AST node kind: {kind}")


def compile_node(node: Any) -> RunNode:
    """
    Compile AST node to RunNode.

    This is where isinstance dispatch happens (once, at compile time).
    Returns a RunNode with an execute function that operates on the VM.

    Args:
        node: AST node to compile

    Returns:
        RunNode with execution function

    Raises:
        CompileError: If node type is unknown
    """
    if isinstance(node, IntNode):
        # Compile integer literal - push value onto AL
        value = node.value
        return RunNode(
            ast_node=node,
            execute=lambda vm: vm.al.append(value)
        )

    elif isinstance(node, StringNode):
        # Compile string literal - push value onto AL
        value = node.value
        return RunNode(
            ast_node=node,
            execute=lambda vm: vm.al.append(value)
        )

    elif isinstance(node, BlockNode):
        # Compile block - recursively compile body, then push Block onto AL
        body = [compile_node(n) for n in node.body]
        block = Block(body)
        return RunNode(
            ast_node=node,
            execute=lambda vm: vm.al.append(block)
        )

    elif isinstance(node, ValuePath):
        # Compile value path read
        components = node.components
        is_register = (components[0] == "_")

        if is_register:
            # Register path: pass full path including "_"
            # The Register class handles "_" as the root Cell
            def read_register_value(vm):
                vm.al.append(vm.register.read_value(components))

            return RunNode(
                ast_node=node,
                execute=read_register_value
            )
        else:
            # Store path
            return RunNode(
                ast_node=node,
                execute=lambda vm: vm.al.append(vm.store.read_value(components))
            )

    elif isinstance(node, ReferencePath):
        # Compile reference path read
        components = node.components
        is_register = (components[0] == "_")

        if is_register:
            # Register path: pass full path including "_"
            # The Register class handles "_" as the root Cell
            def read_register_ref(vm):
                vm.al.append(vm.register.read_ref(components))

            return RunNode(
                ast_node=node,
                execute=read_register_ref
            )
        else:
            # Store path
            return RunNode(
                ast_node=node,
                execute=lambda vm: vm.al.append(vm.store.read_ref(components))
            )

    elif isinstance(node, ExecNode):
        # Compile execute operation
        target_node = compile_node(node.target)

        def exec_fn(vm: VM):
            # Execute target to get value on AL
            target_node.execute(vm)

            # Pop and execute
            if len(vm.al) == 0:
                raise RuntimeError(f"AL underflow: exec requires value on AL")

            thing = vm.al.pop()

            # Execute the thing (must be a Block or BuiltinBlock)
            if isinstance(thing, (Block, BuiltinBlock)):
                thing.execute(vm)
            elif isinstance(thing, (VoidSingleton, NilSingleton)):
                # Void/Nil on AL treated as underflow (nothing to execute)
                raise RuntimeError(
                    f"AL underflow: exec requires executable Block on AL, got {type(thing).__name__}"
                )
            else:
                raise RuntimeError(
                    f"Cannot execute {type(thing).__name__}: only Blocks are executable"
                )

        return RunNode(ast_node=node, execute=exec_fn)

    elif isinstance(node, StoreNode):
        # Compile store operation
        target = node.target
        is_ref = isinstance(target, ReferencePath)
        components = target.components
        is_register = (components[0] == "_")

        def store_fn(vm: VM):
            if len(vm.al) == 0:
                raise RuntimeError(f"AL underflow: store requires value on AL")

            value = vm.al.pop()

            # Write to Store or Register
            storage = vm.register if is_register else vm.store

            if is_ref:
                # Reference write - replace entire cell
                storage.write_ref(components, value)
            else:
                # Value write
                storage.write_value(components, value)

        return RunNode(ast_node=node, execute=store_fn)

    else:
        raise CompileError(f"Unknown AST node type: {type(node).__name__}")


# ==================== Virtual Machine ====================


class VM:
    """
    SOMA Virtual Machine.

    Maintains the three core state structures:
    - AL (Accumulator List): LIFO stack for values
    - Store: Global hierarchical Cell graph
    - Register: Block-local hierarchical Cell graph (changes per block)
    - current_block: Currently executing block (None at top-level)
    """

    def __init__(self, load_stdlib=True):
        """
        Initialize VM with empty AL, fresh Store, and empty Register.

        Args:
            load_stdlib: If True (default), automatically load stdlib.soma
        """
        self.al: List[Thing] = []
        self.store: Store = Store()
        self.register: Register = Register()
        self.current_block: Optional[Block] = None
        self.loaded_extensions: set = set()

        if load_stdlib:
            self._load_stdlib()

    def execute(self, compiled_program: CompiledProgram):
        """
        Execute a compiled program.

        Args:
            compiled_program: CompiledProgram to execute
        """
        compiled_program.execute(self)

    def _load_stdlib(self):
        """
        Load stdlib.soma into the VM.

        Called automatically during VM initialization unless load_stdlib=False.
        Safe to call multiple times (idempotent).
        """
        # Find stdlib.soma relative to this file
        import os
        vm_dir = os.path.dirname(os.path.abspath(__file__))
        stdlib_path = os.path.join(vm_dir, 'stdlib.soma')

        if not os.path.exists(stdlib_path):
            raise RuntimeError(f"stdlib.soma not found at {stdlib_path}")

        # Load and execute stdlib code
        with open(stdlib_path, 'r') as f:
            stdlib_code = f.read()

        # Execute stdlib using the same pipeline as run_soma_program
        from soma.lexer import lex
        from soma.parser import Parser

        tokens = lex(stdlib_code)
        parser = Parser(tokens)
        ast = parser.parse()
        compiled = compile_program(ast)
        compiled.execute(self)

    def execute_code(self, source: str):
        """
        Execute SOMA source code in this VM instance.

        Args:
            source: SOMA source code string
        """
        from soma.lexer import lex
        from soma.parser import Parser

        tokens = lex(source)
        parser = Parser(tokens)
        ast = parser.parse()
        compiled = compile_program(ast)
        compiled.execute(self)

    def register_extension_builtin(self, name: str, builtin_fn):
        """
        Register an extension builtin under the use.* namespace.

        Args:
            name: Fully qualified name (must start with 'use.')
            builtin_fn: Function taking (vm) as parameter

        Raises:
            ValueError: If name doesn't start with 'use.'
        """
        if not name.startswith('use.'):
            raise ValueError(f"Extension builtin name must be under 'use.*' namespace, got '{name}'")

        # Split name into path components
        path = name.split('.')

        # Create BuiltinBlock and store it
        builtin_block = BuiltinBlock(name, builtin_fn)
        self.store.write_value(path, builtin_block)

    def load_extension(self, extension_name: str):
        """
        Load a SOMA extension by name.

        Args:
            extension_name: Name of extension to load (e.g., 'python', 'http')

        Raises:
            RuntimeError: If extension module not found or fails to load
        """
        # Skip if already loaded
        if extension_name in self.loaded_extensions:
            return

        # Try to import extension module
        try:
            import importlib
            extension_module = importlib.import_module(f'soma.extensions.{extension_name}')
        except ImportError as e:
            raise RuntimeError(f"Extension '{extension_name}' not found: {e}")

        # Call register function to register builtins
        if hasattr(extension_module, 'register'):
            extension_module.register(self)
        else:
            raise RuntimeError(f"Extension '{extension_name}' missing register() function")

        # Execute setup SOMA code if provided
        if hasattr(extension_module, 'get_soma_setup'):
            setup_code = extension_module.get_soma_setup()
            if setup_code:
                self.execute_code(setup_code)

        # Mark as loaded
        self.loaded_extensions.add(extension_name)


# ==================== Built-in Operations ====================


def builtin_block(vm: VM):
    """
    >block built-in: Push current block to AL.

    AL before: [...]
    AL after: [current_block, ...]

    Raises:
        RuntimeError: If called at top-level (no current block)
    """
    if vm.current_block is None:
        raise RuntimeError(">block called at top-level (no current block)")

    # Push current block to AL
    vm.al.append(vm.current_block)


def builtin_choose(vm: VM):
    """
    >choose built-in: Conditional selection (SELECTOR, not executor).

    AL before: [condition, true_value, false_value, ...]
    AL after: [selected_value, ...]

    The condition is popped and evaluated:
    - Nil/Void/False = False
    - Everything else (including True) = True

    Then the appropriate value is selected and pushed to AL.
    Does NOT execute - just pushes the selected value to AL.
    Any value type can be selected (blocks, ints, strings, etc.).

    Raises:
        RuntimeError: If AL underflow
    """
    if len(vm.al) < 3:
        raise RuntimeError("AL underflow: >choose requires 3 values")

    # Pop in reverse order: false, true, condition (LIFO)
    false_value = vm.al.pop()
    true_value = vm.al.pop()
    condition = vm.al.pop()

    # Evaluate condition: Nil/Void/False = False, everything else = True
    is_true = not isinstance(condition, (NilSingleton, VoidSingleton, FalseSingleton))

    # Choose value and push to AL
    selected = true_value if is_true else false_value
    vm.al.append(selected)


def builtin_chain(vm: VM):
    """
    >chain built-in: Sequential execution.

    AL before: [block, ...]
    AL after: [... result of block ...]

    Pops block from AL and executes it. The block's effects (AL changes,
    Store/Register modifications) persist after >chain completes.

    Raises:
        RuntimeError: If AL underflow or value is not a Block
    """
    if len(vm.al) < 1:
        raise RuntimeError("AL underflow: >chain requires 1 value (block)")

    # Peek at top of AL
    thing = vm.al.pop()

    # If it's a Block, execute it and loop
    # The loop continues as long as the block leaves a block on AL
    while isinstance(thing, (Block, BuiltinBlock)):
        # Execute the block
        thing.execute(vm)

        # Check if there's another block on AL to continue the chain
        if len(vm.al) > 0 and isinstance(vm.al[-1], (Block, BuiltinBlock)):
            thing = vm.al.pop()
        else:
            # No more blocks, stop chaining
            break

    # If the thing wasn't a block, just push it back (chain stops gracefully)
    if not isinstance(thing, (Block, BuiltinBlock)):
        vm.al.append(thing)


# ==================== FFI Built-ins ====================


def builtin_lt(vm: VM):
    """
    < (less-than): Comparison operator.

    AL before: [a, b, ...]
    AL after: [result, ...]

    Polymorphic: works with int and string.
    - Int: numeric comparison
    - String: lexicographic comparison

    Pushes True or False onto AL.

    Raises:
        RuntimeError: If AL underflow or type mismatch
    """
    if len(vm.al) < 2:
        raise RuntimeError("AL underflow: < requires 2 values")

    b = vm.al.pop()
    a = vm.al.pop()

    # Type check: both must be same type
    if type(a) != type(b):
        raise RuntimeError(f"Type mismatch in <: cannot compare {type(a).__name__} and {type(b).__name__}")

    if isinstance(a, int) and isinstance(b, int):
        result = True_ if a < b else False_
    elif isinstance(a, str) and isinstance(b, str):
        result = True_ if a < b else False_
    else:
        raise RuntimeError(f"Cannot compare type {type(a).__name__} with <")

    vm.al.append(result)


def builtin_add(vm: VM):
    """
    + (add): Integer addition.

    AL before: [a, b, ...]
    AL after: [a + b, ...]

    Raises:
        RuntimeError: If AL underflow or operands not integers
    """
    if len(vm.al) < 2:
        raise RuntimeError("AL underflow: + requires 2 values")

    b = vm.al.pop()
    a = vm.al.pop()

    if not isinstance(a, int) or not isinstance(b, int):
        raise RuntimeError(f"Type error in +: expected int, got {type(a).__name__} and {type(b).__name__}")

    vm.al.append(a + b)


def builtin_subtract(vm: VM):
    """
    - (subtract): Integer subtraction.

    AL before: [a, b, ...]
    AL after: [a - b, ...]

    Raises:
        RuntimeError: If AL underflow or operands not integers
    """
    if len(vm.al) < 2:
        raise RuntimeError("AL underflow: - requires 2 values")

    b = vm.al.pop()
    a = vm.al.pop()

    if not isinstance(a, int) or not isinstance(b, int):
        raise RuntimeError(f"Type error in -: expected int, got {type(a).__name__} and {type(b).__name__}")

    vm.al.append(a - b)


def builtin_multiply(vm: VM):
    """
    * (multiply): Integer multiplication.

    AL before: [a, b, ...]
    AL after: [a * b, ...]

    Raises:
        RuntimeError: If AL underflow or operands not integers
    """
    if len(vm.al) < 2:
        raise RuntimeError("AL underflow: * requires 2 values")

    b = vm.al.pop()
    a = vm.al.pop()

    if not isinstance(a, int) or not isinstance(b, int):
        raise RuntimeError(f"Type error in *: expected int, got {type(a).__name__} and {type(b).__name__}")

    vm.al.append(a * b)


def builtin_divide(vm: VM):
    """
    / (divide): Integer division.

    AL before: [a, b, ...]
    AL after: [a // b, ...]

    Uses floor division (//).

    Raises:
        RuntimeError: If AL underflow, operands not integers, or division by zero
    """
    if len(vm.al) < 2:
        raise RuntimeError("AL underflow: / requires 2 values")

    b = vm.al.pop()
    a = vm.al.pop()

    if not isinstance(a, int) or not isinstance(b, int):
        raise RuntimeError(f"Type error in /: expected int, got {type(a).__name__} and {type(b).__name__}")

    if b == 0:
        raise RuntimeError("Division by zero")

    vm.al.append(a // b)


def builtin_modulo(vm: VM):
    """
    % (modulo): Integer modulo.

    AL before: [a, b, ...]
    AL after: [a % b, ...]

    Raises:
        RuntimeError: If AL underflow, operands not integers, or modulo by zero
    """
    if len(vm.al) < 2:
        raise RuntimeError("AL underflow: % requires 2 values")

    b = vm.al.pop()
    a = vm.al.pop()

    if not isinstance(a, int) or not isinstance(b, int):
        raise RuntimeError(f"Type error in %: expected int, got {type(a).__name__} and {type(b).__name__}")

    if b == 0:
        raise RuntimeError("Modulo by zero")

    vm.al.append(a % b)


def builtin_print(vm: VM):
    """
    print: Output value to stdout.

    AL before: [value, ...]
    AL after: [...]

    Converts value to string and prints it.

    Raises:
        RuntimeError: If AL underflow
    """
    if len(vm.al) < 1:
        raise RuntimeError("AL underflow: print requires 1 value")

    value = vm.al.pop()

    # Convert to string representation
    if isinstance(value, str):
        print(value)
    elif isinstance(value, int):
        print(str(value))
    elif isinstance(value, TrueSingleton):
        print("True")
    elif isinstance(value, FalseSingleton):
        print("False")
    elif isinstance(value, NilSingleton):
        print("Nil")
    elif isinstance(value, VoidSingleton):
        print("Void")
    else:
        print(repr(value))


def builtin_debug_al_dump(vm: VM):
    """
    debug.al.dump: Dump current AL state to stdout for debugging.

    AL before: [...]
    AL after: [...] (unchanged)

    Prints a representation of the AL to help with debugging.
    """
    print(f"DEBUG AL [{len(vm.al)} items]: ", end="")
    items = []
    for item in vm.al:
        if isinstance(item, str):
            items.append(f'({item})')
        elif isinstance(item, int):
            items.append(str(item))
        elif isinstance(item, TrueSingleton):
            items.append('True')
        elif isinstance(item, FalseSingleton):
            items.append('False')
        elif isinstance(item, NilSingleton):
            items.append('Nil')
        elif isinstance(item, VoidSingleton):
            items.append('Void')
        elif isinstance(item, Block):
            items.append('Block')
        elif isinstance(item, CellRef):
            items.append(f'CellRef({id(item.cell)})')
        else:
            items.append(f'{type(item).__name__}')
    print('[' + ', '.join(items) + ']')


def builtin_debug_chain(vm: VM):
    """
    debug.chain: Instrumented version of chain that logs each iteration.

    AL before: [block_or_nil, ...]
    AL after: [...] (depends on block execution)

    Like builtin_chain, but prints:
    - Iteration number
    - AL size before/after each block execution
    - Termination reason (Nil or no more blocks)

    Use the backup/restore pattern:
        chain !backup.chain
        debug.chain !chain
        ... your code ...
        backup.chain !chain

    Includes safety limit of 1000 iterations to detect infinite loops.
    """
    if len(vm.al) < 1:
        raise RuntimeError("AL underflow: >chain requires 1 value (block)")

    # Peek at top of AL
    thing = vm.al.pop()
    iteration = 0
    MAX_ITERATIONS = 1000

    # If it's a Block, execute it and loop
    while isinstance(thing, (Block, BuiltinBlock)):
        iteration += 1
        al_size_before = len(vm.al)

        print(f"\n[DEBUG CHAIN] Iteration {iteration}")
        print(f"  AL before: {al_size_before} items")
        print(f"  → Executing Block")

        # Safety check for infinite loops
        if iteration >= MAX_ITERATIONS:
            print(f"\n[DEBUG CHAIN] ⚠️  WARNING: Reached {MAX_ITERATIONS} iterations!")
            print(f"  Possible infinite loop detected - stopping chain")
            print(f"  Last AL size: {al_size_before} items")
            break

        # Execute the block
        thing.execute(vm)

        al_size_after = len(vm.al)
        print(f"  AL after: {al_size_after} items")

        # Check if there's another block on AL to continue the chain
        if len(vm.al) > 0 and isinstance(vm.al[-1], (Block, BuiltinBlock)):
            thing = vm.al.pop()
        else:
            # No more blocks, stop chaining
            print(f"  → Chain terminating: no more blocks on AL")
            break

    # If the thing wasn't a block, check if it's Nil
    if not isinstance(thing, (Block, BuiltinBlock)):
        if isinstance(thing, NilSingleton):
            print(f"\n[DEBUG CHAIN] → Nil encountered, stopping")
        else:
            vm.al.append(thing)


def builtin_debug_choose(vm: VM):
    """
    debug.choose: Instrumented version of choose that logs branch selection.

    AL before: [condition, true_block, false_block, ...]
    AL after: [chosen_block, ...]

    Like builtin_choose, but prints:
    - Condition value
    - Which branch (TRUE/FALSE) is selected
    - AL size before/after

    Use the backup/restore pattern:
        choose !backup.choose
        debug.choose !choose
        ... your code ...
        backup.choose !choose
    """
    if len(vm.al) < 3:
        raise RuntimeError("Choose requires [condition, true_block, false_block] on AL")

    al_size_before = len(vm.al)

    false_block = vm.al.pop()
    true_block = vm.al.pop()
    condition = vm.al.pop()

    print(f"\n[DEBUG CHOOSE]")
    print(f"  Condition: {type(condition).__name__}")
    print(f"  AL before: {al_size_before} items")

    # Determine which branch based on truthiness
    # In SOMA: True_, non-zero ints, non-empty strings are truthy
    # False_, Nil, Void, 0, empty string are falsy
    if isinstance(condition, (TrueSingleton,)):
        print(f"  → Taking TRUE branch")
        vm.al.append(true_block)
    elif isinstance(condition, (FalseSingleton, VoidSingleton, NilSingleton)):
        print(f"  → Taking FALSE branch")
        vm.al.append(false_block)
    elif isinstance(condition, int):
        if condition != 0:
            print(f"  → Taking TRUE branch (non-zero int: {condition})")
            vm.al.append(true_block)
        else:
            print(f"  → Taking FALSE branch (zero)")
            vm.al.append(false_block)
    elif isinstance(condition, str):
        if condition != "":
            print(f"  → Taking TRUE branch (non-empty string)")
            vm.al.append(true_block)
        else:
            print(f"  → Taking FALSE branch (empty string)")
            vm.al.append(false_block)
    else:
        # Default: truthy for everything else
        print(f"  → Taking TRUE branch (truthy value)")
        vm.al.append(true_block)

    al_size_after = len(vm.al)
    print(f"  AL after: {al_size_after} items")


def builtin_read_line(vm: VM):
    """
    read_line: Read a line from stdin.

    AL before: [...]
    AL after: [string, ...]

    Reads a line from stdin (without trailing newline) and pushes it as a string.

    Raises:
        RuntimeError: If EOF
    """
    try:
        line = input()
        vm.al.append(line)
    except EOFError:
        raise RuntimeError("read_line: EOF encountered")


def builtin_concat(vm: VM):
    """
    concat: String concatenation.

    AL before: [a, b, ...]
    AL after: [a + b, ...]

    Concatenates two strings.

    Raises:
        RuntimeError: If AL underflow or operands not strings
    """
    if len(vm.al) < 2:
        raise RuntimeError("AL underflow: concat requires 2 values")

    b = vm.al.pop()
    a = vm.al.pop()

    if not isinstance(a, str) or not isinstance(b, str):
        raise RuntimeError(f"Type error in concat: expected string, got {type(a).__name__} and {type(b).__name__}")

    vm.al.append(a + b)


def builtin_to_string(vm: VM):
    """
    to_string: Convert int to string.

    AL before: [int, ...]
    AL after: [string, ...]

    Raises:
        RuntimeError: If AL underflow or value not an integer
    """
    if len(vm.al) < 1:
        raise RuntimeError("AL underflow: to_string requires 1 value")

    value = vm.al.pop()

    if not isinstance(value, int):
        raise RuntimeError(f"Type error in to_string: expected int, got {type(value).__name__}")

    vm.al.append(str(value))


def builtin_to_int(vm: VM):
    """
    to_int: Parse string to int.

    AL before: [string, ...]
    AL after: [int, ...] or [Nil, ...]

    Pushes Nil if parsing fails.

    Raises:
        RuntimeError: If AL underflow or value not a string
    """
    if len(vm.al) < 1:
        raise RuntimeError("AL underflow: to_int requires 1 value")

    value = vm.al.pop()

    if not isinstance(value, str):
        raise RuntimeError(f"Type error in to_int: expected string, got {type(value).__name__}")

    try:
        result = int(value)
        vm.al.append(result)
    except ValueError:
        vm.al.append(Nil)


def builtin_is_void(vm: VM):
    """
    IsVoid: Test if value is Void.

    AL before: [value, ...]
    AL after: [True/False, ...]

    Pushes True if value is Void, False otherwise.

    Raises:
        RuntimeError: If AL underflow
    """
    if len(vm.al) < 1:
        raise RuntimeError("AL underflow: IsVoid requires 1 value")

    value = vm.al.pop()
    result = True_ if isinstance(value, VoidSingleton) else False_
    vm.al.append(result)


def builtin_is_nil(vm: VM):
    """
    IsNil: Test if value is Nil.

    AL before: [value, ...]
    AL after: [True/False, ...]

    Pushes True if value is Nil, False otherwise.

    Raises:
        RuntimeError: If AL underflow
    """
    if len(vm.al) < 1:
        raise RuntimeError("AL underflow: IsNil requires 1 value")

    value = vm.al.pop()
    result = True_ if isinstance(value, NilSingleton) else False_
    vm.al.append(result)


def builtin_use(vm: VM):
    """
    use: Load a SOMA extension.

    AL before: [extension_name(string), ...]
    AL after: [...]

    Loads the named extension, registering its builtins under use.* namespace
    and executing its setup code.

    Raises:
        RuntimeError: If AL underflow, argument not string, or extension not found
    """
    if len(vm.al) < 1:
        raise RuntimeError("AL underflow: use requires 1 value (extension name)")

    extension_name = vm.al.pop()

    if not isinstance(extension_name, str):
        raise RuntimeError(f"use: expected string extension name, got {type(extension_name).__name__}")

    vm.load_extension(extension_name)


# ==================== Main Entry Point ====================


def run_soma_program(source: str) -> List[Thing]:
    """
    Complete pipeline: source -> lexed -> parsed -> compiled -> executed.

    This is the main entry point for executing SOMA programs.

    Args:
        source: SOMA source code string

    Returns:
        The final AL state after execution

    Raises:
        CompileError: If compilation fails
        RuntimeError: If execution fails
    """
    # 1. Lex
    from soma.lexer import lex
    tokens = lex(source)

    # 2. Parse
    from soma.parser import Parser
    parser = Parser(tokens)
    ast = parser.parse()

    # 3. Compile
    compiled = compile_program(ast)

    # 4. Execute
    vm = VM()
    vm.execute(compiled)

    return vm.al


# ==================== Example Usage ====================


if __name__ == "__main__":
    # Example: Square function
    source = """
    { !_ _ _ >* } !square
    5 >square
    """

    try:
        result_al = run_soma_program(source)
        print(f"Final AL: {result_al}")  # Should be [25]
    except NotImplementedError as e:
        print(f"Not yet implemented: {e}")
    except (CompileError, RuntimeError) as e:
        print(f"Error: {e}")
