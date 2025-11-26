# Python FFI Examples

This directory contains examples demonstrating SOMA's Python Foreign Function Interface (FFI).

## Running the Examples

```bash
# From the SOMA root directory:
python3 examples/ffi/python_ffi_demo.py
```

## What's Demonstrated

### `python_ffi_demo.py`

Shows three key aspects of the Python FFI:

1. **Mathematical Functions** - Calling Python's `pow()` and `math.sqrt()`
2. **String Operations** - Using `str.upper()` and `str.title()` methods
3. **Error Handling** - The dual-return pattern `[result, exception]`

### Key Concepts

**Dual-Return Pattern:**
```soma
Void arg1 arg2 (function) >use.python.call
) Returns: [result, exception]
) - If success: [result_value, Void]
) - If error: [Void, exception_object]
```

**Error Checking:**
```soma
) Check if exception is Void (= success)
>isVoid {
  ) Success path
} {
  ) Error path
} >ifelse
```

**Benefits:**
- Access Python's entire standard library
- Call any installed Python package
- Robust error handling without exceptions
- Natural integration with SOMA control flow

## Philosophy

SOMA keeps its core minimal and uses FFI to access existing ecosystems. This demonstrates:

> **Minimal core + powerful FFI = maximum flexibility**

Instead of reimplementing everything, SOMA leverages Python's rich standard library and package ecosystem.
