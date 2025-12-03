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

**Escaping Special Characters:**

SOMA uses `\HEX\` format for escapes - backslash, hex digits, backslash:
```soma
(Hello world\29\)           ) \29\ escapes ) (hex 29)
(Path: C:\5C\Users\5C\name) ) \5C\ escapes \ (hex 5C)
(Error :-\29\)              ) Example: smiley with )
(Degree: 98.6\B0\)          ) \B0\ = ° symbol
```

**Adjacent escapes** - each escape is independent, so they sit side-by-side:
```soma
(A closing paren\29\ then backslash\5C\)  ) Produces: )\
(Smiley\29\\5C\29\)                        ) Produces: )\ )
```

**Critical:** Only `)` and `\` need escaping:
- `)` → `\29\` (or it closes the string)
- `\` → `\5C\` (or it starts an escape)
- `(` does NOT need escaping - write it literally!

**Examples of what NOT to escape:**
```soma
(Function call: foo(x, y))              ) Wrong! Closes string early
(Function call: foo(x, y\29\)           ) Right! Escape closing paren
(Inline (parenthetical remark\29\ text) ) Right! Opening ( is literal
(Path: /usr/local/bin)                  ) Right! / needs no escaping
(Quote: "Hello World")                  ) Right! " needs no escaping
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
- Void sits at the bottom of the stack automatically
- Formatters drain items from stack until they hit Void
- You don't need to explicitly add `Void` - it's already there
- Examples may show `Void` for clarity, but it's optional

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

**Style note:** List items should be consecutive with no blank lines between them in SOMA source.

**Common mistake:** Use `>md.ol` for numbered lists, not formatting tricks like `()>md.b`.

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

**Critical - Don't use Markdown syntax directly:**
```soma
) WRONG:
(**bold**)                          ) No! Markdown syntax doesn't work
()+3.3%**)>b                        ) No! Empty () and ** mixed together
(text **bold**)                     ) No! ** inside strings won't be formatted

) RIGHT:
(bold)>md.b                         ) Yes! Use SOMA formatters
(+3.3%)>md.b                        ) Yes! Text in (...), then >md.b
(text ) (bold)>md.b >md.t           ) Yes! Compose with formatters
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

**Format reminder:** Code lines must be in string constants `(...)`. Order is: code strings, then language (or Nil), then `>md.code`.

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

**Critical:** Every data row needs `>md.table.row`. Newlines are whitespace in SOMA, not syntax - unlike Markdown, line breaks don't create rows.

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

### Complex List Items with Inline Formatting

Sometimes you need inline formatting (bold, italic, code, links) **within** list items. The basic list pattern doesn't support this because formatters like `>md.b` consume items from the stack immediately.

**The Problem:**
```soma
) WRONG - This doesn't work:
(Task: ) (Install) >md.b ( dependencies)  ) >md.b drains items!
(Task: ) (Run) >md.c ( the server)         ) >md.c drains items!
>md.ol                                      ) List has no items left!
```

**The Solution - List Item Accumulators:**

Use `>md.oli` (ordered list item) and `>md.uli` (unordered list item) to accumulate formatted content into single list items:

**Ordered List Items (md.oli):**
```soma
(Task: ) (Install) >md.b ( dependencies) >md.oli
(Task: ) (Run) >md.c ( the server) >md.oli
(Task: ) (Test the ) (API endpoint) >md.l ( works) >md.oli
>md.ol
) Produces:
) 1. Task: **Install** dependencies
) 2. Task: `Run` the server
) 3. Task: Test the [API endpoint](url) works
```

**Unordered List Items (md.uli):**
```soma
(Feature: ) (fast) >md.i ( performance) >md.uli
(Feature: ) (simple) >md.b ( API) >md.uli
(Feature: ) (detailed ) (documentation) >md.l >md.uli
>md.ul
) Produces:
) - Feature: _fast_ performance
) - Feature: **simple** API
) - Feature: detailed [documentation](url)
```

**How It Works:**
- `>md.oli` and `>md.uli` accumulate content into a **single list item**
- They store the item internally and put an opaque placeholder on the stack
- Later, `>md.ol` or `>md.ul` consumes these placeholders and renders the full list
- You can use any inline formatter (`>md.b`, `>md.i`, `>md.c`, `>md.l`) before the accumulator

**Pattern - Building Complex Items:**
```soma
) Step 1: Build each item with inline formatting
(Step ) (1) >md.b (: Install ) (Python) >md.c >md.oli
(Step ) (2) >md.b (: Run ) (pip install soma) >md.c >md.oli
(Step ) (3) >md.b (: Read the ) (docs) (https://soma.org) >md.l >md.oli

) Step 2: Consume the accumulated items with a list formatter
>md.ol
```

**When to Use:**
- Task lists with formatted keywords
- Feature lists with code or links
- Step-by-step instructions with emphasis
- Any list where items need internal formatting

**When NOT to Use:**
- Simple text-only lists (use direct `>md.ul` or `>md.ol`)
- When you don't need inline formatting

### Inline Transformations (md.dl and md.dt)

These are **transformation operations** - they consume items from the stack and produce **new items** back on the stack. They do NOT render anything themselves.

**Note on `Void` in examples:** The examples below show `Void` explicitly for clarity, but it's already at the bottom of the stack automatically. You can omit `Void` and the transformations will work the same way - they consume items until hitting the automatic Void sentinel.

**Definition List Transformation (md.dl):**

Takes pairs of items and transforms them into `**label**: value` format:

```soma
Void (Name) (Alice) (Age) (30) >md.dl
) Stack now contains: (**Name**: Alice) (**Age**: 30)
) Nothing rendered yet - items are on stack

>md.ul
) Produces:
) - **Name**: Alice
) - **Age**: 30
```

**Key Points:**
- Requires **even number of items** (pairs)
- Consumes items from stack
- Produces formatted pairs back on stack
- Must use a renderer (`>md.ul`, `>md.ol`, etc.) to output

**Data Title Transformation (md.dt):**

Alternates bold formatting on pairs of items:

```soma
Void (Alice) (Developer) (Bob) (Designer) >md.dt
) Stack now contains: (**Alice**) (Developer) (**Bob**) (Designer)

>md.ul
) Produces:
) - **Alice**
) - Developer
) - **Bob**
) - Designer
```

**Common Use Cases:**

**Configuration Settings:**
```soma
Void (Host) (localhost) (Port) (8080) (Debug) (True) >md.dl
>md.ul
) Produces:
) - **Host**: localhost
) - **Port**: 8080
) - **Debug**: True
```

**Team Directory:**
```soma
Void (Alice) (Engineering) (Bob) (Design) (Carol) (Product) >md.dt
>md.ol
) Produces:
) 1. **Alice**
) 2. Engineering
) 3. **Bob**
) 4. Design
) 5. **Carol**
) 6. Product
```

**CRITICAL WARNING - Placeholder Interactions:**

Transformations **FAIL** if placeholders from `>md.oli` or `>md.uli` are in the items:

```soma
) WRONG - This will ERROR:
(Task) >md.b >md.oli          ) Creates placeholder
(Description) >md.i >md.oli   ) Creates placeholder
>md.dl                         ) ERROR! Can't pair placeholders!

) RIGHT - Render placeholders first, THEN transform:
(Task) >md.b >md.oli
(Description) >md.i >md.oli
>md.ol                         ) Render the complex items

Void (Name) (Alice) (Role) (Engineer) >md.dl
>md.ul                         ) Now transform and render separately
```

**Rules for Using Transformations:**
1. Always work with **even numbers** of items
2. Never mix with placeholders from `>md.oli`/`>md.uli`
3. Transform first, then render with `>md.ul`/`>md.ol`/`>md.p`
4. You can chain transformations if needed

**Example - Chaining Transformations:**
```soma
Void (Key1) (Value1) (Key2) (Value2) >md.dl
) Stack: (**Key1**: Value1) (**Key2**: Value2)

>md.p
) Renders as paragraph with formatted pairs
```

### Convenience Combinators (md.dul and md.dol)

These are shortcuts that combine transformations with rendering in one operation:

**Note on `Void`:** As with `>md.dl` and `>md.dt`, the `Void` shown in examples is optional - the stack already has Void at the bottom automatically.

**Definition Unordered List (md.dul):**

Equivalent to `>md.dl` followed by `>md.ul`:

```soma
) Instead of this:
Void (Name) (Alice) (Age) (30) >md.dl
>md.ul

) Write this:
Void (Name) (Alice) (Age) (30) >md.dul
) Produces:
) - **Name**: Alice
) - **Age**: 30
```

**Definition Ordered List (md.dol):**

Equivalent to `>md.dl` followed by `>md.ol`:

```soma
Void (Step) (Initialize) (Action) (Configure) (Result) (Success) >md.dol
) Produces:
) 1. **Step**: Initialize
) 2. **Action**: Configure
) 3. **Result**: Success
```

**When to Use Combinators:**

**Configuration Files:**
```soma
>md.start

(Server Configuration) >md.h2

Void (Host) (localhost)
     (Port) (8080)
     (Workers) (4)
     (Timeout) (30s)
>md.dul

(config.md) >md.render
```

**Feature Comparison:**
```soma
>md.start

(Feature Comparison) >md.h2

Void (Speed) (Fast)
     (Memory) (Low)
     (Compatibility) (High)
>md.dol

(comparison.md) >md.render
```

**Environment Variables:**
```soma
(Environment Setup) >md.h2

Void (DATABASE_URL) (postgres://localhost/db)
     (API_KEY) (your-api-key-here)
     (LOG_LEVEL) (debug)
>md.dul
```

**When NOT to Use:**
- When you need placeholders (use separate render then transform)
- When you need different output format (use `>md.dl` + custom renderer)

**Remember:**
- `>md.dul` = definition unordered list (bulleted)
- `>md.dol` = definition ordered list (numbered)
- Both require even number of items
- Both fail with placeholders (same rules as `>md.dl`)

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

### Configuration Documentation with Definition Lists

```soma
(python) >use
(markdown) >use
>md.start

(Application Configuration) >md.h1

(Server Settings) >md.h2

Void (Host) (0.0.0.0)
     (Port) (8080)
     (Workers) (4)
     (Timeout) (30s)
     (Debug Mode) (false)
>md.dul

(Database Configuration) >md.h2

Void (Engine) (PostgreSQL)
     (Version) (14.0)
     (Max Connections) (100)
     (Pool Size) (20)
>md.dul

(API Keys) >md.h2

Void (STRIPE_KEY) (sk_test_xxx)
     (SENDGRID_KEY) (SG.xxx)
     (AWS_ACCESS_KEY) (AKIA...)
>md.dul

(config_docs.md) >md.render
```

### Task List with Inline Formatting

```soma
(python) >use
(markdown) >use
>md.start

(Development Tasks) >md.h1

(High Priority) >md.h2

(Fix the ) (authentication) >md.b ( bug in ) (login.py) >md.c >md.oli
(Update ) (API documentation) >md.i ( with new endpoints) >md.oli
(Deploy to ) (staging) >md.b ( environment) >md.oli
>md.ol

(Code Review Checklist) >md.h2

(Check ) (type hints) >md.c ( are present) >md.uli
(Verify ) (tests pass) >md.b ( locally) >md.uli
(Review ) (security) >md.i ( implications) >md.uli
(Update ) (CHANGELOG.md) >md.c >md.uli
>md.ul

(tasks.md) >md.render
```

### Feature Comparison with Definition Ordered List

```soma
(python) >use
(markdown) >use
>md.start

(Product Tiers) >md.h1

(Free Tier) >md.h2

Void (Storage) (10 GB)
     (Users) (1)
     (Support) (Community)
     (API Calls) (1,000/month)
>md.dol

(Pro Tier) >md.h2

Void (Storage) (100 GB)
     (Users) (5)
     (Support) (Email)
     (API Calls) (100,000/month)
>md.dol

(Enterprise Tier) >md.h2

Void (Storage) (Unlimited)
     (Users) (Unlimited)
     (Support) (24/7 Phone)
     (API Calls) (Unlimited)
>md.dol

(pricing.md) >md.render
```

### Installation Guide with Complex Steps

```soma
(python) >use
(markdown) >use
>md.start

(Installation Guide) >md.h1

(Prerequisites) >md.h2

(Install ) (Python 3.8+) >md.b >md.uli
(Install ) (Git) >md.b >md.uli
(Have ) (pip) >md.c ( and ) (virtualenv) >md.c ( available) >md.uli
>md.ul

(Quick Start) >md.h2

(Clone with ) (git clone https://github.com/user/repo.git) >md.c >md.oli
(Navigate with ) (cd repo) >md.c >md.oli
(Create virtualenv with ) (python -m venv venv) >md.c >md.oli
(Activate with ) (source venv/bin/activate) >md.c >md.oli
(Install with ) (pip install -r requirements.txt) >md.c >md.oli
>md.ol

(Configuration) >md.h2

Void (DB_HOST) (localhost)
     (DB_PORT) (5432)
     (SECRET_KEY) (your-secret-here)
     (LOG_LEVEL) (INFO)
>md.dul

(install.md) >md.render
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

**Wrong - Using md.dl/dt with placeholders:**
```soma
(Item1) >md.b >md.oli
(Item2) >md.i >md.oli
>md.dl              ) ERROR! Transformations fail with placeholders
```

**Right - Render placeholders first:**
```soma
(Item1) >md.b >md.oli
(Item2) >md.i >md.oli
>md.ol              ) Render complex list first

Void (Key1) (Val1) (Key2) (Val2) >md.dl
>md.ul              ) Then transform and render separately
```

**Wrong - Odd number of items with md.dl:**
```soma
Void (Name) (Alice) (Age)   ) Only 3 items!
>md.dl                       ) ERROR! Need even number for pairs
```

**Right - Even pairs:**
```soma
Void (Name) (Alice) (Age) (30)  ) 4 items = 2 pairs
>md.dl
>md.ul
```

**Wrong - Forgetting to consume placeholders:**
```soma
(Item) >md.b >md.oli
(Another) >md.i >md.oli
>md.render           ) ERROR! Placeholders not rendered
```

**Right - Always render placeholders:**
```soma
(Item) >md.b >md.oli
(Another) >md.i >md.oli
>md.ol               ) Consume placeholders first
(output.md) >md.render
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

COMPLEX ITEMS:   (text) >md.b >md.oli  ) Ordered list item with formatting
                 (text) >md.i >md.uli  ) Unordered list item with formatting
                 >md.ol or >md.ul      ) Then render the accumulated items

TRANSFORMATIONS: Void (k1) (v1) (k2) (v2) >md.dl >md.ul  ) Definition list
                 Void (a) (b) (c) (d) >md.dt >md.ol      ) Data title pairs

COMBINATORS:     Void (k1) (v1) (k2) (v2) >md.dul        ) Definition + ul
                 Void (k1) (v1) (k2) (v2) >md.dol        ) Definition + ol

COMPOSITION:     (text) >md.b >md.i → _**text**_
CONCATENATION:   (a) (b) >md.b (c) >md.t → a**b**c

WARNINGS:        - Never mix >md.dl/dt with placeholders from >md.oli/uli
                 - Always even number of items for >md.dl/dt/dul/dol
                 - Always render placeholders before >md.render
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
