"""
Unit tests for the initial SOMA lexer.

These tests are designed to lock in the behaviour we have discussed:
- INT vs PATH, including signed integers
- EXEC vs PATH(">")
- illegal numeric literals
- whitespace insensitivity around most boundaries
"""

import unittest

from soma.lexer import lex, TokenKind, LexError


def kinds(tokens):
    return [t.kind for t in tokens[:-1]]


def values(tokens):
    return [t.value for t in tokens[:-1]]


class TestNumbersAndExecute(unittest.TestCase):
    def test_23_exec_print(self):
        tokens = lex("23 >print")
        self.assertEqual(kinds(tokens), [TokenKind.INT, TokenKind.EXEC, TokenKind.PATH])
        self.assertEqual(values(tokens), ["23", ">", "print"])

    def test_23_many_spaces_exec_print(self):
        tokens = lex("23   \t   >print")
        self.assertEqual(kinds(tokens), [TokenKind.INT, TokenKind.EXEC, TokenKind.PATH])
        self.assertEqual(values(tokens), ["23", ">", "print"])

    def test_23_exec_space_print(self):
        tokens = lex("23 > print")
        self.assertEqual(kinds(tokens), [TokenKind.INT, TokenKind.PATH, TokenKind.PATH])
        self.assertEqual(values(tokens), ["23", ">", "print"])

    def test_leading_and_trailing_whitespace(self):
        tokens = lex("   23   >   print   ")
        self.assertEqual(kinds(tokens), [TokenKind.INT, TokenKind.PATH, TokenKind.PATH])
        self.assertEqual(values(tokens), ["23", ">", "print"])

    def test_plain_exec_vs_plain_path(self):
        tokens = lex(">print")
        self.assertEqual(kinds(tokens), [TokenKind.EXEC, TokenKind.PATH])
        self.assertEqual(values(tokens), [">", "print"])

        tokens = lex("> print")
        self.assertEqual(kinds(tokens), [TokenKind.PATH, TokenKind.PATH])
        self.assertEqual(values(tokens), [">", "print"])

    def test_unsigned_int(self):
        tokens = lex("23 >print")
        self.assertEqual(tokens[0].kind, TokenKind.INT)
        self.assertEqual(tokens[0].value, "23")

    def test_positive_int(self):
        tokens = lex("+23 >print")
        self.assertEqual(tokens[0].kind, TokenKind.INT)
        self.assertEqual(tokens[0].value, "+23")
        self.assertEqual(tokens[1].kind, TokenKind.EXEC)

    def test_negative_int(self):
        tokens = lex("-23 >print")
        self.assertEqual(tokens[0].kind, TokenKind.INT)
        self.assertEqual(tokens[0].value, "-23")
        self.assertEqual(tokens[1].kind, TokenKind.EXEC)

    def test_minus_as_word(self):
        tokens = lex("- 23 >print")
        self.assertEqual(
            kinds(tokens),
            [TokenKind.PATH, TokenKind.INT, TokenKind.EXEC, TokenKind.PATH],
        )
        self.assertEqual(values(tokens), ["-", "23", ">", "print"])

    def test_plus_as_word(self):
        tokens = lex("+ 23 >print")
        self.assertEqual(
            kinds(tokens),
            [TokenKind.PATH, TokenKind.INT, TokenKind.EXEC, TokenKind.PATH],
        )
        self.assertEqual(values(tokens), ["+", "23", ">", "print"])


class TestIllegalNumbers(unittest.TestCase):
    def test_23_greater_print_is_error(self):
        with self.assertRaises(LexError):
            lex("23>print")

    def test_23_minus_5_is_error(self):
        with self.assertRaises(LexError):
            lex("23-5 >print")

    def test_23_comma_is_error(self):
        with self.assertRaises(LexError):
            lex("23, >print")

    def test_23_comma_5_is_error(self):
        with self.assertRaises(LexError):
            lex("23,5 >print")

    def test_minus_23_comma_is_error(self):
        with self.assertRaises(LexError):
            lex("-23, >print")

    def test_plus_23_trailing_garbage_is_error(self):
        with self.assertRaises(LexError):
            lex("+23foo >print")


class TestPathsWithWeirdCharacters(unittest.TestCase):
    def test_path_with_comma(self):
        tokens = lex("a,b >print")
        self.assertEqual(
            kinds(tokens),
            [TokenKind.PATH, TokenKind.EXEC, TokenKind.PATH],
        )
        self.assertEqual(values(tokens), ["a,b", ">", "print"])

    def test_plus_is_path_when_not_followed_by_digit(self):
        tokens = lex("+ >print")
        self.assertEqual(
            kinds(tokens),
            [TokenKind.PATH, TokenKind.EXEC, TokenKind.PATH],
        )
        self.assertEqual(values(tokens), ["+", ">", "print"])

    def test_plus_a_is_path(self):
        tokens = lex("+a >print")
        self.assertEqual(
            kinds(tokens),
            [TokenKind.PATH, TokenKind.EXEC, TokenKind.PATH],
        )
        self.assertEqual(values(tokens), ["+a", ">", "print"])

    def test_plain_greater_as_path(self):
        tokens = lex("> ")
        self.assertEqual(kinds(tokens), [TokenKind.PATH])
        self.assertEqual(values(tokens), [">"])


if __name__ == "__main__":
    unittest.main()
