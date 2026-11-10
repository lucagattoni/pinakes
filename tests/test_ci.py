"""`pnk init --ci` — the workflow §6.3 designed in v0.1 and I6b finally writes."""

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


def loads_the_models_between_the_sync_and_the_health_check(workflow: str) -> bool:
    """`pnk doctor` loads models `--offline` and downloads none, and `pnk sync` loads only the
    embedder, so on a cold model cache the health check fails unless something loaded the models
    online first. The order is read from the commands the steps run, not from their names."""
    commands = [str(step.get("run", "")) for step in _steps(workflow)]
    sync = [i for i, command in enumerate(commands) if "pnk sync" in command]
    search = [i for i, command in enumerate(commands) if "pnk search" in command]
    doctor = [i for i, command in enumerate(commands) if "pnk doctor" in command]
    assert len(sync) == 1 and len(doctor) == 1, commands
    return (
        bool(search) and sync[0] < search[0] < doctor[0] and "--offline" not in commands[search[0]]
    )


_LOAD_THE_MODELS = (
    "      - name: Load the models\n"
    "        run: uvx --from 'pinakes[light,pdf]' pnk search warm-up -k 1\n"
)


def test_the_workflow_loads_the_models_between_the_sync_and_the_health_check() -> None:
    assert _LOAD_THE_MODELS in WORKFLOW
    assert loads_the_models_between_the_sync_and_the_health_check(WORKFLOW)


def test_the_check_notices_a_workflow_that_never_loads_the_models_or_loads_them_too_late() -> None:
    """A checker that cannot fail verifies nothing: the workflow as it stood, which failed its
    health check on every cold cache, and one that loads the models after it."""
    without = WORKFLOW.replace(_LOAD_THE_MODELS + "\n", "")
    assert without != WORKFLOW
    assert not loads_the_models_between_the_sync_and_the_health_check(without)

    late = WORKFLOW.replace(_LOAD_THE_MODELS + "\n", "") + "\n" + _LOAD_THE_MODELS
    assert late != WORKFLOW
    assert not loads_the_models_between_the_sync_and_the_health_check(late)


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
