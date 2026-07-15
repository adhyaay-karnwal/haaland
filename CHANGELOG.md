# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow
[SemVer](https://semver.org).

## [Unreleased]

## [0.2.0] - 2026-07-14

### Added

- **Dense profile** (`profile="dense"` / `haal --profile dense`): space delimiter
  plus unpadded `:`/`-` separators. Measured (o200k_base, six-dataset suite):
  **−28.0% tokens vs compact JSON** overall (−22.9% for standard), −54.6% vs
  2-space JSON, −41.4% vs YAML, −6.7% vs standard HAAL; event logs −46.5%.
  The former worst-case shapes are nearly neutralized (deep config +0.9% and
  numeric timeseries +0.8% vs compact JSON, from +13.6%/+1.7%).
- Space added to supported delimiters (the measured cheapest: BPE vocabularies
  merge space-prefixed words into single tokens).
- Decoder now accepts both profiles' separator forms transparently; only the
  delimiter remains a codec parameter.
- `haal stats` reports a `haal (dense)` row.
- Negative results recorded in docs/design-notes.md: single-character
  booleans/null (`T`/`F`/`~`), exotic Unicode delimiters, and symbol-indexed
  value dictionaries all measured at zero or negative gain — under a BPE
  tokenizer, plain space-separated English is the efficient encoding.

### Changed

- Spec bumped to v0.2 (§3.1 Profiles). Standard-profile output is byte-identical
  to v0.1.0; existing documents parse unchanged.

## [0.1.0] - 2026-07-14

### Added

- HAAL format specification v0.1 (`docs/spec.md`): line-oriented, indentation-based
  serialization of the JSON data model with declared array lengths, tabular headers
  for uniform object arrays, and strict validation semantics.
- Reference Python codec (`haaland.dumps`/`loads`/`dump`/`load`) with a lossless
  round-trip guarantee including key order; zero runtime dependencies.
- `haal` CLI: `encode`, `decode`, `check`, `stats` (token comparison under
  `o200k_base`/`cl100k_base`).
- `haaland.tokens` utilities (optional `[tokens]` extra).
- Reproducible benchmark suite with six deterministic datasets, delimiter and
  indent ablations, and committed results: −22.9% tokens vs compact JSON overall,
  −51.3% vs 2-space JSON, −37.3% vs YAML (o200k_base); range −37.4% (uniform
  records) to +13.6% (small deep config, a documented loss).
- `benchmarks/run_anthropic.py` for measuring real Claude token counts via the
  `count_tokens` API.
- Documentation set: quickstart, format-by-example, LLM integration guide,
  enterprise adoption guide, design notes with ablation data, FAQ.
- Prompt kit: HAAL system-prompt primer and an agent-setup prompt for automated
  codebase integration.
- CI: ruff lint/format + pytest (with hypothesis property tests) on Python
  3.10–3.13.
