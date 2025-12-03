#!/usr/bin/env python3
"""
Test that builtin operators raise errors when used incorrectly in text contexts.

Tests for the fix where `(text) - (more)` (incorrect) should raise a TypeError
instead of silently rendering as `text <builtin -> more`.

The correct syntax is `(text) (-) (more)` where (-) is a literal string.
"""

import unittest
import tempfile
import os
from pathlib import Path
import sys

# Add soma to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from soma.vm import run_soma_program


class TestBuiltinOperatorValidation(unittest.TestCase):
    """Test that builtin operators in text contexts raise helpful errors."""

    def test_minus_operator_raises_error(self):
        """Test that - operator (without parens) raises TypeError with helpful message."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use
            >md.start
            md.htmlEmitter >md.emitter

            (humans ) - ( lengthy explanations) >md.t
            >md.p

            ({temp_path}) >md.render
            """

            with self.assertRaises(TypeError) as cm:
                run_soma_program(code)

            error_msg = str(cm.exception)
            self.assertIn("Text concatenation (>md.t) requires string items", error_msg)
            self.assertIn("BuiltinBlock", error_msg)
            self.assertIn("(-)", error_msg)  # Hint about correct syntax
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_minus_operator_correct_syntax(self):
        """Test that (-) (with parens) works correctly."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use
            >md.start
            md.htmlEmitter >md.emitter

            (humans ) (-) ( lengthy explanations) >md.t
            >md.p

            ({temp_path}) >md.render
            """
            run_soma_program(code)
            content = Path(temp_path).read_text()

            # Should render as plain dash
            self.assertIn("humans - lengthy explanations", content)
        finally:
            os.unlink(temp_path)

    def test_plus_operator_raises_error(self):
        """Test that + operator raises TypeError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use
            >md.start
            md.htmlEmitter >md.emitter

            (one ) + ( two) >md.t
            >md.p

            ({temp_path}) >md.render
            """

            with self.assertRaises(TypeError) as cm:
                run_soma_program(code)

            error_msg = str(cm.exception)
            self.assertIn("Text concatenation", error_msg)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_comparison_operator_raises_error(self):
        """Test that < operator raises TypeError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            code = f"""
            (python) >use
            (markdown) >use
            >md.start
            md.htmlEmitter >md.emitter

            (a ) < ( b) >md.t
            >md.p

            ({temp_path}) >md.render
            """

            with self.assertRaises(TypeError) as cm:
                run_soma_program(code)

            error_msg = str(cm.exception)
            self.assertIn("Text concatenation", error_msg)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


if __name__ == '__main__':
    unittest.main()
