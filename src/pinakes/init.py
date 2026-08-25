"""`pnk init` — stamp a new KB from a template.

The whole job is to produce a directory that is already correct: a manifest whose ids are permanent,
a `docs/` to put things in, and a `.gitignore` that keeps `.pinakes/` out of the repository. That
last one matters more than it looks — publishing a KB publishes every sidecar, and the index and
ledger must never leave the machine (docs/DESIGN.md §4.7).
"""

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from pinakes import template
from pinakes.ci import WORKFLOW_PATH, write_workflow
from pinakes.errors import InitError
from pinakes.ids import KbId, mint_kb_id
from pinakes.manifest import MANIFEST_NAME

GITIGNORE = """\
# Generated index, spend ledger and caches. Disposable: `pnk sync --rebuild` recreates them.
# Keeping this ignored is what stops an index or a ledger ever leaving your machine.
.pinakes/
"""

#: How long to wait for git. `check-ignore` refreshes the index, and refreshing the index runs the
#: `core.fsmonitor` hook — a wedged Watchman daemon makes it block forever. `init` has already
#: written `pinakes.toml` by the time this runs, so a hang leaves a half-made KB that the next
#: `pnk init` refuses as "already a KB". Five seconds, then answer from the fallback.
GIT_TIMEOUT_SECONDS = 5

#: Variables by which git chooses a *different repository* than the one `cwd` names. git exports
#: them to every hook it runs, so `pnk init` from a hook, a `rebase --exec`, or any wrapper that
#: sets them would otherwise be answered by an unrelated tree — and answered *confidently*.
GIT_LOCATION_VARIABLES = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_COMMON_DIR",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_CEILING_DIRECTORIES",
)


def _probe_paths() -> tuple[str, ...]:
    """Four pathnames under `.pinakes/` that together ask *is an arbitrary path in there ignored*.

    **Named files were not a cover, and reporting on three of them was a regression.** The first
    version of this probed `index.db`, `ledger.jsonl` and `deep/transcript.json`. Measured 20260825
    against ground truth (`git add -A` then `git ls-files --cached`, so the oracle does not go
    through `check-ignore` at all): a `.gitignore` carrying `*.db` and `*.json` — an ordinary thing
    to write — ignores all three and leaves `index.db-wal` staged, which in WAL mode holds
    megabytes of verbatim document text. The substring test this replaced *warned* there. A check
    that answers about three filenames cannot answer a question about a directory.

    So the probes are **opaque**: a random token no realistic pattern targets, at the top level and
    nested, which only a rule covering the directory itself can match. Two more sit under
    `cache/extract/` and `deep/` — the subtrees holding extracted document text and the user's
    verbatim questions — because `.pinakes/*` with a re-include (`!.pinakes/cache`) ignores both
    opaque probes and tracks the cache regardless. That case is why four rather than two: measured,
    the two-probe set still got it wrong.
    """
    token = uuid4().hex
    return (
        f".pinakes/{token}",
        f".pinakes/{token}/{token}",
        f".pinakes/cache/extract/{token}",
        f".pinakes/deep/{token}",
    )


def _ask_git(arguments: list[str], cwd: Path) -> subprocess.CompletedProcess[str] | None:
    """Run git for an answer, or `None` if it could not give one.

    Every argument here is a failure this check met in review rather than a precaution:
    `stdin=DEVNULL` so a helper git spawns cannot consume the terminal's input or block on an
    invisible prompt; `errors="replace"` because `text=True` alone decodes strictly and raises
    *inside* `subprocess.run`, past any `except OSError`; the scrubbed environment so git answers
    about this directory's repository and not one an ambient variable names.
    """
    environment = {k: v for k, v in os.environ.items() if k not in GIT_LOCATION_VARIABLES}
    try:
        return subprocess.run(
            ["git", *arguments],
            cwd=cwd,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            stdin=subprocess.DEVNULL,
            timeout=GIT_TIMEOUT_SECONDS,
            env=environment,
        )
    except (OSError, subprocess.SubprocessError):
        return None


def _all_probes_ignored(cwd: Path, probes: tuple[str, ...]) -> bool | None:
    """Whether git ignores every probe, or `None` when it did not answer.

    **Exit 1 is only an answer when git said nothing on stderr.** `check-ignore` exits 1 for
    anything short of a fatal, including *"could not open .gitignore"* — a warning. Reading that as
    an authoritative "not ignored" would be a guess wearing an exit code.
    """
    completed = _ask_git(["check-ignore", *probes], cwd)
    if completed is None or completed.returncode not in (0, 1):
        return None
    if completed.returncode == 1 and completed.stderr.strip():
        return None
    matched = {line.strip() for line in completed.stdout.splitlines() if line.strip()}
    return len(matched) == len(probes)


def _ignored_by_git(root: Path, gitignore: Path) -> bool | None:
    """Whether git would keep every path under `.pinakes/` out of the repository.

    **Asked of git rather than read out of `.gitignore`.** The text scan this replaces —
    `".pinakes/" not in gitignore.read_text()` — was wrong in both directions, measured 20260825:
    it warned about `.pinakes` and `.pin*`, which git *does* ignore, and stayed **silent** for
    `!.pinakes/` and a commented-out `#.pinakes/`, which git does *not*. The silent half is the one
    that matters — a commented-out line left the ledger and every deep transcript tracked, and said
    nothing. A scan also cannot see `.git/info/exclude`, the user's global excludes, or a parent
    repository's rules. git can, so git is asked.

    **Outside a repository, git is still asked — in a scratch one.** A KB is often stamped before
    `git init`, and there the hand-rolled fallback got negation *silently* wrong: `.pinakes/`
    followed by `!.pinakes/` read as protection, the very input this module's own in-repo test
    asserts must warn. Copying the `.gitignore` into a throwaway repository and running the
    identical probes keeps one definition of the answer instead of two that can disagree. The text
    fallback below is now reached only when there is no `git` at all.
    """
    verdict = _all_probes_ignored(root, probes := _probe_paths())
    if verdict is not None:
        return verdict

    inside = _ask_git(["rev-parse", "--is-inside-work-tree"], root)
    if inside is None:
        return None
    if inside.returncode == 0 and inside.stdout.strip() == "true":
        # A real repository that git could not answer about. Inventing a verdict from a scratch
        # repo would silently drop its parent rules, its excludes and its index.
        return None

    with tempfile.TemporaryDirectory() as scratch:
        if _ask_git(["init", "-q"], Path(scratch)) is None:
            return None
        if gitignore.exists():
            shutil.copyfile(gitignore, Path(scratch) / ".gitignore")
        return _all_probes_ignored(Path(scratch), probes)


def _read_or_empty(path: Path) -> str:
    """The file's text, or `""` if it cannot be read.

    `init` has already written `pinakes.toml` by the time this runs, so raising here leaves a
    half-made KB that the next `pnk init` refuses as "already a KB". A `.gitignore` holding one
    latin-1 byte — `# café notes` is enough — used to do exactly that, as an unhandled
    `UnicodeDecodeError` rather than an `InitError` with a remedy. Unreadable means unproven, and
    unproven means warn, which is the safe direction.
    """
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _gitignore_names_pinakes(text: str) -> bool:
    """Last resort for a machine with no `git` installed at all.

    Deliberately small, and the smallness is the mechanism. It asks whether a **whole line** names
    the directory, with or without its trailing slash — so `#.pinakes/` cannot match, not because
    comments are stripped but because a commented line is not that line. That is the failure the
    substring test had: `".pinakes/" in text` asks whether the string appears *anywhere*, which a
    comment satisfies. A mutation pass on 20260825 proved the point by deleting an explicit
    comment-skip from this loop and finding every test still green — the skip was never what
    excluded a comment.

    It does **not** interpret globs, negations or precedence, and it is wrong about `/.pinakes/`
    and `.pinakes/**`, which git honours. That is accepted: `init` has never required git, refusing
    to stamp a KB over a missing version-control tool would be a worse failure than the one this
    fixes, and a text scan that pretends to be git is how the original defect happened.
    """
    return any(line.strip().rstrip("/") == ".pinakes" for line in text.splitlines())


DEFAULT_EMBEDDING = ("sentence-transformers", "BAAI/bge-small-en-v1.5", 384)
DEFAULT_RERANK = ("sentence-transformers", "BAAI/bge-reranker-base")

BACKENDS: dict[str, tuple[tuple[str, str, int], tuple[str, str]]] = {
    "st": (DEFAULT_EMBEDDING, DEFAULT_RERANK),
    "light": (
        ("fastembed", "BAAI/bge-small-en-v1.5", 384),
        ("fastembed", "BAAI/bge-reranker-base"),
    ),
}
"""What `--backend` stamps into `[embedding]` and `[rerank]` — one entry per install extra (D-20).

**Both blocks together, because that is the edit users were making by hand.** Every real KB stamped
from `notes` changed the provider in *both*, for one reason (a `[light]` install), and
`docs/GUIDE.md` documents doing it manually as the normal path. Two of two is not a sample, but it
is the whole population that exists.

**An explicit flag, never detection.** `importlib.util.find_spec` can see which extra is installed
— `embed.py` already uses it to name an alternative — and the GUIDE's claim that `init` "cannot see"
is simply false. Stamping what it sees was rejected anyway: `pinakes.toml` is portable and
committed, so writing a machine-local fact into it bakes the author's install into a file
collaborators read, and the KB then fails for whoever has the other extra. A flag records a
*choice*; sniffing records an *accident*.

The default is unchanged: omit `--backend` and you get `st`, exactly as before.
"""


@dataclass(frozen=True, slots=True)
class InitResult:
    root: Path
    kb_id: KbId
    template: str
    created: list[Path]
    workflow: Path | None = None
    """The GitHub Actions workflow `--ci` wrote, or `None`. Returned rather than merely created so
    the CLI can say, in one line, that it forces the free extractor (§6.3)."""
    adopted: list[Path] = field(default_factory=list[Path])
    """Files `init` would have written that were already there, and were **left exactly as they
    are**. Adopting a directory that has content is the point (a repo has a `README.md` and a
    `.gitignore` before it is ever a KB), and overwriting either would be destroying the user's
    work to make room for a template's."""
    gitignore_unprotected: bool = False
    """An existing `.gitignore` that does not mention `.pinakes/`.

    Reported loudly rather than fixed: `.gitignore` is the one skipped file whose *absence of
    content* has a consequence — an index and a spend ledger that can leave the machine. Appending
    to it would be editing a file this tool does not own, so the CLI names the line to add
    instead.
    """


def init(
    root: Path,
    *,
    name: str | None = None,
    template_name: str = template.DEFAULT_TEMPLATE,
    now: str | None = None,
    ci: bool = False,
    backend: str = "st",
) -> InitResult:
    info = template.describe(template_name)
    root = root.resolve()
    _check_target(root, ci=ci)

    # **Everything that can be refused is refused here, before the first byte** (D-18,
    # open-corrections item 4). `init` used to write `pinakes.toml`, `docs/` and `.gitignore` and
    # only then call `copy_extras`, so a template whose `files` declaration is illegal — it names
    # `_versions/`, writes outside the KB, or reads outside the template — raised against a
    # directory that was already almost a KB, which a second `pnk init` then refuses *as* one.
    #
    # `root` does not exist yet and does not need to: `lands_inside` resolves the parent and
    # `resolve()` is non-strict, so containment is decidable against a directory nobody has
    # created. The item this closes assumed otherwise and rejected the fix on that basis.
    #
    # `--ci` has behaved this way since `test_ci_refuses_an_existing_workflow_before_creating_
    # anything` moved its refusal; this makes the same guarantee uniform rather than inventing one.
    declared = template.validate_extras(template_name, root)

    stamp = now or datetime.now(UTC).strftime("%Y%m%d %H:%M")
    kb_id = mint_kb_id()
    if backend not in BACKENDS:
        raise InitError(
            f"{backend!r} is not a backend this build can stamp.",
            remedy=f"Choose one of: {', '.join(sorted(BACKENDS))}.",
        )
    (provider, model, dim), (rerank_provider, rerank_model) = BACKENDS[backend]

    rendered = template.render_manifest(
        template_name,
        {
            "name": name or root.name,
            "kb_id": kb_id,
            "template": info.reference,
            "created": stamp,
            "embedding_provider": provider,
            "embedding_model": model,
            "embedding_dim": dim,
            "rerank_provider": rerank_provider,
            "rerank_model": rerank_model,
        },
    )

    root.mkdir(parents=True, exist_ok=True)
    (root / "docs").mkdir(exist_ok=True)
    manifest_path = root / MANIFEST_NAME
    manifest_path.write_text(rendered, encoding="utf-8")

    adopted: list[Path] = []
    gitignore = root / ".gitignore"
    if gitignore.exists():
        adopted.append(gitignore)
    else:
        gitignore.write_text(GITIGNORE, encoding="utf-8")

    # **Only for a `.gitignore` that was already here.** The first draft ran this unconditionally
    # and justified it with "a repository whose rules negate `.pinakes/` beats the file we wrote" —
    # which review showed cannot happen: git resolves by directory depth, so the `.gitignore` this
    # function just wrote in the KB wins over any ancestor. What widening it *did* reach was a path
    # already in the index, where `check-ignore` reports not-ignored and the warning would tell the
    # user to add a line their file already has. Narrowed back: this increment fixes the existing
    # check's correctness, and does not change when it fires.
    gitignore_unprotected = False
    if gitignore in adopted:
        protected = _ignored_by_git(root, gitignore)
        if protected is None:
            protected = _gitignore_names_pinakes(_read_or_empty(gitignore))
        gitignore_unprotected = not protected

    extras, extras_adopted = template.copy_extras(template_name, root, validated=declared)
    adopted.extend(extras_adopted)

    created = [manifest_path, root / "docs", *extras]
    if gitignore not in adopted:
        created.insert(1, gitignore)
    workflow = write_workflow(root) if ci else None
    if workflow is not None:
        created.append(workflow)
    return InitResult(
        root=root,
        kb_id=kb_id,
        template=info.reference,
        created=created,
        workflow=workflow,
        adopted=adopted,
        gitignore_unprotected=gitignore_unprotected,
    )


def _check_target(root: Path, *, ci: bool = False) -> None:
    if (root / MANIFEST_NAME).exists():
        raise InitError(
            f"{root} is already a KB.",
            remedy="A KB's id is permanent; re-initialising would mint a new one and orphan "
            "every inbound link.",
        )
    if root.exists() and not root.is_dir():
        raise InitError(f"{root} is not a directory.", remedy="Choose another path.")
    # **No emptiness test.** It refused every real adoption — create the repo, clone it, `init`
    # inside it — because a `.git`, a `README.md` and a `pyproject.toml` are already "not empty",
    # and *"clear this one first"* is an alarming thing to read about a directory holding the
    # documents you meant to index. Hit three times independently before it was changed
    # (20260805). What replaces it is narrower and stronger: `init` never overwrites a file that
    # is already there, so there is nothing left for an emptiness test to protect.
    #
    # The accepted cost, stated when the decision was taken: a typo in the path now creates a KB
    # in a directory full of unrelated files rather than refusing. That is recoverable — delete
    # `pinakes.toml` — where overwriting a README is not.
    #
    # **`--ci` is the one file that is refused rather than adopted, and it is checked here rather
    # than where it is written.** `write_workflow` already refuses to overwrite a hand-edited
    # workflow, but it runs *after* `pinakes.toml` exists — so without this the refusal would
    # leave a half-made KB that the next `pnk init` rejects as "already a KB", with no way
    # forward but deleting a manifest the user did not ask for. Skipping it silently is not the
    # alternative: `--ci` is an explicit request, and honouring it by doing nothing is worse than
    # refusing.
    if ci and (root / WORKFLOW_PATH).exists():
        raise InitError(
            f"{root / WORKFLOW_PATH} already exists.",
            remedy="Delete it first if you want the generated workflow; it is never overwritten. "
            "Nothing has been created — re-run without `--ci` to initialise the KB and keep your "
            "workflow.",
        )
