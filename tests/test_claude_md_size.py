"""`tools/claude_md_size_gate.py` — `CLAUDE.md` stays under 150 lines and 2,700 words.

**What is being guarded.** `CLAUDE.md`'s intro states a ceiling and names `wc -l -w CLAUDE.md` as
the way to measure it (the option A plan's § 5.1 calls that D4's instrument); three earlier
slimming passes grew the file back within days because nothing enforced any ceiling. **So the
number this gate must produce is `wc`'s, own-line HTML comments included** — they never reach a
session's context, but the figure a person types to check the file counts them, and a guard that
counted differently would disagree with `wc` where nobody could say why. (The plan's § 5.1
suggested excluding them "as the hygiene rule does"; the gate follows `wc` instead, and reversing
that changes every test here that counts a comment.)

**`wc` is an oracle only where it agrees with the definition of a word the gate follows** — a run of
non-whitespace. GNU `wc` up to at least coreutils 9.1 counts a word only if it holds a printable
character, so in the C locale it skips a lone `—`, a lone NUL and a lone 0xff byte (measured
20261019: `wc -w CLAUDE.md` is 1450 on 8.32 and 9.1 in the C locale and 1497 in `C.UTF-8`, on 9.7
and 9.12 in any locale, and on macOS; 9.2 to 9.6 were not measured). CI runs this suite on ubuntu
only, so the primary pins are **counts worked out by hand**; each comparison with the real `wc` is
either on a body every build agrees on, under a pinned locale, or guarded by a probe that skips
with its reason. This file's first version took `LC_ALL=C` to be "the same on every wc", and it is
not.

**Why the boundary tests use the literals 150 and 2700.** A test that imported the gate's
constants would follow a mutant that moved them and prove nothing. The literals are the file's own
promise, and one test below holds the promise and the prose together. A *ceiling* is the largest
permitted value, so exactly 150 passes — the intro's word is "under", D4's is "hard ceiling", and
this reads both as "within".

**Every failing case asserts the reason it printed, not just a non-zero status**, and the boundary
cases assert that the *other* ceiling was not named. An uncaught exception also exits `1`, so a
status alone cannot tell a gate that measured and refused from one that crashed before measuring.

Exercised as a subprocess, argument parsing included, for the reason
`tests/test_markdown_link_gate.py` gives: the thing under test is the artifact that runs, not an
import of it. `CLAUDE.md` is the real file under test and this module never writes to it; every
oversized case lives in a `tmp_path` repository.
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
GATE = REPO / "tools" / "claude_md_size_gate.py"

#: `wc -l -w` for the real file prints `<lines> <words> CLAUDE.md`; the gate prints the same two
#: numbers (words with thousands separators) after `CLAUDE.md is`.
MEASURED = re.compile(r"CLAUDE\.md is (\d+) lines / ([\d,]+) words")

#: How many lines of `CLAUDE.md` the ceiling sentence is looked for in: its intro. A sentence of the
#: same shape further down is some other statement, and must not stand in for the intro's.
INTRO_LINES = 15


def _run(repo: Path | None = None, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    argv = [sys.executable, str(GATE)]
    if repo is not None:
        argv += ["--repo", str(repo)]
    return subprocess.run(argv, capture_output=True, text=True, cwd=cwd)


def _text(lines: int, words: int, separator: str = " ") -> str:
    """Text holding exactly `lines` newline characters and exactly `words` words.

    One word on each line but the last, which carries the rest — so both counts are known without
    reading the gate's own arithmetic.
    """
    assert 1 <= lines <= words
    one_each = "w\n" * (lines - 1)
    rest = separator.join(["w"] * (words - (lines - 1))) + "\n"
    return one_each + rest


def _repo_with(tmp_path: Path, body: str | bytes) -> Path:
    data = body.encode("utf-8") if isinstance(body, str) else body
    (tmp_path / "CLAUDE.md").write_bytes(data)
    return tmp_path


def _wc(path: Path, *, locale: str) -> tuple[int, int]:
    """`(lines, words)` from the real `wc -l -w`, the instrument `CLAUDE.md`'s intro names, under a
    pinned `LC_ALL`: which words it counts depends on the locale (see the module docstring), so the
    caller says which reading it is comparing against."""
    out = subprocess.run(
        ["wc", "-l", "-w", str(path)],
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, "LC_ALL": locale},
    ).stdout
    lines, words = out.split()[:2]
    return int(lines), int(words)


def _utf8_wc_counts_a_lone_dash() -> bool:
    """Whether `wc -w` under `C.UTF-8` counts the lone em dash in `a — b` as a word — POSIX's
    definition, which the gate follows. Old GNU `wc` does not in the C locale, and a build with no
    `C.UTF-8` falls back to it; either way the comparison would measure the oracle, not the gate."""
    if shutil.which("wc") is None:
        return False
    try:
        probe = subprocess.run(
            ["wc", "-w"],
            input="a — b\n".encode(),
            capture_output=True,
            check=True,
            env={**os.environ, "LC_ALL": "C.UTF-8"},
        )
        return int(probe.stdout.split()[0]) == 3
    except (OSError, subprocess.CalledProcessError, ValueError, IndexError):
        return False


def _gate_counts(result: subprocess.CompletedProcess[str]) -> tuple[int, int]:
    match = MEASURED.search(result.stdout)
    assert match, f"the gate did not print what it measured:\n{result.stdout}\n{result.stderr}"
    return int(match[1]), int(match[2].replace(",", ""))


needs_wc = pytest.mark.skipif(shutil.which("wc") is None, reason="needs the real wc to compare")
needs_posix_wc = pytest.mark.skipif(
    not _utf8_wc_counts_a_lone_dash(),
    reason="wc under C.UTF-8 does not count a lone multibyte character as a word, as POSIX does",
)


def test_the_real_claude_md_is_inside_its_ceiling() -> None:
    result = _run()
    assert result.returncode == 0, result.stderr
    lines, words = _gate_counts(result)
    assert lines <= 150 and words <= 2700
    assert "ceiling 150 / 2,700" in result.stdout, "the success line states the ceilings it used"


def test_the_default_is_this_repository_whatever_the_working_directory(tmp_path: Path) -> None:
    """With no `--repo` the gate measures the repository it lives in. Run from a directory that
    holds a different, oversized `CLAUDE.md`, a gate defaulting to the working directory would
    measure that one and refuse."""
    _repo_with(tmp_path, _text(300, 5000))
    from_elsewhere = _run(cwd=tmp_path)
    assert from_elsewhere.returncode == 0, from_elsewhere.stderr
    assert _gate_counts(from_elsewhere) == _gate_counts(_run(REPO))


@needs_posix_wc
def test_the_count_is_the_one_wc_reports_for_the_real_file() -> None:
    """The real file, under `C.UTF-8`: the locale in which every `wc` build counts a lone `—` (this
    file holds thirty). A person on old GNU `wc` in the C locale gets 1450 for 1497 words and the
    same verdict; that is the oracle deviating, not the gate."""
    assert _gate_counts(_run()) == _wc(REPO / "CLAUDE.md", locale="C.UTF-8")


NON_ASCII = "§ — 🛑 two\twords\n\n   padded   line   \nlast line has no newline"


def test_non_ascii_text_is_counted_by_whitespace_not_by_character(tmp_path: Path) -> None:
    """Section signs, em dashes and an emoji are words, not separators — `CLAUDE.md` is full of
    them. Three newlines and twelve words: `§ — 🛑 two words` (5), `padded line` (2) and
    `last line has no newline` (5), worked out by hand."""
    assert _gate_counts(_run(_repo_with(tmp_path, NON_ASCII))) == (3, 12)


@needs_posix_wc
def test_the_count_matches_wc_on_text_that_is_not_plain_ascii(tmp_path: Path) -> None:
    repo = _repo_with(tmp_path, NON_ASCII)
    assert _gate_counts(_run(repo)) == _wc(repo / "CLAUDE.md", locale="C.UTF-8")


#: Every element is a shape a text-based counter gets wrong: CRLF and a lone CR (only `\n` is a
#: line), a byte-order mark and a NUL standing as words of their own (a mutant that strips either
#: from an end changes the count only there), `\xff` (not UTF-8), a file separator `\x1c`
#: (`str.split` splits on it, `wc` does not), a vertical tab and a form feed (both whitespace), an
#: accented letter, a fenced block and a **multi-line** comment (both ordinary words).
BYTES = (
    b"\xef\xbb\xbf lead\r\nsecond\rthird\r\n"
    b"fs\x1csplit and \xff bad and caf\xc3\xa9 and vt\x0bsplit and ff\x0csplit\n"
    b"```\nfenced words stay\n```\n"
    b"<!--\na multi-line\ncomment block\n-->\n"
    b"last \x00"
)


def test_the_count_is_over_bytes_and_pinned_by_hand(tmp_path: Path) -> None:
    r"""**10 lines and 29 words, worked out by hand — the primary pin, because `wc` itself disagrees
    here.** Newlines: two in the first row (`\r\n` twice, the lone `\r` is not one), one in the
    second, three in the fence, four in the comment: 10. Words: the BOM, `lead`, `second`, `third`
    (4); `fs\x1csplit`, `and`, `\xff`, `bad`, `and`, `café`, `and`, `vt`, `split`, `and`, `ff`,
    `split` (12, the vertical tab and form feed being whitespace and the file separator not);
    the fence's five (5); the comment's six (6); `last` and the NUL (2): 29."""
    assert _gate_counts(_run(_repo_with(tmp_path, BYTES))) == (10, 29)


#: `BYTES` with each of the three tokens that old GNU `wc` refuses to call a word glued to an ASCII
#: letter — the body every `wc` build agrees on under `LC_ALL=C`.
GLUED = (
    BYTES.replace(b"\xef\xbb\xbf lead", b"x\xef\xbb\xbf lead")
    .replace(b"\xff bad", b"x\xff bad")
    .replace(b"last \x00", b"last x\x00")
)


@needs_wc
def test_the_count_matches_wc_on_bytes_every_wc_agrees_on(tmp_path: Path) -> None:
    """Measured 20261019 under `LC_ALL=C` on macOS and on GNU coreutils 8.32, 9.1, 9.7 and 9.12:
    10 lines and 29 words on every one."""
    assert GLUED != BYTES
    repo = _repo_with(tmp_path, GLUED)
    assert _gate_counts(_run(repo)) == _wc(repo / "CLAUDE.md", locale="C") == (10, 29)


def test_a_unicode_space_is_not_a_separator(tmp_path: Path) -> None:
    """The documented difference from some `wc` in a UTF-8 locale (U+00A0 on macOS), pinned so it is
    a decision rather than an accident: the count splits on ASCII whitespace only."""
    body = "a\u00a0b\u2003c\n"
    assert _gate_counts(_run(_repo_with(tmp_path, body))) == (1, 1)


@pytest.mark.parametrize(
    ("lines", "words"),
    [(150, 150), (1, 2700)],
    ids=["exactly 150 lines", "exactly 2700 words"],
)
def test_exactly_at_a_ceiling_passes(tmp_path: Path, lines: int, words: int) -> None:
    """A ceiling is the largest permitted value: the boundary is *over*, not *at*."""
    result = _run(_repo_with(tmp_path, _text(lines, words)))
    assert result.returncode == 0, result.stderr
    assert _gate_counts(result) == (lines, words)


@pytest.mark.parametrize(
    ("lines", "words", "reason", "not_named"),
    [
        (151, 151, "151 lines, over the ceiling of 150", "words, over"),
        (1, 2701, "2,701 words, over the ceiling of 2,700", "lines, over"),
    ],
    ids=["one line over", "one word over"],
)
def test_one_over_a_ceiling_fails_naming_only_it(
    tmp_path: Path, lines: int, words: int, reason: str, not_named: str
) -> None:
    result = _run(_repo_with(tmp_path, _text(lines, words)))
    assert result.returncode == 1
    assert reason in result.stderr, result.stderr
    assert not_named not in result.stderr, "the ceiling that was kept must not be reported"
    assert result.stdout == "", "a failing run must not also print the success line"


def test_both_ceilings_are_reported_when_both_are_over(tmp_path: Path) -> None:
    """An editor told only about the lines trims lines and meets the words next push."""
    result = _run(_repo_with(tmp_path, _text(160, 2800)))
    assert result.returncode == 1
    assert "160 lines, over the ceiling of 150" in result.stderr, result.stderr
    assert "2,800 words, over the ceiling of 2,700" in result.stderr, result.stderr


@pytest.mark.parametrize(
    ("lines", "words"),
    [(473, 6033), (5000, 40000)],
    ids=["the file as it was before A3", "past 64 KiB"],
)
def test_the_numbers_printed_are_the_real_ones_at_scale(
    tmp_path: Path, lines: int, words: int
) -> None:
    """A gate whose status is right and whose numbers are not — a count capped, a read cut short —
    sends the editor to trim to a figure that was never the file's. 473 and 6,033 are what `wc`
    printed for the file before its regeneration; the second case is bigger than any single read
    a careless implementation would make (64 KiB)."""
    body = _text(lines, words)
    assert len(body) > 65536 or lines == 473
    result = _run(_repo_with(tmp_path, body))
    assert result.returncode == 1
    assert f"{lines} lines, over the ceiling of 150" in result.stderr, result.stderr
    assert f"{words:,} words, over the ceiling of 2,700" in result.stderr, result.stderr


def test_a_last_line_with_no_newline_is_not_counted_as_wc_does(tmp_path: Path) -> None:
    """`wc -l` counts newline characters, so 150 newlines plus an unterminated line is *150*, and a
    `splitlines()` count would call it 151 and refuse a file `wc` passes."""
    repo = _repo_with(tmp_path, "w\n" * 150 + "unterminated")
    result = _run(repo)
    assert result.returncode == 0, result.stderr
    assert _gate_counts(result)[0] == 150


def test_an_empty_file_is_measured_not_skipped(tmp_path: Path) -> None:
    result = _run(_repo_with(tmp_path, ""))
    assert result.returncode == 0, result.stderr
    assert _gate_counts(result) == (0, 0)


def test_a_file_of_nothing_but_newlines_is_over_the_line_ceiling(tmp_path: Path) -> None:
    """No words at all, and still 400 lines: a guard that looked only at files with words in them
    would wave it through."""
    result = _run(_repo_with(tmp_path, "\n" * 400))
    assert result.returncode == 1
    assert "400 lines, over the ceiling of 150" in result.stderr, result.stderr
    assert "words, over" not in result.stderr, "there are no words to be over a ceiling"


def test_own_line_html_comments_are_counted(tmp_path: Path) -> None:
    """`wc` has no notion of a comment, and the intro names `wc`. These comments are free in a
    session's context and cost budget here, on purpose."""
    by_lines = _run(_repo_with(tmp_path, "<!-- provenance -->\n" * 11 + "w\n" * 140))
    assert by_lines.returncode == 1
    assert "151 lines, over the ceiling of 150" in by_lines.stderr, by_lines.stderr

    words = ["<!--", *["w"] * 2699, "-->"]
    by_words = _run(_repo_with(tmp_path, " ".join(words) + "\n"))
    assert by_words.returncode == 1
    assert "2,701 words, over the ceiling of 2,700" in by_words.stderr, by_words.stderr


def test_a_comment_spanning_lines_is_counted(tmp_path: Path) -> None:
    """Provenance comments grow: the one-line case above is the shape they start in, and a
    block that opens on one line and closes on a later one is where they end up."""
    by_lines = _run(_repo_with(tmp_path, "<!--\n" + "w\n" * 149 + "-->\n"))
    assert by_lines.returncode == 1
    assert "151 lines, over the ceiling of 150" in by_lines.stderr, by_lines.stderr

    by_words = _run(_repo_with(tmp_path, "<!--\n" + " ".join(["w"] * 2699) + "\n-->\n"))
    assert by_words.returncode == 1
    assert "2,701 words, over the ceiling of 2,700" in by_words.stderr, by_words.stderr


@pytest.mark.parametrize("separator", ["\t", "  ", " \t "], ids=["tab", "double space", "mixed"])
def test_words_are_split_on_any_run_of_whitespace(tmp_path: Path, separator: str) -> None:
    """Splitting on a single space reads tab-separated text as one word and a double space as an
    empty one — and a table cell padded for alignment is exactly that."""
    at_ceiling = _text(1, 2700, separator)
    assert separator in at_ceiling, "the fixture must actually carry the separator it is named for"
    at = _run(_repo_with(tmp_path, at_ceiling))
    assert at.returncode == 0, at.stderr
    over = _run(_repo_with(tmp_path, _text(1, 2701, separator)))
    assert over.returncode == 1
    assert "2,701 words, over the ceiling of 2,700" in over.stderr, over.stderr


def test_the_failure_says_to_move_a_rule_not_to_delete_it(tmp_path: Path) -> None:
    """Three passes grew back because trimming without a destination is how the file got to 473
    lines: the remedy has to name the destination, say what to leave behind and say what not to
    do."""
    result = _run(_repo_with(tmp_path, _text(151, 151)))
    assert result.returncode == 1
    assert "Move a rule to the document that owns it" in result.stderr, result.stderr
    assert "docs/README.md" in result.stderr, "the routing table is where the owner is found"
    assert "leave a pointer behind" in result.stderr, result.stderr
    assert "Do not delete the rule" in result.stderr, result.stderr


def test_a_missing_claude_md_fails_rather_than_passing(tmp_path: Path) -> None:
    result = _run(tmp_path)
    assert result.returncode == 1
    assert "cannot read" in result.stderr and "CLAUDE.md" in result.stderr, result.stderr
    assert result.stdout == ""


def test_a_claude_md_that_is_a_directory_fails_rather_than_passing(tmp_path: Path) -> None:
    (tmp_path / "CLAUDE.md").mkdir()
    result = _run(tmp_path)
    assert result.returncode == 1
    assert "cannot read" in result.stderr, result.stderr


@pytest.mark.skipif(
    not hasattr(os, "geteuid") or os.geteuid() == 0,
    reason="root reads any file, Windows has no chmod",
)
def test_a_claude_md_that_cannot_be_read_fails_rather_than_passing(tmp_path: Path) -> None:
    """`PermissionError` is neither a missing file nor a directory, and "whatever the reason" is
    what the VERIFICATION row promises."""
    repo = _repo_with(tmp_path, "w\n")
    unreadable = tmp_path / "CLAUDE.md"
    unreadable.chmod(0)
    try:
        result = _run(repo)
    finally:
        unreadable.chmod(0o644)
    assert result.returncode == 1
    assert "cannot read" in result.stderr, result.stderr
    assert "Traceback" not in result.stderr, result.stderr


def test_a_repository_that_is_not_a_directory_fails_rather_than_crashing(tmp_path: Path) -> None:
    """`NotADirectoryError` is neither of the two errors the other cases raise: the handler has to
    be `OSError` itself, or this exits `1` with a traceback — the same status as a refusal."""
    not_a_directory = tmp_path / "file"
    not_a_directory.write_text("w\n", encoding="utf-8")
    result = _run(not_a_directory)
    assert result.returncode == 1
    assert "cannot read" in result.stderr, result.stderr
    assert "Traceback" not in result.stderr, result.stderr


def _stated_ceilings(text: str) -> tuple[int, int] | None:
    """The `(lines, words)` ceiling the *intro* of a document states as *under N lines and M
    words*, wrapped or not, or `None` when its intro states none."""
    intro = "\n".join(text.splitlines()[:INTRO_LINES])
    match = re.search(r"under\s+([\d,]+)\s+lines\s+and\s+([\d,]+)\s+words", intro)
    if match is None:
        return None
    return int(match[1].replace(",", "")), int(match[2].replace(",", ""))


def _ceiling_problem(text: str) -> str | None:
    """What is wrong with the ceiling `text` states against the gate's (150, 2700), or `None`."""
    stated = _stated_ceilings(text)
    if stated is None:
        return (
            "CLAUDE.md's intro no longer states its ceiling as 'under N lines and M words'. "
            "Restore that sentence, or change this reader and the gate together — a ceiling "
            "stated nowhere is a ceiling nobody can check the guard against."
        )
    if stated != (150, 2700):
        return (
            f"The first 'under N lines and M words' in CLAUDE.md's first {INTRO_LINES} lines "
            f"states a ceiling of {stated}, but tools/claude_md_size_gate.py and its tests "
            "enforce (150, 2700). A ceiling change is deliberate: change the prose, "
            "the gate's MAX_LINES / MAX_WORDS and the literals in this file in one commit."
        )
    return None


def test_the_stated_ceiling_is_read_wrapped_and_absent_when_unstated() -> None:
    """The reader below has to be able to return *nothing found*, or the test that uses it could
    only ever pass."""
    assert _stated_ceilings("stays under\n150 lines and 2,700 words (`wc`)") == (150, 2700)
    assert _stated_ceilings("stays under 90 lines and 1,000 words") == (90, 1000)
    assert _stated_ceilings("keeps itself short") is None
    assert _stated_ceilings("a table of 150 lines and 2,700 words in all") is None, (
        "without 'under' it is a size, not a ceiling"
    )


def test_only_the_intro_can_state_the_ceiling() -> None:
    """With the intro's sentence gone, the same words further down are some other statement. The
    window is pinned by literals — line 15 is inside it and line 16 is not — so it cannot widen
    or narrow in silence."""
    sentence = "stays under 150 lines and 2,700 words"
    assert INTRO_LINES == 15
    assert _stated_ceilings("\n" * 14 + sentence) == (150, 2700)
    assert _stated_ceilings("\n" * 15 + sentence) is None
    earlier = (
        "stays under 90 lines and 1,000 words\n"
        + "x\n" * 3
        + "stays under 150 lines and 2,700 words"
    )
    assert _stated_ceilings(earlier) == (90, 1000), "the first sentence in the intro is the one"


def test_a_ceiling_that_disagrees_with_the_gate_is_a_problem() -> None:
    """The comparison itself, on text: nothing but a live edit of `CLAUDE.md` would otherwise ever
    exercise the branches that say *red*."""
    assert _ceiling_problem("stays under 150 lines and 2,700 words") is None
    lines_off = _ceiling_problem("stays under 140 lines and 2,700 words")
    assert lines_off is not None and "(140, 2700)" in lines_off
    words_off = _ceiling_problem("stays under 150 lines and 2,600 words")
    assert words_off is not None and "(150, 2600)" in words_off
    both_off = _ceiling_problem("stays under 100 lines and 1,000 words")
    assert both_off is not None and "(100, 1000)" in both_off
    unstated = _ceiling_problem("a short file")
    assert unstated is not None and "no longer states its ceiling" in unstated


def test_the_ceilings_are_the_ones_claude_md_states() -> None:
    """The gate and the file's own intro line are two statements of one number. Raising the ceiling
    in one place only is how the guard would start refusing a file that says it is fine, or passing
    one that says it is not — so this holds them together, and the boundary tests above hold the
    gate to the same literals."""
    problem = _ceiling_problem((REPO / "CLAUDE.md").read_text(encoding="utf-8"))
    assert problem is None, problem
