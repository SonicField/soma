# Error Handling and Value Semantics in SOMA

## Overview

SOMA defines a minimal, explicit error model that reflects its operational philosophy: computation is state transformation, and errors are either machine violations (fatal) or logical conditions representable in state (non-fatal). This document clarifies the critical distinctions between Nil and Void, the nature of fatal versus non-fatal conditions, the semantics of the `!` operator, and the formal rules governing Store mutation and error handling.

SOMA does not provide exceptions, stack unwinding, try/catch blocks, or recovery mechanisms. Errors are either terminal (causing thread halt) or expressible as values that program logic handles via `>choose` and explicit branching.

## 1. Nil vs Void: The Fundamental Distinction

The most critical distinction in SOMA's value model is between **Nil** and **Void**. These represent fundamentally different semantic concepts:

- **Void** = "This cell has never been explicitly set" (absence, uninitialized)
- **Nil** = "This cell has been explicitly set to empty/nothing" (presence of emptiness)

This distinction mirrors several important concepts in computer science:
- **In logic:** Void = logical absurdity (⊥) vs Nil = the empty set (∅)
- **In type theory:** Void = bottom type vs Nil = unit type / Maybe Nothing
- **In programming:** Void = `undefined` (JavaScript) vs Nil = `null`/`None`/`nil`
- **In databases:** Void = column never inserted vs Nil = NULL value explicitly inserted

**The key insight:** "Never set" is semantically different from "set to nothing."

### 1.1 Nil: Explicit Emptiness

**Nil** is a **literal value** representing intentional, explicit emptiness.

Properties:
- Nil **is a legal payload** that can be stored in any Cell
- A Cell containing Nil **has been explicitly set** (but to an empty value)
- Nil **MAY** be pushed onto the AL
- Nil **MAY** be stored in any Cell as its payload
- Nil **MAY** be read back unchanged
- Nil does **NOT** affect Store structure
- Nil represents **deliberate choice** to have no value

**Important:** Cells with Nil value can still have children. A Cell's value and its subpaths (children) are completely orthogonal — setting or reading one does not affect the other.

Example (basic usage):
```soma
Nil !config.middle_name        ; Explicitly set to empty
config.middle_name             ; AL = [Nil] — was set, but to nothing
config.middle_name >isVoid     ; False — has been set
```

Example (Nil with children):
```soma
Nil !a.b          ; Set a.b's VALUE to Nil
23 !a.b.c         ; Create child 'c' in a.b's SUBPATHS

a.b               ; Returns Nil (reads a.b's VALUE)
a.b.c             ; Returns 23 (traverses a.b's SUBPATHS to c)
```

Nil represents "explicitly empty" — the Cell exists and has been set, but it carries the value "nothing." This is useful for representing optional fields that are intentionally left empty.

### 1.2 Void: Never Set / Uninitialized

**Void** is a **literal value** representing **cells that have never been explicitly set**.

Properties:
- Void is **NOT a writable payload** — you cannot write Void to a cell
- Void **denotes uninitialized state** — cells auto-created during path writes
- Void **MAY** be pushed onto the AL (when reading unset paths)
- Void **MAY** participate in AL-level logic or branching
- Void **MAY** be used in structural deletion operations (`Void !path.`)
- Void **MUST NOT** be written as a payload (`Void !path` is fatal)
- Void represents **structural scaffolding** — cells that exist for structure but were never given values

**Important:** Cells with Void value can still have children. A Cell's value and its subpaths (children) are completely orthogonal — setting or reading one does not affect the other.

Example (reading never-set paths):
```soma
42 !a.b.c         ; Auto-vivifies a and a.b with Void payload
a.b.c             ; Returns 42 (explicitly set)
a.b               ; Returns Void (auto-vivified, never set)
a                 ; Returns Void (auto-vivified, never set)

a.b >isVoid       ; True — never explicitly set
```

Example (Void with children):
```soma
42 !parent.child  ; Auto-vivifies parent with Void value
parent            ; Returns Void (parent's VALUE)
parent.child      ; Returns 42 (traverses parent's SUBPATHS)
```

Example (structural deletion):
```soma
42 !a.b.c         ; Create Cell a.b.c with payload 42
Void !a.b.c.      ; Delete Cell a.b.c and its entire subtree
a.b.c             ; AL = [Void] — the Cell no longer exists
```

### 1.3 Void as a Storable Value

Void can be written as a normal value:

**Writing Void is legal:**
```soma
Void !a.b         ; LEGAL — stores Void as payload
Void !_.x         ; LEGAL — stores Void in Register
```

**Structural deletion (trailing dot) is also legal:**
```soma
Void !a.b.        ; LEGAL — delete the cell entirely
Void !_.x.        ; LEGAL — delete Register cell entirely
```

**Cells also START as Void via auto-vivification:**
```soma
42 !a.b.c         ; Creates: a (Void), a.b (Void), a.b.c (42)
                  ; Intermediate cells auto-created with Void payload
a.b               ; Returns Void — never explicitly set
```

This invariant preserves the semantic distinction while allowing sparse data structures:
- You **cannot deliberately write** Void as a payload
- Cells **can be auto-created** with Void payload (structural scaffolding)
- **Nil** = explicitly set to empty
- **Void** = never explicitly set (but may exist for structure)

### 1.4 Summary Table

| Aspect | Nil | Void |
|--------|-----|------|
| Meaning | Explicitly set to empty | Never set / uninitialized |
| Is payload? | Yes | Yes (but only via auto-vivification) |
| Can write? | Yes (`Nil !path`) | No (`Void !path` is fatal) |
| On AL? | Yes | Yes |
| Read missing path | Returns Void | N/A |
| Delete usage | N/A | `Void !path.` |
| Semantic intent | Intentional emptiness | Structural scaffolding |

### 1.5 Auto-Vivification: How Cells Start as Void

When you write to a deep path, SOMA automatically creates intermediate cells. These auto-created cells start with **Void** payload — they exist for structural purposes but have never been explicitly set.

**Example 1: Basic Auto-Vivification**
```soma
42 !a.b.c         ; Creates cells a, a.b, a.b.c

a.b.c             ; Returns 42 (explicitly set)
a.b               ; Returns Void (auto-vivified, never set)
a                 ; Returns Void (auto-vivified, never set)
```

**Resulting structure:**
```
Store:
  a → Cell(payload: Void, children: {...})
    └─ b → Cell(payload: Void, children: {...})
         └─ c → Cell(payload: 42, children: {})
```

**Example 2: Void vs Nil Detection**
```soma
42 !data.b.c           ; Auto-vivifies data and data.b with Void

data.b >isVoid         ; True — never explicitly set
data.b                 ; Returns Void
data.b >isVoid
  { (Never set) >print }
  { (Has been set) >print }
>ifelse                ; Prints "Never set"

Nil !data.b            ; Explicitly set to Nil

data.b >isVoid         ; False — now has been set (to Nil)
data.b                 ; Returns Nil (not Void!)
data.b >isVoid
  { (Never set) >print }
  { (Has been set) >print }
>ifelse                ; Prints "Has been set"
```

**Example 3: Sparse Data Structures**
```soma
; Create a sparse array structure
1 !array.0
2 !array.2
3 !array.5

; Intermediate indices were never set
array.1         ; Void — index 1 was never set
array.3         ; Void — index 3 was never set
array.4         ; Void — index 4 was never set

; We can detect unset vs set-to-empty
array.1 >isVoid
  { (uninitialized) >print }
  { array.1 >toString >print }
>ifelse
```

**Example 4: Distinguishing Nil from Void**
```soma
(John) !person.name
Nil !person.middle_name         ; Explicitly no middle name
42 !person.age

person.middle_name              ; Nil — explicitly set to empty
person.middle_name >isVoid      ; False — has been set

; To check for undefined fields, initialize first:
Nil !person.spouse              ; Initialize as Nil (no spouse)
person.spouse                   ; Nil — can now read safely
person.spouse >isVoid           ; False — has been set (to Nil)
```

**Key insight:** Auto-vivification creates **structural scaffolding** with Void payload. You can later set these cells explicitly if needed, changing them from Void to whatever value you choose.

## 2. Fatal Errors

A **fatal error** occurs when the SOMA interpreter detects a violation of execution rules or machine invariants. When a fatal error occurs:

- Execution of the current thread **stops immediately**
- No cleanup is attempted
- Other threads continue unaffected
- The Store remains in a **valid state** (no corruption, see Section 7.3)
- Individual operations are **atomic** (either complete or don't occur)
- Cross-thread visibility is **implementation-defined** (depends on memory model)
- No unwind or rollback occurs

A fatal error is equivalent to a machine halt for that thread.

**Note on "valid state":** This means the Store has no corrupted data structures. It does NOT mean that all operations before the error necessarily completed. See Section 7.3 for details on error recovery and the memory model.

### 2.1 Fatal Error Conditions

The following conditions cause **fatal errors**:

| Error Type | Description | Example |
|------------|-------------|---------|
| AL Underflow | Popping from empty AL or insufficient values | `>drop` when AL is empty |
| Type Mismatch | Wrong value type for operation | `"hello" 5 >+` |
| Void Payload Write | Storing Void in a Cell (non-trailing-dot) | `Void !a.b` |
| Execution of Non-Block | Using `>` on non-Block value | `42 !x` then `>x` |
| Execution of Void | Using `>` on non-existent path | `>nonexistent` |
| Register Isolation Violation | Inner block accessing outer Register path | `>{1 !_.n >{_.n >print}}` |
| Register Access After Block Ends | Accessing Register after block completes | `>{23 !_.x} _.x >print` |
| Malformed Token | Invalid syntax | `"unterminated` |
| Invalid Built-in Contract | Built-in called with wrong AL state | `>dup` when AL is empty |
| Undefined Path Read | Reading path that was never created | `x.y.z` when x was never written |

**Note on strict read semantics:** SOMA now errors when reading undefined paths. Auto-vivified paths (created during writes) CAN be read and return Void. See Section 3.1 for details.

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
42 { >dup } >choose   ; Fatal: >choose requires Boolean + 2 Blocks
```

#### 2.1.3 Void !path (Legal Payload Write)
Storing Void as a Cell payload is now legal (was previously an error).

**Store examples:**
```soma
Void !a.b         ; Legal: stores Void as payload
```

**Register examples:**
```soma
Void !_.x         ; Legal: stores Void as payload in Register
Void !_.temp      ; Legal: stores Void as payload in Register
```

Writing Void as a value is legal in both Store and Register.

**Reading Void is also legal:**
```soma
42 !a.b.c         ; Auto-vivifies a and a.b with Void payload
a.b               ; Returns Void — this is perfectly legal!
a                 ; Returns Void — no error, just means "never set"
```

**Structural deletion (trailing dot):**
```soma
Void !a.b.        ; Legal: structural delete in Store
Void !_.x.        ; Legal: structural delete in Register
```

**Correct alternative** (auto-vivification):
```soma
; Don't write Void — let auto-vivification handle it
42 !a.b.c         ; a.b is Void automatically (structural scaffolding)

; Or write Nil explicitly if you want "set to empty"
Nil !a.b          ; Explicitly empty (different from never-set!)
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
True { 1 } >choose    ; Fatal: >choose requires 3 values (Boolean + 2 Blocks)
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
  { (No action defined) >print }
  { >user.action }
>ifelse
```

#### 2.1.8 Register Isolation Violation
Inner blocks have completely isolated Registers. Attempting to read a Register path that was set in an outer block's Register returns Void (because the inner block's Register is fresh and empty).

**The error occurs when the Void value is subsequently used incorrectly** (e.g., executed with `>`).

```soma
>{1 !_.n >{_.n >print}}

; What happens:
; - Outer block sets _.n = 1 in Register₁
; - Inner block executes with fresh Register₂ (empty)
; - Inner block reads _.n → resolves to Void (not in Register₂)
; - >print attempts to execute Void
; - Fatal: cannot execute Void
```

```soma
>{
  10 !_.count
  >{
    _.count >print    ; Fatal error
  }
}

; Inner block's Register is empty
; _.count resolves to Void
; >print receives Void → fatal error
```

**Why this happens:**
- Each block execution creates a **fresh, empty Register**
- Inner blocks **cannot see** outer block's Register paths
- There is **no lexical scoping** for Registers
- Registers are **completely isolated** per block

**Correct alternatives** (see section 6.16 for detailed examples):
- Pass data via the AL (stack)
- Use the Store (global state)
- Return values via the AL

#### 2.1.9 Register Access After Block Completes
When a block completes execution, its Register is destroyed. Attempting to read a Register path from a completed block's Register returns Void.

**The error occurs when the Void value is subsequently used incorrectly.**

```soma
>{23 !_.x} _.x >print

; What happens:
; - Inner block sets _.x = 23 in Register₁
; - Inner block completes → Register₁ destroyed
; - Outer block reads _.x from Register₂ (empty)
; - _.x resolves to Void
; - >print receives Void → Fatal: cannot execute Void
```

```soma
>{
  { !_.n _.n _.n >* } !_.square    ; Define square function
}
; Block completes, Register destroyed

>_.square    ; Fatal: _.square is Void (no longer exists)
```

**Why this happens:**
- Registers are **temporary** — destroyed when block completes
- Register values **do not persist** beyond block execution
- Each block has its **own independent Register**

**Correct alternatives**:
- Store blocks/values in the Store (global state): `{ ... } !my_function`
- Return values via the AL before block completes

#### 2.1.10 Undefined Path Read (Strict Semantics)

SOMA uses **strict read semantics**: Reading a path that was never created is a fatal error.

**Store path example:**
```soma
x.y.z             ; Fatal: RuntimeError: "Undefined Store path: 'x'"
                  ; Path 'x' was never created
```

**Register path example:**
```soma
>{
  _.counter       ; Fatal: RuntimeError: "Undefined Register path: '_.counter'"
                  ; Register path '_.counter' was never written
}
```

**Auto-vivified paths are NOT errors:**
```soma
42 !a.b.c         ; Auto-vivifies a and a.b with Void payload
a.b               ; NOT an error — returns Void (cell was auto-created)
a                 ; NOT an error — returns Void (cell was auto-created)
```

**Key distinction:**
- Reading **undefined path** (never created) → Fatal error
- Reading **auto-vivified path** (created during write) → Returns Void (no error)

**Error messages are helpful:**
```
RuntimeError: Undefined Store path: 'config.theme'
  Path was never set. Did you mean to:
    - Initialize it first: () !config.theme
    - Set a nested value: <value> !config.theme.<child>
```

**Why this is an error:**
- Catches typos immediately (e.g., `config.timout` vs `config.timeout`)
- Makes uninitialized access explicit (no silent Void returns)
- Forces proper initialization patterns

**Correct alternatives** (see Section 3.1 for details):
- Initialize paths before reading: `Nil !config.theme`
- Write to nested paths (auto-vivifies parents): `42 !data.nested.value`

## 3. Non-Fatal Conditions

The following conditions are **NOT fatal** and must be handled by program logic:

**Note:** Reading undefined paths (paths that were never created) is now a **fatal error** (see Section 2.1.10). Only auto-vivified cells can be read and return Void.

### 3.1 Reading Void (Never-Set Cells)

**SOMA uses strict read semantics**: Reading a path that was never created raises a **RuntimeError**.

However, **auto-vivified cells CAN be read** and return Void. Auto-vivification happens when you write to a nested path — intermediate cells are created with Void payload.

**Two cases:**

1. **Undefined path (never created)** → RuntimeError
2. **Auto-vivified path (created during write)** → Returns Void

#### 3.1.1 Reading Undefined Paths (Error)

Attempting to read a path that was never created raises a helpful error:

```soma
; Reading non-existent path
x.y.z             ; RuntimeError: "Undefined Store path: 'x'"
                  ; Path was never set. Did you mean to:
                  ;   - Initialize it first: () !x
                  ;   - Set a nested value: <value> !x.y.z

; This catches typos:
42 !config.timeout
config.timout     ; RuntimeError: "Undefined Store path: 'config.timout'"
                  ; (typo: 'timout' vs 'timeout')
```

**Register paths also error on undefined reads:**

```soma
>{
  _.counter       ; RuntimeError: "Undefined Register path: '_.counter'"
                  ; Register paths must be written before reading.
                  ; Did you forget: <value> !_.counter?
}
```

#### 3.1.2 Reading Auto-Vivified Cells (Returns Void)

When you write to a nested path, SOMA creates intermediate cells automatically. These **auto-vivified cells can be read** and return Void:

```soma
; Writing to nested path auto-vivifies parents
42 !a.b.c         ; Creates a (Void), a.b (Void), a.b.c (42)

; Auto-vivified cells CAN be read (they exist!)
a.b               ; AL = [Void] — auto-vivified, never explicitly set
a                 ; AL = [Void] — auto-vivified, never explicitly set
a.b.c             ; AL = [42] — explicitly set
```

**The key distinction:**
- `x.y.z` where `x` was never created → **RuntimeError**
- `a.b` where `a.b.c` was written → **Returns Void** (a and a.b were auto-vivified)

#### 3.1.3 Safe Patterns for Optional Values

**Pattern 1: Initialize before reading**
```soma
; Always initialize optional paths
Nil !config.theme         ; Explicitly set to empty
config.theme              ; AL = [Nil] — safe to read
```

**Pattern 2: Write nested values (auto-vivifies parents)**
```soma
; Writing nested values makes parents readable
() !user.profile.email    ; Auto-vivifies 'user' and 'user.profile'

user.profile              ; AL = [Void] — safe, was auto-vivified
user.profile.email        ; AL = [()] — explicitly set
```

**Pattern 3: Check with >isVoid before reading**
```soma
; This pattern NO LONGER WORKS (can't read undefined path)
; config.theme >isVoid    ; ERROR if config.theme was never created!

; CORRECT: Write a default first, then check
Nil !config.theme         ; Initialize with Nil
config.theme >isVoid      ; Safe to check (path exists)
  { (default-theme) !config.theme }
  { }
>ifelse
```

**Key distinction between Nil and Void:**
```soma
Nil !settings.theme       ; Explicitly set to empty
settings.theme            ; AL = [Nil] — was set (to empty)
settings.theme >isVoid    ; False — has been set

; Auto-vivified (from writing to child)
42 !data.nested.value
data.nested               ; AL = [Void] — auto-vivified
data.nested >isVoid       ; True — never explicitly set
```

### 3.1.4 When Strict Read Errors Occur

**Error case summary:**

| Operation | Path Status | Result |
|-----------|-------------|--------|
| `x` | Never created | RuntimeError: "Undefined Store path: 'x'" |
| `x.y` | x never created | RuntimeError: "Undefined Store path: 'x'" |
| `x.y` | x auto-vivified | Returns Void (x exists from prior write) |
| `_.x` | Register, never written | RuntimeError: "Undefined Register path: '_.x'" |
| `_.x` | Register, auto-vivified | Returns Void (_.x exists from prior write) |

**Error message format (Store):**
```
RuntimeError: Undefined Store path: 'config.theme'
  Path was never set. Did you mean to:
    - Initialize it first: () !config.theme
    - Set a nested value: <value> !config.theme.<child>
```

**Error message format (Register):**
```
RuntimeError: Undefined Register path: '_.counter'
  Register paths must be written before reading.
  Did you forget: <value> !_.counter?
```

**How to fix undefined path errors:**

1. **Initialize the path before reading:**
   ```soma
   Nil !config.optional_field    ; Initialize with Nil
   config.optional_field          ; Safe to read now
   ```

2. **Write to a child path (auto-vivifies parent):**
   ```soma
   42 !data.nested.value          ; Auto-vivifies data and data.nested
   data.nested                    ; Safe to read (was auto-vivified)
   ```

3. **Check your spelling (typos cause these errors):**
   ```soma
   42 !config.timeout
   config.timout                  ; ERROR - typo detected!
   ```

**Why strict reads help:**
- Catches typos immediately (e.g., `config.timout` vs `config.timeout`)
- Makes uninitialized access explicit (no silent Void returns)
- Auto-vivified paths still work (sparse structures preserved)

### 3.2 Nil Values
Reading a Cell that contains Nil returns Nil. This is a **valid payload** and not an error.

```soma
Nil !settings.theme
settings.theme    ; AL = [Nil] — perfectly valid
```

### 3.3 Logical Errors
Conditions like "file not found", "invalid input", or "operation failed" are **not runtime errors**. They are represented as values (Booleans, symbols, error records) on the AL and handled via conditionals.

```soma
; Hypothetical file operation that pushes success/failure
(data.txt) >file_exists
  { (data.txt) >load }
  { (File not found) >print }
>ifelse
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

**Semantics:**
- Creates all missing Cells in the path (auto-vivification)
- Sets the target Cell's **value** to `Val`
- Preserves identity of existing Cells
- Does **NOT** affect the Cell's subpaths (children remain unchanged)

**Key insight:** Writing a value writes ONLY the value component, not the subpaths.

Example (basic write):
```soma
42 !a.b.c         ; Creates a, a.b, a.b.c if needed
                  ; Sets a.b.c's VALUE to 42
```

Example (value independent of children):
```soma
42 !node          ; Set node's VALUE to 42
99 !node.child    ; Create child in node's SUBPATHS

node              ; Returns 42 (node's VALUE)
node.child        ; Returns 99 (child in node's SUBPATHS)

100 !node         ; Update node's VALUE to 100

node              ; Returns 100 (VALUE changed)
node.child        ; Still returns 99 (SUBPATHS unchanged!)
```

**What happens internally:**
1. Parse path `a.b.c`
2. Auto-vivify intermediate Cells (a, a.b) with Void values if they don't exist
3. Create or locate final Cell `a.b.c`
4. Set `a.b.c.value = Val`
5. Leave `a.b.c.subpaths` unchanged

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

This is the **only legal use of Void** in a write operation (applies to both Store and Register).

**Semantics:**
- Navigate to the **parent Cell**
- Delete the child key from the **parent's subpaths dictionary**
- This removes the **path** from the tree, **not the Cell itself**
- The Cell persists if accessible via any CellRef or other path
- This does **NOT** affect the parent's value
- If the Cell does not exist, no action is taken
- No error occurs in either case

**Key insight:** Path deletion removes navigation routes in the tree, not the Cells themselves. A Cell continues to exist as long as it is accessible through any route (CellRef or path).

**Works identically for Store and Register:**
- Store deletion: `Void !a.b.` deletes path a.b from Store tree
- Register deletion: `Void !_.x.` deletes path _.x from Register tree

Example (Store deletion):
```soma
42 !a.b.c
a.b.c             ; AL = [42]

Void !a.b.        ; Delete path a.b from Store tree
a.b.c             ; AL = [Void] — path no longer exists
a.b               ; AL = [Void] — path no longer exists
```

Example (Register deletion):
```soma
{
  23 !_.temp
  _.temp >print     ; Prints: 23

  Void !_.temp.     ; Delete Register cell
  _.temp            ; Returns Void (Cell no longer accessible)
}
```

Example (Register cleanup pattern):
```soma
{
  ; Use Register cells as temporary workspace
  1 !_.a
  2 !_.b
  _.a _.b >+        ; AL = [3]

  ; Clean up workspace
  Void !_.a.
  Void !_.b.

  ; Return result (AL = [3])
}
```

Example (CellRef persists after path deletion):
```soma
Cell c: 42 !foo
CellRef ref: foo.
Void !foo.        ; Delete path 'foo' from Store
ref               ; AL = [42] — Cell still exists via CellRef!
```

In this example, deleting the path `foo` does not delete the Cell. The Cell continues to exist and is accessible via the CellRef `ref`.

Example (parent value unaffected):
```soma
99 !a             ; Set a's VALUE to 99
42 !a.b           ; Create child b in a's SUBPATHS

a                 ; Returns 99 (a's VALUE)

Void !a.b.        ; Delete b from a's SUBPATHS
a                 ; Still returns 99 (a's VALUE unchanged!)
a.b               ; Returns Void (b no longer in a's SUBPATHS)
```

**What happens internally:**
1. Parse path `a.b`
2. Navigate to parent Cell `a`
3. Delete key `"b"` from `a.subpaths`
4. Parent Cell `a.value` remains unchanged

**Visual representation:**
```
Before: Void !a.b.

Cell a:
  value: 99
  subpaths: {"b": Cell(value: 42, subpaths: {})}

After: Void !a.b.

Cell a:
  value: 99          ← UNCHANGED
  subpaths: {}       ← "b" deleted
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

### 4.6 CellRef Semantics: Immutable Values and Cell Lifetime

CellRefs are **immutable values** that provide access to Cells. Understanding CellRef semantics is critical to understanding how Cells persist independently of paths.

#### 4.6.1 CellRefs Have Value Semantics

CellRefs are immutable values, like Int, String, or Block:
- CellRefs can be stored in Cells, passed on the AL, and used in computations
- Multiple CellRefs can refer to the same Cell
- Whether CellRefs are "copied" or internally shared is unobservable and implementation-defined
- SOMA provides no identity comparison for CellRefs — you cannot distinguish "same CellRef" from "different CellRef to same Cell"

**Example: Multiple CellRefs to same Cell**
```soma
42 !data
data. !ref1          ; Create first CellRef
data. !ref2          ; Create second CellRef
data. !ref3          ; Create third CellRef

99 !data             ; Update Cell value
ref1                 ; AL = [99] — all refs point to same Cell
ref2                 ; AL = [99]
ref3                 ; AL = [99]
```

All three CellRefs refer to the same Cell. When the Cell's value changes, all CellRefs reflect the updated value.

#### 4.6.2 Cells Have Independent Lifetime from Paths

**Key principle:** Paths are navigation routes in the tree structure. Cells are independent entities. A Cell persists as long as it is accessible through **any** route (path or CellRef).

A Cell continues to exist if:
- It is accessible via any path in the Store, OR
- It is accessible via any path in any active Register, OR
- Any CellRef referring to it exists anywhere (AL, Store, Register)

**Example: Cell persists after path deletion**
```soma
23 !a.b              ; Create Cell, accessible via path a.b
a.b. !ref            ; Create CellRef to that Cell
Void !a.b.           ; Delete path a.b from Store tree
ref                  ; AL = [23] — Cell still exists via CellRef!
```

What happened:
1. `23 !a.b` created a Cell accessible via Store path `a.b`
2. `a.b. !ref` created an immutable CellRef value pointing to that Cell
3. `Void !a.b.` removed the **path** `a.b` from the Store tree
4. `ref` dereferenced the CellRef and accessed the Cell, returning 23

The Cell still exists because the CellRef at path `ref` provides access to it.

#### 4.6.3 There Are No "Dangling" CellRefs in SOMA

In traditional systems, deleting memory can create "dangling pointers" that point to invalid memory:

```c
// Traditional dangling pointer (C)
int *p = malloc(sizeof(int));
*p = 42;
free(p);          // Delete the memory
*p;               // DANGLING - undefined behavior!
```

**SOMA is fundamentally different.** Deleting a path does NOT delete the Cell:

```soma
; SOMA: Paths vs Cells
42 !cell
cell. !ref
Void !cell.       ; Delete PATH, but Cell persists
ref               ; AL = [42] — NOT dangling, Cell still exists!
```

**Why CellRefs never "dangle":**
- `Void !path.` removes the **path**, not the Cell
- Cells persist as long as they're accessible
- CellRefs provide direct access to Cells
- Dereferencing a CellRef after path deletion is **NOT an error**

#### 4.6.4 Practical Examples

**Example 1: Detached structures (like "new" in other languages)**
```soma
>{
  (initial data) !_.obj.data
  0 !_.obj.counter
  { _.obj.counter 1 >+ !_.obj.counter } !_.obj.increment

  _.obj.        ; Return CellRef to object
} !myObj

; Block destroyed, Register destroyed, but object persists!
myObj.data              ; "initial data"
myObj.counter           ; 0
>myObj.increment        ; Execute increment method
myObj.counter           ; 1
```

The structure was built in the Register (temporary), but returned as a CellRef. The Cells persist even though the Register is gone.

**Example 2: Multiple paths to same Cell**
```soma
42 !node
node. !alias1
node. !alias2
Void !node.       ; Delete original path
alias1            ; AL = [42] — Cell accessible via alias1
alias2            ; AL = [42] — Cell accessible via alias2

99 !alias1        ; Update via one CellRef
alias2            ; AL = [99] — both refs see the update
```

**Example 3: CellRef stored in another Cell**
```soma
42 !data
data. !container.ref     ; Store CellRef as value in another Cell
Void !data.              ; Delete original path
container.ref            ; Returns CellRef (can still dereference)
container.ref            ; Deref: AL = [42]
```

#### 4.6.5 Cell Lifetime Summary

**A Cell persists as long as:**
- It is accessible via any path in Store, OR
- It is accessible via any path in any active Register, OR
- Any CellRef referring to it exists anywhere

**When all access routes are removed:**
- The Cell becomes inaccessible
- The Cell can be reclaimed (implementation-defined, like garbage collection)

This is defined **semantically**, not mechanistically. Implementations might use garbage collection, reference counting, or other techniques — only the observable behavior matters.

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
Token:         !path. (Store: a.b)
               !_.path. (Register: _.x)
Effect:        Navigate to parent Cell
               Delete child key from parent.subpaths
               Parent.value remains unchanged
               If Cell(path) does not exist:
                 No action
               AL' = [...]

Example:       99 !a         ; a.value = 99
               42 !a.b       ; a.subpaths = {"b": Cell(...)}
               Void !a.b.    ; Delete "b" from a.subpaths
                             ; a.value still = 99
```

### 5.2 Read Rules

**Rule R1: Value Read (Cell Exists)**
```
Precondition:  Cell(path) exists
Token:         path (Store: a.b.c)
               _.path (Register: _.x.y)
Effect:        AL' = [Cell(path).value, ...]
               (Reads ONLY the value component)
               (payload may be Nil, Void, or any other value)
               (subpaths are NOT read or affected)
```

**Rule R2: Value Read (Cell Does Not Exist) — STRICT SEMANTICS**
```
Precondition:  Cell(path) does not exist
Token:         path (Store)
               _.path (Register)
Effect:        RuntimeError: "Undefined Store path: '{path}'"
            or RuntimeError: "Undefined Register path: '_.{path}'"
               Thread halts immediately
               No AL modification

Note: This is a FATAL ERROR, not a non-fatal condition.
      Reading undefined paths is now an error (strict semantics).
      Auto-vivified cells CAN be read (they exist, return Void).
```

**Rule R3: CellRef Read (Cell Exists)**
```
Precondition:  Cell(path) exists
Token:         path. (Store)
               _.path. (Register)
Effect:        AL' = [CellRef(path), ...]
```

**Rule R4: CellRef Read (Cell Does Not Exist) — STRICT SEMANTICS**
```
Precondition:  Cell(path) does not exist
Token:         path. (Store)
               _.path. (Register)
Effect:        RuntimeError: "Undefined Store path: '{path}'"
            or RuntimeError: "Undefined Register path: '_.{path}'"
               Thread halts immediately
               No AL modification

Note: This is a FATAL ERROR, not a non-fatal condition.
      CellRef operations on undefined paths also error (strict semantics).
```

### 5.3 Cell Creation Rules

**Rule C1: Automatic Creation During Write (Auto-Vivification)**
```
When executing: Val !a.b.c (Store)
            or: Val !_.x.y (Register)

If path a (or _.x) does not exist:
  Create Cell(a) or Cell(_.x) with payload Void
If path a.b (or _.x.y) does not exist:
  Create Cell(a.b) or Cell(_.x.y) with payload Void
Create/update Cell(a.b.c) or Cell(_.x.y.z) with payload Val
```

All intermediate Cells are created with **Void payloads** (representing "never explicitly set"). Only the final target Cell receives the explicit value.

**Example:**
```soma
42 !data.nested.value

; Creates:
; - Cell(data) with payload Void (auto-vivified)
; - Cell(data.nested) with payload Void (auto-vivified)
; - Cell(data.nested.value) with payload 42 (explicitly set)
```

### 5.4 Cell Deletion Rules

**Rule D1: Structural Deletion Propagates**
```
When executing: Void !a.b. (Store)
            or: Void !_.x. (Register)

Effect:
  Navigate to parent Cell(a) or Cell(_)
  If key "b" or "x" exists in parent.subpaths:
    Delete Cell and all its descendants
    Remove key from parent.subpaths
    Parent.value remains unchanged

  Paths a.b.* or _.x.* become non-existent
  Reading a.b.x or _.x.y returns Void

Key insight: Deletion operates on parent's subpaths dictionary,
             not on parent's value.
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

**Rule E7: Register Isolation Violation (Inner Block Accessing Outer Register)**
```
When: Inner block attempts to read Register path
      that was set in an outer block's Register
Effect: Path resolves to Void (different Register)
        If subsequently executed: FATAL ERROR

Example: >{1 !_.n >{_.n >print}}
         Outer block: _.n = 1 in Register₁
         Inner block: _.n = Void in Register₂ (fresh, empty)
         >print receives Void → attempts to execute Void → FATAL ERROR
```

**Rule E8: Register Access After Block Completes**
```
When: Block completes, destroying its Register
      Outer block attempts to read inner block's Register path
Effect: Path resolves to Void (Register destroyed)
        If subsequently executed: FATAL ERROR

Example: >{23 !_.x} _.x >print
         Inner block: _.x = 23 in Register₁
         Inner block completes → Register₁ destroyed
         Outer block: _.x = Void in Register₂
         >print receives Void → attempts to execute Void → FATAL ERROR
```

## 6. Examples: Correct and Incorrect Usage

### 6.1 Correct: Using Nil for Optional Values

```soma
; Initialize configuration with optional fields
Nil !config.theme
Nil !config.language
(Admin) !config.username

; Check and use
config.theme Nil >==
  { (default) !config.theme }
  { }
>ifelse
```

### 6.2 Correct: Testing for Auto-Vivified Paths

```soma
; First, create nested structure
(default.png) !user.profile.avatar

; Parent was auto-vivified, can test it
user.profile >isVoid
  { (Profile never set) >print }
  { (Profile exists) >print }
>ifelse                          ; Prints "Profile exists" (was auto-vivified)

; Child was explicitly set
user.profile.avatar >isVoid
  { (No avatar) >print }
  { user.profile.avatar >display }
>ifelse                          ; Displays the avatar
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

; AL now has: [False, (Division by zero)]
; Handle it:
  { (Error: ) >concat >print }
  { >toString >print }
>ifelse
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
>ifelse
```

```soma
; Verify a value is a Block before executing
config.startup
Void >==
  { (No startup action) >print }
  {
    config.startup >IsBlock
      { >config.startup }
      { (Startup value is not executable) >print }
    >ifelse
  }
>ifelse
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

### 6.14 Incorrect: Register Isolation Violation (Inner Block Accessing Outer Register)

**Each block gets a fresh, isolated Register. Inner blocks cannot see outer block's Register paths.**

```soma
; ILLEGAL: Inner block trying to access outer Register
>{1 !_.n >{_.n >print}}

; What happens:
; 1. Outer block executes with Register₁
; 2. 1 !_.n → stores 1 in Register₁ at path _.n
; 3. >{_.n >print} → executes inner block
;    - Inner block gets fresh Register₂ (empty)
;    - _.n → reads Register₂ path _.n
;    - Register₂ has no _.n → resolves to Void
;    - Pushes Void onto AL
;    - >print → attempts to execute Void
;    - FATAL ERROR: cannot execute Void
```

```soma
; Another example: accessing non-existent Register path
>{
  10 !_.count
  >{
    _.count >print    ; FATAL ERROR
  }
}

; Inner block's Register is empty
; _.count resolves to Void
; >print receives Void → fatal error
```

### 6.15 Incorrect: Accessing Register After Block Completes

**When a block completes, its Register is destroyed. Values do not persist.**

```soma
; ILLEGAL: Expecting Register to persist after block completes
>{23 !_.x} _.x >print

; What happens:
; 1. Inner block executes with Register₁
; 2. 23 !_.x → stores 23 in Register₁ at path _.x
; 3. Inner block completes
; 4. Register₁ is destroyed
; 5. Back in outer block with Register₂
; 6. _.x → reads Register₂ path _.x
; 7. Register₂ has no _.x → resolves to Void
; 8. >print receives Void → FATAL ERROR
```

```soma
; Another example: helper block with local state
>{
  { !_.n _.n _.n >* } !_.square    ; Define square function
}
; Block completes, Register destroyed

>_.square    ; FATAL ERROR: _.square is Void (no longer exists)
```

### 6.16 Correct: Sharing Data Between Blocks

**To share data between blocks, use the Store, AL, or CellRefs.**

**❌ WRONG - Try to use outer Register (fails):**
```soma
>{1 !_.n >{_.n >print}}    ; FATAL ERROR (as shown above)
```

**✅ RIGHT - Pass via AL:**
```soma
>{1 !_.n _.n >{>print}}    ; Prints 1

; What happens:
; 1. Outer block: 1 !_.n stores 1 in Register₁
; 2. Outer block: _.n pushes 1 onto AL
; 3. Inner block executes with AL = [1]
; 4. Inner block: >print pops and prints 1
```

**✅ RIGHT - Use Store (global state):**
```soma
>{1 !data.n >{data.n >print}}    ; Prints 1

; What happens:
; 1. Outer block: 1 !data.n stores 1 in Store (global)
; 2. Inner block: data.n reads from Store (not Register)
; 3. Inner block: >print prints 1
```

**✅ RIGHT - Return via AL:**
```soma
>{
  >{5 !_.n _.n _.n >*} !_.square    ; Define helper that squares AL top
  7 >_.square                        ; Call it with 7
  >print                             ; Prints 49
}

; What happens:
; 1. Outer block defines _.square in its Register
; 2. 7 pushes 7 onto AL
; 3. >_.square executes the block (fresh Register₃)
;    - !_.n pops 7 from AL, stores in Register₃
;    - _.n _.n >* computes 7 * 7 = 49
;    - Leaves 49 on AL
; 4. Outer block continues with AL = [49]
; 5. >print prints 49
```

### 6.17 Correct: Register Isolation Allows Independent Nested Loops

**Each block has its own Register, so nested blocks can use the same paths without interference.**

```soma
>{
  0 !_.i                           ; Outer counter in outer Register

  {
    0 !_.i                         ; Inner counter in inner Register (isolated!)
    _.i 5 ><
      { _.i 1 >+ !_.i >block }     ; Inner loop uses its own _.i
      { }
    >choose >chain
  } !_.inner_loop

  _.i 3 ><
    {
      >_.inner_loop                ; Call inner loop
      _.i 1 >+ !_.i                ; Increment outer _.i
      >block
    }
    { }
  >choose >chain
}

; Key points:
; - Outer block has _.i for outer counter
; - _.inner_loop block (when executed) has its own _.i for inner counter
; - They don't interfere - different Registers
; - Each loop maintains its own counter independently
```

## 7. Ambiguities and Open Questions

Based on this analysis, the following potential ambiguities or areas for clarification remain:

### 7.1 ~~Intermediate Cell Payloads During Auto-Creation~~ — RESOLVED

~~When executing `42 !a.b.c.d.e`, the specification states that intermediate Cells are created. The formal rule states they receive Nil payloads. However, the original specification (Section 5.5) does not explicitly state what payload intermediate Cells receive.~~

**RESOLVED:** Intermediate cells created during auto-vivification receive **Void** payloads. This preserves the semantic distinction between "never set" (Void) and "explicitly set to empty" (Nil). See Section 1.5 and Rule C1.

Example:
```soma
42 !a.b.c         ; Creates a (Void), a.b (Void), a.b.c (42)
a.b               ; Returns Void — auto-vivified, never explicitly set
```

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

### 7.3 Error Recovery and Memory Model

When a fatal error occurs, the specification states that "the Store remains in its last valid state." This section clarifies what "valid state" means and how it relates to SOMA's memory model.

#### 7.3.1 What "Valid State" Means

**Valid state means the Store has no corruption:**
- All Cell data structures are intact
- No partial writes or inconsistent data
- Individual operations are atomic (either complete or don't occur)

**Valid state does NOT mean:**
- All operations before the error necessarily completed
- The exact boundary between completed/incomplete operations is specified
- Cross-thread visibility follows a specific ordering

**Example:**
```soma
1 !a            ; Completes successfully
2 !b            ; Fatal error here
3 !c            ; Never executes
```

**After the error:**
- `a` contains 1 (operation completed)
- `b` may contain 2 OR may be unchanged (implementation-defined)
- `c` is unchanged (operation never started)
- Store structure is **valid** (no corrupted data structures)

#### 7.3.2 Individual Operations Are Atomic

Each primitive operation completes atomically:

```soma
42 !path    ; Atomic: either completes or doesn't (no partial state)
path        ; Atomic: reads complete value
Void !path. ; Atomic: deletion completes or doesn't
```

**Guaranteed:** You never observe a "half-written" value.

#### 7.3.3 SOMA's Memory Model: Happens-Before (Abstract)

SOMA uses a **happens-before memory model**, but the exact details are intentionally **implementation-defined**.

**What this means:**
- SOMA defines observable ordering relationships between operations
- The exact nature of these relationships depends on the implementation
- Different implementations may use different memory models

**Why this approach:**
- Fits with SOMA's mechanistic philosophy (systematic, observable)
- Allows flexibility for different execution environments
- Prevents over-specification that would limit implementations

#### 7.3.4 What SOMA Guarantees

**Within a single thread:**
Operations occur in program order (sequential consistency):

```soma
1 !a        ; Step 1
2 !b        ; Step 2 (happens-after Step 1)
3 !c        ; Step 3 (happens-after Step 2)
```

**Atomicity:**
Individual operations are atomic:

```soma
42 !path    ; Either completes fully or not at all
path        ; Reads complete value (not partial)
```

**Store consistency:**
The Store is always in a valid state (no corruption).

#### 7.3.5 What Is Implementation-Defined

**Cross-thread visibility ordering:**

```soma
; Thread 1
42 !shared

; Thread 2
shared      ; When does this see 42?
```

The happens-before relationship between threads depends on the implementation's memory model.

**Memory model choices for implementers:**
- **Single-threaded:** Sequential consistency (program order = execution order)
- **Multi-threaded:** Sequential consistency, TSO (Total Store Order), or relaxed
- **Distributed:** Causal consistency, eventual consistency, or strong consistency

**Synchronization primitives:**
SOMA does not define mutexes, semaphores, atomic operations, or memory barriers. These may be provided as built-ins or extensions (implementation-specific).

#### 7.3.6 Happens-Before Model (Formal Definition)

SOMA execution can be described by a partial order of operations with a happens-before relation (⊏).

**Properties:**

1. **Program Order:** Within a thread, if operation A comes before operation B in program text, then A ⊏ B

2. **Transitivity:** If A ⊏ B and B ⊏ C, then A ⊏ C

3. **Synchronization:** The exact synchronization edges that establish happens-before between threads are implementation-defined

**Examples (implementation-dependent):**
- Single-threaded: happens-before = program order
- Multi-threaded with locks: happens-before includes lock release → acquire
- Distributed: happens-before might include message send → receive
- Actor model: happens-before includes message send → message processing

#### 7.3.7 Summary: Guaranteed vs Implementation-Defined

**Guaranteed:**
- Individual operations are atomic
- Single-threaded execution is sequentially consistent
- Store is always in a valid state (no corruption)
- No partial writes or half-written values

**Implementation-defined:**
- Cross-thread visibility ordering
- Memory model (sequential, TSO, relaxed, etc.)
- Synchronization primitives (if any)
- Exact boundary of completed operations after an error

**Recommendation for portable code:**
After an error, only operations that completed before the error are guaranteed to be visible. Cross-thread visibility without explicit synchronization is unspecified.

### 7.4 CellRefs and Path Deletion — RESOLVED

**Question:** If a CellRef is obtained via `a.b.`, then `Void !a.b.` deletes the path, what happens to existing CellRefs?

**Answer:** The CellRef continues to work normally. Deleting a path does NOT delete the Cell — it only removes the path from the tree. The Cell persists as long as it's accessible via any route (including CellRefs).

**Explanation:** See Section 4.6 for complete details on CellRef semantics. Key points:
- `Void !path.` removes the **path**, not the Cell
- Cells have independent lifetime from paths
- A Cell persists as long as any CellRef or path provides access to it
- Dereferencing a CellRef after path deletion is **NOT an error**
- CellRefs never "dangle" in SOMA

**Example:**
```soma
42 !node
node. !ref           ; Create CellRef
Void !node.          ; Delete path 'node'
ref                  ; AL = [42] — Cell still accessible via CellRef
```

### 7.5 Nil in Path Resolution — RESOLVED

**Question:** When a path like `a.b.c` is resolved, if `a.b` has payload Nil (not a structure), does resolution fail?

**Answer:** No. Path resolution succeeds regardless of parent cell values.

**Core Principle:** Cells have two **completely orthogonal** components:

1. **Value** (payload): The data stored at this location (Int, Block, Nil, Void, CellRef, String)
2. **Subpaths** (children): Dictionary mapping names to child Cells

These are independent:
- **Reading a Cell reads ONLY the value**
- **Path traversal uses ONLY subpaths**
- Setting/reading a Cell's value has NO effect on its subpaths

**Visual representation:**
```
        ┌─────────────────┐
        │      Cell       │
        ├─────────────────┤
        │ value: Nil      │  ← Payload (any CellValue)
        ├─────────────────┤
        │ subpaths: {     │  ← Children (independent!)
        │   "c": Cell     │
        │ }               │
        └─────────────────┘
```

**Nil with children:**
```soma
Nil !a.b          ; Set a.b's VALUE to Nil
42 !a.b.c         ; Create child 'c' in a.b's SUBPATHS

a.b               ; Returns Nil (reads a.b's VALUE)
a.b.c             ; Returns 42 (traverses a.b's SUBPATHS to c)
```

Cell `a.b` has:
- Value: `Nil`
- Subpaths: `{"c": Cell(value: 42, subpaths: {})}`

**Void with children:**
```soma
42 !data.parent.child       ; Auto-vivifies data and data.parent with Void VALUES

data.parent                 ; Returns Void (reads data.parent's VALUE)
data.parent.child           ; Returns 42 (traverses data.parent's SUBPATHS)
```

Cell `data.parent` has:
- Value: `Void`
- Subpaths: `{"child": Cell(value: 42, subpaths: {})}`

**Any value can have children:**
```soma
; Int with children
42 !node
99 !node.sub

; Block with children
{ >print } !action
"help text" !action.description

; String with children
"root" !tree.label
"left" !tree.left.label
"right" !tree.right.label
```

This orthogonality enables graph structures (linked lists, trees, cyclic graphs) without requiring explicit node types.

## 7. Common Mistakes and Anti-Patterns

This section catalogs common errors that programmers make when learning SOMA, along with the correct alternatives.

### 7.1 Using `{ } >chain` When `>{ }` Is Cleaner

**Problem:** Using `{ code } >chain` when you just want to execute a block once.

**Why it's wrong:** `>chain` is for tail-call loops — it repeatedly executes blocks returned on the AL. For single execution, `>{ }` is clearer and more direct.

**❌ WRONG:**
```soma
{ 1 2 >+ } >chain !result    ; Unnecessarily verbose

{
  (Hello) >print
  42 !x
} >chain                      ; Confusing — implies looping when there's none
```

**✅ RIGHT:**
```soma
>{ 1 2 >+ } !result          ; Direct execution

>{
  (Hello) >print
  42 !x
}                             ; Clear single execution
```

**When to use `>chain`:**
- Tail-call recursion patterns
- State machines that return next state
- Loops that return blocks to continue

```soma
; CORRECT use of >chain: tail-call loop
{
  counter >print
  counter 1 >+ !counter
  counter 10 ><
    >block      ; Continue: return self for next iteration
    Nil         ; Stop: return non-block to end chain
  >choose
} !loop
loop >chain     ; Keeps executing until Nil returned
```

### 7.2 Expecting Register Values in Child Blocks (Register Isolation)

**Problem:** Trying to access a Register path from an inner block when it was set in an outer block.

**Why it fails:** Each block execution creates a **fresh, empty Register**. Inner blocks have completely isolated Registers and cannot see outer block's Register paths.

**❌ WRONG:**
```soma
>{
  5 !_.x                     ; Store in outer Register
  >{ _.x >print }            ; FATAL: _.x is Void in inner Register!
}

>{
  { _.n _.n >* } !_.square   ; Define in outer Register
  >{ 7 >_.square }           ; FATAL: _.square is Void in inner Register!
}
```

**What happens:**
1. Outer block sets `_.x` in Register₁
2. Inner block executes with fresh Register₂ (empty)
3. Inner block reads `_.x` → resolves to Void
4. Fatal error when Void is used

**✅ RIGHT - Pass via AL:**
```soma
>{
  5 !_.x                     ; Store in outer Register
  _.x                        ; Push to AL
  >{ !_.y _.y >print }       ; Pop from AL, store in inner Register
}
```

**✅ RIGHT - Use Store (global state):**
```soma
>{
  5 !x                       ; Store in Store (global)
  >{ x >print }              ; Read from Store
}
```

**✅ RIGHT - Return values via AL:**
```soma
>{
  { !_.n _.n _.n >* } !_.square   ; Define in outer Register
  7 _.square >^                   ; Pass 7 via AL, execute, result on AL
}
```

**Key rule:** Registers are **block-local only**. No sharing between parent and child.

### 7.3 Using `>choose` and Expecting Execution (It's a Selector!)

**Problem:** Calling `>choose` and expecting it to execute the selected block.

**Why it's wrong:** `>choose` **selects** a value based on a condition — it does NOT execute anything. If you want to execute the result, you need `>^` or use `>ifelse` from stdlib.

**❌ WRONG:**
```soma
x 10 ><
  { (small) >print }
  { (large) >print }
>choose                      ; Pushes a block onto AL, doesn't execute it!
```

**What happens:**
- `>choose` pops condition + two values, pushes one value onto AL
- The selected block is now on the AL (not executed)
- Nothing prints

**✅ RIGHT - Execute with `>^`:**
```soma
x 10 ><
  { (small) >print }
  { (large) >print }
>choose >^                   ; Select, then execute from AL
```

**✅ RIGHT - Use `>ifelse` from stdlib:**
```soma
x 10 ><
  { (small) >print }
  { (large) >print }
>ifelse                      ; Selects AND executes
```

**When `>choose` alone is correct:**
```soma
; Selecting a value (not a block)
x 10 >< 100 200 >choose !result     ; result = 100 or 200

; Selecting a block to store
condition
  { (option A) >print }
  { (option B) >print }
>choose !handler                     ; Store block for later

; Selecting next state in tail-call loop
counter 10 ><
  >block      ; Return current block to continue
  Nil         ; Return Nil to stop
>choose       ; Don't execute! Just return for >chain
```

**Summary:**
- `>choose` = selector (picks one value)
- `>^` = executor (runs block from AL)
- `>ifelse` = `>choose` + `>^` (stdlib convenience)

### 7.4 Confusing Nil and Void in Conditionals

**Problem:** Not understanding the semantic difference between Nil (explicitly empty) and Void (never set).

**Why it matters:**
- **Nil** = "This was set, but to nothing" (explicit emptiness)
- **Void** = "This was never set" (absence/uninitialized) — **only exists for auto-vivified cells**

**❌ WRONG - Reading undefined paths:**
```soma
config.theme >isVoid         ; RuntimeError if config.theme was never created!
                             ; Can't check if path exists without creating it first
```

**✅ RIGHT - Initialize first, then check:**
```soma
; Initialize optional field with Nil
Nil !config.theme             ; Explicitly set to empty
config.theme >isVoid          ; False — has been set (to Nil)

; Or write to a child to auto-vivify parent
() !config.theme.dark.background
config.theme >isVoid          ; True — auto-vivified (never explicitly set)
config.theme.dark >isVoid     ; True — auto-vivified
config.theme.dark.background >isVoid  ; False — explicitly set
```

**✅ RIGHT - Distinguish Nil from Void:**
```soma
; Optional field explicitly empty
Nil !person.middle_name
person.middle_name >isVoid    ; False (was set to Nil)
person.middle_name Nil >==    ; True

; Auto-vivified parent (from writing to child)
() !person.contact.email
person.contact                ; Void — auto-vivified
person.contact >isVoid        ; True (never explicitly set)
person.contact Nil >==        ; False (Void ≠ Nil)
```

**Common pattern - initialize then check:**
```soma
; Always initialize optional paths before checking
Nil !config.theme             ; Default to Nil
config.theme >isVoid
  { (default-theme) !config.theme }    ; Was Void: shouldn't happen (initialized to Nil)
  { }                                  ; Has value or Nil: keep it
>ifelse

; Or check for explicit Nil
config.theme Nil >==
  { (fallback-theme) !config.theme }   ; Was set to Nil: replace
  { }                                  ; Has actual value: keep
>ifelse
```

### 7.5 Storing Void as a Payload

**Note:** Storing Void is now legal (previously was an error).

**✅ Legal - Write Void as payload:**
```soma
Void !x              ; Legal: stores Void as payload
Void !_.temp         ; Legal: stores Void in Register
```

**✅ Legal - Use Nil for "explicitly empty":**
```soma
Nil !x               ; Legal: explicitly set to empty
Nil !_.temp          ; Legal: Register cell set to empty
```

**✅ Legal - Use trailing dot for deletion:**
```soma
Void !x.             ; Legal: delete Cell x entirely
Void !_.temp.        ; Legal: delete Register Cell _.temp
```

**✅ Legal - Auto-vivification creates Void:**
```soma
42 !a.b.c            ; Creates a (Void), a.b (Void), a.b.c (42)
a.b                  ; Returns Void — auto-created, never explicitly set
```

**Note:** You cannot distinguish auto-vivified Void from explicitly written Void. Both are simply Void.

### 7.6 Forgetting Register Destruction After Block Completes

**Problem:** Expecting Register values to persist after a block finishes.

**Why it fails:** When a block completes, its Register is destroyed. Values don't survive beyond block execution.

**❌ WRONG:**
```soma
>{ 23 !_.x }         ; Inner block sets _.x in Register₁
_.x >print           ; FATAL: Register₁ destroyed, _.x is Void in Register₂
```

**✅ RIGHT - Store in Store for persistence:**
```soma
>{ 23 !result }      ; Store in Store (global)
result >print        ; Read from Store — persists
```

**✅ RIGHT - Return via AL:**
```soma
>{ 23 }              ; Block returns 23 on AL
>print               ; Print from AL
```

**✅ RIGHT - Use CellRef to escape Register:**
```soma
>{
  42 !_.data.value
  _.data.              ; Return CellRef to Register structure
} !escaped

; Register destroyed, but CellRef keeps structure alive
escaped.value          ; 42
```

## 8. Conclusion

SOMA's error model is intentionally minimal and explicit:

- **Fatal errors** terminate execution when machine invariants are violated
- **Non-fatal conditions** are represented as values and handled via explicit control flow
- **Strict read semantics** — reading undefined paths raises RuntimeError (catches typos, forces initialization)
- **Auto-vivified paths can be read** — writing to nested paths creates intermediate cells with Void
- **Nil** represents explicit emptiness — a value that was deliberately set to "nothing"
- **Void** can be stored as a normal value, or represents "never set" in auto-vivified cells
- **Auto-vivification** creates intermediate cells with Void payload (structural scaffolding)
- The **! operator** creates, replaces, and deletes Cells based on path form and value type
- **Deletion works identically for Store and Register** — both support `Void !path.` deletion
- **CellRefs** are immutable values that provide access to Cells
- **Cells persist independently of paths** — a Cell exists as long as any access route (path or CellRef) remains
- **Path deletion removes paths, not Cells** — dereferencing a CellRef after path deletion is NOT an error
- **No "dangling" CellRefs exist in SOMA** — Cells are kept alive by any reference
- **No exceptions, unwinding, or recovery** mechanisms exist

**Memory model and concurrency:**
- SOMA uses a **happens-before memory model** (abstract, implementation-defined)
- **Individual operations are atomic** — no partial writes or inconsistent state
- **Single-threaded execution is sequentially consistent** — program order = execution order
- **Cross-thread visibility is implementation-defined** — depends on memory model choice
- **Store remains in valid state after errors** — no corruption, but exact operation boundaries are implementation-defined

This model forces programmers to handle error conditions explicitly through state inspection and branching, reflecting SOMA's philosophy that computation is observable state transformation, not hidden symbolic reduction.

By preserving the strict distinction between Nil (explicitly empty) and Void (never set), enforcing strict reads while allowing auto-vivification, ensuring Cells have independent lifetime from paths, and defining a flexible but systematic concurrency model, SOMA enables:
- **Typo detection** — undefined path reads immediately error, catching misspellings
- **Explicit initialization** — paths must be written before reading (no silent undefined behavior)
- **Sparse data structures** — auto-vivification still works, unset values don't consume explicit storage
- **Semantic clarity** — distinguishing "no value yet" from "intentionally empty"
- **Inspectable state** — presence, absence, and emptiness are all observable concepts
- **Detached data structures** — persist beyond their creation context (via CellRefs)
- **Safe aliasing** — multiple references can coexist without dangling pointer issues
- **Flexible concurrency** — implementations can choose appropriate memory models for their platform

