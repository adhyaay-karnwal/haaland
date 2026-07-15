"""The benchmark datasets must be deterministic and round-trip losslessly."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "benchmarks"))

from datasets import DATASETS  # noqa: E402

import haaland  # noqa: E402


def test_datasets_deterministic():
    for name, factory in DATASETS.items():
        assert factory() == factory(), name


def test_datasets_round_trip_all_delimiters():
    for name, factory in DATASETS.items():
        data = factory()
        for delim in haaland.SUPPORTED_DELIMITERS:
            text = haaland.dumps(data, delimiter=delim)
            assert haaland.loads(text, delimiter=delim) == data, (name, delim)
