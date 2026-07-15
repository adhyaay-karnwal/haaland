# Design notes: what we measured, chose, and rejected

Every default in HAAL was chosen by measurement, not intuition. This page records the
experiments — including the ones that lost — so future changes argue with data.

All numbers are total `o200k_base` tokens across the six benchmark datasets
(`python benchmarks/run.py`; committed output in `benchmarks/results.json`).

## Chosen: 1-space indentation

| Indent | Total tokens |
|---|---:|
| **1 space (default)** | **14,860** |
| 2 spaces | 15,261 |
| 4 spaces | 15,261 |

1 space saves 2.6% over 2 spaces. (2 and 4 tie on this suite because BPE merges runs
of spaces into single tokens at these depths; 1 space wins by keeping short
indent+content merges.) The decoder accepts any consistent width, so hand-written
documents can use whatever is readable.

## Chosen: comma delimiter by default, tab as the max-efficiency profile

| Delimiter | Total tokens | vs. comma |
|---|---:|---:|
| tab | 14,537 | −2.2% |
| **comma (default)** | **14,860** | — |
| semicolon | 15,209 | +2.3% |
| pipe | 15,272 | +2.8% |

Tab measurably wins — partly because tab characters merge well under BPE, partly
because real-world prose contains commas (our RAG dataset includes them
deliberately), which forces quoting under the comma delimiter but not under tab.

We still default to comma, and this is a robustness call, not an efficiency call:

- Editors, chat UIs, terminals, and models themselves silently normalize tabs to
  spaces. A normalized tab corrupts data invisibly; a normalized comma cannot happen.
- Comma-separated rows are the single most training-represented tabular syntax (CSV).

`--delimiter tab` / `dumps(data, delimiter="\t")` is fully supported for closed
pipelines where you control both ends and want the extra 2.2%.

## Rejected: inline first key on list-object items (YAML-style `- key: value`)

Object items in mixed arrays currently cost a lone `-` line. We prototyped merging
the first key onto the dash line and measured the six-dataset suite: the only
affected dataset (`orders_50`) improved by ~1.1%, ~0.3% overall. In exchange it
introduces a real parse ambiguity (`- a: b` as scalar string vs. object) that would
force new quoting rules in list context. Rejected: complexity is permanent,
0.3% is not. Recorded here so it isn't re-litigated without new data.

## Rejected: length-marker-free arrays

Dropping `[N]` would save a handful of tokens per array (measurable on
`timeseries_48h`, where HAAL loses 1.7% to compact JSON largely for this reason).
We keep the markers because they convert LLM output truncation from silent data
loss into a located parse error — the validation story is a core design goal, not
an add-on. This is a deliberate trade documented in the README's "when not to use"
table.

## Rejected: document-level version/delimiter header

A first-line directive (`#haal v1 delim=tab`) costs tokens on every document to
serve the rare case of non-default configuration. Configuration is a codec
parameter; documents stay clean.

## Known losses (kept honest)

- `config` (small, deep, no arrays): **+13.6% vs compact JSON.** Indentation runs
  cost more than braces at depth with no key amortization to offset them.
- `timeseries_48h` (pure numeric arrays): **+1.7%.** `[48]: ` headers vs `[`.
- `orders_50` (nested, small tables): only **−2.8%** — per-order table headers
  (`items[3]{sku,product,qty,unit_price}:`) are re-paid per order. Flattening
  order-item data into one table (denormalizing `order_id` into rows) measured far
  better in the `events_200`-like regime; restructuring guidance beats format
  cleverness here.

## Measurement discipline

Rules the benchmark harness enforces, which PRs must preserve:

1. Datasets are seeded and deterministic — same bytes on every machine.
2. Every HAAL rendering is round-trip-verified against source data *before* being
   counted; a rendering that doesn't round-trip aborts the run.
3. Baselines include the strongest one (compact JSON), not just the flattering ones.
4. Unfavorable dataset shapes stay in the suite permanently.
5. Committed results (`results.json`, `RESULTS.md`) are regenerated in the same PR
   as any change to the encoder, datasets, or harness.
