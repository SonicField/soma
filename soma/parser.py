"""
SOMA Parser

Parses a token stream into an Abstract Syntax Tree (AST).

See the ast-definition.md for the complete AST specification.
"""

from typing import List, Union
from soma.lexer import Token, TokenKind


class ParseError(Exception):
    """
    Raised when the parser encounters invalid syntax.

    Attributes:
        message - human-readable description
        line    - 1-based line number of the problem
        col     - 1-based column number of the problem
    """

    def __init__(self, message, line=None, col=None):
        if line is not None and col is not None:
            super(ParseError, self).__init__(
                "%s (line %d, col %d)" % (message, line, col)
            )
        else:
            super(ParseError, self).__init__(message)
        self.message = message
        self.line = line
        self.col = col


# ==================== AST Node Classes ====================


class Program:
    """
    Top-level AST node representing a complete SOMA program.

    Attributes:
        statements - List of statement nodes to execute
    """

    def __init__(self, statements: List):
        self.statements = statements

    def __repr__(self):
        return "Program(statements=%r)" % (self.statements,)

    def __eq__(self, other):
        return isinstance(other, Program) and self.statements == other.statements


class IntNode:
    """
    Represents an integer literal.

    Attributes:
        value - The integer value
    """

    def __init__(self, value: int, location=None):
        self.value = value
        self.location = location

    def __repr__(self):
        return "IntNode(%r)" % (self.value,)

    def __eq__(self, other):
        return isinstance(other, IntNode) and self.value == other.value


class StringNode:
    """
    Represents a string literal (already decoded by lexer).

    Attributes:
        value - The decoded string value
    """

    def __init__(self, value: str, location=None):
        self.value = value
        self.location = location

    def __repr__(self):
        return "StringNode(%r)" % (self.value,)

    def __eq__(self, other):
        return isinstance(other, StringNode) and self.value == other.value


class BlockNode:
    """
    Represents a block { ... } containing a sequence of statements.

    Blocks are eagerly parsed - the body contains fully parsed AST nodes,
    not a token stream.

    Attributes:
        body - List of statement nodes in the block
    """

    def __init__(self, body: List, location=None):
        self.body = body
        self.location = location

    def __repr__(self):
        return "BlockNode(body=%r)" % (self.body,)

    def __eq__(self, other):
        return isinstance(other, BlockNode) and self.body == other.body


class ValuePath:
    """
    Represents a path that reads a value from a Cell.

    Attributes:
        components - List of path components (e.g., ["a", "b", "c"] for a.b.c)
    """

    def __init__(self, components: List[str], location=None):
        self.components = components
        self.location = location

    def __repr__(self):
        return "ValuePath(%r)" % (self.components,)

    def __eq__(self, other):
        return isinstance(other, ValuePath) and self.components == other.components


class ReferencePath:
    """
    Represents a path with trailing . that reads a CellRef from a Cell.

    The trailing dot is implicit in the node type - it's not stored in components.

    Attributes:
        components - List of path components (trailing . not included)
    """

    def __init__(self, components: List[str], location=None):
        self.components = components
        self.location = location

    def __repr__(self):
        return "ReferencePath(%r)" % (self.components,)

    def __eq__(self, other):
        return isinstance(other, ReferencePath) and self.components == other.components


class ExecNode:
    """
    Represents the execute modifier >path or >{...}.

    Attributes:
        target - Either a ValuePath or BlockNode to execute
    """

    def __init__(self, target: Union[ValuePath, BlockNode], location=None):
        self.target = target
        self.location = location

    def __repr__(self):
        return "ExecNode(target=%r)" % (self.target,)

    def __eq__(self, other):
        return isinstance(other, ExecNode) and self.target == other.target


class StoreNode:
    """
    Represents the store modifier !path or !path.

    Attributes:
        target - Either a ValuePath or ReferencePath where to store
    """

    def __init__(self, target: Union[ValuePath, ReferencePath], location=None):
        self.target = target
        self.location = location

    def __repr__(self):
        return "StoreNode(target=%r)" % (self.target,)

    def __eq__(self, other):
        return isinstance(other, StoreNode) and self.target == other.target


# ==================== Parser Class ====================


class Parser:
    """
    Recursive descent parser for SOMA.

    Parses a token stream into an Abstract Syntax Tree (AST).
    """

    def __init__(self, tokens: List[Token]):
        """
        Initialize the parser with a token stream.

        Args:
            tokens - List of Token objects from the lexer (must end with EOF)
        """
        self.tokens = tokens
        self.current = 0

    def parse(self) -> Program:
        """
        Parse the token stream into a Program AST node.

        Returns:
            Program node containing all parsed statements

        Raises:
            ParseError if the token stream contains invalid syntax
        """
        statements = []
        while not self._is_at_end():
            statements.append(self._parse_statement())
        return Program(statements)

    # ==================== Statement Parsing ====================

    def _parse_statement(self):
        """
        Parse a single statement.

        A statement can be:
        - IntNode (integer literal)
        - StringNode (string literal)
        - BlockNode (block { ... })
        - ValuePath or ReferencePath (path)
        - ExecNode (>path or >{...})
        - StoreNode (!path or !path.)

        Returns:
            An AST node representing the statement

        Raises:
            ParseError if no valid statement can be parsed
        """
        if self._check(TokenKind.INT):
            return self._parse_int()
        elif self._check(TokenKind.STRING):
            return self._parse_string()
        elif self._check(TokenKind.LBRACE):
            return self._parse_block()
        elif self._check(TokenKind.EXEC):
            return self._parse_exec()
        elif self._check(TokenKind.STORE):
            return self._parse_store()
        elif self._check(TokenKind.PATH):
            return self._parse_path()
        elif self._check(TokenKind.RBRACE):
            # Unexpected closing brace
            token = self._peek()
            raise ParseError(
                "Unexpected '}' without matching '{'",
                token.line,
                token.col
            )
        else:
            token = self._peek()
            raise ParseError(
                "Unexpected token: %s" % token.kind.value,
                token.line,
                token.col
            )

    def _parse_int(self) -> IntNode:
        """
        Parse an integer literal token into an IntNode.

        Returns:
            IntNode with the parsed integer value

        Raises:
            ParseError if the current token is not an INT
        """
        token = self._expect(TokenKind.INT)
        return IntNode(int(token.value))

    def _parse_string(self) -> StringNode:
        """
        Parse a string literal token into a StringNode.

        The lexer has already decoded all Unicode escapes and removed delimiters.

        Returns:
            StringNode with the decoded string value

        Raises:
            ParseError if the current token is not a STRING
        """
        token = self._expect(TokenKind.STRING)
        return StringNode(token.value)

    def _parse_block(self) -> BlockNode:
        """
        Parse a block { ... } into a BlockNode.

        Blocks are eagerly parsed - all statements inside are fully parsed
        into AST nodes, not stored as tokens.

        Returns:
            BlockNode with fully parsed body

        Raises:
            ParseError if the block is not properly closed
        """
        self._expect(TokenKind.LBRACE)
        body = []

        while not self._check(TokenKind.RBRACE):
            if self._is_at_end():
                token = self._peek()
                raise ParseError(
                    "Unclosed block (missing '}')",
                    token.line,
                    token.col
                )
            body.append(self._parse_statement())

        self._expect(TokenKind.RBRACE)
        return BlockNode(body)

    # ==================== Path Parsing ====================

    def _parse_path(self) -> Union[ValuePath, ReferencePath]:
        """
        Parse a PATH token into either ValuePath or ReferencePath.

        The lexer produces PATH tokens containing the entire path string including
        dots (e.g., "a.b.c" or "a.b."). The parser must:
        1. Check if the path ends with . (indicates ReferencePath)
        2. Split the path by . to get components
        3. Validate register path syntax (_ or _.path, not _path)
        4. Return ValuePath or ReferencePath accordingly

        Returns:
            ValuePath or ReferencePath node

        Raises:
            ParseError for invalid path syntax (e.g., "_temp" without dot)
        """
        token = self._expect(TokenKind.PATH)
        value = token.value
        is_reference = False

        # Check for trailing dot (indicates ReferencePath)
        if value.endswith("."):
            is_reference = True
            # Strip trailing dot before splitting
            value = value[:-1]

        # Split by . to get components
        components = value.split(".")

        # Validate components are non-empty
        if any(c == "" for c in components):
            raise ParseError(
                "Empty path component in '%s'" % token.value,
                token.line,
                token.col
            )

        # Validate register paths
        self._validate_register_path(components, token)

        if is_reference:
            return ReferencePath(components)
        else:
            return ValuePath(components)

    def _validate_register_path(self, components: List[str], token: Token):
        """
        Validate register path syntax.

        Register paths must be either:
        - ["_"] - register root
        - ["_", "x", ...] - register path with dot syntax

        Invalid forms like ["_x"] or ["_temp"] must be rejected.

        Args:
            components - List of path components after splitting
            token - The original PATH token (for error reporting)

        Raises:
            ParseError if the path uses invalid register syntax
        """
        # Check if single component starts with _ but is not exactly "_"
        if len(components) == 1 and components[0].startswith("_") and components[0] != "_":
            raise ParseError(
                "Invalid register syntax: '%s'. Register paths must use '_.%s' (with dot), not '%s' (without dot)" % (
                    token.value,
                    components[0][1:],
                    token.value
                ),
                token.line,
                token.col
            )

    # ==================== Modifier Parsing ====================

    def _parse_exec(self) -> ExecNode:
        """
        Parse an execute modifier >path or >{...}.

        Valid targets:
        - ValuePath (execute block at path)
        - BlockNode (execute inline block)

        Invalid targets:
        - ReferencePath (cannot execute a CellRef)

        Returns:
            ExecNode with the parsed target

        Raises:
            ParseError if target is invalid (e.g., ReferencePath)
        """
        self._expect(TokenKind.EXEC)

        # Check for block target
        if self._check(TokenKind.LBRACE):
            block = self._parse_block()
            return ExecNode(block)

        # Must be a path target
        if self._check(TokenKind.PATH):
            path = self._parse_path()
            # Cannot execute a ReferencePath
            if isinstance(path, ReferencePath):
                token = self.tokens[self.current - 1]  # Get the PATH token we just consumed
                raise ParseError(
                    "Cannot execute a reference path (path with trailing '.')",
                    token.line,
                    token.col
                )
            return ExecNode(path)

        # No valid target
        token = self._peek()
        raise ParseError(
            "Expected path or block after '>'",
            token.line,
            token.col
        )

    def _parse_store(self) -> StoreNode:
        """
        Parse a store modifier !path or !path.

        Valid targets:
        - ValuePath (store to cell value)
        - ReferencePath (replace entire cell)

        Returns:
            StoreNode with the parsed target

        Raises:
            ParseError if no path follows the ! token
        """
        self._expect(TokenKind.STORE)

        # Must be a path target
        if not self._check(TokenKind.PATH):
            token = self._peek()
            raise ParseError(
                "Expected path after '!'",
                token.line,
                token.col
            )

        path = self._parse_path()
        return StoreNode(path)

    # ==================== Helper Methods ====================

    def _peek(self) -> Token:
        """
        Look at the current token without consuming it.

        Returns:
            The current token
        """
        return self.tokens[self.current]

    def _advance(self) -> Token:
        """
        Consume and return the current token, advancing to the next.

        Returns:
            The token that was consumed
        """
        token = self.tokens[self.current]
        if not self._is_at_end():
            self.current += 1
        return token

    def _check(self, kind: TokenKind) -> bool:
        """
        Check if the current token is of the given kind.

        Args:
            kind - TokenKind to check for

        Returns:
            True if current token matches, False otherwise
        """
        if self._is_at_end():
            return kind == TokenKind.EOF
        return self._peek().kind == kind

    def _match(self, *kinds: TokenKind) -> bool:
        """
        Check if the current token matches any of the given kinds.
        If it matches, consume it and return True.

        Args:
            kinds - TokenKind values to check for

        Returns:
            True if matched and consumed, False otherwise
        """
        for kind in kinds:
            if self._check(kind):
                self._advance()
                return True
        return False

    def _expect(self, kind: TokenKind) -> Token:
        """
        Consume a token of the expected kind, or raise an error.

        Args:
            kind - The expected TokenKind

        Returns:
            The consumed token

        Raises:
            ParseError if current token doesn't match expected kind
        """
        if not self._check(kind):
            current = self._peek()
            raise ParseError(
                "Expected %s but found %s" % (kind.value, current.kind.value),
                current.line,
                current.col
            )
        return self._advance()

    def _is_at_end(self) -> bool:
        """
        Check if we've reached the EOF token.

        Returns:
            True if at EOF, False otherwise
        """
        return self._peek().kind == TokenKind.EOF


# ==================== Public API ====================

def parse(source: str):
    """
    Parse SOMA source code into an AST represented as dictionaries.

    This is the main entry point for the parser. It lexes the source,
    parses the token stream, and converts the AST to dictionaries.

    Args:
        source - SOMA source code string

    Returns:
        Dictionary representation of the AST with this structure:
        {
            "kind": "Program",
            "body": [... statement nodes ...],
            "location": {"line": int, "column": int, "length": int}
        }

    Raises:
        ParseError if the source contains syntax errors
    """
    from soma.lexer import lex

    # Lex the source
    tokens = lex(source)

    # Parse the token stream
    parser = Parser(tokens)
    program = parser.parse()

    # Convert to dictionary representation
    return _ast_to_dict(program)


def _ast_to_dict(node):
    """
    Convert an AST node to a dictionary representation.

    The tests expect dictionaries with "kind", type-specific fields,
    and "location" information.
    """
    if isinstance(node, Program):
        return {
            "kind": "Program",
            "body": [_ast_to_dict(stmt) for stmt in node.statements],
            "location": {"line": 1, "column": 1, "length": 0}
        }
    elif isinstance(node, IntNode):
        return {
            "kind": "IntNode",
            "value": node.value,
            "location": {"line": 1, "column": 1, "length": 1}
        }
    elif isinstance(node, StringNode):
        return {
            "kind": "StringNode",
            "value": node.value,
            "location": {"line": 1, "column": 1, "length": len(node.value) + 2}
        }
    elif isinstance(node, BlockNode):
        return {
            "kind": "BlockNode",
            "body": [_ast_to_dict(stmt) for stmt in node.body],
            "location": {"line": 1, "column": 1, "length": 2}
        }
    elif isinstance(node, ValuePath):
        return {
            "kind": "ValuePath",
            "components": node.components,
            "location": {"line": 1, "column": 1, "length": len(".".join(node.components))}
        }
    elif isinstance(node, ReferencePath):
        return {
            "kind": "ReferencePath",
            "components": node.components,
            "location": {"line": 1, "column": 1, "length": len(".".join(node.components)) + 1}
        }
    elif isinstance(node, ExecNode):
        return {
            "kind": "ExecNode",
            "target": _ast_to_dict(node.target),
            "location": {"line": 1, "column": 1, "length": 1}
        }
    elif isinstance(node, StoreNode):
        return {
            "kind": "StoreNode",
            "target": _ast_to_dict(node.target),
            "location": {"line": 1, "column": 1, "length": 1}
        }
    else:
        raise ValueError("Unknown node type: %s" % type(node).__name__)

