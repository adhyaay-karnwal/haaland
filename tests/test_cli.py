"""CLI behavior tests (run in-process via haaland.cli.main)."""

from __future__ import annotations

import json

import pytest

from haaland.cli import main

SAMPLE = {"users": [{"id": 1, "name": "Ada"}, {"id": 2, "name": "Grace"}]}


@pytest.fixture
def json_file(tmp_path):
    p = tmp_path / "data.json"
    p.write_text(json.dumps(SAMPLE), encoding="utf-8")
    return str(p)


def test_encode_decode_round_trip(json_file, tmp_path, capsys):
    assert main(["encode", json_file]) == 0
    haal_text = capsys.readouterr().out
    assert haal_text.startswith("users[2]{id,name}:")

    p = tmp_path / "data.haal"
    p.write_text(haal_text, encoding="utf-8")
    assert main(["decode", str(p)]) == 0
    assert json.loads(capsys.readouterr().out) == SAMPLE


def test_encode_stdin(monkeypatch, capsys):
    import io

    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps({"a": 1})))
    assert main(["encode"]) == 0
    assert capsys.readouterr().out == "a: 1\n"


def test_encode_tab_delimiter(json_file, capsys):
    assert main(["encode", json_file, "--delimiter", "tab"]) == 0
    assert "id\tname" in capsys.readouterr().out


def test_check_valid_and_invalid(tmp_path, capsys):
    good = tmp_path / "good.haal"
    good.write_text("a: 1\n", encoding="utf-8")
    assert main(["check", str(good)]) == 0
    assert "valid" in capsys.readouterr().out

    bad = tmp_path / "bad.haal"
    bad.write_text("a[3]: 1,2\n", encoding="utf-8")
    assert main(["check", str(bad)]) == 1
    assert "declared 3" in capsys.readouterr().err


def test_stats(json_file, capsys):
    pytest.importorskip("tiktoken")
    assert main(["stats", json_file, "--encoding", "o200k_base"]) == 0
    out = capsys.readouterr().out
    assert "o200k_base" in out
    assert "haal" in out
    assert "% vs JSON" in out


def test_invalid_json_input(tmp_path, capsys):
    p = tmp_path / "bad.json"
    p.write_text("{not json", encoding="utf-8")
    assert main(["encode", str(p)]) == 1
    assert "invalid JSON" in capsys.readouterr().err


def test_missing_file(capsys):
    assert main(["encode", "/nonexistent/file.json"]) == 1
    assert "no such file" in capsys.readouterr().err
