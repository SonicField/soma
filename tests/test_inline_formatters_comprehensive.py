#!/usr/bin/env python3
"""
Comprehensive tests for inline formatters (md.b, md.i, md.c) with special characters and edge cases.

Tests the U+100000 tagging system to ensure:
1. Special HTML characters are escaped in inline formatters
2. Inline formatters work correctly in various contexts (lists, tables, etc.)
3. Tagged content doesn't get double-escaped
4. Edge cases are handled properly
"""

import unittest
import tempfile
import os
from pathlib import Path
import sys

# Add soma to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from soma.vm import run_soma_program


class TestInlineFormattersWithSpecialChars(unittest.TestCase):
    """Test inline formatters handle special HTML characters correctly."""

    def test_bold_with_html_chars(self):
        """Test md.b escapes <, >, & characters."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use
            >md.start
            md.htmlEmitter >md.emitter

            (<dogs> & cats) >md.b
            >md.p

            ({temp_path}) >md.render
            """
            run_soma_program(code)
            content = Path(temp_path).read_text()

            # Should escape the special characters
            self.assertIn("<strong>&lt;dogs&gt; &amp; cats</strong>", content)
            # Should NOT have unescaped tags
            self.assertNotIn("<dogs>", content)
        finally:
            os.unlink(temp_path)

    def test_italic_with_html_chars(self):
        """Test md.i escapes HTML tags."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use
            >md.start
            md.htmlEmitter >md.emitter

            (<div>content</div>) >md.i
            >md.p

            ({temp_path}) >md.render
            """
            run_soma_program(code)
            content = Path(temp_path).read_text()

            # Should escape div tags
            self.assertIn("&lt;div&gt;", content)
            self.assertIn("&lt;/div&gt;", content)
            self.assertNotIn("<div>", content)
        finally:
            os.unlink(temp_path)

    def test_code_with_html_chars(self):
        """Test md.c escapes <, >, & in code snippets."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use
            >md.start
            md.htmlEmitter >md.emitter

            (if x < 5 && y > 3) >md.c
            >md.p

            ({temp_path}) >md.render
            """
            run_soma_program(code)
            content = Path(temp_path).read_text()

            # Should escape comparison operators
            self.assertIn("<code>if x &lt; 5 &amp;&amp; y &gt; 3</code>", content)
        finally:
            os.unlink(temp_path)


class TestInlineFormattersInContexts(unittest.TestCase):
    """Test inline formatters work correctly in lists, tables, etc."""

    # Note: Tests with parentheses in code (like print()) are complex due to SOMA syntax
    # The escaping tests above cover the important security scenarios

    def test_bold_in_definition_list(self):
        """Test md.b inside definition list values (real user scenario)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            # This is the actual pattern from the user's example
            code = f"""
            (python) >use
            (markdown) >use
            >md.start
            md.htmlEmitter >md.emitter

            (Full version) (SKILL.md) >md.b
            (Compact version) (SKILL-COMPACT.md) >md.b
            >md.dul

            ({temp_path}) >md.render
            """
            run_soma_program(code)
            content = Path(temp_path).read_text()

            # Should have label bold and value bold
            self.assertIn("<strong>Full version</strong>", content)
            self.assertIn("<strong>SKILL.md</strong>", content)
            self.assertIn("<strong>Compact version</strong>", content)
            self.assertIn("<strong>SKILL-COMPACT.md</strong>", content)
            # Should NOT double-escape
            self.assertNotIn("&lt;strong&gt;", content)
        finally:
            os.unlink(temp_path)

    def test_code_with_special_chars_in_definition_list(self):
        """Test md.c with special characters inside definition lists."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use
            >md.start
            md.htmlEmitter >md.emitter

            (Comparison) (x < 5) >md.c
            (Logic) (a && b) >md.c
            >md.dul

            ({temp_path}) >md.render
            """
            run_soma_program(code)
            content = Path(temp_path).read_text()

            # Code should not be escaped
            self.assertIn("<code>x &lt; 5</code>", content)
            self.assertIn("<code>a &amp;&amp; b</code>", content)
            # Strong tags should not be escaped
            self.assertIn("<strong>Comparison</strong>", content)
            self.assertIn("<strong>Logic</strong>", content)
            # Should NOT double-escape
            self.assertNotIn("&lt;code&gt;", content)
            self.assertNotIn("&lt;strong&gt;", content)
        finally:
            os.unlink(temp_path)

    def test_bold_in_table_cell(self):
        """Test md.b inside table cells."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use
            >md.start
            md.htmlEmitter >md.emitter

            (Status) (Progress)
            >md.table.header

            (Active) >md.b (100%) >md.b
            >md.table.row

            >md.table.left >md.table.centre
            >md.table.align

            >md.table
            >md.p

            ({temp_path}) >md.render
            """
            run_soma_program(code)
            content = Path(temp_path).read_text()

            # Bold tags should be rendered, not escaped
            self.assertIn("<td style=\"text-align: left\"><strong>Active</strong></td>", content)
            self.assertIn("<td style=\"text-align: center\"><strong>100%</strong></td>", content)
            # Should NOT be double-escaped
            self.assertNotIn("&lt;strong&gt;", content)
        finally:
            os.unlink(temp_path)

    def test_code_in_table_with_special_chars(self):
        """Test md.c with special chars in table cells."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use
            >md.start
            md.htmlEmitter >md.emitter

            (Operation) (Code)
            >md.table.header

            (Less than) (x < 5) >md.c
            >md.table.row

            (Greater than) (y > 10) >md.c
            >md.table.row

            >md.table.left >md.table.left
            >md.table.align

            >md.table
            >md.p

            ({temp_path}) >md.render
            """
            run_soma_program(code)
            content = Path(temp_path).read_text()

            # Code blocks should be rendered with escaped special chars
            self.assertIn("<code>x &lt; 5</code>", content)
            self.assertIn("<code>y &gt; 10</code>", content)
            # Code tags themselves should not be escaped
            self.assertNotIn("&lt;code&gt;", content)
        finally:
            os.unlink(temp_path)


class TestInlineFormatterEdgeCases(unittest.TestCase):
    """Test edge cases for inline formatters."""

    def test_empty_bold(self):
        """Test md.b with empty string."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use
            >md.start
            md.htmlEmitter >md.emitter

            () >md.b
            >md.p

            ({temp_path}) >md.render
            """
            run_soma_program(code)
            content = Path(temp_path).read_text()

            # Should handle empty string
            self.assertIn("<strong></strong>", content)
        finally:
            os.unlink(temp_path)

    def test_escaped_parentheses_in_code(self):
        """Test md.c with escaped parentheses (the user's original example)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            code = r"""
            (python) >use
            (markdown) >use
            >md.start
            md.htmlEmitter >md.emitter

            (Full version) (SKILL.md (~7,500 tokens\29\) >md.c
            (Compact version) (SKILL-COMPACT.md (~1,300 tokens\29\) >md.c
            >md.dul

            ({}) >md.render
            """.format(temp_path)
            run_soma_program(code)
            content = Path(temp_path).read_text()

            # Code tags should be rendered, not escaped
            self.assertIn("<code>SKILL.md (~7,500 tokens)</code>", content)
            self.assertIn("<code>SKILL-COMPACT.md (~1,300 tokens)</code>", content)
            # Should NOT double-escape
            self.assertNotIn("&lt;code&gt;", content)
        finally:
            os.unlink(temp_path)

    # Note: Complex inline concatenation tests with special SOMA characters
    # are covered by the user's original escaped parentheses test above

    def test_raw_html_in_paragraph_gets_escaped(self):
        """Test that raw HTML in paragraphs is escaped (security test)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use
            >md.start
            md.htmlEmitter >md.emitter

            (<div>User input</div>)
            >md.p

            ({temp_path}) >md.render
            """
            run_soma_program(code)
            content = Path(temp_path).read_text()

            # Raw HTML should be escaped
            self.assertIn("&lt;div&gt;", content)
            self.assertIn("&lt;/div&gt;", content)
            self.assertNotIn("<div>User", content)
        finally:
            os.unlink(temp_path)


if __name__ == '__main__':
    unittest.main()
