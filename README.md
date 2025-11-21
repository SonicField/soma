# soma
Semantic Oriented Machine Algebra (SOMA) —
a minimalistic semantic analysis language based on explicit state and mutation, deliberately counterpointing type-centric alternatives.

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
Summary: 65/65 tests passed
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

- All 65 SOMA tests must pass
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
