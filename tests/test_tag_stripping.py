#!/usr/bin/env python3
"""
Test for U+100000 tag stripping bug fix.

This test verifies that tags used internally for preventing double-escaping
are properly stripped from the final output in both >md.print and >md.render.
"""

import unittest
import sys
from pathlib import Path
import tempfile
import os

# Add soma to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from soma.vm import run_soma_program
from soma.extensions.markdown_emitter import ESCAPED_TAG


class TestTagStripping(unittest.TestCase):
    """Test that U+100000 tags are stripped from output."""

    def test_uli_with_bold_strips_tags_in_print(self):
        """Test that >md.uli with inline bold formatting strips tags in >md.print."""
        code = """
(python) >use
(markdown) >use
>md.start
md.htmlEmitter >md.emitter

(Label:) >md.b ( text ) (+value) >md.b >md.uli
>md.ul

>md.print
"""
        # Capture output by running and checking for tag character
        import io
        import sys

        old_stdout = sys.stdout
        sys.stdout = buffer = io.StringIO()

        try:
            run_soma_program(code)
            output = buffer.getvalue()
        finally:
            sys.stdout = old_stdout

        # Verify no tag characters in output
        self.assertNotIn(ESCAPED_TAG, output,
                        f"Output should not contain U+100000 tag character. Output: {repr(output)}")

        # Verify proper HTML formatting
        self.assertIn("<strong>Label:</strong>", output)
        self.assertIn("<strong>+value</strong>", output)
        self.assertIn("<ul>", output)
        self.assertIn("</ul>", output)

    def test_uli_with_bold_strips_tags_in_render(self):
        """Test that >md.uli with inline bold formatting strips tags in >md.render."""
        code = """
(python) >use
(markdown) >use
>md.start
md.htmlEmitter >md.emitter

(Label:) >md.b ( text ) (+value) >md.b >md.uli
>md.ul

(test_tag_output.html) >md.render
"""
        # Create temp file
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "test_tag_output.html"

            # Modify code to use temp file
            code = code.replace("test_tag_output.html", str(output_file))

            # Run program
            run_soma_program(code)

            # Read output file
            content = output_file.read_text()

            # Verify no tag characters in output
            self.assertNotIn(ESCAPED_TAG, content,
                            f"File should not contain U+100000 tag character. Content: {repr(content)}")

            # Verify proper HTML formatting
            self.assertIn("<strong>Label:</strong>", content)
            self.assertIn("<strong>+value</strong>", content)
            self.assertIn("<ul>", content)
            self.assertIn("</ul>", content)

    def test_complex_uli_composition_strips_tags(self):
        """Test complex >md.uli composition with multiple formatters."""
        code = """
(python) >use
(markdown) >use
>md.start
md.htmlEmitter >md.emitter

(Metric:) >md.b ( 100 req/s → 110 req/s = ) (+10%) >md.b ( improvement) >md.i >md.uli
>md.ul

>md.print
"""
        import io
        import sys

        old_stdout = sys.stdout
        sys.stdout = buffer = io.StringIO()

        try:
            run_soma_program(code)
            output = buffer.getvalue()
        finally:
            sys.stdout = old_stdout

        # Verify no tag characters
        self.assertNotIn(ESCAPED_TAG, output,
                        f"Complex composition should not leak tags. Output: {repr(output)}")

        # Verify all formatters applied correctly
        self.assertIn("<strong>Metric:</strong>", output)
        self.assertIn("<strong>+10%</strong>", output)
        self.assertIn("<i> improvement</i>", output)  # Note: space before 'improvement' from SOMA code

    def test_oli_with_code_strips_tags(self):
        """Test that >md.oli with inline code formatting strips tags."""
        code = """
(python) >use
(markdown) >use
>md.start
md.htmlEmitter >md.emitter

(Step 1: Run ) (npm install) >md.c ( to install) >md.oli
(Step 2: Run ) (npm test) >md.c ( to verify) >md.oli
>md.ol

>md.print
"""
        import io
        import sys

        old_stdout = sys.stdout
        sys.stdout = buffer = io.StringIO()

        try:
            run_soma_program(code)
            output = buffer.getvalue()
        finally:
            sys.stdout = old_stdout

        # Verify no tag characters
        self.assertNotIn(ESCAPED_TAG, output,
                        f"OLI with code should not leak tags. Output: {repr(output)}")

        # Verify code tags applied correctly
        self.assertIn("<code>npm install</code>", output)
        self.assertIn("<code>npm test</code>", output)
        self.assertIn("<ol>", output)


if __name__ == "__main__":
    unittest.main()
