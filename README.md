# SOMA

**State-Oriented Machine Algebra (SOMA)** — a minimalistic computational model based on explicit state and mutation, deliberately counterpointing type-centric alternatives.

SOMA treats programs as explicit state-transforming machines with mutable state, visible memory, and observable execution. Blocks are first-class values, not functions. Execution is explicit via `>`. There are no hidden stacks, no return semantics, no exceptions.

## Documentation

Comprehensive documentation is available in the `docs/` folder:

- **[Language Specification](docs/index.md)** - Complete SOMA v1.1 specification
- **[Programming Idioms](docs/09-idioms.md)** - Best practices, common patterns, and anti-patterns
- **[Examples](docs/08-examples.md)** - Working SOMA programs
- **[Comparisons](docs/07-comparisons.md)** - SOMA vs Forth, Haskell, Lambda Calculus, and others

## Examples

The `examples/` directory contains complete, runnable SOMA programs demonstrating real-world applications:

### Sin Calculator (`examples/sin_calculator/`)

A Taylor series implementation of `sin(x)` showcasing:
- **Scaled integer arithmetic** - Simulating decimal precision using 10^10 scale factor
- **>chain iteration** - Taylor series convergence with tail-call optimization
- **Unicode string escapes** - Proper formatting with `\28\(` and `\29\)` characters
- **Store-based state** - Clean iteration without complex context-passing

```bash
python3 examples/sin_calculator/run_soma_sin.py
```

**Output:**
```
sin(0°) = 0.0000000000
sin(30°) = 0.5000000001
sin(45°) = 0.7071067814
sin(90°) = 1.0000000010
```

See `examples/sin_calculator/README.md` for complete documentation including:
- How to read SOMA code
- Detailed walkthrough of the implementation
- Accuracy analysis and design decisions

## Testing

SOMA has a comprehensive test suite covering both FFI built-ins and the standard library.

### Running the Full Test Suite

To run all SOMA tests:

```bash
python3 tests/run_soma_tests.py
```

**Expected output:**
```
============================================================
SOMA Test Suite
============================================================

============================================================
📄 01_ffi_builtins.soma
============================================================
  ✓ True constant
  ✓ False constant
  ... (24 tests total)

============================================================
📄 02_stdlib.soma
   (with stdlib)
============================================================
  ✓ not with True
  ✓ not with False
  ... (41 tests total)

============================================================
📄 03_*.soma files
   (idioms and patterns)
============================================================
  ✓ Context passing patterns
  ✓ Looping with >chain
  ✓ Store vs Register usage
  ... (237 tests total)

============================================================
Summary: 302/302 tests passed
============================================================
✓ All tests passed!
```

### Test Organization

- **`tests/soma/01_ffi_builtins.soma`** - Tests for FFI primitives (24 tests)
  - Boolean constants (`True`, `False`, `Nil`, `Void`)
  - Comparison operators (`<`, `>`, `==`, `!=`, etc.)
  - Arithmetic operators (`+`, `-`, `*`, `/`, `%`)
  - Type predicates (`isVoid`, `isNil`)
  - Type conversions (`toString`, `toInt`)
  - I/O operations (`print`, `readLine`)

- **`tests/soma/02_stdlib.soma`** - Tests for standard library operations (41 tests)
  - Boolean logic (`not`, `and`, `or`)
  - Comparison operators (`>`, `==`, `!=`, `<=`, `>=`)
  - Stack manipulation (`dup`, `drop`, `swap`, `over`, `rot`)
  - Arithmetic helpers (`inc`, `dec`, `abs`, `min`, `max`)
  - Control flow (`times`, `if`, `ifelse`, `while`, `do`)

- **`tests/soma/03_*.soma`** - Tests for idioms and patterns (237 tests)
  - Context-passing idiom (`_.` → `!_.` pattern)
  - Execution scope vs lexical scope
  - Looping with `>chain` (tail-call optimization)
  - Store vs Register usage
  - `>choose` patterns (values vs blocks)
  - Self-referencing blocks
  - Complete examples (Collatz, Fibonacci, counters, etc.)

### Running Python Unit Tests

To run the Python implementation tests:

```bash
python3 -m pytest tests/test_*.py -v
```

Or run individual test modules:

```bash
python3 -m pytest tests/test_vm.py -v       # VM implementation tests
python3 -m pytest tests/test_parser.py -v   # Parser tests
python3 -m pytest tests/test_lexer.py -v    # Lexer tests
```

### Success Criteria

- All 302 SOMA tests must pass
- All Python unit tests must pass
- No errors or exceptions during execution

### Test File Format

SOMA test files use a simple format:

```soma
) TEST: Description of what is being tested
) EXPECT_AL: [expected, values, on, AL]
) EXPECT_OUTPUT: expected printed output (optional, can be multiple lines)

... SOMA code to execute ...
```

Multiple tests can exist in a single `.soma` file. The test runner:
1. Loads `soma/stdlib.soma` for stdlib tests
2. Executes each test independently
3. Verifies the AL matches `EXPECT_AL`
4. Verifies printed output matches `EXPECT_OUTPUT` lines

### Debugging Failed Tests

Run with verbose mode to see full test source:

```bash
python3 tests/run_soma_tests.py -v
```

This shows the SOMA source code for any failing tests.
