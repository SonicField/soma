# Debug Feature Ideas for SOMA

Status: Proposal

Created: 2025-12-01

Motivation: SOMA's execution-scope model vs lexical scope is invisible in code but critical to understanding behavior. Debug tools should make execution scope visible.

## The Core Challenge

In traditional languages like C++, you can see { and } creating lexical scopes. In SOMA, scope changes happen at runtime through >^ and >choose, creating **fresh Registers** that are isolated from parent contexts. This is invisible in the source code, making bugs extremely hard to diagnose.

Example of the problem:

```soma
Code block showing fresh Register isolation issue
```

The inner block gets a **fresh Register** when executed with >^, so _.value doesn't exist. This is correct SOMA semantics, but surprising to developers used to lexical scope.

## Priority 1: debug.register.dump - See Current Register State

### Motivation

Most SOMA bugs are "why can't I access this variable?" The Register is invisible, so developers don't know what's in scope.

### Proposed Behavior

```soma
debug.register.dump >^
```

Output:

```soma
DEBUG Register with bindings: _.old_list, _.new_list, _.new_new_list
```

### Implementation Notes

- Should be a builtin like debug.al.dump

- Prints each binding in the current Register

- Shows both path and value type/preview

- Does NOT consume any AL items

- Should work in any execution context

### Use Case

Debugging list.reverse, we could have added:

```soma
Code block with debug.register.dump showing captured values
```

This would have immediately revealed the variable swap bug.

## Priority 2: debug.scope.trace - Show Execution Scope Boundaries

### Motivation

Developers need to SEE when execution scope changes - when Registers get isolated. This is the fundamental mental model shift from lexical to execution scope.

### Proposed Behavior

Toggle tracing on/off with scope entry/exit messages

```soma
debug.scope.trace >^
```

```soma
Output shows SCOPE messages indicating Register isolation
```

### Advanced: Show context passing

```soma
Code demonstrating Register context passing via AL
```

```soma
Output showing context propagation through blocks
```

### Implementation Notes

- Global flag in VM: debug_scope_trace

- Hook into Block execution around line 990

- Hook into builtin_choose to trace branch selection

- Show Register size changes

## Priority 3: debug.chain.trace - Visualize Chain Execution

### Motivation

>chain loops are confusing because they repeatedly pop and execute blocks. Developers can't see the loop iterations or understand when/why the loop terminates.

### Proposed Behavior

```soma
debug.chain.trace with list.reverse example
```

```soma
Output shows iterations and termination condition
```

### Implementation Notes

- Global flag in VM: debug_chain_trace

- Hook into builtin_chain around line 1240

- Show AL state before each iteration

- Show what block is being executed

- Show why chain terminated: Nil vs empty AL

### Advanced: Show AL diffs

```soma
CHAIN iteration diff output
```

## Priority 4: Enhanced Error Messages with Execution Stack Trace

### Motivation

Current errors just show the path that failed. Developers need to see **where they are in the execution**, including which blocks are executing and what the AL/Register state is.

### Current Error

```soma
Simple error message format
```

### Proposed Enhanced Error

```soma
Enhanced error with full execution stack trace and context
```

### Implementation Notes

- Enhance VM to track execution stack

- Store: block name, source location, AL snapshot, Register snapshot

- When error occurs, unwind stack and format nicely

- Add helpful suggestions based on error type

  - Register undefined → suggest context-passing pattern

  - AL underflow → show AL state at error

  - CellRef access → show what the ref points to

### Stack Frame Structure

```python
ExecutionFrame dataclass with fields for debugging
```

## Implementation Strategy

### Phase 1: Basic Infrastructure

1. Add debug.register.dump builtin similar to debug.al.dump

2. Add global debug flags to VM

3. Test with existing list.reverse code

### Phase 2: Scope Tracing

1. Implement debug.scope.trace

2. Hook into Block execution

3. Hook into choose, chain, >^

### Phase 3: Chain Tracing

1. Implement debug.chain.trace

2. Show iterations and termination conditions

### Phase 4: Enhanced Errors

1. Add execution stack tracking to VM

2. Enhance error formatting

3. Add context-specific suggestions

## Design Principles

1. **Non-invasive**: Debug features should not affect normal execution

2. **Toggleable**: All tracing can be turned on/off

3. **Readable**: Output should be clear and concise

4. **Educational**: Errors should teach SOMA's execution model

5. **Minimal overhead**: When disabled, should have zero performance impact

## Future Ideas - Lower Priority

### debug.cellref.inspect - Show CellRef Contents

```soma
_.node debug.cellref.inspect >^
```

```soma
Output showing CellRef internals
```

### debug.al.snapshot / debug.al.diff - AL Comparison

```soma
AL snapshot and diff commands for state comparison
```

### debug.step - Interactive Step-Through

```soma
debug.step for pausing execution between operations
```

## Related Issues

- SOMA execution scope vs lexical scope - fundamental design

- Error messages need more context

- Learning curve for developers from traditional languages

## Success Metrics

Debug features are successful if:

1. "Why can't I access this variable?" questions decrease

2. Developers understand execution scope model faster

3. Debugging time decreases especially for context-passing bugs

4. Error messages are educational, not just diagnostic

Next Step: Implement debug.register.dump as proof-of-concept, then gather feedback.


