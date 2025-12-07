# SOMA Documentation Conversion Issues

This log tracks issues found during the .md → .soma conversion.

## Issue Categories

- **SYNTAX**: File fails to parse/render
- **OUTPUT**: Uses >md.render instead of >md.print (no stdout)
- **FORMAT**: Renders but output is malformed
- **CONTENT**: Missing sections or incorrect content

---

## Summary

| File | Status | Issues |
|------|--------|--------|
| concepts/engineering-standards.soma | ✓ OK | None |
| core/blocks-execution.soma | SYNTAX | Fails to parse |
| core/builtins.soma | ✓ OK | None |
| core/control-flow.soma | OUTPUT | Uses >md.render not >md.print |
| core/lexer.soma | SYNTAX+OUTPUT | Fails to parse, uses >md.render |
| core/machine-model.soma | ✓ OK | None |
| core/philosophy.soma | OUTPUT | Uses >md.render not >md.print |
| core/stdlib.soma | OUTPUT | Uses >md.render not >md.print |
| debugging/debugging.soma | FORMAT | Headings used for paragraphs, ### for regular text |
| debugging/debug-ideas.soma | ✓ OK | Minor - looks acceptable |
| extensions/extensions.soma | SYNTAX | Fails to parse |
| extensions/index.soma | SYNTAX | Fails to parse |
| extensions/load.soma | SYNTAX | Fails to parse |
| extensions/python-interface.soma | SYNTAX+OUTPUT | "Illegal numeric literal", uses >md.render |
| programming/comparisons.soma | OUTPUT | Uses >md.render not >md.print |
| programming/errors-semantics.soma | FORMAT | Text breaking mid-sentence, >concat not working |
| programming/examples.soma | ✓ OK | Minor - looks acceptable |
| programming/idioms.soma | OUTPUT | Uses >md.render not >md.print |
| index.soma | OUTPUT | Missing >md.print at end |

---

## Detailed Issues

### SYNTAX Errors (6 files)

#### docs/core/blocks-execution.soma
- **Error**: Needs investigation
- **Fix**: Debug and fix syntax

#### docs/core/lexer.soma
- **Error**: Needs investigation
- **Fix**: Debug and fix syntax, change >md.render to >md.print

#### docs/extensions/extensions.soma
- **Error**: Needs investigation
- **Fix**: Debug and fix syntax

#### docs/extensions/index.soma
- **Error**: Needs investigation
- **Fix**: Debug and fix syntax

#### docs/extensions/load.soma
- **Error**: Needs investigation
- **Fix**: Debug and fix syntax

#### docs/extensions/python-interface.soma
- **Error**: "Illegal numeric literal starting at '1024)'" (line 56)
- **Fix**: Escape the `)` in `1024)` as `1024\29\`, change >md.render to >md.print

---

### OUTPUT Issues - Wrong ending (7 files)

These files use `>md.render` or are missing `>md.print`:

1. `core/control-flow.soma` - uses >md.render
2. `core/philosophy.soma` - uses >md.render
3. `core/stdlib.soma` - uses >md.render
4. `extensions/python-interface.soma` - uses >md.render
5. `programming/comparisons.soma` - uses >md.render
6. `programming/idioms.soma` - uses >md.render
7. `index.soma` - missing >md.print

**Fix**: Replace `(filename) >md.render` with `>md.print`

---

### FORMAT Issues (2 files)

#### docs/debugging/debugging.soma
- Empty `# ` heading at start
- `## ` and `### ` used for paragraph text instead of >md.p
- Paragraphs rendered as headings throughout
- **Fix**: Review and add proper >md.p for paragraph content

#### docs/programming/errors-semantics.soma
- Text breaking mid-sentence ("the semantics \n\nof the")
- Bold markers appearing on separate lines
- >concat not properly joining multi-line text
- **Fix**: Review >concat usage, ensure continuous prose

---

## Files OK (5 files)

These render correctly with >md.print:
1. concepts/engineering-standards.soma ✓
2. core/builtins.soma ✓
3. core/machine-model.soma ✓
4. debugging/debug-ideas.soma ✓ (minor issues acceptable)
5. programming/examples.soma ✓ (minor issues acceptable)

---

## Fix Priority

1. **High**: Fix OUTPUT issues (simple find/replace >md.render → >md.print)
2. **Medium**: Fix SYNTAX errors (debug each file)
3. **Low**: Fix FORMAT issues (review and restructure)
