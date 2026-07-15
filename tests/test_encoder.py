"""Golden-output tests for the HAAL encoder."""

from __future__ import annotations

import pytest

import haaland
from haaland.errors import HaalEncodeError


def test_flat_object():
    assert haaland.dumps({"a": 1, "b": "hi", "c": True, "d": None}) == (
        "a: 1\nb: hi\nc: true\nd: null"
    )


def test_nested_object():
    obj = {"server": {"host": "localhost", "port": 8080}}
    assert haaland.dumps(obj) == "server:\n host: localhost\n port: 8080"


def test_tabular_array():
    obj = {
        "users": [
            {"id": 1, "name": "Ada", "admin": True},
            {"id": 2, "name": "Grace", "admin": False},
        ]
    }
    assert haaland.dumps(obj) == "users[2]{id,name,admin}:\n 1,Ada,true\n 2,Grace,false"


def test_inline_primitive_array():
    assert haaland.dumps({"tags": ["a", "b", "c"]}) == "tags[3]: a,b,c"


def test_empty_containers():
    assert haaland.dumps({}) == "{}"
    assert haaland.dumps([]) == "[0]:"
    assert haaland.dumps({"a": {}, "b": []}) == "a: {}\nb[0]:"


def test_root_scalars():
    assert haaland.dumps(42) == "42"
    assert haaland.dumps(None) == "null"
    assert haaland.dumps("hello") == "hello"
    assert haaland.dumps("has: colon") == '"has: colon"'
    assert haaland.dumps("") == '""'


def test_mixed_array_uses_list_form():
    obj = {"items": [1, {"a": 2}, [3, 4]]}
    assert haaland.dumps(obj) == ("items[3]:\n - 1\n -\n  a: 2\n - [2]: 3,4")


def test_non_uniform_objects_fall_back_to_list():
    obj = {"rows": [{"a": 1}, {"b": 2}]}
    assert haaland.dumps(obj) == "rows[2]:\n -\n  a: 1\n -\n  b: 2"


def test_table_requires_scalar_values():
    obj = {"rows": [{"a": 1, "b": [1]}, {"a": 2, "b": [2]}]}
    text = haaland.dumps(obj)
    assert "{a,b}" not in text  # must not tabulate nested values


def test_string_quoting_rules():
    # Number-like, reserved, and whitespace-y strings must be quoted.
    assert haaland.dumps({"a": "123"}) == 'a: "123"'
    assert haaland.dumps({"a": "true"}) == 'a: "true"'
    assert haaland.dumps({"a": " x "}) == 'a: " x "'
    assert haaland.dumps({"a": "line\nbreak"}) == 'a: "line\\nbreak"'
    # Commas are fine in line position, quoted in cell position.
    assert haaland.dumps({"a": "x, y"}) == "a: x, y"
    assert haaland.dumps({"a": ["x, y"]}) == 'a[1]: "x, y"'


def test_unicode_passthrough():
    assert haaland.dumps({"city": "Zürich", "emoji": "🎉"}) == "city: Zürich\nemoji: 🎉"


def test_key_quoting():
    assert haaland.dumps({"a key": 1}) == '"a key": 1'
    assert haaland.dumps({"safe_key-1.x": 1}) == "safe_key-1.x: 1"


def test_delimiter_tab():
    obj = {"users": [{"id": 1, "name": "Ada"}, {"id": 2, "name": "Grace"}]}
    assert haaland.dumps(obj, delimiter="\t") == ("users[2]{id\tname}:\n 1\tAda\n 2\tGrace")


def test_indent_width():
    obj = {"a": {"b": 1}}
    assert haaland.dumps(obj, indent=2) == "a:\n  b: 1"


def test_rejects_nan_and_infinity():
    with pytest.raises(HaalEncodeError):
        haaland.dumps({"a": float("nan")})
    with pytest.raises(HaalEncodeError):
        haaland.dumps({"a": float("inf")})


def test_rejects_non_string_keys():
    with pytest.raises(HaalEncodeError):
        haaland.dumps({1: "a"})


def test_rejects_unsupported_types():
    with pytest.raises(HaalEncodeError):
        haaland.dumps({"a": {1, 2}})


def test_rejects_bad_delimiter():
    with pytest.raises(HaalEncodeError):
        haaland.dumps({"a": 1}, delimiter="~")
