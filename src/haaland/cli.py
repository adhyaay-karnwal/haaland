"""``haal`` command-line interface.

Subcommands:
    encode  JSON -> HAAL
    decode  HAAL -> JSON
    stats   token comparison (JSON vs HAAL) for a JSON document
    check   validate a HAAL document

Files or stdin in, stdout out — composable in shell pipelines:

    curl -s https://api.example.com/users | haal encode | tee users.haal
    haal stats users.json
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from . import __version__, dumps, loads
from .errors import HaalError


def _read(path: str | None) -> str:
    if path is None or path == "-":
        return sys.stdin.read()
    with open(path, encoding="utf-8") as f:
        return f.read()


def _delimiter(name: str) -> str:
    named = {"comma": ",", "tab": "\t", "pipe": "|", "semicolon": ";"}
    if name in named:
        return named[name]
    return name


def _cmd_encode(args: argparse.Namespace) -> int:
    data = json.loads(_read(args.file))
    print(dumps(data, indent=args.indent, delimiter=_delimiter(args.delimiter)))
    return 0


def _cmd_decode(args: argparse.Namespace) -> int:
    value = loads(_read(args.file), delimiter=_delimiter(args.delimiter))
    print(json.dumps(value, ensure_ascii=False, indent=args.indent or None))
    return 0


def _cmd_check(args: argparse.Namespace) -> int:
    try:
        loads(_read(args.file), delimiter=_delimiter(args.delimiter))
    except HaalError as exc:
        print(f"invalid: {exc}", file=sys.stderr)
        return 1
    print("valid")
    return 0


def _cmd_stats(args: argparse.Namespace) -> int:
    from .tokens import KNOWN_ENCODINGS, compare

    data: Any = json.loads(_read(args.file))
    texts = {
        "json": json.dumps(data, ensure_ascii=False, separators=(",", ":")),
        "json (2-space)": json.dumps(data, ensure_ascii=False, indent=2),
        "haal": dumps(data, delimiter=_delimiter(args.delimiter)),
    }
    encodings = KNOWN_ENCODINGS if args.encoding == "all" else (args.encoding,)
    for encoding in encodings:
        results = compare(texts, encoding)
        print(f"tokenizer: {encoding}")
        width = max(len(name) for name in results)
        for name, r in results.items():
            saving = f"  ({r['vs_json_pct']:+.1f}% vs JSON)" if name != "json" else ""
            print(f"  {name:<{width}}  {r['tokens']:>7,} tokens{saving}")
        print()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="haal",
        description="HAAL: token-efficient serialization for LLM contexts.",
    )
    parser.add_argument("--version", action="version", version=f"haal {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument("file", nargs="?", default=None, help="input file (default: stdin)")
        p.add_argument(
            "--delimiter",
            default="comma",
            help="cell delimiter: comma, tab, pipe, or semicolon (default: comma)",
        )

    p = sub.add_parser("encode", help="convert JSON to HAAL")
    add_common(p)
    p.add_argument("--indent", type=int, default=1, help="spaces per level (default: 1)")
    p.set_defaults(func=_cmd_encode)

    p = sub.add_parser("decode", help="convert HAAL to JSON")
    add_common(p)
    p.add_argument("--indent", type=int, default=0, help="JSON output indent (default: compact)")
    p.set_defaults(func=_cmd_decode)

    p = sub.add_parser("check", help="validate a HAAL document")
    add_common(p)
    p.set_defaults(func=_cmd_check)

    p = sub.add_parser("stats", help="token comparison for a JSON document")
    add_common(p)
    p.add_argument(
        "--encoding",
        default="all",
        help="tiktoken encoding (o200k_base, cl100k_base, or 'all'; default: all)",
    )
    p.set_defaults(func=_cmd_stats)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except HaalError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON input: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"error: {exc.filename}: no such file", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
