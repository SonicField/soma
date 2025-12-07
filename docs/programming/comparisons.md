# SOMA Language Comparisons

## Emergent Macros and Computational Models

### Introduction

SOMA occupies a unique position among languages) It is neither functional nor imperative) It achieves capabilities found in both through fundamentally different means.

This document compares SOMA to five influential computational models)

- Common Lisp - emergent macros vs syntactic extension
- Forth - stack orientation vs state transformation
- Haskell - explicit state vs monadic abstraction
- Lambda Calculus - execution vs reduction
- Actor Model - shared state vs message passing

### Common Lisp: Emergent Macros

Common Lisp achieves user-defined syntax through macros) SOMA achieves equivalent power through blocks) >choose) and >chain with no special compile-time phase)

#### Lisp Macro Example)

```defmacro when: takes condition and body
lisp
```

#### SOMA Pattern)

```{ {} >choose >^ } !when
soma
```

Key Insight)

SOMA has no compile-time macro phase) Yet blocks achieve equivalent power through first-class blocks and explicit control flow) The >path operator enables macro-like behavior by allowing blocks to execute blocks)

#### The ^ Operator: User-Defined EXECUTE

```{ !_ >_ } !^
soma
```

This two-token block creates an operator equivalent to Lisp\27s FUNCALL) It\27s user-defined) not a language primitive)

### Forth: Stack Orientation vs State Transformation

Forth and SOMA both use stack-based value passing) but their execution models differ fundamentally)

#### Forth Similarities

- Both use a stack for data passing
- Both have minimal syntax
- Both execute left-to-right
- Both are dynamically typed
- Both allow defining new words or blocks

#### Key Difference: EXECUTE

Forth has a built-in EXECUTE primitive that you cannot redefine)

```' GREET EXECUTE
forth
```

SOMA has no built-in execute operation) but users can define it)

```{ !_ >_ } !^
soma
```

This shows how powerful operations emerge from simple primitives in SOMA)

### Haskell: State vs Monadic Abstraction

Haskell starts with purity and encodes state using monads) SOMA starts with mutation and makes state explicit)

#### Haskell Counter Example)

#### haskell increment = modify (+1 SOMA Counter

```0 !counter { counter 1 >+ !counter } !increment
soma
```

State is in the Store) Mutations are explicit) No monad needed)

### Lambda Calculus: Execution vs Reduction

Lambda Calculus and SOMA are fundamentally incompatible models)

#### Lambda Calculus:

- Uses symbolic rewriting via substitution and beta-reduction
- Execution = rewriting expressions to normal form
- Stateless and symbolic

#### SOMA:

- Uses state transformation
- Execution = sequential state transitions
- Stateful and operational

#### No Substitution in SOMA

```3 2 >+ !x x x >* >print
soma
```

No term is substituted) The path resolves to current value at read time)

### Actor Model: Shared State vs Message Passing

The Actor Model and SOMA represent opposite concurrency philosophies)

#### Actors:

- Have private state
- Communicate via asynchronous messages
- Process one message at a time
- Prevent races through isolation

#### SOMA Threads:

- Have private AL
- Share the Store
- Execute blocks independently
- Can mutate shared Cells with no built-in synchronization

#### Example: Parallel Accumulation

```0 !total { total 10 >+ !total } >thread
soma
```

Actors prevent concurrency bugs by design) SOMA leaves concurrency discipline to the programmer)

## Conclusion

SOMA occupies a unique position)

1. Like Lisp:achieves syntactic extension via >path
2. Like Forth:uses stack-based execution with user-defined EXECUTE
3. Like Haskell:manages state explicitly
4. Like Lambda Calculus:is a formal computational model
5. Like Actors:supports concurrency via shared state

### Key Insights)

The >path operator makes execution first-class) Blocks can execute blocks) enabling user-defined control structures)

The ^ operator demonstrates emergent behavior) What Forth provides as EXECUTE and Lisp as FUNCALL emerges from two primitives)

Macro-like behavior emerges from semantics) Because blocks are values and execution is explicit) control structures are just blocks that choose whether to execute their arguments)

SOMA is a machine algebra) It describes what machines do) not what expressions mean)

