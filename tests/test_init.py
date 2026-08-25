"""`pnk init`: a directory that is already correct, and an id that is never minted twice."""

import os
import subprocess
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import pytest

from pinakes import template
from pinakes.ci import WORKFLOW_PATH
from pinakes.errors import InitError, TemplateError
from pinakes.ids import parse_kb_id
from pinakes.init import init
from pinakes.manifest import load


def test_init_produces_a_kb_that_parses(tmp_path: Path) -> None:
    result = init(tmp_path / "research", now="20260725 17:30")
    manifest = load(result.root)

    assert manifest.kb.name == "research"
    assert manifest.kb.id == result.kb_id
    assert manifest.kb.template == "notes@1.2"
    assert manifest.kb.created == "20260725 17:30"
    assert manifest.embedding.model == "BAAI/bge-small-en-v1.5"
    assert manifest.rerank.model == "BAAI/bge-reranker-base"
    assert parse_kb_id(manifest.kb.id) == manifest.kb.id


def test_init_creates_docs_and_ignores_generated_state(tmp_path: Path) -> None:
    """Publishing a KB must never publish its index or its ledger (§4.7)."""
    result = init(tmp_path / "kb")
    assert (result.root / "docs").is_dir()
    assert ".pinakes/" in (result.root / ".gitignore").read_text(encoding="utf-8")


def test_the_template_ships_its_readme_and_a_golden_set_stub(tmp_path: Path) -> None:
    result = init(tmp_path / "kb")
    assert (result.root / "README.md").is_file()
    assert (result.root / "eval" / "questions.yaml").is_file()


def test_confidence_thresholds_are_commented_out(tmp_path: Path) -> None:
    """Thresholds fitted on someone else's corpus are not a calibration (§4.2)."""
    result = init(tmp_path / "kb")
    manifest_text = (result.root / "pinakes.toml").read_text(encoding="utf-8")
    assert "# [retrieval.confidence]" in manifest_text
    assert load(result.root).retrieval.confidence is None


def test_pdfs_are_off_by_default_but_the_manifest_says_how_to_turn_them_on(tmp_path: Path) -> None:
    """`init` cannot see whether `pinakes[pdf]` is installed, so stamping a `**/*.pdf` glob would
    turn every PDF into a failed document on a core-only install (plan decision 6). Off, then —
    but *discoverably* off: 0.2.0 shipped PDF ingest as its headline feature with no glob and no
    mention of one anywhere the user would look, so a PDF dropped into a fresh KB was skipped in
    silence. `pnk sync` names it now too (`test_sync.py`)."""
    result = init(tmp_path / "kb")
    manifest_text = (result.root / "pinakes.toml").read_text(encoding="utf-8")

    assert "**/*.pdf" in manifest_text  # the exact glob, spelled out to copy
    assert "pinakes[pdf]" in manifest_text  # and the extra it needs
    assert "**/*.pdf" not in load(result.root).sources.include  # but not actually enabled


def test_two_kbs_never_share_an_id(tmp_path: Path) -> None:
    first = init(tmp_path / "a")
    second = init(tmp_path / "b")
    assert first.kb_id != second.kb_id


def test_a_custom_name_is_kept(tmp_path: Path) -> None:
    result = init(tmp_path / "kb-directory", name="My Research")
    assert load(result.root).kb.name == "My Research"


def test_refusing_to_re_initialise_explains_why(tmp_path: Path) -> None:
    root = tmp_path / "kb"
    init(root)
    with pytest.raises(InitError) as exc_info:
        init(root)
    assert "orphan every inbound link" in exc_info.value.remedy


def test_a_directory_that_already_has_content_is_adopted(tmp_path: Path) -> None:
    """**Re-decided 20260805**, after the blanket emptiness refusal was hit three times
    independently. Creating the repo, cloning it, then running `pnk init` inside it is what the
    corpus plan prescribes and what everyone does — and a `.git`, a `README.md` and a
    `pyproject.toml` are already "not empty". *"Clear this one first"* is an alarming thing to read
    about a directory holding the documents you meant to index.

    The emptiness test is gone because what replaced it is narrower and stronger: `init` never
    overwrites a file that is already there, so there is nothing left for it to protect."""
    root = tmp_path / "occupied"
    root.mkdir()
    (root / "something.txt").write_text("hello", encoding="utf-8")

    result = init(root)
    assert (root / "pinakes.toml").exists()
    assert (root / "something.txt").read_text(encoding="utf-8") == "hello"
    assert result.adopted == []


def test_init_never_overwrites_the_files_a_real_repository_already_has(tmp_path: Path) -> None:
    """The adoption case in full: a repo has a README and a .gitignore before it is ever a KB, and
    both are files `init` would otherwise write. Replacing them would be destroying the user's work
    to make room for a template's — so they are left **byte-identical** and reported."""
    root = tmp_path / "repo"
    root.mkdir()
    (root / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
    (root / "README.md").write_text("# My Project\n\nReal content.\n", encoding="utf-8")

    result = init(root)

    assert (root / ".gitignore").read_text(encoding="utf-8") == "node_modules/\n"
    assert (root / "README.md").read_text(encoding="utf-8") == "# My Project\n\nReal content.\n"
    assert {path.name for path in result.adopted} == {".gitignore", "README.md"}
    assert all(path not in result.created for path in result.adopted), (
        "a file that was left alone must never be reported as created"
    )


def test_an_adopted_gitignore_that_misses_pinakes_is_flagged(tmp_path: Path) -> None:
    """`.gitignore` is the one skipped file whose *absence of content* has a consequence: an index
    and a spend ledger that can leave the machine. It is reported rather than appended to, because
    appending would be editing a file this tool does not own."""
    root = tmp_path / "repo"
    root.mkdir()
    (root / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
    assert init(root).gitignore_unprotected is True

    other = tmp_path / "already-safe"
    other.mkdir()
    (other / ".gitignore").write_text("build/\n.pinakes/\n", encoding="utf-8")
    assert init(other).gitignore_unprotected is False, (
        "a .gitignore that already covers .pinakes/ must not be flagged"
    )


@pytest.fixture(autouse=True)
def git_config_is_this_repository_only(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the developer's own git configuration out of every test in this file.

    The check asks git, and git answers from more than the `.gitignore` in front of it: a global
    `core.excludesFile`, a system config, a `init.templateDir` that seeds `.git/info/exclude`. A
    developer who has put `.pinakes/` in their personal global ignore file is doing something
    sensible, and without this fixture it turns three of the tests below red on their machine and
    makes two others pass for a reason the code had nothing to do with. Measured 20260825: with a
    global excludes file naming `.pinakes/`, 3 failed and 9 passed.

    **The production code is right to honour those files** — a global ignore really does protect
    the ledger. It is only the *tests* that must not depend on which machine they run on.
    """
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", os.devnull)


def _git_repo(root: Path, gitignore: str | None = None) -> Path:
    """A real git repository, optionally carrying a `.gitignore` before `init` ever runs.

    These tests need a repository because the check asks **git**, and outside one there is no
    authority to ask. `tmp_path` is not a repository, which is why every test above exercises the
    fallback instead — both paths are covered, deliberately.
    """
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    if gitignore is not None:
        (root / ".gitignore").write_text(gitignore, encoding="utf-8")
    return root


@pytest.mark.parametrize(
    ("case", "gitignore", "unprotected"),
    [
        # The two false positives. git ignores `.pinakes/` under both of these, and the substring
        # test `".pinakes/" not in text` warned anyway — training a user to ignore the warning.
        ("bare directory, no trailing slash", ".pinakes\n", False),
        ("a glob that covers it", ".pin*\n", False),
        # The two false negatives, and these are the ones that cost something. git ignores nothing
        # here, and the substring test stayed **silent**: the string is present, so it read as
        # protection. A commented-out line is the cheapest way to reach it — comment it out to
        # debug, re-run `init`, and the ledger and every deep transcript are tracked, in silence.
        ("negated after being listed", ".pinakes/\n!.pinakes/\n", True),
        ("commented out", "#.pinakes/\n", True),
        # **The cover cases, and the first is a regression the review caught.** Probing three named
        # files reported PROTECTED here while `index.db-wal` — megabytes of verbatim document text
        # in WAL mode — stayed tracked. The substring test this replaces *warned*. A check that
        # answers about filenames cannot answer a question about a directory.
        ("*.db and *.json, which cover the probes but not the directory", "*.db\n*.json\n*.jsonl\n", True),
        ("everything under .pinakes ignored except the extraction cache", ".pinakes/*\n!.pinakes/cache\n", True),
        # Controls. Without these a check that always answered the same way would pass four of six.
        ("the exact line this file writes", ".pinakes/\n", False),
        ("nothing to do with pinakes", "node_modules/\n", True),
    ],
)
def test_the_gitignore_check_answers_what_git_answers(
    tmp_path: Path, case: str, gitignore: str, unprotected: bool
) -> None:
    """Six `.gitignore` files, measured against real git on 20260825. Four of them were answered
    wrongly by the substring test this replaces — two warnings that should not have fired, and two
    silences that should have been warnings."""
    root = _git_repo(tmp_path / "repo", gitignore)

    assert init(root).gitignore_unprotected is unprotected, case


def test_ignoring_only_part_of_pinakes_is_not_protection(tmp_path: Path) -> None:
    """`git check-ignore` exits 0 when **any** argument is ignored, so a `.gitignore` naming just
    the ledger would read as full protection while the index stayed tracked. Every probe has to
    match, and this is the test that says so."""
    root = _git_repo(tmp_path / "repo", ".pinakes/ledger.jsonl\n")

    assert init(root).gitignore_unprotected is True, (
        "the ledger being ignored says nothing about the index or the transcripts"
    )


def test_protection_that_lives_outside_gitignore_is_still_protection(tmp_path: Path) -> None:
    """`.git/info/exclude` ignores `.pinakes/` just as effectively as `.gitignore` does, and **no
    amount of reading `.gitignore` can see it**. Nor could a scan see the user's global excludes or
    a parent repository's rules. This test fails against any implementation that reads the file
    rather than asking git, which is the whole point of the change."""
    root = _git_repo(tmp_path / "repo", "node_modules/\n")
    exclude = root / ".git" / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    exclude.write_text(".pinakes/\n", encoding="utf-8")

    assert init(root).gitignore_unprotected is False


@pytest.mark.parametrize(
    ("case", "gitignore", "unprotected"),
    [
        ("commented out", "#.pinakes/\n", True),
        ("no trailing slash", ".pinakes\n", False),
        ("unrelated", "node_modules/\n", True),
        ("the exact line", ".pinakes/\n", False),
        # **Both of these were wrong before the scratch repo**, and in opposite directions. The
        # hand-rolled fallback read `!.pinakes/` as protection — silently, on the same input the
        # in-repo matrix above asserts must warn — and warned about `/.pinakes/`, the root-anchored
        # form many editors emit, which git honours perfectly well.
        ("negated, which the text scan read as protection", ".pinakes/\n!.pinakes/\n", True),
        ("root-anchored, which the text scan warned about", "/.pinakes/\n", False),
        ("a doublestar form", "**/.pinakes/\n", False),
    ],
)
def test_outside_a_repository_git_is_asked_in_a_scratch_repository(
    tmp_path: Path, case: str, gitignore: str, unprotected: bool
) -> None:
    """A KB is often stamped before `git init`, and there is still no excuse for guessing.

    The `.gitignore` is copied into a throwaway repository and the identical probes are run, so
    there is **one** definition of the answer rather than two that can disagree. The text scan is
    reached only when there is no `git` at all.
    """
    root = tmp_path / "plain"
    root.mkdir()
    (root / ".gitignore").write_text(gitignore, encoding="utf-8")

    assert init(root).gitignore_unprotected is unprotected, case


def test_a_gitignore_written_by_init_is_not_re_examined(tmp_path: Path) -> None:
    """The check fires for an **adopted** `.gitignore` only, which is where it always fired.

    A first draft ran it unconditionally, justified by "an ancestor repository could negate what we
    wrote". Review showed that cannot happen — git resolves by directory depth, so the file `init`
    writes in the KB wins over any ancestor. What widening it actually reached was a path already
    in the index, where `check-ignore` says not-ignored and the warning would tell the user to add a
    line their file already contains.
    """
    root = _git_repo(tmp_path / "repo")
    (root / ".pinakes").mkdir()
    (root / ".pinakes" / "index.db").write_text("x", encoding="utf-8")
    subprocess.run(["git", "add", "-Af", ".pinakes"], cwd=root, check=True, capture_output=True)

    result = init(root)

    assert (root / ".gitignore").read_text(encoding="utf-8").splitlines()[-1] == ".pinakes/"
    assert result.gitignore_unprotected is False, (
        "init wrote the .gitignore itself; re-examining it only produces a warning whose remedy "
        "is already satisfied"
    )


def test_an_ambient_git_dir_cannot_answer_for_another_repository(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """git honours `GIT_DIR`/`GIT_WORK_TREE` over `cwd`, and exports both to every hook it runs.

    Without scrubbing them, `pnk init` run from a hook is answered by whichever repository the
    environment names — confidently, and about the wrong tree.
    """
    elsewhere = _git_repo(tmp_path / "elsewhere", ".pinakes/\n")
    root = _git_repo(tmp_path / "repo", "node_modules/\n")
    monkeypatch.setenv("GIT_DIR", str(elsewhere / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(elsewhere))

    assert init(root).gitignore_unprotected is True, (
        "the KB's own repository protects nothing; another repository's rules are not an answer"
    )


def test_a_gitignore_that_is_not_utf8_does_not_abort_a_half_written_kb(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`pinakes.toml` is already on disk by the time this runs, so raising leaves a KB the next
    `pnk init` refuses as "already a KB". One latin-1 byte in a comment used to do it."""

    def _no_git(*args: object, **kwargs: object) -> object:
        raise FileNotFoundError("git")

    monkeypatch.setattr("pinakes.init.subprocess.run", _no_git)
    root = tmp_path / "repo"
    root.mkdir()
    (root / ".gitignore").write_bytes(b"# caf\xe9 notes\n")

    assert init(root).gitignore_unprotected is True


def test_a_git_that_never_returns_does_not_hang_init(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`check-ignore` refreshes the index, which runs the `core.fsmonitor` hook — a wedged Watchman
    blocks it forever. A timeout has to degrade to an answer, not to a traceback."""
    def _timeout(*args: object, **kwargs: object) -> object:
        raise subprocess.TimeoutExpired(cmd="git", timeout=5)

    monkeypatch.setattr("pinakes.init.subprocess.run", _timeout)
    root = tmp_path / "repo"
    root.mkdir()
    (root / ".gitignore").write_text("#.pinakes/\n", encoding="utf-8")

    assert init(root).gitignore_unprotected is True


def test_init_still_stamps_a_kb_when_git_is_not_installed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`init` has never required git, and refusing to stamp a KB because a version-control tool is
    missing would be a worse failure than the one this change fixes."""

    def _no_git(*args: object, **kwargs: object) -> object:
        raise FileNotFoundError("git")

    monkeypatch.setattr("pinakes.init.subprocess.run", _no_git)
    root = tmp_path / "repo"
    root.mkdir()
    (root / ".gitignore").write_text("#.pinakes/\n", encoding="utf-8")

    result = init(root)

    assert result.gitignore_unprotected is True, "the fallback still catches the commented-out line"


def test_ci_refuses_an_existing_workflow_before_creating_anything(tmp_path: Path) -> None:
    """`write_workflow` already refused to overwrite, but it ran *after* `pinakes.toml` was
    written — so the refusal left a half-made KB that the next `pnk init` rejects as "already a
    KB". The old emptiness check was incidentally preventing that; removing it exposed the gap.

    `--ci` is refused rather than adopted because it is an explicit request: honouring it by
    silently doing nothing is worse than refusing."""
    root = tmp_path / "kb"
    (root / WORKFLOW_PATH).parent.mkdir(parents=True)
    (root / WORKFLOW_PATH).write_text("# mine\n", encoding="utf-8")

    with pytest.raises(InitError) as exc_info:
        init(root, ci=True)
    assert "already exists" in exc_info.value.message
    assert not (root / "pinakes.toml").exists(), "nothing may be created before the refusal"
    assert (root / WORKFLOW_PATH).read_text(encoding="utf-8") == "# mine\n"


@pytest.mark.parametrize(
    ("declared", "expected"),
    [
        (["_versions/1.0/README.md"], "names the version archive"),
        (["../escaped.md"], "writes outside the KB"),
    ],
)
def test_a_refused_declaration_creates_nothing_at_all(
    tmp_path: Path,
    synthetic_template: Callable[..., str],
    declared: list[str],
    expected: str,
) -> None:
    """D-18: `init` validates the template's `files` before it writes anything.

    It used to write `pinakes.toml`, `docs/` and `.gitignore` and only then call `copy_extras`, so
    a refused declaration left a directory that is *almost* a KB — and a second `pnk init` then
    refuses it as one, leaving the user with a directory they can neither init nor were asked
    whether they wanted.

    **The assertion is on the whole tree, not on `pinakes.toml`.** Checking one file would pass
    against an implementation that hoisted only the manifest write and still left `docs/` and
    `.gitignore` behind — the half-fix D-18 rejected. `root` must not exist at all.

    Both refusal kinds run, because different checks raise them: the archive rule needs no target
    and containment does. A hoist that moved only the first satisfies one row and fails the other,
    which is precisely the narrow version this decision turned down."""
    name = synthetic_template("synth", versions={"1.0": "[kb]\n"}, current="1.0", files=declared)
    root = tmp_path / "kb"

    with pytest.raises(TemplateError) as exc_info:
        init(root, template_name=name)

    assert expected in exc_info.value.message
    assert not root.exists(), "a refusal must leave no directory, not merely no manifest"


def test_a_refused_declaration_adds_nothing_to_a_directory_being_adopted(
    tmp_path: Path, synthetic_template: Callable[..., str]
) -> None:
    """The adoption case, where "leaves nothing behind" means something different.

    `init` deliberately has no emptiness test — pointing it at a repository that already holds a
    `.git`, a `README.md` and a `pyproject.toml` is the normal way to adopt one. So for that
    directory the property cannot be *"root does not exist"*: it is **the user's files are
    untouched and nothing new was added.** The sibling tests above assert the create case and are
    blind to this one, because their `root` is a path `init` would have made itself.

    Worth its own test rather than a parametrisation: a refusal that deleted the directory it was
    adopting would pass every assertion in this file except these."""
    name = synthetic_template(
        "synth", versions={"1.0": "[kb]\n"}, current="1.0", files=["../escaped.md"]
    )
    root = tmp_path / "existing-repo"
    root.mkdir()
    (root / "README.md").write_text("mine\n", encoding="utf-8")
    (root / "notes.md").write_text("also mine\n", encoding="utf-8")
    before = sorted(path.name for path in root.iterdir())

    with pytest.raises(TemplateError):
        init(root, template_name=name)

    assert sorted(path.name for path in root.iterdir()) == before, "a refusal added a file"
    assert (root / "README.md").read_text(encoding="utf-8") == "mine\n"
    assert not (root / "pinakes.toml").exists()
    assert not (root / "docs").exists()


def test_a_declaration_is_validated_against_a_target_that_does_not_exist_yet(
    tmp_path: Path, synthetic_template: Callable[..., str]
) -> None:
    """The measurement D-18 turns on, pinned so nobody re-derives the wrong answer from it.

    Open-corrections item 4 rejected the full hoist believing containment could not be judged
    before the target existed — so only the declaration check could move, and the guarantee would
    be half-true. `lands_inside` resolves the *parent* and `resolve()` is non-strict, so it can.

    This asserts the **positive** half deliberately: the refusal tests above would all pass against
    a `validate_extras` that raised for every input, existent target or not."""
    name = synthetic_template(
        "synth",
        versions={"1.0": "[kb]\n"},
        current="1.0",
        files=["README.md", "eval/questions.yaml"],
        extras={"README.md": "hi\n", "eval/questions.yaml": "questions: []\n"},
    )
    root = tmp_path / "not-created-yet"
    assert not root.exists()

    assert template.validate_extras(name, root) == ("README.md", "eval/questions.yaml")
    assert not root.exists(), "validation must not create the thing it validates against"


def test_copy_extras_still_validates_when_nobody_validated_for_it(
    tmp_path: Path, synthetic_template: Callable[..., str]
) -> None:
    """`validated=` is an optimisation for `init`, never a way to skip the rule.

    The split exists so `init` does not check twice; any other caller must still get the check.
    Without this, the refactor quietly converts every other call site into an unchecked copy —
    the standing failure mode of splitting a validate/apply pair."""
    name = synthetic_template(
        "synth", versions={"1.0": "[kb]\n"}, current="1.0", files=["../escaped.md"]
    )
    root = tmp_path / "kb"
    root.mkdir()

    with pytest.raises(TemplateError) as exc_info:
        template.copy_extras(name, root)
    assert "writes outside the KB" in exc_info.value.message


def test_backend_light_stamps_fastembed_in_both_blocks(tmp_path: Path) -> None:
    """D-20. Every real KB stamped from `notes` edited the provider in **both** `[embedding]` and
    `[rerank]`, for one reason — a `[light]` install — and `docs/GUIDE.md` documented doing it by
    hand as the normal path. `--backend light` is that edit, made once and recorded as a choice.

    **Both blocks asserted, because editing only one is the mistake the flag exists to prevent.** A
    KB with `fastembed` embeddings and a `sentence-transformers` reranker pulls in the 2 GB
    dependency the extra was chosen to avoid, and does it at query time rather than at install."""
    manifest = load(init(tmp_path / "kb", backend="light").root)

    assert manifest.embedding.provider == "fastembed"
    assert manifest.rerank.provider == "fastembed"
    assert manifest.embedding.dim == 384, "the dimension must match the model actually stamped"


def test_the_default_backend_is_unchanged(tmp_path: Path) -> None:
    """The negative control, and the compatibility promise. Omitting `--backend` must stamp exactly
    what every release before this one stamped — otherwise the flag is a silent breaking change to
    every scripted `pnk init` in existence."""
    from pinakes.init import DEFAULT_EMBEDDING, DEFAULT_RERANK

    manifest = load(init(tmp_path / "kb").root)

    assert (
        manifest.embedding.provider,
        manifest.embedding.model,
        manifest.embedding.dim,
    ) == DEFAULT_EMBEDDING
    assert (manifest.rerank.provider, manifest.rerank.model) == DEFAULT_RERANK


def test_an_unknown_backend_is_refused_by_name(tmp_path: Path) -> None:
    """`argparse` bounds the CLI, and this bounds the function — `init` is importable, and the API
    is what a test or another tool calls. The refusal names the accepted values, because a message
    that only says "no" sends the caller to read the source."""
    with pytest.raises(InitError) as exc_info:
        init(tmp_path / "kb", backend="torch")

    assert "torch" in exc_info.value.message
    assert "light" in exc_info.value.remedy and "st" in exc_info.value.remedy
    assert not (tmp_path / "kb").exists(), "a refused backend must leave no directory"


def test_an_unknown_template_lists_the_known_ones(tmp_path: Path) -> None:
    with pytest.raises(TemplateError) as exc_info:
        init(tmp_path / "kb", template_name="nonexistent")
    assert "notes" in exc_info.value.remedy


def test_templates_are_readable_from_the_installed_package() -> None:
    assert "notes" in template.available()
    info = template.describe("notes")
    assert info.reference == "notes@1.2"


def test_a_template_variable_that_is_never_supplied_fails_loudly() -> None:
    """StrictUndefined: a typo in a template must not render as an empty manifest key.

    It fails as a `TemplateError` rather than a raw `jinja2.UndefinedError`, which is not a
    `PinakesError` and would reach the user as a traceback. The message names the reference and the
    variable, because "something is undefined somewhere" is not a thing anyone can act on.
    """
    from pinakes.errors import TemplateError

    with pytest.raises(TemplateError) as caught:
        template.render_manifest("notes", {"name": "x"})
    assert "notes@1.2" in str(caught.value)
    assert "kb_id" in str(caught.value)


def test_created_is_utc_even_where_the_machine_clock_is_not(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`created` is the UTC instant, never the machine's wall clock.

    Run under `TZ=Pacific/Kiritimati` (UTC+14), a naive `datetime.now()` reads fourteen hours
    ahead — so a KB minted on one machine and read on another disagrees about when it was made,
    and `pnk doctor`'s age checks compare stamps that never shared a zero point. The zone is
    picked for the size of the gap: at UTC+14 the naive stamp is on a different *date* for ten
    hours of every day, which is what makes this fail loudly rather than by a rounding minute.
    """
    monkeypatch.setenv("TZ", "Pacific/Kiritimati")
    time.tzset()

    before = datetime.now(UTC)
    created = load(init(tmp_path / "kb").root).kb.created
    after = datetime.now(UTC)

    assert created is not None
    assert before.strftime("%Y%m%d %H:%M") <= created <= after.strftime("%Y%m%d %H:%M"), (
        f"created {created!r} is not the UTC instant "
        f"({before:%Y%m%d %H:%M}..{after:%Y%m%d %H:%M}) — a naive clock would read "
        f"{datetime.now().strftime('%Y%m%d %H:%M')}"
    )


# --- T7: a template declares the files it writes -------------------------------------------------
#
# **Every one of these needs a filesystem-backed template, not the packaged one.** `notes` declares
# no `files` key at all (which is what the historical-two test below asserts), and the symlink cases
# need something `resolve()` can follow — `importlib.resources` hands back a `Traversable`, which
# for a zip-imported package has neither symlinks nor a `resolve()`. `synthetic_template` builds a
# real directory in a real importable package, so `_root` runs its actual `importlib.resources`
# path against it.

MINIMAL_MANIFEST = '[kb]\nname = "{{ name }}"\nid = "{{ kb_id }}"\n'


def test_a_template_without_a_files_key_still_copies_the_historical_two(tmp_path: Path) -> None:
    """Absent means the two files that were hardcoded before T7 — never none.

    Every template in existence declares nothing, `notes` included, so reading an absent key as an
    empty list would silently stop stamping a README and a starter golden set into every new KB.
    """
    target = tmp_path / "kb"
    target.mkdir()

    written, adopted = template.copy_extras("notes", target)

    assert adopted == []
    assert {path.relative_to(target).as_posix() for path in written} == {
        "README.md",
        "eval/questions.yaml",
    }


def test_a_declared_file_list_is_copied_and_an_undeclared_file_is_not(
    synthetic_template: Callable[..., str], tmp_path: Path
) -> None:
    """Three files in the tree, two declared. The third is the discriminator.

    Without it the test would pass under an implementation that ignores `files` entirely and copies
    whatever it finds.
    """
    name = synthetic_template(
        "declared",
        versions={"1.0": MINIMAL_MANIFEST},
        current="1.0",
        files=["README.md", "eval/questions.yaml"],
        extras={
            "README.md": "the template's readme\n",
            "eval/questions.yaml": "questions: []\n",
            "UNDECLARED.md": "never asked for\n",
        },
    )
    target = tmp_path / "kb"
    target.mkdir()

    written, _ = template.copy_extras(name, target)

    assert {path.relative_to(target).as_posix() for path in written} == {
        "README.md",
        "eval/questions.yaml",
    }
    assert not (target / "UNDECLARED.md").exists()
    assert (target / "README.md").read_text(encoding="utf-8") == "the template's readme\n"


def test_a_files_entry_naming_the_version_archive_is_refused(
    synthetic_template: Callable[..., str], tmp_path: Path
) -> None:
    """The property that moved here from T1, where it could not fail.

    While `copy_extras` iterated a hardcoded pair, no `_versions/` path was reachable whatever the
    archive held, so an assertion there was satisfied by the hardcoding rather than by any rule.

    **Asserted on the archive rule's own words, not merely on a raise.** Containment would let this
    entry through — it lands *inside* the target — so a test satisfied by any `TemplateError` would
    stay green under an implementation that has no archive rule at all.
    """
    name = synthetic_template(
        "archived",
        versions={"1.0": MINIMAL_MANIFEST},
        current="1.0",
        files=["_versions/1.0/README.md"],
    )
    target = tmp_path / "kb"
    target.mkdir()

    with pytest.raises(TemplateError) as exc_info:
        template.copy_extras(name, target)

    assert "_versions/1.0/README.md" in exc_info.value.message
    assert "version archive" in exc_info.value.message
    assert not (target / "_versions").exists()


def test_a_template_file_entry_that_escapes_the_target_is_refused(
    synthetic_template: Callable[..., str], tmp_path: Path
) -> None:
    """The lexical case: an entry that walks out of the KB with `..`.

    **The symlink case is a separate test below, and the mutation pass is why.** Both cases lived
    here at first. Removing the destination check then turned this test red on its *first*
    assertion — `../../evil.md` escapes the template as well as the target, so the source-side check
    caught it with a different message — and the run stopped before the symlink case, the one only
    the destination check can catch, ever executed. A test whose later half never runs under the
    mutation it exists to detect is not holding that half.
    """
    lexical = synthetic_template(
        "lexical-escape",
        versions={"1.0": MINIMAL_MANIFEST},
        current="1.0",
        files=["../../evil.md"],
        extras={"README.md": "unused\n"},
    )
    target = tmp_path / "kb"
    target.mkdir()

    with pytest.raises(TemplateError) as exc_info:
        template.copy_extras(lexical, target)

    assert "../../evil.md" in exc_info.value.message
    assert "outside the KB" in exc_info.value.message


def test_a_symlinked_directory_in_the_target_is_refused(
    synthetic_template: Callable[..., str], tmp_path: Path
) -> None:
    """The case only the destination check can catch, and the one a real KB presents.

    No `..`, no absolute path — the escape exists only on disk. It is not exotic: `copy_extras`
    runs against whatever directory is being adopted, and the entry it declares is a perfectly
    ordinary relative path that the template really owns, so the source-side check passes it.
    """
    outside = tmp_path / "outside"
    outside.mkdir()

    symlinked = synthetic_template(
        "symlinked-target",
        versions={"1.0": MINIMAL_MANIFEST},
        current="1.0",
        files=["escape/evil.md"],
        extras={"escape/evil.md": "the template's own copy\n"},
    )
    adopted = tmp_path / "adopted"
    adopted.mkdir()
    (adopted / "escape").symlink_to(outside, target_is_directory=True)

    with pytest.raises(TemplateError) as exc_info:
        template.copy_extras(symlinked, adopted)

    assert "escape/evil.md" in exc_info.value.message
    assert "outside the KB" in exc_info.value.message
    assert not (outside / "evil.md").exists(), "the write happened before the refusal"


def test_a_template_file_entry_that_reads_outside_the_template_is_refused(
    synthetic_template: Callable[..., str], tmp_path: Path
) -> None:
    """The read side, which the write-side check cannot catch — it is a second layer.

    A symlinked directory in the *template* tree lands its destination perfectly inside the KB;
    what escapes is the source. The file it names is then copied **into** the KB and published with
    it, which for a repo meant to be committed is the more expensive direction of the two.
    """
    secret = tmp_path / "elsewhere"
    secret.mkdir()
    (secret / "id_rsa").write_text("not the template's to give away\n", encoding="utf-8")

    name = synthetic_template(
        "reads-out",
        versions={"1.0": MINIMAL_MANIFEST},
        current="1.0",
        files=["borrowed/id_rsa"],
    )
    root = template._root(name)  # pyright: ignore[reportPrivateUsage]
    assert isinstance(root, Path), "the fixture must build a real directory for a symlink to exist"
    root.joinpath("borrowed").symlink_to(secret, target_is_directory=True)

    target = tmp_path / "kb"
    target.mkdir()

    with pytest.raises(TemplateError) as exc_info:
        template.copy_extras(name, target)

    assert "borrowed/id_rsa" in exc_info.value.message
    assert "outside the template" in exc_info.value.message
    assert not (target / "borrowed").exists()


def test_init_stamps_the_files_a_template_declares(
    synthetic_template: Callable[..., str], tmp_path: Path
) -> None:
    """End to end, because every other `files` test calls `copy_extras` directly.

    Those prove the rules; this proves `pnk init` reaches them and hands them the KB root it just
    created. Without it, `copy_extras` could be passed the wrong target — or stop being called at
    all — and the unit tests above would every one of them still pass.
    """
    name = synthetic_template(
        "declaring",
        versions={"1.0": MINIMAL_MANIFEST},
        current="1.0",
        files=["README.md", "reference/GLOSSARY.md"],
        extras={
            "README.md": "declared readme\n",
            "reference/GLOSSARY.md": "declared, and nested\n",
            "NOT-DECLARED.md": "never asked for\n",
        },
    )

    result = init(tmp_path / "kb", template_name=name, now="20260808 09:31")

    assert (result.root / "README.md").read_text(encoding="utf-8") == "declared readme\n"
    # Nested, so the writer must create the intermediate directory rather than skipping the entry.
    assert (result.root / "reference" / "GLOSSARY.md").read_text(encoding="utf-8") == (
        "declared, and nested\n"
    )
    assert not (result.root / "NOT-DECLARED.md").exists()
    # The historical pair is *not* implied once a template declares its own list.
    assert not (result.root / "eval" / "questions.yaml").exists()
