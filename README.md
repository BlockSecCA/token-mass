# token-mass

How expensive is a codebase to *work on* through a keyhole — and can you tell
before spending a single token finding out?

A codebase too big for any context window has to be worked through a "keyhole":
you load slices, not the whole thing. The token cost of that is **not** the bulk;
it's how much you must load per task, which is a property of the **dependency
graph**, not the line count. token-mass measures that shape — with classical
graph analysis, **no LLM and no tokens spent**.

It is the sibling of
[llm-cpg-exploration](https://github.com/BlockSecCA/llm-cpg-exploration): the same
CPG machinery, a different question. That project asked whether an LLM could find
*security* design flaws in code it never reads. This one asks where a codebase
will *hurt* to work on, and answers it deterministically, for free.

```bash
./token-mass /path/to/repo report.md
```

## What was done, and why

The premise came from a simple FinOps-for-AI observation: you pay for tokens by
the token, regardless of value, so the cheapest way to manage token pain is to
spend as little as possible *finding* it. Locating a codebase's structural
working-cost is a graph problem — closures, coupling, cycles — and graph problems
are solved, deterministic, and token-free. So the expensive, non-deterministic LLM
is reserved for the two things only it can do (completing edges a parser can't
resolve, and judging whether a flagged structure is really a problem); everything
in between is classical graph theory.

**The "hurt" is the LLM's, and the unit is tokens.** The cost token-mass measures
is what an *LLM* spends to work a codebase through its context-window keyhole — not
a claim about human developer experience. (The same structural pain has long been
studied as human maintainability cost; see [Prior art](#prior-art-and-references).
What's LLM-specific here is the *lens* and the *unit*.) The motivation is
**tokenomics**: the economics of LLM tokens. For the broader effort, see the
emerging Linux Foundation tokenomics work at
[tokeneconomics.com](https://www.tokeneconomics.com/) — token-mass shares that
motivation, though it uses its own reference-token counting rather than
(necessarily) any notions they adopt.

It is **diagnostic, not predictive and not corrective**:

- it tells you the **shape** of the challenge (concentrated vs diffuse pain, the hot core, the knots);
- it does **not** forecast a token bill (the bill is dominated by agent behaviour — loops, retries, cache — which structure can't see);
- it does **not** fix anything (it names refactor *targets*; it doesn't rank or cost the refactor).

## Usage

**Prerequisites:** Joern provisioned at `~/tools/joern-mcp/joern` (via
[`joern-mcp/scripts/install.sh`](https://github.com/BlockSecCA/joern-mcp));
Python 3 (stdlib only). You do **not** need to start a Joern server — token-mass
calls `joern-parse` directly.

**Run it:**

```bash
cd ~/repos/public/token-mass
./token-mass <repo-or-subtree> <report.md>
```

**Point it at the right thing.** Joern parses *everything* under the directory you
give it, so keep it off `node_modules`, build output, and unrelated subtrees.
Either point at the source subtree:

```bash
./token-mass /path/to/repo/src report.md
```

or stage a clean copy first (for repos with vendored or frontend dirs):

```bash
rsync -a --exclude node_modules --exclude .git --exclude dist \
         --exclude build --exclude frontend \
         /path/to/repo/ /tmp/staged/
./token-mass /tmp/staged report.md
```

**Read the report top-down, but check one thing first:**

1. **Graph construction quality** — if edge resolution is low, the shapes below are a floor, not the truth.
2. The distributions, structure/pathologies, and hot core are **measurements** (deterministic — trust them).
3. The **verdict** is a prompt for judgment, not a result (see [method-challenges](docs/experiments/method-challenges.md)).

**Know the limits:**

- **Language:** validated on TypeScript (JS likely fine). Other languages run via Joern's CPG edges but are untested; the source-import densifier is JS/TS-only.
- **Safety:** static analysis only — it never installs or runs the target, so it is safe to point at untrusted code.
- **Time:** the CPG build scales with code size (large repos take minutes).
- **Ergonomics gap:** no `--exclude` flag yet, which is why the staging step exists (planned).

## How it works

```
repo ──► Joern CPG ──► normalized graph (files + dependency edges) ──► graph analysis ──► report
        (joern-parse)   (extract.sc + imports_from_source.py)          (analyze.py)
```

The **normalized graph** (nodes = files sized in reference tokens, edges =
dependency links) is the seam: swap the extractor without touching the analyzers,
and the analyzers stay language-agnostic because graph theory doesn't care about
the language. (For JS/TS the edges come from source-parsed imports, because the
CPG under-resolves dynamic languages — see the methodology note below.)

## Results

Two runs, on two **public** repos, producing two distinct fingerprints from the
same token-free analysis:

| Target (public repo) | Graph | Verdict | Signature | Report |
|---|---|---|---|---|
| [GitNexus](https://github.com/BlockSecCA/GitNexus) (TypeScript) | 68 files, 157 edges | concentrated, **clean** | shared-types hub only, no cycles, thin tail | [gitnexus.md](docs/experiments/gitnexus.md) |
| [vulnerable-app](https://github.com/BlockSecCA/vulnerable-app) (Express/TS) | 250 files, 551 edges | concentrated, **high-stakes hubs** | `lib/insecurity.ts` fan-in 63; a 5-file SCC; worst blast radius 77% of the codebase | [vulnerable-app.md](docs/experiments/vulnerable-app.md) |

The vulnerable app's security primitives (`lib/insecurity.ts`) being a
63-dependent hub is simultaneously a maintainability and a security observation,
surfaced with zero tokens. GitNexus is the clean control case.

## The report

- **Graph construction quality** — node/edge counts, resolution rate (honest about under-counting on dynamic languages)
- **Bulk** — total tokens (context only, *not* the pain)
- **Distributions** — size, out-closure (comprehension cost), in-closure (blast radius), and the over-window fraction
- **Structure & pathologies** — SCCs (knots), god-nodes (fan-in/out), orphans
- **Hot core** — the files where understanding-cost, change-cost, and knots coincide
- **Verdict** — a heuristic label (read [the caveats](docs/experiments/method-challenges.md))

## Reading order

- **[docs/experiments/](docs/experiments/README.md)** — the index, and the methodology finding behind the runs
- **[gitnexus.md](docs/experiments/gitnexus.md)** — run on a clean public repo
- **[vulnerable-app.md](docs/experiments/vulnerable-app.md)** — run on the framework-heavy public target
- **[method-challenges.md](docs/experiments/method-challenges.md)** — the limitations that require judgment (read before trusting a verdict)

## Methodology note (the honest part)

The graph *measurements* (closures, SCCs, fan-in, distributions) are deterministic
and trustworthy. The two soft spots, recorded in
[method-challenges.md](docs/experiments/method-challenges.md):

1. **Graph construction is language-dependent.** Joern's CPG under-resolves
   TypeScript cross-file edges in both directions; source-parsed imports are used
   instead. A report is only as good as its "Graph construction quality" section.
2. **The verdict is an uncalibrated heuristic.** Its thresholds were tuned to fit
   these two repos (N=2). Trust the numbers and the named offenders; treat the
   categorical label as a prompt for judgment, not a measurement.

## Tools

| Tool | Role |
|------|------|
| [Joern](https://joern.io) (v4.0.489) | CPG engine (`joern-parse`, CPGQL extraction) |
| [joern-mcp](https://github.com/BlockSecCA/joern-mcp) | provisions/owns the Joern engine (`scripts/install.sh`) |
| Python 3 (stdlib only) | graph analysis + source-import edges |

## Prerequisites

- **Joern**, provisioned by [`joern-mcp/scripts/install.sh`](https://github.com/BlockSecCA/joern-mcp) (engine at `~/tools/joern-mcp/joern`)
- **Python 3** (standard library only)

## Status & follow-ups

v1 runs end-to-end on JS/TS. Known follow-ups: cross-check the constructed graph
against an independent tool (e.g. madge / tsc) so wrong edges are caught, not just
sparse ones; corpus-calibrate or drop the categorical verdict; fix the
order-dependent per-source edge count; add community/seam detection and the
prescriptive layer (counterfactual graph edits scored by pain-reduction). A
presentation in the style of the sibling project is planned; the runs above are
the recorded raw material.

## Prior art and references

token-mass is a **re-derivation, not a discovery**. The mechanisms here are
established, and several groups have gone considerably further into specific areas.
They are recorded here in honesty, as the territory this work turned out to occupy
and as pointers to those who went deeper:

- **Change-propagation / dependency-structure metrics.** The closures and
  blast-radius computed here are MacCormack et al.'s *propagation cost* over a
  dependency-structure matrix (the transitive-closure "visibility" matrix). Shipped
  in tools like [Lattix](https://docs.lattix.com/lattix/userGuide/Metrics.html),
  applied to real systems (Almossawi,
  [*Evolution of the Firefox Codebase*](https://almossawi.com/firefox/)), and
  extended by others into longitudinal architecture-debt quantification, further
  than this tool goes. Foundational paper:
  [MacCormack, Rusnak & Baldwin, *Exploring the Structure of Complex Software Designs* (2006)](https://dash.harvard.edu/server/api/core/bitstreams/7312037d-5c4d-6bd4-e053-0100007fdf3b/content).
- **Classic coupling / complexity metrics.** Fan-in/fan-out (Henry & Kafura, 1981),
  cyclomatic complexity (McCabe, 1976), instability and the "zone of pain"
  (R. C. Martin). The god-node and pathology section is these, re-derived.
- **Graph-as-context for LLMs.** Using a code graph to fit a repo into an LLM
  context within a token budget is already shipped in
  [Aider's repo-map](https://aider.chat/docs/repomap.html) (personalized PageRank,
  token-budgeted), with clones (RepoMapper, repo-graph MCP) and an arXiv treatment,
  [*Repository Intelligence Graph: Deterministic Architectural Map for LLM Code Assistants*](https://arxiv.org/pdf/2601.10112).
  These go further on the *selection / scheduling* use; token-mass stops at diagnosis.

### A note on origin

Unlike the sibling
[llm-cpg-exploration](https://github.com/BlockSecCA/llm-cpg-exploration), whose
inspiration came *from* the CPG-for-LLM literature (and which cites it), this
project's inspiration came from a **tokenomics** discussion: the FinOps-for-AI
question of how a codebase's structure drives token cost. It reached propagation
cost and repo-map territory *independently*, from the cost side rather than the
software-architecture side. So it converges on this prior work rather than
descending from it — which is why it re-derives rather than builds on it. The
references above are recorded after the fact, not as sources.

## Author

Carlos / [BlockSecCA](https://github.com/BlockSecCA)

## License

MIT
