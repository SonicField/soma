SOMA v1.0 Language Specification                                 SOMA-1.0
State-Oriented Machine Algebra                                 16 Nov 2025
Category: Informational



#  INTRODUCTION
##  What is SOMA?
SOMA (State-Oriented Machine Algebra) is a computational model and language which treats programs as explicit state-transforming machines. SOMA does not reduce expressions. Instead, it reflects the operational and dynamic nature of computation as it unfolds over time. SOMA is not a calculus. It is a semantic algebra over mutable state.

A SOMA program consists of tokens that transform the machine state.

There are three primary state structures:
* The Accumulator List (AL) -- a universal linear, stack-like value conduit
* The Store -- a universal hierarchical graph of identity-bearing cells
* The Register -- an execution localised hierarchical graph of identity-bearing cells

There is one execution structure - the block:
  - The block -- a linear sequence of instructions.
  - Blocks are first class - a block is a value which can be put in the store of the register.
  - Builtins are blocks - blocks can be implemented outside of SOMA (e.g. in C or Python) but will are 'just blocks' in SOMA.
  - Operators are blocks - SOMA does not explicitly implement most operators in syntax.

Execution is strictly linear, explicit, and introspectable. SOMA makes no attempt to hide mutation or state under abstraction.

## Design Philosophy
SOMA is based on the following principles:

* State is fundamental.
 - SOMA rejects the idea that mutable state is impurity.

* Execution is dynamic, not symbolic.
 - SOMA models computation step-by-step, through state evolution.

* Control is explicit.
 - There are no hidden control stacks, continuations, or exceptions.

* Structure is visible.
 - Memory exists as a graph of named and aliasable cells.

* Blocks are not functions.
 - They have no arity and do not return values. They are state transformers.

* Minimal but complete.
 - Features exist only where they serve machine-level clarity.

SOMA is not designed for theorem proving. It is intended for reasoning by execution, observation, and experiment.

## Notes for programmers coming from more traditional languages
* There is no explicit compatuation stack.
  - There is no 'return path' or 'stack unwinding'.
  - There is no exception path. Exceptions must be handled forward.
  - There is no shadowning or hierarhical scoping.
* There is no explicit handling of recursion.
  - SOMA does support recursion as an emergent property of its execution flow.
  - Recusion is not a first class concept.
  - There is no optimisation mandated for recursion (TOC etc.)
* There is no explicit looping or brnanching system.
  - SOMA is Turing Complete via execution block choice.
  - SOMA achieves repetition via eecution block chaining.

## SOMA vs Calculus
Functional languages begin with a calculus and add machinery to simulate mutable reality. For example, Haskell expresses state via IO monads and effect types.

SOMA takes the opposite approach:
* It begins with the machine.
* It exposes state directly.
* It treats computation as state evolution.

Where a calculus hides mutation under abstraction, SOMA expresses mutation as the primary semantic domain.

## Comparison With Related Systems
* Forth:
  - SOMA has structured memory and block semantics that do not rely on self-consuming execution. Control is algebraic rather than syntactic.
* Haskell:
  - Haskell simulates state using monads; SOMA directly expresses it. Haskell abstracts away machine steps; SOMA reveals them. Haskell is based on a calculus; SOMA is based on an algebra.
* Turing Machines:
  - A Turing Machine manipulates one symbol at a time. SOMA can access structured state at arbitrary depth. TM state is implicit; SOMA state is explicit and inspectable.

## SOMA as a Machine Algebra

SOMA defines:
* A space of values (including references and blocks)
* A structured memory model (the Store and Register)
* A linear execution conduit (the AL)
* A set of composable state transformations

These define an algebra over the machine state:

      (AL, Store)  -->  (AL, Store)

This is isomorphic to the state monad, but without abstraction, type theory, or purity constraints.

## Execution Model Overview
SOMA executes by reading tokens left to right. Each token may be:
* A literal value
* A path into the Store
* A path into the Register
* A block / built-in operation

Each token transforms the machine state. No computation is hidden under symbolic reduction.

SOMA (as previously noted)  does not have:

* A call stack
* A return model
* Exceptions
* Implicit control structures

Control is expressed by passing blocks as values, selecting between them (>Choose), and chaining their execution (>Chain).

**SOMA programs do not reduce. They run.**

## Introductory Examples
### Hello world minimallty
```soma
"Hello world" >print
```
1. Push a string onto the AL
2. 'Send to' (execute) the block in the store under key 'print'

### Hello world with block, store and register
```soma
{ !_ "Hello " _ >concat >print } !say_hello
"world" >say_hello
```
1. Create a block.
  1.1 pop from the AL and put in the register
  1.2 push 'Hello' on the stack.
  1.3 push the value of the register in the stack
  1.5 send to concat which pops to strings and pushes the concatentation.
  1.6 send to print
2. Store that block in the key 'say_hello'
3. Push 'world'.
4. Send to the block we stred at 'say_hello'.

### Hello world with cell references and parenthetic strings
```soma
{ !_. "Hello " _.to_say >concat >_.how } !say_hello
(world) !words.to_say
print !words.how
words. >say_hello
```
1. Create a block.
  1.1 pop from the AL and put in the register by reference; this requests the popped value to be a CellReference.
  1.2 push 'Hello' on the stack.
  1.3 push the value of the register's key '_.to_say'.
  1.5 send to concat which pops to strings and pushes the concatentation.
  1.6 send to the value of the register's key '_.how'.
2. Store that block in the key 'say_hello'
3. Push 'world' defining work using parenthesis rather than quotes.
4. Store under the store key 'words.to_sa'.
5. Push the block stored under the key 'print'.
6. Pop and store that under the key 'words.how'.
7. Push the CellReference from the store key 'words'.
8. Send to the block at the store key 'say_hello'.

## Pathological - Register locality
```soma
1 >{_ 1 >+ !_} _ >print [ Register Not Set]
1 !_ >{_ >print}        [ Register Not Set]
```

## Why Store, AL & Registers
The next section defines the Store and Registers. For clarity we can explain here why we have the Store, Registers and the AL. Everything which SOMA does could be done with just the AL and the Store. Programming this environment was found to be very challenging and significantly reduced the clarity of the explanitory power of SOMA. For this reason, Registers were introduced to provide a minimal amount of flexibility without adding significant complexity, especially to the parsing/grammar rules.

# CORE CONCEPTS
## Overview

SOMA programs operate by transforming explicit machine state. The state of a SOMA machine consists of two primary components:
* The Accumulator List (AL)
* The Store
* The Registers

Execution consists of tokens acting upon these structures.

## Values
Values in SOMA are dynamic and may represent:
* Primitive literals (e.g. integers, strings, booleans)
* Cell references
* Blocks
* External objects ("Things")
* Nil
* Void

Values flow through the AL and may be stored in the Store.
Primitives are immutable.


## Cells

```
CellReference --> Cell --> Value
                       |-> Paths
```

1. A Cell is the fundamental unit of storage.
2. Cells have identity, independent of the values they contain.
3. Cells can be referenced by a CellReference.
4. CellReferences can be rooted in a Register or Store.
5. A Cell may contain any value other than Void.
6. Cell values can be an Value other than Void.

## The Store And Register
Registers and the Store are identical in every way other than scope.
* Store: Scope is for the entire eecuting program.
* Register: Scope is the execution of the currently executing block.
  - The current register is not attached to the block, it is attached to the execution of that block.
* Both the Store and Registers are idenitacally structured Value/Path graphs.
* They can share subgraphs and can be cyclic.

### Defining the Store
1. The Store is a graph which has a single root which does not require naming.
2. Tokens which do not represent any thing else (Values, Register paths etc) will be interpreted as paths in the Store relative to this single, universally visible, root.
3. Tokens which start ! and for which the rest of the token does not represent a Register path (i.e. any token starting ! and not !_) is interpreted as setting the Store.

### Defining the Current Register
1. A Register is a graph which has a single root in the currently executing block.
2. A Register cannot escape the execution of that block and will be destroyed after then end of that execution.
3. CellReferences in a Register can escape the local block execution.   
4. Tokens which do not represent any thing else (Values etc) and start _ will be interpreted as paths in the current Register relative to the currently executing root.
5. Tokens which start !_ are interpreted as setting the current Register.

### Notes on The Store and Registers
* **Registers, and alternative view:** If we were to create a unique identifier for every block and then use that in a path in the Store, we would have a system with almost identical semantics as Registers other than they would be directly accessible from outside their block. In this way we can see that Registers are a very minimal expantion of the SOMA execution model. 
* **Anonymous Graphs:** Graphs are made of Cells, Cells are referenced by CellReferences, CellReferences are Values; therefore Graphs can exist rooted in the AL, in other graphs etc. Graphs do not need to be rooted in the Register or Store.
* **Data Structures:** Graphs allow the creating of arbitrarily complex data structures in VSPL and bridge the gap from simple global mutation (like Forth) and fully structured languages (like C). Because blocks first class, graphs form a natural way of managing them and implement control flow (as does the AL).

**From this point on, when discussing the behaviour of the Store or Registers together we will refer to a Graph.**

## Graphs
1. A Graph is a hierarchical graph of Cells.
2. A CellReference referes to a Cell.
3. CellReferences are first class.
4. Paths refer to locations within this graph.
5. Paths are rooted either in a Register or the Store.

Example paths:
```soma
   a.b.c [A Store path]
   _.a.b.c [A Register path]
```

Example CellReference paths:
```soma
  a.b. [Reference to the Cell at a.b in the store]
  _.a.b. [Reference to the Cell at a.b in the current register]
```

If the Cell at "a.b" exists but "a.b.c" does not, referencing a.b.c is an error.

Graphs support structural mutation, aliasing, and deletion.

### Identity and Aliasing
1. Cell identity is preserved even when two paths refer to the same Cell. This allows shared state, pointer-like behavior, and structure reuse.
2. Aliasing is explicit.
  - A Cell may be replaced without modifying another that refers to the same value.
  - A Cell may be replaced without modifying another that refers to the same subpath.
3. A CellReference my be copied, replaced or deleted without change the Cell it references.

Examples:
```soma
[Value aliasing]
23 !a.b a.b !a.c 24 !a.b a.c >print [prints 23]
```

```soma
(hello) !a.b.c a.b. !x.y. [Cell with value 'hello' is referenced from x.y.c an a.b.c]
(goodby) !d.b.c d.b. !a.b. [Cell with value 'goodby' is referenced from d.b.c and a.b.c]
a.b.c >print [prints goodby]
x.y.c >print [prints hello]
```

### CellReferences Are First Class
Examples
```soma
(cat) !a.b.c        [Store the value cat into the Cell referenced from a.b.c]
a.b.c. !ref         [Store the cell reference at a.b.c into !ref by copy]
ref >{!_. (dog) !_} [Put the reference on the AL, store it into the reference for a register, set the Cell value to dog]
a.b.c >print        [Prints 'dog' because the cell value refered ot from a.b.c was set to dog in the sub-block]
```

CellReferences can:
1. Be placed on the AL.
2. Be placed in the value of a Cell.

Cellis cannot:
1. Be accessed or mutated unless in a graph.
2. Be accessed or mutated via their reference unless via a graph.

Example
```soma
[Start to create a linked list implementation using CellReferences]

{Nil !_.next Nil !_.value _.} !list_new_node         [Takes nothing from AL, forward new empty node]
{!_.value !_.node. _.value !_.node.value} !list_set  [Takes a value & node reference, sets node's the value]
{!_.node. >new_node !_.node.next} !list_append       [Takes node reference and appends new node]
{!_.node. _.node.next} !list_forward                 [Takes node reference and forwards next in list]
{!_.node. _,node.value} !list_get                    [Takes node reference and forwards its value]
```

## The Accumulator List (AL)

* The AL is a linear sequence of values, it is a stack in data structure behaviour terms but without the connotation of call/return semantics.
* Tokens push values onto the AL or consume values from it.
* The AL is LIFO to naturally conserve locality of reference without explicit scoping.

The AL:
1. Holds intermediate computation state
2. Is used to pass values into and out of Blocks
  - This can be used similarly to 'arguments' but has no arity or syntactic argument definition.
3. Serves as the decision context for >Choose and >Chain
4. Is the locus of dynamic behavior
5. Has strict LIFO behaviour
6. Cannot be accessed out of order by by offset
  - It is not possible to access the top-n entity on the stack, one can only access the top
7. Is the medium through which graph Cells or updated by value and reference.

Example:
```soma
1 2 3 4 5 [Stack now has five values and the top is 5]
print [prints 5, top is 4]
print [prints 4, top is 3]
print [prints 3, top is 2]
print [prints 2, top is 1]
print [prints 1, stack is empty]
print [Unrecoverable error, runtime exits]
```

Example:
```soma
[
  Push 'Bird' onto the AL
  Pop the AL into the Store cell at path 'animal'
]
"Bird" !animal

[
  Push "Bird" onto AL.
  Push block which prints onto AL
  Execute a block which:
    pops the printing block  
    executes the printing block which
      executes print which
        pops "Bird" and writes it to stdout
]
animal { >print } >{!to_do >to_do}
```

### Execution And The AL
1. It is not possible to directly execute an item on the AL.
2. AL items must be put into a Register or Store path to be executed.
3. Implementing a block to execute the top of the stack is trivial however.
4. Which is why SOMA does not implement syntax for it; SOMA aims to be minimal.

Example:
```soma
[Define a new operator like block to execute the top of the AL]
{!_ >_} !^

[Executes top of AL thus prints 'Hello world']
{(Hello world) >print} >^

[
Pushes 1, 2 and add onto the stack.
Executes + off the top of the stack which:
  Pops 2 and 1 off the stack and pushes 3.
Then pushes print.
Then executes the top of the stack which:
  Pops 3 and writes it to stdout.
]
1 2 + >^ print >^

[Which is the equivalent of this:]
1 2 >+ >print
```

>== HERE ==<

2.7  Blocks

   Blocks are enclosed in braces {} and represent executable behavior.

   Blocks:

      * Are first-class values
      * Are executed by consuming input values from the AL
      * Do not declare arity
      * Transform state and leave new values on the AL
      * Do not return in the traditional sense
      * Do not cause stack growth

   Blocks are not functions. They are state transformers that operate
   directly on the AL and the Store.


2.8  SOMA Program Model

   A SOMA program is a sequence of tokens. Each token:

      * Reads, writes, or transforms state
      * May push or pop values on 
      * May read or update the Store
      * May execute a Block
      * May alter the execution path via >Choose or >Chain

   There is no abstract syntax tree. No substitution rules. No hidden
   evaluation machinery.

   SOMA expresses operational semantics directly.


SOMA v1.0 Language Specification                                 SOMA-1.0
State-Oriented Machine Algebra                                 16 Nov 2025
Category: Informational



3.  LEXICAL RULES AND TOKENS
----------------------------

3.1  Overview

   A SOMA program is a sequence of textual tokens separated by
   whitespace. Tokens are processed left-to-right. There is no
   distinction between compile-time and run-time.


3.2  Whitespace

   Whitespace is required only to separate tokens. Any sequence of
   spaces, tabs, or newlines is treated as a delimiter. Whitespace
   has no semantic meaning.


3.3  Literals

   SOMA supports the following literal forms:

      Integer:
         0
         42
         -17

      String:
         "Hello"
         "A string with spaces"
         "Quotes may not appear inside"

      Boolean:
         True
         False

   Literal values are pushed onto the AL when encountered.


3.4  Path Syntax

   A path refers to a Cell in the Store. Paths consist of one or more
   dot-separated identifiers.

      a
      config.user.name
      session.active.flag

   Resolution semantics are defined in Section 6. Path tokens may
   appear anywhere a value is expected.


3.5  Trailing-Dot Path Syntax

   A path ending in a dot refers to a CellRef instead of a value.

      config.user.
      a.b.c.

   The trailing dot causes SOMA to resolve the location of the Cell,
   not its payload.


3.6  Locals

   Identifiers beginning with "_" refer to local cells that shadow
   Store paths.

      _tmp
      _accumulator
      _x

   Locals behave identically to Store cells but exist in a separate
   namespace. Locals are valid paths and support all Store operations.


3.7  Block Syntax

   Blocks are enclosed in braces:

      { token1 token2 token3 }

   Blocks are first-class values and may contain arbitrary tokens,
   including nested Blocks. A Block is not executed when read; it is
   pushed onto the AL as a value.


3.8  Built-in Words

   Built-in words begin with the ">" symbol:

      >print
      >dup
      >drop
      >+
      >Choose
      >Chain

   Built-ins are executed immediately and consume or produce AL
   values according to their definition.

   Built-ins are reserved and may not be redefined.


3.9  Reserved Symbols

   The following symbols have fixed meaning:

      {  }    Block delimiters
      !        Store write operator
      .        Path separator or trailing-dot CellRef operator
      _        Local namespace prefix
      >        Built-in prefix
      "        String literal delimiter

   These symbols may not be repurposed.


3.10  Invalid Tokens

   A token is invalid if:

      * It violates literal format rules
      * It violates path naming rules
      * It contains illegal characters
      * It conflicts with reserved words
      * It is syntactically incomplete

   Invalid tokens cause a fatal interpreter error.


3.11  ADVANCED STRING AND CHARACTER SET RULES
---------------------------------------------

3.11.1  Source Encoding

   All SOMA source code MUST be encoded in UTF-8. All tokens,
   including identifiers, strings, blocks, and comments, are sequences
   of UTF-8 code units. No other encoding is permitted.


3.11.2  Character Set

   SOMA accepts any valid Unicode scalar value in source input. However,
   Unicode usage is constrained by token type:

      * Identifiers are Unicode but restricted
      * Strings may contain arbitrary Unicode
      * Built-in names SHOULD be ASCII
      * The Store may contain Unicode paths, but ASCII is preferred


3.11.3  Identifier Rules (Unicode-Aware)

   Identifiers follow UAX #31 extended identifier syntax:

      Identifier ::= ID_Start ID_Continue*

   Where:

      ID_Start     ∈ { "_" } ∪ Unicode XID_Start
      ID_Continue  ∈ Unicode XID_Continue ∪ { "_" }

   Identifiers are normalized to Unicode NFC during lookup.


3.11.4  Strings: Two Forms

   SOMA supports two string literal syntaxes:

      1. Escaped Strings
         "Hello\nWorld"
         "Quotes \"require\" escapes"

      2. Raw Parenthesised Strings
         (A raw string containing "quotes" and no escapes)
         (Multiline
          text is allowed)

   Both forms evaluate to the same SOMA type:

      Str


3.11.5  Raw Parenthesised Strings

   A raw parenthesised string:

      ( content )

   Has the following properties:

      * Contains raw UTF-8
      * No escape sequences are processed
      * May span multiple lines
      * May contain quotes and punctuation
      * May NOT contain unmatched ")"
      * Produces a Str when evaluated


3.11.6  Escaped Strings

   Escaped strings are enclosed in double quotes:

      "text"
      "line\nbreak"
      "quote: \""

   Only the following escape sequences are required:

      \"   literal quote
      \\   literal backslash
      \n   newline
      \t   tab


3.11.7  Emoji and Full Unicode in Strings

   Strings may contain arbitrary Unicode, including emojis:

      ("🔧 tools ready 🔧")
      ("مرحبا")
      ("東京")

   The Str type is not restricted to ASCII.


3.11.8  No String → Code Execution

   SOMA does not define:

      * `eval`
      * runtime parsing
      * code injection via strings

   Strings are purely data.


3.11.9  Recommendations

   For maximum interoperability:

      * Built-in names SHOULD remain ASCII
      * Store paths SHOULD be ASCII unless user-facing
      * Identifiers SHOULD avoid emoji and mixed scripts
      * Strings MAY contain any text


3.11.10  Summary

   SOMA strings are UTF-8 sequences represented as:

      * Escaped double-quoted strings
      * Raw parenthesised strings

   Both produce Str values. SOMA allows full Unicode in text while
   preserving identifier rules and parser simplicity.



SOMA v1.0 Language Specification                                 SOMA-1.0
State-Oriented Machine Algebra                                 16 Nov 2025
Category: Informational



4.  VALUE TYPES
---------------

4.1  Overview

   SOMA is dynamically typed. All values are classified at runtime.
   Types do not determine evaluation order; they determine behavior
   when a value is consumed by a token or written to the Store.

   All values may be passed through the AL, bound to paths, stored
   in Cells, and introspected subject to their meaning.


4.2  Integer

   A signed integer value. Integers may be pushed as literals and
   consumed by arithmetic built-ins (e.g. >+, >-, >*, >/).


4.3  String

   A sequence of characters enclosed in double quotes. Strings are
   immutable values. String built-ins provide concatenation and
   comparison behavior.


4.4  Boolean

   Boolean values are:

      True
      False

   They are primarily consumed by >Choose and comparison operators.


4.5  Nil

   Nil indicates that the Cell exists but has no meaningful payload.
   Nil is not an error, nor does it indicate absence. It is a value.


4.6  Void

   Void is produced when a path refers to a Cell that does not exist.
   It is not a value stored in the Cell; it means the Cell itself is
   absent.

   Void is used in two contexts:

      * Failed path resolution
      * Structural deletion


4.7  Block

   A Block is a sequence of tokens enclosed in braces:

      { token token token }

   A Block:

      * Is a first-class value
      * May be pushed onto the AL
      * May be executed by placing it at the top of the AL and invoking
        a word that executes it
      * Does not declare arity
      * Does not return

   Blocks transform state but do not re-enter a caller context.


4.8  Thing

   A Thing is an opaque external object whose internal structure is
   not visible to SOMA. Examples include:

      * Lists
      * File handles
      * Foreign memory buffers
      * GPU objects

   A Thing may only be manipulated by built-in words that understand
   it. If no such built-ins exist, the Thing is inert.


4.9  CellRef

   A CellRef is produced by referring to a path with a trailing dot:

      a.b.
      config.setting.

   A CellRef is a reference to the Cell itself, not its payload.
   CellRef values may be written, aliased, or replaced.


4.10  Summary Table

   The following table summarizes SOMA value types:

      Type      Meaning
      --------  -----------------------------------------
      Int       Signed integer literal
      Str       String literal
      Bool      True or False
      Nil       Cell exists but carries no payload
      Void      Cell does not exist
      Block     Executable state transformer
      Thing     Opaque non-SOMA object
      CellRef   Reference to a Cell, not a value


SOMA v1.0 Language Specification                                 SOMA-1.0
State-Oriented Machine Algebra                                 16 Nov 2025
Category: Informational



5.  STORE SEMANTICS
-------------------

5.1  Overview

   The Store is a hierarchical graph of Cells that holds persistent
   program state. It is addressable via dot-separated paths. The Store
   constitutes the data memory of the SOMA machine.

   All mutation, aliasing, deletion, and structural reasoning within
   SOMA is performed through Store operations.


5.2  The Root Store

   The Store has a single root. All top-level paths are relative to
   this root.

   Example:

      a
      system
      config.user

   The entire Store is always reachable. There is no shadowing between
   top-level paths.


5.3  Cells and Payload

   Each named location in the Store refers to a Cell. A Cell has:

      * A persistent identity
      * A payload value (or Nil)
      * Zero or more child Cells

   Writing a value replaces the payload but preserves the Cell.


5.4  Nil vs Void

   SOMA makes a strict distinction between:

      Nil:
         The Cell exists, but carries no payload.
         Nil is a value.

      Void:
         The Cell does not exist.
         Void is not a stored value.

   This distinction allows SOMA to express:

      * Structure without data
      * Absence of structure
      * Structural deletion as an operation


5.5  Cell Creation

   A Cell is created automatically when a value is written to a path
   that did not previously exist.

   Example:

      42 !a.b.c

   If "a" and "a.b" exist but "a.b.c" does not, all missing Cells
   are created.


5.6  Structural Mutation

   A payload write:

      Val !a.b.c

   Sets the payload of Cell "a.b.c" to Val.

   A structural replacement:

      Val !a.b.c.

   Replaces the entire Cell at "a.b.c" with a new Cell whose payload
   is Val. Any child Cells are discarded.


5.7  Aliasing

   Two paths may refer to the same Cell. This is a structural alias.

   If:

      a.b.
      c.d.

   refer to the same Cell, then:

      99 !c.d

   will also update the payload of a.b.

   Aliasing does not copy values. It shares identity.


5.8  Structural Deletion

   A Cell may be removed entirely:

      Void !a.b.c.

   If the Cell does not exist, no action is taken. If it exists, both
   the Cell and its subtree are removed. Aliases are unaffected unless
   they pointed to the deleted Cell.


5.9  Lifetime and Reachability

   SOMA does not define automatic garbage collection. A Cell persists
   until explicitly deleted or replaced. A conforming implementation
   may reclaim unreachable Cells.


5.10  Summary

   The Store expresses:

      * Persistent named state
      * Mutable structure
      * Explicit absence
      * Aliasing
      * Hierarchical organization

   SOMA exposes the Store openly. No shadow memory model exists beneath
   it. The Store is the machine memory.


SOMA v1.0 Language Specification                                 SOMA-1.0
State-Oriented Machine Algebra                                 16 Nov 2025
Category: Informational



6.  PATH SEMANTICS
------------------

6.1  Overview

   A path is a dot-separated sequence of identifiers that names a Cell
   in the Store. Paths are used to read values, write values, obtain
   CellRefs, and perform structural operations.

   SOMA distinguishes between:
      * Accessing a Cell's payload
      * Accessing the Cell itself


6.2  Value Access

   A path without a trailing dot refers to the payload stored in the
   Cell at that path.

      a.b

   Resolution yields one of:
      * A value (including Nil)
      * Void (if the Cell does not exist)

   Example:

      a.b      => 42
      x.y.z    => Nil
      p.q.r    => Void


6.3  CellRef Access (Trailing Dot)

   A path ending in a dot resolves to a reference to the Cell itself.

      a.b.

   This yields a CellRef, not the payload.

   A CellRef can be:
      * Passed on the AL
      * Stored in another Cell
      * Written through
      * Replaced
      * Deleted structurally


6.4  Payload Mutation

   The write operator (!) mutates Cell payloads.

      Val !path

   This operation:

      * Creates all missing Cells in the path
      * Sets the target Cell's payload to Val
      * Preserves identity of existing Cells
      * Does not affect child Cells


6.5  Cell Replacement (Trailing Dot Write)

   A write to a trailing-dot path:

      Val !path.

   Causes:

      * The existing Cell (if any) to be discarded
      * A new Cell to be created
      * That Cell's payload set to Val
      * All child Cells removed


6.6  Structural Deletion

   Writing Void to a trailing-dot path removes that Cell:

      Void !path.

   The effect is:

      * If the Cell exists, delete it and its subtree
      * If the Cell does not exist, no action is taken

   Void does not propagate or error when used in this context.


6.7  Resolution Errors

   Path resolution never raises an exception. Instead:

      * Absent Cells yield Void
      * Existing Cells with no payload yield Nil
      * Existing Cells with a payload return the payload

   The interpreter must treat all three cases as valid reads.


6.8  Summary of Path Behavior

   Path          Meaning
   ------------  ----------------------------------------
   a.b           Value at a.b  (may be Nil or Void)
   a.b.          CellRef for a.b (may be Void)
   42 !a.b       Write payload 42 into a.b
   X !a.b.       Replace a.b Cell structure with new Cell X
   Void !a.b.    Delete Cell a.b and its subtree


SOMA v1.0 Language Specification                                 SOMA-1.0
State-Oriented Machine Algebra                                 16 Nov 2025
Category: Informational



7.  ACCUMULATOR LIST (AL) SEMANTICS
-----------------------------------

7.1  Overview

   The Accumulator List (AL) is a linear sequence of values that serves
   as the primary conduit of dynamic state in SOMA. It is analogous to
   a stack, but SOMA does not model call/return semantics. Instead, the
   AL provides:

      * Operand passing
      * State threading
      * Control selection
      * Block invocation context

   All computation flows through the AL.


7.2  Push and Pop Behavior

   Most tokens either:

      * Push a value onto the AL
      * Pop one or more values from the AL
      * Transform values already present

   The AL is updated in-place. No copying or implicit duplication occurs
   unless requested by a built-in (e.g. >dup).


7.3  Empty AL

   Reading from an empty AL is a fatal interpreter error. SOMA does
   not define implicit defaults. Programs must ensure AL safety through
   correct sequencing of tokens.


7.4  Error Conditions

   The following conditions cause fatal execution errors:

      * Attempting to pop a value when AL is empty
      * Performing an operation requiring N values when fewer are present
      * Invalid Block execution context
      * Mis-typed value where a specific kind is required

   SOMA does not attempt recovery. User logic, not the interpreter,
   is responsible for preventing such errors.


7.5  AL as the Dynamic Execution Context

   Blocks consume and produce AL state. A SOMA program is a sequence
   of state transformations of the form:

      AL₁, Store   →   AL₂, Store'

   AL₁ and AL₂ may differ:

      * In length
      * In value types
      * In ordering

   There is no expectation of symmetry. Blocks do not "return" a fixed
   number of values.


7.6  No Arity

   Blocks do not declare arguments. They take whatever values they
   require from the AL, and leave whatever values they produce.

   Built-ins behave the same way: each defines its own AL contract.


7.7  AL and Control Flow

   The AL determines which block executes next under >Choose.

   Example:

      A B C >Choose

   If A is:

      True  → B is executed
      False → C is executed

   After execution, AL contents are replaced by the result of the
   chosen Block.


7.8  AL and Block Chaining

   The >Chain operator repeatedly executes Blocks placed at the top
   of the AL. If the result of a Block execution leaves a Block on
   top of the AL, execution continues. Otherwise, >Chain terminates.


7.9  Example

      1 2 >+   → 3
      "Hello"  → AL contains a single Str
      { >dup >* }  → AL contains a Block, not executed
      >dup  → duplicates the top value
      >print → consumes top value and prints it


7.10 Summary

   The AL is:

      * The only evaluation context
      * The mechanism of operand passing
      * The carrier of control decisions
      * A visible part of machine state

   The AL does not model call frames, return contexts, or exception
   handlers. It is a simple, explicit list of values used to drive
   computation.


SOMA v1.0 Language Specification                                 SOMA-1.0
State-Oriented Machine Algebra                                 16 Nov 2025
Category: Informational



8.  BLOCKS AND EXECUTION
------------------------

8.1  Overview

   Blocks are the primary executable units in SOMA. They are enclosed
   in braces and contain arbitrary tokens. A Block is a value until it
   is invoked. Block execution is a transformation of machine state.

   SOMA does not define functions, procedures, or lambdas. All such
   concepts are subsumed by Blocks acting upon state.


8.2  Block Syntax

   A Block is written:

      { token token token }

   Blocks may be nested without limit:

      { 1 { 2 } >drop }

   A Block is not executed when read. It is pushed onto the AL.


8.3  Blocks Are Values

   A Block behaves like any other SOMA value. It may be:

      * Pushed onto the AL
      * Stored in a Cell
      * Passed between Blocks
      * Used in control flow
      * Executed via >Chain or other built-ins


8.4  Execution Model

   A Block executes when a word instructs it to do so. SOMA does not
   define implicit execution. A Block is executed by:

      * Consuming values from the AL if needed
      * Running its tokens in sequence
      * Leaving new AL contents afterward

   Execution always terminates at the end of the Block unless control
   is extended via >Chain.


8.5  No Arity

   Blocks do not declare parameters or argument counts. A Block simply
   consumes whatever values it expects from the AL. A Block may read
   more or fewer values than it leaves.


8.6  No Return

   SOMA Blocks do not return to a caller. They leave values on the AL
   and execution proceeds with the next token. There is no return
   statement or return stack.


8.7  No Call Stack

   Execution of a Block does not create a new stack frame. SOMA does
   not implement function calls. A Block is not a function; it is a
   state transformer.


8.8  Blocks as Control Nodes

   Blocks may reference other Blocks stored in Cells or found on the
   AL. This permits dynamic control structures:

      { _self "tick" >print _self }  → infinite loop
      { >dup >* }                    → square function
      { _n 1 >+ !_n }                → counter step

   Blocks form dynamic execution graphs without recursion.


8.9  Recursion vs Cycles

   SOMA does not define recursion. It defines repeated execution
   through explicit state passing. Cycles occur when Blocks
   reintroduce themselves (or others) via >Chain.

      { _self >Chain }   → infinite self-execution
      { A. >Chain }      → finite state machine node


8.10  Block Lifetime

   Blocks persist as long as they remain referenced:

      * In the AL
      * In the Store
      * In a Thing
      * As part of another Block

   SOMA does not define garbage collection but does not forbid it.


8.11  Summary

   Blocks are:

      * First-class values
      * State transformers
      * Arity-free and return-free
      * Executed only when explicitly invoked
      * Capable of forming control graphs
      * Distinct from functions in both form and semantics

   SOMA models computation by state evolution, not function invocation.


SOMA v1.0 Language Specification                                 SOMA-1.0
State-Oriented Machine Algebra                                 16 Nov 2025
Category: Informational



9.  BUILT-IN WORDS (CORE)
-------------------------

9.1  Overview

   Built-in words are primitive operations provided by the SOMA
   execution environment. They are identified by a leading ">" symbol.

      >word

   Built-ins are executed immediately when encountered. They consume
   and produce AL values according to their defined behavior.

   Built-ins are not user-definable and may not be overridden.


9.2  Arithmetic

   The following built-ins operate on integer values:

      >+
         Pop two integers (b, a); push (a + b)

      >-
         Pop two integers (b, a); push (a - b)

      >*
         Pop two integers (b, a); push (a * b)

      >/
         Pop two integers (b, a); push (a / b), integer division

   Arithmetic on non-integer values is an error.


9.3  Comparison

   Comparison operators pop two values and push a Boolean result:

      >=
         Pop (b, a); push True if a == b else False

      ><
         Pop (b, a); push True if a < b else False

      >>
         Pop (b, a); push True if a > b else False

   String and integer comparisons are defined. Cross-type comparison
   is an error.


9.4  Stack Operations

   The AL is manipulated by:

      >dup
         Duplicate the top value

      >drop
         Remove the top value

      >swap
         Swap the top two values

      >over
         Duplicate the second value and push it on top


9.5  Debug Operations

   >print
      Pop the top value and display it to standard output.

   >dump
      Display the current AL and Store state for debugging.


9.6  Type and Identity Words

   >type
      Pop a value and push a string representing its type.

   >id
      Pop a CellRef or Thing and push an integer identity value.


9.7  No-Op

   >noop
      Perform no operation; AL is unchanged.


9.8  Built-ins and AL Contracts

   Each built-in has a fixed AL contract. For example:

      >dup
         Requires at least 1 value on the AL
         Produces 1 new value

      >drop
         Requires at least 1 value on the AL
         Produces nothing

      >+
         Requires at least 2 integers
         Produces 1 integer

   Violating a contract is a fatal error.


9.9  Summary Table

   The following table summarizes core built-ins:

      Built-in   Pops   Pushes   Action
      --------   ----   ------   -------------------------
      >dup         1       2     Duplicate top value
      >drop        1       0     Drop top value
      >swap        2       2     Swap top two values
      >over        2       3     Duplicate 2nd value
      >+           2       1     Integer addition
      >-           2       1     Integer subtraction
      >*           2       1     Integer multiplication
      >/           2       1     Integer division
      >==          2       1     Equality test
      ><           2       1     Less-than test
      >>           2       1     Greater-than test
      >print       1       0     Print value
      >dump        0       0     Dump machine state
      >noop        0       0     No operation

   More built-ins are defined in later sections. This section lists the
   universal core.


SOMA v1.0 Language Specification                                 SOMA-1.0
State-Oriented Machine Algebra                                 16 Nov 2025
Category: Informational



10.  LOGICAL CONTROL FLOW
-------------------------

10.1  Overview

   SOMA does not define control structures such as IF, WHILE, FOR, or
   RETURN. All control flow arises from two built-in words:

      >Choose
      >Chain

   These operate on Blocks and values already present on the AL and do
   not depend on hidden stacks, jump tables, or continuations.


10.2  No Return Stack

   SOMA does not implement a call stack. Block execution does not
   create new stack frames. Control flow does not depend on return
   semantics.


10.3  No Exceptions

   SOMA does not implement exception handling. Fatal conditions stop
   the interpreter. Non-fatal error cases must be handled by user
   logic using >Choose or equivalent constructs.


10.4  >Choose — Data-Level Branch

   >Choose selects between two Blocks based on a Boolean at the top
   of the AL. The AL must contain:

      A B C >Choose

      Where:
         A is a Boolean
         B is the Block if A is True
         C is the Block if A is False

   Semantics:

      If A == True:
         Execute Block B
      Else:
         Execute Block C

   After execution, the AL contains only the results of the chosen
   Block. The unused Block is discarded.

   >Choose is not a syntactic IF. It is a semantic branch based on
   values already present in machine state.


10.5  >Chain — Block Continuation Loop

   >Chain repeatedly executes the Block on top of the AL. Execution
   proceeds as follows:

      1. Pop the top value from the AL.
      2. If it is not a Block, stop. >Chain terminates normally.
      3. Execute the Block.
      4. After execution, if the new top of the AL is a Block, repeat.
      5. Otherwise stop.

   >Chain does not recurse and does not grow a call stack.

   A Block that leaves itself on top of the AL will continue forever:

      { _self >print _self } >Chain


10.6  Derived Flow Forms (Informative)

   The following examples illustrate how traditional structures arise
   from >Choose and >Chain.


10.6.1  IF

      A B {} >Choose

      If A is True, execute B; otherwise do nothing.


10.6.2  IF / ELSE

      A B C >Choose

      Equivalent to:
         if A then B else C


10.6.3  WHILE

      { Condition Block
         Condition {
             Body
             _self
         } {}
         >Choose
      } >Chain

      A more compact form is possible if Condition returns a Boolean
      and Body leaves the Condition Block on top.


10.6.4  Finite State Machine Node

      { _self >Chain }                   ; infinite loop
      { NextState. >Chain }              ; delegate to another Block
      { Decide NextA NextB >Choose }     ; conditional transition


10.7  Cyclic Block Graphs

   Because Blocks are first-class and execution is linear, SOMA
   directly expresses cycles in control flow:

      A → B → C → A

   Such cycles do not consume stack space, do not require recursion,
   and do not require special syntax. Cycles persist as long as Blocks
   continue to place new Blocks at the top of the AL.


10.8  Summary: SOMA as Dynamic Flow Algebra

   SOMA’s control model is not syntactic but algebraic:

      >Choose
         selects a Block based on AL contents

      >Chain
         repeatedly executes Blocks from the AL

   All other control structures are derivable from these operations. No
   hidden systems, no call frames, no exception unwinding, and no
   continuation capture are required.

   SOMA is a model of computation where flow, like data, is explicit,
   inspectable, and dynamic.


SOMA v1.0 Language Specification                                 SOMA-1.0
State-Oriented Machine Algebra                                 16 Nov 2025
Category: Informational



11.  CONCURRENCY
----------------

11.1  Overview

   SOMA supports concurrency through explicit thread creation. Threads
   are independent SOMA machines that:

      * Begin with their own AL
      * Share access to the Store
      * Execute Blocks independently
      * Run until completion or fatal error

   SOMA does not define preemption, scheduling policy, or timing
   guarantees. These are implementation-defined.


11.2  Thread Creation

   The >thread built-in creates a new SOMA thread. It requires a Block
   on top of the AL:

      { Block } >thread

   Semantics:

      * A new thread is created
      * The Block is placed as its initial AL top
      * The current thread continues execution
      * A thread identifier is pushed onto the AL


11.3  Thread Identifier

   The value pushed by >thread uniquely identifies the new thread. It
   may be stored, compared, or passed as a value. Its internal form is
   implementation-defined.


11.4  AL Isolation

   Each thread has its own AL. Threads do not share AL state. Values
   must be passed through the Store to be visible between threads.


11.5  Shared Store

   The Store is shared across all threads. Writes and reads occur in
   a single, global memory space. Aliasing, deletion, and replacement
   operate identically whether performed by one or many threads.

   SOMA does not define locking, atomicity, or conflict resolution.


11.6  No Locking in Core

   SOMA provides no built-in mutexes, semaphores, monitors, or atomic
   operations. Higher-level coordination must be implemented by
   convention or via host-provided built-ins.


11.7  Retrieving Thread Results

   The >result built-in retrieves the final AL state of a completed
   thread. It requires a thread identifier:

      tid >result

   If the thread has completed, >result pushes its final AL contents.
   If not, behavior is implementation-defined (block, fail, or return
   Void).


11.8  Thread Failure Semantics

   If a thread encounters a fatal error:

      * Its execution terminates immediately
      * Other threads are unaffected
      * The Store remains in the state it had at the moment of failure
      * No unwind or rollback occurs

   Threads do not propagate failure to their parent or creator.


11.9  Example

      { "Hello" >print } >thread
      { 1 2 >+ } >thread
      >dump

   The main thread continues while others execute independently.


11.10  Summary

   SOMA concurrency is defined by:

      * AL isolation
      * Shared Store
      * No call stack
      * No synchronization primitives
      * No exception propagation

   Threading extends SOMA’s dynamic execution model across multiple
   independently evolving state machines.


SOMA v1.0 Language Specification                                 SOMA-1.0
State-Oriented Machine Algebra                                 16 Nov 2025
Category: Informational



12.  REFLECTION
---------------

12.1  Overview

   SOMA supports a minimal reflection model that allows programs to:

      * Convert strings into Store paths
      * Recover canonical names for Store locations

   Reflection in SOMA operates strictly at the level of the Store
   and does not expose language syntax, Blocks, or evaluator state.


12.2  Reflection Philosophy

   SOMA does not support:
      * Source-level introspection
      * Syntax manipulation
      * Runtime code construction
      * Evaluating strings as code ("eval")

   Reflection exists solely to interpret Store structure.


12.3  >ToPath

   The >ToPath built-in converts a string into a Store path. The AL
   must contain a string:

      "config.user.name" >ToPath

   Semantics:

      * The string is parsed as a path
      * The corresponding Cell payload (or Void) is retrieved
      * The payload is pushed on the AL
         (or Void if the path does not exist)

   >ToPath is equivalent to writing the path literally in the program.


12.4  >FromPath

   The >FromPath built-in converts a CellRef into a canonical string
   representing the path by which it is reachable.

   AL must contain a CellRef:

      some.path. >FromPath

   Semantics:

      * If the CellRef corresponds to a named path, its string form
        is pushed onto the AL
      * If no named path exists, Void is pushed

   No attempt is made to reconstruct synthetic or anonymous paths.


12.5  No Value Serialization

   Reflection does not allow values to be converted to strings and back.
   SOMA does not define round-trippable string encoding of values.
   Only paths may be constructed from strings.


12.6  Reflection and Identity

   >ToPath and >FromPath do not affect aliasing:

      a.b. and c.d. may refer to the same Cell
      >FromPath a.b.   → "a.b"
      >FromPath c.d.   → "c.d"

   The CellRef identity is unchanged by reflection.


12.7  Reflection Example

      "session.active" >ToPath
      True =? >Choose
         { "Session active" >print }
         { "Session inactive" >print }
      >Chain


12.8  Summary

   SOMA supports structural reflection only. The reflection layer:

      * Converts strings into Store paths
      * Converts CellRefs into paths, where possible
      * Does not expose syntax or evaluation
      * Does not allow dynamic code execution

   Reflection exists to inspect and navigate SOMA's Store — nothing
   more.


SOMA v1.0 Language Specification                                 SOMA-1.0
State-Oriented Machine Algebra                                 16 Nov 2025
Category: Informational



13.  THINGS
-----------

13.1  Overview

   SOMA supports a class of opaque values called Things. A Thing is a
   reference to a data structure or resource not defined within SOMA
   itself. Examples include:

      * Lists
      * Hash maps
      * File handles
      * Sockets
      * GPU contexts
      * External library objects

   A Thing may be passed through the AL and stored in the Store. Its
   internal structure is not observable from within SOMA.


13.2  Opaqueness

   A Thing is not decomposable, enumerable, or pattern-matchable. SOMA
   does not define words to:

      * Iterate its elements
      * Inspect internals
      * Modify internal layout

   A Thing is either acted on by a host-provided built-in or remains inert.


13.3  Creation

   A Thing is created by some implementation-defined mechanism, such as:

      >list
      >open
      >alloc
      >matrix

   The exact mechanism is not specified by SOMA core. Execution
   environments may extend the Thing vocabulary.


13.4  Identity

   Each Thing has a unique identity value accessible via:

      >id

   Identity is preserved when Things are:
      * Stored in Cells
      * Passed on the AL
      * Duplicated by assignment

   No two distinct Things share the same identity.


13.5  Equality

   By default, equality between two Things is identity-based:

      Thing1 == Thing2   if and only if they are the same object

   Structural or semantic comparison is not defined.


13.6  Interaction with the Store

   Things may be stored in Cells:

      T !a.b

   Or passed as values:

      a.b   → T
      T >print

   The Store does not copy or serialize Things. It holds a reference.


13.7  Interaction with Built-ins

   Things are manipulated via built-in words that understand them. For
   example:

      >push
      >pop
      >len
      >get
      >set
      >send

   SOMA core does not define such words. They are implementation- or
   domain-specific.


13.8  Lifecycle

   SOMA does not define garbage collection or reference counting for
   Things. Implementations may:

      * Track references
      * Require explicit release
      * Leak safely into external runtimes

   SEMANTICS: A Thing persists until the host chooses to reclaim it.


13.9  Example

      >list             ; create new list Thing L
      "alpha" >push     ; L = ["alpha"]
      L !a.items        ; store into a.items

      a.items           ; fetch L
      "beta" >push      ; append
      >pop              ; pop from list

   All mutations occur inside the Thing, not the Store.


13.10  Summary

   Things represent:

      * External or non-SOMA objects
      * Opaque identities
      * Mutable state under host control

   SOMA treats them uniformly:
      * They are values
      * They can be stored
      * They have identity
      * They require dedicated built-ins to manipulate

   Things allow SOMA programs to interact with the outside world
   without compromising SOMA’s semantic model.


SOMA v1.0 Language Specification                                 SOMA-1.0
State-Oriented Machine Algebra                                 16 Nov 2025
Category: Informational



14.  ERROR MODEL
----------------

14.1  Overview

   SOMA defines a strict and minimal error model. Errors are divided
   into two classes:

      * Fatal Errors — execution terminates immediately
      * User-Level Logical Errors — representable in state, not runtime

   SOMA does not define exceptions, stack unwinding, catch blocks,
   recovery frames, or resumable errors.


14.2  Fatal Errors

   A fatal error occurs when the SOMA interpreter detects a violation
   of the execution rules or machine invariants. If a fatal error
   occurs:

      * Execution of the current thread stops immediately
      * No cleanup is attempted
      * Other threads continue
      * The Store remains in its last valid state

   A fatal error is equivalent to a machine halt for that thread.


14.3  Examples of Fatal Errors

   • AL underflow (attempting to pop with insufficient items)
   • Wrong type passed to a built-in
   • Invalid token
   • Unterminated Block
   • Unterminated string literal
   • Reference to a malformed path
   • Attempting arithmetic on non-integers
   • Failing to provide >Choose with a Boolean + 2 Blocks
   • Executing >Chain on a non-Block value
   • Any malformed lexeme or runtime violation


14.4  Non-Fatal Conditions

   The following conditions **are not fatal**:

      • Void path resolution
      • Nil Cell values
      • Logical “errors” represented in AL state
      • Branches that skip certain Blocks
      • Absence of expected structure

   These must be handled by program logic using >Choose and Blocks.


14.5  No Exceptions

   SOMA does not support:

      • try
      • catch
      • throw
      • raise
      • resumable continuation

   Nor does it support unwinding or cleanup handlers.


14.6  User Logic Instead of Exceptions

   SOMA treats error as state, not control. A program may push an error
   record, symbol, or Boolean onto the AL and branch appropriately:

      A B C >Choose

   Where:
      A = True → B handles success
      A = False → C handles failure

   Or more explicitly:

      "error: missing file" !_err
      _err Void == >Choose
         { "OK" >print }
         { _err >print }


14.7  Concurrency and Errors

   A fatal error in one thread:

      • Does not kill other threads
      • Does not roll back the Store
      • Does not propagate

   Threads are independent except for shared state.


14.8  Testing and Static Analysis

   SOMA error conditions are deterministic. A correct interpreter:

      • MUST halt when encountering a fatal error
      • MUST NOT attempt recovery
      • MUST NOT mask runtime errors


14.9  Summary

   SOMA’s error model is:

      * Minimal
      * Explicit
      * Non-recoverable
      * Thread-local

   There are no exceptions, no stack unwinds, no safety rails. Program
   correctness is achieved by state discipline, not control traps.


SOMA v1.0 Language Specification                                 SOMA-1.0
State-Oriented Machine Algebra                                 16 Nov 2025
Category: Informational



15.  ABSTRACT MACHINE SEMANTICS
-------------------------------

15.1  Overview

   SOMA defines a concrete operational semantics. Every SOMA program
   executes on a well-defined abstract machine whose full state is:

      (AL, Store, IP, ThreadState)

   No hidden stacks, continuations, or traces exist beneath this model.


15.2  Machine State Components

   The SOMA machine state consists of:

      AL
         The Accumulator List. A finite sequence of values.

      Store
         A hierarchical graph mapping path → Cell.
         Cells contain values or Nil. Absent Cells are Void.

      IP
         Instruction pointer. A reference to the next token to execute.
         May be a Block-local pointer or a stream pointer.

      ThreadState
         Encodes whether execution is:
            • Running
            • Halted normally
            • Halted fatally


15.3  Transition Function

   SOMA execution proceeds in discrete steps.

      (AL, Store, IP)  →  (AL', Store', IP')

   Each step corresponds to evaluation of one token.

   The transition is deterministic unless a built-in is defined as
   nondeterministic (e.g. time, randomness, or concurrency).


15.4  Token Classification

   Tokens fall into 4 semantic categories:

      • Literal values
      • Paths
      • Blocks
      • Built-in words

   Each category defines a transition rule.


15.5  Literal Rule

      Literal token L:
         AL' = L :: AL
         Store' = Store
         IP' = IP + 1


15.6  Path Rule

   Path P resolves to V:

      V = lookup(P, Store)

   Then:

      AL' = V :: AL
      Store' = Store
      IP' = IP + 1


15.7  Block Rule

      Block B:
         AL' = B :: AL
         Store' = Store
         IP' = IP + 1

   Blocks are not executed here — only placed on the AL.


15.8  Built-in Rule

   For built-in word W:

      (AL, Store)  →  (AL*, Store*)

   Error if AL contains insufficient or mistyped values.

   Then:

      AL' = AL*
      Store' = Store*
      IP' = IP + 1


15.9  Block Execution Rule

   When a Block is executed (via >Choose, >Chain, or another built-in):

      • A new IP is created pointing to the first token in B
      • Execution proceeds until the Block ends
      • Then control returns without stack frames

   No call stack exists. Return is implicit: the Block simply ends.


15.10  Termination

   A SOMA thread halts when:

      • The input token stream is exhausted
      • A block finishes and no further tokens remain
      • A fatal error occurs


15.11  No Continuations

   SOMA defines no mechanism to:

      • Capture the IP
      • Save an execution context for later
      • Rewind state
      • Resume partial frames

   Any such behavior must be implemented using Blocks, AL values,
   and explicit control flow.


15.12  Determinism

   SOMA execution is deterministic except where explicitly defined
   otherwise:

      • Concurrency
      • Interaction with Things
      • Host-provided non-deterministic built-ins


15.13  Summary

   SOMA execution is defined entirely by:

      (AL, Store, IP)

   And a deterministic transition function. There is no hidden control
   structure, no return stack, no CPS layer, and no rewriting calculus.
   SOMA is a machine algebra defined by state change, not expression
   reduction.

SOMA v1.0 Language Specification                                 SOMA-1.0
State-Oriented Machine Algebra                                 16 Nov 2025
Category: Informational



16.  FORMAL GRAMMAR
-------------------

16.1  Notation

   This section uses an extended Backus–Naur Form (BNF), with:

      ::=   defines a production
      |     separates alternatives
      […]   optional element
      …*    zero or more repetitions
      …+    one or more repetitions

   Literal terminals are written in quotes.
   Unicode classes follow UAX #31 notation where applicable.


16.2  Top-Level

   program ::= token*


16.3  Token Classes

   token ::= literal
           | path
           | block
           | builtin


16.4  Literals

   literal ::= int_literal
             | string_literal
             | raw_string_literal
             | boolean_literal


16.5  Integer Literals

   int_literal ::= ["-"] digit+

   digit ::= "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"


16.6  Boolean Literals

   boolean_literal ::= "True"
                     | "False"


16.7  Escaped String Literals

   string_literal ::= '"' string_char* '"'

   string_char ::= any UTF-8 scalar value except:
                     • unescaped quote
                     • unescaped backslash
                   OR
                   escape_sequence

   escape_sequence ::= '\n' | '\t' | '\"' | '\\'


16.8  Raw Parenthesised Strings

   raw_string_literal ::= "(" raw_string_body ")"

   raw_string_body ::= any UTF-8 scalar value except unbalanced ")"
                       (may include newlines)


16.9  Paths

   path ::= identifier ( "." identifier )*

   Paths refer to Cell payloads unless suffixed by a trailing dot:

   cellref_path ::= path "."


16.10  Identifiers

   identifier ::= xid_start xid_continue*

   xid_start     ::= Unicode XID_Start or "_"
   xid_continue  ::= Unicode XID_Continue or "_"

   Identifiers are normalized to NFC.


16.11  Blocks

   block ::= "{" token* "}"


16.12  Built-in Words

   builtin ::= ">" builtin_name

   builtin_name ::= ASCII alphanumeric sequence
                    (no Unicode required or recommended)


16.13  Whitespace

   Whitespace separates tokens.
   Whitespace may consist of spaces, tabs, or newlines.
   Whitespace has no semantic meaning.


16.14  Error Conditions

   A sequence that cannot be parsed according to this grammar is invalid
   SOMA input and MUST cause a fatal interpreter error.


16.15  Summary

   The SOMA grammar defines:

      * Integer, boolean, and string literal forms
      * Unicode identifiers per UAX #31
      * Hierarchical paths
      * Raw and escaped strings
      * First-class blocks
      * Built-ins prefixed by ">"

   SOMA syntax is intentionally minimal. Most structure is semantic,
   not lexical.


SOMA v1.0 Language Specification                                 SOMA-1.0
State-Oriented Machine Algebra                                 16 Nov 2025
Category: Informational



17.  SAMPLE PROGRAMS
--------------------

17.1  Overview

   This section provides worked SOMA examples demonstrating:

      * Literal execution
      * Store mutation
      * Control flow via >Choose
      * Looping via >Chain
      * Finite state behavior
      * Reflection
      * Concurrency


17.2  Literal and AL Behavior

      1 2 >+ >print

   Output:

      3


17.3  Basic Store Writes

      42 !a
      "Hello" !b.message
      True !config.enabled

      a >print          ; prints 42
      b.message >print  ; prints Hello


17.4  Conditional Execution

      config.enabled
      { "Enabled" >print }
      { "Disabled" >print }
      >Choose

   If config.enabled is True, prints "Enabled".
   Otherwise prints "Disabled".


17.5  Block as a Reusable State Transformer

      { >dup >* } !square

      7 square. >Chain >print

   Output:

      49


17.6  Infinite Loop (Example Only)

      { _self "tick" >print _self } >Chain

   Prints “tick” forever. Does not grow stack.


17.7  Simple Counter (Mutable Store)

      0 !counter.n

      {
         counter.n
         1 >+
         !counter.n
         counter.n >print
         _self
      } >Chain

   Prints:

      1
      2
      3
      ... forever


17.8  Finite State Machine (Two-State Toggle)

      {
         state.
         True
         { False !state. "OFF" >print }
         { True  !state. "ON"  >print }
         >Choose
         _self
      } !toggle

      True !state.
      toggle. >Chain

   Prints alternating ON / OFF.


17.9  Reflection Example

      "config.enabled" >ToPath
      { "Yes" >print }
      { "No"  >print }
      >Choose


17.10  Parenthetic Strings

      (
      This string contains "quotes"
      and spans multiple lines
      ) !msg

      msg >print


17.11  Multi-Thread Example (Conceptual)

      {
         "Worker starting" >print
         1 1000000 >+
         "Worker done" >print
      } >thread

      "Main thread continues" >print


17.12  Store aliasing

      99 !a.b
      a.b. !x.y
      x.y >print

   Output:

      99


17.13  Read-Modify-Write

      counter.n          ; push current value
      5 >+               ; add 5
      !counter.n         ; write new value


17.14  Summary

   These examples illustrate SOMA’s core principles:

      * State is explicit
      * Control is explicit
      * Everything is observable
      * Blocks are free, dynamic, and first-class
      * No hidden stacks or return model
      * Flow arises from values, not syntax

SOMA v1.0 Language Specification                                 SOMA-1.0
State-Oriented Machine Algebra                                 16 Nov 2025
Category: Informational



18.  SOMA IN CONTEXT
--------------------

18.1  Overview

   SOMA is a machine algebra: a formal model of computation based on
   explicit state and observable mutation. It is neither an evolution
   nor a subset of the mainstream paradigms. This section places SOMA
   in contrast with several well-known computational frameworks.


18.2  Comparison with Forth

   Similarities:
      • Stack-oriented value passing
      • Small, explicit vocabulary
      • No type declarations
      • Direct access to underlying machine state

   Differences:
      • SOMA has a persistent hierarchical Store
      • Blocks do not self-execute
      • No threaded interpretation model
      • State is first-class rather than memory-mapped
      • Control flow uses algebraic composition (not syntax or jumps)


18.3  Comparison with Lambda Calculus

   Lambda Calculus is:
      • Stateless
      • Referentially transparent
      • Defined by substitution
      • Strongly tied to reduction semantics

   SOMA is:
      • Stateful
      • Procedurally mutable
      • Defined by state transitions
      • Not based on substitution or rewriting

   In SOMA, mutation is not impurity—it is the semantic foundation.


18.4  Comparison with Haskell

   Haskell:
      • Works to prevent mutation
      • Encodes state via monads
      • Hides machine behavior
      • Separates IO from logic through type control

   SOMA:
      • Begins in mutable state
      • Has no static type system
      • Exposes machine behavior directly
      • Treats all computation as IO

   In SOMA, every Block is a "monad" because state is the domain.


18.5  Comparison with Turing Machines

   Turing Machine:
      • One tape
      • One head
      • One symbol at a time
      • State is implicit and minimal

   SOMA:
      • Structured Store
      • Arbitrary data
      • Multiple active threads
      • State is explicit and named

   SOMA is not a weaker or stronger Turing Machine—it is a more direct
   reflection of modern computation.


18.6  Comparison with Actor Models

   Actors:
      • Share nothing
      • Communicate via message passing
      • Are isolated

   SOMA threads:
      • Share Store
      • Communicate via shared state
      • Have no enforced isolation

   SOMA assumes state discipline is the programmer’s responsibility.


18.7  Comparison with Object-Oriented Models

   OO:
      • Encapsulates state
      • Methods operate on hidden data
      • Identity is tied to references

   SOMA:
      • State is globally visible
      • Blocks do not belong to objects
      • Identity is explicit and structural

   SOMA focuses on transformations, not encapsulation.


18.8  Comparison with Process Calculi (π-calculus, CSP)

   Process calculi describe behavior using algebraic relations over
   channels and names.

   SOMA describes behavior using algebraic relations over:
      (AL, Store) → (AL, Store)

   π-calculus "moves names"; SOMA "moves state."


18.9  Summary

   SOMA rejects the idea that mutation is a problem to be tamed or
   abstracted away. Instead:

      • Mutation is the model
      • State is the ontology
      • Flow is algebraic, not syntactic
      • Execution replaces reduction
      • Programs run, they do not rewrite

   SOMA is not an improvement over existing models. It is a reframing:
   a language that tries to describe what machines *actually do*.


SOMA v1.0 Language Specification                                 SOMA-1.0
State-Oriented Machine Algebra                                 16 Nov 2025
Category: Informational



19.  IMPLEMENTATION NOTES
-------------------------

19.1  Overview

   SOMA defines a language and an abstract machine. An implementation
   MUST follow the semantics in Sections 1–18, but may choose:
      • execution strategy
      • performance model
      • internal representation
      • concurrency granularity
      • target platform

   This section clarifies what is required, permitted, and optional.


19.2  Required Behavior

   A conforming SOMA implementation MUST:

      • Treat the AL as an ordered sequence of values
      • Treat the Store as a hierarchical graph of Cells
      • Preserve the Void / Nil distinction
      • Execute tokens left-to-right
      • Honor the semantics of built-ins
      • Enforce fatal errors for invalid AL state
      • Not silently ignore malformed syntax
      • Carry Blocks as first-class runtime values
      • Terminate threads immediately upon fatal error


19.3  Permitted Implementation Variations

   An implementation MAY:

      • JIT-compile Blocks
      • Interpret directly
      • Use a GC for Cells
      • Detect unreachable Store nodes
      • Inline built-in words
      • Intern strings
      • Represent the AL as:
          - a linked list
          - a dynamic array
          - a persistent vector
      • Represent the Store as:
          - a trie
          - a hash map of maps
          - a rope
          - a pointer graph


19.4  Concurrency Semantics

   The following are implementation-defined:

      • Scheduling fairness
      • Preemption or cooperative threading
      • Time-slicing granularity
      • Memory model visibility
      • Progress guarantees

   SOMA specifies that:
      • Threads share Store
      • AL is not shared
      • Fatal errors do not propagate

   Everything else is left open.


19.5  Optimization Freedom

   An implementation MAY optimize by:

      • Collapsing noop Blocks
      • Constant-folding literal sequences
      • Specializing >Choose dispatch
      • Early-stopping >Chain when detectable
      • Sharing structural subgraphs of the Store
      • Removing unreachable Cells

   HOWEVER:
      • Observed semantics MUST NOT change
      • AL contents MUST remain correct at each step
      • Reflection MUST still work


19.6  Allowed Extensions

   SOMA MAY be extended with:

      • Additional built-ins
      • Domain-specific Things
      • Custom numeric types
      • File I/O
      • Network I/O
      • Host system calls
      • Debug and tracing hooks

   Extension built-ins MUST NOT:
      • violate AL semantics
      • redefine >Choose or >Chain
      • mask fatal errors


19.7  Forbidden Changes

   A SOMA implementation MUST NOT:

      • Add implicit call stack behavior
      • Hide mutation behind purity layers
      • Treat absence as Nil
      • Merge Cells that are not aliased
      • Convert fatal errors into resumable conditions
      • Reinterpret Blocks as functions
      • Introduce exceptions


19.8  Timing and Performance

   SOMA does not mandate:

      • Real-time guarantees
      • Execution speed
      • Memory throughput
      • Parallelism requirements

   SOMA defines correctness, not performance targets.


19.9  Validation

   A SOMA implementation is conformant if:

      • All required semantics are observed
      • No forbidden changes are implemented
      • The test programs in Section 17 all behave as specified


19.10  Summary

   Implementations MUST preserve semantics, but MAY vary
   substantially in engineering detail. SOMA encourages
   experimentation in:

      • concurrency models
      • JITs and interpreters
      • graph storage layouts
      • native integration
      • memory reclamation strategies

   SOMA is a semantic contract, not a VM specification.


SOMA v1.0 Language Specification                                 SOMA-1.0
State-Oriented Machine Algebra                                 16 Nov 2025
Category: Informational



20.  TEST SUITE AND CONFORMANCE
-------------------------------

20.1  Overview

   A SOMA implementation is considered conformant if it:

      • Executes SOMA programs according to this specification
      • Correctly handles fatal and non-fatal conditions
      • Passes a suite of required behavioral tests
      • Preserves Store and AL semantics under all cases

   This section defines the minimum test suite required for validation.


20.2  Test Philosophy

   SOMA correctness is behavioral. A conformant implementation must:

      • Not crash or mis-execute
      • Halt cleanly on fatal errors
      • Produce correct AL values when expected
      • Preserve Store identity and aliasing rules
      • Respect strict mutation semantics

   Performance is not tested. Only semantics.


20.3  Test Categories

   The test suite is divided into:

      • Core Execution Tests
      • Literal and AL Operation Tests
      • Store Semantics Tests
      • Control Flow Tests
      • Block Execution Tests
      • Concurrency Tests
      • Reflection Tests
      • Things Tests (If Supported)
      • Error Handling Tests


20.4  Core Execution Tests

   Test: literal evaluation

      Program: 1 2 >+
      Expected AL: [3]

   Test: invalid token halts

      Program: @
      Expected: Fatal error (no Store change)


20.5  Literal and AL Tests

   Test: >dup

      Program: 5 >dup
      Expected AL: [5, 5]

   Test: >swap

      Program: 1 2 >swap
      Expected AL: [1, 2]


20.6  Store Tests

   Test: basic write

      Program: 42 !a.b
      Expected Store: a.b = 42

   Test: Nil vs Void

      Program: a.b
      Expected AL: [Void]
      Program: Nil !a.b
      Program: a.b
      Expected AL: [Nil]


20.7  Control Flow Tests

   Test: True branch

      Program: True { 1 } { 2 } >Choose
      Expected AL: [1]

   Test: False branch

      Program: False { 1 } { 2 } >Choose
      Expected AL: [2]


20.8  Block Execution Tests

   Test: square function

      Program:
         { >dup >* } !sq
         7 sq. >Chain
      Expected AL: [49]


20.9  Concurrency Tests

   Test: thread creation

      { 99 !x } >thread
      Expected: Main thread does not stall
      Store: x = 99 (after thread completion)


20.10  Reflection Tests

   Test: ToPath

      Program:
         "a.b" >ToPath
      Expected AL: [Void]

      Program:
         5 !a.b
         "a.b" >ToPath
      Expected AL: [5]


20.11  Things Tests (Optional)

   Test: List construction (if supported)

      Program:
         >list "alpha" >push
      Expected:
         AL top is a Thing with length 1


20.12  Error Handling Tests

   Test: AL underflow

      Program:
         >drop
      Expected: Fatal error

   Test: Type mismatch

      Program:
         "x" 2 >+
      Expected: Fatal error


20.13  Minimum Conformance Criteria

   An implementation is conformant if:

      • All core tests pass
      • No test produces incorrect AL or Store state
      • Fatal errors occur exactly where required
      • Non-fatal behaviors match specified semantics


20.14  Extending the Test Suite

   Implementations MAY add:

      • Performance tests
      • Host integration tests
      • Additional Block libraries
      • Threading stress tests
      • GC or memory pressure tests

   But MUST still pass the core suite.


20.15  Summary

   The SOMA test suite ensures:

      • Semantic correctness
      • State fidelity
      • Deterministic control flow
      • Proper fatal error behavior

   A SOMA system that passes these tests is considered compliant with
   this specification.


SOMA v1.0 Language Specification                                 SOMA-1.0
State-Oriented Machine Algebra                                 16 Nov 2025
Category: Informational



21.  FUTURE EXTENSIONS & RESEARCH DIRECTIONS
--------------------------------------------

21.1  Overview

   SOMA has been deliberately designed as a minimal state-oriented
   machine algebra. This simplicity leaves room for evolution,
   specialization, and theoretical exploration. This section outlines
   possible extensions which are explicitly NOT part of SOMA v1.0, but
   may be pursued in future versions or external research.


21.2  Static Analysis

   SOMA is defined as a dynamic language, but future directions could
   include:

      • AL flow analysis
      • Mutation tracking
      • Abstract interpretation
      • Liveness and Cell reachability
      • Thread correctness checks

   None of these are required for execution.


21.3  Type Systems

   SOMA intentionally omits static types. Research opportunities:

      • Optional type annotations
      • Linear types for state mutation
      • Refinement types over Cells
      • Capability-based alias restrictions

   These must not alter core execution semantics.


21.4  Advanced Concurrency Semantics

   SOMA defines a minimal thread model. Extensions could introduce:

      • Atomic writes
      • CAS instructions
      • Software transactional memory
      • Channel-based communication
      • Deterministic scheduling

   These must not break Store semantics.


21.5  Host Integration

   A SOMA implementation may embed:

      • File systems
      • Network IO
      • GPU compute
      • FFI bridges
      • Cryptographic devices

   Techniques may include:
      • System calls
      • FFI-backed Things
      • Memory-mapped regions


21.6  Garbage Collection Strategies

   SOMA does not mandate GC. Research may explore:

      • Store-level tracing
      • Reference-counted Cells
      • Region-based lifetimes
      • Alias-aware GC
      • Concurrent reclamation


21.7  JIT and Code Generation

   SOMA Blocks may be compiled:

      • Ahead-of-time
      • Just-in-time
      • Into native code
      • Into bytecode
      • Into vector instructions

   Target domains may include:
      • CPUs
      • GPUs
      • DPUs
      • FPGAs


21.8  Distributed SOMA

   A distributed Store could support:

      • Shared global graphs
      • Partitioned graphs
      • Store-level transactions
      • Actor-like scaling
      • Persistent execution checkpoints


21.9  Formal Semantics

   SOMA lends itself to:

      • Operational semantics (already defined)
      • Denotational semantics (future work)
      • Algebraic laws over state transitions
      • Category-theoretic interpretations
      • Comparison to monoidal computation models


21.10  Visual Representations

   SOMA is well-suited to visualization:

      • AL evolution diagrams
      • Store mutation graphs
      • Block execution traces
      • Interactive debugging views

   Such tools can reinforce SOMA’s educational value.


21.11  Educational Applications

   SOMA can be used to teach:

      • Explicit machine state
      • Mutation and aliasing
      • Control flow without syntax
      • Execution vs reduction
      • Concurrency without stacks

   It reveals computation as it is, not as abstractions pretend it to be.


21.12  Summary

   SOMA v1.0 defines a foundation: a minimal, stateful, explicit,
   mutation-based model. Beyond v1.0, research and experimentation may
   expand:

      • Formal methods
      • Execution substrates
      • Type-theoretic overlays
      • New mutation disciplines
      • Distributed execution
      • Hybrid symbolic/state systems

   The SOMA core is stable, but not closed. It invites evolution.


SOMA v1.0 Language Specification                                 SOMA-1.0
State-Oriented Machine Algebra                                 16 Nov 2025
Category: Informational



22.  DOCUMENT STATUS & VERSIONING
---------------------------------

22.1  Status of This Specification

   This document defines SOMA v1.0, the first complete formal
   specification of the State-Oriented Machine Algebra. It is intended
   to serve as a stable reference for:

      • language implementers
      • researchers
      • educators
      • systems engineers
      • language designers

   This version is considered *complete and normative*.


22.2  Change Control

   SOMA is not governed by a standards committee. Future revisions
   will be issued when:

      • new concepts require formal language changes
      • clarifications are needed
      • errors are discovered
      • major new domains are addressed

   Any such revisions must preserve the semantic principles defined
   in Sections 1–3.


22.3  Version Numbering

   SOMA uses a major/minor version scheme:

      MAJOR.MINOR

      • MAJOR increments break compatibility
      • MINOR increments are backward-compatible

   This document is:

      SOMA v1.0

   Future examples:

      SOMA v1.1 — new built-ins, no breaking changes
      SOMA v2.0 — syntax or semantics altered


22.4  Stability of Core Concepts

   The following elements are considered foundational and MUST NOT
   change within the 1.x series:

      • AL as primary execution context
      • Store as persistent structured memory
      • Nil / Void distinction
      • First-class Blocks
      • No call stack
      • No exceptions
      • No implicit control flow
      • >Choose and >Chain semantics


22.5  Future Specification Work

   Potential future documents may standardize:

      • SOMA binary formats
      • SOMA over network protocols
      • SOMA debugging interfaces
      • SOMA program library formats


22.6  Copyright and Licensing

   SOMA is an open conceptual specification. It may be:

      • implemented freely
      • reproduced in full or in part
      • extended in academic or industrial contexts

   No intellectual property claims are asserted over the SOMA model
   or language semantics.


22.7  Revision History

      v0.1 — Initial notes on SOMA and state semantics
      v0.3 — Training cells and local underscore model
      v0.5 — Unified Store model
      v0.6 — Introduction of stack AL
      v0.7 — Flow control via >Choose and >Chain
      SOMA v1.0 — Complete integrated specification


22.8  Final Statement

   SOMA is not a calculus pretending to be a machine. It is a machine
   described honestly: mutable, direct, explicit, and observable. It
   models computation as it lives at runtime, not as it is imagined
   through abstraction.

   This completes the SOMA v1.0 Specification.

_______________________________________________________________________

SOMA Errata & Clarifications                                      SOMA-ERRATA-1
For SOMA v1.0 Specification                                      16 Nov 2025
Category: Informational



Status of this Memo
-------------------

This document provides normative corrections, clarifications, and
amendments to the SOMA v1.0 Language Specification. It identifies
internal inconsistencies, syntactic omissions, and example errors
which must be addressed to ensure complete implementability and
semantic coherence.

This document does not alter the SOMA operational semantics, Store
model, AL model, or the core language philosophy. It corrects the
language so that its syntax, semantics, and examples are internally
consistent.



1.  UNDEFINED SYNTAX FOR STORE WRITES
-------------------------------------

1.1  Problem Statement

SOMA v1.0 defines:

   Val !path
   Val !path.

as the primary mutation operators, but the token `!` does not appear
anywhere in the formal grammar (Section 16).

Thus, store mutation syntax is undefined at the lexical level.

1.2  Required Correction

Add a new token class:

   write_token ::= "!" path [ "." ]

And extend token classification:

   token ::= literal | path | block | builtin | write_token

1.3  Semantics Note

A write_token SHALL consume the top AL value as `Val` and apply the
Store mutation rules defined in Sections 5 and 6.



2.  NIL AND VOID ARE NOT DEFINED AS LITERALS
-------------------------------------------

2.1  Problem Statement

Sections 4.5 and 4.6 define Nil and Void as runtime values, but
Section 16 (Grammar) does not include them in `literal`.

2.2  Required Correction

Extend 16.4:

   literal ::= int_literal
             | string_literal
             | raw_string_literal
             | boolean_literal
             | nil_literal
             | void_literal

   nil_literal  ::= "Nil"
   void_literal ::= "Void"



3.  BUILT-IN TOKEN GRAMMAR CONTRADICTS OPERATOR BUILT-INS
---------------------------------------------------------

3.1  Problem Statement

Grammar presently defines:

   builtin_name ::= ASCII alphanumeric sequence

However, built-ins include:

   >+
   >-
   >*
   >/
   >==
   ><
   >>

All of which violate this rule.

3.2  Required Correction

Replace 16.12 with:

   builtin ::= ">" builtin_name

   builtin_name ::= 1*ASCII graphic character
                    EXCLUDING whitespace, braces, and quote

This safely admits symbolic and word-like built-ins.



4.  COMPARISON OPERATOR INCONSISTENCIES
---------------------------------------

4.1  Problem Statement

Three conflicting equality forms are present:

   >=    (Section 9.3)
   >==   (Section 9.9)
   =?    (Section 12.7)

4.2  Required Correction

The canonical equality operator SHALL be:

   >==

and all examples SHALL be updated accordingly.

4.3  Additional Guidance

The operators SHALL be:

   >==     equality
   ><      less-than
   >>      greater-than



5.  `_self` IS USED BUT NEVER DEFINED
-------------------------------------

5.1  Problem Statement

Examples in Sections 8, 10, and 17 assume `_self` refers to the
currently executing Block, but the semantics never define such a
binding.

5.2  Required Correction (Option A — Special Binding)

Add a new semantic rule:

   When a Block B begins execution, the interpreter MUST bind a local
   Cell named `_self` whose payload is a CellRef referring to B.

This preserves all existing examples.

5.3  Alternative Correction (Option B — Remove Magic)

If `_self` is NOT given special meaning, all examples using it MUST
be rewritten to explicitly push the relevant Block or CellRef.

(SOMA v1.1 editors SHOULD choose one approach uniformly.)



6.  INVALID USE OF CELLREFS IN `>Chain` EXAMPLES
-----------------------------------------------

6.1  Problem Statement

Multiple examples incorrectly use `square.` or `toggle.` (CellRefs)
where a Block value is required.

Example:

   7 square. >Chain >print

Under current semantics:

   square.   → CellRef
   >Chain    → sees non-Block, halts

6.2  Required Correction

All such examples MUST replace trailing-dot paths with payload paths:

   7 square >Chain >print



7.  NON-FUNCTIONAL LOOP EXAMPLES
-------------------------------

7.1  Sections Affected

   §17.6  Infinite Loop
   §17.7  Simple Counter
   §17.8  Finite State Toggle

7.2  Problem Summary

All rely on `_self` (undefined) and/or leave non-Blocks atop AL after
execution, causing `>Chain` to terminate immediately.

7.3  Required Correction

If `_self` becomes a defined binding (Errata §5), then no further
change is required.

If `_self` is NOT defined, examples MUST be rewritten using explicit
named Cells that contain Blocks and refer to themselves via CellRefs.



8.  INVALID REFLECTION EXAMPLE
------------------------------

8.1  Problem Statement

Section 12.7 uses:

   True =? >Choose

The operator `=?` does not exist.

8.2  Required Correction

Replace §12.7 with the fully correct example already present in §17.9:

   "config.enabled" >ToPath
   { "Yes" >print }
   { "No"  >print }
   >Choose



9.  THINGS EXAMPLE USES UNBOUND IDENTIFIER
------------------------------------------

9.1  Problem Statement

Section 13.9 uses:

   >list              ; create new list Thing L
   "alpha" >push      ; L = ["alpha"]
   L !a.items         ; store into a.items

Identifier `L` is never bound.

9.2  Required Correction

Replace with:

   >list !L
   "alpha" L >push
   L !a.items



10.  GRAMMAR OMITS CELLREF RULE IN SEMANTICS
--------------------------------------------

10.1  Problem Statement

The abstract machine semantics (Section 15) define a Path Rule but do
not define a separate rule for CellRef resolution.

10.2  Required Correction

Add a rule:

   CellRef Path Rule

      For a trailing-dot path P.:

         C = cellref(P, Store)

      AL' = C :: AL
      Store' = Store
      IP' = IP + 1



11.  CLARIFY `>CHOOSE` AL CONTRACT
----------------------------------

11.1 Problem

Specification states:

   “The AL must contain: A B C >Choose”

But at execution time, the AL top holds:

   C (top), then B, then A

11.2 Correction

Replace text with:

   Immediately prior to `>Choose`, the top three AL values MUST be,
   in order from top downward:

      C, B, A

   corresponding to the program text: A B C >Choose



12.  REFLECTION EXAMPLE TRAILING `>Chain` MISLEADING
----------------------------------------------------

12.1 Problem

In §12.7, after the Choose branches, a `>Chain` is appended even though
neither block leaves a Block on the AL.

12.2 Correction

Remove trailing `>Chain` from that example.



13.  TYPOGRAPHIC CLARIFICATION (NON-NORMATIVE)
----------------------------------------------

Replace:

   "`>=`   Pop (b, a); push True if a == b"

With:

   "`>==`  Pop (b, a); push True if a == b"



14.  SUMMARY OF REQUIRED FIXES
------------------------------

A conforming revision to SOMA v1.0 MUST:

   • Add `!` write syntax to grammar
   • Add Nil and Void as literals
   • Expand builtin_name rule to allow symbolic built-ins
   • Standardize equality operator as `>==`
   • Either define `_self` or remove all `_self` usage
   • Correct examples using trailing-dot CellRefs with >Chain
   • Replace or remove §12.7 reflection example
   • Fix unbound `L` in Things example
   • Add CellRef rule to formal semantics
   • Clarify AL ordering for >Choose

These corrections do not alter SOMA’s semantic model. They ensure the
specification is complete, internally consistent, and fully
implementable.



15.  DOCUMENT STATUS
--------------------

This Errata is informational but NORMATIVE for any implementation
claiming to target SOMA v1.0 after its publication.

Future SOMA revisions (v1.1 or later) SHOULD integrate all changes
from this document into the main specification text.

_______________________________________________________________________


SOMA Void / Nil Semantics Addendum                        SOMA-ADDENDUM-VOID-1
For SOMA v1.0 Specification                                      17 Nov 2025
Category: Standards Track



Status of this Memo
-------------------

This document updates SOMA v1.0 by clarifying and finalizing the semantic
status of the Nil and Void literals. It defines the normative rules
governing their use, their legality in Store mutation, and their role in
the SOMA value space.

This addendum is **NORMATIVE**. Any implementation claiming conformance
to SOMA v1.0 **after publication of this document** MUST follow the rules
defined herein.



1.  OVERVIEW
------------

SOMA v1.0 distinguishes Nil and Void both conceptually and operationally.
This addendum makes that distinction explicit, precise, and unambiguous:

   • Nil is a legal Cell payload and general runtime literal.
   • Void is a literal that denotes non-existence, not emptiness.
   • Void MUST NOT be written into any Cell under any circumstances.

This preserves the Store invariant that Void represents **absence of a
Cell**, never a stored value.



2.  LITERAL DEFINITIONS (UPDATED)
---------------------------------

This section replaces the definitions of Nil (Section 4.5) and Void
(Section 4.6) in the SOMA v1.0 specification.


2.1  Nil

Nil is a literal value representing intentional emptiness.

A Cell containing Nil exists, but its payload is explicitly empty.

Nil:

   • MAY be pushed onto the AL
   • MAY be stored in any Cell as its payload
   • MAY be read back unchanged
   • Does NOT affect Store structure


2.2  Void

Void is a literal value representing **the absence of a Cell**.

Void is NOT a payload. It denotes that a path does not resolve to a Cell.

Void:

   • MAY be pushed onto the AL
   • MAY participate in AL-level logic or branching
   • MAY be used in structural deletion operations
   • MUST NOT be stored in any Cell
   • MUST NOT appear as a payload



3.  VOID IS NEVER A PAYLOAD
---------------------------

This rule is normative and absolute.

   VOID-PAYLOAD-INVARIANT:

      A SOMA Cell MUST NOT at any time contain Void as its payload.

If a Store mutation would require placing Void into a Cell as its payload,
that operation MUST be treated as a **fatal error**.

This invariant preserves the semantic distinction:

   Nil  = present but empty
   Void = not present at all



4.  STORE WRITE RULES (UPDATED)
-------------------------------

Section 6.4 of SOMA v1.0 is updated as follows:

Payload write:

   Val !path

   • Creates missing Cells as needed
   • Stores Val as payload
   • PRESERVES identity of existing Cells
   • MUST FAIL if Val is Void


4.1  Fatal Error Rule

The following form is illegal:

   Void !path

Attempting to perform a payload write where the AL top is Void and the
path is not trailing-dot MUST cause a fatal error:

   • No mutation
   • Execution halts for the current thread
   • Other threads continue


4.2  Structural Delete Rule

The following form is legal and unchanged:

   Void !path.

This form deletes the Cell at `path` (if present), including its subtree.
If the Cell is already absent, no action is taken.



5.  ABSTRACT MACHINE SEMANTICS (UPDATED)
----------------------------------------

The store mutation part of the transition function is extended with:

   If Val == Void and write_token is non-trailing-dot:

      • Execution transitions immediately to Fatal Halt
      • Store is unchanged
      • AL is unchanged
      • Other threads are unaffected



6.  EXAMPLES
------------

Legal:

   Nil !a.b
   a.b         ; AL = [Nil]

   x.z         ; AL = [Void]

---

Legal:

   Void !a.b.  ; deletes Cell a.b and its subtree

---

Fatal:

   Void !a.b   ; illegal: attempting to store Void

   ; Interpreter halts the current thread immediately



7.  TEST SUITE IMPACT
---------------------

The SOMA v1.0 conformance test suite SHALL be extended with:

   Test: Void cannot be stored

      Program:
         Void !a.b

      Expected:
         Fatal error
         Store unchanged

Implementations MAY also add:

   Test: Nil is storable

      Program:
         Nil !a.b
         a.b

      Expected AL:
         [Nil]



8.  COMPATIBILITY
-----------------

This clarification does not break conforming SOMA v1.0 programs,
because:

   • Void was never defined as storable
   • All normative examples continue to work
   • All mutation examples using Void already use it with trailing-dot

Programs that previously relied on storing Void were already undefined.



9.  SUMMARY
-----------

This addendum:

   • Canonically defines Nil and Void as literals
   • Guarantees Void is non-storable and purely structural
   • Codifies a fatal error for writing Void as a payload
   • Preserves AL usage of both literals
   • Retains structural deletion via Void !path.

This strengthens SOMA’s semantic clarity and enforces a clean Store model
in which:

   Nil  = empty value
   Void = no Cell exists



10.  DOCUMENT STATUS
--------------------

This addendum is formally part of SOMA v1.0.

All future SOMA specifications (including SOMA v1.1 and higher) MUST
incorporate this material into the body of the language definition.





