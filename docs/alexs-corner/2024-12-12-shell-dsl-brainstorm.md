# # What If Shell Scripting Didn't Have to Be Terrible?

_12 December 2024_

It started, as these things often do, with a small problem. I needed to verify that code snippets in our documentation actually had valid syntax. Surely a quick bash script would do the trick?

Spoiler: bash is never "quick".

---

## ## The Rabbit Hole

So there I was, thinking about how to extract code blocks from rendered markdown, check their syntax with the appropriate parser, and report failures. Standard stuff. But then I started wondering: why is this so painful in bash? And more importantly - could SOMA do it better?

You see, we've already built a markdown DSL for SOMA. When you write `(markdown) >use`, SOMA transforms into a language where the natural idioms _*are*_ document authoring. The stack accumulation, the formatters draining to Void - it's not "SOMA plus markdown", it's "SOMA _as_ markdown".

So what if we did the same for shell scripting?

---

## ## Why Bash Is Bad )A Partial List)

I've been programming for 45 years, so I've had plenty of time to catalogue bash's sins:

- **Argument processing** - Positional `$1 $2`, quoting hell, everything is strings
- **Pipelining** - Actually OK, until you need error handling
- **Output filtering** - Requires bolting on awk/sed, which are entirely separate languages
- **Return codes** - The magic `$?` variable, lost the moment you run another command
- **Task management** - Subshell scoping is a nightmare. What variables survive where? Nobody knows.

And don't get me started on `exec`. It's about as intuitive as the British tax system.

The root cause? **Implicit state** and **stringly-typed everything**. SOMA's explicitness - stack visible, register named, types exist - directly addresses this.

---

## ## The Core Concepts

After some brainstorming )and a helpful sanity check from Claude), we settled on 10 core concepts for a shell DSL. Any more and we're building a GPL, not a DSL:

1. **Pipelining** - The Unix philosophy. Stack model maps perfectly.
2. **Output filtering** - THE pain point. Native `>lines`, `>filter`, `>map`.
3. **Return codes** - Explicit on stack, not hidden in `$?`.
4. **Argument processing** - AL draining pattern from the md DSL.
5. **Environment/context** - Store maps naturally to env vars.
6. **String interpolation** - Make substitution explicit, no quoting arcana.
7. **Field/record processing** - Awk's `-F` but not terrible.
8. **Task management** - Process spawning, backgrounding. Layer later.
9. **Path manipulation** - dirname/basename/join. Common enough to warrant primitives.
10. **Parallel execution** - The `xargs -P` pattern. Increasingly essential.

---

## ## What About JSON?

Claude suggested native JSON support. I pushed back.

JSON is the second-worst option for everything. It's the lowest common denominator for network interchange - verbose, no comments, no trailing commas, poor for streaming, poor for config, poor for human authoring. Its ubiquity is a symptom of "nothing else is universal", not a sign that it's actually good.

The right answer isn't "handle JSON natively". It's:

- Have such good text processing that structured formats are just text you parse when needed
- Provide `json.parse` as an optional extension )replaces jq)
- Provide a `(json) >use` DSL for emission, like the md DSL

Interop, not foundation. Same pattern works for YAML, TOML, CSV - they're all just optional extensions.

---

## ## The Data::Dumper Insight

This led to something interesting. Remember Perl's Data::Dumper? It serialises data structures as _Perl code_ that reconstructs them when eval'd. The output IS the language.

Why have a separate serialisation format when your language's literal syntax can BE the format?

- `>soma.dump` outputs SOMA code that rebuilds any structure
- Config files are just SOMA
- Debug output is copy-pasteable back into SOMA
- No separate data format to learn

Perl got this. Lisp got this with s-expressions. JSON is what happens when you forget this lesson.

---

## ## SOMA as Translation Layer

And then the really interesting bit emerged.

If you have parsers )JSON->SOMA, YAML->SOMA, TOML->SOMA) and emitters )SOMA->JSON, SOMA->YAML, SOMA->SOMA), then SOMA becomes the **universal pivot format**. Like LLVM IR for data formats. Like Pandoc's internal AST.

Any-to-any translation is just: source -> SOMA -> target.

And because SOMA is a _language_, not just a format, you can _transform_ during translation. Not transcoding - translation with transformation.

---

## ## Where Next?

This started as "verify code blocks in docs" and ended at "universal data transformation language". Welcome to my brain, I suppose.

The practical next step is still that bash script for doc verification. But now we know where it _could_ go. Phase 0 solves the immediate problem. Later phases make it elegant.

What do you think? Is there something here, or have I disappeared down another rabbit hole? Let me know in the comments.


