# Debug Feature Ideas for SOMA

**Status**: Proposal
**Created**: 2025-12-01
**Motivation**: SOMA's execution-scope model (vs lexical scope) is invisible in code but critical to understanding behavior. Debug tools should make execution scope visible.

## The Core Challenge

In traditional languages like C++, you can see `{` and `}` creating lexical scopes. In SOMA, scope changes happen at runtime through `>^` and `>choose`, creating **fresh Registers** that are isolated from parent contexts. This is invisible in the source code, making bugs extremely hard to diagnose.

**Example of the problem:**
```soma
{
  42 !_.value        ) Store 42 in Register
  {
    _.value >print   ) ERROR: Undefined Register path!
  } >^               ) Fresh Register - can't see parent's _.value
}
```

The inner block gets a **fresh Register** when executed with `>^`, so `_.value` doesn't exist. This is correct SOMA semantics, but surprising to developers used to lexical scope.

## Priority 1: `debug.register.dump` - See Current Register State

### Motivation
Most SOMA bugs are "why can't I access this variable?" The Register is invisible, so developers don't know what's in scope.

### Proposed Behavior
```soma
debug.register.dump >^
```

**Output:**
```
DEBUG Register [3 bindings]:
  _.old_list → CellRef(140288411993056)
  _.new_list → Nil
  _.new_new_list → CellRef(140288411994112)
```

### Implementation Notes
- Should be a builtin like `debug.al.dump`
- Prints each binding in the current Register
- Shows both path and value type/preview
- Does NOT consume any AL items
- Should work in any execution context

### Use Case
Debugging `list.reverse`, we could have added:
```soma
{
  !_.old_list !_.new_list
  (After pops:) >print
  debug.register.dump >^   ) See exactly what we captured
  ...
}
```

This would have immediately revealed the variable swap bug.

---

## Priority 2: `debug.scope.trace` - Show Execution Scope Boundaries

### Motivation
Developers need to SEE when execution scope changes - when Registers get isolated. This is the fundamental mental model shift from lexical to execution scope.

### Proposed Behavior
Toggle tracing on/off:
```soma
debug.scope.trace >^       ) Turn on tracing

{ (inner block) >print } >^   ) Execution triggers trace

debug.scope.trace >^       ) Turn off tracing
```

**Output:**
```
SCOPE: → Entering new Register (via >^)
  Parent Register: 3 bindings
  New Register: empty
inner block
SCOPE: ← Exiting Register, returning to parent
```

### Advanced: Show context passing
```soma
debug.scope.trace >^

{
  !_.value
  _.                ) Push CellRef to Register onto AL
  {
    !_.             ) Pop CellRef, access parent Register
    _.value >print
  } >choose
} >^
```

**Output:**
```
SCOPE: → Entering new Register (via >^)
SCOPE: Pushing Register CellRef onto AL
SCOPE: → Entering new Register (via >choose)
SCOPE: Popping Register CellRef from AL - can now access parent
  Accessing: _.value (via CellRef)
SCOPE: ← Exiting Register
SCOPE: ← Exiting Register
```

### Implementation Notes
- Global flag in VM: `debug_scope_trace`
- Hook into Block execution (`vm.py` around line 990)
- Hook into `builtin_choose` to trace branch selection
- Show Register size changes

---

## Priority 3: `debug.chain.trace` - Visualize Chain Execution

### Motivation
`>chain` loops are confusing because they repeatedly pop and execute blocks. Developers can't see the loop iterations or understand when/why the loop terminates.

### Proposed Behavior
```soma
debug.chain.trace >^       ) Turn on

Nil >swap                  ) Setup for list.reverse
list.reverse.#loop
>chain                     ) Trace each iteration

debug.chain.trace >^       ) Turn off
```

**Output:**
```
CHAIN: Starting chain execution
CHAIN: iter 1: AL=[Nil, CellRef(0x7f8...), Block]
  → Executing Block from Store: list.reverse.#loop
  → Block returned: [CellRef(0x7f8...), Block]
CHAIN: iter 2: AL=[CellRef(0x7f8...), CellRef(0x7f9...), Block]
  → Executing Block from Store: list.reverse.#loop
  → Block returned: [CellRef(0x7f9...), Block]
CHAIN: iter 3: AL=[Nil]
  → Chain terminated: Nil encountered
```

### Implementation Notes
- Global flag in VM: `debug_chain_trace`
- Hook into `builtin_chain` (`vm.py` around line 1240)
- Show AL state before each iteration
- Show what block is being executed
- Show why chain terminated (Nil vs empty AL)

### Advanced: Show AL diffs
```
CHAIN: iter 2→3 diff:
  - Removed: CellRef(0x7f8...), Block
  + Added: CellRef(0x7f9...), Block
```

---

## Priority 4: Enhanced Error Messages with Execution Stack Trace

### Motivation
Current errors just show the path that failed. Developers need to see **where they are in the execution**, including which blocks are executing and what the AL/Register state is.

### Current Error
```
RuntimeError: Undefined Register path: '_.new_list'
  At: stdlib.soma:245 in list.reverse.#loop
```

### Proposed Enhanced Error
```
RuntimeError: Undefined Register path: '_.new_list'
  At: stdlib.soma:245 in list.reverse.#loop

Execution Stack:
  [0] list.reverse (stdlib.soma:259)
      Setup: AL=[CellRef(0x7f8...), Nil]
  [1] >chain iteration 2 (stdlib.soma:261)
  [2]   list.reverse.#loop (stdlib.soma:238)
      Loop block executing
  [3]     >choose FALSE branch (stdlib.soma:248)
          Register: ISOLATED (fresh from >choose)
          AL state: [CellRef(0x7f9...)]
  [4]       Register access: _.new_list
            ❌ Register has NO bindings (fresh scope!)

Did you forget to pass Register context via AL?
Use the pattern: `_.` before >choose, then `!_.` in branch.
```

### Implementation Notes
- Enhance VM to track execution stack
- Store: current block name, source location, AL snapshot, Register snapshot
- When error occurs, unwind stack and format nicely
- Add helpful suggestions based on error type
  - Register undefined → suggest context-passing pattern
  - AL underflow → show AL state at error
  - CellRef access → show what the ref points to

### Stack Frame Structure
```python
@dataclass
class ExecutionFrame:
    block_name: str           # "list.reverse.#loop"
    source_location: str      # "stdlib.soma:238"
    execution_type: str       # ">chain", ">^", ">choose TRUE"
    al_snapshot: List[Thing]  # Copy of AL at entry
    register_size: int        # Number of bindings
    is_isolated: bool         # Fresh Register?
```

---

## Implementation Strategy

### Phase 1: Basic Infrastructure
1. Add `debug.register.dump` builtin (similar to `debug.al.dump`)
2. Add global debug flags to VM
3. Test with existing `list.reverse` code

### Phase 2: Scope Tracing
1. Implement `debug.scope.trace`
2. Hook into Block execution
3. Hook into `choose`, `chain`, `>^`

### Phase 3: Chain Tracing
1. Implement `debug.chain.trace`
2. Show iterations and termination conditions

### Phase 4: Enhanced Errors
1. Add execution stack tracking to VM
2. Enhance error formatting
3. Add context-specific suggestions

---

## Design Principles

1. **Non-invasive**: Debug features should not affect normal execution
2. **Toggleable**: All tracing can be turned on/off
3. **Readable**: Output should be clear and concise
4. **Educational**: Errors should teach SOMA's execution model
5. **Minimal overhead**: When disabled, should have zero performance impact

---

## Future Ideas (Lower Priority)

### `debug.cellref.inspect` - Show CellRef Contents
```soma
_.node debug.cellref.inspect >^
```
Output:
```
CellRef(0x7f8...) → Cell:
  .value = (a)
  .next = CellRef(0x7f9...)
  .other = Nil
```

### `debug.al.snapshot` / `debug.al.diff` - AL Comparison
```soma
(before) debug.al.snapshot >^
... operations ...
(after) debug.al.snapshot >^
(before) (after) debug.al.diff >^
```

### `debug.step` - Interactive Step-Through
```soma
debug.step >^
{ ... } >^    ) Pause after each operation, wait for Enter
```

---

## Related Issues

- SOMA execution scope vs lexical scope (fundamental design)
- Error messages need more context
- Learning curve for developers from traditional languages

---

## Success Metrics

Debug features are successful if:
1. **"Why can't I access this variable?"** questions decrease
2. Developers understand execution scope model faster
3. Debugging time decreases (especially for context-passing bugs)
4. Error messages are educational, not just diagnostic

---

**Next Step**: Implement `debug.register.dump` as proof-of-concept, then gather feedback.
