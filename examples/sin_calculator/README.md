# SOMA Sin Calculator Example

A complete demonstration of computing sine values using Taylor series expansion in SOMA, showcasing scaled integer arithmetic and the >chain iteration idiom.

## Quick Start

From the SOMA repository root:

```bash
python3 examples/sin_calculator/run_soma_sin.py
```

**Output:**
```
sin(0°) = 0.0000000000
sin(30°) = 0.5000000010
sin(45°) = 0.7071067814
sin(60°) = 0.8660254037
sin(90°) = 1.0000000010
sin(180°) = 0.0000000000
sin(270°) = -0.9999999995
sin(360°) = 0.0000000012
```

---

## Table of Contents

1. [Design Overview](#design-overview)
2. [Reading SOMA Syntax](#reading-soma-syntax)
3. [Code Walkthrough](#code-walkthrough)
4. [How It Works](#how-it-works)
5. [Accuracy Analysis](#accuracy-analysis)
6. [Key Concepts](#key-concepts)

---

## Design Overview

### The Challenge

Compute `sin(angle°)` with the following constraints:
- SOMA only has **integer arithmetic** (no floating point)
- Must use **Taylor series expansion**: sin(x) = x - x³/3! + x⁵/5! - x⁷/7! + ...
- Must use the **>chain idiom** for iteration
- Output format: **D.DDDDDDDDDD** (exactly 10 decimal places)

### The Solution

**Scaled Integer Arithmetic**: Multiply all values by 10^10 to simulate 10 decimal places
- Example: 3.14159 becomes 31,415,900,000
- Allows integer math to represent decimals

**Taylor Series Iteration**: Each term computed from previous term
- term₀ = x
- term_{n+1} = -term_n × x² / ((2n+1)(2n+2))
- Stop when |term| < threshold

**Store-Based State**: Use global Store instead of Register for simplicity
- `sin.x`, `sin.term`, `sin.sum` etc.
- Avoids complex context-passing between blocks

---

## Reading SOMA Syntax

Before diving into the code, here's a quick SOMA syntax guide:

### Basic Syntax

```soma
) This is a comment

42              ) Push integer 42 onto AL (Accumulator List / stack)
(Hello)         ) Push string "Hello" onto AL (note: parentheses, not quotes!)

!variable       ) Pop AL top, store at 'variable' in Store
variable        ) Read 'variable' from Store, push onto AL

>operation      ) Execute operation (pops args from AL, pushes result)
>function       ) Execute function from Store

{ code }        ) Block literal (code is not executed, just pushed to AL)
>{ code }       ) Execute block literal immediately
```

### Key Operators

```soma
>+              ) Add: [a, b] → [a+b]
>-              ) Subtract: [a, b] → [a-b]
>*              ) Multiply: [a, b] → [a×b]
>/              ) Divide: [a, b] → [a/b] (integer division)
><              ) Less than: [a, b] → [bool]
>>              ) Greater than: [a, b] → [bool]

>dup            ) Duplicate AL top: [a] → [a, a]
>drop           ) Remove AL top: [a] → []
>swap           ) Swap top two: [a, b] → [b, a]

>print          ) Print string from AL
>toString       ) Convert int to string
>ifelse         ) Conditional: [bool, true_block, false_block] → executes one
>chain          ) Execute blocks from AL until Nil is returned
```

### Store Paths

```soma
x               ) Simple variable
sin.x           ) Namespace: sin.x
sin.n1          ) Multiple levels: sin.n1
_.x             ) Register (block-local, fresh on each execution)
```

### Example: Reading a Simple Function

```soma
{
  !_.b !_.a              ) Pop AL twice: b first, then a (reverse order!)
  _.a _.b >*             ) Push a, push b, multiply
  SCALE >/               ) Divide result by SCALE
} !scaled_mult           ) Store block as 'scaled_mult'

5 3 >scaled_mult         ) Push 5, push 3, execute scaled_mult
                         ) AL now has result
```

**Reading tip**: SOMA is stack-based, so read bottom-up when analyzing AL state.

---

## Code Walkthrough

Let's walk through `soma_sin_calculator.soma` section by section:

### Part 1: Constants

```soma
10000000000 !SCALE              ) Scale factor: 10^10
31415926536 !PI_SCALED          ) π × SCALE ≈ 3.1415926536 × 10^10
180 !DEGREES_PER_PI             ) 180 degrees = π radians
1000 !MIN_TERM                  ) Convergence threshold (scaled)
```

**What this does:**
- Defines our scale factor (10 billion) for fixed-point arithmetic
- Stores π as an integer (31,415,926,536)
- Sets iteration stop condition

### Part 2: Scaled Multiplication Helper

```soma
{
  !_.b !_.a                     ) Pop b, then a from AL into Register
  _.a _.b >*                    ) Multiply: a × b (result is scaled²!)
  SCALE >/                      ) Divide by SCALE to correct scaling
} !scaled_mult
```

**What this does:**
- Takes two scaled integers from AL
- Multiplies them (creates scale² = 10^20 result)
- Divides by scale (10^10) to return to 10^10 scaling
- Stores as callable function 'scaled_mult'

**Example:**
- Input: 2.5 × 10^10 and 3.0 × 10^10 (representing 2.5 and 3.0)
- Multiply: 75 × 10^20
- Divide by 10^10: 75 × 10^10 (representing 7.5) ✓

### Part 3: Degree to Radian Conversion

```soma
{
  !_.deg                        ) Store input angle from AL
  _.deg PI_SCALED >*            ) degrees × π_scaled
  DEGREES_PER_PI >/             ) Divide by 180
} !deg_to_rad
```

**What this does:**
- Implements: radians = degrees × π / 180
- Input: degrees (unscaled integer like 90)
- Output: radians (scaled by 10^10)

**Example:**
- Input: 90 degrees
- 90 × 31,415,926,536 = 2,827,433,388,240
- 2,827,433,388,240 / 180 = 15,707,963,268
- This represents π/2 ≈ 1.5707963268 radians ✓

### Part 4: Taylor Series Sin Computation (The Core!)

```soma
{
  !sin.x                        ) Store input x in Store (not Register!)
  sin.x !sin.term               ) Initialize: term = x
  sin.x !sin.sum                ) Initialize: sum = x
  1 !sin.power                  ) Initialize: power = 1

  {                             ) Start of iteration block
    ) Compute next term: -term × x² / ((power+1)(power+2))

    sin.term sin.x sin.x        ) AL: [term, x, x]
    >scaled_mult                ) AL: [term, x²]
    >scaled_mult                ) AL: [term×x²]

    sin.power 1 >+ !sin.n1      ) n1 = power + 1 (e.g., 1+1=2)
    sin.n1 1 >+ !sin.n2         ) n2 = n1 + 1 (e.g., 2+1=3)
    sin.n1 sin.n2 >* >/         ) Divide by (n1 × n2) = 2×3 = 6

    0 >swap >-                  ) Negate: 0 - value (alternating signs)
    !sin.term                   ) Store new term

    ) Add term to sum
    sin.sum sin.term >+ !sin.sum

    ) Update power for next iteration
    sin.n2 !sin.power           ) power = 3 (for next term x⁵)

    ) Check convergence: should we continue?
    sin.term >dup 0 ><          ) Check if term < 0
      { 0 >swap >- }            ) If negative, compute abs (0 - term)
      { }                       ) If positive, keep as is
    >ifelse                     ) Execute chosen block

    MIN_TERM >>                 ) Is |term| > MIN_TERM?
      { iter }                  ) Yes: return 'iter' block (continue)
      { Nil }                   ) No: return Nil (stop)
    >ifelse

  } !iter                       ) Store iteration block as 'iter'

  >iter                         ) Execute first iteration
  >chain                        ) Chain: execute iter, if block, execute it, repeat
  >drop                         ) Drop the final Nil
  sin.sum                       ) Push result onto AL
} !compute_sin
```

**Understanding the iteration:**

Iteration 1 (x = π/2):
- term = π/2
- sum = π/2
- Next term = -(π/2) × (π/2)² / (2×3) = -(π/2)³ / 6
- sum = π/2 - (π/2)³/6
- |term| still > 1000, so continue...

Iteration 2:
- term = -(π/2)³/6
- Next term = -(-(π/2)³/6) × (π/2)² / (4×5) = +(π/2)⁵/120
- sum = π/2 - (π/2)³/6 + (π/2)⁵/120
- Continue...

This continues until |term| < 1000, typically 5-7 iterations for convergence.

**The >chain idiom:**
```soma
>iter >chain
```
1. Execute `iter` block
2. `iter` pushes either `iter` (to continue) or `Nil` (to stop) onto AL
3. `>chain` checks AL top:
   - If Block: execute it, goto step 2
   - If not Block (Nil): stop
4. Result: iteration until condition fails!

### Part 5: Decimal Formatting

```soma
{
  !fmt.val                      ) Store scaled value to format

  ) Handle negative sign
  fmt.val 0 ><                  ) Is value < 0?
    { 0 fmt.val >- !fmt.val     ) Yes: make positive, print "-"
      (-) >print }
    { }                         ) No: do nothing
  >ifelse

  ) Print integer part
  fmt.val SCALE >/ !fmt.int     ) Integer part = value / 10^10
  fmt.int >toString >print       ) Print it
  (.) >print                    ) Print decimal point

  ) Print fractional part (exactly 10 digits)
  fmt.val fmt.int SCALE >* >- !fmt.frac    ) frac = value - (int × 10^10)
  10 !fmt.digits                ) Need 10 digits

  {                             ) Iteration block for each digit
    fmt.frac 10 >*              ) Shift left: frac × 10
    >dup SCALE >/ !fmt.digit    ) Extract digit: (frac×10) / 10^10
    fmt.digit >toString >print   ) Print the digit
    fmt.digit SCALE >* >- !fmt.frac  ) Remove digit: frac - (digit×10^10)
    fmt.digits 1 >- !fmt.digits ) Decrement counter

    fmt.digits 0 >>             ) More digits needed?
      { fmt_loop }              ) Yes: continue
      { Nil }                   ) No: stop
    >ifelse
  } !fmt_loop

  >fmt_loop >chain >drop        ) Execute digit printing loop
} !format
```

**Example: Formatting 15707963268 (representing π/2 ≈ 1.5707963268)**

1. Integer part: 15707963268 / 10^10 = 1
   - Print: "1."
2. Fractional part: 15707963268 - (1 × 10^10) = 5707963268
3. Digit loop:
   - Iteration 1: (5707963268 × 10) / 10^10 = 5 → Print "5"
     - Remaining: 5707963268 - (5 × 10^10) = Hmm, this math doesn't work...

Actually, let me recalculate this more carefully:

Initial: 15707963268
- Integer: 15707963268 / 10000000000 = 1
- Fraction: 15707963268 % 10000000000 = 5707963268

Digit 1: (5707963268 × 10) / 10000000000 = 57079632680 / 10000000000 = 5
- New frac: 57079632680 - (5 × 10000000000) = 7079632680

Digit 2: (7079632680 × 10) / 10000000000 = 70796326800 / 10000000000 = 7
- And so on...

Result: "1.5707963268"

### Part 6: Main Program

```soma
(sin(0°) = ) >print
0 >deg_to_rad >compute_sin >format
() >print

(sin(30°) = ) >print
30 >deg_to_rad >compute_sin >format
() >print

) ... more angles ...
```

**Execution flow:**
1. Print label "sin(0°) = "
2. Push 0 onto AL
3. Execute deg_to_rad (converts 0° → 0 radians)
4. Execute compute_sin (computes sin(0) = 0)
5. Execute format (prints "0.0000000000")
6. Print newline
7. Repeat for other angles

---

## How It Works

### The Math

**Taylor Series for sin(x):**
```
sin(x) = x - x³/3! + x⁵/5! - x⁷/7! + x⁹/9! - ...
       = x - x³/6 + x⁵/120 - x⁷/5040 + x⁹/362880 - ...
```

**Iterative Formula:**
```
term₀ = x
term_{n+1} = -term_n × x² / ((2n+1)(2n+2))

For n=0: term₁ = -x × x² / (2×3) = -x³/6 ✓
For n=1: term₂ = -(-x³/6) × x² / (4×5) = x⁵/120 ✓
For n=2: term₃ = -(x⁵/120) × x² / (6×7) = -x⁷/5040 ✓
```

### The Scaling

**Why scale by 10^10?**
- Allows 10 decimal places of precision
- Large enough to minimize rounding errors
- Small enough to avoid integer overflow in intermediate calculations

**Scaling Rules:**
```
Addition/Subtraction: No adjustment needed
  (a×S) + (b×S) = (a+b)×S ✓

Multiplication: Divide by S
  (a×S) × (b×S) = (a×b)×S²
  → Divide by S to get (a×b)×S ✓

Division: No adjustment needed
  (a×S) / (b×S) = a/b ✓
  (a×S) / b = (a/b)×S ✓
```

### The Iteration

**Convergence:**
- Each term gets smaller (for |x| < π)
- Stop when |term| < 1000 (scaled)
- This represents |term| < 0.0000001 (unscaled)

**Typical iteration counts:**
- sin(0°): 1 iteration (term=0, immediate stop)
- sin(30°): 5 iterations
- sin(90°): 6-7 iterations

---

## Accuracy Analysis

### Results vs. Python math.sin()

| Angle | SOMA Output      | Python math.sin() | Error         |
|-------|------------------|-------------------|---------------|
| 0°    | 0.0000000000     | 0.0000000000      | 0.0000000000  |
| 30°   | 0.5000000010     | 0.5000000000      | +0.0000000010 |
| 45°   | 0.7071067814     | 0.7071067812      | +0.0000000002 |
| 60°   | 0.8660254037     | 0.8660254038      | -0.0000000001 |
| 90°   | 1.0000000010     | 1.0000000000      | +0.0000000010 |
| 180°  | 0.0000000000     | 0.0000000000      | 0.0000000000  |
| 270°  | -0.9999999995    | -1.0000000000     | +0.0000000005 |
| 360°  | 0.0000000012     | 0.0000000000      | +0.0000000012 |

### Error Sources

1. **π Approximation**
   - Using: 3.1415926536
   - Actual: 3.14159265358979...
   - Error: ~0.0000000001

2. **Integer Division Rounding**
   - Each `/` operation truncates
   - Example: 31 / 10 = 3 (not 3.1)
   - Accumulates over iterations

3. **Iteration Cutoff**
   - Stop at |term| < 1000 (scaled)
   - Remaining terms contribute ~0.0000001

**Total Error:** Typically < 0.00000002 (2 × 10^-8)

**Accuracy:** 9-10 decimal places

---

## Key Concepts

### 1. Store vs Register

**Store (Global):**
```soma
value !namespace.variable    ) Write
namespace.variable           ) Read
```
- Persistent across all blocks
- Used for: sin.x, sin.term, sin.sum, SCALE, etc.

**Register (Block-local):**
```soma
value !_.variable    ) Write
_.variable           ) Read
```
- Fresh and empty for each block execution
- Used for: temporary values in functions (_.a, _.b)

**Design Choice:** This program uses Store for iteration state (simpler than Register context-passing)

### 2. The >chain Idiom

**Pattern:**
```soma
{
  ) ... do work ...
  condition
    { block_name }    ) Continue
    { Nil }           ) Stop
  >ifelse
} !block_name

>block_name >chain
```

**How it works:**
1. Execute block
2. Block returns either itself (continue) or Nil (stop)
3. >chain executes returned value
4. If Block: goto step 1
5. If Nil: stop

**Why it's powerful:**
- No explicit loop counter needed
- Condition embedded in iteration
- Tail-call optimized (no stack growth)

### 3. Scaled Integer Arithmetic

**Core Idea:** Simulate decimals using integers

```soma
) Store 3.14159 as 31415900000 (scaled by 10^10)
31415900000 !pi_scaled

) Multiplication requires scale correction
pi_scaled 2 >*     ) 62831800000 (still scaled by 10^10)
                   ) Represents 6.283018 ✓

) But scaled × scaled needs correction
pi_scaled pi_scaled >*    ) 987...000... (scaled by 10^20!)
SCALE >/                  ) Divide to get back to 10^10
                          ) Represents π² ≈ 9.8696... ✓
```

**Critical Rules:**
- ✓ Add/subtract scaled numbers directly
- ✓ Divide scaled by unscaled directly
- ✗ Multiply scaled × scaled MUST divide by SCALE after
- ✗ Divide scaled by scaled gives unscaled (rarely wanted)

### 4. Block Execution

**Three ways to execute:**

```soma
{ code } !block      ) Store block

>block               ) Execute from Store
block >chain         ) Execute from Store
>{ code }            ) Execute literal immediately
```

**When to use each:**
- `>block`: Execute once, normal function call
- `block >chain`: Iteration pattern, block returns block or Nil
- `>{ code }`: Inline execution, cleaner than `{ code } >^`

---

## Customization

### Adding More Angles

Edit `soma_sin_calculator.soma` and add:

```soma
(sin(45.5°) = ) >print
455 10 >/ >deg_to_rad >compute_sin >format
() >print
```

Note: Input is integer, so 45.5° = 455/10

### Improving Accuracy

Increase precision:

```soma
100000000000 !SCALE          ) 10^11 instead of 10^10
314159265359 !PI_SCALED      ) More digits of π
100 !MIN_TERM                ) Tighter convergence
```

### Computing Other Functions

The same techniques work for:
- **cos(x)**: cos(x) = 1 - x²/2! + x⁴/4! - x⁶/6! + ...
- **e^x**: e^x = 1 + x + x²/2! + x³/3! + x⁴/4! + ...
- **ln(1+x)**: ln(1+x) = x - x²/2 + x³/3 - x⁴/4 + ... (for |x| < 1)

---

## Further Reading

### SOMA Documentation
- **Idioms**: `../../docs/09-idioms.md` - Context-passing patterns
- **Control Flow**: `../../docs/05-control-flow.md` - >chain details
- **Builtins**: `../../docs/06-builtins.md` - All primitive operations
- **Examples**: `../../docs/08-examples.md` - More code examples

### Mathematical Background
- Taylor Series: https://en.wikipedia.org/wiki/Taylor_series
- Fixed-Point Arithmetic: https://en.wikipedia.org/wiki/Fixed-point_arithmetic
- Sine Function: https://en.wikipedia.org/wiki/Sine_and_cosine

### SOMA Philosophy
- **Explicit over implicit**: State mutation is visible (`!` prefix)
- **Execution is explicit**: Code doesn't run unless you use `>`
- **Minimal primitives**: Everything built from small set of operations
- **Code as data**: Blocks are first-class values

---

## Troubleshooting

### "Module not found" error
```bash
# Make sure you're in the SOMA repo root:
cd /path/to/soma
python3 examples/sin_calculator/run_soma_sin.py
```

### Output prints one character per line
This is expected! SOMA's `>print` outputs each character individually. This is a feature of the SOMA VM.

### Want quiet output?
Modify `run_soma_sin.py` to redirect output:

```python
import io
from contextlib import redirect_stdout

f = io.StringIO()
with redirect_stdout(f):
    al = run_soma_program(full_code)
output = f.getvalue()
print(output)  # Now you can process it
```

---

## License

Part of the SOMA project. See repository root for license details.

---

**Questions or improvements?** Check the main SOMA documentation or contribute to the repository!
