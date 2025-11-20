# Control Flow: The Emergent Macro System

**Status:** Normative
**Version:** SOMA v1.0
**Section:** 05

---

## Overview

SOMA takes a radical approach to control flow. Unlike traditional languages that provide built-in keywords like `if`, `while`, `for`, or `switch`, SOMA defines **only two control primitives**:

- **`>Choose`** — Select between two blocks based on a boolean
- **`>Chain`** — Execute blocks until no block remains on the AL

From these two primitives, something remarkable emerges: control structures that look and behave exactly like built-in language features, but are actually **user-defined patterns**. This is SOMA's emergent macro system — a mechanism similar to Lisp's `defmacro`, but arising naturally from the language's semantics without requiring a separate macro facility.

This section demonstrates how `if`, `ifelse`, `while`, `do`, and finite state machines all emerge from `>Choose` and `>Chain`. Understanding this mechanism is key to grasping SOMA's power as a language that reveals rather than obscures computation.

---

## 1. The Two Primitives

### 1.1 `>Choose` — Conditional Selection

`>Choose` is SOMA's only branching primitive. It selects between two blocks based on a boolean value.

**AL Contract (pre-execution):**
```
Top → C (false branch block)
      B (true branch block)
      A (boolean condition)
```

**Program syntax:**
```soma
A B C >Choose
```

**Semantics:**
1. Pop three values from the AL: `C`, `B`, `A` (in that order)
2. `A` must be a Boolean, or fatal error
3. If `A == True`: execute block `B`
4. If `A == False`: execute block `C`
5. After execution, the AL contains only the results of the chosen block
6. The unchosen block is discarded

**Example:**
```soma
True
  { "Path taken" >print }
  { "Path not taken" >print }
>Choose
```

Output: `Path taken`

The false branch block is never executed and leaves no trace. This is **eager evaluation with dead code elimination** — only the selected branch runs.

---

### 1.2 `>Chain` — Block Continuation Loop

`>Chain` is SOMA's only looping primitive. It repeatedly executes blocks until the AL top is no longer a block.

**Semantics:**
1. Pop the top value from the AL
2. If it is **not** a Block: push it back and stop (`>Chain` terminates)
3. If it **is** a Block: execute it
4. After execution, examine the new AL top
5. If the new top is a Block, repeat from step 3
6. Otherwise, stop

**Key insight:** `>Chain` does not recurse and does not grow a call stack. It is a **flat iteration** over a sequence of blocks left on the AL by each previous block.

**Example 1: Single block execution**
```soma
{ 5 5 >* } >Chain
```
Result: AL contains `[25]`. The block executes once, leaves `25` on the AL, and `>Chain` terminates because `25` is not a block.

**Example 2: Self-perpetuating block**
```soma
{ "tick" >print _.self } >Chain
```

This prints `tick` forever. Why?
- The block executes, prints `tick`, then pushes `_.self` (a reference to itself) onto the AL
- `>Chain` sees a block on top and executes it again
- This repeats infinitely

**IMPORTANT ERRATA CORRECTION:**

The original specification contained examples that incorrectly used **CellRefs** (trailing-dot paths) with `>Chain`. For example:

```soma
7 square. >Chain >print  ; WRONG!
```

Under SOMA semantics:
- `square.` resolves to a **CellRef** (not the block itself)
- `>Chain` sees a non-Block value and immediately terminates
- This is a silent logic error

**Correct form:**
```soma
7 square >Chain >print  ; CORRECT
```

This retrieves the **block value** stored at `square`, not a reference to the cell. All examples in this document use the corrected form.

---

## 2. The `^` Operator: User-Defined Execution

**This is the KEY to understanding SOMA's macro-like behavior.**

### 2.1 The Problem: Executing AL Top

In languages like Forth and Lisp, there are built-in primitives for executing a value on the stack:

- **Forth:** `EXECUTE` — pops the execution token and runs it
- **Lisp:** `(funcall fn args)` — calls the function object

These are **language primitives** — you can't implement them yourself.

SOMA has **no built-in execute-from-AL operation**. But you can define it:

```soma
{ !_ >_ } !^        ) Create "execute top of AL" operator
```

Now `>^` behaves exactly like Forth's `EXECUTE`:

```soma
(Cats) print >^     ) Prints 'Cats'
```

### 2.2 How `^` Works: Step-by-Step Execution Trace

Let's trace the execution of `(Cats) print >^` in detail:

**Initial state:**
```
AL: []
```

**Step 1: `(Cats)` — Push string onto AL**
```
AL: ["Cats"]
```

**Step 2: `print` — Push print block onto AL**
```
AL: ["Cats", print_block]
```
Note: `print` without `>` pushes the **block value** at Store path "print" onto the AL.

**Step 3: `>^` — Execute the block stored at Store path "^"**

The block stored at `^` is: `{ !_ >_ }`

When this block executes:

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

**Final state:**
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

| Language | Execute Operator | Implementation |
|----------|------------------|----------------|
| **Forth** | `EXECUTE` | Built-in primitive |
| **Lisp** | `funcall`, `apply` | Built-in primitive |
| **SOMA** | `{ !_ >_ } !^` | **User-defined!** |

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

The power of `>Choose` and `>Chain` lies not in what they do individually, but in **what emerges when you combine them**. Let's build traditional control structures from scratch.

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
>Choose
```

**How it works:**
- If `condition` is `True`, the body block executes
- If `condition` is `False`, the empty block `{}` executes (does nothing)
- This is **if without else**

**Example:**
```soma
x 10 >>
  { "x is greater than 10" >print }
  { }
>Choose
```

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

**SOMA pattern:**
```soma
condition
  { true_body }
  { false_body }
>Choose
```

**How it works:**
- This is the **natural form** of `>Choose`
- One branch always executes
- No special syntax needed — it's just `>Choose`

**Example:**
```soma
user.authenticated
  { dashboard_page >render }
  { login_page >render }
>Choose
```

---

### 3.3 WHILE Loop

**Traditional syntax:**
```
while (condition) {
  body
}
```

**SOMA pattern:**
```soma
{
  condition
  {
    body
    _.self
  }
  { }
  >Choose
} >Chain
```

**How it works:**

Let's trace execution step by step:

1. The outer block is pushed onto the AL
2. `>Chain` pops and executes it
3. Inside the block:
   - `condition` is evaluated (pushes a boolean)
   - Two blocks are pushed (true branch and false branch)
   - `>Choose` executes
4. If `condition` is `True`:
   - The true branch executes
   - `body` runs
   - `_.self` pushes the outer block back onto the AL
   - Block ends
   - `>Chain` sees a block on top and repeats
5. If `condition` is `False`:
   - The false branch (empty `{}`) executes
   - Nothing is left on the AL
   - Block ends
   - `>Chain` sees no block and terminates

**Complete example: Count to 5**
```soma
0 !_.counter

{
  _.counter 5 ><
  {
    _.counter >print
    _.counter 1 >+ !_.counter
    _.self
  }
  { }
  >Choose
} >Chain
```

Output:
```
0
1
2
3
4
```

This is a **while loop** built from `>Choose` and `>Chain`. No special syntax. No hidden control structures. Just blocks and state.

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
  { _.self }
  { }
  >Choose
} >Chain
```

**How it works:**
- The body executes **first**
- Then the condition is checked
- If true, `_.self` causes the loop to continue
- If false, nothing is pushed and the loop terminates

**Example: Read until sentinel**
```soma
{
  user_input >read !_.input
  _.input "quit" >== >not
  { _.self }
  { }
  >Choose
} >Chain
```

This reads input until the user types "quit". The body (read operation) always executes at least once.

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
{ body _.self } >Chain
```

**How it works:**
- The block always pushes itself onto the AL via `_.self`
- `>Chain` always sees a block and continues forever

**Example: Server loop**
```soma
{
  connection >accept
  request >handle
  response >send
  _.self
} >Chain
```

This is the simplest possible infinite loop in SOMA. One block. One continuation. No condition needed.

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
{ condition { body _.self } { } >Choose } !while
```

Now you can use `while` like this:

```soma
_.counter 10 >< while >Chain
```

To the user, `while` behaves like a built-in control structure. But it's not. It's just a **stored block**.

### 4.2 Why This Matters

**In traditional languages:**
- Control structures are **syntax**
- You cannot define new ones without macros or metaprogramming
- The boundary between "language" and "library" is rigid

**In SOMA:**
- Control structures are **values** (blocks)
- You can define new ones using only `>Choose` and `>Chain`
- The boundary between "language" and "library" disappears

This is **emergent abstraction**. SOMA doesn't provide `if` or `while` because it doesn't need to. They emerge naturally from the semantics.

### 4.3 Comparison to Lisp's `defmacro`

| Feature | Lisp `defmacro` | SOMA Blocks |
|---------|----------------|-------------|
| Define new control flow | ✓ | ✓ |
| No runtime overhead | ✓ | ✓ |
| First-class | ✗ (macros are compile-time) | ✓ (blocks are values) |
| Requires special syntax | ✓ (`defmacro`, backtick) | ✗ (just blocks) |
| Can pass as values | ✗ | ✓ |
| Hygiene issues | ✓ (gensym, etc.) | ✗ (lexical scope) |

SOMA's approach is **simpler** and **more uniform**. There is no distinction between "code" and "data" because blocks are both.

---

## 5. Dispatch Tables Using `>path`

### 5.1 The Pattern

One of the most powerful patterns in SOMA is **dispatch tables** — storing operations at paths and executing them dynamically.

**Basic example:**
```soma
{ (add) >print } !handlers.add
{ (sub) >print } !handlers.sub
{ (mul) >print } !handlers.mul

) Dispatch based on operation name
(add) !_.op
(handlers.) _.op >concat >Store.get >^
```

**What happens:**
1. `(add)` stored in `_.op`
2. `(handlers.)` and `_.op` concatenated → `(handlers.add)`
3. `>Store.get` retrieves the block at that path
4. `>^` executes it
5. Output: `add`

### 5.2 More Elegant Dispatch

A cleaner approach uses direct execution:

```soma
{ (Addition) >print } !commands.add
{ (Subtraction) >print } !commands.sub

) Execute command directly
>commands.add           ) Prints: Addition
```

But for **dynamic dispatch**, you need to compute the path:

```soma
) Build path from user input
user_input !_.cmd
(commands.) _.cmd >concat !_.path

) Execute dynamically
_.path >Store.get >^
```

### 5.3 Complete Dispatch Example: Calculator

```soma
) Define operations
{ !_.b !_.a _.a _.b >+ } !ops.add
{ !_.b !_.a _.a _.b >- } !ops.sub
{ !_.b !_.a _.a _.b >* } !ops.mul

) Dispatcher block
{
  !_.op !_.b !_.a           ) Store inputs
  (ops.) _.op >concat       ) Build path: "ops.add"
  >Store.get                ) Get the block
  _.a _.b                   ) Push arguments
  >^                        ) Execute!
} !dispatch

) Usage
10 5 (add) >dispatch        ) AL = [15]
10 5 (mul) >dispatch        ) AL = [50]
```

**This looks like a language feature** (dynamic dispatch), but it's just user-defined blocks using `>path` and `^`.

---

## 6. Higher-Order Blocks

### 6.1 Execute a Block Twice

```soma
{ !_.f >_.f >_.f } !twice
{ (Hello) >print } >twice
```

**Output:**
```
Hello
Hello
```

**How it works:**
1. `{ (Hello) >print }` pushed onto AL
2. `>twice` executes the `twice` block
3. Block executes:
   - `!_.f` stores the block in Register
   - `>_.f` executes it (prints "Hello")
   - `>_.f` executes it again (prints "Hello")

### 6.2 Execute If Condition Is True

```soma
{ !_.block !_.cond _.cond { >_.block } { } >Choose >Chain } !if_exec

True { (Condition met) >print } >if_exec     ) Prints: Condition met
False { (Won't print) >print } >if_exec      ) Prints nothing
```

**This is conditional execution of AL-passed blocks** — a higher-order control structure.

### 6.3 Execute With Argument

```soma
{ !_.arg !_.func _.arg >_.func } !call_with

42 { !_.x _.x _.x >* } >call_with    ) AL = [1764]  (42 squared)
```

**How it works:**
1. `42` pushed onto AL
2. `{ !_.x _.x _.x >* }` (squaring block) pushed onto AL
3. `>call_with` executes the `call_with` block:
   - `!_.func` stores squaring block in Register
   - `!_.arg` stores `42` in Register
   - `_.arg` pushes `42` onto AL
   - `>_.func` executes the squaring block with `42` on AL
   - Result: `42 * 42 = 1764`

### 6.4 Map: Apply Block to Each Element

```soma
{
  !_.f !_.count             ) Store function and count
  {
    _.count 0 >>            ) While count > 0
    {
      >_.f                  ) Execute function on AL top
      _.count 1 >- !_.count ) Decrement
      _.self
    }
    { }
    >Choose
  } >Chain
} !map

) Usage: Increment three numbers
1 2 3                       ) Push three values
{ 10 >+ } 3 >map           ) Add 10 to each
```

**Result:** AL = `[11, 12, 13]`

**This is higher-order programming** — passing blocks as values and executing them dynamically.

---

## 7. These Look Like Language Features, But They're Not

### 7.1 The Illusion of Built-ins

All of these **look** like built-in language features:

```soma
>^                          ) Execute AL top
>twice                      ) Execute block twice
>if_exec                    ) Conditional execution
>call_with                  ) Apply function to argument
>map                        ) Map over collection
>dispatch                   ) Dynamic dispatch
```

But **none of them are primitives**. They're all user-defined using:
- `!` (store at path)
- `>` (execute from path)
- `>Choose` (branching)
- `>Chain` (looping)

### 7.2 Why This Is Revolutionary

**Traditional approach:**
- Language provides built-ins: `if`, `while`, `for`, `map`, `filter`, `reduce`
- These are **syntax** — you can't extend them
- Adding new control flow requires language changes

**SOMA approach:**
- Language provides primitives: `>Choose`, `>Chain`, `!`, `>`
- Everything else is **user-defined**
- Adding new control flow is just defining a new block

### 7.3 The Power of `>path` Semantics

The `>` prefix is the key to all of this:

```soma
print           ) Pushes the print block onto AL (it's a value)
>print          ) Executes the print block (it's an operation)
```

**Blocks are values** until you explicitly execute them with `>`:

```soma
{ 1 2 >+ }      ) This is a value (a block)
>{ 1 2 >+ }     ) This executes: AL becomes [3]
```

**This makes execution first-class:**

```soma
my_block !_.action          ) Store block in variable
>_.action                   ) Execute it later
```

And from this, **everything emerges**:
- Function calls (`>my_func`)
- Dynamic dispatch (`>^`)
- Higher-order functions (`>map`, `>twice`)
- Control structures (`>while`, `>if_exec`)

---

## 8. Advanced Patterns

### 8.1 Finite State Machine

State machines are a natural fit for SOMA. Each state is a block that transitions to the next state.

**Example: Traffic light**
```soma
{ "RED" >print green } !red
{ "GREEN" >print yellow } !green
{ "YELLOW" >print red } !yellow

red >Chain
```

Execution trace:
1. `red` block executes → prints "RED", pushes `green` (the green block)
2. `>Chain` sees a block, executes it
3. `green` block executes → prints "GREEN", pushes `yellow`
4. `>Chain` sees a block, executes it
5. `yellow` block executes → prints "YELLOW", pushes `red`
6. Loop continues forever

**Key insight:** Each state is a block. Transitions are explicit (push the next block). No hidden state machine interpreter needed.

---

### 8.2 Conditional State Machine

**Example: Two-state toggle with condition**
```soma
{
  sensor.reading 100 >>
  {
    "ALARM ON" >print
    False !alarm.state
    alarm_off
  }
  {
    "Normal" >print
    _.self
  }
  >Choose
} !alarm_on

{
  sensor.reading 50 ><
  {
    "ALARM OFF" >print
    True !alarm.state
    alarm_on
  }
  {
    "Normal" >print
    _.self
  }
  >Choose
} !alarm_off

True !alarm.state
alarm_off >Chain
```

This is a **conditional state machine**:
- `alarm_off` state monitors for low readings
- When sensor drops below 50, transition to `alarm_on`
- `alarm_on` state monitors for high readings
- When sensor exceeds 100, transition back to `alarm_off`

---

### 8.3 Nested Loops

**Traditional syntax:**
```
for i in 0..3 {
  for j in 0..3 {
    print(i, j)
  }
}
```

**SOMA pattern:**
```soma
0 !_.i
{
  _.i 3 ><
  {
    0 !_.j
    {
      _.j 3 ><
      {
        _.i _.j >print
        _.j 1 >+ !_.j
        _.self
      }
      { }
      >Choose
    } >Chain

    _.i 1 >+ !_.i
    _.self
  }
  { }
  >Choose
} >Chain
```

This demonstrates that **loops can be nested** without any special syntax. Each loop is just a block with `>Chain`.

---

## 9. Why Blocks Are The Macro Mechanism

### 9.1 Blocks Are First-Class

In SOMA, blocks can:
- Be stored in the Store (like variables)
- Be passed on the AL (like arguments)
- Be returned from other blocks (like return values)
- Refer to themselves (`_.self`)
- Form recursive structures

This makes blocks **more powerful** than macros in most languages, because macros are typically compile-time only.

### 9.2 Blocks Are Composable

You can build complex control flow by **composing blocks**:

```soma
{ condition_a { body_a _.self } { } >Choose } !loop_a
{ condition_b { body_b _.self } { } >Choose } !loop_b

condition_top
  { loop_a >Chain }
  { loop_b >Chain }
>Choose
```

This selects between two different loop behaviors based on `condition_top`. Try doing that with traditional `while` statements!

### 9.3 No Hidden Machinery

Traditional macro systems require:
- A separate macro expansion phase
- Hygiene rules to prevent variable capture
- Special syntax for quoting and unquoting
- Distinction between "macro time" and "runtime"

SOMA has none of this. Blocks are just values. `>Choose` and `>Chain` are just operations on values. The emergent behavior is a **consequence of the semantics**, not a special feature.

---

## 10. Examples: Building a Control Flow Library

Let's build a small library of reusable control structures:

### 10.1 Define Common Patterns

```soma
[IF - single branch]
{ >swap { } >Choose } !if

[WHILE - loop with precondition]
{ !_.body !_.cond
  {
    _.cond
    { _.body _.self }
    { }
    >Choose
  }
} !while

[DO - loop with postcondition]
{ !_.body !_.cond
  {
    _.body
    _.cond
    { _.self }
    { }
    >Choose
  }
} !do

[REPEAT - fixed count loop]
{ !_.body !_.count
  {
    _.count 0 >>
    {
      _.body
      _.count 1 >- !_.count
      _.self
    }
    { }
    >Choose
  }
} !repeat
```

### 10.2 Use The Library

**Using `if`:**
```soma
x 0 >>
  { "positive" >print }
if >Chain
```

**Using `while`:**
```soma
_.counter 10 ><  ; condition block
{ _.counter >print _.counter 1 >+ !_.counter }  ; body block
while >Chain
```

**Using `repeat`:**
```soma
{ "hello" >print }  ; body
5  ; count
repeat >Chain
```

Output:
```
hello
hello
hello
hello
hello
```

---

## 11. Key Insights

### 11.1 Control Flow Is Data

In SOMA, control flow decisions are made by **values on the AL**:
- Booleans determine which branch to take
- Blocks determine what to execute next
- The AL holds the "program counter" implicitly

This is fundamentally different from syntax-driven control flow.

### 11.2 No Special Forms Needed

SOMA does not need:
- `if` / `else` keywords
- `while` / `for` / `do` keywords
- `break` / `continue` statements
- `switch` / `case` statements

All of these can be **user-defined** using `>Choose` and `>Chain`.

### 11.3 The Emergent Macro Property

The macro-like behavior emerges from three properties:

1. **Blocks are first-class** → can be stored and named
2. **`>Choose` selects blocks** → branching without syntax
3. **`>Chain` executes blocks** → looping without syntax

Together, these create a **compositional control flow algebra** where complex patterns emerge from simple primitives.

### 11.4 The `^` Operator Is The Key Example

The fact that you can define **execute-AL-top** as a user function:

```soma
{ !_ >_ } !^
```

This proves that SOMA has **true macro power** — the ability to define operations that behave exactly like language primitives, but are actually user code.

---

## 12. Comparison to Other Approaches

### 12.1 Forth

Forth has similar primitives (`IF`, `THEN`, `BEGIN`, `UNTIL`), but they are:
- **Immediate words** (compile-time syntax)
- Not first-class values
- Tied to the return stack

Forth also has `EXECUTE`, but it's a **built-in primitive**.

SOMA's blocks are **runtime values**, not syntax. And SOMA's `^` is **user-defined**, not a primitive.

### 12.2 Lisp

Lisp's macros are powerful but:
- Operate at **compile-time**
- Require a separate expansion phase
- Cannot be passed as first-class values at runtime

Lisp has `funcall` and `apply`, but they're **built-in primitives**.

SOMA's blocks are **always first-class** and available at runtime. And SOMA's `^` is **user-defined** using only `!` and `>`.

### 12.3 Lambda Calculus

Lambda calculus encodes control flow using:
- Church encodings
- Combinators (Y combinator for recursion)

But these are **encodings**, not native operations. SOMA's `>Choose` and `>Chain` are **direct semantic primitives**.

And unlike Lambda Calculus, SOMA makes **execution explicit** with the `>` prefix, making computation observable.

---

## 13. Practical Considerations

### 13.1 When To Use `>Choose` vs `>Chain`

**Use `>Choose` when:**
- You need to select between exactly two alternatives
- The decision is based on a boolean
- Both branches should be fully defined (even if one is empty)

**Use `>Chain` when:**
- You need to execute a sequence of blocks
- The sequence length is determined at runtime
- You want loops or state machines

**Use both when:**
- Building complex control flow (while loops, FSMs, etc.)

### 13.2 Performance Implications

- `>Choose`: **No overhead** beyond evaluating the condition and selecting a branch
- `>Chain`: **No call stack growth** — each iteration is flat
- Self-referential blocks: **No recursion** — just iteration

SOMA's control flow is **as efficient as native control structures** in traditional languages.

### 13.3 Debugging

To debug SOMA control flow:
- Inspect the AL before `>Choose` to see the condition and blocks
- Insert `>dump` inside blocks to trace execution
- Use `>print` to mark state transitions in FSMs

Because everything is explicit, debugging is often **easier** than in languages with hidden control stacks.

---

## 14. Errata and Corrections Applied

### 14.1 CellRef vs Block Values

**Problem:** Original examples used `square.` (CellRef) with `>Chain`

**Why this fails:**
- `square.` is a **CellRef** (a reference to a cell)
- `>Chain` requires a **Block value**
- `>Chain` would immediately terminate

**Correction:** All examples now use `square` (payload access) to retrieve the block value.

### 14.2 Equality Operator

**Problem:** Original spec was inconsistent (`>=` vs `>==` vs `=?`)

**Correction:** This document uses `>==` consistently for equality, `><` for less-than, and `>>` for greater-than.

### 14.3 `_.self` Semantics

This document now uses **`_.self`** consistently throughout. When a block executes, the SOMA runtime automatically creates a Register Cell at path `_.self` containing the Block value being executed. This enables self-referential loops without explicit CellRef management.

All register paths use the `_.path` syntax where `_` is the register root.

---

## Summary

SOMA's control flow is **emergent** rather than **prescribed**. By providing only `>Choose` and `>Chain`, SOMA creates a foundation on which all traditional control structures can be built as **user-defined patterns**.

These patterns are not "library functions" in the traditional sense. They are **blocks** — first-class values that behave exactly like built-in language features.

This is SOMA's **emergent macro system**: the ability to define new control structures that are indistinguishable from built-ins, without requiring a separate macro facility.

**The `^` operator is the showcase example:**

```soma
{ !_ >_ } !^        ) Execute AL top - like Forth's EXECUTE
(Cats) print >^     ) Prints 'Cats'
```

This proves that execution itself is not a primitive in SOMA — it's user-defined using `!` and `>`.

From this foundation emerge:
- Function calls
- Dynamic dispatch
- Higher-order functions
- Control structures
- State machines
- Everything that looks like a "language feature"

The key insight is that **blocks are the macro mechanism**. In languages with macros, you manipulate syntax to create new forms. In SOMA, you manipulate blocks. The result is the same, but the mechanism is simpler, more uniform, and available at runtime.

Control flow in SOMA is not hidden behind syntax. It is **explicit state transformation** guided by blocks and boolean values on the AL. This makes SOMA programs **observable, inspectable, and introspectable** in ways that traditional languages cannot match.

---

**Next Section:** [06-blocks-and-state.md](./06-blocks-and-state.md) — Deep dive into block semantics, the Store, and state management patterns.
