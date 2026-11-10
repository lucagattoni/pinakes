"""The repository's own CI: its `eval` job runs the evaluation before `pnk doctor`.

`pnk doctor` loads models `--offline` and downloads none (0.32.9), and `pnk sync` loads only the
embedder. The reranker therefore first reaches the model cache when the evaluation loads it, which
it does once the golden set has a question to score. With the health check ahead of the
evaluation, the first run after the cache expired failed on `FAIL reranker` (job 129990126135 of
run 42861945592, 20261110 17:09 UTC), and a failed job skips the cache's save step.

The order is a fact about a YAML file, so the checker reads the file, and it reads the commands the
steps run and not their names: a renamed step must not change the verdict. A checker that cannot
fail verifies nothing, so the other tests feed it the order that failed and a step it cannot judge.
"""

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
CI = REPO / ".github" / "workflows" / "ci.yml"

#: The `eval` job's block: from its key at two spaces of indent to the next job's key.
_EVAL_JOB = re.compile(r"^  eval:\n(?P<body>.*?)(?=^  [\w-]+:\n|\Z)", re.MULTILINE | re.DOTALL)
_RUN = re.compile(r"^(?:- )?run: (?P<command>.+)$")


def eval_job_commands(workflow: str) -> list[str]:
    """The single-line `run:` commands of the `eval` job, in order, comments left out.

    A conditional step is refused: with an `if:` on it, the order of the commands would not say
    which of them runs.
    """
    job = _EVAL_JOB.search(workflow)
    assert job is not None, "no `eval` job in the workflow"
    commands: list[str] = []
    for line in job.group("body").splitlines():
        text = line.strip()
        if text.startswith("#"):
            continue
        assert not text.startswith("if:"), (
            "a conditional step in the eval job: the order checked here would not mean what it says"
        )
        match = _RUN.match(text)
        if match:
            commands.append(match.group("command"))
    return commands


def evaluation_precedes_health_check(workflow: str) -> bool:
    commands = eval_job_commands(workflow)
    evaluation = [i for i, command in enumerate(commands) if "-m pinakes.eval" in command]
    health = [i for i, command in enumerate(commands) if "pnk doctor" in command]
    assert len(evaluation) == 1 and len(health) == 1, f"expected one of each in {commands}"
    return evaluation[0] < health[0]


#: The eval job as it stood when it failed on a cold cache: health check ahead of the evaluation.
#: `pdf-eval` below it runs its own evaluation, to show the checker stops at the job's end.
_THE_ORDER_THAT_FAILED = """\
jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - name: Cache model weights
        uses: actions/cache@v4
      - name: Index the demo KB
        run: uv run --frozen pnk sync --kb tests/demo-kb
      - name: Health check
        run: uv run --frozen pnk doctor --kb tests/demo-kb
      - name: Golden-set evaluation against the baseline
        run: uv run --frozen python -m pinakes.eval tests/demo-kb

  pdf-eval:
    steps:
      - name: Golden-set evaluation
        run: uv run --frozen python -m pinakes.eval tests/pdf-corpus
"""


def test_the_eval_job_runs_the_evaluation_before_it_asks_doctor_for_the_reranker() -> None:
    assert evaluation_precedes_health_check(CI.read_text(encoding="utf-8"))


def test_the_check_notices_the_order_that_failed_on_a_cold_cache() -> None:
    assert not evaluation_precedes_health_check(_THE_ORDER_THAT_FAILED)
    # ...and reads the right job: the `pdf-eval` evaluation below it is not counted.
    assert eval_job_commands(_THE_ORDER_THAT_FAILED) == [
        "uv run --frozen pnk sync --kb tests/demo-kb",
        "uv run --frozen pnk doctor --kb tests/demo-kb",
        "uv run --frozen python -m pinakes.eval tests/demo-kb",
    ]


def test_a_conditional_step_is_refused_rather_than_trusted() -> None:
    conditional = _THE_ORDER_THAT_FAILED.replace(
        "      - name: Golden-set evaluation against the baseline\n",
        "      - name: Golden-set evaluation against the baseline\n        if: ${{ false }}\n",
    )
    assert conditional != _THE_ORDER_THAT_FAILED
    with pytest.raises(AssertionError, match="conditional step"):
        evaluation_precedes_health_check(conditional)
