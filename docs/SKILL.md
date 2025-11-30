# SOMA Programming Language - Quick Reference Skill

## When to Use This Skill

Use this skill when:
- User asks to write SOMA code
- User asks to run/execute SOMA programs
- User asks about SOMA syntax or semantics
- User wants to learn SOMA programming
- User needs help debugging SOMA code

## Overview

SOMA (State-Oriented Machine Algebra) is a minimalistic stack-based language with explicit state mutation. It deliberately counterpoints type-centric alternatives by making state and mutation visible.

**Core Philosophy:**
- Values exist on the AL (Accumulator List - a stack)
- Names exist in the Store (global hierarchical namespace)
- Blocks are first-class values (code is data)
- Execution is explicit (via `>` prefix)
- State mutation is visible (via `!` prefix)
- **Execution scope, not lexical scope** - blocks get fresh Registers on execution

---

## 1. Quick Start

### Minimal Example
```soma
) Print hello world
(Hello, world!) >print
```

### How SOMA Works
```soma
) 1. Push values onto the AL (stack)
5 3          ) AL: [5, 3]

) 2. Execute operations with >
>+           ) AL: [8]

) 3. Store results with !
!result      ) Store: {result: 8}, AL: []

) 4. Read from Store
result       ) AL: [8]
```

### How to Execute SOMA Code

**Method 1: Python API**
```python
from soma.vm import VM
from soma.parser import parse
from soma.compiler import compile_program

vm = VM()
ast = parse("(Hello) >print")
compiled = compile_program(ast)
compiled.execute(vm)
```

**Method 2: Test File (Recommended)**
Create `tests/soma/06_custom.soma`:
```soma
) TEST: My program
) EXPECT_AL: [42]
) EXPECT_OUTPUT: Answer

(Answer) >print
42
```
Run: `python3 tests/run_soma_tests.py`

---

## 2. Essential Syntax Reference

### Literals
```soma
42                     ) Integer
-17                    ) Negative integer
True                   ) Boolean true
False                  ) Boolean false
Nil                    ) Explicit null/none
Void                   ) Undefined/missing value
{ code }               ) Block (unevaluated code)
(Hello)                ) String (parentheses, not quotes!)
(Hello (world\29\\52\) ) ) and \ must be escaped in strings
```

### Operators and Modifiers

**Store Operations:**
```soma
!path       ) Write: Pop AL top, store at path
path        ) Read: Push value at path onto AL
```

**Execution:**
```soma
>path       ) Execute: Read value at path and execute it
>{ code }   ) Execute block literal immediately (cleaner than { code } >chain)
```

**Paths:**
```soma
a           ) Simple path
a.b.c       ) Nested path (traversal)
a.b.c.      ) CellRef (trailing dot - reference to cell itself)
```

**Register (Block-local storage):**
```soma
_.x         ) Register path (underscore prefix)
!_.x        ) Store in register
_.x         ) Read from register
```

**Comments:**
```soma
) This is a comment
```

### Critical Built-in Operations

**Control Flow:**
```soma
>choose     ) [condition, true_val, false_val] → selects one value (doesn't execute)
>chain      ) Pops AL top. If Block, executes it and repeats. If not Block, stops.
>block      ) Pushes currently executing block onto AL (enables self-reference)
```

**Comparison:**
```soma
><          ) Less-than: [a, b] → [bool]
```

**Arithmetic:**
```soma
>+          ) Add: [a, b] → [a+b]
>-          ) Subtract: [a, b] → [a-b]
>*          ) Multiply: [a, b] → [a*b]
>/          ) Divide: [a, b] → [a/b]
>%          ) Modulo: [a, b] → [a%b]
```

**Strings:**
```soma
>concat     ) Concatenate: [(str1), (str2)] → [(str1str2)]
```

**Type Operations:**
```soma
>toString   ) Convert to string: [42] → [(42)]
>toInt      ) Parse string to int: [(42)] → [42] or [Nil]
>isVoid     ) Check if Void: [value] → [bool]
>isNil      ) Check if Nil: [value] → [bool]
```

**I/O:**
```soma
>print      ) Print: [(text)] → [] (prints text to output)
```

---

## 3. Execution Model

### Three Storage Spaces

**AL (Accumulator List):**
- LIFO stack for computation
- Shared across all blocks
- Values: integers, strings, blocks, booleans, etc.

**Store:**
- Global hierarchical namespace
- Persistent across execution
- Tree structure: `a.b.c` creates cells
- **Auto-vivification on writes**: Writing `!a.b.c` creates intermediate cells `a` and `a.b` (with Void)
- **Strict reads**: Reading undefined paths raises RuntimeError (must initialize first)

**Register:**
- Block-local temporary storage
- Fresh and empty for each block execution
- Destroyed when block exits
- **CRITICAL: Isolated between parent and child blocks**
- Prefix: `_.`

### Register Isolation and Execution Scope

**CRITICAL:** SOMA uses **execution scope**, not lexical scope. Each block gets a **fresh, empty Register** when executed.

```soma
) WRONG - Assuming lexical scope
{
  5 !_.x                ) Store 5 in outer block's Register
  >{ _.x >print }       ) ERROR: Inner block has FRESH Register - _.x is Void!
}

) CORRECT - Use Store for sharing
{
  5 !x                  ) Store in Store (global)
  >{ x >print }         ) Can read from Store
}

) CORRECT - Pass via AL (simple values)
{
  5 !_.x                ) Store in Register
  _.x                   ) Push to AL
  >{ !_.y _.y >print }  ) Inner block pops from AL, stores in its Register
}

) BEST - Context-passing idiom (for multiple values)
{
  5 !_.x
  10 !_.y
  _.                    ) Push CellRef to Register root onto AL
  >{                    ) Execute block WITH context on AL
    !_.                 ) Pop CellRef, store at inner Register root
    _.x _.y >+ >print   ) Access outer Register transparently!
  }
}
```

**The Context-Passing Idiom:**

This is the most important pattern in SOMA. It enables blocks to share state without global variables.

1. `_.` creates a CellRef to the current Register's root Cell
2. Push this CellRef onto the AL
3. `!_.` in the inner block stores that CellRef AT the inner Register's `_` location
4. When the inner block accesses `_.x`, the Register follows the CellRef automatically
5. All reads and writes go through to the aliased Register

**Key Rule:** Parent and child blocks have **completely separate Registers** by default. Use the context-passing idiom (`_.` → `!_.`) to share state explicitly.

### Execution Flow

**Literals push to AL:**
```soma
5 3          ) AL: [5, 3]
```

**Blocks push as values:**
```soma
{ 1 2 >+ }   ) AL: [block]  (NOT executed yet!)
```

**Execute with > prefix:**
```soma
{ 1 2 >+ } !myblock  ) Store block in Store
>myblock             ) Execute from Store, AL: [3]

>{ 1 2 >+ }          ) Execute literal block immediately, AL: [3]

{ 1 2 >+ } >^        ) Push block to AL, execute from AL, AL: [3]
```

**Operations pop arguments, push results:**
```soma
5 3          ) AL: [5, 3]
>+           ) Pops 3 and 5, pushes 8, AL: [8]
```

---

## 4. FFI Primitives Reference

These are the **only** built-in operations in SOMA. Everything else is built from these.

### Control Flow
- `choose` - Conditional selector (selects one value based on condition)
- `chain` - Block continuation loop
- `block` - Self-reference for loops

### Comparison
- `<` - Less-than (only comparison primitive)

### Arithmetic
- `+`, `-`, `*`, `/`, `%`

### String
- `concat` - String concatenation

### Type Operations
- `toString` - Convert value to string
- `toInt` - Parse string to integer
- `isVoid` - Test if value is Void
- `isNil` - Test if value is Nil

### I/O
- `print` - Output text

### Special Values
- `True`, `False` - Boolean values
- `Nil` - Explicit null
- `Void` - Undefined/missing (cannot be stored as Cell value)

---

## 5. Standard Library Quick Reference

Located in `soma/stdlib.soma`. Automatically loaded by the VM on initialization before any user code runs - no manual loading required.

### Boolean Logic
```soma
>not        ) Boolean negation: [bool] → [!bool]
>and        ) Logical AND: [a, b] → [a && b]
>or         ) Logical OR: [a, b] → [a || b]
```

### Comparison Operators (derived from `<`)
```soma
>>          ) Greater-than: [a, b] → [a > b]
>==         ) Equality: [a, b] → [a == b]
>!=         ) Not-equal: [a, b] → [a != b]
>=<         ) Less-or-equal: [a, b] → [a <= b]
>=>         ) Greater-or-equal: [a, b] → [a >= b]
```

### Stack Manipulation
```soma
>dup        ) Duplicate top: [a] → [a, a]
>drop       ) Remove top: [a] → []
>swap       ) Swap top two: [a, b] → [b, a]
>over       ) Copy second to top: [a, b] → [a, b, a]
>rot        ) Rotate top three: [a, b, c] → [b, c, a]
```

### Arithmetic Helpers
```soma
>inc        ) Increment: [n] → [n+1]
>dec        ) Decrement: [n] → [n-1]
>abs        ) Absolute value: [n] → [|n|]
>min        ) Minimum: [a, b] → [min(a,b)]
>max        ) Maximum: [a, b] → [max(a,b)]
```

### Control Flow Helpers
```soma
>^          ) Execute from AL: [block] → (executes block)
>times      ) Execute block N times: [n, block] → []
>if         ) Conditional: [bool, block] → [] (execute if true)
>ifelse     ) Choose then execute: [bool, true_block, false_block] → []
>while      ) While loop: [cond_block, body_block] → []
>do         ) Do-while loop: [body_block, cond_block] → []
```

### Linked List Operations
```soma
>list.new   ) Create empty list: [] → [Nil]
>list.cons  ) Prepend to list: [value, list] → [new_node]
            ) Returns CellRef with .value and .next fields
```

### AL Draining
```soma
>al.drain   ) Drain AL with action: [Void, items..., persistent, {action}] → []
            ) Action block receives: [current, persistent] → [new_persistent]
            ) Processes items until Void, accumulating in persistent state
```

---

## 6. Common Patterns Cookbook

### The Standard Loop Template (with Context-Passing)

This is the idiomatic way to write loops in SOMA using `>chain` and context-passing:

```soma
>{
  0 !_.counter         ) Initialize state in Register

  {
    !_.                ) Pop context from AL

    ) Do work using _.counter, _.other_fields, etc.
    _.counter >toString >print
    _.counter >inc !_.counter

    _.                 ) Push context for next iteration
    _.counter 10 ><    ) Check condition
      { loop }         ) True: continue (return block name)
      { >drop Nil }    ) False: drop context, stop
    >choose >^
  } !loop              ) Store in Store (for self-reference)

  _.                   ) Push initial context
  loop >^              ) Execute first iteration
  >chain               ) Chain remaining iterations
  >drop                ) Clean up Nil result
}
```

**Key points:**
1. **Context flows through AL:** Each iteration receives context via `_.` → `!_.`
2. **Self-reference requires Store:** Block stored as `!loop` (Store), not `!_.loop` (Register)
3. **Always push context:** Before condition check in each iteration
4. **Clean up after >chain:** Add `>drop` when test expects empty AL

### Initialization Patterns

**Why initialize?** SOMA uses strict auto-vivification: reading undefined paths raises RuntimeError. Always initialize before reading.

**Simple initialization:**
```soma
0 !counter           ) Initialize with integer
() !name             ) Initialize with empty string
Nil !result          ) Initialize with Nil
False !flag          ) Initialize with boolean
```

**Auto-vivification on writes:**
```soma
) Writing nested paths auto-creates intermediate cells
42 !config.db.port   ) Creates: config, config.db, config.db.port

) Auto-vivified intermediate cells CAN be read (contain Void)
config >isVoid       ) Pushes: True (auto-vivified, contains Void)
config.db >isVoid    ) Pushes: True (auto-vivified, contains Void)
config.db.port       ) Pushes: 42 (was explicitly written)

) But non-existent paths CANNOT be read
config.web           ) ERROR: Undefined Store path 'config.web'
```

**Conditional initialization (check before read):**
```soma
) Pattern: Initialize if needed, then use
counter >isVoid      ) ERROR! counter doesn't exist yet

) CORRECT - Initialize first, then check
0 !counter           ) Always initialize first
counter >isVoid      ) Now safe to read
  0                  ) Default if Void
  counter            ) Use existing value
>choose
!counter
```

**Register initialization:**
```soma
>{
  0 !_.count         ) Initialize Register fields before use
  () !_.name

  _.count >print     ) Safe - initialized above
}
```

**Best practice:** Initialize all paths at the start of your program or block.

### Counter (Simple)
```soma
0 !counter
counter >inc !counter
counter >print
```

### Conditional Execution
```soma
) Using >ifelse (stdlib - choose + execute)
5 !x                ) Initialize first
x 10 ><
  { (small) >print }
  { (large) >print }
>ifelse

) Or using >choose + >^ directly
15 !x               ) Initialize first
x 10 ><
  { (small) >print }
  { (large) >print }
>choose >^
```

### While Loop
```soma
0 !counter
{ counter 10 >< }           ) Condition: counter < 10
{ counter >print            ) Body: print and increment
  counter >inc !counter }
>while
```

### N Times Loop
```soma
10 { (tick) >print } >times
```

### Simple Recursion (Factorial)
```soma
) Define factorial function in Store
{
  !fact-n                       ) Pop arg from AL, store in Register
  fact-n 0 >==                  ) Base case check
  { 1 }                         ) Base: return 1
  { fact-n fact-n 1 >- fact >chain >* }  ) Recursive: n * fact(n-1)
  >choose >^                    ) Select and execute branch
} !fact

5 fact >chain                   ) Call: AL: [120]
```

### Tail-Call Optimization with >chain

The `>chain` operator is perfect for tail-call optimization since it repeatedly executes blocks from AL without growing the call stack.

**Fibonacci (tail-call optimized):**
```soma
0 !fib.a
1 !fib.b
10 !fib.count

{
  fib.a >toString >print

  fib.count 1 >=<
    Nil                         ) Stop: return Nil
    {                           ) Continue: compute next and return this block
      fib.count 1 >- !fib.count
      fib.a fib.b >+ !fib.next
      fib.b !fib.a
      fib.next !fib.b
      fib-step                  ) Return self for tail-call
    }
  >choose
} !fib-step

fib-step >chain                 ) Start the chain
```

**Factorial (tail-call with accumulator):**
```soma
5 !fact.n
1 !fact.acc

{
  fact.n 0 >=<
    fact.acc                    ) Base: return accumulator
    {                           ) Recursive: update and continue
      fact.n 1 >- !fact.n
      fact.acc fact.n 1 >+ >* !fact.acc
      fact-step                 ) Return self for tail-call
    }
  >choose
} !fact-step

fact-step >chain                ) AL: [120]
```

**State machine pattern:**
```soma
{ (State A) >print state-b } !state-a
{ (State B) >print state-c } !state-b
{ (State C) >print Nil } !state-c

state-a >chain                  ) Executes A → B → C → stops
```

### List Building with CellRefs
```soma
) Build a simple linked list
>list.new
(c) >swap >list.cons
(b) >swap >list.cons
(a) >swap >list.cons
!my_list

) Access list elements
my_list.value              ; AL: [(a)]
my_list.next.value         ; AL: [(b)]
my_list.next.next.value    ; AL: [(c)]
my_list.next.next.next >isNil  ; AL: [True]
```

### AL Draining: Collect Items into List
```soma
) Drain AL items into a linked list
Void (first) (second) (third) Nil {
  !_.persistent !_.current
  _.current _.persistent >list.cons
} >al.drain
!collected_list

) Items are in reverse order (LIFO)
collected_list.value                      ; AL: [(third)]
collected_list.next.value                 ; AL: [(second)]
collected_list.next.next.value            ; AL: [(first)]
```

### AL Draining: Count Items
```soma
) Count how many items on AL
Void (a) (b) (c) (d) 0 {
  !_.persistent !_.current
  _.persistent >inc
} >al.drain
; AL: [4]
```

### AL Draining: Print with Prefix
```soma
) Print each item with a prefix
Void (apple) (banana) (cherry) (Item:) {
  !_.persistent !_.current
  _.persistent >print
  _.current >print
} >al.drain
) Output:
) Item:
) apple
) Item:
) banana
) Item:
) cherry
```

### Higher-Order Function (Apply)
```soma
{ !_.f !_.x _.x >_.f } !apply

{ 1 >+ } !increment
5 increment >apply         ) AL: [6]
```

---

## 7. Complete Example Programs

### Example 1: FizzBuzz (1-15)
```soma
) FizzBuzz from 1 to 15

1 !i

{
  ) Check if divisible by 15 (both 3 and 5)
  i 15 >% 0 >==
    { (FizzBuzz) >print }
    {
      ) Check if divisible by 3
      i 3 >% 0 >==
        { (Fizz) >print }
        {
          ) Check if divisible by 5
          i 5 >% 0 >==
            { (Buzz) >print }
            { i >toString >print }
          >ifelse
        }
      >ifelse
    }
  >ifelse

  i >inc !i
  i 16 ><
    >block
    Nil
  >choose
} !loop

loop >chain
```

### Example 2: Prime Numbers (2-30)
```soma
) Find primes from 2 to 30 using trial division

2 !n

{
  ) Test if n is prime
  True !isPrime
  2 !divisor

  ) Check divisors from 2 to sqrt(n)
  {
    divisor divisor >* n >=<
  }
  {
    n divisor >% 0 >==
      { False !isPrime }
      { }
    >ifelse

    divisor >inc !divisor
  }
  >while

  ) Print if prime
  isPrime
    { n >toString >print }
    { }
  >ifelse

  n >inc !n
  n 31 ><
    >block
    Nil
  >choose
} !loop

loop >chain
```

### Example 3: Fibonacci Sequence (first 10)
```soma
) Print first 10 Fibonacci numbers

0 !a
1 !b
1 !count

a >toString >print
b >toString >print

{
  a b >+ !temp
  b !a
  temp !b

  temp >toString >print

  count >inc !count
  count 10 ><
    >block
    Nil
  >choose
} !loop

loop >chain
```

---

## 8. Debugging Guide

### Common Errors

**Error: "Cannot execute int"**
```soma
) WRONG:
>5              ) Trying to execute the integer 5

) CORRECT:
5               ) Just push 5 onto AL
```

**Error: "AL underflow"**
```soma
) WRONG:
5 >+            ) Not enough values (need 2 for +)

) CORRECT:
5 3 >+          ) Two values on AL
```

**Error: "Undefined Store path" or "Undefined Register path"**
```soma
) WRONG:
counter >print  ) Reading before initialization

) CORRECT - Initialize first:
0 !counter      ) Initialize with a value
counter >print

) AUTO-VIVIFICATION EXAMPLE:
42 !a.b.c       ) Creates a, a.b, and a.b.c
a >print        ) OK! Auto-vivified 'a' exists (contains Void)
a.b >print      ) OK! Auto-vivified 'a.b' exists (contains Void)
a.b.c >print    ) Prints: 42

dogs >print     ) ERROR! Never written, not auto-vivified
```

**Error message format (Store):**
```
Undefined Store path: 'myvar'
  Path was never set. Did you mean to:
    - Initialize it first: () !myvar
    - Set a nested value: <value> !myvar.<child>
    - Check a different path?
  Hint: Auto-vivified intermediate paths can be read after writing to children.
        Example: 42 !a.b.c creates 'a' and 'a.b' with Void, which can be read.
```

**Error message format (Register):**
```
Undefined Register path: '_.myvar'
  Register paths must be written before reading.
  Did you forget: <value> !_.myvar?
```

**Error: "Cannot write Void as payload"**
```soma
) WRONG - Reading undefined path (raises error before reaching !x):
nonexistent !x       ) ERROR: Undefined Store path 'nonexistent'

) CORRECT - Check if exists or use Nil:
Nil !x               ) Store Nil explicitly

) CORRECT - Handle undefined gracefully with a default:
() !x                ) Initialize with empty string
x                    ) Read it (safe now)
```

**Error: Register isolation gotcha**
```soma
) WRONG - Inner block can't see outer Register (lexical scope assumption!)
{
  5 !_.x
  >{ _.x >print }     ) _.x is Void in inner block!
}

) CORRECT - Use Store (if truly global)
{
  5 !x
  >{ x >print }
}

) CORRECT - Pass via AL (single value)
{
  5 !_.x
  _.x                ) Push to AL
  >{ !_.y _.y >print } ) Pop from AL, store in inner Register
}

) BEST - Context-passing idiom (multiple values)
{
  5 !_.x
  10 !_.y
  _.                 ) Push CellRef to Register root
  >{
    !_.              ) Pop and alias the Register
    _.x >print       ) Access outer Register transparently
    _.y >print
  }
}
```

### Debugging Techniques

**Print AL state:**
```soma
5 3 >+
>dup >toString >print    ) Prints "8" and leaves 8 on AL
```

**Check Store values:**
```soma
counter >toString >print  ) Print current value
```

**Trace execution:**
```soma
(Entering block A) >print
) ... code ...
(Exiting block A) >print
```

---

## 9. Problem-Solving Strategy

### Step 1: Understand Data Flow
- What inputs? (on AL? in Store?)
- What outputs? (AL? Store? print?)
- What intermediate values needed?

### Step 2: Choose Storage
- **AL**: Temporary computation, arguments/results
- **Store**: Persistent state, shared across blocks
- **Register**: Block-local temporary (isolated!)

### Step 3: Break into Sub-Problems
- Can you use stdlib operations?
- Need loops? (`while`, `times`, or `chain + block`)
- Need conditionals? (`choose`, `if`)
- Need recursion? (Store block, use `chain`)

### Step 4: Build Incrementally
1. Write smallest working piece
2. Test with `>print` to verify AL state
3. Add one feature at a time
4. Test after each addition

### Step 5: Common Algorithm Patterns

**Iteration:**
```soma
{ condition } { body } >while
```

**Recursion:**
```soma
{ base_case base_result recursive_result >choose } !func
args func >chain
```

**Accumulation:**
```soma
0 !sum
{ condition } { item sum >+ !sum } >while
```

**Filtering:**
```soma
{ condition }
{ item >passes { item >process } { } >ifelse }
>while
```

---

## 10. Language Translation Guide

### From Python to SOMA

```python
# Python                    # SOMA

x = 5                       5 !x

y = x + 3                   x 3 >+ !y

if x < 10:                  x 10 ><
    print("small")            { (small) >print }
else:                         { (large) >print }
    print("large")          >ifelse

while x < 10:               { x 10 >< }
    x += 1                  { x >inc !x }
                            >while

for i in range(10):         10 { body } >times
    body()

print(x)                    x >toString >print
```

### From JavaScript to SOMA

```javascript
// JavaScript               // SOMA

let x = 5;                  5 !x

const y = x + 3;            x 3 >+ !y

if (x < 10) {               x 10 ><
  console.log("small");       { (small) >print }
} else {                      { (large) >print }
  console.log("large");     >ifelse
}

while (x < 10) {            { x 10 >< }
  x++;                      { x >inc !x }
}                           >while

function add(a, b) {        { !_.b !_.a _.a _.b >+ } !add
  return a + b;
}                           5 3 >add
```

### From Functional (Haskell-style) to SOMA

```haskell
-- Haskell                  -- SOMA

let x = 5 in expr           5 !_.x expr (in block)

f x                         x >f

map f xs                    -- Custom with loop
filter p xs                 -- Custom with loop
foldl f acc xs              -- Custom with loop + accumulator
```

---

## 11. SOMA Repository Reference

When you need more details, refer to these files in the SOMA repository:

### Documentation
- **Programming idioms:** `docs/09-idioms.md` - **Start here for execution scope!**
- **Syntax details:** `docs/02-lexer.md`
- **Execution model:** `docs/03-machine-model.md`
- **Blocks and execution:** `docs/04-blocks-execution.md`
- **Control flow:** `docs/05-control-flow.md`
- **FFI reference:** `docs/06-builtins.md`
- **Stdlib reference:** `docs/11-stdlib.md`
- **Examples:** `docs/08-examples.md`
- **Comparisons:** `docs/07-comparisons.md`

### Source Code
- **Stdlib implementation:** `soma/stdlib.soma`
- **VM implementation:** `soma/vm.py`
- **Parser:** `soma/parser.py`
- **Lexer:** `soma/lexer.py`

### Tests (Working Examples)
- **FFI tests:** `tests/soma/01_ffi_builtins.soma`
- **Stdlib tests:** `tests/soma/02_stdlib.soma`
- **Idioms tests:** `tests/soma/03_*.soma` - **Context-passing, loops, execution scope**

### Running Tests
```bash
cd <soma-repository>
python3 tests/run_soma_tests.py
```

---

## 12. Quick Start Template

Use this template to start writing SOMA programs:

```soma
) Program description: [What does this do?]

) Initialize state
0 !counter
Nil !result

) Main logic
{
  ) Your code here
  counter >print
  counter >inc !counter

  ) Loop condition
  counter 10 ><
    >block       ) Continue - push current block
    Nil          ) Stop
  >choose
} !main

) Execute
>main

) Output result
result >toString >print
```

---

## Key Reminders

1. **Initialize before reading:** Reading undefined paths raises RuntimeError - always initialize first
2. **Auto-vivification on writes only:** Writing `!a.b.c` creates intermediate paths that CAN be read
3. **Execution scope, not lexical:** Blocks get fresh Registers - use `_.` → `!_.` to pass context
4. **Strings use parentheses:** `(text)` not `"text"`
5. **Execute with >:** `>operation` not just `operation`
6. **Register is isolated:** Each block gets fresh, empty Register - no automatic access to parent
7. **Blocks are values:** They don't execute until you use `>`
8. **AL is LIFO:** Last pushed is first popped
9. **Store is global:** Visible to all blocks
10. **Void can't be stored:** Use Nil instead
11. **Comments use ):** Not `//` or `#` or `;`
12. **>chain for loops/tail-calls:** Use `>{ }` or `>func` for single execution
13. **>choose selects, doesn't execute:** Use `>^` or `>ifelse` to execute the result
14. **Context-passing is key:** See `docs/09-idioms.md` for the full pattern

---

## When You Get Stuck

This skill document is a **quick reference** designed for common tasks. For comprehensive documentation on all SOMA features, syntax details, and advanced topics:

**📚 Full SOMA Documentation:**
https://github.com/SonicField/soma/blob/main/docs/index.md

**Key documentation highlights:**

- **String escapes and special characters:** `docs/02-lexer.md` section 2.5
  - Unicode escapes: `\HEX\` (e.g., `\28\` for `(`, `\29\` for `)`, `\b0\` for `°`)
  - String literal rules and multiline strings

- **Execution scope and context-passing:** `docs/09-idioms.md`
  - The context-passing idiom with `_.` → `!_.`
  - Advanced patterns for sharing state between blocks

- **Complete builtin reference:** `docs/06-builtins.md`
  - All FFI primitives with detailed signatures
  - Edge cases and type requirements

- **Working examples:** `tests/soma/` directory
  - Real SOMA programs you can run and study
  - Test files demonstrate best practices

**Can't find what you need?** The official docs are comprehensive and regularly updated!

---

## Philosophy

SOMA reveals computation rather than obscuring it:
- State is explicit (visible stores and mutations)
- Execution is explicit (`>` prefix)
- Control flow is explicit (blocks + choose + chain)
- Everything is built from minimal primitives
- Users can extend the language using the same mechanisms as built-ins

This makes SOMA ideal for understanding how computation works at a fundamental level.
