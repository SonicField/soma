# SOMA Documentation Conversion Plan v2

## Lesson Learned

Mechanical/regex-based conversion destroys content. AI agents without proper context make destructive changes. The solution is **section-by-section AI inference** with proper SOMA knowledge.

---

## The Approach

### Step 1: Parse MD into Sections

Split the markdown file on headings (lines starting with `#` that are NOT inside code blocks).

Each section becomes a small chunk (typically 20-100 lines) that can be converted independently.

**Pseudocode:**
```
in_code_block = False
sections = []
current_section = []

for line in file:
    if line.startswith('```'):
        in_code_block = not in_code_block

    if not in_code_block and line.startswith('#'):
        if current_section:
            sections.append(current_section)
        current_section = [line]
    else:
        current_section.append(line)

sections.append(current_section)
```

### Step 2: Convert Each Section with AI

For each section:
1. AI reads `docs/markdown/SKILL.md` first (SOMA markdown DSL reference)
2. AI receives the markdown section
3. AI converts to SOMA, preserving ALL content:
   - Headings → `>md.h1`, `>md.h2`, `>md.h3`
   - Paragraphs → `>md.p`
   - Code blocks → `(lang) (code) >md.code`
   - Lists → `>md.ul`, `>md.ol`, `>md.uli`, `>md.oli`
   - Bold/italic → `>md.b`, `>md.i`
   - Escaping: `)` → `\29\`, `\` → `\5C\`
4. AI validates syntax by reasoning, not regex

### Step 3: Assemble and Test

1. Concatenate all converted sections
2. Add header: `(python) >use (markdown) >use`
3. Add footer: `>md.print`
4. Test: `python3 -m soma < file.soma | diff - file.md`
5. If errors, use AI to fix specific issues

### Step 4: Iterate on Failures

If a section fails to render:
1. Get the specific error message
2. AI reads the error and the section
3. AI fixes using inference, NOT regex
4. Re-test

---

## Section Conversion Prompt Template

```
You are converting a markdown section to SOMA markdown source.

FIRST, read /home/alexturner/local/soma/docs/markdown/SKILL.md to understand the SOMA markdown DSL.

Then convert this markdown section to SOMA:

---
[SECTION CONTENT HERE]
---

Rules:
1. Preserve ALL content exactly - do not summarize or condense
2. Use proper SOMA markdown commands from SKILL.md
3. Escape ) as \29\ and \ as \5C\
4. ( does NOT need escaping
5. For multi-line prose, use >concat to join strings
6. For code blocks: (language) (code content) >md.code
7. Do NOT add >md.print - that goes at the end of the full file

Output ONLY the SOMA code for this section, nothing else.
```

---

## Test Case: philosophy.md

**File:** `docs/core/philosophy.md` (532 lines)

**Expected sections:** ~15-20 (based on heading structure)

**Process:**
1. Parse into sections
2. Convert section 1 as test
3. Verify output matches original
4. If good, convert remaining sections
5. Assemble full .soma file
6. Test rendering

---

## Success Criteria

A successful conversion:
1. Renders without syntax errors
2. Output matches original .md semantically (same headings, paragraphs, code blocks, lists)
3. No content is lost or summarized
4. Line count is comparable (±20% is acceptable due to formatting differences)

---

## Progress Log

### 2024-12-07: Initial Test - Section 7 of philosophy.md

**Test:** Register Isolation Example section (36 lines with code blocks, lists, bold, inline code)

**Result:** ✅ SUCCESS

**Process:**
1. Parsed philosophy.md into 37 sections using heading detection
2. Extracted section 7 (36 lines) as test case
3. Sub-agent read SKILL.md, then converted the section
4. Rendered and compared with original

**Diff Analysis:**
- Extra blank lines after lists (formatting only)
- `*italic*` → `_italic_` (both valid markdown)
- Missing trailing `---` horizontal rule
- All **content** preserved correctly

**Key Escaping Learned:**
- `)` inside strings must be `\29\` when followed by special chars like `:`
- Example: `(global state):` → `(global state\29\:`

**Files Created:**
- `/tmp/section7.soma` - converted section
- `/tmp/test_section7.soma` - full test file with module loading

**Next Steps:**
- Convert remaining 36 sections of philosophy.md
- Assemble into complete philosophy.soma
- Test full file rendering

### 2024-12-07: Full philosophy.md Conversion - SUCCESS ✅

**Process:**
1. Parsed philosophy.md into 37 sections
2. Launched 6 parallel **opus** agents (each handling 6-7 sections)
3. All agents read SKILL.md first, then converted sections
4. Assembled all sections with header/footer
5. Tested full render

**Results:**
- Original: 532 lines
- SOMA source: 558 lines
- Rendered output: 550 lines
- Status: ✅ SUCCESS - renders without errors

**Minor Differences (acceptable):**
- Extra blank lines after some elements
- `*italic*` → `_italic_` (both valid markdown)
- Some `**bold**` in list items not preserved
- Table column alignment different (content identical)

**Key Success Factors:**
1. Used **opus** agents (not haiku) - much better reasoning
2. Section-by-section approach - small chunks converted accurately
3. AI read SKILL.md first - proper DSL knowledge
4. No regex-based fixing - AI inference only

**Files Created:**
- `/home/alexturner/local/soma/docs/core/philosophy.soma` (558 lines)

---

## Learnings

### What Worked

1. **Section-by-section parsing** - Splitting on headings (outside code blocks) creates manageable chunks of 4-56 lines that AI can convert accurately without losing context.

2. **Opus over Haiku** - Haiku made destructive simplifications and regex-based "fixes" that destroyed content. Opus reasons about the conversion properly and preserves everything.

3. **AI reads SKILL.md first** - Essential. Without DSL knowledge, agents guess at syntax. With it, they use the correct commands.

4. **Parallel agents** - 6 agents converting 6-7 sections each completed the 37-section file efficiently. No conflicts since each writes to separate files.

5. **Assemble + test** - Simple concatenation with header/footer works. Testing the full render catches any syntax errors.

### What to Improve

1. **Bold in lists** - Some `**bold**` emphasis in list items was lost. Need to instruct agents to use `>md.b` within `>md.oli`/`>md.uli` more carefully.

2. **Table formatting** - SOMA's table renderer produces nicely aligned columns (actually a feature!). But bold in table cells is inconsistent.

3. **Italic style** - `*text*` becomes `_text_` - both valid markdown, but not byte-identical.

4. **Extra blank lines** - The renderer adds blank lines after some elements. Cosmetic only.

### Known Acceptable Differences

These don't affect meaning and should be accepted:

- Extra blank lines between elements
- `*italic*` vs `_italic_`
- Table column alignment (prettier in output!)
- ```` ``` ```` vs ```` ```text ```` for code blocks
- Minor indentation differences in nested lists

### Conversion Prompt Refinements

For future conversions, add to the prompt:

```
When converting lists with bold text like:
  1. **`>path`** - description

Use this pattern:
  (>path) >md.c >md.b ( - description) >md.oli

This preserves both the code formatting AND the bold emphasis.
```

---

## Recommended Next Steps

### Option A: Continue with Current Approach
1. Commit philosophy.soma as-is (differences are minor)
2. Delete broken .soma files from earlier attempts
3. Convert remaining docs one-by-one using section approach
4. Priority order by importance: core/ → programming/ → extensions/ → debugging/

### Option B: Fix Bold Issue First
1. Refine the conversion prompt to handle bold-in-lists better
2. Re-convert philosophy.md with improved prompt
3. Then proceed with other docs

### Option C: Selective Conversion
1. Only convert the most important docs (philosophy, machine-model, blocks-execution)
2. Keep others as .md only for now
3. Build out the approach incrementally

### Estimated Effort (Option A)

| Directory | Files | Est. Sections | Agent Batches |
|-----------|-------|---------------|---------------|
| core/ | 6 remaining | ~200 | ~6 batches |
| programming/ | 4 files | ~150 | ~5 batches |
| extensions/ | 4 files | ~80 | ~3 batches |
| debugging/ | 2 files | ~40 | ~2 batches |

Total: ~16 agent batches, all using opus for quality.
