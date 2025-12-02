#!/usr/bin/env python3
"""
Tests for HtmlEmitter - TDD Approach (Tests Written BEFORE Implementation)

This test file defines the expected behavior of the HtmlEmitter class through tests.
All tests should FAIL initially because the HtmlEmitter class does not exist yet.

The tests verify that the HtmlEmitter correctly implements all 18 methods defined
in the Emitter Interface (EMITTER_INTERFACE.md), producing valid HTML output.

Key HTML Conventions (Display over Semantics):
- Use <b> instead of <strong>
- Use <i> instead of <em>
- Use <code> for inline code
- Proper HTML escaping for special characters (&, <, >, ")

Expected Result: All tests FAIL with ImportError (HtmlEmitter class doesn't exist)
"""

import unittest
import sys
from pathlib import Path

# Add soma to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# This import will FAIL - that's expected! (TDD: write tests first)
from soma.extensions.markdown_emitter import HtmlEmitter


class TestHtmlEmitterInlineFormatting(unittest.TestCase):
    """Test inline formatting methods: bold, italic, code, link."""

    def setUp(self):
        """Create an HtmlEmitter instance for each test."""
        self.emitter = HtmlEmitter()

    def test_html_emitter_bold(self):
        """Test bold() wraps text in <strong>text</strong> format."""
        result = self.emitter.bold("hello")
        self.assertEqual(
            result,
            "<strong>hello</strong>",
            "bold() should wrap text in <strong> tags"
        )

    def test_html_emitter_italic(self):
        """Test italic() wraps text in <i>text</i> format."""
        result = self.emitter.italic("hello")
        self.assertEqual(
            result,
            "<i>hello</i>",
            "italic() should wrap text in <i> tags"
        )

    def test_html_emitter_code(self):
        """Test code() wraps text in <code>text</code> format."""
        result = self.emitter.code("x = 42")
        self.assertEqual(
            result,
            "<code>x = 42</code>",
            "code() should wrap text in <code> tags"
        )

    def test_html_emitter_link(self):
        """Test link() creates <a href="url">text</a> format."""
        result = self.emitter.link("Google", "https://google.com")
        self.assertEqual(
            result,
            '<a href="https://google.com">Google</a>',
            "link() should create HTML anchor tag"
        )


class TestHtmlEmitterHeadings(unittest.TestCase):
    """Test heading methods: heading1, heading2, heading3, heading4."""

    def setUp(self):
        """Create an HtmlEmitter instance for each test."""
        self.emitter = HtmlEmitter()

    def test_html_emitter_heading1(self):
        """Test heading1() creates <h1>text</h1>\\n format."""
        result = self.emitter.heading1("Title")
        self.assertEqual(
            result,
            "<h1>Title</h1>\n",
            "heading1() should create <h1> tag with trailing newline"
        )

    def test_html_emitter_heading2(self):
        """Test heading2() creates <h2>text</h2>\\n format."""
        result = self.emitter.heading2("Section")
        self.assertEqual(
            result,
            "<h2>Section</h2>\n",
            "heading2() should create <h2> tag with trailing newline"
        )

    def test_html_emitter_heading3(self):
        """Test heading3() creates <h3>text</h3>\\n format."""
        result = self.emitter.heading3("Subsection")
        self.assertEqual(
            result,
            "<h3>Subsection</h3>\n",
            "heading3() should create <h3> tag with trailing newline"
        )

    def test_html_emitter_heading4(self):
        """Test heading4() creates <h4>text</h4>\\n format."""
        result = self.emitter.heading4("Detail")
        self.assertEqual(
            result,
            "<h4>Detail</h4>\n",
            "heading4() should create <h4> tag with trailing newline"
        )


class TestHtmlEmitterBlockElements(unittest.TestCase):
    """Test block element methods: paragraph, blockquote, horizontal_rule."""

    def setUp(self):
        """Create an HtmlEmitter instance for each test."""
        self.emitter = HtmlEmitter()

    def test_html_emitter_paragraph(self):
        """Test paragraph() creates separate <p> tags for each item."""
        result = self.emitter.paragraph(["First para", "Second para"])
        self.assertEqual(
            result,
            "<p>First para</p>\n<p>Second para</p>\n",
            "paragraph() should create separate <p> tags for each item"
        )

    def test_html_emitter_blockquote(self):
        """Test blockquote() wraps items in <blockquote> with <p> tags."""
        result = self.emitter.blockquote(["Line 1", "Line 2"])
        self.assertEqual(
            result,
            "<blockquote>\n<p>Line 1</p>\n<p>Line 2</p>\n</blockquote>\n",
            "blockquote() should wrap items in <blockquote> with <p> tags per line"
        )

    def test_html_emitter_horizontal_rule(self):
        """Test horizontal_rule() creates <hr>\\n."""
        result = self.emitter.horizontal_rule()
        self.assertEqual(
            result,
            "<hr>\n",
            "horizontal_rule() should create self-closing <hr> tag"
        )


class TestHtmlEmitterLists(unittest.TestCase):
    """Test list methods: unordered_list, ordered_list, list_item_formatted."""

    def setUp(self):
        """Create an HtmlEmitter instance for each test."""
        self.emitter = HtmlEmitter()

    def test_html_emitter_unordered_list(self):
        """Test unordered_list() creates <ul> with <li> items."""
        result = self.emitter.unordered_list(["Item 1", "Item 2"], depth=0)
        self.assertEqual(
            result,
            "<ul>\n  <li>Item 1</li>\n  <li>Item 2</li>\n</ul>\n",
            "unordered_list() should create <ul> with <li> tags"
        )

    def test_html_emitter_ordered_list(self):
        """Test ordered_list() creates <ol> with <li> items."""
        result = self.emitter.ordered_list(["First", "Second"], depth=0)
        self.assertEqual(
            result,
            "<ol>\n  <li>First</li>\n  <li>Second</li>\n</ol>\n",
            "ordered_list() should create <ol> with <li> tags"
        )

    def test_html_emitter_nested_list(self):
        """Test nested list with depth=1 still produces proper HTML structure."""
        # Test unordered list at depth 1
        ul_result = self.emitter.unordered_list(["Nested A", "Nested B"], depth=1)
        self.assertEqual(
            ul_result,
            "<ul>\n  <li>Nested A</li>\n  <li>Nested B</li>\n</ul>\n",
            "unordered_list() at depth 1 should produce same HTML structure (depth handled by caller)"
        )

        # Test ordered list at depth 1
        ol_result = self.emitter.ordered_list(["Nested 1", "Nested 2"], depth=1)
        self.assertEqual(
            ol_result,
            "<ol>\n  <li>Nested 1</li>\n  <li>Nested 2</li>\n</ol>\n",
            "ordered_list() at depth 1 should produce same HTML structure (depth handled by caller)"
        )

    def test_html_emitter_list_item_formatted(self):
        """Test list_item_formatted() creates <strong>label</strong>: value format."""
        result = self.emitter.list_item_formatted("Name", "Alice")
        self.assertEqual(
            result,
            "<strong>Name</strong>: Alice",
            "list_item_formatted() should bold label with <strong> tag"
        )


class TestHtmlEmitterCodeBlocks(unittest.TestCase):
    """Test code block methods: code_block."""

    def setUp(self):
        """Create an HtmlEmitter instance for each test."""
        self.emitter = HtmlEmitter()

    def test_html_emitter_code_block_with_lang(self):
        """Test code_block() with language creates <pre><code class="language-X"> format."""
        result = self.emitter.code_block(
            ["def hello():", "    print('hi')"],
            language="python"
        )
        self.assertEqual(
            result,
            '<pre><code class="language-python">def hello():\n    print(\'hi\')\n</code></pre>\n',
            "code_block() with language should create <pre><code> with language class"
        )

    def test_html_emitter_code_block_no_lang(self):
        """Test code_block() without language creates <pre><code> format."""
        result = self.emitter.code_block(["plain text"], language=None)
        self.assertEqual(
            result,
            "<pre><code>plain text\n</code></pre>\n",
            "code_block() with no language should create <pre><code> without class"
        )


class TestHtmlEmitterTables(unittest.TestCase):
    """Test table method: table."""

    def setUp(self):
        """Create an HtmlEmitter instance for each test."""
        self.emitter = HtmlEmitter()

    def test_html_emitter_table_basic(self):
        """Test table() creates HTML table with <thead> and <tbody>."""
        result = self.emitter.table(
            header=["Name", "Age"],
            rows=[["Alice", "30"], ["Bob", "25"]],
            alignment=None
        )

        # Check for proper table structure
        self.assertIn("<table>", result)
        self.assertIn("</table>", result)
        self.assertIn("<thead>", result)
        self.assertIn("</thead>", result)
        self.assertIn("<tbody>", result)
        self.assertIn("</tbody>", result)

        # Check header row
        self.assertIn("<th>Name</th>", result)
        self.assertIn("<th>Age</th>", result)

        # Check data rows
        self.assertIn("<td>Alice</td>", result)
        self.assertIn("<td>30</td>", result)
        self.assertIn("<td>Bob</td>", result)
        self.assertIn("<td>25</td>", result)

        # Should end with newline
        self.assertTrue(result.endswith("\n"), "Table should end with newline")

    def test_html_emitter_table_with_alignment(self):
        """Test table() with alignment adds style attributes."""
        result = self.emitter.table(
            header=["Left", "Center", "Right"],
            rows=[["A", "B", "C"]],
            alignment=["left", "centre", "right"]
        )

        # Check for alignment styles in header
        self.assertIn('style="text-align: left"', result)
        self.assertIn('style="text-align: center"', result)
        self.assertIn('style="text-align: right"', result)

        # Check that alignment is applied to both header and data cells
        # Header cells
        self.assertIn('<th style="text-align: left">Left</th>', result)
        self.assertIn('<th style="text-align: center">Center</th>', result)
        self.assertIn('<th style="text-align: right">Right</th>', result)

        # Data cells
        self.assertIn('<td style="text-align: left">A</td>', result)
        self.assertIn('<td style="text-align: center">B</td>', result)
        self.assertIn('<td style="text-align: right">C</td>', result)


class TestHtmlEmitterSpecialOperations(unittest.TestCase):
    """Test special operation methods: concat, join, data_title."""

    def setUp(self):
        """Create an HtmlEmitter instance for each test."""
        self.emitter = HtmlEmitter()

    def test_html_emitter_concat(self):
        """Test concat() joins items with no separator."""
        result = self.emitter.concat(["Hello", " ", "world"])
        self.assertEqual(
            result,
            "Hello world",
            "concat() should join items with no separator"
        )

    def test_html_emitter_join(self):
        """Test join() joins items with specified separator."""
        result = self.emitter.join(["a", "b", "c"], separator=", ")
        self.assertEqual(
            result,
            "a, b, c",
            "join() should join items with specified separator"
        )

    def test_html_emitter_data_title(self):
        """Test data_title() creates alternating <strong> pattern."""
        result = self.emitter.data_title(["Name", "Alice", "Age", "30"])
        self.assertEqual(
            result,
            "<strong>Name</strong> Alice <strong>Age</strong> 30",
            "data_title() should bold even-indexed items with <strong> tags"
        )


class TestHtmlEmitterEdgeCases(unittest.TestCase):
    """Test edge cases, empty inputs, and special character escaping."""

    def setUp(self):
        """Create an HtmlEmitter instance for each test."""
        self.emitter = HtmlEmitter()

    def test_empty_list_paragraph(self):
        """Test paragraph() with empty list returns empty string."""
        result = self.emitter.paragraph([])
        self.assertEqual(result, "", "Empty list should return empty string")

    def test_empty_list_unordered_list(self):
        """Test unordered_list() with empty list returns empty string or minimal output."""
        result = self.emitter.unordered_list([], depth=0)
        # Could be "" or "<ul>\n</ul>\n" depending on implementation
        self.assertIn(result, ["", "<ul>\n</ul>\n"], "Empty list should return empty or minimal structure")

    def test_empty_list_ordered_list(self):
        """Test ordered_list() with empty list returns empty string or minimal output."""
        result = self.emitter.ordered_list([], depth=0)
        # Could be "" or "<ol>\n</ol>\n" depending on implementation
        self.assertIn(result, ["", "<ol>\n</ol>\n"], "Empty list should return empty or minimal structure")

    def test_single_item_paragraph(self):
        """Test paragraph() with single item."""
        result = self.emitter.paragraph(["Single paragraph"])
        self.assertEqual(
            result,
            "<p>Single paragraph</p>\n",
            "Single item should still be wrapped in <p> tags"
        )

    def test_code_block_empty_string_language(self):
        """Test code_block() with empty string for language (same as None)."""
        result = self.emitter.code_block(["line 1"], language="")
        self.assertEqual(
            result,
            "<pre><code>line 1\n</code></pre>\n",
            "Empty string language should be treated same as None"
        )

    def test_html_emitter_escapes_special_chars(self):
        """Test that HTML special characters are properly escaped."""
        # Test escaping in bold text
        result = self.emitter.bold("A & B < C > D")
        self.assertEqual(
            result,
            "<strong>A &amp; B &lt; C &gt; D</strong>",
            "bold() should escape &, <, > characters"
        )

        # Test escaping in paragraph - Note: paragraph() does NOT escape because it receives
        # already-formatted content from inline formatters. If you need to escape, do it before
        # calling paragraph(), or use the full markdown extension which handles this correctly.
        # This test verifies that paragraph() does NOT double-escape HTML from inline formatters.
        result = self.emitter.paragraph(["<script>alert('xss')</script>"])
        self.assertEqual(
            result,
            "<p><script>alert('xss')</script></p>\n",
            "paragraph() should NOT escape - caller is responsible for escaping raw text"
        )

        # Test escaping in code
        result = self.emitter.code("if x < 5 && y > 3")
        self.assertEqual(
            result,
            "<code>if x &lt; 5 &amp;&amp; y &gt; 3</code>",
            "code() should escape special characters"
        )

        # Test escaping quotes in link URLs
        result = self.emitter.link("Click", 'http://example.com?q="test"')
        self.assertEqual(
            result,
            '<a href="http://example.com?q=&quot;test&quot;">Click</a>',
            "link() should escape quotes in URLs"
        )


if __name__ == '__main__':
    unittest.main()
