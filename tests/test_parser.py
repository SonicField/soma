"""
Unit tests for the SOMA parser (TDD - tests written before implementation).

These tests define the expected behavior of the parser:

- AST node creation for all 8 node types (Program, IntNode, StringNode, BlockNode,
  ValuePath, ReferencePath, ExecNode, StoreNode)
- Path parsing: splitting by '.', detecting trailing '.', validating register syntax
- String handling: verify lexer decoded escapes, parser just uses the value
- Modifier nodes: ExecNode and StoreNode with valid targets
- Error cases: invalid syntax, malformed paths, unbalanced braces
- Edge cases: single '_', empty blocks, nested blocks, register validation

The parser is expected to:
1. Accept a token stream from the lexer
2. Build an AST tree with eager block parsing
3. Split PATH tokens by '.' into components
4. Detect trailing '.' to distinguish ValuePath vs ReferencePath
5. Validate register paths: '_' ok, '_x' error, '_.x' ok
6. Validate modifier targets
7. Provide clear error messages with source locations
"""

import unittest

# Parser will be implemented in soma.parser module
from soma.parser import parse, ParseError


class TestIntNodes(unittest.TestCase):
    """Tests for IntNode creation from INT tokens."""

    def test_simple_positive_integer(self):
        """Test parsing a simple positive integer."""
        ast = parse("42")
        self.assertEqual(ast["kind"], "Program")
        self.assertEqual(len(ast["body"]), 1)

        node = ast["body"][0]
        self.assertEqual(node["kind"], "IntNode")
        self.assertEqual(node["value"], 42)

    def test_negative_integer(self):
        """Test parsing a negative integer."""
        ast = parse("-23")
        node = ast["body"][0]
        self.assertEqual(node["kind"], "IntNode")
        self.assertEqual(node["value"], -23)

    def test_positive_signed_integer(self):
        """Test parsing an explicitly positive integer."""
        ast = parse("+99")
        node = ast["body"][0]
        self.assertEqual(node["kind"], "IntNode")
        self.assertEqual(node["value"], 99)

    def test_zero(self):
        """Test parsing zero."""
        ast = parse("0")
        node = ast["body"][0]
        self.assertEqual(node["kind"], "IntNode")
        self.assertEqual(node["value"], 0)

    def test_multiple_integers(self):
        """Test parsing multiple integers in sequence."""
        ast = parse("1 2 3")
        self.assertEqual(len(ast["body"]), 3)

        self.assertEqual(ast["body"][0]["kind"], "IntNode")
        self.assertEqual(ast["body"][0]["value"], 1)
        self.assertEqual(ast["body"][1]["kind"], "IntNode")
        self.assertEqual(ast["body"][1]["value"], 2)
        self.assertEqual(ast["body"][2]["kind"], "IntNode")
        self.assertEqual(ast["body"][2]["value"], 3)


class TestStringNodes(unittest.TestCase):
    """Tests for StringNode creation from STRING tokens.

    IMPORTANT: Lexer already decoded Unicode escapes and removed parens.
    Parser just creates StringNode with the decoded value.
    """

    def test_simple_string(self):
        """Test parsing a simple string."""
        ast = parse("(hello)")
        node = ast["body"][0]
        self.assertEqual(node["kind"], "StringNode")
        self.assertEqual(node["value"], "hello")

    def test_empty_string(self):
        """Test parsing an empty string."""
        ast = parse("()")
        node = ast["body"][0]
        self.assertEqual(node["kind"], "StringNode")
        self.assertEqual(node["value"], "")

    def test_string_with_spaces(self):
        """Test parsing a string with whitespace."""
        ast = parse("(hello world)")
        node = ast["body"][0]
        self.assertEqual(node["kind"], "StringNode")
        self.assertEqual(node["value"], "hello world")

    def test_string_already_decoded_by_lexer(self):
        """Test that parser receives already-decoded string from lexer."""
        # Lexer decodes \41\ to 'A'
        ast = parse("(\\41\\)")
        node = ast["body"][0]
        self.assertEqual(node["kind"], "StringNode")
        self.assertEqual(node["value"], "A")

    def test_multiple_strings(self):
        """Test parsing multiple strings in sequence."""
        ast = parse("(a) (b) (c)")
        self.assertEqual(len(ast["body"]), 3)

        self.assertEqual(ast["body"][0]["value"], "a")
        self.assertEqual(ast["body"][1]["value"], "b")
        self.assertEqual(ast["body"][2]["value"], "c")


class TestValuePaths(unittest.TestCase):
    """Tests for ValuePath parsing (paths without trailing dot).

    Parser must:
    - Split PATH token value by '.'
    - Create components array
    - Validate register path syntax
    """

    def test_simple_single_component_path(self):
        """Test parsing a single-component path."""
        ast = parse("foo")
        node = ast["body"][0]
        self.assertEqual(node["kind"], "ValuePath")
        self.assertEqual(node["components"], ["foo"])

    def test_multi_component_path(self):
        """Test parsing a multi-component path."""
        ast = parse("a.b.c")
        node = ast["body"][0]
        self.assertEqual(node["kind"], "ValuePath")
        self.assertEqual(node["components"], ["a", "b", "c"])

    def test_two_component_path(self):
        """Test parsing a two-component path."""
        ast = parse("foo.bar")
        node = ast["body"][0]
        self.assertEqual(node["kind"], "ValuePath")
        self.assertEqual(node["components"], ["foo", "bar"])

    def test_register_root_single_underscore(self):
        """Test parsing single '_' as register root."""
        ast = parse("_")
        node = ast["body"][0]
        self.assertEqual(node["kind"], "ValuePath")
        self.assertEqual(node["components"], ["_"])

    def test_valid_register_path_with_dot(self):
        """Test parsing valid register path '_.x'."""
        ast = parse("_.x")
        node = ast["body"][0]
        self.assertEqual(node["kind"], "ValuePath")
        self.assertEqual(node["components"], ["_", "x"])

    def test_valid_nested_register_path(self):
        """Test parsing nested register path '_.a.b.c'."""
        ast = parse("_.a.b.c")
        node = ast["body"][0]
        self.assertEqual(node["kind"], "ValuePath")
        self.assertEqual(node["components"], ["_", "a", "b", "c"])

    def test_invalid_register_path_missing_dot(self):
        """Test that '_x' is rejected (missing dot after underscore)."""
        with self.assertRaises(ParseError) as ctx:
            parse("_x")

        error_msg = str(ctx.exception)
        self.assertIn("_x", error_msg)
        self.assertIn("register", error_msg.lower())

    def test_invalid_register_path_temp(self):
        """Test that '_temp' is rejected (should be '_.temp')."""
        with self.assertRaises(ParseError) as ctx:
            parse("_temp")

        error_msg = str(ctx.exception)
        self.assertIn("_temp", error_msg)
        self.assertIn("register", error_msg.lower())

    def test_path_with_special_characters(self):
        """Test paths can contain special characters (from lexer tests)."""
        ast = parse("a,b")
        node = ast["body"][0]
        self.assertEqual(node["kind"], "ValuePath")
        self.assertEqual(node["components"], ["a,b"])

    def test_multiple_paths(self):
        """Test parsing multiple paths in sequence."""
        ast = parse("a b.c d.e.f")
        self.assertEqual(len(ast["body"]), 3)

        self.assertEqual(ast["body"][0]["components"], ["a"])
        self.assertEqual(ast["body"][1]["components"], ["b", "c"])
        self.assertEqual(ast["body"][2]["components"], ["d", "e", "f"])


class TestReferencePaths(unittest.TestCase):
    """Tests for ReferencePath parsing (paths with trailing dot).

    Parser must:
    - Detect trailing '.' in PATH token value
    - Strip trailing '.' before splitting
    - Create ReferencePath instead of ValuePath
    """

    def test_simple_reference_path(self):
        """Test parsing a simple reference path 'a.'."""
        ast = parse("a.")
        node = ast["body"][0]
        self.assertEqual(node["kind"], "ReferencePath")
        self.assertEqual(node["components"], ["a"])

    def test_multi_component_reference_path(self):
        """Test parsing multi-component reference path 'a.b.'."""
        ast = parse("a.b.")
        node = ast["body"][0]
        self.assertEqual(node["kind"], "ReferencePath")
        self.assertEqual(node["components"], ["a", "b"])

    def test_nested_reference_path(self):
        """Test parsing nested reference path 'foo.bar.baz.'."""
        ast = parse("foo.bar.baz.")
        node = ast["body"][0]
        self.assertEqual(node["kind"], "ReferencePath")
        self.assertEqual(node["components"], ["foo", "bar", "baz"])

    def test_register_root_reference(self):
        """Test parsing register root reference '_.'."""
        ast = parse("_.")
        node = ast["body"][0]
        self.assertEqual(node["kind"], "ReferencePath")
        self.assertEqual(node["components"], ["_"])

    def test_register_path_reference(self):
        """Test parsing register path reference '_.x.'."""
        ast = parse("_.x.")
        node = ast["body"][0]
        self.assertEqual(node["kind"], "ReferencePath")
        self.assertEqual(node["components"], ["_", "x"])

    def test_nested_register_reference(self):
        """Test parsing nested register reference '_.a.b.'."""
        ast = parse("_.a.b.")
        node = ast["body"][0]
        self.assertEqual(node["kind"], "ReferencePath")
        self.assertEqual(node["components"], ["_", "a", "b"])

    def test_value_vs_reference_distinction(self):
        """Test parser correctly distinguishes value vs reference paths."""
        ast = parse("data data.")

        value_node = ast["body"][0]
        self.assertEqual(value_node["kind"], "ValuePath")
        self.assertEqual(value_node["components"], ["data"])

        ref_node = ast["body"][1]
        self.assertEqual(ref_node["kind"], "ReferencePath")
        self.assertEqual(ref_node["components"], ["data"])


class TestBlockNodes(unittest.TestCase):
    """Tests for BlockNode parsing with eager block parsing.

    Parser must:
    - Recursively parse block contents into AST
    - Validate balanced braces
    - Support nested blocks
    - Handle empty blocks
    """

    def test_empty_block(self):
        """Test parsing an empty block."""
        ast = parse("{}")
        node = ast["body"][0]
        self.assertEqual(node["kind"], "BlockNode")
        self.assertEqual(node["body"], [])

    def test_block_with_single_integer(self):
        """Test parsing block containing single integer."""
        ast = parse("{ 42 }")
        node = ast["body"][0]
        self.assertEqual(node["kind"], "BlockNode")
        self.assertEqual(len(node["body"]), 1)
        self.assertEqual(node["body"][0]["kind"], "IntNode")
        self.assertEqual(node["body"][0]["value"], 42)

    def test_block_with_multiple_statements(self):
        """Test parsing block with multiple statements."""
        ast = parse("{ 1 2 3 }")
        node = ast["body"][0]
        self.assertEqual(node["kind"], "BlockNode")
        self.assertEqual(len(node["body"]), 3)

        for i in range(3):
            self.assertEqual(node["body"][i]["kind"], "IntNode")
            self.assertEqual(node["body"][i]["value"], i + 1)

    def test_nested_blocks(self):
        """Test parsing nested blocks (eager parsing)."""
        ast = parse("{ { 1 } }")
        outer_block = ast["body"][0]
        self.assertEqual(outer_block["kind"], "BlockNode")
        self.assertEqual(len(outer_block["body"]), 1)

        inner_block = outer_block["body"][0]
        self.assertEqual(inner_block["kind"], "BlockNode")
        self.assertEqual(len(inner_block["body"]), 1)
        self.assertEqual(inner_block["body"][0]["value"], 1)

    def test_deeply_nested_blocks(self):
        """Test parsing deeply nested blocks."""
        ast = parse("{ { { 42 } } }")

        level1 = ast["body"][0]
        self.assertEqual(level1["kind"], "BlockNode")

        level2 = level1["body"][0]
        self.assertEqual(level2["kind"], "BlockNode")

        level3 = level2["body"][0]
        self.assertEqual(level3["kind"], "BlockNode")
        self.assertEqual(level3["body"][0]["value"], 42)

    def test_block_with_mixed_content(self):
        """Test parsing block with different node types."""
        ast = parse("{ 42 (hello) a.b }")
        node = ast["body"][0]
        self.assertEqual(len(node["body"]), 3)

        self.assertEqual(node["body"][0]["kind"], "IntNode")
        self.assertEqual(node["body"][1]["kind"], "StringNode")
        self.assertEqual(node["body"][2]["kind"], "ValuePath")

    def test_unclosed_block_error(self):
        """Test that unclosed block is detected."""
        with self.assertRaises(ParseError) as ctx:
            parse("{")

        error_msg = str(ctx.exception)
        self.assertIn("unclosed", error_msg.lower())

    def test_unopened_block_error(self):
        """Test that extra closing brace is detected."""
        with self.assertRaises(ParseError) as ctx:
            parse("}")

        error_msg = str(ctx.exception)
        self.assertIn("unexpected", error_msg.lower())

    def test_mismatched_braces_error(self):
        """Test that mismatched braces are detected."""
        with self.assertRaises(ParseError) as ctx:
            parse("{ { } } }")

        error_msg = str(ctx.exception)
        # Should indicate extra closing brace or similar
        self.assertTrue(
            "unexpected" in error_msg.lower() or
            "extra" in error_msg.lower() or
            "unmatched" in error_msg.lower()
        )


class TestExecNodes(unittest.TestCase):
    """Tests for ExecNode parsing.

    Parser must:
    - Accept ValuePath as target (execute value at path)
    - Accept BlockNode as target (execute inline block)
    - Reject ReferencePath as target (cannot execute CellRef)
    """

    def test_exec_simple_path(self):
        """Test parsing >print."""
        ast = parse(">print")
        node = ast["body"][0]
        self.assertEqual(node["kind"], "ExecNode")
        self.assertEqual(node["target"]["kind"], "ValuePath")
        self.assertEqual(node["target"]["components"], ["print"])

    def test_exec_multi_component_path(self):
        """Test parsing >a.b.c."""
        ast = parse(">a.b.c")
        node = ast["body"][0]
        self.assertEqual(node["kind"], "ExecNode")
        self.assertEqual(node["target"]["kind"], "ValuePath")
        self.assertEqual(node["target"]["components"], ["a", "b", "c"])

    def test_exec_register_path(self):
        """Test parsing >_.action."""
        ast = parse(">_.action")
        node = ast["body"][0]
        self.assertEqual(node["kind"], "ExecNode")
        self.assertEqual(node["target"]["kind"], "ValuePath")
        self.assertEqual(node["target"]["components"], ["_", "action"])

    def test_exec_inline_block(self):
        """Test parsing >{ 1 2 >+ }."""
        ast = parse(">{ 1 2 >+ }")
        node = ast["body"][0]
        self.assertEqual(node["kind"], "ExecNode")
        self.assertEqual(node["target"]["kind"], "BlockNode")
        self.assertEqual(len(node["target"]["body"]), 3)

    def test_exec_empty_block(self):
        """Test parsing >{} (execute empty block)."""
        ast = parse(">{}")
        node = ast["body"][0]
        self.assertEqual(node["kind"], "ExecNode")
        self.assertEqual(node["target"]["kind"], "BlockNode")
        self.assertEqual(node["target"]["body"], [])

    def test_exec_nested_block(self):
        """Test parsing >{ { 42 } } (nested blocks)."""
        ast = parse(">{ { 42 } }")
        node = ast["body"][0]
        self.assertEqual(node["kind"], "ExecNode")

        outer_block = node["target"]
        self.assertEqual(outer_block["kind"], "BlockNode")

        inner_block = outer_block["body"][0]
        self.assertEqual(inner_block["kind"], "BlockNode")
        self.assertEqual(inner_block["body"][0]["value"], 42)

    def test_exec_reference_path_error(self):
        """Test that >a.b. (reference path) is rejected."""
        with self.assertRaises(ParseError) as ctx:
            parse(">a.b.")

        error_msg = str(ctx.exception)
        self.assertIn("reference", error_msg.lower())

    def test_exec_special_operator_path(self):
        """Test parsing >+ (execute operator)."""
        ast = parse(">+")
        node = ast["body"][0]
        self.assertEqual(node["kind"], "ExecNode")
        self.assertEqual(node["target"]["components"], ["+"])

    def test_multiple_exec_nodes(self):
        """Test parsing multiple exec nodes in sequence."""
        ast = parse(">a >b >c")
        self.assertEqual(len(ast["body"]), 3)

        for i, name in enumerate(["a", "b", "c"]):
            self.assertEqual(ast["body"][i]["kind"], "ExecNode")
            self.assertEqual(ast["body"][i]["target"]["components"], [name])


class TestStoreNodes(unittest.TestCase):
    """Tests for StoreNode parsing.

    Parser must:
    - Accept ValuePath as target (store to cell value)
    - Accept ReferencePath as target (replace cell)
    - Reject BlockNode as target (lexer already prevents this)
    """

    def test_store_simple_path(self):
        """Test parsing !x."""
        ast = parse("!x")
        node = ast["body"][0]
        self.assertEqual(node["kind"], "StoreNode")
        self.assertEqual(node["target"]["kind"], "ValuePath")
        self.assertEqual(node["target"]["components"], ["x"])

    def test_store_multi_component_path(self):
        """Test parsing !a.b.c."""
        ast = parse("!a.b.c")
        node = ast["body"][0]
        self.assertEqual(node["kind"], "StoreNode")
        self.assertEqual(node["target"]["kind"], "ValuePath")
        self.assertEqual(node["target"]["components"], ["a", "b", "c"])

    def test_store_register_path(self):
        """Test parsing !_.temp."""
        ast = parse("!_.temp")
        node = ast["body"][0]
        self.assertEqual(node["kind"], "StoreNode")
        self.assertEqual(node["target"]["kind"], "ValuePath")
        self.assertEqual(node["target"]["components"], ["_", "temp"])

    def test_store_reference_path(self):
        """Test parsing !x. (store to cell reference)."""
        ast = parse("!x.")
        node = ast["body"][0]
        self.assertEqual(node["kind"], "StoreNode")
        self.assertEqual(node["target"]["kind"], "ReferencePath")
        self.assertEqual(node["target"]["components"], ["x"])

    def test_store_multi_component_reference(self):
        """Test parsing !a.b. (store to nested cell)."""
        ast = parse("!a.b.")
        node = ast["body"][0]
        self.assertEqual(node["kind"], "StoreNode")
        self.assertEqual(node["target"]["kind"], "ReferencePath")
        self.assertEqual(node["target"]["components"], ["a", "b"])

    def test_store_register_reference(self):
        """Test parsing !_.x. (store to register cell)."""
        ast = parse("!_.x.")
        node = ast["body"][0]
        self.assertEqual(node["kind"], "StoreNode")
        self.assertEqual(node["target"]["kind"], "ReferencePath")
        self.assertEqual(node["target"]["components"], ["_", "x"])

    def test_multiple_store_nodes(self):
        """Test parsing multiple store nodes."""
        ast = parse("!a !b !c")
        self.assertEqual(len(ast["body"]), 3)

        for i, name in enumerate(["a", "b", "c"]):
            self.assertEqual(ast["body"][i]["kind"], "StoreNode")
            self.assertEqual(ast["body"][i]["target"]["components"], [name])


class TestCompletePrograms(unittest.TestCase):
    """Tests for complete SOMA programs (token stream → full AST)."""

    def test_simple_arithmetic(self):
        """Test parsing '1 2 >+'."""
        ast = parse("1 2 >+")
        self.assertEqual(len(ast["body"]), 3)

        self.assertEqual(ast["body"][0]["kind"], "IntNode")
        self.assertEqual(ast["body"][0]["value"], 1)

        self.assertEqual(ast["body"][1]["kind"], "IntNode")
        self.assertEqual(ast["body"][1]["value"], 2)

        self.assertEqual(ast["body"][2]["kind"], "ExecNode")
        self.assertEqual(ast["body"][2]["target"]["components"], ["+"])

    def test_store_and_retrieve(self):
        """Test parsing '42 !counter counter >print'."""
        ast = parse("42 !counter counter >print")
        self.assertEqual(len(ast["body"]), 4)

        self.assertEqual(ast["body"][0]["value"], 42)

        self.assertEqual(ast["body"][1]["kind"], "StoreNode")
        self.assertEqual(ast["body"][1]["target"]["components"], ["counter"])

        self.assertEqual(ast["body"][2]["kind"], "ValuePath")
        self.assertEqual(ast["body"][2]["components"], ["counter"])

        self.assertEqual(ast["body"][3]["kind"], "ExecNode")
        self.assertEqual(ast["body"][3]["target"]["components"], ["print"])

    def test_block_definition_and_storage(self):
        """Test parsing '{ >dup >* } !square'."""
        ast = parse("{ >dup >* } !square")
        self.assertEqual(len(ast["body"]), 2)

        block = ast["body"][0]
        self.assertEqual(block["kind"], "BlockNode")
        self.assertEqual(len(block["body"]), 2)
        self.assertEqual(block["body"][0]["kind"], "ExecNode")
        self.assertEqual(block["body"][1]["kind"], "ExecNode")

        store = ast["body"][1]
        self.assertEqual(store["kind"], "StoreNode")
        self.assertEqual(store["target"]["components"], ["square"])

    def test_register_operations(self):
        """Test parsing '1 !_.x _.x _.x >* !_.result'."""
        ast = parse("1 !_.x _.x _.x >* !_.result")
        self.assertEqual(len(ast["body"]), 6)

        # Check register paths are parsed correctly
        store1 = ast["body"][1]
        self.assertEqual(store1["target"]["components"], ["_", "x"])

        path1 = ast["body"][2]
        self.assertEqual(path1["components"], ["_", "x"])

        store2 = ast["body"][5]
        self.assertEqual(store2["target"]["components"], ["_", "result"])

    def test_cellref_operations(self):
        """Test parsing 'data. !ref 42 !ref'."""
        ast = parse("data. !ref 42 !ref")
        self.assertEqual(len(ast["body"]), 4)

        # First: reference path data.
        ref_path = ast["body"][0]
        self.assertEqual(ref_path["kind"], "ReferencePath")
        self.assertEqual(ref_path["components"], ["data"])

        # Second: store to value at ref
        store1 = ast["body"][1]
        self.assertEqual(store1["target"]["kind"], "ValuePath")

        # Fourth: store to cell itself (structural mutation)
        store2 = ast["body"][3]
        self.assertEqual(store2["target"]["kind"], "ValuePath")

    def test_execute_inline_block(self):
        """Test parsing '>{ 5 5 >* }'."""
        ast = parse(">{ 5 5 >* }")
        node = ast["body"][0]

        self.assertEqual(node["kind"], "ExecNode")
        self.assertEqual(node["target"]["kind"], "BlockNode")

        block_body = node["target"]["body"]
        self.assertEqual(len(block_body), 3)
        self.assertEqual(block_body[0]["value"], 5)
        self.assertEqual(block_body[1]["value"], 5)
        self.assertEqual(block_body[2]["kind"], "ExecNode")

    def test_complex_nested_example(self):
        """Test parsing complex nested program."""
        source = """
        {
            0 !_.counter
            _.counter 10 ><
            { _.counter 1 >+ !_.counter }
            >choose
        }
        """
        ast = parse(source)

        block = ast["body"][0]
        self.assertEqual(block["kind"], "BlockNode")

        # Should have multiple statements in block body
        self.assertGreater(len(block["body"]), 0)

    def test_empty_program(self):
        """Test parsing empty program."""
        ast = parse("")
        self.assertEqual(ast["kind"], "Program")
        self.assertEqual(ast["body"], [])

    def test_whitespace_only_program(self):
        """Test parsing whitespace-only program."""
        ast = parse("   \n\t   ")
        self.assertEqual(ast["kind"], "Program")
        self.assertEqual(ast["body"], [])


class TestEdgeCases(unittest.TestCase):
    """Tests for edge cases and corner cases."""

    def test_single_underscore_alone(self):
        """Test that single '_' is valid (register root)."""
        ast = parse("_")
        node = ast["body"][0]
        self.assertEqual(node["kind"], "ValuePath")
        self.assertEqual(node["components"], ["_"])

    def test_single_underscore_with_dot(self):
        """Test that '_.' is valid (register root reference)."""
        ast = parse("_.")
        node = ast["body"][0]
        self.assertEqual(node["kind"], "ReferencePath")
        self.assertEqual(node["components"], ["_"])

    def test_path_with_many_components(self):
        """Test parsing path with many components."""
        ast = parse("a.b.c.d.e.f.g")
        node = ast["body"][0]
        self.assertEqual(len(node["components"]), 7)
        self.assertEqual(node["components"], ["a", "b", "c", "d", "e", "f", "g"])

    def test_standalone_modifier_chars_as_paths(self):
        """Test that standalone > and ! are parsed as paths (from lexer)."""
        ast = parse("> !")

        # Standalone > and ! lex as PATH tokens
        self.assertEqual(len(ast["body"]), 2)
        self.assertEqual(ast["body"][0]["kind"], "ValuePath")
        self.assertEqual(ast["body"][0]["components"], [">"])
        self.assertEqual(ast["body"][1]["kind"], "ValuePath")
        self.assertEqual(ast["body"][1]["components"], ["!"])

    def test_adjacent_blocks(self):
        """Test parsing adjacent blocks."""
        ast = parse("{1}{2}{3}")
        self.assertEqual(len(ast["body"]), 3)

        for i in range(3):
            self.assertEqual(ast["body"][i]["kind"], "BlockNode")
            self.assertEqual(ast["body"][i]["body"][0]["value"], i + 1)

    def test_deeply_nested_empty_blocks(self):
        """Test parsing deeply nested empty blocks."""
        ast = parse("{ { { { } } } }")

        level1 = ast["body"][0]
        level2 = level1["body"][0]
        level3 = level2["body"][0]
        level4 = level3["body"][0]

        self.assertEqual(level4["kind"], "BlockNode")
        self.assertEqual(level4["body"], [])

    def test_mixed_paths_and_references(self):
        """Test mixing value paths and reference paths."""
        ast = parse("a a. b b. c c.")
        self.assertEqual(len(ast["body"]), 6)

        self.assertEqual(ast["body"][0]["kind"], "ValuePath")
        self.assertEqual(ast["body"][1]["kind"], "ReferencePath")
        self.assertEqual(ast["body"][2]["kind"], "ValuePath")
        self.assertEqual(ast["body"][3]["kind"], "ReferencePath")
        self.assertEqual(ast["body"][4]["kind"], "ValuePath")
        self.assertEqual(ast["body"][5]["kind"], "ReferencePath")

    def test_exec_and_store_operators(self):
        """Test executing and storing operator paths."""
        ast = parse(">+ !- >* !/")

        self.assertEqual(ast["body"][0]["kind"], "ExecNode")
        self.assertEqual(ast["body"][0]["target"]["components"], ["+"])

        self.assertEqual(ast["body"][1]["kind"], "StoreNode")
        self.assertEqual(ast["body"][1]["target"]["components"], ["-"])

        self.assertEqual(ast["body"][2]["kind"], "ExecNode")
        self.assertEqual(ast["body"][2]["target"]["components"], ["*"])

        self.assertEqual(ast["body"][3]["kind"], "StoreNode")
        self.assertEqual(ast["body"][3]["target"]["components"], ["/"])


class TestSourceLocations(unittest.TestCase):
    """Tests for source location tracking in AST nodes.

    Every AST node should have location information for error reporting.
    """

    def test_nodes_have_location_info(self):
        """Test that AST nodes include location information."""
        ast = parse("42")
        node = ast["body"][0]

        # Location should exist
        self.assertIn("location", node)

        # Location should have required fields
        loc = node["location"]
        self.assertIn("line", loc)
        self.assertIn("column", loc)
        self.assertIn("length", loc)

    def test_program_has_location(self):
        """Test that Program node has location."""
        ast = parse("1 2 3")
        self.assertIn("location", ast)


class TestErrorMessages(unittest.TestCase):
    """Tests for clear error messages with helpful information."""

    def test_unclosed_block_error_message(self):
        """Test unclosed block error provides helpful message."""
        with self.assertRaises(ParseError) as ctx:
            parse("{")

        error_msg = str(ctx.exception)
        # Should mention unclosed or missing brace
        self.assertTrue(
            "unclosed" in error_msg.lower() or
            "missing" in error_msg.lower()
        )

    def test_invalid_register_error_message(self):
        """Test invalid register path error is helpful."""
        with self.assertRaises(ParseError) as ctx:
            parse("_temp")

        error_msg = str(ctx.exception)
        # Should mention register syntax and suggest correct form
        self.assertIn("register", error_msg.lower())
        self.assertIn("_temp", error_msg)

    def test_exec_reference_error_message(self):
        """Test executing reference path error is clear."""
        with self.assertRaises(ParseError) as ctx:
            parse(">a.b.")

        error_msg = str(ctx.exception)
        # Should mention cannot execute reference/CellRef
        self.assertTrue(
            "reference" in error_msg.lower() or
            "cellref" in error_msg.lower()
        )


class TestParserRobustness(unittest.TestCase):
    """Tests for parser robustness and error recovery."""

    def test_handles_comments_from_lexer(self):
        """Test that parser handles lexer-stripped comments correctly."""
        # Lexer removes comments, parser should see only the code
        ast = parse("42 ) this is a comment\n>print")
        self.assertEqual(len(ast["body"]), 2)
        self.assertEqual(ast["body"][0]["value"], 42)
        self.assertEqual(ast["body"][1]["kind"], "ExecNode")

    def test_handles_multiline_input(self):
        """Test parsing multiline programs."""
        source = """
        1
        2
        >+
        """
        ast = parse(source)
        self.assertEqual(len(ast["body"]), 3)

    def test_consecutive_blocks_with_content(self):
        """Test parsing consecutive non-empty blocks."""
        ast = parse("{1 2}{3 4}{5 6}")
        self.assertEqual(len(ast["body"]), 3)

        for i, block in enumerate(ast["body"]):
            self.assertEqual(len(block["body"]), 2)


if __name__ == "__main__":
    unittest.main()
