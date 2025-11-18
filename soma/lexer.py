"""
SOMA Lexer (initial cut)

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
  Rule: once we've committed to "this is a number", any non-digit
  immediately after the digit sequence that is not whitespace or EOF
  is a lexical error.

- Handle execute `>` vs plain `>` name:
    - >print       -> EXEC(">"), PATH("print")
    - > print      -> PATH(">"), PATH("print")
    - 23 >print    -> INT("23"), EXEC(">"), PATH("print")
    - 23 > print   -> INT("23"), PATH(">"), PATH("print")
    - a,b >print   -> PATH("a,b"), EXEC(">"), PATH("print")
    - 23>print     -> error (illegal numeric literal "23>...")

- Whitespace:
    - Space, tab, newline, and carriage return are treated as separators.
    - They terminate tokens but are not emitted as tokens.

- PATH tokens:
    - Any token that is not recognised as a number and does not start
      with the special EXEC form is a PATH.
    - PATHs may contain any printable, non-whitespace characters
      except the punctuation characters used as token delimiters.
    - In this initial version, the only punctuation delimiter is '>'.

Future extensions (not implemented yet):
- '!' store operator
- '{' and '}' for blocks
- comments, Void/Nil literals, etc.
"""

from enum import Enum


class TokenKind(Enum):
    INT = "INT"
    PATH = "PATH"
    EXEC = "EXEC"
    EOF = "EOF"


class Token(object):
    """
    A single lexical token.

    kind  - a TokenKind (INT, PATH, EXEC, EOF)
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
# In this initial version, only '>' is active; others will be added later.
_PUNCTUATION_KINDS = {
    # char: TokenKind or None (None = reserved for future)
    ">": TokenKind.EXEC,
}


def _is_whitespace(ch):
    return ch in _WHITESPACE_CHARS


def lex(source):
    """
    Lex a SOMA source string into a list of Tokens.

    On success: returns a list of Token instances, ending with an EOF token.
    On error: raises LexError with a descriptive message and position.

    Current rules (summary):

    - Whitespace separates tokens and is not emitted.
    - Numbers:
        * A token is a candidate number if:
            - it starts with a digit, OR
            - it starts with '+' or '-' AND the next char is a digit.
        * For a candidate number:
            - consume optional sign (+/-) if present,
            - consume digits,
            - if the next character is whitespace or EOF: emit INT,
            - otherwise: LexError (illegal numeric literal).
    - PATHs:
        * Any token that is not recognised as a number is a PATH.
        * PATHs may contain any printable, non-whitespace chars,
          except punctuation delimiters in _PUNCTUATION_KINDS.
    - EXEC vs PATH('>'):
        * At token start, if we see '>' and it is immediately followed
          by a non-whitespace character, we emit EXEC(">")
          (the execute sigil), and the following name will be lexed
          as a separate PATH token.
        * If '>' is followed by whitespace or EOF, it is treated as
          a PATH token with value ">".
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

        # --- Special handling for '>' (EXEC vs PATH) at token start ---
        if ch == ">":
            # Look ahead to decide if this is EXEC or PATH(">")
            if i + 1 < n and not _is_whitespace(source[i + 1]):
                # EXEC sigil: '>print' etc.
                emit(TokenKind.EXEC, ">", start_line, start_col)
                i += 1
                col += 1
                continue
            else:
                # Plain PATH name ">"
                emit(TokenKind.PATH, ">", start_line, start_col)
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
        # Not a candidate number, not EXEC. This token is a PATH.
        j = i
        while j < n:
            chj = source[j]
            # Token ends if we hit whitespace or punctuation that is a delimiter.
            if _is_whitespace(chj):
                break
            if chj in _PUNCTUATION_KINDS:
                # Punctuation marks a new token *after* this PATH,
                # so we stop before it.
                break
            j += 1

        value = source[i:j]
        emit(TokenKind.PATH, value, start_line, start_col)
        col += (j - i)
        i = j

    # Append EOF token
    emit(TokenKind.EOF, "", line, col)
    return tokens
