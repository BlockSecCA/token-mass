#!/usr/bin/env python3
"""
analyze.py — turn the normalized graph (methods.tsv + calls.tsv) into a
diagnostic report on a codebase's structural "bill-pain" shape.

Everything here is classical graph analysis. No LLM, no tokens. The report
describes the SHAPE of the challenge (where working-cost concentrates); it does
not forecast a bill and does not fix anything.

Usage: analyze.py <methods.tsv> <calls.tsv> <repo_root> <out.md> [reference_tokenizer_chars_per_token]
"""
import sys, os, collections
from pathlib import Path

methods_tsv, calls_tsv, repo_root, out_md = sys.argv[1:5]
CPT = int(sys.argv[5]) if len(sys.argv) > 5 else 4   # generic reference tokenizer
WINDOW = 200_000                                     # a representative context window
repo_root = Path(repo_root).resolve()

# ---- resolution helpers (canonical file key = absolute disk path) -----------
def resolve(raw):
    for c in (Path(raw), repo_root / raw, repo_root / Path(raw).name):
        try:
            if c.is_file():
                return c.resolve()
        except OSError:
            pass
    return None

def canon(raw):
    p = resolve(raw)
    return str(p) if p else raw

# ---- load method -> file map ------------------------------------------------
m2f = {}
files = set()
file_spans = collections.defaultdict(int)  # fallback size signal: summed LOC
for line in Path(methods_tsv).read_text(errors="ignore").splitlines():
    p = line.split("\t")
    if len(p) != 4:
        continue
    fn, f, s, e = p
    if not f or f in ("<empty>", "<unknown>"):
        continue
    k = canon(f)
    m2f[fn] = k
    files.add(k)
    try:
        s, e = int(s), int(e)
        if e >= s >= 0:
            file_spans[k] += (e - s + 1)
    except ValueError:
        pass

def file_tokens(k):
    p = Path(k)
    if p.is_file():
        try:
            return max(1, p.stat().st_size // CPT)
        except OSError:
            pass
    return max(1, file_spans.get(k, 3) * 8)  # ~8 tok/line fallback

deps = collections.defaultdict(set)   # f -> files f depends on

# ---- import edges (the reliable cross-file signal for dynamic languages) ----
def resolve_spec(importing_raw, spec):
    if not spec.startswith("."):
        return None  # external/package import — not part of the internal graph
    base = resolve(importing_raw)
    if not base:
        return None
    t = base.parent / spec
    cands = [t.with_suffix(".ts"), t.with_suffix(".tsx"),
             Path(str(t) + ".ts"), Path(str(t) + ".tsx"),
             t / "index.ts", t / "index.tsx",
             t.with_suffix(".js"), Path(str(t) + ".js"), t / "index.js"]
    if t.suffix == ".js":
        cands = [t.with_suffix(".ts"), t.with_suffix(".tsx")] + cands
    for c in cands:
        try:
            if c.is_file():
                return str(c.resolve())
        except OSError:
            pass
    return None

imports_tsv = Path(calls_tsv).parent / "imports.tsv"
import_rows = import_resolved = 0
if imports_tsv.is_file():
    for line in imports_tsv.read_text(errors="ignore").splitlines():
        p = line.split("\t")
        if len(p) != 2:
            continue
        import_rows += 1
        f_raw, spec = p
        src = canon(f_raw)
        files.add(src)
        tgt = resolve_spec(f_raw, spec)
        if tgt and tgt != src:
            files.add(tgt)
            deps[src].add(tgt)
            import_resolved += 1

# ---- source-parsed import edges (reliable cross-file signal for JS/TS) ------
src_edges_tsv = Path(calls_tsv).parent / "src_edges.tsv"
src_import_resolved = 0
if src_edges_tsv.is_file():
    for line in src_edges_tsv.read_text(errors="ignore").splitlines():
        p = line.split("\t")
        if len(p) != 2:
            continue
        a, b = p
        files.add(a); files.add(b)
        if b not in deps[a]:
            src_import_resolved += 1
        deps[a].add(b)

# ---- project method calls (cross-file) --------------------------------------
call_rows = call_resolved = 0
for line in Path(calls_tsv).read_text(errors="ignore").splitlines():
    p = line.split("\t")
    if len(p) != 2:
        continue
    call_rows += 1
    a, b = p
    fa, fb = m2f.get(a), m2f.get(b)
    if fa and fb and fa != fb:
        if fb not in deps[fa]:
            call_resolved += 1
        deps[fa].add(fb)

tok = {f: file_tokens(f) for f in files}

rdeps = collections.defaultdict(set)
for f, ds in deps.items():
    for d in ds:
        rdeps[d].add(f)

edge_count = sum(len(s) for s in deps.values())
N = len(files)

# ---- graph algorithms -------------------------------------------------------
def closure(start, adj):
    seen, stack = set(), [start]
    while stack:
        n = stack.pop()
        for m in adj.get(n, ()):
            if m not in seen:
                seen.add(m); stack.append(m)
    seen.discard(start)
    return seen

out_clo = {f: closure(f, deps) for f in files}
in_clo  = {f: closure(f, rdeps) for f in files}
out_tok = {f: tok[f] + sum(tok[x] for x in out_clo[f]) for f in files}
in_tok  = {f: tok[f] + sum(tok[x] for x in in_clo[f]) for f in files}

# Tarjan SCC (iterative)
idx, low, onst, stk, cnt, sccs = {}, {}, {}, [], [0], []
def tarjan(v0):
    work = [(v0, iter(deps.get(v0, ())))]
    idx[v0] = low[v0] = cnt[0]; cnt[0] += 1; stk.append(v0); onst[v0] = True
    while work:
        v, it = work[-1]
        pushed = False
        for w in it:
            if w not in idx:
                idx[w] = low[w] = cnt[0]; cnt[0] += 1; stk.append(w); onst[w] = True
                work.append((w, iter(deps.get(w, ())))); pushed = True; break
            elif onst.get(w):
                low[v] = min(low[v], idx[w])
        if pushed:
            continue
        work.pop()
        if work:
            low[work[-1][0]] = min(low[work[-1][0]], low[v])
        if low[v] == idx[v]:
            comp = []
            while True:
                w = stk.pop(); onst[w] = False; comp.append(w)
                if w == v:
                    break
            sccs.append(comp)
for v in files:
    if v not in idx:
        tarjan(v)
knots = sorted((c for c in sccs if len(c) > 1), key=len, reverse=True)

fan_in  = {f: len(rdeps.get(f, ())) for f in files}
fan_out = {f: len(deps.get(f, ()))  for f in files}
orphans = [f for f in files if fan_in[f] == 0]          # nothing internal depends on them
in_scc  = {f for c in knots for f in c}

# ---- helpers ----------------------------------------------------------------
def pctl(d, q):
    v = sorted(d.values())
    return v[min(len(v) - 1, int(q * len(v)))] if v else 0

def dist_line(d):
    return (f"median {pctl(d,.5):,} | p75 {pctl(d,.75):,} | p90 {pctl(d,.90):,} | "
            f"p99 {pctl(d,.99):,} | max {max(d.values()) if d else 0:,}")

def short(f):
    return f.replace(str(repo_root) + "/", "")

bulk = sum(tok.values())
over = sum(1 for v in out_tok.values() if v > WINDOW)

# verdict inputs: median tells you the typical case; hubs/blast/SCC tell you the tail
med_out = pctl(out_tok, .5)
max_fanin = max(fan_in.values()) if fan_in else 0
max_blast = max(in_tok.values()) if in_tok else 0
blast_frac = (max_blast / bulk) if bulk else 0
largest_scc = len(knots[0]) if knots else 0
diffuse = med_out > WINDOW * 0.10 or (over / N if N else 0) > 0.25
# SCC and absolute fan-in are size-robust signals of a real hub; blast_frac is
# size-sensitive (a shared types file in a small repo trivially reaches a big %),
# so it's reported but not a trigger.
has_hub = (largest_scc >= 3) or (max_fanin >= 25 and max_fanin >= 0.2 * N)
top_fi = sorted(files, key=lambda x: -fan_in[x])[:3]

# hot core: rank by combined out-closure + in-closure rank, bonus for SCC membership
ranks = {}
ol = sorted(files, key=lambda f: out_tok[f]); il = sorted(files, key=lambda f: in_tok[f])
for i, f in enumerate(ol):
    ranks[f] = ranks.get(f, 0) + i
for i, f in enumerate(il):
    ranks[f] = ranks.get(f, 0) + i
hot = sorted(files, key=lambda f: (f in in_scc, ranks[f]), reverse=True)[:8]

# ---- report -----------------------------------------------------------------
L = []
def w(s=""): L.append(s)

w(f"# token-mass report: `{repo_root.name}`")
w()
w("> Diagnostic only. This describes the **shape** of the codebase's structural")
w("> working-cost (the 'keyhole' difficulty), in reference-tokenizer tokens. It does")
w("> **not** forecast a bill and does **not** propose fixes. All metrics are classical")
w("> graph analysis over the file dependency graph (imports + resolved calls) —")
w("> no LLM, no tokens spent.")
w()
w("## Graph construction quality")
w()
if N:
    w(f"- files (nodes): **{N}** | dependency edges: **{edge_count}** | avg out-degree: **{edge_count/N:.1f}**")
else:
    w("- empty graph")
w(f"- source-parsed import edges: **{src_import_resolved:,}** (primary for JS/TS)")
w(f"- CPG import edges: {import_resolved:,} resolved / {import_rows:,} specifiers")
w(f"- CPG call edges (cross-file): {call_resolved:,} resolved / {call_rows:,} call sites")
w(f"- reference tokenizer: ~{CPT} chars/token | window threshold: {WINDOW:,} tok")
if (edge_count / N if N else 0) < 0.5:
    w()
    w("> ⚠️ **Sparse graph.** Few cross-file edges resolved — typical for dynamic languages / "
      "higher-order code, or a genuinely loosely-coupled codebase. Closures below are a floor; "
      "treat the shapes as indicative, not exact.")
w()
w("## Bulk (context, not pain)")
w()
w(f"- total: **{bulk:,} tok** (~{bulk*CPT/1e6:.1f} MB source) across {N} files")
w(f"- fits a {WINDOW:,}-tok window whole? **{'no' if bulk > WINDOW else 'yes'}**")
w()
w("## Distributions (the pain is the shape, not the sum)")
w()
w(f"- **size** (tokens/file): {dist_line(tok)}")
w(f"- **out-closure** (understand a file + all it imports): {dist_line(out_tok)}")
w(f"- **in-closure** (blast radius — change it, re-verify these): {dist_line(in_tok)}")
w()
w(f"- files whose **out-closure exceeds the {WINDOW:,} window**: "
  f"**{over}/{N}** ({100*over/N:.0f}%) — these have no safe keyhole" if N else "")
w()
w("## Structure & pathologies")
w()
w(f"- **strongly-connected components (knots):** {len(knots)} non-trivial")
for c in knots[:5]:
    cf = collections.Counter(Path(x).name.split('/')[-1] for x in c)
    w(f"  - size **{len(c)}**, {sum(tok[x] for x in c):,} tok — e.g. "
      + ", ".join(n for n, _ in cf.most_common(3)))
if not knots:
    w("  - none — the dependency graph is a DAG (no irreducible cyclic core)")
w()
w("- **god-nodes (highest fan-in — 'always loaded'):**")
for f in sorted(files, key=lambda x: -fan_in[x])[:5]:
    w(f"  - fan-in {fan_in[f]:>3} | {short(f)}")
w("- **god-nodes (highest fan-out — pull in the most):**")
for f in sorted(files, key=lambda x: -fan_out[x])[:5]:
    w(f"  - fan-out {fan_out[f]:>3} | {short(f)}")
w(f"- **orphans (no internal dependents):** {len(orphans)} files "
  f"(entrypoints + possibly dead code)")
w()
w("## Hot core (where pain concentrates)")
w()
w("Files that are simultaneously expensive to understand (out-closure), dangerous to")
w("change (in-closure), and/or trapped in a knot (SCC). These dominate the pain:")
w()
for f in hot:
    tags = []
    if f in in_scc: tags.append("SCC")
    w(f"- {short(f)} — out {out_tok[f]:,} / blast {in_tok[f]:,} tok"
      + (f"  [{', '.join(tags)}]" if tags else ""))
w()
w("## Verdict")
w()
if diffuse:
    w("**Diffuse pain.** High median closure / large over-window fraction: coupling is "
      "systemic, not localized. No single refactor relieves it — budget for it or restructure "
      "broadly. This is the Conway-bound / legacy signature.")
elif has_hub:
    hubs = ", ".join(f"{short(f)} (fan-in {fan_in[f]})" for f in top_fi)
    w("**Concentrated, but with high-stakes hubs.** Most files are cheap to work "
      f"(median out-closure {med_out:,} tok), so day-to-day pain is localized — but a few "
      "foundational hubs carry outsized blast radius: a change there re-implicates much of the "
      "codebase.")
    w()
    w(f"- top hubs: {hubs}")
    w(f"- worst blast radius: {max_blast:,} tok (**{blast_frac*100:.0f}%** of the codebase)")
    if largest_scc:
        w(f"- cyclic knot of {largest_scc} files (cannot be keyholed apart)")
    w()
    w("Refactorable, but these hubs are where leverage *and* risk concentrate — the first "
      "targets to decouple, and the most dangerous to touch.")
else:
    w("**Concentrated pain.** Low median closure, thin tail, no severe hubs: the codebase is "
      "cheap to work almost everywhere, and the expense is a small set of named hotspots (see "
      "Hot core). Localized and refactorable.")
w()
w("> *The verdict label is an uncalibrated heuristic (thresholds fit to few repos), not a "
  "measurement. Trust the numbers and named offenders above; treat the label as a prompt for "
  "judgment. See [method-challenges.md](method-challenges.md).*")
w()
w("---")
w("*Caveats: candidates not verdicts (a god-node may be a legitimate facade; an SCC may be "
  "essential domain coupling). Static graph only — coupling hidden in DI/reflection/dynamic "
  "dispatch is invisible here, so a 'clean' result is not proof of health.*")

Path(out_md).write_text("\n".join(L) + "\n")
print(f"report -> {out_md}  ({N} files, {edge_count} edges, {len(knots)} knots, "
      f"{over} over-window, verdict={'diffuse' if diffuse else 'concentrated'})")
