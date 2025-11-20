# SOMA Specification: Open Issues

**Status:** Outstanding questions and clarifications needed
**Date:** 2025-11-20
**Note:** Resolved issues (_.self, >path execution) have been removed

---

## Semantic Ambiguities (Need Decision)

### 1. **Register Lifetime for Nested Blocks**

**Severity:** Medium
**Impact:** Affects how Register variables work in nested contexts

**Question:**
When blocks are nested, does each block get its own Register, or do they share?

**Example:**
```soma
{
  1 !_.x          ) Outer block sets _.x
  {
    2 !_.y        ) Inner block sets _.y
    _.x _.y >+    ) Can inner block see outer's _.x?
  } >Chain
  _.x >print      ) Is _.x still 1?
}
```

**Possible interpretations:**
1. **Fresh Register** - Each block gets completely new Register (can't see parent's `_.x`)
2. **Nested Registers** - Child can read parent's Register cells (like lexical scoping)
3. **Replaced Register** - Inner block overwrites outer's Register

**Recommendation:** Specify Register scoping rules for nested blocks

**Current assumption in docs:** Unclear - needs clarification

---

### 2. **Intermediate Cell Payloads During Auto-Creation**

**Severity:** Low
**Impact:** Edge case behavior for path creation

**Question:**
When `42 !a.b.c` creates intermediate cells `a` and `a.b`, what are their payloads?

**Example:**
```soma
42 !a.b.c       ) Creates cells a, a.b, and a.b.c
a.b >print      ) What does this print?
```

**Possible answers:**
1. Nil (empty but exist)
2. Void initially, then transition to containers
3. Undefined (implementation-specific)
4. Special "container" type

**Current assumption in docs:** Nil

**Recommendation:** Specify intermediate cell payload value

---

### 3. **Nil in Path Resolution with Children**

**Severity:** Low
**Impact:** Affects data structure design

**Question:**
If `a.b` contains Nil but `a.b.c` exists, what does `a.b.c` return?

**Example:**
```soma
Nil !a.b        ) Set a.b to Nil
23 !a.b.c       ) Create a child under a Nil cell
a.b.c           ) Does this work? Returns 23? Error?
```

**Possible interpretations:**
1. **Legal**: Nil cells can have children (they're structural containers)
2. **Error**: Can't add children to Nil (it's truly empty)
3. **Void**: Path resolution fails at Nil

**Recommendation:** Clarify if Nil cells can be structural parents

---

### 4. **Dangling CellRefs After Deletion**

**Severity:** Low
**Impact:** Reference semantics

**Question:**
What happens when you dereference a CellRef after its target Cell is deleted?

**Example:**
```soma
23 !a.b
a.b. !ref       ) Get CellRef to a.b
Void !a.b.      ) Delete the cell
ref             ) What happens here?
```

**Possible answers:**
1. **Void** - Reference is now invalid
2. **Fatal error** - Dangling reference
3. **Undefined behavior**
4. **Returns 23** - CellRef captured the value

**Recommendation:** Specify CellRef behavior after target deletion

---

### 5. **Register Deletion Semantics**

**Severity:** Low
**Impact:** Register cell lifecycle

**Question:**
Can you delete Register cells with `Void !_.path.`?

**Example:**
```soma
23 !_.x
Void !_.x.      ) Delete Register cell?
_.x             ) Void? Error?
```

**Current assumption:** Yes, Register cells can be deleted (symmetric with Store)

**Recommendation:** Explicitly confirm Register deletion semantics

---

### 6. **Error Recovery in Concurrent Threads**

**Severity:** Low
**Impact:** Threading and error handling

**Question:**
When a thread encounters a fatal error, what is the state of the Store?

**Spec says:**
> "The Store remains in its last valid state"

**Ambiguity:**
What if a multi-step operation is partially complete?

**Example:**
```soma
) Thread 1
1 !a            ) Completes
2 !b            ) Fatal error here
3 !c            ) Never executes
```

**Question:** Is `a` set to 1, or is nothing set?

**Current assumption:** `a` is set (Store is updated incrementally)

**Recommendation:** Clarify atomicity boundaries for Store operations

---

## Documentation Notes (Info Only)

These are not bugs or ambiguities - just documentation notes about implementation vs old spec.

### 7. **String Syntax: `"..."` vs `( ... )`**

**Status:** Implementation differs from old spec
**Impact:** None - new docs match implementation

**Old soma-v1.0.md describes:**
```soma
"Hello"           ) escaped strings
(Hello)           ) raw strings
```

**Current implementation (lexer.py):**
```soma
(Hello)           ) strings with \HEX\ escapes only
```

**Note:** Double-quote strings may be future work, or the old spec was aspirational

---

### 8. **Unicode Identifiers: UAX #31**

**Status:** Likely parser's responsibility
**Impact:** None currently

**Old soma-v1.0.md specifies:**
> Identifiers follow UAX #31 extended identifier syntax

**Current implementation:**
Lexer doesn't enforce Unicode rules (treats all non-whitespace as PATH candidates)

**Note:** Parser/runtime will likely handle identifier validation

---

### 9. **Modifier Semantics: Lexer vs Parser**

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
| Semantic ambiguities needing decision | 6 |
| Documentation notes (info only) | 3 |
| **Total open items** | **9** |

---

## Priority Recommendations

### Must Decide for v1.1

**High Priority:**
1. **Register scoping for nested blocks** - Affects how nested execution works

**Medium Priority:**
2. Intermediate cell payloads - Affects Store behavior
3. Nil as structural parent - Design choice for data structures
4. Dangling CellRef behavior - Reference semantics

**Low Priority:**
5. Register deletion - Likely just confirm it works like Store
6. Thread error atomicity - Can defer until concurrency implementation

---

## Notes for Implementers

**Current Implementation Status:**
- ✅ Lexer: Complete and documented
- ⏳ Parser: Not yet implemented
- ⏳ Runtime: Not yet implemented

**What's Resolved:**
- ✅ `_.self` binding is formally specified
- ✅ Register path syntax is `_.path` (where `_` is root)
- ✅ `>path` execution semantics are defined
- ✅ All examples in new docs are consistent

**What Needs Deciding:**
The 6 semantic ambiguities listed above should be resolved before implementing the parser/runtime. Particularly **Register scoping (#1)** is important as it affects execution model.

---

*This document tracks only unresolved issues. For resolved issues, see git history or the full documentation at /home/alexturner/local/soma/docs/*
