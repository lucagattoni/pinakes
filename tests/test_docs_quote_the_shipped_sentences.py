"""Documentation that quotes command output must quote the output this build produces.

**A gate for a defect that has now happened twice, which is this project's threshold.** E1 rewrote
`pnk search`'s escalation notice and left `docs/GUIDE.md` showing the sentence it had just replaced;
its retrospective recorded that nothing in the repo could have caught it. E4 rewrote the same
sentence and left the *same* GUIDE block stale again, caught only because someone grepped.

Everything else in this repo that verifies documentation checks that a **link resolves** or that a
**name exists**. Neither can see this: the prose is well-formed, every link works, `mkdocs --strict`
is green, and the block is simply a transcript of an older build.

**The gate is a retirement list, not a matcher.** Trying to diff a fenced block against real output
would need the command to run, with models and a corpus; and a rule like "every printed constant
must appear in the docs" is false — most of them should not. What is checkable, cheaply and without
false positives, is the opposite: **a sentence this build can no longer print must appear nowhere.**
Retiring a sentence is a deliberate act, so adding a row here is part of it, and the row is what
makes the next rewrite loud.
"""

from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
SEARCHED = (ROOT / "docs", ROOT / "README.md", ROOT / "src")

#: (the retired text, what replaced it and when). One row per sentence a shipped build once printed
#: and no longer can.
#:
#: **Not a style list.** A row belongs here only when the text was *output* — something a user could
#: have pasted out of a terminal — because that is the class of staleness a reader cannot tell from
#: a correct transcript. Prose describing a feature is caught by ordinary review; a quoted line that
#: was true in 0.22 is not.
RETIRED: tuple[tuple[str, str], ...] = (
    (
        "paid synthesis is planned for the deep release",
        "E4 shipped `pnk ask --deep`, so `run_search`'s notice names it. Left stale in GUIDE.md by "
        "E1 and again by E4 — the two occurrences this file exists for.",
    ),
    (
        "paid synthesis is what would turn this evidence into an answer",
        "E1's `DEEP_RELEASE_NOTICE`, replaced by `DEEP_OFFER` at E4: the flag exists now, and the "
        "notice carries the price with it.",
    ),
    (
        "this build cannot do it",
        "The tail of the same E1 notice. Kept as its own row because the first half could be "
        "reworded without this half moving.",
    ),
    (
        "a run would end at its caps rather than at sufficiency",
        "The conditional was E1's, when no run could happen. E4 made it present tense: a run "
        "*does* end at its caps.",
    ),
)


@pytest.mark.parametrize(("retired", "why"), RETIRED, ids=[row[0][:40] for row in RETIRED])
def test_no_document_still_quotes_a_sentence_this_build_cannot_print(
    retired: str, why: str
) -> None:
    """The text must appear nowhere — not in `docs/`, not in `README.md`, not in `src/`.

    `src/` is included deliberately. A retired sentence surviving in a docstring or a comment is the
    same defect one layer in: the next person to touch that module reads it as current, and this
    project's docstrings are where its reasoning lives.
    """
    hits: list[str] = []
    for target in SEARCHED:
        paths = sorted(target.rglob("*")) if target.is_dir() else [target]
        for path in paths:
            if not path.is_file() or path.suffix not in {".md", ".py"}:
                continue
            if path.name == Path(__file__).name:
                continue
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                if retired in line:
                    hits.append(f"{path.relative_to(ROOT)}:{number}")
    assert not hits, (
        f"a retired sentence is still quoted in {', '.join(hits)}.\n"
        f"It was retired because: {why}\n"
        "Update the text to what this build prints — or, if the sentence is genuinely back, "
        "delete its row from RETIRED rather than working around this."
    )


def test_the_retirement_list_is_about_output_rather_than_prose() -> None:
    """Every row must name where it went, or the list decays into a banned-words list.

    The `why` is what a reader hitting a failure needs: the sentence is gone, and the useful
    question is what replaced it. A row with an empty reason would fail a build and explain
    nothing.
    """
    for retired, why in RETIRED:
        assert len(retired) > 20, f"{retired!r} is too short to be a quoted line"
        assert len(why) > 40, f"{retired!r} has no usable reason"
