"""
SOMA Lexer

This module currently knows how to:

- Distinguish INT vs PATH tokens, including signed integers:
    - 23    -> INT("23")
    - -23   -> INT("-23")
    - +23   -> INT("+23")
    - - 23  -> PATH("-"), INT("23")
    - + 23  -> PATH("+"), INT("23")

- Detect illegal numeric literals:
    - 23-5  -> error (digits followed by non-whitespace)
    - 23,   -> error
    - 23,5  -> error
    - 23>   -> error
  Rule (informal): if a token starts as a number (digit or +/-
  followed by digit), and then we hit a non-whitespace character that
  is not part of the number, it is an illegal numeric literal.

- Handle execute `>` vs plain `>` name:
    - >print       -> EXEC(">"), PATH("print")
    - > print      -> PATH(">"), PATH("print")
    - 23 >print    -> INT("23"), EXEC(">"), PATH("print")
    - 23 > print   -> INT("23"), PATH(">"), PATH("print")
    - a>b          -> PATH("a"), EXEC(">"), PATH("b")
    - 23>print     -> error (illegal numeric literal "23>...")

- Handle store `!` vs plain `!` name:
    - !stdout      -> STORE("!"), PATH("stdout")
    - ! stdout     -> PATH("!"), PATH("stdout")
    - a!b          -> PATH("a"), STORE("!"), PATH("b")
    - !+34         -> error (cannot store to numeric-like target)
    - !!a          -> error (cannot attach to target starting with '!')
    - !>stdout     -> error (cannot attach to target starting with '>')
    - !>           -> STORE("!"), PATH(">")

General modifier rules:

- '!' and '>' are the only prefix modifiers.
- At token start:

    * If followed by whitespace or EOF:
        - '!' -> PATH("!")
        - '>' -> PATH(">")

    * If followed by non-whitespace:
        - modifier form, which emits:
            - '!' -> STORE("!")
            - '>' -> EXEC(">")

        - The attached target must be a valid PATH start:
            - It must NOT be numeric-like:
                - not [0-9]
                - not [+-][0-9]
            - It must NOT start with '!' or '>', unless the target
              is exactly a single "!" or ">" at the end of the token
              (e.g. >! and !> are allowed, but >>foo, !!a, !>stdout
              etc. are illegal).

The lexer returns a list of Token objects, ending with an EOF token.
"""

from enum import Enum


class TokenKind(Enum):
    INT = "INT"
    PATH = "PATH"
    EXEC = "EXEC"
    STORE = "STORE"
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"
    STRING = "STRING"
    EOF = "EOF"


class Token(object):
    """
    A single lexical token.

    kind  - a TokenKind (INT, PATH, EXEC, STORE, EOF)
    value - the raw string for this token, as it appears in source
    line  - 1-based line number where the token starts
    col   - 1-based column number where the token starts
    """

    __slots__ = ("kind", "value", "line", "col")

    def __init__(self, kind, value, line, col):
        self.kind = kind
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self):
        return "Token(%s, %r, %d, %d)" % (
            self.kind.name,
            self.value,
            self.line,
            self.col,
        )


class LexError(Exception):
    """
    Raised when the lexer encounters an invalid token.

    Attributes:
        message - human-readable description
        line    - 1-based line number of the problem
        col     - 1-based column number of the problem
    """

    def __init__(self, message, line, col):
        super(LexError, self).__init__(
            "%s (line %d, col %d)" % (message, line, col)
        )
        self.message = message
        self.line = line
        self.col = col


_WHITESPACE_CHARS = (" ", "\t", "\n", "\r")

# Punctuation characters that, by default, form their own tokens.
# In this version, '>' and '!' are the active punctuation; others
# (like '{', '}', etc.) will be added later.
_PUNCTUATION_KINDS = {
    ">": TokenKind.EXEC,
    "!": TokenKind.STORE,
    "{": TokenKind.LBRACE,
    "}": TokenKind.RBRACE,
}


def _is_whitespace(ch):
    return ch in _WHITESPACE_CHARS


def lex(source):
    """
    Lex a SOMA source string into a list of Tokens.

    On success: returns a list of Token instances, ending with an EOF token.
    On error: raises LexError with a descriptive message and position.
    """
    tokens = []
    line = 1
    col = 1
    i = 0
    n = len(source)

    def emit(kind, value, start_line, start_col):
        tokens.append(Token(kind, value, start_line, start_col))

    while i < n:
        ch = source[i]

        # --- Skip whitespace ---
        if _is_whitespace(ch):
            if ch == "\n":
                line += 1
                col = 1
            else:
                col += 1
            i += 1
            continue

        start_line = line
        start_col = col

        # --- String literal: ( ... ) with \HEX\ escapes ---
        if ch == "(":
            value, i, line, col = _lex_string(source, i, line, col)
            emit(TokenKind.STRING, value, start_line, start_col)
            continue

        # --- Braces are always structural ---
        if ch == "{":
            emit(TokenKind.LBRACE, "{", start_line, start_col)
            i += 1
            col += 1
            continue

        if ch == "}":
            emit(TokenKind.RBRACE, "}", start_line, start_col)
            i += 1
            col += 1
            continue

        # --- Modifier or plain punctuation at token start ('>' or '!') ---
        if ch in (">", "!"):
            # Look ahead one character
            if (
                i + 1 >= n
                or _is_whitespace(source[i + 1])
                or source[i + 1] == "}"
            ):
                # Standalone form: treat as plain PATH("!") or PATH(">")
                emit(TokenKind.PATH, ch, start_line, start_col)
                i += 1
                col += 1
                continue

            # Attached modifier form: '!'foo or '>'foo
            next_ch = source[i + 1]
            second_ch = source[i + 2] if (i + 2) < n else None

            # Forbid attaching modifiers to strings
            if next_ch == "(":
                raise LexError(
                "Modifier '%s' cannot target a string literal" % ch,
                start_line,
                start_col,
            )

            # Special-case: '!{...}' is illegal: cannot store directly to a block.
            if ch == "!" and next_ch == "{":
                raise LexError(
                    "Modifier '!' cannot target a block",
                    start_line,
                    start_col,
                )

            # 1) Forbid numeric-like targets:
            #    If target starts with digit, or with +/- followed by digit,
            #    we consider that "numeric-like" and reject.
            if next_ch.isdigit() or (
                next_ch in "+-"
                and second_ch is not None
                and second_ch.isdigit()
            ):
                raise LexError(
                    "Modifier '%s' cannot target numeric-like token" % ch,
                    start_line,
                    start_col,
                )

            # 2) Forbid modifier-prefixed targets, except for the
            #    single-character '!' or '>' case (e.g. >! or !>).
            if next_ch in ("!", ">"):
                # Allowed only if this is the last char in the token,
                # i.e. immediately followed by EOF, whitespace,
                # or structural punctuation like '}' or '{'.
                if (
                    (i + 2) < n
                    and not _is_whitespace(source[i + 2])
                    and source[i + 2] not in ("{", "}")
                ):
                    raise LexError(
                        "Modifier '%s' cannot target '%s'..." % (ch, next_ch),
                        start_line,
                        start_col,
                    )

            # If we reach here, we accept this as a modifier token.
            # We only emit the modifier now; the target will be lexed
            # as a separate PATH (or other token) in the next iteration.
            if ch == ">":
                emit(TokenKind.EXEC, ">", start_line, start_col)
            else:
                emit(TokenKind.STORE, "!", start_line, start_col)

            i += 1
            col += 1
            continue

        # --- Candidate number? ---
        # Rule: candidate if starts with digit,
        # or starts with + / - and next char is digit.
        if ch.isdigit() or (
            ch in "+-"
            and (i + 1) < n
            and source[i + 1].isdigit()
        ):
            # Try to lex a signed or unsigned integer.
            j = i

            # Optional sign
            if source[j] in "+-":
                j += 1

            # At least one digit must follow (guaranteed by the condition above)
            while j < n and source[j].isdigit():
                j += 1

            # Now j points just after the last digit.
            if j == n:
                # End of input: valid integer.
                value = source[i:j]
                emit(TokenKind.INT, value, start_line, start_col)
                col += (j - i)
                i = j
                continue

            next_ch = source[j]

            if _is_whitespace(next_ch):
                # Whitespace terminates the integer token: valid INT.
                value = source[i:j]
                emit(TokenKind.INT, value, start_line, start_col)
                col += (j - i)
                i = j
                continue

            # If we reach here, the character immediately after the digits
            # is not whitespace and not EOF. That is illegal for a numeric literal.
            raise LexError(
                "Illegal numeric literal starting at %r" % source[i : j + 1],
                start_line,
                start_col,
            )

        # --- PATH token ---
        # Not a candidate number, not EXEC/STORE punctuation at start.
        # This token is a PATH, which ends at whitespace or structural punctuation
        # like '{' or '}' (strings '(' will also be added later).
        j = i
        while j < n:
            chj = source[j]
            # Token ends if we hit whitespace
            if _is_whitespace(chj):
                break
            # Or a structural delimiter (braces)
            if chj in ("{", "}"):
                break
            j += 1

        value = source[i:j]
        emit(TokenKind.PATH, value, start_line, start_col)
        col += (j - i)
        i = j

    # Append EOF token
    emit(TokenKind.EOF, "", line, col)
    return tokens


def _lex_string(source, i, line, col):
    """
    Lex a SOMA string literal starting at position i where source[i] == '('.

    Returns:
        (value, new_i, new_line, new_col)

    value   - the decoded string content
    new_i   - index just after the closing ')'
    new_line, new_col - updated line/col at that position

    Raises:
        LexError on unterminated string or invalid \HEX\ escape.
    """
    start_line = line
    start_col = col
    n = len(source)

    # Skip the opening '('
    i += 1
    col += 1

    chars = []

    while i < n:
        ch = source[i]

        if ch == ")":
            # End of string
            i += 1
            col += 1
            return "".join(chars), i, line, col

        if ch == "\\":
            # Start of a \HEX\ escape
            esc_start_line = line
            esc_start_col = col

            i += 1
            col += 1
            if i >= n:
                raise LexError(
                    "Unterminated unicode escape in string",
                    esc_start_line,
                    esc_start_col,
                )

            esc_start = i

            # Scan until the closing backslash
            while i < n and source[i] != "\\":
                ch2 = source[i]
                if ch2 == "\n":
                    line += 1
                    col = 1
                else:
                    col += 1
                i += 1

            if i >= n:
                raise LexError(
                    "Unterminated unicode escape in string",
                    esc_start_line,
                    esc_start_col,
                )

            esc_text = source[esc_start:i]
            if not esc_text:
                raise LexError(
                    "Empty unicode escape in string",
                    esc_start_line,
                    esc_start_col,
                )

            if not all(c in "0123456789abcdefABCDEF" for c in esc_text):
                raise LexError(
                    "Non-hex digit in unicode escape in string",
                    esc_start_line,
                    esc_start_col,
                )

            try:
                codepoint = int(esc_text, 16)
                chars.append(chr(codepoint))
            except ValueError:
                raise LexError(
                    "Invalid unicode codepoint in string",
                    esc_start_line,
                    esc_start_col,
                )

            # Consume the closing backslash
            i += 1
            col += 1
            continue

        # Ordinary character inside string
        chars.append(ch)
        if ch == "\n":
            line += 1
            col = 1
        else:
            col += 1
        i += 1

    # We hit EOF without closing ')'
    raise LexError(
        "Unterminated string literal",
        start_line,
        start_col,
    )

