# SOMA Specification: Open Issues

**Status:** Outstanding questions and clarifications needed
**Date:** 2025-11-20
**Note:** Resolved issues (_.self, >path execution, Register isolation) have been removed
**Latest:** Register isolation for nested blocks resolved 2025-11-20 - complete isolation model adopted

---

## Semantic Ambiguities (Need Decision)

**All semantic ambiguities resolved!**

---

## Documentation Notes (Info Only)

These are not bugs or ambiguities - just documentation notes about implementation vs old spec.

### 3. **Modifier Semantics: Lexer vs Parser**

**Status:** Design decision - lexer emits tokens, parser handles semantics
**Impact:** None - this is correct

**Old soma-v1.0.md conflates:**
- `>` as part of built-in names (e.g., `>print`)
- `>` as a prefix modifier token

**Current implementation:**
- Lexer emits `>` as separate EXEC token
- `>print` becomes two tokens: EXEC(">") + PATH("print")

**Note:** This is the correct approach - lexer is purely syntactic

---

## Summary

| Category | Count |
|----------|-------|
| Semantic ambiguities needing decision | 0 |
| Documentation notes (info only) | 1 |
| **Total open items** | **1** |

---

## Priority Recommendations

### All Semantic Ambiguities Resolved!

**Completed:**
1. Register deletion - confirmed it works identically to Store deletion (symmetric)
2. Memory model - happens-before model adopted, implementation-defined details

**Remaining:**
Only documentation note #3 (Modifier Semantics) remains - this is informational, not a semantic ambiguity.

---

## Notes for Implementers

**Current Implementation Status:**
- ✅ Lexer: Complete and documented
- ⏳ Parser: Not yet implemented
- ⏳ Runtime: Not yet implemented

**What's Resolved:**
- ✅ Block self-reference - replaced `_.self` magic binding with `>block` built-in (enables internationalization, removes special case)
- ✅ Register path syntax is `_.path` (where `_` is root)
- ✅ `>path` execution semantics are defined
- ✅ Register isolation for nested blocks (complete isolation, no nesting, fresh Register per block)
- ✅ Void vs Nil semantics - auto-vivified cells start with Void payload
- ✅ All examples in new docs are consistent
- ✅ Cell architecture - value and subpaths are orthogonal; any value can have children
- ✅ CellRef semantics - CellRefs are immutable values; Cells persist independently of paths; no dangling references
- ✅ Register deletion - works identically to Store deletion (symmetric)
- ✅ Memory model - happens-before model, implementation-defined details

**What Needs Deciding:**
Nothing! All semantic ambiguities are resolved.

---

**All semantic ambiguities resolved! Ready for implementation.**

*This document tracks only unresolved issues. For resolved issues, see git history or the full documentation at /home/alexturner/local/soma/docs/*
