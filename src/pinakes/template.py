"""Templates — the blueprint a KB is stamped from (docs/DESIGN.md §6.1).

Templates version independently of the package, so upgrading `pinakes` never silently re-chunks
someone's corpus. They are packaged inside the wheel and read through `importlib.resources`, so
nothing depends on the source tree being present.
"""

import re
import tomllib
from collections.abc import Sequence
from dataclasses import dataclass
from importlib import resources
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Any, cast

from jinja2 import StrictUndefined, Template, TemplateSyntaxError, UndefinedError

from pinakes.errors import TemplateError, TemplateNotInstalledError
from pinakes.manifest import Manifest
from pinakes.paths import lands_inside

PACKAGE = "pinakes.templates"
MANIFEST_TEMPLATE = "pinakes.toml.j2"
DEFAULT_TEMPLATE = "notes"
VERSIONS_DIR = "_versions"

_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*\Z")
_VERSION = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")

CONTEXT_KEYS: tuple[str, ...] = (
    "name",
    "kb_id",
    "template",
    "created",
    "embedding_provider",
    "embedding_model",
    "embedding_dim",
    "rerank_provider",
    "rerank_model",
)
"""Every variable this build can supply to a manifest template — the **union across versions**.

Not "the variables the current version uses". `render_manifest` renders under `StrictUndefined`, so
a variable a later version drops must keep being supplied or the *older archived* version stops
rendering — and it stops rendering on one side of a comparison only, which turns `pnk doctor` into
a traceback on a KB whose only fault is being old. A variable leaves a template; it does not leave
this tuple.

`tools/template_drift_gate.py` leg (vi) builds its context from exactly these keys, so an archived
version needing a variable outside the union is a red build rather than a user's crash.
"""


@dataclass(frozen=True, slots=True)
class TemplateInfo:
    name: str
    version: str
    description: str

    @property
    def reference(self) -> str:
        """`notes@1.0` — what the manifest records, so a later `pnk upgrade` can diff it."""
        return f"{self.name}@{self.version}"


def _unknown(name: str) -> TemplateNotInstalledError:
    # The narrow type, not `TemplateError`: `doctor` and `upgrade` both branch on it to tell a
    # template that is absent from one that is present and damaged, so widening the annotation
    # would let a raiser here silently stop being distinguishable there.
    return TemplateNotInstalledError(
        f"no template named {name!r}.",
        remedy=f"Available: {', '.join(available()) or '(none)'}.",
    )


def _root(name: str) -> Traversable:
    # A template name is **one path component**, checked before the join and not after. `joinpath`
    # happily accepts separators and `..`, so without this `describe("notes/../notes")` and
    # `describe("../templates/notes")` both succeed — measured, not theorised. That was harmless
    # only while every directory under the package root was a template; `_versions/` ends that,
    # because `--template notes/_versions/1.1` would stamp a KB from an archived version nobody
    # released. The pattern also excludes a leading `_`, which is what `available()` hides.
    if not _NAME.fullmatch(name):
        raise _unknown(name)
    try:
        root = resources.files(PACKAGE).joinpath(name)
    except ModuleNotFoundError as exc:  # pragma: no cover — packaging failure
        raise TemplateError(f"template package {PACKAGE} is missing.", remedy="Reinstall.") from exc
    if not root.is_dir():
        raise _unknown(name)
    return root


def available() -> list[str]:
    return sorted(
        entry.name
        for entry in resources.files(PACKAGE).iterdir()
        if entry.is_dir() and not entry.name.startswith("_")
    )


def _read_text(source: Traversable, *, reference: str, file: str) -> str:
    """Read one of a template's own files, turning a damaged install into a message.

    **Every read of a template's own files goes through here, and that is the point.** None of
    these exceptions is a `PinakesError`, so `cli.main` prints a stack trace instead of a remedy:
    a `_versions/<v>/` without its `pinakes.toml.j2` gives `FileNotFoundError`, an unreadable file
    `PermissionError`, a non-UTF-8 one `UnicodeDecodeError`. `pnk doctor` and `pnk upgrade` both
    reach every one of them, and neither is a command a user runs when things are going well.

    **Unreachable from a wheel this project ships** — `tools/template_drift_gate.py` would be red
    first — so this is message quality on a damaged or third-party install, not correctness. That
    is also why the remedy names reinstalling rather than a repair: a template's own files are not
    the user's to fix.

    `FileNotFoundError` is caught before `OSError` because it is one, and absence rather than state
    is the fact worth printing. `UnicodeDecodeError` is a `ValueError` and needs its own arm.
    """
    try:
        return source.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise TemplateError(
            f"template {reference} is missing {file}.",
            remedy="Its install is incomplete. Reinstall pinakes, or the template it came from.",
        ) from exc
    except UnicodeDecodeError as exc:
        raise TemplateError(
            f"template {reference}'s {file} is not valid UTF-8.",
            remedy="Its install is damaged. Reinstall pinakes, or the template it came from.",
        ) from exc
    except OSError as exc:
        # `strerror` alone, never the exception — `OSError.__str__` appends the filename it
        # carries, and that filename is an absolute path into wherever this build is installed.
        # `pnk doctor` is the command whose output is the natural thing to paste into an issue,
        # which is why it strips the KB root from every message it forwards; a template lives
        # *outside* the KB, so that helper deliberately leaves such a path alone and this is the
        # only place it can be kept out. The class name is the fallback: it names the failure
        # without naming the machine.
        raise TemplateError(
            f"template {reference}'s {file} cannot be read: {exc.strerror or type(exc).__name__}.",
            remedy="Check the file's permissions, or reinstall pinakes.",
        ) from exc


def _declaration(name: str) -> dict[str, Any]:
    """`template.toml`, parsed. Shared so `describe` and `declared_files` cannot disagree about it.

    Two readers of one file is two chances to handle a malformed one differently, and
    `tomllib.TOMLDecodeError` is not a `PinakesError` either — a stray bracket in a third-party
    template's declaration reached `cli.main` as a traceback from whichever of the two ran first.
    """
    raw = _read_text(_root(name).joinpath("template.toml"), reference=name, file="template.toml")
    try:
        return tomllib.loads(raw)
    except tomllib.TOMLDecodeError as exc:
        raise TemplateError(
            f"template {name}'s template.toml is not valid TOML: {exc}.",
            remedy="Its install is damaged. Reinstall pinakes, or the template it came from.",
        ) from exc


def describe(name: str) -> TemplateInfo:
    data = _declaration(name)
    return TemplateInfo(
        name=str(data.get("name", name)),
        version=str(data.get("version", "0")),
        description=str(data.get("description", "")),
    )


def render_context(manifest: Manifest) -> dict[str, Any]:
    """The one variable mapping both sides of a template comparison render through.

    **One context, rendered twice.** Two contexts would let a difference between the *contexts*
    appear as a difference between the *templates*, which is the one thing this report must never
    say. Everything below follows from that.

    **Every identity field comes from the KB's manifest, and `template` is the one that matters.**
    `pnk init` passes the *installed* reference (`init.py:75`) because at `init` time the recorded
    and installed references are the same string. They are not the same string here, and the
    obvious third choice — old side gets the recorded reference, new side gets the installed one —
    puts a `[kb] template` hunk in **every** report on **every** KB, which under T4's
    all-or-nothing conflict rule would make `--apply` refuse for every user who ever touched their
    `[kb]` block. Both sides therefore render the *recorded* reference and `[kb]` is byte-identical
    on both, so it can never produce a hunk.

    Two consequences, both of them the point rather than side-effects: a user's edit to a rendered
    variable (`provider = "fastembed"`) is identical on both sides and cannot appear in the diff,
    and a user's edit to a literal line (`final_k = 4`) never enters either side, because neither
    side is their file.

    `template` and `created` are optional in a manifest. Their fallback is `""` and it is
    unobservable by construction: the value is written to both sides or to neither.
    """
    return {
        "name": manifest.kb.name,
        "kb_id": str(manifest.kb.id),
        "template": manifest.kb.template or "",
        "created": manifest.kb.created or "",
        "embedding_provider": manifest.embedding.provider,
        "embedding_model": manifest.embedding.model,
        "embedding_dim": manifest.embedding.dim,
        "rerank_provider": manifest.rerank.provider,
        "rerank_model": manifest.rerank.model,
    }


#: What a TOML v1.0.0 basic string must escape, and the escape it must use. **Tab is deliberately
#: absent**: it is the one control character a basic string may carry raw, so escaping it would
#: rewrite a legal byte to no purpose. Every other character below U+0020, and U+007F, has no legal
#: raw form and is escaped by the `\uXXXX` fallback in `_toml_basic`.
#:
#: **That fallback would also produce valid TOML for `\b`, `\f`, `\n` and `\r`**, and the value
#: round-trips identically either way — so these four entries change nothing a parser can see,
#: only the bytes a human opens: `name = "a\nb"` rather than `name = "a\u000ab"`. They were four
#: lines no test and no mutant could distinguish until 20260903, found by a review pass applying
#: the standard this file had already applied to the `bool` exclusion.
_TOML_ESCAPES = {
    '"': '\\"',
    "\\": "\\\\",
    "\b": "\\b",
    "\f": "\\f",
    "\n": "\\n",
    "\r": "\\r",
}


def _toml_basic(value: object) -> object:
    """Make one interpolated value safe inside a TOML basic string; pass everything else through.

    Jinja calls this on the result of every `{{ ... }}` in the template, which is what makes it a
    fix to the *mechanism* rather than to one variable. `name` is the value that reached here from
    a user — `pnk init --name`, or the directory name via `root.name` — but the next template
    variable carrying user text inherits this without anyone remembering to, and that is the whole
    reason it lives here instead of beside the one call site (S4, in the sweep plan).

    **What passes through bare is an allow-list, and it is one entry long.** `int` — because
    `dim = {{ embedding_dim }}` is the only variable this build interpolates *outside* a quoted
    string, and `Manifest.embedding.dim` is an `int`. Escaping is a string operation on a string
    position; a bare `int` has neither. **Everything else is stringified and escaped**, which is
    the half a review pass found missing: the guard used to read *not a `str`*, so a `Path`
    carrying a quote went out raw and wrote the same unparseable manifest S4 exists to prevent.
    Jinja calls `str()` on whatever this returns, so declining to inspect a value is declining to
    make it safe.

    **`bool` is inside the allow-list, and excluding it was tried and measured out.** It is an
    `int` in Python, so `isinstance` admits it; `str(True)` is `True` where TOML's literal is
    `true`, which reads like a reason to escape it instead. It is not one: **this function escapes
    content and never adds quotes**, so a bool renders `True` from either branch — bare at
    `dim = {{ embedding_dim }}`, and inside the template's own quotes at `name = "{{ name }}"`.
    The exclusion had no observable effect at any interpolation in this file, which made it code
    no test could pin and a battery row that would have survived. It was removed for that reason.

    **Some values have no TOML representation at all, and those raise.** A lone surrogate
    (U+D800-U+DFFF) cannot appear in a basic string raw — the grammar admits `%x80-D7FF` and
    `%xE000-10FFFF` and skips the gap — and cannot appear escaped either, since `\\uXXXX` must name
    a Unicode scalar value. It reaches here routinely rather than exotically: POSIX decodes an
    invalid UTF-8 byte in `sys.argv` or in a directory name with `surrogateescape` (PEP 383), so
    `pnk init --name $'kb-\\xff'` and a non-UTF-8 directory name both produce one. Left alone it
    crashed `init` with a raw `UnicodeEncodeError` from `Path.write_text` **after** the manifest
    had been created and truncated — a zero-byte `pinakes.toml`, a directory `init` then refuses as
    *already a KB*, which is S4's own end state reproduced by S4's own fix. Raising here fires
    inside `render_manifest`, before `init` creates anything.

    **The message names the code point and never echoes the value.** A name that carries an
    unpaired surrogate can carry an ANSI escape beside it, and this message is printed to a
    terminal.

    **The region this cannot reach, stated rather than implied.** Escaping makes a value safe inside
    a basic string. It does not make a value safe interpolated into a *literal* string (`'...'`,
    which TOML gives no escapes at all), nor bare into a key or a number — a template doing either
    with user text is broken in a way no escape function can repair. **This build's own template
    uses three positions, not two, and the third went unnoticed until 20260903**: every variable
    lands inside a basic string except `embedding_dim`, which is bare, and `rerank_model`, which
    `notes/pinakes.toml.j2:39` *also* interpolates inside a **comment** —
    `# fitted_for = "{{ rerank_model }}@<revision>"`, where the quotes are decorative and TOML
    parses nothing at all. A value is safe there only because a newline is escaped and so cannot
    reach a live line: the guarantee at that position is carried by one entry of
    `_TOML_ESCAPES`, not by the position. A third-party template that arranges otherwise is
    outside what this can promise.
    """
    if isinstance(value, int):
        return value
    # `str()` on a `StrictUndefined` raises `UndefinedError`, which is what `_render` turns into a
    # message. Stringifying here does not swallow that; it is how the raise reaches the handler.
    text = value if isinstance(value, str) else str(value)
    out: list[str] = []
    for character in text:
        escape = _TOML_ESCAPES.get(character)
        if escape is not None:
            out.append(escape)
        elif "\ud800" <= character <= "\udfff":
            raise TemplateError(
                f"a value for this manifest holds U+{ord(character):04X}, an unpaired surrogate, "
                "which TOML cannot represent raw or escaped.",
                remedy="This is what an invalid UTF-8 byte becomes when Python decodes an argument "
                "or a filename. Pass a --name that is valid UTF-8, or rename the directory.",
            )
        elif character != "\t" and (character < " " or character == "\x7f"):
            # No legal raw form in a basic string, and no single-letter escape reserved for it.
            out.append(f"\\u{ord(character):04x}")
        else:
            out.append(character)
    return "".join(out)


def _render(source: str, context: dict[str, Any], *, name: str, version: str | None = None) -> str:
    """Render one manifest template, turning a missing variable into a message rather than a crash.

    `jinja2.UndefinedError` is not a `PinakesError`, so without this `cli.main` prints a traceback.
    `CONTEXT_KEYS` covers every version this build ships — so the templates in the wheel cannot
    reach here — but a third-party template, or an archived version that arrived on the machine
    some other way, can need a variable no union contains. That is a message, not a stack trace.

    The reference is assembled in the `except` branch and nowhere else: naming the version costs a
    second file read, and the successful render is the path that runs.
    """
    try:
        return Template(
            source,
            undefined=StrictUndefined,
            keep_trailing_newline=True,
            finalize=_toml_basic,
        ).render(**context)
    except TemplateSyntaxError as exc:
        # Raised by `Template(...)`, not by `render` — an unclosed `{{` is a fact about the file
        # rather than about the context, so it says the file is damaged rather than that a variable
        # is missing. Caught here because the compile and the render are one expression, and
        # splitting them to give each its own `try` would buy nothing.
        #
        # **The version is not looked up when it is unknown**, unlike the arm below, which resolves
        # it through `describe`. This branch has already established that the install is damaged,
        # and `describe` re-reads `template.toml` — so on an install damaged in both files it would
        # raise its own error from inside this handler and replace a precise *"not valid Jinja"*
        # with a *"missing template.toml"* naming the wrong file. A reference without a version is
        # worth more than a message about the wrong problem.
        reference = f"{name}@{version}" if version is not None else name
        raise TemplateError(
            f"template {reference} is not valid Jinja: {exc.message} (line {exc.lineno}).",
            remedy="Its install is damaged. Reinstall pinakes, or the template it came from.",
        ) from exc
    except UndefinedError as exc:
        reference = f"{name}@{describe(name).version if version is None else version}"
        raise TemplateError(
            f"{reference} needs a variable this build does not supply: {exc.message}",
            remedy=f"This build of Pinakes cannot render {reference}. It supplies "
            f"{', '.join(CONTEXT_KEYS)}. A template needing anything else was written for a "
            "different build.",
        ) from exc


def render_manifest(name: str, context: dict[str, Any]) -> str:
    """Render `pinakes.toml`. `StrictUndefined`: a missing variable fails here, not at read time."""
    source = _read_text(
        _root(name).joinpath(MANIFEST_TEMPLATE), reference=name, file=MANIFEST_TEMPLATE
    )
    return _render(source, context, name=name)


def version_key(version: str) -> tuple[str, ...]:
    """Order versions the way a human reads them: `1.2` < `1.9` < `1.10`.

    A plain string sort puts `1.10` before `1.9`, which would make `archived_versions`' "oldest
    first" a lie the moment a template reaches its tenth revision. Numeric segments are zero-padded
    so they compare by magnitude; a non-numeric segment is prefixed with `~` (above every digit in
    ASCII) so it sorts after every number rather than interleaving with them.
    """
    return tuple(
        part.rjust(12, "0") if part.isdigit() else "~" + part for part in version.split(".")
    )


def archived_versions(name: str) -> list[str]:
    """Every version of `name` whose content is frozen under `_versions/`, oldest first.

    A KB records only a reference (`notes@1.1`), never the content it was stamped from, so the
    archive is the only thing that can say what that reference *meant*. Empty when the template
    has no archive at all — a third-party template need not carry one.
    """
    root = _root(name).joinpath(VERSIONS_DIR)
    if not root.is_dir():
        return []
    return sorted((entry.name for entry in root.iterdir() if entry.is_dir()), key=version_key)


def archived_root(name: str, version: str) -> Traversable:
    """The frozen directory for one version. Raises `TemplateError` naming it when absent.

    The version is validated as its own path component for the same reason the name is: it is
    joined onto a path, and it reaches here from a KB's manifest — a file Pinakes does not write.
    """
    root = _root(name)
    if not _VERSION.fullmatch(version):
        raise TemplateError(
            f"{name}@{version} is not a version this build can read.",
            remedy="A template version is one path component.",
        )
    archived = root.joinpath(VERSIONS_DIR).joinpath(version)
    if not archived.is_dir():
        known = ", ".join(archived_versions(name)) or "(none)"
        raise TemplateError(
            f"{name}@{version} is not archived in this build.",
            remedy=f"Archived versions of {name}: {known}.",
        )
    return archived


def render_archived(name: str, version: str, context: dict[str, Any]) -> str:
    """`render_manifest`'s archived counterpart — what `pnk upgrade` diffs against.

    Rendered rather than read, because the archived file is a template too: comparing a rendered
    manifest against an unrendered `.j2` would report every `{{ variable }}` as a difference.
    """
    source = _read_text(
        archived_root(name, version).joinpath(MANIFEST_TEMPLATE),
        reference=f"{name}@{version}",
        file=MANIFEST_TEMPLATE,
    )
    return _render(source, context, name=name, version=version)


def cannot_compare(missing: Sequence[str], name: str, archived: Sequence[str]) -> tuple[str, str]:
    """The `(detail, remedy)` every surface prints when a version's content is not in the archive.

    **Here rather than in either caller, because two surfaces say it and they must say the same
    thing.** `pnk doctor` reports it as a `WARN` row and `pnk upgrade` as its own outcome; the two
    lived as byte-identical copies for one increment, with nothing that would notice if one were
    reworded. Two surfaces disagreeing about one KB is the defect class this release exists to
    remove, so the wording is a fact with one home like any other.

    **It is the path 100% of today's KBs take, so it is written for someone who did nothing
    wrong.** `notes@1.0` is deliberately not archived — it denotes eleven different template
    contents, and a diff computed from the wrong base is worse than no diff — and this is what they
    get instead. It promises nothing a release *cannot* keep: an unarchived version's content
    is gone, not pending.
    """
    shipped = ", ".join(f"{name}@{version}" for version in archived)
    return (
        f"cannot compare: {' and '.join(missing)} "
        f"{'is' if len(missing) == 1 else 'are'} not in this build's archive",
        f"Nothing is wrong with your KB and nothing needs changing. A manifest records a version "
        f"string, never the content that version meant, and this build ships the content of "
        f"{shipped or 'no version of this template'} — so there is no baseline to diff against, "
        f"and there will not be a later one: an unarchived version's content is gone, not pending. "
        f"To see what moved, compare it by hand: run `pnk init` on a throwaway directory and diff "
        f"its pinakes.toml against yours. A KB stamped from "
        # `archived[0]`, the **oldest** archived version, because the sentence says *or later*.
        # `[-1]` names the newest and reads as a promise that excludes every version between —
        # true while one version is archived, false and user-facing from the next bump onward.
        f"{f'{name}@{archived[0]}' if archived else 'an archived version'} or later is compared "
        f"automatically.",
    )


HISTORICAL_FILES: tuple[str, ...] = ("README.md", "eval/questions.yaml")
"""What `copy_extras` copied before a template could declare it, and what an absent `files` means.

**Absent is these two, never none.** Every template that exists today declares nothing — `notes`
included — so reading an absent key as an empty list would stop stamping a README and a starter
golden set into every new KB, and would do it silently. It also means no third-party template
written against an earlier build changes behaviour by standing still.
"""


def declared_files(name: str) -> tuple[str, ...]:
    """The files `name` says it writes into a KB, validated as a declaration rather than as a path.

    **What is checked here is what can be judged without a target**: the shape of the value, and the
    version archive. Whether an entry *lands* inside a KB depends on the KB — a symlinked directory
    in the target is a fact about the target, not about the template — so `copy_extras` checks that
    against the real one.

    **`_versions` is refused as a path component, and this is the increment where such a rule can
    first fail.** While `copy_extras` iterated a hardcoded pair, no archive path was reachable
    whatever the archive held, and a test asserting otherwise was satisfied by the hardcoding rather
    than by any rule. The moment the list is read from `template.toml`, a template can declare
    `_versions/1.0/README.md` — and containment would **pass** it, because it lands inside the
    target. Containment is the wrong instrument here: it measures escape, not provenance. An
    archived version is the frozen record of what a reference once meant, so copying it into a KB
    would stamp content from a version nobody released under the name of one they did.
    """
    data = _declaration(name)
    if "files" not in data:
        return HISTORICAL_FILES

    # Narrowed element by element rather than with `all(isinstance(...))`: `tomllib` returns `Any`,
    # so the comprehension's item type stays unknown under pyright strict and the list would be
    # `list[str]` only by assertion. Building the typed list is the narrowing.
    declared: object = data["files"]
    shape = TemplateError(
        f"template {name} declares a `files` that is not a list of strings.",
        remedy='`files = ["README.md", "eval/questions.yaml"]` — paths relative to the KB.',
    )
    if not isinstance(declared, list):
        raise shape

    entries: list[str] = []
    for item in cast(list[object], declared):
        if not isinstance(item, str):
            raise shape
        entries.append(item)

    for entry in entries:
        if not entry or Path(entry).is_absolute():
            raise TemplateError(
                f"template {name} declares {entry!r}, which is not a relative path.",
                remedy="Every `files` entry is relative to the KB root.",
            )
        if VERSIONS_DIR in Path(entry).parts:
            raise TemplateError(
                f"template {name} declares {entry!r}, which names the version archive.",
                remedy=(
                    f"A template cannot copy anything out of {VERSIONS_DIR}/. What is archived "
                    "there is the frozen content of a released version, kept so `pnk upgrade` can "
                    "say what a recorded reference meant — never content to stamp into a KB."
                ),
            )
    return tuple(entries)


def validate_extras(name: str, target: Path) -> tuple[str, ...]:
    """Every check `copy_extras` makes, with nothing written. Returns the validated entries.

    **Separated so `pnk init` can run it before it creates anything** (open-corrections item 4,
    D-18). `init` wrote `pinakes.toml`, `docs/` and `.gitignore` and *then* called `copy_extras`,
    so a template whose declaration is refused left a directory that is almost a KB — and a second
    `pnk init` then refuses it as one.

    **`target` need not exist**, which is what makes the hoist possible at all and is worth stating
    because the item it closes assumed the opposite. `lands_inside` resolves the *parent* and
    Python's `resolve()` is non-strict, so containment is decidable against a directory that has
    not been created: measured against a path never created, `README.md` lands inside and
    `../escape.md` does not.

    **This is "validated before writing", never "atomic".** A symlinked *ancestor* of the target
    can change between this call and the write, and nothing here closes that. The guarantee is that
    a refusal `init` can foresee happens before the first byte, not that the filesystem is frozen.
    """
    root = _root(name)
    anchor = target.resolve()
    entries = declared_files(name)

    for relative in entries:
        try:
            inside = lands_inside(anchor, target, relative)
        except (ValueError, OSError) as exc:
            raise TemplateError(
                f"template {name} declares {relative!r}, which cannot be written: {exc}",
                remedy="Correct the template's `files`.",
            ) from exc
        if not inside:
            raise TemplateError(
                f"template {name} declares {relative!r}, which writes outside the KB.",
                remedy=(
                    "Every `files` entry must land inside the KB being created. An entry that "
                    "walks out writes into a directory the user never pointed pinakes at."
                ),
            )
        # **The source side of the same question, and it is a second layer rather than the same one
        # twice.** The check above stops an entry *writing* outside the KB; this one stops it
        # *reading* outside the template. A symlinked directory in the template tree points wherever
        # it likes on the machine, and the file it names would be copied **into** the KB — which for
        # a KB that is then committed and published is the more expensive direction of the two.
        # Neither layer catches the other's case: an escaping destination lands inside the template,
        # and an escaping source lands inside the target.
        #
        # Guarded on `Path` because `importlib.resources` hands back a `Traversable`, which for a
        # zip-imported package has no symlinks to follow and no `resolve()` to follow them with. A
        # wheel installs unpacked, so the real path is the one users get.
        if isinstance(root, Path) and not lands_inside(root.resolve(), root, relative):
            raise TemplateError(
                f"template {name} declares {relative!r}, which reads outside the template.",
                remedy=(
                    "Every `files` entry must name a file inside the template's own directory. An "
                    "entry that walks out copies something the template does not own into the KB."
                ),
            )
    return entries


def copy_extras(
    name: str, target: Path, *, validated: Sequence[str] | None = None
) -> tuple[list[Path], list[Path]]:
    """Copy everything a KB should own: the template's README and its starter golden set.

    Returns `(written, adopted)` — the second being files that were **already there and left
    exactly as they are**. A directory worth adopting usually has a `README.md` already, and it is
    the user's; replacing it with a template's would be destroying the thing they wrote to make
    room for boilerplate.

    **Every entry is checked before any entry is written**, and since D-18 the checking is
    `validate_extras`, called from here when the caller has not already run it. A template whose
    second declaration escapes would otherwise leave the first one written into a KB that then
    fails to be created — the partial state `pnk init` has no way to describe.

    **`validated` exists so `init` does not check twice, and defaults to checking anyway.** `init`
    must validate long before it copies — that is the whole of D-18 — but a second caller that
    simply calls `copy_extras` must not silently get an unchecked copy. One rule, one
    implementation, and the only way to skip it is to have already run it.

    **A template is packaged data, which is not the same as trusted data.** `pnk init --template`
    names whatever is installed, and that can have arrived from anywhere, so the declaration is
    checked against the target it will actually be written into rather than assumed well-formed.
    """
    root = _root(name)
    entries = tuple(validated) if validated is not None else validate_extras(name, target)

    written: list[Path] = []
    adopted: list[Path] = []
    for relative in entries:
        source = root
        for part in Path(relative).parts:
            source = source.joinpath(part)
        if not source.is_file():
            continue
        destination = target / relative
        if destination.exists():
            adopted.append(destination)
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        body = _read_text(source, reference=name, file=relative)
        destination.write_text(body, encoding="utf-8")
        written.append(destination)
    return written, adopted
