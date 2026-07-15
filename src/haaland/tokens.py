"""Token counting utilities.

Counts use OpenAI's open-source ``tiktoken`` BPE vocabularies, which are the
only major production LLM tokenizers that are public and runnable offline.
Other vendors' tokenizers differ in vocabulary but share the BPE mechanics
that HAAL optimizes for (fewer structural characters, fewer forced token
boundaries); measure with your own provider's token counter for exact numbers.

This module requires the ``tokens`` extra: ``pip install haaland[tokens]``.
"""

from __future__ import annotations

from functools import lru_cache

DEFAULT_ENCODING = "o200k_base"  # GPT-4o / o-series
KNOWN_ENCODINGS = ("o200k_base", "cl100k_base")


@lru_cache(maxsize=8)
def _encoder(encoding: str):
    try:
        import tiktoken
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "token counting requires tiktoken; install with: pip install haaland[tokens]"
        ) from exc
    return tiktoken.get_encoding(encoding)


def count_tokens(text: str, encoding: str = DEFAULT_ENCODING) -> int:
    """Number of tokens *text* occupies under the given BPE vocabulary."""
    return len(_encoder(encoding).encode(text))


def compare(texts: dict[str, str], encoding: str = DEFAULT_ENCODING) -> dict[str, dict]:
    """Token counts and savings for several renderings of the same data.

    Args:
        texts: mapping of format name -> serialized text. Must include a
            ``"json"`` entry to serve as the baseline.

    Returns:
        Mapping of format name -> ``{"tokens": int, "vs_json_pct": float}``,
        where ``vs_json_pct`` is the percentage saved relative to JSON
        (positive = fewer tokens than JSON).
    """
    if "json" not in texts:
        raise ValueError('compare() needs a "json" baseline entry')
    counts = {name: count_tokens(text, encoding) for name, text in texts.items()}
    baseline = counts["json"]
    return {
        name: {
            "tokens": n,
            "vs_json_pct": round(100.0 * (baseline - n) / baseline, 2) if baseline else 0.0,
        }
        for name, n in counts.items()
    }
