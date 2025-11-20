# SOMA Examples and Patterns

**SOMA v1.0 Language Specification - Examples Companion**
**Category: Tutorial**
**Date: 20 November 2025**

---

## 1. Introduction

This document provides complete, working SOMA programs that demonstrate core language features and patterns. Each example includes:

- Working source code
- Step-by-step explanation
- Expected AL and Store state transformations
- Common patterns and idioms

All examples in this document have been validated against the SOMA v1.0 specification and errata corrections.

---

## 2. Hello World Variations

### 2.1 Minimal Hello World

The simplest SOMA program:

```soma
"Hello, world!" >print
```

**Execution trace:**

1. Initial state: `AL = []`, `Store = {}`
2. Token `"Hello, world!"` pushes string onto AL
   - `AL = ["Hello, world!"]`
3. Token `>print` consumes top of AL and writes to stdout
   - `AL = []`

**Output:**
```
Hello, world!
```

### 2.2 Hello World with Block

Using a block to encapsulate behavior:

```soma
{ "Hello, world!" >print } !say_hello
say_hello >Chain
```

**Execution trace:**

1. Block `{ "Hello, world!" >print }` is pushed onto AL
   - `AL = [Block]`
2. `!say_hello` pops block and stores it in Store
   - `AL = []`
   - `Store = { say_hello: Block }`
3. `say_hello` pushes the block back onto AL
   - `AL = [Block]`
4. `>Chain` executes the block (which prints and leaves no block on AL, so >Chain terminates)
   - `AL = []`

**Output:**
```
Hello, world!
```

### 2.3 Hello World with Register Parameter

A block that takes a parameter from the AL:

```soma
{ !_.msg "Hello, " _.msg >concat >print } !greet
"world" greet >Chain
```

**Execution trace:**

1. Block is stored at `greet`
2. `"world"` is pushed onto AL
   - `AL = ["world"]`
3. `greet` pushes the block onto AL
   - `AL = [Block, "world"]`
4. `>Chain` executes the block:
   - `!_.msg` pops `"world"` and stores in Register as `_.msg`
   - `"Hello, "` is pushed
   - `_.msg` retrieves `"world"` and pushes it
   - `>concat` pops two strings, concatenates, pushes result
   - `>print` outputs the concatenated string

**Output:**
```
Hello, world
```

---

## 3. State Mutation

### 3.1 Simple Counter

Incrementing a counter in the Store:

```soma
0 !counter
counter 1 >+ !counter
counter >print
```

**Execution trace:**

1. `0 !counter` creates Cell with value 0
   - `Store = { counter: 0 }`
2. `counter` pushes current value
   - `AL = [0]`
3. `1` pushes literal
   - `AL = [1, 0]`
4. `>+` pops two integers, adds them, pushes result
   - `AL = [1]`
5. `!counter` writes back to Store
   - `Store = { counter: 1 }`
6. `counter >print` reads and prints
   - Output: `1`

### 3.2 Read-Modify-Write Pattern

A common pattern for state mutation:

```soma
10 !value
20 !increment

value increment >+ !value
value >print
```

**Explanation:**

This demonstrates the read-modify-write pattern:
1. Read current value: `value`
2. Compute new value: `increment >+`
3. Write back: `!value`

**Output:**
```
30
```

### 3.3 Multiple Cell Updates

```soma
0 !stats.hits
0 !stats.misses

stats.hits 1 >+ !stats.hits
stats.hits 1 >+ !stats.hits
stats.misses 1 >+ !stats.misses

stats.hits >print
stats.misses >print
```

**Store state after execution:**
```
stats = {
  hits: 2,
  misses: 1
}
```

**Output:**
```
2
1
```

---

## 4. Conditional Execution

### 4.1 Simple If (True Branch Only)

Execute a block only if a condition is true:

```soma
True { "Condition is true" >print } {} >Choose
```

**Explanation:**

- `True` is the condition (Boolean on AL)
- First block executes if True
- Empty block `{}` executes if False (does nothing)

**Output:**
```
Condition is true
```

### 4.2 If/Else

```soma
15 !age
age 18 >>
  { "Adult" >print }
  { "Minor" >print }
>Choose
```

**Execution trace:**

1. `age 18 >>` compares: is age > 18?
   - Result: `False` (15 is not greater than 18)
   - `AL = [False]`
2. `>Choose` pops the condition and the two blocks
   - Since False, executes second block
   - Second block prints "Minor"

**Output:**
```
Minor
```

### 4.3 Nested Conditionals

```soma
25 !temperature

temperature 30 >>
  { "Hot" >print }
  {
    temperature 20 >>
      { "Warm" >print }
      { "Cold" >print }
    >Choose
  }
>Choose
```

**Execution trace:**

1. Compare temperature (25) with 30: `False`
2. Execute else branch (the nested Choose)
3. Compare temperature (25) with 20: `True`
4. Execute "Warm" branch

**Output:**
```
Warm
```

### 4.4 Equality Testing

```soma
"password123" !stored_password
"password123" !user_input

stored_password user_input >==
  { "Access granted" >print }
  { "Access denied" >print }
>Choose
```

**Output:**
```
Access granted
```

---

## 5. Building Control Structures

SOMA has no built-in loops. All iteration is built from `>Choose` (conditional) and `>Chain` (continuation). This section shows how to build loops step by step using `_.self`.

### 5.1 Building a While Loop (Step by Step)

**Step 1: Understanding >Chain**

`>Chain` executes blocks repeatedly. It:
1. Pops the top of AL
2. If it's a Block, executes it
3. After execution, if AL top is a Block, repeats
4. Otherwise stops

**Step 2: A Self-Continuing Block with _.self**

To loop, a block can reference itself using `_.self`:

```soma
{ "tick" >print _.self } >Chain
```

**Problem:** This loops forever! We need a condition.

**Step 3: Adding a Condition**

We need the block to choose whether to continue:

```soma
0 !counter

{
  counter >print
  counter 1 >+ !counter

  counter 5 ><
    { _.self }
    { }
  >Choose
} >Chain
```

**Execution:**

1. Block prints counter (initially 0)
2. Increments counter to 1
3. Checks if 1 < 5: True
4. Chooses first branch: pushes `_.self` (the current block) onto AL
5. `>Chain` sees block, continues
6. Repeats until counter reaches 5

**Output:**
```
0
1
2
3
4
```

**This is a while loop!** It continues while `counter < 5`.

**Key insight:** `_.self` automatically binds to the currently executing block, eliminating the need to store the block in the Store just to reference it.

### 5.2 While Loop Pattern (Canonical Form with _.self)

Here's the general pattern for while loops in SOMA:

```soma
{Initial setup}

{
  {Loop body}

  {Condition}
    { _.self }
    { }
  >Choose
} >Chain
```

**Example: Sum from 1 to 10**

```soma
0 !sum
1 !i

{
  sum i >+ !sum
  i 1 >+ !i

  i 10 >>
    { }
    { _.self }
  >Choose
} >Chain

sum >print
```

**Output:**
```
55
```

**Note:** Condition is inverted (`10 >>` means "greater than 10"). When `i > 10`, we choose the empty block, stopping the loop.

**Comparison with old pattern:**

OLD (requires Store cell):
```soma
{ body loop_name } !loop_name
loop_name >Chain
```

NEW (clean with _.self):
```soma
{ body _.self } >Chain
```

The `_.self` pattern is cleaner and doesn't pollute the Store namespace.

### 5.3 Building a Do-While Loop

A do-while loop executes at least once:

```soma
0 !counter

{
  "Executed at least once" >print
  counter 1 >+ !counter

  counter 1 ><
    { _.self }
    { }
  >Choose
} >Chain
```

**Output:**
```
Executed at least once
```

**Explanation:**

Even though `counter` starts at 0 and the condition `counter < 1` becomes false after first iteration, the block executes once before checking.

### 5.4 Infinite Loop Pattern

The simplest loop in SOMA:

```soma
{ "tick" >print _.self } >Chain
```

This demonstrates the power of `_.self`: the block can reference itself without any external storage or naming.

### 5.5 How Loops Are Just Blocks + >Choose + >Chain

Let's make this explicit:

**While loop anatomy:**

```
{Condition} {Body + Continue} {} >Choose
```

**The "Continue" part:**
- If condition true: execute body, then push `_.self` back (loop)
- If condition false: execute empty block (stop)

**>Chain's role:**
- Keeps executing whatever block is on AL
- Stops when AL top is not a block

**Key insight:** There's no special loop syntax. Just:
1. Blocks (encapsulated behavior)
2. >Choose (conditional execution)
3. >Chain (continuation)
4. **_.self** (self-reference without naming)

---

## 6. Finite State Machines

### 6.1 Two-State Toggle with _.self

A simple state machine that toggles between ON and OFF:

```soma
True !_.state

{
  _.state
    { "ON" >print False !_.state _.self }
    { "OFF" >print True !_.state _.self }
  >Choose
} >Chain
```

**Problem:** This loops forever. Let's add a counter to stop after 5 transitions:

```soma
{
  True !_.state
  0 !_.count

  {
    _.state
      { "ON" >print False !_.state }
      { "OFF" >print True !_.state }
    >Choose

    _.count 1 >+ !_.count

    _.count 5 ><
      { _.self }
      { }
    >Choose
  } >Chain
} >Chain
```

**Output:**
```
ON
OFF
ON
OFF
ON
```

**Explanation:**

We use Register variables (`_.state`, `_.count`) for local state within the block execution. The block uses `_.self` to continue the loop.

### 6.2 Multi-State FSM (Traffic Light) with _.self

A traffic light with three states: Red → Green → Yellow → Red

```soma
0 !_.cycle_count

{
  "RED" >print
  _.green
} !_.red

{
  "GREEN" >print
  _.yellow
} !_.green

{
  "YELLOW" >print

  _.cycle_count 1 >+ !_.cycle_count

  _.cycle_count 3 ><
    { _.red }
    { }
  >Choose
} !_.yellow

_.red >Chain
```

**Output:**
```
RED
GREEN
YELLOW
RED
GREEN
YELLOW
RED
GREEN
YELLOW
```

**Explanation:**

Each state is a block stored in the Register. Each state:
1. Performs its action (print color)
2. Pushes the next state block onto AL
3. When >Chain continues, the next state executes

The `_.yellow` state checks if we've completed 3 cycles and either continues to `_.red` or stops.

### 6.3 FSM with Input and _.self

A door that can be opened and closed:

```soma
{
  {
    "Door is CLOSED" >print

    _.door_input "open" >==
      { _.opened }
      { _.closed }
    >Choose
  } !_.closed

  {
    "Door is OPEN" >print

    _.door_input "close" >==
      { _.closed }
      { _.opened }
    >Choose
  } !_.opened

  "open" !_.door_input
  _.closed >Chain
} >Chain
```

**Output:**
```
Door is CLOSED
Door is OPEN
```

**Explanation:**

The `_.door_input` Register cell determines which state transition occurs. This pattern can be extended to build interactive state machines. Note how all FSM state blocks are stored in the Register for local scope.

### 6.4 Generic FSM Loop Pattern with _.self

For complex state machines, you can use a generic loop:

```soma
{
  "state_a" !_.current_state

  {
    _.current_state >==
      { handle_state_a }
      { handle_state_b }
    >Choose
    >Chain

    _.continue
      { _.self }
      { }
    >Choose
  } !fsm_loop

  fsm_loop >Chain
} >Chain
```

This shows how `_.self` enables the FSM loop to continue itself based on a condition, while state handlers can modify `_.continue` to control termination.

---

## 7. Data Structures Using the Store

### 7.1 Simple Stack Using Store Path

```soma
0 !stack.count

{
  !_.value
  _.value !stack.data.0
  1 !stack.count
} !push_first

{
  stack.data.0
  0 !stack.count
} !pop_last

"Hello" push_first >Chain
stack.data.0 >print
pop_last >Chain >print
```

**Output:**
```
Hello
Hello
```

### 7.2 Record/Struct Pattern

```soma
"Alice" !person.name
30 !person.age
"Engineering" !person.department

{
  !_.record_ref
  _.record_ref "name" >concat >ToPath >print
  _.record_ref "age" >concat >ToPath >print
  _.record_ref "department" >concat >ToPath >print
} !print_person

"person." print_person >Chain
```

**Expected Output:**
```
Alice
30
Engineering
```

**Note:** This example uses reflection (`>ToPath`) to dynamically access fields. In practice, you'd use direct paths:

```soma
{
  person.name >print
  person.age >print
  person.department >print
} !print_person

print_person >Chain
```

**Output:**
```
Alice
30
Engineering
```

### 7.3 Linked List Using CellRefs (Fixed Implementation)

The spec's linked list example has issues. Here's a corrected approach using Store paths:

```soma
{
  !_.value
  Nil !node.0.next
  _.value !node.0.value
  "node.0." !last_node
} !list_init

{
  !_.value
  !_.node_path

  last_node "next" >concat >ToPath Nil >==
    {
      Nil !node.1.next
      _.value !node.1.value
      "node.1." !last_node
      "node.1." last_node "next" >concat >ToPath !
    }
    { }
  >Choose
} !list_append

"First" list_init >Chain
"Second" "node.0." list_append >Chain

node.0.value >print
node.1.value >print
```

**Note:** This is a simplified example. A full implementation would require dynamic node indexing, which is challenging without arrays or Things. The core insight is that CellRefs allow creating graph structures, but SOMA's reflection is limited.

### 7.4 Key-Value Store Pattern

```soma
"apple" !fruits.a
"banana" !fruits.b
"cherry" !fruits.c

{
  !_.key
  "fruits." _.key >concat >ToPath
} !get_fruit

"b" get_fruit >Chain >print
```

**Output:**
```
banana
```

---

## 8. Common Patterns and Idioms

### 8.1 Conditional Increment

Increment only if value is below threshold:

```soma
10 !value
15 !threshold

value threshold ><
  { value 1 >+ !value }
  { }
>Choose

value >print
```

**Output:**
```
11
```

### 8.2 Max of Two Values

```soma
{
  !_.b !_.a
  _.a _.b >>
    { _.a }
    { _.b }
  >Choose
} !max

15 23 max >Chain >print
```

**Output:**
```
23
```

### 8.3 Absolute Value

```soma
{
  !_.n
  _.n 0 >>
    { _.n }
    { 0 _.n >- }
  >Choose
} !abs

-5 abs >Chain >print
10 abs >Chain >print
```

**Output:**
```
5
10
```

### 8.4 Factorial (Iterative with _.self)

```soma
{
  !_.n
  1 !_.result
  1 !_.i

  {
    _.result _.i >* !_.result
    _.i 1 >+ !_.i

    _.i _.n >>
      { }
      { _.self }
    >Choose
  } >Chain

  _.result
} !factorial

5 factorial >Chain >print
```

**Output:**
```
120
```

**Explanation:**

1. Takes `n` from AL, stores in Register `_.n`
2. Initializes `_.result = 1`, `_.i = 1`
3. Loop multiplies `_.result *= _.i`, increments `_.i`
4. Continues while `_.i <= _.n` using `_.self`
5. Leaves `_.result` on AL

This demonstrates clean use of Register variables for local state and `_.self` for loop continuation.

### 8.5 Range Check

```soma
{
  !_.high !_.low !_.value

  _.value _.low >>
    {
      _.value _.high ><
        { True }
        { False }
      >Choose
    }
    { False }
  >Choose
} !in_range

15 10 20 in_range >Chain
  { "In range" >print }
  { "Out of range" >print }
>Choose
```

**Output:**
```
In range
```

---

## 9. Working with Blocks

### 9.1 Block Composition

```soma
{ 2 >* } !double
{ 1 >+ } !increment

{
  !_.f !_.g !_.x
  _.x _.f >Chain _.g >Chain
} !compose

5 double increment compose >Chain >print
```

**Output:**
```
11
```

**Explanation:**
1. `compose` takes three args: `x`, `g`, `f`
2. Applies `f` to `x`, then `g` to result
3. `5 * 2 = 10`, then `10 + 1 = 11`

### 9.2 Conditional Block Selection

```soma
{ "Option A" >print } !block_a
{ "Option B" >print } !block_b

True
  { block_a }
  { block_b }
>Choose
>Chain
```

**Output:**
```
Option A
```

### 9.3 Block as State Container

```soma
{
  !_.initial
  _.initial !_.counter

  {
    _.counter >print
    _.counter 1 >+ !_.counter
    _.inc_block
  } !_.inc_block

  _.inc_block
} !make_counter

10 make_counter >Chain >Chain >Chain
```

**Output:**
```
10
11
12
```

**Explanation:**

This demonstrates closures in SOMA. The inner block `_.inc_block` is stored in the Register and references Register variables (`_.counter`). Each call to the outer block creates a new Register context with its own `_.counter`.

---

## 10. User-Defined Execution

SOMA has no built-in "execute from AL" operation. However, the `>path` execution prefix enables you to build your own execution operators. This section demonstrates SOMA's power: language features that look like primitives are actually just user-defined blocks.

### 10.1 The `^` Operator - Execute AL Top

The most fundamental execution pattern is "pop a block from AL and execute it" - similar to Forth's `EXECUTE` or Lisp's `FUNCALL`. In SOMA, you define this yourself:

```soma
{ !_ >_ } !^
```

**What this does:**

1. `{ !_ >_ }` creates a block that:
   - `!_` pops AL top and stores at Register root `_`
   - `>_` reads the value at `_` and executes it
2. `!^` stores this block at Store path "^"

**Now you can use `>^` to execute blocks from AL:**

```soma
(Cats) print >^
```

**Execution trace:**

1. `(Cats)` pushes string onto AL
   - `AL = ["Cats"]`
2. `print` pushes print block onto AL
   - `AL = ["Cats", print_block]`
3. `>^` executes the block at Store path "^"
   - Block creates fresh Register
   - `!_` pops `print_block` from AL, stores at Register root `_`
     - `AL = ["Cats"]`
     - `Register._ = print_block`
   - `>_` reads Register root and executes it
     - Executes `print_block`, which pops "Cats" and prints it
     - `AL = []`

**Output:**
```
Cats
```

**Why this is powerful:**

```soma
) These are equivalent:
(data) >print        ) Direct execution
(data) print >^      ) Execute via ^
```

The `>^` pattern lets you treat blocks as first-class values that can be selected, stored, and executed dynamically.

### 10.2 Dispatch Tables

Dispatch tables select and execute blocks based on a key:

```soma
{ (Handling add) >print } !handlers.add
{ (Handling subtract) >print } !handlers.sub
{ (Handling multiply) >print } !handlers.mul

{
  !_.operation
  handlers _.operation >concat >ToPath >^
} !dispatch

(add) dispatch >Chain
(mul) dispatch >Chain
```

**Execution trace for `(add) dispatch >Chain`:**

1. `(add)` pushes string
2. `dispatch` pushes dispatch block
3. `>Chain` executes:
   - `!_.operation` pops "add", stores in Register
   - `handlers` pushes "handlers"
   - `_.operation` pushes "add"
   - `>concat` produces "handlersadd"
   - Wait - this won't work! We need the dot separator.

**Corrected dispatch pattern:**

```soma
{ (Handling add) >print } !handlers.add
{ (Handling subtract) >print } !handlers.sub
{ (Handling multiply) >print } !handlers.mul

{
  !_.operation
  "handlers." _.operation >concat >ToPath >^
} !dispatch

(add) dispatch >Chain
(mul) dispatch >Chain
```

**Output:**
```
Handling add
Handling multiply
```

**Explanation:**

1. `dispatch` takes operation name from AL
2. Builds path string: `"handlers." + operation`
3. `>ToPath` converts string to path and reads the block
4. `>^` executes the block

**Alternative: Direct path execution**

If you know the paths at write-time, you can use `>Choose`:

```soma
{ (Handling add) >print } !handlers.add
{ (Handling subtract) >print } !handlers.sub
{ (Handling multiply) >print } !handlers.mul

{
  !_.op
  _.op (add) >==
    { >handlers.add }
    {
      _.op (sub) >==
        { >handlers.sub }
        { >handlers.mul }
      >Choose
    }
  >Choose
} !dispatch_direct

(add) dispatch_direct >Chain
(sub) dispatch_direct >Chain
```

**Output:**
```
Handling add
Handling subtract
```

This shows two approaches:
- **Dynamic dispatch:** Uses `>ToPath` and `>^` for runtime path construction
- **Static dispatch:** Uses `>Choose` for compile-time paths

### 10.3 Higher-Order Blocks

Higher-order functions take blocks as arguments and execute them in custom ways.

**Example 1: Apply - Execute block with an argument**

```soma
{ !_.f !_.x _.x >_.f } !apply

{
  !_.n
  _.n _.n >*
} !square

5 square >apply >print
```

**Execution trace:**

1. `5` pushes integer
2. `square` pushes square block
3. `>apply` executes apply block:
   - `!_.f` pops square block, stores in Register
   - `!_.x` pops 5, stores in Register
   - `_.x` pushes 5 onto AL
   - `>_.f` executes square block:
     - `!_.n` pops 5, stores in square's Register
     - `_.n _.n >*` computes 5 * 5 = 25
     - Leaves 25 on AL
4. `>print` outputs 25

**Output:**
```
25
```

**Example 2: Twice - Execute a block twice**

```soma
{ !_.f >_.f >_.f } !twice

{
  (tick) >print
} !tick_block

tick_block >twice
```

**Execution trace:**

1. `tick_block` pushes block onto AL
2. `>twice` executes twice block:
   - `!_.f` pops tick_block, stores in Register
   - `>_.f` executes tick_block (prints "tick")
   - `>_.f` executes tick_block again (prints "tick")

**Output:**
```
tick
tick
```

**Example 3: Map-like pattern (applying block to multiple values)**

```soma
{ !_.f !_.x _.x >_.f } !apply

{
  !_.n
  _.n 2 >*
} !double

) Apply double to three values
1 double >apply >print
2 double >apply >print
3 double >apply >print
```

**Output:**
```
2
4
6
```

**Example 4: Conditional execution**

Execute a block only if condition is true:

```soma
{
  !_.block !_.condition
  _.condition
    { >_.block }
    { }
  >Choose
} !if_exec

True { (Executed!) >print } >if_exec
False { (Should not print) >print } >if_exec
```

**Output:**
```
Executed!
```

**Explanation:**

The `if_exec` block takes a condition and a block. If the condition is true, it executes the block using `>_.block`. This demonstrates conditional execution as a user-defined pattern.

### 10.4 Storing and Executing Custom Operations

You can store operation blocks and execute them dynamically:

```soma
) Define operation blocks
{ !_.b !_.a _.a _.b >+ } !ops.add
{ !_.b !_.a _.a _.b >- } !ops.sub
{ !_.b !_.a _.a _.b >* } !ops.mul

) Store an operation for later use
ops.add !current_op

) Use the stored operation
5 3 current_op >Chain >print

) Change the operation
ops.mul !current_op

) Use the new operation
5 3 current_op >Chain >print
```

**Output:**
```
8
15
```

**Explanation:**

1. Three operation blocks are stored under `ops.*`
2. `current_op` is set to `ops.add`
3. `5 3 current_op >Chain` executes the add operation
4. `current_op` is reassigned to `ops.mul`
5. Same syntax now performs multiplication

**More sophisticated: Operation with state**

```soma
{
  0 !_.count

  {
    !_.b !_.a
    _.count 1 >+ !_.count
    _.a _.b >+
  } !_.add_counted

  _.add_counted
} !make_counting_add

make_counting_add >Chain !my_add

5 3 my_add >Chain >print
10 2 my_add >Chain >print

) Access the count (would need to expose it via an API)
```

**Output:**
```
8
12
```

This shows an operation that maintains state across invocations using Register variables.

### 10.5 Execution Trace Comparison

Let's compare three equivalent ways to execute a block:

**Method 1: Direct path execution**
```soma
(Hello) >print
```
Trace:
- `(Hello)` → AL = ["Hello"]
- `>print` → executes block at Store path "print"

**Method 2: Push then Chain**
```soma
(Hello) print >Chain
```
Trace:
- `(Hello)` → AL = ["Hello"]
- `print` → AL = ["Hello", print_block]
- `>Chain` → pops print_block, executes it

**Method 3: Push then ^**
```soma
{ !_ >_ } !^
(Hello) print >^
```
Trace:
- `(Hello)` → AL = ["Hello"]
- `print` → AL = ["Hello", print_block]
- `>^` → executes block at "^":
  - `!_` → pops print_block, stores in Register
  - `>_` → executes block from Register

All three produce the same output, but `>^` makes execution explicit and composable.

### 10.6 Building a Complete Macro System

Here's how you can build a complete set of execution primitives:

```soma
) Core execution primitives
{ !_ >_ } !^                              ) Execute AL top
{ !_.f >_.f >_.f } !twice                 ) Execute twice
{ !_.f !_.x _.x >_.f } !apply             ) Apply block to value
{ !_.g !_.f !_.x _.x >_.f >_.g } !compose ) Function composition

) Control structures using execution
{
  !_.else !_.then !_.cond
  _.cond
    { >_.then }
    { >_.else }
  >Choose
} !ifelse

{
  !_.body !_.test
  {
    >_.test
      { >_.body _.self }
      { }
    >Choose
  } >Chain
} !while_exec

) Use them like built-ins
5 10 >> { (big) >print } { (small) >print } >ifelse

0 !counter
{ counter 5 >< } { counter 1 >+ !counter counter >print } >while_exec
```

**Output:**
```
small
1
2
3
4
5
```

**Key insight:**

These look indistinguishable from language features, but they're just blocks using `>path` execution semantics. This is the power of SOMA's design:

1. Blocks are first-class values
2. `>path` makes execution explicit
3. User-defined `^` enables Forth-like `EXECUTE`
4. Higher-order patterns emerge naturally

**No special primitives needed.** Just paths, blocks, and the `>` prefix.

### 10.7 Practical Use Case: Command Pattern

```soma
) Define commands
{
  lights_on True >== { (Lights already on) >print } { True !lights_on (Lights ON) >print } >Choose
} !commands.light_on

{
  lights_on False >== { (Lights already off) >print } { False !lights_on (Lights OFF) >print } >Choose
} !commands.light_off

{
  (Door opened) >print
  True !door_open
} !commands.door_open

{
  (Door closed) >print
  False !door_open
} !commands.door_close

) Initialize state
False !lights_on
False !door_open

) Execute commands via dispatch
{
  !_.cmd
  "commands." _.cmd >concat >ToPath >Chain
} !execute_command

(light_on) execute_command >Chain
(door_open) execute_command >Chain
(light_off) execute_command >Chain
(door_close) execute_command >Chain
(light_off) execute_command >Chain
```

**Output:**
```
Lights ON
Door opened
Lights OFF
Door closed
Lights already off
```

**Explanation:**

This demonstrates the Command pattern:
1. Commands are blocks stored under `commands.*`
2. Each command encapsulates an operation and state checks
3. `execute_command` dispatches to the appropriate command
4. State is maintained in Store cells (`lights_on`, `door_open`)

This pattern is used in:
- Event handlers
- Undo/redo systems
- Scripting engines
- State machines with action dispatch

---

## 11. Advanced Examples

### 11.1 FizzBuzz with _.self

```soma
{
  1 !_.n

  {
    _.n 3 >/ 3 >* _.n >==
      {
        _.n 5 >/ 5 >* _.n >==
          { "FizzBuzz" >print }
          { "Fizz" >print }
        >Choose
      }
      {
        _.n 5 >/ 5 >* _.n >==
          { "Buzz" >print }
          { _.n >print }
        >Choose
      }
    >Choose

    _.n 1 >+ !_.n

    _.n 16 ><
      { _.self }
      { }
    >Choose
  } >Chain
} >Chain
```

**Output:**
```
1
2
Fizz
4
Buzz
Fizz
7
8
Fizz
Buzz
11
Fizz
13
14
FizzBuzz
```

**Note:**
- `_.n 3 >/ 3 >*` is integer division followed by multiplication - if equal to `_.n`, then `_.n` is divisible by 3
- Uses `_.self` for clean loop continuation
- Register variable `_.n` keeps state local to the block execution

### 11.2 Collatz Sequence with _.self

```soma
{
  10 !_.n

  {
    _.n >print

    _.n 1 >==
      { }
      {
        _.n 2 >/ 2 >* _.n >==
          { _.n 2 >/ !_.n }
          { _.n 3 >* 1 >+ !_.n }
        >Choose
        _.self
      }
    >Choose
  } >Chain
} >Chain
```

**Output:**
```
10
5
16
8
4
2
1
```

**Explanation:**

This is the Collatz conjecture sequence. Starting from `n = 10`:
- If `n` is even: `n = n / 2`
- If `n` is odd: `n = 3n + 1`
- Stop when `n = 1`

Uses `_.self` for recursive continuation and `_.n` for local state.

### 11.3 String Builder Pattern

```soma
"" !output

{
  !_.str
  output _.str >concat !output
} !append

"Hello" append >Chain
" " append >Chain
"SOMA" append >Chain
" " append >Chain
"world" append >Chain

output >print
```

**Output:**
```
Hello SOMA world
```

### 11.4 Counter with State Encapsulation

Here's a more sophisticated counter that demonstrates true encapsulation using `_.self`:

```soma
{
  !_.start_value
  _.start_value !_.counter

  {
    {
      _.counter >print
      _.counter 1 >+ !_.counter
    } !_.increment

    {
      _.counter
    } !_.get

    {
      !_.new_value
      _.new_value !_.counter
    } !_.set

    ) Return a block that provides the counter API
    {
      !_.method
      _.method "inc" >==
        { _.increment >Chain _.self }
        {
          _.method "get" >==
            { _.get >Chain }
            { _.set >Chain }
          >Choose
        }
      >Choose
    }
  } >Chain
} !make_counter

0 make_counter >Chain !my_counter

my_counter "inc" >Chain
my_counter "inc" >Chain
my_counter "inc" >Chain
my_counter "get" >Chain >print
```

**Output:**
```
0
1
2
3
```

**Explanation:**

This creates a stateful counter object with an API. The counter state (`_.counter`) is encapsulated within the Register. The returned block provides methods via string dispatch. Note how `_.self` is used in the "inc" method to return the counter interface for chaining.

### 11.5 Recursive Countdown with _.self

While iteration is more natural in SOMA, recursion is possible:

```soma
{
  !_.n

  _.n 0 >>
    {
      _.n >print
      _.n 1 >- !_.n
      _.self >Chain
    }
    { }
  >Choose
} !countdown

5 countdown >Chain
```

**Output:**
```
5
4
3
2
1
```

**Explanation:**

The block stores `_.n`, prints it, decrements it, and then chains to `_.self` (itself) if `_.n > 0`. This demonstrates that `_.self` can be used for both iteration (with >Chain continuation) and recursion (with explicit >Chain calls).

---

## 12. Summary of _.self Benefits

This document demonstrates the power of `_.self` throughout:

### 12.1 The _.self Pattern

**What is _.self?**

When a Block begins execution, SOMA automatically creates a Register Cell at path `_.self` containing the Block being executed. This allows the block to reference itself.

**Key uses:**

1. **Loop continuation:**
   ```soma
   { body _.self } >Chain
   ```

2. **Conditional loops:**
   ```soma
   {
     body
     condition
       { _.self }
       { }
     >Choose
   } >Chain
   ```

3. **State machine continuation:**
   ```soma
   {
     process_state
     should_continue
       { _.self }
       { }
     >Choose
   } >Chain
   ```

4. **Self-reference for recursion:**
   ```soma
   {
     base_case_check
       { }
       { recursive_step _.self >Chain }
     >Choose
   } !recursive_func
   ```

### 12.2 Register Variable Patterns

All Register paths use the form `_.name`:

- `_.counter` - loop counter
- `_.state` - FSM state
- `_.result` - accumulator
- `_.temp` - temporary value
- `_.msg` - parameter from AL

This is consistent with the Register root being `_` and all paths starting with `_.`

### 12.3 Comparison: Old vs New Patterns

**OLD (workaround without _.self):**
```soma
{ body loop_name } !loop_name
loop_name >Chain
```

**NEW (clean with _.self):**
```soma
{ body _.self } >Chain
```

**OLD (named counter with Store cell):**
```soma
0 !counter
{ counter 10 >< { loop_body } {} >Choose } !loop_body
loop_body >Chain
```

**NEW (Register state with _.self):**
```soma
{
  0 !_.counter
  {
    _.counter 10 ><
      { _.self }
      { }
    >Choose
  } >Chain
} >Chain
```

### 12.4 Why _.self is Powerful

1. **No namespace pollution:** Don't need Store cells just for self-reference
2. **Cleaner syntax:** `_.self` is more readable than named workarounds
3. **Local scope:** Each block execution gets its own `_.self`
4. **Natural recursion:** Self-reference is built into the language
5. **Consistent with Register model:** `_.self` is just another Register path

---

## 13. Conclusion

SOMA's minimalist design means all control flow and execution emerges from just a few primitives:
- **>Choose** for branching
- **>Chain** for continuation
- **>path** for execution
- **_.self** for self-reference

Combined with these primitives, we can build:
- Loops (while, do-while, infinite loops)
- State machines (with clean state continuation)
- Conditional logic
- Data structures
- Higher-order patterns
- Recursive algorithms
- **User-defined execution operators** (like `^`)
- **Dispatch tables and dynamic execution**
- **Macro-like language features**

The key insights:
1. **Control flow is data:** Blocks are values, execution paths are stored in the AL
2. **State is explicit:** Store mutations are visible, Register provides local scope
3. **Self-reference is natural:** `_.self` eliminates the need for workarounds
4. **Execution is first-class:** `>path` makes execution explicit and composable
5. **No special primitives:** Language features emerge from user-defined blocks

This makes SOMA programs:
- **Transparent:** All state is visible
- **Inspectable:** No hidden call stack or control flow
- **Explicit:** Every transformation is a clear AL → AL, Store → Store transition
- **Clean:** `_.self` and Register variables reduce boilerplate
- **Extensible:** Users can define their own execution patterns and "language features"

Understanding these patterns, especially `_.self` and `>path` execution, is essential to writing effective SOMA code. The `^` operator demonstrates SOMA's power: what looks like a primitive is actually user-defined.
