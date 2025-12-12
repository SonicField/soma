# How Building a Language Taught Me to Stop Vibe Coding

_12 December 2025_

I didn't set out to develop a philosophy of AI collaboration. I just wanted to build a weird little language.

---

## It Started With Curiosity

Well, "started" is a bit generous. The truth is, this particular itch has been bothering me for about twenty years.

Back around 2005, I built something called VSPL - the Very Simple Programming Language. Implemented in Java, stack-based, blocks as first-class values. It worked, sort of. But it was rough. I didn't really understand what I was reaching for.

Twenty years is a long time. In that span I've led compiler teams, built bank finance systems, worked on VR, and spent far too many hours making Python go fast. Each domain taught me something. Compilers taught me about representation. Finance taught me about correctness under pressure. VR taught me about state management. Python taught me that elegance and performance aren't enemies.

SOMA is what happens when you let all that percolate. The stack-based core comes from VSPL, but the _interesting_ bits - cell-referenced graphs, the insight that builtins are just Store paths so DSLs become transparent, the way you can replicate Lisp's macro power without needing a macro system - those emerged from two decades of learning by doing.

We might be slow at learning, but we sure do a lot of it given enough time.

So in late 2025, when I finally sat down to build this properly, I had Claude Code as my collaborator.

And here's where things got interesting.

---

## The First Lesson: Context Is Mortal

On the first day, I hit context compaction. You know the feeling - you've been deep in conversation with the AI, building up shared understanding, and then suddenly it's gone. Compressed. The AI remembers the broad strokes but has lost the nuances, the gotchas, the "oh, we tried that and it didn't work because..."

My first reaction was frustration. How can you build anything complex when your collaborator keeps forgetting?

But then something clicked. **Context compaction isn't a bug - it's a forcing function.** It was pushing me to crystallise understanding into artefacts that would survive. Documentation. Tests. Skill guides. If I wanted the knowledge to persist, I had to write it down _properly_, not just chat about it.

This felt oddly familiar. It's what good engineering teams do anyway - they don't rely on tribal knowledge living in people's heads. They document. They test. They create systems that survive personnel changes.

The AI was teaching me to be a better engineer by having a terrible memory.

---

## The Second Lesson: Tests Are Truth

Here's the thing about working with an AI that can write code faster than you can read it: speed amplifies everything. Good decisions compound faster. Bad decisions compound faster too.

Early on, I'd describe what I wanted, Claude would implement it, and I'd say "looks good" without really verifying. We were vibe coding - it _felt_ right, the demo worked, ship it.

Then the bugs started appearing. Edge cases we'd missed. Behaviour that "seemed right" but wasn't quite. And the worst part? I couldn't always tell if Claude had misunderstood my specification or if my specification had been wrong in the first place.

So we switched to test-driven development. Properly. Not "write tests after" but "write tests first, make them fail, then implement."

The difference was transformative. Tests became _executable specifications_ - falsifiable claims about what the system should do. If we disagreed about behaviour, we wrote a test. If context compaction happened, the tests remained. They were truth that survived forgetting.

I started to realise: the tests weren't just checking the code. They were checking _our shared understanding_.

---

## The Third Lesson: Roles Matter

Something subtle shifted in how I thought about the collaboration. I stopped thinking of Claude as "the AI that writes code" and started thinking in terms of roles.

I was the _engineer_ - responsible for specification, for knowing what we were building and why, for defining success criteria. Claude was the _machinist_ - responsible for implementation, for flagging concerns, for honest reporting of what was and wasn't working.

Neither role was superior. Both were essential. And crucially - **neither trusted the other's assertions without evidence**.

If Claude said "it works," I'd ask to see the test output. If I said "this is the right approach," Claude would (rightly) push back with edge cases I hadn't considered. We weren't being adversarial. We were being _epistemically honest_.

Trust the evidence. Question the assertions. Even your own.

---

## The Accidental Research Project

Somewhere along the way, I realised I'd stopped thinking primarily about SOMA. Oh, we were still building it - and it was coming along nicely - but the _interesting_ thing had become the process itself.

We'd stumbled into a methodology. Specification before implementation. Falsifiable acceptance criteria. Test-driven development as the anchor. Documentation as a first-class artefact. Explicit roles with explicit contracts.

None of this was new, of course. Good engineers have known these things for decades. But AI collaboration _amplifies_ their importance. When your collaborator works a thousand times faster than you, you can't afford to be vague. When context compaction is inevitable, you can't afford to skip documentation. When the AI can confidently generate plausible-looking nonsense, you can't afford to trust without verification.

The old disciplines become non-negotiable.

---

## Zero-Code

I've started calling this approach "zero-code" - a deliberate counterpoint to "vibe coding." Not because there's no code (there's plenty), but because the _code isn't the point_. The point is the specification, the tests, the evidence. The code is just what falls out when you've done those properly.

The **[Zero-Code Manifesto](/docs/concepts/zero-code-manifesto.md)** captures the philosophy in more rigorous terms. It's deliberately a bit stern - it's meant to be a corrective to the seductive ease of "just prompt it and see what happens."

But really, it all comes back to one principle: **falsifiability**. If you can't articulate what would prove you wrong, you don't actually know what you're claiming. And if you don't know what you're claiming, how can you know if the AI has delivered it?

---

## Where SOMA Fits

SOMA is still being built. It's become a sort of test bed for these ideas - a complex enough project that the methodology actually matters, but constrained enough that I can hold the whole thing in my head (with documentation's help).

And there's a pleasing recursion to it. SOMA is a language designed around explicitness - stack visible, execution explicit, no hidden state. Zero-code is a methodology designed around the same principles. They're both reactions against the same enemy: _implicit assumptions that accumulate until the system becomes incomprehensible_.

Maybe that's what I was really building all along. Not a language. A way of thinking clearly in an age where it's very easy not to.

---

_I'd love to hear if any of this resonates with your own experience. What's worked for you in AI collaboration? What's failed spectacularly? Let me know._


