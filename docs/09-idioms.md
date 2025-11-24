# SOMA Programming Idioms and Best Practices

**SOMA v1.1 Language Specification - Programming Style Guide**
**Category: Tutorial**
**Date: 24 November 2025**

---

## Introduction

SOMA uses **execution scope**, not lexical scope. This fundamental difference from languages like JavaScript, Python, or C shapes every programming pattern in SOMA.

### The Core Principle

Every time a block `{ }` executes (via `>^`, `>{`, or `>chain`), it receives a **fresh Register** with no automatic access to any parent scope. To pass data between block executions, you must explicitly use the Accumulator List (AL).

```soma
) This does NOT work - lexical scope assumption
>{
  42 !_.x
  { _.x >toString >print } >^   ) ERROR: _.x is Void in nested block!
}

) This DOES work - explicit context passing
>{
  42 !_.x
  _.              ) Push context reference onto AL
  >{              ) Execute block WITH context on AL
    !_.           ) Pop context into this block's Register
    _.x >toString >print
  }
}
```

**Remember:** Blocks are VALUES, not scopes. They execute with whatever context you explicitly provide via the AL.

---

## The Context-Passing Idiom

The context-passing idiom is the most important pattern in SOMA. It enables blocks to share state without global variables or complex stack juggling.

### Basic Pattern

```soma
>{
  ) Set up state in outer Register
  42 !_.x
  100 !_.y

  ) Push reference to outer Register onto AL
  _.

  ) Execute block with context
  >{
    ) Pop context reference and store at THIS Register's root
    !_.

    ) Now we can access outer Register's data transparently
    _.x _.y >+ >toString >print    ) Prints: 142
  }
}
```

### How It Works

1. `_.` creates a CellRef to the current Register's root Cell
2. This CellRef is pushed onto the AL
3. `!_.` in the inner block stores that CellRef AT the inner Register's `_` location
4. When the inner block accesses `_.x`, the Register follows the CellRef automatically
5. All reads and writes go through to the aliased Register

### Why It Matters

Without this idiom, passing multiple values between blocks requires:
- Stack juggling (pushing/popping values in correct order)
- Complex AL management
- Error-prone code

With this idiom:
- Named access to shared state (`_.counter`, `_.total`, etc.)
- Clear data flow
- Maintainable code

---

## Looping with >chain

The `>chain` operator enables tail-call optimization for loops. A block returns either `Nil` (stop) or another block (continue).

### Basic Loop Pattern

```soma
{
  !_.                    ) Pop context from AL

  ) Do work using _.fields...

  _.                     ) Push context for next iteration
  _.condition
    { blockname }        ) True: continue (return self)
    { >drop Nil }        ) False: drop context, stop
  >choose >^
} !blockname             ) Store in Store (for self-reference)

_.                       ) Push initial context
blockname >^             ) Execute first iteration
>chain                   ) Chain remaining iterations
>drop                    ) Clean up Nil result if needed
```

### Complete Example: Counter

```soma
>{
  0 !_.counter

  {
    !_.                          ) Pop context
    _.counter >inc !_.counter    ) Increment
    _.counter >toString >print   ) Print

    _.                           ) Push context
    _.counter 10 ><              ) Less than 10?
      { loop }                   ) True: continue
      { >drop Nil }              ) False: stop
    >choose >^
  } !loop                        ) Store in Store

  _.
  loop >^
  >chain
  >drop
}
) Prints: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
```

### Key Points

1. **Context flows through AL:** Each iteration receives context via `_.` → `!_.`
2. **Self-reference requires Store:** Block stored as `!loop` (Store), not `!_.loop` (Register)
3. **Clean up after >chain:** Add `>drop` if test expects empty AL
4. **Condition before choose:** Push context, check condition, choose continuation

---

## Using >choose Effectively

`>choose` is a selector, not an executor. It pops a condition and two choices, then pushes the selected choice onto the AL.

### Pattern 1: Choose Between Values

When you just need to select between two values, use them directly:

```soma
) Select max of two numbers
_.x _.y >>
  _.x          ) True: select x
  _.y          ) False: select y
>choose
!_.max         ) Store selected value
```

**No blocks needed!** This avoids execution scope issues entirely.

### Pattern 2: Choose Between Computations

When branches need to DO something different, use blocks:

```soma
_.value 0 ><
  { _.value }          ) Positive: use value
  { _.value -1 >* }    ) Negative: negate
>choose >^             ) Execute chosen block
```

### Pattern 3: Choose Continuation for >chain

The standard loop pattern:

```soma
_.
_.count 10 ><
  { loop }           ) Continue: return block name
  { >drop Nil }      ) Stop: drop context, return Nil
>choose >^
```

### Common Mistake

```soma
) WRONG - branches need context but get fresh Registers
_.x _.max >>
  { _.x !_.max }     ) ERROR: _.x is Void in fresh Register!
  { }
>choose >^

) RIGHT - push context before choose
_.
_.x _.max >>
  { >{ !_. _.x !_.max } }    ) Execute WITH context
  { >drop }                  ) Drop context
>choose >^
```

---

## Store vs Register

Understanding when to use Store (global) vs Register (local) storage is crucial.

### Store (!name)

**Use Store when:**
- Blocks need to reference themselves by name (loops)
- Functions should be globally accessible
- Data should persist across block executions

```soma
{
  !_.
  _.counter >toString >print
  _.
  _.counter 10 ><
    { countdown }      ) References itself by name
    { >drop Nil }
  >choose >^
} !countdown           ) MUST be in Store

_.
countdown >^
>chain
```

### Register (!_.name)

**Use Register when:**
- Data is local to current execution
- State should NOT leak between invocations
- Working with context-passing idiom

```soma
>{
  42 !_.local_value    ) Local to this block execution
  _.
  >{
    !_.
    _.local_value >toString >print
  }
}
```

### Quick Reference

| Storage | Syntax | Scope | Use Case |
|---------|--------|-------|----------|
| Store | `!name` | Global | Self-referencing blocks, shared functions |
| Register | `!_.name` | Local to block execution | Context data, temporary state |

---

## Common Patterns

### Pattern: Tail-Recursive Loop

```soma
{
  !_.
  ) Work...
  _.
  _.condition { loop } { >drop Nil } >choose >^
} !loop

_.
loop >^
>chain
>drop
```

### Pattern: Accumulator

```soma
>{
  0 !_.sum
  1 !_.n

  {
    !_.
    _.sum _.n >+ !_.sum
    _.n >inc !_.n

    _.
    _.n 100 >>
      { accumulate }
      { >drop Nil }
    >choose >^
  } !accumulate

  _.
  accumulate >^
  >chain
  >drop

  _.sum >toString >print    ) Prints: 5050
}
```

### Pattern: Conditional Update

```soma
) Update max if new value is larger
_.new_value _.max >>
  _.new_value    ) True: use new value
  _.max          ) False: keep max
>choose
!_.max
```

### Pattern: State Machine

```soma
{
  !_.
  _.state >toString >print

  _.
  _.state (processing) >==
    { state_processing }
    { _.state (done) >==
        { >drop Nil }
        { state_waiting }
      >choose >^
    }
  >choose >^
} !state_waiting

{
  !_.
  (processing...) >print
  (done) !_.state
  _.
  state_waiting
} !state_processing

(waiting) !_.state
_.
state_waiting >^
>chain
>drop
```

---

## Anti-Patterns to Avoid

### ❌ Assuming Lexical Scope

```soma
) WRONG
>{
  42 !_.x
  { _.x >toString >print } >^    ) _.x is Void!
}

) RIGHT
>{
  42 !_.x
  _.
  >{ !_. _.x >toString >print }
}
```

### ❌ Storing Self-Referencing Blocks in Register

```soma
) WRONG
{
  !_.
  _.
  _.counter 10 >< { loop } { >drop Nil } >choose >^
} !_.loop              ) Stored in Register

_.
_.loop >^              ) Can't reference by bare name 'loop'!
>chain

) RIGHT
{
  !_.
  _.
  _.counter 10 >< { loop } { >drop Nil } >choose >^
} !loop                ) Stored in Store

_.
loop >^
>chain
```

### ❌ Using Blocks When Values Suffice

```soma
) WRONG - unnecessary blocks with execution scope issues
_.x _.y >>
  { _.x }              ) Fresh Register, _.x might be Void
  { _.y }
>choose >^

) RIGHT - just use values
_.x _.y >>
  _.x
  _.y
>choose
```

### ❌ Forgetting Context for Iterations

```soma
) WRONG
{
  !_.
  _.counter >toString >print
  ) ... missing _.
  _.counter 10 >< { loop } { >drop Nil } >choose >^
} !loop

loop >chain            ) No context for first iteration!

) RIGHT
{
  !_.
  _.counter >toString >print
  _.                   ) Push context
  _.counter 10 >< { loop } { >drop Nil } >choose >^
} !loop

_.                     ) Push initial context
loop >^
>chain
```

### ❌ Not Cleaning Up After >chain

```soma
) If test expects empty AL but >chain leaves Nil:

_.
loop >^
>chain                 ) Leaves Nil on AL

) Add >drop:
_.
loop >^
>chain
>drop                  ) Clean AL
```

---

## Complete Examples

### Example 1: Collatz Sequence

```soma
6 !_.current

{
  !_.
  _.current >toString >print

  _.
  _.current 1 >==
    {
      >drop Nil
    }
    {
      >{
        !_.
        _.current
        _.current 2 >% 0 >==
          { 2 >/ }
          { 3 >* 1 >+ }
        >choose >^
        !_.current

        _.
        collatz-step
      }
    }
  >choose >^
} !collatz-step

_.
collatz-step >^
>chain
) Prints: 6, 3, 10, 5, 16, 8, 4, 2, 1
```

### Example 2: Fibonacci

```soma
>{
  0 !_.a
  1 !_.b
  0 !_.count

  {
    !_.
    _.b >toString >print

    _.a _.b >+ !_.tmp
    _.b !_.a
    _.tmp !_.b
    _.count >inc !_.count

    _.
    _.count 10 ><
      { fib }
      { >drop Nil }
    >choose >^
  } !fib

  _.
  fib >^
  >chain
  >drop
}
) Prints first 10 Fibonacci numbers
```

### Example 3: Find Maximum

```soma
>[5, 2, 9, 1, 7] !values    ) Assume array support

>{
  0 !_.max
  0 !_.index

  {
    !_.
    values _.index >at
    _.max >>
      {
        >{
          !_.
          values _.index >at !_.max
          _.
          process
        }
      }
      {
        _.
        process
      }
    >choose >^

    ) Continue or stop
    _.
    _.index >inc !_.index
    _.index values >length ><
      { process }
      { >drop Nil }
    >choose >^
  } !process

  _.
  process >^
  >chain
  >drop

  _.max >toString >print    ) Prints: 9
}
```

---

## Summary

### Golden Rules

1. **Execution scope, not lexical scope** - Blocks get fresh Registers
2. **Context flows via AL** - Use `_.` → `!_.` pattern
3. **Store for self-reference** - Use `!name` not `!_.name` for loops
4. **Values over blocks** - Use `>choose` with values when possible
5. **Always push context** - Before loops, before continuation checks

### The Standard Loop Template

```soma
{
  !_.                    ) Pop context
  ) Work...
  _.                     ) Push context
  condition
    { blockname }        ) Continue
    { >drop Nil }        ) Stop
  >choose >^
} !blockname

_.                       ) Initial context
blockname >^
>chain
>drop
```

### When in Doubt

- If accessing parent block's data → use context-passing idiom
- If block references itself → store in Store
- If selecting between values → use `>choose` with values
- If forgetting context → add `_.` before continuation

---

## Further Reading

- **SKILL.md** - Complete language reference
- **FIXME_LEXICAL_SCOPE.md** - Learning journey from lexical to execution scope thinking
- **Test files** (`tests/soma/03_*.soma`) - Working examples of all patterns
