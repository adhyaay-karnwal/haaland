"""Decoder behavior: strict validation, helpful errors, tolerated input forms."""

from __future__ import annotations

import pytest

import haaland
from haaland.errors import HaalDecodeError


def test_comments_and_blank_lines_ignored():
    text = "# config\n\na: 1\n\n# trailing comment\nb: 2\n"
    assert haaland.loads(text) == {"a": 1, "b": 2}


def test_length_marker_validated_inline():
    with pytest.raises(HaalDecodeError, match="declared 3"):
        haaland.loads("a[3]: 1,2")


def test_length_marker_validated_table_truncated():
    with pytest.raises(HaalDecodeError, match="declared 2 rows"):
        haaland.loads("users[2]{id,name}:\n 1,Ada")


def test_length_marker_validated_table_extra():
    with pytest.raises(HaalDecodeError, match="more follow"):
        haaland.loads("users[1]{id,name}:\n 1,Ada\n 2,Grace")


def test_row_width_validated():
    with pytest.raises(HaalDecodeError, match="2 cells"):
        haaland.loads("users[1]{id,name,x}:\n 1,Ada")


def test_duplicate_keys_rejected():
    with pytest.raises(HaalDecodeError, match="duplicate key"):
        haaland.loads("a: 1\na: 2")


def test_duplicate_fields_rejected():
    with pytest.raises(HaalDecodeError, match="duplicate field"):
        haaland.loads("t[1]{a,a}:\n 1,2")


def test_tabs_in_indentation_rejected():
    with pytest.raises(HaalDecodeError, match="tabs"):
        haaland.loads("a:\n\tb: 1")


def test_error_carries_line_number():
    try:
        haaland.loads("a: 1\nb[2]: 1")
    except HaalDecodeError as e:
        assert e.line == 2
    else:
        pytest.fail("expected HaalDecodeError")


def test_empty_document_rejected():
    with pytest.raises(HaalDecodeError, match="empty"):
        haaland.loads("   \n\n")


def test_scalar_types():
    assert haaland.loads("a: 1") == {"a": 1}
    assert haaland.loads("a: 1.5") == {"a": 1.5}
    assert haaland.loads("a: 1e3") == {"a": 1000.0}
    assert haaland.loads("a: null") == {"a": None}
    assert haaland.loads("a: true") == {"a": True}
    assert haaland.loads('a: "123"') == {"a": "123"}
    assert haaland.loads("a: hello world") == {"a": "hello world"}
    # Leading-zero strings are not JSON numbers, so they stay strings.
    assert haaland.loads("a: 007") == {"a": "007"}


def test_quoted_cells_with_delimiter():
    assert haaland.loads('a[2]: "x, y",z') == {"a": ["x, y", "z"]}


def test_root_forms():
    assert haaland.loads("{}") == {}
    assert haaland.loads("[0]:") == []
    assert haaland.loads("[2]: 1,2") == [1, 2]
    assert haaland.loads("[1]{a}:\n 5") == [{"a": 5}]
    assert haaland.loads("42") == 42
    assert haaland.loads('"has: colon"') == "has: colon"


def test_crlf_input_accepted():
    assert haaland.loads("a: 1\r\nb: 2\r\n") == {"a": 1, "b": 2}


def test_wider_indentation_accepted():
    # Any consistent indent width decodes, not just the encoder default.
    text = "server:\n    host: localhost\n    port: 8080"
    assert haaland.loads(text) == {"server": {"host": "localhost", "port": 8080}}


def test_inconsistent_indentation_rejected():
    with pytest.raises(HaalDecodeError):
        haaland.loads("a:\n  b: 1\n   c: 2")


def test_missing_colon_rejected():
    with pytest.raises(HaalDecodeError, match="expected ':'"):
        haaland.loads("just a bare line\nanother: 1")


def test_trailing_garbage_rejected():
    with pytest.raises(HaalDecodeError, match="unexpected"):
        haaland.loads("[1]: 1\nextra: 2")


def test_empty_cell_rejected():
    with pytest.raises(HaalDecodeError, match="empty cell"):
        haaland.loads("a[2]: 1,")


def test_list_items():
    text = "items[3]:\n - 1\n -\n   a: 2\n - [2]: 3,4"
    assert haaland.loads(text) == {"items": [1, {"a": 2}, [3, 4]]}


def test_empty_object_item():
    assert haaland.loads("items[1]:\n - {}") == {"items": [{}]}


def test_file_round_trip(tmp_path):
    p = tmp_path / "data.haal"
    obj = {"a": [1, 2], "b": {"c": "d"}}
    with open(p, "w", encoding="utf-8") as f:
        haaland.dump(obj, f)
    with open(p, encoding="utf-8") as f:
        assert haaland.load(f) == obj
