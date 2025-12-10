# SOMA Markdown - AI Reference (Compact)

## Mental Model (READ FIRST)

SOMA is stack-based. You **push items onto stack, then call a formatter once** to drain them all.

```soma
) WRONG - formatting each item separately
(item1) >md.ul
(item2) >md.ul

) RIGHT - stack items, format once
(item1)
(item2)
>md.ul
```

**Escaping:** Only `)` and `\` need escaping. `(` does NOT.
- `)` → `\29\`
- `\` → `\5C\`
- `(` → just `(` (no escape needed)

## Syntax Essentials

**Strings:** `(text)` - multiline OK, `(` is literal, escape `)` as `\29\`
**Formatters:** `>md.command` - drains stack items to Void
**Variables:** `!name` (store), `name` (retrieve)
**Comments:** `) text`
**Void:** Auto-present at stack bottom - marks where draining stops
**Nil:** Singleton "nothing" value (like Python's None) - use for optional params

## Document Lifecycle

```soma
(python) >use (markdown) >use
>md.start
) ... content ...
(file.md) >md.render
```

## Complete API

### Structure
- `>md.h1` `>md.h2` `>md.h3` `>md.h4` - headings
- `>md.p` - paragraphs (each stacked string = separate paragraph)
- `>md.hr` - horizontal rule

### Lists (drain all stacked items)
```soma
) Stack items first, then format
(First item)
(Second item)
(Third item)
>md.ul    ) or >md.ol for numbered
```

**Nesting:** `>md.nest` saves outer items, then inner list, then outer list
```soma
(Outer 1)
(Outer 2)
>md.nest
  (Inner A)
  (Inner B)
  >md.ol
(Outer 3)
>md.ul
```

**Per-item nesting:** Each outer item can have its own nested sublist
```soma
(Project Alpha)
>md.nest
  (Status) (Active) >md.dli
  (Lead) (Alice) >md.dli
  >md.dul
(Project Beta)
>md.nest
  (Status) (Planning) >md.dli
  (Lead) (Bob) >md.dli
  >md.dul
(Project Gamma)
>md.ol
```
Produces:
```markdown
1. Project Alpha
  - **Status**: Active
  - **Lead**: Alice
2. Project Beta
  - **Status**: Planning
  - **Lead**: Bob
3. Project Gamma
```

**Supported nested formatters:** `>md.ul`, `>md.ol`, `>md.dul`, `>md.dol`

### Inline Formatting (chainable, immediate)
- `>md.b` - **bold**
- `>md.i` - _italic_
- `>md.c` - `code`
- `>md.l` - link (takes 2: text, url)
- `>md.t` - concatenate items (drains to Void, leaves one string)

**Composition:** `(text) >md.b >md.i` → `_**text**_` (chain on same item)
**Concat:** `(a) (b)>md.b (c) >md.t` → `a**b**c` (join multiple items)

```soma
(This has ) (bold) >md.b ( and ) (code) >md.c ( and ) (italic) >md.i ( text.) >md.t >md.p
```

### Complex List Items (when items need inline formatting)
- `>md.oli` - accumulate into ordered list item (auto-concatenates, no `>md.t` needed)
- `>md.uli` - accumulate into unordered list item (auto-concatenates, no `>md.t` needed)

**IMPORTANT:** When ANY item in a list needs inline formatting, use `>md.uli` (or `>md.oli`) for ALL items in that list - including plain items. Do not mix plain stacked items with `>md.uli` items - the plain items will be absorbed into the next `>md.uli` call, corrupting your output.

```soma
) Mixed list where some items have formatting - use >md.uli for ALL items
(Clone the repository) >md.uli
(Install dependencies) >md.uli
(Run ) (make build) >md.c >md.uli
(Run ) (make test) >md.c >md.uli
>md.ul
```

```soma
(Step: ) (Install) >md.b ( dependencies) >md.oli
(Step: ) (Run) >md.c ( the build) >md.oli
>md.ol
```

**Why `>md.t` with `>md.p` but not with `>md.oli`?**
- `>md.oli`/`>md.uli` - implicitly join all items into ONE list item
- `>md.p`/`>md.ul`/`>md.ol` - each stacked item handled SEPARATELY

```soma
) These are DIFFERENT:
(a) (b) (c) >md.p      ) 3 separate paragraphs
(a) (b) (c) >md.t >md.p ) 1 paragraph: "abc"
```

### Definition Lists
- `>md.dul` - definition unordered list
- `>md.dol` - definition ordered list
- `>md.dli` - definition list item (use when values need inline formatting)
- `>md.dt` - alternating bold pairs for inline display

```soma
) Simple (no formatting needed) - use pairs directly
Void (Name) (Alice) (Age) (30) >md.dul

) With formatted values - use >md.dli
(Command) (git ) (pull) >md.c >md.dli
(Status) (Build ) (passed) >md.b >md.dli
>md.dul
```

### Tables
```soma
(H1) (H2) (H3)
>md.table.header
(R1C1) (R1C2) (R1C3)
>md.table.row
(R2C1) (R2C2) (R2C3)
>md.table.row
>md.table
```

**Alignment:** After header, before rows:
```soma
>md.table.left >md.table.centre >md.table.right
>md.table.align
```

### Blockquotes & Code
```soma
(Quote line 1)
(Quote line 2)
>md.q

(code line 1)
(code line 2)
(python) >md.code    ) with language
Nil >md.code         ) no language (preferred over empty string)
```

## Common Mistakes

| Wrong | Right | Why |
|-------|-------|-----|
| `(text\)` | `(text\29\)` | Escapes are `\HEX\` format |
| `(a\(b)` | `(a(b)` | `(` needs no escaping |
| `(x)>md.ul (y)>md.ul` | `(x) (y) >md.ul` | Stack first, format once |
| `(**bold**)` | `(bold) >md.b` | Never use markdown syntax in strings |
| `(a)(b)>md.t >md.oli` | `(a)(b) >md.oli` | `>md.oli`/`>md.uli`/`>md.dli` auto-concatenate |
| `(a) (b) (c) >md.c >md.uli >md.ul` | `(a) >md.uli (b) >md.uli (c) >md.c >md.uli >md.ul` | Plain items get absorbed by next `>md.uli` |

## Critical Rules

1. **Even counts** for `>md.dt` and simple `>md.dul`/`>md.dol` (pairs)
2. **At least 2 items** for `>md.dli` (label + value)
3. **Tables:** Each row needs `>md.table.row` - newlines ≠ rows
4. **Always `>md.start`** before content
5. **`>md.print`** for stdout, **`>md.render`** for file

## Stack Model

```
(Item1)           ) [Void, "Item1"]
(Item2)           ) [Void, "Item1", "Item2"]
>md.ul            ) drains → [Void]
```

## Minimal Complete Example

```soma
(python) >use (markdown) >use
>md.start

(My Document) >md.h1

(This is a paragraph with ) (bold) >md.b ( text.) >md.t >md.p

(Features:) >md.h2

(Fast)
(Simple)
(Composable)
>md.ul

(Author) (Alice) >md.dli
(Version) (1.0) >md.dli
>md.dul

(output.md) >md.render
```
