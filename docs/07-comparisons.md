SOMA Language Comparisons                                    SOMA-COMPARISONS
Emergent Macros and Computational Models                         20 Nov 2025
Category: Informational




1.  INTRODUCTION
----------------

SOMA (State-Oriented Machine Algebra) occupies a unique position in the
landscape of programming languages. It is neither functional nor imperative
in the traditional sense, yet it achieves capabilities found in both
paradigms through fundamentally different means.

This document compares SOMA to five influential computational models and
languages, with particular emphasis on how SOMA achieves macro-like behavior
without requiring a macro system. The comparisons are:

   1. Common Lisp — emergent macros vs syntactic extension
   2. Forth — stack orientation vs state transformation
   3. Haskell — explicit state vs monadic abstraction
   4. Lambda Calculus — execution vs reduction
   5. Actor Model — shared state vs message passing

Each comparison is code-heavy and demonstrates the fundamental semantic
differences between SOMA and these well-established models.




2.  COMMON LISP: EMERGENT MACROS
---------------------------------

This is the most critical comparison for understanding SOMA's design.

Common Lisp achieves user-defined syntax through macros. SOMA achieves
equivalent power through blocks, >Choose, and >Chain—with no special
compile-time phase.


2.1  The Lisp Macro System

Common Lisp macros are functions that execute at compile time and return
code. They allow programmers to extend the language's syntax.

Example: Implementing WHEN

```lisp
; Common Lisp macro definition
(defmacro when (condition &body body)
  `(if ,condition
       (progn ,@body)))

; Usage
(when (> x 10)
  (print "large")
  (print "value"))

; Expands to:
(if (> x 10)
    (progn
      (print "large")
      (print "value")))
```

The macro system requires:

   * A reader that parses source into S-expressions
   * A macro expander that runs macros at compile time
   * A code walker that performs substitution
   * A compiler that processes the expanded code

Crucially, macros are **meta-level**. They do not execute—they generate code
that executes.


2.2  SOMA's Emergent Macro Behavior

SOMA has no macro system. No compile-time phase. No code generation.

Yet SOMA achieves the same capability through first-class blocks and
explicit control flow.

Example: Implementing WHEN

```soma
{ >dup { >drop } >swap >Choose >Chain } !when

; Usage
x 10 >> { "large" >print "value" >print } >when
```

How it works:

   1. >dup duplicates the boolean condition
   2. { >drop } is the "false branch" (discard the block)
   3. >swap reorders: [block, bool, drop-block]
   4. >Choose executes drop-block if false, else executes the body block
   5. >Chain executes whatever block was chosen

**This is not a macro. It is a block.**

No code is generated. No expansion occurs. The `when` block transforms
state at runtime, selecting which block to execute based on the AL contents.


2.3  The `^` Operator: User-Defined FUNCALL

The most powerful demonstration of SOMA's macro-like capabilities is the
user-defined "execute top of AL" operator:

```soma
{ !_ >_ } !^
```

This two-token block creates an operator equivalent to Lisp's FUNCALL or
Forth's EXECUTE—but it's **user-defined**, not a language primitive.

Example usage:

```soma
(Cats) print >^     ) Prints 'Cats'
```

**Execution trace:**

   1. `(Cats)` → AL = ["Cats"]
   2. `print` → AL = ["Cats", print_block]
   3. `>^` → executes block at "^", which is `{ !_ >_ }`
      - Block executes with fresh Register:
        - `!_` → pops print_block from AL, stores at register root `_`
        - `>_` → reads register root value and **executes it** (the print_block)
        - Print block pops "Cats" and prints it

**Output:** `Cats`

This demonstrates the key insight: **`>path` enables macro-like behavior**.

The `>` prefix modifier reads the value at a path AND executes it. This
atomic operation works with:

   * Store paths: `>print`, `>my_func`, `>^`
   * Register paths: `>_`, `>_.action`, `>_.self`

Because blocks can store and execute other blocks via `>path`, users can
define execution patterns that look indistinguishable from language features.


2.4  How `>path` Enables Macros Without a Macro System

Common Lisp requires macros because:

   * Functions evaluate their arguments before execution
   * Control structures must prevent evaluation of branches not taken
   * This requires compile-time code transformation

SOMA requires no macro system because:

   * Blocks are unevaluated values until explicitly executed
   * Passing a block to another block does not execute it
   * Execution only occurs via `>Chain`, `>Choose`, or `>path`

The `>path` operator is the key. It makes execution **first-class**:

```soma
print           ) Pushes the print block onto AL (it's a value)
>print          ) Executes the print block (it's an operation)
```

This means control structures can be defined as blocks that choose whether
to execute their arguments:

```soma
) Define IF/ELSE
{ >swap >Choose } !if_else

) Use it exactly like a built-in
x 0 >== { "zero" >print } { "non-zero" >print } >if_else
```

The `if_else` block is not syntactically privileged. It's just a block stored
in the Store. It can be redefined, inspected, passed as a value, or deleted.


2.5  Side-by-Side: IF / ELSE

Common Lisp:

```lisp
(defmacro my-if (test then else)
  `(cond (,test ,then)
         (t ,else)))

(my-if (zerop x)
  (print "zero")
  (print "non-zero"))
```

SOMA:

```soma
{ >swap >Choose } !my-if

x 0 >== { "zero" >print } { "non-zero" >print } >my-if
```

The SOMA version is **not** syntactically privileged. It's a block stored in
the Store. It can be redefined, inspected, passed as a value, or deleted.

Lisp macros, once defined, become part of the syntax until redefined.
SOMA blocks remain values.


2.6  UNLESS: Condition Negation

Common Lisp:

```lisp
(defmacro unless (condition &body body)
  `(if (not ,condition)
       (progn ,@body)))

(unless (file-exists-p "config.txt")
  (create-default-config))
```

SOMA:

```soma
{ >swap {} >swap >Choose >Chain } !unless

config.exists False >== { >create-default-config } >unless
```

Decomposition:

   * >swap: reorder [block, bool] → [bool, block]
   * {}: push empty block (the "do nothing" branch)
   * >swap: reorder [bool, block, {}] → [bool, {}, block]
   * >Choose: if bool is True, execute {}; else execute block
   * >Chain: execute the chosen block


2.7  WHILE: Looping Constructs

Common Lisp:

```lisp
(defmacro while (condition &body body)
  (let ((loop-tag (gensym)))
    `(tagbody
       ,loop-tag
       (when ,condition
         ,@body
         (go ,loop-tag)))))

(while (< counter 10)
  (print counter)
  (incf counter))
```

This requires TAGBODY and GO—non-local jumps.

SOMA:

```soma
{
  !_.body
  !_.test
  {
    _.test >Chain
    { _.body >Chain _.self }
    {}
    >Choose
  }
} !while

{ counter 10 >< } !cond
{ counter >print counter 1 >+ !counter _.self } !body
cond body >while >Chain
```

More concisely:

```soma
{
  !_.body
  !_.test
  {
    _.test >Chain
    { _.body >Chain _.self }
    {}
    >Choose
  }
} !while
```

Here, the while block:

   1. Stores the test and body blocks in the register
   2. Constructs a self-referencing loop block
   3. Returns the loop block for >Chain to execute

No jumps. No labels. No macro expansion. Just blocks referring to blocks.


2.8  Higher-Order Functions Using `>path`

The `>path` operator enables higher-order function patterns:

Example: APPLY

```soma
{ !_.x !_.f _.x >_.f } !apply
42 increment >apply     ) Apply increment to 42
```

**Execution:**
   1. `42` → AL = [42]
   2. `increment` → AL = [42, increment_block]
   3. `>apply` → executes apply block:
      - `!_.x` → stores 42 in register
      - `!_.f` → stores increment_block in register
      - `_.x` → AL = [42]
      - `>_.f` → executes increment_block with 42 on AL

Example: TWICE (execute a block twice)

```soma
{ !_.f >_.f >_.f } !twice
{ "Hello" >print } >twice     ) Prints "Hello" twice
```

Example: CALL-WITH (execute with argument)

```soma
{ !_.arg !_.func _.arg >_.func } !call_with
42 square >call_with     ) Squares 42
```

These look like **language features** but they're **user-defined blocks**
using `>path` semantics.


2.9  Dispatch Tables Using `>path`

Dispatch tables become trivial with `>path`:

```soma
) Define handlers
{ "Adding..." >print } !handlers.add
{ "Subtracting..." >print } !handlers.sub
{ "Multiplying..." >print } !handlers.mul

) Dispatch based on operation
"add" !op
op "handlers." >swap >concat >Store-read >^     ) Executes handlers.add
```

More sophisticated dispatching:

```soma
{
  !_.op
  _.op "add" >== { 10 20 >+ >print } !_.actions.add
  _.op "mul" >== { 10 20 >* >print } !_.actions.mul

  _.op "_.actions." >swap >concat >Register-read >^
} !dispatch

"add" >dispatch     ) Executes add operation
"mul" >dispatch     ) Executes mul operation
```

The `>^` pattern (execute AL top) enables dynamic dispatch without any
special language support.


2.10  User-Defined Control That Looks Like Built-ins

Because blocks can execute blocks via `>path`, user-defined control
structures are indistinguishable from built-ins:

```soma
) Define control primitives
{ !_ >_ } !^                              ) Execute AL top
{ !_.body !_.test _.test { >_.body _.self } { } >Choose } !while
{ !_.else !_.then !_.cond _.cond { >_.then } { >_.else } >Choose >Chain } !ifelse

) Use them exactly like language features
0 !counter
{ counter 10 >< } { counter 1 >+ !counter } >while     ) Count to 10
counter 5 >> { "big" >print } { "small" >print } >ifelse
```

These control structures:

   * Have no special syntax
   * Are stored as regular blocks in the Store
   * Can be redefined or removed
   * Work via `>path` execution

This is **macro-like power without macros**.


2.11  Macro Hygiene and Capture

Common Lisp macros face variable capture problems:

```lisp
; Bad macro: captures 'it'
(defmacro my-when (test &body body)
  `(let ((it ,test))
     (if it
         (progn ,@body))))

; User code accidentally captures 'it'
(let ((it 5))
  (my-when (> x 10)
    (print it)))  ; Prints the test result, not 5
```

Hygiene requires gensyms or packages.

SOMA has no capture problem because:

   * Blocks reference Store or Register paths explicitly
   * Underscore-prefixed paths are Register-local
   * No substitution occurs—only state transformation

Example:

```soma
{
  !_.it
  _.it { >print } {} >Choose
} !my-when

5 !it
x 10 >> >my-when  ; 'it' in the Store is unaffected
```

The Register's `_.it` is local to the block execution. The Store's `it` is
untouched.


2.12  Performance: Compile-Time vs Runtime

Lisp Macros:

   * Expand once at compile time
   * Generate static code
   * Zero runtime overhead for expansion
   * Requires separate compilation phase

SOMA Blocks:

   * Execute at runtime
   * Select blocks dynamically
   * Overhead = block selection + >Chain dispatch
   * No separate compilation phase needed

SOMA trades macro expansion overhead for simplicity. Blocks are not "faster"
than Lisp macros—they are **simpler**. The entire computational model is
runtime state transformation.


2.13  Expressiveness Comparison

What Lisp macros can do that SOMA cannot:

   * Perform arbitrary computation on syntax trees at compile time
   * Generate optimized code based on static analysis
   * Implement reader macros that change the parser

What SOMA blocks can do that Lisp macros cannot:

   * Be dynamically redefined at runtime without recompilation
   * Be stored in data structures as first-class values
   * Be introspected as part of the Store
   * Execute with different semantics in different threads

Both are Turing-complete. Both allow user-defined control structures. The
difference is **when** and **how** the extension occurs.


2.14  Summary: Macros Without a Macro System

SOMA demonstrates that **macro-like behavior emerges from semantics**, not
syntax.

Common Lisp:
   * Requires defmacro, backquote, comma, splice
   * Operates at the meta-level (code generating code)
   * Requires multi-phase execution model

SOMA:
   * Requires only blocks, >Choose, >Chain, and `>path`
   * Operates at the value level (blocks selecting blocks)
   * Single-phase execution model

The profound insight:

   **If blocks are first-class and execution is explicit via `>path`, you
   don't need macros—control structures ARE blocks.**

The `>` prefix modifier makes execution first-class. The `^` operator
demonstrates that users can define execution patterns that look like
language primitives but are just blocks using `>path` semantics.




3.  FORTH: STACK ORIENTATION VS STATE TRANSFORMATION
-----------------------------------------------------

Forth and SOMA both use stack-based value passing, but their execution
models differ fundamentally.


3.1  Similarities

Both languages:

   * Use a stack (or AL) for data passing
   * Have minimal syntax
   * Execute left-to-right
   * Expose low-level machine operations
   * Are dynamically typed
   * Allow defining new "words" or blocks


3.2  Differences in Memory Model

Forth:

   * Flat memory space
   * Words can read/write arbitrary memory addresses
   * Dictionary is a linked list of word definitions
   * Variables are memory locations

SOMA:

   * Hierarchical Store (graph of Cells)
   * Paths reference named Cells, not addresses
   * No direct memory pointers
   * Variables are Cells with identity


3.3  Differences in Execution Model

Forth:

   * Words execute immediately when parsed (interpretation)
   * Colon definitions compile sequences of word addresses
   * Control structures (IF, THEN) compile jump addresses
   * Execution = following a threaded code pointer chain

SOMA:

   * Tokens push values or transform state
   * Blocks are not executed when read
   * Control = block selection via >Choose / >Chain
   * Execution = state transformation, no jumps


3.4  Example: Conditional Execution

Forth:

```forth
: test-value ( n -- )
  DUP 10 > IF
    ." Greater than 10"
  ELSE
    ." Not greater"
  THEN
  DROP ;

15 test-value
```

The IF...THEN structure compiles to conditional jumps.

SOMA:

```soma
{
  !_.n
  _.n 10 >>
  { "Greater than 10" >print }
  { "Not greater" >print }
  >Choose
} !test-value

15 >test-value
```

No jumps are compiled. >Choose selects which block executes.


3.5  Example: Looping

Forth:

```forth
: count-up ( n -- )
  0 DO
    I .
  LOOP ;

10 count-up
```

DO...LOOP compiles to loop control structures with index management.

SOMA:

```soma
{
  !_.max
  0 !_.i
  {
    _.i _.max ><
    {
      _.i >print
      _.i 1 >+ !_.i
      _.self
    }
    {}
    >Choose
  }
} !count-up

10 >count-up >Chain
```

The loop is a self-referencing block, not a compiled construct.


3.6  The EXECUTE Primitive vs User-Defined `^`

This is a critical difference between Forth and SOMA.

Forth has a built-in primitive called EXECUTE:

```forth
: GREET ( -- ) ." Hello" ;

' GREET    \ Get execution token for GREET
EXECUTE    \ Execute it
```

**EXECUTE is a language primitive.** It's built into Forth—you cannot
implement it yourself. It pops an execution token from the stack and
executes it.

SOMA has **no built-in execute-from-AL operation**. But you can define it:

```soma
{ !_ >_ } !^
```

Now `>^` behaves exactly like Forth's EXECUTE:

```soma
{ "Hello" >print } !greet

greet >^        ) Execute the block on AL top
```

**Comparison:**

Forth:
   * EXECUTE is a built-in primitive
   * Cannot be redefined or removed
   * Special syntax: `'` to get execution tokens

SOMA:
   * `^` is a user-defined block
   * Can be redefined or removed
   * No special syntax: just `{ !_ >_ } !^`

**Why this matters:**

In Forth, EXECUTE is a fundamental operation. In SOMA, it's **emergent
behavior** from two primitives:

   1. `!_` — store at register root
   2. `>_` — execute from register root

This demonstrates SOMA's core philosophy: **powerful operations emerge from
simple primitives**.

Example usage comparison:

```forth
\ Forth
: TWICE ( xt -- ) DUP EXECUTE EXECUTE ;
' GREET TWICE
```

```soma
) SOMA
{ !_.f >_.f >_.f } !twice
greet >twice
```

Both achieve the same result, but SOMA's version uses user-defined
execution (`>_.f`), while Forth uses the built-in EXECUTE.


3.7  Key Distinction: Self-Executing vs First-Class

In Forth, defining a word immediately makes it executable. The word is an
entry in the dictionary that points to machine code or threaded code.

In SOMA, defining a block stores it as a value. It does not self-execute.
Execution requires explicit `>path` or another invocation mechanism.

Example:

Forth:

```forth
: greet ." Hello" ;
greet  \ Executes immediately
```

SOMA:

```soma
{ "Hello" >print } !greet
greet  \ Pushes the block onto AL, does NOT execute
>greet \ Executes the block
```


3.8  Summary: Forth vs SOMA

Similarities:
   * Stack-based value passing
   * Minimal, explicit execution model
   * User-extensible

Differences:
   * Forth: Memory-mapped, self-executing words, compiled control, built-in EXECUTE
   * SOMA: Hierarchical Store, first-class blocks, algebraic control, user-defined `^`

SOMA is not "Forth with a Store." It is a different computational model that
happens to use a stack-like value conduit.

The key insight: **Forth's EXECUTE primitive is emergent behavior in SOMA**,
defined as `{ !_ >_ } !^`. This shows how SOMA achieves powerful semantics
through composition of simple primitives.




4.  HASKELL: STATE VS MONADIC ABSTRACTION
------------------------------------------

Haskell and SOMA represent opposite approaches to state.


4.1  Haskell's Philosophy

Haskell:
   * Starts with purity (no mutation)
   * Encodes state using the State monad
   * Hides state changes under type abstractions
   * Treats IO as a special effect type

SOMA:
   * Starts with mutation (state is primary)
   * State changes are direct Store operations
   * State is visible and explicit
   * All computation is "effectful"


4.2  Example: Stateful Counter

Haskell (using State monad):

```haskell
import Control.Monad.State

type Counter = State Int

increment :: Counter ()
increment = modify (+1)

getCount :: Counter Int
getCount = get

runCounter :: Counter Int
runCounter = do
  increment
  increment
  increment
  getCount

main = print $ evalState runCounter 0  -- prints 3
```

The state is threaded implicitly through the monadic bind (>>=).

SOMA:

```soma
0 !counter

{
  counter 1 >+ !counter
} !increment

{
  counter
} !getCount

>increment >increment >increment >getCount >print
```

State is in the Store. Mutations are explicit. No monad needed.


4.3  Example: Combining State and IO

Haskell:

```haskell
import Control.Monad.State

type App = StateT Int IO

runApp :: App ()
runApp = do
  modify (+1)
  count <- get
  liftIO $ putStrLn $ "Count: " ++ show count
  modify (+1)
  count2 <- get
  liftIO $ putStrLn $ "Count: " ++ show count2

main = evalStateT runApp 0
```

State and IO are layered via monad transformers.

SOMA:

```soma
0 !count

count 1 >+ !count
"Count: " count >to-string >concat >print

count 1 >+ !count
"Count: " count >to-string >concat >print
```

No layering needed. Everything is state. Printing is a state operation that
affects stdout.


4.4  The Philosophical Divide

Haskell asks:
   "How do we model mutable state in a pure language?"

SOMA asks:
   "How do we model computation as state transformation?"

Haskell simulates a machine using mathematical abstractions.
SOMA directly describes a machine.


4.5  Monads in SOMA?

SOMA blocks are, in a sense, monadic:

   (AL, Store) -> (AL', Store')

This is isomorphic to the State monad. But SOMA does not abstract it. There
is no bind operator, no return, no do-notation. Blocks simply transform
state, and sequencing is linear token execution.

In Haskell terms, every SOMA program is already "inside the IO/State monad."


4.6  Summary: Haskell vs SOMA

Haskell:
   * Hides state in type abstractions
   * Uses monads to sequence effects
   * Separates pure and impure code

SOMA:
   * Exposes state as the computational foundation
   * Uses >Chain to sequence blocks
   * Makes no purity distinction

Haskell models mutation. SOMA is mutation.




5.  LAMBDA CALCULUS: EXECUTION VS REDUCTION
--------------------------------------------

Lambda Calculus and SOMA are fundamentally incompatible models.


5.1  Lambda Calculus

The Lambda Calculus is a symbolic rewriting system based on:

   * Abstraction: λx. E
   * Application: (E₁ E₂)
   * Substitution: β-reduction

Execution = rewriting expressions until normal form is reached (if possible).

Example:

   (λx. x + 1) 5

   β-reduces to:

   5 + 1

   reduces to:

   6


5.2  SOMA

SOMA is a state transformation system based on:

   * Accumulator List (AL)
   * Store
   * Tokens that mutate state

Execution = sequential state transitions.

Example:

   5 1 >+

   State₀: AL = [], Store = {}
   State₁: AL = [5], Store = {}
   State₂: AL = [1, 5], Store = {}
   State₃: AL = [6], Store = {}


5.3  No Substitution

Lambda Calculus uses substitution:

   (λx. x * x) (3 + 2)

   Step 1: Reduce argument:
      3 + 2 → 5

   Step 2: Substitute:
      (λx. x * x) 5 → 5 * 5 → 25

SOMA uses no substitution. Variables are Store/Register paths. Reading a
path retrieves the current Cell value:

   3 2 >+ !x
   x x >* >print  ; Prints 25

No term is substituted. The path `x` resolves to 5 at the time of reading.


5.4  Programs Run, They Don't Reduce

Lambda Calculus:
   * Expressions reduce to values
   * Reduction may not terminate
   * Result = normal form (if it exists)

SOMA:
   * Programs execute token by token
   * Execution may not terminate (infinite >Chain)
   * Result = final AL and Store state


5.5  Example: Factorial

Lambda Calculus (Y combinator):

```
FACT = Y (λf. λn. IF (= n 0) 1 (* n (f (- n 1))))

FACT 5
```

Reduction proceeds via β-reduction until a normal form is reached.

SOMA:

```soma
{
  !_.n
  _.n 0 >==
  { 1 }
  { _.n _.n 1 >- >fact >* }
  >Choose
} !fact

5 >fact >Chain >print
```

Execution proceeds via >Chain repeatedly selecting blocks.


5.6  Summary: LC vs SOMA

Lambda Calculus:
   * Stateless
   * Symbolic
   * Reduction-based
   * Defines computation as rewriting

SOMA:
   * Stateful
   * Operational
   * Execution-based
   * Defines computation as transformation

LC asks: "What does this expression mean?"
SOMA asks: "What does this program do?"




6.  ACTOR MODEL: SHARED STATE VS MESSAGE PASSING
-------------------------------------------------

The Actor Model and SOMA represent opposite concurrency philosophies.


6.1  Actor Model

Actors:
   * Have private state
   * Communicate via asynchronous messages
   * Process one message at a time
   * Create new actors dynamically
   * No shared memory

Example (conceptual):

```
actor Counter {
  state: count = 0

  on Increment:
    count := count + 1

  on GetCount:
    reply count
}
```


6.2  SOMA Threads

SOMA threads:
   * Have private AL
   * Share the Store
   * Execute Blocks independently
   * Can mutate shared Cells

Example:

```soma
0 !counter

{ counter 1 >+ !counter } >thread
{ counter 1 >+ !counter } >thread
{ counter 1 >+ !counter } >thread
```

All three threads mutate the same Cell. No isolation. No message passing.


6.3  Synchronization

Actors:
   * Mailbox queues prevent race conditions
   * Single-threaded message processing guarantees atomicity

SOMA:
   * No built-in synchronization
   * Races are possible
   * Discipline is the programmer's responsibility


6.4  Example: Parallel Accumulation

Actors:

```
actor Accumulator {
  state: total = 0

  on Add(value):
    total := total + value

  on GetTotal:
    reply total
}

spawn worker1: send Add(10) to Accumulator
spawn worker2: send Add(20) to Accumulator
spawn worker3: send Add(30) to Accumulator
```

SOMA:

```soma
0 !total

{ total 10 >+ !total } >thread
{ total 20 >+ !total } >thread
{ total 30 >+ !total } >thread
```

If implemented without atomic writes, the result may be non-deterministic.


6.5  Design Philosophy

Actor Model:
   * Isolates state to prevent sharing bugs
   * Uses message queues as synchronization mechanism
   * Scales to distributed systems naturally

SOMA:
   * Exposes shared state directly
   * Provides no synchronization primitives
   * Assumes programmer will coordinate manually


6.6  Summary: Actors vs SOMA

Actors:
   * Private state
   * Message passing
   * Enforced isolation

SOMA:
   * Shared Store
   * Direct mutation
   * No isolation

Actors prevent concurrency bugs by design.
SOMA leaves concurrency discipline to the programmer.




7.  CONCLUSION
--------------

SOMA occupies a unique position among computational models:

   * Like Lisp: Achieves syntactic extension (but without macros, using `>path`)
   * Like Forth: Uses stack-based execution (but with structured state and user-defined EXECUTE)
   * Like Haskell: Manages state (but explicitly, not monadically)
   * Like Lambda Calculus: Is a formal model (but of execution, not reduction)
   * Like Actors: Supports concurrency (but via shared state, not isolation)

SOMA is not an improvement over these models. It is a **reframing**. It asks:

   "What if we stopped abstracting away the machine and described it directly?"

The result is a language where:

   * Mutation is the foundation, not a problem to solve
   * Blocks are data, and data determines control
   * Macros emerge from `>path` semantics, not syntax
   * State is visible, not hidden
   * Execution is observable, not symbolic

The key insights:

   1. **The `>path` operator makes execution first-class.** Blocks can
      execute blocks, enabling user-defined control structures.

   2. **The `^` operator (`{ !_ >_ } !^`) demonstrates emergent behavior.**
      What Forth provides as EXECUTE and Lisp as FUNCALL emerges from two
      primitives: store and execute.

   3. **Macro-like behavior emerges from semantics.** Because blocks are
      values and execution is explicit, control structures are just blocks
      that choose whether to execute their arguments.

SOMA is a machine algebra. It describes what machines **do**, not what
expressions **mean**.


_______________________________________________________________________
