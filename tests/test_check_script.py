"""`check.sh`'s own pdf-quality gate: skips with a printed reason when the extra is absent, and the
script still exits 0 — never silently, never a failure.

Faithfully re-synchronising this repo's `.venv` without `[pdf]` just to prove the skip branch would
make this test as expensive as the gate it is checking; instead, `test_check_sh_declares_the_guard`
pins down that `check.sh` *itself* contains the exact guard, with `make pdf-eval` specifically
inside the `then` branch and specifically absent from the `else` branch — not merely present
*somewhere* in the file, which an explanatory comment sitting next to a silently gutted call would
also satisfy — and `test_the_skip_and_continue_shape_exits_zero` proves the shape that guard is
written in — "a failed import check prints a reason and the script still exits 0" — actually
behaves that way, using a subprocess and an import guaranteed to fail rather than trying to fake
pypdfium2's absence inside an environment where it is, in this checkout, actually installed.
"""

import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

CHECK_SH = Path(__file__).parent.parent / "check.sh"
WORKFLOW = Path(__file__).parent.parent / ".github" / "workflows" / "ci.yml"


def _workflow() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_check_sh_declares_the_pdf_quality_guard() -> None:
    """A bare substring check (`"make pdf-eval" in text`) would still pass if the real call were
    replaced with a no-op while the explanatory comment above it stayed put — verified directly:
    doing exactly that left every bare-substring assertion green. Matching the actual
    `if ... then / else / fi` block and asserting *where* each string falls (inside `then`, absent
    from `else`) is what a silently gutted gate cannot survive.
    """
    text = CHECK_SH.read_text(encoding="utf-8")
    match = re.search(
        r'if uv run --frozen python3 -c "import pypdfium2" 2>/dev/null; then\n'
        r"(?P<then>.*?)\n"
        r"else\n"
        r"(?P<else>.*?)\n"
        r"fi",
        text,
        re.DOTALL,
    )
    assert match is not None, "check.sh's pdf-quality if/then/else/fi block was not found"
    then_branch, else_branch = match.group("then"), match.group("else")
    assert "make pdf-eval" in then_branch
    assert "make pdf-eval" not in else_branch
    assert "pdf-quality: skipped" in else_branch
    assert "pdf-quality: skipped" not in then_branch


def test_the_skip_and_continue_shape_exits_zero() -> None:
    """The exact shape `check.sh` uses for every extras-dependent gate: `if <python import check>;
    then <run the gate>; else echo '<name>: skipped -- <reason>'; fi`, followed by more script. An
    import guaranteed to fail stands in for "pypdfium2 not installed" — the shape under test is
    generic to every such guard in `check.sh`, not specific to which module it names.
    """
    script = f"""
set -e
if {sys.executable} -c "import definitely_not_a_real_module_xyz" 2>/dev/null; then
    echo "gate ran"
else
    echo "some-gate: skipped -- reason"
fi
echo "all gates green"
"""
    result = subprocess.run(["sh", "-c", script], capture_output=True, text=True)
    assert result.returncode == 0
    assert "some-gate: skipped -- reason" in result.stdout
    assert "gate ran" not in result.stdout
    assert "all gates green" in result.stdout


def test_check_sh_declares_the_prices_toml_gate() -> None:
    """I6a: unlike the extras-gated checks above, this one has no skip branch — `budget/` has no
    extra to be absent — so nothing else would notice if it were quietly deleted or reduced to a
    no-op. `pyright`/`ruff` never see it: it is shell embedding Python, not a module either
    checker parses."""
    text = CHECK_SH.read_text(encoding="utf-8")
    assert "load_prices" in text
    assert "strptime" in text
    assert "%Y%m%d %H:%M" in text


def test_check_sh_declares_the_link_density_gate() -> None:
    """L1 added a gate to `check.sh` and a job to `ci.yml` and asserted neither, so deleting
    either left the whole suite green. Same reasoning as the pdf-quality guard above: match the
    real invocation, not a substring an explanatory comment would also satisfy."""
    text = CHECK_SH.read_text(encoding="utf-8")
    assert re.search(
        r"^uv run --frozen python3 tools/link_density_gate\.py\s*$", text, re.MULTILINE
    ), "check.sh no longer invokes the link-density gate"


def test_ci_runs_the_link_density_gate_and_proves_it_can_fail() -> None:
    """`ci.yml` never invokes `check.sh`, so a gate living only there runs only where someone
    remembers. The negative step matters as much as the positive one: a gate nobody has watched
    fail is a gate nobody knows works."""
    workflow = _workflow()
    job = re.search(r"^  link-density:\n(?P<body>(?:    .*\n|\n)*)", workflow, re.MULTILINE)
    assert job is not None, "ci.yml has no link-density job"
    body = job.group("body")
    assert "tools/link_density_gate.py" in body
    assert "--max-degree 0" in body, "the negative check is gone — nothing proves the gate gates"
    assert "exit 1" in body, "the negative check no longer fails the job"


def test_check_sh_declares_the_traversal_cap_gate() -> None:
    """L3's caps are the only thing between an agent's `depth=99` and most of a KB in one
    response. Same pinning as the two gates above: match the real invocation."""
    text = CHECK_SH.read_text(encoding="utf-8")
    assert re.search(
        r"^uv run --frozen python3 tools/traversal_cap_gate\.py\s*$", text, re.MULTILINE
    ), "check.sh no longer invokes the traversal-cap gate"


def test_ci_runs_the_traversal_cap_gate() -> None:
    workflow = _workflow()
    job = re.search(r"^  traversal-caps:\n(?P<body>(?:    .*\n|\n)*)", workflow, re.MULTILINE)
    assert job is not None, "ci.yml has no traversal-caps job"
    body = job.group("body")
    assert "tools/traversal_cap_gate.py" in body
    assert "--expect-depth 99" in body, "the negative check is gone — nothing proves it gates"
    assert "the caps moved" in body, "the negative check no longer requires the stated reason"


def test_check_sh_declares_the_eval_reproducibility_gate() -> None:
    """G1. Same pinning as its three siblings: match the real invocation, never a substring that an
    explanatory comment would also satisfy."""
    text = CHECK_SH.read_text(encoding="utf-8")
    assert re.search(
        r"^uv run --frozen python3 tools/eval_reproducibility_gate\.py\s*$", text, re.MULTILINE
    ), "check.sh no longer invokes the eval-reproducibility gate"


def test_ci_runs_the_eval_reproducibility_gate_and_proves_it_can_fail() -> None:
    workflow = _workflow()
    job = re.search(r"^  eval-reproducibility:\n(?P<body>(?:    .*\n|\n)*)", workflow, re.MULTILINE)
    assert job is not None, "ci.yml has no eval-reproducibility job"
    body = job.group("body")
    assert "tools/eval_reproducibility_gate.py" in body
    assert "--inject-difference" in body, "the negative check is gone — nothing proves it gates"
    assert "questions changed outcome" in body, (
        "the negative check no longer requires the stated reason, so a crash would satisfy it"
    )


def test_check_sh_declares_the_status_header_gate() -> None:
    """docs/STATUS.md's header drifted from `__version__` for four consecutive releases because
    only a checklist watched it (plans/20260731_1202-open-corrections.md, 20260803). Same pinning
    as its
    siblings: match the real invocation, never a substring that an explanatory comment would also
    satisfy."""
    text = CHECK_SH.read_text(encoding="utf-8")
    assert re.search(
        r"^uv run --frozen python3 tools/status_header_gate\.py\s*$", text, re.MULTILINE
    ), "check.sh no longer invokes the status-header gate"


def test_ci_runs_the_status_header_gate_and_proves_it_can_fail() -> None:
    """Its four siblings above assert the negative check by bare substring, which a comment
    quoting the same phrase would satisfy after the real `grep` line was deleted. Here the two
    halves of the negative check are matched as *commands* — a line whose first non-space
    character is not `#` — so a comment cannot stand in for either.
    """
    workflow = _workflow()
    job = re.search(r"^  status-header:\n(?P<body>(?:    .*\n|\n)*)", workflow, re.MULTILINE)
    assert job is not None, "ci.yml has no status-header job"
    body = job.group("body")
    assert re.search(r"^\s*[^#\s].*tools/status_header_gate\.py\s*$", body, re.MULTILINE), (
        "ci.yml no longer invokes the status-header gate"
    )
    assert re.search(r"^\s*[^#\s].*--expect-version 99\.99\.99", body, re.MULTILINE), (
        "the negative check is gone — nothing proves it gates"
    )
    assert re.search(
        r"^\s*[^#\s].*grep -q \"the header drifted from the release\"", body, re.MULTILINE
    ), "the negative check no longer requires the stated reason, so a crash would satisfy it"


def test_check_sh_declares_the_release_order_gate() -> None:
    """Five ordered release sequences drifted while every other gate stayed green, because
    ordering is a property of the sequence and everything else here reads rows (docs/RELEASING.md).
    Same pinning as its siblings: match the real invocation, never a substring an explanatory
    comment would also satisfy."""
    text = CHECK_SH.read_text(encoding="utf-8")
    assert re.search(r"^python3 tools/release_order_gate\.py\s*$", text, re.MULTILINE), (
        "check.sh no longer invokes the release-order gate"
    )


def test_ci_runs_the_release_order_gate_and_proves_it_can_fail() -> None:
    """In the `build` job, beside `paid_path_gate.py`, for the same reason: stdlib-only and no
    install. Both halves matched as *commands* — a line whose first non-space character is not
    `#` — so a comment quoting the phrase cannot stand in for a deleted one.
    """
    workflow = _workflow()
    assert re.search(r"^\s*[^#\s].*tools/release_order_gate\.py\s*$", workflow, re.MULTILINE), (
        "ci.yml no longer invokes the release-order gate"
    )
    assert re.search(
        r"^\s*[^#\s].*release_order_gate\.py \"\$RUNNER_TEMP", workflow, re.MULTILINE
    ), "the negative check is gone — nothing proves it gates"
    assert re.search(r"^\s*[^#\s].*grep -q \"reads ascending, but\"", workflow, re.MULTILINE), (
        "the negative check no longer requires the stated reason, so a crash would satisfy it"
    )


def test_ci_compares_per_question_outcomes_across_two_operating_systems() -> None:
    """The half a single machine cannot answer (G1).

    The point of the job is that the two legs are *different architectures*. A matrix that quietly
    lost one of them would still be green, still upload an artifact, and prove nothing — so the two
    runner names are asserted here rather than left to the reader of the workflow.
    """
    workflow = _workflow()
    job = re.search(r"^  eval-cross-machine:\n(?P<body>(?:    .*\n|\n)*)", workflow, re.MULTILINE)
    assert job is not None, "ci.yml has no eval-cross-machine job"
    body = job.group("body")
    assert "ubuntu-latest" in body and "macos-latest" in body, (
        "the cross-machine comparison is down to one machine, which compares nothing"
    )
    assert "--record-outcomes" in body

    compare = re.search(
        r"^  eval-cross-machine-compare:\n(?P<body>(?:    .*\n|\n)*)", workflow, re.MULTILINE
    )
    assert compare is not None, "the two legs are recorded and never compared"
    assert "diff" in compare.group("body")
    assert "needs: eval-cross-machine" in compare.group("body")


RELEASE_WORKFLOW = Path(__file__).parent.parent / ".github" / "workflows" / "release.yml"


def test_the_release_workflow_creates_the_github_release_after_publishing() -> None:
    """D-19. **The step this workflow never had, and whose absence was misdiagnosed six times.**

    `docs/STATUS.md` recorded "the workflow failed to create the release" at every release from
    0.20.1 to 0.21.1, while `git log -S` shows no workflow in this repository's history had ever
    contained a release-creating step and `docs/RELEASING.md` step 8 had always said to create it
    by hand. The job's `success` was honest. Checking the symptom harder — `gh release view` says
    *not found* — could never distinguish an absent feature from a broken one, because it is
    equally consistent with both.

    **Parsed, not grepped, and the ordering is the assertion.** PyPI refuses a version twice, so
    the upload is the irreversible step: anything able to fail must come after it, or a failure
    here costs the release its version number. A test that merely found `gh release create`
    somewhere in the file would pass with the step first.
    """
    import yaml

    document = yaml.safe_load(RELEASE_WORKFLOW.read_text(encoding="utf-8"))
    steps = document["jobs"]["publish"]["steps"]
    names = [str(step.get("name", "")) for step in steps]

    publish = names.index("Publish to PyPI")
    release = next(i for i, step in enumerate(steps) if "gh release create" in str(step.get("run")))
    assert publish < release, "a step that can fail must not run in front of the PyPI upload"

    assert "contents: write" in RELEASE_WORKFLOW.read_text(encoding="utf-8"), (
        "gh release create needs it, and the job requested only id-token: write"
    )
    # **The command line, not the whole `run` block.** The block includes the comment explaining
    # the flag, so `"--verify-tag" in run` is satisfied by the explanation with the flag deleted
    # from the command — measured: that version of this assertion survived the mutation that
    # removed it. Assert on the line that actually invokes `gh`.
    invocation = next(
        line for line in str(steps[release]["run"]).splitlines() if "gh release create" in line
    )
    assert "--verify-tag" in invocation, (
        "without it the step would invent a release for a tag that was never pushed"
    )
    assert "--notes-from-tag" in invocation, (
        "the notes are the maintainer's tag annotation, not a generated diff nobody reviewed"
    )


def _no_failure_path_exits_zero(run: str, where: str) -> None:
    """Every `exit` in a step body must be non-zero.

    `::error::` is a log annotation and fails nothing; the `exit` beside it is the whole
    mechanism. Every one of these steps captures a status, greps the output and then exits — and
    the tests asserted all three of those *shapes* while nothing asserted the last one exits
    non-zero. Changing `exit 1` to `exit 0` in the handshake left it printing
    `::error::pnk serve exited 1` and reporting success, on a wheel that could not serve; the same
    edit in `release.yml` put that in front of `uv publish`. Found by the third review's battery,
    20260822.

    Comment lines are dropped first: one of these steps explains its own guard with the words
    "and exit 0", and reading that as a command is this repository's most-recorded mistake —
    committed here, once, while writing the assertion against it.
    """
    commands = "\n".join(line for line in run.splitlines() if not line.lstrip().startswith("#"))
    zeros = [code for code in re.findall(r"\bexit (\d+)", commands) if code == "0"]
    assert not zeros, f"{where}: a failure path that exits 0 is not a failure path"


def _job_cannot_be_switched_off(document: dict[str, Any], name: str) -> None:
    """The steps were guarded against `if:`/`continue-on-error:` and the **job** was not.

    It is the same key one level up and the shorter edit: `continue-on-error: true` on `build`
    makes the entire fresh-resolve leg advisory, and `if: false` deletes it, while every
    step-level assertion stays true. Both survived the suite until this existed.
    """
    jobs: dict[str, Any] = document["jobs"]
    job: dict[str, Any] = jobs[name]
    disabling = {"if", "continue-on-error"} & set(job)
    assert not disabling, f"the {name} job itself carries {sorted(disabling)}"


def test_ci_imports_every_module_out_of_a_freshly_resolved_wheel_and_proves_it_can_fail() -> None:
    """The durable half of the `mcp` 2.0 outage fix, and the half that matters.

    `pnk serve` raised `ModuleNotFoundError: No module named 'mcp.server.fastmcp'` on every fresh
    install from the first PyPI release to 0.27.1, and CI stayed green throughout: all 37 other
    `uv` invocations in `ci.yml` carry `--frozen`, and the one job that does resolve fresh never
    imported `pinakes.serve`. Capping `mcp` closes that instance; the wheel-import gate is what
    closes the class, so a cap without this leg would be the whole fix undone by the next
    dependency's major.

    Matched as *commands* — a line whose first non-space character is not `#` — for the reason
    `test_ci_runs_the_status_header_gate_and_proves_it_can_fail` gives: the step is preceded by a
    comment that names the same strings, and a bare substring assertion would be satisfied by the
    explanation after the command was deleted.
    """
    workflow = _workflow()
    assert re.search(r"^[ \t]*(?![ \t#]).*tools/wheel_import_gate\.py", workflow, re.MULTILINE), (
        "ci.yml no longer invokes the wheel-import gate"
    )
    assert re.search(r"^[ \t]*(?![ \t#]).*--require pinakes\.serve", workflow, re.MULTILINE), (
        "nothing requires the walk to have reached pinakes.serve — the module the gate exists for"
    )
    assert re.search(
        r"^[ \t]*(?![ \t#]).*--allow-missing pinakes\.extract\.pdfium:pypdfium2",
        workflow,
        re.MULTILINE,
    ), (
        "the bare-wheel leg is gone, and with it the run that proves the gate sees a missing "
        "dependency. The allowance must stay `MODULE:LIBRARY`: keyed on the library alone it "
        "would excuse any module failing on pypdfium2, pinakes.serve included"
    )
    assert re.search(
        r"^[ \t]*(?![ \t#]).*pinakes\[light,pdf,claude\] @ file://", workflow, re.MULTILINE
    ), "the extras leg is gone — the modules behind [light], [pdf] and [claude] are unwalked"
    for lazy in ("anthropic", "fastembed", "fastembed.rerank.cross_encoder"):
        assert re.search(
            rf"^[ \t]*(?![ \t#]).*--also-import {re.escape(lazy)}(\s|$)", workflow, re.MULTILINE
        ), f"{lazy} is imported lazily by src/, so only --also-import reaches it"


def test_cis_negative_check_names_the_failure_it_expects_not_the_generic_headline() -> None:
    """A gate nobody has watched fail is a gate nobody knows works — and the watching has to be
    of the right failure.

    The first version grepped for the tool's generic headline. An environment where `--with`
    installed nothing prints that headline too, so the step was satisfiable by a run in which the
    gate never executed — the repository's own recorded defect class, inside the step written to
    prevent it. It now requires the one failure the bare wheel genuinely has.
    """
    workflow = _workflow()
    job = re.search(r"^  build:\n(?P<body>(?:    .*\n|\n)*)", workflow, re.MULTILINE)
    assert job is not None, "ci.yml has no build job"
    body = job.group("body")
    assert re.search(
        r"""^[ \t]*(?![ \t#]).*grep -q "pinakes\.extract\.pdfium: ModuleNotFoundError""",
        body,
        re.MULTILINE,
    ), "the negative check no longer names the failure it expects"
    import yaml

    negative = next(
        step
        for step in yaml.safe_load(workflow)["jobs"]["build"]["steps"]
        if str(step.get("name")) == "The wheel-import gate can still fail"
    )
    _no_failure_path_exits_zero(str(negative["run"]), "ci.yml's negative check")
    assert not re.search(
        r"^[ \t]*(?![ \t#]).*did not import against the resolved dependency set",
        body,
        re.MULTILINE,
    ), "grepping the generic headline lets a wheel that installed nothing satisfy this step"
    # Matched as a *command*, not as a substring of the whole body: a comment explaining the
    # distinction between the two headlines is exactly what a reader of this step needs, and a
    # bare `not in body` would turn that comment red — the line-shaped-tool-on-structure class
    # this repository keeps recording, in the assertion guarding against it.


def test_ci_drives_a_real_mcp_handshake_against_a_freshly_resolved_install() -> None:
    """An import is not a session. `import pinakes.serve` proves the module loads; only a
    handshake proves the server was constructed, the tools were registered and the stdio transport
    answered — which is what `pnk serve` actually is.

    **The session is driven by `tools/mcp_handshake_gate.py`, and this test's job is to keep it
    from going back to hand-rolled JSON-RPC.** That version wrote three lines and closed stdin;
    `mcp` 1.28.1 drained the queue before exiting and answered `tools/list` 10 times in 10, while
    2.0.0 answered 2 in 10 (measured 20260822 14:35). A step that fails four runs in five for a
    server that works is not a weaker gate, it is a gate that teaches people to re-run it.

    `--expect-version` is required and must *not* come from `pnk --version`: the field it checks
    carried the `mcp` library's version on every release to 0.27.2, and asking the same install
    which version it is would agree with itself while both were wrong. The wheel's filename is the
    independent source.

    The KB path is asserted against the step that *creates* it rather than as a literal, because
    renaming it in one place and not the other fails at runtime and nowhere else.
    """
    workflow = _workflow()
    job = re.search(r"^  build:\n(?P<body>(?:    .*\n|\n)*)", workflow, re.MULTILINE)
    assert job is not None, "ci.yml has no build job"
    body = job.group("body")

    created = re.search(r"^[ \t]*(?![ \t#]).*pnk init (?P<kb>/\S+)", body, re.MULTILINE)
    assert created is not None, "the build job no longer creates a smoke KB"
    kb = created.group("kb")
    gate = re.search(
        r"^[ \t]*(?![ \t#]).*tools/mcp_handshake_gate\.py.*\n(?:[ \t]*(?![ \t#]).*\n)*",
        body,
        re.MULTILINE,
    )
    assert gate is not None, (
        "ci.yml no longer drives a handshake against the freshly-resolved wheel"
    )
    invocation = gate.group(0)
    assert re.search(rf"--kb {re.escape(kb)}(\s|$)", invocation), (
        f"the handshake does not serve the KB the job creates ({kb})"
    )
    assert "--expect-version" in invocation, (
        "nothing asserts which version the server tells a client it is — the field that carried "
        "the mcp library's version on every release to 0.27.2"
    )
    assert not re.search(r"--expect-version[= ]\"?\$\(.*pnk --version", invocation), (
        "the expected version is read from the install under test, so it would agree with itself"
    )
    assert re.search(
        r"^[ \t]*(?![ \t#]).*version=\$\(basename .*cut -d- -f2", body, re.MULTILINE
    ), (
        "the expected version no longer comes from the built wheel's filename, the one source "
        "here that is independent of the process being checked"
    )
    assert re.search(r"^[ \t]*(?![ \t#]).*timeout \d+ uv run", body, re.MULTILINE), (
        "how a session ends is a property of whichever mcp the fresh resolve took — the very "
        "thing that changes with no commit here — so a hang must cost seconds, not the job"
    )
    assert re.search(r"^    timeout-minutes: \d+$", body, re.MULTILINE), (
        "the only job here whose runtime a third party can change has no ceiling on it"
    )
    # **The gate's own exit status is the step's.** The previous shape captured the output into a
    # variable, tested `code=$?` and grepped what it had captured — three places to get wrong, and
    # the battery had to pin each one. Running the gate bare removes them: `set -e` plus a
    # non-zero exit is the whole mechanism. So what has to be asserted now is the *absence* of a
    # capture, because reintroducing one is how this step would quietly stop reading failures.
    assert not re.search(r"^\s*out=\$\(timeout", body, re.MULTILINE), (
        "the handshake's output is captured into a variable again — a gate is only a gate when "
        "its exit status is what the next command reads"
    )
    import yaml

    document = yaml.safe_load(workflow)
    handshake = next(
        step
        for step in document["jobs"]["build"]["steps"]
        if "tools/mcp_handshake_gate.py" in str(step.get("run", ""))
        and "--expect-version 0.0.0" not in str(step.get("run", ""))
    )
    _no_failure_path_exits_zero(str(handshake["run"]), "ci.yml's handshake")
    _job_cannot_be_switched_off(document, "build")


def test_the_handshake_gate_is_watched_failing_for_the_reason_it_claims() -> None:
    """A gate nobody has watched fail is a gate nobody knows works — and `ci.yml` already carries
    that check for the wheel-import gate. This is its twin for the handshake, and it exists because
    the two ways this gate can fail are not equally informative.

    `--expect-version 0.0.0` must be refused **by the version assertion**, not by a missing `pnk`,
    an absent KB or a session that never started. Each of those also exits non-zero, so a negative
    check reading only the exit status would be satisfied by a run in which the gate never reached
    a server — the repository's recorded defect class, inside the step written to prevent it. The
    grep therefore names `serverInfo.version`, a string no other failure path prints.
    """
    import yaml

    workflow = _workflow()
    document = yaml.safe_load(workflow)
    negative = next(
        (
            step
            for step in document["jobs"]["build"]["steps"]
            if "--expect-version 0.0.0" in str(step.get("run", ""))
        ),
        None,
    )
    assert negative is not None, (
        "nothing in ci.yml watches the handshake gate fail, so a gate that silently passes "
        "everything would look exactly like this one does now"
    )
    run = str(negative["run"])
    assert "serverInfo.version is" in run, (
        "the negative check does not name the failure it expects, so a run where the gate never "
        "reached a server would satisfy it"
    )
    _no_failure_path_exits_zero(run, "ci.yml's handshake negative check")


def test_the_release_workflow_exercises_the_wheel_it_is_about_to_publish() -> None:
    """`ci.yml` runs on push and pull_request, and a dependency's major arrives with **no commit
    in this repository**. So `main` can be green on Monday, the break can publish on Wednesday,
    and a tag on Thursday would carry it to PyPI, which never takes a version back.

    Until this was written (20260822) the pre-publish smoke test was `pnk --version` + `pnk
    init` — a fresh resolve asked two questions that touch no dependency, which is how every
    release from the first to 0.27.1 shipped with `pnk serve` dead. Both checks must sit **in
    front of** `uv publish`: a failure before the upload costs a deleted tag, a failure after it
    costs the version number.
    """
    import yaml

    workflow = RELEASE_WORKFLOW.read_text(encoding="utf-8")
    document = yaml.safe_load(workflow)
    steps = document["jobs"]["publish"]["steps"]
    runs = [str(step.get("run", "")) for step in steps]

    exercised = next((i for i, run in enumerate(runs) if "tools/wheel_import_gate.py" in run), None)
    assert exercised is not None, "release.yml does not import the wheel it is about to publish"
    assert "tools/mcp_handshake_gate.py" in runs[exercised], (
        "it imports the wheel and never starts the server the outage was in"
    )

    # The same assertions its `ci.yml` twin makes, and for the same reasons: the release path is
    # the one where being wrong is irreversible, so it may not check *less*. Each of these
    # survived deletion from release.yml while this test stayed green (second review, 20260822).
    assert "--expect-version" in runs[exercised], (
        "the wheel about to be uploaded is never asked which version it tells a client it is — "
        "the field that carried the mcp library's version on every release to 0.27.2"
    )
    assert re.search(r"version=\$\(basename .*cut -d- -f2", runs[exercised]), (
        "the expected version no longer comes from the wheel's own filename, so it could be read "
        "from the install under test and agree with itself"
    )
    assert "--require pinakes.serve" in runs[exercised], (
        "nothing requires the walk to have reached the module the whole gate exists for"
    )
    assert "--min-modules" in runs[exercised], (
        "without it the gate falls back to a floor a half-empty wheel would clear"
    )
    assert re.search(r"timeout \d+ uv run", runs[exercised]), (
        "an mcp whose session never ends would hang the job that publishes"
    )
    assert not re.search(r"^\s*out=\$\(timeout", runs[exercised], re.MULTILINE), (
        "the handshake's output is captured into a variable again — on the publish path above all, "
        "the gate's own exit status must be what `set -e` reads"
    )

    # **Unconditional, in both senses.** `Publish to PyPI` is legitimately gated on a repository
    # variable; a check in front of it must not be, because a gate that can be switched off is not
    # a gate. `if:` is the obvious way to switch one off and `continue-on-error:` is the quiet one
    # — the step fails, the job carries on, and `uv publish` runs anyway. Both leave the step's own
    # body intact, so every assertion above still passes; the mutation battery found the second.
    disabling = {"if", "continue-on-error"} & set(steps[exercised])
    assert not disabling, (
        f"the pre-publish check carries {sorted(disabling)} — it can be skipped or ignored while "
        f"still reading correctly, and what it guards is an upload PyPI will not take back"
    )
    _no_failure_path_exits_zero(runs[exercised], "release.yml's pre-publish check")
    _job_cannot_be_switched_off(document, "publish")

    published = next((i for i, run in enumerate(runs) if "uv publish" in run), None)
    assert published is not None, "release.yml no longer publishes"
    assert exercised < published, (
        "the check runs after the upload, where a failure costs the version number rather than a "
        "deleted tag"
    )


def test_the_extras_not_core_gate_reads_requirements_and_not_the_comments_around_them() -> None:
    """`check.sh`'s extras-not-core gate greps a *range of lines*, so it used to fail on a comment
    that merely mentioned a library — measured 20260822, when a comment above `mcp` explaining why
    `anthropic` was deliberately left uncapped turned the gate red and reported it as a core
    dependency.

    Both directions, against the real pipeline lifted out of `check.sh`: a mention inside a comment
    must not fire, and a real entry must. Stripping comments could have silenced the gate outright,
    and only the second half can tell that apart from a fix.
    """
    text = CHECK_SH.read_text(encoding="utf-8")
    match = re.search(
        r"^(?P<pipeline>if awk .*?)\s*; then$",
        text,
        re.MULTILINE | re.DOTALL,
    )
    assert match is not None, "check.sh's extras-not-core pipeline was not found"
    pipeline = match.group("pipeline").removeprefix("if ").replace("\\\n", " ")
    assert "pyproject.toml" in pipeline

    def fires(manifest: str, tmp: Path) -> bool:
        (tmp / "pyproject.toml").write_text(manifest, encoding="utf-8")
        return (
            subprocess.run(
                ["sh", "-c", pipeline], cwd=tmp, capture_output=True, text=True
            ).returncode
            == 0
        )

    with tempfile.TemporaryDirectory() as directory:
        tmp = Path(directory)
        commented = (
            'dependencies = [\n    # anthropic and pypdfium2 are extras\n    "mcp>=1.28",\n]\n'
        )
        assert not fires(commented, tmp), "a comment mentioning the library must not fire the gate"
        declared = 'dependencies = [\n    "mcp>=1.28",\n    "anthropic>=1.0",\n]\n'
        assert fires(declared, tmp), (
            "stripping comments has silenced the gate — a real core entry no longer fires it"
        )
        assert fires('dependencies = [\n    "pypdfium2>=5.12",\n]\n', tmp), (
            "the pdf half of the gate no longer fires either"
        )


def test_no_step_that_resolves_fresh_can_be_switched_off() -> None:
    """`if:` is the obvious way to disable a step; `continue-on-error:` is the quiet one — the
    step fails, the job carries on, and everything after it runs as though it had passed.

    These steps are the entire fresh-resolve leg. Each reads correctly with either key attached,
    because neither touches the step's body, so nothing else here would notice. Found by the
    second review's mutation battery, 20260822. The **job** carrying either key is the same edit
    one level up and is asserted in the two tests above.
    """
    import yaml

    document = yaml.safe_load(_workflow())
    guarded = [
        step
        for step in document["jobs"]["build"]["steps"]
        if "wheel_import_gate.py" in str(step.get("run", ""))
        or "mcp_handshake_gate.py" in str(step.get("run", ""))
    ]
    # Four: two wheel-import steps and two handshake steps, each pair being the gate and the run
    # that watches it fail. The selector names the two *tools* — it read `pnk serve` until the
    # handshake became a script that spawns `pnk` itself, at which point it silently stopped
    # matching the steps it exists to guard and the floor is what said so.
    assert len(guarded) >= 4, f"the fresh-resolve leg has shrunk to {len(guarded)} step(s)"
    for step in guarded:
        disabling = {"if", "continue-on-error"} & set(step)
        assert not disabling, f"{step.get('name')!r} carries {sorted(disabling)}"


def test_every_invocation_of_the_wheel_import_gate_carries_its_floor_and_its_sentinel() -> None:
    """`--min-modules` and `--require` are the two flags that stop a walk finding nothing from
    reading exactly like a clean run, and both live at the call site rather than in the tool.

    Five call sites across three files, so "the flag is present" was true of the file the last
    edit touched and unpinned everywhere else: deleting `--min-modules 50` from any one of them
    survived every test, and the tool then falls silently back to a default of 20 against a
    package of 57 modules. Asserted per invocation, not per file — and by value, because
    `--min-modules 1` survived too.
    """
    sources = {
        path: (Path(__file__).parent.parent / path).read_text(encoding="utf-8")
        for path in (".github/workflows/ci.yml", ".github/workflows/release.yml", "Makefile")
    }
    invocations = 0
    for path, text in sources.items():
        # An invocation is a command line naming the script; the continuation lines that follow
        # carry its flags, so the block is read up to the first line that does not continue.
        lines = text.splitlines()
        for index, line in enumerate(lines):
            if "wheel_import_gate.py" not in line or line.lstrip().startswith("#"):
                continue
            block = [line]
            while block[-1].rstrip().endswith("\\") and index + len(block) < len(lines):
                block.append(lines[index + len(block)])
            joined = " ".join(block)
            invocations += 1
            floor = re.search(r"--min-modules (\d+)", joined)
            assert floor is not None, f"{path}: an invocation with no floor: {joined!r}"
            # The **value**, not only the flag. `--min-modules 1` survived every test, which is
            # the defect the flag exists for, one step in. The number that matters: a walk that
            # stopped at the top level finds 31 of the package's 57 modules and still satisfies
            # `--require pinakes.serve`, because `serve` is top-level. Anything above 31 catches
            # it; 40 keeps headroom in both directions.
            assert int(floor.group(1)) >= 40, (
                f"{path}: a floor of {floor.group(1)} is below the 31 modules a walk that "
                f"stopped at the top level would still find: {joined!r}"
            )
            assert "--require pinakes.serve" in joined, (
                f"{path}: an invocation with no sentinel: {joined!r}"
            )
    assert invocations >= 5, f"only {invocations} invocation(s) found; the call sites have moved"


def test_make_smoke_exercises_the_wheel_rather_than_only_its_version() -> None:
    """`make smoke`'s help text says *what release does*, and for 45 releases what it did was
    `pnk --version` — a fresh resolve asked one question that touches no dependency.

    It is the local pre-tag check a maintainer runs, so it must carry the same two checks the two
    workflows do. And the output must not go into a pipe: `pnk serve | grep -q` returns *grep's*
    status, and grep closing the pipe on its first match kills the server with a BrokenPipeError
    that the target then reports as success — measured 20260822, printing a 70-line traceback and
    exiting 0.
    """
    makefile = (Path(__file__).parent.parent / "Makefile").read_text(encoding="utf-8")
    target = re.search(r"^smoke:.*?\n(?P<body>(?:\t.*\n|\n)*)", makefile, re.MULTILINE)
    assert target is not None, "the Makefile has no smoke target"
    body = target.group("body")
    assert "tools/wheel_import_gate.py" in body, "make smoke no longer imports the wheel"
    assert '"method":"initialize"' in body, "make smoke no longer drives a handshake"
    assert "serverInfo" in body, "nothing asserts the server answered"
    assert "pinakes_search" in body, "nothing asserts it registered any tools"
    # Continuation lines joined first: the pipe that caused this lived on the line *after*
    # `pnk serve`, so a per-line check saw nothing and reintroducing `| tee` survived the battery.
    # The same shape as reading a sequence rather than a neighbourhood.
    logical = re.sub(r"\\\n\s*", " ", body)
    piped = [line for line in logical.splitlines() if "pnk serve" in line and "|" in line]
    assert not piped, (
        f"pnk serve's output is piped, so the target reports the last stage's exit status and a "
        f"`grep -q` closing the pipe kills the server it is reading: {piped}"
    )
    # make has its own `continue-on-error`, and it is one character: a recipe line beginning `-`
    # has its exit status ignored. Prefixing either `grep` restored the exact defect the pipe fix
    # removed — the target printing "answers an MCP handshake" over a check that failed, exit 0.
    # Over `logical`, not over the raw body: a continuation line carrying `--require` starts with
    # a hyphen and is not a recipe line at all.
    ignored = [line for line in logical.splitlines() if line.lstrip("\t").startswith("-")]
    assert not ignored, f"make is told to ignore the exit status of: {ignored}"
