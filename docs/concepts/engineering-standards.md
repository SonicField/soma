# Engineering Standards: A Verification-First Approach

## Philosophy and Principles

This document defines engineering standards built on a fundamental insight: **safety comes from verbs, not nouns**. Correctness emerges from actions - checking, validating, asserting, testing, monitoring - not from static structures like type systems or design patterns. The act of verification matters more than the classification system.

### Core Tenets

- **Falsifiability as Foundation**: You cannot prove code correct, but you CAN prove it wrong. A single counterexample demolishes a claim. Tests should try to break code, not confirm it works. "All tests pass" provides weak confidence; "I tried hard to break it and failed" provides strong confidence.
- **Verbs Over Nouns**: Correctness comes from actions, not classifications. "This value was validated" matters more than "this has type ValidatedInput". The verb happened or it didn't. The assertion passed or it failed. That's provable.
- **Types Are Hints, Not Guarantees**: Type systems are incomplete - they cannot express "this list is sorted" or "this connection is authenticated". Types constrain design toward what the checker can verify, not what the problem demands. Use types as documentation, but rely on assertions and invariants for correctness.
- **Test the Real System**: Mocks hide integration failures. Real systems have real network latency, real concurrency, real resource contention, real failure modes. Integration-first testing, with targeted unit tests only for complex isolated logic.
- **The Cycle of Verified Construction**: Design, Plan, Deconstruct into testable steps. For each step: write tests FIRST, then write code to make tests pass, then document learnings before moving to next step. This is not optional ceremony - it is the engine of quality.

---

_Prove you understand the problem by defining how you would falsify the solution, then build the solution, then record what you learned._

---

## The Assertion Protocol

Assertions are not optional debugging aids to be disabled in production. They are executable specifications - documentation that verifies itself. A triggered assertion is proof of a bug, not merely a hint.

### The Three-Level Hierarchy

- **Level 1: Preconditions (Entry Guards)**
  - Verify assumptions about inputs before processing
  - Fail fast with clear messages when violated
  - Document what the function requires to operate correctly
- **Level 2: Postconditions (Exit Guarantees)**
  - Verify promises about outputs before returning
  - Capture relationships between inputs and outputs
  - Detect corruption that occurred during processing
- **Level 3: Invariants (Always-True Properties)**
  - Properties that must hold at all times
  - Checked at key state transitions
  - Represent fundamental system correctness constraints

### Example: All Three Levels

```python
def transfer_funds(from_account, to_account, amount):
    # PRECONDITIONS - what must be true on entry
    assert from_account != to_account, "Cannot transfer to same account"
    assert amount > 0, f"Amount must be positive, got {amount}"
    assert from_account.balance >= amount, \
        f"Insufficient funds: {from_account.balance} < {amount}"

    # Capture state for postcondition
    old_total = from_account.balance + to_account.balance

    # Perform the operation
    from_account.balance -= amount
    to_account.balance += amount

    # POSTCONDITION - what must be true on exit
    assert from_account.balance + to_account.balance == old_total, \
        "Invariant violated: money created or destroyed"

    # INVARIANT - always true for accounts
    assert from_account.balance >= 0, "Account balance went negative"
    assert to_account.balance >= 0, "Account balance went negative"
```

### Assertion Messages

Every assertion message should answer three questions:

- **What**: was expected?
- **What**: actually occurred?
- **Why**: does this matter?

```python
# BAD: States the obvious
assert x > 0, "x must be greater than 0"

# GOOD: Provides context and values
assert x > 0, f"Request count must be positive for rate limiting, got {x}"

# BEST: Actionable guidance
assert x > 0, \
    f"Request count must be positive for rate limiting, got {x}. "
    f"Check if the counter was reset incorrectly or input validation failed."
```

## Testing for Falsification

Traditional testing asks "does it work for these examples?" Falsification testing asks "can I find any input that breaks it?" The difference is profound: one confirms, the other challenges.

### Property-Based Testing

Instead of testing specific examples, define properties that must
always hold, then generate many inputs to search for counterexamples:

```python
# Example-based: proves almost nothing
def test_sort_example():
    assert sort([3, 1, 2]) == [1, 2, 3]

# Property-based: actively seeks counterexamples
def test_sort_properties():
    for _ in range(1000):
        data = generate_random_list()
        result = sort(data)

        # Property 1: Output is sorted
        assert all(result[i] <= result[i+1]
                   for i in range(len(result)-1))

        # Property 2: Output is permutation of input
        assert sorted(result) == sorted(data)

        # Property 3: Idempotent
        assert sort(result) == result
```

### Adversarial Input Generation

For any function, systematically generate inputs designed to break it:

- **`Empty inputs`**: empty strings, empty lists, zero, None
- **`Boundary values`**: MAX_INT, MIN_INT, epsilon around boundaries
- **`Type confusion`**: strings where numbers expected, nested structures
- **`Resource exhaustion`**: very large inputs, deeply nested structures
- **`Malformed data`**: invalid UTF-8, truncated data, corruption
- **`Timing attacks`**: race conditions, reordering, delays

### Integration-First Methodology

- **AVOID**
  - Unit test with mocks → Unit test with mocks → Integration test (maybe)
- **PREFER**
  - Integration test (real system) → Targeted unit tests for complex logic

The real system reveals what mocks hide:

- Network latency and timeouts
- Concurrency and race conditions
- Resource contention and deadlocks
- Configuration mismatches
- Real failure modes and error messages

### Decomposition Criterion: Testability

**If you cannot write a test for a step, you haven't decomposed it far enough, or you don't understand it yet.**

- **BAD decomposition** - "Implement authentication" (How do you test this?)
- **GOOD decomposition**:
  - Validate password meets complexity rules
  - Hash password with salt
  - Compare hash against stored hash
  - Generate session token on success
  - Return appropriate error on failure

Each step is independently testable. Each test defines what success means.

## The Development Cycle in Practice

### The Cycle of Verified Construction

1. **DESIGN**
  - Understand the problem before proposing solutions
  - Identify constraints, dependencies, and risks
  - Define what success looks like
2. **PLAN**
  - Structure the approach before writing code
  - Identify the sequence of changes
  - Anticipate integration points and failure modes
3. **DECONSTRUCT into testable steps**
  - Break work into independently verifiable units
  - Each step must have a clear test criterion
  - If you can't test it, decompose further
4. **For each step: TEST FIRST**
  - Write the test before the implementation
  - The test defines what would falsify success
  - Include adversarial cases, not just happy paths
5. **For each step: WRITE CODE**
  - Implement to make tests pass
  - Include assertions for preconditions and postconditions
  - Write clear, maintainable code
6. **For each step: DOCUMENT LEARNINGS**
  - What did you learn? (Often different from expected)
  - What assumptions were validated or invalidated?
  - What edge cases emerged?
  - Do this BEFORE moving to next step
7. **NEXT STEP**
  - Repeat until complete
  - Each step builds on verified foundation

### Phase Entry and Exit Criteria

| Phase     | Entry Criterion          | Exit Criterion               |
|-----------|--------------------------|------------------------------|
| Design    | Problem statement exists | Success criteria defined     |
| Plan      | Success criteria clear   | Testable steps identified    |
| Decompose | Steps identified         | Each step has test criterion |
| Test      | Test criterion defined   | Test code written and fails  |
| Code      | Test fails correctly     | Test passes, assertions hold |
| Document  | Test passes              | Learnings recorded           |

## Runtime Verification

Verification extends beyond tests into production. The same assertions that catch bugs in development can detect corruption in production - if you let them.

### Health Checks and Watchdogs

- **Self-checks**: Periodic verification of internal invariants
- **Dependency checks**: Verify external services remain available
- **Data integrity checks**: Validate critical data hasn't corrupted
- **Watchdog timers**: Detect hung processes or infinite loops

### Graceful Degradation

When a runtime assertion fails in production:

1. **Log**: Capture full context for debugging
2. **Alert**: Notify operators immediately
3. **Contain**: Prevent corruption from spreading
4. **Degrade**: Fall back to safe mode if possible
5. **Recover**: Attempt automatic recovery or await intervention

**Never silently continue after an invariant violation. The data is no longer trustworthy.**

## AI-Accelerated Development

AI processing power transforms verification from impractical ceremony into routine practice. Use AI to handle the verification burden that makes rigorous approaches infeasible for most software.

### AI Capabilities by Phase

| Phase     | AI Contribution                                                |
|-----------|----------------------------------------------------------------|
| Design    | Explore patterns, identify constraints, analyze existing code  |
| Plan      | Verify completeness, identify missing steps, find dependencies |
| Decompose | Suggest testable units, identify implicit assumptions          |
| Test      | Generate adversarial cases, property-based tests, edge cases   |
| Code      | Implement with assertions, verify against tests                |
| Document  | Summarize learnings, trace to requirements                     |

### Context Management Principles

- **Delegate exploration to agents**: Don't read large files directly
- **Parallel analysis**: Launch multiple agents for independent tasks
- **Structured summaries**: Agent analysis beats raw file dumps
- **Preserve context for implementation**: Don't waste tokens on exploration

### AI-Assisted Test Generation

AI can systematically generate tests that humans often miss:

- **Boundary conditions**: Values at edges of valid ranges
- **Null and empty cases**: What happens with nothing?
- **Type coercion edge cases**: String "0" vs integer 0
- **Unicode edge cases**: Emoji, RTL text, zero-width characters
- **Concurrency scenarios**: Race conditions, deadlocks
- **Resource exhaustion**: What breaks under load?

## Language-Specific Patterns

The philosophy is portable across all languages.
These patterns show concrete implementations.

### Python

```python
# Assertions - use liberally
assert precondition, f"Meaningful message with {context}"

# Property-based testing with Hypothesis
from hypothesis import given, strategies as st

@given(st.lists(st.integers()))
def test_sort_properties(data):
    result = sort(data)
    # Properties checked automatically for many inputs
    assert is_sorted(result)
    assert is_permutation(result, data)

# Type hints as documentation (not enforcement)
def process(data: list[int]) -> list[int]:
    """Types hint intent; assertions verify it."""
    assert isinstance(data, list), f"Expected list, got {type(data)}"
    return sorted(data)
```

### Shell/Bash

```bash
#!/bin/bash
# Strict mode - fail fast on errors
set -euo pipefail

# Assertions via guard functions
assert_file_exists() {
    local file="$1"
    [[ -f "$file" ]] || {
        echo "ASSERTION FAILED: File not found: $file" >&2
        exit 1
    }
}

assert_not_empty() {
    local var_name="$1"
    local var_value="$2"
    [[ -n "$var_value" ]] || {
        echo "ASSERTION FAILED: $var_name is empty" >&2
        exit 1
    }
}

# Use assertions
assert_not_empty "CONFIG_PATH" "$CONFIG_PATH"
assert_file_exists "$CONFIG_PATH"
```

### C/Systems Programming

```c
/* Assertions with context */
#define ASSERT_MSG(cond, msg, ...) do { \
    if (!(cond)) { \
        fprintf(stderr, "ASSERT FAILED %s:%d: " msg "\n", \
                __FILE__, __LINE__, ##__VA_ARGS__); \
        abort(); \
    } \
} while(0)

/* Defensive programming */
void* safe_malloc(size_t size) {
    ASSERT_MSG(size > 0, "Allocation size must be positive: %zu", size);
    ASSERT_MSG(size < MAX_ALLOC, "Allocation too large: %zu", size);

    void* ptr = malloc(size);
    ASSERT_MSG(ptr != NULL, "malloc failed for size %zu", size);

    return ptr;
}

/* Postcondition verification */
int* create_sorted_array(int* input, size_t len) {
    int* result = /* ... sorting logic ... */;

    /* Postcondition: result is sorted */
    for (size_t i = 1; i < len; i++) {
        ASSERT_MSG(result[i-1] <= result[i],
                   "Sort postcondition violated at index %zu", i);
    }

    return result;
}
```

## Anti-Patterns and Failure Modes

### Anti-Pattern 1: The Quick Fix Trap

**WRONG:**

```python
# Skip this for now, fix later
if problematic_condition:
    return None  # TODO: handle properly
```

**RIGHT:**

```python
# Understand root cause, fix properly
assert not problematic_condition, \
    f"Unexpected state: {context}. Investigate why this occurs."
```

### Anti-Pattern 2: Mock-Heavy Testing

**WRONG:**

```python
# Everything mocked - tests pass, integration fails
@mock.patch('database')
@mock.patch('network')
@mock.patch('filesystem')
def test_everything_mocked():
    # This test proves nothing about real behavior
    pass
```

**RIGHT:**

```python
# Test real integration, mock only external dependencies
def test_with_real_database(test_db):
    # Uses real database, real queries
    result = service.process(test_db)
    assert result.saved_to_db()
```

### Anti-Pattern 3: Type-System False Confidence

**WRONG:**

```python
# "It type-checks, therefore it's correct"
def process(data: ValidatedInput) -> SafeOutput:
    # Types say it's valid, but is it really?
    return transform(data)
```

**RIGHT:**

```python
# Types hint, assertions verify
def process(data: ValidatedInput) -> SafeOutput:
    assert data.is_actually_validated(), \
        "ValidatedInput was not actually validated"
    result = transform(data)
    assert result.meets_safety_criteria(), \
        "Transform produced unsafe output"
    return result
```

### Anti-Pattern 4: Silent Failure

**WRONG:**

```python
try:
    risky_operation()
except Exception:
    pass  # Silently swallow all errors
```

**RIGHT:**

```python
try:
    risky_operation()
except SpecificException as e:
    logger.error("Operation failed: %s. Context: %s", e, context)
    raise OperationError(f"Failed with {e}") from e
```

### Anti-Pattern 5: Skipping the Cycle

- **WRONG**: "I'll write tests after the code works"
- **WRONG**: "Documentation can wait until the end"
- **WRONG**: "It's a small change, no need to plan"
- **RIGHT**: Follow the cycle every time, adjust scope to match

## Summary and Quick Reference

### The Cycle (Memorize This)

**Design → Plan → Deconstruct → [Test → Code → Document] → Next**

### The Philosophy (Internalize This)

- Safety through verbs, not nouns.
- Falsifiability as the foundation.
- Types as hints, assertions as guarantees.
- Test the real system.
- Document before moving on.

### The Questions (Ask Every Time)

- **Before implementing**: What would falsify this?
- **Before committing**: Did I try to break it?
- **Before moving on**: What did I learn?

---

**_Prove you understand the problem by defining how you would falsify the solution, then build the solution, then record what you learned._**


