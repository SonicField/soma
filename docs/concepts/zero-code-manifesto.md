# Zero-Code: The Anti-Vibe-Coding Manifesto

**Why specification + falsifiability beats "just prompt it"**

---

> _"Vibe coding is like vibe piloting a jet liner; it works till you hit the ground."_

---

## Why Vibe Coding Fails

Vibe coding feels productive. Code appears. Features materialise. The demo works. Ship it.

Then reality intrudes. Edge cases. Integration failures. Behaviour that "seemed right" but wasn't.

Two root causes:

**Underspecification**: A vibe is not a specification. "Make it better" contains no falsifiable criteria. Without falsifiable acceptance criteria, there is no definition of success. The AI generates _something_. The human accepts it because they cannot articulate why they shouldn't.

**Epistemic Drift**: All intelligence-based systems lose coherence over time. Context degrades. Assumptions compound. Without periodic re-grounding against falsifiable criteria, the AI's model of "what we're building" drifts from the human's intent. Both parties end up confident about the wrong thing.

---

## The Roles

| Role                 | Does                                                                                      | Does Not                                                         |
|----------------------|-------------------------------------------------------------------------------------------|------------------------------------------------------------------|
| **Engineer (Human)** | Specifies requirements, defines acceptance criteria, validates alignment, final sign-off  | Write implementation code, rubber-stamp without evidence         |
| **Machinist (AI)**   | Clarifies requirements, proposes falsifiers, implements, reports honestly, flags concerns | Decide what to build, declare "done" unilaterally, hide problems |

**The contract**: Neither party trusts assertions. Both parties trust evidence.

---

## The Workflow

### Phase 1: Specification

_Engineer leads_

Define what must be built and what would prove it wrong.

```markdown
## Requirement
[What must exist]

## Acceptance Criteria
- [ ] [Falsifiable condition 1]
- [ ] [Falsifiable condition 2]

## Out of Scope
[What this is NOT]
```

**Gate**: Machinist restates requirements. Engineer confirms understanding.

### Phase 2: Falsification Design

_Machinist proposes, Engineer approves_

Before any implementation: what tests would prove it wrong?

**Gate**: Both parties agree on what "done" means.

### Phase 3: Decomposition

_Machinist leads_

Break work into testable steps. **If you cannot write a test for a step, decompose further.**

**Gate**: Engineer acknowledges the plan.

### Phase 4: Implementation (TDD Loop)

_Machinist executes, Engineer reviews at checkpoints_

For each step:

```
TEST FIRST    → Write test; it must fail
IMPLEMENT     → Minimum code to pass
VERIFY        → All tests must pass
DOCUMENT      → Record what was learned
CHECKPOINT    → Report to Engineer with evidence
```

**Critical rule**: Never proceed past a failing test.

**Gate**: All steps complete, all tests passing.

### Phase 5: Integration

_Machinist executes_

Run full test suite against original acceptance criteria.

**Gate**: All acceptance tests pass.

### Phase 6: Sign-off

_Both parties_

Engineer reviews evidence, not assertions. Explicit acceptance required.

---

## The TDD Contract

1. **No implementation without a failing test** — the test defines success
2. **No more test than necessary to fail** — keep tests focused
3. **No more code than necessary to pass** — build what is tested, no more

TDD prevents drift: the growing test suite is evidence, not assertion. At any checkpoint, the Machinist demonstrates the state of the system.

---

## Communication

**Clarification request (Machinist → Engineer):**

- State what is ambiguous
- Propose interpretations
- Wait for decision. Do not guess.

**Checkpoint report (Machinist → Engineer):**

- Steps completed
- Test results (evidence, not claims)
- Concerns or blockers

**The Machinist's duty**: Flag contradictions, infeasibilities, ambiguities, and risks. Flagging is honesty, not failure.

---

## Anti-Patterns

| Anti-Pattern        | Why It Fails                    | Prevention                        |
|---------------------|---------------------------------|-----------------------------------|
| Vibe specification  | No falsifiable criteria         | Require acceptance criteria first |
| Rubber stamp        | Allows drift                    | Require evidence review           |
| Confident assertion | "It works" ≠ evidence           | Require test output               |
| Assumption cascade  | Misalignments compound          | Flag and wait                     |
| Skipped test        | Test fits code, not requirement | Test must fail first              |
| Monolithic step     | Errors hide                     | Decompose until testable          |
| Silent blocker      | Workarounds accumulate          | Duty to flag                      |

---

## The Promise

The AI is thousands of times faster at writing code. Speed without direction is just faster failure. Zero-Code harnesses the speed while the human provides direction.

- Falsifiability replaces trust
- TDD maintains coherence
- Respect flows both ways
- Problems surface early

No vibes. Just evidence.

---

_Prove you understand the problem by defining how you would falsify the solution, then build the solution, then record what you learned._

