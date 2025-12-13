# Control Flow: The Emergent Macro System

- **Status**: Normative
- **Version**: SOMA v1.0
- **Section**: 05

---

## Overview

SOMA takes a radical approach to control flow. Unlike traditional languages that provide built-in keywords like `if`, `while`, `for`, or `switch`, SOMA defines **only two control primitives**:

- **`>choose`**: Select between two blocks based on a boolean
- **`>chain`**: Execute blocks until no block remains on the AL

From these two primitives, something remarkable emerges: control structures that look and behave exactly like built-in language features, but are actually **user-defined patterns**. This is SOMA's emergent macro system — a mechanism similar to Lisp's `defmacro`, but arising naturally from the language's semantics without requiring a separate macro facility.

This section demonstrates how `if`, `ifelse`, `while`, `do`, and finite state machines all emerge from `>choose` and `>chain`. Understanding this mechanism is key to grasping SOMA's power as a language that reveals rather than obscures computation.

---

## 1. The Two Primitives

### 1.1 `>choose` — Conditional Selection

`>choose` is SOMA's only branching primitive. **CRITICAL:)** It is a **SELECTOR**, not an executor.

**AL Contract (pre-execution):)**

```
Top → C (false branch value)
      B (true branch value)
      A (boolean condition)
```

**Program syntax:)**

```soma
A B C >choose
```

**Semantics:)**

1. Pop three values from the AL: `C`, `B`, `A` (in that order)
2. `A` must be a Boolean, or fatal error
3. If `A == True`:) **push value **`B`** onto AL**
4. If `A == False`:) **push value **`C`** onto AL**
5. `>choose`** does NOT execute blocks** — it only selects one value
6. The unchosen value is discarded

**Example:)**

```soma
True
  { "Path taken" >print }
  { "Path not taken" >print }
>choose
```

Result: AL contains the **block** `{ "Path taken" >print }` (NOT executed)

To execute the selected block, use `>^`:)

```soma
True
  { "Path taken" >print }
  { "Path not taken" >print }
>choose >^
```

Output: `Path taken`

**Key distinction:)** `>choose` is a **selector** (picks a value), while `>^` is an **executor** (runs a block from AL). This separation is fundamental to SOMA's semantics.

---

### 1.2 `>chain` — Block Continuation Loop

`>chain` is SOMA's only looping primitive. It repeatedly executes blocks until the AL top is no longer a block.

**Semantics:**

1. Pop the top value from the AL
2. If it is **not** a Block: push it back and stop (
3. `>chain` terminates)
4. If it **is** a Block: execute it
5. After execution, examine the new AL top
6. If the new top is a Block, repeat from step 3
7. Otherwise, stop

**Key insight:** `>chain` does not recurse and does not grow a call stack. It is a **flat iteration** over a sequence of blocks left on the AL by each previous block.

**Example 1: Single block execution**

```soma
{ 5 5 >* } >chain
```

Result: AL contains `[25]`. The block executes once, leaves `25` on the AL, and `>chain` terminates because `25` is not a block.

**Note:** For single execution, `>{ 5 5 >* }` is simpler (see section 1.3). This example demonstrates `>chain`'s termination behaviour.

**Example 2: Self-perpetuating block**

```soma
{ "tick" >print >block } >chain
```

This prints `tick` forever. Why?

- The block executes, prints `tick`, then pushes `>block` (the currently executing block) onto the AL
- `>chain` sees a block on top and executes it again
- This repeats infinitely

**IMPORTANT ERRATA CORRECTION:**

The original specification contained examples that incorrectly used **CellRefs** (trailing-dot paths) with `>chain`. For example:

```soma
7 square. >chain >print  ; WRONG!
```

Under SOMA semantics:

- `square.` resolves to a **CellRef** (not the block itself)
- `>chain` sees a non-Block value and immediately terminates
- This is a silent logic error

**Correct form:**

```soma
7 square >chain >print  ; CORRECT
```

This retrieves the **block value** stored at `square`, not a reference to the cell. All examples in this document use the corrected form.

---

### 1.3 Direct Block Execution: `>{...}`

The simplest form of control flow is direct block execution. The `>` prefix executes what follows — including inline blocks.

**Pushing vs Executing:**

```soma
{ 5 5 >* }           ) Pushes block onto AL (not executed)
>{ 5 5 >* }          ) Executes block immediately, AL = [25]
```

The difference is the `>` prefix. Without it, the block is a value on the AL. With it, the block runs immediately.

**When to use direct execution:**

- **Immediate evaluation**: When you want code to run now, not later
- **Grouping operations**: When you need a sequence to execute as a unit
- **Inline control flow**: When defining a named block would be overkill

**Example:**

```soma
10 !x
>{ x 5 >> { (x is large) >print } { } >choose >^ }
x >print
```

The block executes immediately, conditionally printing before the final `x >print`.

**Contrast with `>chain`:**

- **`>{ body }`**:  — execute once, immediately
- **`{ body } >chain`**:  — execute and continue while blocks remain on AL

Use `>{...}` for single execution. Use `>chain` when you need looping or block continuation.

---

## 2. The `^` Operator: User-Defined Execution

**This is the KEY to understanding SOMA's macro-like behavior.**

### 2.1 The Problem: Executing AL Top

In languages like Forth and Lisp, there are built-in primitives for executing a value on the stack:

- ****Forth**: `EXECUTE` — pops the execution token and runs it**:  
- **Lisp**
- : 
- (funcall fn args

These are **language primitives** — you can't implement them yourself.

SOMA has **no built-in execute-from-AL operation**. But you can define it:

```soma
{ !_ >_ } !^        ) Create "execute top of AL" operator
```

Now `>^` behaves exactly like Forth's `EXECUTE`:)

```soma
(Cats) print >^     ) Prints 'Cats'
```

### 2.2 How `^)` Works: Step-by-Step Execution Trace

Let's trace the execution of `(Cats) print >^)` in detail:)

**Initial state:)**

```
AL: []
```

```
Step 1: 
(Cats
AL: ["Cats"]
```

**Step 2: `print` — Push print block onto AL**

```
AL: ["Cats", print_block]
```

Note: `print` without `>` pushes the **block value** at Store path "print" onto the AL.

**Step 3: `>^` — Execute the block stored at Store path "^")**

The block stored at `^)` is: `{ !_ >_ }`

When this block executes:)

**3a. Block starts with fresh Register**

```
AL: ["Cats", print_block]
Register: {}
```

**3b. `!_` — Pop AL top, store at Register root**

```
AL: ["Cats"]
Register: {_: print_block}
```

The `!_` operation pops `print_block` from the AL and stores it at the Register root path `_`.

**3c. `>_` — Read Register root and execute it**

```
AL: ["Cats"]
Register: {_: print_block}
```

The `>_` operation reads the value at Register path `_` (which is `print_block`) and **executes** it.

**3d. `print_block` executes — Pops "Cats" and prints it**

```
AL: []
Output: Cats
```

**Final state:)**

```
AL: []
Output: Cats
```

### 2.3 Why This Is Powerful

The `^` operator is **user-defined** using only SOMA primitives:

- `!_` (store at Register root)
- `>_` (execute from Register root)

This demonstrates that **execution itself is not a primitive** in SOMA — it's emergent from the `>path` semantics.

### 2.4 Comparison to Other Languages

| Language                   | Execute Operator   | Implementation     |
|----------------------------|--------------------|--------------------|
| **Forth**                  | `EXECUTE`          | Built-in primitive |
| **Lisp**`funcall`, `apply` | Built-in primitive |                    |
| **SOMA**                   | `{ !_ >_ } !^`     | **User-defined!**  |

This is exactly like Forth's `EXECUTE` or Lisp's `FUNCALL`, but **you defined it yourself** using only paths and blocks.

### 2.5 Examples Using `^`

**Execute different operations based on data:**

```soma
(Hello) print >^        ) Prints: Hello
42 inc >^               ) Increments: AL = [43]
5 { 10 >+ } >^          ) Adds 10: AL = [15]
```

**Store operations in variables:**

```soma
print !_.operation
(World) _.operation >^  ) Prints: World
```

**Build execution tables (see Section 5):**

```soma
print !commands.show
inc !commands.next
(show) commands >^      ) Executes 'print'
```

---

## 3. Building Emergent Control Structures

The power of `>choose` and `>chain` lies not in what they do individually, but in **what emerges when you combine them**. Let's build traditional control structures from scratch.

### 3.1 IF (Single Branch)

**Traditional syntax:**

```
if (condition) {
  body
}
```

**SOMA pattern:**

```soma
condition
  { body }
  { }
>choose >^
```

**How it works:**

- `>choose` selects the body block if `True`, or empty block if `False`
- `>^` executes the selected block
- This is **if without else**

**Example:**

```soma
x 10 >>
  { "x is greater than 10" >print }
  { }
>choose >^
```

**Note:** Without `>^`, the selected block would just sit on the AL without executing. The `>^` operator is what actually runs it.

---

### 3.2 IF/ELSE (Two Branches)

**Traditional syntax:**

```
if (condition) {
  true_body
} else {
  false_body
}
```

**SOMA pattern (using `>ifelse` from stdlib):**

```soma
condition
  { true_body }
  { false_body }
>ifelse
```

**How it works:**

- `>ifelse` is defined in stdlib as `{ >choose >^ }`
- It combines selection (`>choose`) and execution (`>^`)
- One branch always executes

**Raw pattern (without stdlib):**

```soma
condition
  { true_body }
  { false_body }
>choose >^
```

**Example:**

```soma
user.authenticated
  { dashboard_page >render }
  { login_page >render }
>ifelse
```

**Key insight:** The `>ifelse` helper demonstrates SOMA's macro-like behavior — it looks like a built-in control structure but is actually just `{ >choose >^ }` defined in user code.

---

### 3.3 WHILE Loop

**Traditional syntax:**

```
while (condition) {
  body
}
```

**SOMA pattern (using Store for loop variable):**

```soma
{
  condition
  {
    body
    >block
  }
  { }
  >choose >^
} >chain
```

**How it works:**

Let's trace execution step by step:

1. The outer block is pushed onto the AL
2. `>chain` pops and executes it
3. Inside the block:
  - `condition` is evaluated (pushes a boolean)
  - Two blocks are pushed (true branch and false branch)
  - `>choose` selects one block based on condition
  - `>^` executes the selected block
4. If `condition` is `True`:
  - The true branch executes
  - `body` runs
  - `>block` pushes the outer block back onto the AL
  - Block ends
  - `>chain` sees a block on top and repeats
5. If `condition` is `False`:
  - The false branch (empty `{}`) executes
  - Nothing is left on the AL
  - Block ends
  - `>chain` sees no block and terminates

**Complete example: Count to 5**

```soma
0 !counter

{
  counter 5 ><
  {
    counter >print
    counter 1 >+ !counter
    >block
  }
  { }
  >choose >^
} >chain
```

Output:

```
0
1
2
3
4
```

**CRITICAL: Why `>^` is needed:**

- `>choose` only **selects** which block to use (true branch or false branch)
- It doesn't **execute** the selected block
- `>^` pops the selected block from AL and executes it
- Without `>^`, the block would just sit on the AL and `>chain` would try to execute it, but the pattern wouldn't work correctly

**Note:** This example uses `counter` (Store path) rather than `_.counter` (Register path) because nested block executions have **isolated Registers**. The inner blocks cannot access the outer block's Register. The Store is globally accessible to all blocks.

This is a **while loop** built from `>choose` and `>chain`. No special syntax. No hidden control structures. Just blocks and state.

---

### 3.4 DO Loop (Body-First Loop)

**Traditional syntax:**

```
do {
  body
} while (condition);
```

**SOMA pattern:**

```soma
{
  body
  condition
  { >block }
  { }
  >choose >^
} >chain
```

**How it works:**

- The body executes **first**
- Then the condition is checked
- `>choose` selects `>block` (continue) or `{}` (stop)
- `>^` executes the selected block
- If true, `>block` causes the loop to continue
- If false, nothing is pushed and the loop terminates

**Example: Read until sentinel**

```soma
{
  user_input >read !input
  input "quit" >== >not
  { >block }
  { }
  >choose >^
} >chain
```

This reads input until the user types "quit". The body (read operation) always executes at least once.

**Note:** The `input` variable is stored in the Store (not `_.input`) so that nested block executions can access it.

---

### 3.5 Infinite Loop

**Traditional syntax:**

```
while (true) {
  body
}
```

**SOMA pattern:**

```soma
{ body >block } >chain
```

**How it works:**

- The block always pushes itself onto the AL via `>block`
- `>chain` always sees a block and continues forever

**Example: Server loop**

```soma
{
  connection >accept
  request >handle
  response >send
  >block
} >chain
```

This is the simplest possible infinite loop in SOMA. One block. One continuation. No condition needed.

---

### 3.6 Tail-Call Optimization with >chain

**Key insight:** `>chain` is perfect for tail-call optimization because it repeatedly executes blocks from the AL **without growing the call stack**. Each iteration is flat — the previous block's execution completes before the next begins.

#### Pattern: Accumulator-Based Recursion

Traditional recursion builds up a call stack. In SOMA, we use an **accumulator pattern** with `>chain` to achieve the same result with constant stack space.

**Example 1: Factorial with Accumulator**

```soma
5 !fact.n
1 !fact.acc

{
  fact.n 0 >=<
    fact.acc                    ) Base case: return accumulator
    {                           ) Recursive case: update and continue
      fact.n 1 >- !fact.n
      fact.acc fact.n 1 >+ >* !fact.acc
      fact-step                 ) Return self for tail-call
    }
  >choose
} !fact-step

fact-step >chain                ) AL: [120]
```

**How it works:**

1. Initialize `fact.n = 5`, `fact.acc = 1`
2. Block checks: is `n <= 0`?
3. If no (5 > 0): update `n = 4`, `acc = 1 * 5 = 5`, push `fact-step` block
4. `>choose` selects the recursive block (which contains `fact-step`)
5. Block execution completes, leaving `fact-step` on AL
6. `>chain` sees a block and executes it again
7. Repeat until `n <= 0`, then push `acc` (120) to AL
8. `>chain` sees a number (not a block) and stops

**Key differences from traditional recursion:**

- No call stack growth — `>chain` is a flat loop
- State stored in Store )`fact.n`, `fact.acc`), not in function parameters
- Each iteration completely replaces the previous one

**Example 2: Fibonacci with Tail-Call Optimization**

```soma
0 !fib.a
1 !fib.b
7 !fib.count

{
  fib.a >toString >print

  fib.count 1 >=<
    Nil                         ) Base: stop (chain terminates)
    {                           ) Recursive: compute next
      fib.count 1 >- !fib.count
      fib.a fib.b >+ !fib.next
      fib.b !fib.a
      fib.next !fib.b
      fib-step                  ) Return self for tail-call
    }
  >choose
} !fib-step

fib-step >chain
```

**Output:**

```
0
1
1
2
3
5
8
```

**How it works:**

1. Print current Fibonacci number (`fib.a`)
2. Check if count has reached 1
3. If no: compute next Fibonacci number, update state, push `fib-step`
4. `>choose` selects the block (which ends with `fib-step`)
5. Block completes, leaving `fib-step` on AL
6. `>chain` executes it again
7. When count reaches 1, `>choose` selects `Nil`
8. `>chain` sees non-block value and terminates

**Example 3: Countdown Pattern**

```soma
3 !count

{
  count >toString >print
  count 1 >- !count

  count 0 >=<
    { (Liftoff) >print }
    countdown
  >choose >^
} !countdown

countdown >chain
```

**Output:**

```
3
2
1
Liftoff
```

Note the 

`>^`

** usage:**

- When count reaches 0, `>choose` selects the liftoff block
- `>^` **executes** it (prints "Liftoff")
- Result is nothing on AL, so `>chain` stops
- When count > 0, `>choose` selects `countdown` (the block value)
- `>^` **executes** it, which runs the whole countdown block again
- The recursive call is a tail-call because it's the last thing executed

#### Tail-Call Pattern Summary

**General pattern:**

```soma
{
  ) Do work
  work_step

  ) Check condition
  done_condition
    final_result          ) Base case: value to return
    {                     ) Recursive case:
      ) Update state
      state_update
      self_block_name     ) Tail-call: return self
    }
  >choose
} !self_block_name

self_block_name >chain
```

**When to use:**

- Recursion that would normally build deep call stacks
- Loops with complex state transitions
- State machines (see next section)
- Any algorithm that can be expressed as "do work, then decide whether to continue"

**Benefits:**

- Constant stack space (no stack overflow)
- Clear state evolution (all state in Store)
- Natural expression of recursive algorithms
- Same performance as iterative loops

---

### 3.7 Internationalization: Aliasing >block

One of the key advantages of `>block` over the deprecated `_.self` magic binding is that **>block can be aliased**. This enables fully international code where programmers can use their native language for all built-ins.

**Example: German programmer**

```soma
) Alias built-ins to German
Chain !Kette
block !Block

) Infinite loop in pure German
{ "tick" >print >block } >Kette
```

**Example: Swedish programmer**

```soma
) Alias built-ins to Swedish
Chain !Kedja
block !blockera

) Infinite loop in pure Swedish
{ "tick" >print >blockera } >Kedja
```

**Why this matters:**

The old 

`_.self`

 approach was English-centric and couldn't be aliased:

```soma
) OLD WAY - forced to use English "self"
Chain !Kette
{ "tick" >print _.self } >Kette    ) Must use English word "self"
```

With `>block`, **every part of the control flow is aliasable**:

```soma
) NEW WAY - fully international
Chain !Kette
Choose !Wählen
block !Block
Equal !Gleich

) Pure German control flow
bedingung
  { "wahr" >print >block }
  { "falsch" >print }
>Wählen >^                       ) Note: >^ needed to execute selected block
```

This demonstrates that SOMA has **no English-centric special cases**. All built-ins, including block self-reference, can be renamed to match the programmer's language and coding style.

**Important:** Note the `>^` at the end — this is needed because `>Wählen` (choose) only **selects** a block, it doesn't execute it. The `>^` executes the selected block.

---

## 4. The Macro-Like Behavior

### 4.1 What Makes This "Macro-Like"?

In Lisp, you can define new control structures using `defmacro`:

```lisp
(defmacro while (condition &body body)
  `(loop
     (unless ,condition (return))
     ,@body))
```

After defining this macro, `while` looks exactly like a built-in language feature. Users can't tell the difference.

SOMA achieves the same effect **without macros**:

```soma
{ condition { body >block } { } >choose } !while
```

Now you can use `while` like this:

```soma
{ loop_counter 10 >< } { loop_body } while >chain
```

To the user, `while` behaves like a built-in control structure. But it's not. It's just a **stored block**.

**Note:** The condition and body blocks would access shared state via the Store (e.g., `loop_counter`), not via Register paths, due to Register isolation between blocks.

### 4.2 Why This Matters

**In traditional languages:**

- Control structures are **syntax**
- You cannot define new ones without macros or metaprogramming
- The boundary between "language" and "library" is rigid

**In SOMA:**

- Control structures are **values** (blocks)
- You can define new ones using only `>choose` and `>chain`
- The boundary between "language" and "library" disappears

This is **emergent abstraction**. SOMA doesn't provide `if` or `while` because it doesn't need to. They emerge naturally from the semantics.

### 4.3 Comparison to Lisp's defmacro

| Feature                 | Lisp defmacro               | SOMA Blocks            |
|-------------------------|-----------------------------|------------------------|
| Define new control flow | ✓                           | ✓                      |
| No runtime overhead     | ✓                           | ✓                      |
| First-class             | ✗ (macros are compile-time) | ✓ (blocks are values)  |
| Requires special syntax | ✓ (defmacro, backtick)      | ✗ (just blocks)        |
| Can pass as values      | ✗                           | ✓                      |
| Hygiene issues          | ✓ (gensym, etc.)            | ✗ (Register isolation) |

SOMA's approach is **simpler** and **more uniform**. There is no distinction between "code" and "data" because blocks are both.

**Note on hygiene:** SOMA avoids variable capture issues because each block execution has its own isolated Register. Nested blocks cannot accidentally access outer block Register paths, eliminating a whole class of hygiene problems.

---

## 5. Errata and Corrections Applied

### 5.1 CellRef vs Block Values

**Problem:** Original examples used `square.` - CellRef - with `>chain`

- **Why this fails:**`square.` is a **CellRef** - a reference to a cell
- `>chain` requires a **Block value**
- `>chain` would immediately terminate

**Correction:** All examples now use `square` - payload access - to retrieve the block value.

### 5.2 Equality Operator

**Problem:** Original spec was inconsistent ((`>=` vs `>==` vs `=?`)

**Correction:** This document uses `>==` consistently for equality, `><` for less-than, and `>>` for greater-than.

### 5.3 `>block` Built-in

This document now uses **>block** consistently throughout. The `>block` built-in pushes the currently executing block onto the AL. This enables self-referential loops and recursive block patterns.

Key properties of `>block`:

- It's a built-in operation - like `>choose`, `>chain`
- Can be aliased to any name - enabling internationalization
- Always returns the currently executing block
- Works at all nesting levels

All control flow patterns use `>block` rather than the deprecated `_.self` magic binding.

### 5.4 `>choose` Semantics — Critical Clarification

**CRITICAL CHANGE:** The semantics of `>choose` documented here differ from some earlier informal descriptions.

- **Current correct semantics:**`>choose` is a **SELECTOR** — it selects one value based on a boolean
- It does **NOT** execute blocks
- To execute the selected block, you must use `>^` - or store and execute separately

**Pattern:** `>choose >^` - select, then execute

1. **This was clarified based on:**Test files - `02_advanced_chain.soma`, `05_test_docs_stdlib.soma`
2. Standard library implementation - `>ifelse = { >choose >^ }`
3. Working SOMA code that consistently uses `>choose >^` for execution

- **Why this matters:**Separating selection from execution makes SOMA more compositional
- Blocks are truly first-class — you can select without executing
- The `>^` operator demonstrates that execution itself is user-defined
- This enables patterns like storing the selected block before executing it

**All examples in this document have been updated** to use the correct `>choose >^` pattern where execution is intended.

---

## Summary

SOMA's control flow is **emergent** rather than **prescribed**. By providing only `>choose` and `>chain`, SOMA creates a foundation on which all traditional control structures can be built as **user-defined patterns**.

**Key Semantic Principles:**

- **`>choose`**: SELECTOR — pops condition and two values, pushes the selected value. Does NOT execute blocks.
- **`>^`**: EXECUTOR — user-defined as { !_ >_ }, pops a block from AL and executes it.
- **`>chain`**: LOOPING — repeatedly executes blocks from AL until a non-block value appears. No stack growth.
- **`>{...}`**: DIRECT EXECUTION — executes an inline block immediately.

**The fundamental execution pattern:**

```soma
condition { true_branch } { false_branch } >choose >^
```

Control flow in SOMA is not hidden behind syntax. It is **explicit state transformation** guided by blocks and boolean values on the AL.

---

**Next:** [Higher-Order Patterns](./higher-order-patterns.md) — Dispatch tables, finite state machines, higher-order blocks, and building a control flow library.


