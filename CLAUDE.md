# token-mass

## What This Is

A token-free, deterministic repo diagnostic. Point it at a codebase; it builds a
Joern CPG, projects a file-level dependency graph, and reports the **shape** of
the structural working-cost (the "keyhole" difficulty). No LLM in the core path.

## Pipeline

```
repo → joern-parse (CPG) → tokenmass/extract.sc → methods.tsv + calls.tsv
     → tokenmass/analyze.py → markdown report
```

`token-mass` (bash) orchestrates the three stages.

## Design invariant

The **normalized graph** (nodes = files w/ token size, edges = dependencies) is
the seam between construction and analysis. Keep it that way:
- The extractor (`extract.sc`) may be language-/Joern-specific and imperfect.
- The analyzers (`analyze.py`) are pure graph algorithms and must stay
  language-agnostic — they consume only the normalized graph.

## Scope discipline

This is **diagnostic only**. It describes the shape of pain; it does not forecast
a bill and does not fix code. Every report metric carries its caveat. Do not add
"estimated cost = $X" outputs — that crosses into forecasting, which the project
deliberately refuses (the bill is dominated by agent behaviour the static graph
can't observe).

## Conventions

- Graph math in Python (stdlib only), CPG extraction in CPGQL.
- Reference tokenizer is a constant (chars/token); model-specific tokenizers are
  out of scope by design — the measure is model-free "mass," not per-model weight.
- Commit format: `scope(area): summary` (feat/fix/refactor/docs/chore).

## Prerequisites

Joern provisioned by `joern-mcp/scripts/install.sh` at `~/tools/joern-mcp/joern`.
