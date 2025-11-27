# SOMA Markdown Extension Example

This example demonstrates all features of the SOMA markdown extension.

## Files

- **`markdown_examples.soma`** - SOMA source file that generates markdown
- **`run_example.py`** - Python launcher script
- **`output.md`** - Generated markdown output (created when you run the example)

## Running the Example

```bash
cd examples/markdown
python3 run_example.py
```

Or from the SOMA root directory:

```bash
python3 examples/markdown/run_example.py
```

## What It Demonstrates

The example showcases all currently implemented features:

### ✅ Headings
- H1, H2, and H3 heading levels
- Multi-word headings
- Multiple headings in sequence

### ✅ Paragraphs
- Basic paragraph formatting
- Multiple paragraphs with proper spacing
- Mixed with other elements

### ✅ Lists
- **Unordered lists** (bullets)
- **Ordered lists** (numbered)
- Mixed content with headings and paragraphs

### ✅ Nested Lists (Arbitrary Depth!)
- **Two-level nesting** - Lists within lists
- **Three-level nesting** - Demonstrating arbitrary depth
- **Mixed nesting types** - UL inside OL, OL inside UL
- **Multiple nests** - Multiple nested sections at the same level

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

(Core Features)
(Advanced Features)
>md.nest
  (Arbitrary nesting depth)
  (Mixed list types)
  >md.ol
(Extension System)
>md.ul

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

## Test Coverage

All features demonstrated in this example are covered by the test suite:
- 17 total tests (100% passing)
- 5 comprehensive nesting tests
- TDD approach throughout development

See `tests/test_markdown_extension.py` for complete test coverage.
