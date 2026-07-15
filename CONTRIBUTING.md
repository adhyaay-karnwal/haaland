# Contributing to Haaland

Thanks for your interest. This project values measured claims and small, verifiable
changes.

## Development setup

```bash
git clone https://github.com/adhyaay-karnwal/haaland.git
cd haaland
pip install -e ".[dev]"
pytest                      # full suite, includes property-based round-trip tests
ruff check . && ruff format --check .
```

## Ground rules

1. **No unmeasured performance claims.** Any statement about token savings — in
   code comments, docs, or PR descriptions — must come from a committed benchmark
   run (`python benchmarks/run.py`) or an equivalent reproducible measurement.
2. **Round-trip is sacred.** `loads(dumps(x)) == x` for every JSON-model value,
   including key order. Changes to the codec must keep the hypothesis suite green;
   format changes need new golden tests in the same PR.
3. **Spec and code move together.** If behavior changes, `docs/spec.md` changes in
   the same PR.
4. **Regenerate benchmark results** (`results.json`, `RESULTS.md`) in any PR that
   touches the encoder, datasets, or harness.
5. **Unfavorable results stay.** Datasets where HAAL loses are part of the suite
   permanently; PRs that quietly drop them will be declined.

## Workflow

- Branch from `main`; use `feat/`, `fix/`, `docs/`, `bench/` prefixes.
- Keep PRs focused; CI (lint + tests on Python 3.10–3.13) must pass.
- For format/spec changes, open an issue first — syntax is a compatibility surface,
  and pre-1.0 is the only time we can still say no cheaply.

## Ideas that are welcome

- A TypeScript/JavaScript implementation tracking the conformance suite (top ask)
- Independent model-comprehension evaluations (we will link results, favorable or not)
- New benchmark datasets modeling payload shapes we don't cover
- Streaming row decoder
- Fuzzing beyond hypothesis (e.g. structure-aware corpus for OSS-Fuzz)

## Code style

Enforced by ruff (config in `pyproject.toml`). Match the existing code's comment
density: comments explain constraints, not narration.
