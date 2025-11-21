# 2. Lexical Analysis and Parsing

This section defines how SOMA source code is converted from raw text into an Abstract Syntax Tree (AST). This happens in two phases:

1. **Lexical Analysis (Lexer)** — Converts raw text into a stream of tokens
2. **Parsing (Parser)** — Converts the token stream into an AST

The lexer is **purely syntactic**: it recognizes token boundaries and categories but does not interpret semantic meaning. The parser builds the AST structure and performs validation like register path syntax checking.

## 2.1 Lexer Overview

The SOMA lexer (defined in `soma/lexer.py`) converts source text into a stream of tokens. Each token has:

* **kind** — one of INT, PATH, EXEC, STORE, STRING, LBRACE, RBRACE, or EOF
* **value** — the string representation as it appears in source (decoded for STRING tokens)
* **line**, **col** — position of the first character (1-based)

Tokenization is deterministic and proceeds left-to-right, character by character. The lexer maintains state for line and column tracking but has no other state—each character is processed independently based on local context.

Characters that do not match any token rule generate a `LexError` exception.

## 2.2 Token Categories

SOMA defines eight token kinds:

| Token Kind | Description | Example |
|------------|-------------|---------|
| `INT` | Decimal integer (signed or unsigned) | `42`, `-7`, `+9` |
| `PATH` | General identifier or name | `foo`, `x.y`, `print` |
| `EXEC` | Execute prefix modifier `>` | `>print` (two tokens: EXEC + PATH) |
| `STORE` | Store prefix modifier `!` | `!x` (two tokens: STORE + PATH) |
| `STRING` | String literal `( … )` | `(hello)`, `(\41\)` |
| `LBRACE` | Block start `{` | `{` |
| `RBRACE` | Block end `}` | `}` |
| `EOF` | End-of-file marker | — |

All tokens except `EOF` correspond to explicit characters in the source.

**Important:** `EXEC` and `STORE` are **prefix modifiers**, not standalone tokens. When the lexer sees `>print`, it produces two separate tokens: EXEC(">") followed by PATH("print"). The `>` is not part of the path name. The semantic meaning (execution or storage) is handled by the parser/runtime, not the lexer.

## 2.3 Whitespace

Whitespace separates tokens but is otherwise ignored. Whitespace characters are:

* ASCII space (`U+0020`)
* Tab (`U+0009`)
* Line feed (`\n`, `U+000A`)
* Carriage return (`\r`, `U+000D`)

Line/column tracking rules:
* `\n` advances line, resets column to 1
* `\r\n` (CRLF) counts as a single line terminator
* Bare `\r` also ends the line

## 2.4 Comments

A **comment** begins with `)` at the start of a token (after whitespace or at column 1), outside any string literal.

**Syntax:**
```
COMMENT ::= ')' <any characters until line terminator or EOF>
```

**Rules:**
* The `)` and all characters until `\n`, `\r`, `\r\n`, or EOF are ignored
* Comments do not emit tokens
* Inside a string literal `( … )`, the `)` closes the string, not a comment
* A `)` in the middle of a PATH is part of the path, not a comment starter

**Examples:**

```soma
) This is a full-line comment

>foo ) This is a trailing comment

{ >a
  ) Comment inside a block
  >b
}

42 ) Number followed by comment
```

## 2.5 String Literals

String literals use parenthesis delimiters with Unicode escape sequences.

**Syntax:**
```
STRING ::= '(' STRING_CONTENT ')'
```

**Rules:**
* Any character except `)` and backslash is literal
* `)` closes the string
* Backslash (`\`) starts a Unicode escape

### 2.5.1 Unicode Escapes: `\HEX\`

```
ESCAPE ::= '\' HEXDIGITS '\'
HEXDIGITS ::= one or more [0-9A-Fa-f]
```

**Escape Rules:**
* Hex digits are decoded using `int(hex, 16)`
* The result is converted to Unicode using `chr(codepoint)`
* Empty escapes `\\` are illegal
* Non-hex characters in the escape raise an error
* Each escape is independent; they do not overlap

**Examples:**

| SOMA Source | Decoded Value | Description |
|-------------|---------------|-------------|
| `(\41\)` | `"A"` | Unicode U+0041 (letter A) |
| `(Hello\d\)` | `"Hello\r"` | Carriage return |
| `(\5C\)` | `"\"` | Backslash |
| `(\41\42\43\)` | `"ABC"` | Three consecutive escapes |
| `(\D\A\)` | `"\r\n"` | CRLF sequence |

**Error Cases:**

```soma
(hello          ) Unterminated string (missing closing paren)
(hello\5C       ) Unterminated escape (missing closing backslash)
(\g\)           ) Invalid hex digit 'g'
(\\)            ) Empty escape (no hex digits)
```

**Multiline Strings:**

Strings may span multiple lines:

```soma
(This is a
multiline
string)
```

## 2.6 Blocks

Blocks are delimited by braces:

```
BLOCK ::= '{' <tokens>* '}'
```

**Token Rules:**
* `{` produces `LBRACE`
* `}` produces `RBRACE`

**Modifier Rules:**
* `>{...}` is valid: EXEC followed by LBRACE
* `!{...}` is **illegal**: cannot store directly into a block

**Example:**

```soma
{ >a >b }           ) Valid block
>{ >print }         ) Valid: execute a block
!{ >print }         ) LEXER ERROR: cannot store to block
```

## 2.7 Prefix Modifiers

SOMA has two prefix operators that modify the token that follows.

### 2.7.1 Execute: `>`

The `>` operator is a **prefix modifier** that marks execution of the value at the following path. It produces an `EXEC` token followed by the target token.

**Semantic Note:** The `>` modifier means "read the value at this path and execute it". This is an atomic operation handled by the parser/runtime, not the lexer. For example, `>print` reads the Block stored at Store path "print" and executes it. All SOMA built-ins are just Blocks at Store paths—there is no special built-in mechanism.

**Token Structure:**
* `>print` → Two tokens: EXEC(">") + PATH("print")
* `>_.action` → Two tokens: EXEC(">") + PATH("_.action")
* `>{ ... }` → EXEC(">") + LBRACE + ... + RBRACE

**Valid Targets:**
* PATH: `>foo` → EXEC, PATH("foo")
* LBRACE: `>{ ... }` → EXEC, LBRACE, ...

**Examples:**

| Source | Tokens | Description |
|--------|--------|-------------|
| `>foo` | EXEC, PATH("foo") | Execute value at path "foo" |
| `>print` | EXEC, PATH("print") | Execute Block at Store path "print" |
| `>_.self` | EXEC, PATH("_.self") | Execute Block at Register path "_.self" |
| `>{ a }` | EXEC, LBRACE, PATH("a"), RBRACE | Execute inline block |
| `>` | PATH(">") | Standalone (no target) |

**Invalid Forms:**

```soma
>(foo)              ) Cannot execute a string literal
>42                 ) Cannot execute a number
```

### 2.7.2 Store: `!`

The `!` operator is a **prefix modifier** that marks storage of a value into the following path. It produces a `STORE` token followed by the target token.

**Semantic Note:** The `!` modifier means "pop the top of the Argument List and store it at this path". This operation is handled by the parser/runtime, not the lexer.

**Token Structure:**
* `!counter` → Two tokens: STORE("!") + PATH("counter")
* `!_.temp` → Two tokens: STORE("!") + PATH("_.temp")

**Valid Targets:**
* PATH: `!x` → STORE, PATH("x")

**Examples:**

| Source | Tokens | Description |
|--------|--------|-------------|
| `!x` | STORE, PATH("x") | Store to path "x" |
| `!a.b.c` | STORE, PATH("a.b.c") | Store to nested path |
| `!_.temp` | STORE, PATH("_.temp") | Store to Register path |
| `!` | PATH("!") | Standalone (no target) |

**Invalid Forms:**

```soma
!{a}                ) Cannot store to a block
!(foo)              ) Cannot store to a string
!42                 ) Cannot store to a number
```

### 2.7.3 Modifier Detection

The lexer determines whether `>` or `!` is a modifier based on context:

**Modifier Form** (produces EXEC or STORE token):
* Followed immediately by a valid target (PATH, LBRACE for `>`)
* No whitespace between modifier and target

**PATH Form** (produces PATH token):
* Followed by whitespace, EOF, or `}`
* Appears mid-token: `a>b` → PATH("a>b"), `x!y` → PATH("x!y")

**Examples:**

```soma
>foo                ) EXEC, PATH("foo")
> foo               ) PATH(">"), PATH("foo")
a>b                 ) PATH("a>b")
!x                  ) STORE, PATH("x")
! x                 ) PATH("!"), PATH("x")
concat>             ) PATH("concat>")
```

## 2.8 Integers

Integer literals follow this syntax:

```
INT ::= [ '+' | '-' ] DIGITS
DIGITS ::= [0-9]+
```

**Rules:**
* Leading sign (`+` or `-`) is optional
* The sign **must** be followed by a digit to form an integer
* Otherwise, the sign begins a PATH

**Valid Integers:**

```soma
23                  ) INT(23)
+23                 ) INT(+23)
-23                 ) INT(-23)
0                   ) INT(0)
```

**Non-Integer Tokens:**

```soma
+hello              ) PATH("+hello")
-foo                ) PATH("-foo")
+                   ) PATH("+")
-                   ) PATH("-")
```

**Invalid Forms:**

These cause lexical errors:

```soma
23a                 ) Illegal: letter after digits
23-5                ) Illegal: sign after digits
23,5                ) Illegal: comma after digits
```

## 2.9 Paths

A PATH is any sequence of non-whitespace characters that doesn't match another token category.

```
PATH ::= any non-whitespace printable sequence
         excluding: '{', '}' at token level
         and excluding ')' at start (comment introducer)
         and excluding '(' at start (string literal)
         and excluding integers and modifier forms
```

**Characteristics:**
* May contain `>`, `!`, `.`, `:`, or other printable characters
* Ends at whitespace, `{`, `}`, `(`, or a comment starter `)`

**Valid Paths:**

```soma
foo                 ) Simple identifier
dog-3               ) Path with hyphen
x!y                 ) Path containing !
a>b                 ) Path containing >
concat>             ) Path ending with >
a.b.c               ) Dotted path (Store path)
_                   ) Register root (underscore alone)
_.x                 ) Register path (root → x)
_.x.y.z             ) Register path (root → x → y → z)
_.self              ) Register path to self binding
_tmp                ) PATH token, but not standard register syntax
```

**Register Paths:**

The lexer recognizes register-related tokens purely syntactically:

* `_` alone is a valid PATH token representing the register root
* `_.x`, `_.x.y`, etc. are valid PATH tokens for register paths
* `_tmp`, `_x`, `_self` (without dot after `_`) are lexically valid PATH tokens, but are **not** standard register syntax

The distinction between `_x` and `_.x` is **semantic**, not lexical:
* The lexer tokenizes both as PATH tokens
* The **parser** validates register syntax: only `_` (register root) and paths starting with `_.` (e.g., `_.x`) are valid
* Paths like `_x` (without dot) cause a `ParseError` with a helpful message suggesting the correct `_.x` form

**Edge Cases:**

```soma
>                   ) Standalone: PATH(">")
!                   ) Standalone: PATH("!")
-)                  ) PATH("-)") – special case
```

## 2.10 Token Reference Table

Complete reference of SOMA token categories:

| Category | Pattern | Token Kind | Notes |
|----------|---------|------------|-------|
| Comment | `)` at token start | — | Skipped, no token emitted |
| String | `(` ... `)` | STRING | Unicode escapes via `\HEX\` |
| Block open | `{` | LBRACE | Structural delimiter |
| Block close | `}` | RBRACE | Structural delimiter |
| Execute | `>` + target | EXEC | Prefix modifier; `>print` is two tokens |
| Store | `!` + target | STORE | Prefix modifier; `!x` is two tokens |
| Integer | `[+-]?[0-9]+` | INT | Sign must precede digits |
| Path | everything else | PATH | Default category |
| End of file | — | EOF | Implicit, always last |

## 2.11 Lexical Errors

The lexer raises errors for:

* **Unterminated strings**: `(hello` (missing `)`)
* **Invalid escapes**: `(\g\)` (non-hex digit), `(\\)` (empty escape)
* **Invalid modifier targets**:
  * `>(foo)` — cannot execute string
  * `!{...}` — cannot store to block
  * `>42` — cannot execute number
* **Illegal numeric forms**: `23a`, `42-x`
* **Unexpected characters**: Any malformed token sequence

## 2.12 Examples

### 2.12.1 Valid Tokenization

```soma
42 >print
```
Tokens: INT("42"), EXEC(">"), PATH("print"), EOF

**Note:** `>print` is two tokens—EXEC prefix modifier followed by PATH. The lexer does not interpret this as "calling a built-in". It simply recognizes the prefix modifier `>` and the path name `print`. The execution semantics (reading and executing the Block at Store path "print") are handled by the parser/runtime.

```soma
(hello) !message
```
Tokens: STRING("hello"), STORE("!"), PATH("message"), EOF

```soma
{ >a >b } >execute
```
Tokens: LBRACE("{"), EXEC(">"), PATH("a"), EXEC(">"), PATH("b"), RBRACE("}"), EXEC(">"), PATH("execute"), EOF

```soma
a.b.c 23 +hello
```
Tokens: PATH("a.b.c"), INT("23"), PATH("+hello"), EOF

### 2.12.2 Edge Cases

```soma
>
```
Tokens: PATH(">"), EOF

```soma
!
```
Tokens: PATH("!"), EOF

```soma
> { }
```
Tokens: PATH(">"), LBRACE("{"), RBRACE("}"), EOF

```soma
concat> !result
```
Tokens: PATH("concat>"), STORE("!"), PATH("result"), EOF

### 2.12.3 Register Paths

```soma
_ !_.x
```
Tokens: PATH("_"), STORE("!"), PATH("_.x"), EOF

```soma
_.counter 1 >+ !_.counter
```
Tokens: PATH("_.counter"), INT("1"), EXEC(">"), PATH("+"), STORE("!"), PATH("_.counter"), EOF

```soma
_.self >chain
```
Tokens: PATH("_.self"), EXEC(">"), PATH("Chain"), EOF

**Lexical vs Semantic:**

```soma
_tmp                ) Lexically: PATH("_tmp")
                    ) Semantically: Not valid register syntax (missing dot)
```

```soma
_.tmp               ) Lexically: PATH("_.tmp")
                    ) Semantically: Valid register path (root → tmp)
```

The lexer does not enforce register syntax rules—it only produces PATH tokens. The parser or runtime must validate that register paths follow the `_.path` convention.

### 2.12.4 Comments and Strings

```soma
) This is a comment
(This is ) a string) ) Another comment
```
Tokens: STRING("This is ) a string"), EOF

Note: The first `)` inside the string does not start a comment; it closes the string.

## 2.13 Lexer Summary

The SOMA lexer is intentionally simple and orthogonal:

* **`(` ... `)`** — strings with Unicode escapes (decoded during lexing)
* **`{` ... `}`** — blocks (produces LBRACE/RBRACE tokens)
* **`)` at token start** — comments (skipped, no token produced)
* **`>` / `!` at token start** — prefix modifiers (produces EXEC/STORE tokens)
* **`[+-]?[0-9]+`** — integers (sign must precede digits)
* **Everything else** — paths (default category)

Each category is mutually exclusive and unambiguous. The lexer enforces structural correctness but does not interpret semantics—that is the parser's responsibility.

**Key Design Points:**

1. **Stateless token recognition** — Each token is recognized based on its starting character and local context
2. **String decoding happens in lexer** — Unicode escapes (`\HEX\`) are decoded during lexing; the parser receives the final decoded string
3. **Register syntax is not enforced** — The lexer accepts both `_x` and `_.x` as PATH tokens; the parser enforces the `_.x` convention
4. **Modifier detection is context-sensitive** — `>foo` produces EXEC + PATH, while `> foo` produces PATH + PATH
5. **Error reporting includes location** — `LexError` exceptions include line/col information for precise error messages

---

# 3. Parser and AST Construction

The SOMA parser (defined in `soma/parser.py`) consumes the token stream from the lexer and builds an Abstract Syntax Tree (AST). The parser is a recursive descent parser that:

1. Validates syntax and structure
2. Builds typed AST nodes
3. Splits paths into components
4. Validates semantic rules (like register path syntax)
5. Eagerly parses block contents

## 3.1 Parser Overview

**Entry Point:**
```python
from soma.parser import parse

ast = parse("42 >print")  # Returns dictionary representation of AST
```

The `parse()` function is the main entry point and performs these steps:
1. Calls `lex(source)` to tokenize the source
2. Creates a `Parser(tokens)` instance
3. Calls `parser.parse()` to build the AST
4. Converts AST nodes to dictionary representation for external use

**Parser Architecture:**

The parser uses a simple recursive descent design:
- **Current position tracker** — `self.current` index into token list
- **Lookahead** — `_peek()` to examine current token without consuming
- **Token consumption** — `_advance()`, `_expect()`, `_check()`, `_match()`
- **Recursive parsing** — Each AST node type has its own parsing method

## 3.2 AST Node Types

The parser produces eight AST node types:

### 3.2.1 Program

Top-level container for a complete SOMA program.

**Structure:**
```python
Program(
    statements=[...]  # List of statement nodes
)
```

**Example:**
```soma
1 2 >+
```
Produces:
```python
Program(statements=[
    IntNode(1),
    IntNode(2),
    ExecNode(target=ValuePath(["+"]))
])
```

### 3.2.2 IntNode

Represents an integer literal. The lexer provides the string representation; the parser converts it to an integer.

**Structure:**
```python
IntNode(
    value=42  # int
)
```

**Example:**
```soma
-23
```
Produces:
```python
IntNode(value=-23)
```

### 3.2.3 StringNode

Represents a string literal. The lexer has already decoded Unicode escapes; the parser just wraps the value.

**Structure:**
```python
StringNode(
    value="hello"  # str (already decoded by lexer)
)
```

**Example:**
```soma
(\41\BC\)
```
Lexer produces: `Token(STRING, "ABC", ...)`
Parser produces: `StringNode(value="ABC")`

### 3.2.4 BlockNode

Represents a block `{ ... }`. Blocks are **eagerly parsed** — the parser recursively parses all statements inside the block immediately.

**Structure:**
```python
BlockNode(
    body=[...]  # List of fully parsed statement nodes
)
```

**Example:**
```soma
{ 1 2 >+ }
```
Produces:
```python
BlockNode(body=[
    IntNode(1),
    IntNode(2),
    ExecNode(target=ValuePath(["+"]))
])
```

**Nesting:**
Blocks can be nested to any depth. Each level is fully parsed:
```soma
{ { { 42 } } }
```
Produces:
```python
BlockNode(body=[
    BlockNode(body=[
        BlockNode(body=[
            IntNode(42)
        ])
    ])
])
```

### 3.2.5 ValuePath

Represents a path that reads a value from a Cell (no trailing dot).

**Structure:**
```python
ValuePath(
    components=["a", "b", "c"]  # List[str]
)
```

**Parsing Process:**
1. Lexer produces: `Token(PATH, "a.b.c", ...)`
2. Parser splits by `.` to get `["a", "b", "c"]`
3. Parser validates register syntax if first component is `"_"`

**Examples:**

| Source | Components | Description |
|--------|------------|-------------|
| `foo` | `["foo"]` | Single-component path |
| `a.b.c` | `["a", "b", "c"]` | Multi-component path |
| `_` | `["_"]` | Register root (valid) |
| `_.x` | `["_", "x"]` | Register path (valid) |
| `_.x.y.z` | `["_", "x", "y", "z"]` | Nested register path (valid) |

### 3.2.6 ReferencePath

Represents a path with a trailing dot that reads a CellRef from a Cell.

**Structure:**
```python
ReferencePath(
    components=["a", "b"]  # List[str], trailing dot NOT included
)
```

**Parsing Process:**
1. Lexer produces: `Token(PATH, "a.b.", ...)`
2. Parser detects trailing `.`
3. Parser strips trailing `.` → `"a.b"`
4. Parser splits by `.` to get `["a", "b"]`

**Examples:**

| Source | Components | Description |
|--------|------------|-------------|
| `a.` | `["a"]` | Single-component reference |
| `a.b.` | `["a", "b"]` | Multi-component reference |
| `_.` | `["_"]` | Register root reference |
| `_.x.` | `["_", "x"]` | Register path reference |

**Key Difference from ValuePath:**
The node type itself (ReferencePath vs ValuePath) indicates the trailing dot—it's not stored in the components array.

### 3.2.7 ExecNode

Represents the execute modifier `>path` or `>{...}`.

**Structure:**
```python
ExecNode(
    target=<ValuePath or BlockNode>
)
```

**Valid Targets:**
- **ValuePath** — Execute the Block stored at this path
- **BlockNode** — Execute this inline block

**Invalid Targets:**
- **ReferencePath** — Cannot execute a CellRef (raises `ParseError`)

**Parsing Process:**
1. Lexer produces: `Token(EXEC, ">", ...)` + target token
2. Parser consumes EXEC token
3. Parser checks next token:
   - If `LBRACE` → parse block → `ExecNode(BlockNode(...))`
   - If `PATH` → parse path → validate not ReferencePath → `ExecNode(ValuePath(...))`

**Examples:**

```soma
>print
```
→ `ExecNode(target=ValuePath(["print"]))`

```soma
>{ 5 5 >* }
```
→ `ExecNode(target=BlockNode(body=[IntNode(5), IntNode(5), ExecNode(...)]))`

```soma
>a.b.
```
→ `ParseError: "Cannot execute a reference path (path with trailing '.')"`

### 3.2.8 StoreNode

Represents the store modifier `!path` or `!path.`.

**Structure:**
```python
StoreNode(
    target=<ValuePath or ReferencePath>
)
```

**Valid Targets:**
- **ValuePath** — Store to the Cell's value (modifies Cell content)
- **ReferencePath** — Replace the entire Cell (structural mutation)

**Parsing Process:**
1. Lexer produces: `Token(STORE, "!", ...)` + `Token(PATH, "...", ...)`
2. Parser consumes STORE token
3. Parser parses path (which may be ValuePath or ReferencePath)
4. Parser creates `StoreNode(target=<path>)`

**Examples:**

```soma
!counter
```
→ `StoreNode(target=ValuePath(["counter"]))`

```soma
!a.b.c
```
→ `StoreNode(target=ValuePath(["a", "b", "c"]))`

```soma
!data.
```
→ `StoreNode(target=ReferencePath(["data"]))`

## 3.3 Path Parsing and Validation

Path parsing is one of the parser's key responsibilities. The lexer produces a single PATH token (e.g., `"a.b.c."`); the parser must:

1. Detect trailing dot (determines ValuePath vs ReferencePath)
2. Strip trailing dot if present
3. Split remaining string by `.` to get components
4. Validate each component is non-empty
5. Validate register path syntax if first component is `"_"`

### 3.3.1 Path Splitting Algorithm

```python
def _parse_path(self):
    token = self._expect(TokenKind.PATH)
    value = token.value
    is_reference = False

    # Step 1: Check for trailing dot
    if value.endswith("."):
        is_reference = True
        value = value[:-1]  # Strip trailing dot

    # Step 2: Split by dot
    components = value.split(".")

    # Step 3: Validate non-empty components
    if any(c == "" for c in components):
        raise ParseError("Empty path component in '%s'" % token.value, ...)

    # Step 4: Validate register paths
    self._validate_register_path(components, token)

    # Step 5: Return appropriate node type
    if is_reference:
        return ReferencePath(components)
    else:
        return ValuePath(components)
```

### 3.3.2 Register Path Validation

Register paths must follow strict syntax rules:

**Valid Forms:**
- `_` — Register root (single component)
- `_.x` — Register path (two components: `["_", "x"]`)
- `_.x.y.z` — Nested register path (components: `["_", "x", "y", "z"]`)

**Invalid Forms:**
- `_x` — Missing dot after underscore
- `_temp` — Missing dot after underscore
- `_self` — Missing dot after underscore

**Validation Logic:**

```python
def _validate_register_path(self, components, token):
    # Check if single component starts with _ but is not exactly "_"
    if len(components) == 1 and components[0].startswith("_") and components[0] != "_":
        raise ParseError(
            "Invalid register syntax: '%s'. Register paths must use '_.%s' (with dot), not '%s' (without dot)" % (
                token.value,
                components[0][1:],  # Suggest correct form
                token.value
            ),
            token.line,
            token.col
        )
```

**Error Messages:**

```soma
_temp
```
→ `ParseError: "Invalid register syntax: '_temp'. Register paths must use '_.temp' (with dot), not '_temp' (without dot) (line 1, col 1)"`

This validation ensures that register paths are unambiguous and follow the documented convention.

## 3.4 Block Parsing (Eager Evaluation)

Blocks are parsed **eagerly** — when the parser encounters a `{`, it immediately parses all statements inside until the matching `}`. The block body contains fully parsed AST nodes, not tokens.

**Parsing Algorithm:**

```python
def _parse_block(self):
    self._expect(TokenKind.LBRACE)
    body = []

    while not self._check(TokenKind.RBRACE):
        if self._is_at_end():
            raise ParseError("Unclosed block (missing '}')", ...)
        body.append(self._parse_statement())  # Recursive parsing

    self._expect(TokenKind.RBRACE)
    return BlockNode(body)
```

**Why Eager Parsing?**

Eager parsing means blocks are fully validated at parse time:
- **Syntax errors detected early** — No need to wait until execution
- **AST is complete** — All code structures are represented in the AST
- **Simpler interpreter** — No need to re-parse blocks during execution

**Trade-offs:**
- **Parse time** — Must parse all code upfront (but SOMA programs are typically small)
- **Memory** — Full AST in memory (but SOMA ASTs are compact)

**Example:**

```soma
{ 1 { 2 { 3 } } }
```

Parsing trace:
1. `_parse_block()` — Enter outer block
2. `_parse_statement()` → `IntNode(1)`
3. `_parse_statement()` → calls `_parse_block()` — Enter middle block
4. `_parse_statement()` → `IntNode(2)`
5. `_parse_statement()` → calls `_parse_block()` — Enter inner block
6. `_parse_statement()` → `IntNode(3)`
7. Return from inner block → `BlockNode(body=[IntNode(3)])`
8. Return from middle block → `BlockNode(body=[IntNode(2), BlockNode(...)])`
9. Return from outer block → `BlockNode(body=[IntNode(1), BlockNode(...)])`

The result is a fully populated AST with all nesting preserved.

## 3.5 Modifier Parsing and Validation

Modifiers (`>` and `!`) are parsed by consuming the modifier token and then parsing the target.

### 3.5.1 Execute Modifier (`>`)

**Valid Targets:**
- ValuePath — `>print`, `>a.b.c`, `>+`
- BlockNode — `>{ ... }`

**Invalid Targets:**
- ReferencePath — `>a.` raises error (cannot execute a CellRef)

**Parsing:**

```python
def _parse_exec(self):
    self._expect(TokenKind.EXEC)

    # Check for block target
    if self._check(TokenKind.LBRACE):
        block = self._parse_block()
        return ExecNode(block)

    # Must be a path target
    if self._check(TokenKind.PATH):
        path = self._parse_path()
        # Validate not ReferencePath
        if isinstance(path, ReferencePath):
            raise ParseError(
                "Cannot execute a reference path (path with trailing '.')",
                ...
            )
        return ExecNode(path)

    # No valid target
    raise ParseError("Expected path or block after '>'", ...)
```

### 3.5.2 Store Modifier (`!`)

**Valid Targets:**
- ValuePath — `!x`, `!a.b.c`
- ReferencePath — `!x.`, `!a.b.`

**Invalid Targets:**
- BlockNode — Lexer already prevents `!{...}` (raises `LexError`)

**Parsing:**

```python
def _parse_store(self):
    self._expect(TokenKind.STORE)

    # Must be a path target
    if not self._check(TokenKind.PATH):
        raise ParseError("Expected path after '!'", ...)

    path = self._parse_path()
    return StoreNode(path)  # Can be ValuePath or ReferencePath
```

**Semantic Difference:**

```soma
!x      ) ValuePath — Store value to Cell at 'x' (modifies Cell content)
!x.     ) ReferencePath — Replace entire Cell at 'x' (structural mutation)
```

The trailing dot fundamentally changes the semantics of the store operation.

## 3.6 Error Handling and Reporting

The parser provides detailed error messages with source location information.

### 3.6.1 ParseError Exception

```python
class ParseError(Exception):
    def __init__(self, message, line=None, col=None):
        # Formats as: "message (line X, col Y)"
        self.message = message
        self.line = line
        self.col = col
```

### 3.6.2 Common Error Scenarios

**Unclosed Block:**
```soma
{ 1 2 3
```
→ `ParseError: "Unclosed block (missing '}') (line 1, col 8)"`

**Unexpected Closing Brace:**
```soma
}
```
→ `ParseError: "Unexpected '}' without matching '{' (line 1, col 1)"`

**Invalid Register Syntax:**
```soma
_temp
```
→ `ParseError: "Invalid register syntax: '_temp'. Register paths must use '_.temp' (with dot), not '_temp' (without dot) (line 1, col 1)"`

**Cannot Execute Reference:**
```soma
>data.
```
→ `ParseError: "Cannot execute a reference path (path with trailing '.') (line 1, col 1)"`

**Empty Path Component:**
```soma
a..b
```
→ `ParseError: "Empty path component in 'a..b' (line 1, col 1)"`

## 3.7 Complete Parsing Examples

### 3.7.1 Simple Arithmetic

**Source:**
```soma
1 2 >+
```

**Token Stream:**
```
Token(INT, "1", 1, 1)
Token(INT, "2", 1, 3)
Token(EXEC, ">", 1, 5)
Token(PATH, "+", 1, 6)
Token(EOF, "", 1, 7)
```

**AST:**
```python
Program(statements=[
    IntNode(value=1),
    IntNode(value=2),
    ExecNode(target=ValuePath(components=["+"]))
])
```

### 3.7.2 Block Storage

**Source:**
```soma
{ >dup >* } !square
```

**Token Stream:**
```
Token(LBRACE, "{", 1, 1)
Token(EXEC, ">", 1, 3)
Token(PATH, "dup", 1, 4)
Token(EXEC, ">", 1, 8)
Token(PATH, "*", 1, 9)
Token(RBRACE, "}", 1, 11)
Token(STORE, "!", 1, 13)
Token(PATH, "square", 1, 14)
Token(EOF, "", 1, 20)
```

**AST:**
```python
Program(statements=[
    BlockNode(body=[
        ExecNode(target=ValuePath(components=["dup"])),
        ExecNode(target=ValuePath(components=["*"]))
    ]),
    StoreNode(target=ValuePath(components=["square"]))
])
```

### 3.7.3 Register Operations

**Source:**
```soma
5 !_.x _.x _.x >* !_.result
```

**Token Stream:**
```
Token(INT, "5", 1, 1)
Token(STORE, "!", 1, 3)
Token(PATH, "_.x", 1, 4)
Token(PATH, "_.x", 1, 8)
Token(PATH, "_.x", 1, 12)
Token(EXEC, ">", 1, 16)
Token(PATH, "*", 1, 17)
Token(STORE, "!", 1, 19)
Token(PATH, "_.result", 1, 20)
Token(EOF, "", 1, 29)
```

**AST:**
```python
Program(statements=[
    IntNode(value=5),
    StoreNode(target=ValuePath(components=["_", "x"])),
    ValuePath(components=["_", "x"]),
    ValuePath(components=["_", "x"]),
    ExecNode(target=ValuePath(components=["*"])),
    StoreNode(target=ValuePath(components=["_", "result"]))
])
```

**Path Parsing Details:**
- `"_.x"` → Split by `.` → `["_", "x"]` → Validate register syntax → Valid (two components, first is `"_"`)
- `"_.result"` → Split by `.` → `["_", "result"]` → Valid

### 3.7.4 CellRef Operations

**Source:**
```soma
data. !ref 42 !ref
```

**Token Stream:**
```
Token(PATH, "data.", 1, 1)
Token(STORE, "!", 1, 7)
Token(PATH, "ref", 1, 8)
Token(INT, "42", 1, 12)
Token(STORE, "!", 1, 15)
Token(PATH, "ref", 1, 16)
Token(EOF, "", 1, 19)
```

**AST:**
```python
Program(statements=[
    ReferencePath(components=["data"]),      # Read CellRef for 'data'
    StoreNode(target=ValuePath(["ref"])),    # Store CellRef to 'ref' (value store)
    IntNode(value=42),
    StoreNode(target=ValuePath(["ref"]))     # Store 42 to 'ref' (value store)
])
```

**Note:** Both stores use ValuePath because `"ref"` has no trailing dot. The first store receives a CellRef value (from `data.`), the second receives an integer.

### 3.7.5 Nested Blocks with Execute

**Source:**
```soma
>{ { 1 2 >+ } >execute }
```

**Token Stream:**
```
Token(EXEC, ">", 1, 1)
Token(LBRACE, "{", 1, 2)
Token(LBRACE, "{", 1, 4)
Token(INT, "1", 1, 6)
Token(INT, "2", 1, 8)
Token(EXEC, ">", 1, 10)
Token(PATH, "+", 1, 11)
Token(RBRACE, "}", 1, 13)
Token(EXEC, ">", 1, 15)
Token(PATH, "execute", 1, 16)
Token(RBRACE, "}", 1, 24)
Token(EOF, "", 1, 25)
```

**AST:**
```python
ExecNode(target=BlockNode(body=[
    BlockNode(body=[
        IntNode(value=1),
        IntNode(value=2),
        ExecNode(target=ValuePath(components=["+"]))
    ]),
    ExecNode(target=ValuePath(components=["execute"]))
]))
```

**Parsing Trace:**
1. `_parse_exec()` — Consumes EXEC
2. `_parse_block()` — Outer block
3. `_parse_statement()` → `_parse_block()` — Inner block
4. Parse `1`, `2`, `>+` inside inner block
5. Return inner `BlockNode`
6. `_parse_statement()` → `_parse_exec()` → `ExecNode(ValuePath(["execute"]))`
7. Return outer `BlockNode`
8. Return `ExecNode(target=<outer block>)`

## 3.8 Lexer/Parser Boundary

Understanding the division of responsibilities between lexer and parser is crucial:

### Lexer Responsibilities

1. **Character-level tokenization** — Recognize token boundaries
2. **String decoding** — Decode `\HEX\` escapes in strings
3. **Comment stripping** — Remove `)` comments completely
4. **Whitespace handling** — Skip whitespace, track line/col
5. **Basic validation** — Reject illegal numeric forms (e.g., `23a`)
6. **Modifier detection** — Distinguish `>foo` (EXEC + PATH) from `> foo` (PATH + PATH)

**What lexer does NOT do:**
- Split paths into components (produces single PATH token)
- Validate register syntax (accepts both `_x` and `_.x`)
- Distinguish ValuePath vs ReferencePath (both are PATH tokens)
- Parse blocks (just produces LBRACE/RBRACE tokens)
- Enforce semantic rules

### Parser Responsibilities

1. **AST construction** — Build typed node tree
2. **Path splitting** — Split `"a.b.c"` into `["a", "b", "c"]`
3. **Trailing dot detection** — Distinguish ValuePath vs ReferencePath
4. **Register validation** — Reject `_x`, accept `_.x`
5. **Modifier target validation** — Ensure `>` targets ValuePath or Block, not ReferencePath
6. **Block nesting** — Recursively parse block contents
7. **Semantic validation** — Enforce rules beyond syntax

### Data Flow

```
Source Code
    ↓
┌─────────────────┐
│     LEXER       │
│  (lexer.py)     │
├─────────────────┤
│ • Tokenization  │
│ • String decode │
│ • Comment strip │
│ • Whitespace    │
└─────────────────┘
    ↓
Token Stream (List[Token])
    ↓
┌─────────────────┐
│    PARSER       │
│  (parser.py)    │
├─────────────────┤
│ • AST building  │
│ • Path parsing  │
│ • Validation    │
│ • Type checking │
└─────────────────┘
    ↓
Abstract Syntax Tree (Program)
    ↓
Dictionary Representation (for API)
```

### Example: Register Path Validation

**Source:** `_temp`

**Lexer Output:**
```python
Token(PATH, "_temp", 1, 1)  # Lexer accepts this as valid PATH
```

**Parser Processing:**
```python
# _parse_path() is called
token = Token(PATH, "_temp", 1, 1)
components = "_temp".split(".")  # ["_temp"]

# _validate_register_path() is called
# components[0] is "_temp"
# Starts with "_" but is not exactly "_"
# len(components) == 1

# RAISE ParseError:
# "Invalid register syntax: '_temp'.
#  Register paths must use '_.temp' (with dot), not '_temp' (without dot)
#  (line 1, col 1)"
```

The lexer produces a valid token, but the parser rejects it semantically.

## 3.9 Parser Implementation Notes

### 3.9.1 Helper Methods

The parser uses standard recursive descent helper methods:

**`_peek()`** — Look at current token without consuming:
```python
def _peek(self):
    return self.tokens[self.current]
```

**`_advance()`** — Consume current token and move to next:
```python
def _advance(self):
    token = self.tokens[self.current]
    if not self._is_at_end():
        self.current += 1
    return token
```

**`_check(kind)`** — Test if current token matches kind:
```python
def _check(self, kind):
    if self._is_at_end():
        return kind == TokenKind.EOF
    return self._peek().kind == kind
```

**`_expect(kind)`** — Consume token of expected kind or raise error:
```python
def _expect(self, kind):
    if not self._check(kind):
        current = self._peek()
        raise ParseError(
            "Expected %s but found %s" % (kind.value, current.kind.value),
            current.line,
            current.col
        )
    return self._advance()
```

**`_is_at_end()`** — Check if we've reached EOF:
```python
def _is_at_end(self):
    return self._peek().kind == TokenKind.EOF
```

### 3.9.2 Statement Dispatching

The `_parse_statement()` method dispatches to appropriate parsers:

```python
def _parse_statement(self):
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
        raise ParseError("Unexpected '}' without matching '{'", ...)
    else:
        raise ParseError("Unexpected token: %s" % token.kind.value, ...)
```

### 3.9.3 AST to Dictionary Conversion

The public API returns dictionaries, not Python objects, for easier serialization:

```python
def _ast_to_dict(node):
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
    # ... etc for all node types
```

This conversion allows the AST to be easily inspected, serialized to JSON, or consumed by other tools.

## 3.10 Summary: Lexer and Parser Together

The SOMA lexer and parser work together to transform source code into a validated AST:

**Lexer (lexer.py):**
- Scans character by character
- Recognizes token boundaries
- Decodes string escapes
- Strips comments
- Produces flat token stream
- Reports lexical errors (invalid syntax at character level)

**Parser (parser.py):**
- Consumes token stream
- Builds hierarchical AST
- Splits paths into components
- Validates semantic rules (register syntax, modifier targets)
- Eagerly parses blocks
- Reports parse errors (invalid syntax at token/structure level)

**Design Philosophy:**

1. **Separation of concerns** — Lexer handles characters, parser handles tokens
2. **Eager validation** — Errors caught at parse time, not runtime
3. **Simple and deterministic** — No ambiguity, no backtracking
4. **Helpful errors** — Clear messages with source locations
5. **Complete AST** — All code structures represented in tree

**When to use each:**

- **Lexer alone** — If you only need tokens (e.g., syntax highlighting)
- **Parser** — For complete AST (e.g., interpretation, analysis, transformation)

**Example workflow:**

```python
from soma.parser import parse

source = """
{ 0 !_.counter
  _.counter 10 ><
  { _.counter 1 >+ !_.counter }
  >choose
}
"""

# Parse source → AST
ast = parse(source)

# ast["kind"] == "Program"
# ast["body"][0]["kind"] == "BlockNode"
# ast["body"][0]["body"][0]["kind"] == "IntNode"
# ... etc
```

The result is a complete, validated AST ready for interpretation or further analysis.
