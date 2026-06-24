# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.2.0]

### Added
- Graph JSON export from `analyze.py` (`<report>.graph.json`): nodes with
  tokens / fan-in / fan-out / SCC / hot-core flags and closures, plus edges, for
  visualization.
- `graph.html` - interactive dependency-graph viewer (Cytoscape): nodes sized by
  tokens, fill by fan-in (hubs), red ring for SCC, gold ring for hot core; hover
  for stats; switch between example runs.
- `index.html` - reveal.js presentation embedding the live graph as an
  interactive slide. GitHub-Pages-ready (no build step).

### Fixed
- Presentation: clickable URLs on the closing slide; long text and the graph
  caption now wrap on narrow viewports.
- Presentation: slide numbers (current/total); smaller base font, tighter
  spacing, and a flattened dense slide so content fits the viewport.

## [0.1.0]

Initial release.

### Added
- `token-mass` entrypoint: point at a repo, get a markdown diagnostic of its
  structural working-cost ("keyhole" difficulty) shape. Token-free.
- Joern CPG extraction (`tokenmass/extract.sc`) + source-parsed import edges
  (`tokenmass/imports_from_source.py`) feeding one normalized graph.
- Analyzer suite (`tokenmass/analyze.py`): size / out-closure / in-closure
  distributions, SCCs, god-nodes, orphans, hot-core intersection, and a 3-way
  verdict (diffuse / concentrated-with-hubs / concentrated-clean).
- Recorded experiments under `docs/experiments/` (vulnerable-app, GitNexus).

### Notes
- Joern under-resolves cross-file edges for TypeScript in both directions;
  source-parsed imports are the reliable JS/TS edge source, swapped in behind the
  normalized-graph seam without touching the analyzers.
- Diagnostic only: no bill forecasting, no code changes. Static graph, so
  DI/reflection/dynamic coupling is invisible.
