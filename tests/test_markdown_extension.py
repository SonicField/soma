#!/usr/bin/env python3
"""Tests for SOMA markdown extension."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add soma to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from soma.vm import VM, run_soma_program, Void, compile_program
from soma.parser import Parser
from soma.lexer import lex


class TestMarkdownExtension(unittest.TestCase):
    """Test cases for markdown extension - Stage 1: Basic Infrastructure."""

    def test_markdown_extension_loads(self):
        """Test that markdown extension can be loaded."""
        code = """
        (python) >use
        (markdown) >use
        """
        vm = VM()
        tokens = lex(code)
        parser = Parser(tokens)
        ast = parser.parse()
        compiled = compile_program(ast)
        vm.execute(compiled)
        # Should not error

    def test_md_start_initializes_state(self):
        """Test that >md.start sets up state machine."""
        code = """
        (python) >use
        (markdown) >use

        >md.start
        """
        al = run_soma_program(code)
        # Last item should be Void
        self.assertEqual(al[-1], Void)

    def test_empty_document_renders(self):
        """Test rendering empty document."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            # File should exist and be empty
            content = Path(temp_path).read_text()
            self.assertEqual(content, "")
        finally:
            os.unlink(temp_path)


class TestMarkdownStage2(unittest.TestCase):
    """Test cases for markdown extension - Stage 2: Simple Headings."""

    def test_single_h1_heading(self):
        """Test rendering a single H1 heading."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (My Title)
            >md.h1
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            self.assertEqual(content, "# My Title\n\n")
        finally:
            os.unlink(temp_path)

    def test_multiple_headings(self):
        """Test rendering multiple heading levels."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (Main Title)
            >md.h1
            (Section One)
            >md.h2
            (Subsection)
            >md.h3
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            expected = "# Main Title\n\n## Section One\n\n### Subsection\n\n"
            self.assertEqual(content, expected)
        finally:
            os.unlink(temp_path)

    def test_h4_heading(self):
        """Test H4 heading level."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (Main)
            >md.h1
            (Section)
            >md.h2
            (Subsection)
            >md.h3
            (Detail Level)
            >md.h4
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            expected = "# Main\n\n## Section\n\n### Subsection\n\n#### Detail Level\n\n"
            self.assertEqual(content, expected)
        finally:
            os.unlink(temp_path)

    def test_heading_drains_until_void(self):
        """Test that heading consumes all items until Void."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (This) (is) (a) (multi-word) (heading)
            >md.h1
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            # Should join with spaces
            self.assertEqual(content, "# This is a multi-word heading\n\n")
        finally:
            os.unlink(temp_path)


class TestMarkdownStage3(unittest.TestCase):
    """Test cases for markdown extension - Stage 3: Paragraphs."""

    def test_single_paragraph(self):
        """Test rendering a single paragraph."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (This is a paragraph.)
            >md.p
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            self.assertEqual(content, "This is a paragraph.\n\n")
        finally:
            os.unlink(temp_path)

    def test_mixed_headings_and_paragraphs(self):
        """Test rendering headings mixed with paragraphs."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (Document Title)
            >md.h1
            (This is the introduction paragraph.)
            >md.p
            (Section One)
            >md.h2
            (Some content for section one.)
            >md.p
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            expected = (
                "# Document Title\n\n"
                "This is the introduction paragraph.\n\n"
                "## Section One\n\n"
                "Some content for section one.\n\n"
            )
            self.assertEqual(content, expected)
        finally:
            os.unlink(temp_path)

    def test_multi_word_paragraph(self):
        """Test that paragraph treats each string as a separate paragraph."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (This) (is) (a) (multi-word) (paragraph.)
            >md.p
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            # Each string becomes a separate paragraph
            expected = "This\n\nis\n\na\n\nmulti-word\n\nparagraph.\n\n"
            self.assertEqual(content, expected)
        finally:
            os.unlink(temp_path)


class TestMarkdownStage4(unittest.TestCase):
    """Test cases for markdown extension - Stage 4: Simple Lists (No Nesting)."""

    def test_unordered_list(self):
        """Test rendering an unordered list."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (First item)
            (Second item)
            (Third item)
            >md.ul
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            expected = (
                "- First item\n"
                "- Second item\n"
                "- Third item\n\n"
            )
            self.assertEqual(content, expected)
        finally:
            os.unlink(temp_path)

    def test_ordered_list(self):
        """Test rendering an ordered list."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (First item)
            (Second item)
            (Third item)
            >md.ol
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            expected = (
                "1. First item\n"
                "2. Second item\n"
                "3. Third item\n\n"
            )
            self.assertEqual(content, expected)
        finally:
            os.unlink(temp_path)

    def test_mixed_content_with_lists(self):
        """Test rendering lists mixed with headings and paragraphs."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (My Document)
            >md.h1
            (Here is some introduction text.)
            >md.p
            (Item A)
            (Item B)
            (Item C)
            >md.ul
            (That was a list!)
            >md.p
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            expected = (
                "# My Document\n\n"
                "Here is some introduction text.\n\n"
                "- Item A\n"
                "- Item B\n"
                "- Item C\n\n"
                "That was a list!\n\n"
            )
            self.assertEqual(content, expected)
        finally:
            os.unlink(temp_path)


class TestMarkdownStage5(unittest.TestCase):
    """Test cases for markdown extension - Stage 5: Nesting Infrastructure."""

    def test_nest_ul_with_ol_nested(self):
        """Test UL outer list with OL nested inside."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (Outer 1)
            (Outer 2)
            >md.nest
              (Nested A)
              (Nested B)
              >md.ol
            (Outer 3)
            >md.ul
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            expected = (
                "- Outer 1\n"
                "- Outer 2\n"
                "  1. Nested A\n"
                "  2. Nested B\n"
                "- Outer 3\n\n"
            )
            self.assertEqual(content, expected)
        finally:
            os.unlink(temp_path)

    def test_nest_ol_with_ul_nested(self):
        """Test OL outer list with UL nested inside."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (First task)
            (Second task)
            >md.nest
              (Subtask A)
              (Subtask B)
              >md.ul
            (Third task)
            >md.ol
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            expected = (
                "1. First task\n"
                "2. Second task\n"
                "  - Subtask A\n"
                "  - Subtask B\n"
                "3. Third task\n\n"
            )
            self.assertEqual(content, expected)
        finally:
            os.unlink(temp_path)

    def test_triple_nesting_mixed_types(self):
        """Test 3 levels of nesting with mixed list types."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (Level 1 - Item 1)
            >md.nest
              (Level 2 - Item A)
              >md.nest
                (Level 3 - Item i)
                (Level 3 - Item ii)
                >md.ul
              (Level 2 - Item B)
              >md.ul
            (Level 1 - Item 2)
            >md.ol
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            expected = (
                "1. Level 1 - Item 1\n"
                "  - Level 2 - Item A\n"
                "    - Level 3 - Item i\n"
                "    - Level 3 - Item ii\n"
                "  - Level 2 - Item B\n"
                "2. Level 1 - Item 2\n\n"
            )
            self.assertEqual(content, expected)
        finally:
            os.unlink(temp_path)

    def test_multiple_nests_same_level(self):
        """Test multiple nested sections in same list."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (Item 1)
            >md.nest
              (Sub 1a)
              (Sub 1b)
              >md.ul
            (Item 2)
            >md.nest
              (Sub 2a)
              (Sub 2b)
              >md.ul
            (Item 3)
            >md.ul
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            expected = (
                "- Item 1\n"
                "  - Sub 1a\n"
                "  - Sub 1b\n"
                "- Item 2\n"
                "  - Sub 2a\n"
                "  - Sub 2b\n"
                "- Item 3\n\n"
            )
            self.assertEqual(content, expected)
        finally:
            os.unlink(temp_path)

    def test_nest_with_mixed_content(self):
        """Test nesting works with headings and paragraphs."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (Task List)
            >md.h2
            (Main tasks:)
            >md.p
            (Task 1)
            >md.nest
              (Subtask 1a)
              (Subtask 1b)
              >md.ul
            (Task 2)
            >md.ul
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            expected = (
                "## Task List\n\n"
                "Main tasks:\n\n"
                "- Task 1\n"
                "  - Subtask 1a\n"
                "  - Subtask 1b\n"
                "- Task 2\n\n"
            )
            self.assertEqual(content, expected)
        finally:
            os.unlink(temp_path)


class TestMarkdownStage6(unittest.TestCase):
    """Test cases for markdown extension - Stage 6: Inline Formatting."""

    def test_bold_text(self):
        """Test bold inline formatting."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (This is ) (bold text) >md.b (!) >md.t
            >md.p
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            self.assertEqual(content, "This is **bold text**!\n\n")
        finally:
            os.unlink(temp_path)

    def test_italic_text(self):
        """Test italic inline formatting."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (This is ) (italic text) >md.i (!) >md.t
            >md.p
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            self.assertEqual(content, "This is _italic text_!\n\n")
        finally:
            os.unlink(temp_path)

    def test_link(self):
        """Test link creation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (Check out ) (this link) (https://example.com) >md.l (!) >md.t
            >md.p
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            self.assertEqual(content, "Check out [this link](https://example.com)!\n\n")
        finally:
            os.unlink(temp_path)

    def test_bold_and_italic_composition(self):
        """Test composing bold and italic."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (This is ) (bold and italic) >md.b >md.i ( text!) >md.t
            >md.p
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            self.assertEqual(content, "This is _**bold and italic**_ text!\n\n")
        finally:
            os.unlink(temp_path)

    def test_link_with_italic(self):
        """Test link composed with italic."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (Here is an ) (italic link) (https://example.com) >md.l >md.i ( in text.) >md.t
            >md.p
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            self.assertEqual(content, "Here is an _[italic link](https://example.com)_ in text.\n\n")
        finally:
            os.unlink(temp_path)

    def test_mixed_inline_formatting(self):
        """Test multiple inline formats in one paragraph."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (This has ) (bold) >md.b ( and ) (italic) >md.i ( and a ) (link) (https://example.com) >md.l (!) >md.t
            >md.p
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            self.assertEqual(content, "This has **bold** and _italic_ and a [link](https://example.com)!\n\n")
        finally:
            os.unlink(temp_path)

    def test_inline_code(self):
        """Test inline code formatting."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (Use the ) (print) >md.c ( function in Python.) >md.t
            >md.p
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            self.assertEqual(content, "Use the `print` function in Python.\n\n")
        finally:
            os.unlink(temp_path)


class TestMarkdownStage7(unittest.TestCase):
    """Test cases for markdown extension - Stage 7: Tables."""

    def test_basic_table(self):
        """Test basic table without alignment."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (Name) (Age) (Status)
            >md.table.header
            (Alice) (30) (Active)
            >md.table.row
            (Bob) (25) (Pending)
            >md.table.row
            >md.table
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            expected = (
                "| Name  | Age | Status  |\n"
                "|-------|-----|---------|\n"
                "| Alice | 30  | Active  |\n"
                "| Bob   | 25  | Pending |\n\n"
            )
            self.assertEqual(content, expected)
        finally:
            os.unlink(temp_path)

    def test_table_with_alignment(self):
        """Test table with column alignment."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (Name) (Age) (Status)
            >md.table.header
            >md.table.left >md.table.centre >md.table.right
            >md.table.align
            (Alice) (30) (Active)
            >md.table.row
            (Bob) (25) (Pending)
            >md.table.row
            >md.table
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            expected = (
                "| Name  | Age | Status  |\n"
                "|:------|:---:|--------:|\n"
                "| Alice | 30  | Active  |\n"
                "| Bob   | 25  | Pending |\n\n"
            )
            self.assertEqual(content, expected)
        finally:
            os.unlink(temp_path)

    def test_table_with_inline_formatting(self):
        """Test table cells with inline formatting."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (Feature) (Status) (Link)
            >md.table.header
            (Bold text) >md.b (Complete) (docs) (https://example.com) >md.l
            >md.table.row
            >md.table
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            # Check that the table contains the expected content with inline formatting
            self.assertIn("**Bold text**", content)
            self.assertIn("Complete", content)
            self.assertIn("[docs](https://example.com)", content)
            self.assertIn("| Feature", content)
            self.assertIn("| Status", content)
            self.assertIn("| Link", content)
        finally:
            os.unlink(temp_path)

    def test_multiple_tables(self):
        """Test multiple tables in same document."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (Table 1)
            >md.h3
            (A) (B)
            >md.table.header
            (1) (2)
            >md.table.row
            >md.table

            (Table 2)
            >md.h3
            (X) (Y)
            >md.table.header
            (3) (4)
            >md.table.row
            >md.table
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            self.assertIn("### Table 1", content)
            self.assertIn("| A | B |", content)
            self.assertIn("| 1 | 2 |", content)
            self.assertIn("### Table 2", content)
            self.assertIn("| X | Y |", content)
            self.assertIn("| 3 | 4 |", content)
        finally:
            os.unlink(temp_path)

    def test_table_with_header_only(self):
        """Test table with just header, no rows."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (Column 1) (Column 2) (Column 3)
            >md.table.header
            >md.table
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            expected = (
                "| Column 1 | Column 2 | Column 3 |\n"
                "|----------|----------|----------|\n\n"
            )
            self.assertEqual(content, expected)
        finally:
            os.unlink(temp_path)


class TestMarkdownStage8(unittest.TestCase):
    """Test cases for markdown extension - Stage 8: Horizontal Rules."""

    def test_horizontal_rule(self):
        """Test horizontal rule creates --- separator."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (Section 1)
            >md.h2
            (Some content)
            >md.p
            >md.hr
            (Section 2)
            >md.h2
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            expected = (
                "## Section 1\n\n"
                "Some content\n\n"
                "---\n\n"
                "## Section 2\n\n"
            )
            self.assertEqual(content, expected)
        finally:
            os.unlink(temp_path)

    def test_multiple_horizontal_rules(self):
        """Test multiple horizontal rules in document."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (Part 1)
            >md.p
            >md.hr
            (Part 2)
            >md.p
            >md.hr
            (Part 3)
            >md.p
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            self.assertEqual(content.count("---\n\n"), 2)
            self.assertIn("Part 1\n\n---\n\nPart 2\n\n---\n\nPart 3", content)
        finally:
            os.unlink(temp_path)

    def test_table_separator_format(self):
        """Test that table separator rows have correct pipe format (no double pipes)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (Col1) (Col2) (Col3)
            >md.table.header
            (A) (B) (C)
            >md.table.row
            >md.table
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            lines = content.split('\n')
            separator_line = lines[1]  # Second line is separator

            # Separator should not have double pipes
            self.assertNotIn('||', separator_line,
                "Table separator row should not contain double pipes '||'")

            # Separator should start and end with single pipe
            self.assertTrue(separator_line.startswith('|'),
                "Table separator should start with '|'")
            self.assertTrue(separator_line.endswith('|'),
                "Table separator should end with '|'")

            # Count pipes - should be num_cols + 1 (one before each column, one at end)
            pipe_count = separator_line.count('|')
            self.assertEqual(pipe_count, 4,  # 3 columns + 1 = 4 pipes
                f"Expected 4 pipes in separator, got {pipe_count}")
        finally:
            os.unlink(temp_path)


class TestMarkdownStage9(unittest.TestCase):
    """Test cases for markdown extension - Stage 9: Blockquotes and Code Blocks."""

    def test_simple_blockquote(self):
        """Test simple blockquote."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (This is a quote.) >md.q
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            self.assertEqual(content, "> This is a quote.\n\n")
        finally:
            os.unlink(temp_path)

    def test_multi_line_blockquote(self):
        """Test blockquote with multiple lines."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (First line of quote)
            (Second line of quote)
            (Third line of quote)
            >md.q
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            expected = (
                "> First line of quote\n"
                "> Second line of quote\n"
                "> Third line of quote\n\n"
            )
            self.assertEqual(content, expected)
        finally:
            os.unlink(temp_path)

    def test_code_block_no_language(self):
        """Test code block without language specification."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (def hello)
            (  return 42)
            Nil >md.code
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            expected = (
                "```\n"
                "def hello\n"
                "  return 42\n"
                "```\n\n"
            )
            self.assertEqual(content, expected)
        finally:
            os.unlink(temp_path)

    def test_code_block_with_language(self):
        """Test code block with language specification."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (def greet name)
            (  puts "Hello")
            (ruby) >md.code
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            expected = (
                "```ruby\n"
                "def greet name\n"
                "  puts \"Hello\"\n"
                "```\n\n"
            )
            self.assertEqual(content, expected)
        finally:
            os.unlink(temp_path)

    def test_code_block_empty_string_language(self):
        """Test code block with empty string for language (same as Nil)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (line 1)
            (line 2)
            () >md.code
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            expected = (
                "```\n"
                "line 1\n"
                "line 2\n"
                "```\n\n"
            )
            self.assertEqual(content, expected)
        finally:
            os.unlink(temp_path)


class TestMarkdownStage10(unittest.TestCase):
    """Test cases for markdown extension - Stage 10: List Item Builders (oli/uli)."""

    def test_oli_simple_items(self):
        """Test building ordered list items with >md.oli."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (First) >md.oli
            (Second) >md.oli
            (Third) >md.oli
            >md.ol
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            expected = (
                "1. First\n"
                "2. Second\n"
                "3. Third\n\n"
            )
            self.assertEqual(content, expected)
        finally:
            os.unlink(temp_path)

    def test_uli_simple_items(self):
        """Test building unordered list items with >md.uli."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (Item A) >md.uli
            (Item B) >md.uli
            (Item C) >md.uli
            >md.ul
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            expected = (
                "- Item A\n"
                "- Item B\n"
                "- Item C\n\n"
            )
            self.assertEqual(content, expected)
        finally:
            os.unlink(temp_path)

    def test_oli_with_inline_formatting(self):
        """Test oli with bold and inline text composition."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (Term:) >md.b ( Definition text) >md.t >md.oli
            (Term2:) >md.b ( Another definition) >md.t >md.oli
            >md.ol
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            expected = (
                "1. **Term:** Definition text\n"
                "2. **Term2:** Another definition\n\n"
            )
            self.assertEqual(content, expected)
        finally:
            os.unlink(temp_path)

    def test_uli_with_inline_formatting(self):
        """Test uli with multiple inline formats."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (Feature:) >md.b ( See ) (docs) (https://example.com) >md.l >md.t >md.uli
            (Bug:) >md.b ( Status ) (pending) >md.i >md.t >md.uli
            >md.ul
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            expected = (
                "- **Feature:** See [docs](https://example.com)\n"
                "- **Bug:** Status _pending_\n\n"
            )
            self.assertEqual(content, expected)
        finally:
            os.unlink(temp_path)

    def test_oli_glossary_example(self):
        """Test the original glossary use case that motivated oli/uli."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (Glossary) >md.h2
            (GIL:) >md.b ( Global Interpreter Lock) >md.t >md.oli
            (P99 latency:) >md.b ( 99th percentile latency) >md.t >md.oli
            (Zero-copy:) >md.b ( Technique avoiding memory copies) >md.t >md.oli
            >md.ol
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            expected = (
                "## Glossary\n\n"
                "1. **GIL:** Global Interpreter Lock\n"
                "2. **P99 latency:** 99th percentile latency\n"
                "3. **Zero-copy:** Technique avoiding memory copies\n\n"
            )
            self.assertEqual(content, expected)
        finally:
            os.unlink(temp_path)

    def test_oli_newlines_are_whitespace(self):
        """
        Test that newlines are just whitespace in SOMA - they don't separate items.

        In this test, (Plain item) on a separate line is NOT a separate list item.
        It gets concatenated with the next >md.t call because newlines are whitespace.
        This demonstrates SOMA's fundamental parsing rule: newlines = whitespace.
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (First:) >md.b ( formatted) >md.t >md.oli
            (Plain item)
            (Last:) >md.b ( also formatted) >md.t >md.oli
            >md.ol
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            # Expected: Only 2 items because newlines are whitespace!
            # Item 1: "**First:** formatted"
            # Item 2: "Plain item**Last:** also formatted" (concatenated by >md.t)
            expected = (
                "1. **First:** formatted\n"
                "2. Plain item**Last:** also formatted\n\n"
            )
            self.assertEqual(content, expected)
        finally:
            os.unlink(temp_path)

    def test_oli_nested_homogeneous(self):
        """Test oli with nested oli (homogeneous nesting)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (Outer 1) >md.oli
            >md.nest
            (Inner 1a) >md.oli
            (Inner 1b) >md.oli
            >md.ol
            (Outer 2) >md.oli
            >md.ol
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            expected = (
                "1. Outer 1\n"
                "  1. Inner 1a\n"
                "  2. Inner 1b\n"
                "2. Outer 2\n\n"
            )
            self.assertEqual(content, expected)
        finally:
            os.unlink(temp_path)

    def test_uli_nested_homogeneous(self):
        """Test uli with nested uli (homogeneous nesting)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (Outer A) >md.uli
            >md.nest
            (Inner A1) >md.uli
            (Inner A2) >md.uli
            >md.ul
            (Outer B) >md.uli
            >md.ul
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            expected = (
                "- Outer A\n"
                "  - Inner A1\n"
                "  - Inner A2\n"
                "- Outer B\n\n"
            )
            self.assertEqual(content, expected)
        finally:
            os.unlink(temp_path)

    def test_oli_nested_heterogeneous(self):
        """Test oli with nested uli (heterogeneous nesting)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (Step 1) >md.oli
            >md.nest
            (Bullet A) >md.uli
            (Bullet B) >md.uli
            >md.ul
            (Step 2) >md.oli
            >md.ol
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            expected = (
                "1. Step 1\n"
                "  - Bullet A\n"
                "  - Bullet B\n"
                "2. Step 2\n\n"
            )
            self.assertEqual(content, expected)
        finally:
            os.unlink(temp_path)

    def test_uli_nested_heterogeneous(self):
        """Test uli with nested oli (heterogeneous nesting)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (Category A) >md.uli
            >md.nest
            (First) >md.oli
            (Second) >md.oli
            >md.ol
            (Category B) >md.uli
            >md.ul
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            expected = (
                "- Category A\n"
                "  1. First\n"
                "  2. Second\n"
                "- Category B\n\n"
            )
            self.assertEqual(content, expected)
        finally:
            os.unlink(temp_path)

    def test_placeholder_in_paragraph_fails(self):
        """Test that placeholders in >md.p throw clear error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (Item 1) >md.oli
            (Para 1) (Para 2) >md.p
            ({temp_path}) >md.render
            """
            with self.assertRaises(RuntimeError) as cm:
                run_soma_program(code)

            self.assertIn("OliPlaceholder", str(cm.exception))
            self.assertIn(">md.p", str(cm.exception))
            # New error message is type-specific
            self.assertIn("Did you forget to call >md.ol?", str(cm.exception))
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass

    def test_placeholder_in_blockquote_fails(self):
        """Test that placeholders in >md.q throw clear error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (Item 1) >md.uli
            (Quote line) >md.q
            ({temp_path}) >md.render
            """
            with self.assertRaises(RuntimeError) as cm:
                run_soma_program(code)

            self.assertIn("UliPlaceholder", str(cm.exception))
            self.assertIn(">md.q", str(cm.exception))
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass

    def test_placeholder_in_code_block_fails(self):
        """Test that placeholders in >md.code throw clear error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (Item 1) >md.oli
            (def foo) (python) >md.code
            ({temp_path}) >md.render
            """
            with self.assertRaises(RuntimeError) as cm:
                run_soma_program(code)

            self.assertIn("OliPlaceholder", str(cm.exception))
            self.assertIn(">md.code", str(cm.exception))
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass

    def test_placeholder_in_data_title_fails(self):
        """Test that placeholders in >md.dt throw clear error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            Void (Name) (Item 1) >md.uli (Alice) >md.dt
            ({temp_path}) >md.render
            """
            with self.assertRaises(RuntimeError) as cm:
                run_soma_program(code)

            self.assertIn("UliPlaceholder", str(cm.exception))
            self.assertIn(">md.dt", str(cm.exception))
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass

    def test_placeholder_in_definition_list_fails(self):
        """Test that placeholders in >md.dl throw clear error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            Void (Term) (Item 1) >md.oli (Definition) >md.dl >md.ul
            ({temp_path}) >md.render
            """
            with self.assertRaises(RuntimeError) as cm:
                run_soma_program(code)

            self.assertIn("OliPlaceholder", str(cm.exception))
            self.assertIn(">md.dl", str(cm.exception))
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass

    def test_placeholder_in_table_header_fails(self):
        """Test that placeholders in table operations throw clear error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (Item 1) >md.uli
            (Col1) (Col2) >md.table.header
            ({temp_path}) >md.render
            """
            with self.assertRaises(RuntimeError) as cm:
                run_soma_program(code)

            self.assertIn("UliPlaceholder", str(cm.exception))
            self.assertIn(">md.table.header/row/align", str(cm.exception))
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass

    def test_unterminated_oli_fails_on_render(self):
        """Test that oli without ol fails when trying to render."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (Item 1) >md.oli
            (Item 2) >md.oli
            ) Forgot >md.ol!
            ({temp_path}) >md.render
            """
            with self.assertRaises(RuntimeError) as cm:
                run_soma_program(code)

            # Should fail in validate_document when rendering
            self.assertIn("OliPlaceholder", str(cm.exception))
            self.assertIn(">md.render/print", str(cm.exception))
            self.assertIn("Did you forget to call >md.ol or >md.ul?", str(cm.exception))
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass

    def test_unterminated_uli_fails_on_print(self):
        """Test that uli without ul fails when trying to print."""
        try:
            code = """
            (python) >use
            (markdown) >use

            >md.start
            (Item 1) >md.uli
            (Item 2) >md.uli
            ) Forgot >md.ul!
            >md.print
            """
            with self.assertRaises(RuntimeError) as cm:
                run_soma_program(code)

            self.assertIn("UliPlaceholder", str(cm.exception))
            self.assertIn(">md.render/print", str(cm.exception))
        except Exception as e:
            # If exception isn't RuntimeError, test should fail
            self.assertIsInstance(e, RuntimeError)

    def test_wrong_list_type_oli_to_ul_fails(self):
        """Test that using >md.ul for oli items throws clear error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (Item 1) >md.oli
            (Item 2) >md.oli
            >md.ul
            ({temp_path}) >md.render
            """
            with self.assertRaises(RuntimeError) as cm:
                run_soma_program(code)

            self.assertIn("OliPlaceholder", str(cm.exception))
            self.assertIn(">md.ul encountered OliPlaceholder", str(cm.exception))
            self.assertIn("Did you mean to use >md.ol instead of >md.ul?", str(cm.exception))
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass

    def test_wrong_list_type_uli_to_ol_fails(self):
        """Test that using >md.ol for uli items throws clear error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (Item 1) >md.uli
            (Item 2) >md.uli
            >md.ol
            ({temp_path}) >md.render
            """
            with self.assertRaises(RuntimeError) as cm:
                run_soma_program(code)

            self.assertIn("UliPlaceholder", str(cm.exception))
            self.assertIn(">md.ol encountered UliPlaceholder", str(cm.exception))
            self.assertIn("Did you mean to use >md.ul instead of >md.ol?", str(cm.exception))
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass

    def test_oli_uli_interleaved_in_document(self):
        """Test oli and uli can be used in separate lists in same document."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (Steps) >md.h2
            (First) >md.oli
            (Second) >md.oli
            >md.ol

            (Features) >md.h2
            (Fast) >md.uli
            (Reliable) >md.uli
            >md.ul
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            expected = (
                "## Steps\n\n"
                "1. First\n"
                "2. Second\n\n"
                "## Features\n\n"
                "- Fast\n"
                "- Reliable\n\n"
            )
            self.assertEqual(content, expected)
        finally:
            os.unlink(temp_path)

    def test_oli_with_complex_inline_formatting(self):
        """Test oli with multiple formatters (bold, italic, code, links)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (Method:) >md.b ( ) (getValue) >md.c ( returns ) (number) >md.i >md.t >md.oli
            (See ) (docs) (https://example.com) >md.l ( for details) >md.t >md.oli
            >md.ol
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            expected = (
                "1. **Method:** `getValue` returns _number_\n"
                "2. See [docs](https://example.com) for details\n\n"
            )
            self.assertEqual(content, expected)
        finally:
            os.unlink(temp_path)

    def test_uli_empty_accumulator(self):
        """Test that ul works normally when no uli items accumulated."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (Item 1)
            (Item 2)
            >md.ul
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            expected = (
                "- Item 1\n"
                "- Item 2\n\n"
            )
            self.assertEqual(content, expected)
        finally:
            os.unlink(temp_path)

    def test_oli_multiple_lists(self):
        """Test oli accumulator clears between lists."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (List 1) >md.h3
            (A) >md.oli
            (B) >md.oli
            >md.ol

            (List 2) >md.h3
            (C) >md.oli
            (D) >md.oli
            >md.ol
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            # Each list should start at 1
            self.assertIn("### List 1\n\n1. A\n2. B\n\n", content)
            self.assertIn("### List 2\n\n1. C\n2. D\n\n", content)
        finally:
            os.unlink(temp_path)


class TestMarkdownEdgeCases(unittest.TestCase):
    """Test edge cases with md.dl, md.dt, and placeholder interactions."""

    def test_dl_with_placeholder_as_part_of_pair_fails(self):
        """Test that placeholder as part of a pair in md.dl fails with clear error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            Void (Label1) (Item 1) >md.uli (Value2) >md.dl
            ({temp_path}) >md.render
            """
            with self.assertRaises(RuntimeError) as cm:
                run_soma_program(code)

            # Should mention the placeholder
            self.assertIn("UliPlaceholder", str(cm.exception))
            # Should mention md.dl
            self.assertIn(">md.dl", str(cm.exception))
            # Should mention pairing hint
            self.assertIn("processes items in pairs", str(cm.exception))
            # Should suggest consuming placeholders first
            self.assertIn("BEFORE calling >md.dl", str(cm.exception))
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass

    def test_dt_with_placeholder_in_middle_fails(self):
        """Test that placeholder in middle of md.dt items fails with helpful error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            Void (Name) (Item 1) >md.oli (Age) (30) >md.dt
            ({temp_path}) >md.render
            """
            with self.assertRaises(RuntimeError) as cm:
                run_soma_program(code)

            # Should explain the pairing issue
            self.assertIn("OliPlaceholder", str(cm.exception))
            self.assertIn(">md.dt", str(cm.exception))
            self.assertIn("processes items in pairs", str(cm.exception))
            # Should include position information
            self.assertIn("at position", str(cm.exception))
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass

    def test_dl_output_works_with_placeholders_below(self):
        """Test that md.dl works when placeholders are below Void (not included in pairing)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (Item 1) >md.uli
            (Item 2) >md.uli
            Void (Term1) (Def1) (Term2) (Def2) >md.dl
            >md.ul
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            # md.dl only processes items ABOVE the Void
            # Placeholders are BELOW Void, so they don't get included in this list
            # Only the definition list items are rendered
            self.assertIn("- **Term1**: Def1\n", content)
            self.assertIn("- **Term2**: Def2\n", content)
            # The placeholders below Void are NOT consumed by this md.ul
            self.assertNotIn("Item 1", content)
            self.assertNotIn("Item 2", content)
        finally:
            os.unlink(temp_path)

    def test_dl_then_ul_with_separate_placeholders(self):
        """Test md.dl and md.ul - placeholders below Void are orphaned (not consumed)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (Item 1) >md.uli
            (Item 2) >md.uli
            Void (Label1) (Value1) >md.dl
            >md.ul
            ({temp_path}) >md.render
            """
            # This succeeds because md.ul clears the accumulator after consuming items above Void
            # The placeholders below Void are orphaned (no accumulator items) but we don't error
            # because we only check accumulator counts, not AL contents
            run_soma_program(code)

            content = Path(temp_path).read_text()
            # Only the definition list item is rendered
            self.assertIn("- **Label1**: Value1\n", content)
            # The orphaned placeholders don't appear in output
            self.assertNotIn("Item 1", content)
            self.assertNotIn("Item 2", content)
        finally:
            os.unlink(temp_path)

    def test_mixing_oli_uli_with_dl_fails_with_type_error(self):
        """Test that mixing oli and uli with md.dl fails when wrong list type is used."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            (Item A) >md.uli
            (Item B) >md.oli
            Void (Label) (Value) >md.dl
            >md.ul
            ({temp_path}) >md.render
            """
            with self.assertRaises(RuntimeError) as cm:
                run_soma_program(code)

            # Should complain about wrong placeholder type in UL
            self.assertIn("OliPlaceholder", str(cm.exception))
            self.assertIn(">md.ul", str(cm.exception))
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass

    def test_dt_odd_number_of_items_fails(self):
        """Test that md.dt with odd number of items fails with helpful error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            Void (Name) (Alice) (Age) >md.dt
            ({temp_path}) >md.render
            """
            with self.assertRaises(ValueError) as cm:
                run_soma_program(code)

            # Should mention even number requirement
            self.assertIn("even number", str(cm.exception))
            self.assertIn("got 3", str(cm.exception))
            # Should provide hint
            self.assertIn("Hint", str(cm.exception))
            self.assertIn("Each label needs a value", str(cm.exception))
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass

    def test_dl_odd_number_of_items_fails(self):
        """Test that md.dl with odd number of items fails with helpful error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            Void (Label1) (Value1) (Label2) >md.dl
            >md.ul
            ({temp_path}) >md.render
            """
            with self.assertRaises(ValueError) as cm:
                run_soma_program(code)

            # Should mention even number requirement
            self.assertIn("even number", str(cm.exception))
            self.assertIn("got 3", str(cm.exception))
            # Should provide hint
            self.assertIn("Hint", str(cm.exception))
            self.assertIn("Each label needs a definition", str(cm.exception))
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass

    def test_dul_convenience_works(self):
        """Test that md.dul (definition unordered list) convenience combinator works."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            Void (API) (Application Programming Interface) (CLI) (Command Line Interface) >md.dul
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            self.assertIn("- **API**: Application Programming Interface\n", content)
            self.assertIn("- **CLI**: Command Line Interface\n", content)
        finally:
            os.unlink(temp_path)

    def test_dol_convenience_works(self):
        """Test that md.dol (definition ordered list) convenience combinator works."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            Void (First) (The beginning) (Second) (The middle) (Third) (The end) >md.dol
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            self.assertIn("1. **First**: The beginning\n", content)
            self.assertIn("2. **Second**: The middle\n", content)
            self.assertIn("3. **Third**: The end\n", content)
        finally:
            os.unlink(temp_path)

    def test_dt_then_paragraph_works(self):
        """Test that md.dt output can be consumed by md.p."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            Void (Name) (Alice) (Age) (30) (City) (NYC) >md.dt
            >md.p
            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()
            self.assertEqual(content, "**Name** Alice **Age** 30 **City** NYC\n\n")
        finally:
            os.unlink(temp_path)


if __name__ == '__main__':
    unittest.main()
