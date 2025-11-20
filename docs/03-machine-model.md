# 03 — Machine Model

**SOMA v1.0 Language Specification**
**State-Oriented Machine Algebra**

---

## Overview

SOMA is not a calculus. It is a **machine algebra** defined entirely by observable state transformations. This chapter specifies the three fundamental state structures that comprise the SOMA execution model:

1. **The Accumulator List (AL)** — a LIFO value conduit for dynamic state
2. **The Store** — a persistent hierarchical graph of identity-bearing Cells
3. **The Register** — a block-local hierarchical graph of identity-bearing Cells

Together with Blocks (executable state transformers), these structures define the complete operational semantics of SOMA.

SOMA execution is **linear, explicit, and introspectable**. There is no hidden call stack, no return path, no exception unwinding, and no shadowing. All state is visible. All mutation is observable.

---

## 1. The Accumulator List (AL)

### 1.1 What the AL Is (and Is Not)

The AL is a **linear sequence of values** serving as the primary dynamic execution context. It is LIFO in behavior but **not a call stack**:

- It does not track return addresses
- It does not manage stack frames
- It does not unwind on errors
- It is a **value conduit**, not a control structure

### 1.2 AL Operations

Most tokens either:

- **Push** a value onto the AL
- **Pop** one or more values from the AL
- **Transform** values already present

Example:

```soma
1 2 >+
```

| Step | Token | AL State | Description |
|------|-------|----------|-------------|
| 0 | (start) | `[]` | Empty AL |
| 1 | `1` | `[1]` | Push literal 1 |
| 2 | `2` | `[2, 1]` | Push literal 2 (top is 2) |
| 3 | `>+` | `[3]` | Execute block at Store path "+", pops 2 and 1, pushes sum |

The AL is updated **in-place**. No copying or implicit duplication occurs unless requested by a built-in (e.g. `>dup`).

**Note on Execution Prefix (`>`):** The `>` prefix reads the value at a path and executes it. This works with both Store paths (e.g. `>+`, `>print`) and Register paths (e.g. `>_.action`). See Section 5.4 for details.

### 1.3 AL Ordering Convention

In this document, we write AL states as:

```
AL = [top, second, third, ...]
```

where the **leftmost element is the top** of the stack.

### 1.4 Empty AL

Reading from an empty AL is a **fatal interpreter error**. SOMA does not define implicit defaults. Programs must ensure AL safety through correct sequencing.

Example (fatal):

```soma
>drop
```

AL is empty. Execution halts immediately.

### 1.5 No Arity

Blocks do not declare arguments. They take whatever values they require from the AL and leave whatever values they produce.

Example:

```soma
{ >dup >* } !square
5 square >Chain
```

| Step | Token | AL State | Description |
|------|-------|----------|-------------|
| 0 | (start) | `[]` | Empty |
| 1 | Block literal | `[{>dup >*}]` | Push block |
| 2 | `!square` | `[]` | Pop block, store at `square` |
| 3 | `5` | `[5]` | Push 5 |
| 4 | `square` | `[{>dup >*}, 5]` | Push block from Store |
| 5 | `>Chain` | Executes block | |
| 5.1 | `>dup` | `[5, 5]` | Duplicate top |
| 5.2 | `>*` | `[25]` | Multiply |
| 6 | (end) | `[25]` | Final AL state |

The block consumed 1 value (implicitly) and produced 1 value.

### 1.6 AL as Control Context

The AL determines which Block executes next under `>Choose` and `>Chain`.

Example: Conditional execution

```soma
True { "Yes" >print } { "No" >print } >Choose
```

| Before `>Choose` | AL State |
|------------------|----------|
| Top → Bottom | `[{...No...}, {...Yes...}, True]` |

Execution:

1. Pop the false-branch Block: `{...No...}`
2. Pop the true-branch Block: `{...Yes...}`
3. Pop the Boolean: `True`
4. Since `True`, execute `{...Yes...}`
5. Result: prints "Yes"

After execution, AL contains only the results of the chosen Block.

### 1.7 Example: AL Transformations

```soma
10 20 30 >swap >drop >dup
```

| Step | Token | AL State | Description |
|------|-------|----------|-------------|
| 0 | (start) | `[]` | Empty |
| 1 | `10` | `[10]` | Push 10 |
| 2 | `20` | `[20, 10]` | Push 20 |
| 3 | `30` | `[30, 20, 10]` | Push 30 |
| 4 | `>swap` | `[20, 30, 10]` | Swap top 2 |
| 5 | `>drop` | `[30, 10]` | Drop top |
| 6 | `>dup` | `[30, 30, 10]` | Duplicate top |

---

## 2. The Store

### 2.1 What the Store Is

The Store is a **persistent hierarchical graph of Cells** that holds program state. It is addressable via dot-separated paths and constitutes the **data memory** of the SOMA machine.

- The Store has a **single root**
- All top-level paths are relative to this root
- The Store is **globally visible**
- There is **no shadowing** between top-level paths

### 2.2 Cells and Payloads

Each named location in the Store refers to a **Cell**. A Cell has:

- A **persistent identity**
- A **payload value** (which may be Nil)
- Zero or more **child Cells**

Writing a value **replaces the payload** but **preserves the Cell identity**.

### 2.3 Nil vs Void (Corrected Semantics)

SOMA makes a strict distinction:

| Concept | Meaning | Storability |
|---------|---------|-------------|
| **Nil** | Cell exists, but carries no meaningful payload | **Legal payload** |
| **Void** | Cell does **not exist** | **Cannot be stored** |

**CRITICAL RULE:**

```
Void !path     → FATAL ERROR
Void !path.    → Legal (deletes Cell)
Nil !path      → Legal (stores Nil as payload)
```

Example:

```soma
Nil !a.b
a.b          ; AL = [Nil]
```

```soma
Void !a.b    ; FATAL: cannot store Void as payload
```

```soma
Void !a.b.   ; Legal: deletes Cell a.b
```

### 2.4 Cell Creation

A Cell is created automatically when a value is written to a path that did not previously exist.

Example:

```soma
42 !a.b.c
```

**Before:**
```
Store = {}
```

**After:**
```
Store = {
  a: {
    b: {
      c: 42
    }
  }
}
```

If `a` and `a.b` did not exist, all missing Cells are created with Nil payloads. The final Cell `a.b.c` receives payload `42`.

### 2.5 Paths and CellReferences

SOMA distinguishes between:

- **Value access**: `a.b` → retrieves payload
- **Cell access**: `a.b.` → retrieves CellReference

Example:

```soma
99 !config.timeout
config.timeout      ; Pushes 99 onto AL
config.timeout.     ; Pushes CellRef onto AL
```

A **trailing dot** denotes a reference to the Cell itself, not its payload.

### 2.6 Aliasing

Two paths may refer to the **same Cell**. This is structural aliasing.

Example: Value aliasing (no sharing)

```soma
23 !a.b
a.b !a.c
24 !a.b
a.c >print   ; prints 23
```

| Step | Store State | Description |
|------|-------------|-------------|
| 1 | `a.b = 23` | Store 23 in a.b |
| 2 | `a.c = 23` | Copy value to a.c |
| 3 | `a.b = 24` | Update a.b |
| 4 | `a.c` still `23` | No aliasing occurred |

Example: Cell aliasing (sharing)

```soma
(hello) !a.b.c
a.b. !x.y.
(goodbye) !d.b.c
d.b. !a.b.
a.b.c >print   ; prints "goodbye"
x.y.c >print   ; prints "hello"
```

| Step | Description |
|------|-------------|
| 1 | Create Cell at `a.b.c` with payload "hello" |
| 2 | Store **CellRef** to `a.b` at `x.y` |
| 3 | Create Cell at `d.b.c` with payload "goodbye" |
| 4 | Replace Cell at `a.b` with CellRef to `d.b` |
| 5 | `a.b.c` now resolves to "goodbye" (via `d.b.c`) |
| 6 | `x.y.c` still resolves to "hello" (original Cell preserved) |

Aliasing does not copy values. It **shares identity**.

### 2.7 Structural Mutation

**Payload write:**

```soma
Val !a.b.c
```

- Sets the payload of Cell `a.b.c` to `Val`
- Preserves identity of existing Cells
- Does not affect child Cells

**Cell replacement:**

```soma
Val !a.b.c.
```

- Replaces the entire Cell at `a.b.c` with a new Cell
- New Cell's payload is `Val`
- All child Cells are **discarded**

**Structural deletion:**

```soma
Void !a.b.c.
```

- Deletes Cell `a.b.c` and its entire subtree
- If Cell does not exist, no action is taken
- Aliases are unaffected unless they pointed to the deleted Cell

### 2.8 Example: Store Mutations

```soma
1 !counter.n
counter.n 1 >+ !counter.n
counter.n >print
```

| Step | Token | AL State | Store State | Description |
|------|-------|----------|-------------|-------------|
| 1 | `1` | `[1]` | `{}` | Push 1 |
| 2 | `!counter.n` | `[]` | `counter.n = 1` | Store 1 |
| 3 | `counter.n` | `[1]` | `counter.n = 1` | Read value |
| 4 | `1` | `[1, 1]` | - | Push 1 |
| 5 | `>+` | `[2]` | - | Add |
| 6 | `!counter.n` | `[]` | `counter.n = 2` | Write back |
| 7 | `counter.n` | `[2]` | `counter.n = 2` | Read |
| 8 | `>print` | `[]` | - | Print 2 |

---

## 3. The Register

### 3.1 What the Register Is

A **Register** is a hierarchical graph identical in structure to the Store, but with **block-local scope**.

- Register scope is the **execution of the currently executing Block**
- Each Block execution has its **own Register**
- Registers are destroyed at the end of Block execution
- **CellReferences in a Register can escape** the local Block execution

**CRITICAL:** Registers and the Store are **identical in every way other than scope**. Both are hierarchical graphs of Cells with a single root.

### 3.2 Store vs Register

| Feature | Store | Register |
|---------|-------|----------|
| Scope | Global | Block-local |
| Lifetime | Persistent | Execution-local |
| Root | Single, unnamed | Single, named `_` |
| Syntax | `a.b` | `_.a.b` |
| Write syntax | `!a.b` | `!_.a.b` |
| Root value access | N/A (unnamed) | `_` |
| Root CellRef access | N/A (unnamed) | `_.` |

### 3.3 Register Root

The Register is a hierarchical graph with a **single root named `_`**. All Register paths begin with `_` followed by a dot and subsequent path components.

**Why `_` is the Root:**

The Store has an unnamed root that cannot be directly referenced. For symmetry, the Register has a **named root** `_` that can be referenced and manipulated:

```soma
_                 ; Register root value
_.                ; Register root CellRef
_.x               ; Register path: root → x (value)
_.x.              ; Register path: root → x (CellRef)
_.x.y.z           ; Register path: root → x → y → z (value)
_.x.y.z.          ; Register path: root → x → y → z (CellRef)
```

This allows the entire Register graph to be captured, stored, or manipulated as a single entity.

### 3.4 Register Path Syntax

**Valid Register Syntax:**

```soma
_                 ; Register root value (payload at root)
_.                ; Register root CellRef
_.x               ; Register path to child cell (value)
_.x.              ; Register path to child cell (CellRef)
_.counter         ; Nested register path (value)
_.counter.        ; Nested register path (CellRef)
```

**Invalid Register Syntax:**

```soma
_x                ; ILLEGAL: missing dot after _
_counter          ; ILLEGAL: must be _.counter
_x.y              ; ILLEGAL: must be _.x.y
```

**NORMATIVE RULE:**

> All Register paths MUST use the form `_.path` where `_` is the root component. The syntax `_name` (without a dot) is not a valid Register path and MUST be rejected by the lexer.

### 3.5 Register Write Operations

Register writes follow the same syntax as Store writes, but target Register paths:

```soma
42 !_.x           ; Store 42 in register path _.x
!_.y              ; Pop AL and store in register path _.y
Nil !_.z          ; Store Nil in register path _.z
Void !_.w.        ; Delete register cell at _.w
Void !_.w         ; FATAL ERROR: cannot store Void as payload
```

### 3.6 Register Locality

Registers cannot escape the execution of their Block, but **CellReferences can**.

Example: Register isolation

```soma
1 { _ 1 >+ !_ } >Chain _  >print   ; ERROR: Register Not Set
```

| Step | Description |
|------|-------------|
| 1 | Push 1 onto AL |
| 2 | Execute Block: pop 1, add 1, store in `_` (Register root) |
| 3 | Block ends, Register is **destroyed** |
| 4 | `_` refers to non-existent Register → Void |
| 5 | `>print` receives Void (or error if undefined) |

Example: CellRef escape

```soma
{ (value) !_.data _.data. } !make_ref
make_ref >Chain !escaped_ref
escaped_ref >print   ; ERROR: Cell no longer exists
```

The CellRef **escapes**, but the Cell it references is destroyed when the Register is destroyed.

### 3.7 Capturing the Entire Register

Because `_` is the named root, the entire Register graph can be captured as a CellReference:

```soma
{
  1 !_.x
  2 !_.y
  _.              ; Push CellRef to entire Register graph
  !saved_context  ; Store it in the Store
}
```

After the Block completes, the saved CellRef can be used:

```soma
saved_context.x >print      ; prints 1
saved_context.y >print      ; prints 2
```

This demonstrates that the Register **is a graph with a root**, and that root can be referenced via `_` (value) or `_.` (CellRef).

### 3.8 Example: Register Usage

```soma
{ !_.x !_.y _.x _.y >+ } !add_two
3 5 add_two >Chain
```

| Step | Token | AL State | Register State | Description |
|------|-------|----------|----------------|-------------|
| 0 | (Block starts) | `[5, 3]` | `{}` | Fresh Register |
| 1 | `!_.y` | `[3]` | `_.y = 5` | Pop 5, store in Register |
| 2 | `!_.x` | `[]` | `_.x = 3, _.y = 5` | Pop 3, store |
| 3 | `_.x` | `[3]` | - | Read from Register |
| 4 | `_.y` | `[5, 3]` | - | Read from Register |
| 5 | `>+` | `[8]` | - | Add |
| 6 | (Block ends) | `[8]` | *destroyed* | Register discarded |

---

## 4. Cells and CellReferences

### 4.1 Cell Identity

A **Cell** is the fundamental unit of storage. Cells have:

- **Identity** — independent of the values they contain
- **Payload** — any value except Void
- **Child Cells** — hierarchical structure

Cells cannot:

- Be accessed unless in a graph (Store or Register)
- Be mutated except via a path or CellReference

### 4.2 CellReferences Are First-Class

A **CellReference** is a reference to a Cell, not its payload.

CellReferences can:

- Be placed on the AL
- Be placed in the payload of another Cell
- Be passed between Blocks

Example:

```soma
(cat) !a.b.c
a.b.c. !ref
ref { !_.ref. (dog) !_.ref }
a.b.c >print   ; prints "dog"
```

| Step | Description |
|------|-------------|
| 1 | Store "cat" at `a.b.c` |
| 2 | Store **CellRef** to `a.b.c` at `ref` |
| 3 | Execute Block: pop CellRef into Register, set its payload to "dog" |
| 4 | `a.b.c` now reads "dog" |

### 4.3 CellReference Syntax

```soma
a.b      ; Value at a.b (may be Nil or Void)
a.b.     ; CellRef for Cell a.b (may be Void if Cell absent)
```

The trailing dot is **syntactically significant**.

---

## 5. Paths

### 5.1 Path Syntax

A **path** is a dot-separated sequence of identifiers:

```
a
config.user.name
session.active.flag
```

Paths refer to locations within the Store or Register.

### 5.2 Path Resolution

**Value access** (no trailing dot):

```soma
a.b
```

Resolution yields one of:

- A value (including Nil)
- Void (if the Cell does not exist)

**CellRef access** (trailing dot):

```soma
a.b.
```

Resolution yields:

- A CellReference to the Cell at `a.b`
- Void (if the Cell does not exist)

### 5.3 Path Behavior Summary

| Path | Meaning | May Return |
|------|---------|------------|
| `a.b` | Payload at a.b | Value, Nil, or Void |
| `a.b.` | CellRef for a.b | CellRef or Void |
| `42 !a.b` | Write payload 42 into a.b | (mutates Store) |
| `X !a.b.` | Replace Cell a.b with new Cell | (mutates Store) |
| `Void !a.b.` | Delete Cell a.b | (mutates Store) |
| `Void !a.b` | **FATAL ERROR** | (cannot store Void) |

**Note:** The same rules apply to Register paths. Simply replace `a.b` with `_.a.b` for Register operations:

| Path | Meaning | May Return |
|------|---------|------------|
| `_.a.b` | Payload at Register path _.a.b | Value, Nil, or Void |
| `_.a.b.` | CellRef for Register path _.a.b | CellRef or Void |
| `42 !_.a.b` | Write payload 42 into Register | (mutates Register) |
| `X !_.a.b.` | Replace Cell _.a.b with new Cell | (mutates Register) |
| `Void !_.a.b.` | Delete Cell _.a.b | (mutates Register) |
| `Void !_.a.b` | **FATAL ERROR** | (cannot store Void) |

### 5.4 Execution Prefix (`>`)

The `>` prefix is used to **execute the value at a path**. This is an atomic operation: read the value and execute it.

**Syntax:**
- `>path` — Execute the Block at Store path `path`
- `>_.path` — Execute the Block at Register path `_.path`

**Examples:**

```soma
>print          ) Execute block at Store path "print"
>+              ) Execute block at Store path "+"
>my_func        ) Execute block at Store path "my_func"
```

**Execution from Register:**

```soma
{
  print !_.action           ) Store print block in Register
  (Hello from register)     ) Push string
  >_.action                 ) Execute block at Register path _.action
}
```

**Output:** `Hello from register`

The `>` modifier works identically with both Store and Register paths. See Chapter 4 (Blocks and Execution) for detailed execution semantics.

---

## 6. Nil vs Void (Corrected Semantics)

### 6.1 Nil

**Nil** is a literal value representing **intentional emptiness**.

- A Cell containing Nil **exists**, but its payload is explicitly empty
- Nil **may be pushed** onto the AL
- Nil **may be stored** in any Cell as its payload
- Nil **may be read back** unchanged
- Nil does **not affect Store structure**

Example:

```soma
Nil !status
status >print   ; prints "Nil"
```

### 6.2 Void

**Void** is a literal value representing **the absence of a Cell**.

- Void is **not a payload**
- Void denotes that a path does **not resolve** to a Cell
- Void **may be pushed** onto the AL
- Void **may participate** in AL-level logic or branching
- Void **may be used** in structural deletion operations
- Void **MUST NOT** be stored in any Cell

Example:

```soma
x.z         ; AL = [Void] (Cell does not exist)
```

### 6.3 The Void-Payload Invariant

**NORMATIVE RULE:**

> A SOMA Cell MUST NOT at any time contain Void as its payload.

If a Store mutation would require placing Void into a Cell as its payload, that operation **MUST be treated as a fatal error**.

Example (fatal):

```soma
Void !a.b   ; FATAL: attempting to store Void
```

Example (legal):

```soma
Void !a.b.  ; Legal: deletes Cell a.b
```

### 6.4 Comparison Table

| Operation | Nil | Void |
|-----------|-----|------|
| Push onto AL | ✓ Legal | ✓ Legal |
| Store as payload | ✓ Legal | ✗ **FATAL** |
| Use in structural delete | ✗ No effect | ✓ Legal |
| Read from non-existent Cell | Returns Void | Returns Void |
| Read from empty Cell | Returns Nil | N/A |

---

## 7. Examples

### 7.1 AL Operations

**Example: Stack manipulation**

```soma
1 2 3 >swap >drop >dup
```

| Step | AL State | Description |
|------|----------|-------------|
| 0 | `[]` | Empty |
| 1 | `[1]` | Push 1 |
| 2 | `[2, 1]` | Push 2 |
| 3 | `[3, 2, 1]` | Push 3 |
| 4 | `[2, 3, 1]` | Swap top 2 |
| 5 | `[3, 1]` | Drop top |
| 6 | `[3, 3, 1]` | Duplicate top |

### 7.2 Store Mutations

**Example: Read-Modify-Write**

```soma
0 !counter.n
counter.n 1 >+ !counter.n
counter.n 1 >+ !counter.n
counter.n >print
```

| Step | Store State | Description |
|------|-------------|-------------|
| 1 | `counter.n = 0` | Initialize |
| 2 | `counter.n = 1` | Increment |
| 3 | `counter.n = 2` | Increment |
| 4 | Prints `2` | Read and print |

### 7.3 Aliasing

**Example: Value copy (no aliasing)**

```soma
42 !a
a !b
99 !a
b >print   ; prints 42
```

**Example: Cell aliasing (shared identity)**

```soma
42 !a
a. !b.
99 !b
a >print   ; prints 99
```

| Description |
|-------------|
| Store 42 at `a` |
| Store **CellRef** to `a` at `b` |
| Update `b` (which is aliased to `a`) |
| `a` now reads 99 |

### 7.4 Register Isolation

**Example: Register does not escape**

```soma
{ 100 !_.temp _.temp } !block
block >Chain >print   ; prints 100
_.temp >print         ; ERROR: Register not set
```

The Register is destroyed when the Block ends.

**Example: Execution from Register path**

```soma
{
  print !_.action           ) Store print block in Register
  (Hello from register)     ) Push string
  >_.action                 ) Execute what's at Register path _.action
}
```

| Step | Token | AL State | Register State | Description |
|------|-------|----------|----------------|-------------|
| 0 | (Block starts) | `[]` | `{}` | Fresh Register |
| 1 | `print` | `[print_block]` | - | Push print block |
| 2 | `!_.action` | `[]` | `_.action = print_block` | Store in Register |
| 3 | `(Hello from register)` | `[(Hello from register)]` | - | Push string |
| 4 | `>_.action` | `[]` | - | Execute block at _.action (prints string) |
| 5 | (Block ends) | `[]` | *destroyed* | Register discarded |

**Output:** `Hello from register`

### 7.5 Nil vs Void

**Example: Nil is storable**

```soma
Nil !status
status >print   ; prints "Nil"
```

**Example: Void denotes absence**

```soma
missing.key >print   ; prints "Void"
```

**Example: Void cannot be stored**

```soma
Void !x   ; FATAL ERROR
```

**Example: Void deletes Cells**

```soma
42 !data.x
Void !data.x.   ; Deletes Cell data.x
data.x >print   ; prints "Void"
```

### 7.6 Combined Example: Linked List Node

```soma
{ Nil !_.next Nil !_.value _.  } !list_new_node
{ !_.value !_.node. _.value !_.node.value } !list_set
{ !_.node. >list_new_node !_.node.next } !list_append
{ !_.node. _.node.next } !list_forward
{ !_.node. _.node.value } !list_get

>list_new_node !head.
(first) head. list_set
head. list_append !head.
(second) head. list_set
head. list_forward list_get >print   ; prints "second"
```

---

## 8. Machine State Summary

The SOMA machine state consists of:

```
(AL, Store, Register, IP)
```

Where:

- **AL** — Finite sequence of values (LIFO)
- **Store** — Hierarchical graph of Cells (global)
- **Register** — Hierarchical graph of Cells (block-local)
- **IP** — Instruction pointer (next token to execute)

Each token transforms the machine state:

```
(AL₁, Store₁, Register₁) → (AL₂, Store₂, Register₂)
```

No hidden stacks, no return contexts, no exception handlers.

---

## Unclear or Contradictory Statements

During analysis of the specification, the following issues were identified:

1. **`_.self` binding mechanism**: The `_.self` automatic binding is defined in Chapter 4 (Blocks and Execution). When a Block begins execution, the SOMA runtime automatically creates a Register Cell at path `_.self` containing the Block value being executed. This binding is local to the execution context and destroyed when the Block completes. Note: Earlier drafts used `_self` (without dot), which is invalid syntax.

2. **CellRef vs Block in `>Chain` examples**: Several examples use `square.` or `toggle.` (CellRefs) where `>Chain` expects a Block value. These should use `square` (payload) instead.

3. **Register destruction semantics for escaped CellRefs**: While the spec states "CellReferences in a Register can escape the local block execution," it does not clarify what happens when an escaped CellRef is dereferenced after the Register is destroyed. This should cause an error or return Void.

4. **Path resolution for intermediate Nil Cells**: If `a.b` exists with payload Nil, does `a.b.c` resolve to Void (Cell absent) or is it an error? The specification should clarify whether Nil payloads block further path traversal.

These issues do not affect the fundamental machine model but require clarification for full implementability.

---

**End of Chapter 03 — Machine Model**
