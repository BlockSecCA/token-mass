#!/usr/bin/env python3
"""
imports_from_source.py — extract file->file dependency edges by parsing imports
directly from JS/TS source.

Why this exists: Joern's CPG import/call resolution is unreliable for dynamic
languages (it returned 0 usable cross-file edges on real TS codebases, in both
directions). Imports, however, are textually trivial and 100% reliable to parse.
This is a language-specific extractor that feeds the SAME normalized graph the
analyzers consume — the seam stays intact; only the edge source is swapped.

Emits TSV: <srcAbsPath>\t<dstAbsPath>  (one resolved internal import per line)

Usage: imports_from_source.py <repo_root> <out_edges.tsv>
"""
import re, sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
out = sys.argv[2]

EXCLUDE = re.compile(r"(/node_modules/|/\.git/|/dist/|/build/|\.d\.ts$)")
SRC_EXT = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")

files = [p.resolve() for p in root.rglob("*")
         if p.suffix in SRC_EXT and not EXCLUDE.search(str(p).replace("\\", "/"))]
fileset = set(files)

# import './x' | export ... from './x' | import('./x') | require('./x') | import x = require('./x')
SPEC = re.compile(
    r"""(?:import|export)\s+(?:[^'"]*?\sfrom\s+)?['"]([^'"]+)['"]"""
    r"""|(?:require|import)\(\s*['"]([^'"]+)['"]\s*\)"""
    r"""|require\(\s*['"]([^'"]+)['"]\s*\)""")

def resolve(spec, frm):
    if not spec.startswith("."):
        return None  # external / package import
    base = (frm.parent / spec)
    cands = [base.with_suffix(e) for e in SRC_EXT]
    cands += [Path(str(base) + e) for e in SRC_EXT]
    cands += [base / ("index" + e) for e in SRC_EXT]
    for c in cands:
        try:
            r = c.resolve()
        except OSError:
            continue
        if r in fileset:
            return r
    return None

edges = []
for f in files:
    try:
        txt = f.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        continue
    for m in SPEC.finditer(txt):
        spec = m.group(1) or m.group(2) or m.group(3)
        if not spec:
            continue
        r = resolve(spec, f)
        if r and r != f:
            edges.append((str(f), str(r)))

with open(out, "w") as fh:
    for a, b in edges:
        fh.write(f"{a}\t{b}\n")

print(f"src-imports: {len(edges)} edges across {len(files)} files -> {out}")
