# 04 - Blocks and Execution

## Overview

Blocks are the fundamental executable units in SOMA. Unlike functions in traditional languages, blocks are **first-class values** that transform machine state directly. They have no arity, declare no parameters, and do not return values. A block is not called-it is executed, transforming the pair `)AL, Store)` into a new state `)AL', Store')`.

This document clarifies what blocks are, how they execute, and what distinguishes them from functions.

---

## 1. Blocks Are Values

A block is written as a sequence of tokens enclosed in braces:

```soma
{ token token token }
```

Blocks may be nested without limit:

```soma
{ 1 { 2 3 >+ } >drop }
```

**Critically: a block is not executed when it is read.** It is pushed onto the AL as a value, just like an integer or string.

```soma
{ 5 5 >* }     ) AL now contains a Block, not 25
```

Blocks behave like any other SOMA value. They may be:

- Pushed onto the ALStored in a CellPassed between BlocksUsed in control flow )`>choose`, `>chain`)
- Executed via built-ins or path execution

### Example: Storing and Reusing a Block

```soma
{ >dup >* } !square

7 square >chain >print
```

**Output:** `49`

Here:

1. A block is created and stored in the Cell `square`
2. The integer `7` is pushed onto the AL
3. The block stored at `square` is retrieved and executed via `>chain`
4. The block duplicates `7` and multiplies it by itself
5. The result `49` is printed

---

## 2. No Arity, No Return

SOMA blocks do not declare parameters. They simply consume whatever values they need from the AL and leave new values behind.

There is no signature like `f)x, y) -> z`. Instead:

- A block reads from the AL if it needs input
- A block writes to the AL )or Store) if it produces output
- The "contract" is entirely dynamic

### Example: A Block That Consumes Two Values

```soma
{ >+ } !add_two_numbers

3 4 add_two_numbers >chain
) AL now contains [7]
```

The block `add_two_numbers` doesn't declare "I take two integers." It simply executes `>+`, which consumes two values from the AL. If fewer than two values are present, execution fails fatally.

### Example: A Block That Leaves Multiple Values

```soma
{ 1 2 3 } !push_three

push_three >chain
) AL now contains [1, 2, 3]
```

There is no formal return statement. The block simply leaves values on the AL.

---

## 3. Execution Model: Linear, Token-by-Token

When a block executes, SOMA processes its tokens **left to right**, one at a time. Each token transforms the machine state:

```
)AL, Store, Register, IP) -> )AL', Store', Register', IP')
```

Where:

- **AL**: The Accumulator List
- **Store**: The global graph of Cells
- **Register**: The block-local graph of Cells
- **IP**: Instruction Pointer )next token to execute)

Execution proceeds **strictly linearly**. There is no symbolic reduction, no lazy evaluation, no hidden control flow. Each token is processed in sequence until the block ends.

### Example: Step-by-Step Execution

```soma
{ 2 3 >+ 5 >* }
```

Initial state:

- AL = `[]`
- Register = `{}` )empty graph)

After token `2`:

- AL = `[2]`

After token `3`:

- AL = `[3, 2]`

After token `>+`:

- AL = `[5]` )pops 3 and 2, pushes their sum)

After token `5`:

- AL = `[5, 5]`

After token `>*`:

- AL = `[25]` )pops two 5s, pushes their product)

Final state:

- AL = `[25]`

---

## 4. No Call Stack

SOMA does not implement a call stack. Executing a block **does not create a new stack frame**. There is no return path, no stack unwinding, and no exception model.

Instead, block execution is a **direct state transformation**:

```
Before: )AL1, Store1, Register1)
After:  )AL2, Store2, Register2)
```

When a block finishes, execution simply continues with the next token in the enclosing context.

### Comparison: Function Call vs. SOMA Block

Traditional function call:

```python
def square(x):
    return x * x

result = square(7)
```

Here:

- A new stack frame is createdThe value `7` is bound to parameter `x`
- A value is returned and the frame is popped
- Control returns to the caller

SOMA block execution:

```soma
{ >dup >* } !square
7 square >chain
```

Here:

- No stack frame is createdThe value `7` is already on the AL
- A new Register is created for the block's execution
- The block reads and transforms the AL in-place
- When the block ends, execution continues linearly and the Register is destroyed

---

## 5. Everything is a Block

### The `>block` Built-in

SOMA provides a built-in operation `>block` that pushes the currently executing block onto the AL. This enables blocks to reference themselves without any special magic or automatic bindings.

Stack Effect:

```
[] -> [Block]
```

Semantics:

Pushes the currently executing block onto the AL.

### Everything Executes in a Block Context

All SOMA execution occurs within a block context:

- **Top-level code** is itself a block (the outermost block)**Explicit blocks** `{ ... }` are nested blocks
- There is no "outside" the outermost block-that's the runtime environment

### No Infinite Regress

We don't need to ask "what executes the top-level block?" The top-level code IS a block, axiomatically. The SOMA runtime executes it. There's nothing to formalize "outside" SOMA's computational model.

### `>block` Works Everywhere

```soma
) Top-level
>block              ) Returns the outermost block (the "program")

) Inside explicit block
{ >block }          ) Returns this block

) Nested blocks
{
  >block !outer
  {
    >block !inner
    outer inner >Equal    ) False - different blocks
  }
}
```

### Just Another Built-in

`>block` is not special syntax or a magic binding. It's a regular built-in operation, just like `>choose` or `>chain`. This means:

- It can be aliased to any name: `block !blok` (Russian), `block !kedja` (Swedish)
- No English-centric constraints
- No special Register treatment
- Simpler specification

### Example: Infinite Loop

```soma
{ >block >chain }
```

How it works:

1. Block begins execution`>block` pushes this block onto the AL`>chain` executes the block (which is on top of AL)
2. The cycle repeats indefinitely

This creates an infinite loop without any external naming or storage.

### Example: Nested Blocks Each Have Access to Their Own Block

```soma
{
  "Outer block executing" >print
  >block !outer_self_reg           ) Store in outer's Register

  {
    "Inner block executing" >print
    >block !inner_self_reg         ) Store in inner's Register
  } >chain

  ) After inner block completes, inner's Register is destroyed
  ) outer_self_reg still exists in outer's Register
  ) inner_self_reg is GONE (was in inner's Register)

  >block outer_self_reg >==        ) Compare current block with saved value
  { "Same block (correct)" }
  { "Different blocks (impossible)" }
  >choose >chain >print
}
```

Output:

```
Outer block executing
Inner block executing
Same block (correct)
```

How it works:

1. Outer block executes, `>block` returns the outer BlockOuter Block stores the block reference in Register1 at path `outer_self_reg`Inner block executes, creates Register2Inner block's `>block` returns the inner BlockInner Block stores the block reference in Register2 at path `inner_self_reg`Inner block completes -> **Register2 is destroyed** (along with `inner_self_reg`)Back in outer block with Register1`>block` refers to outer block againComparing `>block` with `outer_self_reg` shows they're the same

Key insight:

- Each block can use `>block` to get a reference to itself
- Inner block's Register is destroyed when it completes
- Outer block's Register persists and its values are still accessible
- **If you want to compare blocks across execution contexts, store them in the Store, not the Register!**

### Corrected Example: Comparing Inner and Outer Blocks

If you want to actually compare the inner and outer blocks, you must use the Store:

```soma
{
  "Outer block executing" >print
  >block !outer_block              ) Store in Store (global)

  {
    "Inner block executing" >print
    >block !inner_block            ) Store in Store (global)
  } >chain

  outer_block inner_block >==
  { "SAME block (impossible)" }
  { "DIFFERENT blocks (correct)" }
  >choose >chain >print
}
```

Output:

```
Outer block executing
Inner block executing
DIFFERENT blocks (correct)
```

Now the comparison works because both blocks are stored in the Store, which persists across block executions.

---

## 6. Block Execution Patterns

SOMA provides multiple ways to execute blocks, each serving different purposes. Understanding these patterns is essential for writing idiomatic SOMA code.

### Overview of Execution Patterns

```soma
{ 1 2 >+ } !myblock         ) Store a block
>myblock                    ) Pattern 1: Execute from Store path
>{ 1 2 >+ }                 ) Pattern 2: Execute block literal directly
myblock >chain              ) Pattern 3: Execute via chain (loops/tail-calls)
myblock >^                  ) Pattern 4: Execute from AL
```

---

### 6.1 Executing Blocks from Paths: `>path`

The **execution prefix **`>` is an atomic read-and-execute operation for blocks stored at paths.

**Core Semantics:**

The `>` prefix performs a single atomic operation:

1. Resolve `path` to a value
2. If the value is a Block, execute it
3. If the value is not a Block, this is a fatal error

**This is NOT two separate operations.** It's an atomic read-and-execute.

**Blocks Are Values Until Executed:**

```soma
print           ) Pushes the print Block onto AL (it's a value)
>print          ) Executes the print Block (it's an operation)
```

**Without `>`, blocks are just values:**

```soma
{ 1 2 >+ }      ) This is a value (a Block) pushed onto AL
{ 1 2 >+ } >^   ) This pushes the block, then executes from AL
>{ 1 2 >+ }     ) This executes immediately (cleaner!)
```

The `>` modifier makes execution **explicit and first-class**.

#### Execution from Store Paths

The most common use of `>` is executing blocks stored in the Store:

```soma
{ >dup >* } !square

>square         ) Execute the block at Store path "square"
```

**How it works:**

1. `>`square reads the Block stored at path "square"
2. Executes that Block immediately
3. The Block operates on whatever's on the AL

**Example: Storing and executing a greeting:**

```soma
{ (Hello) >print } !say_hello

>say_hello      ) Prints: Hello
```

#### Execution from Register Paths

The `>` modifier works identically with Register paths:

```soma
{
  { (Hi from register) >print } !_.greet
  >_.greet      ) Execute block at Register path "_.greet"
}
```

**Output:** `Hi from register`

This is crucial for local execution patterns:

```soma
{
  { >dup >* } !_.operation
  7 >_.operation    ) Execute the locally-stored operation
}
```

**Output:** AL contains `[49]`

#### Built-ins Are Just Store Paths

**All SOMA built-ins are Blocks stored at Store paths.** When you write `>print`, you're not calling a "built-in function"—you're executing the Block at Store path "print".

```soma
>print          ) Execute block at Store path "print"
>dup            ) Execute block at Store path "dup"
>+              ) Execute block at Store path "+"
>==             ) Execute block at Store path "=="
```

There's no special built-in syntax. They're just pre-populated Store paths!

User-defined blocks work exactly the same:

```soma
{ ... } !my_func    ) Store block at path "my_func"
>my_func            ) Execute block at path "my_func"
```

**The key distinction:**

```soma
square          ) Pushes the Block value onto AL
>square         ) Executes the Block (nothing pushed onto AL)
```

---

### 6.2 Executing Block Literals: `>{ }`

The `>{ }` pattern executes a block literal **immediately** without storing it first. This is the cleanest way to execute ad-hoc code.

**Syntax:**

```soma
>{ code }       ) Execute this block immediately
```

**Examples from test suite:**

```soma
) TEST: Simple execute block literal
) EXPECT_OUTPUT: Hello
>{ (Hello) >print }

) TEST: Execute block with result
) EXPECT_AL: [42]
>{ 42 }

) TEST: Execute block with computation
) EXPECT_AL: [8]
>{ 5 3 >+ }
```

#### Passing Arguments via AL

Blocks can receive arguments from the AL:

```soma
) TEST: Execute block with argument from AL
) EXPECT_AL: [10]
5 >{ !_.x _.x 2 >* }
```

**How it works:**

1. `5` is pushed onto ALThe block executes with AL = [5]`!_.x` pops 5 and stores in Register`_.x 2 >*` computes 5 x 2 = 10
2. Leaves 10 on AL

#### #### Multiple Arguments

```soma
) TEST: Execute block with multiple arguments
) EXPECT_AL: [15]
5 10 >{ !_.b !_.a _.a _.b >+ }
```

**Note the order:** LIFO @Last In, First OutA. `10` is popped first into `_.b`, then `5` into `_.a`.

#### Nested Execute Blocks

```soma
) TEST: Nested execute blocks
) EXPECT_AL: [100]
>{
  >{ 10 }
  >{ !_.x _.x _.x >* }
}
```

**How it works:**

1. Outer block executes`>{ 10 }` executes, leaving 10 on AL`>{ !_.x _.x _.x >* }` executes:
  - Pops 10 into `_.x`
  - Computes 10 x 10 = 100
  - Leaves 100 on AL

#### Execute Block vs Chain Comparison

**Old pattern (verbose):**

```soma
{ 42 } >chain       ) Push block to AL, then execute with chain
```

**New pattern (cleaner):**

```soma
>{ 42 }             ) Execute block literal directly
```

Both give the same result, but `>{ }` is more concise and clearer in intent.

#### Register Isolation

Each `>{ }` execution creates a fresh Register:

```soma
) TEST: Execute block with Register isolation
) EXPECT_AL: [5]
>{
  5 !_.outer
  _.outer >{ !_.inner _.inner }
}
```

**How it works:**

1. Outer block creates Register1Store 5 in Register1 at path `_.outer`Push 5 onto ALInner block executes with fresh Register2`! _.inner` pops 5, stores in Register2`_.inner` pushes 5 back onto AL
2. Inner block completes -> Register2 destroyed
3. Back in outer block with Register1

---

### 6.3 Loops and Tail-Calls: `>chain`

The `>chain` operation enables loops and tail-call optimization. It repeatedly pops the AL top and executes it **if it's a Block**. If the top is not a Block, `>chain` stops and leaves it on the AL.

**Behavior:**

```
Loop:
  Pop AL top
  If it's a Block:
    Execute the block
    Repeat
  Else:
    Push it back onto AL
    Stop
```

**Stack Effect:**

```
[Block1, ...] -> (execute Block1 and repeat)
[Nil, ...] -> [Nil, ...] (stop)
[42, ...] -> [42, ...] (stop)
```

#### Basic Chain Example

```soma
{ (Hello) >print Nil } !say_hello
>say_hello
```

**How it works:**

1. Execute the block at path `say_hello`Block prints "Hello" and pushes Nil`>chain` sees Nil (not a Block), stops
2. AL = [Nil]

#### Tail-Call Optimization: Fibonacci

From `02_advanced_chain.soma`:

```soma
) TEST: Fibonacci with tail-call optimization via chain
0 !fib.a
1 !fib.b
7 !fib.count

{
  fib.a >toString >print

  fib.count 1 >=<
    Nil
    {
      fib.count 1 >- !fib.count
      fib.a fib.b >+ !fib.next
      fib.b !fib.a
      fib.next !fib.b
      fib-step
    }
  >choose
} !fib-step

fib-step >chain
```

**Output:** `0 1 1 2 3 5 8`

**How it works:**

1. `fib-step >chain` executes the block and continues chaining
2. Block prints current Fibonacci number
3. Check if count <= 1:
  - If yes: return `Nil` (stops chain)If no: update state and return `fib-step` block (continues chain)
4. `>choose` selects the appropriate result`>chain` sees either Nil (stops) or fib-step Block (continues)

**Key insight:** This is tail-call optimization! No call stack grows. The block returns itself for the next iteration.

#### Tail-Call Optimization: Factorial with Accumulator

```soma
) TEST: Factorial with tail-call via chain (accumulator pattern)
5 !fact.n
1 !fact.acc

{
  fact.n 0 >=<
    fact.acc
    {
      fact.n 1 >- !fact.n
      fact.acc fact.n 1 >+ >* !fact.acc
      fact-step
    }
  >choose
} !fact-step

fact-step >chain
```

**Output:** AL = [120]

**How it works:**

1. Check if n <= 0:
  - Base case: return accumulator (stops chain)Recursive case: update state, return `fact-step` block
2. Each iteration multiplies accumulator by current n
3. No stack growth--constant space!

#### State Machine Pattern

```soma
) TEST: State machine via chain
{
  (State A) >print
  state-b
} !state-a

{
  (State B) >print
  state-c
} !state-b

{
  (State C) >print
  { (Done) >print }
} !state-c

state-a >chain
```

**Output:**

```
State A
State B
State C
Done
```

**How it works:**

1. Each state block prints its message and returns the next state block`state-c` returns a block (not a simple value), so chain continues
2. Final block prints "Done" and implicitly returns Void
3. Chain stops when no Block is left on AL

#### Countdown with Mixed Execution

From test suite:

```soma
) TEST: Countdown using chain
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

**How it works:**

1. Print current count, decrement
2. Check if count <= 0:
  - If yes: return a block that prints "Liftoff"If no: return `countdown` block itself
3. `>choose` selects the result`>^` executes whatever's on AL (either the liftoff block or countdown block)
4. Chain continues until the liftoff block completes

**Note:** This uses `>^` to execute the chosen value. See next section.

#### Trampoline Pattern: Mutual Recursion

```soma
) TEST: Trampoline pattern - mutual recursion via chain
{
  (even: ) parity.n >toString >concat >print

  parity.n 0 >==
    { (Result: True) >print }
    { parity.n 1 >- !parity.n is-odd }
  >choose
} !is-even

{
  (odd: ) parity.n >toString >concat >print

  parity.n 0 >==
    { (Result: False) >print }
    { parity.n 1 >- !parity.n is-even }
  >choose
} !is-odd

4 !parity.n
is-even >chain
```

**Output:**

```
even: 4
odd: 3
even: 2
odd: 1
even: 0
Result: True
```

**How it works:**

1. Each function checks base caseIf not base case, returns the other function`>chain` continues bouncing between functions
2. No stack growth--trampolining handles mutual recursion in constant space!

---

### 6.4 Execute from AL: `>^`

The `>^` pattern executes a block that's **already on the AL**. This is typically user-defined in stdlib:

```soma
{ !_ >_ } !^                 ) Like Forth's EXECUTE
```

**How it works:**

1. `!_` pops the AL top and stores it in Register at path `_``>_` reads from Register path `_` and executes it

**Example:**

```soma
(Data) print >^              ) Execute print block on "Data"
```

**How it works:**

1. Push string `(Data)` onto ALPush `print` block onto AL (AL = [print, (Data)])`>^` executes:
  - Pops `print` block, stores in `_``>_` executes the print block
  - Print block pops "(Data)" and prints it

#### Pattern: Higher-Order Operations

```soma
{ !_.f !_.x _.x >_.f } !apply

{ 1 >+ } !increment
5 increment >apply         ) AL: [6]
```

**How it works:**

1. Push 5 onto ALPush `increment` block onto AL
2. `apply` block executes:

- Pops `increment` into `_.f`
- Pops 5 into `_.x`
- Pushes 5 back onto AL
- `>_.f` executes `increment` block
- Result: 6

This pattern is powerful: it takes a Block from the AL and executes it, similar to Forth's `EXECUTE` or Lisp's `FUNCALL`, but **user-defined** using only primitives!

---

### Summary: Execution Patterns

| Pattern               | Syntax      | Use Case                                  | Example           |
|-----------------------|-------------|-------------------------------------------|-------------------|
| **Execute from path** | `>path`     | Call stored blocks )like functions)       | `>square`         |
| **Execute literal**   | `>{ code }` | Ad-hoc execution, inline blocks           | `>{ 5 3 >+ }`     |
| **Chain execution**   | `>chain`    | Loops, tail-calls, state machines         | `fib-step >chain` |
| **Execute from AL**   | `>^`        | Higher-order functions, dynamic execution | `myblock >^`      |

**When to use each:**

- `>path`: Calling predefined functions, accessing built-ins
- `>{ }`: One-off execution, passing code blocks as arguments
- `>chain`: Iterative algorithms, tail-recursive functions, FSMs
- `>^`: Higher-order patterns, dynamic dispatch

---

### Self-Execution via `>block`

The `>block` built-in can be combined with these patterns:

**With `>chain` )loops):**

```soma
{
  counter 1 >+ !counter
  counter >print
  counter 10 ><
    >block              ) Continue if counter < 10
    Nil                 ) Stop otherwise
  >choose
} !count_to_ten

0 !counter
>count_to_ten
```

**How it works:**

1. The Block increments and prints `counter`
2. Checks if `counter < 10`
3. If true, `>choose` returns the current block )via `>block`)
4. If false, `>choose` returns `Nil`
5. `>chain` continues if a Block is returned, stops on Nil

**Important:** `counter` must be in the **Store** )not Register) because each recursive execution needs to see the updated value.

---

### Complete Example: Overriding Built-ins

Because built-ins are just Store paths, you can override them:

```soma
print !old_print                ) Save original print
{ )LOUD: ) >old_print >old_print } !print    ) Override print

)hello) >print                  ) Prints: LOUD: hello
```

**What happens:**

1. Original `print` Block is saved at path "old_print"
2. New Block is stored at path "print"
3. New Block prints "LOUD: " then calls the original twice
4. `>print` now executes the new behavior

---

## 7. Examples

### Example 1: Executing Block Literals

**Simple execution:**

```soma
>{ )Hello) >print }
```

**Output:** `Hello`

The block literal is executed immediately with `>{ }`.

**With computation:**

```soma
>{ 5 3 >+ }     ) AL: [8]
```

**With arguments from AL:**

```soma
5 >{ !_.x _.x 2 >* }    ) AL: [10]
```

---

### Example 2: Executing Stored Blocks

```soma
{ >dup >* } !square

7 >square       ) Execute stored block, AL: [49]
```

**How it works:**

1. Block is stored at path "square"
2. `7` is pushed onto AL
3. `>square` executes the block
4. Block duplicates 7 and multiplies: 7 x 7 = 49

---

### Example 3: Block Consuming and Producing AL Values

```soma
{ !_.x !_.y _.x _.y >+ } !add_named

3 7 >add_named
) AL = [10]
```

**How it works:**

1. Block starts execution -> Creates fresh Register
2. Pops 7 and stores in `_.y` )in this block's Register)
3. Pops 3 and stores in `_.x` )in this block's Register)
4. Pushes `_.x` )3) back onto AL
5. Pushes `_.y` )7) back onto AL
6. Adds them with `>+`
7. Leaves result )10) on AL
8. Block completes -> Register )with `_.x` and `_.y`) is destroyed

**Key insight:** The Register cells `_.x` and `_.y` are temporary and destroyed when the block ends. The result persists only because it was left on the AL.

---

### Example 4: Block Passed as an Argument

```soma
{ !_.action >_.action } !do_it

{ )Action executed) >print } >do_it
```

**Output:** `Action executed`

**How it works:**

1. The action block is pushed onto AL
2. `do_it` block executes:

- Pops the action block into `_.action`
- `>_.action` executes it from Register

---

### Example 5: Loops with >chain )Correct Pattern)

**Countdown loop:**

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

**Output:** `3 2 1 Liftoff`

**How it works:**

1. Store counter in **Store** )not Register)
2. Each iteration prints and decrements
3. When count <= 0, executes liftoff block
4. Otherwise, executes countdown again )tail-call)

**Important:** The counter must be in the **Store** because each recursive execution needs to see the updated value. Register values are isolated between executions.

---

### Example 6: Tail-Call Optimized Factorial

```soma
5 !fact.n
1 !fact.acc

{
  fact.n 0 >=<
    fact.acc
    {
      fact.n 1 >- !fact.n
      fact.acc fact.n 1 >+ >* !fact.acc
      fact-step
    }
  >choose
} !fact-step

fact-step >chain
```

**Output:** AL = [120]

**How it works:**

- Check if n <= 0:
- Base case: return accumulator )stops chain)
- Recursive case: update state, return fact-step block

1. Each iteration multiplies accumulator by current nNo stack growth--constant space!Uses **Store** for state )fact.n, fact.acc) so values persist across iterations

---

### Example 7: Finite State Machine

```soma
{
  )State A) >print
  state-b
} !state-a

{
  )State B) >print
  state-c
} !state-b

{
  )State C) >print
  { )Done) >print }
} !state-c

state-a >chain
```

**Output:**

```
State A
State B
State C
Done
```

**How it works:**

1. Each state block prints its message and returns the next state block
2. `>chain continues as long as Blocks are returned`
3. Final block completes and chain stops

---

### Example 8: Register Isolation

**Wrong: Trying to share Register between blocks**

```soma
) This will FAIL
{
  42 !_.value
  >{ _.value >print }  ) ERROR: _.value is Void in inner block
}
```

**Right: Pass data via AL**

```soma
{
  42 !_.value
  _.value              ) Push onto AL
  >{ !_.y _.y >print } ) Inner block pops from AL
}
```

**Output:** `42`

**Right: Share data via Store**

```soma
{
  42 !shared_value     ) Store in Store )global)
  >{
    shared_value >print  ) Inner reads from Store
  }
}
```

**Output:** `42`

**Key insight:** Registers are completely isolated between blocks. Use Store )global) or AL )explicit passing) to share data.

---

## 8. Register Lifetime and Isolation

### The Fundamental Rule: Complete Isolation

**Each block execution creates a fresh, empty Register that is destroyed when the block completes.**

Registers are **completely isolated** between blocks:

- Inner blocks **cannot** see outer block's Register cellsParent blocks **cannot** see child block's Register cellsThere is **no lexical scoping** of RegistersThere is **no Register nesting** or inheritance

**If you want to share data between blocks, you must:**

- Use the **Store** )global, persistent state)Pass values via the **AL** )stack-based communication)Use **CellRefs** to share structure

### Register Lifecycle

When a block begins execution:

1. **Create** a fresh, empty RegisterExecute the block's tokens**Destroy** the Register completely

### Register Properties

- ****Isolated****: : No connection to parent/child block Registers
- ****Temporary****: : Destroyed when block completes
- ****Local****: : Only visible within the executing block
- ****Fresh****: : Always starts empty

---

### Example 1: Nested Blocks Have Separate Registers

```soma
{
  1 !_.x
  { 2 !_.x _.x >print } >chain  ) Prints: 2
  _.x >print                     ) Prints: 1
}
```

**Execution trace:**

1. Outer block executes -> Creates **Register1**`1 !_.x` -> Store 1 in Register1 at path `_.x``{ 2 !_.x _.x >print }` -> Creates a Block value )not executed yet)`>chain` -> Execute the inner block
  - Inner block starts -> Creates **Register2** )empty, completely separate)`2 !_.x` -> Store 2 in Register2 at path `_.x``_.x` -> Read Register2 path `_.x` )value: 2)`>print` -> Prints `2`Inner block completes -> **Register2 is destroyed**
2. Back in outer block with Register1`_.x` -> Read Register1 path `_.x` )still 1)`>print` -> Prints `1`

**Key insight:** The inner block's `_.x` and outer block's `_.x` are in **completely different Registers**. They don't interfere with each other at all.

**Output:**

```
2
1
```

---

### Example 2: Inner Block Cannot See Outer Register )ERROR)

```soma
>{1 !_.n >{_.n >print}}  ) FATAL ERROR
```

**What happens:**

1. Outer block executes -> Creates Register1`1 !_.n` -> Store 1 in Register1 at path `_.n``>{_.n >print}` -> Execute inner block
  - Inner block starts -> Creates **Register2** )fresh, empty)`_.n` -> Try to read Register2 at path `_.n`Register2 has no `_.n` -> Resolves to **Void**Push Void onto AL`>print` -> Try to execute the path "print" )not `>print`!)
  - Wait, this example needs fixing...

Let me show the correct error case:

```soma
>{1 !_.n >{_.n 10 >+}}  ) Inner block gets Void for _.n
```

**What happens:**

1. Outer block executes -> Creates Register1`1 !_.n` -> Store 1 in Register1 at path `_.n``>{_.n 10 >+}` -> Execute inner block
  - Inner block starts -> Creates **Register2** )fresh, empty)`_.n` -> Read Register2 at path `_.n`Register2 has no `_.n` -> Resolves to **Void**Push Void onto AL`10` -> Push 10 onto AL`>+` -> Try to add Void and 10 -> **FATAL ERROR**

**Key insight:** Inner blocks cannot access outer block's Register cells. Each block sees **only its own Register**.

---

### Example 3: Multiple Nested Blocks, Each Isolated

```soma
{
  1 !_.n                ) Outer Register: _.n = 1

  { 2 !_.n } >chain     ) Inner1 Register: _.n = 2 )then destroyed)

  _.n >print            ) Outer Register: _.n still = 1

  { 3 !_.n } >chain     ) Inner2 Register: _.n = 3 )then destroyed)

  _.n >print            ) Outer Register: _.n still = 1
}
```

**Output:**

```
1
1
```

**Key insight:** Each inner block gets its own fresh Register. Neither inner block can affect the outer block's Register, and the two inner blocks don't share a Register either.

---

### WRONG: Trying to Access Outer Register

```soma
) WRONG - Inner block can't see outer's _.value
{
  42 !_.value
  >{_.value >print }  ) ERROR: _.value is Void in inner block
}
```

This **fails** because the inner block has its own empty Register.

---

### RIGHT: Pass Data via AL

```soma
) RIGHT - Pass value through the AL
{
  42 !_.value
  _.value              ) Push onto AL
  >{ >print }          ) Inner block pops from AL and prints
}
```

**Output:** `42`

**How it works:**

1. Outer block stores 42 in `_.value`
2. Outer block pushes 42 onto AL
3. Inner block executes with AL containing [42]
4. Inner block pops 42 and prints it

**Key insight:** The AL is shared across all blocks. Use it to pass data explicitly.

---

### RIGHT: Share Data via Store

```soma
) RIGHT - Use Store for shared state
{
  42 !shared_value     ) Store in Store (global)
  >{
    shared_value >print  ) Inner reads from Store
  }
}
```

**Output:** `42`

**How it works:**

1. Outer block writes 42 to Store at path "shared_value"
2. Inner block reads from Store at path "shared_value"
3. Inner block prints 42

**Key insight:** The Store is global and persistent. All blocks can access it.

---

### RIGHT: Return Data via AL

```soma
{
  >{ 5 !_.n _.n _.n >* } !_.square  ) Define helper in outer Register

  7 >_.square          ) Call with 7
  >print               ) Prints: 49
}
```

**How it works:**

1. Define `_.square` block in outer Register
2. `7` pushes 7 onto AL
3. `>_.square` executes the block
4. Outer block continues with AL = [49]
5. `>print` prints 49

The block execution:

1. Creates fresh Register3
2. `!_.n` pops 7 from AL, stores in Register3
3. `_.n _.n >*` computes 7 x 7 = 49
4. Leaves 49 on AL
5. Register3 is destroyed

**Key insight:** Blocks communicate via the AL. The inner block receives input from AL and returns output to AL.

---

### Common Pattern: Nested Loop Counters

```soma
{
  0 !_.i                           ) Outer counter

  {
    0 !_.i                         ) Inner counter (different Register!)
    _.i 5 ><
      { _.i 1 >+ !_.i >block >chain }    ) Inner loop uses its own _.i
      { }
    >choose >chain
  } !_.inner_loop

  _.i 3 ><
    {
      >_.inner_loop                ) Call inner loop
      _.i 1 >+ !_.i                ) Increment outer _.i
      >block >chain
    }
    { }
  >choose >chain
}
```

**Key points:**

- Outer block has `_.i` for outer counter
- `_.inner_loop` block (when executed) has its own `_.i` for inner counter
- They don't interfere because they're in different Registers
- Each loop maintains its own counter independently

---

### Common Pattern: Helper Functions with Local State

```soma
{
  { !_.x _.x _.x >* } !_.square    ) Helper: square a number
  { !_.x _.x 2 >* } !_.double      ) Helper: double a number

  5 >_.square >print               ) Prints: 25
  5 >_.double >print               ) Prints: 10
}
```

**Key points:**

- Each helper function call gets a fresh Register
- Both `_.square` and `_.double` use `_.x` in their own Registers
- No interference even though both use the same path name
- Complete isolation guarantees safety

---

### Register vs Store vs AL: When to Use Each

| Aspect                       | Store                 | Register             | AL               |
|------------------------------|-----------------------|----------------------|------------------|
| Scope                        | Global                | Block-local          | Flow-based       |
| Lifetime                     | Persistent            | Block execution only | Transient        |
| Sharing                      | All blocks can access | Isolated per block   | Explicit passing |
| Purpose                      | Shared state          | Local computation    | Data flow        |
| Example`config.port``_.temp` | Stack operations      |                      |                  |

**When to use Store:**

- Shared configuration
- Persistent data
- Global state
- Communication between unrelated blocks

**When to use Register:**

- Temporary computation (`_.temp`, `_.result`)
- Loop counters in recursive blocks
- Local variables that don't need to persist

**When to use AL:**

- Function arguments (pass to inner blocks)
- Return values (leave on stack)
- Stack-based computation
- Explicit data flow between blocks

---

### Recursive Self-Reference

The `>block` built-in enables recursion. For tail-call optimization with `>chain`, state should be stored in the **Store** (not Register) so it persists across iterations:

**Tail-call optimized factorial (recommended pattern):**

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

fact-step >chain
```

**Output:** AL = [120]

**How it works:**

1. State (`fact.n`, `fact.acc`) is in the **Store**
2. Each iteration updates Store values
3. Returns either `fact.acc` (stops) or `fact-step` block (continues)
4. `>chain` continues as long as a Block is returned
5. No stack growth—constant space tail-call optimization!

**Key insight:** Using Store for state enables true tail-call optimization. Each iteration sees the updated state without creating new stack frames.

---

### Alternative: Register-Based Recursion via AL

If you want Register-local state, you must pass state via AL (this builds a traditional call stack):

```soma
{
  !_.n                           ) Pop initial value into Register
  _.n 0 >==
  { 1 }                          ) Base case: return 1
  {
    _.n 1 >-                     ) Compute n-1
    >block >chain                ) Recursive call with n-1
    _.n >*                       ) Multiply result by original n
  }
  >choose >^
} !factorial

5 >factorial
```

**Output:** AL = [120]

**This works because:**

1. Each recursive call gets its own Register with its own `_.n`
2. The recursive call pops n-1 from AL and stores it in its own `_.n`
3. Results are returned via AL
4. Each level of recursion has isolated state

**Warning:** This pattern builds a call stack and is NOT tail-call optimized. For loops and tail-calls, use the Store-based `>chain` pattern instead.

---

## 9. Blocks Are Not Functions

It is critical to understand that **blocks are fundamentally different from functions**:

| **Functions (Traditional)**      | **Blocks (SOMA)**                  |
|----------------------------------|------------------------------------|
| Declare parameters               | No declared parameters             |
| Return a value                   | Leave values on AL                 |
| Create stack frames              | Transform state in-place           |
| Support recursion via call stack | Support cycles via >block built-in |
| Hidden execution machinery       | Explicit state transformation      |

**Functions hide state.** They abstract over arguments and returns.

**Blocks expose state.** They operate directly on the AL and Store, making every transformation visible.

---

## Summary

Blocks in SOMA are:

- **First-class values** that can be stored, passed, and executed
- **Arity-free** – they don't declare how many values they consume or produce
- **Return-free** – they leave values on the AL, not via a return statement
- **Executed linearly** – token by token, left to right
- **Stack-free** – no call frames, no return path
- **State transformers** – they transform `AL, Store, Register)` into `AL', Store', Register')`
- **Self-referential** – every block can reference itself via the `>block` built-in

### Execution Patterns Summary

SOMA provides four primary ways to execute blocks:

1. **`>path`** — Execute block from Store or Register path (like function calls)
2. **`>{ code }`** — Execute block literal immediately (cleanest for ad-hoc code)
3. **`>chain`** — Loop/tail-call execution (for iteration and state machines)
4. **`>^`** — Execute block from AL (user-defined, for higher-order patterns)

### Register Isolation Summary

**Critical rule:** Each block execution creates a **fresh, empty Register** that is destroyed when the block completes.

- Registers are **completely isolated** between parent and child blocks
- No lexical scoping of Registers
- To share data: use **Store** (global) or **AL** (explicit passing)
- For tail-calls and loops: use **Store** for state, `>chain` for execution

### The `>block` Built-in Summary

**`>block`** is a built-in operation that pushes the currently executing block onto the AL. This enables:

- Self-referential loops
- Recursive computation
- Finite state machines
- Conditional continuation

`>block` is just another built-in (like `>choose` or `>chain`), which means it can be aliased to any name in any language, removing English-centric constraints.

SOMA programs do not reduce. **They run.**

---

## Resolved Design Questions

### 1. **How are blocks executed?**

**Answer:** Blocks are executed in four primary ways (see Section 6):

- **`>path`** executes blocks at Store or Register paths (atomic read-and-execute)
- **`>{ code }`** executes block literals immediately (cleaner than `{ code } >chain`)
- **`>chain`** executes blocks from AL repeatedly (for loops and tail-calls)
- **`>^`** executes blocks from AL (user-defined pattern)

### 2. **Register Isolation**

**Answer:** Each block gets a **completely fresh, isolated Register**. Parent Registers are completely inaccessible during nested execution.

```soma
{
  >block !outer_self     ) Store in Store (not Register!)
  >{ >block !inner_self }
  outer_self             ) This works because outer_self is in Store
}
```

**Key points:**

- **Store writes** during nested execution ARE visible after the nested block completes (Store is global)
- **Register writes** are lost when the nested block ends (Registers are block-local and destroyed)
- Parent and child blocks have **completely separate Registers** with no sharing
- To share data between blocks: use Store (global) or AL (explicit passing)

### 3. **Tail-Call Optimization**

**Answer:** Use `>chain` with Store-based state for true tail-call optimization:

```soma
) State in Store (persists across iterations)
5 !fact.n
1 !fact.acc

{
  fact.n 0 >=<
    fact.acc
    {
      fact.n 1 >- !fact.n
      fact.acc fact.n 1 >+ >* !fact.acc
      fact-step
    }
  >choose
} !fact-step

fact-step >chain
```

This pattern uses constant space—no stack growth.

---

## Conclusion

Blocks are SOMA's answer to functions, procedures, and lambdas—but they reject the abstraction model entirely. They are **values that transform state**, nothing more and nothing less. Understanding blocks means understanding that SOMA doesn't hide mutation under the hood. It makes mutation the foundation of computation.

The `>block` built-in is what makes blocks truly powerful, enabling self-reference without requiring external naming schemes or workarounds. Every block can access itself via `>block`, and that capability is the foundation of control flow in SOMA.


