"""`tools/markdown_link_gate.py` — the checker that watches the Markdown MkDocs never sees.

**Why this file is long.** A link checker fails in two directions and only one of them is loud.
A false *positive* is reported and argued with; a false *negative* is a clean bill nobody earned,
and it is the one that shipped here: the first draft of this checker forbade newlines in link text,
so in a repository that wraps prose at 100 columns it silently skipped every wrapped link, and an
earlier draft blanked inline code spans with `re.S` and reported 82 broken links in `docs/` — a
surface `mkdocs build --strict` guarantees is clean. **Both bugs were found by running the checker
against a corpus with a known-correct answer, not by reading it.** So the tests below cover the
skips as carefully as the catches, and the last one runs the real checker over the real `docs/`,
where MkDocs' own guarantee supplies the expected answer.

Exercised **as a subprocess**, argument parsing included, for the reason
`tests/test_wheel_import_gate.py` gives: the thing under test is the artifact `check.sh` runs, not
an import of it. The one exception is the drift test, which must hold two implementations of the
same function side by side and says so.
"""

import importlib.util
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import cast

import pytest

REPO = Path(__file__).resolve().parent.parent
GATE = REPO / "tools" / "markdown_link_gate.py"
MKDOCS_YML = "docs_dir: docs\nexclude_docs: |\n  /README.md\n"


def _run(root: Path, *paths: str) -> subprocess.CompletedProcess[str]:
    argv = [sys.executable, str(GATE), "--repo", str(root)]
    if paths:
        argv += ["--paths", *[str(root / name) for name in paths]]
    return subprocess.run(argv, capture_output=True, text=True, cwd=str(root))


def _write(root: Path, name: str, body: str) -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    _write(tmp_path, "mkdocs.yml", MKDOCS_YML)
    return tmp_path


# --------------------------------------------------------------------------------------------
# What it must catch
# --------------------------------------------------------------------------------------------


def test_a_link_to_a_file_that_does_not_exist_is_reported(repo: Path) -> None:
    _write(repo, "a.md", "see [the guide](guide.md) for more\n")
    result = _run(repo, "a.md")
    assert result.returncode == 1
    assert "no such file or directory" in result.stderr
    assert "a.md:1" in result.stderr


def test_a_link_to_a_heading_that_does_not_exist_is_reported(repo: Path) -> None:
    _write(repo, "target.md", "# Real heading\n")
    _write(repo, "a.md", "see [there](target.md#imagined-heading)\n")
    result = _run(repo, "a.md")
    assert result.returncode == 1
    assert "no such heading anchor in target.md" in result.stderr


def test_a_link_to_a_heading_in_this_very_file_is_checked_too(repo: Path) -> None:
    _write(repo, "a.md", "# Only heading\n\njump to [nowhere](#not-a-heading)\n")
    result = _run(repo, "a.md")
    assert result.returncode == 1
    assert "no such heading anchor in this file" in result.stderr


def test_a_link_that_resolves_above_the_repository_root_is_reported(repo: Path) -> None:
    """Three of these were live in `CHANGELOG.md` when this gate was written: `../docs/...`
    written from the repository *root*, which resolves above the repository and 404s on GitHub."""
    _write(repo, "a.md", "see [manifest](../docs/MANIFEST.md#chunking)\n")
    result = _run(repo, "a.md")
    assert result.returncode == 1
    assert "resolves outside the repository root" in result.stderr


def test_a_root_absolute_link_is_reported_because_github_resolves_it_off_the_repository(
    repo: Path,
) -> None:
    _write(repo, "docs/GUIDE.md", "# Guide\n")
    _write(repo, "a.md", "see [guide](/docs/GUIDE.md)\n")
    result = _run(repo, "a.md")
    assert result.returncode == 1
    assert "root-absolute link" in result.stderr


def test_a_link_whose_case_does_not_match_the_filesystem_is_reported(repo: Path) -> None:
    """The macOS/Linux split: `Path.exists()` says `True` for `Target.md` on the machine that
    writes the link and `False` on the runner that publishes it. Delegating to the filesystem
    makes this gate green exactly where it is useless."""
    _write(repo, "target.md", "# Heading\n")
    _write(repo, "a.md", "see [there](Target.md)\n")
    result = _run(repo, "a.md")
    assert result.returncode == 1
    assert "no such file or directory" in result.stderr


def test_link_text_wrapped_across_lines_is_still_parsed(repo: Path) -> None:
    """The false negative that shipped in the first draft. `CLAUDE.md` wraps link text over two
    lines in seven places; a newline-forbidding regex reports every one of them as clean."""
    _write(repo, "a.md", "see [`docs/BUILDING.md` § some very long\nsection name](gone.md)\n")
    result = _run(repo, "a.md")
    assert result.returncode == 1
    assert "no such file or directory" in result.stderr


def test_link_syntax_the_parser_cannot_read_is_reported_rather_than_skipped(repo: Path) -> None:
    """A checker that silently matches less than it should reports a pass it never earned."""
    _write(repo, "a.md", "a stray ]( that is not a link\n")
    result = _run(repo, "a.md")
    assert result.returncode == 1
    assert "could not parse" in result.stderr


def test_a_reference_style_definition_is_resolved(repo: Path) -> None:
    _write(repo, "a.md", "see [the guide][g]\n\n[g]: guide.md\n")
    result = _run(repo, "a.md")
    assert result.returncode == 1
    assert "no such file or directory" in result.stderr


def test_an_html_anchor_href_is_resolved(repo: Path) -> None:
    _write(repo, "a.md", '<a href="guide.md">the guide</a>\n')
    result = _run(repo, "a.md")
    assert result.returncode == 1
    assert "no such file or directory" in result.stderr


# --------------------------------------------------------------------------------------------
# What it must NOT catch — the skips, which are where a noisy gate gets switched off
# --------------------------------------------------------------------------------------------


def test_a_link_inside_a_fenced_block_is_not_resolved(repo: Path) -> None:
    _write(repo, "a.md", "```\n[not a link](nowhere.md)\n```\n")
    assert _run(repo, "a.md").returncode == 0


def test_a_quoted_link_inside_a_code_span_is_not_resolved(repo: Path) -> None:
    """The class that decides whether this gate is usable. `plans/20260807_2143-docs-audit-
    findings.md` quotes six of other documents' links verbatim; they are correct relative to
    `docs/` and dead relative to `plans/`. Code-spanning a quotation is the fix — the alternative
    is a gate that can only be satisfied by corrupting the quote."""
    _write(repo, "a.md", "the file says `[KB-UPDATES.md](KB-UPDATES.md)` which is wrong\n")
    assert _run(repo, "a.md").returncode == 0


def test_a_link_to_a_directory_is_accepted(repo: Path) -> None:
    """GitHub renders a directory link as a listing, so it is a legitimate target — and resolving
    it with `Path.is_file()` rejects every one. Not hypothetical, and not mine to have found: a
    peer's independent scanner reported six false positives on this repository's real directory
    links (`docs/graph/`, `../plans/`, `../retro.d/`), all correct as authored, while its control
    leg over `docs/` stayed green throughout. **A control validates only the behaviours its corpus
    exercises.** This test exercises the one that corpus missed.
    """
    _write(repo, "graph/PAGE.md", "# Page\n")
    _write(repo, "a.md", "see [the graph notes](graph/) and [also](graph)\n")
    assert _run(repo, "a.md").returncode == 0


def test_a_trailing_slash_directory_that_does_not_exist_is_still_reported(repo: Path) -> None:
    _write(repo, "a.md", "see [gone](imagined/)\n")
    result = _run(repo, "a.md")
    assert result.returncode == 1
    assert "no such file or directory" in result.stderr


def test_a_link_in_an_indented_code_block_is_not_resolved(repo: Path) -> None:
    """The false positive that did real damage. `retro.d/README.md:37` is a four-space-indented
    example teaching fragment authors which anchor form to write — it renders no link at all, and
    a real renderer confirms that file emits exactly one href, which is not this one. A peer acting
    on the false positive rewrote the example into one teaching the **wrong** form before catching
    it. A false positive gets acted on, which is why the skips are tested as hard as the catches.
    """
    body = "Link to the heading instead:\n\n    [example](#an-anchor-that-is-not-here)\n"
    _write(repo, "a.md", body)
    assert _run(repo, "a.md").returncode == 0


def test_a_heading_in_an_indented_code_block_is_not_an_anchor(repo: Path) -> None:
    _write(repo, "t.md", "Real:\n\n# Real\n\nExample:\n\n    # Fake\n")
    _write(repo, "a.md", "[fake](t.md#fake)\n")
    result = _run(repo, "a.md")
    assert result.returncode == 1
    assert "no such heading anchor" in result.stderr


def test_a_wrapped_bullet_continuation_is_still_checked(repo: Path) -> None:
    """The false-negative half of the same rule. Continuation lines inside a list item are indented
    to the item's content column and stay prose; treating four spaces as code unconditionally would
    stop checking every wrapped bullet in a repository that wraps at 100 columns."""
    # A blank line before the continuation is what makes this the list stack's case rather than
    # `after_blank`'s: without the stack, four spaces after a blank line reads as an indented code
    # block, and the link inside it silently stops being checked. The first version of this test
    # omitted the blank line and the mutation pass caught it SURVIVING.
    body = "-   a bullet\n\n    a continuation paragraph that [wraps](gone.md) onto its own line\n"
    _write(repo, "a.md", body)
    result = _run(repo, "a.md")
    assert result.returncode == 1
    assert "no such file or directory" in result.stderr


def test_an_external_link_is_never_fetched_or_resolved(repo: Path) -> None:
    _write(repo, "a.md", "[site](https://example.invalid/nope) [mail](mailto:a@b.c)\n")
    assert _run(repo, "a.md").returncode == 0


def test_a_jinja_placeholder_in_a_template_is_not_resolved(repo: Path) -> None:
    _write(repo, "a.md", "[docs]({{kb_name}}/docs.md) and [x]({{ url }})\n")
    assert _run(repo, "a.md").returncode == 0


def test_a_percent_encoded_target_is_decoded_before_it_is_resolved(repo: Path) -> None:
    _write(repo, "a b.md", "# Heading\n")
    _write(repo, "a.md", "[spaced](a%20b.md)\n")
    assert _run(repo, "a.md").returncode == 0


def test_repeated_headings_take_githubs_numeric_suffixes(repo: Path) -> None:
    _write(repo, "t.md", "# Dup\n\n# Dup\n\n# Dup\n")
    _write(repo, "a.md", "[one](t.md#dup) [two](t.md#dup-1) [three](t.md#dup-2)\n")
    assert _run(repo, "a.md").returncode == 0


def test_the_em_dash_rule_that_the_site_hook_exists_for_is_honoured(repo: Path) -> None:
    """`a — b` slugs to `a--b`: the em dash is discarded and the two spaces around it are not.
    Getting this wrong is not hypothetical — it is the whole reason `mkdocs_hooks.py` exists."""
    _write(repo, "t.md", "# The sidecar — `<file>.pnk.yaml`\n")
    _write(repo, "a.md", "[sidecar](t.md#the-sidecar--filepnkyaml)\n")
    assert _run(repo, "a.md").returncode == 0


def test_a_heading_inside_a_fenced_block_is_not_an_anchor(repo: Path) -> None:
    _write(repo, "t.md", "# Real\n\n```\n# Fake\n```\n")
    _write(repo, "a.md", "[fake](t.md#fake)\n")
    result = _run(repo, "a.md")
    assert result.returncode == 1
    assert "no such heading anchor" in result.stderr


def test_an_explicit_html_id_is_a_valid_anchor(repo: Path) -> None:
    _write(repo, "t.md", '<a id="hand-written"></a>\n\n# Heading\n')
    _write(repo, "a.md", "[there](t.md#hand-written)\n")
    assert _run(repo, "a.md").returncode == 0


# --------------------------------------------------------------------------------------------
# Scope, and the two implementations that must not drift
# --------------------------------------------------------------------------------------------


def test_the_scope_is_read_from_mkdocs_yml_and_covers_the_readme_the_site_excludes(
    tmp_path: Path,
) -> None:
    """`docs/README.md` is excluded from the site by `mkdocs.yml`, so its links are resolved by
    nothing — 53 of them in the real repository. A gate that assumed `docs/` was covered would
    leave the routing table unchecked."""
    _write(tmp_path, "mkdocs.yml", MKDOCS_YML)
    _write(tmp_path, "docs/GUIDE.md", "[gone](nowhere.md)\n")  # covered by mkdocs: skipped
    _write(tmp_path, "docs/README.md", "[gone](nowhere.md)\n")  # excluded there: ours
    _write(tmp_path, "CLAUDE.md", "[gone](nowhere.md)\n")
    subprocess.run(["git", "init", "-q"], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "add", "-A"], cwd=str(tmp_path), check=True)
    result = _run(tmp_path)
    assert result.returncode == 1
    assert "docs/README.md:1" in result.stderr
    assert "CLAUDE.md:1" in result.stderr
    assert "docs/GUIDE.md" not in result.stderr


def test_a_missing_docs_dir_in_mkdocs_yml_is_refused_rather_than_defaulted(tmp_path: Path) -> None:
    """Defaulting would silently shrink the scope to nothing and still print a pass."""
    _write(tmp_path, "mkdocs.yml", "site_name: Nope\n")
    _write(tmp_path, "CLAUDE.md", "# hi\n")
    subprocess.run(["git", "init", "-q"], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "add", "-A"], cwd=str(tmp_path), check=True)
    result = _run(tmp_path)
    assert result.returncode != 0
    assert "no `docs_dir:`" in result.stderr


def test_the_gate_and_the_site_slugify_every_heading_in_the_repository_identically() -> None:
    """The gate cannot import `mkdocs_hooks.py` (the repo root is not on `sys.path`, and the hook
    sits outside pyright's `include`), so the algorithm is duplicated. Duplication that drifts is
    worse than none: here both copies are held against **every heading in the repository**, so the
    site and this gate cannot disagree about what an anchor is without a test going red.
    """
    spec = importlib.util.spec_from_file_location("_hooks", REPO / "mkdocs_hooks.py")
    assert spec is not None and spec.loader is not None
    hooks = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hooks)
    site_slugify = cast(Callable[[str, str], str], hooks._github_slugify)

    gate_spec = importlib.util.spec_from_file_location("_gate", GATE)
    assert gate_spec is not None and gate_spec.loader is not None
    gate = importlib.util.module_from_spec(gate_spec)
    gate_spec.loader.exec_module(gate)
    gate_slugify = cast(Callable[[str, str], str], gate.github_slugify)

    headings: list[str] = []
    for path in sorted(REPO.glob("**/*.md")):
        if any(part in {".git", "site", ".venv", "node_modules"} for part in path.parts):
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            match = re.match(r"^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$", line)
            if match is not None:
                headings.append(match.group(1))
    assert len(headings) > 500, f"only {len(headings)} headings found — the corpus is not loaded"
    mismatched = [h for h in headings if site_slugify(h, "-") != gate_slugify(h, "-")]
    assert not mismatched, (
        f"gate and site slugifiers disagree on {len(mismatched)}: {mismatched[:5]}"
    )


def test_the_real_docs_directory_is_clean_which_is_this_checkers_only_control() -> None:
    """`mkdocs build --strict` resolves every link and anchor under `docs/`, so the expected
    answer for that corpus is known independently of this checker. Running it there is the only
    thing standing between this gate and a false negative nobody would ever notice: both bugs
    caught while writing it were caught exactly here, and neither was visible by reading the code.
    """
    tracked = subprocess.run(
        ["git", "ls-files", "docs/*.md", "docs/**/*.md"],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    assert len(tracked) > 25, f"only {len(tracked)} files under docs/ — the control is not loaded"
    result = subprocess.run(
        [sys.executable, str(GATE), "--repo", str(REPO), "--paths", *tracked],
        capture_output=True,
        text=True,
        cwd=str(REPO),
    )
    assert result.returncode == 0, (
        "this checker reports broken links in docs/, which `mkdocs build --strict` guarantees is "
        f"clean — so the checker is wrong, not the docs:\n{result.stderr}"
    )


def test_the_extractor_agrees_with_a_real_renderer_on_every_file_in_the_repository() -> None:
    """The oracle. Every other test here asserts a behaviour someone thought to write down; this
    one asks a real Markdown implementation what links each file *actually* emits and requires the
    regex extractor to have found the same set — the check that catches the failure nobody
    predicted. Measured 20260823 over 114 files and 894 rendered links: **zero** disagreements in
    the direction that matters.

    Skipped, with its reason printed, where Python-Markdown is absent — it ships with the docs
    toolchain (`requirements-docs.txt`), never with the runtime or test extras, and this gate is
    deliberately stdlib-only so `check.sh` and CI can run it with no install at all. So this is the
    evidence that the cheap implementation earns its keep, not a gate anyone depends on.

    The one tolerated difference is a bare `<https://…>` autolink, which the renderer emits and the
    extractor does not parse. It is external, and external targets are never resolved, so it cannot
    change a verdict.
    """
    markdown = pytest.importorskip(
        "markdown", reason="Python-Markdown ships with requirements-docs.txt, not the test extras"
    )
    from html.parser import HTMLParser

    class _Links(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.hrefs: list[str] = []

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            if tag == "a":
                self.hrefs += [v for k, v in attrs if k == "href" and v is not None]

    gate_spec = importlib.util.spec_from_file_location("_gate_oracle", GATE)
    assert gate_spec is not None and gate_spec.loader is not None
    gate = importlib.util.module_from_spec(gate_spec)
    gate_spec.loader.exec_module(gate)

    tracked = subprocess.run(
        ["git", "ls-files", "*.md"], cwd=str(REPO), capture_output=True, text=True, check=True
    ).stdout.split()
    assert len(tracked) > 80, f"only {len(tracked)} markdown files — the corpus is not loaded"

    invented: list[str] = []
    for rel in tracked:
        path = REPO / rel
        html = markdown.markdown(
            path.read_text(encoding="utf-8"),
            extensions=["tables", "fenced_code", "attr_list", "md_in_html", "footnotes"],
        )
        parser = _Links()
        parser.feed(html)
        emitted = set(parser.hrefs)
        for link in gate.links_of(path)[0]:
            if link.target not in emitted:
                invented.append(f"{rel}:{link.line} -> {link.target}")
    assert not invented, (
        "the extractor found links a real renderer does not emit — every one of these would be "
        "reported to a human as a broken link in text that is not a link:\n  "
        + "\n  ".join(invented)
    )
