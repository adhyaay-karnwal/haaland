"""Property-based round-trip guarantee: loads(dumps(x)) == x for all JSON x."""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

import haaland

# Finite floats only: HAAL, like strict JSON, rejects NaN/Infinity.
scalars = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-(10**18), max_value=10**18),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(max_size=40),
)

json_values = st.recursive(
    scalars,
    lambda children: st.one_of(
        st.lists(children, max_size=8),
        st.dictionaries(st.text(max_size=20), children, max_size=8),
    ),
    max_leaves=60,
)


@settings(max_examples=500, deadline=None)
@given(json_values)
def test_roundtrip_default(value):
    assert haaland.loads(haaland.dumps(value)) == value


@settings(max_examples=200, deadline=None)
@given(json_values)
def test_roundtrip_tab_delimiter(value):
    text = haaland.dumps(value, delimiter="\t")
    assert haaland.loads(text, delimiter="\t") == value


@settings(max_examples=200, deadline=None)
@given(json_values)
def test_roundtrip_pipe_delimiter_indent2(value):
    text = haaland.dumps(value, delimiter="|", indent=2)
    assert haaland.loads(text, delimiter="|") == value


@settings(max_examples=200, deadline=None)
@given(json_values)
def test_key_order_preserved(value):
    """Round-trip must preserve dict insertion order, not just equality."""
    import json

    a = haaland.loads(haaland.dumps(value))
    assert json.dumps(a, sort_keys=False) == json.dumps(value, sort_keys=False)
