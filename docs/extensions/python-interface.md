# Python FFI Interface

**Extension for Python Reference Implementation**

## Overview

The Python reference implementation provides an extension that enables SOMA programs to call Python code. Following SOMA's philosophy of minimal primitives, this extension adds **zero global builtins** - instead, it provides namespaced operations under `use.python.*` that are loaded via the core `>use` mechanism.

**Architecture:**
- **Core language:** Only adds `>use` to global namespace (the universal extension loader)
- **Python extension:** Provides `use.python.*` builtins (FFI, file loading, etc.)
- **SOMA wrappers:** Extension includes SOMA code that creates friendly macros in the Store
- **stdlib.soma:** Auto-loaded by VM, 100% pure SOMA (no extension dependencies)

**Key Insight:** By convention, implementation extensions (python, js, native, jvm) provide a `.load` operation for loading SOMA files from their respective platforms. Feature extensions (posix, http, db) provide domain-specific operations.

## Loading the Python Extension

```soma
) Load Python implementation extension
(python) >use

) This automatically:
) 1. Registers builtins: >use.python.call, >use.python.load, >use.python.import
) 2. Runs SOMA setup code that creates Store macros
```

After `(python) >use`, you have access to:
- **Builtins:** `>use.python.call`, `>use.python.load`, etc. (primitive operations)
- **Store macros:** `use.python.isException`, `use.python.safe`, etc. (created by setup code)

## Core Builtins

### `>use.python.call` - FFI Primitive

**AL Contract:**
- **Consumes:** Callable name (string), then arguments until Void terminator
- **Produces:** Two values:
  1. Return value from Python callable (or Void if exception occurred)
  2. Exception object (or Void if successful)

**Behavior:**
1. Pop callable name from AL (must be a string)
2. Pop values from AL until encountering Void
3. Reverse the collected arguments (so they're in the order pushed)
4. Call the Python callable with those arguments
5. Push return value (or Void if exception)
6. Push exception object (or Void if successful)

**Example:**

```soma
(python) >use

) Call Python: int("42")
Void (42) (int) >use.python.call
!_.exc !_.ret

) Call Python: pow(2, 10)
Void (2) (10) (pow) >use.python.call
!_.exc !_.ret
) _.ret should be 1024
```

**Argument Order:** Arguments are pushed in natural order (first arg first) and reversed internally to match Python's positional parameters.

**Return Pattern:** Always pushes two values - pop both and check which case occurred:

```soma
Void (not_a_number) (int) >use.python.call
!_.exc !_.ret

) Case 1: _.ret = Void, _.exc = ValueError exception object
) Case 2: _.ret = result, _.exc = Void
```

### `>use.python.load` - Load SOMA Files

**AL Contract:**
- **Consumes:** File path (string)
- **Produces:** Nothing (executes the loaded code)

**Behavior:**
1. Pop file path from AL
2. Read SOMA code from filesystem using Python's file I/O
3. Execute the code in the current VM context

**Example:**

```soma
(python) >use

) Load additional SOMA libraries
(extensions/python_ffi_advanced.soma) >use.python.load

) Load user code
(myapp/main.soma) >use.python.load
```

**Note:** `stdlib.soma` is automatically loaded by the VM before any user code runs, so you never need to load it manually.

### `>use.python.import` - Import Python Modules

**AL Contract:**
- **Consumes:** Module name (string)
- **Produces:** Success boolean

**Behavior:**
1. Pop module name from AL
2. Import the Python module (making it available for `>use.python.call`)
3. Push True if successful, False if failed

**Example:**

```soma
(python) >use

) Import numpy
(numpy) >use.python.import
{ (NumPy imported successfully) >print }
{ (Failed to import NumPy) >print }
>ifelse

) Now can call numpy functions
Void 3.14 (numpy.sin) >use.python.call
```

## The Helper Library Pattern

Rather than adding builtins for exception handling, type checking, etc., the Python extension uses a two-layer approach:

### Layer 1: Python Helpers (`soma.py`)

```python
# soma.py - Python helpers for SOMA FFI

def isException(obj):
    """Check if obj is an exception instance."""
    return isinstance(obj, BaseException)

def getExceptionMessage(obj):
    """Get exception message as string."""
    if isinstance(obj, BaseException):
        return str(obj)
    return ""

def getExceptionType(obj):
    """Get exception type name."""
    if isinstance(obj, BaseException):
        return type(obj).__name__
    return ""

def formatException(obj):
    """Format exception for display."""
    if isinstance(obj, BaseException):
        return f"{type(obj).__name__}: {str(obj)}"
    return "Not an exception"

def pythonType(obj):
    """Get the Python type name of any object."""
    return type(obj).__name__

def readFile(path):
    """Read entire file as string."""
    with open(path, 'r') as f:
        return f.read()

def writeFile(path, content):
    """Write string to file."""
    with open(path, 'w') as f:
        f.write(content)
    return True

def fileExists(path):
    """Check if file exists."""
    import os
    return os.path.exists(path)
```

### Layer 2: SOMA Wrappers (Automatic Setup)

When `(python) >use` is executed, the extension automatically runs this SOMA code to create Store macros:

```soma
) Extension setup code (runs automatically during >use)

) Exception handling wrappers
{ Void >swap (soma.isException) >use.python.call } !use.python.isException
{ Void >swap (soma.getExceptionMessage) >use.python.call } !use.python.getMessage
{ Void >swap (soma.getExceptionType) >use.python.call } !use.python.getType
{ Void >swap (soma.formatException) >use.python.call } !use.python.format

) Type introspection
{ Void >swap (soma.pythonType) >use.python.call } !use.python.typeof

) File operations
{ Void >swap (soma.readFile) >use.python.call } !use.python.readFile
{ Void >swap >swap (soma.writeFile) >use.python.call } !use.python.writeFile
{ Void >swap (soma.fileExists) >use.python.call } !use.python.fileExists

) High-level safe wrapper
{
  !_.callable
  >swap
  Void >swap _.callable >use.python.call
  !_.exc !_.ret
  _.exc >use.python.isException
    { (Error: ) _.exc >use.python.format >concat >print Void }
    { _.ret }
  >ifelse
} !use.python.safe
```

**Benefits:**
- Clean namespace: `use.python.*` clearly indicates FFI usage
- Self-documenting API
- No global namespace pollution (only `>use` is global)
- Easy to extend - add functions to `soma.py`, add wrappers to setup code

## Building Higher-Level Abstractions

Users can build on the provided macros:

### Example 1: Using Safe Wrapper

```soma
(python) >use

) use.python.safe already exists from setup code
(42) (int) >use.python.safe !result

result >isVoid
  { (Conversion failed) >print }
  { (Result: ) result >toString >concat >print }
>ifelse
```

### Example 2: Retry Logic

```soma
) Build on top of provided wrappers
{
  !_.max_tries !_.callable
  0 !retry.count

  {
    _.callable >use.python.safe !_.result
    _.result >isVoid
      {
        ) Failed - try again?
        retry.count _.max_tries ><
          {
            retry.count 1 >+ !retry.count
            iter
          }
          { Nil }
        >ifelse
      }
      {
        _.result
      }
    >ifelse
  } !iter

  >iter >chain
} !use.python.retry

) Usage
(flaky_api_call) 3 (requests.get) >use.python.retry
```

### Example 3: File Operations API

```soma
) High-level file reading with error handling
{
  !_.path
  _.path >use.python.fileExists
    {
      _.path >use.python.readFile
      !_.exc !_.content
      _.exc >use.python.isException
        { (Failed to read: ) _.exc >use.python.format >concat >print Void }
        { _.content }
      >ifelse
    }
    {
      (File not found: ) _.path >concat >print Void
    }
  >ifelse
} !file.read.safe

) Usage
(/tmp/data.txt) >file.read.safe !content
content >isVoid
  { (Read failed) >print }
  { content >print }
>ifelse
```

## Error Handling Patterns

### Pattern 1: Immediate Check

```soma
Void (arg) (callable) >use.python.call
!_.exc !_.ret

_.exc >isVoid
  { _.ret ) Use result }
  { (Error occurred) >print Void }
>ifelse
```

### Pattern 2: Store Both for Later

```soma
Void (arg) (callable) >use.python.call
!call.exc !call.ret

) Later in the code...
call.exc >use.python.isException
  { call.exc >use.python.getMessage >print }
  { call.ret ) Use result }
>ifelse
```

### Pattern 3: Exception Propagation

```soma
{
  !_.callable
  Void >swap _.callable >use.python.call
  !_.exc !_.ret

  _.exc >use.python.isException
    { _.exc )  Propagate exception up by returning it }
    { _.ret )  Return successful result }
  >ifelse
} !use.python.propagate
```

## Complete Usage Example

Bringing it all together:

```soma
) Step 1: Load Python extension
(python) >use

) Step 2: Load additional SOMA libraries (using Python's file I/O)
(extensions/python_ffi_advanced.soma) >use.python.load

) Step 3: Import Python modules
(math) >use.python.import >drop

) Step 4: Use Python FFI with error handling
Void 45 (math.radians) >use.python.call
!_.exc !_.rad

_.exc >isVoid
  {
    ) Success - compute sine
    Void _.rad (math.sin) >use.python.call
    !_.exc2 !_.sin

    _.exc2 >isVoid
      { (sin(45°) = ) _.sin >toString >concat >print }
      { (Error in sin: ) _.exc2 >use.python.format >concat >print }
    >ifelse
  }
  {
    (Error in radians: ) _.exc >use.python.format >concat >print
  }
>ifelse
```

Or using the safe wrapper:

```soma
(python) >use

45 (math.radians) >use.python.safe
>dup >isVoid
  { >drop (Conversion failed) >print }
  {
    (math.sin) >use.python.safe
    (sin(45°) = ) >swap >toString >concat >print
  }
>ifelse
```

## Why This Design Works

### Namespace Isolation

**Global namespace:**
- `>use` ← only addition

**Extension builtins:**
- `>use.python.call` ← FFI primitive
- `>use.python.load` ← load SOMA files
- `>use.python.import` ← import Python modules

**Store macros (created by extension):**
- `use.python.isException` ← SOMA block
- `use.python.safe` ← SOMA block
- `use.python.typeof` ← SOMA block

No pollution. Clear boundaries. Easy to audit what's available.

### Traditional Macro Systems vs SOMA

**Lisp/Scheme:**
- Separate macro expansion phase at compile-time
- Special syntax and rules for macros vs functions
- Hygiene issues require special handling

**C Preprocessor:**
- Textual substitution only
- No access to runtime values
- Debugging is opaque

**SOMA Approach:**
- No phase separation - everything is runtime
- Uniform syntax - `>foo` works for builtins, stdlib, user code
- First-class blocks are both data and code
- Debugging is just stepping through block execution

### The Power of Minimal Primitives

With just `>use` in the core and the Python extension's primitives, you can build:

1. **Exception handling** via `soma.isException` helper + SOMA wrappers
2. **Type introspection** via `soma.pythonType` helper + SOMA wrappers
3. **Safe wrappers** via composed SOMA blocks
4. **Retry logic** via `>chain` and composed blocks
5. **Domain-specific APIs** (file I/O, networking, etc.) via layers of wrappers
6. **Library ecosystem** via `>use.python.load`

None of these require new global builtins. They're emergent properties of:
- First-class blocks
- Minimal FFI primitive
- Extension-provided SOMA setup code

### Comparison to Other Languages

**Python's `ctypes`:** Requires explicit type declarations, struct definitions, calling conventions.

**Haskell's FFI:** Requires `Foreign` imports, marshaling code, `IO` monad wrapping.

**SOMA's Python extension:** Load extension, call Python, check exception. Build abstractions with blocks.

The simplicity comes from SOMA's design:
- No type system to satisfy
- No purity to maintain (mutation is explicit)
- Blocks are values (easy to compose)
- AL is visible (easy to debug)
- Extensions are namespaced (easy to isolate)

## Implementation Architecture

### Core VM Changes

```python
# soma/vm.py (core implementation)
class VM:
    def __init__(self, load_stdlib=True):
        self.builtins = self._core_builtins()
        self.builtins['use'] = self._use_builtin  # Only global addition
        self.loaded_extensions = set()

        # Auto-load stdlib (100% pure SOMA)
        if load_stdlib:
            self._load_stdlib()

    def _load_stdlib(self):
        """Load stdlib.soma - pure SOMA, no extension dependencies."""
        stdlib_path = Path(__file__).parent / 'stdlib.soma'
        with open(stdlib_path, 'r') as f:
            stdlib_code = f.read()
        self._execute_code(stdlib_code)

    def _use_builtin(self, al, store, reg):
        """Load an extension by name."""
        ext_name = al.pop()
        if ext_name in self.loaded_extensions:
            return

        ext_module = importlib.import_module(f'soma.extensions.{ext_name}')
        ext_module.register(self)

        # Run extension's SOMA setup code (creates Store macros)
        if hasattr(ext_module, 'get_soma_setup'):
            setup_code = ext_module.get_soma_setup()
            if setup_code:
                self._execute_code(setup_code)

        self.loaded_extensions.add(ext_name)

    def register_extension_builtin(self, name, func):
        """Extensions call this - enforces use.* namespace."""
        if not name.startswith('use.'):
            raise ValueError(f"Extension builtins must be under 'use.*': {name}")
        self.builtins[name] = func
```

### Python Extension Implementation

```python
# soma/extensions/python.py
import importlib

def call_builtin(vm, al, store, reg):
    """FFI primitive - call any Python callable."""
    callable_name = al.pop()

    # Collect arguments until Void
    args = []
    while True:
        val = al.pop()
        if isinstance(val, VoidValue):
            break
        args.append(val)

    # Reverse to match natural push order
    args.reverse()

    # Resolve callable (support module.function syntax)
    try:
        parts = callable_name.split('.')
        if len(parts) == 1:
            # Built-in function
            func = eval(callable_name)
        else:
            # Module.function
            mod = importlib.import_module('.'.join(parts[:-1]))
            func = getattr(mod, parts[-1])

        # Call with converted args
        py_args = [_soma_to_python(arg) for arg in args]
        result = func(*py_args)

        # Success: push result and Void exception
        al.push(_python_to_soma(result))
        al.push(VoidValue())

    except Exception as e:
        # Failure: push Void result and exception
        al.push(VoidValue())
        al.push(ThingValue(e))

def load_builtin(vm, al, store, reg):
    """Load SOMA code from filesystem."""
    filepath = al.pop()
    with open(filepath, 'r') as f:
        code = f.read()
    vm._execute_code(code)

def import_builtin(vm, al, store, reg):
    """Import a Python module."""
    module_name = al.pop()
    try:
        importlib.import_module(module_name)
        al.push(BoolValue(True))
    except ImportError:
        al.push(BoolValue(False))

def register(vm):
    """Register Python extension builtins."""
    vm.register_extension_builtin('use.python.call', call_builtin)
    vm.register_extension_builtin('use.python.load', load_builtin)
    vm.register_extension_builtin('use.python.import', import_builtin)

def get_soma_setup():
    """Return SOMA code that creates Store macros."""
    return """
    ) Python FFI Wrapper Library
    ) Auto-loaded when (python) >use is executed

    ) Exception handling
    { Void >swap (soma.isException) >use.python.call } !use.python.isException
    { Void >swap (soma.getExceptionMessage) >use.python.call } !use.python.getMessage
    { Void >swap (soma.getExceptionType) >use.python.call } !use.python.getType
    { Void >swap (soma.formatException) >use.python.call } !use.python.format

    ) Type introspection
    { Void >swap (soma.pythonType) >use.python.call } !use.python.typeof

    ) File operations
    { Void >swap (soma.readFile) >use.python.call } !use.python.readFile
    { Void >swap >swap (soma.writeFile) >use.python.call } !use.python.writeFile
    { Void >swap (soma.fileExists) >use.python.call } !use.python.fileExists

    ) Safe call wrapper
    {
      !_.callable
      >swap
      Void >swap _.callable >use.python.call
      !_.exc !_.ret
      _.exc >use.python.isException
        { (Error: ) _.exc >use.python.format >concat >print Void }
        { _.ret }
      >ifelse
    } !use.python.safe
    """
```

### Type Conversions

**Python → SOMA:**
- `None` → `Void`
- `bool` → SOMA boolean (`True`/`False`)
- `int` → SOMA integer
- `str` → SOMA string
- Other → Opaque `Thing` (can be passed back to Python)

**SOMA → Python:**
- `Void` → `None`
- Boolean → `bool`
- Integer → `int`
- String → `str`
- Block → Error (blocks can't be marshaled to Python)

## Best Practices

### 1. Always Load Extension First

**Good:**
```soma
(python) >use
Void (42) (int) >use.python.call
```

**Bad:**
```soma
) This will fail - extension not loaded!
Void (42) (int) >use.python.call
```

### 2. Use Provided Macros

**Good:**
```soma
exception_obj >use.python.isException
```

**Bad:**
```soma
) Reinventing the wheel
Void exception_obj (soma.isException) >use.python.call
!_.exc !_.ret
```

### 3. Check Exceptions

**Good:**
```soma
Void (arg) (func) >use.python.call
!_.exc !_.ret
_.exc >use.python.isException { ) handle } { ) use result } >ifelse
```

**Bad:**
```soma
Void (arg) (func) >use.python.call
>drop  ) Ignore exception - dangerous!
```

### 4. Build Layered Abstractions

Start with low-level, build higher:

```soma
) Layer 1: Direct FFI (provided by extension)
>use.python.call

) Layer 2: Safe wrapper (provided by extension setup)
>use.python.safe

) Layer 3: Domain-specific (build yourself)
{
  !_.path
  _.path >use.python.fileExists
    { _.path >use.python.readFile }
    { Void }
  >ifelse
} !file.read.or.void

) Layer 4: Application-specific
{
  !_.config_path
  _.config_path >file.read.or.void !content
  content >isVoid
    { (default config) }
    { content }
  >ifelse
} !load.config.or.default
```

### 5. Document Dependencies

```soma
) REQUIRES: (python) >use
) REQUIRES: soma.py helper library
) REQUIRES: Python requests module

(python) >use
(requests) >use.python.import >drop

{ Void (https://api.example.com) (requests.get) >use.python.call } !http.get
```

## Bootstrapping and Library Loading

### Automatic Stdlib Loading

The VM automatically loads `stdlib.soma` on initialization:

```python
vm = VM()  # stdlib.soma already loaded
vm.run(user_code)
```

This ensures all pure SOMA operations (`>if`, `>while`, `>dup`, etc.) are always available without any extension dependencies.

### Manual Library Loading

Use `>use.python.load` to load additional SOMA libraries:

```soma
(python) >use

) Load Python FFI helpers
(extensions/python_ffi_advanced.soma) >use.python.load

) Load application code
(myapp/utils.soma) >use.python.load
(myapp/main.soma) >use.python.load
```

### Testing Without Stdlib

For testing FFI builtins in isolation:

```python
# Disable stdlib auto-loading
vm = VM(load_stdlib=False)
vm.run("2 3 >+")  # Only FFI builtins available
```

## Future Enhancements

Possible additions to the Python extension:

1. **`>use.python.eval`** - Evaluate Python expressions dynamically
2. **`>use.python.getattr`** - Access object attributes
3. **`>use.python.setattr`** - Modify object attributes
4. **`>use.python.dir`** - List object attributes
5. **Keyword arguments** - Convention for passing kwargs
6. **List/dict builders** - Construct Python collections from AL
7. **Async support** - Integration with `asyncio`

All can be added as new `use.python.*` builtins without touching the core VM.

## Comparison: Implementation vs Feature Extensions

**Implementation extensions** (provide `.load` by convention):
- `(python) >use` → `>use.python.load` for loading SOMA files via Python
- `(js) >use` → `>use.js.load` for loading via JavaScript fetch/require
- `(native) >use` → `>use.native.load` for loading via C fread

**Feature extensions** (provide domain operations):
- `(posix) >use` → `>use.posix.open`, `>use.posix.read`, etc.
- `(http) >use` → `>use.http.get`, `>use.http.post`, etc.
- `(db) >use` → `>use.db.query`, `>use.db.execute`, etc.

This separation keeps responsibilities clear:
- Implementation extensions bridge SOMA to the platform
- Feature extensions provide capabilities regardless of platform

---

*Category: Extension | Implementation: Python Reference | Version: 1.1 | Date: 25 Nov 2025*
