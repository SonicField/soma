# SOMA Extensions

**Implementation-Specific Features**

This directory contains documentation for features that are not part of the core SOMA specification but are specific to particular implementations. These extensions demonstrate how SOMA's minimal core can be augmented with platform-specific capabilities while maintaining the language's philosophical principles.

## What Belongs Here

**Extensions** are features that:

- Are specific to a particular implementation (e.g., Python reference implementation)
- Provide platform integration (FFI, I/O beyond basic print, OS interaction)
- Extend SOMA with capabilities not in the core specification
- Are optional - other implementations may provide different extensions

**Not Extensions** (these belong in core docs):

- Core language features (AL, Store, Register, blocks)
- Standard library built from core primitives
- Language semantics and execution model
- Built-ins required by the specification

## Philosophy of Extensions

SOMA's design principle: **Minimal primitives, maximal expressiveness.**

Extensions follow this principle by:

1. **Adding minimal builtins**: One primitive that serves as a gateway
2. **Building ecosystems in SOMA**: Use first-class blocks to create abstractions
3. **Maintaining explicitness**: No hidden behavior, clear execution model
4. **Leveraging composition**: Build complex features from simple blocks

### Example: Python FFI

Rather than adding dozens of builtins for exception handling, type checking, file I/O, etc., the Python implementation adds **one** FFI builtin (`>python`) and builds everything else in SOMA:

```soma
) Single primitive builtin
>python  ) Call any Python function

) Build the ecosystem in SOMA
{ Void >swap (soma.isException) >python } !python.isException
{ Void >swap (soma.getMessage) >python } !python.getMessage
{ Void >swap (soma.readFile) >python } !python.readFile

) Create high-level abstractions
{
  !_.path
  _.path >python.readFile
  !_.exc !_.ret
  _.exc >python.isException
    { (Error) >print Void }
    { _.ret }
  >ifelse
} !file.read.safe
```

This demonstrates SOMA's macro-like power without requiring a macro system.

## Available Extensions

### [Python FFI Interface](Python-Interface.md)

- **Implementation**: Python Reference Implementation
- **Status**: Proposed (v1.1)

The `>python` builtin provides a universal gateway to Python code, enabling:

- Foreign function calls with automatic exception handling
- Python helper library pattern (`soma.py` + SOMA wrappers)
- Building domain-specific APIs (file I/O, networking, etc.) without new builtins
- Type introspection and conversion

**Key Features:**

- Single builtin: `>python`
- Void-terminated argument lists
- Dual return: value + exception
- Clean namespace hierarchy via `python.*` wrappers
- Demonstrates first-class blocks as macro replacement

**Use Cases:**

- File I/O beyond basic `>print`
- Network operations
- Mathematical libraries (NumPy, SciPy)
- System interaction (subprocess, environment variables)
- Integration with existing Python codebases

See [Python-Interface.md](Python-Interface.md) for complete specification and examples.

### [Load Extension](Load.md)

- **Implementation**: Python Reference Implementation
- **Status**: Complete (v1.0)
- **Dependencies**: Python FFI Extension

The `load` extension provides file loading and path searching for SOMA programs, enabling modular code organization.

**Key Innovation:** Implemented entirely in pure SOMA code - adds **zero Python builtins**.

**Key Features:**

- Single public function: `>load`
- Path searching: current directory -> `$SOMA_LIB`
- Clear error messages
- Pure SOMA implementation using Python FFI primitives
- Demonstrates context-passing idiom throughout

**Use Cases:**

- Splitting code across multiple files
- Creating reusable library modules
- Sharing common code via `$SOMA_LIB`
- Building modular applications

**Example:**

```soma
(python) >use
(load) >use

(my_library.soma) >load
my_library.function
```

See [Load.md](Load.md) for complete documentation and implementation details.

---

## Future Extensions

Potential extensions for various implementations:

### JavaScript/WebAssembly Implementation

- Browser DOM interaction
- Web APIs (fetch, localStorage)
- WebAssembly module loading

### Native Implementation (C/C++/Rust)

- System calls via FFI
- Direct memory access
- Performance-critical operations

### JVM Implementation

- Java interop
- JVM library access
- Reflection and introspection

### Network Extensions

- HTTP client/server
- WebSocket support
- Protocol implementations

### Database Extensions

- SQL queries
- NoSQL operations
- Transaction management

### Graphics Extensions

- 2D/3D rendering
- GUI frameworks
- Image processing

## Guidelines for Creating Extensions

When creating a new extension:

1. **Start with one primitive**: Don't add multiple builtins when one gateway suffices
2. **Build in SOMA**: Create helper libraries and wrappers as SOMA blocks
3. **Document the ecosystem**: Show how to compose abstractions
4. **Follow naming conventions**: Use namespaced paths (e.g., python.*, http.*)
5. **Handle errors explicitly**: Return error indicators, don't hide failures
6. **Maintain SOMA philosophy**: Explicit state, visible execution, composable blocks

### Extension Documentation Template

Each extension document should include:

1. **Overview**: What problem does this solve?
2. **Specification**: Precise builtin contracts (AL consumption/production)
3. **Helper Library Pattern**: How to build the ecosystem
4. **Complete Examples**: Working code demonstrating typical usage
5. **Best Practices**: Patterns and anti-patterns
6. **Implementation Notes**: How to implement in the target platform

## Contributing Extensions

To propose a new extension:

1. Create a draft document in `docs/extensions/`
2. Follow the template above
3. Show how it maintains SOMA's principles
4. Provide working implementation or detailed specification
5. Update this index with a summary

Extensions should be **implementation-specific**. If a feature could be built entirely from existing primitives, it belongs in the standard library, not as an extension.

---

_Category: Extensions Index | Version: 1.1 | Date: 25 Nov 2025_


