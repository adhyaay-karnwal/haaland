"""HAAL encoder: Python objects (JSON data model) -> HAAL text.

The encoder guarantees that ``decode(encode(x)) == x`` for every value ``x``
representable in the JSON data model (dicts with string keys, lists, strings,
ints, finite floats, bools, None), including key order.
"""

from __future__ import annotations

import json
import math
import re
from typing import Any

from .errors import HaalEncodeError

# Keys and root-level bare strings restricted to this set never collide with
# HAAL structural syntax (':', '[', '{', '"', '#', '-' prefix, delimiters,
# whitespace) under any supported delimiter.
_SAFE_KEY_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_./+-]*\Z")

# Exactly the JSON number grammar. Bare strings matching this must be quoted
# so they don't decode as numbers.
_NUMBER_RE = re.compile(r"^-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?\Z")

_RESERVED = frozenset({"null", "true", "false"})

SUPPORTED_DELIMITERS = (",", "\t", "|", ";")

# Contexts a scalar can appear in; each has different collision rules.
_CTX_LINE = "line"  # after "key: " -- runs to end of line
_CTX_CELL = "cell"  # inside a delimiter-separated row or inline array
_CTX_LIST = "list"  # after "- " in a list item
_CTX_ROOT = "root"  # entire single-line document


def encode(obj: Any, *, indent: int = 1, delimiter: str = ",") -> str:
    """Serialize *obj* to HAAL text.

    Args:
        obj: A value in the JSON data model.
        indent: Spaces per nesting level (default 1, the measured optimum).
        delimiter: Cell separator for rows and inline arrays.
    """
    if indent < 1:
        raise HaalEncodeError("indent must be >= 1")
    if delimiter not in SUPPORTED_DELIMITERS:
        raise HaalEncodeError(
            f"unsupported delimiter {delimiter!r}; expected one of {SUPPORTED_DELIMITERS}"
        )
    enc = _Encoder(indent, delimiter)
    return enc.document(obj)


class _Encoder:
    def __init__(self, indent: int, delimiter: str):
        self.indent = indent
        self.delimiter = delimiter
        self.lines: list[str] = []

    def document(self, obj: Any) -> str:
        if isinstance(obj, dict):
            if not obj:
                return "{}"
            self._object(obj, 0)
        elif isinstance(obj, list):
            self._array_with_header(prefix="", arr=obj, depth=0)
        else:
            return self._scalar(obj, _CTX_ROOT)
        return "\n".join(self.lines)

    # -- structure ---------------------------------------------------------

    def _pad(self, depth: int) -> str:
        return " " * (self.indent * depth)

    def _object(self, d: dict, depth: int) -> None:
        pad = self._pad(depth)
        for key, value in d.items():
            if not isinstance(key, str):
                raise HaalEncodeError(f"object keys must be strings, got {type(key).__name__}")
            ek = self._key(key)
            if isinstance(value, dict):
                if value:
                    self.lines.append(f"{pad}{ek}:")
                    self._object(value, depth + 1)
                else:
                    self.lines.append(f"{pad}{ek}: {{}}")
            elif isinstance(value, list):
                self._array_with_header(prefix=f"{pad}{ek}", arr=value, depth=depth)
            else:
                self.lines.append(f"{pad}{ek}: {self._scalar(value, _CTX_LINE)}")

    def _array_with_header(self, prefix: str, arr: list, depth: int) -> None:
        """Emit an array whose header line starts with *prefix* at *depth*."""
        n = len(arr)
        if all(_is_scalar(v) for v in arr):
            if n == 0:
                self.lines.append(f"{prefix}[0]:")
            else:
                cells = self.delimiter.join(self._scalar(v, _CTX_CELL) for v in arr)
                self.lines.append(f"{prefix}[{n}]: {cells}")
            return

        fields = _tabular_fields(arr)
        if fields is not None:
            header_fields = self.delimiter.join(self._key(f) for f in fields)
            self.lines.append(f"{prefix}[{n}]{{{header_fields}}}:")
            pad = self._pad(depth + 1)
            for item in arr:
                row = self.delimiter.join(self._scalar(item[f], _CTX_CELL) for f in fields)
                self.lines.append(f"{pad}{row}")
            return

        self.lines.append(f"{prefix}[{n}]:")
        pad = self._pad(depth + 1)
        for item in arr:
            if isinstance(item, dict):
                if item:
                    self.lines.append(f"{pad}-")
                    self._object(item, depth + 2)
                else:
                    self.lines.append(f"{pad}- {{}}")
            elif isinstance(item, list):
                self._array_with_header(prefix=f"{pad}- ", arr=item, depth=depth + 1)
            else:
                self.lines.append(f"{pad}- {self._scalar(item, _CTX_LIST)}")

    # -- scalars -----------------------------------------------------------

    def _key(self, k: str) -> str:
        if _SAFE_KEY_RE.match(k):
            return k
        return json.dumps(k, ensure_ascii=False)

    def _scalar(self, v: Any, ctx: str) -> str:
        if v is None:
            return "null"
        if v is True:
            return "true"
        if v is False:
            return "false"
        if isinstance(v, int):
            return str(v)
        if isinstance(v, float):
            if not math.isfinite(v):
                raise HaalEncodeError("NaN and Infinity are not representable in HAAL")
            return repr(v)
        if isinstance(v, str):
            return self._string(v, ctx)
        raise HaalEncodeError(f"cannot encode value of type {type(v).__name__}")

    def _string(self, s: str, ctx: str) -> str:
        if self._needs_quotes(s, ctx):
            return json.dumps(s, ensure_ascii=False)
        return s

    def _needs_quotes(self, s: str, ctx: str) -> bool:
        if s == "" or s != s.strip():
            return True
        if any(ord(c) < 0x20 or ord(c) == 0x7F for c in s):
            return True
        if s[0] == '"':
            return True
        if s in _RESERVED or _NUMBER_RE.match(s):
            return True
        if ctx == _CTX_CELL:
            # Cells split on the delimiter; the first cell of a row also
            # starts a physical line, where '#' would read as a comment.
            return self.delimiter in s or s[0] == "#"
        if ctx == _CTX_LIST:
            # "- [" opens a nested array header; "- {}" is an empty object.
            return s[0] == "[" or s == "{}"
        if ctx == _CTX_LINE:
            # "key: {}" is the empty-object literal.
            return s == "{}"
        if ctx == _CTX_ROOT:
            # A bare root string must not parse as a key line, array header,
            # empty object, comment, or list item.
            return not _SAFE_KEY_RE.match(s)
        return False


def _is_scalar(v: Any) -> bool:
    return v is None or isinstance(v, (str, int, float, bool))


def _tabular_fields(arr: list) -> list[str] | None:
    """Return the shared field list if *arr* qualifies for tabular form.

    Qualifies when every item is a non-empty dict with the same keys in the
    same order and every value is a scalar. Identical key order is required
    so decoding reproduces each object exactly.
    """
    first = arr[0]
    if not isinstance(first, dict) or not first:
        return None
    fields = list(first.keys())
    for item in arr:
        if not isinstance(item, dict) or list(item.keys()) != fields:
            return None
        for v in item.values():
            if not _is_scalar(v):
                return None
    if any(not isinstance(f, str) for f in fields):
        return None
    return fields
