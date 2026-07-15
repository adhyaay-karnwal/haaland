# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow
[SemVer](https://semver.org).

## [Unreleased]

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
