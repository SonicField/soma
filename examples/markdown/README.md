# SOMA Markdown Extension Example

This example demonstrates all features of the SOMA markdown extension.

## Files

- **`markdown_examples.soma`** - SOMA source file that generates markdown
- **`run_example.py`** - Python launcher script
- **`output.md`** - Generated markdown output (created when you run the example)

## Running the Example

From anywhere in the project:

```bash
python3 examples/markdown/run_example.py
```

Or from within the example directory:

```bash
cd examples/markdown
python3 run_example.py
```

Both commands will create `output.md` in the `examples/markdown/` directory.

## What It Demonstrates

The example showcases all currently implemented features:

### ✅ Headings
- H1, H2, H3, and H4 heading levels
- Multi-word headings
- Multiple headings in sequence

### ✅ Paragraphs
- Basic paragraph formatting
- Multiple paragraphs with proper spacing
- Each string constant becomes a separate paragraph
- Mixed with other elements

### ✅ Inline Formatting
- **Bold text** using `>b`
- _Italic text_ using `>i`
- `Inline code` using `>c`
- [Links](https://example.com) using `>md.l`
- Composition: `(text) >b >i` → `_**text**_`
- Inline text concatenation with `>md.t`

### ✅ Lists
- **Unordered lists** (bullets)
- **Ordered lists** (numbered)
- Mixed content with headings and paragraphs

### ✅ Nested Lists (Arbitrary Depth!)
- **Two-level nesting** - Lists within lists
- **Three-level nesting** - Demonstrating arbitrary depth
- **Mixed nesting types** - UL inside OL, OL inside UL
- **Multiple nests** - Multiple nested sections at the same level

### ✅ Blockquotes
- Simple blockquotes using `>md.q`
- Multi-line blockquotes
- Perfect for callouts and quoted text

### ✅ Code Blocks
- **Without language**: `(line1) (line2) Nil >md.code`
- **With language**: `(line1) (line2) (python) >md.code`
- Supports syntax highlighting when language specified
- Multi-line strings allowed

### ✅ Tables
- **Basic tables** - Headers and rows
- **Column alignment** - Left, center, right alignment
- **Inline formatting in cells** - Bold, italic, links in table cells
- **Multiple tables** - Multiple tables in same document

### ✅ Horizontal Rules
- Section separators using `>md.hr`
- Creates `---` markdown divider

## Example SOMA Syntax

Here's a taste of what the SOMA code looks like:

```soma
(python) >use
(markdown) >use

>md.start

(My Document Title)
>md.h1

(This is a paragraph of text.)
>md.p

(You can make text ) (bold) >b ( or ) (italic) >i (!) >md.t
>md.p

(Core Features)
(Advanced Features)
>md.nest
  (Arbitrary nesting depth)
  (Mixed list types)
  >md.ol
(Extension System)
>md.ul

(Name) (Age) (Status)
>md.table.header
(Alice) (30) (Active)
>md.table.row
>md.table

>md.hr

(output.md) >md.render
```

## Output

The generated markdown file (`output.md`) is a comprehensive demonstration document that:
- Explains the markdown extension
- Shows all syntax examples
- Demonstrates nested structures
- Documents technical implementation details

## Architecture Highlights

The implementation uses several innovative patterns:

1. **Void Sentinel Pattern** - Void at bottom of AL marks end of items
2. **Nesting Stack** - Enables arbitrary depth nesting
3. **Two-Phase Rendering** - Nested formatters add to parent context, outer formatters render everything
4. **Generic Nesting** - `>md.nest` doesn't know list type, making it truly generic
5. **Stack-Based Composition** - Inline formatters naturally compose: `(text) >b >i` → `_**text**_`
6. **Column-Width-Aware Tables** - Automatically calculates widths for readable output

## Test Coverage

All features demonstrated in this example are covered by the test suite:
- **38 total tests** (100% passing)
- 5 comprehensive nesting tests
- 7 inline formatting tests (including inline code)
- 5 table tests
- 2 blockquote tests
- 3 code block tests
- 2 horizontal rule tests
- TDD approach throughout development

See `tests/test_markdown_extension.py` for complete test coverage.
