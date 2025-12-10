# 10. Standard Library

**The SOMA standard library demonstrates the power of building complex operations from simple primitives.** Every operation in `stdlib.soma` is built using only FFI )Foreign Function Interface) primitives—the minimal set of built-ins that must be implemented by the runtime. This is SOMA's philosophy in action: start with a tiny kernel of irreducible operations, then build everything else as user-defined blocks.

**Status:** Normative

**Version:** SOMA v1.1

**Section:** 10

---

## Overview

The standard library )`stdlib.soma`) provides:

1. **Boolean Logic**:  — `not`, `and`, `or`
2. **Comparison Operators**:  — `>`, `!=!`, `==`, `=<`, `=>`
3. **Stack Manipulation**:  — `dup`, `drop`, `swap`, `over`, `rot`
4. **Arithmetic Helpers**:  — `inc`, `dec`, `abs`, `min`, `max`
5. **Control Flow Helpers**:  — `times`, `if`, `ifelse`, `^`, `while`, `do`
6. **Linked List Operations**:  — `list.new`, `list.cons`
7. **AL Draining**:  — `al.drain`

All of these are **user-defined blocks**, not language primitives. They are stored at Store paths and executed with the `>` prefix, just like any user-defined operation.

**Key insight:** The stdlib is not special. You could rewrite it, extend it, or replace it entirely. It's just SOMA code.

---

## Philosophy: FFI Primitives vs Derived Operations

### What Are FFI Primitives?

FFI primitives are the minimal operations that **must** be implemented by the SOMA runtime. These cannot be defined in SOMA itself because they require access to the machine's underlying execution model.

**FFI primitives include:**

- Stack operations: `>dup`, `>drop`, `>swap`, `>over` )as built from Register operations)Arithmetic: `>+`, `>-`, `>*`, `>/`Comparison: `><` )less-than), `>==` )equality)Control flow: `>choose`, `>chain`, `>block`I/O: `>print`, `>dump`Type introspection: `>type`, `>id`

These are the **irreducible kernel** of SOMA. Everything else is emergent.

### What Are Derived Operations?

Derived operations are **user-defined blocks** built from FFI primitives. They feel like built-ins, but they're not. They're stored at Store paths and executed with `>`.

**The stdlib provides derived operations like:**

- `>not` — Boolean negation )built from `>choose`)`>and` — Logical AND )built from `>choose` and `>drop`)`>>` — Greater-than )built from `>swap` and `><`)`>dup` — Duplicate top )built from Register operations)`>times` — Execute block N times )built from `>chain` and `>choose`)

This demonstrates SOMA's **compositional power**: complex behavior emerges from simple primitives.

---

## 1. Boolean Logic

Boolean logic operations transform `True`/`False` values on the AL. All three operations )`not`, `and`, `or`) are built using only `>choose`.

### 1.1 `>not` — Boolean Negation

**Signature:** `(Bool) -> Bool`

#### Definition:

```soma
{False True >choose} !not
```

#### Semantics:

Pops a Boolean from the AL and pushes its negation.

#### AL Transformation:

```
Before: [True, ...]
After:  [False, ...]

Before: [False, ...]
After:  [True, ...]
```

#### How It Works:

1. The block `{False True >choose}` is stored at Store path `not`
2. When executed via `>not`:
  - The top value (a Boolean) is on the AL
  - `False` is pushed onto AL
  - `True` is pushed onto AL
  - `>choose` pops the boolean and both values, selecting based on the boolean:
    - If boolean was `True`: selects `False` (the false-branch value)
    - If boolean was `False`: selects `True` (the true-branch value)
3. Result: the Boolean is inverted

#### Example:

```soma
True >not     ; AL: [False]
False >not    ; AL: [True]
```

#### Usage Example:

```soma
) Negate a condition
user.logged_in >not
  { "Please log in" >print }
  { }
>choose
```

**Note:** This is **direct value selection** — `>choose` selects between the two literal values `False` and `True` without executing them as blocks.

---

### 1.2 `>and` — Logical AND

**Signature:** `(Bool, Bool) -> Bool`

**Definition:**

```soma
{False >choose} !and

```

**Semantics:**

Pops two Booleans `(b, a)` and pushes `True` if both are `True`, otherwise `False`.

**AL Transformation:**

```
Before: [True, True, ...]
After:  [True, ...]

Before: [True, False, ...] or [False, True, ...] or [False, False, ...]
After:  [False, ...]

```

**How It Works:**

1. Two Booleans are on the AL: `b` (top), `a` (second)
2. The `and` block executes:
  - Pushes `False` onto AL: `[b, a, False]`
  - `>choose` pops `False`, pops `b`, pops `a`
  - If `a` is `True`: selects `b` (the false-branch value)
    - Result: `True` if b is True, `False` if b is False
  - If `a` is `False`: selects `False` (the true-branch value)
    - Result: `False`

**Truth Table:**

| a     | b     | Result |
|-------|-------|--------|
| True  | True  | True   |
| True  | False | False  |
| False | True  | False  |
| False | False | False  |

**Example:**

```soma
True True >and      ; AL: [True]
True False >and     ; AL: [False]
False True >and     ; AL: [False]
False False >and    ; AL: [False]

```

**Usage Example:**

```soma
) Check two conditions
user.logged_in user.premium >and
  { premium_feature >enable }
  { "Premium required" >print }
>choose

```

**Note on Short-Circuiting:**

SOMA's `>and` is **not short-circuiting**. Both operands must be evaluated before calling `>and`. For short-circuit behavior, use explicit `>choose` with `>^`:

```soma
) Short-circuit AND
condition_a
  { condition_b { action } {} >choose >^ }
  { }
>choose >^

```

---

### 1.3 `>or` — Logical OR

**Signature:** `(Bool, Bool) -> Bool`

**Definition:**

```soma
{True >swap >choose} !or

```

**Semantics:**

Pops two Booleans `(b, a)` and pushes `True` if either is `True`, otherwise `False`.

**AL Transformation:**

```
Before: [False, False, ...]
After:  [False, ...]

Before: [True, False, ...] or [False, True, ...] or [True, True, ...]
After:  [True, ...]

```

**How It Works:**

1. Two Booleans are on the AL: `b` (top), `a` (second)
2. The `or` block executes:
  - Pushes `True` onto AL: `[b, a, True]`
  - `>swap` swaps top two: `[True, a, b]`
  - `>choose` pops `b`, pops `a`, pops `True`
  - If `a` is `True`: selects `True` (the true-branch value)
    - Result: `True`
  - If `a` is `False`: selects `b` (the false-branch value)
    - Result: `True` if b is True, `False` if b is False

**Truth Table:**

| a     | b     | Result |
|-------|-------|--------|
| True  | True  | True   |
| True  | False | True   |
| False | True  | True   |
| False | False | False  |

**Example:**

```soma
True True >or       ; AL: [True]
True False >or      ; AL: [True]
False True >or      ; AL: [True]
False False >or     ; AL: [False]

```

**Usage Example:**

```soma
) Check if either condition is true
user.admin user.moderator >or
  { admin_panel >show }
  { }
>choose

```

---

## 2. Comparison Operators

The stdlib extends the FFI primitive `><` )less-than) to provide a complete set of comparison operators.

### 2.1 `>>` — Greater-Than

**Signature:** `(Value, Value) -> Bool`

#### Definition:

```soma
{>swap ><} !>
```

#### Semantics:

Pops two values `(b, a)` and pushes `True` if `a > b`, otherwise `False`.

#### AL Transformation:

```
Before: [5, 10, ...]
After:  [True, ...]    ; 10 > 5

Before: [10, 5, ...]
After:  [False, ...]   ; 5 > 10
```

#### How It Works:

1. Two values on AL: `b` (top), `a` (second)`>swap` swaps them: AL becomes `[a, b, ...]``><` computes `a < b`Result: `a > b` is equivalent to `b < a` (which is what we computed)

**Wait, that's backwards!** Let's trace this more carefully:

#### Corrected trace:

1. Initial AL: `[b, a, ...]` where we want to test `a > b`We want: `True` if `a > b`Note: `a > b` is the same as `b < a``>swap` gives us: `[a, b, ...]``><` pops `(b, a)` and computes `a < b`

**Actually, this needs reconsideration.** Let's verify against the definition of `><`:

From `06-builtins.md`: `><` pops `(b, a)` and pushes `True` if `a < b`.

So for `>>`:

- Initial: `[b, a, ...]`Want: `a > b``>swap`: `[a, b, ...]``><`: pops `(b, a)` (so now `a` is second, `b` is top after swap... wait, that's confusing)

Let me trace with concrete values:

```
10 5        ; AL: [5, 10]   ; We want to test 10 > 5
>>          ; Execute: {>swap ><}
  >swap     ; AL: [10, 5]
  ><        ; Pops (5, 10), tests 10 < 5 → False
```

**Hmm, that's wrong.** Let me re-read the FFI definition more carefully...

Actually, the issue is operator order. In SOMA: `a b >op` means `op(b, a)` where the second-popped value is the left operand.

So: `10 5 ><` means "pop 5, pop 10, compute 10 < 5" → `False`.

And: `10 5 >>` should mean "pop 5, pop 10, compute 10 > 5" → `True`.

Let's trace `>>` again:

```
10 5        ; AL: [5, 10]
>>          ; Execute: {>swap ><}
  >swap     ; AL: [10, 5]
  ><        ; Pop 5, pop 10, compute 10 < 5 → False
```

**Still wrong!** The issue is: we want `10 > 5` to be `True`, but we're getting `False`.

Let me check the stdlib source again... Ah! The definition is:

```soma
{>swap ><} !>
```

So the Store path is `>`, not `>>`. Let me reconsider the notation.

#### Operator Naming:

- The built-in less-than is stored at path `<`Executed as `><`The stdlib greater-than is stored at path `>`Executed as `>>`

#### Let me trace again with the correct understanding:

To compute `10 > 5`:

```
10 5        ; AL: [5, 10]   (10 is second, 5 is top)
>>          ; Execute block stored at `>`
            ; Block is: {>swap ><}
  >swap     ; AL: [10, 5]   (now 10 is top, 5 is second)
  ><        ; Pop (5, 10), compute: 10 < 5 → False
```

**Still wrong!** Let me check if I'm understanding the pop order correctly.

From `06-builtins.md`: `><` pops `(b, a)` and tests `a < b`.

So `><` pops in this order: first pop is `b`, second pop is `a`, test is `a < b`.

```
10 5        ; AL: [5, 10]
><          ; First pop: b = 5, second pop: a = 10, test: 10 < 5 → False
```

So `10 5 ><` tests if `10 < 5` → `False`. Correct.

Now for `>>`:

```
10 5        ; AL: [5, 10]
>>          ; Execute: {>swap ><}
  >swap     ; AL: [10, 5]  (swapped)
  ><        ; First pop: b = 5, second pop: a = 10, test: 10 < 5 → False
```

**This is still wrong!** I'm misunderstanding something.

Let me think about what we want: `a > b` is equivalent to `b < a`.

```
Initial: a = 10, b = 5
We want: a > b = 10 > 5 = True
Equivalent to: b < a = 5 < 10 = True
```

So if initial AL is `[b, a, ...]` (i.e., `[5, 10, ...]`):

- After `>swap`: AL is `[a, b, ...]` (i.e., `[10, 5, ...]`)After `><`: pops `(5, 10)`, tests `10 < 5` → `False`

**I see the problem!** After swap, the AL is `[10, 5]` where `10` is top and `5` is second.

When `><` pops `(b, a)`:

- First pop: `b = 10` (the top)Second pop: `a = 5` (the second)Test: `a < b` = `5 < 10` = `True`

**Ah!** So:

```
10 5        ; AL: [5, 10]  (10 is second, 5 is top)
>>          ; Execute: {>swap ><}
  >swap     ; AL: [10, 5]  (10 is top, 5 is second)
  ><        ; Pop b=10 (top), pop a=5 (second), test: 5 < 10 → True
```

But wait, we wanted `10 > 5`, and `5 < 10` is `True`, so that's correct!

Let me verify my understanding one more time:

**Stack notation:** `[top, second, third, ...]` (top is leftmost)

```
10 5        ; Push 10, then push 5
            ; AL: [5, 10, ...]  (5 is top, 10 is second)
            ; We want to test: 10 > 5 (i.e., second > top)
>>
  >swap     ; AL: [10, 5, ...]  (10 is top, 5 is second)
  ><        ; Pop top=10 into b, pop second=5 into a, test: a < b = 5 < 10 = True
```

**Perfect!** So `10 5 >>` correctly tests `10 > 5` and returns `True`.

#### How It Works (corrected):

1. AL has `[b, a, ...]` where we want to test `a > b`Note: `a > b` ⟺ `b < a``>swap` reverses the order: `[a, b, ...]``><` pops top first (gets `a`), second (gets `b`), and tests `b < a`Result: `b < a` which is equivalent to `a > b`

**Wait, I'm confusing myself again.** Let me use the stdlib's own naming:

The stack in SOMA notation has the rightmost value as top:

```
a b         ; AL: [..., a, b]  where b is top
```

When `><` pops `(b, a)`:

- First value popped is top: `b`Second value popped: `a`Tests: `a < b`

So `a b ><` tests `a < b`.

For `>>`:

```
a b         ; AL: [..., a, b]
>>          ; Execute: {>swap ><}
  >swap     ; AL: [..., b, a]
  ><        ; Pop (a, b), test: b < a
```

So `a b >>` tests `b < a`, which is equivalent to `a > b`. **Correct!**

Concrete example:

```
10 5 >>     ; Test: 10 > 5
            ; After swap: 5 10
            ; Test: 5 < 10 → True ✓
```

#### Example:

```soma
10 5 >>         ; AL: [True]   (10 > 5)
5 10 >>         ; AL: [False]  (5 > 10)
5 5 >>          ; AL: [False]  (5 > 5)
```

#### Usage Example:

```soma
score 100 >>
  { "High score!" >print }
  { }
>choose
```

---

### 2.2 `>!=!` — Not Equal (Inequality)

**Signature:** `(Value, Value) -> Bool`

#### Definition:

```soma
{>over >over >swap >< >rot >rot >< >or} !=!
```

#### Semantics:

Pops two values `(b, a)` and pushes `True` if `a ≠ b`, otherwise `False`.

#### AL Transformation:

```
Before: [5, 10, ...]
After:  [True, ...]    ; 10 ≠ 5

Before: [5, 5, ...]
After:  [False, ...]   ; 5 = 5
```

#### How It Works:

The key insight: `a ≠ b` means `(a < b) OR (b < a)`.

Step-by-step execution:

```
a b             ; AL: [..., a, b]
>over >over     ; AL: [..., a, b, a, b]
>swap           ; AL: [..., a, b, b, a]
><              ; AL: [..., a, b, (b < a)]  ; Call this X
>rot            ; AL: [..., b, X, a]
>rot            ; AL: [..., X, a, b]
><              ; AL: [..., X, (a < b)]     ; Call this Y
>or             ; AL: [..., X OR Y]
```

Final result: `(b < a) OR (a < b)` which is `True` iff `a ≠ b`.

#### Example:

```soma
5 10 >!=!       ; AL: [True]   (5 ≠ 10)
5 5 >!=!        ; AL: [False]  (5 = 5)
```

#### Usage Example:

```soma
current_value expected_value >!=!
  { "Values don't match!" >print }
  { }
>choose
```

**Note:** This implementation only works for types that support `><`. For a more general inequality test, see `>==` and `>not` composition.

---

### 2.3 `>==` — Equality

**Signature:** `(Value, Value) -> Bool`

#### Definition:

```soma
{>=! >not} !==
```

#### Semantics:

Pops two values `(b, a)` and pushes `True` if `a = b`, otherwise `False`.

#### AL Transformation:

```
Before: [5, 5, ...]
After:  [True, ...]

Before: [5, 10, ...]
After:  [False, ...]
```

#### How It Works:

1. `>=!` tests if values are not equal`>not` negates the resultResult: `NOT (a ≠ b)` = `a = b`

#### Example:

```soma
5 5 >==         ; AL: [True]
5 10 >==        ; AL: [False]
"cat" "cat" >== ; AL: [True]
```

#### Usage Example:

```soma
user.role "admin" >==
  { admin_panel >show }
  { }
>choose
```

**Note:** This builds on `>=!`, which uses `><` internally. For types without ordering (like some custom types), you'd need a different implementation (possibly using FFI `>==` directly if available).

---

### 2.4 `>=<` — Less-Than-Or-Equal

**Signature:** `(Value, Value) -> Bool`

#### Definition:

```soma
{>swap >< >not} !=<
```

#### Semantics:

Pops two values `(b, a)` and pushes `True` if `a ≤ b`, otherwise `False`.

#### AL Transformation:

```
Before: [10, 5, ...]
After:  [True, ...]    ; 5 ≤ 10

Before: [5, 5, ...]
After:  [True, ...]    ; 5 ≤ 5

Before: [5, 10, ...]
After:  [False, ...]   ; 10 ≤ 5
```

#### How It Works:

1. We want: `a ≤ b`Equivalent to: `NOT (a > b)`Equivalent to: `NOT (b < a)``>swap`: gives us `[a, b]``><`: tests `b < a``>not`: negates to get `NOT (b < a)` = `a ≤ b`

#### Example:

```soma
5 10 >=<        ; AL: [True]   (5 ≤ 10)
10 10 >=<       ; AL: [True]   (10 ≤ 10)
10 5 >=<        ; AL: [False]  (10 ≤ 5)
```

#### Usage Example:

```soma
temperature 32 >=<
  { "Freezing or below" >print }
  { }
>choose
```

---

### 2.5 `>=>` — Greater-Than-Or-Equal

**Signature:** `(Value, Value) -> Bool`

#### Definition:

```soma
{>< >not} !=>
```

#### Semantics:

Pops two values `(b, a)` and pushes `True` if `a ≥ b`, otherwise `False`.

#### AL Transformation:

```
Before: [5, 10, ...]
After:  [True, ...]    ; 10 ≥ 5

Before: [5, 5, ...]
After:  [True, ...]    ; 5 ≥ 5

Before: [10, 5, ...]
After:  [False, ...]   ; 5 ≥ 10
```

#### How It Works:

1. We want: `a ≥ b`Equivalent to: `NOT (a < b)``><`: tests `a < b``>not`: negates to get `NOT (a < b)` = `a ≥ b`

#### Example:

```soma
10 5 >=>        ; AL: [True]   (10 ≥ 5)
5 5 >=>         ; AL: [True]   (5 ≥ 5)
5 10 >=>        ; AL: [False]  (5 ≥ 10)
```

#### Usage Example:

```soma
user.age 18 >=>
  { "Access granted" >print }
  { "Must be 18 or older" >print }
>choose
```

---

## 3. Stack Manipulation

Stack operations are built using the Register as temporary storage. This demonstrates how AL manipulation can be implemented using Register paths.

### 3.1 `>dup` — Duplicate Top

**Signature:** `(Value) -> (Value, Value)`

#### Definition:

```soma
{!_.value _.value _.value} !dup
```

#### Semantics:

Duplicates the top value on the AL.

#### AL Transformation:

```
Before: [x, ...]
After:  [x, x, ...]
```

#### How It Works:

1. `!_.value`: Pop top value, store at Register path `value``_.value`: Read from Register, push onto AL`_.value`: Read from Register again, push onto ALResult: two copies of the original value

#### Example:

```soma
42 >dup         ; AL: [42, 42]
"hello" >dup    ; AL: ["hello", "hello"]
```

#### Usage Example:

) Duplicate a value for multiple uses
x >dup >dup >* >*    ; Compute x³ (x * x * x)**Note:** Each execution of `>dup` gets its own isolated Register, so `_.value` is local to that execution.

---

### 3.2 `>drop` — Remove Top

**Signature:** `(Value) -> ()`

#### Definition:

```soma
{!_} !drop
```

#### Semantics:

Removes the top value from the AL.

#### AL Transformation:

```
Before: [x, ...]
After:  [...]
```

#### How It Works:

1. `!_`: Pop top value and store at Register rootBlock ends without pushing anything backResult: value is discarded

#### Example:

```soma
1 2 3 >drop     ; AL: [1, 2]
```

#### Usage Example:

---

### 3.3 `>swap` — Swap Top Two

**Signature:** `(a, b) -> (b, a)`

#### Definition:

```soma
{!_.a !_.b _.a _.b} !swap
```

#### Semantics:

Swaps the top two values on the AL.

#### AL Transformation:

```
Before: [b, a, ...]
After:  [a, b, ...]
```

#### How It Works:

1. `!_.a`: Pop top (b), store as `_.a``!_.b`: Pop second (a), store as `_.b``_.a`: Push b`_.b`: Push aResult: order reversed

#### Example:

```soma
1 2 >swap       ; AL: [2, 1]
"a" "b" >swap   ; AL: ["b", "a"]
```

#### Usage Example:

---

### 3.4 `>over` — Copy Second to Top

**Signature:** `(a, b) -> (a, b, a)`

#### Definition:

```soma
{!_.a !_.b _.b _.a _.b} !over
```

#### Semantics:

Copies the second value and pushes it on top.

#### AL Transformation:

```
Before: [b, a, ...]
After:  [b, a, b, ...]
```

#### How It Works:

1. `!_.a`: Pop top (b), store as `_.a``!_.b`: Pop second (a), store as `_.b``_.b`: Push a`_.a`: Push b`_.b`: Push a againResult: `[b, a, b]` with second value duplicated on top

#### Example:

```soma
1 2 >over       ; AL: [1, 2, 1]
```

#### Usage Example:

---

### 3.5 `>rot` — Rotate Top Three

**Signature:** `(a, b, c) -> (b, a, c)`

**Definition:**

```soma
{!_.a !_.b !_.c _.b _.a _.c} !rot
```

**Semantics:**

Rotates the top three values, moving the third value to the top.

**AL Transformation:**

```
Before: [c, b, a, ...]
After:  [b, a, c, ...]
```

**How It Works:**

1. **`!_.a`**: Pop top (c)
2. **`!_.b`**: Pop second (b)
3. **`!_.c`**: Pop third (a)
4. **`_.b`**: Push b
5. **`_.a`**: Push c
6. **`_.c`**: Push a
7. **Result**: rotated order

**Example:**

```soma
1 2 3 >rot      ; AL: [2, 1, 3]
```

**Usage Example:**

```soma
) Rearrange three values
a b c >rot      ; Bring third value to top
```

---

## 4. Arithmetic Helpers

Arithmetic helpers build on the FFI primitives `>+`, `>-`, `>*`, `>/` to provide common operations.

### 4.1 `>inc` — Increment by 1

**Signature:** `(Int) -> Int`

**Definition:**

```soma
{1 >+} !inc
```

**Semantics:**

Pops an integer and pushes its value plus 1.

**AL Transformation:**

```
Before: [n, ...]
After:  [n+1, ...]
```

**How It Works:**

1. Push `1` onto AL
2. `>+` adds top two values
3. Result: original value incremented

**Example:**

```soma
5 >inc          ; AL: [6]
0 >inc          ; AL: [1]
-1 >inc         ; AL: [0]
```

**Usage Example:**

```soma
) Increment a counter
counter >inc !counter
```

---

### 4.2 `>dec` — Decrement by 1

**Signature:** `(Int) -> Int`

**Definition:**

```soma
{1 >-} !dec
```

**Semantics:**

Pops an integer and pushes its value minus 1.

**AL Transformation:**

```
Before: [n, ...]
After:  [n-1, ...]
```

**How It Works:**

1. Push `1` onto AL
2. `>-` subtracts: computes `n - 1`
3. Result: original value decremented

**Example:**

```soma
5 >dec          ; AL: [4]
0 >dec          ; AL: [-1]
```

**Usage Example:**

```soma
) Decrement a counter
counter >dec !counter
```

---

### 4.3 `>abs` — Absolute Value

**Signature:** `(Int) -> Int`

**Definition:**

```soma
{>dup 0 >< {0 >swap >-} {} >choose >^} !abs
```

**Semantics:**

Pops an integer and pushes its absolute value.

**AL Transformation:**

```
Before: [n, ...]
After:  [|n|, ...]
```

**How It Works:**

1. `>dup`: Duplicate the value → `[n, n]`
2. `0 ><`: Test if `n < 0` → `[n, bool]`
3. `{0 >swap >-} {}`: Push the two branch blocks
4. `>choose`: Selects based on bool:
  - If `True` (n is negative): selects `{0 >swap >-}`
  - If `False` (n is non-negative): selects `{}` (empty block)
5. `>^`: Executes the selected block
  - If negative: computes `0 - n` = `-n` (positive)
  - If non-negative: does nothing, value remains
6. Result: non-negative value

**Example:**

```soma
-5 >abs         ; AL: [5]
5 >abs          ; AL: [5]
0 >abs          ; AL: [0]
```

**Usage Example:**

```soma
) Compute distance
a b >- >abs     ; |a - b|
```

---

### 4.4 `>min` — Minimum of Two Values

**Signature:** `(Int, Int) -> Int`

**Definition:**

```soma
{>over >over >< {>drop} {>swap >drop} >choose >^} !min
```

**Semantics:**

Pops two integers `(b, a)` and pushes the smaller value.

**AL Transformation:**

```
Before: [b, a, ...]
After:  [min(a, b), ...]
```

**How It Works:**

1. `>over >over`: Duplicate both values → `[b, a, b, a]`
2. `><`: Test `a < b` → `[b, a, bool]`
3. `{>drop} {>swap >drop}`: Push the two branch blocks
4. `>choose`: Selects based on bool:
  - If `True` (a < b): selects `{>drop}`
  - If `False` (a ≥ b): selects `{>swap >drop}`
5. `>^`: Executes the selected block
  - If a < b: drops top (b), keeps a
  - If a ≥ b: swaps then drops, keeps b

Step-by-step execution with concrete values:

```
3 7                    ; AL: [7, 3]    (want min = 3)
>over                  ; AL: [7, 3, 7]
>over                  ; AL: [7, 3, 7, 3]
><                     ; Pop (3, 7), test: 7 < 3 → False
                       ; AL: [7, 3, False]
{>drop} {>swap >drop} >choose
                       ; Pops: {>swap >drop}, {>drop}, False
                       ; Leaves: [7, 3]
                       ; Selects: {>swap >drop} (false branch)
>^                     ; Executes the selected block
  >swap                ; AL: [3, 7]
  >drop                ; AL: [3]
                       ; Result: 3 ✓
```

Verify with opposite order:

```
7 3                    ; AL: [3, 7]    (want min = 3)
>over                  ; AL: [3, 7, 3]
>over                  ; AL: [3, 7, 3, 7]
><                     ; Pop (7, 3), test: 3 < 7 → True
                       ; AL: [3, 7, True]
{>drop} {>swap >drop} >choose
                       ; Selects: {>drop} (true branch)
                       ; AL: [3, 7]
>^                     ; Executes the selected block
  >drop                ; AL: [3]
                       ; Result: 3 ✓
```

**Example:**

```soma
5 3 >min        ; AL: [3]
3 5 >min        ; AL: [3]
5 5 >min        ; AL: [5]
```

**Usage Example:**

```soma
) Clamp value to maximum
value limit >min
```

---

### 4.5 `>max` — Maximum of Two Values

**Signature:** `(Int, Int) -> Int`

**Definition:**

```soma
{>over >over >> {>drop} {>swap >drop} >choose >^} !max
```

**Semantics:**

Pops two integers `(b, a)` and pushes the larger value.

**AL Transformation:**

```
Before: [b, a, ...]
After:  [max(a, b), ...]
```

**How It Works:**

Similar to `>min`, but uses `>>` (greater-than) instead of `><`:

1. `>over >over`: Duplicate both → `[b, a, b, a]`
2. `>>`: Test `a > b` → `[b, a, bool]`
3. `{>drop} {>swap >drop}`: Push the two branch blocks
4. `>choose`: Selects based on bool:
  - If `True` (a > b): selects `{>drop}` → keep a
  - If `False` (a ≤ b): selects `{>swap >drop}` → keep b
5. `>^`: Executes the selected block

**Example:**

```soma
5 3 >max        ; AL: [5]
3 5 >max        ; AL: [5]
5 5 >max        ; AL: [5]
```

**Usage Example:**

```soma
) Ensure minimum value
value minimum >max
```

---

## 5. Control Flow Helpers

These are high-level control flow abstractions built on top of `>choose` and `>chain`.

### 5.1 `>times` — Execute Block N Times

**Signature:** `[n, block, ...] -> [...]`

**Definition:**

```soma
{
  {
    !_.user_blk !_.cnt
    >_.user_blk
    _.cnt 1 >-
    !_.new_cnt
    _.new_cnt _.user_blk
    >block
    0 _.new_cnt ><
    {}
    {>drop >drop >drop Nil}
    >choose
  } >chain
  >drop
} !times
```

**Semantics:**

Executes a block N times. Consumes count and block from AL.

**AL Transformation:**

```
Before: [N, {body}, ...]
After:  [...]
```

**How It Works:**

This is a sophisticated loop built using `>chain` and `>choose`. Let's trace it:

1. Outer block executes an inner block via `>chain`, then drops result
2. Inner block (the loop body):
  - Pops block and count from AL, stores in Register
  - Executes user block (`>_.user_blk`)
  - Decrements count (`_.cnt 1 >-`)
  - Stores new count
  - Pushes new count and block back onto AL
  - Pushes self (`>block`) onto AL
  - Tests if count > 0 (`0 _.new_cnt ><`)
  - Pushes empty block `{}` and cleanup block `{>drop >drop >drop Nil}`
  - `>choose` selects based on the test:
    - If true: selects empty block (continue loop via `>chain`)
    - If false: selects cleanup block
  - `>^` executes the selected block
3. Loop continues until count reaches 0

**Example:**

```soma
3 { "Hello" >print } >times
```

Output:

```
Hello
Hello
Hello
```

**Usage Example:**

```soma
) Print numbers 1 to 10
10 { counter >print counter >inc !counter } >times
```

**Note:** Variables referenced in the block body must be in the Store (like `counter`), not in Register paths, due to Register isolation between block executions.

---

### 5.2 `>if` — Conditional Execution

**Signature:** `[condition, block, ...] -> [...]`

**Definition:**

```soma
{{} >choose >^} !if
```

**Semantics:**

Executes a block if condition is true, otherwise does nothing.

**AL Transformation:**

```
Before: [True, {body}, ...]
After:  [<result of body>, ...]

Before: [False, {body}, ...]
After:  [...]
```

**How It Works:**

1. AL has: `[block, bool]`
2. Push empty block: `[block, bool, {}]`
3. `>choose` selects:
  - If `bool` is `True`: pushes `block` onto AL
  - If `bool` is `False`: pushes `{}` (empty block) onto AL
4. `>^` executes the selected block from the AL

**Example:**

```soma
True { "Executed" >print } >if     ; Prints: Executed
False { "Not executed" >print } >if ; Prints nothing
```

**Usage Example:**

```soma
user.authenticated { show_dashboard } >if
```

---

### 5.3 `>ifelse` — Conditional with Both Branches

- **Signature:**: `[(condition, true_block, false_block, ...] -> [...]`

Definition:

```soma
{>choose >^} !ifelse
```

Semantics:

Executes one of two blocks based on a boolean. This is the select-then-execute pattern.

AL Transformation:

```
Before: [True, {true_body}, {false_body}, ...]
After:  [<result of true_body>, ...]

Before: [False, {true_body}, {false_body}, ...]
After:  [<result of false_body>, ...]
```

How It Works:

1. AL has: `[false_block, true_block, bool]`
2. `>choose` selects based on bool:
  - If `True`: pushes `true_block` onto AL
  - If `False`: pushes `false_block` onto AL
3. `>^` executes the selected block from the AL

Example:

```soma
x 0 >< { "positive" } { "not positive" } >ifelse
```

Usage Example:

```soma
score 60 >=>
  { "Pass" >print }
  { "Fail" >print }
>ifelse
```

---

### 5.4 `>^` — Execute from AL

- **Signature:**: `[block, ...] -> [<result of block>, ...]`

Definition:

```soma
{!_ >_} !^
```

Semantics:

Pops a block from the AL and executes it. Like Forth's `EXECUTE`.

AL Transformation:

```
Before: [{body}, ...]
After:  [<result of body>, ...]
```

How It Works:

1. `!_`: Pop block from AL, store at Register root
2. `>_`: Execute block from Register root
3. Result: block's effects on AL

Example:

```soma
{ 2 3 >+ } >^       ; AL: [5]
print >^            ; Executes print block (pops and prints value)
```

Usage Example:

```soma
) Store operation in variable and execute later
add !_.operation
5 3 _.operation >^  ; AL: [8]
```

Dynamic Dispatch:

```soma
) Define operations
{ 10 >+ } !ops.add_ten
{ 2 >* } !ops.double

) Dispatch based on name
"add_ten" !_.op_name
"ops." _.op_name >concat >Store.get >^
```

This is **user-defined execution** — SOMA has no built-in `EXECUTE` primitive!

---

### 5.5 `>while` — Loop While Condition Is True

- **Signature:**: `[cond_block, body_block, ...] -> [...]`

Definition:

```soma
{
  {
    !_.body !_.cond
    _.cond _.body                 ) Push state back onto AL
    >block                        ) Push loop block
    >_.cond                       ) Execute condition LAST so bool is on top
    {
      !_.loop !_.body !_.cond     ) Pop state from AL (choose already popped)
      >_.body                     ) Execute body
      _.cond _.body _.loop        ) Push state back for next iteration
    }
    {>drop >drop >drop Nil}       ) False: cleanup
    >choose
  } >chain
  >drop
} !while
```

Semantics:

Loops while a condition block returns `True`.

AL Transformation:

```
Before: [{condition}, {body}, ...]
After:  [...]
```

How It Works:

This is a sophisticated while loop that:

1. Stores condition and body blocks in the loop's Register
2. On each iteration:
  - Pushes condition and body back onto AL
  - Pushes self-reference (`>block`)
  - Executes condition block (leaving boolean on AL)
  - Pushes continuation block and cleanup block
  - `>choose` selects based on boolean:
    - If `True`: selects continuation block (executes body and continues)
    - If `False`: selects cleanup block
  - `>^` executes the selected block

Example:

```soma
0 !counter
{ counter 5 >< }           ; condition
{ counter >print counter >inc !counter }  ; body
>while
```

Output:

```
0
1
2
3
4
```

Usage Example:

```soma
) Read until sentinel
{ input "quit" >== >not }
{ user_input >read !input input >process }
>while
```

- **Note**: Variables like `counter` and `input` must be Store paths (not Register paths) so that the condition and body blocks can access them.

---

### 5.6 `>do` — Execute Body First, Then Loop While True

- **Signature:**: `[body_block, cond_block, ...] -> [...]`

Definition:

```soma
{
  {
    !_.cond !_.body
    >_.body                       ) Execute body first
    _.body _.cond                 ) Push state back onto AL
    >block                        ) Push loop block
    >_.cond                       ) Execute condition LAST so bool is on top
    {}                            ) True: empty (state already on AL)
    {>drop >drop >drop Nil}       ) False: cleanup
    >choose
  } >chain
  >drop
} !do
```

Semantics:

Executes body, then loops while condition is true. Body always executes at least once.

AL Transformation:

```
Before: [{body}, {condition}, ...]
After:  [...]
```

How It Works:

Similar to `>while`, but executes body **before** testing condition:

1. Stores body and condition in Register
2. Executes body immediately
3. Pushes state and self-reference
4. Tests condition (leaving boolean on AL)
5. Pushes empty block and cleanup block
6. `>choose` selects based on boolean:
  - If `True`: selects empty block (continues loop)
  - If `False`: selects cleanup block
7. `>^` executes the selected block

Example:

```soma
0 !count
{ count >print count >inc !count }  ; body (executed first)
{ count 3 >< }                      ; condition
>do
```

Output:

```
0
1
2
```

Usage Example:

```soma
) Prompt until valid input
{ "Enter password: " >print user_input >read !password }
{ password >validate }
>do
```

- **Key Difference from **: `>while`The body executes **at least once**, even if condition is initially false.

---

## 6. Linked List Operations

SOMA's linked list operations demonstrate the power of CellRefs and the context-passing pattern. Lists are built using pure CellRef structures stored in block Registers, yet they persist after the block exits because CellRefs are first-class values.

### 6.1 `>list.new` — Create Empty List

- **Signature:**: `() -> Nil`

Definition:

```soma
{
  Nil
} !list.new
```

Semantics:

Creates an empty list, represented by `Nil`.

AL Transformation:

```
Before: [...]
After:  [Nil, ...]
```

How It Works:

Simply pushes `Nil` onto the AL to represent an empty list.

Example:

```soma
>list.new        ; AL: [Nil]
!my_list         ; Store empty list
```

Usage Example:

```soma
) Start with empty list
>list.new !items
```

---

### 6.2 `>list.cons` — Prepend Value to List

- **Signature:**: `(Value, List) -> CellRef`

Definition:

```soma
{
  !_.list !_.value  ) Pop list first (top), then value
  _.value !_.node.value
  _.list !_.node.next
  _.node.  ) Return CellRef to the node (persists after block!)
} !list.cons
```

Semantics:

Creates a new list node containing `value` with `next` pointing to the existing `list`. This is the classic functional programming `cons` operation—prepending a value to the front of a list (like pushing onto a stack).

AL Transformation:

```
Before: [list, value, ...]
After:  [new_node_ref, ...]
```

List Structure:

Each node is a CellRef with two fields:

- **`.value`**: The data stored in this node
- **`.next`**: CellRef to the next node (or `Nil` for end of list)

How It Works:

1. The block receives `value` and `list` on the AL
2. Stores both in the block's Register
3. Creates a new node structure: `_.node.value` and `_.node.next`
4. Returns `_.node.` (CellRef to the node root)
5. **Key insight:** The CellRef persists even after the block exits!

Example:

```soma
) Build list: (a, b, c)
Nil
(c) >swap >list.cons
!list1

(b) list1 >list.cons
!list2

(a) list2 >list.cons
!my_list

) Access list elements
my_list.value         ; AL: [(a)]
my_list.next.value    ; AL: [(b)]
my_list.next.next.value ; AL: [(c)]
my_list.next.next.next >isNil ; AL: [True]
```

Usage Example:

```soma
) Build a list of numbers
>list.new
3 >swap >list.cons
2 >swap >list.cons
1 >swap >list.cons
!numbers
; numbers represents: 1 -> 2 -> 3 -> Nil
```

Stack-Based Operation:

Notice that `list.cons` operates like a stack push: each new value goes to the front. This makes it perfect for accumulating items in reverse order, which is exactly what `al.drain` does.

Why CellRefs Persist:

When a block returns `_.node.`, it's returning a **reference** to a Cell in its Register. Even though the Register is local to the block execution, the CellRef itself is a first-class value that can be stored and passed around. The referenced Cell continues to exist as long as there's a reference to it.

---

## 7. AL Draining Operations

AL draining is a powerful pattern for processing all values on the AL using a user-supplied action block. It demonstrates advanced context-passing and state transformation.

### 7.1 `>al.drain` — Drain AL with Action Block

- **Signature:**: `[Void, item1, item2, ..., itemN, persistent, action_block, ...] -> [...]`

Definition:

```soma
{
  {
    !_.todo !_.persistent !_.current    ) Pop action, persistent, current

    ) Put context on AL for choose blocks
    _.
    _.current >isVoid                   ) Check: AL=[bool, CTX, ...rest]
    {
      ) Void - cleanup and stop
      >drop                             ) Drop context
      Nil                               ) Stop chain
    }
    {
      ) Not void - process and continue
      !_.                               ) Pop context
      _.current _.persistent _.todo >^  ) Execute action with args
      _.persistent _.todo               ) Push state for next iteration
      loop                              ) AL=[loop, todo, persistent, ...rest]
    }
    >choose
  } !loop

  loop >^
  >chain
  >drop
} !al.drain
```

Semantics:

Pops values from the AL one at a time until encountering `Void`, executing an action block for each value. The action block receives the current item and a persistent accumulator value.

AL Transformation:

```
Before: [Void, item1, item2, ..., itemN, persistent_init, {action}, ...]
After:  [...]
```

Action Block Signature:

The action block receives: `[current_item, persistent, ...]` on the AL.

The action block should:

- Pop `current_item` and `persistent` from AL
- Perform any desired operation (print, accumulate, etc.)
- Push updated `persistent` value back onto AL

How It Works:

1. The drainer pops `action_block`, `persistent`, and `current` from AL
2. Tests if `current` is `Void`:
  - If `Void`: cleanup and stop (end of items)
  - If not `Void`: execute action block with `current` and `persistent`
3. The loop continues via `>chain`, processing each item from the AL
4. The `persistent` value flows through each iteration

Example 1: Simple Print

```soma
Void (a) (b) (c) Nil { !_.persistent !_.current _.current >print } >al.drain
```

Output:

```
a
b
c
```

The action block just pops both arguments and prints `current`. The `persistent` value (Nil) is unused but must be managed.

Example 2: Collect into List

```soma
Void (a) (b) (c) Nil { !_.persistent !_.current _.current _.persistent >list.cons } >al.drain
!my_list

my_list.value                ; AL: [(c)]
my_list.next.value           ; AL: [(b)]
my_list.next.next.value      ; AL: [(a)]
```

This collects all items into a linked list. Note that the list is built in reverse order (last item first) because `list.cons` prepends to the front.

Example 3: Count Items

```soma
Void (a) (b) (c) 0 { !_.persistent !_.current _.persistent >inc } >al.drain
; AL: [3]
```

The action block ignores `current` and just increments the persistent counter.

Example 4: Action with Side Effects

```soma
Void (x) (y) (z) (PREFIX:) {
  !_.persistent !_.current
  _.persistent >print
  _.current >print
} >al.drain
```

Output:

```
PREFIX:
x
PREFIX:
y
PREFIX:
z
```

The persistent value is used as a prefix for each printed item.

Usage Pattern:

```soma
) Setup: Mark end of items with Void, push items, push initial state, push action
Void
item1
item2
item3
initial_persistent_value
{
  !_.persistent !_.current
  ) Process current and persistent
  ) Push updated persistent back
  updated_persistent
}
>al.drain
```

Why This Pattern Matters:

The `al.drain` operation is a generalized **iterator** that can:

- Collect items into data structures (lists, counts, etc.)
- Perform side effects for each item (print, store, etc.)
- Transform sequences with persistent state
- Work with any AL content, regardless of type

Relationship to Functional Programming:

This is similar to a `foldl` or `reduce` operation:

- **`persistent`**: is the accumulator
- **`current`**: is the current element
- **The action block**: is the combining function
- **The AL contents**: are the sequence being reduced

Common Mistake:

```soma
) WRONG - forgetting to push persistent back
Void (a) (b) 0 {
  !_.persistent !_.current
  _.persistent >inc
  ) Missing: push updated value!
} >al.drain
; AL: [] (persistent value was lost!)

) RIGHT - always push persistent back
Void (a) (b) 0 {
  !_.persistent !_.current
  _.persistent >inc
} >al.drain
; AL: [2]
```

Design Note:

The `al.drain` operation uses the Store for the `loop` block (not Register) because the loop needs to reference itself by name for self-recursion. This is the standard pattern for any self-referencing block in SOMA.

---

## Composing Operations

The real power of the stdlib comes from **composing** these operations to build more complex behaviors.

### Example 1: Clamp Value to Range

```soma
Clamp value to [min, max]
{ !_.max !_.min !_.val
  _.val _.min >max _.max >min
} !clamp

Usage: clamp value to [0, 100]
-5 0 100 >clamp     ; AL: [0]
150 0 100 >clamp    ; AL: [100]
50 0 100 >clamp     ; AL: [50]
```

### Example 2: Boolean XOR

```soma
XOR: (a AND NOT b) OR (NOT a AND b)
{
  >over >over        ; Duplicate both bools
  >swap >not >and    ; a AND NOT b
  >rot >rot          ; Bring copies back
  >not >and          ; NOT a AND b
  >or                ; Combine
} !xor

True False >xor      ; AL: [True]
True True >xor       ; AL: [False]
```

### Example 3: Factorial Using `>times`

```soma
1 !result
5 !n

n {
  result counter >* !result
  counter >dec !counter
} >times

result >print        ; Output: 120
```

### Example 4: Conditional Loop with Multiple Tests

```soma
0 !x

{
  x 100 ><           ; Test 1: x < 100
  x 2 >/ 2 >* x >==  ; Test 2: x is even
  >and               ; Both must be true
}
{
  x >toString >print
  x 2 >+ !x
}
>while

Output: 0, 2, 4, 6, ..., 98
```

### Example 5: Find Maximum in Sequence

```soma
Assumes values are on AL, count in variable
first_value !current_max

count 1 >- {
  value                    ; Get next value
  current_max >over >over  ; Duplicate for comparison
  >>                       ; Is value > current_max?
  { !current_max }         ; If yes, update
  { >drop }                ; If no, discard
  >choose >^
} >times

current_max              ; Result on AL
```

---

## Design Patterns

### Pattern 1: Using Register for Local State

Stack manipulation operations use the Register as temporary storage:

```soma
{!_.a !_.b _.b _.a _.b} !over
```

**Why?** The Register provides named, isolated storage for each block execution. This is more readable than pure stack manipulation.

### Pattern 2: Building New Comparisons from `><`

All comparison operators are built from `><` and boolean logic:

- **`>>`**: Swap then `><`
- **`!=!`**: Test both `<` directions, `OR` results
- **`==`**: NOT (!=!)
- **`=<`**: NOT (>)
- **`=>`**: NOT (<)

**Why?** Minimizes FFI primitives while providing full comparison suite.

### Pattern 3: Loops as Self-Referencing Blocks

Complex loops use `>block` to push self-reference:

```soma
{
  <body>
  <test>
  { >block }           ; Continue loop block
  { }                  ; Exit loop block
  >choose              ; Select block
  >^                   ; Execute selected block
} >chain
```

**Why?** This creates iterative loops without recursion or call stack growth. The `>^` operator executes the selected block from the AL.

### Pattern 4: Storing Loop State in Store

Loops that need shared state use Store paths, not Register paths:

```soma
0 !counter             ; Store, not _.counter
{
  counter 10 ><
  {
    counter >print
    counter >inc !counter
    >block
  }
  {}
  >choose >^
} >chain
```

**Why?** Nested blocks have isolated Registers, but all blocks share the Store. The `>^` executes the selected continuation or exit block.

---

## Implementation Insights

### Why Use Register Paths?

Operations like `>dup`, `>swap`, `>over` could theoretically be FFI primitives. But defining them in SOMA using Register operations:

1. **Proves the model is complete**: AL manipulation doesn't need special primitives
2. **Demonstrates composability**: everything builds from paths and blocks
3. **Enables user extension**: users can define custom stack operations the same way

### Why Build Comparisons from `><`?

The FFI only provides `><` )less-than). All other comparisons are derived:

1. **Minimizes runtime burden**: fewer primitives to implement
2. **Shows algebraic relationships**: a > b is b < a, etc.
3. **Encourages composition**: users think in terms of building blocks

### Why Provide Both `>while` and `>do`?

These are **patterns**, not primitives. They demonstrate:

1. **Pre-condition vs post-condition loops**: fundamental algorithmic patternsTemplate for user loopsusers can copy and modify for custom loopsDocumentation valueshows how to build loops with `>chain`

### Why the `>^` Operator?

`>^` is the **showcase of SOMA's power**:

1. **User-defined execution**: something other languages provide as a primitive
2. **Enables dynamic dispatch**: build operation tables and execute dynamically
3. **Demonstrates path semantics**: > is not special syntax, it's uniform

---

## Extending the Standard Library

You can add your own operations following the same patterns:

### Custom Stack Operation: `tuck`

```soma
) Insert second value at third position
{!_.a !_.b !_.c _.a _.c _.b} !tuck

1 2 3 >tuck     ; AL: [3, 1, 2, 3]

```

### Custom Comparison: `between`

```soma
) Test if value is in range [min, max]
{
  !_.max !_.min !_.val
  _.val _.min >=>        ; val >= min
  _.val _.max >=<        ; val <= max
  >and
} !between

50 0 100 >between        ; AL: [True]
150 0 100 >between       ; AL: [False]

```

### Custom Control Flow: `unless`

```soma
) Execute block if condition is false
{>swap >not >swap >if} !unless

False { "Executed" >print } >unless   ; Prints: Executed

```

### Custom Loop: `repeat_until`

```soma
) Execute body repeatedly until condition is true
{
  {
    !_.cond !_.body
    >_.body
    _.body _.cond >block
    >_.cond
    { >drop >drop Nil }    ; Exit if true
    {}                     ; Continue if false
    >choose >^
  } >chain
  >drop
} !repeat_until

```

---

## Summary

The SOMA standard library demonstrates that **most operations you think of as primitives are actually composable from simpler parts**:

- ****Boolean logic****:  builds from `>choose`
- ****Comparisons****:  build from `><` and boolean ops
- ****Stack operations****:  build from Register paths
- ****Arithmetic helpers****:  build from `>+`, `>-`, `><`
- ****Control flow****:  builds from `>choose`, `>chain`, `>block`
- ****Linked lists****:  build from CellRefs and context-passing
- ****AL draining****:  builds from `>chain`, `>choose`, and action blocks

**Key insights:**

1. **Everything is a block**: Even "operators" are just blocks at Store paths
2. **Execution is explicit**: The > prefix makes computation visible
3. **Composition is natural**: Complex operations emerge from simple ones
4. **The FFI is tiny**: Minimal primitives, maximal expressiveness
5. **Users are equals**: You can extend stdlib using the same primitives
6. **CellRefs enable persistent structures**: Register-local data can outlive the block
7. **Context-passing enables iteration**: Persistent state flows through loops

**The elegance of SOMA:** A small kernel of irreducible operations, and everything else built transparently in user space. No magic. No hidden machinery. Just paths, blocks, and explicit state transformation.

---

**Next:** See `08-examples.md` for complete programs using stdlib operations.


