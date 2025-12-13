# Error Handling and Value Semantics in SOMA

## Overview

SOMA defines a minimal, explicit error model that reflects its operational philosophy: computation is state transformation, and errors are either machine violations )fatal) or logical conditions representable in state )non-fatal). This document clarifies the critical distinctions between Nil and Void, the nature of fatal versus non-fatal conditions, the semantics 

of the 

`!` operator, and the formal rules governing Store mutation and error handling.

SOMA does not provide exceptions, stack unwinding, try/catch blocks, or recovery mechanisms. Errors are either terminal )causing thread halt) or expressible as values that program 

logic handles via 

`>choose` and explicit branching.

## 1. Nil vs Void: The Fundamental Distinction

The most critical distinction in SOMA's value model is between 

**Nil**

 and 

**Void**

. These represent fundamentally different semantic concepts:

- **Void** = "This cell has never been explicitly set" )absence, uninitialized)
- **Nil** = "This cell has been explicitly set to empty/nothing" )presence of emptiness)

This distinction mirrors several important concepts in computer science:

- **In logic:** Void = logical absurdity )⊥) vs Nil = the empty set )∅)
- **In type theory:** Void = bottom type vs Nil = unit type / Maybe Nothing
- **In programming:** Void = `undefined` )JavaScript) vs Nil = `null`/`None`/`nil`
- **In databases:** Void = column never inserted vs Nil = NULL value explicitly inserted

**The key insight:** "Never set" is semantically different from "set to nothing."

### 1.1 Nil: Explicit Emptiness

**Nil**

 is a 

**literal value** representing intentional, explicit emptiness.

Properties:

- Nil **is a legal payload** that can be stored in any Cell
- A Cell containing Nil **has been explicitly set** )but to an empty value)
- Nil **MAY** be pushed onto the AL
- Nil **MAY** be stored in any Cell as its payload
- Nil **MAY** be read back unchanged
- Nil does **NOT** affect Store structure
- Nil represents **deliberate choice** to have no value

**Important:**

 Cells with Nil value can still have children. A Cell's value and its subpaths )children) are completely orthogonal — setting or reading one does not affect the other.

Example )basic usage):

```soma
Nil !config.middle_name        ) Explicitly set to empty
config.middle_name             ) AL = [Nil] — was set, but to nothing
config.middle_name >isVoid     ) False — has been set
```

Example )Nil with children):

```soma
Nil !a.b          ) Set a.b's VALUE to Nil
23 !a.b.c         ) Create child 'c' in a.b's SUBPATHS

a.b               ) Returns Nil )reads a.b's VALUE)
a.b.c             ) Returns 23 )traverses a.b's SUBPATHS to c)
```

Nil represents "explicitly empty" — the Cell exists and has been set, but it carries the value "nothing." This is useful for representing optional fields that are intentionally left empty.

### 1.2 Void: Never Set / Uninitialized

**Void**

 is a 

**literal value**

 representing 

**cells that have never been explicitly set**.

Properties:

- Void is **NOT a writable payload** — you cannot write Void to a cell
- Void **denotes uninitialized state** — cells auto-created during path writes
- Void **MAY** be pushed onto the AL )when reading unset paths)
- Void **MAY** participate in AL-level logic or branching
- Void **MAY** be used in structural deletion operations )`Void !path.`)
- Void **MUST NOT** be written as a payload )`Void !path` is fatal)
- Void represents **structural scaffolding** — cells that exist for structure but were never given values

**Important:**

 Cells with Void value can still have children. A Cell's value and its subpaths )children) are completely orthogonal — setting or reading one does not affect the other.

Example )reading never-set paths):

```soma
42 !a.b.c         ) Auto-vivifies a and a.b with Void payload
a.b.c             ) Returns 42 )explicitly set)
a.b               ) Returns Void )auto-vivified, never set)
a                 ) Returns Void )auto-vivified, never set)

a.b >isVoid       ) True — never explicitly set
```

Example )Void with children):

```soma
42 !parent.child  ) Auto-vivifies parent with Void value
parent            ) Returns Void )parent's VALUE)
parent.child      ) Returns 42 )traverses parent's SUBPATHS)
```

Example )structural deletion):

```soma
42 !a.b.c         ) Create Cell a.b.c with payload 42
Void !a.b.c.      ) Delete Cell a.b.c and its entire subtree
a.b.c             ) AL = [Void] — the Cell no longer exists
```

## Conclusion

SOMA's error model is intentionally minimal and explicit:

- **Fatal errors** terminate execution when machine invariants are violated
- **Non-fatal conditions** are represented as values and handled via explicit control flow
- **Strict read semantics** — reading undefined paths raises RuntimeError
- **Auto-vivified paths can be read** — writing to nested paths creates intermediate cells with Void
- **Nil** represents explicit emptiness — deliberately set to "nothing"
- **Void** represents "never set" in auto-vivified cells
- **The ! operator** creates, replaces, and deletes Cells based on path form
- **CellRefs** are immutable values that provide access to Cells
- **Cells persist independently of paths** — no "dangling" references
- **No exceptions, unwinding, or recovery** mechanisms exist

This model forces programmers to handle error conditions explicitly through state inspection and branching, reflecting SOMA's philosophy that computation is observable state transformation.


