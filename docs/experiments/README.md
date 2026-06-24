# Experiments

Target-practice runs of `token-mass`, recorded for comparison. Sibling in spirit
to [llm-cpg-exploration](https://github.com/BlockSecCA/llm-cpg-exploration), which
ran the same CPG machinery against the same vulnerable app for *security* design
flaws. Here the question is different: **what shape is the codebase's structural
working-cost** - where would an LLM struggle to keyhole through it, and why -
answered with zero tokens, by graph analysis alone.

## Runs

| Target | Files | Edges | Verdict | Notable |
|---|---|---|---|---|
| [vulnerable-app](vulnerable-app.md) (Express/TS backend) | 250 | 551 | concentrated **+ high-stakes hubs** | `lib/insecurity.ts` fan-in 63; 5-file SCC; worst blast radius 77% of the codebase |

The vulnerable app's security primitives (`lib/insecurity.ts`) are a 63-dependent
hub - a change there re-implicates three-quarters of the codebase, which is both a
maintainability and a *security* observation. (For the opposite shape - low median,
no knot - run token-mass on a well-modularized repo; the fingerprint inverts.)

## Method challenges (read before trusting a verdict)

The honest limitations behind these results (what is measurement, what is
judgment) are recorded in [method-challenges.md](method-challenges.md). Short
version: the graph *measurements* are deterministic and trustworthy; the
categorical *verdict* is an uncalibrated heuristic, tuned to a tiny sample, and
should be read as a prompt, not a result.

## The methodology finding (the important one)

We built this **Joern-backed** (the CPG is the richer, multi-language graph). But
on the vulnerable app's TypeScript, **Joern's CPG under-resolved cross-file edges
in both directions**:

- CPG **call** edges resolved = 0 / 28,670 call sites (dynamic dispatch / higher-order calls)
- CPG **import** edges resolved = 0 / 1,025 specifiers (extension-less relative imports)

A Joern-only graph for TypeScript is near-empty and the verdict it produces is an
artifact of that sparsity. The fix - behind the same normalized-graph seam - is
**source-parsed import edges**, which are textually trivial and 100% reliable for
JS/TS. This empirically confirms the project's core thesis: *graph construction is
the language-dependent weak link; the analysis on top is universal.* For
statically-dispatched languages (Java/C/Go) the CPG edges should carry their
weight; for dynamic languages, source-parsed imports are the dependable source.

## Toward a presentation

These runs are the raw material for a write-up in the style of the sibling
project (chronological docs + a built presentation). Not yet built; the data and
the contrast are recorded here first.

> Caveat carried by every run: diagnostic, not predictive and not corrective.
> Candidates not verdicts; static graph only (DI/reflection coupling is invisible).
