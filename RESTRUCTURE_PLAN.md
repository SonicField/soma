# SOMA Documentation Restructure Plan

## Status: APPROVED - PHASE 1 READY
**Created**: 2024-12-06
**Last Updated**: 2024-12-06
**Approved**: 2024-12-06

---

## Overview

This document tracks the restructuring of SOMA's documentation and tooling to:
1. Organize docs into logical subdirectories
2. Elevate markdown system from examples to top-level
3. Elevate soma runner to top-level
4. Convert all .md files to .soma source with build system
5. Create docs/concepts for engineering-focused documentation

---

## Current Structure (Before)

```
soma/
├── docs/                          # 19 .md files, flat structure
│   ├── 01-philosophy.md (20K)
│   ├── 02-lexer.md (39K)
│   ├── 03-machine-model.md (67K)
│   ├── 04-blocks-execution.md (40K)
│   ├── 05-control-flow.md (43K)
│   ├── 06-builtins.md (11K)
│   ├── 07-comparisons.md (29K)
│   ├── 08-examples.md (81K)       # LARGEST
│   ├── 09-idioms.md (17K)
│   ├── 10-errors-semantics.md (69K)
│   ├── 11-stdlib.md (47K)
│   ├── 12-extensions.md (18K)
│   ├── 13-debugging.md (17K)
│   ├── IDEAS_FOR_DEBUG_FEATURES.md (8K)
│   ├── index.md (4K)
│   ├── SKILL.md (27K)
│   └── extensions/
│       ├── index.md (6K)
│       ├── Load.md (11K)
│       └── Python-Interface.md (21K)
├── examples/
│   ├── markdown/                  # 14 files - WILL MOVE TO TOP LEVEL
│   │   ├── SKILL.md (26K)
│   │   ├── SKILL-COMPACT.md (4.6K)
│   │   ├── markdown-user-guide.soma (49K)
│   │   ├── markdown-examples.soma (13K)
│   │   └── ... (9 more files)
│   ├── soma_runner/
│   │   └── soma.py (1.2K, 48 lines)  # WILL MOVE
│   ├── ffi/
│   └── sin_calculator/
├── soma/                          # Source code
│   ├── lexer.py
│   ├── parser.py
│   ├── vm.py (55K - largest)
│   ├── stdlib.soma
│   └── extensions/
├── tests/
├── editors/
│   └── vim/
├── README.md
├── LICENSE
└── (other root files)
```

**Total .md files: 40**
- Documentation: 23
- Examples: 10
- Planning/Development: 4
- GitHub Templates: 3

---

## Target Structure (After)

```
soma/
├── docs/
│   ├── core/                      # Core language spec
│   │   ├── index.md
│   │   ├── philosophy.md          # was 01-philosophy.md
│   │   ├── lexer.md               # was 02-lexer.md
│   │   ├── machine-model.md       # was 03-machine-model.md
│   │   ├── blocks-execution.md    # was 04-blocks-execution.md
│   │   ├── control-flow.md        # was 05-control-flow.md
│   │   ├── builtins.md            # was 06-builtins.md
│   │   └── stdlib.md              # was 11-stdlib.md
│   ├── programming/               # Programming patterns & semantics
│   │   ├── comparisons.md         # was 07-comparisons.md
│   │   ├── examples.md            # was 08-examples.md
│   │   ├── idioms.md              # was 09-idioms.md
│   │   └── errors-semantics.md    # was 10-errors-semantics.md
│   ├── debugging/                 # Debug-related docs
│   │   ├── debugging.md           # was 13-debugging.md
│   │   └── debug-ideas.md         # was IDEAS_FOR_DEBUG_FEATURES.md
│   ├── skills/                    # AI assistant guides
│   │   └── SKILL.md               # core SOMA skill
│   ├── extensions/                # Already exists, enhanced
│   │   ├── index.md
│   │   ├── extensions.md          # was 12-extensions.md
│   │   ├── load.md                # was Load.md
│   │   └── python-interface.md    # was Python-Interface.md
│   ├── markdown/                  # Markdown system docs (from examples)
│   │   ├── index.md               # was README.md
│   │   ├── SKILL.md               # updated from SKILL-COMPACT.md
│   │   ├── quickstart.md
│   │   ├── css.md                 # was CSS-README.md
│   │   └── wrap-script.md         # was WRAP-SCRIPT-README.md
│   ├── concepts/                  # NEW: Engineering concepts
│   │   └── engineering-standards.md
│   └── index.md                   # Main entry point
├── markdown/                      # ELEVATED from examples/markdown
│   ├── markdown-user-guide.soma
│   ├── markdown-examples.soma
│   ├── html_example.soma
│   ├── run_example.py
│   ├── soma-document.css
│   ├── template.html
│   └── wrap-html.sh
├── soma/                          # Source code (add runner)
│   ├── __main__.py                # NEW: soma.py moved here as entry point
│   ├── lexer.py
│   ├── parser.py
│   ├── vm.py
│   ├── stdlib.soma
│   └── extensions/
├── examples/                      # Remaining examples
│   ├── ffi/
│   └── sin_calculator/
├── build_docs.sh                  # NEW: Build all docs from .soma
├── tests/
├── editors/
└── (root files)
```

**Naming changes:**
- Drop numeric prefixes (01-, 02-, etc.)
- Lowercase with hyphens for consistency
- Keep SKILL.md uppercase (AI convention)

---

## Phase 1: Directory Structure Changes

### Task 1.1: Create new doc subdirectories
- [ ] Create docs/core/
- [ ] Create docs/programming/
- [ ] Create docs/debugging/
- [ ] Create docs/skills/
- [ ] Create docs/concepts/
- [ ] Create docs/markdown/

### Task 1.2: Move and rename docs to core/
- [ ] 01-philosophy.md → core/philosophy.md
- [ ] 02-lexer.md → core/lexer.md
- [ ] 03-machine-model.md → core/machine-model.md
- [ ] 04-blocks-execution.md → core/blocks-execution.md
- [ ] 05-control-flow.md → core/control-flow.md
- [ ] 06-builtins.md → core/builtins.md
- [ ] 11-stdlib.md → core/stdlib.md

### Task 1.3: Move and rename docs to programming/
- [ ] 07-comparisons.md → programming/comparisons.md
- [ ] 08-examples.md → programming/examples.md
- [ ] 09-idioms.md → programming/idioms.md
- [ ] 10-errors-semantics.md → programming/errors-semantics.md

### Task 1.4: Move and rename docs to debugging/
- [ ] 13-debugging.md → debugging/debugging.md
- [ ] IDEAS_FOR_DEBUG_FEATURES.md → debugging/debug-ideas.md

### Task 1.5: Move and rename docs to extensions/
- [ ] 12-extensions.md → extensions/extensions.md
- [ ] Load.md → extensions/load.md (lowercase)
- [ ] Python-Interface.md → extensions/python-interface.md (lowercase)

### Task 1.6: Setup skills/
- [ ] Move docs/SKILL.md → docs/skills/SKILL.md

### Task 1.7: Elevate markdown system
- [ ] Move examples/markdown/ to top-level markdown/
- [ ] Move markdown docs to docs/markdown/:
  - README.md → index.md
  - SKILL-COMPACT.md → SKILL.md (enhanced)
  - QUICKSTART.md → quickstart.md
  - CSS-README.md → css.md
  - WRAP-SCRIPT-README.md → wrap-script.md
- [ ] Delete old examples/markdown/SKILL.md (26K verbose version)

### Task 1.8: Elevate soma runner
- [ ] Move examples/soma_runner/soma.py to soma/__main__.py
- [ ] Update import paths in soma/__main__.py
- [ ] Verify `python -m soma` works as entry point
- [ ] Update examples/soma_runner/README.md or remove

### Task 1.5: Update cross-references
- [ ] Update docs/index.md with new structure
- [ ] Update root README.md
- [ ] Check all internal links in docs

---

## Phase 2: SOMA Source Conversion

### Task 2.1: Create build system
- [ ] Create build_docs.sh skeleton
- [ ] Test with one simple .md conversion
- [ ] Iterate until reliable

### Task 2.2: Convert docs (parallel agents by size)

**Batch 1 - Largest (parallel):**
- [ ] programming/examples.md (81K) → programming/examples.soma
- [ ] programming/errors-semantics.md (69K) → programming/errors-semantics.soma
- [ ] core/machine-model.md (67K) → core/machine-model.soma

**Batch 2 - Large (parallel):**
- [ ] core/stdlib.md (47K) → core/stdlib.soma
- [ ] core/control-flow.md (43K) → core/control-flow.soma
- [ ] core/blocks-execution.md (40K) → core/blocks-execution.soma

**Batch 3 - Medium (parallel):**
- [ ] core/lexer.md (39K) → core/lexer.soma
- [ ] programming/comparisons.md (29K) → programming/comparisons.soma
- [ ] extensions/python-interface.md (21K) → extensions/python-interface.soma

**Batch 4 - Smaller (parallel):**
- [ ] core/philosophy.md (20K) → core/philosophy.soma
- [ ] extensions/extensions.md (18K) → extensions/extensions.soma
- [ ] debugging/debugging.md (17K) → debugging/debugging.soma
- [ ] programming/idioms.md (17K) → programming/idioms.soma

**Batch 5 - Small (parallel):**
- [ ] extensions/load.md (11K) → extensions/load.soma
- [ ] core/builtins.md (11K) → core/builtins.soma
- [ ] debugging/debug-ideas.md (8K) → debugging/debug-ideas.soma
- [ ] extensions/index.md (6K) → extensions/index.soma

### Task 2.3: Convert remaining docs
- [ ] docs/index.md (4K)
- [ ] docs/skills/SKILL.md
- [ ] docs/markdown/SKILL.md
- [ ] docs/markdown/index.md
- [ ] docs/markdown/quickstart.md
- [ ] docs/markdown/css.md
- [ ] docs/markdown/wrap-script.md

### Task 2.4: Finalize build system
- [ ] build_docs.sh handles all conversions
- [ ] Add to git pre-commit hook (optional)
- [ ] Document in README

---

## Phase 3: Add docs/concepts

### Task 3.1: Initial content
- [ ] Copy engineering_standards.soma from ~/docs/
- [ ] Render engineering-standards.md
- [ ] Update docs/index.md to reference concepts/

### Task 3.2: Future concepts (not this session)
- [ ] Testing methodology
- [ ] Debugging philosophy
- [ ] Other engineering topics

---

## Parallel Execution Strategy

### Phase 1: Sequential (requires coordination)
Execute tasks 1.1-1.5 in order, single agent or direct execution.

### Phase 2: Parallel conversion
Launch multiple agents simultaneously:
- Agent batch 1: 08-examples.md, 10-errors-semantics.md, 03-machine-model.md
- Agent batch 2: 11-stdlib.md, 05-control-flow.md, 04-blocks-execution.md
- Agent batch 3: 02-lexer.md, 07-comparisons.md, 01-philosophy.md
- Agent batch 4: Remaining smaller files

Each agent:
1. Reads the .md file
2. Converts to .soma using patterns from engineering_standards.soma
3. Runs soma to render .md
4. Verifies output matches original intent (not byte-for-byte)
5. Reports success/issues

### Phase 3: Sequential (small tasks)

---

## Progress Log

### 2024-12-06
- [x] Parallel exploration of current structure (4 agents)
- [x] Created this restructure plan
- [x] User feedback incorporated:
  - Renamed idioms/ to programming/
  - Added 07-comparisons, 10-errors-semantics to programming/
  - Moved 11-stdlib to core/
  - Dropped numeric prefixes from all filenames
- [x] Plan APPROVED - ready for Phase 1
- [x] **Phase 1 COMPLETE**:
  - Created directories: core/, programming/, debugging/, skills/, concepts/, docs/markdown/
  - Moved 7 files to core/ (dropped numeric prefixes)
  - Moved 4 files to programming/
  - Moved 2 files to debugging/
  - Updated extensions/ (3 files renamed to lowercase)
  - Setup skills/ with SKILL.md
  - Elevated markdown/ to top level (from examples/markdown/)
  - Moved markdown docs to docs/markdown/
  - Elevated soma runner to soma/__main__.py (verified working)
  - Updated docs/index.md with new Table of Contents
  - Copied engineering_standards.soma to docs/concepts/
  - Added engineering-standards.md to concepts/

---

## Notes and Learnings

### From engineering_standards.soma work:
- Use `>concat` for multi-line source that renders as continuous prose
- Definition lists (`>md.dul`) auto-bold terms, no need for `>md.b`
- Stack items, format once (SOMA's core pattern)
- Escape `)` as `\29\`, `\` as `\5C\`
- `(` does NOT need escaping
- Comments use `) text` format

### Path adjustments needed:
- soma.py currently uses `Path(__file__).parent.parent.parent` to find soma root
- When moved to soma/__main__.py, will need `Path(__file__).parent`

### Files to NOT convert:
- .github templates (GitHub-specific format)
- LICENSE, CODE_OF_CONDUCT.md (standard formats)
- CONTRIBUTING.md (standard format)

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Context compaction loses progress | This document tracks all state |
| Conversion changes meaning | Human review of key docs |
| Broken links after restructure | Systematic link check task |
| soma.py path breaks | Test immediately after move |

---

## Approval Checklist

Before starting Phase 1:
- [x] User approves target structure
- [x] User approves file categorization
- [ ] User confirms which docs to convert vs keep as .md
