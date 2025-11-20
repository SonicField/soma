# **SOMA Lexer Specification**

*Version 1.0 — matches implementation & tests as of 2025-11-20*

This document defines the lexical structure of SOMA source code. It describes the token categories, structural punctuation, prefix modifiers, string literals, comments, whitespace rules, and error conditions.

The lexer is **purely syntactic**: it does not interpret semantics such as the operational meaning of blocks, paths, or numbers.

---

# **1. Overview**

The SOMA lexer converts a source text into a stream of tokens, each with:

* **kind** (enumeration from `TokenKind`)
* **value** (string representation)
* **line**, **column** of first character (1-based)

Tokenization is deterministic and left-to-right.

Characters not covered by a token rule generate a `LexError`.

---

# **2. Token Categories**

| Token Kind | Description                          | Example             |
| ---------- | ------------------------------------ | ------------------- |
| `INT`      | Decimal integer (signed or unsigned) | `42`, `-7`, `+9`    |
| `PATH`     | General identifier / name            | `foo`, `x>y`, `a!b` |
| `EXEC`     | Prefix modifier `>`                  | `>dog`, `> { ... }` |
| `STORE`    | Prefix modifier `!`                  | `!x`, `!!z`         |
| `STRING`   | String literal `( … )`               | `(hello)`, `(\41\)` |
| `LBRACE`   | Block start `{`                      | `{`                 |
| `RBRACE`   | Block end `}`                        | `}`                 |
| `EOF`      | End-of-file marker                   | *none*              |

All tokens (except `EOF`) correspond to explicit characters in the source.

---

# **3. Whitespace**

Whitespace characters:

* ASCII space (`U+0020`)
* tab (`U+0009`)
* line feed (`\n`)
* carriage return (`\r`)
* CRLF (`\r\n`) is treated as a single line terminator

Whitespace **separates tokens** but is otherwise ignored.

Column/line tracking follows the usual rules:

* `\n` advances line++, resets col=1
* `\r` followed by `\n` counts as one newline
* bare `\r` also ends the line

---

# **4. Comments**

A **comment** is introduced by a bare `)` at the **start of a token** (i.e. immediately after whitespace or at column 1), *outside any string literal*.

Grammar:

```
COMMENT ::= ')' <any characters until line terminator or EOF>
```

Rules:

* The initial `)` and all characters until `\n`, `\r`, `\r\n`, or EOF are ignored.
* Ending the file is a valid termination for a comment.
* Comments do **not** emit tokens.
* Inside a string literal `( … )`, `)` is *not* a comment introducer; it closes the string.
* A `)` appearing **in the middle of a PATH** does not start a comment.

Examples:

```
) full line comment
>foo ) trailing comment
{ >a
  ) inner comment inside block
  >b
}
```

---

# **5. Strings**

String literals use parentheses:

```
STRING ::= '(' STRING_CONTENT ')'
```

Inside a string:

* Any character except `)` and backslash is literal.
* `)` closes the string.
* Backslash (`\`) starts a **Unicode escape**:

### 5.1. Unicode escape: `\HEX\`

```
ESCAPE ::= '\' HEXDIGITS '\'
HEXDIGITS ::= one or more [0–9A–Fa–f]
```

Meaning:

* The hex number is decoded using `int(hex, 16)`.
* The Unicode `chr()` of that codepoint is appended to the string.
* Empty escapes `\\` are illegal.
* Non-hex digits raise a lexical error.
* Escapes do **not** overlap: each escape is independent and must be written separately.

Examples:

| SOMA Source      | Meaning               |
| ---------------- | --------------------- |
| `(\41\)`         | `"A"`                 |
| `(Hello\d\)`     | `"Hello" + chr(0x0D)` |
| `(\\5C\\)`       | `"\\"`                |
| `(\41\\42\\43\)` | `"ABC"`               |

Error cases:

* `(hello` → unterminated
* `(hello\5C` → unterminated escape
* `(\g\)` → invalid hex
* `(\\)` → empty escape

---

# **6. Blocks**

Blocks are introduced by `{` and terminated by `}`.

```
BLOCK ::= '{' ... '}'
```

These are lexical tokens:

* `{` → `LBRACE`
* `}` → `RBRACE`

Blocks cannot begin with prefix modifiers:

* `!{...}` → **LexError**
* `>{...}` → valid (`EXEC`, then `LBRACE`)

Blocks may contain nested blocks.

---

# **7. Prefix Modifiers**

SOMA has **two prefix operators** that attach only to certain token types:

### 7.1 `>` — EXEC (execute)

`>` at the start of a token means:

```
EXEC <target>
```

Where `<target>` is either:

* a PATH name, or
* a block `{…}`

Examples:

| Source    | Tokens                          |
| --------- | ------------------------------- |
| `>foo`    | EXEC, PATH("foo")               |
| `>{a}`    | EXEC, LBRACE, PATH("a"), RBRACE |
| `> (foo)` | PATH(">"), STRING("foo")        |
| `(foo)`   | STRING                          |

Illegal:

* `>(foo)` → cannot EXEC a string literal
* `>!dog` → PATH(">"), STORE("!"), PATH("dog") (not EXEC)

### 7.2 `!` — STORE

`!` attaches only to a PATH:

| Source | Meaning                |
| ------ | ---------------------- |
| `!x`   | STORE("!"), PATH("x")  |
| `!!y`  | STORE("!"), PATH("!y") |

Illegal:

* `!{a}` — cannot store into a block
* `!(foo)` — cannot store into a string literal
* `!>foo` — cannot store into EXEC

### Detection rules:

* If the `>` or `!` appears at **token start**, it may be a modifier.
* If it appears **inside a PATH**, it is just a character:

  * `a>b` → PATH("a>b")
  * `x!y` → PATH("x!y")

The lexer distinguishes this based on whether we are in “token-start position”.

---

# **8. Integers**

Integers follow:

```
INT ::= [ '+' | '-' ] DIGITS
DIGITS ::= [0–9]+
```

Rules:

* Leading sign is optional.
* A leading `+` or `-` **must** be followed by a digit to count as an integer.
* Otherwise it begins a PATH:

  * `+foo` → PATH("+foo")
  * `-bar` → PATH("-bar")
* Illegal combinations:

  * `23a` → LexError
  * `23-5` → LexError
  * `23,5` → LexError

Examples:

```
23       → INT(23)
+23      → INT(+23)
-23      → INT(-23)
+hello   → PATH("+hello")
-foo     → PATH("-foo")
```

---

# **9. Paths**

A path is:

```
PATH ::= any non-whitespace printable sequence
         excluding: '{', '}', '(' at start,
         and excluding ')' at start (comment introducer)
         and excluding integers and prefix-modifier forms.
```

Key details:

* May contain `>`, `!`, `,`, `:`, `.` or any other printable characters.
* A PATH ends when:

  * whitespace is reached,
  * `{` or `}` is reached,
  * the beginning of a string (`(`),
  * the beginning of a comment (`)`),
  * or we would otherwise begin a structurally distinct token.

Examples:

```
foo
dog-3
x!y
a>b
concat>
```

---

# **10. Error conditions**

The lexer raises a `LexError` on:

* Invalid numeric literals.
* Attachments of modifiers to illegal targets:

  * `!(foo)`
  * `>(foo)`
  * `!{block}`
* Unterminated strings.
* Invalid `\HEX\` escapes.
* `)` inside a string literal (only allowed as string terminator).
* Any unexpected or illogical punctuation sequence not matching a rule.

---

# **11. Summary**

The SOMA lexer is intentionally simple, consistent, and orthogonal:

* **`(` … `)`**: strings
* **`{` … `}`**: blocks
* **`)` at token start**: comment
* **`>` / `!` at token start**: prefix modifiers
* otherwise: **integers or PATHs**

Each category is mutually exclusive, unambiguous, and test-driven.

