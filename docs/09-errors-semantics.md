# Error Handling and Value Semantics in SOMA

## Overview

SOMA defines a minimal, explicit error model that reflects its operational philosophy: computation is state transformation, and errors are either machine violations (fatal) or logical conditions representable in state (non-fatal). This document clarifies the critical distinctions between Nil and Void, the nature of fatal versus non-fatal conditions, the semantics of the `!` operator, and the formal rules governing Store mutation and error handling.

SOMA does not provide exceptions, stack unwinding, try/catch blocks, or recovery mechanisms. Errors are either terminal (causing thread halt) or expressible as values that program logic handles via `>Choose` and explicit branching.

## 1. Nil vs Void: CORRECTED SEMANTICS

The most critical distinction in SOMA's value model is between **Nil** and **Void**. These are fundamentally different concepts with different operational roles.

### 1.1 Nil: Valid Payload Representing Emptiness

**Nil** is a **literal value** representing intentional emptiness.

Properties:
- Nil **is a legal payload** that can be stored in any Cell
- A Cell containing Nil **exists** but has an explicitly empty value
- Nil **MAY** be pushed onto the AL
- Nil **MAY** be stored in any Cell as its payload
- Nil **MAY** be read back unchanged
- Nil does **NOT** affect Store structure

Example:
```soma
Nil !a.b.c        ; Store Nil in Cell a.b.c
a.b.c >print      ; prints "Nil"
a.b.c             ; AL = [Nil]
```

Nil represents "empty value" — the Cell exists, but it carries no meaningful data. This is useful for initialization, clearing values, or representing optional absence of data.

### 1.2 Void: Structural Non-Existence

**Void** is a **literal value** representing **the absence of a Cell**.

Properties:
- Void is **NOT a payload** — it denotes that a path does not resolve to a Cell
- Void **MAY** be pushed onto the AL
- Void **MAY** participate in AL-level logic or branching
- Void **MAY** be used in structural deletion operations
- Void **MUST NOT** be stored in any Cell
- Void **MUST NOT** appear as a payload

Example (reading non-existent paths):
```soma
x.y.z             ; If x.y.z does not exist:
                  ; AL = [Void]

x.y.z Void >==    ; AL = [True]
```

Example (structural deletion):
```soma
42 !a.b.c         ; Create Cell a.b.c with payload 42
Void !a.b.c.      ; Delete Cell a.b.c and its entire subtree
a.b.c             ; AL = [Void] — the Cell no longer exists
```

### 1.3 The Void-Payload-Invariant

This rule is **normative and absolute**:

**VOID-PAYLOAD-INVARIANT:**
> A SOMA Cell MUST NOT at any time contain Void as its payload.

If a Store mutation would require placing Void into a Cell as its payload, that operation **MUST** be treated as a **fatal error**.

This invariant preserves the semantic distinction:
- **Nil** = present but empty
- **Void** = not present at all

### 1.4 Summary Table

| Aspect | Nil | Void |
|--------|-----|------|
| Meaning | Empty value | Cell does not exist |
| Is payload? | Yes | No |
| Can store? | Yes | No (fatal error) |
| On AL? | Yes | Yes |
| Read missing path | Returns Void | N/A |
| Delete usage | N/A | `Void !path.` |

## 2. Fatal Errors

A **fatal error** occurs when the SOMA interpreter detects a violation of execution rules or machine invariants. When a fatal error occurs:

- Execution of the current thread **stops immediately**
- No cleanup is attempted
- Other threads continue unaffected
- The Store remains in its last valid state
- No unwind or rollback occurs

A fatal error is equivalent to a machine halt for that thread.

### 2.1 Fatal Error Conditions

The following conditions cause **fatal errors**:

| Error Type | Description | Example |
|------------|-------------|---------|
| AL Underflow | Popping from empty AL or insufficient values | `>drop` when AL is empty |
| Type Mismatch | Wrong value type for operation | `"hello" 5 >+` |
| Void Payload Write | Storing Void in a Cell (non-trailing-dot) | `Void !a.b` |
| Execution of Non-Block | Using `>` on non-Block value | `42 !x` then `>x` |
| Execution of Void | Using `>` on non-existent path | `>nonexistent` |
| Malformed Token | Invalid syntax | `"unterminated` |
| Invalid Built-in Contract | Built-in called with wrong AL state | `>dup` when AL is empty |

#### 2.1.1 AL Underflow
Attempting to pop a value when the AL is empty, or when fewer values are present than required by an operation.

```soma
>drop             ; Fatal: AL is empty
```

```soma
1 >+              ; Fatal: >+ requires two values, only one present
```

#### 2.1.2 Type Mismatches
Performing an operation on a value of the wrong type.

```soma
"hello" 5 >+      ; Fatal: >+ requires integers, got string
```

```soma
42 { >dup } >Choose   ; Fatal: >Choose requires Boolean + 2 Blocks
```

#### 2.1.3 Void !path (Illegal Payload Write)
Attempting to store Void as a Cell payload (non-trailing-dot write).

**Store examples:**
```soma
Void !a.b         ; Fatal: cannot store Void as payload
```

**Register examples:**
```soma
Void !_.x         ; Fatal: cannot store Void as payload in Register
Void !_.temp      ; Fatal: cannot store Void as payload in Register
```

This is **illegal** because it would violate the Void-Payload-Invariant. Void represents non-existence and cannot be contained.

**Correct alternative** (structural deletion):
```soma
Void !a.b.        ; Legal: structural delete in Store
Void !_.x.        ; Legal: structural delete in Register
```

#### 2.1.4 Malformed Tokens
Invalid syntax, unterminated strings, unterminated blocks, or illegal characters.

```soma
"unterminated     ; Fatal: unterminated string literal
```

```soma
{ 1 2 >+          ; Fatal: unterminated block
```

```soma
@#$%              ; Fatal: invalid token
```

#### 2.1.5 Invalid Built-in Contracts
Calling a built-in without satisfying its AL contract.

```soma
>dup              ; Fatal if AL is empty
```

```soma
True { 1 } >Choose    ; Fatal: >Choose requires 3 values (Boolean + 2 Blocks)
```

#### 2.1.6 Execution of Non-Block Values
Attempting to execute a value that is not a Block using the `>` prefix.

The `>` prefix operator reads a value at a path and executes it. If the value at that path is not a Block, this is a fatal error.

**Store examples:**
```soma
42 !not_a_block
>not_a_block      ; Fatal: cannot execute Integer (not a Block)
```

```soma
"hello" !greeting
>greeting         ; Fatal: cannot execute String (not a Block)
```

**Register examples:**
```soma
{
  100 !_.value
  >_.value        ; Fatal: cannot execute Integer (not a Block)
}
```

#### 2.1.7 Execution of Void
Attempting to execute Void using the `>` prefix.

```soma
>nonexistent      ; If path "nonexistent" does not exist, resolves to Void
                  ; Fatal: cannot execute Void
```

```soma
{
  _.missing       ; AL = [Void] if _.missing doesn't exist
  !_.target
  >_.target       ; Fatal: cannot execute Void
}
```

**Correct alternative** (test before executing):
```soma
user.action
Void >==
  { "No action defined" >print }
  { >user.action }
>Choose
```

## 3. Non-Fatal Conditions

The following conditions are **NOT fatal** and must be handled by program logic:

### 3.1 Void Path Resolution
Reading a path that does not exist simply returns Void. This is a **normal operation**.

```soma
x.y.z             ; If x.y.z doesn't exist, AL = [Void]
                  ; No error — Void is a valid value
```

This allows programs to test for existence:

```soma
config.user.name
Void >==
  { "No user configured" >print }
  { config.user.name >print }
>Choose
```

### 3.2 Nil Values
Reading a Cell that contains Nil returns Nil. This is a **valid payload** and not an error.

```soma
Nil !settings.theme
settings.theme    ; AL = [Nil] — perfectly valid
```

### 3.3 Logical Errors
Conditions like "file not found", "invalid input", or "operation failed" are **not runtime errors**. They are represented as values (Booleans, symbols, error records) on the AL and handled via `>Choose`.

```soma
; Hypothetical file operation that pushes success/failure
"data.txt" >file_exists
  { "data.txt" >load }
  { "File not found" >print }
>Choose
```

## 4. The ! Operator: Store Mutation Semantics

The `!` operator is SOMA's primary mutation mechanism. Its behavior depends on the form of the path and the value being written.

### 4.1 Syntax Forms

```soma
Val !path         ; Payload write (creates Cells as needed)
Val !path.        ; Cell replacement (discards existing structure)
Void !path.       ; Structural deletion (special case)
```

### 4.2 Payload Write: `Val !path`

Semantics:
- Creates all missing Cells in the path
- Sets the target Cell's payload to `Val`
- Preserves identity of existing Cells
- Does **NOT** affect child Cells

Example:
```soma
42 !a.b.c         ; Creates a, a.b, a.b.c if needed
                  ; Sets a.b.c payload to 42
```

**Fatal Error Rule:**
```soma
Void !a.b         ; Fatal: cannot store Void as payload
```

### 4.3 Cell Replacement: `Val !path.`

The trailing dot indicates **structural replacement**.

Semantics:
- The existing Cell (if any) is discarded
- A new Cell is created at that location
- The new Cell's payload is set to `Val`
- All child Cells are removed

Example:
```soma
1 !a.b
2 !a.b.c
3 !a.b.d          ; a.b has children c and d

99 !a.b.          ; Replace entire Cell at a.b
a.b.c             ; AL = [Void] — children were discarded
a.b               ; AL = [99]
```

### 4.4 Structural Deletion: `Void !path.`

This is the **only legal use of Void** in a Store write operation.

Semantics:
- If the Cell exists, delete it and its entire subtree
- If the Cell does not exist, no action is taken
- No error occurs in either case

Example:
```soma
42 !a.b.c
a.b.c             ; AL = [42]

Void !a.b.        ; Delete Cell a.b and all descendants
a.b.c             ; AL = [Void] — Cell no longer exists
a.b               ; AL = [Void] — Cell no longer exists
```

### 4.5 Summary of ! Operator Rules

| Form | Meaning | Creates Cells? | Fatal if Void? |
|------|---------|----------------|----------------|
| `Val !path` | Payload write (Store) | Yes | **Yes** |
| `Val !_.path` | Payload write (Register) | Yes | **Yes** |
| `Val !path.` | Cell replacement (Store) | No (replaces) | No |
| `Val !_.path.` | Cell replacement (Register) | No (replaces) | No |
| `Void !path.` | Structural delete (Store) | No | No |
| `Void !_.path.` | Structural delete (Register) | No | No |
| `Void !path` | **ILLEGAL** (Store) | N/A | **Yes** |
| `Void !_.path` | **ILLEGAL** (Register) | N/A | **Yes** |

## 5. Formal Rules

This section provides formal semantics for Store operations and error conditions.

### 5.1 Write Rules

**Rule W1: Payload Write (Store and Register)**
```
Precondition:  AL = [Val, ...]
               Val ≠ Void
Token:         !path  (Store: a.b.c)
               !_.path (Register: _.x.y)
Effect:        Create Cells for missing segments of path
               Set Cell(path).payload = Val
               AL' = [...]
```

**Rule W2: Payload Write with Void (Fatal)**
```
Precondition:  AL = [Void, ...]
Token:         !path (Store, non-trailing-dot)
               !_.path (Register, non-trailing-dot)
Effect:        FATAL ERROR
               Thread halts immediately
               Store/Register unchanged
               AL unchanged
```

**Rule W3: Cell Replacement (Store and Register)**
```
Precondition:  AL = [Val, ...]
Token:         !path. (Store)
               !_.path. (Register)
Effect:        Delete Cell(path) and all descendants
               Create new Cell(path)
               Set Cell(path).payload = Val
               AL' = [...]
```

**Rule W4: Structural Deletion (Store and Register)**
```
Precondition:  AL = [Void, ...]
Token:         !path. (Store)
               !_.path. (Register)
Effect:        If Cell(path) exists:
                 Delete Cell(path) and all descendants
               Else:
                 No action
               AL' = [...]
```

### 5.2 Read Rules

**Rule R1: Value Read (Cell Exists)**
```
Precondition:  Cell(path) exists
Token:         path (Store: a.b.c)
               _.path (Register: _.x.y)
Effect:        AL' = [Cell(path).payload, ...]
               (payload may be Nil or any other value)
```

**Rule R2: Value Read (Cell Does Not Exist)**
```
Precondition:  Cell(path) does not exist
Token:         path (Store)
               _.path (Register)
Effect:        AL' = [Void, ...]
               No error
```

**Rule R3: CellRef Read (Cell Exists)**
```
Precondition:  Cell(path) exists
Token:         path. (Store)
               _.path. (Register)
Effect:        AL' = [CellRef(path), ...]
```

**Rule R4: CellRef Read (Cell Does Not Exist)**
```
Precondition:  Cell(path) does not exist
Token:         path. (Store)
               _.path. (Register)
Effect:        AL' = [Void, ...]
               No error
```

### 5.3 Cell Creation Rules

**Rule C1: Automatic Creation During Write**
```
When executing: Val !a.b.c (Store)
            or: Val !_.x.y (Register)

If path a (or _.x) does not exist:
  Create Cell(a) or Cell(_.x) with payload Nil
If path a.b (or _.x.y) does not exist:
  Create Cell(a.b) or Cell(_.x.y) with payload Nil
Create/update Cell(a.b.c) or Cell(_.x.y.z) with payload Val
```

All intermediate Cells are created with Nil payloads unless otherwise specified.

### 5.4 Cell Deletion Rules

**Rule D1: Structural Deletion Propagates**
```
When executing: Void !a.b. (Store)
            or: Void !_.x. (Register)

Effect:
  If Cell(a.b) or Cell(_.x) exists:
    Delete Cell(a.b.c) or Cell(_.x.y) for all children c or y
    Delete Cell(a.b) or Cell(_.x) itself
  Paths a.b.* or _.x.* become non-existent
  Reading a.b.x or _.x.y returns Void
```

**Rule D2: Deletion of Non-Existent Cells**
```
When executing: Void !x.y.z. (Store)
            or: Void !_.x.y. (Register)

If Cell(x.y.z) or Cell(_.x.y) does not exist:
  No action
  No error
```

### 5.5 Error Condition Rules

**Rule E1: AL Underflow**
```
When: Any operation requires N values on AL
      but |AL| < N
Effect: FATAL ERROR
```

**Rule E2: Type Mismatch**
```
When: Built-in requires type T
      but AL top is type U ≠ T
Effect: FATAL ERROR
```

**Rule E3: Void Payload Write**
```
When: AL = [Void, ...]
      Token = !path (Store, non-trailing-dot)
           or !_.path (Register, non-trailing-dot)
Effect: FATAL ERROR
```

**Rule E4: Malformed Path**
```
When: Token does not conform to path grammar
      (e.g., _x without dot, invalid characters)
Effect: FATAL ERROR
```

**Rule E5: Execution of Non-Block**
```
When: Token = >path (Store) or >_.path (Register)
      Value at path is not a Block
Effect: FATAL ERROR
        Thread halts immediately
```

**Rule E6: Execution of Void**
```
When: Token = >path (Store) or >_.path (Register)
      Path does not exist (resolves to Void)
Effect: FATAL ERROR
        Thread halts immediately
```

## 6. Examples: Correct and Incorrect Usage

### 6.1 Correct: Using Nil for Optional Values

```soma
; Initialize configuration with optional fields
Nil !config.theme
Nil !config.language
"Admin" !config.username

; Check and use
config.theme Nil >==
  { "default" !config.theme }
  { }
>Choose
```

### 6.2 Correct: Using Void for Existence Testing

```soma
; Test if a path exists
user.profile.avatar
Void >==
  { "No avatar set" >print }
  { user.profile.avatar >display }
>Choose
```

### 6.3 Correct: Structural Deletion

```soma
; Create structure
1 !cache.session.data.key1
2 !cache.session.data.key2

; Delete entire session subtree
Void !cache.session.

; Verify deletion
cache.session.data.key1    ; AL = [Void]
```

### 6.4 Incorrect: Attempting to Store Void

```soma
; This is ILLEGAL and causes fatal error
Void !user.status

; Thread halts immediately
; No Store mutation occurs
```

### 6.5 Correct: Clearing a Value with Nil

```soma
; Set a value
"active" !user.status

; Clear it (Cell still exists)
Nil !user.status

; Read it back
user.status       ; AL = [Nil]
```

### 6.6 Correct: Deleting a Value with Void

```soma
; Set a value
"active" !user.status

; Delete the Cell entirely
Void !user.status.

; Read it back
user.status       ; AL = [Void] — Cell no longer exists
```

### 6.7 Correct: Non-Fatal Error Handling

```soma
; Function that may fail, represented as Boolean + value/message

; Hypothetical: divide operation that checks for zero
5 0 >safe_divide

; AL now has: [False, "Division by zero"]
; Handle it:
  { "Error: " >concat >print }
  { >print }
>Choose
```

### 6.8 Register Examples: Correct Usage

```soma
; Store values in Register paths
42 !_.counter
"data" !_.cache.key

; Read Register values
_.counter            ; AL = [42]
_.cache.key          ; AL = ["data"]

; Delete Register Cell structure
Void !_.cache.       ; Delete _.cache and all descendants
_.cache.key          ; AL = [Void] — Cell no longer exists
```

### 6.9 Register Examples: Incorrect Usage

```soma
; ILLEGAL: Attempting to store Void in Register (fatal error)
Void !_.status

; LEGAL: Structural deletion with trailing dot
Void !_.status.

; LEGAL: Store Nil in Register (Cell exists but empty)
Nil !_.status
_.status             ; AL = [Nil]
```

### 6.10 Incorrect: Executing Non-Block Values

```soma
; Store an integer
42 !answer

; ILLEGAL: Attempting to execute it (fatal error)
>answer
; Thread halts: cannot execute Integer (not a Block)
```

```soma
; Store a string
"Hello" !message

; ILLEGAL: Attempting to execute it (fatal error)
>message
; Thread halts: cannot execute String (not a Block)
```

### 6.11 Incorrect: Executing Void (Non-Existent Path)

```soma
; Attempt to execute a path that doesn't exist
>undefined_function
; Thread halts: path resolves to Void, cannot execute Void
```

```soma
; Delete a block, then try to execute it
{ (Hello) >print } !greet
Void !greet.          ; Delete the Cell

>greet                ; FATAL: path now resolves to Void
```

### 6.12 Correct: Testing Before Execution

```soma
; Store a block at an optional path
{ (Default handler) >print } !handlers.default

; Safe execution: test before executing
handlers.custom
Void >==
  { >handlers.default }    ; Use default if custom doesn't exist
  { >handlers.custom }     ; Use custom if it exists
>Choose
```

```soma
; Verify a value is a Block before executing
config.startup
Void >==
  { "No startup action" >print }
  {
    config.startup >IsBlock
      { >config.startup }
      { "Startup value is not executable" >print }
    >Choose
  }
>Choose
```

### 6.13 Correct: Executable vs Non-Executable Values

```soma
; Blocks are executable
{ 1 2 >+ } !add_block
>add_block            ; Legal: executes block, AL = [3]

; Other values are data, not executable
42 !number
number                ; Legal: pushes 42 onto AL
>number               ; ILLEGAL: fatal error (not a Block)

; Built-ins are just Blocks stored at paths
print !my_print       ; Store the print block elsewhere
>my_print             ; Legal: executes the print block
```

## 7. Ambiguities and Open Questions

Based on this analysis, the following potential ambiguities or areas for clarification remain:

### 7.1 Intermediate Cell Payloads During Auto-Creation

When executing `42 !a.b.c.d.e`, the specification states that intermediate Cells are created. The formal rule states they receive Nil payloads. However, the original specification (Section 5.5) does not explicitly state what payload intermediate Cells receive.

**Recommendation:** The specification should explicitly state in Section 5.5:
> "When a write operation creates intermediate Cells (e.g., `a` and `a.b` when writing to `a.b.c`), those Cells are created with a payload of **Nil**."

### 7.2 Behavior of `Void !_.path` in Registers

The specification defines Store behavior comprehensively but is less explicit about Register behavior. Since Registers are "identical in every way other than scope" to the Store, the same rules should apply.

**Confirmed Rules for Registers:**
- `Void !_.x` is a **fatal error** (same as `Void !x` — cannot store Void as payload)
- `Void !_.x.` **deletes the Register Cell** (same as `Void !x.` — structural deletion)

Example (fatal error):
```soma
Void !_.status       ; Fatal: cannot store Void as payload in Register
```

Example (valid structural deletion):
```soma
42 !_.temp.data
_.temp.data          ; AL = [42]

Void !_.temp.        ; Delete Register Cell _.temp and descendants
_.temp.data          ; AL = [Void] — Cell no longer exists
```

### 7.3 Error Recovery in Concurrent Threads

Section 14.7 states that a fatal error in one thread does not affect other threads, and the Store remains in its "last valid state." However, with concurrent writes, the interleaving of operations may make "last valid state" ambiguous.

**Recommendation:** Clarify that:
> "When a thread encounters a fatal error, the Store reflects all completed operations up to (but not including) the operation that caused the error. Other threads observe Store state as of their own execution timeline. SOMA does not define memory ordering guarantees between threads."

### 7.4 Can CellRefs Point to Non-Existent Cells?

If a CellRef is obtained via `a.b.`, then `Void !a.b.` deletes the Cell, what happens to existing CellRefs?

**Recommendation:** Clarify:
> "A CellRef that points to a deleted Cell becomes a dangling reference. Attempting to dereference it (read through it) returns Void. Attempting to write through it recreates the Cell at that location."

### 7.5 Nil in Path Resolution

When a path like `a.b.c` is resolved, if `a.b` has payload Nil (not a structure), does resolution fail?

**Implication:** The specification treats Cells as having both a payload and potential children. A Cell with payload Nil can still have children.

**Recommendation:** Explicitly state:
> "A Cell may simultaneously have a payload (including Nil) and child Cells. The payload and children are orthogonal. Reading `a.b` returns the payload; reading `a.b.c` traverses to child `c` regardless of `a.b`'s payload."

## 8. Conclusion

SOMA's error model is intentionally minimal and explicit:

- **Fatal errors** terminate execution when machine invariants are violated
- **Non-fatal conditions** are represented as values and handled via explicit control flow
- **Nil** represents an empty value and is a legal, storable payload
- **Void** represents structural non-existence and cannot be stored
- The **! operator** creates, replaces, and deletes Cells based on path form and value type
- **No exceptions, unwinding, or recovery** mechanisms exist

This model forces programmers to handle error conditions explicitly through state inspection and branching, reflecting SOMA's philosophy that computation is observable state transformation, not hidden symbolic reduction.

By preserving the strict distinction between Nil (empty value) and Void (no Cell), SOMA maintains a clean, inspectable Store model where presence, absence, and emptiness are all first-class, observable concepts.
