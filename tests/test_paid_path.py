"""The paid-path allowlist gate (plans/20260727_1543-v0.2.md, I7a) — proved in both directions.

`docs/INVARIANTS.md` calls "the free path stays free" non-negotiable. v0.1 promised a CI grep
enforcing it under a heading with no increment number, nobody owned it, and it never shipped
(docs/RETROSPECTIVES.md, 20260727 15:35). This increment's whole subject is that gate, so its own
principle applies to every gate in it: **a gate only ever observed passing is a gate nobody has
tested.** Each of the three gates below therefore has a test that makes it *fail*.

Gates 1 and 2 are exercised through `tools/paid_path_gate.py` as a subprocess — the same artifact
`check.sh` and CI run, rather than an in-process re-implementation that could agree with itself
while the shipped script does something else.

Gate 3 (`anthropic` must never reach `[project.dependencies]`) is I1's, already owned by
`test_packaging.py::test_extractors_stay_extras`, and is not duplicated here.

Gate 4 is the one that actually matters, and it is a runtime check rather than a grep: no spelling
of an import can hide from `sys.modules`.
"""

import json
import subprocess
import sys
from importlib.util import find_spec
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
GATE_SCRIPT = REPO_ROOT / "tools" / "paid_path_gate.py"
FREE_PATH_RUN = REPO_ROOT / "tests" / "free_path_run.py"

# The modules that cost money, as `sys.modules` spells them. Kept in step with
# `tools/paid_path_gate.py`'s PAID_CLIENTS minus the regex escaping —
# `test_the_two_paid_client_lists_agree` is what stops the two drifting apart.
#
# **`google.generativeai` in full, never the bare root.** Matching on `name.split(".")[0]` would
# make `google.protobuf` a paid client, and protobuf arrives transitively with onnxruntime, grpc
# and half the ML ecosystem — so the flagship safety gate would fail on a platform where fastembed
# happens to pull it in, for a reason having nothing to do with spending money. The repair a future
# maintainer reaches for when a safety gate cries wolf is to weaken the gate.
PAID_CLIENT_MODULES = ("anthropic", "openai", "cohere", "mistralai", "google.generativeai")


def _is_paid_module(name: str) -> bool:
    """`anthropic` and `anthropic.types` are the client; `anthropic_shim` and `google.protobuf`
    are not. Submodule matching is on a dotted-prefix boundary, never `startswith` on the raw
    string, which would swallow any module whose name merely begins with a paid one."""
    return any(name == paid or name.startswith(f"{paid}.") for paid in PAID_CLIENT_MODULES)


def _run_gate(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(GATE_SCRIPT), "--root", str(root)],
        capture_output=True,
        text=True,
    )


def _make_root(tmp_path: Path, *, allowlist: str, files: dict[str, str]) -> Path:
    """A synthetic repo root: a `src/` tree and an allowlist, which is all the gate reads."""
    root = tmp_path / "repo"
    for relative, body in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    (root / ".paid-path-allowlist").write_text(allowlist, encoding="utf-8")
    return root


# --------------------------------------------------------------------------------------------
# Gate 1 — every listed path exists
# --------------------------------------------------------------------------------------------


#: Exactly the modules permitted to import a paid client, hard-coded rather than read from the
#: allowlist: a test that reads the same file it checks would pass on any content at all.
#:
#: **Two, and the second one is the last.** E3 adds `deep/client.py` — `pnk ask --deep` is the final
#: paid entry point the design has (docs/DESIGN.md §1). `src/pinakes/paid.py`, which both of them
#: use, is deliberately absent: it holds the rules a paid call obeys and imports no client, so gate
#: 2 scans it like any other file.
EXPECTED_ALLOWLIST = ("src/pinakes/extract/claude.py", "src/pinakes/deep/client.py")


def test_the_allowlist_matches_the_source_tree() -> None:
    """Gate 1 against the real repo, and against the *shipped* list.

    The count is asserted as well as the exit code, because gate 1 passing says only that every
    listed path exists — it says nothing about a path being quietly *added*. Widening the
    allowlist is how a gate like this one dies, so it takes an edit here too.
    """
    result = _run_gate(REPO_ROOT)
    assert result.returncode == 0, result.stderr
    assert f"{len(EXPECTED_ALLOWLIST)} exempt path(s)" in result.stdout
    # Parsed here rather than through the gate's own `read_allowlist`: borrowing the parser under
    # test would let a parser bug and a content change cancel out.
    listed = tuple(
        line.strip()
        for line in (REPO_ROOT / ".paid-path-allowlist").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    )
    assert listed == EXPECTED_ALLOWLIST


def test_a_stale_allowlist_entry_fails_gate_1(tmp_path: Path) -> None:
    """The failure gate 1 exists for: a module was renamed and its exemption stayed behind.

    Without this, gate 1 is only ever observed passing against an empty list — which passes
    whether or not the existence check is implemented at all.
    """
    root = _make_root(
        tmp_path,
        allowlist="src/pkg/renamed_away.py\n",
        files={"src/pkg/still_here.py": "x = 1\n"},
    )
    result = _run_gate(root)
    assert result.returncode == 1
    assert "does not exist" in result.stderr
    assert "renamed_away.py" in result.stderr


def test_an_allowlist_entry_outside_src_fails_gate_1(tmp_path: Path) -> None:
    """An entry gate 2 would never consult reads like an exemption and grants none. Silent
    inertness is worse than absence: the reader believes a file is covered when nothing is."""
    root = _make_root(
        tmp_path,
        allowlist="tests/helper.py\n",
        files={"src/pkg/a.py": "x = 1\n", "tests/helper.py": "y = 2\n"},
    )
    result = _run_gate(root)
    assert result.returncode == 1
    assert "must live under src/" in result.stderr


def test_a_directory_entry_fails_gate_1(tmp_path: Path) -> None:
    """`src/pinakes/extract/` in the allowlist must not exempt everything under it.

    This is the concrete shape of "a prefix match would silently exempt a whole directory": the
    cheapest way to write that bug is to list a directory and let the exclusion be a prefix test.
    Gate 1 refuses the entry outright — it must name a *file* — so gate 2 never gets the chance.
    """
    root = _make_root(
        tmp_path,
        allowlist="src/pkg\n",
        files={"src/pkg/a.py": "import anthropic\n"},
    )
    result = _run_gate(root)
    assert result.returncode == 1
    # The *gate-1* message specifically. Asserting only `returncode == 1` passed even with the
    # directory branch removed, because gate 2 then reported the planted import anyway — the test
    # would have been green while proving nothing about gate 1 (caught by mutation, 20260728 19:40).
    assert "names a directory" in result.stderr
    assert "src/pkg" in result.stderr


# --------------------------------------------------------------------------------------------
# Gate 2 — no paid-client import outside the allowlist
# --------------------------------------------------------------------------------------------


def test_no_paid_client_outside_the_allowlist() -> None:
    """Gate 2 against the real repo.

    The scan count is asserted non-zero on purpose: every assertion about "no hits" is also
    satisfied by a walk that visited nothing, which is how a gate keeps passing after someone
    breaks its glob. `src/` holds ~40 files, so any single-digit count means the walk collapsed.
    """
    result = _run_gate(REPO_ROOT)
    assert result.returncode == 0, result.stderr
    scanned = int(result.stdout.split("file(s) scanned")[0].split(",")[-1].strip())
    assert scanned > 10, f"gate 2 only walked {scanned} file(s) — the scan collapsed"


def test_a_paid_import_outside_the_allowlist_fails_gate_2(tmp_path: Path) -> None:
    """Gate 2's negative: an import planted in a **non**-allowlisted module must fail the gate."""
    root = _make_root(
        tmp_path,
        allowlist="src/pkg/paid.py\n",
        files={
            "src/pkg/paid.py": "import anthropic\n",
            "src/pkg/free.py": "import anthropic\n",
        },
    )
    result = _run_gate(root)
    assert result.returncode == 1
    assert "src/pkg/free.py" in result.stderr
    assert "src/pkg/paid.py" not in result.stderr, "the allowlisted file must stay exempt"


def test_the_allowlist_exempts_only_the_exact_path(tmp_path: Path) -> None:
    """The part most likely to be wrong is the exclusion itself, and gate 1 cannot see it wrong.

    An entry of `src/pkg/claude.py` implemented as a prefix or substring match would silently
    exempt `src/pkg/claude_helper.py` and everything under a `src/pkg/claude/` directory — while
    gate 1 stays green, because the listed path does exist. Both shapes are planted here; both
    must be reported.
    """
    root = _make_root(
        tmp_path,
        allowlist="src/pkg/claude.py\n",
        files={
            "src/pkg/claude.py": "import anthropic\n",
            "src/pkg/claude_helper.py": "import anthropic\n",
            "src/pkg/claude/inner.py": "from anthropic import Anthropic\n",
        },
    )
    result = _run_gate(root)
    assert result.returncode == 1
    assert "claude_helper.py" in result.stderr
    assert "inner.py" in result.stderr


def test_gate_2_matches_every_paid_client_and_ignores_lookalikes(tmp_path: Path) -> None:
    """One test per direction of the pattern, because `\\b` is doing real work in it.

    `anthropic_version = "1"` and `import openai_shim` are ordinary lines this project already
    writes (`extract/__init__.py` names `anthropic` as a *string* in two places); a pattern loose
    enough to flag them would be turned off within a week.
    """
    root = _make_root(
        tmp_path,
        allowlist="",
        files={"src/pkg/innocent.py": 'anthropic_version = "1"\nimport openai_shim\n'},
    )
    assert _run_gate(root).returncode == 0

    for spelling in ("import anthropic", "from openai import OpenAI", "import cohere"):
        planted = _make_root(
            tmp_path / spelling.replace(" ", "_"),
            allowlist="",
            files={"src/pkg/guilty.py": f"{spelling}\n"},
        )
        assert _run_gate(planted).returncode == 1, f"gate 2 missed {spelling!r}"


def test_the_two_paid_client_lists_agree() -> None:
    """`PAID_CLIENT_MODULES` here and `PAID_CLIENTS` in the gate script name the same providers —
    one as `sys.modules` keys, one as regex alternatives. Adding a provider to one and not the
    other leaves gate 2 or gate 4 quietly narrower than its twin, and nothing else would notice."""
    text = GATE_SCRIPT.read_text(encoding="utf-8")
    line = next(line for line in text.splitlines() if line.startswith("PAID_CLIENTS = "))
    in_script = {
        part.strip().strip("r").strip("\"'").replace("\\.", ".")
        for part in line.split("(", 1)[1].rstrip(")").split(",")
        if part.strip()
    }
    assert in_script == set(PAID_CLIENT_MODULES)


def test_the_paid_module_test_ignores_unrelated_namespace_packages() -> None:
    """The false-positive direction, which matters as much as the true-positive one here.

    `google.protobuf` travels with onnxruntime and grpc; `openai_shim` is an ordinary name. A gate
    that flags either would be switched off the first time it cried wolf, and this gate is the last
    thing standing between the free path and a paid client.
    """
    assert _is_paid_module("anthropic")
    assert _is_paid_module("anthropic.types.beta")
    assert _is_paid_module("google.generativeai")

    assert not _is_paid_module("google")
    assert not _is_paid_module("google.protobuf")
    assert not _is_paid_module("openai_shim")
    assert not _is_paid_module("anthropic_helpers")


# --------------------------------------------------------------------------------------------
# Gate 4 — the free path never imports a paid client, observed at runtime
# --------------------------------------------------------------------------------------------

_NO_CLIENT = find_spec("anthropic") is None
_SKIP_REASON = (
    "pinakes[claude] not installed — with `anthropic` absent, 'anthropic not in sys.modules' is "
    "true by construction and can no longer tell a clean free path from a compromised one. CI's "
    "[light,pdf,claude] leg is where this gate is meaningful."
)


def _free_path_modules(tmp_path: Path, prelude: str = "") -> set[str]:
    """Run the whole free path in a **fresh** subprocess and return what it imported.

    Fresh, because in-process any earlier test's import would defeat the assertion — the exact
    shape of v0.1's `-wal` test, which was correct and then silently defeated by an environmental
    fact (docs/RETROSPECTIVES.md, I8b).

    The module list travels through a file rather than stdout: the free-path run prints two full
    `pnk doctor` reports and a search result, and parsing a payload out of that is a parser nobody
    should have to debug when this gate fails.
    """
    output = tmp_path / "modules.json"
    program = (
        f"{prelude}\n"
        "import runpy, sys\n"
        f"sys.argv = ['free_path_run.py', {str(output)!r}]\n"
        f"runpy.run_path({str(FREE_PATH_RUN)!r}, run_name='__main__')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", program], capture_output=True, text=True, cwd=REPO_ROOT
    )
    assert result.returncode == 0, f"the free-path run itself failed:\n{result.stderr}"
    modules = set(json.loads(output.read_text(encoding="utf-8")))

    # The run must actually have reached the surfaces it claims to cover. Without this, a
    # free-path run that quietly did nothing would satisfy every "no paid import" assertion below.
    for surface in (
        "pinakes.cli",
        "pinakes.sync",
        "pinakes.search",
        "pinakes.doctor",
        "pinakes.serve",
        # Modules, not commands: this list is about what the import graph actually reached, and
        # the traversal core plus its provider are new territory on the free path (L3, L4).
        "pinakes.graph.traverse",
        "pinakes.graph.provider",
        # The projection both surfaces return through — the module the fixture's authored links
        # exist to reach, and the one whose loop body a paid import could have hidden in.
        "pinakes.graph.present",
        # The edge deriver (G3). It runs inside every `pnk sync`, which is the free path by
        # definition — and this gate's *coverage* is extended per increment rather than assumed
        # to follow from the increment being free.
        "pinakes.graph.edges",
        # `pnk upgrade` (T3), for that same reason. Without this row the free-path run could stop
        # calling the command and every "no paid import" assertion below would still pass.
        "pinakes.upgrade",
    ):
        assert surface in modules, f"the free-path run never reached {surface}"
    return modules


def test_the_free_path_run_never_loads_yaml(tmp_path: Path) -> None:
    """PyYAML must not be reachable from the free path — the runtime half of L5b's pair.

    Lives here rather than in `test_packaging.py` because this file already owns `FREE_PATH_RUN`
    and the fresh-subprocess harness. The predicate is an exact match or a `yaml.` prefix, never a
    substring: the module list legitimately contains `pydantic_settings.sources.providers.yaml`.

    This caught a real one. `free_path_run.py` wrote a sidecar through `yaml.safe_dump`, so the
    harness itself put `yaml` into the list — the gate was defeated by its own fixture, and that
    line was also the last PyYAML sidecar *writer* in the repo.
    """
    modules = _free_path_modules(tmp_path)
    loaded = sorted(name for name in modules if name == "yaml" or name.startswith("yaml."))
    assert not loaded, f"the free path loaded PyYAML: {loaded}"
    assert any(name.startswith("ruamel") for name in modules), "...and it must have loaded ruamel"


def _assert_no_paid_client(modules: set[str]) -> None:
    """The checker itself, named so gate 4's negative test has something to make fail."""
    found = sorted(name for name in modules if _is_paid_module(name))
    if found:
        raise AssertionError(f"the free path imported a paid client: {found}")


@pytest.mark.skipif(_NO_CLIENT, reason=_SKIP_REASON)
def test_the_free_path_never_imports_the_paid_client(tmp_path: Path) -> None:
    """`pnk init`, `sync`, `search`, `doctor` and an MCP handshake — over a free KB *and* over a
    KB configured for `claude-vision` — leave `anthropic` unimported.

    The second KB is what makes this more than decoration. Both leaks this increment fixed were
    availability probes that only fire on a paid-configured KB: `doctor._extraction` loaded the
    backend to report whether it was installed, and `sync._missing_pdf_extra` did the same to build
    the hint about a skipped `.pdf`. Verified by mutation, 20260728 19:23: restoring either one
    alone puts `anthropic` back in `sys.modules` and fails this test.
    """
    _assert_no_paid_client(_free_path_modules(tmp_path))


@pytest.mark.skipif(_NO_CLIENT, reason=_SKIP_REASON)
def test_the_free_path_gate_fails_when_an_import_is_planted(tmp_path: Path) -> None:
    """Gate 4's negative. The identical subprocess, with one line of prelude, must be caught."""
    modules = _free_path_modules(tmp_path, prelude="import anthropic")
    with pytest.raises(AssertionError, match="imported a paid client"):
        _assert_no_paid_client(modules)


def test_the_free_path_gate_says_so_when_it_cannot_run() -> None:
    """A skip nobody can see is the vacuous-metric failure wearing a different hat (ground rules).

    Asserts the reason exists and explains *why* the gate is meaningless without the extra, rather
    than merely naming a missing package — this is the flagship safety check, and "skipped" on the
    two legs that cannot run it must not read as "passed".
    """
    assert "true by construction" in _SKIP_REASON
    assert "light,pdf,claude" in _SKIP_REASON


# --------------------------------------------------------------------------------------------
# The deep client, and the MCP surface (E3)
# --------------------------------------------------------------------------------------------

#: The module `pnk ask --deep` spends through. Named as a string rather than imported: the whole
#: assertion is that this name never reaches `sys.modules` on a surface that must not spend, and a
#: test that imported it would put it there itself.
DEEP_CLIENT = "pinakes.deep.client"


def _assert_no_deep_client(modules: set[str]) -> None:
    """The checker, named so the negative control has something to make fail."""
    if DEEP_CLIENT in modules:
        raise AssertionError(f"a free surface imported the deep client: {DEEP_CLIENT}")


def test_the_free_path_and_the_mcp_server_never_load_the_deep_client(tmp_path: Path) -> None:
    """DESIGN §4.3: an MCP caller composes `pinakes_search` -> `pinakes_get` on reasoning it has
    already paid for. A server-side loop would spend the **operator's** money on the *caller's*
    question, so `pnk serve` must never reach `pinakes.deep.client` — enforced by a gate, not by a
    convention (§1 of the deep release's plan).

    The free-path run builds the MCP server, lists its tools and calls one, and runs every free CLI
    command including `pnk ask` — so this covers both surfaces at once. It lands in E3 rather than
    E5 because an assertion cannot name a module that does not exist; that ordering is the opposite
    of the allowlist gate's, and is acceptable only because this is the **second** line of defence.
    The first, `test_the_free_path_never_imports_the_paid_client`, catches the leak whatever the
    module is called — but it needs `pinakes[claude]` installed to mean anything, and this one runs
    on every leg.
    """
    _assert_no_deep_client(_free_path_modules(tmp_path))


def test_the_free_path_reaches_the_estimator_and_still_not_the_client(tmp_path: Path) -> None:
    """The two `deep` modules are separable, and the free path proves it by using **one** of them.

    Since E4, `pnk ask` without `--deep` prices the run it offers, which imports
    `pinakes.deep.estimate` on a path that must never spend. That is safe — the estimator holds no
    client and reads a table shipped in the wheel — but "safe" is a claim, and this is the only
    place it is observed: a fresh subprocess where one module is present and its sibling is not.

    **The positive half is what makes it worth writing.** Asserting the client's absence alone
    passes on a run that imported neither, and would go on passing if the free path stopped pricing
    anything at all. `pinakes.deep` importing nothing in its `__init__` is what keeps the two
    apart, and this is what would notice that changing.
    """
    modules = _free_path_modules(tmp_path)
    assert "pinakes.deep.estimate" in modules, (
        "the free `pnk ask` no longer reaches the estimator — either it stopped pricing the run it "
        "offers, or this gate stopped covering `pnk ask`"
    )
    # E5 gave the free path a *second* module in that package: `pnk sync --clear-cache=transcripts`
    # reads and empties `.pinakes/deep/`. Two siblings of `pinakes.deep.client` are now reachable
    # without spending, which makes the `__init__` importing nothing load-bearing twice over.
    assert "pinakes.deep.transcript" in modules, (
        "the free path no longer reaches the transcript module — either "
        "`--clear-cache=transcripts` stopped reading it, or this gate stopped covering it"
    )
    _assert_no_deep_client(modules)


def test_the_deep_client_gate_fails_when_an_import_is_planted(tmp_path: Path) -> None:
    """The negative control, and the only thing that makes the assertion above non-vacuous.

    "`pinakes.deep.client` is not in this set" is also true of a run that imported nothing at all,
    or of a checker that never looks. Planting the import in the prelude proves the module *can*
    appear in the list the harness collects, and that the checker sees it when it does.
    """
    modules = _free_path_modules(tmp_path, prelude=f"import {DEEP_CLIENT}")
    with pytest.raises(AssertionError, match="imported the deep client"):
        _assert_no_deep_client(modules)
