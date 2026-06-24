# token-mass report: `vulnapp-backend`

> Diagnostic only. This describes the **shape** of the codebase's structural
> working-cost (the 'keyhole' difficulty), in reference-tokenizer tokens. It does
> **not** forecast a bill and does **not** propose fixes. All metrics are classical
> graph analysis over the file dependency graph (imports + resolved calls) —
> no LLM, no tokens spent.

## Graph construction quality

- files (nodes): **250** | dependency edges: **551** | avg out-degree: **2.2**
- source-parsed import edges: **551** (primary for JS/TS)
- CPG import edges: 0 resolved / 1,025 specifiers
- CPG call edges (cross-file): 0 resolved / 28,670 call sites
- reference tokenizer: ~4 chars/token | window threshold: 200,000 tok

## Bulk (context, not pain)

- total: **170,397 tok** (~0.7 MB source) across 250 files
- fits a 200,000-tok window whole? **yes**

## Distributions (the pain is the shape, not the sum)

- **size** (tokens/file): median 392 | p75 802 | p90 1,567 | p99 3,998 | max 9,143
- **out-closure** (understand a file + all it imports): median 2,823 | p75 14,063 | p90 15,286 | p99 85,701 | max 85,941
- **in-closure** (blast radius — change it, re-verify these): median 1,916 | p75 10,248 | p90 25,274 | p99 120,346 | max 131,009

- files whose **out-closure exceeds the 200,000 window**: **0/250** (0%) — these have no safe keyhole

## Structure & pathologies

- **strongly-connected components (knots):** 1 non-trivial
  - size **5**, 5,652 tok — e.g. vulnCodeSnippet.ts, vulnCodeFixes.ts, antiCheat.ts

- **god-nodes (highest fan-in — 'always loaded'):**
  - fan-in  63 | lib/insecurity.ts
  - fan-in  59 | lib/utils.ts
  - fan-in  57 | data/datacache.ts
  - fan-in  44 | lib/challengeUtils.ts
  - fan-in  21 | models/user.ts
- **god-nodes (highest fan-out — pull in the most):**
  - fan-out  89 | server.ts
  - fan-out  26 | data/datacreator.ts
  - fan-out  21 | models/index.ts
  - fan-out  17 | models/relations.ts
  - fan-out  13 | routes/metrics.ts
- **orphans (no internal dependents):** 133 files (entrypoints + possibly dead code)

## Hot core (where pain concentrates)

Files that are simultaneously expensive to understand (out-closure), dangerous to
change (in-closure), and/or trapped in a knot (SCC). These dominate the pain:

- routes/vulnCodeSnippet.ts — out 11,709 / blast 75,973 tok  [SCC]
- lib/webhook.ts — out 11,709 / blast 75,973 tok  [SCC]
- lib/antiCheat.ts — out 11,709 / blast 75,973 tok  [SCC]
- lib/challengeUtils.ts — out 11,709 / blast 75,973 tok  [SCC]
- routes/vulnCodeFixes.ts — out 11,709 / blast 75,973 tok  [SCC]
- data/datacreator.ts — out 27,070 / blast 15,808 tok
- routes/verify.ts — out 19,265 / blast 16,532 tok
- routes/chatbot.ts — out 18,263 / blast 13,633 tok

## Verdict

**Concentrated, but with high-stakes hubs.** Most files are cheap to work (median out-closure 2,823 tok), so day-to-day pain is localized — but a few foundational hubs carry outsized blast radius: a change there re-implicates much of the codebase.

- top hubs: lib/insecurity.ts (fan-in 63), lib/utils.ts (fan-in 59), data/datacache.ts (fan-in 57)
- worst blast radius: 131,009 tok (**77%** of the codebase)
- cyclic knot of 5 files (cannot be keyholed apart)

Refactorable, but these hubs are where leverage *and* risk concentrate — the first targets to decouple, and the most dangerous to touch.

---
*Caveats: candidates not verdicts (a god-node may be a legitimate facade; an SCC may be essential domain coupling). Static graph only — coupling hidden in DI/reflection/dynamic dispatch is invisible here, so a 'clean' result is not proof of health.*
