# token-mass

Point it at a repo, say go, get a report on the **shape of the codebase's
structural working-cost** — where an LLM will struggle to keyhole through it,
and why.

```bash
./token-mass /path/to/repo report.md
```

## What it does (and doesn't)

A codebase too big for any context window has to be worked through a "keyhole" —
you load slices, not the whole thing. The token cost of doing that is **not** the
bulk; it's how much you must load per task, which is a property of the
**dependency graph**, not the line count. token-mass measures that shape.

It is **diagnostic, not predictive and not corrective**:

- it tells you the **shape** of the challenge (concentrated vs diffuse pain, the hot core, the knots);
- it does **not** forecast a token bill (the bill is dominated by agent behaviour — loops, retries, cache — which structure can't see);
- it does **not** fix anything (it names refactor *targets*; it doesn't rank or cost the refactor).

Crucially, the whole analysis is **classical graph algorithms — no LLM, no tokens
spent.** You use cheap deterministic computation to locate the expensive resource's
pain before committing it.

## How it works

```
repo ──► Joern CPG ──► normalized graph (files + dependency edges) ──► graph analysis ──► report
        (joern-parse)   (tokenmass/extract.sc)                         (tokenmass/analyze.py)
```

The normalized graph (nodes = files sized in reference tokens, edges = dependency
links) is the seam: swap the extractor without touching the analyzers, and the
analyzers stay language-agnostic because graph theory doesn't care about the
language.

## The report

- **Graph construction quality** — node/edge counts, resolution rate (honest about under-counting on dynamic languages)
- **Bulk** — total tokens (context only, *not* the pain)
- **Distributions** — size, out-closure (comprehension cost), in-closure (blast radius), and the over-window fraction
- **Structure & pathologies** — SCCs (knots), god-nodes (fan-in/out), orphans
- **Hot core** — the files where understanding-cost, change-cost, and knots coincide
- **Verdict** — concentrated (localized, refactorable) vs diffuse (systemic) pain

## Prerequisites

- **Joern**, provisioned by [`joern-mcp/scripts/install.sh`](https://github.com/BlockSecCA/joern-mcp) (engine at `~/tools/joern-mcp/joern`)
- **Python 3** (standard library only)

## Status

v1: Joern builds the CPG; for JS/TS the dependency edges come from source-parsed
imports (the CPG under-resolves dynamic languages). **Read
[docs/experiments/method-challenges.md](docs/experiments/method-challenges.md)
before trusting a verdict**: the measurements are deterministic, but the
categorical verdict is an uncalibrated heuristic.

Known follow-ups: cross-check the constructed graph against an independent tool
(e.g. madge / tsc for TS) so wrong edges are caught, not just sparse ones;
corpus-calibrate or drop the categorical verdict; fix the order-dependent
per-source edge count; add community/seam detection and the prescriptive layer
(counterfactual graph edits scored by pain-reduction). Sibling project to
[llm-cpg-exploration](https://github.com/BlockSecCA/llm-cpg-exploration), which
runs the same CPG machinery for *security* design pathologies.

## License

MIT
