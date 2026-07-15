"""Dense profile: golden output, round-trip guarantee, cross-profile decoding."""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

import haaland
from haaland.errors import HaalEncodeError

SAMPLE = {
    "users": [
        {"id": 1, "name": "Ada Lovelace", "active": True},
        {"id": 2, "name": "Grace Hopper", "active": False},
    ],
    "server": {"host": "localhost", "port": 8443},
    "tags": ["a", "b"],
    "empty": {},
}


def test_dense_golden():
    assert haaland.dumps(SAMPLE, profile="dense") == (
        "users[2]{id name active}:\n"
        ' 1 "Ada Lovelace" true\n'
        ' 2 "Grace Hopper" false\n'
        "server:\n"
        " host:localhost\n"
        " port:8443\n"
        "tags[2]:a b\n"
        "empty:{}"
    )


def test_dense_round_trip():
    text = haaland.dumps(SAMPLE, profile="dense")
    assert haaland.loads(text, profile="dense") == SAMPLE


def test_dense_list_form():
    obj = {"items": [1, {"a": 2}, [3, 4], {}, "-x"]}
    text = haaland.dumps(obj, profile="dense")
    assert text == "items[5]:\n -1\n -\n  a:2\n -[2]:3 4\n -{}\n --x"
    assert haaland.loads(text, profile="dense") == obj


def test_decoder_accepts_both_profiles_without_hints():
    # Separator forms are always accepted; only the delimiter must match.
    assert haaland.loads("a:1\nb: 2") == {"a": 1, "b": 2}
    assert haaland.loads("xs[2]:\n - 1\n -2") == {"xs": [1, 2]}
    assert haaland.loads("e:{}") == {"e": {}}
    assert haaland.loads("e: {}") == {"e": {}}


def test_space_delimiter_quoting():
    obj = {"rows": [{"a": "two words", "b": "one"}]}
    text = haaland.dumps(obj, profile="dense")
    assert '"two words"' in text
    assert haaland.loads(text, profile="dense") == obj


def test_explicit_delimiter_overrides_profile_default():
    obj = {"xs": [1, 2, 3]}
    assert haaland.dumps(obj, profile="dense", delimiter=",") == "xs[3]:1,2,3"


def test_rejects_unknown_profile():
    with pytest.raises(HaalEncodeError):
        haaland.dumps({"a": 1}, profile="tiny")


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
def test_dense_round_trip_property(value):
    text = haaland.dumps(value, profile="dense")
    assert haaland.loads(text, profile="dense") == value


@settings(max_examples=300, deadline=None)
@given(json_values)
def test_standard_decoder_reads_dense_separators(value):
    """Dense docs decode with a standard-profile decoder given the delimiter."""
    text = haaland.dumps(value, profile="dense")
    assert haaland.loads(text, delimiter=" ") == value
