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


