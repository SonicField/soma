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
        """Test that paragraph drains all items until Void."""
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
            self.assertEqual(content, "This is a multi-word paragraph.\n\n")
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


if __name__ == '__main__':
    unittest.main()
