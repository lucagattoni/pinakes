"""The repository's own CI: its `eval` job scores a question before `pnk doctor` asks for a model.

`pnk doctor` loads models `--offline` and downloads none (0.32.9), and `pnk sync` loads only the
embedder. The reranker therefore first reaches the model cache when the evaluation scores a
question.
With the health check ahead of the evaluation, the first run after the cache expired failed on
`FAIL reranker` (run 42861945592, 20261110), and a failed job skips the cache's save step.

The order is a fact about a YAML file, so the checker reads the file. A checker that cannot fail
verifies nothing, so a second test feeds it the order that failed.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CI = REPO / ".github" / "workflows" / "ci.yml"

EVALUATION = "Golden-set evaluation against the baseline"
HEALTH_CHECK = "Health check"

#: The `eval` job's block: from its key at two spaces of indent to the next job's key.
_EVAL_JOB = re.compile(r"^  eval:\n(?P<body>.*?)(?=^  [\w-]+:\n|\Z)", re.MULTILINE | re.DOTALL)
_STEP_NAME = re.compile(r"^ +- name: (?P<name>.+?)\s*$", re.MULTILINE)


def eval_step_names(workflow: str) -> list[str]:
    """The names of the `eval` job's steps, in order."""
    job = _EVAL_JOB.search(workflow)
    assert job is not None, "no `eval` job in the workflow"
    return _STEP_NAME.findall(job.group("body"))


def evaluation_precedes_health_check(workflow: str) -> bool:
    names = eval_step_names(workflow)
    assert EVALUATION in names, f"the eval job has no step named {EVALUATION!r}: {names}"
    assert HEALTH_CHECK in names, f"the eval job has no step named {HEALTH_CHECK!r}: {names}"
    return names.index(EVALUATION) < names.index(HEALTH_CHECK)


#: The eval job as it stood when it failed on a cold cache: health check ahead of the evaluation.
_THE_ORDER_THAT_FAILED = """\
jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - name: Cache model weights
      - name: Index the demo KB
      - name: Health check
      - name: Golden-set evaluation against the baseline

  pdf-eval:
    steps:
      - name: Golden-set evaluation against the baseline
"""


def test_the_eval_job_scores_a_question_before_it_asks_doctor_for_the_reranker() -> None:
    assert evaluation_precedes_health_check(CI.read_text(encoding="utf-8"))


def test_the_check_notices_the_order_that_failed_on_a_cold_cache() -> None:
    assert not evaluation_precedes_health_check(_THE_ORDER_THAT_FAILED)
    # ...and reads the right job: `pdf-eval` below it has an evaluation step and no health check.
    assert eval_step_names(_THE_ORDER_THAT_FAILED) == [
        "Cache model weights",
        "Index the demo KB",
        "Health check",
        "Golden-set evaluation against the baseline",
    ]
