# 

Debug Philosophy: Leveraging SOMA's Mutable Namespace

## Status: Reference Implementation Guide - Version SOMA v1.0 - Created 2025-12-01

Overview

This document establishes the design philosophy for all debugging tools in SOMA. Unlike traditional languages that require special VM hooks, debugging features, or runtime instrumentation, SOMA's debugging approach leverages its fundamental property: the namespace is mutable.

## The key insight: chain, choose, and other control flow primitives are not VM magic. They are just Store bindings that you can swap out.

### 1. Core Philosophy

State is Accessible, Not Hidden

SOMA's machine model exposes three explicit state components:

The Accumulator List AL - the value conduit

The Store - global persistent state

The Register - block-local isolated state

### Because these are explicit and introspectable, debugging tools don't need to peek behind abstraction layers. They just need to observe and report state transitions.

Debug Tools Should Not Modify the VM

The reference implementation's VM (soma/vm.py) defines SOMA's semantics. Debug tools should never require changes to the execution model, the semantics of >choose or >chain, the Register isolation model, or the AL manipulation primitives.

### Instead, debug tools work within SOMA's existing semantics by exploiting the mutable namespace.

The Pattern: Swap Store Bindings

```soma
All debug tools follow this pattern:
chain !backup.chain
debug.chain !chain
execute your code being debugged
backup.chain !chain
```

## This works because chain is just a path in the Store. When you write >chain, SOMA looks up chain in the Store, finds a Block, and executes that Block. By swapping the binding, you intercept the execution without modifying the VM.

### 2. Why This Works: Understanding SOMA's Execution Model

Control Flow is Not Special

In languages like Python or C++, if and while are keywords baked into the parser. You cannot redefine them.

In SOMA, >choose and >chain are builtins stored in the namespace. These are just Cells in the Store. The > operator looks up paths and executes blocks. There's nothing preventing you from replacing these bindings.

### Now every >choose in your program logs its execution.

Scoped Replacement via Backup/Restore

## The backup/restore pattern ensures debug instrumentation is scoped locally to specific code sections. This is zero-overhead when not in use and scoped to specific code sections.

3. Key Point: debug.* is NOT Part of the SOMA Spec

The SOMA language specification defines the machine model, the execution semantics, and the builtin primitives. It does not define debug.al.dump, debug.chain, debug.choose, or any other debugging utilities.

These are reference implementation tools provided in the standard library or as VM-provided helpers for convenience. They are not required for SOMA compliance.

## Implication: Different SOMA implementations can provide different debug tools. The pattern remains universal, but the specific tools are implementation-defined.

### 4. Current Debug Tools

4.1 debug.al.dump - Non-Destructive AL State Dump

Purpose: Inspect the current AL state without consuming any items.

Implementation: Builtin in vm.py

Usage: Call debug.al.dump >^ before and after operations to observe AL state changes.

Why it's a builtin: Requires direct access to vm.al to read without popping.

### Design principle: Zero side effects. The AL is unchanged after calling this.

4.2 debug.chain - Instrumented Chain Loop

Purpose: Log each iteration of a >chain loop, showing AL state before each block execution.

Implementation: Defined in stdlib.soma or as a VM helper

### Why this helps: Makes the invisible iteration process visible. Shows when each block executes, what the AL looks like before execution, and why the chain terminated.

4.3 debug.choose - Branch Selection Logger

Purpose: Log which branch >choose selects, making control flow visible.

Implementation: Defined in stdlib.soma

## Expected behavior: Logs the condition value and which branch was selected before executing it.

### 5. Design Principles for All Debug Tools

5.1 Zero Overhead When Not in Use

### If you don't install the debug version, there's zero performance impact. The original builtin executes directly. This is different from languages with debug mode flags that affect all execution. SOMA's approach is opt-in and granular.

5.2 Scoped to Specific Code Sections

### The backup/restore pattern ensures instrumentation is local to specific sections. You don't instrument the entire program—just the section you're debugging.

5.3 Educational: Shows SOMA's Execution Model

### Good debug output doesn't just say "error here." It teaches the user how SOMA executes. Debug tools should reveal when Registers are created and isolated, what's on the AL before and after operations, how >chain iterates, and why >choose selected a particular branch.

5.4 No VM Modifications Needed

## The reference implementation should not need changes to support debug tools. If a debug feature requires modifying the VM, it's the wrong approach. Find a way to implement it via Store binding replacement or AL/Register introspection. Exception: Built-in non-destructive introspection that cannot be implemented in pure SOMA.

6. Practical Example: Debugging a Problematic Loop

Let's debug the classic list.reverse implementation. The bug might be a typo in a variable name like _.new_new_list instead of _.new_list.

### Install the instrumented chain version. Run the failing code with debug output. The error message shows the iteration count, Register state, AL state, and which paths are available. This makes the bug immediately visible: Typo in variable name.

Why This Debug Pattern Works

Shows iteration count - We're only on iteration 1, so the bug happens immediately

Shows Register state - We can see what variables exist

Shows AL state - We can verify the right values are being passed

## Non-invasive - After restoring chain, the program runs normally

7. Future Debug Tools

### These follow the same philosophy:

7.1 debug.register.dump - Inspect Current Register

### Implementation: VM builtin - requires direct access to current Register.

7.2 debug.^ - Instrumented Block Execution

### Implementation: SOMA-level wrapper around the original ^ binding.

7.3 debug.step - Interactive Step-Through

## Implementation: Requires VM support for pausing execution, but still uses binding replacement pattern.

### 8. Contrast with Traditional Debuggers

Traditional Approach - GDB, pdb, etc.

### External tool that attaches to running process. VM modifications required for breakpoint hooks and stack introspection. Language-agnostic but requires deep runtime integration. Always available but potentially high overhead.

SOMA Approach

### Language-level tools defined in SOMA itself. No VM modifications required, uses mutable namespace. Language-specific and leverages SOMA's explicit state model. Opt-in with zero overhead when not in use.

Why SOMA's Approach Works

## SOMA's execution model is already explicit: The AL is visible, the Store is accessible, the Register can be introspected, control flow primitives are Store bindings. Traditional debuggers fight against hidden state. SOMA has no hidden state to fight against.

### 9. Guidelines for Implementing New Debug Tools

Step 1: Identify What You Need to Observe

### AL state transitions? Register bindings? Control flow decisions? Store modifications?

Step 2: Find the Interception Point

### Replacing a builtin like choose, chain, or ^. Wrapping a stdlib function like list.reverse or times. Adding introspection like debug.al.dump or debug.register.dump.

Step 3: Implement via Binding Replacement

### Create a wrapper block that logs or instruments operations, delegates to the original binding, and logs results if needed.

Step 4: Document the Backup/Restore Pattern

### Users should always save the original binding, install the instrumented version, run their code, and restore the original binding.

Step 5: Keep It Educational

## Debug output should teach SOMA's execution model, not just dump data. Good messages show context: iteration count, state before operations, why the program made decisions, and suggestions for what went wrong.

### 10. Limitations and Trade-offs

What This Approach Cannot Do

Time-travel debugging - SOMA's state is mutable and forward-only

Breakpoints at arbitrary tokens - Requires VM modification

Post-mortem inspection - Once a fatal error occurs, state is lost

### These would require VM changes or external tooling.

What This Approach Excels At

Scoped instrumentation - Debug specific functions without affecting the rest

Teaching execution model - Makes SOMA's semantics visible

Zero overhead - No performance cost when not in use

## Pure SOMA implementation - Most tools can be written in SOMA itself

11. Summary

SOMA's debug philosophy is simple: Leverage the mutable namespace. Use backup/restore pattern. Keep tools educational. Avoid VM modifications.

The result is a debugging approach that requires no special VM support, has zero overhead when not in use, teaches users how SOMA executes, and maintains the language's transparency and explicitness.

## Remember: debug.* is not part of the SOMA specification. It's a reference implementation tool demonstrating what's possible when the namespace is mutable and state is explicit.

```soma
Appendix: Complete Debug Pattern Template
chain !backup.chain
debug.chain !chain
your code here being debugged
backup.chain !chain
```


