"""haaland: HAAL, a token-efficient serialization language for LLM contexts.

HAAL represents the JSON data model with dramatically fewer tokens by
removing repeated keys and structural punctuation, while remaining lossless:
``loads(dumps(x)) == x`` for every JSON-representable value.

Basic usage:

    >>> import haaland
    >>> haaland.dumps({"users": [{"id": 1, "name": "Ada"}, {"id": 2, "name": "Grace"}]})
    'users[2]{id,name}:\\n 1,Ada\\n 2,Grace'
    >>> haaland.loads(_)
    {'users': [{'id': 1, 'name': 'Ada'}, {'id': 2, 'name': 'Grace'}]}
"""

from __future__ import annotations

from typing import IO, Any

from ._decoder import decode
from ._encoder import SUPPORTED_DELIMITERS, SUPPORTED_PROFILES, encode
from .errors import HaalDecodeError, HaalEncodeError, HaalError

__version__ = "0.2.0"

__all__ = [
    "SUPPORTED_DELIMITERS",
    "SUPPORTED_PROFILES",
    "HaalDecodeError",
    "HaalEncodeError",
    "HaalError",
    "__version__",
    "dump",
    "dumps",
    "load",
    "loads",
]


def dumps(
    obj: Any, *, indent: int = 1, delimiter: str | None = None, profile: str = "standard"
) -> str:
    """Serialize *obj* to a HAAL string. Mirrors ``json.dumps``.

    ``profile="dense"`` produces the measured maximum-efficiency encoding
    (space delimiter, no separator padding); see docs/design-notes.md.
    """
    return encode(obj, indent=indent, delimiter=delimiter, profile=profile)


def loads(text: str, *, delimiter: str | None = None, profile: str = "standard") -> Any:
    """Parse a HAAL string into Python objects. Mirrors ``json.loads``.

    Pass ``profile="dense"`` (or the explicit ``delimiter``) used at encode
    time; separator forms from both profiles are always accepted.
    """
    return decode(text, delimiter=delimiter, profile=profile)


def dump(
    obj: Any,
    fp: IO[str],
    *,
    indent: int = 1,
    delimiter: str | None = None,
    profile: str = "standard",
) -> None:
    """Serialize *obj* as HAAL to the file-like object *fp*."""
    fp.write(dumps(obj, indent=indent, delimiter=delimiter, profile=profile))
    fp.write("\n")


def load(fp: IO[str], *, delimiter: str | None = None, profile: str = "standard") -> Any:
    """Parse HAAL from the file-like object *fp*."""
    return loads(fp.read(), delimiter=delimiter, profile=profile)
