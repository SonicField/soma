# SOMA v1.0 Language Specification

**State-Oriented Machine Algebra**

## TL;DR

SOMA is a computational model that treats programs as explicit state-transforming machines. Unlike functional languages that begin with a calculus and simulate mutation through abstractions, SOMA starts with the machine itself: mutable state, visible memory, and observable execution. There are no hidden stacks, no return semantics, no exceptions. Instead, computation flows through three structures—the Accumulator List (a stack-like value conduit), the Store (a hierarchical graph of named cells), and the Register (execution-local storage)—transformed by blocks that are values, not functions. SOMA doesn't reduce expressions; it runs programs by evolving state step by step, making mutation the primary semantic domain rather than an impurity to be hidden.

## Hello World

```soma
"Hello world" >print
```

This pushes a string onto the Accumulator List, then executes the `print` block which consumes it.

A more elaborate example showing blocks, the store, and the register:

```soma
{ !_ "Hello " _ >concat >print } !say_hello
"world" >say_hello
```

This creates a block that pops a value into the register, concatenates it with "Hello ", and prints the result. The block is stored under `say_hello`, then invoked with "world" on the stack.

## Implementation Status

**Implemented:** Lexer

**Future:** Parser, Runtime

## Table of Contents

1. [Philosophy](01-philosophy.md) - SOMA's design principles and relationship to other computational models
2. [Lexer](02-lexer.md) - Tokens, literals, paths, and syntactic rules
3. [Machine Model](03-machine-model.md) - The Accumulator List, Store, Registers, and Values
4. [Blocks and Execution](04-blocks-execution.md) - First-class blocks and the execution model
5. [Control Flow](05-control-flow.md) - `>Choose`, `>Chain`, and algebraic flow control
6. [Built-ins](06-builtins.md) - Core operations and their AL contracts
7. [Comparisons](07-comparisons.md) - SOMA vs Forth, Haskell, Lambda Calculus, and others
8. [Examples](08-examples.md) - Working SOMA programs demonstrating key concepts
9. [Errors and Semantics](09-errors-semantics.md) - Fatal errors, abstract machine, and formal grammar

---

*Category: Informational | Version: 1.0 | Date: 16 Nov 2025*
