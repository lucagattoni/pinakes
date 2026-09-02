"""The fragment assembler, driven as a subprocess against a temp tree.

A subprocess rather than an import, for the reason `tests/test_paid_path.py` gives about
`tools/paid_path_gate.py`: it exercises **the same artifact** the release procedure and `check.sh`
run, argument parsing included, and it needs no `sys.path` surgery the type checkers then cannot
resolve. `--repo` exists so this can point the real tool at a temp directory.

The failure that matters is not a crash — it is `--apply` silently corrupting `CHANGELOG.md`, found
at release time with the fragments it consumed already deleted. Most assertions here are therefore
about what splicing must leave *untouched*.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

TOOL = Path(__file__).parent.parent / "tools" / "fragments.py"

CHANGELOG_BEFORE = (
    "# Changelog\n\n"
    "## [Unreleased]\n\n"
    "- a pre-existing entry nobody migrated\n\n"
    "## [0.1.0] - 20260101 09:00\n\n"
    "- older\n"
)

RETRO_BEFORE = (
    "# Retrospectives\n\n"
    "## I1 - first (20260725 13:40)\n\n"
    "body\n\n"
    "## Design review passes 1-7 (pre-implementation)\n\n"
    "footer\n"
)


def run(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), "--repo", str(repo), *args],
        capture_output=True,
        text=True,
    )


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / "changelog.d").mkdir()
    (tmp_path / "retro.d").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "CHANGELOG.md").write_text(CHANGELOG_BEFORE, encoding="utf-8")
    (tmp_path / "docs" / "RETROSPECTIVES.md").write_text(RETRO_BEFORE, encoding="utf-8")
    return tmp_path


def write(repo: Path, rel: str, body: str) -> None:
    (repo / rel).write_text(body, encoding="utf-8")


def changelog(repo: Path) -> str:
    return (repo / "CHANGELOG.md").read_text(encoding="utf-8")


def test_a_category_comes_from_the_filename_and_groups_the_body(repo: Path) -> None:
    write(repo, "changelog.d/added-one.md", "- **A new thing.**")
    write(repo, "changelog.d/fixed-two.md", "- **A fixed thing.**")
    write(repo, "changelog.d/added-three.md", "- **Another new thing.**")

    out = run(repo, "--stream", "changelog", "--render").stdout

    assert "### Added" in out and "### Fixed" in out
    assert out.index("### Added") < out.index("### Fixed"), (
        "categories follow the stream's declared order, not the filesystem's"
    )
    added = out[out.index("### Added") : out.index("### Fixed")]
    assert "A new thing." in added and "Another new thing." in added


def test_an_unknown_category_is_refused_by_name(repo: Path) -> None:
    write(repo, "changelog.d/improved-something.md", "- **No such category.**")

    result = run(repo, "--check")

    assert result.returncode == 1
    assert "improved-something.md" in result.stderr
    assert "added" in result.stderr, "the message must name the vocabulary it expected"


def test_an_empty_fragment_is_refused(repo: Path) -> None:
    """An empty fragment renders an empty bullet and reads as a tooling bug at release time, when
    the fragment that would have explained it has already been deleted."""
    write(repo, "changelog.d/added-nothing.md", "   \n\n")

    result = run(repo, "--check")

    assert result.returncode == 1
    assert "is empty" in result.stderr


def test_check_reports_every_problem_not_just_the_first(repo: Path) -> None:
    write(repo, "changelog.d/improved-a.md", "- x")
    write(repo, "changelog.d/added-b.md", "")

    assert "2 malformed" in run(repo, "--check").stderr


def test_apply_leaves_existing_unreleased_prose_exactly_where_it_was(repo: Path) -> None:
    """Adoption must not require migrating what is already in `[Unreleased]` — a migration commit
    would itself collide with whatever the other agents are holding."""
    write(repo, "changelog.d/added-one.md", "- **A new thing.**")

    assert run(repo, "--stream", "changelog", "--apply").returncode == 0

    after = changelog(repo)
    assert "- a pre-existing entry nobody migrated" in after
    assert "## [0.1.0] - 20260101 09:00" in after
    assert "- older" in after
    assert after.index("### Added") < after.index("- a pre-existing entry"), (
        "fragments splice directly under the anchor, above what was already there"
    )
    assert CHANGELOG_BEFORE.count("## [") == after.count("## ["), (
        "no release heading gained or lost"
    )


def test_apply_deletes_the_fragments_it_consumed(repo: Path) -> None:
    """Consumed, not copied: leaving them behind would re-splice the same entry into the next
    release as well."""
    write(repo, "changelog.d/added-one.md", "- **A new thing.**")

    run(repo, "--stream", "changelog", "--apply")

    assert list((repo / "changelog.d").glob("*.md")) == []
    assert "A new thing." in changelog(repo)


def test_a_missing_anchor_is_an_error_rather_than_a_silent_append(repo: Path) -> None:
    """Appending to the end of a changelog whose anchor was renamed would bury the entry under
    every historical release, where nobody would look for it."""
    write(repo, "CHANGELOG.md", "# Changelog\n\n## [0.1.0]\n")
    write(repo, "changelog.d/added-one.md", "- **A new thing.**")

    result = run(repo, "--stream", "changelog", "--apply")

    assert result.returncode != 0
    assert "anchor" in (result.stderr + result.stdout)


def test_nothing_to_apply_is_not_an_error(repo: Path) -> None:
    result = run(repo, "--apply")

    assert result.returncode == 0
    assert changelog(repo) == CHANGELOG_BEFORE, "an empty run must not touch the document at all"


def test_the_readme_is_not_treated_as_a_fragment(repo: Path) -> None:
    """Each fragment directory documents itself in place, where somebody about to add a fragment
    will actually see it."""
    write(repo, "changelog.d/README.md", "# Changelog fragments\n\nnot an entry")

    assert run(repo, "--check").returncode == 0
    assert changelog(repo) == CHANGELOG_BEFORE


def test_the_retrospectives_stream_splices_above_its_footer(repo: Path) -> None:
    """`docs/RETROSPECTIVES.md` ends with the pre-implementation design-review passes, which must
    stay last — so this stream inserts *before* an anchor rather than after one."""
    write(repo, "retro.d/i7d-recorded.md", "## I7d - Recording (20260729 03:36)\n\n**HIGH - x.**\n")

    assert run(repo, "--stream", "retrospectives", "--apply").returncode == 0

    after = (repo / "docs" / "RETROSPECTIVES.md").read_text(encoding="utf-8")
    assert after.index("## I7d") > after.index("## I1")
    assert after.index("## I7d") < after.index("## Design review passes"), (
        "the design-review footer must stay at the foot"
    )


def test_a_free_form_stream_needs_no_category_prefix(repo: Path) -> None:
    write(repo, "retro.d/i7d-recorded.md", "## I7d - Recording\n\nbody\n")

    assert run(repo, "--check").returncode == 0
    assert "## I7d" in run(repo, "--stream", "retrospectives", "--render").stdout


def test_both_streams_apply_in_one_run(repo: Path) -> None:
    """The release procedure runs this once, with no `--stream`. If the default silently did one
    document, a release would ship with its retrospectives still sitting in `retro.d/`."""
    write(repo, "changelog.d/added-one.md", "- **A new thing.**")
    write(repo, "retro.d/i7d-recorded.md", "## I7d - Recording\n\nbody\n")

    assert run(repo, "--apply").returncode == 0

    assert "A new thing." in changelog(repo)
    assert "## I7d" in (repo / "docs" / "RETROSPECTIVES.md").read_text(encoding="utf-8")
    assert list((repo / "changelog.d").glob("*.md")) == []
    assert list((repo / "retro.d").glob("*.md")) == []


def test_fragments_merge_into_a_category_heading_that_already_exists(repo: Path) -> None:
    """Found by cutting a release with this tool: dumping rendered blocks under the anchor gave
    `[Unreleased]` **two** `### Added` headings, because the section already had one from prose
    nobody had migrated. A reader scanning for "what was added" stops at the first."""
    write(
        repo,
        "CHANGELOG.md",
        "# Changelog\n\n## [Unreleased]\n\n### Added\n\n- an existing added entry\n\n"
        "### Fixed\n\n- an existing fix\n\n## [0.1.0] - 20260101 09:00\n\n### Added\n\n- older\n",
    )
    write(repo, "changelog.d/added-one.md", "- **A new thing.**")

    assert run(repo, "--stream", "changelog", "--apply").returncode == 0

    after = changelog(repo)
    unreleased = after[after.index("## [Unreleased]") : after.index("## [0.1.0]")]
    assert unreleased.count("### Added") == 1, "one heading per category"
    assert "- an existing added entry" in unreleased and "A new thing." in unreleased
    assert unreleased.index("### Added") < unreleased.index("### Fixed"), (
        "the existing heading order is preserved, not rebuilt"
    )


def test_a_category_heading_in_an_older_release_is_never_written_into(repo: Path) -> None:
    """The merge region stops at the next `##`. Writing into a shipped release's `### Added` would
    silently amend history that is already published."""
    write(
        repo,
        "CHANGELOG.md",
        "# Changelog\n\n## [Unreleased]\n\n## [0.1.0] - 20260101 09:00\n\n### Added\n\n- older\n",
    )
    write(repo, "changelog.d/added-one.md", "- **A new thing.**")

    run(repo, "--stream", "changelog", "--apply")

    after = changelog(repo)
    released = after[after.index("## [0.1.0]") :]
    assert "A new thing." not in released, "a shipped release must not be amended"
    assert "A new thing." in after[: after.index("## [0.1.0]")]


def test_a_new_category_is_added_in_the_streams_declared_order(repo: Path) -> None:
    write(
        repo,
        "CHANGELOG.md",
        "# Changelog\n\n## [Unreleased]\n\n### Fixed\n\n- an existing fix\n\n## [0.1.0]\n",
    )
    write(repo, "changelog.d/added-one.md", "- **A new thing.**")
    write(repo, "changelog.d/removed-two.md", "- **A removed thing.**")

    run(repo, "--stream", "changelog", "--apply")

    after = changelog(repo)
    unreleased = after[: after.index("## [0.1.0]")]
    assert unreleased.index("### Added") < unreleased.index("### Removed"), (
        "new sections follow the stream's declared order"
    )
    assert "- an existing fix" in unreleased


def test_the_timestamp_prefix_is_stripped_before_the_category_is_read(repo: Path) -> None:
    """`YYYYMMDD_HHMM-added-x.md` is an `added` fragment, not a `20260804_0700` one.

    The prefix arrived 20260804 for chronological ordering. `category_of` split the stem on the
    first hyphen, so without stripping it first every prefixed fragment fails validation with its
    own date quoted back as the offending category, and `--apply` files it under nothing.
    """
    write(repo, "changelog.d/20260804_0700-added-a-thing.md", "- **A thing.** Body.\n")
    assert run(repo, "--check").returncode == 0
    assert run(repo, "--stream", "changelog", "--apply").returncode == 0
    changelog = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "### Added" in changelog
    assert "20260804_0700" not in changelog
    assert "- **A thing.** Body." in changelog


def test_a_fragment_without_a_timestamp_prefix_still_validates(repo: Path) -> None:
    """The convention began 20260804 07:00; refusing files that predate it buys nothing."""
    write(repo, "changelog.d/added-a-thing.md", "- **A thing.** Body.\n")
    assert run(repo, "--check").returncode == 0


def test_a_prefixed_fragment_with_no_valid_category_is_refused(repo: Path) -> None:
    """Stripping the prefix must not become a way to smuggle an unknown category past the check."""
    write(repo, "changelog.d/20260804_0700-invented-a-thing.md", "- body\n")
    result = run(repo, "--check")
    assert result.returncode != 0
    assert "invented" in result.stdout + result.stderr


def test_the_error_names_what_the_author_wrote_not_the_date_it_stripped(repo: Path) -> None:
    """A message quoting the timestamp back sends the author to fix the wrong half of the name."""
    write(repo, "changelog.d/20260804_0700-nonsense-thing.md", "- body\n")
    result = run(repo, "--check")
    output = result.stdout + result.stderr
    assert "nonsense" in output
    assert "'20260804_0700'" not in output


def test_a_fragment_that_opens_with_front_matter_is_refused(repo: Path) -> None:
    """The defect this check was written for, in the exact shape it shipped in.

    Three 0.24.0 fragments carried `---` / `category: added` / `---`. The category was read from
    the filename, so the fence was inert and nothing here objected; `--apply` then copied it into
    `CHANGELOG.md`, where all three are still published. The fence is the only observable — the
    body below it is well-formed — so that is what this refuses.
    """
    write(repo, "changelog.d/added-one.md", "---\ncategory: added\n---\n\n- **A new thing.**\n")

    result = run(repo, "--check")

    assert result.returncode == 1
    assert "added-one.md" in result.stderr
    assert "front-matter" in result.stderr
    assert "CHANGELOG.md" in result.stderr, (
        "the message must name the document the fence would be spliced into — that consequence "
        "is the whole reason this is refused rather than ignored"
    )


def test_a_leading_blank_line_does_not_hide_the_fence(repo: Path) -> None:
    """`render` strips leading newlines before splicing, so a fence behind one reaches the
    document exactly as a fence on line 1 does. A check reading only the literal first line would
    pass it."""
    write(repo, "changelog.d/added-one.md", "\n\n---\ncategory: added\n---\n\n- **A thing.**\n")

    result = run(repo, "--check")

    assert result.returncode == 1
    assert "added-one.md" in result.stderr


def test_a_horizontal_rule_inside_a_body_is_left_alone(repo: Path) -> None:
    """The discriminating case. Refusing every `---` would be wrong: a body is spliced verbatim,
    so a rule between two paragraphs is legitimate markdown. Only the opening fence declares
    metadata. Without this test the check could be `"---" in body` and look correct."""
    write(
        repo,
        "changelog.d/added-one.md",
        "- **A new thing.**\n\n---\n\n  and a second paragraph after a rule.\n",
    )

    result = run(repo, "--check")

    assert result.returncode == 0, result.stderr


def test_front_matter_is_refused_before_apply_can_splice_it(repo: Path) -> None:
    """`--apply` deletes the fragments it consumed, so a fragment found malformed *afterwards* is
    found with the evidence already gone. The target must be byte-identical after the refusal.

    **The refusal is named, not just counted.** 0.30.0's document gate gave `--apply` a second
    reason to refuse this same fragment — a spliced `---` is not a `- ` list item either — so
    every assertion below passed whether or not the front-matter check still ran, and the battery
    row claiming it did went from KILLED to SURVIVED. A test that cannot say *which* guard fired
    stops pinning either of them once a second one exists."""
    before = changelog(repo)
    write(repo, "changelog.d/added-one.md", "---\ncategory: added\n---\n\n- **A new thing.**\n")

    result = run(repo, "--stream", "changelog", "--apply")

    assert result.returncode == 1
    assert "front-matter fence" in result.stderr, (
        "refused as front matter, not as a stray non-bullet"
    )
    assert changelog(repo) == before, "a refused run must not have written to the document"
    assert (repo / "changelog.d" / "added-one.md").exists(), (
        "nor deleted the fragment that explains the failure"
    )


# ────────────────────────────────────────────────────────────────────────────────────────────────
# The assembled document, rather than the fragments going into it (0.30.0's open-corrections item).
#
# `--check` read every pending fragment and asserted nothing about the result of `--apply`, so a
# splice could leave `CHANGELOG.md` malformed with every gate in this repository green — and had.
# The fixtures below are the real shapes, reduced: `## [0.28.3]` carried `### Fixed` twice
# consecutively with a bare paragraph for a body, and one `### Changed` further down did the same.
# ────────────────────────────────────────────────────────────────────────────────────────────────


def test_a_heading_that_repeats_consecutively_is_refused(repo: Path) -> None:
    """`## [0.28.3]`'s real shape. `_merge_into_section` reuses the first heading it finds, so
    nothing can ever merge into the second and a reader scanning for the category stops at the
    first — while every gate in this repository stayed green on it."""
    write(
        repo,
        "CHANGELOG.md",
        "# Changelog\n\n## [Unreleased]\n\n## [0.1.0] - 20260101 09:00\n\n"
        "### Fixed\n\n### Fixed\n\n- **A fix.**\n",
    )

    result = run(repo, "--stream", "changelog", "--check")

    assert result.returncode == 1
    assert "repeats the heading on line" in result.stderr
    assert "CHANGELOG.md:9" in result.stderr, "the second heading is named, with its line"


def test_the_same_heading_under_a_different_release_is_left_alone(repo: Path) -> None:
    """The discriminating case, and the one that decides whether this can land at all: every
    changelog repeats `### Fixed` once per release. The rule is *adjacency*, never recurrence."""
    write(
        repo,
        "CHANGELOG.md",
        "# Changelog\n\n## [Unreleased]\n\n## [0.2.0] - 20260102 09:00\n\n"
        "### Fixed\n\n- **A later fix.**\n\n## [0.1.0] - 20260101 09:00\n\n"
        "### Fixed\n\n- **An earlier fix.**\n",
    )

    assert run(repo, "--stream", "changelog", "--check").returncode == 0


def test_a_heading_that_repeats_after_intervening_entries_is_the_decided_scope(repo: Path) -> None:
    """**A hole, pinned deliberately rather than left to be discovered.** The rule decided in
    `plans/20260731_1202-open-corrections.md` is *adjacency* — "a stream heading never repeats
    consecutively" — because that is the shape the evidence had. A repeat separated by real
    entries is a defect this does **not** catch, and asserting so here is what keeps that a
    decision: strengthening it to section-scoped changes what the plan specified, so it reopens
    the item rather than quietly widening the gate."""
    write(
        repo,
        "CHANGELOG.md",
        "# Changelog\n\n## [Unreleased]\n\n## [0.1.0] - 20260101 09:00\n\n"
        "### Fixed\n\n- **A fix.**\n\n### Fixed\n\n- **Another, under a second heading.**\n",
    )

    assert run(repo, "--stream", "changelog", "--check").returncode == 0


def test_an_entry_that_opens_with_a_paragraph_is_refused(repo: Path) -> None:
    """`render` splices a fragment body verbatim, so a paragraph in the document is a paragraph
    the fragment wrote. `changelog.d/README.md` requires `- **claim.**`."""
    write(
        repo,
        "CHANGELOG.md",
        "# Changelog\n\n## [Unreleased]\n\n## [0.1.0] - 20260101 09:00\n\n"
        "### Changed\n\n`pnk doctor` reports link coverage as a ratio.\n",
    )

    result = run(repo, "--stream", "changelog", "--check")

    assert result.returncode == 1
    assert "opens with a paragraph rather than a `- ` list item" in result.stderr


def test_a_bullets_indented_continuation_is_not_read_as_a_second_entry(repo: Path) -> None:
    """Only the *first* non-blank line under a heading is judged. A wrapped bullet indents its
    continuation to the content column, and reading that as an entry would refuse every long
    entry in the document."""
    write(
        repo,
        "CHANGELOG.md",
        "# Changelog\n\n## [Unreleased]\n\n## [0.1.0] - 20260101 09:00\n\n"
        "### Fixed\n\n- **A fix.** Its first line.\n  a continuation, indented, not a bullet.\n\n"
        "- **Another fix.**\n",
    )

    assert run(repo, "--stream", "changelog", "--check").returncode == 0


def test_the_bullet_rule_never_reaches_the_free_form_stream(repo: Path) -> None:
    """`retro.d/` fragments are free-form prose carrying their own `##` heading. A bullet
    requirement there would refuse the format that stream exists for — so the rule is scoped to
    the stream with a category vocabulary, and this is the assertion that says so.

    **The `###` heading in the fixture is load-bearing.** The bullet rule only ever reads a `###`,
    so a fixture built from `##` alone exercises nothing and the scoping guard could be deleted
    with this test still green — which is what the mutation pass reported. The real document
    carried 42 `###` headings at `0aea036` (`grep -c '^### ' docs/RETROSPECTIVES.md`), 41 of
    them opening with prose. The forty-second is `### Smaller things` at line 2679, which opens
    with a `- ` bullet — the exact shape the changelog arm refuses, sitting in the stream this
    test says the arm never reaches, so the scoping is load-bearing and not decorative.
    **The count is stamped with the commit it was measured
    at, because it grows at every release** — an unstamped one was written here as
    *thirty-four*, copied from here into a second docstring, and was 42 by the time anybody
    counted."""
    write(
        repo,
        "docs/RETROSPECTIVES.md",
        "# Retrospectives\n\n## I1 - first (20260725 13:40)\n\n"
        "A paragraph, which is what this document is made of.\n\n"
        "### The review pass over I1's own diff\n\n"
        "Three defects, all in the new check — prose under a `###`, which the real document does "
        "dozens of times.\n\n"
        "## Design review passes 1-7 (pre-implementation)\n\nfooter\n",
    )

    assert run(repo, "--stream", "retrospectives", "--check").returncode == 0


def test_a_heading_inside_a_fenced_block_is_not_read_as_structure(repo: Path) -> None:
    """An entry demonstrating Markdown is an ordinary thing to write. A line-based scanner reading
    a fenced example as document structure would refuse a correct document, and
    `tools/markdown_link_gate.py` records a false positive of exactly that shape being *acted on*
    before it was disbelieved."""
    write(
        repo,
        "CHANGELOG.md",
        "# Changelog\n\n## [Unreleased]\n\n## [0.1.0] - 20260101 09:00\n\n"
        "### Fixed\n\n- **A fix.** It renders this:\n\n"
        "  ```markdown\n### Fixed\n### Fixed\nnot a bullet\n  ```\n",
    )

    assert run(repo, "--stream", "changelog", "--check").returncode == 0


def test_apply_refuses_to_write_a_document_it_would_leave_malformed(repo: Path) -> None:
    """The refusal is placed before the write, and therefore before the deletes. Found *after*
    `--apply`, a malformed document is found with the fragments that caused it already gone —
    which is the same reason `check.sh` runs `--check` at commit time rather than at release
    time, one step further in."""
    write(
        repo,
        "CHANGELOG.md",
        "# Changelog\n\n## [Unreleased]\n\n### Fixed\n\n### Fixed\n\n- **existing.**\n\n"
        "## [0.1.0] - 20260101 09:00\n\n- older\n",
    )
    write(repo, "changelog.d/added-one.md", "- **A new thing.**")
    before = changelog(repo)

    result = run(repo, "--stream", "changelog", "--apply")

    assert result.returncode == 1
    assert "refusing to write" in result.stderr
    assert changelog(repo) == before, "nothing written"
    assert (repo / "changelog.d" / "added-one.md").is_file(), "no fragment deleted"


def test_the_real_documents_are_clean_which_is_this_checkers_only_control() -> None:
    """A control leg, for the reason `tools/markdown_link_gate.py` gives: the fixtures above prove
    the checker *fires*, and nothing else proves it does not fire on a correct document. Run
    against the two real documents, over their full history, the answer must be zero — so a
    failure here means **the checker is wrong, or the document is**, and the message says which
    line to read to tell them apart."""
    repo = Path(__file__).parent.parent
    result = run(repo, "--check")

    assert result.returncode == 0, result.stderr


def test_an_unclosed_fence_is_refused_rather_than_silently_swallowing_the_rest(repo: Path) -> None:
    """A skipped region is not a checked region. An unclosed fence hides every line below it, so
    without this the gate prints *well-formed* having read half the document — the shape
    `tools/markdown_link_gate.py` names as "a clean bill it never earned". The malformed content
    below the fence is real and would be caught if the fence were closed."""
    write(
        repo,
        "CHANGELOG.md",
        "# Changelog\n\n## [Unreleased]\n\n## [0.1.0] - 20260101 09:00\n\n"
        "### Fixed\n\n- **A fix.**\n\n```text\nnever closed\n\n### Fixed\n\n### Fixed\n\nprose\n",
    )

    result = run(repo, "--stream", "changelog", "--check")

    assert result.returncode == 1
    assert "opened here and never closed" in result.stderr
    assert "CHANGELOG.md:11" in result.stderr, "the fence's own line, not the damage below it"


def test_the_duplicate_message_names_the_mechanism_that_belongs_to_the_stream(repo: Path) -> None:
    """`_merge_into_section` runs only for a stream with a category vocabulary, so quoting it at
    `docs/RETROSPECTIVES.md` would explain a mechanism that never touches that file. An error
    message describing the wrong cause sends the reader to the wrong code."""
    write(
        repo,
        "docs/RETROSPECTIVES.md",
        "# Retrospectives\n\n## I1 - first (20260725 13:40)\n\n"
        "## I1 - first (20260725 13:40)\n\nbody\n\n"
        "## Design review passes 1-7 (pre-implementation)\n\nfooter\n",
    )
    write(
        repo,
        "CHANGELOG.md",
        "# Changelog\n\n## [Unreleased]\n\n## [0.1.0] - 20260101 09:00\n\n"
        "### Fixed\n\n### Fixed\n\n- **A fix.**\n",
    )

    retro = run(repo, "--stream", "retrospectives", "--check").stderr
    changelog_err = run(repo, "--stream", "changelog", "--check").stderr

    assert "repeats the heading" in retro and "repeats the heading" in changelog_err
    assert "_merge_into_section" in changelog_err, "the stream that actually has that merge step"
    assert "_merge_into_section" not in retro, "…and the stream that does not, must not claim it"


def test_apply_is_one_step_or_none_across_every_stream(repo: Path) -> None:
    """`--apply` walks two streams. Refusing mid-walk wrote `CHANGELOG.md` and deleted its
    fragments, then exited 1 printing *"Nothing written, no fragment deleted"* — a false statement
    about a half-applied release, in the direction that destroys the evidence. Every stream is
    spliced and validated before any stream is written."""
    write(
        repo,
        "docs/RETROSPECTIVES.md",
        "# Retrospectives\n\n## I1 - first (20260725 13:40)\n\n"
        "## I1 - first (20260725 13:40)\n\nbody\n\n"
        "## Design review passes 1-7 (pre-implementation)\n\nfooter\n",
    )
    write(repo, "changelog.d/added-one.md", "- **A changelog thing.**")
    write(repo, "retro.d/a-lesson.md", "## A lesson\n\nRetro prose.")
    before = changelog(repo)

    result = run(repo, "--apply")

    assert result.returncode == 1
    assert "no fragment deleted" in result.stderr
    assert changelog(repo) == before, "the healthy stream must not be written either"
    assert (repo / "changelog.d" / "added-one.md").is_file(), "…nor its fragments deleted"


def test_a_heading_inside_a_fenced_block_is_not_a_splice_target(repo: Path) -> None:
    """The splicer and the checker have to agree about what a heading is. `document_problems`
    skips fenced blocks and `_merge_into_section` did not, so a column-zero fence containing
    `### Added` was a heading to one and not the other: the entry spliced *inside* the code block,
    `--apply` exited 0, the fragment was deleted, and `--check` passed on the result — the entry
    rendering as sample code nobody would ever find."""
    write(
        repo,
        "CHANGELOG.md",
        "# Changelog\n\n## [Unreleased]\n\n- **Pre-existing.** Rendered:\n\n"
        "```markdown\n### Added\n\n- an example, inside a fence\n```\n\n"
        "## [0.1.0] - 20260101 09:00\n\n- older\n",
    )
    write(repo, "changelog.d/added-one.md", "- **A new thing.**")

    assert run(repo, "--stream", "changelog", "--apply").returncode == 0

    after = changelog(repo)
    unreleased = after[after.index("## [Unreleased]") : after.index("## [0.1.0]")]
    entry = unreleased.index("A new thing")
    fences = [i for i, line in enumerate(unreleased[:entry].split("\n")) if line.startswith("```")]
    assert len(fences) % 2 == 0, "the entry landed inside the fenced example"
    assert unreleased.index("### Added") < entry, "…under a real heading of its own"


def test_an_anchor_inside_a_fenced_block_is_not_the_splice_point(repo: Path) -> None:
    """Same disagreement, one function up: `splice` finds the anchor by scanning for the literal
    line, so a changelog entry quoting `## [Unreleased]` inside a fence would become the insertion
    point and bury every future release inside a code block."""
    write(
        repo,
        "CHANGELOG.md",
        "# Changelog\n\n- **A note.** The anchor looks like this:\n\n"
        "```markdown\n## [Unreleased]\n```\n\n"
        "## [Unreleased]\n\n## [0.1.0] - 20260101 09:00\n\n- older\n",
    )
    write(repo, "changelog.d/added-one.md", "- **A new thing.**")

    assert run(repo, "--stream", "changelog", "--apply").returncode == 0

    after = changelog(repo)
    assert after.index("A new thing") > after.index("```\n\n## [Unreleased]"), (
        "spliced at the quoted anchor rather than the real one"
    )


def test_check_reads_the_document_apply_would_write_not_only_the_one_on_disk(repo: Path) -> None:
    """The item's own sentence: *"It asserts nothing about the result of `--apply`."* Reading only
    the file on disk answers whether the **last** splice went well, while the fragment that will
    break the next one sits in the tree unread.

    This fixture is the recurring cause, reduced. Both instances the item cites came from a
    fragment whose body opens with its own `### Fixed`, which `render` then wraps in a second one —
    `changelog.d/fixed-two-frozen-yaml-behaviours.md` at 0.6.0, hand-repaired seven minutes after
    the release, and `…0233-fixed-published-versions-row…` at 0.28.3, twenty-two days later.
    Replayed against the tree as it stood at each of those commits, this check exits 1."""
    write(repo, "changelog.d/fixed-one.md", "### Fixed\n\n- **A fix.**\n")

    result = run(repo, "--stream", "changelog", "--check")

    assert result.returncode == 1
    assert "repeats the heading" in result.stderr
    assert "would write, not the one on disk" in result.stderr, "and says which document it read"
    assert changelog(repo) == CHANGELOG_BEFORE, "a check writes nothing"


def test_a_fault_already_in_the_document_is_reported_once_not_twice(repo: Path) -> None:
    """The assembly contains the whole file, so every existing fault appears in both documents at
    different line numbers. Reporting each twice would bury the one that is new."""
    write(
        repo,
        "CHANGELOG.md",
        "# Changelog\n\n## [Unreleased]\n\n## [0.1.0] - 20260101 09:00\n\n"
        "### Fixed\n\n### Fixed\n\n- **A fix.**\n",
    )
    write(repo, "changelog.d/added-one.md", "- **A new thing.**")

    result = run(repo, "--stream", "changelog", "--check")

    assert result.returncode == 1
    assert result.stderr.count("repeats the heading") == 1, "the pre-existing fault, once"
    assert "would write, not the one on disk" not in result.stderr


def test_check_validates_the_exact_bytes_apply_writes(repo: Path) -> None:
    """**The coupling `--check` acquired when it stopped being read-only.** It no longer inspects
    the document; it simulates the write. So `--check` and `--apply` must agree about assembly
    forever, and a disagreement would be silent — `--check` green on an assembly `--apply` would
    never produce, which is the failure mode this whole increment exists to remove.

    `main` calls `prospective` rather than re-deriving the splice, so they are the same code and
    not two paths that happen to match. This holds them to it from the outside anyway: the module
    is imported by path — the pattern `tests/test_markdown_link_gate.py` uses to keep the gate and
    `mkdocs_hooks.py` from drifting — and the bytes are compared against what the real subprocess
    writes. A refactor giving either path its own assembly turns this red.
    """
    spec = importlib.util.spec_from_file_location("_fragments", TOOL)
    assert spec is not None and spec.loader is not None
    module: Any = importlib.util.module_from_spec(spec)
    # Registered *before* `exec_module`: `@dataclass` resolves its annotations through
    # `sys.modules[cls.__module__]`, which is `None` while the module is still executing.
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)

        write(repo, "changelog.d/added-one.md", "- **A new thing.**")
        write(repo, "changelog.d/fixed-two.md", "- **A fixed thing.**")
        write(repo, "retro.d/a-lesson.md", "## A lesson\n\nProse.")

        predicted = {
            name: module.prospective(stream, repo) for name, stream in module.STREAMS.items()
        }
        targets = {name: str(stream.target) for name, stream in module.STREAMS.items()}
    finally:
        del sys.modules[spec.name]

    assert run(repo, "--apply").returncode == 0

    for name, target in targets.items():
        assert predicted[name] is not None, f"{name}: nothing predicted for a stream with fragments"
        assert predicted[name] == (repo / target).read_text(encoding="utf-8"), (
            f"{name}: --check validated bytes --apply did not write"
        )


def test_a_retro_fragment_with_no_heading_of_its_own_is_refused(repo: Path) -> None:
    """The fragment does not become malformed — it becomes **somebody else's retrospective**.

    `render` joins bodies with a blank line, so prose with no `##` of its own lands under whichever
    fragment sorts before it. The spliced document is well-formed markdown asserting something
    false about which increment the lesson came from, and the reader who could have noticed is the
    one who no longer can: by release time the fragment that would have explained it is deleted."""
    write(repo, "retro.d/20260901_0710-a-lesson.md", "Prose that starts straight in.\n")

    result = run(repo, "--stream", "retrospectives", "--check")

    assert result.returncode == 1
    assert "20260901_0710-a-lesson.md" in result.stderr
    assert "must open with its own `## ` heading" in result.stderr


def test_a_headingless_fragment_is_invisible_to_the_checker_that_reads_the_document(
    repo: Path,
) -> None:
    """**Why the rule lives in `check` and not in `document_problems`** — the ruling's own words,
    turned into the assertion that holds them.

    `document_problems` reads the assembled document, and absorption leaves nothing there to find:
    the result is a correct document. So this asserts the negative directly — the document checker
    returns *no* problems on the very assembly the fragment checker refuses — and then asserts the
    absorption itself, that the orphaned prose really does land under the previous fragment's
    heading. Without both halves, "put it in `document_problems` instead" reads as a free
    simplification.

    A test asserting a **non**-behaviour has no fix to revert, so reverting proves nothing about
    it. It is run forward instead: delete the `heading_problems` call from `check` and the first
    assertion below still passes, which is the point — that is the state this test describes."""
    spec = importlib.util.spec_from_file_location("_fragments", TOOL)
    assert spec is not None and spec.loader is not None
    module: Any = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)

        write(repo, "retro.d/20260901_0700-first.md", "## First (20260901 07:00)\n\nIts own body.")
        write(repo, "retro.d/20260901_0710-orphan.md", "Prose belonging to nobody.")

        stream = module.STREAMS["retrospectives"]
        assembled = module.prospective(stream, repo)
        assert assembled is not None
        document = module.document_problems(stream, assembled)
    finally:
        del sys.modules[spec.name]

    assert document == [], (
        "the assembled document is well-formed — absorption is invisible to a checker that reads "
        f"the result, which is why the rule reads the fragments going in: {document}"
    )

    orphan = assembled.index("Prose belonging to nobody.")
    heading = assembled.index("## First (20260901 07:00)")
    assert heading < orphan, "the orphan follows the heading it would be read as belonging to"
    assert "##" not in assembled[heading + 2 : orphan], (
        "nothing separates them: the orphaned prose reads as part of the first fragment's incident"
    )

    assert run(repo, "--stream", "retrospectives", "--check").returncode == 1


def test_a_third_level_heading_does_not_open_a_fragment(repo: Path) -> None:
    """The heading arm on its own, with the stamp arm satisfied — the only way to isolate it, since
    the stamp lives inside the heading and a fragment with no heading fails both.

    `###` is the level `render` gives a *changelog* category, and `docs/RETROSPECTIVES.md` carries
    42 of them at `0aea036` **inside** entries. A fragment opening at that level is a section of
    something, and the something is whatever precedes it."""
    write(
        repo,
        "retro.d/20260901_0710-a-lesson.md",
        "### A lesson (20260901 07:10)\n\nProse.\n",
    )

    result = run(repo, "--stream", "retrospectives", "--check")

    assert result.returncode == 1
    assert "must open with its own `## ` heading" in result.stderr
    assert "must carry" not in result.stderr, "the stamp is correct; only the level is wrong"


def test_a_heading_whose_stamp_disagrees_with_the_filename_is_refused(repo: Path) -> None:
    """One minute out, which is the drift nothing prompts you to check.

    The stamp is a *copy* of the filename's prefix — one reading of the clock written twice — and
    a second reading is a second chance to be wrong. On 20260826 three headings were typed from
    memory in one morning, out by 1 minute, 2 minutes and 3 hours 30 minutes; only the filename can
    settle which was meant."""
    write(
        repo,
        "retro.d/20260901_0710-a-lesson.md",
        "## A lesson (20260901 07:11)\n\nProse.\n",
    )

    result = run(repo, "--stream", "retrospectives", "--check")

    assert result.returncode == 1
    assert "(20260901 07:10)" in result.stderr, "the message names the stamp the filename requires"
    assert "must open with its own" not in result.stderr, "the heading is fine; the stamp is not"


@pytest.mark.parametrize(
    "heading",
    [
        "## A lesson (20260901)",
        "## A lesson — 20260901 07:10",
        "## A lesson (20260901 07:10 UTC)",
        "## A lesson ((20260901 07:10))",
        "## A lesson (20260901 0710)",
        "## A lesson ( (20260901 07:10) )",
        "## A lesson [(20260901 07:10)]",
        "## A lesson x(20260901 07:10)x",
    ],
)
def test_nothing_looser_than_the_ruled_stamp_is_accepted(repo: Path, heading: str) -> None:
    """**A gate that accepts three spellings of a stamp is not checking the stamp.** Each of these
    is a plausible near-miss a writer would defend, and each breaks the property the rule is for:
    the heading and the filename can no longer be compared by equality, so nothing can tell a
    correct stamp from a remembered one. Accepting the ruled form and nothing else was the
    decision, so this is the assertion that keeps it from being loosened by sympathy."""
    write(repo, "retro.d/20260901_0710-a-lesson.md", f"{heading}\n\nProse.\n")

    result = run(repo, "--stream", "retrospectives", "--check")

    assert result.returncode == 1
    assert "(20260901 07:10)" in result.stderr


def test_a_fragment_with_no_prefix_owes_a_heading_and_not_a_stamp(repo: Path) -> None:
    """The exemption, and its exact width. Fragments predating the naming rule have no prefix to
    copy, so there is nothing to compare a stamp against and the stamp arm cannot run. The heading
    arm is unaffected — absorption does not care when the file was named."""
    write(repo, "retro.d/a-lesson.md", "## A lesson\n\nProse.\n")

    assert run(repo, "--stream", "retrospectives", "--check").returncode == 0

    write(repo, "retro.d/a-lesson.md", "Prose with no heading.\n")

    result = run(repo, "--stream", "retrospectives", "--check")

    assert result.returncode == 1
    assert "must open with its own `## ` heading" in result.stderr
    assert "must carry" not in result.stderr, "there is no prefix to require a stamp against"


def test_a_fragment_that_is_neither_reports_both_problems(repo: Path) -> None:
    """Two mistakes with two fixes, so two messages. A single "malformed fragment" line would send
    a writer who adds a heading straight back for a second round over the stamp."""
    write(repo, "retro.d/20260901_0710-a-lesson.md", "Prose with no heading at all.\n")

    result = run(repo, "--stream", "retrospectives", "--check")

    assert result.returncode == 1
    assert "must open with its own `## ` heading" in result.stderr
    assert "(20260901 07:10)" in result.stderr


def test_the_stamp_arm_reads_the_heading_and_not_whatever_line_is_first(repo: Path) -> None:
    """A comment above a *correct* stamped heading was told the heading lacked its stamp.

    One true message — the fragment does not open with its `## ` heading, and `render` splices it
    under whichever fragment sorts before it — and one false one, about a stamp sitting three lines
    down and spelled exactly right. That pair is the failure the byte-order-mark arm was fixed to
    stop producing, reached from a different input: a writer who obeys the false half edits a
    correct line, and a message that sends someone to break working text costs more than the
    silence it replaces.

    The refusal itself is unchanged and must stay — `retro.d/README.md` § Contents says the
    fragment *opens* with its heading, and an HTML comment above it means it does not. Only the
    second message goes.

    Pinned against the fallback too, and the fallback's guard is not the test it looks like.
    Falling back to `""` instead of `first` leaves *this* test green, and leaves
    `test_a_fragment_that_is_neither_reports_both_problems` green as well — a fragment with no
    heading collects both messages either way. What dies is
    `test_the_separator_is_one_space_and_the_gate_is_stricter_than_the_renderer`: a *malformed*
    opening has no `_OPENING` match either, so an empty fallback hands the stamp arm nothing to
    read and it condemns a stamp that is spelled correctly. Read off a run — a first draft of this
    paragraph reasoned its way to the other test and was wrong."""
    write(
        repo,
        "retro.d/20260901_0710-a-lesson.md",
        "<!-- an editorial note -->\n\n## A lesson (20260901 07:10)\n\nProse.\n",
    )

    result = run(repo, "--stream", "retrospectives", "--check")

    assert result.returncode == 1
    assert "must open with its own `## ` heading" in result.stderr
    assert "must carry" not in result.stderr, "the heading three lines down carries the stamp"
    assert result.stderr.count("20260901_0710-a-lesson.md") == 1, "one fault, named once"


def test_the_heading_rule_never_reaches_the_changelog_stream(repo: Path) -> None:
    """`changelog.d/` fragments are `- ` bullets that `render` merges under a category heading it
    synthesises for them; a heading of their own is the defect `document_problems` already
    refuses. Requiring one here would refuse the format that stream exists for — the mirror of the
    bullet rule's scoping, and the same reason."""
    write(repo, "changelog.d/20260901_0710-added-one.md", "- **A new thing.**")

    assert run(repo, "--stream", "changelog", "--check").returncode == 0


def test_a_byte_order_mark_is_named_rather_than_reported_as_a_missing_heading(repo: Path) -> None:
    """A fragment saved as "UTF-8 with BOM" opens with `\\ufeff## …`, so `startswith("## ")` is
    False about a heading that is plainly there.

    **Refusing it is right and the first draft's reason was wrong.** `render` would splice the mark
    into the *middle* of `docs/RETROSPECTIVES.md`, where it is invisible and belongs to nothing —
    so the fragment must not pass. But a message sending the writer to add the heading they already
    wrote is worse than no message: it is the failure
    `test_the_duplicate_message_names_the_mechanism_that_belongs_to_the_stream` already rules
    against, an error naming the wrong cause. `tools/build_rfc_corpus.py` strips a BOM from
    ingested text with a comment saying why, so this is an input class this repository has met."""
    write(
        repo,
        "retro.d/20260901_0710-a-lesson.md",
        "﻿## A lesson (20260901 07:10)\n\nProse.\n",
    )

    result = run(repo, "--stream", "retrospectives", "--check")

    assert result.returncode == 1
    assert "byte-order mark" in result.stderr
    assert "must open with its own" not in result.stderr, "the heading is there; the mark is not it"
    assert "must carry" not in result.stderr, "and the stamp is right once the mark is stripped"


@pytest.mark.parametrize(
    ("opener", "shown"),
    [
        (" ## A lesson (20260901 07:10)", "' ##"),
        ("\t## A lesson (20260901 07:10)", "'\\t##"),
    ],
    ids=["leading-space", "leading-tab"],
)
def test_a_heading_hidden_by_leading_whitespace_is_quoted_with_the_whitespace_showing(
    repo: Path, opener: str, shown: str
) -> None:
    """The refusal was right and the message was unreadable, which is the same defect as the BOM.

    Refusing both is right, and not for one reason. Measured 20260901 against Python-Markdown with
    `mkdocs.yml`'s own extension list: `" ## A lesson"` renders as a **paragraph** under the
    previous fragment's heading — absorbed, the mechanism the gate exists for, and one leading
    space is enough because Python-Markdown is stricter than CommonMark — while `"\t## A lesson"`
    renders as a **code block**. Both also mint an anchor from `anchors_of`
    (`tools/markdown_link_gate.py`, a regex allowing three leading spaces) that the built page does
    not have, so a link to either passes the link gate and 404s on the site.

    **What it said was not.** The message quoted the offending line `.strip()`ped, so it read *must
    open with its own `## ` heading, and opens with `'## A lesson (20260901 07:10)'`* — a complaint
    and a counter-example to itself, naming the one character the writer cannot see and then
    deleting it. Found by running the gate, not by reading it: a probe fed it a leading space and a
    leading tab and both came back with the same self-contradicting line.

    **The positive assertion is the one that kills the mutant, and this paragraph said the
    opposite until it was run.** Restore the `.strip()` and the message shows `'## A lesson …'`:
    the whitespace is missing, so `assert shown in result.stderr` fails first and pytest never
    reaches the line below it. The negative assertion is not redundant — it is what would catch a
    message showing the raw line *and* the stripped one beside it, which the positive assertion
    alone would accept — but it is a guard against a defect nobody has written, not the killer of
    the one in the battery. The false version of this sentence was copied into `f1de4c1`'s commit
    message, where it cannot be edited."""
    write(repo, "retro.d/20260901_0710-a-lesson.md", f"{opener}\n\nProse.\n")

    result = run(repo, "--stream", "retrospectives", "--check")

    assert result.returncode == 1
    assert "must open with its own `## ` heading" in result.stderr
    assert shown in result.stderr, "the message shows the whitespace that caused the refusal"
    assert "opens with '## " not in result.stderr, (
        "quoted stripped, the message contradicts itself and names nothing to fix"
    )
    assert "must carry" not in result.stderr, "the stamp is correct; only the opening is hidden"


def test_a_byte_order_mark_alone_on_the_first_line_reports_only_itself(repo: Path) -> None:
    """The same defect as the mark itself, one input shape further in — and it took a second review.

    A mark on its own line leaves `"\\ufeff\\n## A lesson …"`, and `"\\ufeff".strip()` is
    truthy — so that line was chosen as the fragment's opening line, stripping the mark *there*
    left `""`, and the heading two lines down was never read. The fragment collected three
    messages: the true one, plus a missing heading and a missing stamp, about a heading and a
    stamp that were both already correct.

    Pass 1 added the mark arm precisely so a fragment would not be sent to fix what is right, and
    then did exactly that to the next input shape. The fix strips the mark from the *text* before
    the opening line is chosen, which is the only place the choice is not already poisoned."""
    write(
        repo,
        "retro.d/20260901_0710-a-lesson.md",
        "﻿\n## A lesson (20260901 07:10)\n\nProse.\n",
    )

    result = run(repo, "--stream", "retrospectives", "--check")

    assert result.returncode == 1
    assert "byte-order mark" in result.stderr
    assert "must open with its own" not in result.stderr, "the heading is two lines down, and fine"
    assert "must carry" not in result.stderr, "so is the stamp inside it"
    assert result.stderr.count("20260901_0710-a-lesson.md") == 1, "one fault, named once"


@pytest.mark.parametrize(
    "opener",
    [
        "##  A lesson (20260901 07:10)",
        "##\tA lesson (20260901 07:10)",
        "##\t A lesson (20260901 07:10)",
        "##A lesson (20260901 07:10)",
    ],
    ids=["two-spaces", "tab", "tab-then-space", "no-space"],
)
def test_the_separator_is_one_space_and_the_gate_is_stricter_than_the_renderer(
    repo: Path, opener: str
) -> None:
    """All four of these render *byte-identically* to the ruled form, and all four are refused.

    Measured 20260902 against Python-Markdown with `mkdocs.yml`'s own extension list: all four —
    two spaces, a tab, a tab then a space, and no space at all — produce the same
    `<h2 id="a-lesson-20260901-0710">` as the ruled opening, byte for byte. `anchors_of` mints
    that anchor for the first three and **nothing** for `"##A lesson"`, which is the only
    difference between the four that anything downstream can see. **This sentence said *three*
    until 20260902**: the three whitespace forms had been rendered and the fourth inferred from
    `anchors_of`'s silence, which answers a different question than the renderer does. So this
    arm is not about a
    consequence in the built page — it is about `retro.d/README.md` § Contents saying the opening is
    `## ` **exactly** and that this checker refuses anything else. A gate accepting a form that
    sentence excludes makes the sentence false, and the sentence is the thing writers read.

    **The line the code drew before this was drawn by an idiom, not by a decision.**
    `first.startswith("## ")` accepted `"##  A lesson"` and refused `"##\tA lesson"` — neither the
    ruled form nor the renderer's tolerance, and stated nowhere. `"##A lesson"` is the fourth case
    and the only one with a consequence of its own: it renders as a correct heading that
    `tools/markdown_link_gate.py` cannot see, so nothing may link to it."""
    write(repo, "retro.d/20260901_0710-a-lesson.md", f"{opener}\n\nProse.\n")

    result = run(repo, "--stream", "retrospectives", "--check")

    assert result.returncode == 1
    assert "must open with its own `## ` heading" in result.stderr
    assert "must carry" not in result.stderr, "the stamp is correct; only the separator is not"


def test_a_whitespace_only_first_line_is_not_read_as_the_opening(repo: Path) -> None:
    """An editor leaves one behind routinely, and the heading is on the next line.

    `next((line for line in text.split("\n") if line.strip()), "")` picks the first line with
    something on it, so `"   \n## A lesson …"` opens with the heading and the fragment is correct.
    Drop the `.strip()` and the blank line becomes the opening: the writer is told the fragment has
    no `## ` heading *and* no stamp, about a heading and a stamp that are both already right — the
    exact false-positive class the mark arms exist to prevent, reintroduced by the selector that
    chooses which line the arms are about.

    Pinned here because it was not pinned anywhere: pass 4 mutated `if line.strip()` to `if line`
    and all 56 tests stayed green."""
    write(
        repo,
        "retro.d/20260901_0710-a-lesson.md",
        "   \n## A lesson (20260901 07:10)\n\nProse.\n",
    )

    result = run(repo, "--stream", "retrospectives", "--check")

    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "breaker",
    ["\x0b", "\x0c", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029"],
)
def test_the_stamp_must_end_the_real_line_not_a_break_python_invents(
    repo: Path, breaker: str
) -> None:
    """`str.splitlines()` breaks on eight characters Markdown does not, and the arm above asks
    whether the stamp ends the line it is given. Hand it the part before a form feed and a heading
    whose visible text runs well past the stamp reads as correctly stamped: python-markdown renders
    `## A lesson (20260901 07:10)\x0c- trailing text` as a single `<h2>` containing all of it.

    The gate's own comment and `docs/VERIFICATION.md` both say the stamp must *end* the heading, so
    this is the assertion that makes those two sentences true rather than nearly true. Splitting on
    `\n` alone is what the renderer does, and it is what the checker now does."""
    write(
        repo,
        "retro.d/20260901_0710-a-lesson.md",
        f"## A lesson (20260901 07:10){breaker}- trailing text after the stamp\n\nProse.\n",
    )

    result = run(repo, "--stream", "retrospectives", "--check")

    assert result.returncode == 1
    assert "(20260901 07:10)" in result.stderr
