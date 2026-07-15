"""Measure HAAL vs JSON/YAML token counts under Anthropic's tokenizer.

Anthropic's tokenizer is not runnable offline, so the committed benchmark results
use OpenAI's public BPE vocabularies. This script produces the Claude-side numbers
for anyone with an API key, using the official ``count_tokens`` endpoint (which is
free to call).

Usage:
    pip install anthropic pyyaml
    export ANTHROPIC_API_KEY=...   # or `ant auth login`
    python benchmarks/run_anthropic.py [--model claude-opus-4-8]

Counts include a small fixed per-request wrapper overhead (the message envelope),
identical across formats, so the *relative* savings are accurate.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import yaml  # type: ignore[import-untyped]
from datasets import DATASETS

import haaland


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="claude-opus-4-8")
    args = parser.parse_args()

    try:
        import anthropic
    except ImportError:
        raise SystemExit("pip install anthropic") from None

    client = anthropic.Anthropic()

    def count(text: str) -> int:
        return client.messages.count_tokens(
            model=args.model,
            messages=[{"role": "user", "content": text}],
        ).input_tokens

    print(f"model: {args.model}\n")
    totals: dict[str, int] = {}
    for name, factory in DATASETS.items():
        data = factory()
        renderings = {
            "json": json.dumps(data, ensure_ascii=False, separators=(",", ":")),
            "json_pretty": json.dumps(data, ensure_ascii=False, indent=2),
            "yaml": yaml.safe_dump(data, sort_keys=False, default_flow_style=False, width=10**9),
            "haal": haaland.dumps(data),
        }
        assert haaland.loads(renderings["haal"]) == data
        counts = {fmt: count(text) for fmt, text in renderings.items()}
        for fmt, n in counts.items():
            totals[fmt] = totals.get(fmt, 0) + n
        base = counts["json"]
        print(f"{name:16}", end="")
        for fmt in ("json", "json_pretty", "yaml", "haal"):
            pct = 100 * (base - counts[fmt]) / base
            print(f"  {fmt}={counts[fmt]:6} ({pct:+5.1f}%)", end="")
        print()

    base = totals["json"]
    print("\ntotals:")
    for fmt in ("json", "json_pretty", "yaml", "haal"):
        pct = 100 * (base - totals[fmt]) / base
        print(f"  {fmt:12} {totals[fmt]:7,} tokens  ({pct:+.1f}% vs compact JSON)")


if __name__ == "__main__":
    main()
