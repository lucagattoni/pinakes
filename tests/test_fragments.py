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

import subprocess
import sys
from pathlib import Path

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
    found with the evidence already gone. The target must be byte-identical after the refusal."""
    before = changelog(repo)
    write(repo, "changelog.d/added-one.md", "---\ncategory: added\n---\n\n- **A new thing.**\n")

    result = run(repo, "--stream", "changelog", "--apply")

    assert result.returncode == 1
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
    the stream with a category vocabulary, and this is the assertion that says so."""
    write(
        repo,
        "docs/RETROSPECTIVES.md",
        "# Retrospectives\n\n## I1 - first (20260725 13:40)\n\n"
        "A paragraph, which is what this document is made of.\n\n"
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
