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
from ._encoder import SUPPORTED_DELIMITERS, encode
from .errors import HaalDecodeError, HaalEncodeError, HaalError

__version__ = "0.1.0"

__all__ = [
    "SUPPORTED_DELIMITERS",
    "HaalDecodeError",
    "HaalEncodeError",
    "HaalError",
    "__version__",
    "dump",
    "dumps",
    "load",
    "loads",
]


def dumps(obj: Any, *, indent: int = 1, delimiter: str = ",") -> str:
    """Serialize *obj* to a HAAL string. Mirrors ``json.dumps``."""
    return encode(obj, indent=indent, delimiter=delimiter)


def loads(text: str, *, delimiter: str = ",") -> Any:
    """Parse a HAAL string into Python objects. Mirrors ``json.loads``."""
    return decode(text, delimiter=delimiter)


def dump(obj: Any, fp: IO[str], *, indent: int = 1, delimiter: str = ",") -> None:
    """Serialize *obj* as HAAL to the file-like object *fp*."""
    fp.write(dumps(obj, indent=indent, delimiter=delimiter))
    fp.write("\n")


def load(fp: IO[str], *, delimiter: str = ",") -> Any:
    """Parse HAAL from the file-like object *fp*."""
    return loads(fp.read(), delimiter=delimiter)
