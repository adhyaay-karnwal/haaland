# FAQ

## Is HAAL lossless?

Yes, by construction and by test. `haaland.loads(haaland.dumps(x)) == x` for every
value in the JSON data model — including object key order — verified by
property-based tests (hypothesis) in CI and a 25,000-document fuzz across all
supported delimiters and indent widths. `NaN`/`Infinity` are rejected, exactly as in
strict JSON.

## What are the real numbers?

Across six benchmark datasets, tokenized with `o200k_base`: **−22.9% vs compact
JSON, −51.3% vs 2-space JSON, −37.3% vs YAML**. Best shape: uniform event records at
−37.4%. Worst shape: small deep config at **+13.6% (HAAL loses)**. Full tables and
methodology: [../benchmarks/RESULTS.md](../benchmarks/RESULTS.md). Reproduce with
`python benchmarks/run.py`.

## Do these savings apply to Claude / Gemini / Llama?

Not verbatim, and we won't pretend otherwise. Our percentages are measured on the
two production BPE vocabularies that are public and runnable offline (OpenAI's
`o200k_base`, `cl100k_base`). The *structural* savings — writing each key once per
array instead of once per element, dropping quotes/braces — reduce characters and
token-boundary breaks under any BPE tokenizer, but the exact rate differs by
vocabulary. For Claude, run [`benchmarks/run_anthropic.py`](../benchmarks/run_anthropic.py)
with your API key: it measures real counts via Anthropic's `count_tokens` endpoint.

## Will models understand it?

The tabular form reads like CSV/markdown tables, which are heavily represented in
training data; the nested forms are more novel. We make no unmeasured comprehension
claims — run the A/B described in
[llm-integration.md](llm-integration.md#evaluating-comprehension) on your own eval
set. If you publish results, open an issue; we'll link them.

## How is this different from TOON?

[TOON](https://github.com/toon-format/toon) (Token-Oriented Object Notation) is
prior art with the same core insight — tabular folding of uniform object arrays for
LLM contexts — and deserves the credit for popularizing it. Differences in HAAL's
approach:

- **Validation-first decoder.** Strict length/width/duplicate checking with
  line-numbered errors is the design center, aimed at parsing LLM-*emitted* data.
- **Measured defaults.** Indent width and delimiter were chosen by committed
  ablation runs (see [design-notes.md](design-notes.md)), and the benchmark suite
  deliberately contains shapes where the whole approach loses.
- **Property-tested losslessness** including key order, as a hard guarantee.

If TOON already serves you well, there is no urgent reason to switch; the formats
are conceptually siblings. We benchmark against JSON/YAML rather than TOON because
apples-to-apples comparison would require pinning their implementation semantics —
an independent bake-off would be welcome.

## Why not just gzip the JSON?

Compression reduces *bytes*, not *tokens*. Models consume tokens; you cannot feed a
gzip stream into a context window. Token efficiency has to happen in the text
representation itself.

## Why not protobuf / MessagePack / CBOR?

Binary formats are not valid model input either. HAAL competes in the space of
*plain text a model can read*: JSON, YAML, CSV, markdown tables.

## Should model OUTPUT be HAAL?

Only for bulk record extraction, with the validation-retry loop, and never in place
of provider-enforced structured outputs (JSON schema modes). Input is where the bulk
of tokens and the bulk of savings live.

## Is there a JavaScript/TypeScript implementation?

Not yet — the Python reference implementation and the spec come first (a spec plus
one verified implementation beats two divergent ones). A TypeScript port tracking
the same property-test suite is the top item on the roadmap; the codec is under 600 lines,
and the spec (docs/spec.md §9) defines conformance if you want to build it — PRs
welcome.

## What about streaming very large documents?

The current decoder parses whole documents in memory. Row-streaming a table is
mechanically easy (rows are independent lines) but not yet in the API. Open an issue
with your use case.

## Who is behind this / why "Haaland"?

An open-source research project into token-efficiency as a first-class axis of
LLM systems engineering. The name is a nod to a certain striker's efficiency in
front of goal: fewest touches, most output.
