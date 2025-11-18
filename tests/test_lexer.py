"""
Unit tests for the SOMA lexer.

These tests are designed to lock in behaviour as we go:

- INT vs PATH, including signed integers
- EXEC vs PATH(">")
- '!' as STORE modifier
- illegal numeric literals
- whitespace insensitivity around most boundaries
- basic behaviour when '!' or '>' appear inside names
"""

import unittest

from soma.lexer import lex, TokenKind, LexError


def kinds(tokens):
    """Helper: get TokenKind sequence excluding EOF."""
    return [t.kind for t in tokens[:-1]]


def values(tokens):
    """Helper: get token values excluding EOF."""
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
        # "-" alone becomes a PATH, then an INT, then EXEC, then PATH
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
        # "+" is a PATH, then EXEC, then PATH("print")
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


class TestStoreModifier(unittest.TestCase):
    """
    Tests for the '!' store modifier.

    Rules being tested:
    - '!' and '>' are the only prefix modifiers.
    - Attached form:
        !foo  -> STORE, PATH("foo")
        >foo  -> EXEC, PATH("foo")
    - Standalone form:
        ! foo -> PATH("!"), PATH("foo")
        > foo -> PATH(">"), PATH("foo")
    - Attached target must be a valid PATH:
        * not a numeric literal starting [0-9] or [+-][0-9]
        * must not start with '!' or '>', unless the target is exactly
          "!" or ">" (i.e. >! and !> are allowed, but >>foo, !!a, !>stdout
          etc. are illegal).
    """

    def test_store_attached_to_simple_path(self):
        tokens = lex("!stdout")
        self.assertEqual(kinds(tokens), [TokenKind.STORE, TokenKind.PATH])
        self.assertEqual(values(tokens), ["!", "stdout"])

    def test_store_standalone_then_path(self):
        tokens = lex("! stdout")
        # Standalone '!' behaves like a PATH when followed by whitespace
        self.assertEqual(kinds(tokens), [TokenKind.PATH, TokenKind.PATH])
        self.assertEqual(values(tokens), ["!", "stdout"])

    def test_store_attached_to_path_with_dash(self):
        tokens = lex("!a-23-")
        self.assertEqual(kinds(tokens), [TokenKind.STORE, TokenKind.PATH])
        self.assertEqual(values(tokens), ["!", "a-23-"])

    def test_store_attached_to_localish_name(self):
        tokens = lex("!__local")
        self.assertEqual(kinds(tokens), [TokenKind.STORE, TokenKind.PATH])
        self.assertEqual(values(tokens), ["!", "__local"])

    def test_store_then_store_word(self):
        tokens = lex("! !a")
        # First '!' is standalone PATH, then attached STORE("!"), PATH("a")
        self.assertEqual(
            kinds(tokens),
            [TokenKind.PATH, TokenKind.STORE, TokenKind.PATH],
        )
        self.assertEqual(values(tokens), ["!", "!", "a"])

    def test_store_cannot_attach_to_positive_int(self):
        # !+34 is illegal: attached modifier cannot target a numeric-like token
        with self.assertRaises(LexError):
            lex("!+34")

    def test_store_cannot_attach_to_negative_int(self):
        with self.assertRaises(LexError):
            lex("!-23")

    def test_store_standalone_before_negative_int_is_ok(self):
        tokens = lex("! -23")
        # Standalone PATH("!"), then INT("-23")
        self.assertEqual(kinds(tokens), [TokenKind.PATH, TokenKind.INT])
        self.assertEqual(values(tokens), ["!", "-23"])

    def test_store_cannot_attach_to_modifier_target_bang(self):
        # !!a is illegal: attached '!' target starts with '!'
        with self.assertRaises(LexError):
            lex("!!a")

    def test_store_cannot_attach_to_modifier_target_exec(self):
        # !>stdout is illegal: attached '!' target starts with '>'
        with self.assertRaises(LexError):
            lex("!>stdout")

    def test_store_cannot_attach_to_modifier_target_exec_plus(self):
        # !>+ is illegal: attached '!' target starts with '>'
        with self.assertRaises(LexError):
            lex("!>+")

    def test_store_attached_to_single_greater_is_allowed(self):
        # !> is allowed: store to the path ">"
        tokens = lex("!>")
        self.assertEqual(kinds(tokens), [TokenKind.STORE, TokenKind.PATH])
        self.assertEqual(values(tokens), ["!", ">"])


class TestExecModifierEdgeCases(unittest.TestCase):
    """
    Extra tests for '>' as a modifier, now that '!' is also a modifier.

    We reuse the same attached/standalone rules as for '!':
    - >foo  -> EXEC, PATH("foo")
    - > foo -> PATH(">"), PATH("foo")
    - target must not be numeric-like
    - target must not start with '!' or '>', unless target is exactly "!".
    """

    def test_exec_cannot_attach_to_positive_int(self):
        with self.assertRaises(LexError):
            lex(">+34")

    def test_exec_cannot_attach_to_negative_int(self):
        with self.assertRaises(LexError):
            lex(">-23")

    def test_exec_standalone_before_negative_int_is_ok(self):
        tokens = lex("> -23")
        self.assertEqual(kinds(tokens), [TokenKind.PATH, TokenKind.INT])
        self.assertEqual(values(tokens), [">", "-23"])

    def test_exec_cannot_attach_to_modifier_target_exec(self):
        # >>foo is illegal: attached '>' target starts with '>'
        with self.assertRaises(LexError):
            lex(">>foo")

    def test_exec_cannot_attach_to_modifier_target_store(self):
        # >!dog is illegal: attached '>' target starts with '!'
        with self.assertRaises(LexError):
            lex(">!dog")

    def test_exec_attached_to_single_bang_is_allowed(self):
        tokens = lex(">!")
        # Execute the path "!"
        self.assertEqual(kinds(tokens), [TokenKind.EXEC, TokenKind.PATH])
        self.assertEqual(values(tokens), [">", "!"])


class TestModifierInsideNames(unittest.TestCase):
    """
    Tests where '!' or '>' appear inside a larger sequence.

    For now we treat '!' and '>' as punctuation that always split tokens,
    not as ordinary path characters, so:
        a!b -> PATH("a"), STORE("!"), PATH("b")
        a>b -> PATH("a"), EXEC(">"), PATH("b")
    """

    def test_store_splits_path_when_inside_name(self):
        tokens = lex("a!b")
        self.assertEqual(
            kinds(tokens),
            [TokenKind.PATH, TokenKind.STORE, TokenKind.PATH],
        )
        self.assertEqual(values(tokens), ["a", "!", "b"])

    def test_exec_splits_path_when_inside_name(self):
        tokens = lex("a>b")
        self.assertEqual(
            kinds(tokens),
            [TokenKind.PATH, TokenKind.EXEC, TokenKind.PATH],
        )
        self.assertEqual(values(tokens), ["a", ">", "b"])


class TestBlocks(unittest.TestCase):
    """
    Tests for '{' and '}' as structural block delimiters.

    Design decisions encoded here:

    - '{' and '}' are ALWAYS structural; they are never part of PATH tokens.
    - Whitespace around braces is irrelevant for tokenisation:
        {>print}   and   { >print }   => same token sequence.
    - '>' may precede a block:
        >{>print}  => EXEC, LBRACE, EXEC, PATH("print"), RBRACE
    - '!' may NOT attach directly to a block:
        !{>print}  => LexError
        but:
        ! {>print} => PATH("!"), LBRACE, EXEC, PATH("print"), RBRACE
    """

    def test_simple_block(self):
        tokens = lex("{>print}")
        self.assertEqual(
            kinds(tokens),
            [
                TokenKind.LBRACE,
                TokenKind.EXEC,
                TokenKind.PATH,
                TokenKind.RBRACE,
            ],
        )
        self.assertEqual(values(tokens), ["{", ">", "print", "}"])

    def test_simple_block_with_whitespace(self):
        tokens = lex("{  >print  }")
        self.assertEqual(
            kinds(tokens),
            [
                TokenKind.LBRACE,
                TokenKind.EXEC,
                TokenKind.PATH,
                TokenKind.RBRACE,
            ],
        )
        self.assertEqual(values(tokens), ["{", ">", "print", "}"])

    def test_exec_of_block_no_space(self):
        tokens = lex(">{>print}")
        self.assertEqual(
            kinds(tokens),
            [
                TokenKind.EXEC,
                TokenKind.LBRACE,
                TokenKind.EXEC,
                TokenKind.PATH,
                TokenKind.RBRACE,
            ],
        )
        self.assertEqual(values(tokens), [">", "{", ">", "print", "}"])

    def test_exec_of_block_with_space(self):
        tokens = lex("> { >print }")
        self.assertEqual(
            kinds(tokens),
            [
                TokenKind.PATH,      # standalone '>' because of space
                TokenKind.LBRACE,
                TokenKind.EXEC,
                TokenKind.PATH,
                TokenKind.RBRACE,
            ],
        )
        self.assertEqual(values(tokens), [">", "{", ">", "print", "}"])

    def test_store_cannot_attach_to_block(self):
        # !{>print} is illegal: attached '!' cannot target a block
        with self.assertRaises(LexError):
            lex("!{>print}")

    def test_store_word_before_block_is_ok(self):
        # ! {>print} => PATH("!"), LBRACE, EXEC, PATH("print"), RBRACE
        tokens = lex("! {>print}")
        self.assertEqual(
            kinds(tokens),
            [
                TokenKind.PATH,
                TokenKind.LBRACE,
                TokenKind.EXEC,
                TokenKind.PATH,
                TokenKind.RBRACE,
            ],
        )
        self.assertEqual(values(tokens), ["!", "{", ">", "print", "}"])

    def test_nested_blocks(self):
        tokens = lex("{{>print}}")
        self.assertEqual(
            kinds(tokens),
            [
                TokenKind.LBRACE,
                TokenKind.LBRACE,
                TokenKind.EXEC,
                TokenKind.PATH,
                TokenKind.RBRACE,
                TokenKind.RBRACE,
            ],
        )
        self.assertEqual(values(tokens), ["{", "{", ">", "print", "}", "}"])


if __name__ == "__main__":
    unittest.main()
