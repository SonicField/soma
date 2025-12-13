# # 10. Standard Library: Logic and Control Flow

The SOMA standard library provides derived operations built from FFI primitives. While the core built-ins )Section 06) provide the minimal foundation, the stdlib extends this with convenient, composable operations for everyday programming. These derived operations demonstrate that SOMA's small core is sufficient for practical computation.

This section covers logic operations, comparison operators, stack manipulation utilities, arithmetic helpers, and control flow constructs. Each operation is defined purely in terms of SOMA primitives and other stdlib operations, with no additional FFI calls.

---

## ## Philosophy: FFI vs Derived Operations

SOMA's design philosophy separates operations into two categories:

- **FFI Primitives** are implemented in the runtime )Rust, in the reference implementation) and cannot be expressed in SOMA itself. These include `>+`, `>-`, `><`, `>choose`, and `>chain`. They form the irreducible core.
- **Derived Operations** are written in SOMA using FFI primitives. They live in `stdlib.soma` and are loaded at runtime. Examples include `>not`, `>if`, and `>while`.

This separation has practical benefits:

- The FFI surface is minimal and auditable
- Derived operations can be inspected, modified, or extended by users
- The stdlib serves as documentation for idiomatic SOMA patterns

---

## ## Boolean Logic

Boolean operations leverage `>choose` to implement standard logical operators. Since `>choose` selects between two values based on a Boolean condition, it provides the foundation for all Boolean algebra.

### ### >not

**Signature:** `[Bool] -> [Bool]`

Negates a Boolean value. Returns `True` if the input is `False`, and `False` if the input is `True`.

**Definition:**

```soma
{False True >choose} !not
```

The implementation exploits `>choose`'s semantics: when the condition is `True`, it selects the first value )`False`); when `False`, it selects the second value )`True`).

**Example:**

```soma
True >not      ) AL: [False]
False >not     ) AL: [True]
```

---

### ### >and

**Signature:** `[Bool, Bool] -> [Bool]`

Logical AND of two Boolean values. Returns `True` only if both inputs are `True`.

**Definition:**

```soma
{False >choose} !and
```

If the top value )first argument) is `True`, returns the second value; if `False`, returns `False` immediately. This implements short-circuit AND semantics.

**Example:**

```soma
True True >and    ) AL: [True]
True False >and   ) AL: [False]
False True >and   ) AL: [False]
False False >and  ) AL: [False]
```

---

### ### >or

**Signature:** `[Bool, Bool] -> [Bool]`

Logical OR of two Boolean values. Returns `True` if either input is `True`.

**Definition:**

```soma
{True >swap >choose} !or
```

If the top value is `True`, returns `True` immediately; otherwise returns the second value. This implements short-circuit OR semantics.

**Example:**

```soma
True True >or     ) AL: [True]
True False >or    ) AL: [True]
False True >or    ) AL: [True]
False False >or   ) AL: [False]
```

---

## ## Comparison Operators

The FFI provides only `><` )less-than) as a primitive comparison. All other comparison operators are derived from this single primitive using Boolean logic and stack manipulation.

### ### >>

**Signature:** `[Value, Value] -> [Bool]`

Tests if the first value is greater than the second. Returns `True` if `a > b`.

**Definition:**

```soma
{>swap ><} !>
```

Greater-than is simply less-than with swapped arguments: `a > b` is equivalent to `b < a`.

**Example:**

```soma
10 5 >>      ) AL: [True]
3 7 >>       ) AL: [False]
5 5 >>       ) AL: [False]
```

---

### ### >=!

**Signature:** `[Value, Value] -> [Bool]`

Tests if two values are not equal. Returns `True` if `a != b`.

**Definition:**

```soma
{>over >over >swap >< >rot >rot >< >or} !=!
```

Two values are not equal if either `a < b` or `b < a`. The implementation duplicates both values, computes both less-than comparisons, and combines them with OR.

**Example:**

```soma
5 3 >=!      ) AL: [True]
5 5 >=!      ) AL: [False]
"cat" "dog" >=!  ) AL: [True]
```

---

### ### >==

**Signature:** `[Value, Value] -> [Bool]`

Tests if two values are equal. Returns `True` if `a == b`.

**Definition:**

```soma
{>=! >not} !==
```

Equality is the negation of inequality. Note: This stdlib `>==` shadows the FFI `>==`. The implementations are equivalent, but the stdlib version demonstrates derivability.

**Example:**

```soma
5 5 >==      ) AL: [True]
5 3 >==      ) AL: [False]
"cat" "cat" >==  ) AL: [True]
```

---

### ### >=<

**Signature:** `[Value, Value] -> [Bool]`

Tests if the first value is less than or equal to the second. Returns `True` if `a <= b`.

**Definition:**

```soma
{>swap >< >not} !=<
```

Less-than-or-equal is the negation of greater-than: `a <= b` is equivalent to `NOT )b < a)`.

**Example:**

```soma
3 5 >=<      ) AL: [True]
5 5 >=<      ) AL: [True]
7 5 >=<      ) AL: [False]
```

---

### ### >=>

**Signature:** `[Value, Value] -> [Bool]`

Tests if the first value is greater than or equal to the second. Returns `True` if `a >= b`.

**Definition:**

```soma
{>< >not} !=>
```

Greater-than-or-equal is the negation of less-than: `a >= b` is equivalent to `NOT )a < b)`.

**Example:**

```soma
7 5 >=>      ) AL: [True]
5 5 >=>      ) AL: [True]
3 5 >=>      ) AL: [False]
```

---

## ## Stack Manipulation

Stack manipulation operations provide convenient ways to rearrange values on the AL. These are fundamental building blocks for more complex operations. While FFI versions exist for `>dup`, `>drop`, `>swap`, and `>over`, the stdlib provides pure SOMA implementations.

### ### >dup

**Signature:** `[Value] -> [Value, Value]`

Duplicates the top value on the AL.

**Definition:**

```soma
{!_.value _.value _.value} !dup
```

The value is stored in the Register, then pushed twice.

**Example:**

```soma
7 >dup       ) AL: [7, 7]
"hello" >dup ) AL: ["hello", "hello"]
```

---

### ### >drop

**Signature:** `[Value] -> []`

Removes the top value from the AL.

**Definition:**

```soma
{!_} !drop
```

The value is stored in the Register and discarded.

**Example:**

```soma
1 2 3 >drop  ) AL: [1, 2]
```

---

### ### >swap

**Signature:** `[Value, Value] -> [Value, Value]`

Swaps the top two values on the AL.

**Definition:**

```soma
{!_.a !_.b _.a _.b} !swap
```

Both values are stored, then pushed in reverse order.

**Example:**

```soma
1 2 >swap    ) AL: [2, 1]
"a" "b" >swap ) AL: ["b", "a"]
```

---

### ### >over

**Signature:** `[Value, Value] -> [Value, Value, Value]`

Copies the second value and pushes it on top.

**Definition:**

```soma
{!_.a !_.b _.b _.a _.b} !over
```

Both values are stored, then the second is pushed, followed by the first, followed by the second again.

**Example:**

```soma
1 2 >over    ) AL: [1, 2, 1]
```

---

### ### >rot

**Signature:** `[Value, Value, Value] -> [Value, Value, Value]`

Rotates the top three values, bringing the third to the top.

**Definition:**

```soma
{!_.a !_.b !_.c _.b _.a _.c} !rot
```

All three values are stored. The rotation brings the deepest value )`c`) to the top: `[a, b, c] -> [b, c, a]`.

**Example:**

```soma
1 2 3 >rot   ) AL: [2, 3, 1]
```

---

## ## Arithmetic Helpers

These operations provide convenient arithmetic utilities built from the core `>+`, `>-`, and comparison operations.

### ### >inc

**Signature:** `[Int] -> [Int]`

Increments an integer by 1.

**Definition:**

```soma
{1 >+} !inc
```

**Example:**

```soma
5 >inc       ) AL: [6]
-1 >inc      ) AL: [0]
```

---

### ### >dec

**Signature:** `[Int] -> [Int]`

Decrements an integer by 1.

**Definition:**

```soma
{1 >-} !dec
```

**Example:**

```soma
5 >dec       ) AL: [4]
0 >dec       ) AL: [-1]
```

---

### ### >abs

**Signature:** `[Int] -> [Int]`

Returns the absolute value of an integer.

**Definition:**

```soma
{>dup 0 >< {0 >swap >-} {} >choose >^} !abs
```

If the value is negative )less than 0), it is negated by subtracting from 0. Otherwise, it is returned unchanged.

**Example:**

```soma
5 >abs       ) AL: [5]
-5 >abs      ) AL: [5]
0 >abs       ) AL: [0]
```

---

### ### >min

**Signature:** `[Int, Int] -> [Int]`

Returns the smaller of two integers.

**Definition:**

```soma
{>over >over >< {>drop} {>swap >drop} >choose >^} !min
```

Both values are duplicated for comparison. If the first is less than the second, the second is dropped; otherwise the first is dropped.

**Example:**

```soma
3 7 >min     ) AL: [3]
7 3 >min     ) AL: [3]
5 5 >min     ) AL: [5]
```

---

### ### >max

**Signature:** `[Int, Int] -> [Int]`

Returns the larger of two integers.

**Definition:**

```soma
{>over >over >> {>drop} {>swap >drop} >choose >^} !max
```

Both values are duplicated for comparison. If the first is greater than the second, the second is dropped; otherwise the first is dropped.

**Example:**

```soma
3 7 >max     ) AL: [7]
7 3 >max     ) AL: [7]
5 5 >max     ) AL: [5]
```

---

## ## Control Flow

Control flow in SOMA is built from `>choose` and `>chain`. These stdlib operations provide familiar control structures while maintaining SOMA's explicit, stack-based nature.

### ### >times

**Signature:** `[Int, Block] -> []`

Executes a block N times.

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
    >choose >^
  } >chain
  >drop
} !times
```

The implementation uses `>chain` for iteration. On each iteration, it executes the user's block, decrements the counter, and decides whether to continue or terminate.

**Example:**

```soma
3 { (Hello) >print } >times
) Output:
) Hello
) Hello
) Hello
```

---

### ### >if

**Signature:** `[Bool, Block] -> []`

Executes a block if the condition is true.

**Definition:**

```soma
{{} >choose >^} !if
```

Uses `>choose` to select between the provided block and an empty block, then executes the result.

**Example:**

```soma
True { (yes) >print } >if   ) Output: yes
False { (no) >print } >if   ) No output
```

---

### ### >ifelse

**Signature:** `[Bool, Block, Block] -> [...]`

Executes one of two blocks based on a condition. This is an alias for `>choose >^`.

**Definition:**

```soma
{>choose >^} !ifelse
```

**Example:**

```soma
5 0 >< { (positive) } { (not positive) } >ifelse
) AL: ["positive"]
```

---

### ### >^

**Signature:** `[Block] -> [...]`

Executes a block from the AL. This is SOMA's equivalent of Forth's `EXECUTE`.

**Definition:**

```soma
{ !_ >_ } !^
```

The block is stored in the Register, then executed via `>_`.

**Example:**

```soma
{ 5 3 >+ } >^   ) AL: [8]
{ (hello) } >^  ) AL: ["hello"]
```

---

### ### >while

**Signature:** `[Block, Block] -> []`

Loops while a condition block returns true. The first block is the condition, the second is the body.

**Definition:**

```soma
{
  {
    !_.body !_.cond
    _.cond _.body                 ) Push state back onto AL
    >block                        ) Push loop block
    >_.cond                       ) Execute condition LAST so bool is on top
    {
      !_.loop !_.body !_.cond     ) Pop state from AL
      >_.body                     ) Execute body
      _.cond _.body _.loop        ) Push state back for next iteration
    }
    {>drop >drop >drop Nil}       ) False: cleanup
    >choose >^
  } >chain
  >drop
} !while
```

The loop executes the condition block first. If true, it executes the body and repeats. The implementation uses context-passing to preserve state across iterations.

**Example:**

```soma
0 !count
{ count 5 >< } { count >print count >inc !count } >while
) Output: 0 1 2 3 4
```

---

### ### >do

**Signature:** `[Block, Block] -> []`

Executes the body first, then loops while the condition is true. This is a do-while loop.

**Definition:**

```soma
{
  {
    !_.cond !_.body
    >_.body                       ) Execute body first
    _.body _.cond                 ) Push state back onto AL
    >block                        ) Push loop block
    >_.cond                       ) Execute condition LAST so bool is on top
    {}                            ) True: empty
    {>drop >drop >drop Nil}       ) False: cleanup
    >choose >^
  } >chain
  >drop
} !do
```

Unlike `>while`, the body executes before the condition is checked, guaranteeing at least one execution.

**Example:**

```soma
0 !count
{ count >print count >inc !count } { count 3 >< } >do
) Output: 0 1 2
```

---

## ## Design Patterns

The stdlib implementations demonstrate several important SOMA patterns.

### ### Context-Passing Pattern

Blocks inside `>choose` branches cannot access the outer Register directly. The solution is to push context onto the AL before `>choose`, then pop it inside each branch:

```soma
_.                    ) Push context reference
<condition>
{ !_. _.outer_var ... } ) Pop context, access outer variables
{ !_. _.other_var ... }
>choose >^
```

This pattern appears throughout the stdlib, particularly in `>while` and `>do`.

### ### Chain Pattern for Iteration

Use `>chain` with Nil-terminated loops for iteration. The loop block returns either `[result, Nil]` to stop or `[state..., loop]` to continue:

```soma
{
  ) ... do work ...
  <condition>
    { ) Continue: push state and loop block
      state... >block
    }
    { ) Stop: cleanup and push Nil
      >drop >drop Nil
    }
  >choose >^
} >chain
```

This avoids deep recursion and enables clean iterative patterns with explicit state management.

### ### Private Helper Naming

Internal helper blocks use the `#` prefix convention:

```soma
list.fold.#loop    ) Private loop helper
dict.put.#update   ) Private update helper
```

This signals "private/internal" and avoids polluting the public namespace.

---

## ## Reference Table

The following table summarises all stdlib logic and control flow operations:

| Operation | Signature                          | Description            |
|-----------|------------------------------------|------------------------|
| `>not`    | [Bool] -> [Bool]                   | Boolean negation       |
| `>and`    | [Bool, Bool] -> [Bool]             | Logical AND            |
| `>or`     | [Bool, Bool] -> [Bool]             | Logical OR             |
| `>>`      | [Val, Val] -> [Bool]               | Greater-than           |
| `>=!`     | [Val, Val] -> [Bool]               | Not equal              |
| `>==`     | [Val, Val] -> [Bool]               | Equality               |
| `>=<`     | [Val, Val] -> [Bool]               | Less-than-or-equal     |
| `>=>`     | [Val, Val] -> [Bool]               | Greater-than-or-equal  |
| `>dup`    | [Val] -> [Val, Val]                | Duplicate top          |
| `>drop`   | [Val] -> []                        | Remove top             |
| `>swap`   | [Val, Val] -> [Val, Val]           | Swap top two           |
| `>over`   | [Val, Val] -> [Val, Val, Val]      | Copy second to top     |
| `>rot`    | [Val, Val, Val] -> [Val, Val, Val] | Rotate top three       |
| `>inc`    | [Int] -> [Int]                     | Increment by 1         |
| `>dec`    | [Int] -> [Int]                     | Decrement by 1         |
| `>abs`    | [Int] -> [Int]                     | Absolute value         |
| `>min`    | [Int, Int] -> [Int]                | Minimum of two         |
| `>max`    | [Int, Int] -> [Int]                | Maximum of two         |
| `>times`  | [Int, Block] -> []                 | Execute block N times  |
| `>if`     | [Bool, Block] -> []                | Conditional execution  |
| `>ifelse` | [Bool, Block, Block] -> [...]      | Two-branch conditional |
| `>^`      | [Block] -> [...]                   | Execute block from AL  |
| `>while`  | [Block, Block] -> []               | While loop             |
| `>do`     | [Block, Block] -> []               | Do-while loop          |

---

## Notes

- All operations in this section are derived from FFI primitives and can be inspected in `stdlib.soma`
- The stdlib versions of `>dup`, `>drop`, `>swap`, and `>over` shadow their FFI counterparts; both implementations are equivalent
- Stack effects follow the convention `[...args] -> [...results]` where rightmost = top of stack
- The `>^` operation is fundamental to SOMA's control flow and appears in many derived operations


