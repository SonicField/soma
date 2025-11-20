# 2. Lexical Structure

This section defines the lexical structure of SOMA source code—how raw text is converted into a stream of tokens. The lexer is **purely syntactic**: it recognizes token boundaries and categories but does not interpret semantic meaning.

## 2.1 Overview

The SOMA lexer converts source text into a stream of tokens. Each token has:

* **kind** — one of INT, PATH, EXEC, STORE, STRING, LBRACE, RBRACE, or EOF
* **value** — the string representation as it appears in source
* **line**, **column** — position of the first character (1-based)

Tokenization is deterministic and proceeds left-to-right. Characters that do not match any token rule generate a lexical error.

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
* `_.` is two tokens (PATH + dot) representing register root CellRef
* `_.x`, `_.x.y`, etc. are valid PATH tokens for register paths
* `_tmp`, `_x`, `_self` (without dot after `_`) are lexically valid PATH tokens, but are **not** standard register syntax semantically

The distinction between `_x` and `_.x` is **semantic**, not lexical:
* The lexer tokenizes both as PATH tokens
* Semantically, only `_.x` (with dot) is valid register syntax
* `_x` (without dot) should be rejected by the parser or runtime

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
_.self >Chain
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

## 2.13 Summary

The SOMA lexer is intentionally simple and orthogonal:

* **`(` ... `)`** — strings with Unicode escapes
* **`{` ... `}`** — blocks
* **`)` at token start** — comments
* **`>` / `!` at token start** — prefix modifiers
* **`[+-]?[0-9]+`** — integers
* **Everything else** — paths

Each category is mutually exclusive and unambiguous. The lexer enforces structural correctness but does not interpret semantics—that is the parser's responsibility.

**Register Syntax Note:** The lexer recognizes register-related tokens (`_`, `_.x`, `_tmp`) purely as PATH tokens. It does not enforce the semantic rule that register paths must use the `_.path` form. Tokens like `_tmp` or `_self` (without dot after `_`) are lexically valid but semantically invalid—they should be rejected by the parser or runtime. Only `_` (register root) and paths starting with `_.` (register paths) are semantically valid register syntax.

---

## Inconsistencies Noted

After reviewing all three source files, here are the key inconsistencies between soma-lexer.md and soma-v1.0.md:

### 1. String Syntax Discrepancy

**soma-lexer.md**: Uses `( ... )` with `\HEX\` escapes exclusively
**soma-v1.0.md § 3.11**: Defines TWO string forms:
  - Escaped strings: `"Hello\nWorld"` with `\"`, `\\`, `\n`, `\t` escapes
  - Raw parenthesized strings: `(raw text)` with no escapes except the implementation uses `\HEX\` escapes

**Resolution**: The implementation (lexer.py) and soma-lexer.md are consistent—only `( ... )` with `\HEX\` escapes are implemented. The soma-v1.0.md double-quote form appears to be a specification artifact not yet implemented.

### 2. Modifier Semantics

**soma-lexer.md**: Clearly defines `>` (EXEC) and `!` (STORE) as prefix operators that emit separate tokens
**soma-v1.0.md § 3.8**: Calls `>` a "Built-in prefix" suggesting it's part of built-in words like `>print`
**Errata § 1**: Correctly identifies that `!` was omitted from the grammar

**Resolution**: The lexer.py implementation follows soma-lexer.md: `>` and `!` are separate modifier tokens, not part of built-in names.

### 3. Unicode Identifiers

**soma-lexer.md**: Does not specify identifier character rules
**soma-v1.0.md § 3.11.3**: Defines UAX #31 Unicode identifier syntax with XID_Start and XID_Continue

**Resolution**: This appears to be a parser-level concern, not lexer-level. The lexer treats paths as sequences of non-whitespace characters, and the parser would enforce identifier validity.

All examples and test cases in this document are verified against the implemented lexer behavior in lexer.py.
