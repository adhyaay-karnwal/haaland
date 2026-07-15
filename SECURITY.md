# Security Policy

## Supported versions

Pre-1.0: only the latest release / `main` receives fixes.

## Reporting a vulnerability

Please report suspected vulnerabilities privately via
[GitHub Security Advisories](https://github.com/adhyaay-karnwal/haaland/security/advisories/new)
rather than public issues. You can expect an acknowledgment within 7 days.

## Threat model notes

- The decoder executes no code and supports no references/anchors or expansion
  constructs; documents parse in memory proportional to their input size.
- The package makes no network calls and has zero runtime dependencies.
- Parsing untrusted input: `haaland.loads` is strict and raises `HaalDecodeError`
  on malformed input. As with any parser, wrap it and bound input sizes at your
  application boundary.
