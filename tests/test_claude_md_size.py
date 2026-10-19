"""`tools/claude_md_size_gate.py` — `CLAUDE.md` stays under 150 lines and 2,700 words.

**What is being guarded, and why it is not a count of sentences.** The file states its own ceiling,
decision D4 of `plans/20261018_2354-option-a-review-coverage-and-claude-md.md` names
`wc -l -w CLAUDE.md` as the instrument, and three earlier slimming passes grew back within days
because nothing enforced either. **So the number this gate must produce is `wc`'s, own-line HTML
comments included** — they never reach a session's context, but the figure a person types to check
the file counts them, and a guard that counted differently would disagree with `wc` where nobody
could say why. `test_the_count_is_the_one_wc_reports_for_the_real_file` compares the two on the real
file and `test_the_count_matches_wc_on_text_that_is_not_plain_ascii` on a hand-built one.

**Why every fixture is built from a line count and a word count, and the boundary tests use the
literals 150 and 2700.** A test that imported the gate's constants would follow a mutant that moved
them and prove nothing. The literals are the file's own promise, and one test below holds the
promise and the prose together.

**Every failing case asserts the reason it printed, not just a non-zero status.** An uncaught
exception also exits `1`, so a status alone cannot tell a gate that measured and refused from one
that crashed before measuring.

Exercised as a subprocess, argument parsing included, for the reason
`tests/test_markdown_link_gate.py` gives: the thing under test is the artifact that runs, not an
import of it. `CLAUDE.md` is the planner's file and this module never writes to it; every oversized
case lives in a `tmp_path` repository.
"""

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


def _run(repo: Path | None = None) -> subprocess.CompletedProcess[str]:
    argv = [sys.executable, str(GATE)]
    if repo is not None:
        argv += ["--repo", str(repo)]
    return subprocess.run(argv, capture_output=True, text=True)


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


def _wc(path: Path) -> tuple[int, int]:
    """`(lines, words)` from the real `wc -l -w`, the instrument decision D4 names."""
    out = subprocess.run(
        ["wc", "-l", "-w", str(path)], capture_output=True, text=True, check=True
    ).stdout
    lines, words = out.split()[:2]
    return int(lines), int(words)


def _gate_counts(result: subprocess.CompletedProcess[str]) -> tuple[int, int]:
    match = MEASURED.search(result.stdout)
    assert match, f"the gate did not print what it measured:\n{result.stdout}\n{result.stderr}"
    return int(match[1]), int(match[2].replace(",", ""))


needs_wc = pytest.mark.skipif(shutil.which("wc") is None, reason="needs the real wc to compare")


def test_the_real_claude_md_is_inside_its_ceiling() -> None:
    result = _run()
    assert result.returncode == 0, result.stderr
    lines, words = _gate_counts(result)
    assert lines <= 150 and words <= 2700


@needs_wc
def test_the_count_is_the_one_wc_reports_for_the_real_file() -> None:
    assert _gate_counts(_run()) == _wc(REPO / "CLAUDE.md")


@needs_wc
def test_the_count_matches_wc_on_text_that_is_not_plain_ascii(tmp_path: Path) -> None:
    """Section signs, em dashes and an emoji are words to `wc`, not separators — `CLAUDE.md` is full
    of them — and tabs, runs of spaces, blank lines and a last line with no newline are the shapes a
    hand-rolled counter gets wrong."""
    body = "§ — 🛑 two\twords\n\n   padded   line   \nlast line has no newline"
    repo = _repo_with(tmp_path, body)
    assert _gate_counts(_run(repo)) == _wc(repo / "CLAUDE.md")


@pytest.mark.parametrize(
    ("lines", "words"),
    [(150, 150), (1, 2700)],
    ids=["exactly 150 lines", "exactly 2700 words"],
)
def test_exactly_at_a_ceiling_passes(tmp_path: Path, lines: int, words: int) -> None:
    """The boundary is *over*, not *at* — the file says it stays under 150, and means that 150 is
    the last number it may be."""
    result = _run(_repo_with(tmp_path, _text(lines, words)))
    assert result.returncode == 0, result.stderr
    assert _gate_counts(result) == (lines, words)


@pytest.mark.parametrize(
    ("lines", "words", "reason"),
    [
        (151, 151, "151 lines, over the ceiling of 150"),
        (1, 2701, "2,701 words, over the ceiling of 2,700"),
    ],
    ids=["one line over", "one word over"],
)
def test_one_over_a_ceiling_fails_naming_it(
    tmp_path: Path, lines: int, words: int, reason: str
) -> None:
    result = _run(_repo_with(tmp_path, _text(lines, words)))
    assert result.returncode == 1
    assert reason in result.stderr, result.stderr
    assert result.stdout == "", "a failing run must not also print the success line"


def test_both_ceilings_are_reported_when_both_are_over(tmp_path: Path) -> None:
    """An editor told only about the lines trims lines and meets the words next push."""
    result = _run(_repo_with(tmp_path, _text(160, 2800)))
    assert result.returncode == 1
    assert "160 lines, over the ceiling of 150" in result.stderr, result.stderr
    assert "2,800 words, over the ceiling of 2,700" in result.stderr, result.stderr


def test_a_last_line_with_no_newline_is_not_counted_as_wc_does(tmp_path: Path) -> None:
    """`wc -l` counts newline characters, so 150 newlines plus an unterminated line is *150*, and a
    `splitlines()` count would call it 151 and refuse a file `wc` passes."""
    repo = _repo_with(tmp_path, "w\n" * 150 + "unterminated")
    result = _run(repo)
    assert result.returncode == 0, result.stderr
    assert _gate_counts(result)[0] == 150


def test_own_line_html_comments_are_counted(tmp_path: Path) -> None:
    """Decision D4 names `wc`, and `wc` has no notion of a comment. These comments are free in a
    session's context and cost budget here, on purpose."""
    by_lines = _run(_repo_with(tmp_path, "<!-- provenance -->\n" * 11 + "w\n" * 140))
    assert by_lines.returncode == 1
    assert "151 lines, over the ceiling of 150" in by_lines.stderr, by_lines.stderr

    words = ["<!--", *["w"] * 2699, "-->"]
    by_words = _run(_repo_with(tmp_path, " ".join(words) + "\n"))
    assert by_words.returncode == 1
    assert "2,701 words, over the ceiling of 2,700" in by_words.stderr, by_words.stderr


@pytest.mark.parametrize("separator", ["\t", "  ", " \t "], ids=["tab", "double space", "mixed"])
def test_words_are_split_on_any_run_of_whitespace(tmp_path: Path, separator: str) -> None:
    """Splitting on a single space reads tab-separated text as one word and a double space as an
    empty one — and a table cell padded for alignment is exactly that."""
    at = _run(_repo_with(tmp_path, _text(1, 2700, separator)))
    assert at.returncode == 0, at.stderr
    over = _run(_repo_with(tmp_path, _text(1, 2701, separator)))
    assert over.returncode == 1
    assert "2,701 words, over the ceiling of 2,700" in over.stderr, over.stderr


def test_the_failure_says_to_move_a_rule_not_to_delete_it(tmp_path: Path) -> None:
    """Three passes grew back because trimming without a destination is how the file got to 473
    lines: the remedy has to name the destination, and say what not to do."""
    result = _run(_repo_with(tmp_path, _text(151, 151)))
    assert result.returncode == 1
    assert "Move a rule to the document that owns it" in result.stderr, result.stderr
    assert "docs/README.md" in result.stderr, "the routing table is where the owner is found"
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


def _stated_ceilings(text: str) -> tuple[int, int] | None:
    """The `(lines, words)` ceiling a document states as *under N lines and M words*, wrapped or
    not, or `None` when it states none."""
    match = re.search(r"under\s+([\d,]+)\s+lines\s+and\s+([\d,]+)\s+words", text)
    if match is None:
        return None
    return int(match[1].replace(",", "")), int(match[2].replace(",", ""))


def test_the_stated_ceiling_is_read_wrapped_and_absent_when_unstated() -> None:
    """The reader below has to be able to return *nothing found*, or the test that uses it could
    only ever pass."""
    assert _stated_ceilings("stays under\n150 lines and 2,700 words (`wc`)") == (150, 2700)
    assert _stated_ceilings("stays under 90 lines and 1,000 words") == (90, 1000)
    assert _stated_ceilings("keeps itself short") is None


def test_the_ceilings_are_the_ones_claude_md_states() -> None:
    """The gate and the file's own intro line are two statements of one number. Raising the ceiling
    in one place only is how the guard would start refusing a file that says it is fine, or passing
    one that says it is not — so this holds them together, and the boundary tests above hold the
    gate to the same literals."""
    text = (REPO / "CLAUDE.md").read_text(encoding="utf-8")
    stated = _stated_ceilings(text)
    assert stated is not None, (
        "CLAUDE.md no longer states its ceiling as 'under N lines and M words'. Restore that "
        "sentence, or change this reader and the gate together — a ceiling stated nowhere is a "
        "ceiling nobody can check the guard against."
    )
    assert stated == (150, 2700), (
        f"CLAUDE.md states a ceiling of {stated}, but tools/claude_md_size_gate.py and its tests "
        "enforce (150, 2700). A ceiling change is the planner's decision: change the prose, the "
        "gate's MAX_LINES / MAX_WORDS and the literals in this file in one commit."
    )
