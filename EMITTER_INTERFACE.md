# Emitter Interface Specification

## Overview

This document defines the complete interface contract for emitters in the SOMA markdown extension. All emitters (MarkdownEmitter, HtmlEmitter, etc.) must implement these methods to be compatible with the markdown extension builtins.

**Design Principles:**
- **Display over semantics**: Use `<b>`, `<i>`, `<code>` not `<strong>`, `<em>`, `<kbd>`
- **Minimal interface**: Only operations currently supported by markdown extension
- **State transformers**: Methods accept inputs and return strings (no internal state mutation)
- **Consistent output**: Each method documents exact expected output format

---

## Method Categories

1. **Inline Formatting** - Wrap text with formatting markers
2. **Block Elements** - Headings, paragraphs, blockquotes, horizontal rules
3. **Lists** - Ordered and unordered lists (including nested)
4. **Code** - Inline code and code blocks
5. **Links** - Hyperlinks
6. **Tables** - Complete table rendering
7. **Special** - Text concatenation and joining operations

---

## 1. Inline Formatting Methods

### `bold(text: str) -> str`

Wraps text in bold formatting.

**Parameters:**
- `text`: The text to make bold

**Returns:** String with bold formatting

**Markdown Example:**
```python
emitter.bold("hello")
# Returns: "**hello**"
```

**HTML Example:**
```python
emitter.bold("hello")
# Returns: "<b>hello</b>"
```

---

### `italic(text: str) -> str`

Wraps text in italic formatting.

**Parameters:**
- `text`: The text to italicize

**Returns:** String with italic formatting

**Markdown Example:**
```python
emitter.italic("hello")
# Returns: "_hello_"
```

**HTML Example:**
```python
emitter.italic("hello")
# Returns: "<i>hello</i>"
```

---

### `code(text: str) -> str`

Wraps text in inline code formatting.

**Parameters:**
- `text`: The text to format as code

**Returns:** String with inline code formatting

**Markdown Example:**
```python
emitter.code("x = 42")
# Returns: "`x = 42`"
```

**HTML Example:**
```python
emitter.code("x = 42")
# Returns: "<code>x = 42</code>"
```

---

### `link(text: str, url: str) -> str`

Creates a hyperlink.

**Parameters:**
- `text`: The link text to display
- `url`: The URL to link to

**Returns:** String with link formatting

**Markdown Example:**
```python
emitter.link("Google", "https://google.com")
# Returns: "[Google](https://google.com)"
```

**HTML Example:**
```python
emitter.link("Google", "https://google.com")
# Returns: '<a href="https://google.com">Google</a>'
```

---

## 2. Block Elements

### `heading1(text: str) -> str`

Creates a level 1 heading.

**Parameters:**
- `text`: The heading text

**Returns:** String with heading formatting and trailing blank line

**Markdown Example:**
```python
emitter.heading1("Title")
# Returns: "# Title\n\n"
```

**HTML Example:**
```python
emitter.heading1("Title")
# Returns: "<h1>Title</h1>\n"
```

---

### `heading2(text: str) -> str`

Creates a level 2 heading.

**Parameters:**
- `text`: The heading text

**Returns:** String with heading formatting and trailing blank line

**Markdown Example:**
```python
emitter.heading2("Section")
# Returns: "## Section\n\n"
```

**HTML Example:**
```python
emitter.heading2("Section")
# Returns: "<h2>Section</h2>\n"
```

---

### `heading3(text: str) -> str`

Creates a level 3 heading.

**Parameters:**
- `text`: The heading text

**Returns:** String with heading formatting and trailing blank line

**Markdown Example:**
```python
emitter.heading3("Subsection")
# Returns: "### Subsection\n\n"
```

**HTML Example:**
```python
emitter.heading3("Subsection")
# Returns: "<h3>Subsection</h3>\n"
```

---

### `heading4(text: str) -> str`

Creates a level 4 heading.

**Parameters:**
- `text`: The heading text

**Returns:** String with heading formatting and trailing blank line

**Markdown Example:**
```python
emitter.heading4("Detail")
# Returns: "#### Detail\n\n"
```

**HTML Example:**
```python
emitter.heading4("Detail")
# Returns: "<h4>Detail</h4>\n"
```

---

### `paragraph(items: List[str]) -> str`

Formats multiple items as separate paragraphs.

**Parameters:**
- `items`: List of paragraph text strings

**Returns:** String with each item as a separate paragraph, each followed by blank line

**Markdown Example:**
```python
emitter.paragraph(["First para", "Second para"])
# Returns: "First para\n\nSecond para\n\n"
```

**HTML Example:**
```python
emitter.paragraph(["First para", "Second para"])
# Returns: "<p>First para</p>\n<p>Second para</p>\n"
```

---

### `blockquote(items: List[str]) -> str`

Formats multiple items as blockquote lines.

**Parameters:**
- `items`: List of quote line strings

**Returns:** String with blockquote formatting and trailing blank line

**Markdown Example:**
```python
emitter.blockquote(["Line 1", "Line 2"])
# Returns: "> Line 1\n> Line 2\n\n"
```

**HTML Example:**
```python
emitter.blockquote(["Line 1", "Line 2"])
# Returns: "<blockquote>\n<p>Line 1</p>\n<p>Line 2</p>\n</blockquote>\n"
```

**Note:** HTML version wraps each line in `<p>` tags for semantic correctness.

---

### `horizontal_rule() -> str`

Creates a horizontal rule/divider.

**Parameters:** None

**Returns:** String with horizontal rule and trailing blank line

**Markdown Example:**
```python
emitter.horizontal_rule()
# Returns: "---\n\n"
```

**HTML Example:**
```python
emitter.horizontal_rule()
# Returns: "<hr>\n"
```

---

## 3. Lists

### `unordered_list(items: List[str], depth: int = 0) -> str`

Formats items as an unordered list at the specified depth.

**Parameters:**
- `items`: List of item strings (may contain already-formatted nested lists)
- `depth`: Nesting depth (0 = top level, 1 = nested once, etc.)

**Returns:** String with unordered list formatting and trailing blank line (at depth 0 only)

**Markdown Example:**
```python
emitter.unordered_list(["Item 1", "Item 2"], depth=0)
# Returns: "- Item 1\n- Item 2\n\n"

emitter.unordered_list(["Nested A", "Nested B"], depth=1)
# Returns: "  - Nested A\n  - Nested B\n"  # No trailing blank line
```

**HTML Example:**
```python
emitter.unordered_list(["Item 1", "Item 2"], depth=0)
# Returns: "<ul>\n<li>Item 1</li>\n<li>Item 2</li>\n</ul>\n"

# Nested lists in HTML are embedded within <li> tags by the caller
emitter.unordered_list(["Nested A", "Nested B"], depth=1)
# Returns: "<ul>\n<li>Nested A</li>\n<li>Nested B</li>\n</ul>\n"
```

**Notes:**
- Depth controls indentation in markdown (2 spaces per level)
- Blank line only added at depth 0 in markdown
- HTML nesting handled by structure, not depth parameter

---

### `ordered_list(items: List[str], depth: int = 0) -> str`

Formats items as an ordered list at the specified depth.

**Parameters:**
- `items`: List of item strings (may contain already-formatted nested lists)
- `depth`: Nesting depth (0 = top level, 1 = nested once, etc.)

**Returns:** String with ordered list formatting and trailing blank line (at depth 0 only)

**Markdown Example:**
```python
emitter.ordered_list(["First", "Second"], depth=0)
# Returns: "1. First\n2. Second\n\n"

emitter.ordered_list(["Nested 1", "Nested 2"], depth=1)
# Returns: "  1. Nested 1\n  2. Nested 2\n"  # No trailing blank line
```

**HTML Example:**
```python
emitter.ordered_list(["First", "Second"], depth=0)
# Returns: "<ol>\n<li>First</li>\n<li>Second</li>\n</ol>\n"

emitter.ordered_list(["Nested 1", "Nested 2"], depth=1)
# Returns: "<ol>\n<li>Nested 1</li>\n<li>Nested 2</li>\n</ol>\n"
```

**Notes:**
- Markdown numbers sequentially (1., 2., 3., ...)
- Depth controls indentation in markdown (2 spaces per level)
- Blank line only added at depth 0 in markdown
- HTML uses `<ol>` with automatic numbering

---

### `list_item_formatted(label: str, value: str) -> str`

Formats a definition-style list item with bold label and value.

**Parameters:**
- `label`: The label/term to bold
- `value`: The value/definition

**Returns:** String formatted as "**label**: value"

**Markdown Example:**
```python
emitter.list_item_formatted("Name", "Alice")
# Returns: "**Name**: Alice"
```

**HTML Example:**
```python
emitter.list_item_formatted("Name", "Alice")
# Returns: "<b>Name</b>: Alice"
```

**Notes:**
- This is used by `>md.dl` to create definition list items
- Output is meant to be passed to `unordered_list()` or `ordered_list()`
- Not a complete list element on its own

---

## 4. Code

### `code_block(lines: List[str], language: str = None) -> str`

Formats lines as a code block with optional syntax highlighting language.

**Parameters:**
- `lines`: List of code line strings
- `language`: Optional language identifier (e.g., "python", "javascript")

**Returns:** String with code block formatting and trailing blank line

**Markdown Example:**
```python
emitter.code_block(["def hello():", "    print('hi')"], language="python")
# Returns: "```python\ndef hello():\n    print('hi')\n```\n\n"

emitter.code_block(["plain text"], language=None)
# Returns: "```\nplain text\n```\n\n"
```

**HTML Example:**
```python
emitter.code_block(["def hello():", "    print('hi')"], language="python")
# Returns: '<pre><code class="language-python">def hello():\n    print(\'hi\')\n</code></pre>\n'

emitter.code_block(["plain text"], language=None)
# Returns: "<pre><code>plain text\n</code></pre>\n"
```

**Notes:**
- Language can be `None`, empty string, or language identifier
- Each line ends with newline in output
- HTML uses `class="language-{lang}"` for syntax highlighting support

---

## 5. Special Operations

### `concat(items: List[str]) -> str`

Concatenates items into a single string with no separator.

**Parameters:**
- `items`: List of strings to concatenate

**Returns:** Single concatenated string

**Markdown Example:**
```python
emitter.concat(["Hello", " ", "world"])
# Returns: "Hello world"
```

**HTML Example:**
```python
emitter.concat(["Hello", " ", "world"])
# Returns: "Hello world"
```

**Notes:**
- Used by `>md.t` for inline text joining
- Identical behavior in markdown and HTML
- No formatting added

---

### `join(items: List[str], separator: str) -> str`

Joins items with a separator.

**Parameters:**
- `items`: List of strings to join
- `separator`: String to insert between items

**Returns:** Single joined string

**Markdown Example:**
```python
emitter.join(["a", "b", "c"], separator=", ")
# Returns: "a, b, c"
```

**HTML Example:**
```python
emitter.join(["a", "b", "c"], separator=", ")
# Returns: "a, b, c"
```

**Notes:**
- Used internally for text operations
- Identical behavior in markdown and HTML
- No formatting added

---

## 6. Tables

### `table(header: List[str], rows: List[List[str]], alignment: List[str] = None) -> str`

Renders a complete table with header, rows, and optional column alignment.

**Parameters:**
- `header`: List of header cell strings
- `rows`: List of row lists (each row is a list of cell strings)
- `alignment`: Optional list of alignment specifiers per column
  - Valid values: `"left"`, `"centre"`, `"right"`, or `None`
  - `None` or missing entries default to no alignment

**Returns:** String with complete table formatting and trailing blank line

**Markdown Example:**
```python
emitter.table(
    header=["Name", "Age"],
    rows=[["Alice", "30"], ["Bob", "25"]],
    alignment=None
)
# Returns:
# | Name  | Age |
# |-------|-----|
# | Alice | 30  |
# | Bob   | 25  |
#
# (with proper spacing and trailing blank line)

emitter.table(
    header=["Left", "Center", "Right"],
    rows=[["A", "B", "C"]],
    alignment=["left", "centre", "right"]
)
# Returns:
# | Left | Center | Right |
# |:-----|:------:|------:|
# | A    | B      | C     |
#
```

**HTML Example:**
```python
emitter.table(
    header=["Name", "Age"],
    rows=[["Alice", "30"], ["Bob", "25"]],
    alignment=None
)
# Returns:
# <table>
# <thead>
# <tr><th>Name</th><th>Age</th></tr>
# </thead>
# <tbody>
# <tr><td>Alice</td><td>30</td></tr>
# <tr><td>Bob</td><td>25</td></tr>
# </tbody>
# </table>
#

emitter.table(
    header=["Left", "Center", "Right"],
    rows=[["A", "B", "C"]],
    alignment=["left", "centre", "right"]
)
# Returns:
# <table>
# <thead>
# <tr><th style="text-align: left">Left</th><th style="text-align: center">Center</th><th style="text-align: right">Right</th></tr>
# </thead>
# <tbody>
# <tr><td style="text-align: left">A</td><td style="text-align: center">B</td><td style="text-align: right">C</td></tr>
# </tbody>
# </table>
#
```

**Notes:**
- Markdown calculates column widths for proper alignment
- Markdown alignment uses `:---`, `:---:`, `---:` markers
- HTML uses `text-align` CSS styles for alignment
- Blank line added after table

---

## 7. Advanced Operations

### `data_title(items: List[str]) -> str`

Formats alternating items with bold (for data title pattern).

**Parameters:**
- `items`: List of strings (must be even count)
- Items at even indices (0, 2, 4...) are bolded
- Items at odd indices (1, 3, 5...) are plain

**Returns:** Single string with alternating bold formatting, items joined with spaces

**Markdown Example:**
```python
emitter.data_title(["Name", "Alice", "Age", "30"])
# Returns: "**Name** Alice **Age** 30"
```

**HTML Example:**
```python
emitter.data_title(["Name", "Alice", "Age", "30"])
# Returns: "<b>Name</b> Alice <b>Age</b> 30"
```

**Notes:**
- Used by `>md.dt` builtin
- Requires even number of items (pairs)
- Items joined with single space

---

## Implementation Notes

### List Nesting Complexity

The markdown extension handles list nesting through a complex state machine in the Python builtins (`drain_and_format_ul_builtin` and `drain_and_format_ol_builtin`). The emitter methods receive:

1. **Simple case**: `items` at `depth=0` for top-level lists
2. **Nested case**: The builtin manages the nesting context and calls the emitter method multiple times, once per nesting level

**Key behaviors:**
- `depth=0`: Add trailing blank line after list
- `depth>0`: No trailing blank line (nested within parent)
- Markdown indents with 2 spaces per depth level
- HTML nesting uses nested `<ul>`/`<ol>` tags (handled by caller structure)

### Placeholder System

The markdown extension uses `OliPlaceholder` and `UliPlaceholder` objects for accumulating list items built with `>md.oli` and `>md.uli`. These are **internal to the builtin layer** and:

- **Never passed to emitter methods** - builtins resolve them first
- Emitters only receive final string values
- Validation happens in builtins before emitter methods are called

### Empty Values

Methods should handle empty inputs gracefully:
- Empty list `[]` returns empty string `""`
- `None` or missing optional parameters use defaults
- Empty strings `""` are valid inputs and preserved

### Character Escaping (HTML Only)

HTML emitters must escape special characters:
- `&` → `&amp;`
- `<` → `&lt;`
- `>` → `&gt;`
- `"` → `&quot;` (in attributes)

Markdown emitters do NOT escape (markdown is the source format).

---

## Emitter Method Summary

| Method | Category | Parameters | Returns |
|--------|----------|------------|---------|
| `bold(text)` | Inline | `text: str` | `str` |
| `italic(text)` | Inline | `text: str` | `str` |
| `code(text)` | Inline | `text: str` | `str` |
| `link(text, url)` | Inline | `text: str, url: str` | `str` |
| `heading1(text)` | Block | `text: str` | `str` |
| `heading2(text)` | Block | `text: str` | `str` |
| `heading3(text)` | Block | `text: str` | `str` |
| `heading4(text)` | Block | `text: str` | `str` |
| `paragraph(items)` | Block | `items: List[str]` | `str` |
| `blockquote(items)` | Block | `items: List[str]` | `str` |
| `horizontal_rule()` | Block | None | `str` |
| `unordered_list(items, depth)` | List | `items: List[str], depth: int = 0` | `str` |
| `ordered_list(items, depth)` | List | `items: List[str], depth: int = 0` | `str` |
| `list_item_formatted(label, value)` | List | `label: str, value: str` | `str` |
| `code_block(lines, language)` | Code | `lines: List[str], language: str = None` | `str` |
| `concat(items)` | Special | `items: List[str]` | `str` |
| `join(items, separator)` | Special | `items: List[str], separator: str` | `str` |
| `data_title(items)` | Special | `items: List[str]` | `str` |
| `table(header, rows, alignment)` | Table | `header: List[str], rows: List[List[str]], alignment: List[str] = None` | `str` |

**Total Methods: 18**

---

## Edge Cases and Considerations

### 1. Newline Handling
- Block elements (headings, paragraphs, lists) include newlines in output
- Inline elements (bold, italic, code, links) do NOT include newlines
- Consistency: markdown adds `\n\n` after blocks, HTML adds `\n` after blocks

### 2. Depth and Nesting
- Only `unordered_list` and `ordered_list` accept `depth` parameter
- Other methods are depth-agnostic
- Nesting logic lives in builtins, not emitters

### 3. Table Column Width (Markdown Only)
- Markdown tables calculate column widths for visual alignment
- HTML tables use CSS/browser rendering for width
- Both support alignment specifications

### 4. Language Identifiers
- Code blocks accept any string as language identifier
- `None` or `""` means no language specification
- Markdown uses triple backtick with language
- HTML uses `class="language-{lang}"` convention

### 5. Definition Lists
- `list_item_formatted()` creates the formatted item string
- Actual list rendering uses `unordered_list()` or `ordered_list()`
- Example: `>md.dl` transforms pairs then passes to list renderer

### 6. Multiple Paragraphs vs Single Paragraph
- `paragraph(["A", "B"])` creates TWO paragraphs
- Each string in the list becomes a separate paragraph
- Not a multi-line single paragraph

### 7. Blockquote Lines
- Each item in `blockquote(items)` is a separate line
- Markdown prefixes each with `> `
- HTML wraps each in `<p>` tags within `<blockquote>`

---

## Compatibility Requirements

Any emitter implementation must:

1. **Implement all 18 methods** with exact signatures
2. **Return strings** (never None, never mutate state)
3. **Handle empty inputs** gracefully (return `""` for empty lists)
4. **Support optional parameters** with documented defaults
5. **Produce valid output** for the target format (markdown syntax or HTML syntax)
6. **Be stateless** (methods can be called in any order, multiple times)

---

## Testing Strategy

Each emitter implementation should be tested for:

1. **Basic functionality** - Each method produces correct output
2. **Edge cases** - Empty inputs, None values, single items
3. **Nesting** - Lists at various depths
4. **Special characters** - HTML escaping (HTML emitter only)
5. **Round-trip compatibility** - Markdown → HTML produces equivalent semantics
6. **Integration** - Works with actual markdown extension builtins

**Next Steps:**
- Step 2: Write MarkdownEmitter tests (18 tests)
- Step 3: Implement MarkdownEmitter class
- Step 6: Write HtmlEmitter tests (19 tests, includes escaping)
- Step 7: Implement HtmlEmitter class
