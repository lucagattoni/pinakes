"""`pnk init` — stamp a new KB from a template.

The whole job is to produce a directory that is already correct: a manifest whose ids are permanent,
a `docs/` to put things in, and a `.gitignore` that keeps `.pinakes/` out of the repository. That
last one matters more than it looks — publishing a KB publishes every sidecar, and the index and
ledger must never leave the machine (docs/DESIGN.md §4.7).
"""

import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

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

#: What the warning is actually about: the index, the spend ledger, and a deep transcript — the
#: first file under `.pinakes/` to hold the user's **verbatim question** (docs/DESIGN.md §4.7).
#: They are pathnames to ask git about, never files to look for; none of them exists at `init`
#: time, and `check-ignore` answers about a path whether or not anything is there.
GITIGNORE_PROBES = (
    ".pinakes/index.db",
    ".pinakes/ledger.jsonl",
    ".pinakes/deep/transcript.json",
)


def _ignored_by_git(root: Path) -> bool | None:
    """Whether git ignores every path in `GITIGNORE_PROBES`, or `None` when git cannot answer.

    **Asked of git rather than read out of `.gitignore`.** The text scan this replaces —
    `".pinakes/" not in gitignore.read_text()` — was wrong in both directions, measured 20260825:
    it warned about `.pinakes` and `.pin*`, which git *does* ignore, and stayed **silent** for
    `!.pinakes/` and a commented-out `#.pinakes/`, which git does *not*. The silent half is the
    one that matters: a commented-out line left the ledger and every deep transcript tracked, and
    said nothing. A scan also cannot see `.git/info/exclude`, the user's global excludes, or a
    parent repository's rules — git can, so git is asked.

    **The probes are descendants, never the bare directory.** `git check-ignore .pinakes` reports
    *not ignored* for the canonical `.pinakes/` pattern whenever the directory is absent from disk:
    a trailing slash only matches a path git can already see is a directory. At `init` time
    `.pinakes/` has never been created, so the bare query would answer "unprotected" for the very
    pattern this file writes. A path *inside* it carries the directory in its own name and answers
    correctly either way.

    **Every path must match, not merely one.** `check-ignore` exits 0 when *any* argument is
    ignored, so a `.gitignore` naming only `.pinakes/ledger.jsonl` would otherwise read as full
    protection while the index stayed tracked. Counting the matched paths is what distinguishes
    the two.
    """
    try:
        completed = subprocess.run(
            ["git", "check-ignore", *GITIGNORE_PROBES],
            cwd=root,
            capture_output=True,
            text=True,
        )
    except OSError:
        # git is not on PATH. `init` has never required it, and refusing to stamp a KB because a
        # version-control tool is missing would be a far worse failure than the one being fixed.
        return None
    if completed.returncode not in (0, 1):
        # 128 — not a git repository. There is no authority to consult, so there is no answer.
        return None
    matched = {line.strip() for line in completed.stdout.splitlines() if line.strip()}
    return len(matched) == len(GITIGNORE_PROBES)


def _gitignore_names_pinakes(text: str) -> bool:
    """Best effort for a directory that is not a git repository, where git cannot be asked.

    Deliberately small. It strips comments — the failure that let `#.pinakes/` read as protection
    — and accepts the directory with or without its trailing slash. It does **not** interpret
    globs, negations or precedence: a text scan that pretends to be git is precisely how the
    original defect happened, and outside a repository there is nothing yet to protect against.
    """
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.rstrip("/") == ".pinakes":
            return True
    return False


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

    # Asked after the file is on disk, whether it was adopted or just written, so git reads the
    # state the user will actually have. A KB stamped inside a repository whose rules negate
    # `.pinakes/` is unprotected however good the file this function wrote is.
    protected = _ignored_by_git(root)
    if protected is None:
        protected = _gitignore_names_pinakes(gitignore.read_text(encoding="utf-8"))
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
