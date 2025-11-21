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

The AL is a **shared LIFO stack** serving as the primary dynamic execution context. It is a **value conduit**, not a call stack:

- **Shared**: All blocks (parent, child, nested) share the same AL
- **LIFO**: Last In, First Out - values are pushed and popped from the top
- It does not track return addresses
- It does not manage stack frames
- It does not unwind on errors
- It is a **value conduit** for passing data between blocks, not a control structure

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
5 square >chain
```

| Step | Token | AL State | Description |
|------|-------|----------|-------------|
| 0 | (start) | `[]` | Empty |
| 1 | Block literal | `[{>dup >*}]` | Push block |
| 2 | `!square` | `[]` | Pop block, store at `square` |
| 3 | `5` | `[5]` | Push 5 |
| 4 | `square` | `[{>dup >*}, 5]` | Push block from Store |
| 5 | `>chain` | (enters block) | Pop block and execute it |
| 5.1 | `>dup` | `[5, 5]` | Duplicate top |
| 5.2 | `>*` | `[25]` | Multiply |
| 5.3 | (block ends) | `[25]` | Returns to chain, AL has Nil, stops |
| 6 | (end) | `[25]` | Final AL state |

The block consumed 1 value (implicitly) and produced 1 value.

### 1.6 AL as Control Context

The AL determines which Block executes next under `>choose` and `>chain`.

Example: Conditional execution

```soma
True { "Yes" >print } { "No" >print } >choose
```

| Before `>choose` | AL State |
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

Each named location in the Store refers to a **Cell**. A Cell has two **orthogonal (independent) components**:

1. **Value** (payload): The data stored at this Cell (Int, Block, Nil, Void, CellRef, String)
2. **Subpaths** (children): Dictionary mapping names to child Cells

**These components are completely independent.** Setting or reading a Cell's value has NO effect on its subpaths.

**Cell Structure:**

```
        ┌─────────────────┐
        │      Cell       │
        ├─────────────────┤
        │ value: 42       │  ← Payload (any CellValue)
        ├─────────────────┤
        │ subpaths: {     │  ← Children (independent of value)
        │   "x": Cell,    │
        │   "y": Cell     │
        │ }               │
        └─────────────────┘
```

**Key Properties:**

- A Cell has a **persistent identity** independent of its value or subpaths
- Writing a value **replaces the payload** but **preserves the Cell identity and subpaths**
- Adding child Cells **modifies subpaths** but **does not affect the payload**
- A Cell can have **both** a meaningful value **and** children simultaneously

**Example: Value and Subpaths Coexist**

```soma
Nil !a.b        ; Set a.b's VALUE to Nil
23 !a.b.c       ; Create child 'c' in a.b's SUBPATHS
a.b             ; Returns Nil (reads VALUE)
a.b.c           ; Returns 23 (traverses SUBPATHS to c)
```

**Cell `a.b` now has:**
- Value: `Nil`
- Subpaths: `{"c": Cell(value: 23, subpaths: {})}`

This orthogonality enables powerful patterns like graph structures where nodes have both data and edges.

### 2.2.1 Value vs Subpaths Orthogonality

The independence of value and subpaths is fundamental to understanding SOMA's Cell model. These two components operate on separate axes:

**Reading a Cell reads ONLY its value:**

```soma
42 !node
node            ; Returns 42 (reads VALUE only, ignores subpaths)
```

**Path traversal uses ONLY subpaths:**

```soma
42 !a.b.c       ; a.b.c has value 42
a.b.c           ; Traverses a → b → c through SUBPATHS, returns c's VALUE (42)
```

Path resolution walks through the **subpaths dictionary**, completely ignoring the values of intermediate Cells.

**Any value can have children:**

All of these are perfectly legal:

```soma
) Void with children (from auto-vivification)
42 !a.b.c       ; 'a' has Void value but children {"b": ...}
                ; 'a.b' has Void value but children {"c": ...}

) Nil with children
Nil !parent
23 !parent.child
parent          ; Returns Nil (VALUE)
parent.child    ; Returns 23 (traverses SUBPATHS)

) Int with children
42 !node
99 !node.sub
node            ; Returns 42 (VALUE)
node.sub        ; Returns 99 (traverses SUBPATHS)

) Block with children
{ >print } !action
(help text) !action.description
>action                      ; Executes the block (reads VALUE)
action.description >print   ; Prints "help text" (traverses SUBPATHS)
```

**Why this matters:**

This orthogonality enables **graph structures as first-class citizens** without requiring explicit node types. A Cell can simultaneously:

- Hold a value (data at this node)
- Point to other Cells (edges in a graph)

Example: Linked list node

```soma
) Node with both value and next pointer
1 !list.value
list.next. !list.next        ; CellRef to next node

) The Cell at 'list' has:
)   value: Void (never set)
)   subpaths: {"value": Cell(1), "next": Cell(CellRef)}
```

**Key Principle:**

> Setting or reading a Cell's **value** never affects its **subpaths**.
> Creating or removing **subpaths** never affects the **value**.

### 2.3 Nil vs Void — The Semantic Distinction

SOMA distinguishes between "never set" and "explicitly set to empty":

| Concept | Meaning | Can WRITE? | Can READ? |
|---------|---------|------------|-----------|
| **Void** | Cell exists for structure but has **never been set** | **No** (fatal error) | **Yes** (returns Void) |
| **Nil** | Cell has been **explicitly set to empty** | **Yes** (legal) | **Yes** (returns Nil) |

**The Key Insight:** Void represents "this was never initialized" while Nil represents "this was set to nothing."

**CRITICAL RULES:**

```
Void !path     → FATAL ERROR (cannot write Void as payload)
Void !path.    → Legal (deletes Cell structurally)
Nil !path      → Legal (stores Nil as payload)
```

**Examples:**

```soma
Nil !a.b     ; Legal: explicitly set a.b to Nil
a.b          ; AL = [Nil] - was set to empty
```

```soma
Void !a.b    ; FATAL ERROR: cannot write Void as payload
```

```soma
Void !a.b.   ; Legal: delete Cell a.b structurally
```

```soma
42 !a.b.c    ; Auto-vivifies a and a.b with Void payload
a.b          ; AL = [Void] - never set (auto-vivified)
a.b.c        ; AL = [42] - was explicitly set
```

### 2.4 Cell Creation and Auto-Vivification

A Cell is created automatically when a value is written to a path that did not previously exist. This is called **auto-vivification**.

**Key principle:** Intermediate cells created during auto-vivification are added to their parent's **subpaths** with **Void** payload (never set).

**CRITICAL: Auto-vivification affects VALUE only, not SUBPATHS**

When auto-vivification creates intermediate Cells:
- Their **value** is set to Void (representing "never explicitly set")
- Their **subpaths** remain independent and can still exist/be traversed
- The two components are orthogonal

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
  a: Cell(value: Void, subpaths: {"b": ...})
    └─ b: Cell(value: Void, subpaths: {"c": ...})
         └─ c: Cell(value: 42, subpaths: {})
}
```

**What happened:**

1. Cell `a` was auto-created with **Void** value and subpaths `{"b": ...}`
2. Cell `a.b` was auto-created with **Void** value and subpaths `{"c": ...}`
3. Cell `a.b.c` was explicitly set with value **42** and empty subpaths

**Reading auto-vivified cells:**

```soma
42 !a.b.c
a.b.c        ; AL = [42] - explicitly set (reads VALUE)
a.b          ; AL = [Void] - auto-vivified, never set (reads VALUE)
a            ; AL = [Void] - auto-vivified, never set (reads VALUE)
```

**Path traversal through Void:**

Void intermediate cells allow path traversal - you can traverse through cells with Void value to reach deeper values:

```soma
42 !a.b.c       ; a and a.b have Void value
a.b.c           ; Can traverse through a (Void) and a.b (Void) to reach c (42)
                ; Path traversal uses SUBPATHS, ignores intermediate VALUES
                ; Returns 42 ✓
```

This is crucial for sparse structures - you don't have to explicitly initialize every intermediate node.

**Auto-vivified Cells can still have children:**

Because value and subpaths are orthogonal, a Cell with Void value can still have children in its subpaths:

```soma
42 !a.b.c       ; Auto-vivifies 'a' with Void value
99 !a.x         ; Add child 'x' to a's SUBPATHS

a               ; Returns Void (VALUE was never set)
a.b.c           ; Returns 42 (traverses SUBPATHS)
a.x             ; Returns 99 (traverses SUBPATHS)
```

Cell `a` now has:
- Value: `Void` (never explicitly set, from auto-vivification)
- Subpaths: `{"b": Cell(...), "x": Cell(99)}`

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

**Structural deletion (path deletion):**

```soma
Void !a.b.c.
```

- Deletes the **path** `a.b.c` from the Store tree
- Removes the edge from parent's subpaths dictionary
- **Does not delete the Cell** if other references (CellRefs or paths) to it exist
- If the Cell is still accessible via CellRefs, it persists (see Section 4.4)
- If no other references exist, the Cell becomes unreachable and may be reclaimed

**Example: Path deletion with surviving CellRef**

```soma
42 !a.b
a.b. !ref       ) Create CellRef to Cell
Void !a.b.      ) Delete path a.b
ref             ) Still works! Returns 42 - Cell persists via CellRef
```

**Example: Path deletion without CellRefs**

```soma
42 !a.b
Void !a.b.      ) Delete path a.b
a.b             ) Returns Void - Cell is now unreachable
```

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

A **Register** is a hierarchical graph identical in structure to the Store, but with **block-local scope and complete isolation**.

**CRITICAL ISOLATION PRINCIPLE:**

> **Each block execution creates a fresh, empty Register that is destroyed when the block completes.**

**Key Properties:**

- **Isolated**: Each block gets its own Register, completely independent from all other blocks
- **Fresh**: Every block starts with an empty Register
- **Temporary**: Registers are destroyed when the block completes
- **No Sharing**: Inner blocks **cannot** see outer block's Register paths
- **No Nesting**: There is **no lexical scoping** between parent and child block Registers

**Note on Block Access:** To access the currently executing block, use the `>block` built-in (see Chapter 6 — Built-ins). There are no automatic Register bindings.

**If you want to share data between blocks, you MUST:**
- Use the **Store** (global, persistent state)
- Pass values via the **AL** (stack-based communication)
- Use **CellRefs** to share structure

### 3.2 Register Lifecycle

When a Block begins execution:

1. **Create** a fresh, empty Register
2. Execute the block's code
3. **Destroy** the Register when block completes

**Properties:**

- **Isolated**: No connection to parent/child block Registers
- **Temporary**: Destroyed when block completes
- **Local**: Only visible within the executing block
- **Fresh**: Always starts empty

### 3.3 Store vs Register

| Feature | Store | Register |
|---------|-------|----------|
| **Scope** | Global | Block-local |
| **Lifetime** | Persistent | Block execution |
| **Sharing** | All blocks can access | **Completely isolated per block** |
| **Purpose** | Shared state | Local computation |
| **Visibility** | Global across all blocks | Only the executing block |
| **Nesting** | N/A (single global) | **No nesting - fresh per block** |
| **Root** | Single, unnamed | Single, named `_` |
| **Syntax** | `a.b` | `_.a.b` |
| **Write syntax** | `!a.b` | `!_.a.b` |
| **Root value access** | N/A (unnamed) | `_` |
| **Root CellRef access** | N/A (unnamed) | `_.` |

### 3.4 When to Use Store vs Register vs AL

**Use Store when:**
- Sharing data between unrelated blocks
- Persisting configuration or state
- Global variables or shared counters
- Communication across the entire program

**Use Register when:**
- Temporary local computation (`_.temp`, `_.result`)
- Loop counters in recursive blocks
- Local variables that don't need to escape

**Use AL when:**
- Passing arguments to blocks
- Returning values from blocks
- Stack-based computation
- Explicit data flow between blocks

### 3.5 Register Root

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

### 3.6 Register Path Syntax

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

### 3.7 Register Write Operations

Register writes follow the same syntax as Store writes, but target Register paths:

```soma
42 !_.x           ; Store 42 in register path _.x
!_.y              ; Pop AL and store in register path _.y
Nil !_.z          ; Store Nil in register path _.z
Void !_.w.        ; Delete register cell at _.w
Void !_.w         ; FATAL ERROR: cannot store Void as payload
```

### 3.8 Register Deletion Semantics

**Register and Store have identical Cell structure and identical deletion semantics.**

Deletion works the same way in both hierarchical graphs. To delete a Register cell, use `Void !_.path.` (with trailing dot), just like Store deletion `Void !path.`:

**Example: Simple Register deletion**

```soma
{
  23 !_.temp
  _.temp >print     ) Prints: 23

  Void !_.temp.     ) Delete Register cell
  _.temp            ) Returns Void (Cell no longer accessible)
}
```

**Example: Register deletion with CellRef**

```soma
{
  42 !_.data
  _.data. !_.ref    ) CellRef to Cell

  Void !_.data.     ) Delete path _.data
  _.ref             ) Still works! Cell persists via CellRef
}
```

**Example: Register cleanup pattern**

```soma
{
  ) Use Register cells as temporary workspace
  1 !_.a
  2 !_.b
  _.a _.b >+        ) AL = [3]

  ) Clean up workspace
  Void !_.a.
  Void !_.b.

  ) Return result (AL = [3])
}
```

**Cross-reference:** Register deletion follows the exact same rules as Store deletion (Section 2.7). Both operate on Cell hierarchies with identical semantics:

- `Void !path.` (Store) deletes the path from Store tree
- `Void !_.path.` (Register) deletes the path from Register tree
- Both preserve Cells if other references (CellRefs) exist
- Both make the path return Void after deletion

### 3.9 Register Isolation

**CRITICAL: Registers are completely isolated per block.**

Inner blocks **cannot** see outer block's Register cells. Each block sees only its own Register.

#### Example 1: Inner Block Has Its Own Register

```soma
>{1 !_.n >{2 !_.n} _.n >print}  ) Prints 1
```

**What happens:**

1. Outer block executes, gets Register₁
2. `1 !_.n` → Store 1 in Register₁ path `_.n`
3. `>{2 !_.n}` → Execute inner block
   - Inner block gets **fresh Register₂** (empty)
   - `2 !_.n` → Store 2 in Register₂ path `_.n`
   - Inner block completes
   - Register₂ is **destroyed**
4. Back in outer block with Register₁
5. `_.n >print` → Register₁ still has `_.n = 1`
6. **Prints 1** ✓

**Key insight:** Inner block's `_.n` was in a different Register. It didn't affect outer block's `_.n`.

#### Example 2: Inner Block Cannot See Outer Register

```soma
>{1 !_.n >{_.n >print}}  ) FATAL ERROR
```

**What happens:**

1. Outer block executes, gets Register₁
2. `1 !_.n` → Store 1 in Register₁ path `_.n`
3. `>{_.n >print}` → Execute inner block
   - Inner block gets **fresh Register₂** (empty)
   - `_.n` → Try to read Register₂ path `_.n`
   - Register₂ has no `_.n` → resolves to **Void**
   - Push Void onto AL
   - `>print` → Try to execute Void
   - **FATAL ERROR**: Cannot execute Void ❌

**Key insight:** Inner blocks cannot access outer block's Register cells.

#### Example 3: Root Scope Is A Block

```soma
23 !_
_ >print  ) Prints 23
```

**What happens:**

- The root/top-level is itself a block
- It has its own Register with root `_`
- `23 !_` → Store 23 at Register root
- `_ >print` → Read Register root value (23), print it
- **Prints 23** ✓

### 3.10 The Correct Way to Share Data Between Blocks

#### ❌ WRONG - Try to use outer Register (fails)

```soma
>{1 !_.n >{_.n >print}}  ) FATAL ERROR
```

Inner block can't see outer's `_.n`.

#### ✅ RIGHT - Pass via AL

```soma
>{1 !_.n _.n >{>print}}  ) Prints 1
```

**Execution:**
1. Outer block: `1 !_.n` stores 1
2. Outer block: `_.n` pushes 1 onto AL
3. Inner block executes with AL = [1]
4. Inner block: `>print` pops and prints 1

Data passed explicitly via the AL.

#### ✅ RIGHT - Use Store

```soma
>{1 !data.n >{data.n >print}}  ) Prints 1
```

**Execution:**
1. Outer block: `1 !data.n` stores 1 in **Store** (global)
2. Inner block: `data.n` reads from **Store**
3. Inner block: `>print` prints 1

Data shared via the Store (persistent, global state).

#### ✅ RIGHT - Return via AL

```soma
>{
  >{5 !_.n _.n _.n >*} !_.square     ) Define helper that squares AL top
  7 >_.square                         ) Call it with 7
  >print                              ) Prints 49
}
```

**Execution:**
1. Define `_.square` block in outer Register
2. `7` pushes 7 onto AL
3. `>_.square` executes the block (which has its own fresh Register)
   - Pops 7 from AL → stores in its own `_.n`
   - Computes `_.n * _.n = 49`
   - Leaves 49 on AL
4. Outer block continues with AL = [49]
5. `>print` prints 49

Blocks communicate via the AL (stack).

### 3.11 Examples Showing Isolation in Practice

#### Example: Nested Loop Counters

```soma
>{
  0 !_.i                           ) Outer counter
  {
    0 !_.i                         ) Inner counter (different Register!)
    _.i 5 ><
      { _.i 1 >+ !_.i >block }     ) Inner loop uses its own _.i
      { }
    >choose >chain
  } !_.inner_loop

  _.i 3 ><
    {
      >_.inner_loop                ) Call inner loop
      _.i 1 >+ !_.i                ) Increment outer _.i
      >block
    }
    { }
  >choose >chain
}
```

**Key points:**
- Outer block has `_.i` for outer counter
- `_.inner_loop` block has its own `_.i` for inner counter
- They don't interfere - different Registers
- Each loop maintains its own counter independently

#### Example: Helper Functions with Local State

```soma
>{
  { !_.x _.x _.x >* } !_.square    ) Helper: square a number
  { !_.x _.x 2 >* } !_.double      ) Helper: double a number

  5 >_.square >print               ) 25
  5 >_.double >print               ) 10
}
```

**Key points:**
- Each helper function call gets fresh Register
- `_.square` and `_.double` each have their own `_.x`
- No interference even though both use `_.x`
- Completely isolated

#### Example: Passing Context via Store

```soma
>{
  (config) !_.context              ) Outer has context in Register

  _.context !global_context        ) Save to Store for sharing

  >{
    global_context >print          ) Inner reads from Store
  }
}
```

**Key points:**
- Outer block's Register context not visible to inner
- Must explicitly save to Store to share
- Inner block reads from Store (global)

### 3.12 Common Patterns

#### Pattern 1: Accumulator via AL

```soma
>{
  0                                ) Initial value on AL
  { !_.acc _.acc 1 >+ } !_.inc    ) Increment AL top
  >_.inc >_.inc >_.inc             ) Apply 3 times
  >print                           ) Prints 3
}
```

#### Pattern 2: Shared State via Store

```soma
0 !counter                         ) Global counter in Store

{ counter 1 >+ !counter } !increment
{ counter >print } !show

>increment >increment >show        ) Prints 2
```

#### Pattern 3: Local Computation in Register

```soma
>{
  42 !_.value                      ) Local to this block
  _.value _.value >* !_.squared    ) Local computation
  _.squared >print                 ) Prints 1764
}
```

### 3.13 Register Locality and CellRef Escape

Registers are destroyed when their Block completes, but **Cells referenced by escaped CellRefs can persist**.

**Key Principle:** Just like Store Cells (Section 4.4), Register Cells persist as long as they're accessible via any CellRef, even after the Register is destroyed.

**Example: Register destroyed, but value lost (no CellRef)**

```soma
1 { _ 1 >+ !_ } >chain _  >print   ; ERROR: Register Not Set
```

| Step | Description |
|------|-------------|
| 1 | Push 1 onto AL |
| 2 | Execute Block: pop 1, add 1, store in `_` (Register root) |
| 3 | Block ends, Register is **destroyed** |
| 4 | `_` refers to non-existent Register → Void |
| 5 | `>print` receives Void (or error if undefined) |

**Example: CellRef escapes, Cell persists**

```soma
{ (value) !_.data _.data. } >chain !escaped_ref
escaped_ref >print   ; Prints "value" - Cell persists!
```

| Step | Description |
|------|-------------|
| 1 | Execute Block: store "value" in Register path `_.data` |
| 2 | Create CellRef to Register Cell `_.data` |
| 3 | Push CellRef onto AL |
| 4 | Block ends, Register destroyed, but **Cell persists** |
| 5 | CellRef stored at `escaped_ref` in Store |
| 6 | Dereferencing `escaped_ref` accesses the Cell → "value" |

**The Cell persists** because the CellRef provides access to it, even though the Register that originally contained it is gone.

**Example: Detached linked list**

```soma
{
  1 !_.head.value
  _.head.next. !_.head.next
  2 !_.head.next.value
  Nil !_.head.next.next

  _.head.       ) Return CellRef to list
} >chain !list

) Block destroyed, Register destroyed, but list persists!
list.value              ) 1
list.next.value         ) 2
list.next.next          ) Nil
```

The linked list was built in the Register, but returned as a CellRef. The Register Cells persist even though the Register is gone, because the CellRef keeps them accessible.

**Example: "New" pattern (object creation)**

```soma
{
  (initial data) !_.obj.data
  0 !_.obj.counter
  {
    ) Note: This block needs the object CellRef on AL to work
    !_.this                          ) Pop object from AL
    _.this.counter 1 >+ !_.this.counter
  } !_.obj.increment

  _.obj.        ) Return handle to object
} >chain !myObj

myObj.data              ) "initial data"
myObj.counter           ) 0
myObj. >myObj.increment ) Pass object to its own increment method
myObj.counter           ) 1
```

Create a structure in the Register, return a CellRef - like `new` in other languages. The structure persists because the CellRef keeps it accessible.

### 3.14 Capturing the Entire Register

Because `_` is the named root, the entire Register graph can be captured as a CellReference:

```soma
{
  1 !_.x
  2 !_.y
  _.              ; Push CellRef to entire Register graph
  !saved_context  ; Store it in the Store
}
```

After the Block completes and the Register is destroyed, the Cells persist because the CellRef keeps them accessible:

```soma
saved_context.x >print      ; prints 1
saved_context.y >print      ; prints 2
```

**Key insight:** Even though the Register is destroyed, the **Cells** in the graph persist because the CellRef at `saved_context` provides access to them (see Section 4.4 on Cell Lifetime).

### 3.15 Example: Register Usage

```soma
{ !_.x !_.y _.x _.y >+ } !add_two
3 5 add_two >chain
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

### 4.2 CellReferences Are Immutable Values

A **CellReference (CellRef)** is an immutable value that provides access to a Cell.

**CellRefs have value semantics:**

- CellRefs are immutable values, like Int, String, or Block
- They provide direct access to Cells
- Whether they are "copied" or shared internally is unobservable and implementation-defined
- **No identity comparison** — you cannot distinguish between "same CellRef" vs "different CellRef to same Cell"
- Multiple CellRefs can refer to the same Cell

**CellRefs can:**

- Be placed on the AL
- Be stored in the payload of another Cell
- Be passed between Blocks
- Persist independently of the paths that created them

**Key Principle:** CellRefs are values, not references in the traditional pointer sense. They behave like all other SOMA values (Int, String, Block, Nil).

**Example: Basic CellRef usage**

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

**Example: Multiple CellRefs to the same Cell**

```soma
42 !cell
cell. !ref1
cell. !ref2
cell. !ref3

99 !cell        ) Change Cell's value
ref1            ) Returns 99 (all refs point to same Cell)
ref2            ) Returns 99
ref3            ) Returns 99
```

All three CellRefs refer to the same Cell. When the Cell's value changes, all CellRefs reflect the updated value.

**Example: CellRefs are immutable values**

```soma
node. !ref1     ) ref1 is immutable value
ref1 !ref2      ) ref2 gets same immutable value
ref1 !ref3      ) ref3 gets same immutable value
```

Whether the runtime copies or shares the internal representation of these CellRefs is unobservable. They behave identically as immutable values.

### 4.3 CellReference Syntax

```soma
a.b      ; Value at a.b (may be Nil or Void)
a.b.     ; CellRef for Cell a.b (may be Void if Cell absent)
```

The trailing dot is **syntactically significant**.

### 4.4 Cell Lifetime and Persistence

**Cells have independent existence from paths.**

A Cell persists as long as it is accessible through any route:
- Any path in the Store
- Any path in any active Register
- Any CellRef on the AL
- Any CellRef stored in another Cell's value

**Key Principle:** Deleting a path removes the path from the tree, not the Cell itself.

#### Path Deletion vs Cell Deletion

**Path deletion removes the path:**

```soma
23 !a.b
a.b. !ref       ) Create CellRef to the Cell
Void !a.b.      ) Delete path a.b from Store tree
ref             ) Still works! Returns 23
```

**What happened:**

1. `23 !a.b` — Created Cell, made accessible via Store path `a.b`
2. `a.b. !ref` — Created immutable CellRef value pointing to that Cell
3. `Void !a.b.` — Removed path `a.b` from Store tree (deleted tree edge)
4. `ref` — Dereferenced CellRef, accessed Cell, returned value 23

**The Cell still exists** because the CellRef at path `ref` provides access to it.

#### Cell Persistence Rules

A Cell persists as long as it is accessible. When all access routes are removed, the Cell becomes inaccessible and may be reclaimed (implementation-defined, like garbage collection).

**Example 1: Path deleted, CellRef persists**

```soma
42 !a
a. !ref
Void !a.        ) Delete path a
ref             ) Returns 42 - Cell persists via CellRef
```

**Example 2: Multiple paths to same Cell**

```soma
42 !node
node. !alias1
node. !alias2
Void !node.     ) Delete original path
alias1          ) Returns 42 - Cell accessible via alias1
alias2          ) Returns 42 - Cell accessible via alias2
```

**Example 3: CellRef in AL**

```soma
42 !temp
temp.           ) CellRef on AL
Void !temp.     ) Delete path
                ) AL = [CellRef to Cell]
                ) Dereference AL top -> 42
```

The CellRef on the AL keeps the Cell alive.

**Example 4: CellRef stored in another Cell**

```soma
42 !data
data. !container.ref    ) Store CellRef as value in another Cell
Void !data.             ) Delete original path
container.ref           ) Returns CellRef (can still dereference)
```

#### CellRefs Never "Dangle"

In traditional languages, deleting memory can create dangling pointers:

```c
int *p = malloc(sizeof(int));
*p = 42;
free(p);
*p;         // DANGLING - undefined behavior
```

**In SOMA, CellRefs never dangle:**

```soma
42 !cell
cell. !ref
Void !cell.     ) Delete path, but Cell persists
ref             ) NOT dangling - Cell still exists!
```

CellRefs in SOMA never "dangle" in the traditional sense because:
- Deleting a path doesn't delete the Cell
- Cells persist as long as accessible
- CellRefs provide direct access

#### Semantic Definition, Not Mechanism

This behavior is defined **semantically, not mechanistically**:
- We don't prescribe heap allocation
- We don't prescribe garbage collection
- We don't prescribe reference counting
- We only define observable behavior

Implementations might use garbage collection, reference counting, or other techniques, but the observable semantics remain: **Cells persist as long as they're accessible.**

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

## 6. Nil vs Void — Complete Semantics

### 6.1 The Fundamental Distinction

**Void and Nil are fundamentally different:**

- **Void** = "This cell has never been explicitly set" (absence, uninitialized)
- **Nil** = "This cell has been explicitly set to empty/nothing" (presence of emptiness)

**CRITICAL: Both Nil and Void can have children.**

The distinction between Nil and Void applies **only to the Cell's value**. It has **nothing to do with subpaths**. Because value and subpaths are orthogonal (Section 2.2.1):

- A Cell with **Nil** value can have children
- A Cell with **Void** value can have children
- A Cell with **any** value can have children

**Example: Nil with children**

```soma
Nil !parent
42 !parent.child
parent           ; Returns Nil (VALUE)
parent.child     ; Returns 42 (traverses SUBPATHS)
```

Cell `parent` has:
- Value: `Nil` (explicitly set to empty)
- Subpaths: `{"child": Cell(42)}`

**Example: Void with children**

```soma
42 !a.b.c        ; Auto-vivifies 'a' and 'a.b' with Void values
a.b              ; Returns Void (VALUE)
a.b.c            ; Returns 42 (traverses SUBPATHS)
```

Cell `a.b` has:
- Value: `Void` (never explicitly set, auto-vivified)
- Subpaths: `{"c": Cell(42)}`

This distinction is analogous to:

| Domain | Void | Nil |
|--------|------|-----|
| **JavaScript** | `undefined` | `null` |
| **Python** | Uninitialized variable | `None` |
| **Databases** | Column never inserted | `NULL` value explicitly inserted |
| **Logic** | Logical absurdity (⊥) | Empty set (∅) |
| **Type Theory** | Bottom type / uninhabited | Unit type / Maybe Nothing |

### 6.2 Void — "Never Set"

**Void** represents the state of a Cell that exists for structural purposes but has never been given a value.

**Properties:**

- Auto-vivified intermediate cells start with Void value
- Can be detected (hypothetically with `>isVoid`)
- Reading returns Void (not an error)
- **Cannot** be written as a value (fatal error)
- **Can** be used for structural deletion (`Void !path.`)
- **Can have children** (value and subpaths are orthogonal)

**When do cells have Void value?**

1. When auto-vivified during path writes
2. After structural deletion (cell no longer exists, read returns Void)
3. When reading a path that doesn't exist

**Examples:**

```soma
42 !a.b.c       ; Creates: a (Void), a.b (Void), a.b.c (42)

a.b.c           ; Returns 42 (explicitly set)
a.b             ; Returns Void (auto-vivified, never set)
a               ; Returns Void (auto-vivified, never set)
```

```soma
) Attempt to write Void as value
Void !a.b       ; FATAL ERROR - violates Void-Payload-Invariant
```

```soma
) Reading Void is legal
42 !a.b.c
a.b             ; Returns Void - this is fine! ✓
```

```soma
) Void cells can have children
42 !a.b.c       ; Auto-vivifies 'a' with Void value
99 !a.x         ; Add sibling to 'a.b' in a's subpaths
a               ; Returns Void (value never set)
a.b.c           ; Returns 42 (traverses subpaths)
a.x             ; Returns 99 (traverses subpaths)
```

### 6.3 Nil — "Explicitly Set to Empty"

**Nil** is a literal value representing **intentional emptiness**.

**Properties:**

- Deliberately chosen value
- Represents intentional absence
- Reading returns Nil
- **Can** be written as a value
- **Can** be read back unchanged
- Distinct from "never initialized"
- **Can have children** (value and subpaths are orthogonal)

**Examples:**

```soma
Nil !status
status >print   ; prints "Nil"
```

```soma
(default value) !config.setting       ; Set explicitly
Nil !optional.field                   ; Explicitly empty

config.setting                         ; "default value"
optional.field                         ; Nil (not Void)
```

```soma
) Nil cells can have children
Nil !node
42 !node.left
99 !node.right
node             ; Returns Nil (value is explicitly empty)
node.left        ; Returns 42 (traverses subpaths)
node.right       ; Returns 99 (traverses subpaths)
```

### 6.4 The Void-Payload Invariant

**NORMATIVE RULE:**

> A SOMA Cell MUST NOT at any time contain Void as its value. If a Store or Register mutation would require placing Void into a Cell as its value, that operation MUST be treated as a fatal error.

**Fatal error:**

```soma
Void !a.b       ; FATAL ERROR - cannot write Void as value
```

**Legal (structural deletion):**

```soma
Void !a.b.      ; Legal - delete the cell entirely
```

**Why this matters:** Void represents "never set" - you cannot intentionally set something to "never set". Only auto-vivification can create cells with Void value.

**Important: This applies ONLY to the value, not subpaths**

The Void-Payload Invariant restricts the **value** component only. A Cell's **subpaths** are independent and can exist regardless of whether the value is Void:

```soma
42 !a.b.c       ; Auto-vivifies 'a' with Void value
                ; 'a' has: value=Void, subpaths={"b": ...}
                ; This is legal! ✓
```

### 6.5 Distinguishing Void from Nil

**Hypothetical `>isVoid` operation:**

```soma
42 !a.b.c       ; Auto-vivifies a and a.b with Void

a.b >isVoid     ; True - never explicitly set
(Never set) (Has been set) >choose >print    ; Prints "Never set"

Nil !a.b        ; Explicitly set to Nil

a.b >isVoid     ; False - now has been set (to Nil)
a.b             ; Returns Nil
(Never set) (Has been set) >choose >print    ; Prints "Has been set"
```

**The distinction in practice:**

```soma
) Void vs Nil in optional fields
(John) !person.name
Nil !person.middle_name         ; Explicitly no middle name
42 !person.age

person.middle_name              ; Nil - explicitly empty
person.spouse                   ; Void - never set (different meaning!)
```

### 6.6 Reading Void vs Nil

**Both are valid values to read - neither is an error:**

```soma
42 !intermediate.node.leaf
intermediate.node           ; Returns Void (auto-vivified) ✓

Nil !empty.node
empty.node                  ; Returns Nil ✓
```

**The difference:**

- Reading **Void** means "this was never set" (auto-vivified or doesn't exist)
- Reading **Nil** means "this was set to empty"

### 6.7 Writing Void vs Nil

**You CAN write Nil:**

```soma
Nil !path       ; Legal - set payload to Nil ✓
```

**You CANNOT write Void:**

```soma
Void !path      ; FATAL ERROR - violates Void-Payload-Invariant ❌
```

**But you CAN use Void for structural deletion:**

```soma
Void !path.     ; Legal - delete the cell ✓
```

### 6.8 Comparison Table

| Operation | Nil | Void |
|-----------|-----|------|
| Push onto AL | ✓ Legal | ✓ Legal |
| Store as value | ✓ Legal | ✗ **FATAL** |
| Use in structural delete | ✗ No effect | ✓ Legal (`!path.`) |
| Read from non-existent Cell | Returns Void | Returns Void |
| Read from Cell with this value | Returns Nil | Returns Void |
| Read from auto-vivified Cell | Returns Void | Returns Void |
| Result of path traversal failure | Returns Void | Returns Void |
| Can have children in subpaths | ✓ Yes | ✓ Yes |

### 6.9 Auto-Vivification Creates Void

**When writing to a.b.c:**

1. **If `a` doesn't exist:**
   - Create cell `a` with **Void** value and empty subpaths
   - Add `a` to parent's subpaths

2. **If `a.b` doesn't exist:**
   - Create cell `a.b` with **Void** value and empty subpaths
   - Add `b` to `a`'s subpaths

3. **Set `a.b.c`:**
   - Create cell `a.b.c` with the provided value
   - Add `c` to `a.b`'s subpaths

**Result:**

```
Store:
  a → Cell(value: Void, subpaths: {"b": ...})
    └─ b → Cell(value: Void, subpaths: {"c": ...})
         └─ c → Cell(value: 42, subpaths: {})
```

**Key insight:** Intermediate nodes are **structural scaffolding** with Void value until explicitly set. But they still have subpaths that allow path traversal.

### 6.10 Implications for Sparse Data Structures

**Sparse arrays:**

```soma
) Only set the values you need
1 !array.0
1 !array.100
1 !array.1000

) Intermediate indices are Void (not Nil)
array.50        ; Void - never set, not "set to empty"
```

**Optional fields:**

```soma
(John) !person.name
Nil !person.middle_name         ; Explicitly no middle name
42 !person.age

person.middle_name              ; Nil - explicitly empty
person.spouse                   ; Void - never set (different meaning!)
```

**Nested structures:**

```soma
(value) !deep.nested.path.value

deep                    ; Void - structural parent
deep.nested             ; Void - structural parent
deep.nested.path        ; Void - structural parent
deep.nested.path.value  ; "value" - explicitly set
```

### 6.11 Error Cases

**Fatal error: Writing Void as value**

```soma
Void !a.b       ; FATAL ERROR
```

**Why:** Violates Void-Payload-Invariant.

**Solution:** Don't write anything (leave auto-vivified) or write Nil:

```soma
) Don't write - let auto-vivification handle it
42 !a.b.c       ; a.b has Void value automatically ✓

) Or write Nil explicitly
Nil !a.b        ; Explicitly empty ✓
42 !a.b.c       ; a.b now has Nil value, not Void
                ; Both approaches: a.b can have children in subpaths
```

**Not an error: Reading Void**

```soma
42 !a.b.c
a.b             ; Returns Void - this is fine! ✓
```

Reading Void is not an error. It just means "this cell exists structurally but has never had its value set."

### 6.12 Path Traversal Through Void

**Path traversal uses subpaths, not values:**

Because value and subpaths are orthogonal (Section 2.2.1), path traversal walks through the **subpaths dictionary** and completely ignores intermediate Cell values.

**Void intermediate cells allow path traversal:**

```soma
42 !a.b.c       ; a and a.b have Void value

a.b.c           ; Traverses a's subpaths → b's subpaths → c
                ; Returns c's VALUE (42)
                ; Intermediate VALUES (Void) are ignored ✓
```

This is crucial for sparse structures - you don't have to explicitly initialize every intermediate node's value.

**Path traversal through Nil also works:**

```soma
Nil !a.b        ; Explicitly set a.b's VALUE to Nil
42 !a.b.c       ; Create child 'c' in a.b's SUBPATHS

a.b             ; Returns Nil (reads VALUE)
a.b.c           ; Returns 42 (traverses SUBPATHS, ignores a.b's VALUE)
```

**Why this works:** Path resolution uses only the **subpaths** component. The **value** component (whether Void, Nil, or any other value) is completely ignored during path traversal. Only the final Cell's value is returned.

**The mechanism:**

```
Path: a.b.c
Step 1: Start at root, lookup "a" in root's subpaths → find Cell(a)
Step 2: Lookup "b" in Cell(a)'s subpaths → find Cell(b)  [ignores a's value]
Step 3: Lookup "c" in Cell(b)'s subpaths → find Cell(c)  [ignores b's value]
Step 4: Return Cell(c)'s value → 42
```

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
>block >print         ) prints 100
_.temp >print         ) ERROR: Register not set (block's Register is destroyed)
```

The Register is destroyed when the Block ends.

**Example: Execution from Register path**

```soma
>{
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

**Example: Nested blocks with isolated Registers**

```soma
>{
  1 !_.outer_val

  >{
    2 !_.inner_val
    _.inner_val >print      ) Prints 2
    _.outer_val >print      ) FATAL ERROR: _.outer_val is Void
  }

  _.outer_val >print        ) Prints 1
  _.inner_val >print        ) FATAL ERROR: _.inner_val is Void
}
```

**Key points:**
- Outer block's `_.outer_val` is in Outer Register
- Inner block's `_.inner_val` is in Inner Register (completely separate)
- Inner block **cannot** access `_.outer_val` from outer block
- Outer block **cannot** access `_.inner_val` from inner block (already destroyed)

**Example: Correct data sharing via Store**

```soma
>{
  1 !shared.outer_val       ) Store in global Store

  >{
    2 !shared.inner_val     ) Store in global Store
    shared.inner_val >print ) Prints 2
    shared.outer_val >print ) Prints 1 (reads from Store)
  }

  shared.outer_val >print   ) Prints 1
  shared.inner_val >print   ) Prints 2
}
```

**Key points:**
- Both blocks use Store paths (no `_` prefix)
- Store is global - all blocks can access
- Data persists across block boundaries

### 7.5 Nil vs Void

**Example: Nil is storable, Void is not**

```soma
Nil !status
status >print   ; prints "Nil"
```

```soma
Void !x   ; FATAL ERROR - cannot write Void as payload
```

**Example: Auto-vivification creates Void**

```soma
42 !a.b.c
a.b.c >print   ; prints "42" (explicitly set)
a.b >print     ; prints "Void" (auto-vivified, never set)
a >print       ; prints "Void" (auto-vivified, never set)
```

**Example: Void vs Nil distinction**

```soma
42 !data.x.y        ; Auto-vivifies data and data.x with Void
Nil !config.opt     ; Explicitly set to Nil

data.x              ; Returns Void (never set)
config.opt          ; Returns Nil (set to empty)
```

**Example: Void allows path traversal**

```soma
42 !a.b.c       ; a and a.b have Void payload
a.b.c           ; Traverses through Void cells, returns 42
```

**Example: Void deletes Cells structurally**

```soma
42 !data.x
Void !data.x.   ; Deletes Cell data.x
data.x >print   ; prints "Void" (cell no longer exists)
```

**Example: Sparse array with Void**

```soma
1 !array.0
1 !array.100
1 !array.1000

array.0 >print      ; prints "1"
array.50 >print     ; prints "Void" (never set)
array.100 >print    ; prints "1"
```

### 7.6 Combined Example: Linked List Node

```soma
{ Nil !_.next Nil !_.value _.  } !list_new_node
{ !_.value !_.node. _.value !_.node.value } !list_set
{ !_.node. >list_new_node !_.node.next } !list_append
{ !_.node. _.node.next } !list_forward
{ !_.node. _.node.value } !list_get

>list_new_node !head.
(first) head. list_set >chain
head. list_append >chain !head.
(second) head. list_set >chain
head. list_forward >chain list_get >chain >print   ) prints "second"
```

### 7.7 CellRef Persistence and Path Deletion

**Example: Path deleted, Cell persists via CellRef**

```soma
42 !data
data. !ref
Void !data.     ) Delete path
ref >print      ) Prints 42 - Cell persists via CellRef
```

**Example: Multiple CellRefs to same Cell**

```soma
100 !counter
counter. !ref1
counter. !ref2
200 !counter    ) Update Cell value
ref1 >print     ) Prints 200
ref2 >print     ) Prints 200
```

**Example: Aliasing with path deletion**

```soma
Chain !kette            ) German name for Chain
print !drucken          ) German name for print

(Hallo Welt) >drucken   ) Works! Prints "Hallo Welt"
1 2 >+ !result { result >drucken } >kette  ) Prints 3
```

Store a CellRef to a built-in at a different path - create aliases.

**Example: Detached data structure**

```soma
{
  ) Build a tree structure in Register
  5 !_.root.value
  3 !_.root.left.value
  7 !_.root.right.value

  _.root.       ) Return CellRef to root
} >chain !tree

) Tree persists, accessible via CellRef (Register destroyed)
tree.value              ) 5
tree.left.value         ) 3
tree.right.value        ) 7
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
- **Register** — Hierarchical graph of Cells (block-local, isolated)
- **IP** — Instruction pointer (next token to execute)

Each token transforms the machine state:

```
(AL₁, Store₁, Register₁) → (AL₂, Store₂, Register₂)
```

No hidden stacks, no return contexts, no exception handlers.

---

## 9. Concurrency and Memory Model

### 9.1 Happens-Before Memory Model

**SOMA is defined with a happens-before memory model, but the exact nature of that model is intentionally implementation-defined.**

This approach:
- Fits with machine algebra (systematic, mechanistic)
- Defines observable ordering relationships
- Is well-understood in concurrent systems

The specification leaves the exact memory model undefined because:
- It may be application-specific (single-threaded, multi-threaded, distributed)
- It may be hardware-specific (x86, ARM, GPU)
- An overly restrictive specification would limit implementations

### 9.2 What SOMA Specifies

#### 9.2.1 Sequential Consistency Within a Thread

Within a single execution thread, operations occur in program order:

```soma
1 !a        ) Step 1
2 !b        ) Step 2 (happens-after Step 1)
3 !c        ) Step 3 (happens-after Step 2)
```

**Guaranteed:** If a thread executes these statements, they occur in this order.

#### 9.2.2 Atomicity of Individual Operations

Each primitive operation is atomic:

```soma
42 !path    ) Atomic: either completes or doesn't (no partial state)
path        ) Atomic: reads complete value
Void !path. ) Atomic: deletion completes or doesn't
```

**Guaranteed:** You never observe a "half-written" value.

This applies to both Store and Register operations - all individual operations are atomic.

#### 9.2.3 Store Consistency

The Store has a consistent state at all times:

```soma
) Thread 1
1 !a
2 !b        ) Fatal error here
3 !c        ) Never executes
```

**Guaranteed:** Store is in a valid state after the error. Cell `a` contains 1, `b` and `c` are unchanged.

**Not guaranteed:** Whether other threads see `a=1` before the error depends on the memory model.

### 9.3 What SOMA Does NOT Specify

#### 9.3.1 Cross-Thread Visibility Ordering

```soma
) Thread 1
42 !shared

) Thread 2
shared      ) When does this see 42?
```

**Unspecified:** The happens-before relationship between threads depends on the implementation's memory model.

#### 9.3.2 Synchronization Primitives

SOMA does not define:
- Mutexes
- Semaphores
- Atomic compare-and-swap
- Memory barriers

**Rationale:** These may be provided as built-ins or extensions, but are not part of the core language.

#### 9.3.3 Thread Creation/Management

SOMA does not specify:
- How threads are created
- How threads are synchronized
- Thread scheduling

**Rationale:** This may be platform-specific or provided by runtime.

### 9.4 Happens-Before Model (Abstract)

**Definition:** SOMA execution can be described by a partial order of operations with a happens-before relation (⊏).

**Properties:**

1. **Program Order:** Within a thread, if operation A comes before operation B in program text, then A ⊏ B

2. **Transitivity:** If A ⊏ B and B ⊏ C, then A ⊏ C

3. **Synchronization:** The exact synchronization edges that establish happens-before between threads are implementation-defined

**What this means:**
- Single-threaded: happens-before = program order (simple)
- Multi-threaded with locks: happens-before includes lock release → acquire
- Distributed: happens-before might include message send → receive
- Actor model: happens-before includes message send → message processing

### 9.5 Single-Threaded vs Multi-Threaded Execution

#### Single-Threaded Execution

In a single-threaded SOMA implementation:
- Happens-before is simply program order
- All operations are sequentially consistent
- No memory model concerns

**Example:**

```soma
1 !a
2 !b
a b >+
```

**Execution:** Totally ordered, deterministic, simple.

#### Multi-Threaded Execution

In multi-threaded implementations:
- Happens-before relationships must be defined by the implementation
- Cross-thread visibility depends on synchronization
- Memory model must be documented

**Example: Unsynchronized access (behavior undefined)**

```soma
) Thread 1
42 !x

) Thread 2
x >print
```

**Result:** Undefined - Thread 2 might see previous value, 42, or any intermediate state depending on memory model.

**Example: Synchronized via Store (implementation-defined)**

```soma
) Thread 1
>lock
42 !shared
>unlock

) Thread 2
>lock
shared >print
>unlock
```

**Result:** Implementation must define happens-before for lock/unlock operations.

### 9.6 Implementation Guidance

#### For Single-Threaded Implementations

Sequential consistency - program order equals execution order. No additional concerns.

#### For Multi-Threaded Implementations

**Choose a memory model:**
- Sequential consistency (simplest, may be slower)
- TSO (Total Store Order - like x86)
- Relaxed (like ARM, requires careful synchronization)

**Document it:** Specify the happens-before edges for your synchronization primitives.

#### For Distributed Implementations

**Choose a consistency model:**
- Causal consistency
- Eventual consistency
- Strong consistency

**Document it:** Specify the happens-before edges for your message passing.

### 9.7 Error Recovery and Valid State

When a fatal error occurs: **"The Store remains in its last valid state."**

**What this means:**

```soma
1 !a            ) Completes successfully
2 !b            ) Fatal error here
3 !c            ) Never executes
```

**After the error:**
- `a` contains 1 (operation completed)
- Store is in a **valid** state (no corrupted data structures)
- Individual operations are atomic (no partial writes)

**Guaranteed:** The Store is in a valid state (no corruption).

**Not guaranteed:** Exactly which operations completed in multi-threaded scenarios (depends on memory model).

**Conservative interpretation for portable code:** After an error, only operations that completed *before* the error are guaranteed to be visible. Cross-thread visibility is unspecified.

### 9.8 Key Principles Summary

1. **SOMA uses a happens-before memory model** (systematic, mechanistic)
2. **Exact details are implementation-defined** (application/hardware specific)
3. **Single-threaded execution is straightforward** (program order)
4. **Multi-threaded requires implementation-specific synchronization**
5. **Individual operations are atomic** (no partial writes)
6. **Store remains valid after errors** (no corruption)

---

## Unclear or Contradictory Statements

During analysis of the specification, the following issues were identified:

1. **CellRef vs Block in `>chain` examples**: Several examples use `square.` or `toggle.` (CellRefs) where `>chain` expects a Block value. These should use `square` (payload) instead.

~~2. **Register destruction semantics for escaped CellRefs**: RESOLVED - Section 3.13 and Section 4.4 now clarify that Cells (whether in Store or Register) persist as long as they're accessible via any CellRef, even after the Register is destroyed. The CellRef keeps the Cell alive.~~

~~3. **Path resolution through Nil payloads**: RESOLVED - Section 6.12 now clarifies that path traversal works through ANY value (including Nil and Void) because path resolution uses only the subpaths component. Value and subpaths are orthogonal (Section 2.2.1).~~

These issues do not affect the fundamental machine model but require clarification for full implementability.

---

**End of Chapter 03 — Machine Model**
