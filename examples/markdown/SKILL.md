# SOMA Markdown Extension - AI Assistant Skill Guide

This guide teaches AI assistants how to help users write markdown documents using the SOMA markdown extension.

## Prerequisites

**Assumed Knowledge:**
- You understand markdown syntax (headings, lists, tables, etc.)
- User wants to generate markdown programmatically using SOMA

**What You'll Learn:**
- Minimal SOMA syntax needed for markdown generation
- Complete SOMA markdown extension API
- Patterns for common document structures
- How to execute SOMA code to generate markdown files

---

## SOMA Basics (Just What You Need)

SOMA is a stack-based language. For markdown generation, you only need these concepts:

### 1. String Literals
```soma
(This is a string)
(Multi-line strings
work naturally)
```

### 2. Formatters (Functions)
```soma
>md.h1          ) Call the h1 formatter
>md.p           ) Call the paragraph formatter
```

### 3. State Persistence
```soma
!variable       ) Store value in named location
variable        ) Retrieve value
```

### 4. Comments
```soma
) This is a comment
```

### 5. The Void Sentinel
- Void sits at the bottom of the stack
- Formatters drain items from stack until they hit Void
- You don't need to think about this - it's automatic

---

## Complete SOMA Markdown API

### Document Structure

```soma
(python) >use          ) Load Python FFI
(markdown) >use        ) Load markdown extension

>md.start              ) Initialize document

) ... your content here ...

(output.md) >md.render ) Write to file
) OR
>md.print              ) Print to stdout
```

### Headings (H1-H4)

```soma
(Document Title) >md.h1
(Major Section) >md.h2
(Subsection) >md.h3
(Detail Level) >md.h4
```

**Pattern:** Multi-word headings are automatically joined with spaces:
```soma
(My) (Document) (Title) >md.h1
) Produces: # My Document Title
```

### Paragraphs

```soma
(First paragraph text) >md.p

(Second paragraph)
(Third paragraph)
>md.p
) Each string becomes a separate paragraph
```

**Key Point:** Each string constant becomes its own paragraph with `\n\n` spacing.

### Lists

**Unordered Lists:**
```soma
(First item)
(Second item)
(Third item)
>md.ul
```

**Ordered Lists:**
```soma
(Step 1)
(Step 2)
(Step 3)
>md.ol
```

**Nested Lists:**
```soma
(Outer item 1)
(Outer item 2)
>md.nest
  (Nested A)
  (Nested B)
  >md.ol          ) Inner list type
(Outer item 3)
>md.ul            ) Outer list type
```

**Nesting Rules:**
- `>md.nest` saves current items and increases depth
- Inner list formatter determines inner list type
- Outer list formatter determines outer list type
- Supports arbitrary depth (nest inside nest inside nest...)

### Inline Formatting

**Bold:**
```soma
(bold text) >md.b
) Produces: **bold text**
```

**Italic:**
```soma
(italic text) >md.i
) Produces: _italic text_
```

**Inline Code:**
```soma
(code text) >md.c
) Produces: `code text`
```

**Links:**
```soma
(link text) (https://example.com) >md.l
) Produces: [link text](https://example.com)
```

**Composition:**
```soma
(bold and italic) >md.b >md.i
) Produces: _**bold and italic**_

(link) (https://example.com) >md.l >md.i
) Produces: _[link](https://example.com)_
```

**Inline Text Concatenation:**
```soma
(This has ) (bold) >md.b ( and ) (italic) >md.i ( text) >md.t
) Produces: This has **bold** and _italic_ text

(This has ) (bold) >md.b ( and ) (italic) >md.i ( text) >md.t
>md.p
) Makes it a paragraph
```

### Blockquotes

```soma
(This is a quote) >md.q
) Produces: > This is a quote
```

**Multi-line blockquotes:**
```soma
(First line of quote)
(Second line of quote)
(Third line of quote)
>md.q
) Produces:
) > First line of quote
) > Second line of quote
) > Third line of quote
```

### Code Blocks

**Code block without language:**
```soma
(def hello)
(  return 42)
Nil >md.code
) Produces:
) ```
) def hello
)   return 42
) ```
```

**Code block with language:**
```soma
(def greet name)
(  puts "Hello")
(ruby) >md.code
) Produces:
) ```ruby
) def greet name
)   puts "Hello"
) ```
```

**Using empty string (same as Nil):**
```soma
(line 1)
(line 2)
() >md.code
) Also produces a code block without language
```

### Tables

**Basic Table:**
```soma
(Name) (Age) (Status)
>md.table.header
(Alice) (30) (Active)
>md.table.row
(Bob) (25) (Pending)
>md.table.row
>md.table
```

**Table with Alignment:**
```soma
(Name) (Age) (Status)
>md.table.header
>md.table.left >md.table.centre >md.table.right
>md.table.align
(Alice) (30) (Active)
>md.table.row
(Bob) (25) (Pending)
>md.table.row
>md.table
```

**Alignment Options:**
- `>md.table.left` - Left align column
- `>md.table.centre` - Center align column
- `>md.table.right` - Right align column

**Tables with Inline Formatting:**
```soma
(Feature) (Status) (Link)
>md.table.header
(SOMA) (In Development) >md.b (docs) (https://soma.org) >md.l
>md.table.row
>md.table
```

**Key Point:** Each item on stack = one table cell. Use inline formatters to style cell content.

### Horizontal Rules

```soma
>md.hr
) Produces: ---\n\n
```

**Pattern:** Use to visually separate major sections:
```soma
(Section 1) >md.h2
(Content...) >md.p
>md.hr
(Section 2) >md.h2
```

---

## Execution Patterns

### Method 1: Write to Python File

Create `generate_doc.py`:
```python
#!/usr/bin/env python3
from soma.vm import run_soma_program

code = """
(python) >use
(markdown) >use

>md.start

(My Document) >md.h1
(Introduction paragraph) >md.p

(output.md) >md.render
"""

run_soma_program(code)
print("Generated output.md")
```

Run:
```bash
python3 generate_doc.py
```

### Method 2: Pure SOMA File

Create `document.soma`:
```soma
(python) >use
(markdown) >use

>md.start

(My Document) >md.h1
(Introduction paragraph) >md.p

(output.md) >md.render
```

Run:
```python
from soma.vm import run_soma_program

with open('document.soma', 'r') as f:
    run_soma_program(f.read())
```

### Method 3: Interactive

```python
from soma.vm import VM

vm = VM()
vm.execute_string('(python) >use')
vm.execute_string('(markdown) >use')
vm.execute_string('>md.start')
vm.execute_string('(Title) >md.h1')
vm.execute_string('(Text) >md.p')
vm.execute_string('(out.md) >md.render')
```

---

## Common Patterns & Recipes

### API Documentation

```soma
(python) >use
(markdown) >use
>md.start

(API Reference) >md.h1

(Authentication) >md.h2

(All API requests require authentication using Bearer tokens.)
>md.p

(Endpoint) (Method) (Description)
>md.table.header
(/api/users) (GET) (List all users)
>md.table.row
(/api/users/:id) (GET) (Get user by ID)
>md.table.row
>md.table

(api_reference.md) >md.render
```

### Feature Comparison Table

```soma
(python) >use
(markdown) >use
>md.start

(Feature Comparison) >md.h1

(Feature) (Free) (Pro) (Enterprise)
>md.table.header
>md.table.left >md.table.centre >md.table.centre >md.table.centre
>md.table.align
(Storage) (10 GB) (100 GB) (Unlimited)
>md.table.row
(Users) (1) (5) (Unlimited)
>md.table.row
(Support) (Email) (Priority) >md.b (24/7 Phone) >md.b
>md.table.row
>md.table

(comparison.md) >md.render
```

### Technical Documentation with Code Sections

```soma
(python) >use
(markdown) >use
>md.start

(Installation Guide) >md.h1

(Prerequisites) >md.h2

(Ensure you have the following installed:)
>md.p

(Python 3.8 or higher)
(Git)
(pip package manager)
>md.ul

(Installation Steps) >md.h2

(Clone the repository)
(Install dependencies)
(Run tests)
>md.ol

(Verification) >md.h2

(Run the following command to verify installation:)
>md.p

>md.hr

(Troubleshooting) >md.h2

(Common Issues) >md.h3

(Installation fails)
>md.nest
  (Check Python version)
  (Verify pip is up to date)
  (Check internet connection)
  >md.ul
(Tests fail)
>md.nest
  (Run in clean environment)
  (Check dependency versions)
  >md.ul
>md.ul

(install.md) >md.render
```

### Meeting Notes with Nested Action Items

```soma
(python) >use
(markdown) >use
>md.start

(Project Planning Meeting - 2024-11-27) >md.h1

(Attendees) >md.h2

(Alice (Engineering))
(Bob (Design))
(Carol (Product))
>md.ul

>md.hr

(Discussion Topics) >md.h2

(Feature Roadmap) >md.h3

(Q1 Goals)
>md.nest
  (Launch mobile app)
  (Implement user analytics)
  (Performance optimization)
  >md.ol
(Q2 Goals)
>md.nest
  (Internationalization)
  (API v2)
  >md.ol
>md.ol

>md.hr

(Action Items) >md.h2

(Name) (Task) (Due Date)
>md.table.header
(Alice) (Design API v2) >md.b (2024-12-15)
>md.table.row
(Bob) (Create mobile mockups) >md.b (2024-12-10)
>md.table.row
(Carol) (Write requirements doc) >md.b (2024-12-05)
>md.table.row
>md.table

(meeting_notes.md) >md.render
```

---

## Tips for Helping Users

### 1. **Start Simple**
Begin with basic structure, then add formatting:
```soma
) Start here:
>md.start
(Title) >md.h1
(Text) >md.p
(output.md) >md.render

) Then enhance:
(Bold text) >md.b >md.p
```

### 2. **One Concept at a Time**
Don't mix tables + nesting + inline formatting initially. Build incrementally.

### 3. **Stack Thinking**
Remember: items accumulate until a formatter drains them:
```soma
(Item 1)     ) Stack: [Void, "Item 1"]
(Item 2)     ) Stack: [Void, "Item 1", "Item 2"]
(Item 3)     ) Stack: [Void, "Item 1", "Item 2", "Item 3"]
>md.ul       ) Drains all three items → unordered list
             ) Stack: [Void]
```

### 4. **Common Mistakes to Watch For**

**Wrong - Missing >md.start:**
```soma
(Title) >md.h1  ) ERROR: document not initialized
```

**Wrong - Forgetting to render:**
```soma
>md.start
(Title) >md.h1
) Oops! No >md.render - file not created
```

**Wrong - Using >md.t in table rows:**
```soma
(A) (B) >md.t (C)  ) Drains to Void - only one cell!
>md.table.row
) Should be: (A) (B) (C) >md.table.row
```

**Wrong - Nest without outer formatter:**
```soma
(Outer)
>md.nest
  (Inner) >md.ul
) Oops! Outer items never rendered - need >md.ul or >md.ol
```

### 5. **Debugging**
If output is wrong, check:
1. Did you call `>md.start`?
2. Are items in the right order on the stack?
3. Did you close nested lists with the correct formatter?
4. Did you call `>md.render` with filename?

---

## Quick Reference Card

```
SETUP:           (python) >use (markdown) >use >md.start
TEARDOWN:        (filename.md) >md.render  OR  >md.print

HEADINGS:        (text) >md.h1/h2/h3/h4
PARAGRAPHS:      (text) (text) >md.p
BLOCKQUOTES:     (text) (text) >md.q
LISTS:           (i1) (i2) (i3) >md.ul/ol
NESTING:         >md.nest ... >md.ul/ol ... >md.ul/ol
INLINE:          (text) >md.b >md.i >md.c >md.l
TABLES:          (h1) >md.table.header (r1) >md.table.row >md.table
ALIGNMENT:       >md.table.left/centre/right >md.table.align
CODE BLOCKS:     (line1) (line2) Nil/>md.code  OR  (line1) (python) >md.code
SEPARATOR:       >md.hr

COMPOSITION:     (text) >md.b >md.i → _**text**_
CONCATENATION:   (a) (b) >md.b (c) >md.t → a**b**c
```

---

## Example: Complete Document

```soma
(python) >use
(markdown) >use

>md.start

(SOMA Markdown Extension) >md.h1

(The SOMA markdown extension provides a programmatic way to generate
markdown documents using a simple, stack-based API.)
>md.p

(Features) >md.h2

(Core Features) >md.h3

(Headings (H1-H4))
(Paragraphs with multi-line support)
(Ordered and unordered lists)
(Arbitrary nesting depth)
>md.ul

(Advanced Features) >md.h3

(Inline formatting) >md.b
>md.nest
  (Bold text)
  (Italic text)
  (Hyperlinks)
  >md.ul
(Tables with alignment)
(Horizontal rules)
>md.ul

>md.hr

(Quick Start) >md.h2

(Installation) >md.h3

(Clone the repository)
(Load the extension)
(Start writing)
>md.ol

(Usage Example) >md.h3

(Here's a minimal example:)
>md.p

>md.hr

(API Reference) >md.h2

(Formatter) (Purpose) (Example)
>md.table.header
>md.table.left >md.table.left >md.table.left
>md.table.align
(>md.h1) (Level 1 heading) ((Title) >md.h1)
>md.table.row
(>md.p) (Paragraph) ((Text) >md.p)
>md.table.row
(>md.ul) (Unordered list) ((A) (B) >md.ul)
>md.table.row
>md.table

(README.md) >md.render
```

This generates a complete, well-structured README file!

---

## Summary

**To help a user generate markdown with SOMA:**

1. **Understand their document structure** (outline, sections, data)
2. **Start with skeleton** (`>md.start`, headings, `>md.render` or `>md.print`)
3. **Add content incrementally** (paragraphs, lists, tables)
4. **Apply formatting** (bold, italic, links)
5. **Test and iterate** (run code, check output, refine)

**Key Mental Model:**
- SOMA markdown is like a document builder
- Stack items (strings), then format them
- Each formatter consumes items and adds to document
- Finally render to file

You now have everything you need to help users create beautiful markdown documents using SOMA!
