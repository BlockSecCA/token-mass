# token-mass report: `src`

> Diagnostic only. This describes the **shape** of the codebase's structural
> working-cost (the 'keyhole' difficulty), in reference-tokenizer tokens. It does
> **not** forecast a bill and does **not** propose fixes. All metrics are classical
> graph analysis over the file dependency graph (imports + resolved calls) —
> no LLM, no tokens spent.

## Graph construction quality

- files (nodes): **68** | dependency edges: **157** | avg out-degree: **2.3**
- source-parsed import edges: **28** (primary for JS/TS)
- CPG import edges: 249 resolved / 382 specifiers
- CPG call edges (cross-file): 0 resolved / 31,558 call sites
- reference tokenizer: ~4 chars/token | window threshold: 200,000 tok

## Bulk (context, not pain)

- total: **173,858 tok** (~0.7 MB source) across 68 files
- fits a 200,000-tok window whole? **yes**

## Distributions (the pain is the shape, not the sum)

- **size** (tokens/file): median 1,825 | p75 3,389 | p90 5,562 | p99 15,036 | max 15,036
- **out-closure** (understand a file + all it imports): median 5,393 | p75 27,530 | p90 56,284 | p99 170,166 | max 170,166
- **in-closure** (blast radius — change it, re-verify these): median 14,334 | p75 38,255 | p90 53,538 | p99 93,230 | max 93,230

- files whose **out-closure exceeds the 200,000 window**: **0/68** (0%) — these have no safe keyhole

## Structure & pathologies

- **strongly-connected components (knots):** 0 non-trivial
  - none — the dependency graph is a DAG (no irreducible cyclic core)

- **god-nodes (highest fan-in — 'always loaded'):**
  - fan-in  12 | core/graph/types.ts
  - fan-in  10 | storage/repo-manager.ts
  - fan-in   8 | mcp/local/local-backend.ts
  - fan-in   6 | core/ingestion/utils.ts
  - fan-in   6 | lib/utils.ts
- **god-nodes (highest fan-out — pull in the most):**
  - fan-out  15 | core/ingestion/pipeline.ts
  - fan-out  12 | cli/index.ts
  - fan-out  10 | server/api.ts
  - fan-out  10 | core/ingestion/parsing-processor.ts
  - fan-out   9 | core/ingestion/call-processor.ts
- **orphans (no internal dependents):** 4 files (entrypoints + possibly dead code)

## Hot core (where pain concentrates)

Files that are simultaneously expensive to understand (out-closure), dangerous to
change (in-closure), and/or trapped in a knot (SCC). These dominate the pain:

- mcp/local/local-backend.ts — out 40,044 / blast 38,255 tok
- core/kuzu/csv-generator.ts — out 7,842 / blast 57,312 tok
- core/ingestion/workers/parse-worker.ts — out 23,279 / blast 41,870 tok
- mcp/resources.ts — out 44,304 / blast 18,464 tok
- core/kuzu/kuzu-adapter.ts — out 15,149 / blast 53,538 tok
- core/ingestion/import-processor.ts — out 34,918 / blast 23,728 tok
- core/search/bm25-index.ts — out 18,782 / blast 42,842 tok
- core/ingestion/framework-detection.ts — out 4,748 / blast 53,826 tok

## Verdict

**Concentrated pain.** Low median closure, thin tail, no severe hubs: the codebase is cheap to work almost everywhere, and the expense is a small set of named hotspots (see Hot core). Localized and refactorable.

> *The verdict label is an uncalibrated heuristic (thresholds fit to few repos), not a measurement. Trust the numbers and named offenders above; treat the label as a prompt for judgment. See [method-challenges.md](method-challenges.md).*

---
*Caveats: candidates not verdicts (a god-node may be a legitimate facade; an SCC may be essential domain coupling). Static graph only — coupling hidden in DI/reflection/dynamic dispatch is invisible here, so a 'clean' result is not proof of health.*
