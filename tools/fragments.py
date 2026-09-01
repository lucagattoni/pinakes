"""Per-change fragment files for the documents every agent appends to.

Several agents work in this repo at once. `CHANGELOG.md` and `docs/RETROSPECTIVES.md` are the two
documents *every* piece of work must write to, which makes them the two files most likely to be
edited twice in an hour — and the collision has a quiet shape as well as a loud one:

    the loud one   `git merge` conflicts.
    the quiet one  `git merge` succeeds because the edits landed on different lines. Git merged
                   them because they did not overlap textually, never because they agree.

`tools/shared_file_overlap.py` *reports* both. This removes the cause for these two documents: a
change writes `changelog.d/<category>-<slug>.md` instead of editing `CHANGELOG.md`, so two agents
cannot touch the same file — the conflict class stops existing rather than being managed. The
fragments are spliced into the real document at release time, by one actor, with nothing else
running. That is the towncrier/scriv/reno model, and this is a small stdlib implementation of it.

**Traceability is unchanged, which is the point.** `docs/BUILDING.md` step 6 requires the changelog
entry to land in the same commit as the code; a fragment lands in the same commit as the code. What
changes is only which file it lands in.

**Category lives in the filename**, never inside the file: `added-record-fixtures.md`. A category
that cannot drift from its content is one fewer thing to check, and `ls changelog.d/` is then a
readable summary of everything unreleased.

That rule is now a gate rather than a convention, because it was silently not followed: three
fragments written for 0.24.0 carried YAML front matter (`---` / `category: added` / `---`), and
`--apply` spliced all three verbatim into `CHANGELOG.md`, where they stayed for six weeks. Nothing
here could see it — the category was read from the filename, so the front matter was inert, and a
body is copied unchanged by design. `check` therefore refuses a fragment whose first non-blank line
is a `---` fence, which is the one shape that means "front matter" rather than "a horizontal rule".

**Both streams took it, and the residue was worse than "spliced text".** Re-measured 20260823:
three in `CHANGELOG.md` under `## [0.24.0]` and **two more in `docs/RETROSPECTIVES.md`**, which the
first count missed because it looked only at the stream the refusal was written for. And the
spliced shape is not inert. `category: added` followed by `---` is a **setext H2**, so each residue
*rendered as a heading* — `site/RETROSPECTIVES/index.html` carried
`<h2 id="category-lesson">category: lesson</h2>` twice, permalinks and search index included, on
the published site. All five were removed at `9718aaa` (20260824 01:17), and the count in
both files is now zero.

**What the repair does not change, and the reason this paragraph stays:** `mkdocs build --strict`
was green on it throughout, because a spurious heading is not a broken link — and
`document_problems` below would not catch it either, because it reads **ATX** headings and this is
**setext**. That blind spot is still here. So is the lesson the undercount taught: the first
measurement looked at one stream and was reported as the whole story.

**The assembled document is checked too, not only the fragments going into it.** `--check` read
every pending fragment and asserted nothing about the result, so a splice could leave
`CHANGELOG.md` malformed with every gate in this repository green — and had: `## [0.28.3]` carried
`### Fixed` twice consecutively, with a bare paragraph for a body. Two rules, on the result: a
heading never repeats consecutively, and (`changelog` only, since `retro.d/` is free-form prose) an
entry opens with a `- ` list item.

**Existing `[Unreleased]` prose is left exactly where it is.** Splicing puts fragments *after* the
anchor without touching what is already below, so this can be adopted without a migration commit
that would itself collide with whatever the other agents are holding.

Stdlib only, importing nothing from this project — same constraint as `tools/paid_path_gate.py`.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_REPO = Path(__file__).resolve().parent.parent

#: Keep a Changelog's six, lowercased for use as a filename prefix.
CHANGELOG_CATEGORIES = ("added", "changed", "deprecated", "removed", "fixed", "security")


@dataclass(frozen=True)
class Stream:
    """One fragment-backed document."""

    name: str
    directory: str
    target: str
    #: Fragments are spliced immediately after the first line equal to this.
    insert_after: str | None = None
    #: …or immediately before the first line starting with this, for a document with a footer.
    insert_before: str | None = None
    #: Filename-prefix vocabulary, or None when a fragment is free-form prose.
    categories: tuple[str, ...] | None = None

    def path(self, repo: Path) -> Path:
        return repo / self.directory


STREAMS: dict[str, Stream] = {
    "changelog": Stream(
        name="changelog",
        directory="changelog.d",
        target="CHANGELOG.md",
        insert_after="## [Unreleased]",
        categories=CHANGELOG_CATEGORIES,
    ),
    "retrospectives": Stream(
        name="retrospectives",
        directory="retro.d",
        target="docs/RETROSPECTIVES.md",
        # This file ends with the pre-implementation design-review passes, which must stay last.
        insert_before="## Design review passes",
    ),
}

_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class FragmentError(Exception):
    """A fragment that would produce a malformed document. Reported with its filename."""


def fragments_of(stream: Stream, repo: Path) -> list[Path]:
    directory = stream.path(repo)
    if not directory.is_dir():
        return []
    return sorted(p for p in directory.glob("*.md") if p.name != "README.md")


#: `YYYYMMDD_HHMM-`, the timestamp prefix every fragment and plan carries.
_STAMP = re.compile(r"^\d{8}_\d{4}-")


def body_of(path: Path) -> str:
    """The filename with its `YYYYMMDD_HHMM-` prefix removed.

    The prefix orders `ls` chronologically and dates a fragment without opening it. Everything
    downstream — the category, the slug — reads what follows it, so the stem is stripped once
    here rather than at each caller. A fragment *without* a prefix is not an error: the
    convention began 20260804 07:00 and refusing files that predate it buys nothing.
    """
    return _STAMP.sub("", path.stem, count=1)


def category_of(stream: Stream, path: Path) -> str | None:
    """The category a fragment's filename declares, validated against the stream's vocabulary."""
    if stream.categories is None:
        return None
    head = body_of(path).split("-", 1)[0]
    if head not in stream.categories:
        raise FragmentError(
            f"{stream.directory}/{path.name}: filename must be "
            f"`YYYYMMDD_HHMM-<category>-<slug>.md` with a category from "
            f"{', '.join(stream.categories)} — found {head!r}"
        )
    return head


def opens_with_front_matter(text: str) -> bool:
    """A `---` fence as the fragment's first non-blank line.

    Only the *opening* fence counts. A body is spliced verbatim, so a `---` further down is a
    legitimate horizontal rule between paragraphs and refusing it would be wrong; a fragment that
    opens with one is declaring metadata this assembler never reads.
    """
    for line in text.splitlines():
        if not line.strip():
            continue
        return line.rstrip() == "---"
    return False


_FENCE = re.compile(r"^[ \t]*(```+|~~~+)")


def prose_lines(text: str) -> tuple[list[tuple[int, str]], int | None]:
    """Every line *outside* a fenced code block, and the line a fence was left open on.

    **The second half of that return is the point.** An unclosed fence swallows every line after
    it, so a scanner that just skips them reports a well-formed document having read half of one —
    *"a clean bill it never earned"*, in `tools/markdown_link_gate.py`'s words about the same
    failure in its own regex. Both documents are balanced today (two fences each); the caller
    refuses rather than trusting that.

    **Fenced blocks are the only code form that needs skipping, and the fence may be indented.**
    Everything read below matches `#` at column zero, and an *indented* code block's lines begin
    with four spaces by definition — so it can never hold a column-zero heading and needs no
    handling. A fence can: it may itself sit at any indent, inside a list item, while the lines it
    encloses start at column zero. `tools/markdown_link_gate.py` needs the indented form and a
    list stack as well, because it reads link syntax anywhere on a line; a heading lives in one
    column, which is what lets this stay smaller without being weaker.

    **The indent is not hypothetical, and assuming it away is how this was first written wrong.**
    Measured 20260823: `CHANGELOG.md`'s only fenced block is indented two spaces inside a bullet
    (`- **…** …` then `  ```text`), and the file contains no column-zero fence at all — so a
    scanner anchored at column zero skips nothing in the one document it most needs to read. A
    changelog entry demonstrating a Markdown heading is an ordinary thing to write, and the
    failure that follows is a gate refusing a correct document. `tools/markdown_link_gate.py`
    records a false positive of that shape being *acted on* before it was disbelieved.
    """
    out: list[tuple[int, str]] = []
    fence: str | None = None
    opened_at: int | None = None
    for number, line in enumerate(text.splitlines(), start=1):
        match = _FENCE.match(line)
        if fence is not None:
            if (
                match is not None
                and match.group(1)[0] == fence[0]
                and len(match.group(1)) >= len(fence)
            ):
                fence, opened_at = None, None
            continue
        if match is not None:
            fence, opened_at = match.group(1), number
            continue
        out.append((number, line))
    return out, opened_at


def document_problems(stream: Stream, text: str) -> list[str]:
    """Every structural problem in the assembled document, rather than in a fragment.

    `check` reads the fragments going *in*. Nothing read the document coming *out*, and the gap
    was not theoretical: `CHANGELOG.md` carried `### Fixed` twice consecutively under
    `## [0.28.3]`, and that entry's body — like one `### Changed` further down — was a bare
    paragraph rather than the `- **claim.**` bullet `changelog.d/README.md` requires.
    `--check` exited **0** on both. Every fragment involved was well-formed; the defect existed
    only in the result, which is why the result is what this reads.

    **Two checks, and the first is worth more than it looks.** A duplicated heading is a property
    of *adjacency*, and every other gate here reads rows — `mkdocs build --strict` resolves links,
    `tools/release_order_gate.py` reads sequences — so all of them walk straight past two
    identical headings in a row. Nothing in this repository had ever read the assembled file.

    **The bullet rule is `changelog`-only.** `retro.d/` fragments are free-form prose carrying
    their own `##` heading, so requiring a bullet there would refuse the format that stream is
    for. The adjacency rule applies to both, because two identical headings in a row are never
    intended in either.

    Both are whole-document rather than anchor-scoped, because both instances that prove them
    necessary sat in *shipped* sections: a rule guarding only `[Unreleased]` would have left the
    evidence in the file. Measured 20260823 against `main` at 0.30.0 — zero violations of either,
    over the full history of both documents.
    """
    problems: list[str] = []
    lines, unclosed = prose_lines(text)
    if unclosed is not None:
        problems.append(
            f"{stream.target}:{unclosed}: a code fence is opened here and never closed, so every "
            "line below it was skipped and neither rule below has read them. Close the fence."
        )

    previous: tuple[int, str] | None = None
    for number, line in lines:
        if line.startswith("#"):
            heading = line.rstrip()
            if previous is not None and previous[1] == heading:
                # The consequence differs by stream, and naming the wrong one is its own defect:
                # `_merge_into_section` runs only for a stream with a category vocabulary, so
                # quoting it at `docs/RETROSPECTIVES.md` would explain a mechanism that never
                # touches that file.
                why = (
                    "`_merge_into_section` reuses the first it finds, so nothing will ever merge "
                    "into the second"
                    if stream.categories is not None
                    else "the second is dead weight a reader has no way to tell from the first"
                )
                problems.append(
                    f"{stream.target}:{number}: `{heading}` repeats the heading on line "
                    f"{previous[0]} with nothing between them. {why}, and a reader scanning for "
                    "it stops at the first."
                )
            previous = (number, heading)
        elif line.strip():
            previous = None

    if stream.categories is None:
        return problems

    opened: tuple[int, str] | None = None
    for number, line in lines:
        if line.startswith("#"):
            opened = (number, line.rstrip()) if line.startswith("### ") else None
        elif line.strip() and opened is not None:
            if not line.startswith("- "):
                problems.append(
                    f"{stream.target}:{number}: `{opened[1]}` opens with a paragraph rather than "
                    f"a `- ` list item: {line.strip()[:60]!r}. Keep a Changelog entries are list "
                    "items, and `render` splices a fragment body verbatim — so this is what the "
                    "fragment said."
                )
            opened = None
    return problems


def heading_problems(stream: Stream, path: Path, text: str) -> list[str]:
    """The two ways a retrospective fragment joins the incident above it without saying so.

    **Neither is visible to `document_problems`, and that is not an oversight — it is the
    mechanism.** A fragment carrying no `##` heading is not malformed once spliced. It is
    *absorbed*: `render` joins bodies with a blank line, so its prose lands under whichever
    fragment sorts before it and reads as a continuation of that incident. The result is
    well-formed markdown making a false claim about whose retrospective it is, every existing gate
    stays green, and the reader who would notice is the one who no longer can. A checker reading
    the assembled document is reading the evidence after it has been destroyed, so this reads the
    fragments going in.

    The stamp is the second half and a different failure. `retro.d/README.md` requires the
    heading's `(YYYYMMDD HH:MM)` to be a **copy** of the filename's prefix — one reading of the
    clock written twice — because a second reading is a second chance to be wrong. On 20260826
    three headings were typed from memory in one morning, out by 1 minute, 2 minutes and **3 hours
    30 minutes**, in fragments whose own subject was measurement discipline; the largest drift is
    the one nothing prompts you to check. Only the filename can settle it, so only a fragment that
    has a prefix is checked here — the fragments predating the naming rule are exempt from this
    arm and **not** from the first.

    Nothing looser than the ruled form passes: not a date without a time, not an em-dash in place
    of the parentheses, not a trailing `UTC`. A gate that accepts three spellings of a stamp is
    not checking the stamp, it is checking that somebody typed a date.

    Reported separately because they are separate mistakes with separate fixes, and a fragment can
    have either without the other.

    **This is the retrospectives stream only.** `changelog.d/` fragments are `- ` bullets merged
    under a category heading `render` synthesises for them, so requiring a heading of their own
    would refuse the format that stream is for.
    """
    if stream.name != "retrospectives":
        return []

    problems: list[str] = []
    first = next((line for line in text.splitlines() if line.strip()), "")
    if not first.startswith("## "):
        problems.append(
            f"{stream.directory}/{path.name}: must open with its own `## ` heading, and opens "
            f"with {first.strip()[:60]!r}. `render` joins fragment bodies with a blank line, so "
            f"this one would be spliced into {stream.target} under the heading of whichever "
            "fragment sorts before it, and read as part of that incident."
        )

    stamp = _STAMP.match(path.stem)
    if stamp is None:
        return problems
    day, clock = stamp.group(0)[:8], stamp.group(0)[9:13]
    wanted = f"({day} {clock[:2]}:{clock[2:]})"
    if wanted not in first:
        problems.append(
            f"{stream.directory}/{path.name}: its heading must carry `{wanted}` — the filename's "
            "own prefix, pasted, not the clock read a second time. Nothing else counts: not the "
            "date alone, not an em-dash instead of the parentheses, not a trailing `UTC`."
        )
    return problems


#: The two places a problem carries a line number: its `file:line:` prefix, and the `on line N`
#: back-reference inside a duplicate-heading message. Both shift when the same fault is seen in the
#: assembled document instead of the one on disk, and stripping only the prefix left the *other*
#: number in the key — so every existing fault compared unequal to itself and was reported twice.
_POSITION = re.compile(r"^[^:]*:\d+: |on line \d+")


def _without_position(problem: str) -> str:
    """A problem's text with every line number removed, for comparing it across two documents."""
    return _POSITION.sub("", problem)


def prospective(stream: Stream, repo: Path) -> str | None:
    """The document `--apply` would write right now, or `None` when there is nothing to apply."""
    rendered = render(stream, repo)
    return splice(stream, rendered, repo) if rendered else None


def validate_document(stream: Stream, repo: Path) -> list[str]:
    """The document on disk **and the one `--apply` would write from the fragments now pending.**

    The second half is the item's own sentence: *"It asserts nothing about the result of
    `--apply`. So a splice can produce a malformed `CHANGELOG.md` and every gate in this
    repository stays green."* Reading only the file on disk answers a narrower question — whether
    the *last* splice went well — and the fragment that causes the next one is sitting in the tree
    unread while it does.

    **That is not hypothetical; it is the recurring cause.** Both instances the item cites came
    from a fragment whose body opens with its own `### Fixed` heading, which `render` then wraps
    in a second one: `changelog.d/fixed-two-frozen-yaml-behaviours.md` at 0.6.0 (hand-repaired
    seven minutes after the release) and
    `changelog.d/20260823_0233-fixed-published-versions-row-is-a-checked-sequence.md` at 0.28.3.
    Checked here, that fragment fails at the commit that adds it, with the evidence in the tree.
    Checked only at `--apply`, it fails at the release, and `docs/RELEASING.md` is where somebody
    is then deciding whether to hand-edit a document to get the release out.

    A problem already reported against the file on disk is not repeated for the assembly — the
    assembly contains the whole file, so every existing fault appears in both at different line
    numbers, and reporting each twice would bury the one that is new.
    """
    target = repo / stream.target
    if not target.is_file():
        return [f"{stream.target}: missing — `--apply` has nothing to splice into."]

    problems = document_problems(stream, target.read_text(encoding="utf-8"))
    try:
        assembled = prospective(stream, repo)
    except FragmentError as exc:
        return [*problems, str(exc)]
    if assembled is None:
        return problems

    already = {_without_position(p) for p in problems}
    for problem in document_problems(stream, assembled):
        if _without_position(problem) not in already:
            problems.append(
                f"{problem}  ← in the document `--apply` would write, not the one on disk. "
                "Fix the fragment; the line number is the assembled document's."
            )
    return problems


def check(stream: Stream, repo: Path) -> list[str]:
    """Every problem found, rather than the first.

    A caller fixing fragments wants the whole list.
    """
    problems: list[str] = []
    for path in fragments_of(stream, repo):
        try:
            category = category_of(stream, path)
        except FragmentError as exc:
            problems.append(str(exc))
            continue
        stem = body_of(path)
        slug = stem.split("-", 1)[1] if category and "-" in stem else stem
        if not _SLUG.fullmatch(slug):
            problems.append(f"{stream.directory}/{path.name}: name must be lowercase-with-hyphens")
        body = path.read_text(encoding="utf-8")
        if not body.strip():
            problems.append(f"{stream.directory}/{path.name}: is empty")
        elif opens_with_front_matter(body):
            problems.append(
                f"{stream.directory}/{path.name}: opens with a `---` front-matter fence, which is "
                f"spliced verbatim into {stream.target}. The category lives in the filename, "
                "never inside the file — delete the fence and start with the entry body."
            )
        else:
            problems.extend(heading_problems(stream, path, body))
    return problems


def render(stream: Stream, repo: Path) -> str:
    """The fragments as one markdown block, grouped by category in the stream's declared order."""
    paths = fragments_of(stream, repo)
    if not paths:
        return ""

    def body(path: Path) -> str:
        return path.read_text(encoding="utf-8").strip("\n")

    if stream.categories is None:
        return "\n\n".join(body(p) for p in paths) + "\n"

    grouped: dict[str, list[str]] = {}
    for path in paths:
        category = category_of(stream, path)
        assert category is not None
        grouped.setdefault(category, []).append(body(path))

    blocks: list[str] = []
    for category in stream.categories:
        if category not in grouped:
            continue
        blocks.append(f"### {category.capitalize()}\n\n" + "\n\n".join(grouped[category]))
    return "\n\n".join(blocks) + "\n"


def grouped_bodies(stream: Stream, repo: Path) -> dict[str, list[str]]:
    """Fragment bodies keyed by category, for a stream that has one."""
    grouped: dict[str, list[str]] = {}
    for path in fragments_of(stream, repo):
        category = category_of(stream, path)
        assert category is not None
        grouped.setdefault(category, []).append(path.read_text(encoding="utf-8").strip("\n"))
    return grouped


def _prose_indices(lines: list[str]) -> set[int]:
    """0-based indices into `lines` that are *not* inside a fenced code block.

    **The splicer and the checker have to agree about what a heading is.** `document_problems`
    skips fenced blocks; the scans below did not, so a column-zero ```` ``` ```` block containing
    `### Added` was a heading to `_merge_into_section` and not one to the gate. Demonstrated: a
    fragment spliced *inside* the code block, `--apply` exited 0, the fragment was deleted, and
    `--check` passed on the result — the entry rendering as sample code nobody would find.

    Before this increment nothing read the document, so the disagreement had no second party and
    the splicer's blindness was merely latent. Adding a gate that claims `--apply` cannot leave
    the document malformed is what makes closing it part of the same change.
    """
    return {number - 1 for number, _ in prose_lines("".join(lines))[0]}


def _merge_into_section(
    stream: Stream, lines: list[str], anchor_index: int, grouped: dict[str, list[str]]
) -> str:
    """Merge fragments into the anchor's section, reusing a `### Category` heading if one is there.

    Found by cutting a release with it: dumping every rendered `### Category` block under the anchor
    produced a `[Unreleased]` with **two** `### Added` headings, because the section already had one
    from prose nobody had migrated. Keep a Changelog expects one heading per category, and a reader
    scanning for "what was added" would stop at the first.

    The region is the anchor's own section — up to the next `##` heading — so a `### Added`
    belonging to an *older release* further down is never written into.
    """
    prose = _prose_indices(lines)

    end = len(lines)
    for index in range(anchor_index + 1, len(lines)):
        if index in prose and lines[index].startswith("## "):
            end = index
            break

    existing: dict[str, int] = {}
    for index in range(anchor_index + 1, end):
        if index not in prose:
            continue
        heading = lines[index].rstrip("\n")
        if heading.startswith("### "):
            existing.setdefault(heading[4:].strip().lower(), index)

    # Applied last-first so that an insertion never shifts an index still to be used.
    additions: list[tuple[int, str]] = []
    fresh: list[str] = []
    for category in stream.categories or ():
        if category not in grouped:
            continue
        body = "\n\n".join(grouped[category])
        if category in existing:
            additions.append((existing[category] + 1, "\n" + body + "\n"))
        else:
            fresh.append(f"### {category.capitalize()}\n\n{body}\n")

    out = list(lines)
    for index, block in sorted(additions, reverse=True):
        out.insert(index, block)
    if fresh:
        out.insert(anchor_index + 1, "\n" + "\n".join(fresh))
    return "".join(out)


def splice(stream: Stream, rendered: str, repo: Path) -> str:
    """`rendered` inserted at the stream's anchor, leaving everything else byte-identical."""
    text = (repo / stream.target).read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    prose = _prose_indices(lines)
    if stream.insert_after is not None:
        for index, line in enumerate(lines):
            if index in prose and line.rstrip("\n") == stream.insert_after:
                if stream.categories is not None:
                    return _merge_into_section(stream, lines, index, grouped_bodies(stream, repo))
                head, tail = lines[: index + 1], lines[index + 1 :]
                return "".join(head) + "\n" + rendered + "".join(tail)
        raise FragmentError(f"{stream.target}: anchor {stream.insert_after!r} not found")

    assert stream.insert_before is not None
    for index, line in enumerate(lines):
        if index in prose and line.startswith(stream.insert_before):
            head, tail = lines[:index], lines[index:]
            return "".join(head) + rendered + "\n" + "".join(tail)
    raise FragmentError(f"{stream.target}: anchor {stream.insert_before!r} not found")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stream", choices=[*sorted(STREAMS), "all"], default="all", help="which document"
    )
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check", action="store_true", help="validate fragments (a gate)")
    action.add_argument("--render", action="store_true", help="print the assembled markdown")
    action.add_argument(
        "--apply",
        action="store_true",
        help="splice fragments into the document and delete them (the release step)",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=DEFAULT_REPO,
        help="repository root (default: this script's own). Lets the tests drive the real "
        "artifact against a temp tree rather than importing it.",
    )
    args = parser.parse_args()
    repo: Path = args.repo

    streams = list(STREAMS.values()) if args.stream == "all" else [STREAMS[args.stream]]

    if args.check:
        problems = [p for stream in streams for p in check(stream, repo)]
        # …and the document `--apply` writes, which nothing here read until 0.30.0's item. Both
        # halves run even when the first fails: an author fixing this wants the whole list, the
        # same reason `check` returns every problem rather than the first.
        documents = [p for stream in streams for p in validate_document(stream, repo)]
        for problem in [*problems, *documents]:
            print(problem, file=sys.stderr)
        if problems:
            print(f"{len(problems)} malformed fragment(s).", file=sys.stderr)
        if documents:
            print(f"{len(documents)} problem(s) in the assembled document.", file=sys.stderr)
        if problems or documents:
            return 1
        counts = ", ".join(f"{len(fragments_of(s, repo))} {s.name}" for s in streams)
        targets = ", ".join(s.target for s in streams)
        print(f"fragments: {counts} — all well-formed; {targets} well-formed.")
        return 0

    # Every stream is spliced and validated before *any* stream is written, so the refusal below
    # is true of the whole run rather than of the stream that happened to fail. `--apply` walks
    # two streams: refusing mid-walk wrote `CHANGELOG.md` and deleted its fragments, then exited 1
    # saying "Nothing written, no fragment deleted" — a false statement about a half-applied
    # release, in the direction that destroys the evidence. A release step is one step or none.
    planned: list[tuple[Stream, str]] = []
    for stream in streams:
        if problems := check(stream, repo):
            for problem in problems:
                print(problem, file=sys.stderr)
            return 1
        if args.render:
            if rendered := render(stream, repo):
                print(rendered, end="")
            continue
        # `prospective` — the same function `--check` validates through, called rather than
        # re-derived. `--check` now simulates a write, so the two must agree about assembly
        # forever, and a disagreement between them would be *silent*: `--check` green on an
        # assembly `--apply` would never produce. Sharing the definition makes them the same code
        # rather than two paths that happen to match;
        # `test_check_validates_the_exact_bytes_apply_writes` holds them to it from the outside.
        spliced = prospective(stream, repo)
        if spliced is None:
            print(f"fragments: nothing to apply for {stream.name}.")
            continue
        # Checked before the write, and therefore before the deletes below. A malformed document
        # found *after* `--apply` is found with the fragments that caused it already gone — the
        # same reasoning `check.sh` gives for running `--check` at commit time rather than at
        # release time, one step further in.
        if damage := document_problems(stream, spliced):
            for problem in damage:
                print(problem, file=sys.stderr)
            print(
                f"fragments: refusing to write {stream.target} — the splice would leave it "
                "malformed. Nothing written, no fragment deleted.",
                file=sys.stderr,
            )
            return 1
        planned.append((stream, spliced))

    for stream, spliced in planned:
        (repo / stream.target).write_text(spliced, encoding="utf-8")
        for path in fragments_of(stream, repo):
            path.unlink()
        print(f"fragments: applied {stream.name} into {stream.target}, fragments removed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
