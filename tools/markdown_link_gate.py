"""Relative links resolve in the Markdown MkDocs never sees — a gate, not a convention.

**Why a gate at all.** `mkdocs build --strict` resolves every internal link and heading anchor in
this repository, and it is the *only* thing that does. It reads `docs/` alone (`mkdocs.yml`
`docs_dir`), and `exclude_docs` drops `docs/README.md` even from that. So `CLAUDE.md`, the root
`README.md`, `CHANGELOG.md`, all of `plans/`, the `changelog.d/` and `retro.d/` READMEs and
`docs/README.md` itself — 28 files carrying 163 checkable links when this gate was written — are
checked by nothing at all. Measured 20260823, before this existed: **eleven were broken**, five of
them unambiguously dead as authored, including three in `CHANGELOG.md` pointing at `../docs/...`
from the repository *root* (resolving above the repository) and one citing a `docs/STATUS.md`
heading that a re-measurement had since renamed. Four more had been fixed in `CLAUDE.md` that same
morning. A surface that accumulates dead links faster than anyone reads it is this project's own
threshold for turning a convention into a gate — the same reason `status_header_gate.py`,
`release_order_gate.py` and `nul-scan` exist.

**What it refuses to do is as important as what it checks.** It never resolves a link inside a
fenced block or an inline code span, because a *quoted* link is not a link: a document that quotes
another document's `[text](target)` verbatim would otherwise be told its quotation is broken, and
the only way to satisfy the gate would be to corrupt the quote. Code-span it and it is inert.

**A fragment is checked where its body is going, not where the file is.** `retro.d/` and
`changelog.d/` are *consuming* directories: `tools/fragments.py --apply` copies each body into
`docs/RETROSPECTIVES.md` or `CHANGELOG.md` and deletes the file. So a link written in a fragment has
two resolutions and only the second one matters, and they disagree in exactly the case the fragment
READMEs forbid — `[x](20260902_0245-….md)` names a real sibling inside `retro.d/` and a file that
never existed inside `docs/`. Nothing pre-splice could see it: this gate resolved it from
`retro.d/`, `mkdocs build --strict` never reads `retro.d/` at all, and the failure therefore
surfaced at the release cut with the whole build red. It happened at 0.12.0's cut and **twice more
on 20260902**, the second time on `main`. Resolving a fragment's targets from its destination
directory closes it, and the same move makes the *other* half legal: a `#…` anchor into a sibling
fragment's heading is correct about the spliced document and was the thing this gate used to refuse,
which is why the READMEs carried an instruction to degrade those links to code spans. The anchor
universe is the destination's own headings plus every pending fragment's; a slug two files both
contribute is refused rather than guessed at.

**The slug algorithm is GitHub's, and it is duplicated on purpose.** `mkdocs_hooks.py` installs the
same function into the site build so the two renderings agree; this gate cannot import it (the repo
root is not on `sys.path`, and the hook is deliberately outside pyright's `include`). Duplication
that drifts is worse than none, so `tests/test_markdown_link_gate.py` imports the hook by path and
asserts the two produce identical output for **every heading in the repository** — the copies
cannot diverge silently.

**Case is compared against the filesystem, never delegated to it.** macOS is case-insensitive and
CI's ubuntu runner is not, so `Path.exists()` answers `True` locally for a link that 404s on GitHub
and fails in CI. Every path component is matched against the real directory listing instead.

**Every `](` it cannot parse is a failure, never a skip.** A control leg proves a checker has no
false *positives* — run this over `docs/` and MkDocs' own guarantee says the answer must be zero —
but nothing proves it has no false *negatives*, and a link regex that quietly matches less than it
should reports a clean bill it never earned. The first draft of this checker forbade newlines in
link text, which silently dropped every wrapped link in a repository that wraps prose at 100
columns. So the parser counts what it saw and fails if it did not understand all of it.

`--paths` and `--repo` exist for the unit tests; with neither, it checks the real repository.
"""

import argparse
import os
import re
import subprocess
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

REPO = Path(__file__).resolve().parent.parent

_DISCARDED = re.compile(r"[^\w\s-]", re.UNICODE)


def github_slugify(text: str, separator: str = "-") -> str:
    """GitHub's heading-anchor algorithm: strip, lowercase, drop punctuation, spaces to hyphens.

    Byte-identical to `_github_slugify` in `mkdocs_hooks.py`; `tests/test_markdown_link_gate.py`
    asserts they agree on every heading in the repository. Whitespace is *not* collapsed — that is
    the whole point, and why `a — b` yields `a--b`: the em dash is discarded and the two spaces
    around it are not.
    """
    text = unicodedata.normalize("NFC", text).strip().lower()
    return _DISCARDED.sub("", text).replace(" ", separator)


_FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
_LIST_MARKER = re.compile(r"^ *(?:[-*+]|\d+[.)]) +")
_HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
_HTML_ANCHOR = re.compile(r"""<[^>]*\b(?:id|name)\s*=\s*["']([^"']+)["']""")
_CODE_SPAN = re.compile(r"(`+)(?:(?!\1).)*?\1")

_LINK = re.compile(
    r"\[(?:[^\[\]]|\[[^\[\]]*\])*\]\(\s*(<[^>\n]*>|(?:[^()\s]|\([^()\s]*\))+)"
    r"(?:\s+[\"'][^\"'\n]*[\"'])?\s*\)",
    re.S,
)
_REFDEF = re.compile(r"^ {0,3}\[[^\]\n]+\]:\s*(<[^>\n]*>|\S+)")
_HREF = re.compile(r"""<a\b[^>]*\bhref\s*=\s*["']([^"']*)["']""", re.I)
_UNPARSED = re.compile(r"\]\(")

_EXTERNAL = ("http://", "https://", "mailto:", "ftp://", "tel:", "data:", "irc:", "news:")


def blank_fences(src: str) -> list[str]:
    """Blank every line that is *code* rather than prose, preserving the line count.

    Two block forms, and the second is not optional. A **fenced** block is obvious. An
    **indented** block — four spaces after a blank line — is not, and it is where this checker
    first went wrong in the direction that does real damage: `retro.d/README.md:37` is an indented
    example teaching fragment authors which anchor form to write, and a checker that reads it as a
    live link reports a dead one. A peer acting on that false positive rewrote the example into one
    teaching the *wrong* form before catching it. **A false positive gets acted on**, so the skips
    matter as much as the catches.

    List content is not code. Inside `- item`, continuation lines are indented to the item's
    content column and stay prose; only four columns *beyond* that is a code block. Without the
    list stack every wrapped bullet in this repository would silently stop being checked, which is
    the false-negative half of the same mistake.
    """
    out: list[str] = []
    fence: str | None = None
    lists: list[int] = []
    after_blank = True
    in_indented = False
    for line in src.split("\n"):
        match = _FENCE.match(line)
        if fence is not None:
            if (
                match is not None
                and match.group(1)[0] == fence[0]
                and len(match.group(1)) >= len(fence)
            ):
                fence = None
            out.append("")
            continue
        if match is not None:
            fence = match.group(1)
            after_blank = False
            in_indented = False
            out.append("")
            continue
        if not line.strip():
            after_blank = True
            in_indented = False
            out.append(line)
            continue
        indent = len(line) - len(line.lstrip(" "))
        while lists and indent < lists[-1]:
            lists.pop()
        threshold = lists[-1] if lists else 0
        if indent >= threshold + 4 and (after_blank or in_indented):
            in_indented = True
            out.append("")
            continue
        in_indented = False
        after_blank = False
        marker = _LIST_MARKER.match(line)
        if marker is not None:
            lists.append(len(marker.group(0)))
        out.append(line)
    return out


def blank_code_spans(line: str) -> str:
    """Inline code spans to same-length spaces. **Per line, never across them.**

    A single unbalanced backtick with `re.S` swallows every heading after it: the first run of this
    checker reported 82 broken links in `docs/ROADMAP.md`'s neighbourhood (2616 backticks, zero
    fences) for exactly that reason, on a surface `--strict` guarantees is clean.
    """
    return _CODE_SPAN.sub(lambda m: " " * len(m.group(0)), line)


def readable_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def anchors_of(path: Path) -> set[str]:
    """Every fragment a link may target: heading slugs, plus explicit HTML `id=`/`name=`.

    Headings are slugged from their **raw** text — the slugifier discards backticks and angle
    brackets itself, which is how ``# The sidecar — `<file>.pnk.yaml` `` yields
    `the-sidecar--filepnkyaml` on GitHub. Repeats take GitHub's `-1`, `-2` suffixes.
    """
    raw = readable_text(path)
    seen: dict[str, int] = {}
    out: set[str] = set()
    for line in blank_fences(raw):
        match = _HEADING.match(line)
        if match is None:
            continue
        slug = github_slugify(match.group(2))
        count = seen.get(slug, 0)
        seen[slug] = count + 1
        out.add(slug if count == 0 else f"{slug}-{count}")
    out.update(_HTML_ANCHOR.findall(raw))
    return out


@dataclass(frozen=True)
class Link:
    line: int
    target: str


def links_of(path: Path) -> tuple[list[Link], list[int]]:
    """Every link target in the file, with its 1-based line, and the lines it failed to parse."""
    body = "\n".join(blank_code_spans(line) for line in blank_fences(readable_text(path)))
    found: list[Link] = []
    covered: set[int] = set()

    def line_of(offset: int) -> int:
        return body.count("\n", 0, offset) + 1

    for match in _LINK.finditer(body):
        target = match.group(1)
        # `](` sits at the end of the bracket run; record the line it is actually written on so a
        # wrapped link is credited to the line a reader would look at.
        covered.add(line_of(body.index("](", match.start())))
        found.append(Link(line_of(match.start()), target))
    for number, line in enumerate(body.split("\n"), start=1):
        for pattern in (_REFDEF, _HREF):
            for match in pattern.finditer(line):
                found.append(Link(number, match.group(1)))
    unparsed = [
        number
        for number, line in enumerate(body.split("\n"), start=1)
        # A Jinja placeholder carrying spaces — `[x]({{ url }})` — is not link syntax this gate is
        # entitled to an opinion about; it has no target until a template is rendered.
        if _UNPARSED.search(line)
        and number not in covered
        and "{{" not in line
        and "{%" not in line
    ]
    cleaned = [
        Link(link.line, link.target[1:-1] if link.target.startswith("<") else link.target)
        for link in found
    ]
    return cleaned, unparsed


def exists_case_sensitively(repo: Path, target: Path) -> bool:
    """`Path.exists()` lies on a case-insensitive filesystem; compare against the real listing.

    macOS answers `True` for `docs/status.md`; GitHub and CI's ubuntu runner do not. Without this
    the gate is green on the machine that writes the link and red on the one that publishes it.
    """
    current = repo
    try:
        parts = target.resolve().relative_to(repo).parts
    except ValueError:
        return False
    for part in parts:
        try:
            entries = os.listdir(current)
        except OSError:
            return False
        if part not in entries:
            return False
        current = current / part
    return True


#: Where each fragment stream's bodies end up. **Duplicated from `tools/fragments.py`'s `STREAMS`
#: on purpose, for the reason the slug algorithm is** — this gate must run as a bare script from a
#: repository root that is not on `sys.path`, and importing a sibling in `tools/` only works for
#: some of the ways it is invoked. `tests/test_markdown_link_gate.py` asserts the two tables are
#: identical, so the copies cannot drift in silence.
SPLICE_TARGETS: dict[str, str] = {
    "changelog.d": "CHANGELOG.md",
    "retro.d": "docs/RETROSPECTIVES.md",
}


@dataclass(frozen=True)
class Problem:
    path: Path
    line: int
    target: str
    reason: str


def mkdocs_scope(repo: Path) -> tuple[str, set[str]]:
    """What the site build covers, read out of `mkdocs.yml` rather than assumed.

    Hard-coding `docs/` would let this gate and the site disagree the moment either moved; a
    missing key is a failure rather than a default, because defaulting silently would shrink this
    gate's scope to nothing and still report success.
    """
    text = (repo / "mkdocs.yml").read_text(encoding="utf-8")
    docs_dir = re.search(r"^docs_dir:\s*(\S+)\s*$", text, re.M)
    if docs_dir is None:
        raise SystemExit("markdown-links: mkdocs.yml has no `docs_dir:` — cannot derive scope")
    block = re.search(r"^exclude_docs:\s*\|\s*$((?:\n(?:[ \t]+\S.*|\s*))*)", text, re.M)
    excluded: set[str] = set()
    if block is not None:
        for line in block.group(1).split("\n"):
            entry = line.strip().lstrip("/")
            if entry:
                excluded.add(entry)
    return docs_dir.group(1).strip().rstrip("/"), excluded


def ungated_markdown(repo: Path) -> list[Path]:
    """Every tracked `.md` file `mkdocs build --strict` does not resolve links for."""
    try:
        listed = subprocess.run(
            ["git", "ls-files", "-z", "*.md"],
            cwd=repo,
            capture_output=True,
            check=True,
        ).stdout.split(b"\0")
    except (subprocess.CalledProcessError, FileNotFoundError, NotADirectoryError) as exc:
        # Without this the failure is a traceback and `git`'s own exit status 128, which says
        # nothing about what was asked. Reached whenever `--repo` names somewhere that is not a
        # work tree, which is also what a bare invocation from outside this repository does.
        raise SystemExit(f"markdown-links: cannot list tracked files under {repo}: {exc}") from exc
    docs_dir, excluded = mkdocs_scope(repo)
    out: list[Path] = []
    for entry in filter(None, listed):
        rel = entry.decode()
        if rel.startswith(f"{docs_dir}/"):
            inside = rel[len(docs_dir) + 1 :]
            if inside not in excluded:
                continue
        path = repo / rel
        # **Tracked but absent is a normal state, not a broken link.** `docs/RELEASING.md` step 1
        # runs `tools/fragments.py --apply`, which splices each fragment into its document and
        # *deletes* it — and `check.sh` runs before the `git add` that records the deletion. So on
        # every release there is a window where `git ls-files` names a file the disk does not have.
        # Reading it raised `FileNotFoundError` here, which would have failed the release commit on
        # every release from this one onwards. Found by a peer hitting the identical bug in their
        # own scanner ten minutes earlier, on this same release.
        if not path.is_file():
            continue
        out.append(path)
    return sorted(out)


def splice_destination(repo: Path, path: Path) -> Path | None:
    """The document this file's body ends up inside, or `None` if it stays where it is.

    A fragment is not checked where it sits. `tools/fragments.py --apply` copies its body into
    `CHANGELOG.md` or `docs/RETROSPECTIVES.md` and deletes the file, so every relative target in it
    is resolved by a reader from *that* document's directory. The two READMEs are not fragments and
    are excluded, along with anything nested deeper than the stream directory itself.
    """
    try:
        rel = path.resolve().relative_to(repo)
    except ValueError:
        return None
    if len(rel.parts) != 2 or rel.name == "README.md":
        return None
    target = SPLICE_TARGETS.get(rel.parts[0])
    return None if target is None else repo / target


def spliced_anchors(repo: Path, directory: str) -> tuple[set[str], set[str]]:
    """Every heading anchor the spliced document will carry, and the ones it will carry twice.

    A cross-fragment link is written before the document it will live in exists, so the universe is
    the destination's own anchors plus every pending fragment's. **The ambiguous set is returned
    rather than discarded**: two files contributing one slug means the rendered document numbers the
    second `-1`, and which one keeps the bare form depends on where the splice lands. Refusing that
    link is honest; accepting it would be this gate reporting a certainty it does not have. Measured
    20260902 at `06d8a91`: zero such collisions across 25 `retro.d/` fragments, 11 `changelog.d/`
    fragments and both destination documents, so the refusal costs nothing today.
    """
    contributors: list[Path] = []
    target = repo / SPLICE_TARGETS[directory]
    if target.is_file():
        contributors.append(target)
    source = repo / directory
    if source.is_dir():
        contributors.extend(sorted(p for p in source.glob("*.md") if p.name != "README.md"))
    seen: dict[str, int] = {}
    for contributor in contributors:
        for slug in anchors_of(contributor):
            seen[slug] = seen.get(slug, 0) + 1
    return set(seen), {slug for slug, count in seen.items() if count > 1}


def check_file(
    repo: Path,
    path: Path,
    anchor_cache: dict[Path, set[str]],
    spliced_cache: dict[str, tuple[set[str], set[str]]] | None = None,
) -> list[Problem]:
    problems: list[Problem] = []
    # **A fragment is checked where its body is going, not where the file is.** This is the whole
    # of the splice-destination arm: `destination` is `None` for every other file in the repository
    # and nothing below it changes behaviour for those.
    destination = splice_destination(repo, path)
    base = path.parent if destination is None else destination.parent
    if spliced_cache is None:
        spliced_cache = {}
    links, unparsed = links_of(path)
    for number in unparsed:
        problems.append(
            Problem(
                path,
                number,
                "",
                "link syntax this gate could not parse — it must not skip what it cannot read",
            )
        )
    for link in links:
        target = link.target
        if not target or target.startswith(_EXTERNAL) or target.startswith("//"):
            continue
        if "{{" in target or "{%" in target:
            continue  # a Jinja placeholder in a template: it has no meaning until rendered
        if target == "#":
            continue  # "top of this page" — every renderer treats it as a no-op, not an anchor
        if target.startswith("#"):
            wanted = unquote(target[1:])
            if destination is None:
                anchors = anchor_cache.setdefault(path, anchors_of(path))
                if wanted not in anchors:
                    problems.append(
                        Problem(path, link.line, target, "no such heading anchor in this file")
                    )
                continue
            directory = path.resolve().relative_to(repo).parts[0]
            if directory not in spliced_cache:
                spliced_cache[directory] = spliced_anchors(repo, directory)
            universe, ambiguous = spliced_cache[directory]
            where = destination.relative_to(repo)
            if wanted in ambiguous:
                problems.append(
                    Problem(
                        path,
                        link.line,
                        target,
                        f"two files contribute this heading to {where}, so the anchor the site "
                        f"generates depends on splice order — rename one heading",
                    )
                )
            elif wanted not in universe:
                problems.append(
                    Problem(
                        path,
                        link.line,
                        target,
                        f"no such heading anchor in {where} or in any pending "
                        f"{directory}/ fragment — this body is spliced into {where}",
                    )
                )
            continue
        if target.startswith("/"):
            problems.append(
                Problem(
                    path,
                    link.line,
                    target,
                    "root-absolute link — GitHub resolves it against the site root, not the repo",
                )
            )
            continue
        rest, _, fragment = target.partition("#")
        rest = unquote(rest.split("?", 1)[0])
        dest = base if rest == "" else (base / rest)
        if not dest.resolve().is_relative_to(repo):
            problems.append(
                Problem(path, link.line, target, "resolves outside the repository root")
            )
            continue
        if not exists_case_sensitively(repo, dest):
            shown = dest.resolve()
            where = shown.relative_to(repo) if shown.is_relative_to(repo) else shown
            reason = f"no such file or directory: {where}"
            if destination is not None:
                # Without this the message reads as a plain typo for the one case it exists to
                # catch: `[x](20260902_0245-….md)` from inside `retro.d/` names a file that is
                # right there on disk, and the gate is refusing it for where it is *going*.
                reason += (
                    f" — a fragment's relative links resolve from "
                    f"{destination.relative_to(repo)}, where its body is spliced. Link to the "
                    f"sibling's heading anchor instead of its filename."
                )
            problems.append(Problem(path, link.line, target, reason))
            continue
        if fragment and dest.suffix == ".md":
            anchors = anchor_cache.setdefault(dest.resolve(), anchors_of(dest))
            if unquote(fragment) not in anchors:
                rel = dest.resolve().relative_to(repo)
                problems.append(
                    Problem(path, link.line, target, f"no such heading anchor in {rel}")
                )
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="markdown_link_gate", description=__doc__)
    parser.add_argument("--repo", type=Path, default=REPO, help="repository root (tests use this)")
    parser.add_argument(
        "--paths",
        type=Path,
        nargs="*",
        help="check these files instead of every ungated tracked .md (tests use this)",
    )
    args = parser.parse_args(argv)
    repo: Path = args.repo.resolve()
    paths: list[Path] = list(args.paths) if args.paths else ungated_markdown(repo)

    missing = [path for path in paths if not path.is_file()]
    if missing:
        raise SystemExit(
            "markdown-links: --paths named file(s) that do not exist: "
            + ", ".join(str(path) for path in missing)
        )

    anchor_cache: dict[Path, set[str]] = {}
    spliced_cache: dict[str, tuple[set[str], set[str]]] = {}
    problems: list[Problem] = []
    total = 0
    for path in paths:
        total += len(links_of(path)[0])
        problems.extend(check_file(repo, path, anchor_cache, spliced_cache))

    if problems:
        print(
            f"markdown-links: {len(problems)} broken link(s) in Markdown the docs site never "
            f"resolves. A quoted link belongs in a code span, where this gate leaves it alone.",
            file=sys.stderr,
        )
        for problem in problems:
            rel = (
                problem.path.relative_to(repo)
                if problem.path.is_relative_to(repo)
                else problem.path
            )
            shown = f" -> {problem.target}" if problem.target else ""
            print(f"  {rel}:{problem.line}{shown}\n      {problem.reason}", file=sys.stderr)
        return 1

    print(f"markdown-links: {len(paths)} ungated file(s), {total} link(s), none broken.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
