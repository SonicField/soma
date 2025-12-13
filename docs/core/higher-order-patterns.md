# Higher-Order Patterns: Advanced Control Flow

- **Status**: Normative
- **Version**: SOMA v1.0
- **Section**: 05b
- **Prerequisite**: Control Flow (05)

---

## Overview

This document covers advanced control flow patterns that build on the primitives introduced in **Control Flow**. You should understand `>choose`, `>chain`, `>{...}`, and `>^` before reading this.

Topics covered:

- Dispatch tables using dictionaries
- Higher-order blocks (blocks that operate on blocks)
- Finite state machines
- The macro-like behaviour of SOMA blocks
- Building a control flow library
- Comparisons to Forth, Lisp, and Lambda Calculus

---

## 1. Dispatch Tables Using Dictionaries

### 1.1 The Pattern

One of the most powerful patterns in SOMA is **dispatch tables** — storing operations and executing them dynamically. SOMA achieves this using **dictionaries** and **first-class blocks**.

**Basic example:**

```soma
) Build dispatch table: key, then value, then dict
(add) { (add called) >print } >dict.new >dict.put
(sub) { (sub called) >print } >dict.put
(mul) { (mul called) >print } >dict.put
!handlers

) Dispatch: key, then dict → value
(add) handlers >dict.get >^
```

**What happens:**

1. `(add) { ... } >dict.new >dict.put` creates a new dict with key `(add)` mapped to the block
2. Subsequent `>dict.put` calls add more key-block pairs (dict is immutable — each returns a new dict)
3. `!handlers` stores the final dict at Store path `handlers`
4. `(add) handlers >dict.get` retrieves the block mapped to `(add)`
5. `>^` executes the retrieved block

### 1.2 Dict Semantics

SOMA's **dict** provides:

- ****Immutable** — each `dict.put` returns a **new** dict; the original is unchanged**:  
- ****O(log n) lookup****:  — efficient even for large dispatch tables 
- ****First-class****:  — dicts can be passed, returned, and stored like any value 

**Argument order:**

- **`dict.put`: AL: [key, value, dict, ...] → [new_dict, ...]**:  
- **`dict.get`: AL: [key, dict, ...] → [value, ...]**:  

The dict is always on **top** of the AL. This enables chaining: each `>dict.put` leaves a new dict on top, ready for the next operation.

### 1.3 Complete Dispatch Example: Calculator

```soma
) Define operations as blocks
{ !_.b !_.a _.a _.b >+ } !op.add
{ !_.b !_.a _.a _.b >- } !op.sub
{ !_.b !_.a _.a _.b >* } !op.mul

) Build dispatch table
(add) op.add >dict.new >dict.put
(sub) op.sub >dict.put
(mul) op.mul >dict.put
!ops

) Dispatcher block
{
  !_.op !_.b !_.a           ) Store inputs
  _.op ops >dict.get        ) Look up operation by key
  _.a _.b                   ) Push arguments
  >^                        ) Execute!
} !dispatch

) Usage
10 5 (add) >dispatch        ) AL = [15]
10 5 (mul) >dispatch        ) AL = [50]
```

**This looks like a language feature** (dynamic dispatch), but it's just user-defined blocks using `dict` and `^`. No special language support required.

### 1.4 Why Dictionaries Over Store Paths?

An alternative approach might store handlers at Store paths (e.g., `handlers.add`, `handlers.sub`) and dynamically construct the path. Dictionaries are preferred because:

- ****Explicit data structure****:  — the dispatch table is a first-class value, not implicit in the Store namespace
- ****Portable****:  — can be passed between blocks, returned from functions, stored anywhere
- ****Immutable****:  — modifications create new dicts, preserving the original for safe concurrent use
- ****No namespace pollution****:  — keys don't become global Store paths

Combined with **blocks as first-class values**, dictionaries provide full dynamic dispatch without any special language features.

---

## 2. Higher-Order Blocks

### 2.1 Execute a Block Twice

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
3. The `twice` block executes:
  1. `!_.f` stores the print block in `twice`'s Register
  2. `>_.f` executes it (prints "Hello")
  3. `>_.f` executes it again (prints "Hello")
4. Each execution of the print block gets its own fresh Register

**Note:** The print block `{ (Hello) >print }` executes twice, and each execution has its own isolated Register (though this simple block doesn't use Register paths).

### 2.2 Execute If Condition Is True

```soma
{ !if_exec_block !if_exec_cond
  if_exec_cond { if_exec_block >^ } { } >choose >^
} !if_exec

True { (Condition met) >print } >if_exec     ) Prints: Condition met
False { (Won't print) >print } >if_exec      ) Prints nothing
```

**This is conditional execution of AL-passed blocks** — a higher-order control structure.

**How it works:**

1. Arguments on AL: `False`, `{ (Won't print) >print }`
2. `>if_exec` executes the `if_exec` block
3. Block stores condition in `if_exec_cond`, block in `if_exec_block`
4. Reads `if_exec_cond` (False), pushes two blocks
5. `>choose` selects empty block `{}`
6. `>^` executes the empty block (does nothing)

**Note on Register isolation and why we use Store:**

- Original attempt: `{ !_.block !_.cond _.cond { >_.block } {} >choose >^ }`
- This would fail because inner block `{ >_.block }` cannot access outer block's Register path `_.block`
- Corrected version stores in Store )`if_exec_block`, `if_exec_cond`), making them accessible to nested executions
- Uses `>^` to execute the block from the AL after it's pushed by the inner block

### 2.3 Execute With Argument

```soma
{ !_.arg !_.func _.arg >_.func } !call_with

42 { !_.x _.x _.x >* } >call_with    ) AL = [1764]  (42 squared)
```

**How it works:**

1. `42` pushed onto AL
2. `{ !_.x _.x _.x >* }` (squaring block) pushed onto AL
3. `>call_with` executes the `call_with` block:
  1. `!_.func` stores squaring block in `call_with`'s Register
  2. `!_.arg` stores `42` in `call_with`'s Register
  3. `_.arg` pushes `42` onto AL
  4. `>_.func` executes the squaring block with `42` on AL
4. The squaring block executes with its **own fresh Register**:
  1. `!_.x` stores `42` in the squaring block's Register (isolated from `call_with`'s Register)
  2. `_.x _.x >*` reads from its own Register and computes `42 * 42 = 1764`
  3. Leaves `1764` on AL
5. Result: `42 * 42 = 1764`

**Key point:** Each block execution )`call_with` and the squaring block) has its own isolated Register. They communicate via the AL, not via shared Register paths.

### 2.4 Map: Apply Block to Each Element

```soma
{
  !_.f !_.count             ) Store function and count in outer block's Register
  {
    _.count 0 >>            ) ERROR: Inner block can't see outer's _.count!
    {
      >_.f                  ) ERROR: Inner block can't see outer's _.f!
      _.count 1 >- !_.count ) ERROR: Inner block can't access outer's _.count!
      >block
    }
    { }
    >choose
  } >chain
} !map
```

**CRITICAL: Register Isolation Issue**

The above example **violates Register isolation** — the inner blocks try to access the outer block's Register paths `_.f` and `_.count`, which is **not allowed**.

**Corrected version using Store:**

```soma
{
  !map_f !map_count         ) Store in Store (global), not Register
  {
    map_count 0 >>          ) Read from Store
    {
      >map_f                ) Execute from Store
      map_count 1 >- !map_count  ) Update Store counter
      >block
    }
    { }
    >choose
  } >chain
} !map

) Usage: Increment three numbers
1 2 3                       ) Push three values
{ 10 >+ } 3 >map            ) Add 10 to each
```

**Result:** AL = `[11, 12, 13]`

**How it works with Register isolation:**

1. The outer `map` block stores `{ 10 >+ }` at Store path `map_f` (not `_.f`)
2. The outer block stores `3` at Store path `map_count` (not `_.count`)
3. The outer block then executes the inner loop block
4. **The inner loop block has its own fresh Register** (isolated from outer)
5. The inner blocks read from **Store** (`map_f`, `map_count`), which is globally accessible
6. Each iteration executes `>map_f` (pops value, adds 10, pushes result)
7. Decrements the Store counter until it reaches 0
8. The loop uses `>block` to reference itself for recursion

**Key insight:** Nested blocks must share data via **Store** (global state) or **AL** (explicit passing), not via Register paths.

---

## 3. These Look Like Language Features, But They're Not

### 3.1 The Illusion of Built-ins

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

- `!`
-  (store at path
- `>`
-  (execute from path
- `>choose`
-  (branching
- `>chain`
-  (looping

### 3.2 Why This Is Revolutionary

**Traditional approach:**Traditional approach:Language provides built-ins: `if`, `while`, `for`, `map`, `filter`, `reduce`

- These are **syntax** — you can't extend them
- Adding new control flow requires language changes

**SOMA approach:**SOMA approach:Language provides primitives: `>choose`, `>chain`, `!`, `>`

- Everything else is 
- **user-defined**
- Adding new control flow is just defining a new block

### 3.3 The Power of `>path` Semantics

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

- Function calls (
- `>my_func`
- )
- Dynamic dispatch (
- `>^`
- )
- Higher-order functions (
- `>map`
- , 
- `>twice`
- )
- Control structures (
- `>while`
- , 
- `>if_exec`
- )

---

## 4. Advanced Patterns

### 4.1 Finite State Machine

State machines are a natural fit for SOMA. Each state is a block that transitions to the next state.

**Example: Traffic light**

```soma
{ "RED" >print green } !red
{ "GREEN" >print yellow } !green
{ "YELLOW" >print red } !yellow

red >chain
```

Execution trace:

1. `red`
2.  block executes → prints "RED", pushes 
3. `green`
4.  (the green block)
5. `>chain`
6.  sees a block, executes it
7. `green`
8.  block executes → prints "GREEN", pushes 
9. `yellow`
10. `>chain`
11.  sees a block, executes it
12. `yellow`
13.  block executes → prints "YELLOW", pushes 
14. `red`
15. Loop continues forever

**Key insight:** Each state is a block. Transitions are explicit (push the next block). No hidden state machine interpreter needed.

---

### 4.2 Conditional State Machine

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
    >block
  }
  >choose >^
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
    >block
  }
  >choose >^
} !alarm_off

True !alarm.state
alarm_off >chain
```

This is a **conditional state machine**:

- `alarm_off`
-  state monitors for low readings
- When sensor drops below 50, 
- `>choose`
-  selects the block containing 
- `alarm_on`
- , 
- `>^`
-  executes it
- That block transitions to the 
- `alarm_on`
-  state
- `alarm_on`
-  state monitors for high readings
- When sensor exceeds 100, 
- `>choose`
-  selects the block containing 
- `alarm_off`
- , 
- `>^`
-  executes it
- That block transitions back to 
- `alarm_off`

**Key difference from simple state machine:**

- Uses 
- `>choose >^`
-  to conditionally select and execute the next state
- Can stay in same state (
- `>block`
-  keeps looping) or transition to different state

---

### 4.3 Nested Loops

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
0 !outer_i
{
  outer_i 3 ><
  {
    0 !inner_j
    {
      inner_j 3 ><
      {
        outer_i inner_j >print
        inner_j 1 >+ !inner_j
        >block
      }
      { }
      >choose >^
    } >chain

    outer_i 1 >+ !outer_i
    >block
  }
  { }
  >choose >^
} >chain
```

**CRITICAL: Register Isolation**

This example demonstrates a common pitfall. Note that:

- The outer loop counter 
- `outer_i`
-  is stored in the 
- **Store**
-  (no 
- `_.  `
-  prefix)
- The inner loop counter 
- `inner_j`
-  is stored in the 
- **Store**
-  (no 
- `_.`
-  prefix)

Why not use Register paths (`_.i`, `_.j`)?

Each nested block execution gets its **own independent Register**. If we tried:

```soma
0 !_.i           ) Outer block's Register
{
  _.i 3 ><       ) Read from outer block's Register
  {
    0 !_.j       ) Inner block's Register (DIFFERENT from outer!)
    {
      _.j 3 ><   ) Read from innermost block's Register
      {
        _.i _.j >print   ) ERROR: This inner block can't see outer's _.i!
```

The innermost block cannot access the outer block's `_.i` because **each block has its own isolated Register**.

**Solutions for nested loops:**

- ****Use Store****:  (shown above) — Store is global and accessible to all blocks
- ****Pass via AL****:  — Pass outer counter values explicitly through the AL
- ****Use CellRefs****:  — Share structure references between blocks

This demonstrates that **loops can be nested** without any special syntax, but **nested blocks must communicate via Store or AL**, not via Register paths.

---

## 5. Why Blocks Are The Macro Mechanism

### 5.1 Blocks Are First-Class

In SOMA, blocks can:

- Be stored in the Store (like variables)
- Be passed on the AL (like arguments)
- Be returned from other blocks (like return values)
- Refer to themselves (
- `>block`
-  built-in)
- Form recursive structures

This makes blocks **more powerful** than macros in most languages, because macros are typically compile-time only.

### 5.2 Blocks Are Composable

You can build complex control flow by **composing blocks**:

```soma
{ condition_a { body_a >block } { } >choose } !loop_a
{ condition_b { body_b >block } { } >choose } !loop_b

condition_top
  { loop_a >chain }
  { loop_b >chain }
>choose
```

This selects between two different loop behaviors based on `condition_top`. Try doing that with traditional `while` statements!

**Note:** The loop definitions reference `condition_a`, `body_a`, `condition_b`, and `body_b` which would be Store paths (not Register paths), making them accessible to the nested loop blocks. Each loop's body block uses `>block` to refer to its own enclosing loop block.

### 5.3 No Hidden Machinery

Traditional macro systems require:

- A separate macro expansion phase
- Hygiene rules to prevent variable capture
- Special syntax for quoting and unquoting
- Distinction between "macro time" and "runtime"

SOMA has none of this. Blocks are just values. `>choose` and `>chain` are just operations on values. The emergent behavior is a **consequence of the semantics**, not a special feature.

---

## 6. Building a Control Flow Library

Let's build a small library of reusable control structures:

### 6.1 Define Common Patterns

```soma
{ >swap { } >choose >^ } !if
[IF - single branch]

```

```soma
{ !while_body !while_cond
  {
    while_cond                ) Read condition from Store
    { while_body >block }     ) Read body from Store, continue loop
    { }
    >choose >^                ) Select and execute
  }
} !while
[WHILE - loop with precondition]

```

```soma
{ !do_body !do_cond
  {
    do_body                   ) Execute body from Store
    do_cond                   ) Read condition from Store
    { >block }
    { }
    >choose >^                ) Select and execute
  }
} !do
[DO - loop with postcondition]

```

```soma
{ !repeat_body !repeat_count
  {
    repeat_count 0 >>         ) Read count from Store
    {
      repeat_body             ) Execute body from Store
      repeat_count 1 >- !repeat_count  ) Update Store counter
      >block
    }
    { }
    >choose >^                ) Select and execute
  }
} !repeat
[REPEAT - fixed count loop]

```

**Note on Register isolation:**Note on Register isolation:These control structure definitions store their parameters in the **Store** (e.g., `while_cond`, `while_body`) rather than in Register paths (`_. cond`, `_.body`). This is necessary because:

- The outer block that defines the control structure has its own Register
- The inner loop blocks have 
- **separate, isolated Registers**
- Inner blocks cannot access the outer block's Register
- Store paths are globally accessible to all blocks

**Note on `>choose >^` pattern:**All these control structures use the pattern `>choose >^`:

- `>choose`
-  
- **selects**
-  which block to use (continue or stop)
- `>^`
-  
- **executes**
-  the selected block
- This is the fundamental execution pattern in SOMA control flow

### 6.2 Use The Library

**Using `if`:**

```soma
x 0 >>
  { "positive" >print }
if >^
```

**Note:** The `if` helper swaps the arguments so the condition comes first, then adds an empty block, calls `>choose >^`. You still need to call it with `>^` (or use `>chain`).

**Using `while`:**

```soma
{ outer_counter 10 >< }      ) condition block (reads from Store)
{ outer_counter >print outer_counter 1 >+ !outer_counter }  ) body block (uses Store)
while >^
```

**Using `repeat`:**

```soma
{ "hello" >print }  ) body
5  ) count
repeat >^
```

Output:

```
hello
hello
hello
hello
hello
```

**Note:** All these library functions return blocks, so you need to either:

1. Execute with 
2. `>^`
3.  (as shown above)
4. Use with 
5. `>chain`
6.  (e.g., 
7. `while >chain`
8. )

---

## 7. Key Insights

### 7.1 Control Flow Is Data

In SOMA, control flow decisions are made by **values on the AL**:

- Booleans determine which branch to take
- Blocks determine what to execute next
- The AL holds the "program counter" implicitly

This is fundamentally different from syntax-driven control flow.

### 7.2 No Special Forms Needed

SOMA does not need:

- `if` / `else` keywords
- `while` / `for` / `do` keywords
- `break` / `continue` statements
- `switch` / `case` statements

All of these can be **user-defined** using `>choose` and `>chain`.

### 7.3 The Emergent Macro Property

The macro-like behavior emerges from three properties:

1. **Blocks are first-class**: can be stored and named

1. **`>choose`**:  selects blocksbranching without syntax
2. **`>chain`**:  executes blockslooping without syntax

Together, these create a **compositional control flow algebra** where complex patterns emerge from simple primitives.

### 7.4 The `^` Operator Is The Key Example

The fact that you can define **execute-AL-top** as a user function:

```soma
{ !_ >_ } !^
```

This proves that SOMA has **true macro power** — the ability to define operations that behave exactly like language primitives, but are actually user code.

---

## 8. Comparison to Other Approaches

### 8.1 Forth

Forth has similar primitives `(IF`, `THEN`, `BEGIN`, `UNTIL`, but they are:

- **Immediate words** - compile-time syntax
- Not first-class values
- Tied to the return stack

Forth also has `EXECUTE`, but it's a **built-in primitive**.

SOMA's blocks are **runtime values**, not syntax. And SOMA's `^` is **user-defined**, not a primitive.

### 8.2 Lisp

Lisp's macros are powerful but:

- Operate at **compile-time**
- Require a separate expansion phase
- Cannot be passed as first-class values at runtime

Lisp has `funcall` and `apply`, but they're **built-in primitives**.

SOMA's blocks are **always first-class** and available at runtime. And SOMA's `^` is **user-defined** using only `!^` and `>`.

### 8.3 Lambda Calculus

Lambda calculus encodes control flow using:

- Church encodings
- Combinators - Y combinator for recursion

But these are **encodings**, not native operations. SOMA's `>choose` and `>chain` are **direct semantic primitives**.

And unlike Lambda Calculus, SOMA makes **execution explicit** with the `>` prefix, making computation observable.

---

## 9. Practical Considerations

### 9.1 When To Use `>choose` vs `>chain`

- **Use `>choose` when:**You need to select between exactly two alternatives
- The decision is based on a boolean
- Both branches should be fully defined - even if one is empty

- **Use `>chain` when:**You need to execute a sequence of blocks
- The sequence length is determined at runtime
- You want loops or state machines

- **Use both when:**Building complex control flow - while loops, finite state machines, etc.

### 9.2 Performance Implications

- **`>choose`**: : **No overhead** beyond evaluating the condition and selecting a branch
- **`>chain`**: : **No call stack growth** — each iteration is flat
- **Self-referential blocks: **: **No recursion** — just iteration

SOMA's control flow is **as efficient as native control structures** in traditional languages.

### 9.3 Debugging

To debug SOMA control flow:

- Inspect the AL before `>choose` to see the condition and blocks
- Insert `>dump` inside blocks to trace execution
- Use `>print` to mark state transitions

Because everything is explicit, debugging is often **easier** than in languages with hidden control stacks.

---

## Summary

This document covered advanced patterns that emerge from SOMA's control flow primitives:

- ****Dispatch tables****:  — dynamic function lookup using dictionaries
- ****Higher-order blocks****:  — blocks that accept and execute other blocks
- ****Finite state machines****:  — states as blocks, transitions as block pushes
- ****Macro-like behaviour****:  — user-defined control structures indistinguishable from built-ins
- ****Control flow library****:  — reusable patterns built from primitives

The key insight is that SOMA's power comes from **uniformity**: blocks are values, execution is explicit, and the primitives compose cleanly. There is no hidden machinery.

---

**Previous:** [Control Flow](./control-flow.md) — The core primitives and basic patterns.


