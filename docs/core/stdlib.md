# 10. Standard Library

The SOMA standard library demonstrates compositional power from simple primitives.

## Overview

- Boolean Logic
- Comparison Operators
- Stack Manipulation
- Arithmetic Helpers
- Control Flow Helpers
- Linked List Operations
- AL Draining

## 1. Boolean Logic

### >not — Boolean Negation

`Signature: (Bool) -> Bool`

`{False True >choose} !not`

### >and — Logical AND

`Signature: (Bool, Bool) -> Bool`

`{False >choose} !and`

### >or — Logical OR

`Signature: (Bool, Bool) -> Bool`

`{True >swap >choose} !or`

## 2. Comparison Operators

### >> — Greater-Than

`Signature: (Value, Value) -> Bool`

`{>swap ><} !>`

### >!=! — Not Equal

`Signature: (Value, Value) -> Bool`

`{>over >over >swap >< >rot >rot >< >or} !=!`

### >== — Equality

`Signature: (Value, Value) -> Bool`

`{>=! >not} !==`

### >=< — Less-Than-Or-Equal

`Signature: (Value, Value) -> Bool`

`{>swap >< >not} !=<`

### >=> — Greater-Than-Or-Equal

`Signature: (Value, Value) -> Bool`

`{>< >not} !=>`

## 3. Stack Manipulation

### >dup — Duplicate Top

`Signature: (Value) -> (Value, Value)`

`{!_.value _.value _.value} !dup`

### >drop — Remove Top

`Signature: (Value) -> ()`

`{!_} !drop`

### >swap — Swap Top Two

`Signature: (a, b) -> (b, a)`

`{!_.a !_.b _.a _.b} !swap`

### >over — Copy Second to Top

`Signature: (a, b) -> (a, b, a)`

`{!_.a !_.b _.b _.a _.b} !over`

### >rot — Rotate Top Three

`Signature: (a, b, c) -> (b, a, c)`

`{!_.a !_.b !_.c _.b _.a _.c} !rot`

## 4. Arithmetic Helpers

### >inc — Increment by 1

`Signature: (Int) -> Int`

`{1 >+} !inc`

### >dec — Decrement by 1

`Signature: (Int) -> Int`

`{1 >-} !dec`

### >abs — Absolute Value

`Signature: (Int) -> Int`

`{>dup 0 >< {0 >swap >-} {} >choose >^} !abs`

### >min — Minimum of Two

`Signature: (Int, Int) -> Int`

`{>over >over >< {>drop} {>swap >drop} >choose >^} !min`

### >max — Maximum of Two

`Signature: (Int, Int) -> Int`

`{>over >over >> {>drop} {>swap >drop} >choose >^} !max`

## 5. Control Flow

### >if — Conditional Execution

`Signature: (condition, block) -> (...)`

`{{} >choose >^} !if`

### >ifelse — Conditional with Both Branches

`Signature: (condition, true_block, false_block) -> (...)`

`{>choose >^} !ifelse`

### >^ — Execute from AL

`Signature: (block) -> (result)`

`{!_ >_} !^`

## 6. Linked Lists

### >list.new — Create Empty List

Returns Nil representing empty list.

### >list.cons — Prepend Value to List

`Signature: (Value, List) -> CellRef`

## Design Philosophy

All operations are user-defined blocks, not primitives.

Boolean logic builds from `>choose`.

Comparisons build from `><` and boolean ops.

Stack operations use Register paths for local state.

Control flow uses `>chain` for iteration.

The FFI kernel is tiny; everything else is composable.

