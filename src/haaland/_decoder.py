"""HAAL decoder: HAAL text -> Python objects (JSON data model).

A strict, line-oriented recursive-descent parser. Structure is carried by
indentation (spaces only); declared lengths (``[N]``) and field headers are
validated, which lets consumers detect truncated or corrupted documents --
including documents emitted by an LLM.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from ._encoder import _NUMBER_RE
from .errors import HaalDecodeError

_ARRAY_HEADER_RE = re.compile(r"^\[(\d+)\]")


def decode(text: str, *, delimiter: str = ",") -> Any:
    """Parse HAAL *text* into Python objects.

    Args:
        text: The document. Blank lines and full-line ``#`` comments are ignored.
        delimiter: Cell separator used when the document was encoded.
    """
    lines = _scan_lines(text)
    if not lines:
        raise HaalDecodeError("empty document")
    parser = _Parser(lines, delimiter)
    return parser.document()


@dataclass
class _Line:
    number: int  # 1-based line number in the source
    indent: int  # count of leading spaces
    text: str  # content with indentation stripped


def _scan_lines(text: str) -> list[_Line]:
    lines: list[_Line] = []
    for number, raw in enumerate(text.split("\n"), start=1):
        raw = raw.rstrip("\r")
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        content = raw.lstrip(" ")
        indent = len(raw) - len(content)
        if content[0] == "\t" or "\t" in raw[:indent]:
            raise HaalDecodeError("tabs are not allowed in indentation", number)
        lines.append(_Line(number, indent, content))
    return lines


class _Parser:
    def __init__(self, lines: list[_Line], delimiter: str):
        self.lines = lines
        self.delimiter = delimiter
        self.pos = 0

    # -- helpers -----------------------------------------------------------

    def _peek(self) -> _Line | None:
        if self.pos < len(self.lines):
            return self.lines[self.pos]
        return None

    def _fail(self, message: str, line: _Line | None = None) -> HaalDecodeError:
        number = line.number if line else None
        return HaalDecodeError(message, number)

    # -- entry point -------------------------------------------------------

    def document(self) -> Any:
        first = self.lines[0]
        if first.indent != 0:
            raise self._fail("document must start at indentation 0", first)

        if len(self.lines) == 1 and first.text == "{}":
            self.pos = 1
            value: Any = {}
        elif first.text.startswith("["):
            self.pos = 1
            value = self._array_body(first.text, first)
        elif len(self.lines) == 1 and not self._looks_like_key_line(first.text):
            self.pos = 1
            value = self._scalar(first.text, first)
        else:
            value = self._object(0)

        trailing = self._peek()
        if trailing is not None:
            raise self._fail("unexpected content after end of document", trailing)
        return value

    def _looks_like_key_line(self, text: str) -> bool:
        if text.startswith('"'):
            try:
                json.loads(text)
            except json.JSONDecodeError:
                return True  # not a lone quoted scalar, so it must be a key line
            return False
        return ":" in text

    # -- objects -----------------------------------------------------------

    def _object(self, indent: int) -> dict:
        obj: dict[str, Any] = {}
        while True:
            line = self._peek()
            if line is None or line.indent < indent:
                if not obj:
                    raise self._fail("expected at least one key in object block")
                return obj
            if line.indent > indent:
                raise self._fail(
                    f"unexpected indentation (expected {indent} spaces, got {line.indent})", line
                )
            self.pos += 1
            key, after = self._key(line)
            if key in obj:
                raise self._fail(f"duplicate key {key!r}", line)
            obj[key] = self._value_after_key(after, line)

    def _key(self, line: _Line) -> tuple[str, str]:
        text = line.text
        if text.startswith('"'):
            end = _closing_quote(text, 0)
            if end is None:
                raise self._fail("unterminated quoted key", line)
            key = json.loads(text[: end + 1])
            after = text[end + 1 :]
        else:
            cut = len(text)
            for ch in (":", "["):
                idx = text.find(ch)
                if idx != -1:
                    cut = min(cut, idx)
            if cut == len(text):
                raise self._fail("expected ':' or '[N]' after key", line)
            key, after = text[:cut], text[cut:]
            if not key:
                raise self._fail("missing key", line)
        if not after or after[0] not in ":[":
            raise self._fail("expected ':' or '[N]' after key", line)
        return key, after

    def _value_after_key(self, after: str, line: _Line) -> Any:
        if after.startswith("["):
            return self._array_body(after, line)
        rest = after[1:]  # drop ':'
        if rest == "":
            child = self._peek()
            if child is None or child.indent <= line.indent:
                raise self._fail("expected an indented block after ':'", line)
            return self._object(child.indent)
        if rest == " {}":
            return {}
        if rest.startswith(" "):
            return self._scalar(rest[1:], line)
        raise self._fail("expected a space after ':'", line)

    # -- arrays ------------------------------------------------------------

    def _array_body(self, header: str, line: _Line) -> list:
        """Parse from an array header: '[N]...' possibly with '{fields}'."""
        m = _ARRAY_HEADER_RE.match(header)
        if not m:
            raise self._fail("malformed array header, expected [N]", line)
        n = int(m.group(1))
        rest = header[m.end() :]

        if rest.startswith("{"):
            fields, rest = self._fields(rest, line)
            if rest != ":":
                raise self._fail("expected ':' after field header", line)
            return self._table_rows(n, fields, line)

        if not rest.startswith(":"):
            raise self._fail("expected ':' after [N]", line)
        rest = rest[1:]
        if rest == "":
            if n == 0:
                return []
            return self._list_items(n, line)
        if not rest.startswith(" "):
            raise self._fail("expected a space before inline array values", line)
        cells = self._split_cells(rest[1:], line)
        if len(cells) != n:
            raise self._fail(f"array declared {n} values but has {len(cells)}", line)
        return cells

    def _fields(self, text: str, line: _Line) -> tuple[list[str], str]:
        """Parse '{f1,f2,...}' from *text*; returns (fields, remainder)."""
        i = 1
        fields: list[str] = []
        while True:
            if i >= len(text):
                raise self._fail("unterminated field header", line)
            if text[i] == '"':
                end = _closing_quote(text, i)
                if end is None:
                    raise self._fail("unterminated quoted field name", line)
                fields.append(json.loads(text[i : end + 1]))
                i = end + 1
            else:
                j = i
                while j < len(text) and text[j] not in (self.delimiter, "}"):
                    j += 1
                if j == i:
                    raise self._fail("empty field name", line)
                fields.append(text[i:j])
                i = j
            if i >= len(text):
                raise self._fail("unterminated field header", line)
            if text[i] == "}":
                return fields, text[i + 1 :]
            if text[i] != self.delimiter:
                raise self._fail(f"expected {self.delimiter!r} or '}}' in field header", line)
            i += 1

    def _table_rows(self, n: int, fields: list[str], header: _Line) -> list:
        if len(set(fields)) != len(fields):
            raise self._fail("duplicate field names in header", header)
        rows: list[dict] = []
        row_indent: int | None = None
        for _ in range(n):
            line = self._peek()
            if line is None or line.indent <= header.indent:
                raise self._fail(f"table declared {n} rows but has {len(rows)}", line or header)
            if row_indent is None:
                row_indent = line.indent
            elif line.indent != row_indent:
                raise self._fail("inconsistent row indentation", line)
            self.pos += 1
            cells = self._split_cells(line.text, line)
            if len(cells) != len(fields):
                raise self._fail(
                    f"row has {len(cells)} cells but header declares {len(fields)} fields", line
                )
            rows.append(dict(zip(fields, cells, strict=True)))
        extra = self._peek()
        if extra is not None and extra.indent > header.indent:
            raise self._fail(f"table declared {n} rows but more follow", extra)
        return rows

    def _list_items(self, n: int, header: _Line) -> list:
        items: list[Any] = []
        item_indent: int | None = None
        for _ in range(n):
            line = self._peek()
            if line is None or line.indent <= header.indent:
                raise self._fail(f"array declared {n} items but has {len(items)}", line or header)
            if item_indent is None:
                item_indent = line.indent
            elif line.indent != item_indent:
                raise self._fail("inconsistent list item indentation", line)
            self.pos += 1
            items.append(self._list_item(line))
        extra = self._peek()
        if extra is not None and extra.indent > header.indent:
            raise self._fail(f"array declared {n} items but more follow", extra)
        return items

    def _list_item(self, line: _Line) -> Any:
        text = line.text
        if text == "-":
            child = self._peek()
            if child is None or child.indent <= line.indent:
                raise self._fail("expected an indented object block after '-'", line)
            return self._object(child.indent)
        if not text.startswith("- "):
            raise self._fail("expected list item starting with '-'", line)
        rest = text[2:]
        if rest == "{}":
            return {}
        if rest.startswith("["):
            return self._array_body(rest, line)
        return self._scalar(rest, line)

    # -- scalars -----------------------------------------------------------

    def _scalar(self, raw: str, line: _Line) -> Any:
        if raw.startswith('"'):
            try:
                value = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise self._fail(f"invalid quoted string: {exc.msg}", line) from exc
            if not isinstance(value, str):
                raise self._fail("quoted value must be a string", line)
            return value
        if raw == "null":
            return None
        if raw == "true":
            return True
        if raw == "false":
            return False
        if _NUMBER_RE.match(raw):
            if any(c in raw for c in ".eE"):
                return float(raw)
            return int(raw)
        return raw

    def _split_cells(self, text: str, line: _Line) -> list[Any]:
        cells: list[Any] = []
        i = 0
        n = len(text)
        while True:
            if i < n and text[i] == '"':
                end = _closing_quote(text, i)
                if end is None:
                    raise self._fail("unterminated quoted cell", line)
                token = text[i : end + 1]
                try:
                    cells.append(json.loads(token))
                except json.JSONDecodeError as exc:
                    raise self._fail(f"invalid quoted cell: {exc.msg}", line) from exc
                i = end + 1
                if i == n:
                    return cells
                if text[i] != self.delimiter:
                    raise self._fail("expected delimiter after quoted cell", line)
                i += 1
            else:
                j = text.find(self.delimiter, i)
                if j == -1:
                    raw = text[i:]
                    if raw == "":
                        raise self._fail('empty cell (use "" for an empty string)', line)
                    cells.append(self._scalar(raw, line))
                    return cells
                raw = text[i:j]
                if raw == "":
                    raise self._fail('empty cell (use "" for an empty string)', line)
                cells.append(self._scalar(raw, line))
                i = j + 1


def _closing_quote(text: str, start: int) -> int | None:
    """Index of the closing '"' for the string opening at *start*, or None."""
    i = start + 1
    while i < len(text):
        c = text[i]
        if c == "\\":
            i += 2
            continue
        if c == '"':
            return i
        i += 1
    return None
