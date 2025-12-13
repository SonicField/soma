# # 06. Built-in Words

**Built-ins are just Blocks stored at Store paths.** When you write `>print`, `>dup`, or `>+`, you're not invoking special syntax—you're executing the Block stored at that path in the Store. There is no special "built-in" mechanism in SOMA. The `>` prefix means "read the value at this path and execute it," which works identically for built-in operations and user-defined blocks.

This means built-ins could theoretically be overridden by storing a different Block at paths like `"print"` or `"dup"` (though this is not recommended). The execution model is uniform: `>name` executes whatever Block is stored at that path, whether it was pre-populated by the runtime or defined by user code.

---

## ## Arithmetic Operations

Arithmetic built-ins operate on integer values. Arithmetic on non-integer values is a fatal error.

### ### >+

**Signature:** `(Int, Int) -> Int`

Pops two integers `(b, a)` from the AL and pushes `(a + b)`.

**Example:**

```soma
5 3 >+    ; AL: [8]
```

**Errors:** Fatal if AL has fewer than 2 values or if either value is not an integer.

---

### ### >-

**Signature:** `(Int, Int) -> Int`

Pops two integers `(b, a)` from the AL and pushes `(a - b)`.

**Example:**

```soma
10 3 >-   ; AL: [7]
```

**Errors:** Fatal if AL has fewer than 2 values or if either value is not an integer.

---

### ### >*

**Signature:** `(Int, Int) -> Int`

Pops two integers `(b, a)` from the AL and pushes `(a * b)`.

**Example:**

```soma
4 5 >*    ; AL: [20]
```

**Errors:** Fatal if AL has fewer than 2 values or if either value is not an integer.

---

### ### >/

**Signature:** `(Int, Int) -> Int`

Pops two integers `(b, a)` from the AL and pushes `(a / b)` using integer division.

**Example:**

```soma
10 3 >/   ; AL: [3]
```

**Errors:** Fatal if AL has fewer than 2 values, if either value is not an integer, or if `b` is zero.

---

## ## Comparison Operations

Comparison operators pop two values and push a Boolean result. String and integer comparisons are defined. Cross-type comparison is a fatal error.

### ### >==

**Signature:** `(Value, Value) -> Bool`

Pops two values `(b, a)` from the AL and pushes `True` if `a == b`, otherwise `False`.

**Example:**

```soma
5 5 >==       ; AL: [True]
"cat" "dog" >==   ; AL: [False]
```

**Errors:** Fatal if AL has fewer than 2 values or if types are incompatible for comparison.

---

### ### ><

**Signature:** `(Value, Value) -> Bool`

Pops two values `(b, a)` from the AL and pushes `True` if `a < b`, otherwise `False`.

**Example:**

```soma
3 5 ><        ; AL: [True]
10 2 ><       ; AL: [False]
```

**Errors:** Fatal if AL has fewer than 2 values or if types are incompatible for comparison.

---

### ### >>

**Signature:** `(Value, Value) -> Bool`

Pops two values `(b, a)` from the AL and pushes `True` if `a > b`, otherwise `False`.

**Example:**

```soma
10 5 >>       ; AL: [True]
3 7 >>        ; AL: [False]
```

**Errors:** Fatal if AL has fewer than 2 values or if types are incompatible for comparison.

---

## ## Stack Operations

Stack operations manipulate the AL structure without performing computation.

### ### >dup

**Signature:** `(Value) -> (Value, Value)`

Duplicates the top value on the AL.

**Example:**

```soma
7 >dup        ; AL: [7, 7]
```

**Errors:** Fatal if AL is empty.

---

### ### >drop

**Signature:** `(Value) -> ()`

Removes the top value from the AL.

**Example:**

```soma
1 2 3 >drop   ; AL: [1, 2]
```

**Errors:** Fatal if AL is empty.

---

### ### >swap

**Signature:** `(Value, Value) -> (Value, Value)`

Swaps the top two values on the AL.

**Example:**

```soma
1 2 >swap     ; AL: [2, 1]
```

**Errors:** Fatal if AL has fewer than 2 values.

---

### ### >over

**Signature:** `(Value, Value) -> (Value, Value, Value)`

Duplicates the second value and pushes it on top.

**Example:**

```soma
1 2 >over     ; AL: [1, 2, 1]
```

**Errors:** Fatal if AL has fewer than 2 values.

---

## Debug Operations

Debug built-ins are used for development and introspection.

### >print

**Signature: **`(Value) -> ()`

Pops the top value from the AL and displays it to standard output.

**Example:**

```soma
"Hello" >print   ; Output: Hello
42 >print        ; Output: 42
```

**Errors:** Fatal if AL is empty.

---

## Control Flow Operations

Control flow in SOMA is explicit and built from minimal primitives. These operations enable conditionals and loops.

### >choose

**Signature: **`(Bool, Value, Value) -> Value`

Pops three values 

(false_val, true_val, condition

**Behavior:**

- If `condition` is `True`, pushes `true_val`
- If `condition` is `False`, pushes `false_val`
- The selected value is pushed to AL as-is )not executed)
- To execute the result, use `>^` or `>chain` after `>choose`

**Examples:**

```soma
; Select a value
True 10 20 >choose      ; AL: [10]
False 10 20 >choose     ; AL: [20]

; Select and execute a block
5 3 ><
  { (small) >print }
  { (large) >print }
>choose >^              ; Selects { (large) >print }, then executes it

; Common pattern: select block for loop continuation
counter 10 ><
  >block                ; Continue - return current block
  Nil                   ; Stop
>choose                 ; AL: [block] or [Nil]
```

**Errors:** Fatal if AL has fewer than 3 values or if first value is not a Boolean.

---

### >chain

**Signature: **`(Value) -> ()`

Pops a value from the AL. If it's a Block, executes it and repeats )pops again). If it's not a Block, stops.

**Behavior:**

- Pops top value from AL
- If value is a Block: executes it, then repeats )pops from AL again)
- If value is NOT a Block: stops execution
- Enables loops, recursion, and state machines
- Perfect for tail-call optimization )no stack growth)

**Examples:**

```soma
; Execute a block once
{ 5 3 >+ } >chain       ; AL: [8]

; Infinite loop )block returns itself)
{
  (tick) >print
  >block                ; Push self back to AL
} >chain                ; Prints "tick" forever

; Conditional loop )using >choose)
0 !counter
{
  counter >toString >print
  counter >inc !counter
  counter 10 ><
    >block              ; Continue: push self
    Nil                 ; Stop: push Nil
  >choose
} !loop
loop >chain             ; Prints 0..9, then stops

; State machine
{ (A) >print state-b } !state-a
{ (B) >print state-c } !state-b
{ (C) >print Nil } !state-c
state-a >chain          ; Prints "A", "B", "C", stops
```

**Errors:** None )stops cleanly on non-Block values).

---

### >block

**Signature: **`() -> Block`

Pushes the currently executing block onto the AL.

**Behavior:**

- Always succeeds )execution always occurs within a block context)
- At top-level: returns the outermost block )the implicit "program" block)
- In nested blocks: returns the current block )not the parent block)
- Enables self-reference for loops and recursion
- Can be aliased like any built-in, enabling internationalization

**Examples:**

```soma
; Get current block for recursion
0 !counter
{
  counter >toString >print
  counter >inc !counter
  counter 5 ><
    >block              ; Continue: push self
    Nil                 ; Stop
  >choose
} >chain                ; Prints 0..4

; Store reference to current block
{ >block !_.me _.me }   ; Store reference in Register, push to AL

; Internationalization via aliasing
block !блок             ; Russian
block !ブロック          ; Japanese
{ (loop) >print >блок } >chain   ; Use Russian alias
```

**Errors:** None.

---

## No-Op

### >noop

**Signature: **`() -> ()`

Performs no operation. The AL is unchanged.

**Example:**

```soma
>noop         ; AL unchanged
```

**Errors:** None.

---

## Reference Table

The following table summarizes all core built-in operations:

| Built-in  | Pops | Pushes | Action                                            |
|-----------|------|--------|---------------------------------------------------|
| `>dup`    | 1    | 2      | Duplicate top value                               |
| `>drop`   | 1    | 0      | Drop top value                                    |
| `>swap`   | 2    | 2      | Swap top two values                               |
| `>over`   | 2    | 3      | Duplicate 2nd value                               |
| `>+`      | 2    | 1      | Integer addition                                  |
| `>-`      | 2    | 1      | Integer subtraction                               |
| `>*`      | 2    | 1      | Integer multiplication                            |
| `>/`      | 2    | 1      | Integer division                                  |
| `>==`     | 2    | 1      | Equality test                                     |
| `><`      | 2    | 1      | Less-than test                                    |
| `>>`      | 2    | 1      | Greater-than test                                 |
| `>choose` | 3    | 1      | Select value based on condition )doesn't execute) |
| `>chain`  | 1    | 0      | Execute blocks repeatedly until non-Block         |
| `>block`  | 0    | 1      | Push current executing block                      |
| `>print`  | 1    | 0      | Print value to stdout                             |
| `>noop`   | 0    | 0      | No operation                                      |

---

## AL Contracts

Each built-in has a fixed AL contract:

- ****AL underflow****: Attempting to pop from an empty AL is a fatal error
- ****Type mismatch****: Providing the wrong type to a built-in is a fatal error
- ****Arity violation****: Having insufficient values on the AL for an operation is a fatal error

SOMA does not attempt recovery from violations. Program correctness is the programmer's responsibility.

---

## Notes

- While built-ins could theoretically be overridden )they're just Store paths), doing so is strongly discouraged
- All built-in operations are synchronous and deterministic )except those involving external I/O)
- Built-ins operate directly on the AL and do not access the Store unless explicitly documented
- More specialized built-ins may be defined in extensions )e.g., for Things, concurrency, or I/O)


