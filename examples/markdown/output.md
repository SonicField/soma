# SOMA Markdown Extension Demo

This document was generated using the SOMA markdown extension.
It demonstrates all currently implemented features including headings,
paragraphs, lists, and nested lists with arbitrary depth.

Each string constant passed to >md.p becomes a separate paragraph,
making it easy to structure your document naturally.

## Heading Levels

The markdown extension supports multiple heading levels.

### H3 Example

This is a level 3 heading, useful for subsections.

#### H4 Example

This is a level 4 heading, useful for detailed technical sections.

## Paragraphs

Paragraphs are the basic text blocks in markdown.
They automatically get proper spacing with double newlines.

You can have multiple paragraphs in a document.
Each one is separated for readability.

Notice how we can pass multiple string constants to a single >md.p call,
and each becomes its own paragraph with proper spacing!

## Inline Formatting

SOMA supports inline formatting through simple composition.

### Bold and Italic

You can make text **bold** or _italic_ using >b and >i formatters.

Composition works beautifully: _**bold and italic**_ text!

### Links

Creating links is straightforward: [click here](https://example.com)!

You can even compose links with other formatting: _[an italic link](https://github.com/soma-lang)_.

### Mixed Formatting

Everything composes: **bold**, _italic_, `code`, and [a link](https://soma-lang.org) in one paragraph!

You can use `inline code` to reference `variable names` or `function calls` in text.

## Lists

### Simple Unordered Lists

Here are some features of the SOMA markdown extension:

- State machine based architecture
- Pure SOMA implementation with Python FFI
- Void sentinel pattern for clean syntax
- Test-driven development approach

### Simple Ordered Lists

Implementation stages completed:

1. Stage 1: Basic Infrastructure
2. Stage 2: Simple Headings
3. Stage 3: Paragraphs
4. Stage 4: Simple Lists
5. Stage 5: Nesting Infrastructure
6. Stage 6: Inline Formatting

## Nested Lists

### Two-Level Nesting

The extension supports arbitrary nesting depth.
Here's an example with unordered outer and ordered inner:

- Core Features
- Advanced Features
  1. Arbitrary nesting depth
  2. Mixed list types
  3. Clean syntax
- Extension System

### Mixed Nesting Types

You can mix ordered and unordered lists at any level:

1. Setup markdown extension
2. Write your content
  - Add headings
  - Add paragraphs
  - Add lists
3. Render to file

### Three-Level Nesting

The nesting stack supports arbitrary depth. Here's a three-level example:

1. Project Structure
  - Core Components
    - VM and Parser
    - Store and Stack
    - Extensions
  - Test Suite
2. Documentation

### Multiple Nested Sections

You can have multiple nested sections in the same list:

- Frontend
  - React components
  - State management
- Backend
  - API endpoints
  - Database layer
- Testing

## Tables

### Basic Tables

Tables organize data into rows and columns using simple syntax:

| Name  | Age | Role     |
|-------|-----|----------|
| Alice | 30  | Engineer |
| Bob   | 25  | Designer |
| Carol | 28  | Manager  |

### Tables with Alignment

You can specify column alignment using alignment markers:

| Feature     | Status   | Priority |
|:------------|:--------:|---------:|
| Tables      | Complete | High     |
| Nesting     | Complete | High     |
| Code blocks | Planned  | Medium   |

### Tables with Inline Formatting

Table cells can contain inline formatting:

| Item     | Description              | Link                                 |
|----------|--------------------------|--------------------------------------|
| SOMA     | **Stack-based language** | [repo](https://github.com/soma-lang) |
| Markdown | _Document generation_    | [docs](https://example.com/docs)     |

## Blockquotes

### Simple Blockquote

Blockquotes are great for highlighting important information:

> This is a notable quote or important callout.

### Multi-line Blockquotes

You can create longer blockquotes with multiple lines:

> The SOMA markdown extension makes document generation simple.
> Each line becomes part of the same blockquote block.
> Perfect for extended quotes or callouts.

## Code Blocks

### Code Without Language

For generic code snippets without syntax highlighting:

```
function greet
  echo Hello World
```

### Code With Language

Specify the language for proper syntax highlighting:

```ruby
def fibonacci n
  return 1 if n <= 1
  fibonacci n-1 plus fibonacci n-2
```

Another example in Python:

```python
def factorial n
  return 1 if n == 0 else n times factorial n-1
```

---

## Technical Implementation

### Architecture

The implementation uses several key patterns:

1. Void Sentinel Pattern
  - Void at bottom of AL marks end of items
  - Enables clean draining without explicit terminators
2. Nesting Stack
  - Each context contains items, depth, and nested text
  - Supports arbitrary nesting depth
3. Two-Phase Rendering
  - Nested formatters add to parent context
  - Outer formatters render everything

### Test Coverage

The extension has comprehensive test coverage:

- 38 total tests passing
- 5 table tests covering all table features
- 7 inline formatting tests including inline code
- 5 nesting tests covering complex scenarios
- 2 blockquote tests
- 3 code block tests with and without language
- 2 horizontal rule tests
- 100% of implemented features tested
- TDD approach throughout development

## Summary

This document demonstrates all features of the SOMA markdown extension.
The syntax is lightweight and readable while remaining pure SOMA code.
The extension supports headings, paragraphs, lists with arbitrary nesting,
inline formatting including code, blockquotes, code blocks with syntax highlighting,
tables with alignment, and horizontal rules - everything needed for rich technical documentation.

