"""`CLAUDE.md` stays inside the size it says it stays inside — a gate, not an intention.

**Why a gate.** Three earlier slimming passes each grew the file back within days
(`plans/20261018_2354-option-a-review-coverage-and-claude-md.md` § 5.1), and A3's regenerated file
states a ceiling of 150 lines and 2,700 words (decision D4) that nothing enforced. A rule that only
the file repeats is a rule the next session reads and then adds a paragraph beside.

**The instrument is `wc`, so this counts the way `wc -l -w` counts** — the file's own intro names
`wc -l -w CLAUDE.md` as the measure, and that plan's § 5.1 calls it D4's instrument. That has one
consequence worth stating: **own-line HTML comments are counted.** They never reach a session's
context, and the same section's recommendation for this guard was to exclude them "as the hygiene
rule does" — this gate follows `wc` instead, because the number a person types to check the file is
`wc`'s, and a guard that counts differently would be red where `wc` says green (or the other way
round) with nobody able to say why. Provenance comments cost budget here, on purpose; reversing
that means changing `measure()` and every test that counts a comment (the own-line, the spanning
and the two `wc` comparisons).

* **Lines** are newline bytes, as `wc -l` reports them: a last line with no trailing newline is not
  counted, and `str.splitlines()` would count it.
* **Words** are runs of non-whitespace bytes, split on ASCII whitespace: POSIX's definition, and
  what `wc -w` reports on macOS and on GNU coreutils 9.7 and later. **GNU `wc` up to at least 9.1
  also requires a word to hold a printable character**, so in the C locale it does not count a lone
  NUL, a lone byte above 0x7f or a lone multibyte character such as `—`: measured 20261019,
  `wc -w CLAUDE.md` prints 1450 words on coreutils 8.32 and 9.1 in the C locale and 1497 in
  `C.UTF-8`, which is what this gate counts (9.2 to 9.6 were not measured). The file's headroom
  (about 1,500 words against 2,700) keeps that out of the verdict; it is why
  `tests/test_claude_md_size.py` pins the count with literals worked out by hand and compares with
  `wc` only where `wc` agrees. In a UTF-8 locale some `wc` implementations also split on certain
  Unicode spaces (U+00A0 on macOS) and this gate does not; `CLAUDE.md` holds none, and the
  comparison on the real file would show one as a disagreement.

**A red here is fixed by moving a rule, never by deleting one.** The message says where: to the
document that already owns the fact (`docs/README.md` routes each fact to its one home) with a
pointer left behind, in the same commit that put it over.

Stdlib only, run as `python3 tools/claude_md_size_gate.py [--repo ROOT]`. Exit `0` within the
ceilings, `1` over either, or when `CLAUDE.md` cannot be read — a missing file is a failure, never a
pass. It prints the measured numbers on success too, so a gate that measured nothing is visible as
one. **Deliberately not in `check.sh`:** `pytest` runs `tests/test_claude_md_size.py`, which runs
this against the real file, and a second invocation would only be a second place to forget.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

#: D4 — the hard ceiling, not an aim (the aim is about 100 lines). Changing either number is a
#: deliberate act, and `tests/test_claude_md_size.py` fails until `CLAUDE.md`'s own intro line
#: states the same two numbers, so the prose and this constant cannot drift apart in silence.
MAX_LINES = 150
MAX_WORDS = 2700

REMEDY = (
    "Move a rule to the document that owns it (docs/README.md routes each fact to its one home) "
    "and leave a pointer behind. Do not delete the rule to make room."
)


def measure(data: bytes) -> tuple[int, int]:
    """`(lines, words)` exactly as `wc -l -w` reports them for these bytes."""
    return data.count(b"\n"), len(data.split())


def complaints(data: bytes) -> list[str]:
    """One sentence per ceiling that `data` is over. Empty means within both."""
    lines, words = measure(data)
    found: list[str] = []
    if lines > MAX_LINES:
        found.append(f"{lines} lines, over the ceiling of {MAX_LINES}")
    if words > MAX_WORDS:
        found.append(f"{words:,} words, over the ceiling of {MAX_WORDS:,}")
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0] if __doc__ else None)
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="repository root holding CLAUDE.md (default: this repository)",
    )
    args = parser.parse_args(argv)

    target = args.repo / "CLAUDE.md"
    try:
        data = target.read_bytes()
    except OSError as exc:
        print(
            f"FAIL: cannot read {target}: {exc}. A guard that measures nothing is not a pass.",
            file=sys.stderr,
        )
        return 1

    lines, words = measure(data)
    found = complaints(data)
    if found:
        print(
            f"FAIL: CLAUDE.md is {'; and '.join(found)} (`wc -l -w CLAUDE.md`, decision D4).",
            file=sys.stderr,
        )
        print(REMEDY, file=sys.stderr)
        return 1
    print(
        f"ok: CLAUDE.md is {lines} lines / {words:,} words "
        f"(ceiling {MAX_LINES} / {MAX_WORDS:,}, `wc -l -w`)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
