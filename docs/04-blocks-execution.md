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
- Used in control flow (`>Choose`, `>Chain`)
- Executed via built-ins or path execution

### Example: Storing and Reusing a Block

```soma
{ >dup >* } !square

7 square >Chain >print
```

**Output:** `49`

Here:
1. A block is created and stored in the Cell `square`
2. The integer `7` is pushed onto the AL
3. The block stored at `square` is retrieved and executed via `>Chain`
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

3 4 add_two_numbers >Chain
; AL now contains [7]
```

The block `add_two_numbers` doesn't declare "I take two integers." It simply executes `>+`, which consumes two values from the AL. If fewer than two values are present, execution fails fatally.

### Example: A Block That Leaves Multiple Values

```soma
{ 1 2 3 } !push_three

push_three >Chain
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
7 square >Chain
```

Here:
- No stack frame is created
- The value `7` is already on the AL
- A new Register is created for the block's execution
- The block reads and transforms the AL in-place
- When the block ends, execution continues linearly and the Register is destroyed

---

## 5. The _.self Binding

### Automatic Binding Rule

**When a Block begins execution, the SOMA runtime automatically creates a Register Cell at path `_.self` containing the Block value being executed.** This binding is local to the execution context and is destroyed when the Block completes.

This is a **core semantic feature** of SOMA, enabling self-referential blocks without requiring external naming or storage.

### Formal Definition

When Block B begins execution:

1. A new Register is created for this execution context
2. A Cell is automatically created at Register path `_.self`
3. The Cell's payload is set to the Block value B
4. During execution, `_.self` resolves to this Block value
5. When execution ends, the Register (including `_.self`) is destroyed

### Type and Scope

- `_.self` is a **Register path** (starts with `_`)
- Accessing it yields a **Block value** (not a CellRef)
- Can be pushed onto AL, stored, or passed like any Block
- Local to the currently executing Block
- **Nested blocks get their own `_.self`** (pointing to their Block, not parent's)

### Example: Infinite Loop

```soma
{ _.self >Chain }
```

**How it works:**
1. Block begins execution
2. `_.self` is automatically bound to this block
3. `_.self` is pushed onto the AL
4. `>Chain` executes the block (which is on top of AL)
5. The cycle repeats indefinitely

This creates an infinite loop without any external naming or storage.

### Example: Nested Blocks Each Get Their Own _.self

```soma
{
  "Outer block executing" >print
  _.self !outer_self

  {
    "Inner block executing" >print
    _.self !inner_self
  } >Chain

  outer_self inner_self >==
  { "DIFFERENT blocks" }
  { "SAME block (impossible)" }
  >Choose >Chain >print
}
```

**Output:**
```
Outer block executing
Inner block executing
DIFFERENT blocks
```

**How it works:**
1. Outer block executes, `_.self` is bound to the outer Block
2. Outer Block stores its `_.self` in `outer_self`
3. Inner block executes, `_.self` is **rebound** to the inner Block
4. Inner Block stores its `_.self` in `inner_self`
5. The two blocks are compared and found to be different

**Key insight:** Each block execution context has its own `_.self` binding. Nested execution creates a new binding that shadows the parent's binding for the duration of the inner block.

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
square >Chain       ; Two operations: push, then execute

; Pattern 2: Execute directly
>square             ; One atomic operation: read-and-execute
```

**When the path contains a Block, these are usually equivalent.** But `>path` is the direct, atomic form.

**The key distinction:**

```soma
square          ; Pushes the Block value onto AL
>square         ; Executes the Block (nothing pushed onto AL)
```

### Self-Execution via `>_.self`

The automatic `_.self` binding can be executed with `>`:

```soma
{
  (Loop iteration) >print
  >_.self           ; Execute this block again (infinite loop)
}
```

**How it works:**
1. The Block prints a message
2. `>_.self` executes the Block again
3. This creates an infinite loop

**More practical: Conditional self-execution:**

```soma
{
  _.counter 1 >+ !_.counter
  _.counter >print
  _.counter 10 ><
    { >_.self }     ; Continue if counter < 10
    { }             ; Stop otherwise
  >Choose >Chain
} !count_to_ten

0 !_.counter
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
- Enables self-execution via `>_.self`
- Foundation for user-defined execution patterns

The `>` modifier is what makes SOMA's execution model explicit and first-class. Blocks are values until you explicitly execute them.

---

## 7. Examples

### Example 1: Block as a Value

```soma
{ "Hello" >print } !greet

greet >Chain
```

**Output:** `Hello`

The block is stored, then retrieved and executed.

---

### Example 2: Block Consuming and Producing AL Values

```soma
{ !_.x !_.y _.x _.y >+ } !add_named

3 7 add_named >Chain
; AL = [10]
```

**How it works:**
1. Block pops two values and stores them in local register cells `_.x` and `_.y`
2. Pushes both back onto the AL
3. Adds them with `>+`
4. Leaves the result on the AL

---

### Example 3: Block Passed as an Argument

```soma
{ !_.action _.action >Chain } !do_it

{ "Action executed" >print } do_it >Chain
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
    { _.self }
    { }
  >Choose >Chain
} !count_to_ten

0 !_.counter
count_to_ten >Chain
```

**Output:** `1 2 3 4 5 6 7 8 9 10`

**How it works:**
1. Block increments and prints `_.counter`
2. Checks if `_.counter < 10`
3. If true, pushes `_.self` (the block itself) back onto the AL
4. If false, pushes an empty block `{}`
5. `>Chain` continues execution as long as a Block is on top of AL
6. When `_.counter` reaches 10, the empty block is executed and the loop terminates

**Note:** The register path `_.counter` is local to the block's execution context and persists across recursive invocations via the Store binding `count_to_ten`.

---

### Example 5: Finite State Machine

```soma
True !state

{
  state
  { False !state "Switched to OFF" >print _.self }
  { True !state "Switched to ON" >print _.self }
  >Choose
} !toggle

toggle >Chain
```

**Output:** Alternates between `Switched to OFF` and `Switched to ON` forever.

**How it works:**
1. The block reads `state` from the Store
2. Uses `>Choose` to select between two blocks
3. Each block updates `state` and pushes `_.self` back onto the AL
4. `>Chain` continues execution indefinitely

---

### Example 6: Conditional Recursion Pattern

```soma
{
  _.condition
  { _.self }    ; Recurse if true
  { }           ; Terminate if false
  >Choose >Chain
} !loop_while_true
```

This is the fundamental pattern for loops in SOMA:
- Test a condition
- If true, push `_.self` to continue
- If false, push empty block to terminate
- `>Chain` executes whatever's on top of the AL

---

### Example 7: Block That Transforms Store

```soma
{ !_.value !_.path _.value _.path !Store. } !store_at

42 "answer" store_at >Chain
; Cell at Store path `answer` now contains 42
```

**How it works:**
1. Block pops a path (as a string) and a value from AL
2. Stores them in local register cells `_.path` and `_.value`
3. Uses `!Store.` to write the value into the Store at the specified path

---

## 8. Register Lifetime and Nested Execution

### Register Creation and Destruction

Each block execution creates a fresh Register:

```soma
{
  1 !_.x
  { 2 !_.x _.x >print } >Chain  ; Prints: 2
  _.x >print                     ; Prints: 1
}
```

**How it works:**
1. Outer block creates Register₁ with `_.x = 1`
2. Inner block creates Register₂ with `_.x = 2`
3. Inner block prints its own `_.x` (value: 2)
4. Inner block completes, Register₂ is destroyed
5. Outer block prints its own `_.x` (value: 1)

**Key insight:** Registers are **stack-allocated** even though SOMA has no call stack. They are scoped to block execution, not to a call frame.

### Recursive Self-Reference

The `_.self` binding enables recursion without external state:

```soma
{
  _.n 0 >==
  { 1 }                          ; Base case
  { _.n 1 >- !_.n _.self >Chain  ; Recursive case
    _.n >* }
  >Choose >Chain
} !factorial

5 !_.n
factorial >Chain >print  ; Prints: 120
```

**How it works:**
1. Check if `_.n == 0`
2. If true, push `1` (base case)
3. If false:
   - Decrement `_.n`
   - Push `_.self` (the factorial block)
   - Execute it with `>Chain`
   - Multiply the result by current `_.n`

**Note:** Each recursive invocation gets its own `_.self` binding pointing to the same Block value, but with a fresh Register.

---

## 9. Blocks Are Not Functions

It is critical to understand that **blocks are fundamentally different from functions**:

| **Functions (Traditional)**       | **Blocks (SOMA)**                    |
|-----------------------------------|--------------------------------------|
| Declare parameters                | No declared parameters               |
| Return a value                    | Leave values on AL                   |
| Create stack frames               | Transform state in-place             |
| Support recursion via call stack  | Support cycles via _.self reference  |
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
- **Self-aware** – every block has access to itself via the automatic `_.self` binding

### The _.self Binding (Summary)

**When a Block begins execution, `_.self` is automatically bound to the Block value being executed.** This is a core semantic feature that enables:

- Self-referential loops
- Recursive computation
- Finite state machines
- Conditional continuation

Nested blocks each receive their own `_.self` binding, ensuring clean scoping and preventing interference between execution contexts.

SOMA programs do not reduce. **They run.**

---

## Ambiguities and Open Questions

Based on the specification and errata, the following ambiguities remain:

### 1. **When exactly is a block executed?**

Blocks are executed in the following ways:

- `>Chain` executes blocks from the AL
- `>Choose` executes the selected block
- **`>path` executes blocks at any path** (Store or Register) — this is now formally defined (see Section 6)

### 2. **What happens to parent's _.self during nested execution?**

If block A executes block B, we know B gets its own `_.self` binding. But:
- Does A's `_.self` remain accessible in A's Register?
- Is it shadowed, or is it in a different scope entirely?

The specification suggests each block gets a **completely fresh Register**, which would mean parent registers are inaccessible during nested execution. This implies:

```soma
{
  _.self !outer_self
  { _.self !inner_self } >Chain
  outer_self >print  ; Is outer_self accessible here?
}
```

**Clarification needed:** Are Store writes during nested execution visible after the nested block completes? (Answer: Yes, because the Store is global.) But are Register writes lost when the nested block ends? (Answer: Yes, because Registers are local to execution context.)

---

## Conclusion

Blocks are SOMA's answer to functions, procedures, and lambdas—but they reject the abstraction model entirely. They are **values that transform state**, nothing more and nothing less. Understanding blocks means understanding that SOMA doesn't hide mutation under the hood. It makes mutation the foundation of computation.

The automatic `_.self` binding is what makes blocks truly powerful, enabling self-reference without requiring external naming schemes or workarounds. Every block knows itself, and that self-knowledge is the foundation of control flow in SOMA.
