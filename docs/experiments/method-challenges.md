# Method challenges (require judgment)

These are the honest limitations behind the assessments in this folder. They
explain why the recorded results read the way they do, and which parts of a
report you should trust as measurement versus treat as a prompt for your own
judgment. This is an experiment, not a published method; recording the soft spots
is part of reading the results responsibly.

## 1. Graph construction is language-dependent (caveat)

Joern's CPG under-resolves cross-file edges for TypeScript in both directions
(on the vulnerable app: 0 of 28,670 call edges, 0 of 1,025 import edges), so the
graph here is built from source-parsed imports instead.

- **Construction here:** the vulnerable-app graph is built *entirely* from
  source-parsed imports (the CPG contributed 0 usable cross-file edges). The edge
  source is swappable behind the normalized-graph seam; the analyzers don't change.
- **Requires judgment:** trust a report only as far as its "Graph construction
  quality" section shows edges resolved. A sparse graph yields a floor, not the
  truth. We cannot qualify this per language or framework here; that needs a
  developer's eye on the specific stack.
- **Status:** a caveat. It is honest about uncertainty, and acceptable for an
  experiment.

## 2. The verdict is an uncalibrated heuristic (defect)

The categorical verdict (clean / concentrated-with-hubs / diffuse) uses thresholds
(SCC size, absolute fan-in relative to repo size) that were chosen against a tiny
sample of repos. There is no principled cutoff between "clean" and "hubs" without
a corpus of codebases with known shapes.

- **Be blunt about it:** the thresholds were tuned so the sample repos came out
  the way we already expected (clean vs hubs). That is calibration to expectation
  on a tiny sample. The current form is more defensible than the first attempt
  (which used a size-sensitive blast-fraction), but it is still overfit.
- **What is trustworthy:** the underlying measurements (closures, SCC membership,
  fan-in counts, distributions) are deterministic graph facts and were never
  touched. Only the categorical label is unjustified.
- **Requires judgment:** read the verdict as a prompt, not a measurement. The
  named offenders and the numbers are the signal; the label is opinion.
- **Status:** a defect. It manufactures false certainty. Fix: drop the categorical
  verdict, or calibrate it against a real corpus.

## 3. Per-source edge counts are order-dependent (reporting bug)

The "source-parsed import edges: N" line counts only edges not already added by
the CPG pass, so it understates the source parser's contribution when the CPG also
contributed (it reports only the *additional* unique edges the parser adds beyond
the CPG's). The **total** edge count is correct; the per-source attribution is not
a clean measurement.

- **Requires judgment:** read the total edge count, not the per-source counts.
- **Status:** a reporting bug, to fix.

## The line

The deterministic graph facts are trustworthy. Anything categorical or labelled
(the verdict) requires human judgment: candidates, not verdicts. That boundary is
the whole premise of the tool, and these three notes are exactly where it bites.
