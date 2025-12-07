# Debug Philosophy: Leveraging SOMA's Mutable Namespace

**Status:** Reference Implementation Guide
**Version:** SOMA v1.0
**Created:** 2025-12-01

---

## Overview

This document establishes the design philosophy for all debugging tools in SOMA. Unlike traditional languages that require special VM hooks, debugging features, or runtime instrumentation, SOMA's debugging approach leverages the language's fundamental property: **the namespace is mutable**.

The key insight: `chain`, `choose`, and other control flow primitives are not VM magic—they're just Store bindings. You can swap them out.

---

## 1. Core Philosophy

### State is Accessible, Not Hidden

SOMA's machine model exposes three explicit state components:
- **The Accumulator List (AL)** — the value conduit
- **The Store** — global persistent state
- **The Register** — block-local isolated state

Because these are explicit and introspectable, debugging tools don't need to peek behind abstraction layers. They just need to observe and report state transitions.

### Debug Tools Should Not Modify the VM

The reference implementation's VM (`soma/vm.py`) defines SOMA's semantics. Debug tools should **never** require changes to:
- The execution model
- The semantics of `>choose` or `>chain`
- The Register isolation model
- The AL manipulation primitives

Instead, debug tools work **within** SOMA's existing semantics by exploiting the mutable namespace.

### The Pattern: Swap Store Bindings

All debug tools follow this pattern:

```soma
) Save the original binding
chain !backup.chain

) Replace with instrumented version
debug.chain !chain

) Run code being debugged
{ ... your problematic loop ... } >chain

) Restore original binding
backup.chain !chain
```

This works because `chain` is just a path in the Store. When you write `>chain`, SOMA:
1. Looks up `chain` in the Store
2. Finds a Block (either the builtin or your replacement)
3. Executes that Block

By swapping the binding, you intercept the execution without modifying the VM.

---

## 2. Why This Works: Understanding SOMA's Execution Model

### Control Flow is Not Special

In languages like Python or C++, `if` and `while` are keywords baked into the parser. You cannot redefine them.

In SOMA, `>choose` and `>chain` are **builtins stored in the namespace**:

```python
# vm.py initialization
self.root["choose"] = Cell(value=BuiltinBlock("choose", builtin_choose))
self.root["chain"] = Cell(value=BuiltinBlock("chain", builtin_chain))
```

These are just Cells in the Store. The `>` operator looks up paths and executes blocks. There's nothing preventing you from replacing these bindings:

```soma
) Replace 'choose' with a logging version
{
  (CHOOSE called!) >print
  builtin.choose >^           ) Delegate to original
} !choose
```

Now every `>choose` in your program logs its execution.

### Scoped Replacement via Backup/Restore

The backup/restore pattern ensures debug instrumentation is **scoped**:

```soma
) Original behavior
some.function >^              ) Normal execution

) Instrumented behavior
chain !backup.chain           ) Save original
debug.chain !chain            ) Install instrumented version
some.function >^              ) Executes with logging
backup.chain !chain           ) Restore original

) Back to original behavior
some.function >^              ) Normal execution again
```

This is zero-overhead when not in use and scoped to specific code sections.

---

## 3. Key Point: debug.* is NOT Part of the SOMA Spec

The SOMA language specification defines:
- The machine model (AL, Store, Register)
- The execution semantics
- The builtin primitives (`>choose`, `>chain`, `>^`, etc.)

It does **not** define:
- `debug.al.dump`
- `debug.chain`
- `debug.choose`
- Any other debugging utilities

These are **reference implementation tools** provided in the standard library (`stdlib.soma`) or as VM-provided helpers for convenience. They are not required for SOMA compliance.

**Implication:** Different SOMA implementations can provide different debug tools. The pattern (swap bindings, instrument, restore) remains universal, but the specific tools are implementation-defined.

---

## 4. Current Debug Tools

### 4.1 `debug.al.dump` — Non-Destructive AL State Dump

**Purpose:** Inspect the current AL state without consuming any items.

**Implementation:** Builtin in `vm.py`

**Usage:**
```soma
(Before operation) >print
debug.al.dump >^
42 13 >+
(After operation) >print
debug.al.dump >^
```

**Output:**
```
Before operation
DEBUG AL [0 items]: []
After operation
DEBUG AL [1 items]: [55]
```

**Why it's a builtin:** Requires direct access to `vm.al` to read without popping.

**Design principle:** Zero side effects. The AL is unchanged after calling this.

---

### 4.2 `debug.chain` — Instrumented Chain Loop

**Purpose:** Log each iteration of a `>chain` loop, showing AL state before each block execution.

**Implementation:** Defined in `stdlib.soma` (or as a VM helper)

**Usage:**
```soma
) Save original chain
chain !backup.chain

) Install debug version
debug.chain !chain

) Run problematic loop
Nil
(a) (b) (c) >list.from_strings
list.reverse
>chain

) Restore original
backup.chain !chain
```

**Expected output:**
```
CHAIN: iter 1
  AL state: [Nil, CellRef(0x7f8a...), Block(list.reverse.#loop)]
  Executing: list.reverse.#loop
CHAIN: iter 2
  AL state: [CellRef(0x7f8b...), Block(list.reverse.#loop)]
  Executing: list.reverse.#loop
CHAIN: iter 3
  AL state: [CellRef(0x7f8c...), Block(list.reverse.#loop)]
  Executing: list.reverse.#loop
CHAIN: terminated (Nil encountered)
  Final AL: [CellRef(0x7f8c...)]
```

**Why this helps:** Makes the invisible iteration process visible. Shows:
- When each block executes
- What the AL looks like before execution
- Why the chain terminated (Nil vs non-Block)

**Implementation sketch:**
```soma
{
  ) debug.chain: Instrumented version of chain
  0 !_.iteration
  {
    !_.candidate
    _.candidate >type (Block) >==
      {
        _.iteration >inc !_.iteration
        (CHAIN: iter ) >print _.iteration >toString >print
        (  AL state: ) >print debug.al.dump >^
        (  Executing block) >print
        _.candidate >^              ) Execute the block
        ) Continue - check AL top again
        { !_.candidate } >^         ) Loop back with updated _.candidate
      }
      {
        (CHAIN: terminated) >print
        (  Final AL: ) >print debug.al.dump >^
        _.candidate                 ) Push back non-Block value
        Nil                         ) Terminate the meta-loop
      }
    >choose >^
  } >chain
} !debug.chain
```

---

### 4.3 `debug.choose` — Branch Selection Logger

**Purpose:** Log which branch `>choose` selects, making control flow visible.

**Implementation:** Defined in `stdlib.soma`

**Usage:**
```soma
) Save original
choose !backup.choose

) Install debug version
debug.choose !choose

) Run code
x 0 ><
  { (positive) >print }
  { (not positive) >print }
>choose >^

) Restore
backup.choose !choose
```

**Expected output:**
```
CHOOSE: condition = True
  Selected: TRUE branch
  (Executing...)
positive
```

**Implementation sketch:**
```soma
{
  ) AL: [False-branch, True-branch, condition]
  !_.condition !_.true_branch !_.false_branch

  (CHOOSE: condition = ) >print _.condition >toString >print
  _.condition
    {
      (  Selected: TRUE branch) >print
      _.true_branch
    }
    {
      (  Selected: FALSE branch) >print
      _.false_branch
    }
  builtin.choose >^              ) Delegate to real choose
} !debug.choose
```

---

## 5. Design Principles for All Debug Tools

### 5.1 Zero Overhead When Not in Use

If you don't install the debug version, there's **zero performance impact**. The original builtin executes directly.

This is different from languages with "debug mode" flags that affect all execution. SOMA's approach is opt-in and granular.

### 5.2 Scoped to Specific Code Sections

The backup/restore pattern ensures instrumentation is **local**:

```soma
) Only this section is instrumented
chain !backup.chain
debug.chain !chain
problematic.function >^
backup.chain !chain

) Rest of program runs normally
other.function >^
```

You don't instrument the entire program—just the section you're debugging.

### 5.3 Educational: Shows SOMA's Execution Model

Good debug output doesn't just say "error here." It teaches the user how SOMA executes:

**Bad debug message:**
```
Error at line 42
```

**Good debug message:**
```
CHAIN: iter 3
  AL state: [Nil, Block]
  Register: { _.old_list, _.new_list }
  ERROR: Undefined Register path '_.new_new_list'

  Did you forget to pop context?
  Pattern: !_.  (pop CellRef, then access fields)
```

Debug tools should reveal:
- When Registers are created (and isolated)
- What's on the AL before/after operations
- How `>chain` iterates
- Why `>choose` selected a particular branch

### 5.4 No VM Modifications Needed

The reference implementation (`vm.py`) should **not** need changes to support debug tools.

If a debug feature requires modifying the VM, it's the wrong approach. Find a way to implement it via Store binding replacement or AL/Register introspection.

**Exception:** Built-in non-destructive introspection (like `debug.al.dump`) that cannot be implemented in pure SOMA. These should be minimal and clearly documented as VM-specific helpers.

---

## 6. Practical Example: Debugging a Problematic Loop

Let's debug the classic `list.reverse` implementation.

### The Bug

```soma
{
  ) Loop body for list.reverse
  !_.old_list !_.new_list

  _.old_list >nil?
    { _.new_list }              ) Done: return accumulated list
    {
      ) Continue: pop head, cons onto new_list
      _.old_list >car           ) Get head
      _.new_new_list            ) BUG: typo in variable name!
      >cons
      !_.new_list

      _.old_list >cdr !_.old_list
      _.old_list _.new_list list.reverse.#loop
    }
  >choose >^
} !list.reverse.#loop
```

**Error:**
```
RuntimeError: Undefined Register path: '_.new_new_list'
  At: list.reverse.#loop
```

### Debug Session

```soma
) Install instrumented chain
chain !backup.chain
debug.chain !chain

) Run the failing code
Nil
(a) (b) (c) >list.from_strings
list.reverse
>chain

) Restore
backup.chain !chain
```

**Output:**
```
CHAIN: iter 1
  AL state: [Nil, CellRef(0x7f8a1234), Block(list.reverse.#loop)]
  Register (before): { }
  Executing: list.reverse.#loop

  Register (after pop): { _.old_list: CellRef(0x7f8a1234), _.new_list: Nil }

  CHOOSE: condition = False (list not nil)
    Selected: FALSE branch (continue)

  ERROR: Undefined Register path '_.new_new_list'
    Current Register: { _.old_list: CellRef(0x7f8a1234), _.new_list: Nil }
    Looking for: _.new_new_list

    Available paths:
      - _.old_list
      - _.new_list

    Did you mean '_.new_list'?
```

**The bug is immediately visible:** Typo in variable name. Should be `_.new_list`, not `_.new_new_list`.

### Why This Debug Pattern Works

1. **Shows iteration count** — We're only on iteration 1, so the bug happens immediately
2. **Shows Register state** — We can see what variables exist
3. **Shows AL state** — We can verify the right values are being passed
4. **Non-invasive** — After restoring `chain`, the program runs normally

---

## 7. Future Debug Tools (Examples)

These follow the same philosophy:

### 7.1 `debug.register.dump` — Inspect Current Register

```soma
debug.register.dump >^
```

**Output:**
```
DEBUG Register [3 bindings]:
  _.old_list → CellRef(0x7f8a1234)
  _.new_list → Nil
  _.counter → 42
```

**Implementation:** VM builtin (requires direct access to current Register).

### 7.2 `debug.^` — Instrumented Block Execution

```soma
^ !backup.^
debug.^ !^

{ (inner) >print } >^    ) Logs: "Executing block from AL"

backup.^ !^
```

**Implementation:** SOMA-level wrapper around the original `^` binding.

### 7.3 `debug.step` — Interactive Step-Through

```soma
debug.step.on >^

{ ... } >^    ) Pauses after each token, waits for Enter key

debug.step.off >^
```

**Implementation:** Requires VM support for pausing execution, but still uses binding replacement pattern.

---

## 8. Contrast with Traditional Debuggers

### Traditional Approach (GDB, pdb, etc.)

- **External tool** that attaches to running process
- **VM modifications** required (breakpoint hooks, stack introspection)
- **Language-agnostic** but requires deep runtime integration
- **Always available** but potentially high overhead

### SOMA Approach

- **Language-level** tools defined in SOMA itself
- **No VM modifications** required (uses mutable namespace)
- **Language-specific** and leverages SOMA's explicit state model
- **Opt-in** with zero overhead when not in use

### Why SOMA's Approach Works

SOMA's execution model is **already explicit**:
- The AL is visible
- The Store is accessible
- The Register can be introspected
- Control flow primitives are Store bindings

Traditional debuggers fight against hidden state (call stacks, exception handlers, implicit variables). SOMA has no hidden state to fight against.

---

## 9. Guidelines for Implementing New Debug Tools

### Step 1: Identify What You Need to Observe

- AL state transitions?
- Register bindings?
- Control flow decisions?
- Store modifications?

### Step 2: Find the Interception Point

- Replacing a builtin? (`choose`, `chain`, `^`)
- Wrapping a stdlib function? (`list.reverse`, `times`)
- Adding introspection? (`debug.al.dump`, `debug.register.dump`)

### Step 3: Implement via Binding Replacement

```soma
{
  ) Log or instrument
  (DEBUG: ...) >print

  ) Delegate to original
  original.binding >^

  ) Log result if needed
  (DEBUG: result = ...) >print
} !instrumented.version
```

### Step 4: Document the Backup/Restore Pattern

Users should always see:

```soma
) Backup
original !backup.original

) Install
instrumented !original

) Use
... your code ...

) Restore
backup.original !original
```

### Step 5: Keep It Educational

Debug output should teach SOMA's execution model, not just dump data.

**Bad:**
```
AL: [25, Block, CellRef, 42]
```

**Good:**
```
CHAIN: iter 2
  AL before: [CellRef(accumulator), Block(loop-body)]
  Why still looping: Top of AL is a Block
  Executing: loop-body
```

---

## 10. Limitations and Trade-offs

### What This Approach Cannot Do

1. **Time-travel debugging** — SOMA's state is mutable and forward-only
2. **Breakpoints at arbitrary tokens** — Requires VM modification
3. **Post-mortem inspection** — Once a fatal error occurs, state is lost

These would require VM changes or external tooling.

### What This Approach Excels At

1. **Scoped instrumentation** — Debug specific functions without affecting the rest
2. **Teaching execution model** — Makes SOMA's semantics visible
3. **Zero overhead** — No performance cost when not in use
4. **Pure SOMA implementation** — Most tools can be written in SOMA itself

---

## 11. Summary

SOMA's debug philosophy is simple:

1. **Leverage the mutable namespace** — Control flow primitives are Store bindings
2. **Use backup/restore pattern** — Scope instrumentation to specific code sections
3. **Keep tools educational** — Teach SOMA's execution model through debug output
4. **Avoid VM modifications** — Work within SOMA's existing semantics

The result is a debugging approach that:
- Requires no special VM support
- Has zero overhead when not in use
- Teaches users how SOMA executes
- Maintains the language's transparency and explicitness

**Remember:** `debug.*` is not part of the SOMA specification. It's a reference implementation tool demonstrating what's possible when the namespace is mutable and state is explicit.

---

## Appendix: Complete Debug Pattern Template

```soma
) ============================================================
) DEBUGGING SESSION TEMPLATE
) ============================================================

) 1. Save original bindings
chain !backup.chain
choose !backup.choose

) 2. Install debug versions
debug.chain !chain
debug.choose !choose

) 3. Run problematic code with instrumentation
{
  ) Your code here
  some.function >^
} >^

) 4. Restore original bindings
backup.chain !chain
backup.choose !backup.choose

) 5. Verify normal operation restored
some.function >^    ) Should run without debug output
```

Copy this template whenever you need to debug a SOMA program.

---

**End of Debug Philosophy Document**
