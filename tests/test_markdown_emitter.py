#!/usr/bin/env python3
"""
Tests for MarkdownEmitter - TDD Approach (Tests Written BEFORE Implementation)

This test file defines the expected behavior of the MarkdownEmitter class through tests.
All tests should FAIL initially because the MarkdownEmitter class does not exist yet.

The tests verify that the MarkdownEmitter correctly implements all 18 methods defined
in the Emitter Interface (EMITTER_INTERFACE.md).

Expected Result: All tests FAIL with ImportError (MarkdownEmitter class doesn't exist)
"""

import unittest
import sys
from pathlib import Path

# Add soma to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# This import will FAIL - that's expected! (TDD: write tests first)
from soma.extensions.markdown_emitter import MarkdownEmitter


class TestMarkdownEmitterInlineFormatting(unittest.TestCase):
    """Test inline formatting methods: bold, italic, code, link."""

    def setUp(self):
        """Create a MarkdownEmitter instance for each test."""
        self.emitter = MarkdownEmitter()

    def test_markdown_emitter_bold(self):
        """Test bold() wraps text in **text** format."""
        result = self.emitter.bold("hello")
        self.assertEqual(
            result,
            "**hello**",
            "bold() should wrap text in double asterisks"
        )

    def test_markdown_emitter_italic(self):
        """Test italic() wraps text in _text_ format."""
        result = self.emitter.italic("hello")
        self.assertEqual(
            result,
            "_hello_",
            "italic() should wrap text in underscores"
        )

    def test_markdown_emitter_code(self):
        """Test code() wraps text in `text` format."""
        result = self.emitter.code("x = 42")
        self.assertEqual(
            result,
            "`x = 42`",
            "code() should wrap text in backticks"
        )

    def test_markdown_emitter_link(self):
        """Test link() creates [text](url) format."""
        result = self.emitter.link("Google", "https://google.com")
        self.assertEqual(
            result,
            "[Google](https://google.com)",
            "link() should create markdown link format"
        )


class TestMarkdownEmitterHeadings(unittest.TestCase):
    """Test heading methods: heading1, heading2, heading3, heading4."""

    def setUp(self):
        """Create a MarkdownEmitter instance for each test."""
        self.emitter = MarkdownEmitter()

    def test_markdown_emitter_heading1(self):
        """Test heading1() creates # text\\n\\n format."""
        result = self.emitter.heading1("Title")
        self.assertEqual(
            result,
            "# Title\n\n",
            "heading1() should create H1 with # and trailing blank line"
        )

    def test_markdown_emitter_heading2(self):
        """Test heading2() creates ## text\\n\\n format."""
        result = self.emitter.heading2("Section")
        self.assertEqual(
            result,
            "## Section\n\n",
            "heading2() should create H2 with ## and trailing blank line"
        )

    def test_markdown_emitter_heading3(self):
        """Test heading3() creates ### text\\n\\n format."""
        result = self.emitter.heading3("Subsection")
        self.assertEqual(
            result,
            "### Subsection\n\n",
            "heading3() should create H3 with ### and trailing blank line"
        )

    def test_markdown_emitter_heading4(self):
        """Test heading4() creates #### text\\n\\n format."""
        result = self.emitter.heading4("Detail")
        self.assertEqual(
            result,
            "#### Detail\n\n",
            "heading4() should create H4 with #### and trailing blank line"
        )


class TestMarkdownEmitterBlockElements(unittest.TestCase):
    """Test block element methods: paragraph, blockquote, horizontal_rule."""

    def setUp(self):
        """Create a MarkdownEmitter instance for each test."""
        self.emitter = MarkdownEmitter()

    def test_markdown_emitter_paragraph(self):
        """Test paragraph() creates separate paragraphs for each item."""
        result = self.emitter.paragraph(["First para", "Second para"])
        self.assertEqual(
            result,
            "First para\n\nSecond para\n\n",
            "paragraph() should create separate paragraphs with blank lines"
        )

    def test_markdown_emitter_blockquote(self):
        """Test blockquote() creates > prefixed lines."""
        result = self.emitter.blockquote(["Line 1", "Line 2"])
        self.assertEqual(
            result,
            "> Line 1\n> Line 2\n\n",
            "blockquote() should prefix each line with > and add trailing blank line"
        )

    def test_markdown_emitter_horizontal_rule(self):
        """Test horizontal_rule() creates ---\\n\\n."""
        result = self.emitter.horizontal_rule()
        self.assertEqual(
            result,
            "---\n\n",
            "horizontal_rule() should create --- with trailing blank line"
        )


class TestMarkdownEmitterLists(unittest.TestCase):
    """Test list methods: unordered_list, ordered_list, list_item_formatted."""

    def setUp(self):
        """Create a MarkdownEmitter instance for each test."""
        self.emitter = MarkdownEmitter()

    def test_markdown_emitter_unordered_list(self):
        """Test unordered_list() creates - prefixed items at depth 0."""
        result = self.emitter.unordered_list(["Item 1", "Item 2"], depth=0)
        self.assertEqual(
            result,
            "- Item 1\n- Item 2\n\n",
            "unordered_list() at depth 0 should create - items with trailing blank line"
        )

    def test_markdown_emitter_ordered_list(self):
        """Test ordered_list() creates numbered items at depth 0."""
        result = self.emitter.ordered_list(["First", "Second"], depth=0)
        self.assertEqual(
            result,
            "1. First\n2. Second\n\n",
            "ordered_list() at depth 0 should create numbered items with trailing blank line"
        )

    def test_markdown_emitter_nested_list(self):
        """Test nested list with depth=1 indents with 2 spaces and no trailing blank line."""
        # Test unordered list at depth 1
        ul_result = self.emitter.unordered_list(["Nested A", "Nested B"], depth=1)
        self.assertEqual(
            ul_result,
            "  - Nested A\n  - Nested B\n",
            "unordered_list() at depth 1 should indent 2 spaces and have no trailing blank line"
        )

        # Test ordered list at depth 1
        ol_result = self.emitter.ordered_list(["Nested 1", "Nested 2"], depth=1)
        self.assertEqual(
            ol_result,
            "  1. Nested 1\n  2. Nested 2\n",
            "ordered_list() at depth 1 should indent 2 spaces and have no trailing blank line"
        )

    def test_markdown_emitter_list_item_formatted(self):
        """Test list_item_formatted() creates **label**: value format."""
        result = self.emitter.list_item_formatted("Name", "Alice")
        self.assertEqual(
            result,
            "**Name**: Alice",
            "list_item_formatted() should bold label and append colon and value"
        )


class TestMarkdownEmitterCodeBlocks(unittest.TestCase):
    """Test code block methods: code_block."""

    def setUp(self):
        """Create a MarkdownEmitter instance for each test."""
        self.emitter = MarkdownEmitter()

    def test_markdown_emitter_code_block_with_lang(self):
        """Test code_block() with language creates ```lang format."""
        result = self.emitter.code_block(
            ["def hello():", "    print('hi')"],
            language="python"
        )
        self.assertEqual(
            result,
            "```python\ndef hello():\n    print('hi')\n```\n\n",
            "code_block() with language should create fenced code block with language"
        )

    def test_markdown_emitter_code_block_no_lang(self):
        """Test code_block() without language creates ``` format."""
        result = self.emitter.code_block(["plain text"], language=None)
        self.assertEqual(
            result,
            "```\nplain text\n```\n\n",
            "code_block() with no language should create fenced code block without language"
        )


class TestMarkdownEmitterTables(unittest.TestCase):
    """Test table method: table."""

    def setUp(self):
        """Create a MarkdownEmitter instance for each test."""
        self.emitter = MarkdownEmitter()

    def test_markdown_emitter_table(self):
        """Test table() creates markdown table with header and rows."""
        result = self.emitter.table(
            header=["Name", "Age"],
            rows=[["Alice", "30"], ["Bob", "25"]],
            alignment=None
        )

        # Check that result contains expected table structure
        lines = result.strip().split('\n')

        # Should have 4 lines: header, separator, row1, row2
        self.assertEqual(len(lines), 4, "Table should have 4 lines: header + separator + 2 rows")

        # Header should contain column names
        self.assertIn("Name", lines[0])
        self.assertIn("Age", lines[0])

        # Separator should be second line with dashes
        self.assertIn("---", lines[1])

        # Rows should contain data
        self.assertIn("Alice", lines[2])
        self.assertIn("30", lines[2])
        self.assertIn("Bob", lines[3])
        self.assertIn("25", lines[3])

        # Should end with blank line
        self.assertTrue(result.endswith("\n\n"), "Table should end with blank line")

    def test_markdown_emitter_table_with_alignment(self):
        """Test table() with alignment creates proper alignment markers."""
        result = self.emitter.table(
            header=["Left", "Center", "Right"],
            rows=[["A", "B", "C"]],
            alignment=["left", "centre", "right"]
        )

        lines = result.strip().split('\n')

        # Check separator line has alignment markers
        separator = lines[1]
        self.assertIn(":---", separator, "Left alignment should have :--- marker")
        self.assertIn(":---:", separator, "Center alignment should have :---: marker")
        self.assertIn("---:", separator, "Right alignment should have ---: marker")


class TestMarkdownEmitterSpecialOperations(unittest.TestCase):
    """Test special operation methods: concat, join, data_title."""

    def setUp(self):
        """Create a MarkdownEmitter instance for each test."""
        self.emitter = MarkdownEmitter()

    def test_markdown_emitter_concat(self):
        """Test concat() joins items with no separator."""
        result = self.emitter.concat(["Hello", " ", "world"])
        self.assertEqual(
            result,
            "Hello world",
            "concat() should join items with no separator"
        )

    def test_markdown_emitter_join(self):
        """Test join() joins items with specified separator."""
        result = self.emitter.join(["a", "b", "c"], separator=", ")
        self.assertEqual(
            result,
            "a, b, c",
            "join() should join items with specified separator"
        )

    def test_markdown_emitter_data_title(self):
        """Test data_title() creates alternating bold pattern."""
        result = self.emitter.data_title(["Name", "Alice", "Age", "30"])
        self.assertEqual(
            result,
            "**Name** Alice **Age** 30",
            "data_title() should bold even-indexed items and join with spaces"
        )


class TestMarkdownEmitterEdgeCases(unittest.TestCase):
    """Test edge cases and empty inputs."""

    def setUp(self):
        """Create a MarkdownEmitter instance for each test."""
        self.emitter = MarkdownEmitter()

    def test_empty_list_paragraph(self):
        """Test paragraph() with empty list returns empty string."""
        result = self.emitter.paragraph([])
        self.assertEqual(result, "", "Empty list should return empty string")

    def test_empty_list_unordered_list(self):
        """Test unordered_list() with empty list returns empty string or minimal output."""
        result = self.emitter.unordered_list([], depth=0)
        # Could be "" or "\n\n" depending on implementation
        self.assertIn(result, ["", "\n\n"], "Empty list should return empty or blank line")

    def test_empty_list_ordered_list(self):
        """Test ordered_list() with empty list returns empty string or minimal output."""
        result = self.emitter.ordered_list([], depth=0)
        # Could be "" or "\n\n" depending on implementation
        self.assertIn(result, ["", "\n\n"], "Empty list should return empty or blank line")

    def test_single_item_paragraph(self):
        """Test paragraph() with single item."""
        result = self.emitter.paragraph(["Single paragraph"])
        self.assertEqual(
            result,
            "Single paragraph\n\n",
            "Single item should still add trailing blank line"
        )

    def test_code_block_empty_string_language(self):
        """Test code_block() with empty string for language (same as None)."""
        result = self.emitter.code_block(["line 1"], language="")
        self.assertEqual(
            result,
            "```\nline 1\n```\n\n",
            "Empty string language should be treated same as None"
        )


if __name__ == '__main__':
    unittest.main()
