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

## Chosen: comma delimiter for standard, space for dense

| Delimiter | Total tokens | vs. comma |
|---|---:|---:|
| **space (dense default)** | **13,909** | −6.4% |
| tab | 14,537 | −2.2% |
| **comma (standard default)** | **14,860** | — |
| semicolon | 15,209 | +2.3% |
| pipe | 15,272 | +2.8% |

**Space is the cheapest delimiter by a wide margin** — the central finding of the
v0.2 research pass. BPE vocabularies are built from natural text, so their most
common merges are space-prefixed words: ` engineering` is one token where
`,engineering` is two. A space-delimited row is, to the tokenizer, an English-like
sentence. On the event-log dataset the space delimiter alone is −14.4% vs the comma
form. Cells that contain spaces get quoted (the standard collision rule), which is
why prose-heavy columns temper the win rather than break correctness.

The standard profile keeps comma for robustness and CSV familiarity; the dense
profile defaults to space. Tab remains supported but is now dominated: space is both
cheaper and immune to tab-normalizing editors.

## v0.2 research pass: "it doesn't have to be English"

We tested the hypothesis that a *less* human-readable surface — exotic characters,
symbol codes, compressed keywords — would be more token-efficient. Measured verdict:
**the opposite.** BPE vocabularies are English-optimized, so the efficient encoding
is the one that looks most like plain English text. The winners (space delimiter,
unpadded separators) make HAAL read *more* like natural language, not less.

### Adopted: unpadded separators (dense profile)

`key:value` instead of `key: value`, `-item` instead of `- item`. Suite total:
14,860 → 14,822 (comma) / 13,909 → 13,871 (space). The overall gain is +0.27%, but
it concentrates exactly where HAAL was weakest: `config` improves 259 → 232 (−10.4%)
because `:8443` is one token cheaper than `: 8443` on numeric and keyword values.
With both dense changes, the former worst cases nearly vanish: config is +0.9% vs
compact JSON (was +13.6%) and timeseries +0.8% (was +1.7%).

### Rejected: single-character keywords (`T`/`F` for booleans, `~`/`∅` for null)

Measured: `,true` and `,false` are **already single tokens** under `o200k_base`
(`true`/`false`/`null` are common enough to have dedicated merges). `,T` is also one
token — zero gain — while `,~` is two and `,∅` is three (worse). Single-character
keywords would also force quoting of legitimate `"T"`/`"F"` string data. Rejected
with prejudice.

### Rejected: exotic Unicode delimiters (`·`, `、`, `¦`, `‖`, `␟`, U+001F)

Measured on a realistic row: `·`, `、`, `¦`, and U+001F all tie comma at 29 tokens;
`‖` costs 36 and `␟` costs 43. Rare codepoints fragment into multi-byte tokens.
There is no exotic-character shortcut; the vocabulary rewards ordinary text.

### Rejected: symbol-indexed value dictionaries (enum folding)

The idea: declare repeated categorical values once in the table header and emit
digit indices in cells (`type=(push|fork|release)` … `,2`). Under the comma
delimiter this measured ~1 token saved per multi-token value. Under the space
delimiter it collapses: ` engineering`, ` delivered`, ` returned` are already
**one token each** — the same cost as an index — and ` pull_request` (2 tokens)
saves at most 1 minus dictionary overhead. Net gain ≈ 0 at a real complexity and
model-legibility cost. Rejected. The tokenizer's vocabulary *is* the value
dictionary; plain words are the compressed form.

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

- `config` (small, deep, no arrays): **+13.6% vs compact JSON** standard,
  **+0.9% dense.** Indentation runs cost more than braces at depth with no key
  amortization to offset them; the dense separators close most of the gap.
- `timeseries_48h` (pure numeric arrays): **+1.7%** standard, **+0.8% dense.**
  `[48]:` headers vs `[`.
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
