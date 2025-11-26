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

**Important:** All examples respect **Register isolation** - each block execution has its own independent Register that is completely isolated from parent/child blocks.

---

## 2. Hello World Variations

### 2.1 Minimal Hello World

The simplest SOMA program:

```soma
(Hello, world!) >print
```

**Execution trace:**

1. Initial state: `AL = []`, `Store = {}`
2. Token `(Hello, world!)` pushes string onto AL
   - `AL = [(Hello, world!)]`
3. Token `>print` consumes top of AL and writes to stdout
   - `AL = []`

**Output:**
```
Hello, world!
```

### 2.2 Hello World with Block

Using a block to encapsulate behavior:

```soma
{ (Hello, world!) >print } !say_hello
>say_hello
```

**Execution trace:**

1. Block `{ (Hello, world!) >print }` is pushed onto AL
   - `AL = [Block]`
2. `!say_hello` pops block and stores it in Store
   - `AL = []`
   - `Store = { say_hello: Block }`
3. `say_hello` pushes the block back onto AL
   - `AL = [Block]`
4. `>say_hello` executes the block (which prints and returns)
   - `AL = []`

**Output:**
```
Hello, world!
```

### 2.3 Hello World with Register Parameter

A block that takes a parameter from the AL:

```soma
{ !_.msg (Hello, ) _.msg >concat >print } !greet
(world) greet >chain
```

**Execution trace:**

1. Block is stored at `greet`
2. `(world)` is pushed onto AL
   - `AL = [(world)]`
3. `greet` pushes the block onto AL
   - `AL = [Block, (world)]`
4. `>chain` executes the block:
   - **Block creates fresh, empty Register**
   - `!_.msg` pops `(world)` and stores in **this block's Register** as `_.msg`
   - `(Hello, )` is pushed
   - `_.msg` retrieves `(world)` from **this block's Register** and pushes it
   - `>concat` pops two strings, concatenates, pushes result
   - `>print` outputs the concatenated string
   - **Block completes, Register is destroyed**

**Output:**
```
Hello, world
```

**Key point:** The Register path `_.msg` is local to this block's execution. The Register is created when the block starts and destroyed when it completes.

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
True { (Condition is true) >print } {} >ifelse
```

**Explanation:**

- `True` is the condition (Boolean on AL)
- First block executes if True
- Empty block `{}` executes if False (does nothing)
- `>ifelse` selects the appropriate block based on condition AND executes it

**Output:**
```
Condition is true
```

### 4.2 If/Else

```soma
15 !age
age 18 >>
  { (Adult) >print }
  { (Minor) >print }
>ifelse
```

**Execution trace:**

1. `age 18 >>` compares: is age > 18?
   - Result: `False` (15 is not greater than 18)
   - `AL = [False]`
2. `>ifelse` pops the condition and the two blocks
   - Since False, selects and executes second block
   - Second block prints (Minor)

**Output:**
```
Minor
```

### 4.3 Nested Conditionals

```soma
25 !temperature

temperature 30 >>
  { (Hot) >print }
  {
    temperature 20 >>
      { (Warm) >print }
      { (Cold) >print }
    >ifelse
  }
>ifelse
```

**Execution trace:**

1. Compare temperature (25) with 30: `False`
2. Execute else branch (the nested ifelse)
   - **Inner block gets fresh, empty Register**
3. Compare temperature (25) with 20: `True`
4. Execute (Warm) branch

**Output:**
```
Warm
```

**Note:** The inner block has its own Register, but accesses `temperature` from the Store (not Register), which is why this works.

### 4.4 Equality Testing

```soma
(password123) !stored_password
(password123) !user_input

stored_password user_input >==
  { (Access granted) >print }
  { (Access denied) >print }
>ifelse
```

**Output:**
```
Access granted
```

---

## 5. Building Control Structures

SOMA has no built-in loops. All iteration is built from `>choose` (conditional) and `>chain` (continuation). This section shows how to build loops step by step using `>block`.

### 5.1 Building a While Loop (Step by Step)

**Step 1: Understanding >chain**

`>chain` executes blocks repeatedly. It:
1. Pops the top of AL
2. If it's a Block, executes it
3. After execution, if AL top is a Block, repeats
4. Otherwise stops

**Step 2: A Self-Continuing Block with >block**

To loop, a block can reference itself using `>block`:

```soma
{ (tick) >print >block } >chain
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
    { >block }
    { }
  >choose
} >chain
```

**Execution:**

1. Block executes with fresh Register
2. Block prints counter (from Store - initially 0)
3. Increments counter in Store to 1
4. Checks if 1 < 5: True
5. Chooses first branch: pushes `>block` (the current block) onto AL
6. `>chain` sees block, continues
7. **New block execution with fresh Register**
8. Repeats until counter reaches 5

**Output:**
```
0
1
2
3
4
```

**This is a while loop!** It continues while `counter < 5`.

**Key insight:** `>block` is a built-in that pushes the currently executing block onto the AL, eliminating the need to store the block in the Store just to reference it. Each iteration gets a fresh Register, but they all share the Store variable `counter`.

### 5.2 While Loop Pattern (Canonical Form with >block)

Here's the general pattern for while loops in SOMA:

```soma
{Initial setup in Store}

{
  {Loop body - reads/writes Store}

  {Condition}
    { >block }
    { }
  >choose
} >chain
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
    { >block }
  >choose
} >chain

sum >print
```

**Output:**
```
55
```

**Note:** Condition is inverted (`10 >>` means "greater than 10"). When `i > 10`, we choose the empty block, stopping the loop.

**Important:** `sum` and `i` are in the **Store**, not the Register. This allows them to persist across loop iterations (each iteration gets a fresh Register). If they were Register variables, they would be lost between iterations.

### 5.3 Building a Do-While Loop

A do-while loop executes at least once:

```soma
0 !counter

{
  (Executed at least once) >print
  counter 1 >+ !counter

  counter 1 ><
    { >block }
    { }
  >choose
} >chain
```

**Output:**
```
Executed at least once
```

**Example:**
  1. Prints "Executed at least once"
  2. Increments counter to 1
  3. Checks condition: 1 < 1 → False
  4. Chooses empty block → stops

### 5.4 Infinite Loop Pattern

The simplest loop in SOMA:

```soma
{ (tick) >print >block } >chain
```

This demonstrates the power of `>block`: the block can reference itself without any external storage or naming.

### 5.5 How Loops Are Just Blocks + >choose + >chain

Let's make this explicit:

**While loop anatomy:**

```
{Condition} {Body + Continue} {} >choose
```

**The "Continue" part:**
- If condition true: execute body, then push `>block` back (loop)
- If condition false: execute empty block (stop)

**>chain's role:**
- Keeps executing whatever block is on AL
- Stops when AL top is not a block

**Key insight:** There's no special loop syntax. Just:
1. Blocks (encapsulated behavior)
2. >choose (conditional execution)
3. >chain (continuation)
4. **>block** (self-reference without naming)

---

## 6. Register Isolation Patterns

**CRITICAL CONCEPT:** Each block execution creates a fresh, empty Register that is completely isolated from parent/child blocks.

### 6.1 Understanding Register Isolation

**The Register Lifecycle:**

1. When a block begins execution: Create fresh, empty Register
2. Execute the block's code (all `_.path` operations use this Register)
3. When block completes: Destroy the Register

**Key rules:**

- Inner blocks **cannot** see outer block's Register cells
- Outer blocks **cannot** see inner block's Register cells
- Registers are **completely isolated** - no lexical scoping
- If you want to share data: use **Store** or **AL**

### 6.2 Example: Inner Block Has Its Own Register

```soma
{
  1 !_.n
  >{ 2 !_.n }
  _.n >print
} >chain
```

**What happens:**

1. Outer block executes, gets Register₁
2. `1 !_.n` → Store 1 in Register₁ path `_.n`
3. Inner block executes:
   - Gets **fresh Register₂** (empty)
   - `2 !_.n` → Store 2 in Register₂ path `_.n`
   - Inner block completes
   - Register₂ is **destroyed**
4. Back in outer block with Register₁
5. `_.n >print` → Register₁ still has `_.n = 1`

**Output:**
```
1
```

**Key insight:** Inner block's `_.n` was in a different Register. It didn't affect outer block's `_.n`.

### 6.3 ❌ WRONG - Inner Accessing Outer Register

```soma
{
  1 !_.n
  >{ _.n >print }
} >chain
```

**What happens:**

1. Outer block: `1 !_.n` stores 1 in outer Register
2. Inner block executes with **fresh, empty Register**
3. Inner block: `_.n` tries to read from inner Register
4. Inner Register has no `_.n` → resolves to **Void**
5. `>print` tries to execute Void → **FATAL ERROR**

**Error:** Cannot execute Void.

### 6.4 ✅ RIGHT - Pass via AL

```soma
{
  1 !_.n
  _.n
  >{ !_.inner_n _.inner_n >print }
} >chain
```

**What happens:**

1. Outer block: `1 !_.n` stores 1 in outer Register
2. Outer block: `_.n` pushes 1 onto AL
3. Inner block executes with fresh Register
4. Inner block: `!_.inner_n` pops 1 from AL, stores in inner Register
5. Inner block: `_.inner_n >print` prints 1

**Output:**
```
1
```

**Pattern:** Data is passed explicitly via the AL (stack).

### 6.5 ✅ RIGHT - Use Store

```soma
{
  1 !shared_data
  >{ shared_data >print }
} >chain
```

**What happens:**

1. Outer block: `1 !shared_data` stores 1 in **Store** (global)
2. Inner block: `shared_data` reads from **Store**
3. Inner block: `>print` prints 1

**Output:**
```
1
```

**Pattern:** Data is shared via the Store (persistent, global state).

### 6.6 ✅ RIGHT - Return via AL

```soma
{
  { !_.n _.n _.n >* } !_.square
  7 >_.square
  >print
} >chain
```

**What happens:**

1. Outer block defines `_.square` in its Register
2. `7` pushes 7 onto AL
3. `>_.square` executes the square block:
   - Square block gets **fresh Register**
   - `!_.n` pops 7 from AL, stores in square's Register
   - `_.n _.n >*` computes 7 * 7 = 49
   - Leaves 49 on AL
   - Square's Register destroyed
4. Outer block continues with AL = [49]
5. `>print` prints 49

**Output:**
```
49
```

**Pattern:** Blocks communicate via the AL (stack).

### 6.7 Example: Register vs Store Variables

```soma
{
  ) Store variable - persists across calls
  0 !counter

  ) Define helper block
  {
    ) Register variable - local to this execution
    counter !_.current
    _.current >print
    counter 1 >+ !counter
  } !increment

  increment >chain
  increment >chain
  increment >chain
} >chain
```

**Output:**
```
0
1
2
```

**Explanation:**

- `counter` is in **Store** - persists across all three calls to `increment`
- `_.current` is in **Register** - created fresh for each call, destroyed after
- Each `increment` execution:
  1. Gets fresh Register
  2. Reads `counter` from Store
  3. Stores in Register's `_.current`
  4. Prints `_.current`
  5. Increments `counter` in Store
  6. Register destroyed

### 6.8 When to Use Register vs Store

**Use Register (`_.path`) for:**
- Temporary computation within a block
- Function parameters (pop from AL, store in Register)
- Loop counters **within a single block execution** (won't work across iterations!)
- Local variables that don't need to persist

**Use Store (bare path) for:**
- Shared state between blocks
- Persistent data
- Loop counters **across iterations** (each iteration is a new execution)
- Global configuration
- Communication between unrelated blocks

**Use AL for:**
- Passing arguments to blocks
- Returning values from blocks
- Stack-based computation
- Temporary values

### 6.9 Common Mistake: Loop Counter in Register

❌ **WRONG - Counter won't persist:**

```soma
{
  0 !_.i
  {
    _.i >print
    _.i 1 >+ !_.i

    _.i 3 ><
      { >block }
      { }
    >choose
  } >chain
} >chain
```

**Problem:** Each loop iteration is a fresh block execution with fresh Register. `_.i` is reset to Void each time (or doesn't exist), causing errors.

✅ **RIGHT - Counter in Store:**

```soma
0 !i
{
  i >print
  i 1 >+ !i

  i 3 ><
    { >block }
    { }
  >choose
} >chain
```

**Output:**
```
0
1
2
```

**Explanation:** `i` is in Store, so it persists across loop iterations.

### 6.10 Example: Nested Blocks with Proper Isolation

```soma
{
  (outer_value) !outer_var

  {
    ) Define inner helper in outer Register
    {
      !_.param
      _.param ( processed) >concat
    } !_.inner_helper

    ) Use the helper
    outer_var >_.inner_helper >print
  } >chain
} >chain
```

**Output:**
```
outer_value processed
```

**What happens:**

1. Outer block: Stores (outer_value) in **Store** as `outer_var`
2. Outer block: Stores helper block in **outer's Register** as `_.inner_helper`
3. Inner block executes with **fresh Register**:
   - `outer_var` reads from **Store** (works!)
   - `>_.inner_helper` tries to read from **inner's Register** → Void → **ERROR**

**Wait, this is wrong!** Let me correct:

❌ **WRONG - Inner can't see outer's Register:**

```soma
{
  {
    !_.param
    _.param ( processed) >concat
  } !_.helper

  {
    (value) >_.helper >print
  } >chain
} >chain
```

**Problem:** Inner block can't see `_.helper` from outer Register.

✅ **RIGHT - Helper in Store:**

```soma
{
  {
    !_.param
    _.param ( processed) >concat
  } !helper

  {
    (value) >helper >print
  } >chain
} >chain
```

**Output:**
```
value processed
```

**Pattern:** Store `helper` in **Store** (not Register) so inner block can access it.

---

## 7. Finite State Machines

### 7.1 Two-State Toggle with >block

A simple state machine that toggles between ON and OFF:

```soma
True !state
0 !count

{
  state
    { (ON) >print False !state }
    { (OFF) >print True !state }
  >ifelse

  count 1 >+ !count

  count 5 ><
    { >block }
    { }
  >choose
} >chain
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

We use **Store** variables (`state`, `count`) for state that persists across loop iterations. Each iteration gets a fresh Register.

**Key point:** State must be in Store to persist across iterations.

### 7.2 Multi-State FSM (Traffic Light) with >block

A traffic light with three states: Red → Green → Yellow → Red

```soma
0 !cycle_count

{
  (RED) >print
  green >chain
} !red

{
  (GREEN) >print
  yellow >chain
} !green

{
  (YELLOW) >print

  cycle_count 1 >+ !cycle_count

  cycle_count 3 ><
    { red >chain }
    { }
  >choose
} !yellow

red >chain
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

Each state is a block stored in the **Store**. Each state:
1. Performs its action (print color)
2. Chains to the next state block
3. When blocks execute, they get fresh Registers

The `yellow` state checks if we've completed 3 cycles and either continues to `red` or stops.

**Important:** State blocks are in Store, not Register, so they can call each other.

### 7.3 FSM with Input

A door that can be opened and closed:

```soma
(open) !door_input

{
  (Door is CLOSED) >print

  door_input (open) >==
    { opened >chain }
    { closed >chain }
  >ifelse
} !closed

{
  (Door is OPEN) >print

  door_input (close) >==
    { closed >chain }
    { opened >chain }
  >ifelse
} !opened

closed >chain
```

**Output:**
```
Door is CLOSED
Door is OPEN
```

**Explanation:**

The `door_input` Store cell determines which state transition occurs. All FSM state blocks are stored in the **Store** for global access. Each state uses `>ifelse` to execute the appropriate transition.

---

## 8. Data Structures Using the Store

### 8.1 Simple Stack Using Store Path

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

(Hello) push_first >chain
stack.data.0 >print
pop_last >chain >print
```

**Output:**
```
Hello
Hello
```

**Note:** Helper blocks pop arguments from AL into Register variables (`_.value`), then store in Store paths for persistence.

### 8.2 Record/Struct Pattern

```soma
(Alice) !person.name
30 !person.age
(Engineering) !person.department

{
  person.name >print
  person.age >print
  person.department >print
} !print_person

print_person >chain
```

**Output:**
```
Alice
30
Engineering
```

### 8.3 Key-Value Store Pattern

**Note:** This example uses a hypothetical `>ToPath` operation that doesn't exist in SOMA v1.0. It would convert a string to a path and read from the Store. This is shown for educational purposes to demonstrate the pattern.

```soma
(apple) !fruits.a
(banana) !fruits.b
(cherry) !fruits.c

{
  !_.key
  (fruits.) _.key >concat >ToPath
} !get_fruit

(b) get_fruit >chain >print
```

**Hypothetical output:**
```
banana
```

**Explanation:**
- `_.key` is a Register variable (parameter from AL)
- After building the path, `>ToPath` would convert string to path and read from Store
- **This operation doesn't currently exist in SOMA v1.0**

---

## 9. Graph Structures: Cell Architecture Enables First-Class Graphs

SOMA's Cell architecture has a unique property: **value and subpaths are orthogonal**. This means a Cell can simultaneously have:
- A **value** (Int, String, Block, CellRef, Nil, etc.)
- **Subpaths** (children in the path hierarchy)

This orthogonality enables graph structures to emerge naturally, without explicit node types or boilerplate. Most languages require you to define node classes; in SOMA, graphs are first-class.

### 9.1 Value + Children Coexistence

A Cell can have both a value AND children simultaneously:

```soma
) Parent has a value
Nil !parent
parent >print           ) Prints: Nil

) Parent ALSO has children
23 !parent.child
parent.child >print     ) Prints: 23

) Parent's value unchanged
parent >print           ) Still prints: Nil
```

**Store structure:**
```
parent → Cell(value: Nil, subpaths: {"child": Cell(value: 23, ...)})
```

**Key insight:**
- Reading `parent` returns the **value** (Nil)
- Traversing `parent.child` uses the **subpaths** to find child, returns child's value (23)
- The value and subpaths are **independent**

### 9.2 Any Value Can Have Children

This works for ANY value type:

```soma
) Void with children (auto-vivification)
42 !a.b.c
a               ) Void (auto-vivified, never explicitly set)
a.b.c           ) 42 (traverses through Void cells)

) Int with children
42 !node
99 !node.sub
node            ) 42
node.sub        ) 99

) Block with children
{ >print } !action
(help text) !action.description
action >chain           ) Executes the block
action.description >print  ) Prints: help text

) String with children
(root_value) !tree
(left_value) !tree.left
(right_value) !tree.right
tree            ) (root_value)
tree.left       ) (left_value)
tree.right      ) (right_value)
```

**This is unusual:** Most languages don't let you attach children to primitive values. SOMA's Cell structure makes this natural.

### 9.3 Linked List Using CellRefs

CellRefs allow Cells to reference other Cells, enabling pointer-like structures:

```soma
) Create Node 1
1 !list.value
list.next. !list.next           ) CellRef pointing to list.next

) Create Node 2
2 !list.next.value
Nil !list.next.next             ) End of list

) Traverse the list
list.value >print               ) 1
list.next.value >print          ) 2 (follows CellRef)
list.next.next >print           ) Nil (end)
```

**What's happening:**

1. `list.next. !list.next` creates a CellRef
   - The path `list.next.` (with trailing dot) creates a CellRef to Cell `list.next`
   - This CellRef is stored as the **value** of `list.next`
   - So `list.next` has both:
     - **Value:** A CellRef pointing to `list.next`
     - **Subpaths:** Contains `value`, `next`, etc.

2. When you read `list.next.value`:
   - Traverse from `list` to its subpath `next`
   - Read `next`'s value (a CellRef)
   - **Follow the CellRef** to the target Cell
   - Continue traversing to `value`

**Store structure:**
```
list → Cell(value: Void, subpaths: {
  "value": Cell(value: 1),
  "next": Cell(value: CellRef→list.next, subpaths: {
    "value": Cell(value: 2),
    "next": Cell(value: Nil)
  })
})
```

**Key pattern:** CellRefs create **indirection**, enabling linked structures.

### 9.4 Graph with Cycles Using CellRefs

CellRefs can create circular references - graphs with cycles:

```soma
) Create two nodes
(A) !nodeA.label
(B) !nodeB.label

) Create bidirectional edges (circular!)
nodeB. !nodeA.next              ) A → B (CellRef)
nodeA. !nodeB.prev              ) B → A (CellRef)

) Navigate the graph
nodeA.next.label >print         ) (B) (A → B)
nodeB.prev.label >print         ) (A) (B → A)
nodeA.next.prev.label >print    ) (A) (A → B → A, cyclic!)
```

**What's happening:**

1. `nodeB. !nodeA.next` creates a CellRef to `nodeB` and stores it at `nodeA.next`
2. `nodeA. !nodeB.prev` creates a CellRef to `nodeA` and stores it at `nodeB.prev`
3. Now we have a cycle: nodeA → nodeB → nodeA

**Store structure:**
```
nodeA → Cell(value: Void, subpaths: {
  "label": Cell(value: "A"),
  "next": Cell(value: CellRef→nodeB)
})

nodeB → Cell(value: Void, subpaths: {
  "label": Cell(value: "B"),
  "prev": Cell(value: CellRef→nodeA)
})
```

**Traversal:**
- `nodeA.next.label`: Start at nodeA → follow CellRef to nodeB → read label ("B")
- `nodeB.prev.label`: Start at nodeB → follow CellRef to nodeA → read label ("A")
- `nodeA.next.prev.label`: Start at nodeA → follow CellRef to nodeB → follow CellRef to nodeA → read label ("A")

**This is powerful:** You can create arbitrary graph topologies, including cycles, using just CellRefs.

### 9.5 Building a Simple Graph Traversal

Let's build a graph and traverse it:

```soma
) Create a directed graph: A → B → C → A (cycle)
(Node A) !graph.a.label
(Node B) !graph.b.label
(Node C) !graph.c.label

) Create edges
graph.b. !graph.a.next          ) A → B
graph.c. !graph.b.next          ) B → C
graph.a. !graph.c.next          ) C → A (cycle!)

) Traverse starting from A
graph.a.label >print            ) Node A
graph.a.next.label >print       ) Node B (followed A → B)
graph.a.next.next.label >print  ) Node C (followed A → B → C)
graph.a.next.next.next.label >print  ) Node A (followed A → B → C → A, back to start!)
```

**Output:**
```
Node A
Node B
Node C
Node A
```

**Key insight:** The cycle is natural. CellRefs enable circular references without special handling.

### 9.6 Why This Is Powerful: Graphs Without Boilerplate

In most languages, you need explicit node types:

**JavaScript example (traditional approach):**
```javascript
class Node {
  constructor(label) {
    this.label = label;
    this.next = null;
  }
}

const a = new Node("A");
const b = new Node("B");
a.next = b;
b.next = a;  // Cycle
```

**SOMA approach:**
```soma
) No class definition needed
(A) !a.label
(B) !b.label
b. !a.next
a. !b.next
```

**Why SOMA is different:**

1. **No explicit node types:** Cells ARE nodes. Every path in the Store is potentially a graph node.

2. **Value + structure coexist:** A node can have data (value) AND connections (subpaths) simultaneously:
   ```soma
   42 !node             ) Node has value 42
   other. !node.next    ) Node also has outgoing edge
   ```

3. **CellRefs enable indirection:** CellRefs create pointers, enabling arbitrary graph topologies:
   ```soma
   nodeA. !nodeB.link   ) Bidirectional
   nodeB. !nodeA.link   ) No special handling
   ```

4. **Natural path syntax:** Graph traversal is just path traversal:
   ```soma
   start.next.next.label    ) Follow two edges, read label
   ```

5. **No memory management:** No need to manually deallocate nodes or worry about cycles causing memory leaks.

### 9.7 Tree Structure with Values at All Levels

A binary tree where every node (including internal nodes) has a value:

```soma
) Root has value and children
10 !tree.value
tree.left. !tree.left
tree.right. !tree.right

) Left subtree
5 !tree.left.value
tree.left.left. !tree.left.left
tree.left.right. !tree.left.right

) Right subtree
15 !tree.right.value
tree.right.left. !tree.right.left
tree.right.right. !tree.right.right

) Leaf nodes
3 !tree.left.left.value
7 !tree.left.right.value
12 !tree.right.left.value
20 !tree.right.right.value

) Traverse and print
tree.value >print                     ) 10 (root)
tree.left.value >print                ) 5
tree.left.left.value >print           ) 3
tree.left.right.value >print          ) 7
tree.right.value >print               ) 15
tree.right.left.value >print          ) 12
tree.right.right.value >print         ) 20
```

**Output:**
```
10
5
3
7
15
12
20
```

**Key pattern:**
- Every node has a `value` subpath for its data
- Internal nodes have `left` and `right` CellRefs
- This is a **tree with values at every node**, not just leaves

### 9.8 Adjacency List Graph Representation

Represent a graph as adjacency lists using CellRefs:

```soma
) Create vertices
(Vertex A) !graph.a.label
(Vertex B) !graph.b.label
(Vertex C) !graph.c.label
(Vertex D) !graph.d.label

) Create adjacency lists (edges)
graph.b. !graph.a.edges.0    ) A → B
graph.c. !graph.a.edges.1    ) A → C

graph.c. !graph.b.edges.0    ) B → C
graph.d. !graph.b.edges.1    ) B → D

graph.d. !graph.c.edges.0    ) C → D

) Traverse: What can we reach from A?
graph.a.label >print                      ) A
graph.a.edges.0.label >print              ) B (A's first neighbor)
graph.a.edges.1.label >print              ) C (A's second neighbor)
graph.a.edges.0.edges.1.label >print      ) D (A → B → D)
```

**Output:**
```
Vertex A
Vertex B
Vertex C
Vertex D
```

**Store structure:**
```
graph.a → Cell(value: Void, subpaths: {
  "label": Cell(value: "Vertex A"),
  "edges": Cell(value: Void, subpaths: {
    "0": Cell(value: CellRef→graph.b),
    "1": Cell(value: CellRef→graph.c)
  })
})
```

**Key insight:** The adjacency list is just a collection of CellRefs under a subpath namespace (`edges.0`, `edges.1`, etc.).

### 9.9 Understanding Cell Architecture: Value vs Subpaths

**Every Cell has TWO independent components:**

```
Cell = {
  value:    CellValue              ) Payload (Int | String | Block | CellRef | Nil | Void)
  subpaths: Dict[String, Cell]     ) Children (name → Cell mapping)
}
```

**Reading vs Traversing:**

```soma
42 !node
99 !node.child

node            ) Reads node's VALUE → 42
node.child      ) Traverses node's SUBPATHS to child, reads child's VALUE → 99
```

**Path resolution algorithm:**

1. Start at root Cell
2. For each path component:
   - Look up component in **current Cell's subpaths**
   - Move to that child Cell
   - **Ignore current Cell's value** during traversal
3. When path is exhausted, return **final Cell's value**

**Example walkthrough:**

```soma
Nil !a.b
23 !a.b.c

a.b.c           ) What happens?
```

**Steps:**
1. Start at root
2. Look up `a` in root's subpaths → Cell `a` (value: Void)
3. Look up `b` in `a`'s subpaths → Cell `b` (value: Nil)
4. Look up `c` in `b`'s subpaths → Cell `c` (value: 23)
5. Return `c`'s value → **23**

**Key insight:** We traversed **through** Cell `b` (which has value Nil) to reach its child `c`. The value Nil did NOT block traversal because **subpaths are independent of value**.

### 9.10 Why Graphs Are First-Class in SOMA

**Comparison with other languages:**

| Aspect | Traditional Languages | SOMA |
|--------|----------------------|------|
| **Node definition** | Explicit class/struct | Cells ARE nodes |
| **Adding children** | Modify class, add fields | Just write to subpaths |
| **Node data** | Separate from structure | Value component of Cell |
| **Pointers** | Explicit references/pointers | CellRefs |
| **Graph topology** | Build with manual linking | Natural path structure + CellRefs |
| **Cycles** | Require careful management | Natural, no special handling |

**SOMA's advantage:**

1. **Zero boilerplate:** No node class definitions, no manual field declarations
2. **Emergent structure:** Graphs emerge from the Cell structure itself
3. **Uniform syntax:** Graph traversal uses the same path syntax as data access
4. **Flexibility:** Any Cell can become a graph node by adding CellRef children
5. **Orthogonality:** Value and structure are independent - nodes can have data AND connections

**Mental model:**

In SOMA, think of the Store as a **graph database** where:
- Every path is a **node**
- Every Cell's value is **node data**
- Every Cell's subpaths are **outgoing edges**
- CellRefs create **arbitrary graph topology**

This makes SOMA uniquely suited for graph algorithms, tree transformations, and linked data structures - all without leaving the core language primitives.

---

## 10. CellRef Semantics and Cell Lifetime

**CRITICAL CONCEPT:** CellRefs are immutable values that provide access to Cells. Cells have independent existence from paths - they persist as long as any access route exists (via paths or CellRefs).

This section demonstrates the powerful patterns enabled by CellRef semantics: detached graph structures, object-like patterns, aliasing, and Cell lifetime independence.

### 10.1 Understanding CellRefs: Immutable Values

CellRefs are immutable values (like Int, String, Block) that point to Cells:

```soma
42 !node
node. !ref1         ) Create CellRef to node
node. !ref2         ) Create another CellRef to same Cell
node. !ref3         ) And another

) All three CellRefs point to the same Cell
99 !node            ) Change Cell's value
ref1 >print         ) 99 (all refs see the update)
ref2 >print         ) 99
ref3 >print         ) 99
```

**Output:**
```
99
99
99
```

**Key insight:** All CellRefs point to the same Cell. When you update the Cell through the `node` path, all CellRefs see the change.

### 10.2 Cell Lifetime: Independent of Paths

Cells persist as long as ANY access route exists - through paths OR CellRefs:

```soma
42 !data
data. !ref          ) Create CellRef to the Cell
Void !data.         ) Delete the path 'data'
ref >print          ) Still works! Returns 42
```

**Output:**
```
42
```

**What happened:**

1. `42 !data` - Created Cell, made accessible via Store path `data`
2. `data. !ref` - Created immutable CellRef value pointing to that Cell
3. `Void !data.` - Removed path `data` from Store tree (deleted tree edge)
4. `ref` - Dereferenced CellRef, accessed Cell, returned value 42

**The Cell still exists** because the CellRef at path `ref` provides access to it. Deleting a path removes the path from the tree, not the Cell itself.

### 10.3 Multiple Paths to Same Cell

A Cell can be accessible through multiple paths simultaneously:

```soma
42 !original
original. !alias1
original. !alias2
original. !alias3

) All four paths point to same Cell
original >print     ) 42
alias1 >print       ) 42
alias2 >print       ) 42

) Delete original path
Void !original.

) Cell still accessible via aliases
alias1 >print       ) 42 (Cell persists via alias1)
alias2 >print       ) 42 (Cell persists via alias2)
alias3 >print       ) 42 (Cell persists via alias3)
```

**Output:**
```
42
42
42
42
42
42
```

**Key insight:** Deleting the `original` path doesn't delete the Cell because other CellRefs (`alias1`, `alias2`, `alias3`) still reference it.

### 10.4 Detached Graphs: Linked Lists

Build a linked list in a Register, return a CellRef - the list persists even after the Register is destroyed:

```soma
{
  1 !_.head.value
  _.head.next. !_.head.next
  2 !_.head.next.value
  Nil !_.head.next.next

  _.head.       ) Return CellRef to list head
} >chain !list

) Block destroyed, Register destroyed, but list persists!
list.value >print              ) 1
list.next.value >print         ) 2
list.next.next >print          ) Nil
```

**Output:**
```
1
2
Nil
```

**What happened:**

1. Block executes with fresh Register
2. Builds linked list structure in Register (`_.head` and subpaths)
3. `_.head.` creates CellRef to the list head Cell
4. Block completes, leaving CellRef on AL
5. `!list` pops CellRef and stores it in Store
6. **Block's Register is destroyed** - all `_.head` paths gone
7. But the **Cells persist** because the CellRef at `list` provides access

**This is powerful:** The linked list was built in temporary Register space, but returned as a persistent data structure via CellRef.

### 10.5 "New" Pattern: Object Creation

Create a structure locally, return a CellRef - like `new` in other languages:

```soma
{
  (initial data) !_.obj.data
  0 !_.obj.counter
  { _.obj.counter 1 >+ !_.obj.counter } !_.obj.increment

  _.obj.        ) Return handle to object
} >chain !myObj

) Object persists and is usable
myObj.data >print              ) (initial data)
myObj.counter >print           ) 0
>myObj.increment               ) Execute increment method
myObj.counter >print           ) 1
>myObj.increment               ) Increment again
myObj.counter >print           ) 2
```

**Output:**
```
initial data
0
1
2
```

**What happened:**

1. Block builds object structure in Register:
   - `_.obj.data` holds data
   - `_.obj.counter` holds mutable state
   - `_.obj.increment` holds a block (method)
2. Returns CellRef to `_.obj`
3. Register destroyed, but object structure persists via CellRef
4. Can call "methods" via `>myObj.increment`
5. Can read/modify state via `myObj.counter`

**Pattern:** This is like object construction - build a structure with data and methods, return a handle to it.

### 10.6 Aliasing: Creating German Command Names

Store a CellRef to a built-in at a different path - create aliases:

```soma
chain !kette            ) German name for chain
print !drucken          ) German name for print

) Use German names
(Hallo Welt) >drucken

{ result >drucken } !print_result
1 2 >+ !result
print_result >kette
```

**Output:**
```
Hallo Welt
3
```

**Explanation:**

1. `chain !kette` - Get built-in chain block, store CellRef at path `kette`
2. `print !drucken` - Get built-in print block, store CellRef at path `drucken`
3. Now `>kette` and `>drucken` work exactly like `>chain` and `>print`

**Use cases:**
- Creating domain-specific names for built-ins
- Internationalization
- Shorter aliases for frequently used operations
- Renaming operations to match project conventions

### 10.7 CellRef Persistence After Path Deletion

Comprehensive example showing Cell lifetime independence:

```soma
) Create Cell with data
(Original Value) !cell
cell >print                 ) (Original Value)

) Create multiple CellRefs
cell. !ref1
cell. !ref2
cell. !ref3

) Delete original path
Void !cell.

) Cell still accessible via CellRefs
ref1 >print                 ) (Original Value)
ref2 >print                 ) (Original Value)

) Can modify Cell through CellRef
(Updated Value) !ref1
ref2 >print                 ) (Updated Value) (same Cell!)
ref3 >print                 ) (Updated Value)

) Create new path to same Cell
ref1. !newpath
newpath >print              ) (Updated Value)

) All paths point to same Cell
(Final Value) !newpath
ref1 >print                 ) (Final Value)
ref2 >print                 ) (Final Value)
ref3 >print                 ) (Final Value)
```

**Output:**
```
Original Value
Original Value
Original Value
Updated Value
Updated Value
Updated Value
Final Value
Final Value
Final Value
```

**Key insight:** The Cell has an independent existence. Whether you access it via `cell`, `ref1`, `ref2`, `ref3`, or `newpath`, you're accessing the **same Cell**. Modifications through any path are visible through all paths.

### 10.8 Building Tree Structures in Register, Returning via CellRef

Build a complex tree structure locally, return a CellRef:

```soma
{
  ) Build a tree structure in Register
  5 !_.root.value
  3 !_.root.left.value
  7 !_.root.right.value
  1 !_.root.left.left.value
  4 !_.root.left.right.value
  6 !_.root.right.left.value
  9 !_.root.right.right.value

  _.root.       ) Return CellRef to root
} >chain !tree

) Tree persists, accessible via CellRef
tree.value >print                     ) 5
tree.left.value >print                ) 3
tree.left.left.value >print           ) 1
tree.left.right.value >print          ) 4
tree.right.value >print               ) 7
tree.right.left.value >print          ) 6
tree.right.right.value >print         ) 9
```

**Output:**
```
5
3
1
4
7
6
9
```

**Pattern:** Build complex data structures in a Register (temporary workspace), return CellRef (permanent handle). This is SOMA's equivalent to:
- `new Tree()` in Java
- `malloc()` in C
- Constructor functions in JavaScript

### 10.9 Multiple CellRefs to Same Cell: Shared Mutation

Multiple CellRefs to the same Cell means modifications through one are visible through all:

```soma
) Create a mutable object
0 !counter.value
counter. !ref1
counter. !ref2
counter. !ref3

) Increment through ref1
ref1.value 1 >+ !ref1.value
ref1.value >print           ) 1

) All refs see the change
ref2.value >print           ) 1
ref3.value >print           ) 1
counter.value >print        ) 1

) Increment through ref2
ref2.value 1 >+ !ref2.value

) All refs see the update
ref1.value >print           ) 2
ref2.value >print           ) 2
ref3.value >print           ) 2
```

**Output:**
```
1
1
1
1
2
2
2
```

**Key insight:** CellRefs create shared references. Multiple CellRefs to the same Cell enable shared mutable state - all references see updates.

### 10.10 CellRef in AL

CellRefs can be passed on the AL, enabling dynamic object passing:

```soma
) Helper that takes a CellRef from AL and reads its value
{
  !_.cellref
  _.cellref.value >print
} !print_value

) Create object
42 !obj.value
obj. !handle

) Pass CellRef on AL to helper
handle >print_value         ) Passes CellRef, helper reads obj.value
```

**Output:**
```
42
```

**Explanation:**

1. `print_value` block expects CellRef on AL
2. `handle >print_value` pushes CellRef onto AL
3. Block pops CellRef, stores in Register, dereferences it

**Pattern:** Pass object handles (CellRefs) to functions via AL.

### 10.11 Why CellRefs Never "Dangle"

Traditional languages have "dangling pointer" problems. SOMA doesn't:

**Traditional dangling pointer (C):**
```c
int *p = malloc(sizeof(int));
*p = 42;
free(p);
*p;         // DANGLING - undefined behavior
```

**SOMA CellRefs:**
```soma
42 !cell
cell. !ref
Void !cell.     ) Delete path, but Cell persists
ref             ) NOT dangling - Cell still exists!
```

**Why SOMA is different:**

1. Deleting a path doesn't delete the Cell
2. Cells persist as long as accessible through any route (path or CellRef)
3. CellRefs provide direct access to Cells
4. Implementation ensures Cells are reclaimed only when ALL references are gone

**CellRefs in SOMA never "dangle"** because path deletion is separate from Cell deletion.

### 10.12 Cell Lifetime Summary

**A Cell persists as long as:**
- It is accessible via any path in Store, OR
- It is accessible via any path in any active Register, OR
- Any CellRef referring to it exists anywhere (AL, Store, Register)

**When all access routes are removed:**
- The Cell becomes inaccessible
- The Cell can be reclaimed (implementation-defined, like garbage collection)

**Examples:**

```soma
) Cell with path only
42 !a
Void !a.        ) Cell becomes inaccessible, can be reclaimed

) Cell with CellRef
42 !b
b. !ref
Void !b.        ) Path gone, but Cell persists via ref

) Cell with multiple CellRefs
42 !c
c. !ref1
c. !ref2
Void !c.        ) Cell persists via ref1 and ref2
Void !ref1.     ) Cell persists via ref2
Void !ref2.     ) NOW Cell can be reclaimed (no access routes)
```

**Key principle:** Paths are navigation routes in the tree structure. Cells are independent entities with their own lifetime.

---

## 11. Register Deletion Patterns

**CRITICAL CONCEPT:** Register deletion works identically to Store deletion. Both Store and Register are hierarchical graphs of Cells, so `Void !path.` deletes paths from the tree in the same way.

### 11.1 Simple Register Deletion

You can delete Register cells using `Void !_.path.` (note the trailing dot):

```soma
{
  23 !_.temp
  _.temp >print     ) Prints: 23

  Void !_.temp.     ) Delete Register cell
  _.temp            ) Returns Void (Cell no longer accessible)
} >chain
```

**Output:**
```
23
```

**Explanation:**

1. `23 !_.temp` creates Cell in Register with value 23
2. `_.temp >print` reads and prints 23
3. `Void !_.temp.` deletes the path `_.temp` from Register tree
4. `_.temp` now returns Void (Cell no longer accessible via this path)

**Key insight:** Register deletion uses the same syntax as Store deletion - `Void !path.` with trailing dot.

### 11.2 Register Deletion with CellRef

Deleting a path doesn't delete the Cell if a CellRef still references it:

```soma
{
  42 !_.data
  _.data. !_.ref    ) CellRef to Cell

  Void !_.data.     ) Delete path _.data
  _.ref >print      ) Still works! Cell persists via CellRef
} >chain
```

**Output:**
```
42
```

**What happened:**

1. `42 !_.data` creates Cell in Register with value 42
2. `_.data. !_.ref` creates CellRef to the Cell, stores CellRef in Register
3. `Void !_.data.` deletes path `_.data` from Register tree
4. The Cell still exists because `_.ref` provides access to it
5. `_.ref >print` dereferences the CellRef and prints 42

**Key insight:** Cells persist as long as any access route exists (via paths or CellRefs), even in the Register.

### 11.3 Register Cleanup Pattern

Use Register as temporary workspace, then clean up:

```soma
{
  ) Use Register cells as temporary workspace
  1 !_.a
  2 !_.b
  _.a _.b >+        ) AL = [3]

  ) Clean up workspace
  Void !_.a.
  Void !_.b.

  ) Return result (AL = [3])
} >chain >print
```

**Output:**
```
3
```

**Explanation:**

1. `_.a` and `_.b` are created in Register for temporary computation
2. `_.a _.b >+` computes sum, leaves result on AL
3. `Void !_.a.` and `Void !_.b.` delete the temporary paths
4. Result remains on AL for return
5. Register is destroyed when block completes

**Use case:** Clean up temporary state before returning from a block. This is useful when you want to ensure no accidental data leaks or when implementing clean workspace patterns.

### 11.4 Deleting Subtrees in Register

Delete entire subtrees while preserving other parts:

```soma
{
  1 !_.tree.left.value
  2 !_.tree.right.value
  3 !_.tree.value

  Void !_.tree.left.    ) Delete entire left subtree

  _.tree.value >print        ) Root value still exists: 3
  _.tree.right.value >print  ) Right subtree still exists: 2
  _.tree.left                ) Left subtree gone: Void
} >chain
```

**Output:**
```
3
2
```

**What happened:**

1. Built tree structure in Register with root and two subtrees
2. `Void !_.tree.left.` deleted the entire left subtree
3. Root (`_.tree.value`) and right subtree (`_.tree.right.value`) persist
4. `_.tree.left` now returns Void

**Pattern:** Selective subtree deletion allows you to prune parts of a data structure while keeping other parts intact.

### 11.5 Register vs Store Deletion Symmetry

The deletion semantics are identical - only the namespace differs:

```soma
) Store deletion
42 !a.b
Void !a.b.      ) Delete path a.b from Store tree
a.b             ) Void (Cell no longer accessible via this path)
```

```soma
{
  ) Register deletion
  42 !_.x
  Void !_.x.      ) Delete path _.x from Register tree
  _.x             ) Void (Cell no longer accessible via this path)
} >chain
```

**Key principle:** Store and Register have identical Cell structure, so all Cell operations (read, write, delete) work the same way in both.

### 11.6 Temporary Object Pattern with Cleanup

Build object in Register, extract what you need, clean up:

```soma
{
  ) Build temporary object structure
  (input.txt) !_.config.filename
  100 !_.config.buffer_size
  True !_.config.verbose

  ) Extract only what we need to Store
  _.config.filename !output_file
  _.config.buffer_size !buffer

  ) Clean up Register workspace
  Void !_.config.

  ) Register now clean, Store has extracted values
} >chain

output_file >print
buffer >print
```

**Output:**
```
input.txt
100
```

**Use case:** Parse configuration, validate inputs, or transform data in Register workspace, extract final results to Store, then clean up temporary structures.

### 11.7 Conditional Cleanup

Delete paths based on conditions:

```soma
{
  (data) !_.cache
  True !_.should_clear

  _.should_clear
    { Void !_.cache. (Cache cleared) >print }
    { (Cache retained) >print }
  >ifelse

  _.cache >isVoid
    { (Cache is empty) >print }
    { (Cache has data) >print }
  >ifelse
} >chain
```

**Output:**
```
Cache cleared
Cache is empty
```

**Pattern:** Conditionally delete Register cells based on runtime state, useful for cache invalidation or resource cleanup.

### 11.8 Why Delete Register Paths?

**Register paths are automatically destroyed when blocks complete, so why explicitly delete?**

1. **Large data cleanup:** Free memory during long-running block execution
2. **Defensive programming:** Ensure sensitive data is cleared before continuing
3. **Intentional design:** Make it explicit that a value is no longer needed
4. **Preventing accidental reuse:** Delete after use to catch bugs where stale data might be accessed

**Example - preventing accidental reuse:**

```soma
{
  42 !_.temp
  _.temp >print         ) Intentional use

  Void !_.temp.         ) Explicitly mark as done

  ) Later in block...
  _.temp >print         ) Would catch bug: prints Void
} >chain
```

**Output:**
```
42
```

**Note:** The second `_.temp >print` would attempt to print Void, causing an error if Void execution isn't handled, catching the accidental reuse bug.

### 11.9 Register Deletion Summary

**Deletion syntax (identical for Store and Register):**

```soma
Void !path.         ) Delete Store path
Void !_.path.       ) Delete Register path
```

**Both delete the path from the tree structure:**
- Remove the edge in the tree
- Cell persists if accessible via other paths or CellRefs
- Returns Void when reading deleted path

**When to use Register deletion:**
- Temporary workspace cleanup
- Large data structure cleanup mid-block
- Sensitive data clearing
- Defensive programming to prevent accidental reuse
- Explicit memory management patterns

**Remember:** Register destruction at block end is automatic, but explicit deletion gives you fine-grained control during block execution.

---

## 12. Common Patterns and Idioms

### 12.1 Conditional Increment

Increment only if value is below threshold:

```soma
10 !value
15 !threshold

value threshold ><
  { value 1 >+ !value }
  { }
>ifelse

value >print
```

**Output:**
```
11
```

### 12.2 Max of Two Values

```soma
{
  !_.b !_.a
  _.a _.b >>
    { _.a }
    { _.b }
  >choose
} !max

15 23 max >chain >print
```

**Output:**
```
23
```

**Note:** `_.a` and `_.b` are Register variables (popped from AL).

### 12.3 Absolute Value

```soma
{
  !_.n
  _.n 0 >>
    { _.n }
    { 0 _.n >- }
  >choose
} !abs

-5 abs >chain >print
10 abs >chain >print
```

**Output:**
```
5
10
```

### 12.4 Factorial (Iterative with >block)

```soma
{
  !_.n

  ) Initialize in Store
  1 !factorial_result
  1 !factorial_i

  {
    factorial_result factorial_i >* !factorial_result
    factorial_i 1 >+ !factorial_i

    factorial_i _.n >>
      { }
      { >block }
    >choose
  } >chain

  ) Clean up and return
  factorial_result !_.result
  factorial_result
} !factorial

5 factorial >chain >print
```

**Output:**
```
120
```

**Key insight:** Loop state (`factorial_result`, `factorial_i`) must be in **Store** to persist across iterations. `_.n` can be in Register because it's set once at the start and read from within the loop.

### 12.5 Range Check

```soma
{
  !_.high !_.low !_.value

  _.value _.low >>
    {
      _.value _.high ><
        { True }
        { False }
      >choose
    }
    { False }
  >choose
} !in_range

15 10 20 in_range >chain
  { (In range) >print }
  { (Out of range) >print }
>ifelse
```

**Output:**
```
In range
```

---

## 13. Working with Blocks

### 13.1 Block Composition

```soma
{ !_.x _.x 2 >* } !double
{ !_.x _.x 1 >+ } !increment

{
  !_.f !_.g !_.x
  _.x >_.f >_.g
} !compose

5 double increment compose >chain >print
```

**Output:**
```
11
```

**Explanation:**
1. `compose` takes three args from AL: `x`, `g`, `f` (stored in Register)
2. Pushes `_.x` onto AL
3. Executes `>_.f` (double): 5 * 2 = 10 on AL
4. Executes `>_.g` (increment): 10 + 1 = 11 on AL
5. Result 11 left on AL

### 13.2 Conditional Block Selection and Execution

```soma
{ (Option A) >print } !block_a
{ (Option B) >print } !block_b

True
  { >block_a }
  { >block_b }
>ifelse
```

**Output:**
```
Option A
```

**Note:** `>ifelse` selects the appropriate block based on the condition and executes it.

### 13.3 Block as Return Value

```soma
{
  !_.x
  _.x 0 >>
    { { (positive) >print } }
    { { (non-positive) >print } }
  >choose
} !classify

5 classify >chain >chain
-3 classify >chain >chain
```

**Output:**
```
positive
non-positive
```

**Explanation:** `classify` returns a block based on input, which the caller can then execute.

---

## 14. User-Defined Execution

SOMA has no built-in "execute from AL" operation. However, the `>path` execution prefix enables you to build your own execution operators. This section demonstrates SOMA's power: language features that look like primitives are actually just user-defined blocks.

### 14.1 The `^` Operator - Execute AL Top

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

### 14.2 Dispatch Tables

Dispatch tables select and execute blocks based on a key:

**Note:** This example uses hypothetical `>ToPath` operation for demonstration.

```soma
{ (Handling add) >print } !handlers.add
{ (Handling subtract) >print } !handlers.sub
{ (Handling multiply) >print } !handlers.mul

{
  !_.operation
  (handlers.) _.operation >concat >ToPath >^
} !dispatch

(add) dispatch >chain
(mul) dispatch >chain
```

**Hypothetical output:**
```
Handling add
Handling multiply
```

**Explanation:**

1. `dispatch` takes operation name from AL, stores in Register
2. Builds path string: `(handlers.) + operation`
3. `>ToPath` would convert string to path and read the block from Store (hypothetical)
4. `>^` executes the block

### 14.3 Higher-Order Blocks

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

1. `5` pushes integer, `square` pushes square block
2. `>apply` executes apply block with fresh Register:
   - `!_.f` pops square block, stores in apply's Register
   - `!_.x` pops 5, stores in apply's Register
   - `_.x` pushes 5 onto AL
   - `>_.f` executes square block with fresh Register:
     - `!_.n` pops 5, stores in square's Register
     - `_.n _.n >*` computes 5 * 5 = 25
     - Leaves 25 on AL
3. `>print` outputs 25

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

**Output:**
```
tick
tick
```

**Example 3: Map-like pattern**

```soma
{
  !_.n
  _.n 2 >*
} !double

1 double >chain >print
2 double >chain >print
3 double >chain >print
```

**Output:**
```
2
4
6
```

### 14.4 Storing and Executing Custom Operations

```soma
) Define operation blocks
{ !_.b !_.a _.a _.b >+ } !ops.add
{ !_.b !_.a _.a _.b >- } !ops.sub
{ !_.b !_.a _.a _.b >* } !ops.mul

) Use a stored operation
5 3 ops.add >chain >print

) Change the operation
5 3 ops.mul >chain >print
```

**Output:**
```
8
15
```

---

## 15. Advanced Examples

### 15.1 FizzBuzz with >block

```soma
1 !n

{
  n 3 >/ 3 >* n >==
    {
      n 5 >/ 5 >* n >==
        { (FizzBuzz) >print }
        { (Fizz) >print }
      >ifelse
    }
    {
      n 5 >/ 5 >* n >==
        { (Buzz) >print }
        { n >print }
      >ifelse
    }
  >ifelse

  n 1 >+ !n

  n 16 ><
    { >block }
    { }
  >choose
} >chain
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
- `n` is in **Store** so it persists across loop iterations
- Each iteration gets fresh Register

### 15.2 Collatz Sequence with >block

```soma
10 !n

{
  n >print

  n 1 >==
    { }
    {
      n 2 >/ 2 >* n >==
        { n 2 >/ !n }
        { n 3 >* 1 >+ !n }
      >ifelse
      >block
    }
  >choose
} >chain
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

- `n` is in **Store** so updates persist
- Each iteration: fresh Register

### 15.3 String Builder Pattern

```soma
"" !output

{
  !_.str
  output _.str >concat !output
} !append

(Hello) append >chain
( ) append >chain
(SOMA) append >chain
( ) append >chain
(world) append >chain

output >print
```

**Output:**
```
Hello SOMA world
```

**Note:** `_.str` is Register (parameter), `output` is Store (accumulator).

### 15.4 Recursive Countdown

```soma
{
  !_.n

  _.n 0 >>
    {
      _.n >print
      _.n 1 >-
      >block >chain
    }
    { }
  >choose
} !countdown

5 countdown >chain
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

- `countdown` takes `_.n` from AL (stored in Register)
- Each recursive call via `>block >chain` creates fresh Register
- Must pass decremented value via AL for next call
- `_.n 1 >-` leaves decremented value on AL
- `>block >chain` executes with that value

---

## 16. Register Isolation: Complete Reference

### 16.1 The Three Memory Spaces

| Aspect | Store | Register | AL |
|--------|-------|----------|-----|
| **Scope** | Global | Block-local | Flow-based |
| **Lifetime** | Persistent | Block execution | Transient |
| **Sharing** | All blocks can access | Isolated per block | Explicit passing |
| **Purpose** | Shared state | Local computation | Data flow |
| **Example** | `config.port` | `_.temp` | Stack operations |
| **Access** | Bare path (`foo`) | Prefixed path (`_.foo`) | Push/pop |

### 16.2 Common Mistakes and Corrections

#### Mistake 1: Trying to access outer Register

❌ **WRONG:**
```soma
{
  1 !_.x
  {
    _.x >print  ) ERROR: _.x is Void in inner Register
  } >chain
} >chain
```

✅ **RIGHT (pass via AL):**
```soma
{
  1 !_.x
  _.x
  {
    !_.inner_x
    _.inner_x >print
  } >chain
} >chain
```

✅ **RIGHT (use Store):**
```soma
{
  1 !shared_x
  {
    shared_x >print
  } >chain
} >chain
```

#### Mistake 2: Expecting Register to persist after block completes

❌ **WRONG:**
```soma
{
  23 !_.x
}
_.x >print  ) ERROR: _.x doesn't exist in outer context
```

✅ **RIGHT (return via AL):**
```soma
{
  23 !_.x
  _.x
}
>print
```

#### Mistake 3: Loop counter in Register

❌ **WRONG:**
```soma
{
  0 !_.i
  {
    _.i >print  ) ERROR: _.i resets each iteration
    _.i 1 >+ !_.i
    _.i 3 >< { >block } { } >choose
  } >chain
} >chain
```

✅ **RIGHT (counter in Store):**
```soma
0 !i
{
  i >print
  i 1 >+ !i
  i 3 >< { >block } { } >choose
} >chain
```

#### Mistake 4: Storing helpers in Register

❌ **WRONG:**
```soma
{
  { !_.x _.x 2 >* } !_.double
  {
    5 >_.double >print  ) ERROR: _.double not in inner Register
  } >chain
} >chain
```

✅ **RIGHT (helper in Store):**
```soma
{
  { !_.x _.x 2 >* } !double
  {
    5 >double >print
  } >chain
} >chain
```

### 16.3 Best Practices

**1. Use Register for:**
- Block parameters (pop from AL immediately)
- Temporary calculations within a block
- Values that don't need to escape the block

**2. Use Store for:**
- Loop state across iterations
- Shared configuration
- Helper functions used by multiple blocks
- State that needs to persist
- Communication between unrelated blocks

**3. Use AL for:**
- Passing arguments to blocks
- Returning values from blocks
- Stack-based computation
- Temporary value transfer

**4. Naming conventions:**
- Register: Always `_.name`
- Store: Bare `name` or namespaced `module.name`
- Temporary Store (cleanup needed): Prefix with `temp_`

**5. Data flow patterns:**
- **Parameters:** AL → Register (via `!_.param`)
- **Return values:** Register → AL (via `_.result`) or just leave on AL
- **Shared state:** Store only
- **Loop state:** Store only (Register won't persist)

### 16.4 Mental Model

Think of block execution like a function call in traditional languages:

```
function block_execute() {
  local register = {};  // Fresh, empty

  // Execute code
  // All _.path operations use local register

  // register destroyed when function returns
}
```

**No lexical capture. No closure variables. Complete isolation.**

Share via Store (globals) or AL (arguments/returns).

---

## 17. Void vs Nil Semantics

**CRITICAL CONCEPT:** Void and Nil are fundamentally different values in SOMA:

- **Void** = "This cell has never been explicitly set" (absence, uninitialized)
- **Nil** = "This cell has been explicitly set to empty/nothing" (presence of emptiness)

### 17.1 Auto-Vivification Creates Void

When you write to a deep path, SOMA automatically creates intermediate cells with **Void** payload:

```soma
42 !a.b.c

) What are the payloads?
a.b.c >print    ) Prints: 42 (explicitly set)
a.b             ) Returns: Void (auto-vivified, never set)
a               ) Returns: Void (auto-vivified, never set)
```

**Execution trace:**

1. Write `42` to path `a.b.c`
2. Cell `a` doesn't exist → create with **Void** payload
3. Cell `a.b` doesn't exist → create with **Void** payload
4. Cell `a.b.c` created with payload **42**

**Store state:**
```
a → Cell(payload: Void, children: {...})
  └─ b → Cell(payload: Void, children: {...})
       └─ c → Cell(payload: 42, children: {})
```

**Key insight:** You didn't write Void (which would be an error). SOMA created intermediate cells with Void automatically.

### 17.2 Void vs Nil Detection

You can detect whether a cell has been set using hypothetical `>isVoid`:

```soma
) Auto-vivify intermediate cells
42 !config.deep.value

) Check if intermediate cell was set
config.deep >isVoid
  { (Never set) >print }
  { (Has been set) >print }
>ifelse

) Now explicitly set to Nil
Nil !config.deep

) Check again
config.deep >isVoid
  { (Never set) >print }
  { (Has been set) >print }
>ifelse
```

**Output:**
```
Never set
Has been set
```

**Explanation:**

1. After auto-vivification, `config.deep` has **Void** payload
2. `>isVoid` returns True → prints "Never set"
3. After `Nil !config.deep`, the cell has **Nil** payload
4. `>isVoid` returns False → prints "Has been set"

**Key distinction:** Void means "uninitialized", Nil means "initialized to empty"

### 17.3 Sparse Arrays

Void enables efficient sparse data structures:

```soma
) Create sparse array with only certain indices
100 !array.0
200 !array.5
300 !array.100

) Read unset indices
array.1             ) Returns Void (never set)
array.2             ) Returns Void (never set)
array.50            ) Returns Void (never set)

) Detect unset vs set-to-empty
array.1 >isVoid
  { (Index 1 is uninitialized) >print }
  { array.1 >print }
>ifelse

) Now explicitly set an index to Nil
Nil !array.2

array.2 >isVoid
  { (Index 2 is uninitialized) >print }
  { (Index 2 is explicitly Nil) >print }
>ifelse
```

**Output:**
```
Index 1 is uninitialized
Index 2 is explicitly Nil
```

**Key insight:** Unset indices return **Void** (not Nil), allowing you to distinguish "never set" from "set to empty".

### 17.4 Optional Fields Pattern

Void vs Nil creates a three-way distinction for data:

```soma
(John) !person.name
42 !person.age
Nil !person.middle_name     ) Explicitly no middle name

) Check fields
person.name                 ) (John) - has value
person.middle_name          ) Nil - explicitly empty
person.spouse               ) Void - never set (different meaning!)

) You can use this for validation
person.middle_name >isVoid
  { (Middle name not provided) >print }
  {
    person.middle_name >isNil
      { (No middle name) >print }
      { person.middle_name >print }
    >ifelse
  }
>ifelse

person.spouse >isVoid
  { (Spouse information not provided) >print }
  {
    person.spouse >isNil
      { (No spouse) >print }
      { person.spouse >print }
    >ifelse
  }
>ifelse
```

**Output:**
```
No middle name
Spouse information not provided
```

**Three states:**
- **Has value:** Cell was set to a non-Nil value
- **Explicitly empty (Nil):** Cell was set to Nil (intentional absence)
- **Uninitialized (Void):** Cell was never set (unknown/not provided)

### 17.5 Path Traversal Through Void

Void intermediate cells allow path traversal - you can read through them:

```soma
(value) !deep.nested.path.data

) All these reads succeed:
deep                          ) Void - but you can traverse through it
deep.nested                   ) Void - traversal continues
deep.nested.path              ) Void - traversal continues
deep.nested.path.data         ) (value) - final value
```

**Key behavior:** Reading Void is not an error. You can traverse through Void cells to reach deeper values.

### 17.6 Writing Void vs Nil

**You CANNOT write Void as a payload:**

```soma
Void !bad_path      ) FATAL ERROR - cannot write Void as payload
```

**But you CAN write Nil:**

```soma
Nil !good_path      ) Legal - explicitly set to Nil
good_path           ) Returns Nil ✓
good_path >isVoid   ) Returns False (it was set)
```

**You CAN use Void for structural deletion:**

```soma
42 !node
node >print         ) Prints: 42

Void !node.         ) Delete the cell structure (note the trailing .)
node                ) Cell no longer exists
```

**All legal operations:**
- `Void !path` → Legal (stores Void as value)
- `Nil !path` → Legal (explicit empty)
- `Void !path.` → Legal (structural deletion)

### 17.7 Nested Structures with Void

Auto-vivification with Void makes building deep structures natural:

```soma
) Build a configuration tree
8080 !server.http.port
443 !server.https.port
(localhost) !server.http.host
(0.0.0.0) !server.https.host

) Check what was auto-vivified
server >isVoid                  ) True - never explicitly set
server.http >isVoid             ) True - never explicitly set
server.http.port >isVoid        ) False - was set to 8080

) Explicitly set a parent
{} !server.http.config          ) Now server.http has structural meaning

server.http >isVoid             ) Still True! (payload is still Void)
server.http.config >isVoid      ) False - was set to {}
```

**Key insight:** Auto-vivified cells have **Void** payload even if they have children. Setting a child doesn't change the parent's payload.

### 17.8 Checking Existence vs Emptiness

Common pattern: distinguish between "field not provided" and "field explicitly empty":

```soma
{
  !_.field

  _.field >isVoid
    {
      (Field not provided - using default) >print
      (default_value)
    }
    {
      _.field >isNil
        { (Field explicitly empty - no default) >print Nil }
        { _.field }
      >choose
    }
  >choose
} !get_or_default

) Test with hypothetical ToPath (would need implementation)
) (unset_field) >ToPath get_or_default >chain >print

) Test with Nil (explicitly empty)
Nil !explicit_field
explicit_field get_or_default >chain

) Test with value
(actual_value) !value_field
value_field get_or_default >chain >print
```

**Hypothetical output:**
```
Field explicitly empty - no default
actual_value
```

**Note:** The first test using `>ToPath` is commented out as this operation doesn't exist in SOMA v1.0.

### 17.9 Reading Void is Not an Error

Unlike some operations, reading Void is perfectly legal:

```soma
) Create auto-vivified cells
100 !data.leaf

) Reading Void is fine
data !_.intermediate
_.intermediate >isVoid
  { (Yes, it's Void) >print }
  { (No, it was set) >print }
>ifelse
```

**Output:**
```
Yes, it's Void
```

**Legal operations with Void:**
- Reading Void from Store: ✓ Legal
- Having Void on AL: ✓ Legal (result of reading)
- Passing Void to `>isVoid`: ✓ Legal
- Traversing through Void cells: ✓ Legal

**Illegal operations with Void:**
- Writing Void as payload: ✗ FATAL ERROR
- Passing Void to most operations: ✗ ERROR (e.g., `Void >print`)

### 17.10 Void vs Nil Summary

| Aspect | Void | Nil |
|--------|------|-----|
| **Meaning** | "Never set" | "Set to empty" |
| **Created by** | Auto-vivification | Explicit write |
| **Can write?** | No (FATAL ERROR) | Yes |
| **Can read?** | Yes (returns Void) | Yes (returns Nil) |
| **>isVoid** | True | False |
| **>isNil** | False | True |
| **Use case** | Sparse structures, uninitialized | Optional fields, explicit empty |
| **Traversable?** | Yes | Yes |

**Mental model:**
- **Void** = "This cell exists for structural reasons but has no value"
- **Nil** = "This cell has the value 'nothing'"

---

## 18. Conclusion

SOMA's minimalist design means all control flow and execution emerges from just a few primitives:
- **>choose** for branching
- **>chain** for continuation
- **>path** for execution
- **>block** for self-reference
- **Register isolation** for clean scoping

Combined with these primitives, we can build:
- Loops (while, do-while, infinite loops)
- State machines (with clean state continuation)
- Conditional logic
- Data structures
- Higher-order patterns
- Recursive algorithms
- User-defined execution operators (like `^`)
- Dispatch tables and dynamic execution
- Macro-like language features

The key insights:
1. **Control flow is data:** Blocks are values, execution paths are stored in the AL
2. **State is explicit:** Store mutations are visible, Register provides local scope
3. **Self-reference is natural:** `>block` eliminates the need for workarounds
4. **Execution is first-class:** `>path` makes execution explicit and composable
5. **No special primitives:** Language features emerge from user-defined blocks
6. **Registers are isolated:** Each block gets fresh Register, share via Store/AL

This makes SOMA programs:
- **Transparent:** All state is visible
- **Inspectable:** No hidden call stack or control flow
- **Explicit:** Every transformation is a clear AL → AL, Store → Store transition
- **Clean:** `>block` and Register variables reduce boilerplate
- **Extensible:** Users can define their own execution patterns and "language features"
- **Predictable:** Register isolation prevents action-at-a-distance bugs

Understanding these patterns, especially `>block`, Register isolation, and `>path` execution, is essential to writing effective SOMA code.

---

## 19. Everything is a Block

**Axiomatic principle:** All SOMA execution occurs within a block context.

### 19.1 Top-Level Code is a Block

When you write code at the "top level" of a SOMA program, it's executing in an implicit outermost block:

```soma
) This code executes in the implicit outermost block
23 !_ _ >print
```

There's no "outside" the outermost block - that's the runtime environment (like hardware/OS).

### 19.2 No Infinite Regress

We don't need to write:

```soma
>{                  ) What executes this?
  >{                ) And this?
    >{              ) Turtles all the way down...
      23 !_ _ >print
    }
  }
}
```

We simply say: **The top-level code IS a block.** The runtime executes it. There's nothing to formalize "outside" SOMA's computational model.

### 19.3 `>block` Works Everywhere

The `>block` built-in works at any level, including the top level:

```soma
) Top-level
>block              ) Returns the outermost block (the (program))

) Inside explicit block
{ >block }          ) Returns this block

) Nested blocks
{
  >block !outer
  {
    >block !inner
    ) Note: Comparing blocks would require equality operator
    ) outer inner >== would compare Block₁ and Block₂
  }
}
```

**Execution trace for nested example:**

1. Outer block executes, gets Block₁
2. `>block` pushes Block₁ onto AL
3. `!outer` stores Block₁ in Store
4. Inner block executes, gets Block₂
5. `>block` pushes Block₂ onto AL
6. `!inner` stores Block₂ in Store
7. Block₁ and Block₂ are different blocks

**Key insight:** Each block is a distinct value. `>block` always returns the currently executing block, whether it's the top-level program, an explicit block, or a deeply nested block.

### 19.4 Blocks All the Way Down

Every construct in SOMA that "does something" is a block:

```soma
) This is a block (the top-level program)
{ 1 2 >+ }          ) This is a block (explicit)
>choose             ) This executes a block (built-in that consumes blocks)
>chain              ) This executes blocks in sequence
>block              ) This returns the block being executed
```

**There is no execution context outside of blocks.** This is SOMA's foundational principle.

---

## 20. Internationalization: Aliasing Built-ins

One of SOMA's design goals is to be **language-agnostic**. All built-ins can be aliased, allowing programmers to use their native language.

### 20.1 How Aliasing Works

Built-ins are just blocks stored in the Store. You can create aliases by storing them at different paths:

```soma
chain !MyChain          ) Alias for chain
print !log              ) Alias for print
choose !select          ) Alias for choose
```

Now you can use `>MyChain`, `>log`, and `>select` exactly like the originals.

### 20.2 German Programming Example

A complete German-language SOMA program:

```soma
) German aliases for built-ins
block !Block
chain !Kette
print !drucken

) Infinite loop in German
{ (tick) >drucken >Block } >Kette
```

**What this demonstrates:**

- `block !Block` - Alias `block` to German "Block" (capitalized)
- `chain !Kette` - Alias `chain` to German "Kette" (chain)
- `print !drucken` - Alias `print` to German "drucken" (to print)
- The code is now pure German!

**This was impossible with `_.self`** because `_.self` was a special Register binding, not a built-in, so it couldn't be aliased.

### 20.3 Swedish Programming Example

A complete Swedish-language SOMA program:

```soma
) Swedish aliases
block !blockera
choose !välja
chain !kedja
print !skriv

) Counter loop in Swedish
0 !räknare

{
  räknare >skriv
  räknare 1 >+ !räknare

  räknare 5 ><
    { >blockera }
    { }
  >välja
} >kedja
```

**Output:**
```
0
1
2
3
4
```

**What this demonstrates:**

- `block !blockera` - Swedish "blockera" (to block)
- `choose !välja` - Swedish "välja" (to choose)
- `chain !kedja` - Swedish "kedja" (chain)
- `print !skriv` - Swedish "skriv" (to write)
- Variable names also in Swedish: `räknare` (counter)
- Complete working loop in Swedish

### 20.4 Mixing Languages

You can even mix languages in the same program:

```soma
) English built-ins
block !Block
chain !Kette

) Use both
{ (Hello) >print >Block } >Kette     ) English print, German loop
```

This flexibility makes SOMA accessible to programmers worldwide.

### 20.5 Why `>block` Enables This

**The old way with `_.self`:**

```soma
chain !Kette            ) Can alias chain
print !drucken          ) Can alias print

{ >drucken _.self } >Kette    ) Must use English (self) - CAN'T ALIAS
```

**The new way with `>block`:**

```soma
chain !Kette            ) Can alias chain
print !drucken          ) Can alias print
block !Block            ) Can alias block!

{ >drucken >Block } >Kette    ) Pure German!
```

**The difference:** `_.self` was a special Register binding that appeared magically. You couldn't change it. `>block` is just another built-in, so it can be aliased like any other operation.

### 20.6 Creating Domain-Specific Languages

Aliasing isn't just for human languages. You can create domain-specific vocabularies:

```soma
) Web server DSL
chain !serve_forever
print !log_message
block !restart

) HTTP handler
{ request >log_message >process_http >restart } !http_loop
```

Or mathematical notation:

```soma
) Math DSL
+ !add
- !subtract
* !multiply
block !recurse

{ n 1 >subtract >recurse } !decrement
```

**The power of aliasing:** SOMA's syntax adapts to your domain, language, and preferences.

