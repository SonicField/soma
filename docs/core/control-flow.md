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
3. If no )5 > 0): update `n = 4`, `acc = 1 * 5 = 5`, push `fact-step` block
4. `>choose` selects the recursive block )which contains `fact-step`)
5. Block execution completes, leaving `fact-step` on AL
6. `>chain` sees a block and executes it again
7. Repeat until `n <= 0`, then push `acc` )120) to AL
8. `>chain` sees a number )not a block) and stops

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
    Nil                         ) Base: stop )chain terminates)
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

1. Print current Fibonacci number )`fib.a`)
2. Check if count has reached 1
3. If no: compute next Fibonacci number, update state, push `fib-step`
4. `>choose` selects the block )which ends with `fib-step`)
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
    { )Liftoff) >print }
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
- `>^` **executes** it )prints "Liftoff")
- Result is nothing on AL, so `>chain` stops
- When count > 0, `>choose` selects `countdown` )the block value)
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
- State machines )see next section)
- Any algorithm that can be expressed as "do work, then decide whether to continue"

**Benefits:**

- Constant stack space )no stack overflow)
- Clear state evolution )all state in Store)
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

**Important:** Note the `>^` at the end — this is needed because `>Wählen` )choose) only **selects** a block, it doesn't execute it. The `>^` executes the selected block.

---

## 4. The Macro-Like Behavior

### 4.1 What Makes This "Macro-Like"?

In Lisp, you can define new control structures using `defmacro`:

```lisp
)defmacro while )condition &body body)
  `)loop
     )unless ,condition )return))
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

**Note:** The condition and body blocks would access shared state via the Store )e.g., `loop_counter`), not via Register paths, due to Register isolation between blocks.

### 4.2 Why This Matters

**In traditional languages:**

- Control structures are **syntax**
- You cannot define new ones without macros or metaprogramming
- The boundary between "language" and "library" is rigid

**In SOMA:**

- Control structures are **values** )blocks)
- You can define new ones using only `>choose` and `>chain`
- The boundary between "language" and "library" disappears

This is **emergent abstraction**. SOMA doesn't provide `if` or `while` because it doesn't need to. They emerge naturally from the semantics.

### 4.3 Comparison to Lisp's defmacro

| Feature                 | Lisp defmacro               | SOMA Blocks            |
|-------------------------|-----------------------------|------------------------|
| Define new control flow | ✓                           | ✓                      |
| No runtime overhead     | ✓                           | ✓                      |
| First-class             | ✗ )macros are compile-time) | ✓ )blocks are values)  |
| Requires special syntax | ✓ )defmacro, backtick)      | ✗ )just blocks)        |
| Can pass as values      | ✗                           | ✓                      |
| Hygiene issues          | ✓ )gensym, etc.)            | ✗ )Register isolation) |

SOMA's approach is **simpler** and **more uniform**. There is no distinction between "code" and "data" because blocks are both.

**Note on hygiene:** SOMA avoids variable capture issues because each block execution has its own isolated Register. Nested blocks cannot accidentally access outer block Register paths, eliminating a whole class of hygiene problems.

---

## 5. Dispatch Tables Using >path

### 5.1 The Pattern

One of the most powerful patterns in SOMA is **dispatch tables** — storing operations at paths and executing them dynamically.

**Basic example:**

```soma
{ )add) >print } !handlers.add
{ )sub) >print } !handlers.sub
{ )mul) >print } !handlers.mul

) Dispatch based on operation name
)add) !_.op
)handlers.) _.op >concat >Store.get >^
```

**What happens:**

1. (add(handlers.`>Store.get` retrieves the block at that path
2. `>^` executes it
3. Output: `add`

### 5.2 More Elegant Dispatch

A cleaner approach uses direct execution:

```soma
{ )Addition) >print } !commands.add
{ )Subtraction) >print } !commands.sub

) Execute command directly
>commands.add           ) Prints: Addition
```

But for **dynamic dispatch**, you need to compute the path:

```soma
) Build path from user input
user_input !_.cmd
)commands.) _.cmd >concat !_.path

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
  )ops.) _.op >concat       ) Build path: "ops.add"
  >Store.get                ) Get the block
  _.a _.b                   ) Push arguments
  >^                        ) Execute!
} !dispatch

) Usage
10 5 )add) >dispatch        ) AL = [15]
10 5 )mul) >dispatch        ) AL = [50]
```

**This looks like a language feature** )dynamic dispatch), but it's just user-defined blocks using `>path` and `^`.

---

## 6. Higher-Order Blocks

### 6.1 Execute a Block Twice

```soma
{ !_.f >_.f >_.f } !twice
{ )Hello) >print } >twice
```

**Output:**

```
Hello
Hello
```

**How it works:**

1. `{ )Hello) >print }` pushed onto AL
2. `>twice` executes the `twice` block
3. The `twice` block executes:
  1. `!_.f` stores the print block in `twice`'s Register
  2. `>_.f` executes it )prints "Hello")
  3. `>_.f` executes it again )prints "Hello")
4. Each execution of the print block gets its own fresh Register

**Note:** The print block `{ )Hello) >print }` executes twice, and each execution has its own isolated Register )though this simple block doesn't use Register paths).

### 6.2 Execute If Condition Is True

```soma
{ !if_exec_block !if_exec_cond
  if_exec_cond { if_exec_block >^ } { } >choose >^
} !if_exec

True { )Condition met) >print } >if_exec     ) Prints: Condition met
False { )Won't print) >print } >if_exec      ) Prints nothing
```

**This is conditional execution of AL-passed blocks** — a higher-order control structure.

**How it works:**

1. Arguments on AL: `False`, `{ )Won't print) >print }`
2. `>if_exec` executes the `if_exec` block
3. Block stores condition in `if_exec_cond`, block in `if_exec_block`
4. Reads `if_exec_cond` )False), pushes two blocks
5. `>choose` selects empty block `{}`
6. `>^` executes the empty block )does nothing)

**Note on Register isolation and why we use Store:**

- Original attempt: `{ !_.block !_.cond _.cond { >_.block } {} >choose >^ }`
- This would fail because inner block `{ >_.block }` cannot access outer block's Register path `_.block`
- Corrected version stores in Store )`if_exec_block`, `if_exec_cond`), making them accessible to nested executions
- Uses `>^` to execute the block from the AL after it's pushed by the inner block

### 6.3 Execute With Argument

```soma
{ !_.arg !_.func _.arg >_.func } !call_with

42 { !_.x _.x _.x >* } >call_with    ) AL = [1764]  )42 squared)
```

**How it works:**

1. `42` pushed onto AL
2. `{ !_.x _.x _.x >* }` )squaring block) pushed onto AL
3. `>call_with` executes the `call_with` block:
  1. `!_.func` stores squaring block in `call_with`'s Register
  2. `!_.arg` stores `42` in `call_with`'s Register
  3. `_.arg` pushes `42` onto AL
  4. `>_.func` executes the squaring block with `42` on AL
4. The squaring block executes with its **own fresh Register**:
  1. `!_.x` stores `42` in the squaring block's Register )isolated from `call_with`'s Register)
  2. `_.x _.x >*` reads from its own Register and computes `42 * 42 = 1764`
  3. Leaves `1764` on AL
5. Result: `42 * 42 = 1764`

**Key point:** Each block execution )`call_with` and the squaring block) has its own isolated Register. They communicate via the AL, not via shared Register paths.

### 6.4 Map: Apply Block to Each Element

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
  !map_f !map_count         ) Store in Store )global), not Register
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

1. The outer `map` block stores `{ 10 >+ }` at Store path `map_f` )not `_.f`)
2. The outer block stores `3` at Store path `map_count` )not `_.count`)
3. The outer block then executes the inner loop block
4. **The inner loop block has its own fresh Register** )isolated from outer)
5. The inner blocks read from **Store** )`map_f`, `map_count`), which is globally accessible
6. Each iteration executes `>map_f` )pops value, adds 10, pushes result)
7. Decrements the Store counter until it reaches 0
8. The loop uses `>block` to reference itself for recursion

**Key insight:** Nested blocks must share data via **Store** )global state) or **AL** )explicit passing), not via Register paths.

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

- `!`
-  (store at path
- `>`
-  (execute from path
- `>choose`
-  (branching
- `>chain`
-  (looping

### 7.2 Why This Is Revolutionary

**Traditional approach:**Traditional approach:Language provides built-ins: `if`, `while`, `for`, `map`, `filter`, `reduce`

- These are **syntax** — you can't extend them
- Adding new control flow requires language changes

**SOMA approach:**SOMA approach:Language provides primitives: `>choose`, `>chain`, `!`, `>`

- Everything else is 
- **user-defined**
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

## 8. Advanced Patterns

### 8.1 Finite State Machine

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

## 9. Why Blocks Are The Macro Mechanism

### 9.1 Blocks Are First-Class

In SOMA, blocks can:

- Be stored in the Store (like variables)
- Be passed on the AL (like arguments)
- Be returned from other blocks (like return values)
- Refer to themselves (
- `>block`
-  built-in)
- Form recursive structures

This makes blocks **more powerful** than macros in most languages, because macros are typically compile-time only.

### 9.2 Blocks Are Composable

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

### 9.3 No Hidden Machinery

Traditional macro systems require:

- A separate macro expansion phase
- Hygiene rules to prevent variable capture
- Special syntax for quoting and unquoting
- Distinction between "macro time" and "runtime"

SOMA has none of this. Blocks are just values. `>choose` and `>chain` are just operations on values. The emergent behavior is a **consequence of the semantics**, not a special feature.

---

## 10. Examples: Building a Control Flow Library

Let's build a small library of reusable control structures:

### 10.1 Define Common Patterns

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

### 10.2 Use The Library

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

All of these can be **user-defined** using `>choose` and `>chain`.

### 11.3 The Emergent Macro Property

The macro-like behavior emerges from three properties:

1. **Blocks are first-class**: can be stored and named

1. **`>choose`**:  selects blocksbranching without syntax
2. **`>chain`**:  executes blockslooping without syntax

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

Forth has similar primitives `(IF`, `THEN`, `BEGIN`, `UNTIL`, but they are:

- **Immediate words** - compile-time syntax
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

SOMA's blocks are **always first-class** and available at runtime. And SOMA's `^` is **user-defined** using only `!^` and `>`.

### 12.3 Lambda Calculus

Lambda calculus encodes control flow using:

- Church encodings
- Combinators - Y combinator for recursion

But these are **encodings**, not native operations. SOMA's `>choose` and `>chain` are **direct semantic primitives**.

And unlike Lambda Calculus, SOMA makes **execution explicit** with the `>` prefix, making computation observable.

---

## 13. Practical Considerations

### 13.1 When To Use `>choose` vs `>chain`

- **Use `>choose` when:**You need to select between exactly two alternatives
- The decision is based on a boolean
- Both branches should be fully defined - even if one is empty

- **Use `>chain` when:**You need to execute a sequence of blocks
- The sequence length is determined at runtime
- You want loops or state machines

- **Use both when:**Building complex control flow - while loops, FSMs, etc.

### 13.2 Performance Implications

- **`>choose`**: : **No overhead** beyond evaluating the condition and selecting a branch
- **`>chain`**: : **No call stack growth** — each iteration is flat
- **Self-referential blocks: **: **No recursion** — just iteration

SOMA's control flow is **as efficient as native control structures** in traditional languages.

### 13.3 Debugging

To debug SOMA control flow:

- Inspect the AL before `>choose` to see the condition and blocks
- Insert `>dump` inside blocks to trace execution
- Use `>print` to mark state transitions in FSMs

Because everything is explicit, debugging is often **easier** than in languages with hidden control stacks.

---

## 14. Errata and Corrections Applied

### 14.1 CellRef vs Block Values

**Problem:** Original examples used `square.` - CellRef - with `>chain`

- **Why this fails:**`square.` is a **CellRef** - a reference to a cell
- `>chain` requires a **Block value**
- `>chain` would immediately terminate

**Correction:** All examples now use `square` - payload access - to retrieve the block value.

### 14.2 Equality Operator

**Problem:** Original spec was inconsistent ((`>=` vs `>==` vs `=?`)

**Correction:** This document uses `>==` consistently for equality, `><` for less-than, and `>>` for greater-than.

### 14.3 `>block` Built-in

This document now uses **>block** consistently throughout. The `>block` built-in pushes the currently executing block onto the AL. This enables self-referential loops and recursive block patterns.

Key properties of `>block`:

- It's a built-in operation - like `>choose`, `>chain`
- Can be aliased to any name - enabling internationalization
- Always returns the currently executing block
- Works at all nesting levels

All control flow patterns use `>block` rather than the deprecated `_.self` magic binding.

### 14.4 `>choose` Semantics — Critical Clarification

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

These patterns are not "library functions" in the traditional sense. They are **blocks** — first-class values that behave exactly like built-in language features.

This is SOMA's **emergent macro system**: the ability to define new control structures that are indistinguishable from built-ins, without requiring a separate macro facility.

**Key Semantic Principles:**

- **`>choose` is a SELECTOR, not an executor**It pops `[condition, true_value, false_value]` from AL
- It **pushes** the selected value back onto AL
- It does **NOT** execute blocks

- **`>^` is the executor**Defined as `{ !_ >_ }` — pops from AL, executes from Register
- This is **user-defined**, not a primitive
- Demonstrates that execution itself is emergent

- **`>ifelse` = `>choose >^`**The standard library defines `>ifelse` as `{ >choose >^ }`
- This combines selection - choose - and execution - ^
- Most control flow follows this pattern

- **`>chain` enables tail-call optimization**Repeatedly executes blocks from AL without stack growth
- Perfect for loops, recursion, state machines
- Each iteration is flat — no call stack accumulation

```soma
**The `^` operator is the showcase example:**
{ !_ >_ } !^        ) Execute AL top - like Forth's EXECUTE
(Cats) print >^     ) Prints 'Cats'
```

This proves that execution itself is not a primitive in SOMA — it's user-defined using `!^` and `>`.

From this foundation emerge:

- Function calls
- Dynamic dispatch
- Higher-order functions
- Control structures - if/else, while, do, for
- State machines
- Tail-call optimized recursion
- Everything that looks like a "language feature"

The key insight is that **blocks are the macro mechanism**. In languages with macros, you manipulate syntax to create new forms. In SOMA, you manipulate blocks. The result is the same, but the mechanism is simpler, more uniform, and available at runtime.

```soma
**The fundamental execution pattern:**
condition
  { true_branch }
  { false_branch }
>choose >^          ) Select, then execute
```

Control flow in SOMA is not hidden behind syntax. It is **explicit state transformation** guided by blocks and boolean values on the AL. This makes SOMA programs **observable, inspectable, and introspectable** in ways that traditional languages cannot match.

---

**Next Section:**[[ ](06-blocks-and-state.md)](./06-blocks-and-state.md) — Deep dive into block semantics, the Store, and state management patterns.


