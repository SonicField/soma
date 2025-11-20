# SOMA Philosophy
## State-Oriented Machine Algebra

---

## 1. What SOMA Is

SOMA (State-Oriented Machine Algebra) is a computational model that treats programs as explicit state-transforming machines. It is not a calculus. It does not reduce expressions. Instead, it models computation as it actually unfolds: through observable mutation of explicit state over time.

**Programs run. They do not reduce.**

### State-Oriented vs Calculus-Oriented

Most programming languages begin with a mathematical calculus and then add machinery to simulate the mutable reality of computers. Functional languages like Haskell express state through IO monads, effect types, and elaborate type systems designed to preserve referential transparency while grudgingly accommodating the fact that computers have memory and IO.

SOMA takes the opposite approach:

- **It begins with the machine** - the actual, physical reality of computation
- **It exposes state directly** - mutation is not hidden under abstraction
- **It treats computation as state evolution** - not symbolic reduction

Where a calculus hides mutation under layers of abstraction, SOMA expresses mutation as the primary semantic domain. State is not an "impurity" to be managed. State is fundamental.

### The Machine State

A SOMA program operates on explicit, visible machine state:

1. **The Accumulator List (AL)** - a linear stack-like value conduit
2. **The Store** - a hierarchical graph of identity-bearing cells
3. **The Register** - execution-local hierarchical graph of cells

That's it. No hidden call stack. No exception handlers. No continuation frames. Everything that happens is visible, explicit, and introspectable.

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

- **`>Choose`** - select and execute one of two blocks based on a boolean
- **`>Chain`** - repeatedly execute blocks until a non-block value appears

All control structures—loops, conditionals, recursion, finite state machines—emerge from these primitives acting on explicit state.

```soma
True { "Yes" >print } { "No" >print } >Choose
```

No hidden jumps. No implicit context. The boolean is on the AL. The blocks are on the AL. `>Choose` executes one and discards the other. That's it.

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

A SOMA block:
- Has no arity (consumes whatever it needs from the AL)
- Does not return (leaves new values on the AL)
- Does not create a stack frame

Blocks are **state transformers**. They act upon the machine state and leave it changed.

```soma
{ >dup >* } !square
5 >square >print    ; prints 25
```

`square` is not a function. It is a sequence of tokens that transforms state.

### Execution is Explicit

In SOMA, blocks are values until you explicitly execute them. This is fundamental to how the language works.

The `>` prefix modifier makes execution explicit:

```soma
print           ; Pushes the print block onto the AL (it's a value)
>print          ; Executes the print block (it's an operation)
```

When you write `>path`, you are saying: "read the value at this path and execute it." This is an atomic operation—not two separate steps, but a single unified action.

This applies to any path:

```soma
>print          ; Execute block at Store path "print"
>my_func        ; Execute block at Store path "my_func"
>_.action       ; Execute block at Register path "_.action"
```

**Built-ins are just blocks.** When you write `>print`, `>dup`, or `>+`, you are executing blocks stored at Store paths. There is no special "built-in" syntax—they are simply pre-populated Store entries.

This design enables powerful patterns. You can store blocks and execute them later:

```soma
{ (Hello) >print } !greet
>greet          ; Executes the stored block
```

You can even define user-defined execution operators. For example, `{ !_ >_ } !^` creates an operator that executes the top of the AL, similar to Forth's `EXECUTE` or Lisp's `FUNCALL`. This enables macro-like behavior from simple primitives:

```soma
{ !_ >_ } !^              ; Define "execute AL top"
(Data) print >^           ; Prints "Data"
```

The separation between values and execution is what makes SOMA's control structures algebraic rather than syntactic. Blocks flow through the AL as data until explicitly executed with `>`.

---

## 3. Design Philosophy

### Why Explicit Mutation?

Because that's what computers do. Every program you run mutates registers, cache lines, RAM, disk. Pretending otherwise requires building elaborate abstractions—monads, lenses, zippers, free structures—to encode something that hardware does natively.

SOMA says: let's model what actually happens.

Mutation in SOMA is:
- **Visible** - you can always see the Store
- **Explicit** - every write uses `!`
- **Controlled** - structure and identity are first-class

You do not fight the machine. You work with it.

### Why No Call Stack?

Call stacks are a fiction. They make sense in the context of function calls and return values, but SOMA has neither.

A block executes. When it finishes, execution continues with the next token. There is no "return to caller" because there was no "call" in the first place—only state transformation.

This eliminates:
- Stack overflow from deep recursion
- Hidden control flow through exception propagation
- Confusion about scope and shadowing

Instead, you build control graphs explicitly:

```soma
{ _.self "tick" >print _.self } >Chain
```

This block prints "tick" and then re-executes itself. Forever. No stack growth. No tail call optimization needed. Just explicit state.

### Why the AL?

The Accumulator List serves as the universal conduit for values. It is:
- Simple (LIFO, no random access)
- Explicit (you always know what's on it)
- Sufficient (all computation flows through it)

It replaces:
- Function arguments
- Return values
- Expression evaluation order
- Temporary variables

You could build SOMA with just the Store, but the AL provides a minimal amount of dynamic structure without sacrificing clarity.

---

## 4. A Motivating Example

Let's implement a simple counter that prints numbers until it reaches a limit.

### SOMA Version

```soma
0 !counter.n
5 !counter.limit

{
  counter.n >print
  counter.n 1 >+ !counter.n

  counter.n counter.limit >>
  { {} }
  { _.self }
  >Choose
} >Chain
```

**What happens:**
1. Initialize counter and limit in the Store
2. Define a block that:
   - Prints current value
   - Increments counter
   - Checks if counter exceeds limit
   - If yes, push empty block (terminates Chain)
   - If no, push self (continues Chain)
3. Execute the block with `>Chain`

No recursion. No stack frames. No return values. Just state evolution.

### Haskell Version

```haskell
counter :: Int -> Int -> IO ()
counter n limit
  | n > limit = return ()
  | otherwise = do
      print n
      counter (n + 1) limit

main :: IO ()
main = counter 0 5
```

**Differences:**

| Aspect | Haskell | SOMA |
|--------|---------|------|
| **State** | Passed as function parameters | Stored explicitly in the Store |
| **Control** | Recursive function calls | Explicit block chaining |
| **Stack** | Grows with recursion depth | No stack |
| **Purity** | IO monad separates pure/impure | Everything is state transformation |
| **Execution model** | Expression reduction | Token-by-token state mutation |

Haskell works hard to preserve the illusion of purity. SOMA simply describes what the machine does.

### Python Version

```python
counter = {"n": 0, "limit": 5}

while counter["n"] <= counter["limit"]:
    print(counter["n"])
    counter["n"] += 1
```

**Differences:**

| Aspect | Python | SOMA |
|--------|--------|------|
| **Syntax** | Implicit control structures (`while`) | Explicit block selection |
| **Stack** | Hidden call stack for functions | No call stack |
| **State visibility** | Variables and objects | Explicit Store paths |
| **Control flow** | Keywords (`if`, `while`, `for`) | Algebraic operations (`>Choose`, `>Chain`) |

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

1. **No hidden machinery** - everything that happens is visible
2. **State is explicit** - students see mutation, aliasing, sharing
3. **Control is algebraic** - not buried in syntax
4. **Execution is observable** - you can trace every step

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

If you want to understand how programs run—not how they reduce, not how they type-check, but how they **run**—SOMA shows you the machine.

No call stack. No exceptions. No purity. Just state, blocks, and explicit flow.

**This is computation as it is, not as we wish it were.**

---

### Further Reading

- **Section 2: Core Concepts** - Details on AL, Store, Registers, and Cells
- **Section 8: Blocks and Execution** - How blocks work without being functions
- **Section 10: Logical Control Flow** - `>Choose` and `>Chain` in depth
- **Section 18: SOMA in Context** - Comparisons with other computational models
