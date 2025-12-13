# # 12. Debugging and Invariants

Debugging tools and assertion mechanisms for verifying program invariants.

---

## ## Philosophy: Falsifiability and Invariant Testing

**A claim without a potential falsifier is not useful.** This principle underlies all debugging in SOMA. An assertion that cannot fail provides no information; a test that cannot detect a bug catches no bugs.

Debugging is not merely finding errors—it is constructing a falsifiable model of program behaviour. Each assertion, each `>debug.al.dump`, each `>print` is a probe that tests a hypothesis about state. If the hypothesis cannot be falsified, the probe is worthless.

**Assertions and tests "colour in" the state manifold where invariants hold.** This is not proof in the general case, but it builds confidence that further invariants can be layered on top. Rigour compounds; so does sloppiness.

The invariant-testing approach:

- State the invariant explicitly
- Write code that asserts the invariant
- Attempt to break it with adversarial inputs
- If it survives, layer additional invariants on top

A test which is not falsifiable is not useful. This principle extends beyond code to reasoning, documents, and all collaborative work.

---

## ## Implementation-Specific Debug Tools

**WARNING:** The `debug.*` namespace is **implementation-specific**, not part of SOMA's core semantics. These tools exist solely for debugging and instrumentation. They must **NEVER** be used for normal program control flow or logic. Different SOMA implementations may provide different debug facilities or none at all.

### ### >debug.al.dump

**Signature:** `() -> ()`

Displays the current AL and Store state for debugging. Does not modify AL or Store. This is a non-destructive snapshot of machine state.

**Example:**

```soma
1 2 3
>debug.al.dump   ; Shows AL: [1, 2, 3] and Store contents
>+               ; Compute 2 + 3
>debug.al.dump   ; Shows AL: [1, 5] - verify operation
```

**Use cases:**

- Understanding complex AL manipulations
- Verifying Store state after assignments
- Debugging unexpected stack depth issues

**Errors:** None.

---

### ### >debug.type

**Signature:** `(Value) -> Str`

Pops a value and pushes a string representing its type. Essential for runtime type checking and debugging type-related issues.

**Example:**

```soma
42 >debug.type        ; AL: ["Int"]
(hello) >debug.type   ; AL: ["Str"]
True >debug.type      ; AL: ["Bool"]
{ >noop } >debug.type ; AL: ["Block"]
```

**Use cases:**

- Runtime type assertions
- Debugging unexpected value types
- Polymorphic dispatch based on type

**Errors:** Fatal if AL is empty.

---

### ### >debug.id

**Signature:** `(Value) -> Int`

Pops any value and pushes an integer identity value. For CellRefs, returns the identity of the underlying Cell. Useful for distinguishing between different instances of mutable structures.

**Example:**

```soma
a.b. >debug.id        ; AL: [<identity integer>]
thing. >debug.id      ; AL: [<identity integer>]

; Comparing identities
cell1. >debug.id
cell2. >debug.id
>==             ; AL: [True] if same cell, [False] otherwise
```

**Use cases:**

- Verifying that two references point to the same cell
- Debugging aliasing issues
- Tracking object identity through transformations

**Errors:** Fatal if AL is empty.

---

## ## Stdlib Debug Tools

The standard library provides higher-level debugging facilities built atop the builtins.

### ### >debug.assert

**Signature:** `(Block, Str) -> () | HALT`

Executes a condition block; if the result is `False`, halts execution with the provided error message. If `True`, execution continues normally with the condition result consumed.

This is the primary invariant-testing mechanism in SOMA. Use it to assert conditions that must hold for correct program execution.

**Usage:**

```soma
{ x 0 >> } (x must be positive) >debug.assert
{ count limit >< } (count must not exceed limit) >debug.assert
{ name >debug.type "Str" >== } (name must be a string) >debug.assert
```

**Definition:**

```soma
{
  !_.msg !_.cond
  _.                                   ) Push context for choose branches
  >_.cond                              ) Execute condition block
  {
    !_.                                ) Pop context (True branch - discard)
  }
  {
    !_.                                ) Pop context
    _.msg >debug.error                 ) Halt with error message
  }
  >choose >^
} !debug.assert
```

**How it works:**

- Stores the message and condition block in the register
- Pushes the register context for later access
- Executes the condition block, leaving a boolean on the AL
- Uses `>choose` to select between continuation (True) and error (False)
- On False, calls `>debug.error` which halts execution with the stored message

---

## ## Debugging Patterns

Effective debugging in SOMA requires understanding the stack-based model. The following patterns address common debugging scenarios.

### ### AL Inspection Techniques

Strategic use of `>debug.al.dump` reveals AL state at key points:

```soma
) Pattern: Bracketed inspection
) Wrap complex operations to see before/after state
(Before operation:) >print >debug.al.dump
) ... complex AL manipulation ...
(After operation:) >print >debug.al.dump

) Pattern: Tagged checkpoints
(Checkpoint A) >print >debug.al.dump
) ... code section A ...
(Checkpoint B) >print >debug.al.dump
) ... code section B ...

) Pattern: Value tagging
) Print with context without consuming the value
>dup (Current value: ) >swap >toString >cat >print
```

### ### Incremental Testing Approach

Build confidence through layered assertions:

```soma
) Level 1: Input validation
{ input >debug.type "Int" >== } (input must be integer) >debug.assert
{ input 0 >> } (input must be positive) >debug.assert

) Level 2: Intermediate state
) ... computation ...
{ partial-result limit >< } (intermediate value in range) >debug.assert

) Level 3: Output validation
) ... more computation ...
{ result expected-type >debug.type >== } (result type correct) >debug.assert
{ result minimum >> } (result above minimum) >debug.assert
```

This layered approach:

- Catches errors early, close to their source
- Documents assumptions explicitly
- Provides clear error messages when invariants fail
- Builds a falsifiable model of correct behaviour

### ### Writing Testable SOMA Code

Design for testability:

- **Isolate pure computations** - Blocks that only manipulate the AL are easy to test. Push inputs, execute, verify outputs.
- **Use assertions as documentation** - Assertions serve dual purpose: runtime checks and specification of expected behaviour.
- **Make state explicit** - Store state in named locations rather than relying on AL depth. Named state is easier to inspect and verify.
- **Test boundary conditions** - Zero, negative, maximum values. Empty strings, single characters. These are where bugs hide.

---

## ## Reference Table

| Debug operation  | Location | AL transformation         | Purpose                  |
|------------------|----------|---------------------------|--------------------------|
| `>print`         | Builtin  | `(Value) -> ()`           | Output value to stdout   |
| `>debug.al.dump` | Builtin  | `() -> ()`                | Display machine state    |
| `>debug.type`    | Builtin  | `(Value) -> Str`          | Get type name as string  |
| `>debug.id`      | Builtin  | `(Value) -> Int`          | Get identity of value    |
| `>debug.assert`  | Stdlib   | `(Block, Str) -> ()|HALT` | Assert condition or halt |
| `>debug.error`   | Builtin  | `(Str) -> HALT`           | Halt with error message  |

---

## ## Summary

Debugging in SOMA is an exercise in constructing falsifiable hypotheses about program state. The tools provided—`>print`, `>debug.al.dump`, `>debug.type`, `>debug.id`, `>debug.assert`, and `>debug.error`—are probes for testing these hypotheses.

- Make invariants explicit through assertions
- Observe AL and Store state at critical points
- Verify types when crossing abstraction boundaries
- Halt execution when unrecoverable errors occur

Remember: a test which is not falsifiable is not useful. Every assertion should be capable of failing, and every debugging probe should tell you something you did not already know with certainty.


