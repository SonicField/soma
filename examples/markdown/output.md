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

Everything composes: **bold**, _italic_, and [a link](https://soma-lang.org) in one paragraph!

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

- 17 total tests passing
- 5 nesting tests covering complex scenarios
- 100% of implemented features tested
- TDD approach throughout development

## Summary

This document demonstrates all features of the SOMA markdown extension.
The syntax is lightweight and readable while remaining pure SOMA code.
The nesting stack architecture enables arbitrary depth nesting with mixed list types,
making it suitable for complex document structures.

Next steps include additional block elements like code blocks,
blockquotes, and horizontal rules.

