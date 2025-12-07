# SOMA Markdown Conversion Prompt

This is the refined prompt for converting markdown sections to SOMA markdown source.
Use with opus agents for best results.

---

## Prompt Template

```
You are converting a markdown section to SOMA markdown source.

FIRST, read /home/alexturner/local/soma/docs/markdown/SKILL.md to understand the SOMA markdown DSL completely.

Then convert this markdown section to SOMA:

---
[SECTION CONTENT HERE]
---

## Rules

1. **Preserve ALL content exactly** - do not summarize or condense
2. **Use proper SOMA markdown commands** from SKILL.md
3. **Escape special characters**:
   - `)` → `\29\`
   - `\` → `\5C\`
   - `(` does NOT need escaping

## Definition Lists (IMPORTANT)

When you see list items with the pattern `**Term** - description`:
- This is a DEFINITION LIST pattern
- Use `>md.dul` for unordered or `>md.dol` for ordered
- These auto-bold the term and use `:` as separator
- Stack (term) (description) pairs, then call >md.dul or >md.dol

Examples:

**Simple definition list (unordered):**
```markdown
- **It begins with the machine** - the actual reality
- **It exposes state directly** - mutation is not hidden
```
→
```soma
(It begins with the machine) (the actual reality)
(It exposes state directly) (mutation is not hidden)
>md.dul
```

**Numbered definition list:**
```markdown
1. **The AL** - a linear stack-like value conduit
2. **The Store** - a global persistent graph
```
→
```soma
(The AL) (a linear stack-like value conduit)
(The Store) (a global persistent graph)
>md.dol
```

**Definition list with CODE in the term:**
```markdown
- **`>choose`** - select one of two values
- **`>chain`** - repeatedly execute blocks
```
→
```soma
(>choose) >md.c (select one of two values) >md.dli
(>chain) >md.c (repeatedly execute blocks) >md.dli
>md.dul
```

**Numbered definition list with CODE:**
```markdown
1. **`>path`** - Execute a block from a path
2. **`>{ code }`** - Execute a block literal
```
→
```soma
(>path) >md.c (Execute a block from a path) >md.dli
(>{ code }) >md.c (Execute a block literal) >md.dli
>md.dol
```

## Other Patterns

**Headings:**
- `# Title` → `(Title) >md.h1`
- `## Section` → `(Section) >md.h2`
- `### Subsection` → `(Subsection) >md.h3`

**Paragraphs:**
- `text` → `(text) >md.p`

**Code blocks:**
```markdown
\`\`\`soma
code here
\`\`\`
```
→
```soma
(code here) (soma) >md.code
```

**Simple lists (no bold terms):**
```markdown
- item one
- item two
```
→
```soma
(item one) (item two) >md.ul
```

**Horizontal rules:**
- `---` → `>md.hr`

**Inline formatting in paragraphs:**
- Bold: `(text) >md.b`
- Italic: `(text) >md.i`
- Code: `(text) >md.c`
- Combine with `>md.t`: `(bold part) >md.b ( and normal) >md.t >md.p`

## Output

Do NOT add `>md.print` or module loading - these are just sections.
Output ONLY the SOMA code for this section.
```

---

## Usage

1. Parse markdown file into sections (split on headings outside code blocks)
2. For each section, call an opus agent with this prompt + section content
3. Assemble all sections with header and footer:
   ```soma
   (python) >use (markdown) >use
   >md.start
   [all sections concatenated]
   >md.print
   ```
4. Test render: `python3 -m soma < file.soma`

---

## Key Learnings

1. **Use opus, not haiku** - Haiku makes destructive simplifications
2. **Section-by-section** - Small chunks (4-56 lines) convert accurately
3. **AI reads SKILL.md first** - Essential for correct DSL usage
4. **Definition lists** - Recognize `**Term** - desc` pattern, use >md.dul/>md.dol
5. **Code in terms** - Use `>md.dli` with `>md.c` for code-formatted terms
6. **No regex fixing** - All fixes via AI inference only
