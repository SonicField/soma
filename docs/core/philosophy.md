# SOMA Philosophy

## State-Oriented Machine Algebra

---

## 1. What SOMA Is

SOMA (State-Oriented Machine Algebra) is a computational model that treats programs as explicit state-transforming machines. It is not a calculus. It does not reduce expressions. Instead, it models computation as it actually unfolds: through observable mutation of explicit state over time.

**Programs run. They do not reduce.**

### State-Oriented vs Calculus-Oriented

Most programming languages begin with a mathematical calculus and then add machinery to simulate the mutable reality of computers. Functional languages like Haskell express state through IO monads, effect types, and elaborate type systems designed to preserve referential transparency while grudgingly accommodating the fact that computers have memory and IO.

SOMA takes the opposite approach:

- **It begins with the machine**: the actual, physical reality of computation
- **It exposes state directly**: mutation is not hidden under abstraction
- **It treats computation as state evolution**: not symbolic reduction

Where a calculus hides mutation under layers of abstraction, SOMA expresses mutation as the primary semantic domain. State is not an "impurity" to be managed. State is fundamental.

### The Machine State

A SOMA program operates on explicit, visible machine state:

1. **The Accumulator List (AL)**: a linear stack-like value conduit for passing data between operations
2. **The Store**: a global, persistent hierarchical graph of identity-bearing cells
3. **The Register**: a block-local, isolated hierarchical graph of cells created fresh for each block execution

That's it. No hidden call stack. No exception handlers. No continuation frames. Everything that happens is visible, explicit, and introspectable.

### State Scope and Lifetime

Each of these three components serves a distinct purpose in SOMA's state model:

**The AL (flow-based):** Values flow through the AL as computation proceeds. The AL is the universal conduit—all operations read from it and write to it. When a block executes, it inherits the current AL state and may modify it for subsequent operations.

**The Store (global, persistent):** The Store is shared state that persists across all block executions. When you write `!config.port`, that value lives in the Store and remains accessible from anywhere, at any time. The Store is how different parts of your program share data.

**The Register (block-local, isolated):** The Register is fundamentally different. Each time a block executes, it receives a completely fresh, empty Register. Inner blocks cannot see outer blocks' Registers. There is no lexical scoping, no nesting, no inheritance—only complete isolation.

### Register Isolation Example

Consider this code:

```soma
>{1 !_.n >{2 !_.n} _.n >print}
```

**What happens:**

1. Outer block executes with fresh Register
2. `1 !_.n` stores 1 in Register
3. `>{2 !_.n}` executes inner block with fresh Register (empty!)
4. `2 !_.n` stores 2 in Register at path `_.n`
5. Inner block completes, Register is destroyed
6. `_.n >print` reads from Register, which still has `_.n = 1`
7. **Prints 1**

The inner block's Register is completely separate. Its `_.n` does not affect the outer block's `_.n`.

If the inner block tried to _read_ the outer's Register, it would fail:

```soma
>{1 !_.n >{_.n >print}}  ; FATAL ERROR
```

The inner block's Register has no `_.n` path, so `_.n` resolves to Void. Trying to execute Void is a fatal error.

**To share data between blocks, you must use:**

- **The Store** (global state): `!data.value` in outer, `data.value` in inner
- **The AL** (explicit passing): push values before calling inner block
- **Return values** via AL: inner block leaves values on AL for outer to consume

This isolation model keeps state boundaries explicit and prevents hidden dependencies.

---

## 2. Core Principles

### State is Fundamental

SOMA rejects the idea that mutable state is impurity. The notion that "pure" computation is superior to "impure" computation is a prejudice born from mathematical foundations that never had to run on silicon.

Real programs mutate memory. SOMA models this directly.

```soma
42 !counter.value
counter.value >print    ; prints 42
```

The state exists. You can see it. You can change it. You can reason about it. This is not a problem to be solved—it is the nature of computation.

### Execution is Dynamic, Not Symbolic

Functional languages reduce expressions according to symbolic rewrite rules. SOMA executes tokens that transform state. There is no expression tree, no substitution model, no reduction semantics.

Consider the difference:

**Haskell** thinks: "The expression `1 + 2` reduces to the value `3` by applying the addition rule."

**SOMA** thinks: "Push 1 onto the AL. Push 2 onto the AL. Execute `>+`, which pops both values and pushes their sum."

SOMA models step-by-step execution. Every operation is a concrete state transition:

```
(AL, Store) → (AL', Store')
```

This is not the lambda calculus. This is a machine algebra.

### Control is Explicit

SOMA has no control stack. No return path. No exception unwinding.

Instead, control arises from two primitive operations:

- **`>choose`**: select one of two values based on a boolean (does NOT execute)
- **`>chain`**: repeatedly execute blocks until a non-block value appears

All control structures—loops, conditionals, recursion, finite state machines—emerge from these primitives acting on explicit state.

```soma
True { (Yes) >print } { (No) >print } >choose >^
```

No hidden jumps. No implicit context. The boolean is on the AL. The blocks are on the AL. `>choose` selects one and discards the other. Then `>^` executes the selected block. That's it.

### Structure is Visible

Memory in SOMA is not a flat array of bytes. It is a graph of named, aliasable cells. You can inspect it. You can mutate it. You can create cycles. You can share structure.

```soma
99 !a.b
a.b. !x.y
x.y >print      ; prints 99
```

The cell at `a.b` is aliased from `x.y`. This is not pointer arithmetic—it is structural identity preserved across multiple paths.

### Blocks Are Not Functions

SOMA has blocks. They look like lambdas, but they are not.

A function:

- Has arity
- Returns a value
- Creates a stack frame
- Has lexical scope

A SOMA block:

- Has no arity (consumes whatever it needs from the AL)
- Does not return (leaves new values on the AL)
- Does not create a stack frame
- Gets a fresh, isolated Register on each execution

Blocks are **state transformers**. They act upon the machine state and leave it changed.

```soma
{ >dup >* } !square
5 >square >print    ; prints 25
```

`square` is not a function. It is a sequence of tokens that transforms state.

**Each time a block executes, it gets a brand new Register.** The Register exists only during that block's execution and is destroyed when the block completes. This means blocks cannot rely on outer block Register values—they must receive data via the AL or Store.

### Execution is Explicit

In SOMA, blocks are values until you explicitly execute them. This is fundamental to how the language works.

The `>` prefix modifier makes execution explicit:

```soma
print           ; Pushes the print block onto the AL (it's a value)
>print          ; Executes the print block (it's an operation)
```

When you write `>path`, you are saying: "read the value at this path and execute it." This is an atomic operation--not two separate steps, but a single unified action.

This applies to any path:

```soma
>print          ; Execute block at Store path "print"
>my_func        ; Execute block at Store path "my_func"
>_.action       ; Execute block at Register path "_.action"
```

**Built-ins are just blocks.** When you write `>print`, `>dup`, or `>+`, you are executing blocks stored at Store paths. There is no special "built-in" syntax--they are simply pre-populated Store entries.

This design enables powerful patterns. You can store blocks and execute them later:

```soma
{ (Hello) >print } !greet
>greet          ; Executes the stored block
```

You can also execute block literals directly with `>{ }`:

```soma
>{ 1 2 >+ >print }    ; Execute block immediately
```

This is cleaner than the older pattern `{ 1 2 >+ >print } >chain` for single execution.

The standard library defines `>^` which executes the top value from the AL:

```soma
{ !_ >_ } !^              ; Store this block as "^"
(Data) print >^           ; Pushes "Data", pushes print block, executes it
```

This enables macro-like behavior from simple primitives. The `>^` operator is similar to Forth's `EXECUTE` or Lisp's `FUNCALL`.

**Three ways to execute:**

1. **`>path`**: Execute a block stored at a path
2. **`>{ code }`**: Execute a block literal directly
3. **`>^`**: Execute a block from the AL (useful when blocks are computed)

The separation between values and execution is what makes SOMA's control structures algebraic rather than syntactic. Blocks flow through the AL as data until explicitly executed.

---

## 3. Design Philosophy

### Why Explicit Mutation?

Because that's what computers do. Every program you run mutates registers, cache lines, RAM, disk. Pretending otherwise requires building elaborate abstractions--monads, lenses, zippers, free structures--to encode something that hardware does natively.

SOMA says: let's model what actually happens.

Mutation in SOMA is:

- **Visible**: you can always see the Store
- **Explicit**: every write uses `!`
- **Controlled**: structure and identity are first-class

You do not fight the machine. You work with it.

### Why No Call Stack?

Call stacks are a fiction. They make sense in the context of function calls and return values, but SOMA has neither.

A block executes. When it finishes, execution continues with the next token. There is no "return to caller" because there was no "call" in the first place--only state transformation.

This eliminates:

- Stack overflow from deep recursion
- Hidden control flow through exception propagation
- Confusion about scope and shadowing

Instead, you build control graphs explicitly using `>chain`:

```soma
{ _.self (tick) >print _.self } >chain
```

This block prints "tick" and then returns itself to `>chain`, which executes it again. Forever. No stack growth. No tail call optimization needed--it's built into the execution model.

**`>chain`** is the key to tail-call optimization. It pops from the AL and:

- If the value is a Block, executes it and repeats
- If the value is anything else, stops and leaves it on the AL

This makes tail-recursive patterns natural and efficient:

```soma
) Countdown from 10
10 !counter
{
  counter >toString >print
  counter 1 >- !counter

  counter 0 >>
    _.self          ; Continue: return this block
    Nil             ; Stop: return Nil
  >choose
} !countdown

countdown >chain    ; No stack growth!
```

**Functional elegance with imperative mutation:** SOMA combines the best of both worlds. The control flow is functional (blocks returning blocks), but the state mutation is explicit and visible. You can see exactly what changes and when, while still writing clean tail-recursive loops.

### Why the AL?

The Accumulator List serves as the universal conduit for values. It is:

- ****Simple****: LIFO, no random access
- ****Explicit****: you always know what's on it
- ****Sufficient****: all computation flows through it

It replaces:

- Function arguments
- Return values
- Expression evaluation order
- Temporary variables

You could build SOMA with just the Store, but the AL provides a minimal amount of dynamic structure without sacrificing clarity.

### Functional Elegance with Imperative Mutation

SOMA achieves a unique synthesis: **functional control flow with imperative state**.

Traditional approaches force a choice:

- **Functional languages** (Haskell, ML) hide mutation under monads and abstractions
- **Imperative languages** (C, Python) hide control flow under syntax keywords

SOMA rejects this false dichotomy. Instead:

**Control flow is functional:** Blocks return values. `>choose` selects between alternatives. `>chain` implements tail-call optimization. Loops are just blocks returning themselves.

**State mutation is imperative:** The Store is explicitly mutated with `!`. You can see what changes, when it changes, and where it lives.

This combination provides:

- ****Clarity of mutation****: no hidden state transformations
- ****Elegance of tail calls****: no stack growth, pure data flow
- ****Simplicity of primitives****: both aspects emerge from minimal operations

Example - tail-recursive factorial with accumulator:

```soma
5 !fact.n
1 !fact.acc

{
  fact.n 0 >=<
    fact.acc                    ; Base: return accumulator (stops chain)
    {                           ; Recursive: mutate and continue
      fact.acc fact.n >* !fact.acc
      fact.n 1 >- !fact.n
      _.self                    ; Return self (continues chain)
    }
  >choose
} !fact-step

fact-step >chain                ; AL: [120]
```

**What's happening:**

- **Functional:** Block returns either `fact.acc` (number, stops) or `_.self` (block, continues)
- **Imperative:** State clearly mutates via `!fact.acc` and `!fact.n`
- **Efficient:** No stack frames, just tail calls through `>chain`

You can trace every mutation. You can see the control flow. There are no hidden mechanics. This is SOMA's philosophical core: computation made visible through the marriage of functional structure and imperative clarity.

### Comparing the Three State Spaces

| Aspect         | Store                    | Register                        | AL                           |
|----------------|--------------------------|---------------------------------|------------------------------|
| Scope          | Global                   | Block-local                     | Flow-based                   |
| Lifetime       | Persistent               | Single block execution          | Transient                    |
| Sharing        | All blocks can access    | Isolated per block              | Inherited by nested blocks   |
| Purpose        | Shared, persistent state | Local computation scratch space | Data flow between operations |
| Example        | `config.port`            | `_.temp`                        | Stack operations             |
| Access pattern | By path                  | By path )within block only)     | Push/pop                     |

**When to use each:**

- **Store**: Configuration, shared data, persistence across block executions
- **Register**: Temporary local variables, loop counters within a block, `_.self` reference
- **AL**: Passing arguments to blocks, returning values from blocks, intermediate computation results

---

## 4. A Motivating Example

Let's implement a simple counter that prints numbers until it reaches a limit.

### SOMA Version

```soma
0 !counter.n
5 !counter.limit

{
  counter.n >toString >print
  counter.n 1 >+ !counter.n

  counter.n counter.limit >>
  { Nil }           ; Stop: return Nil to terminate chain
  { _.self }        ; Continue: return self to continue chain
  >choose
} !counter-loop

counter-loop >chain
```

**What happens:**

1. Initialize counter and limit in the StoreDefine a block that:
  - Prints current valueIncrements counterChecks if counter exceeds limitUses `>choose` to select which value to return
  - If yes, returns Nil )terminates chain)
  - If no, returns self )continues chain)
2. Execute the block with `>chain`

No recursion. No stack frames. No return values. Just state evolution through tail-call optimization.

**This is functional elegance:** The loop control is purely functional )blocks returning blocks), but the state mutation is explicit and imperative )Store updates with `!`). You get the clarity of mutation with the efficiency of tail calls.

### Haskell Version

```haskell
counter :: Int -> Int -> IO ))
counter n limit
  | n > limit = return ))
  | otherwise = do
      print n
      counter )n + 1) limit

main :: IO ))
main = counter 0 5
```

**Differences:**

| Aspect          | Haskell                        | SOMA                               |
|-----------------|--------------------------------|------------------------------------|
| State           | Passed as function parameters  | Stored explicitly in the Store     |
| Control         | Recursive function calls       | Explicit block chaining            |
| Stack           | Grows with recursion depth     | No stack                           |
| Purity          | IO monad separates pure/impure | Everything is state transformation |
| Execution model | Expression reduction           | Token-by-token state mutation      |

Haskell works hard to preserve the illusion of purity. SOMA simply describes what the machine does.

### Python Version

```python
counter = {"n": 0, "limit": 5}

while counter["n"] <= counter["limit"]:
    print)counter["n"])
    counter["n"] += 1
```

**Differences:**

| Aspect                                                                                | Python                          | SOMA                 |
|---------------------------------------------------------------------------------------|---------------------------------|----------------------|
| SyntaxImplicit control structures )`while`)                                           | Explicit block selection        |                      |
| Stack                                                                                 | Hidden call stack for functions | No call stack        |
| State visibility                                                                      | Variables and objects           | Explicit Store paths |
| Control flowKeywords )`if`, `while`, `for`)Algebraic operations )`>choose`, `>chain`) |                                 |                      |

Python hides the control machinery behind syntax. SOMA makes it explicit through state.

---

## 5. What SOMA Is Not

### Not a Better Lambda Calculus

Lambda calculus is stateless, referentially transparent, and based on substitution. SOMA is stateful, procedurally mutable, and based on state transitions. They are orthogonal models.

### Not a Scripting Language

SOMA has no special syntax for common patterns. It is minimal by design. You build what you need from primitives.

### Not Optimized for Convenience

SOMA prioritizes clarity and explicitness over syntactic sugar. Every operation is visible. Every transformation is explicit.

### Not a Type System Laboratory

SOMA is dynamically typed. Values have types, but the Store and AL do not enforce them statically. Type errors are runtime errors.

---

## 6. SOMA as a Teaching Tool

SOMA reveals how programs actually execute. It is pedagogically valuable because:

1. **No hidden machinery**: everything that happens is visible
2. **State is explicit**: students see mutation, aliasing, sharing
3. **Control is algebraic**: not buried in syntax
4. **Execution is observable**: you can trace every step

Students learning SOMA understand:

- What a stack is (the AL)
- What memory is (the Store)
- What execution is (state transformation)
- What control flow is (block selection and chaining)

There are no magic keywords. No implicit behaviors. No "just trust the compiler."

---

## 7. SOMA in Context

### Where Forth is minimalist syntax over a stack...

SOMA is structured state with algebraic control.

### Where Haskell is purity enforced through types...

SOMA is mutation expressed as the foundation.

### Where Lisp is code as data...

SOMA is state as the program.

### Where Turing Machines are one symbol at a time...

SOMA is structured graphs at arbitrary depth.

---

## Conclusion

SOMA does not try to be a better Haskell or a safer C or a faster Python. It tries to be an honest description of what computers do: transform state, step by step, without hidden mechanisms.

But it also reveals something deeper: **functional elegance and imperative clarity are not opposites.** They are complementary perspectives on computation. SOMA shows how they can coexist:

- ****Control flow****:  is functional - blocks as values, tail-call optimization, algebraic composition
- ****State mutation****:  is imperative - visible writes, explicit paths, observable changes
- ****Execution****:  is explicit - no hidden machinery, no implicit behaviors

If you want to understand how programs run—not how they reduce, not how they type-check, but how they **run**—SOMA shows you the machine. And it shows you that the machine can be both elegant and explicit.

No call stack. No exceptions. No false dichotomy between purity and mutation. Just state, blocks, and explicit flow.

**This is computation as it is, not as we wish it were.**

---

### Further Reading

- **Section 2: Core Concepts** - Details on AL, Store, Registers, and Cells
- **Section 8: Blocks and Execution** - How blocks work without being functions
- **Section 10: Logical Control Flow** - `>choose` and `>chain` in depth
- **Section 18: SOMA in Context** - Comparisons with other computational models


