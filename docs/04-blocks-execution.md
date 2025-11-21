# 04 – Blocks and Execution

## Overview

Blocks are the fundamental executable units in SOMA. Unlike functions in traditional languages, blocks are **first-class values** that transform machine state directly. They have no arity, declare no parameters, and do not return values. A block is not called—it is executed, transforming the pair `(AL, Store)` into a new state `(AL', Store')`.

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
{ 5 5 >* }     ; AL now contains a Block, not 25
```

Blocks behave like any other SOMA value. They may be:

- Pushed onto the AL
- Stored in a Cell
- Passed between Blocks
- Used in control flow (`>choose`, `>chain`)
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

There is no signature like `f(x, y) -> z`. Instead:

- A block reads from the AL if it needs input
- A block writes to the AL (or Store) if it produces output
- The "contract" is entirely dynamic

### Example: A Block That Consumes Two Values

```soma
{ >+ } !add_two_numbers

3 4 add_two_numbers >chain
; AL now contains [7]
```

The block `add_two_numbers` doesn't declare "I take two integers." It simply executes `>+`, which consumes two values from the AL. If fewer than two values are present, execution fails fatally.

### Example: A Block That Leaves Multiple Values

```soma
{ 1 2 3 } !push_three

push_three >chain
; AL now contains [1, 2, 3]
```

There is no formal return statement. The block simply leaves values on the AL.

---

## 3. Execution Model: Linear, Token-by-Token

When a block executes, SOMA processes its tokens **left to right**, one at a time. Each token transforms the machine state:

```
(AL, Store, Register, IP) → (AL', Store', Register', IP')
```

Where:
- **AL**: The Accumulator List
- **Store**: The global graph of Cells
- **Register**: The block-local graph of Cells
- **IP**: Instruction Pointer (next token to execute)

Execution proceeds **strictly linearly**. There is no symbolic reduction, no lazy evaluation, no hidden control flow. Each token is processed in sequence until the block ends.

### Example: Step-by-Step Execution

```soma
{ 2 3 >+ 5 >* }
```

Initial state:
- AL = `[]`
- Register = `{}` (empty graph)

After token `2`:
- AL = `[2]`

After token `3`:
- AL = `[3, 2]`

After token `>+`:
- AL = `[5]` (pops 3 and 2, pushes their sum)

After token `5`:
- AL = `[5, 5]`

After token `>*`:
- AL = `[25]` (pops two 5s, pushes their product)

Final state:
- AL = `[25]`

---

## 4. No Call Stack

SOMA does not implement a call stack. Executing a block **does not create a new stack frame**. There is no return path, no stack unwinding, and no exception model.

Instead, block execution is a **direct state transformation**:

```
Before: (AL₁, Store₁, Register₁)
After:  (AL₂, Store₂, Register₂)
```

When a block finishes, execution simply continues with the next token in the enclosing context.

### Comparison: Function Call vs. SOMA Block

**Traditional function call:**
```python
def square(x):
    return x * x

result = square(7)
```

Here:
- A new stack frame is created
- The value `7` is bound to parameter `x`
- A value is returned and the frame is popped
- Control returns to the caller

**SOMA block execution:**
```soma
{ >dup >* } !square
7 square >chain
```

Here:
- No stack frame is created
- The value `7` is already on the AL
- A new Register is created for the block's execution
- The block reads and transforms the AL in-place
- When the block ends, execution continues linearly and the Register is destroyed

---

## 5. Everything is a Block

### The `>block` Built-in

SOMA provides a built-in operation `>block` that pushes the currently executing block onto the AL. This enables blocks to reference themselves without any special magic or automatic bindings.

**Stack Effect:**
```
[] → [Block]
```

**Semantics:**
Pushes the currently executing block onto the AL.

### Everything Executes in a Block Context

All SOMA execution occurs within a block context:

- **Top-level code** is itself a block (the outermost block)
- **Explicit blocks** `{ ... }` are nested blocks
- There is no "outside" the outermost block—that's the runtime environment

### No Infinite Regress

We don't need to ask "what executes the top-level block?" The top-level code IS a block, axiomatically. The SOMA runtime executes it. There's nothing to formalize "outside" SOMA's computational model.

### `>block` Works Everywhere

```soma
; Top-level
>block              ; Returns the outermost block (the "program")

; Inside explicit block
{ >block }          ; Returns this block

; Nested blocks
{
  >block !outer
  {
    >block !inner
    outer inner >Equal    ; False - different blocks
  }
}
```

### Just Another Built-in

`>block` is not special syntax or a magic binding. It's a regular built-in operation, just like `>choose` or `>chain`. This means:

- It can be aliased to any name: `block !блок` (Russian), `block !kedja` (Swedish)
- No English-centric constraints
- No special Register treatment
- Simpler specification

### Example: Infinite Loop

```soma
{ >block >chain }
```

**How it works:**
1. Block begins execution
2. `>block` pushes this block onto the AL
3. `>chain` executes the block (which is on top of AL)
4. The cycle repeats indefinitely

This creates an infinite loop without any external naming or storage.

### Example: Nested Blocks Each Have Access to Their Own Block

```soma
{
  "Outer block executing" >print
  >block !outer_self_reg           ; Store in outer's Register

  {
    "Inner block executing" >print
    >block !inner_self_reg         ; Store in inner's Register
  } >chain

  ; After inner block completes, inner's Register is destroyed
  ; outer_self_reg still exists in outer's Register
  ; inner_self_reg is GONE (was in inner's Register)

  >block outer_self_reg >==        ; Compare current block with saved value
  { "Same block (correct)" }
  { "Different blocks (impossible)" }
  >choose >chain >print
}
```

**Output:**
```
Outer block executing
Inner block executing
Same block (correct)
```

**How it works:**
1. Outer block executes, `>block` returns the outer Block
2. Outer Block stores the block reference in Register₁ at path `outer_self_reg`
3. Inner block executes, creates Register₂
4. Inner block's `>block` returns the inner Block
5. Inner Block stores the block reference in Register₂ at path `inner_self_reg`
6. Inner block completes → **Register₂ is destroyed** (along with `inner_self_reg`)
7. Back in outer block with Register₁
8. `>block` refers to outer block again
9. Comparing `>block` with `outer_self_reg` shows they're the same

**Key insight:**
- Each block can use `>block` to get a reference to itself
- Inner block's Register is destroyed when it completes
- Outer block's Register persists and its values are still accessible
- **If you want to compare blocks across execution contexts, store them in the Store, not the Register!**

### Corrected Example: Comparing Inner and Outer Blocks

If you want to actually compare the inner and outer blocks, you must use the Store:

```soma
{
  "Outer block executing" >print
  >block !outer_block              ; Store in Store (global)

  {
    "Inner block executing" >print
    >block !inner_block            ; Store in Store (global)
  } >chain

  outer_block inner_block >==
  { "SAME block (impossible)" }
  { "DIFFERENT blocks (correct)" }
  >choose >chain >print
}
```

**Output:**
```
Outer block executing
Inner block executing
DIFFERENT blocks (correct)
```

Now the comparison works because both blocks are stored in the Store, which persists across block executions.

---

## 6. Block Execution via `>`

### The Execution Prefix

SOMA provides the **execution prefix `>`** as an explicit way to read and execute blocks stored at paths. The `>` modifier is a prefix operator that performs an atomic read-and-execute operation:

```soma
>path        ; Read the Block at path and execute it
```

This works with both **Store paths** and **Register paths**.

### Core Semantics

The `>` prefix performs a single atomic operation:

1. Resolve `path` to a value
2. If the value is a Block, execute it
3. If the value is not a Block, this is a fatal error

**This is NOT two separate operations.** It's an atomic read-and-execute.

### Blocks Are Values Until Executed

Understanding `>` requires understanding the fundamental distinction in SOMA:

```soma
print           ; Pushes the print Block onto AL (it's a value)
>print          ; Executes the print Block (it's an operation)
```

**Without `>`, blocks are just values:**

```soma
{ 1 2 >+ }      ; This is a value (a Block) pushed onto AL
>{ 1 2 >+ }     ; This executes immediately: AL becomes [3]
```

The `>` modifier makes execution **explicit and first-class**.

### Execution from Store Paths

The most common use of `>` is executing blocks stored in the Store:

```soma
{ >dup >* } !square

>square         ; Execute the block at Store path "square"
```

**How it works:**
1. `>square` reads the Block stored at path "square"
2. Executes that Block immediately
3. The Block operates on whatever's on the AL

**Example: Storing and executing a greeting:**

```soma
{ (Hello) >print } !say_hello

>say_hello      ; Prints: Hello
```

### Execution from Register Paths

The `>` modifier works identically with Register paths:

```soma
{
  { (Hi from register) >print } !_.greet
  >_.greet      ; Execute block at Register path "_.greet"
}
```

**Output:** `Hi from register`

This is crucial for local execution patterns:

```soma
{
  { >dup >* } !_.operation
  7 >_.operation    ; Execute the locally-stored operation
}
```

**Output:** AL contains `[49]`

### Built-ins Are Just Store Paths

**All SOMA built-ins are Blocks stored at Store paths.** When you write `>print`, you're not calling a "built-in function"—you're executing the Block at Store path "print".

```soma
>print          ; Execute block at Store path "print"
>dup            ; Execute block at Store path "dup"
>+              ; Execute block at Store path "+"
>==             ; Execute block at Store path "=="
```

There's no special built-in syntax. They're just pre-populated Store paths!

User-defined blocks work exactly the same:

```soma
{ ... } !my_func    ; Store block at path "my_func"
>my_func            ; Execute block at path "my_func"
```

### The Difference: Value vs. Execution

Consider these two patterns:

```soma
; Pattern 1: Push value, then execute
square >chain       ; Two operations: push, then execute

; Pattern 2: Execute directly
>square             ; One atomic operation: read-and-execute
```

**When the path contains a Block, these are usually equivalent.** But `>path` is the direct, atomic form.

**The key distinction:**

```soma
square          ; Pushes the Block value onto AL
>square         ; Executes the Block (nothing pushed onto AL)
```

### Self-Execution via `>block`

The `>block` built-in can be combined with `>` prefix to execute the current block:

```soma
{
  (Loop iteration) >print
  >block >chain         ; Execute this block again (infinite loop)
}
```

**How it works:**
1. The Block prints a message
2. `>block` pushes the current block onto the AL
3. `>chain` executes it again
4. This creates an infinite loop

**More practical: Conditional self-execution:**

```soma
{
  counter 1 >+ !counter
  counter >print
  counter 10 ><
    { >block >chain }     ; Continue if counter < 10
    { }                   ; Stop otherwise
  >choose >chain
} !count_to_ten

0 !counter
>count_to_ten       ; Prints: 1 2 3 4 5 6 7 8 9 10
```

### Complete Example: Overriding Built-ins

Because built-ins are just Store paths, you can override them:

```soma
print !old_print                ; Save original print
{ (LOUD: ) >old_print >old_print } !print    ; Override print

(hello) >print                  ; Prints: LOUD: hello
```

**What happens:**
1. Original `print` Block is saved at path "old_print"
2. New Block is stored at path "print"
3. New Block prints "LOUD: " then calls the original twice
4. `>print` now executes the new behavior

### Execution Patterns

**Pattern 1: Function-like calls**

```soma
{ !_.x _.x _.x >* } !square
5 !_.x >square               ; AL = [25]
```

**Pattern 2: Higher-order operations**

```soma
{ !_.f !_.x _.x >_.f } !apply
42 inc >apply                ; Apply inc to 42
```

**Pattern 3: User-defined execute-from-AL**

```soma
{ !_ >_ } !^                 ; Like Forth's EXECUTE

(Data) print >^              ; Execute print block on "Data"
```

This pattern is powerful: it takes a Block from the AL and executes it, similar to Forth's `EXECUTE` or Lisp's `FUNCALL`, but **user-defined** using only primitives!

### Summary: The `>` Prefix

- **`>path`** — Atomic read-and-execute operation
- Works with **Store paths** and **Register paths**
- Makes execution **explicit**: `print` (value) vs `>print` (execution)
- Built-ins are just Blocks at Store paths
- Enables self-execution via `>block`
- Foundation for user-defined execution patterns

The `>` modifier is what makes SOMA's execution model explicit and first-class. Blocks are values until you explicitly execute them.

---

## 7. Examples

### Example 1: Block as a Value

```soma
{ "Hello" >print } !greet

greet >chain
```

**Output:** `Hello`

The block is stored, then retrieved and executed.

---

### Example 2: Block Consuming and Producing AL Values

```soma
{ !_.x !_.y _.x _.y >+ } !add_named

3 7 add_named >chain
; AL = [10]
```

**How it works:**
1. Block starts execution → Creates fresh Register
2. Pops 7 and stores in `_.y` (in this block's Register)
3. Pops 3 and stores in `_.x` (in this block's Register)
4. Pushes `_.x` (3) back onto AL
5. Pushes `_.y` (7) back onto AL
6. Adds them with `>+`
7. Leaves result (10) on AL
8. Block completes → Register (with `_.x` and `_.y`) is destroyed

**Key insight:** The Register cells `_.x` and `_.y` are temporary and destroyed when the block ends. The result persists only because it was left on the AL.

---

### Example 3: Block Passed as an Argument

```soma
{ !_.action _.action >chain } !do_it

{ "Action executed" >print } do_it >chain
```

**Output:** `Action executed`

**How it works:**
1. The first block takes a block from the AL and executes it
2. The second block (the action) is passed in
3. `do_it` retrieves and executes it

---

### Example 4: Counter with Self-Recursion

```soma
{
  _.counter 1 >+ !_.counter
  _.counter >print
  _.counter 10 ><
    { >block >chain }
    { }
  >choose >chain
} !count_to_ten

0 !_.counter
count_to_ten >chain
```

**Output:** `1 2 3 4 5 6 7 8 9 10`

**How it works:**
1. Block increments and prints `_.counter` (from the **Register**)
2. Checks if `_.counter < 10`
3. If true, executes a block containing `>block >chain` (recursive call)
4. If false, executes an empty block `{}`
5. `>chain` continues execution as long as a Block is on top of AL
6. When `_.counter` reaches 10, the empty block is executed and the loop terminates

**Important Register note:**
- `_.counter` is in the **Register** (local to each execution)
- Each recursive call via `>block` gets its own fresh Register
- BUT the counter persists because... wait, this example is **wrong**!

**This example is actually broken** due to Register isolation. Each recursive call would get a fresh Register with no `_.counter`, causing it to fail. The correct version would store the counter in the **Store**:

```soma
{
  counter 1 >+ !counter      ; Use Store, not Register
  counter >print
  counter 10 ><
    { >block >chain }
    { }
  >choose >chain
} !count_to_ten

0 !counter                   ; Initialize in Store
>count_to_ten
```

Now it works because `counter` is in the Store (global, persistent).

---

### Example 5: Finite State Machine

```soma
True !state

{
  state
  { False !state "Switched to OFF" >print >block >chain }
  { True !state "Switched to ON" >print >block >chain }
  >choose >chain
} !toggle

>toggle
```

**Output:** Alternates between `Switched to OFF` and `Switched to ON` forever.

**How it works:**
1. The block reads `state` from the **Store** (not Register!)
2. Uses `>choose` to select between two blocks
3. Each block updates `state` in the **Store** and recursively calls `>block >chain`
4. `>chain` continues execution indefinitely

**Key insight:** The `state` variable must be in the Store (global) for it to persist across recursive calls. If it were in the Register (`_.state`), each recursive call would get a fresh Register and lose the state.

---

### Example 6: Conditional Recursion Pattern

```soma
{
  condition                ; Read from Store (must be global!)
  { >block >chain }        ; Recurse if true
  { }                      ; Terminate if false
  >choose >chain
} !loop_while_true
```

This is the fundamental pattern for loops in SOMA:
- Test a condition (from Store or AL)
- If true, execute `>block >chain` to continue
- If false, execute empty block to terminate
- `>chain` executes whatever's on top of the AL

**Important:** The condition must come from the Store or be passed via AL. If it's in the Register (`_.condition`), each recursive call gets a fresh Register and won't see the condition.

---

### Example 7: Block That Transforms Store

```soma
{ !_.value !_.path _.value _.path !Store. } !store_at

42 "answer" store_at >chain
; Cell at Store path `answer` now contains 42
```

**How it works:**
1. Block pops a path (as a string) and a value from AL
2. Stores them in local register cells `_.path` and `_.value`
3. Uses `!Store.` to write the value into the Store at the specified path

---

## 8. Register Lifetime and Isolation

### The Fundamental Rule: Complete Isolation

**Each block execution creates a fresh, empty Register that is destroyed when the block completes.**

Registers are **completely isolated** between blocks:
- Inner blocks **cannot** see outer block's Register cells
- Parent blocks **cannot** see child block's Register cells
- There is **no lexical scoping** of Registers
- There is **no Register nesting** or inheritance

**If you want to share data between blocks, you must:**
- Use the **Store** (global, persistent state)
- Pass values via the **AL** (stack-based communication)
- Use **CellRefs** to share structure

### Register Lifecycle

When a block begins execution:

1. **Create** a fresh, empty Register
2. Execute the block's tokens
3. **Destroy** the Register completely

### Register Properties

- **Isolated**: No connection to parent/child block Registers
- **Temporary**: Destroyed when block completes
- **Local**: Only visible within the executing block
- **Fresh**: Always starts empty

---

### Example 1: Nested Blocks Have Separate Registers

```soma
{
  1 !_.x
  { 2 !_.x _.x >print } >chain  ; Prints: 2
  _.x >print                     ; Prints: 1
}
```

**Execution trace:**

1. Outer block executes → Creates **Register₁** (empty)
2. `1 !_.x` → Store 1 in Register₁ at path `_.x`
3. `{ 2 !_.x _.x >print }` → Creates a Block value (not executed yet)
4. `>chain` → Execute the inner block
   - Inner block starts → Creates **Register₂** (empty, completely separate)
   - `2 !_.x` → Store 2 in Register₂ at path `_.x`
   - `_.x` → Read Register₂ path `_.x` (value: 2)
   - `>print` → Prints `2`
   - Inner block completes → **Register₂ is destroyed**
5. Back in outer block with Register₁
6. `_.x` → Read Register₁ path `_.x` (still 1)
7. `>print` → Prints `1`

**Key insight:** The inner block's `_.x` and outer block's `_.x` are in **completely different Registers**. They don't interfere with each other at all.

**Output:**
```
2
1
```

---

### Example 2: Inner Block Cannot See Outer Register (ERROR)

```soma
>{1 !_.n >{_.n >print}}  ; FATAL ERROR
```

**What happens:**

1. Outer block executes → Creates Register₁
2. `1 !_.n` → Store 1 in Register₁ at path `_.n`
3. `>{_.n >print}` → Execute inner block
   - Inner block starts → Creates **Register₂** (fresh, empty)
   - `_.n` → Try to read Register₂ at path `_.n`
   - Register₂ has no `_.n` → Resolves to **Void**
   - Push Void onto AL
   - `>print` → Try to execute the path "print" (not `>print`!)
   - Wait, this example needs fixing...

Let me show the correct error case:

```soma
>{1 !_.n >{_.n 10 >+}}  ; Inner block gets Void for _.n
```

**What happens:**

1. Outer block executes → Creates Register₁
2. `1 !_.n` → Store 1 in Register₁ at path `_.n`
3. `>{_.n 10 >+}` → Execute inner block
   - Inner block starts → Creates **Register₂** (fresh, empty)
   - `_.n` → Read Register₂ at path `_.n`
   - Register₂ has no `_.n` → Resolves to **Void**
   - Push Void onto AL
   - `10` → Push 10 onto AL
   - `>+` → Try to add Void and 10 → **FATAL ERROR**

**Key insight:** Inner blocks cannot access outer block's Register cells. Each block sees **only its own Register**.

---

### Example 3: Multiple Nested Blocks, Each Isolated

```soma
{
  1 !_.n                ; Outer Register: _.n = 1

  { 2 !_.n } >chain     ; Inner₁ Register: _.n = 2 (then destroyed)

  _.n >print            ; Outer Register: _.n still = 1

  { 3 !_.n } >chain     ; Inner₂ Register: _.n = 3 (then destroyed)

  _.n >print            ; Outer Register: _.n still = 1
}
```

**Output:**
```
1
1
```

**Key insight:** Each inner block gets its own fresh Register. Neither inner block can affect the outer block's Register, and the two inner blocks don't share a Register either.

---

### ❌ WRONG: Trying to Access Outer Register

```soma
; WRONG - Inner block can't see outer's _.value
{
  42 !_.value
  >{ _.value >print }  ; ERROR: _.value is Void in inner block
}
```

This **fails** because the inner block has its own empty Register.

---

### ✅ RIGHT: Pass Data via AL

```soma
; RIGHT - Pass value through the AL
{
  42 !_.value
  _.value              ; Push onto AL
  >{ >print }          ; Inner block pops from AL and prints
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

### ✅ RIGHT: Share Data via Store

```soma
; RIGHT - Use Store for shared state
{
  42 !shared_value     ; Store in Store (global)
  >{
    shared_value >print  ; Inner reads from Store
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

### ✅ RIGHT: Return Data via AL

```soma
{
  >{ 5 !_.n _.n _.n >* } !_.square  ; Define helper in outer Register

  7 >_.square          ; Call with 7
  >print               ; Prints: 49
}
```

**How it works:**
1. Define `_.square` block in outer Register
2. `7` pushes 7 onto AL
3. `>_.square` executes the block
   - Creates fresh Register₃
   - `!_.n` pops 7 from AL, stores in Register₃
   - `_.n _.n >*` computes 7 × 7 = 49
   - Leaves 49 on AL
   - Register₃ is destroyed
4. Outer block continues with AL = [49]
5. `>print` prints 49

**Key insight:** Blocks communicate via the AL. The inner block receives input from AL and returns output to AL.

---

### Common Pattern: Nested Loop Counters

```soma
{
  0 !_.i                           ; Outer counter

  {
    0 !_.i                         ; Inner counter (different Register!)
    _.i 5 ><
      { _.i 1 >+ !_.i >block >chain }    ; Inner loop uses its own _.i
      { }
    >choose >chain
  } !_.inner_loop

  _.i 3 ><
    {
      >_.inner_loop                ; Call inner loop
      _.i 1 >+ !_.i                ; Increment outer _.i
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
  { !_.x _.x _.x >* } !_.square    ; Helper: square a number
  { !_.x _.x 2 >* } !_.double      ; Helper: double a number

  5 >_.square >print               ; Prints: 25
  5 >_.double >print               ; Prints: 10
}
```

**Key points:**
- Each helper function call gets a fresh Register
- Both `_.square` and `_.double` use `_.x` in their own Registers
- No interference even though both use the same path name
- Complete isolation guarantees safety

---

### Register vs Store vs AL: When to Use Each

| Aspect | Store | Register | AL |
|--------|-------|----------|-----|
| **Scope** | Global | Block-local | Flow-based |
| **Lifetime** | Persistent | Block execution only | Transient |
| **Sharing** | All blocks can access | Isolated per block | Explicit passing |
| **Purpose** | Shared state | Local computation | Data flow |
| **Example** | `config.port` | `_.temp` | Stack operations |

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

The `>block` built-in enables recursion without external state:

```soma
{
  _.n 0 >==
  { 1 }                          ; Base case
  { _.n 1 >- !_.n >block >chain  ; Recursive case
    _.n >* }
  >choose >chain
} !factorial

5 !_.n
factorial >chain >print  ; Prints: 120
```

**How it works:**
1. Check if `_.n == 0`
2. If true, push `1` (base case)
3. If false:
   - Decrement `_.n`
   - Push the current block via `>block`
   - Execute it with `>chain`
   - Multiply the result by current `_.n`

**Important:** Each recursive invocation uses `>block` to reference the same Block value, but with a **completely fresh, isolated Register**.

**Note about this example:** The `_.n` here is in the **outer scope** (before `!factorial`), not in the factorial block's Register. The factorial block reads and writes `_.n` from the Store, not from its Register. If `_.n` were in the Register, it would be destroyed after the first execution, breaking the recursion.

### Corrected Recursive Example (Using Register)

If you want to use Register-local state for recursion, you need to pass state via AL:

```soma
{
  !_.n                           ; Pop initial value into Register
  _.n 0 >==
  { 1 }                          ; Base case: return 1
  {
    _.n 1 >-                     ; Compute n-1
    >block >chain                ; Recursive call with n-1
    _.n >*                       ; Multiply result by original n
  }
  >choose >chain
} !factorial

5 >factorial >print  ; Prints: 120
```

**This works because:**
1. Each recursive call gets its own Register with its own `_.n`
2. The recursive call pops n-1 from AL and stores it in its own `_.n`
3. Results are returned via AL
4. Each level of recursion has isolated state

---

## 9. Blocks Are Not Functions

It is critical to understand that **blocks are fundamentally different from functions**:

| **Functions (Traditional)**       | **Blocks (SOMA)**                    |
|-----------------------------------|--------------------------------------|
| Declare parameters                | No declared parameters               |
| Return a value                    | Leave values on AL                   |
| Create stack frames               | Transform state in-place             |
| Support recursion via call stack  | Support cycles via >block built-in   |
| Hidden execution machinery        | Explicit state transformation        |

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
- **State transformers** – they transform `(AL, Store, Register)` into `(AL', Store', Register')`
- **Self-referential** – every block can reference itself via the `>block` built-in

### The `>block` Built-in (Summary)

**`>block` is a built-in operation that pushes the currently executing block onto the AL.** This enables:

- Self-referential loops
- Recursive computation
- Finite state machines
- Conditional continuation

`>block` is just another built-in (like `>choose` or `>chain`), which means it can be aliased to any name in any language, removing English-centric constraints.

SOMA programs do not reduce. **They run.**

---

## Ambiguities and Open Questions

Based on the specification and errata, the following ambiguities remain:

### 1. **When exactly is a block executed?**

Blocks are executed in the following ways:

- `>chain` executes blocks from the AL
- `>choose` executes the selected block
- **`>path` executes blocks at any path** (Store or Register) — this is now formally defined (see Section 6)

### 2. **Register Isolation (RESOLVED)**

**Question:** What happens during nested execution?

**Answer:** Each block gets a **completely fresh, isolated Register**. Parent Registers are completely inaccessible during nested execution.

```soma
{
  >block !outer_self     ; Store in Store (not Register!)
  { >block !inner_self } >chain
  outer_self >print      ; This works because outer_self is in Store
}
```

**Clarified:**
- **Store writes** during nested execution ARE visible after the nested block completes (Store is global)
- **Register writes** are lost when the nested block ends (Registers are block-local and destroyed)
- Parent and child blocks have **completely separate Registers** with no sharing
- To share data between blocks: use Store (global) or AL (explicit passing)

---

## Conclusion

Blocks are SOMA's answer to functions, procedures, and lambdas—but they reject the abstraction model entirely. They are **values that transform state**, nothing more and nothing less. Understanding blocks means understanding that SOMA doesn't hide mutation under the hood. It makes mutation the foundation of computation.

The `>block` built-in is what makes blocks truly powerful, enabling self-reference without requiring external naming schemes or workarounds. Every block can access itself via `>block`, and that capability is the foundation of control flow in SOMA.
