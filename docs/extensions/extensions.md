# 12. Extensions and the `>use` System

**Implementation-Specific Features via Dynamic Loading**

Extensions are implementation-specific features that augment SOMA's minimal core with platform capabilities while maintaining the language's philosophical principles. The reference Python implementation provides the `>use` builtin for dynamic extension loading and a Python FFI extension for platform integration.

---

## 12.1 The `>use` Builtin

The `>use` builtin enables dynamic loading of extensions at runtime.

**Contract:**
```
AL Before:  [(extension-name), ...]
AL After:   [...]
Effect:     Loads named extension, registers its builtins under use.* namespace
```

**Usage:**
```soma
(python) >use    ) Loads Python FFI extension
                 ) Registers: use.python.call, use.python.load, use.python.import
```

**Design Principles:**

1. **Minimal global namespace pollution** - Only `>use` in global namespace
2. **Namespaced builtins** - Extensions register under `use.*` prefix
3. **Idempotent loading** - Loading same extension multiple times is safe
4. **No dependencies** - Extensions can't depend on each other (yet)

**Example:**
```soma
) Load extension
(python) >use

) Extension builtins now available
Void 2 10 (pow) >use.python.call    ) [1024, Void]
```

---

## 12.2 Extension Architecture

### Extension Registration

Extensions register themselves via the VM's extension system:

```python
# soma/extensions/python.py
def register(vm):
    """Register Python FFI builtins."""
    vm.register_extension_builtin('python.call', call_builtin)
    vm.register_extension_builtin('python.load', load_builtin)
    vm.register_extension_builtin('python.import', import_builtin)
```

### Namespace Rules

- **Global namespace:** Only `>use` allowed
- **Extension namespace:** `use.<ext>.*` pattern
- **No nesting:** `use.python.call` not `use.python.ffi.call`
- **Validation:** VM enforces namespace structure

**Invalid:**
```python
vm.register_extension_builtin('my_func', func)      # Error: no namespace
vm.register_extension_builtin('global.func', func)  # Error: reserved
```

**Valid:**
```python
vm.register_extension_builtin('python.call', func)  # ✓
vm.register_extension_builtin('http.get', func)     # ✓
```

---

## 12.3 Available Extensions

### Python FFI Extension

**Status:** Complete (v1.1)
**Load:** `(python) >use`
**Documentation:** [extensions/Python-Interface.md](extensions/Python-Interface.md)

**Builtins:**
- `>use.python.call` - Call Python functions
- `>use.python.load` - Load SOMA files
- `>use.python.import` - Import Python modules

**Example:**
```soma
(python) >use

) Basic FFI call
Void (42) (int) >use.python.call           ) [42, Void]

) Mathematical computation
Void 2 10 (pow) >use.python.call           ) [1024, Void]

) Import and use module
(math) >use.python.import                   ) [True] if success
Void 3.14159 (math.sin) >use.python.call   ) [0.0000026..., Void]
```

See [Python-Interface.md](extensions/Python-Interface.md) for complete specification.

---

## 12.4 Standard Library Auto-Loading

The VM automatically loads `soma/stdlib.soma` on initialization. This is **not** an extension - it's pure SOMA code with no platform dependencies.

**Control:**
```python
# Python API
from soma.vm import VM, run_soma_program

vm = VM()                    # Stdlib auto-loads (default)
vm = VM(load_stdlib=False)   # Disable for testing/embedding
```

**Why Auto-Load:**
- Stdlib is 100% pure SOMA (no FFI dependencies)
- Provides essential derived operations (`>dup`, `>drop`, `>swap`, etc.)
- Users expect these to be available
- Can be disabled for minimal embeddings

**What's in Stdlib:**
- Boolean logic (`>not`, `>and`, `>or`)
- Comparison operators (`>>`, `>=`, `><=`, `>==`, `>!=`)
- Stack manipulation (`>dup`, `>drop`, `>swap`, `>over`, `>rot`)
- Control flow helpers (`>if`, `>unless`, `>when`)
- Higher-order operations (`>times`, `>map`, `>filter`)

See [11-stdlib.md](11-stdlib.md) for complete stdlib reference.

---

## 12.5 Creating New Extensions

### Step 1: Define the Extension Module

Create `soma/extensions/myext.py`:

```python
def my_builtin(vm):
    """Example builtin implementation."""
    from soma.vm import Void

    arg = vm.al.pop()
    result = f"Processed: {arg}"

    vm.al.append(result)
    vm.al.append(Void)  # No exception

def register(vm):
    """Register extension builtins."""
    vm.register_extension_builtin('myext.process', my_builtin)
```

### Step 2: Use in SOMA

```soma
(myext) >use
(hello) >use.myext.process    ) ["Processed: hello", Void]
```

### Step 3: Build SOMA Ecosystem

Create helper wrappers in pure SOMA:

```soma
) Load extension
(myext) >use

) Build convenience wrappers
{ >use.myext.process >isVoid >not >drop } !myext.safe
{ (myext-) >swap >concat >use.myext.process } !myext.prefixed

) Use high-level abstractions
(world) >myext.safe            ) Just the result, discards exception
(test) >myext.prefixed         ) Adds prefix via composition
```

---

## 12.6 Extension Best Practices

### DO: Minimal Primitives

**Good:**
```python
# One FFI gateway
vm.register_extension_builtin('python.call', call_builtin)
```

**Bad:**
```python
# Don't add dozens of specific builtins
vm.register_extension_builtin('python.pow', pow_builtin)
vm.register_extension_builtin('python.sqrt', sqrt_builtin)
vm.register_extension_builtin('python.sin', sin_builtin)
# ... 50 more builtins
```

### DO: Dual Return Pattern

**Good:**
```python
def ffi_builtin(vm):
    try:
        result = risky_operation()
        vm.al.append(result if result is not None else Void)
        vm.al.append(Void)  # No exception
    except Exception as e:
        vm.al.append(Void)
        vm.al.append(e)     # Exception
```

**Bad:**
```python
def ffi_builtin(vm):
    result = risky_operation()  # Exception crashes VM!
    vm.al.append(result)
```

### DO: Void-Terminated Arguments

**Good:**
```soma
Void arg1 arg2 arg3 (func) >use.ext.call
) Clear termination, variable arity
```

**Bad:**
```soma
(3) arg1 arg2 arg3 (func) >use.ext.call
) Requires counting arguments - fragile
```

### DO: Build Ecosystem in SOMA

**Good:**
```soma
(http) >use

) Build safe wrappers in SOMA
{
  !_.url
  Void _.url (http.get) >use.http.call
  !_.exc !_.resp
  _.exc >isVoid >not
    { (HTTP Error) >print Void }
    { _.resp }
  >choose
} !http.safe.get
```

**Bad:**
```python
# Don't add builtins for every wrapper
vm.register_extension_builtin('http.safe_get', safe_get_builtin)
vm.register_extension_builtin('http.retry', retry_builtin)
vm.register_extension_builtin('http.timeout', timeout_builtin)
```

---

## 12.7 Extension vs Standard Library

**When to make an Extension:**
- Requires platform-specific code (FFI, I/O, system calls)
- Cannot be implemented in pure SOMA
- Needs implementation language access (Python, C, JavaScript)

**When to add to Standard Library:**
- Can be built from existing builtins
- Pure SOMA implementation
- Platform-independent
- Universally useful across implementations

**Examples:**

| Feature | Category | Rationale |
|---------|----------|-----------|
| `>python.call` | Extension | Requires Python runtime |
| `>http.get` | Extension | Requires networking primitives |
| `>dup` | Stdlib | Built from `{ !_.x _.x _.x }` pattern |
| `>if` | Stdlib | Built from `>choose` + blocks |
| `>times` | Stdlib | Built from `>chain` + blocks |

---

## 12.8 Extension Security

Extensions bypass SOMA's memory safety guarantees. Best practices:

### Input Validation

```python
def call_builtin(vm):
    if len(vm.al) < 2:
        raise RuntimeError("AL underflow: python.call requires [Void, args..., name]")

    callable_name = vm.al.pop()
    if not isinstance(callable_name, str):
        raise RuntimeError(f"python.call requires string name, got {type(callable_name)}")
```

### Exception Safety

```python
def safe_builtin(vm):
    try:
        # Risky operation
        result = do_something()
        vm.al.append(result if result is not None else Void)
        vm.al.append(Void)
    except Exception as e:
        # Never let exceptions escape to VM
        vm.al.append(Void)
        vm.al.append(e)
```

### Resource Management

```python
def file_builtin(vm):
    try:
        with open(path, 'r') as f:  # Use context managers
            data = f.read()
        vm.al.append(data)
        vm.al.append(Void)
    except Exception as e:
        vm.al.append(Void)
        vm.al.append(e)
```

---

## 12.9 Extension Lifecycle

### Loading Sequence

1. User code: `(extension-name) >use`
2. VM pops extension name from AL
3. VM checks if already loaded (idempotent)
4. VM imports `soma.extensions.{name}`
5. VM calls `register(vm)` function
6. Extension registers builtins via `vm.register_extension_builtin()`
7. Builtins available at `use.{name}.*` paths

### Example Loading Flow

```soma
(python) >use
) VM loads soma/extensions/python.py
) Calls python.register(vm)
) Registers: use.python.call, use.python.load, use.python.import

Void 10 (abs) >use.python.call    ) Now available!
```

### Idempotent Loading

```soma
(python) >use
(python) >use    ) No-op, already loaded
(python) >use    ) Still a no-op

Void 5 (abs) >use.python.call    ) Works fine
```

---

## 12.10 Complete Example: HTTP Extension

Here's how to design a hypothetical HTTP extension following SOMA principles:

### Extension Implementation (Python)

```python
# soma/extensions/http.py
import urllib.request
from soma.vm import Void

def get_builtin(vm):
    """
    HTTP GET request.

    AL Before: [url, Void, ...]
    AL After:  [response_body, exception, ...]
    """
    url = vm.al.pop()
    terminator = vm.al.pop()

    if not isinstance(terminator, type(Void)):
        raise RuntimeError("http.get requires Void terminator")

    try:
        with urllib.request.urlopen(url) as response:
            body = response.read().decode('utf-8')
        vm.al.append(body)
        vm.al.append(Void)
    except Exception as e:
        vm.al.append(Void)
        vm.al.append(e)

def register(vm):
    vm.register_extension_builtin('http.get', get_builtin)
```

### SOMA Ecosystem

```soma
) Load extension
(http) >use

) Build safe wrapper
{
  !_.url
  Void _.url >use.http.get
  !_.exc !_.resp

  _.exc >isVoid >not
    { (HTTP request failed) >print Nil }
    { _.resp }
  >choose
} !http.safe.get

) Build retry logic
{
  !_.url !_.attempts
  {
    _.url >http.safe.get
    !_.result

    _.result >isNil
      {
        _.attempts 1 >- !_.attempts
        _.attempts 0 >>
          { >loop }
          { Nil }
        >choose >^
      }
      { _.result }
    >choose
  } !loop
  >loop
} !http.retry.get

) Use high-level abstraction
(https://api.example.com/data) 3 >http.retry.get
) Returns data or Nil after 3 attempts
```

---

## 12.11 Testing Extensions

### Unit Tests (Python)

```python
# tests/test_http_extension.py
import unittest
from soma.vm import VM, run_soma_program, Void

class TestHttpExtension(unittest.TestCase):
    def test_http_extension_loads(self):
        vm = VM(load_stdlib=False)
        vm.load_extension('http')
        self.assertIn('http', vm.loaded_extensions)

    def test_http_get_builtin_exists(self):
        code = "(http) >use use.http.get >isVoid >not"
        al = run_soma_program(code)
        self.assertEqual(al[-1], True)
```

### Integration Tests (SOMA)

```soma
) tests/soma/06_http_extension.soma

) TEST: Load HTTP extension
) EXPECT_AL: []
(http) >use

) TEST: HTTP GET builtin exists
) EXPECT_AL: [True]
(http) >use
use.http.get >isVoid >not
```

### Error Tests

```soma
) tests/soma/06_http_errors.soma

) TEST: HTTP GET requires Void terminator
) EXPECT_ERROR: RuntimeError
(http) >use
(invalid-terminator) (http://example.com) >use.http.get
```

---

## 12.12 Stdlib vs Extensions

### What is Stdlib?

**Located:** `soma/stdlib.soma`
**Language:** 100% pure SOMA code
**Dependencies:** Only core builtins (no extensions)
**Loading:** Auto-loaded by VM on initialization

**Example:**
```soma
) Pure SOMA - no platform dependencies
{ !_.x !_.y _.x _.y } !swap
{ !_.x _.x _.x } !dup
{ !_.x } !drop
```

### What is an Extension?

**Located:** `soma/extensions/*.py`
**Language:** Implementation language (Python, C, Rust, etc.)
**Dependencies:** Platform-specific libraries
**Loading:** Explicit via `>use`

**Example:**
```python
# Requires Python runtime
def call_builtin(vm):
    import importlib
    # ... Python-specific code
```

### Decision Matrix

| Feature | Pure SOMA? | Platform Code? | Category |
|---------|------------|----------------|----------|
| `>dup` | ✓ | ✗ | Stdlib |
| `>if` | ✓ | ✗ | Stdlib |
| `>times` | ✓ | ✗ | Stdlib |
| `>use.python.call` | ✗ | ✓ | Extension |
| `>use.http.get` | ✗ | ✓ | Extension |
| `>use.file.read` | ✗ | ✓ | Extension |

---

## 12.13 Python FFI Quick Reference

The reference implementation includes a complete Python FFI extension.

### Loading

```soma
(python) >use    ) Load once at program start
```

### Calling Functions

```soma
) Syntax: Void arg1 arg2 ... argN (callable-name) >use.python.call
) Returns: [result, exception] where one is always Void

Void (42) (int) >use.python.call        ) [42, Void]
Void 2 10 (pow) >use.python.call        ) [1024, Void]
Void (HELLO) (str.lower) >use.python.call  ) ["hello", Void]
```

### Error Handling

```soma
) Exception case
Void (invalid) (int) >use.python.call
) Returns: [Void, <Exception object>]

!_.exc !_.result
_.exc >isVoid >not
  { (Error occurred) >print }
  { _.result >print }
>choose
```

### Loading SOMA Files

```soma
Void (path/to/file.soma) >use.python.load
) Executes SOMA code in current VM context
```

### Importing Modules

```soma
(math) >use.python.import    ) [True] if success, [False] if failure
```

**Complete Example:**
```soma
(python) >use

) Import math module
(math) >use.python.import >drop

) Calculate sin(π/2)
Void 3.14159 2 >/ (math.sin) >use.python.call
!_.exc !_.result

_.exc >isVoid
  { _.result >print }
  { (Error calculating sin) >print }
>choose
```

---

## 12.14 Extension Design Patterns

### Pattern 1: Gateway Primitive + SOMA Wrappers

**Primitive:**
```python
vm.register_extension_builtin('db.query', query_builtin)
```

**SOMA Wrappers:**
```soma
{ Void >swap (SELECT * FROM users) >use.db.query } !db.users.all
{ !_.id Void _.id (SELECT * FROM users WHERE id=?) >use.db.query } !db.users.get
{ !_.email Void _.email (SELECT * FROM users WHERE email=?) >use.db.query } !db.users.find
```

### Pattern 2: Exception Unwrapping

```soma
) Generic exception checker
{ >isVoid >not } !isException

) Generic result extractor (throws away exception)
{ >swap >drop } !getResult

) Safe wrapper pattern
{
  !_.operation
  _.operation >^
  !_.exc !_.result

  _.exc >isException
    { (Operation failed) >print Nil }
    { _.result }
  >choose
} !safe.execute
```

### Pattern 3: Type Conversions

```soma
(python) >use

) SOMA → Python conversions (automatic)
42 ) int → Python int
(hello) ) str → Python str

) Python → SOMA conversions
Void () (list) >use.python.call        ) Python list
Void () (dict) >use.python.call        ) Python dict
Void None (id) >use.python.call        ) Python None → SOMA Void
```

---

## 12.15 Future Extensions

Potential extensions for different implementations:

### File I/O Extension
```soma
(file) >use
Void (path.txt) >use.file.read     ) [contents, exception]
Void (data) (path.txt) >use.file.write
```

### Network Extension
```soma
(net) >use
Void (example.com) 80 >use.net.connect
Void (GET /) >use.net.send
>use.net.receive
```

### System Extension
```soma
(sys) >use
Void (ls) (-la) >use.sys.exec      ) Run shell commands
>use.sys.env.get                   ) Environment variables
```

### Graphics Extension
```soma
(gfx) >use
Void 800 600 (Window) >use.gfx.create
Void 100 100 50 >use.gfx.circle
>use.gfx.render
```

---

## 12.16 Embedding SOMA

Extensions enable embedding SOMA in larger applications:

### Python Integration

```python
from soma.vm import VM

# Create VM without stdlib for minimal embedding
vm = VM(load_stdlib=False)

# Register custom builtins
def app_callback(vm):
    data = vm.al.pop()
    print(f"App received: {data}")
    vm.al.append(True)

vm.register_extension_builtin('app.callback', app_callback)

# Execute SOMA code
vm.execute_code("(app) >use")
vm.execute_code("(Hello from SOMA) >use.app.callback")
```

### Bidirectional Communication

```python
# Python → SOMA
vm.execute_code("42 !shared.value")

# SOMA → Python
result = vm.store.read_value(['shared', 'value'])
print(f"SOMA computed: {result}")
```

---

## 12.17 Specification Compliance

**Core SOMA:** Portable across all implementations
**Extensions:** Implementation-specific, not portable

**Portable Code:**
```soma
) Works everywhere - uses only core builtins
{ !_.x _.x _.x >* } !square
5 >square    ) [25]
```

**Non-Portable Code:**
```soma
) Only works in Python implementation
(python) >use
Void 5 (abs) >use.python.call
```

**Best Practice:** Keep core logic portable, use extensions at boundaries:

```soma
) Core business logic (portable)
{ !_.x _.x 2 >* 3 >+ } !compute

) I/O via extension (not portable)
{
  !_.filename
  _.filename >file.read.safe
  !_.data
  _.data >compute
  _.data >file.write.safe
} !process.file
```

---

## 12.18 Summary

**The `>use` System:**
- One builtin (`>use`) enables entire extension ecosystem
- Extensions register under `use.*` namespace
- Idempotent loading, no inter-extension dependencies
- Maintains SOMA's minimal core + maximal expressiveness

**Design Philosophy:**
- Add one primitive gateway, build ecosystem in SOMA
- Dual return pattern for error handling
- Void-terminated arguments for variable arity
- Keep core logic portable, extensions at boundaries

**Available Now:**
- Python FFI extension ([Python-Interface.md](extensions/Python-Interface.md))
- Auto-loading stdlib (pure SOMA, no extensions needed)

**Next Steps:**
- See [extensions/Python-Interface.md](extensions/Python-Interface.md) for Python FFI details
- Check `soma/extensions/` for implementation examples
- Create your own extensions following the patterns above

---

*Category: Extensions | Version: 1.1 | Date: 25 Nov 2025*
