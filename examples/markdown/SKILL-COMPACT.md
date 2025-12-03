# SOMA Markdown - AI Reference (Compact)

## Syntax Essentials

**Strings:** `(text)` - multiline OK
**Escapes:** `\HEX\` format - `\29\`=`)`, `\5C\`=`\` - **only these need escaping** - `(` does NOT need escaping
**Formatters:** `>md.command`
**Variables:** `!name` (store), `name` (retrieve)
**Comments:** `) text`
**Void:** Auto-present at bottom of stack - you don't need to add it explicitly

## Document Lifecycle

```soma
(python) >use (markdown) >use
>md.start
) ... content ...
(file.md) >md.render  ) or >md.print for stdout
```

## Complete API

### Structure
- `>md.h1` `>md.h2` `>md.h3` `>md.h4` - headings, multi-word auto-joined
- `>md.p` - paragraphs (each string = separate paragraph)
- `>md.hr` - horizontal rule

### Lists
- `>md.ul` - unordered list (drains all items to Void)
- `>md.ol` - ordered list (drains all items to Void)
- `>md.nest` - save current items, increase depth, then inner list formatter, then outer list formatter
- Nesting: `(outer items) >md.nest (inner items) >md.ol (more outer) >md.ul`

### Inline Formatting (chainable)
- `>md.b` - **bold**
- `>md.i` - _italic_
- `>md.c` - `code`
- `>md.l` - [text](url) - takes 2 args: text, url
- `>md.t` - concatenate inline items (drains to Void)

Composition: `(text) >md.b >md.i` → `_**text**_`
Concat: `(a) (b)>md.b (c) >md.t` → `a**b**c`

### Blockquotes
- `>md.q` - blockquote (multi-line: each string = separate `>` line)

### Code Blocks
```soma
(line1) (line2) Nil >md.code          ) no language
(line1) (line2) (python) >md.code     ) with language
```

### Tables
```soma
(H1) (H2) (H3) >md.table.header
(R1C1) (R1C2) (R1C3) >md.table.row    ) MUST use .row for each row
(R2C1) (R2C2) (R2C3) >md.table.row
>md.table
```

**Alignment:**
```soma
(H1) (H2) (H3) >md.table.header
>md.table.left >md.table.centre >md.table.right >md.table.align
) ... rows ...
>md.table
```

**With formatting:** Each stack item = one cell, use inline formatters

### Complex List Items (with inline formatting)
**Problem:** `>md.b` drains items immediately, breaking lists
**Solution:** Accumulators

- `>md.oli` - accumulate into ordered list item placeholder
- `>md.uli` - accumulate into unordered list item placeholder

```soma
(Task: ) (Install) >md.b ( deps) >md.oli
(Task: ) (Run) >md.c ( server) >md.oli
>md.ol    ) renders accumulated items
```

### Transformations (consume items, produce new items)
- `>md.dl` - pairs → `**label**: value` (even count required)
- `>md.dt` - alternates bold on pairs (even count required)

**Note:** `Void` shown in examples is optional (already at stack bottom)

```soma
Void (Name) (Alice) (Age) (30) >md.dl
) Stack now: (**Name**: Alice) (**Age**: 30)
>md.ul  ) render it
```

### Combinators (transform + render)
- `>md.dul` - definition unordered list = `>md.dl >md.ul`
- `>md.dol` - definition ordered list = `>md.dl >md.ol`

**Note:** `Void` optional here too

```soma
Void (Host) (localhost) (Port) (8080) >md.dul
```

## Critical Rules

1. **Never use markdown syntax in strings** - `(text)>md.b` not `(**text**)`
2. **Tables:** Each row needs `>md.table.row` - newlines ≠ rows
3. **Nesting:** Must render outer list after inner: `>md.nest (inner) >md.ol (outer) >md.ul`
4. **Transformations FAIL with placeholders** - render `>md.oli/uli` lists first, transform separately
5. **Even counts only** for `>md.dl` `>md.dt` `>md.dul` `>md.dol`
6. **Always `>md.start` before content**
7. **Render all placeholders before `>md.render`**

## Execution

Python file:
```python
from soma.vm import run_soma_program
run_soma_program("(python)>use (markdown)>use >md.start (Title)>md.h1 (out.md)>md.render")
```

## Common Patterns

**Nested list:**
```soma
(A) (B) >md.nest (B1) (B2) >md.ul (C) >md.ol
```

**Table with bold cells:**
```soma
(Name) (Status) >md.table.header
(Alice) (Active)>md.b >md.table.row
>md.table
```

**Definition list:**
```soma
Void (Key1) (Val1) (Key2) (Val2) >md.dul
```

**Complex ordered list:**
```soma
(Install ) (Python) >md.c >md.oli
(Run ) (pip install) >md.c >md.oli
>md.ol
```

**Inline composition:**
```soma
(This has ) (bold) >md.b ( and ) (italic) >md.i ( text) >md.t >md.p
```

## Stack Model

```
(Item1)           ) [Void, "Item1"]
(Item2)           ) [Void, "Item1", "Item2"]
>md.ul            ) drains → [Void]
```

## Escape Examples
```soma
(Error :-\29\)                  ) :-)
(C:\5C\Users)                   ) C:\Users
(Paren (text\29\ example)       ) Paren (text) example - only ) needs escaping
(Quote: "hello")                ) Quote: "hello" - " doesn't need escaping
```
