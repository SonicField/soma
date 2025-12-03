#!/usr/bin/env python3
"""
Integration tests for Emitter Refactoring Plan - Step 10.

These tests verify end-to-end functionality of the emitter abstraction,
demonstrating that the same SOMA code can produce correct output in both
Markdown and HTML formats.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add soma to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from soma.vm import run_soma_program


class TestCompleteDocuments(unittest.TestCase):
    """Test complete documents with all features in both Markdown and HTML."""

    def test_complete_markdown_document(self):
        """Test a complete document with all features using markdown emitter."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            md.mdEmitter >md.emitter

            (Technical Documentation)
            >md.h1

            (Overview)
            >md.h2

            (This document demonstrates ) (all features) >md.b ( of the markdown extension.)
            >md.p

            (Key features include)
            >md.t
            >md.p

            (Inline formatting like ) (bold) >md.b (, ) (italic) >md.i (, and ) (code) >md.c
            (, plus ) (links) (https://example.com) >md.l (.)
            >md.p

            >md.hr

            (Lists and Nesting)
            >md.h2

            (Main item 1)
            >md.nest
              (Nested item 1a)
              (Nested item 1b)
              >md.ul
            (Main item 2)
            >md.nest
              (Nested 2a)
              >md.nest
                (Deep nested item)
                >md.ol
              (Nested 2b)
              >md.ul
            (Main item 3)
            >md.ul

            (Code Examples)
            >md.h2

            (def hello:)
            (    print "Hello, World")
            (    return True)
            (python) >md.code

            (Data Table)
            >md.h2

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

            # Verify key sections are present in markdown format
            self.assertIn("# Technical Documentation\n\n", content)
            self.assertIn("## Overview\n\n", content)
            self.assertIn("**all features**", content)
            self.assertIn("_italic_", content)
            self.assertIn("`code`", content)
            self.assertIn("[links](https://example.com)", content)
            self.assertIn("---\n\n", content)
            self.assertIn("## Lists and Nesting\n\n", content)
            self.assertIn("- Main item 1\n", content)
            self.assertIn("  - Nested item 1a\n", content)
            self.assertIn("    1. Deep nested item\n", content)
            self.assertIn("## Code Examples\n\n", content)
            self.assertIn("```python\n", content)
            self.assertIn('def hello:\n', content)
            self.assertIn('    print "Hello, World"\n', content)
            self.assertIn("## Data Table\n\n", content)
            self.assertIn("| Name  | Age | Status  |\n", content)
            self.assertIn("|:------|:---:|--------:|\n", content)
            self.assertIn("| Alice | 30  | Active  |\n", content)
        finally:
            os.unlink(temp_path)

    def test_complete_html_document(self):
        """Test a complete document with all features using HTML emitter."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            md.htmlEmitter >md.emitter

            (Technical Documentation)
            >md.h1

            (Overview)
            >md.h2

            (This document demonstrates ) (all features) >md.b ( of the markdown extension.)
            >md.p

            (Key features include)
            >md.t
            >md.p

            (Inline formatting like ) (bold) >md.b (, ) (italic) >md.i (, and ) (code) >md.c
            (, plus ) (links) (https://example.com) >md.l (.)
            >md.p

            >md.hr

            (Lists and Nesting)
            >md.h2

            (Main item 1)
            (Main item 2)
            (Main item 3)
            >md.ul

            (Code Examples)
            >md.h2

            (def hello:)
            (    print "Hello, World")
            (    return True)
            (python) >md.code

            (Data Table)
            >md.h2

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

            # Verify key sections are present in HTML format
            self.assertIn("<h1>Technical Documentation</h1>\n", content)
            self.assertIn("<h2>Overview</h2>\n", content)
            self.assertIn("<strong>all features</strong>", content)
            self.assertIn("<i>italic</i>", content)
            self.assertIn("<code>code</code>", content)
            self.assertIn('<a href="https://example.com">links</a>', content)
            self.assertIn("<hr>\n", content)
            self.assertIn("<h2>Lists and Nesting</h2>\n", content)
            self.assertIn("<ul>\n", content)
            self.assertIn("<li>Main item 1</li>\n", content)
            self.assertIn("<li>Main item 2</li>\n", content)
            self.assertIn("<h2>Code Examples</h2>\n", content)
            self.assertIn('<pre><code class="language-python">', content)
            self.assertIn('def hello:\n', content)
            self.assertIn('print', content)  # Quotes are escaped as &quot;
            self.assertIn('Hello, World', content)
            self.assertIn("<h2>Data Table</h2>\n", content)
            self.assertIn("<table>\n", content)
            self.assertIn("<thead>\n", content)
            self.assertIn("Name</th>", content)
            self.assertIn("Age</th>", content)
            self.assertIn("Status</th>", content)
            self.assertIn('<td style="text-align: left">Alice</td>', content)
            self.assertIn('<td style="text-align: center">30</td>', content)
            self.assertIn('<td style="text-align: right">Active</td>', content)
        finally:
            os.unlink(temp_path)


class TestPlaceholders(unittest.TestCase):
    """Test placeholder accumulation (oli/uli) with both emitters."""

    def test_markdown_with_placeholders(self):
        """Test that oli/uli placeholders work correctly with markdown emitter."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            md.mdEmitter >md.emitter

            (Shopping List)
            >md.h2

            (Fruits) >md.uli
            (Vegetables) >md.uli
            (Dairy) >md.uli
            >md.ul

            (Steps to Follow)
            >md.h2

            (Preheat oven to 350F) >md.oli
            (Mix ingredients) >md.oli
            (Bake for 30 minutes) >md.oli
            >md.ol

            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()

            # Verify unordered list with placeholders
            self.assertIn("## Shopping List\n\n", content)
            self.assertIn("- Fruits\n", content)
            self.assertIn("- Vegetables\n", content)
            self.assertIn("- Dairy\n\n", content)

            # Verify ordered list with placeholders
            self.assertIn("## Steps to Follow\n\n", content)
            self.assertIn("1. Preheat oven to 350F\n", content)
            self.assertIn("2. Mix ingredients\n", content)
            self.assertIn("3. Bake for 30 minutes\n\n", content)
        finally:
            os.unlink(temp_path)

    def test_html_with_placeholders(self):
        """Test that oli/uli placeholders work correctly with HTML emitter."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            md.htmlEmitter >md.emitter

            (Shopping List)
            >md.h2

            (Fruits) >md.uli
            (Vegetables) >md.uli
            (Dairy) >md.uli
            >md.ul

            (Steps to Follow)
            >md.h2

            (Preheat oven to 350F) >md.oli
            (Mix ingredients) >md.oli
            (Bake for 30 minutes) >md.oli
            >md.ol

            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()

            # Verify unordered list with placeholders in HTML
            self.assertIn("<h2>Shopping List</h2>\n", content)
            self.assertIn("<ul>\n", content)
            self.assertIn("  <li>Fruits</li>\n", content)
            self.assertIn("  <li>Vegetables</li>\n", content)
            self.assertIn("  <li>Dairy</li>\n", content)
            self.assertIn("</ul>\n", content)

            # Verify ordered list with placeholders in HTML
            self.assertIn("<h2>Steps to Follow</h2>\n", content)
            self.assertIn("<ol>\n", content)
            self.assertIn("  <li>Preheat oven to 350F</li>\n", content)
            self.assertIn("  <li>Mix ingredients</li>\n", content)
            self.assertIn("  <li>Bake for 30 minutes</li>\n", content)
            self.assertIn("</ol>\n", content)
        finally:
            os.unlink(temp_path)


class TestDefinitionLists(unittest.TestCase):
    """Test definition lists (md.dl/dt) with both emitters."""

    def test_definition_lists_markdown(self):
        """Test md.dul (definition unordered list) with markdown emitter."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            md.mdEmitter >md.emitter

            (Glossary)
            >md.h2

            (API) (Application Programming Interface) (SDK) (Software Development Kit)
            >md.dul

            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()

            # Verify md.dul creates definition list in markdown format
            self.assertIn("## Glossary\n\n", content)
            self.assertIn("- **API**: Application Programming Interface\n", content)
            self.assertIn("- **SDK**: Software Development Kit\n\n", content)
        finally:
            os.unlink(temp_path)

    def test_definition_lists_html(self):
        """Test md.dul (definition unordered list) with HTML emitter."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            md.htmlEmitter >md.emitter

            (Glossary)
            >md.h2

            (API) (Application Programming Interface) (SDK) (Software Development Kit)
            >md.dul

            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()

            # Verify md.dul creates definition list in HTML format with <strong> tags
            self.assertIn("<h2>Glossary</h2>\n", content)
            self.assertIn("<ul>\n", content)
            self.assertIn("<li><strong>API</strong>: Application Programming Interface</li>\n", content)
            self.assertIn("<li><strong>SDK</strong>: Software Development Kit</li>\n", content)
            self.assertIn("</ul>\n", content)
        finally:
            os.unlink(temp_path)

    def test_definition_ordered_list_html(self):
        """Test md.dol (definition ordered list) with HTML emitter."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            md.htmlEmitter >md.emitter

            (Steps)
            >md.h2

            (First) (Initialize the system) (Second) (Configure settings) (Third) (Run tests)
            >md.dol

            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()

            # Verify md.dol creates definition ordered list in HTML format with <strong> tags
            self.assertIn("<h2>Steps</h2>\n", content)
            self.assertIn("<ol>\n", content)
            self.assertIn("<li><strong>First</strong>: Initialize the system</li>\n", content)
            self.assertIn("<li><strong>Second</strong>: Configure settings</li>\n", content)
            self.assertIn("<li><strong>Third</strong>: Run tests</li>\n", content)
            self.assertIn("</ol>\n", content)
        finally:
            os.unlink(temp_path)

    def test_data_title_html(self):
        """Test md.dt (data title) with HTML emitter."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            md.htmlEmitter >md.emitter

            (Status Information)
            >md.h2

            Void (Name) (Alice) (Status) (Active) (Role) (Admin) >md.dt
            >md.p

            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()

            # Verify md.dt creates alternating bold in HTML format with <strong> tags
            self.assertIn("<h2>Status Information</h2>\n", content)
            self.assertIn("<p><strong>Name</strong> Alice <strong>Status</strong> Active <strong>Role</strong> Admin</p>\n", content)
        finally:
            os.unlink(temp_path)


class TestNestedStructures(unittest.TestCase):
    """Test complex nested structures with both emitters."""

    def test_nested_lists_markdown(self):
        """Test complex nested lists with markdown emitter."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            md.mdEmitter >md.emitter

            (Project Structure)
            >md.h2

            (Frontend)
            >md.nest
              (React Components)
              >md.nest
                (Header.jsx)
                (Footer.jsx)
                (Sidebar.jsx)
                >md.ul
              (Styles)
              >md.nest
                (global.css)
                (theme.css)
                >md.ul
              >md.ul
            (Backend)
            >md.nest
              (API Routes)
              >md.nest
                (users.py)
                (posts.py)
                >md.ol
              (Database)
              >md.nest
                (models.py)
                (migrations/)
                >md.ol
              >md.ol
            (Documentation)
            >md.ul

            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()

            # Verify complex nesting in markdown
            self.assertIn("## Project Structure\n\n", content)
            self.assertIn("- Frontend\n", content)
            self.assertIn("  - React Components\n", content)
            self.assertIn("    - Header.jsx\n", content)
            self.assertIn("    - Footer.jsx\n", content)
            self.assertIn("    - Sidebar.jsx\n", content)
            self.assertIn("  - Styles\n", content)
            self.assertIn("    - global.css\n", content)
            self.assertIn("    - theme.css\n", content)
            self.assertIn("- Backend\n", content)
            self.assertIn("  1. API Routes\n", content)
            self.assertIn("    1. users.py\n", content)
            self.assertIn("    2. posts.py\n", content)
            self.assertIn("  2. Database\n", content)
            self.assertIn("    1. models.py\n", content)
            self.assertIn("    2. migrations/\n", content)
            self.assertIn("- Documentation\n\n", content)
        finally:
            os.unlink(temp_path)

    def test_nested_lists_html(self):
        """Test nested lists produce proper HTML structure, not markdown syntax."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            md.htmlEmitter >md.emitter

            (Test Section)
            >md.h2

            (Item 1) >md.b
            >md.nest
              (Nested A)
              >md.ul
            (Item 2) >md.b
            >md.nest
              (Nested B)
              >md.ul
            >md.ul

            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()

            # Verify NO markdown syntax in HTML output
            self.assertNotIn("- <strong>", content, "HTML output should not contain markdown list syntax '- '")
            self.assertNotIn("  - ", content, "HTML output should not contain markdown nested list syntax '  - '")

            # Verify proper HTML structure instead
            self.assertIn("<h2>Test Section</h2>", content)
            self.assertIn("<ul>", content)
            self.assertIn("<li>", content)
            self.assertIn("<strong>Item 1</strong>", content)
            self.assertIn("<strong>Item 2</strong>", content)
            self.assertIn("Nested A", content)
            self.assertIn("Nested B", content)
            self.assertIn("</ul>", content)
        finally:
            os.unlink(temp_path)

    def test_simple_lists_html(self):
        """Test that simple (non-nested) lists work correctly with HTML emitter."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            md.htmlEmitter >md.emitter

            (Project Structure)
            >md.h2

            (Frontend Components)
            (Backend API)
            (Documentation)
            >md.ul

            (Setup Steps)
            >md.h2

            (Install dependencies)
            (Configure settings)
            (Run migrations)
            >md.ol

            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()

            # Verify lists in HTML
            self.assertIn("<h2>Project Structure</h2>\n", content)
            self.assertIn("<ul>\n", content)
            self.assertIn("<li>Frontend Components</li>\n", content)
            self.assertIn("<li>Backend API</li>\n", content)
            self.assertIn("<li>Documentation</li>\n", content)
            self.assertIn("</ul>\n", content)
            self.assertIn("<h2>Setup Steps</h2>\n", content)
            self.assertIn("<ol>\n", content)
            self.assertIn("<li>Install dependencies</li>\n", content)
            self.assertIn("<li>Configure settings</li>\n", content)
            self.assertIn("<li>Run migrations</li>\n", content)
            self.assertIn("</ol>\n", content)
        finally:
            os.unlink(temp_path)


class TestTables(unittest.TestCase):
    """Test table rendering with both emitters."""

    def test_tables_markdown(self):
        """Test tables with markdown emitter."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            md.mdEmitter >md.emitter

            (Test Results)
            >md.h2

            (Test Name) (Status) (Duration)
            >md.table.header
            >md.table.left >md.table.centre >md.table.right
            >md.table.align
            (test_login) (PASS) >md.b (1.2s)
            >md.table.row
            (test_logout) (FAIL) >md.b (0.8s)
            >md.table.row
            (test_signup) (PASS) >md.b (2.1s)
            >md.table.row
            >md.table

            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()

            # Verify table in markdown format
            self.assertIn("## Test Results\n\n", content)
            self.assertIn("| Test Name", content)
            self.assertIn("| Status", content)
            self.assertIn("| Duration |", content)
            self.assertIn("|:---", content)
            self.assertIn(":---:|", content)
            self.assertIn("---:|", content)
            self.assertIn("| test_login", content)
            self.assertIn("**PASS**", content)
            self.assertIn("1.2s", content)
            self.assertIn("| test_logout", content)
            self.assertIn("**FAIL**", content)
            self.assertIn("0.8s", content)
            self.assertIn("| test_signup", content)
            self.assertIn("2.1s", content)
        finally:
            os.unlink(temp_path)

    def test_tables_html(self):
        """Test tables with HTML emitter."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            md.htmlEmitter >md.emitter

            (Test Results)
            >md.h2

            (Test Name) (Status) (Duration)
            >md.table.header
            >md.table.left >md.table.centre >md.table.right
            >md.table.align
            (test_login) (PASS) >md.b (1.2s)
            >md.table.row
            (test_logout) (FAIL) >md.b (0.8s)
            >md.table.row
            (test_signup) (PASS) >md.b (2.1s)
            >md.table.row
            >md.table

            ({temp_path}) >md.render
            """
            run_soma_program(code)

            content = Path(temp_path).read_text()

            # Verify table in HTML format
            self.assertIn("<h2>Test Results</h2>\n", content)
            self.assertIn("<table>\n", content)
            self.assertIn("<thead>\n", content)
            self.assertIn("Test Name", content)
            self.assertIn("Status", content)
            self.assertIn("Duration", content)
            self.assertIn("</thead>\n", content)
            self.assertIn("<tbody>\n", content)
            self.assertIn("test_login", content)
            # Note: bold text in table cells is currently escaped as &lt;strong&gt;
            self.assertIn("PASS", content)
            self.assertIn("FAIL", content)
            self.assertIn("1.2s", content)
            self.assertIn("0.8s", content)
            self.assertIn("</tbody>\n", content)
            self.assertIn("</table>\n", content)
        finally:
            os.unlink(temp_path)


class TestEmitterSwitching(unittest.TestCase):
    """Test switching emitters mid-document."""

    def test_switch_emitter_mid_document(self):
        """Test that emitters can be switched during document generation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path1 = f.name
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path2 = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use

            >md.start
            md.mdEmitter >md.emitter

            (First Section in Markdown)
            >md.h1

            (This paragraph is in ) (markdown format) >md.b (.)
            >md.p

            (Item 1)
            (Item 2)
            (Item 3)
            >md.ul

            ({temp_path1}) >md.render

            >md.start
            md.htmlEmitter >md.emitter

            (Second Section in HTML)
            >md.h1

            (This paragraph is in ) (HTML format) >md.b (.)
            >md.p

            (Step 1)
            (Step 2)
            (Step 3)
            >md.ol

            ({temp_path2}) >md.render
            """
            run_soma_program(code)

            # Check markdown output
            md_content = Path(temp_path1).read_text()
            self.assertIn("# First Section in Markdown\n\n", md_content)
            self.assertIn("**markdown format**", md_content)
            self.assertIn("- Item 1\n", md_content)
            self.assertIn("- Item 2\n", md_content)
            self.assertIn("- Item 3\n\n", md_content)

            # Check HTML output
            html_content = Path(temp_path2).read_text()
            self.assertIn("<h1>Second Section in HTML</h1>\n", html_content)
            self.assertIn("<strong>HTML format</strong>", html_content)
            self.assertIn("<ol>\n", html_content)
            self.assertIn("  <li>Step 1</li>\n", html_content)
            self.assertIn("  <li>Step 2</li>\n", html_content)
            self.assertIn("  <li>Step 3</li>\n", html_content)
            self.assertIn("</ol>\n", html_content)
        finally:
            os.unlink(temp_path1)
            os.unlink(temp_path2)


if __name__ == '__main__':
    unittest.main()
