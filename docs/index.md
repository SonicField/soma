# SOMA v1.1 Language Specification

**State-Oriented Machine Algebra**

## TL;DR

SOMA is a computational model that treats programs as explicit state-transforming machines. Unlike functional languages that begin with a calculus and simulate mutation through abstractions, SOMA starts with the machine itself: mutable state, visible memory, and observable execution. There are no hidden stacks, no return semantics, no exceptions. Instead, computation flows through three structures—the Accumulator List (a stack-like value conduit), the Store (a hierarchical graph of named cells), and the Register (execution-local storage)—transformed by blocks that are values, not functions.

**Core Philosophy:**
- **Blocks are first-class values** — code is data, execution is explicit via `>`
- **`>choose` selects, doesn't execute** — selector-based branching (choose + `>^` to execute)
- **`>chain` enables tail-call optimization** — loops and recursion without stack growth
- **Clean execution patterns** — `>func` from paths, `>{ }` for literals, `>^` from AL
- **Functional elegance meets imperative clarity** — algebraic control flow with visible state

SOMA doesn't reduce expressions; it runs programs by evolving state step by step, making mutation the primary semantic domain rather than an impurity to be hidden.

## Hello World

```soma
(Hello world) >print
```

This pushes a string onto the Accumulator List, then executes the `print` block which consumes it.

A more elaborate example showing blocks, execution patterns, and state:

```soma
{ !_.name (Hello ) _.name >concat >print } !greet
(world) >greet
```

This creates a block that pops a value into Register storage, concatenates it with "Hello ", and prints the result. The block is stored at Store path `greet`, then executed with "world" on the stack.

**Key execution patterns:**

```soma
>func           ) Execute block from Store/Register path
>{ code }       ) Execute block literal immediately (cleaner than { code } >chain)
block >^        ) Execute block from AL (like Forth's EXECUTE, user-defined!)
block >chain    ) Execute and continue tail-calls/loops (no stack growth)
```

## Implementation Status

**✅ Complete Reference Implementation:**

- **Lexer** (`soma/lexer.py`) - Full tokenization with unicode escape sequences
- **Parser** (`soma/parser.py`) - AST generation with path validation
- **VM/Runtime** (`soma/vm.py`) - Complete virtual machine with AL, Store, and Register
- **Standard Library** (`soma/stdlib.soma`) - Derived operations built on FFI primitives
- **Test Framework** (`tests/run_soma_tests.py`) - Automated test runner with EXPECT_AL/EXPECT_OUTPUT
- **Examples** (`examples/`) - Working programs demonstrating SOMA concepts
  - `examples/sin_calculator/` - Taylor series sin(x) computation with scaled integer arithmetic

**Run SOMA:**
```bash
# Execute SOMA code via Python API
from soma.vm import run_soma_program
run_soma_program("(Hello, SOMA!) >print")

# Run test suite
python3 tests/run_soma_tests.py

# Try examples
python3 examples/sin_calculator/run_soma_sin.py
```

The reference implementation is **production-ready** and demonstrates all language features described in this specification.

## Table of Contents

### Core Language
- [Philosophy](core/philosophy.md) - SOMA's design principles and relationship to other computational models
- [Lexical Analysis and Parsing](core/lexer.md) - Tokens, AST nodes, path parsing, and validation
- [Machine Model](core/machine-model.md) - The Accumulator List, Store, Registers, and Values
- [Blocks and Execution](core/blocks-execution.md) - First-class blocks and the execution model
- [Control Flow](core/control-flow.md) - `>choose`, `>chain`, and algebraic flow control
- [Built-ins](core/builtins.md) - Core operations and their AL contracts
- [Standard Library](core/stdlib.md) - Derived operations built from FFI primitives

### Programming
- [Comparisons](programming/comparisons.md) - SOMA vs Forth, Haskell, Lambda Calculus, and others
- [Examples](programming/examples.md) - Working SOMA programs demonstrating key concepts
- [Programming Idioms](programming/idioms.md) - Idiomatic patterns, best practices, and common anti-patterns
- [Errors and Semantics](programming/errors-semantics.md) - Fatal errors, abstract machine, and formal grammar

### Extensions
- [Extensions Overview](extensions/extensions.md) - Extension system and `>use` builtin
- [Python Interface](extensions/python-interface.md) - Python FFI integration
- [Load Extension](extensions/load.md) - File loading capabilities

### Debugging
- [Debugging](debugging/debugging.md) - Debug tools, philosophy, and troubleshooting techniques
- [Debug Ideas](debugging/debug-ideas.md) - Proposals for future debug features

### Markdown Extension
- [Markdown Overview](markdown/index.md) - SOMA markdown generation system
- [Markdown Skill](markdown/SKILL.md) - AI assistant reference for markdown extension

### Concepts
- [Engineering Standards](concepts/engineering-standards.md) - Verification-first development methodology

---

*Category: Informational | Version: 1.1 | Date: 20 Nov 2025*
