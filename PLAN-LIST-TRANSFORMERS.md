# List Transformers and Markdown Formatters - Implementation Plan

## Goal
Build general-purpose list transformation operations in stdlib to support markdown formatting and other AL/list transformation use cases.

## Motivation
To convert `Void (a) (b) (c) (d)` on AL to `Void (**a**: b) (**c**: d)` for markdown definition lists, we need:
1. AL → list transformation
2. List manipulation operations
3. List → AL transformation

This enables a powerful pattern: `AL → list → transform → list → AL`

## Phase 1: Core List Operations ✅ COMPLETE

### 1.1 Basic List Structure ✅
- **`list.new`** - Create empty list (returns Nil)
- **`list.cons`** - Prepend value to list (functional cons/stack push)
- Implementation: Pure CellRefs in Register (no Store paths)
- Tests: `tests/soma/08_list_stdlib.soma` (3 tests)
- Status: **LOCKED DOWN** - All tests passing

### 1.2 AL Draining with Context-Passing ✅
- **`al.drain`** - Generalized AL iterator with action blocks
- Signature: `[void, items..., persistent, action] → [final_persistent]`
- Action blocks receive `[current, persistent]` and return `new_persistent`
- Context-passing pattern using `_.` CellRef on AL
- Tests: `tests/soma/10_al_drain.soma` (5 tests)
- Status: **LOCKED DOWN** - Fixed accumulator bug, all tests passing

## Phase 2: List Transformations ✅ COMPLETE

### 2.1 List ↔ AL Conversions ✅
- **`list.from_al`** - Drain AL into linked list
  - Uses `al.drain` with `list.cons` action
  - Preserves AL order: `Void (a) (b) (c)` → list `(a,b,c)`

- **`list.to_al`** - Push list items onto AL
  - Traverses list, pushes each `.value` onto AL
  - Preserves order: list `(a,b,c)` → `AL: [(a), (b), (c)]`

### 2.2 List Manipulation ✅
- **`list.reverse`** - Reverse a list by copying
  - Traverses original, cons's onto new list
  - Reverses order: `(a,b,c)` → `(c,b,a)`

Tests: `tests/soma/09_list_from_al.soma` (9 tests total)
Status: **LOCKED DOWN** - All tests passing (76/76 total)

## Phase 3: List Element Transformers 🚧 NEXT

### 3.1 Map Operation
Transform each element in a list with an action block.

**Signature**: `[list, action_block] → [new_list]`
**Action**: Receives `[value]`, returns `[new_value]`

Example use case: Make every item bold
```soma
my_list { >md.b } >list.map
```

### 3.2 Filter Operation
Keep only elements that match a predicate.

**Signature**: `[list, predicate_block] → [filtered_list]`
**Predicate**: Receives `[value]`, returns `[bool]`

### 3.3 Alternating Transform
Transform every other element (for definition titles).

**Signature**: `[list, action_block] → [new_list]`
**Behavior**: Applies action to elements at indices 0, 2, 4, ...

Example: `(a) (b) (c) (d)` with `>md.b` → `(**a**) (b) (**c**) (d)`

### 3.4 Pair Operations
- **`list.pair`** - Group consecutive elements: `(a) (b) (c) (d)` → `((a,b)) ((c,d))`
- **`list.unpair`** - Flatten pairs back to flat list

## Phase 4: Markdown Formatters 📋 PLANNED

Once we have list transformers, build markdown formatters:

### 4.1 Definition Title (`md.dt`)
Transform: `(a) (b) (c) (d)` → `(**a**) (b) (**c**) (d)`
Implementation: `>list.from_al { >md.b } >list.alternate_map >list.to_al`

### 4.2 Definition List (`md.dl`)
Transform: `(a) (b) (c) (d)` → `(**a**: b) (**c**: d)`
Implementation:
1. Alternate bold: `(**a**) (b) (**c**) (d)`
2. Pair: `((**a**,b)) ((**c**,d))`
3. Join pairs with `: ` and flatten to AL

### 4.3 Definition Ordered/Unordered Lists (`md.dol`, `md.dul`)
Apply `md.dl` then wrap with `md.ol` or `md.ul`

## Design Conventions

### Naming Convention for Private Helpers
**Pattern**: `library.operation.#helper`
**Meaning**: `#` prefix indicates private/internal use only

Examples:
- `!al.drain.#loop` - Internal loop for al.drain
- `!list.to_al.#loop` - Internal loop for list.to_al
- `!list.reverse.#loop` - Internal loop for list.reverse

Benefits:
- Prevents namespace collisions
- Clear ownership of helpers
- Standard convention across stdlib

### Context-Passing Pattern
When loops need to maintain state across iterations:
1. Store state in Register with `!_.state`
2. Push context onto AL with `_.` before blocks that need it
3. Blocks pop context with `!_.` to access state
4. Return updated state for next iteration

## Test Coverage

| Operation | Tests | Status |
|-----------|-------|--------|
| list.new | 1 | ✅ Pass |
| list.cons | 2 | ✅ Pass |
| list.from_al | 3 | ✅ Pass |
| list.to_al | 3 | ✅ Pass |
| list.reverse | 3 | ✅ Pass |
| al.drain | 5 | ✅ Pass |
| **Total** | **76** | **✅ All Pass** |

## Documentation Status

### Completed ✅
- `docs/11-stdlib.md` - Full reference for list ops and al.drain
- `docs/SKILL.md` - Quick reference and cookbook examples
- `docs/09-idioms.md` - Context-passing and CellRef patterns

### TODO 📋
- Document `#` naming convention for private helpers
- Add Phase 3 operations when implemented
- Update cookbook with markdown formatter examples

## Next Steps

1. **Implement `list.map`** - Transform each element
2. **Implement `list.filter`** - Filter by predicate
3. **Implement `list.alternate_map`** - Transform alternating elements
4. **Test markdown formatters** - Build `md.dt`, `md.dl`, etc.

## Notes

- All implementations must be pure SOMA (no Python changes to VM)
- Use TDD: Write tests first, then implement
- Each operation should be general-purpose (not markdown-specific)
- Markdown formatters compose stdlib operations

---

**Last Updated**: 2025-11-30
**Status**: Phase 2 Complete (6/6 operations restored after compact), Phase 3 Next

## Recent Changes

### 2025-11-30 - Phase 2 Restoration
- Restored `list.from_al`, `list.to_al`, and `list.reverse` operations that were lost during compact
- All three operations re-implemented using pure CellRefs and context-passing pattern
- Private helpers use `#` naming convention (e.g., `list.to_al.#loop`)
- Committed in: ccf0ec9 "Restore Phase 2 list transformation operations"
