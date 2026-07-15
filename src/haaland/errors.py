"""Exception types raised by the HAAL codec."""

from __future__ import annotations


class HaalError(ValueError):
    """Base class for all HAAL codec errors."""


class HaalEncodeError(HaalError):
    """Raised when a Python value cannot be represented in HAAL."""


class HaalDecodeError(HaalError):
    """Raised when a document is not valid HAAL.

    Attributes:
        line: 1-based line number in the source document, when known.
    """

    def __init__(self, message: str, line: int | None = None):
        self.line = line
        if line is not None:
            message = f"line {line}: {message}"
        super().__init__(message)
