"""`pnk init --ci` — the workflow §6.3 designed in v0.1 and I6b finally writes."""

import re
from pathlib import Path
from typing import Any

import pytest

from pinakes.ci import WORKFLOW, WORKFLOW_PATH, write_workflow
from pinakes.cli import EXIT_FAILURE, EXIT_OK, main
from pinakes.errors import InitError
from pinakes.hooks import FREE_BACKEND_FLAG
from pinakes.init import init


def test_init_without_ci_writes_no_workflow(tmp_path: Path) -> None:
    result = init(tmp_path / "kb", now="20260728 12:00")
    assert result.workflow is None
    assert not (result.root / WORKFLOW_PATH).exists()


def test_init_ci_writes_the_workflow_and_reports_it(tmp_path: Path) -> None:
    result = init(tmp_path / "kb", now="20260728 12:00", ci=True)
    assert result.workflow == result.root / WORKFLOW_PATH
    assert result.workflow in result.created
    assert result.workflow.is_file()


def test_the_workflow_forces_the_free_backend(tmp_path: Path) -> None:
    """CI is the most non-interactive caller there is: no terminal to answer a confirmation from,
    and no CI job in this project ever holds an API key."""
    result = init(tmp_path / "kb", now="20260728 12:00", ci=True)
    body = result.workflow.read_text(encoding="utf-8") if result.workflow else ""
    assert f"pnk sync {FREE_BACKEND_FLAG}" in body
    assert "must never spend" in body


def test_the_workflow_and_the_hooks_cannot_disagree() -> None:
    """One constant, two writers. Two literals would be two places for the forced backend to
    drift, and the drift would be invisible until a CI run spent money."""
    assert WORKFLOW.count(FREE_BACKEND_FLAG) >= 1
    assert "--extract=claude-vision" not in WORKFLOW


def test_the_workflow_caches_the_state_directory_that_holds_the_ledger(tmp_path: Path) -> None:
    result = init(tmp_path / "kb", now="20260728 12:00", ci=True)
    body = result.workflow.read_text(encoding="utf-8") if result.workflow else ""
    assert "path: .pinakes" in body


def test_an_existing_workflow_is_never_overwritten(tmp_path: Path) -> None:
    """The same trust rule `install-hooks` applies to a foreign git hook: it may be hand-edited,
    so it is refused rather than clobbered."""
    root = tmp_path / "kb"
    target = root / WORKFLOW_PATH
    target.parent.mkdir(parents=True)
    target.write_text("# mine\n", encoding="utf-8")

    with pytest.raises(InitError) as exc_info:
        write_workflow(root)
    assert "never overwritten" in exc_info.value.remedy
    assert target.read_text(encoding="utf-8") == "# mine\n"


def test_the_cli_flag_is_wired_and_says_what_it_did(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["init", str(tmp_path / "kb"), "--ci"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "workflow:" in out
    assert FREE_BACKEND_FLAG in out
    assert (tmp_path / "kb" / WORKFLOW_PATH).is_file()


def test_init_ci_refuses_a_directory_that_already_holds_the_workflow(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`init` refuses an existing workflow; this asserts the *reported* failure rather than a
    traceback, which is the only difference a user sees.

    It used to be refused as "not empty" — incidentally, by a blanket emptiness check that has
    since been removed so a directory with content can be adopted (20260805). The refusal now
    names the workflow itself, which is both more precise and the only thing actually in the way.
    """
    root = tmp_path / "kb"
    (root / WORKFLOW_PATH).parent.mkdir(parents=True)
    (root / WORKFLOW_PATH).write_text("# mine\n", encoding="utf-8")

    assert main(["init", str(root), "--ci"]) == EXIT_FAILURE
    assert "already exists" in capsys.readouterr().err


def test_the_generated_workflow_is_valid_yaml(tmp_path: Path) -> None:
    """The interpolated cache key carries literal `${{ }}`, which is exactly the shape an f-string
    breaks. Parsing it is how that stays true."""
    import yaml

    result = init(tmp_path / "kb", now="20260728 12:00", ci=True)
    assert result.workflow is not None
    parsed = yaml.safe_load(result.workflow.read_text(encoding="utf-8"))
    steps = parsed["jobs"]["sync"]["steps"]
    cache = next(step for step in steps if step.get("uses", "").startswith("actions/cache"))
    assert "${{ runner.os }}" in cache["with"]["key"]
    assert "${{ hashFiles(" in cache["with"]["key"]
    assert cache["with"]["path"] == ".pinakes"


def test_the_init_line_describes_the_workflow_not_the_hooks(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """One notice, two writers. Printing "hooks run …" beneath a line announcing a workflow
    describes a different file from the one just written."""
    assert main(["init", str(tmp_path / "kb"), "--ci"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "workflow:" in out
    assert "hooks" not in out


def _steps(workflow: str) -> list[dict[str, Any]]:
    import yaml

    return yaml.safe_load(workflow)["jobs"]["sync"]["steps"]


#: A step whose whole `run:` is one `pnk` invocation through `uvx`. Anything else (an `echo`, a
#: block of several commands) is not counted as one.
_INVOCATION = re.compile(r"^uvx --from '[^']+' pnk (?P<verb>sync|search|doctor)\b(?P<rest>[^\n]*)$")


def loads_the_models_between_the_sync_and_the_health_check(workflow: str) -> bool:
    """`pnk doctor` loads models `--offline` and downloads none, and `pnk sync` loads only the
    embedder, so on a cold model cache the health check fails unless something loaded the models
    online first. The order is read from the commands the steps run, not from their names.

    A step that is conditional, or that chains another command after the invocation (`|| true`,
    `&&`, a pipe), is refused: the order would no longer say what runs.
    """
    invocations: list[tuple[str, str]] = []
    for step in _steps(workflow):
        run = str(step.get("run", ""))
        found = _INVOCATION.match(run)
        if found is None:
            continue
        assert "if" not in step and "continue-on-error" not in step, f"a conditional step: {run}"
        assert re.search(r"[|;&]", found.group("rest")) is None, f"a chained command: {run}"
        invocations.append((found.group("verb"), run))
    verbs = [verb for verb, _ in invocations]
    assert verbs.count("sync") == 1 and verbs.count("doctor") == 1, verbs
    if "search" not in verbs:
        return False
    search = verbs.index("search")
    return (
        verbs.index("sync") < search < verbs.index("doctor")
        and "--offline" not in invocations[search][1]
    )


#: The step that runs the search, found by what it runs and not by its name or its arguments, so
#: that renaming the step or changing the query does not break the tests that cut it out.
_LOAD_STEP = re.compile(
    r"^      - name: [^\n]+\n        run: [^\n]*pnk search[^\n]*\n\n", re.MULTILINE
)


def test_the_workflow_loads_the_models_between_the_sync_and_the_health_check() -> None:
    assert _LOAD_STEP.search(WORKFLOW) is not None
    assert loads_the_models_between_the_sync_and_the_health_check(WORKFLOW)


def test_the_check_notices_a_workflow_that_never_loads_the_models_or_loads_them_too_late() -> None:
    """A checker that cannot fail verifies nothing: the workflow as it stood, which failed its
    health check on every cold cache, and one that loads the models after it."""
    step = _LOAD_STEP.search(WORKFLOW)
    assert step is not None
    without = WORKFLOW.replace(step.group(0), "")
    assert without != WORKFLOW
    assert not loads_the_models_between_the_sync_and_the_health_check(without)

    late = without + "\n" + step.group(0).rstrip("\n") + "\n"
    assert late != WORKFLOW
    assert not loads_the_models_between_the_sync_and_the_health_check(late)


def test_a_conditional_or_chained_load_step_is_refused_rather_than_trusted() -> None:
    """Each of these keeps the commands in the right order and makes the step unable to load the
    models: a condition that is never true, a failure swallowed by `|| true`, and a command that is
    only echoed. The checker must not call any of them a pass."""
    step = _LOAD_STEP.search(WORKFLOW)
    assert step is not None
    text = step.group(0)
    conditional = WORKFLOW.replace(
        text, text.replace("        run:", "        if: ${{ false }}\n        run:")
    )
    swallowed = WORKFLOW.replace(text, re.sub(r"(pnk search[^\n]*)", r"\1 || true", text))
    echoed = WORKFLOW.replace(
        text, '      - name: Load the models\n        run: echo "pnk search"\n\n'
    )
    for variant in (conditional, swallowed):
        assert variant != WORKFLOW
        with pytest.raises(AssertionError, match=r"conditional step|chained command"):
            loads_the_models_between_the_sync_and_the_health_check(variant)
    assert echoed != WORKFLOW
    assert not loads_the_models_between_the_sync_and_the_health_check(echoed)


def test_the_search_output_is_discarded_because_an_actions_log_can_be_public() -> None:
    """A search prints passage text (`docs/DOGFOODING.md` warns of it), and the log of a public
    repository's workflow run is public. The models still load: progress goes to stderr."""
    assert re.search(r"pnk search[^\n]*> /dev/null\n", WORKFLOW) is not None


def test_the_workflow_caches_the_model_weights_under_a_key_of_its_own() -> None:
    caches = [step for step in _steps(WORKFLOW) if step.get("uses", "").startswith("actions/cache")]
    index = next(step for step in caches if step["with"]["path"] == ".pinakes")
    models = next(step for step in caches if step["with"]["path"] == "~/.cache/huggingface")
    assert models["with"]["key"].startswith("pinakes-models-${{ runner.os }}-")
    assert "hashFiles('pinakes.toml')" in models["with"]["key"]
    # Restoring the index must never restore the weights, or the other way round: neither key may
    # sit under the other's restore prefix.
    assert not models["with"]["key"].startswith(index["with"]["restore-keys"])
    assert not index["with"]["key"].startswith(models["with"]["restore-keys"])
    # `startswith` is vacuous against a multi-line restore-keys block, which is never a prefix of a
    # key: both must be one line for the two assertions above to mean anything.
    assert "\n" not in index["with"]["restore-keys"]
    assert "\n" not in models["with"]["restore-keys"]
    # It must save as well as restore (`actions/cache/restore` would not), and be restored before
    # anything loads a model.
    assert models["uses"].startswith("actions/cache@")
    steps = _steps(WORKFLOW)
    sync = next(i for i, step in enumerate(steps) if "pnk sync" in str(step.get("run", "")))
    assert steps.index(models) < sync
