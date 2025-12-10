# Load Extension

**Pure SOMA File Loading System**

**Implementation:** Python Reference Implementation

**Status:** Complete (v1.0)

**Dependencies:** Python FFI Extension (`>use.python.*`)

## Overview

The `load` extension provides a file loading system for SOMA programs, enabling modular code organization across multiple files. It implements path searching (current directory -> `$SOMA_LIB`) entirely in pure SOMA using the Python FFI primitives.

**Key Innovation:** This extension adds **zero Python builtins**. All logic is implemented in SOMA code (`soma/extensions/load.soma`) using only the existing `>use.python.call` and `>use.python.load` primitives.

## Problem & Solution

### Problem

SOMA programs need to:

- Split code across multiple files for organization
- Share common libraries between programs
- Search multiple directories for dependencies
- Provide clear error messages when files aren't found

### Solution

The `load` extension provides `>load` which:

1. Searches current directory first
2. Falls back to `$SOMA_LIB` environment variable
3. Loads and executes SOMA code in current context
4. Reports clear errors if file not found

## Usage

### Basic Usage

```soma
) Load the extension
(python) >use
(load) >use

) Load a file from current directory
(my_library.soma) >load

) Now you can use whatever that file defined
my_library.function
```

### With $SOMA_LIB

```bash
# Set SOMA_LIB to your library directory
export SOMA_LIB=/home/user/soma_libraries
```

```soma
(python) >use
(load) >use

) Searches pwd first, then $SOMA_LIB
(utils.soma) >load
(math_helpers.soma) >load
```

### Directory Search Order

1. **Current working directory** (checked first)
2. `$SOMA_LIB` (checked if not found in pwd)
3. **Error** if not found in either location

This ensures local files override library versions.

## Complete Examples

### Example 1: Simple Library

**my_math.soma:**

```soma
) Define some math helpers
{ >dup >* } !square
{ !_.n  1 { _.n >* } >repeat } !factorial
```

**main.soma:**

```soma
(python) >use
(load) >use

(my_math.soma) >load

5 >square     ) Returns 25
5 >factorial  ) Returns 120
```

### Example 2: Library with Dependencies

**constants.soma:**

```soma
3.14159 !math.pi
2.71828 !math.e
```

**geometry.soma:**

```soma
(python) >use
(load) >use

) Load dependency
(constants.soma) >load

) Define functions using constants
{ >square math.pi >* } !circle.area
```

**app.soma:**

```soma
(python) >use
(load) >use

(geometry.soma) >load

5 >circle.area  ) Returns 78.5398
```

### Example 3: $SOMA_LIB Usage

Directory structure:

```
/home/user/soma_libraries/
  |- string_utils.soma
  |- list_utils.soma

/home/user/my_project/
  |- app.soma
```

**app.soma:**

```soma
(python) >use
(load) >use

) These load from $SOMA_LIB
(string_utils.soma) >load
(list_utils.soma) >load

) Use the library functions
(hello) >string.uppercase  ) Returns (HELLO)
```

## Implementation Details

### Architecture

The `load` extension demonstrates SOMA's **layered extension model**:

```
+-------------------------------------+
|   >load (Pure SOMA)                 |
|   - Path searching logic            |
|   - Error handling                  |
|   - File existence checking         |
+-------------------------------------+
              | uses
+-------------------------------------+
|   Python FFI Primitives             |
|   - >use.python.call                |
|   - >use.python.load                |
+-------------------------------------+
              | wraps
+-------------------------------------+
|   Python Standard Library           |
|   - os.getcwd()                     |
|   - os.path.join()                  |
|   - os.path.exists()                |
|   - os.getenv()                     |
+-------------------------------------+
```

### Python Extension Module

**soma/extensions/load.py:**

```python
"""Pure SOMA Load Extension"""

def register(vm):
    """Register extension (no Python builtins needed)."""
    pass  # Pure SOMA implementation

def get_soma_setup():
    """Return SOMA code implementing >load."""
    import os
    soma_file = os.path.join(os.path.dirname(__file__), 'load.soma')
    with open(soma_file, 'r') as f:
        return f.read()
```

**Key Points:**

- `register()` is empty - no Python builtins added
- `get_soma_setup()` loads SOMA code from `load.soma`
- Uses `__file__` to find the `.soma` file in same directory
- Extension is entirely self-contained

### SOMA Implementation Highlights

The implementation (`soma/extensions/load.soma`) demonstrates advanced SOMA patterns:

**1. Context-Passing Pattern**

```soma
) Context-passing for nested blocks
_.                           ) Push context
_.getcwd_exception >isVoid   ) Test condition
{
  >{
    !_.                      ) Restore context in block
    _.getcwd_result !_.pwd   ) Access parent variables
    ...
  }
}
{
  >{
    !_.                      ) Restore context in block
    ...
  }
}
>choose >^                   ) Execute chosen block
```

This pattern is used throughout to pass Register variables across nested block boundaries.

**2. Python FFI Error Handling**

```soma
) Call Python function
Void _.dir _.filename (os.path.join) >use.python.call

) Store both return values
!_.exception !_.result

) Test if call succeeded
_.exception >isVoid
  { ) Success branch }
  { ) Error branch }
>choose >^
```

All Python calls follow the dual-return pattern: `[result, exception]`.

**3. Helper Function Composition**

```soma
) Helper: Check if file exists at directory + filename
{ ... } !load.checkpath

) Main function uses helper
_.pwd _.filename >load.checkpath
!_.found !_.path
```

The implementation is split into focused, composable functions.

## Error Messages

The extension provides clear error messages:

| Situation                              | Error Message                                                   |
|----------------------------------------|-----------------------------------------------------------------|
| File not in pwd, `$SOMA_LIB` not set   | Error: File not found in current directory and SOMA_LIB not set |
| File not in pwd or `$SOMA_LIB`         | Error: File not found in pwd or $SOMA_LIB                       |
| Cannot get current directory           | Error: Could not get current working directory                  |
| File not in pwd (no `$SOMA_LIB` check) | Error: File not found in current directory                      |

## Best Practices

### Do

```soma
) Load at start of file
(python) >use
(load) >use

) Load dependencies before using them
(utils.soma) >load
utils.function
```

### Do

```soma
) Use descriptive filenames
(string_utilities.soma) >load
(database_helpers.soma) >load
```

### Do

```bash
# Set SOMA_LIB for shared libraries
export SOMA_LIB=/usr/local/lib/soma
```

### Don't

```soma
) Don't forget to load dependencies
math.pi  ) Error: undefined if constants.soma not loaded
```

### Don't

```soma
) Don't rely on load order for local variables
) Loaded files share the VM context, but Register variables
) are execution-scoped, not file-scoped
```

## Design Rationale

### Why Pure SOMA?

The `load` extension could have been implemented as a Python builtin, but implementing it in pure SOMA demonstrates:

1. **SOMA's Expressiveness** - Complex file system operations using only basic primitives
2. **Composability** - Building extensions on top of extensions
3. **Transparency** - All logic is visible in `load.soma`
4. **Maintainability** - SOMA code is easier to modify than Python code for SOMA developers

### Why Register Variables?

The implementation uses Register variables (not Store) for all temporary state:

```soma
!_.filename        ) Register variable (local to block)
!load.checkpath   ) Store variable (global, part of public API)
```

**Benefits:**

- Doesn't pollute global Store namespace with temporary variables
- Demonstrates proper context-passing idiom
- Ensures library code is well-encapsulated

### Why >choose >^ Instead of >ifelse?

The implementation uses the context-passing pattern throughout:

```soma
_.
_.condition
  { >{ !_. ... } }
  { >{ !_. ... } }
>choose >^
```

This makes the two-step "choose then execute" process explicit and idiomatic for nested blocks that need parent context.

## Extension API

### Public Functions

| Function          | Input                                        | Output                          | Description                                    |
|-------------------|----------------------------------------------|---------------------------------|------------------------------------------------|
| `>load`           | `[filename(string), ...]`                    | `[...]`                         | Load and execute SOMA file with path searching |
| `>load.checkpath` | `[filename(string), directory(string), ...]` | `[fullpath, exists(bool), ...]` | Check if file exists in directory (helper)     |

### Dependencies

Requires Python FFI extension with:

- `>use.python.call` - Call Python functions
- `>use.python.load` - Load and execute SOMA files

## Testing

The extension includes comprehensive tests in `tests/test_load_extension.py`:

1. Loading from current directory
2. Loading from `$SOMA_LIB`
3. Current directory takes precedence over `$SOMA_LIB`
4. Loaded code executes in current context
5. Error messages for missing files

All 305 tests in the SOMA test suite pass.

## Future Enhancements

Potential additions:

1. **Multiple search paths** - `$SOMA_PATH` with colon-separated directories
2. **Relative imports** - Load files relative to current file
3. **Circular dependency detection** - Prevent infinite load loops
4. **Load once semantics** - Track loaded files to prevent duplicate execution
5. **Namespace isolation** - Optional sandboxing for loaded code

## Comparison to Other Languages

| Language   | Mechanism              | SOMA Equivalent       |
|------------|------------------------|-----------------------|
| Python     | `import module`        | `(module.soma) >load` |
| JavaScript | `require('./file.js')` | `(file.soma) >load`   |
| C          | `#include "file.h"`    | `(file.soma) >load`   |
| Lua        | `require "module"`     | `(module.soma) >load` |

**Key Difference:** SOMA's `>load` executes in the same context (shared Store/Register), similar to C's `#include`, rather than creating isolated namespaces like Python's `import`.

## Conclusion

The `load` extension demonstrates that SOMA's minimal primitives enable building sophisticated features entirely in SOMA code. By composing Python FFI calls with SOMA's context-passing patterns, we achieve:

- **Zero new Python builtins**
- **Full path searching**
- **Clear error messages**
- **Clean, maintainable code**

This exemplifies SOMA's philosophy: **Minimal primitives, maximal expressiveness.**

---

_Category: Extension | Version: 1.0 | Dependencies: Python FFI | Date: 26 Nov 2025_


