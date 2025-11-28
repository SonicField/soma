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


if __name__ == '__main__':
    unittest.main()
