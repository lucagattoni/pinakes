"""`.claude/workflows/adversarial-review.js`, run with stub hooks by `review_workflow_harness.mjs`.

**The defect these tests exist to catch is a review that cannot say whether anyone looked.** The
runtime returns `null` for an agent that died and the documented idiom for collecting a fan-out is
`.filter(Boolean)`, so the obvious script turns a dead agent into an absent finding: 17 of 19 agents
died on a session limit once and the run returned `{"raised":0,"confirmed":[],"refuted":[]}`
(`REVIEW-FINDINGS-RECOVERED.md`). Every test that kills something therefore asserts the *stated
reason* and not only the verdict, and `test_a_complete_pass_is_clean` is the control: a script that
always answered PARTIAL fails it, and a script that never did fails every other test here.

**A reply is only evidence if it is the shape that was asked for**, and the schemas are enforced by
the runtime, not by the script. So a block of tests feeds the script replies the schema forbids -
a lens with no `findings`, a refuter whose `refuted` is the string `"false"`, a ruling with no
`real` - and asserts the pass is PARTIAL and not CLEAN. An earlier version of this file had none of
them, and a mutation that gutted every schema survived all of its tests.

The harness runs the script file itself, so these tests exercise its control flow - which lens
starts first, what is counted before what is filtered, which model each call names, whether a
lens's refuters wait for the other lenses. They cannot exercise the real fan-out, which has not
been run yet (the first live run is the smoke run planned in
`plans/20261018_2354-option-a-review-coverage-and-claude-md.md`). The harness is itself an
instrument, so it has tests that show it can fail: it must refuse what the runtime refuses.

Node is required for the tests that run the script. Locally a machine without it skips them; under
`CI` a runner without it fails, so an image change cannot turn this gate into a skip nobody reads.
"""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).parent.parent
SCRIPT = ROOT / ".claude" / "workflows" / "adversarial-review.js"
HARNESS = Path(__file__).parent / "review_workflow_harness.mjs"
NODE = shutil.which("node")

LENS_ORDER = ["runtime", "missing-set", "population", "docs-vs-tree"]
SHA = "abc1234"
BASE = "def5678"
ARGS: dict[str, Any] = {"sha": SHA, "base": BASE}

#: "no `checks` argument", distinct from `None`: a test that passes `None` means a reply whose
#: `checks_run` is null, and a helper that read `None` as "use the default" would never send it.
DEFAULT: Any = object()


def node(
    mode: str,
    payload: object = None,
    raw: str | None = None,
    script: Path | None = None,
) -> dict[str, Any]:
    if NODE is None and not os.environ.get("CI"):
        pytest.skip("node is not installed; the review workflow is JavaScript and is run with it")
    env = os.environ | ({"REVIEW_WORKFLOW_PATH": str(script)} if script else {})
    stdin = raw if raw is not None else (json.dumps(payload) if payload is not None else None)
    done = subprocess.run(
        [NODE or "node", str(HARNESS), mode],
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert done.returncode == 0, done.stdout + done.stderr
    out: dict[str, Any] = json.loads(done.stdout)
    return out


def review(
    replies: dict[str, Any],
    args: dict[str, Any] | None = None,
    delays: dict[str, int] | None = None,
    allow_missing: bool = False,
) -> dict[str, Any]:
    out = node(
        "run",
        {"args": ARGS if args is None else args, "replies": replies, "delays": delays or {}},
    )
    if not allow_missing:
        # pipeline() and parallel() absorb a throw, so a scenario that forgot a reply would read
        # as a dead agent and a PARTIAL-expecting test would pass for the wrong reason.
        assert out["missing"] == [], f"scenario has no reply for {out['missing']}"
    return out


def lens(
    findings: list[dict[str, Any]] | None = None,
    not_run: list[str] | None = None,
    checks: Any = DEFAULT,
    diff_files: int = 3,
) -> dict[str, Any]:
    return {
        "diff_files": diff_files,
        "checks_run": ["rg -n foo src"] if checks is DEFAULT else checks,
        "not_run": not_run or [],
        "findings": findings or [],
    }


def finding(claim: str = "a claim", severity: str = "medium") -> dict[str, Any]:
    return {
        "claim": claim,
        "severity": severity,
        "file": "src/pinakes/sync.py",
        "line": 12,
        "evidence": "ran pnk sync; it printed 0 removed",
    }


def verdict(refuted: bool, commands: Any = None, basis: str = "checked") -> dict[str, Any]:
    return {
        "refuted": refuted,
        "basis": basis,
        "commands_run": ["ls -la docs"] if commands is None else commands,
        "observed": "the directory lists the file",
    }


def ruling(id_: str, real: bool = True, severity: str = "high") -> dict[str, Any]:
    return {"id": id_, "real": real, "severity": severity, "rationale": "reproduced it"}


def everyone_returns() -> dict[str, Any]:
    return {f"lens:{key}": lens() for key in LENS_ORDER}


def one_survivor(judge: Any) -> dict[str, Any]:
    """A runtime finding no refuter could kill, with the judge's reply supplied."""
    return everyone_returns() | {
        "lens:runtime": lens([finding("pnk sync deletes a file")]),
        "refute:runtime-1": verdict(False),
        "judge": judge,
    }


def labels(out: dict[str, Any]) -> list[str]:
    return [c["label"] for c in out["calls"]]


# --- the control, then the deaths --------------------------------------------------------------


def test_a_complete_pass_is_clean() -> None:
    """The control. Every lens returned and nothing was raised: CLEAN, with nothing said missing,
    and with the checks each lens says it ran shown to whoever reads the verdict."""
    out = review(everyone_returns())
    assert out["ok"], out
    result = out["result"]
    assert result["coverage"] == "CLEAN"
    assert result["lenses"]["died"] == []
    assert result["lenses"]["returned"] == LENS_ORDER
    assert result["unrefuted"] == [] and result["unjudged"] == [] and result["not_run"] == {}
    assert result["checks"] == {key: ["rg -n foo src"] for key in LENS_ORDER}
    assert "NOT a clean pass" not in result["note"]


def test_a_dead_lens_is_partial_not_clean() -> None:
    """A lens returned null, `.filter(Boolean)` would erase it, and the remaining three found
    nothing. That must not read as a clean bill."""
    replies = everyone_returns() | {"lens:runtime": "__dead__"}
    result = review(replies)["result"]
    assert result["coverage"] == "PARTIAL"
    assert result["lenses"]["died"] == ["runtime"]
    assert result["lenses"]["returned"] == ["missing-set", "population", "docs-vs-tree"]
    assert "runtime" not in result["checks"]
    assert "NOT a clean pass" in result["note"] and "1 of 4 lenses died" in result["note"]


def test_every_lens_dead_is_vacuous_and_not_clean() -> None:
    """17 of 19 agents died and the run said {"raised":0}. Nobody looked: VACUOUS, which is a
    different outcome from CLEAN and not a smaller one."""
    replies = {f"lens:{key}": "__dead__" for key in LENS_ORDER}
    result = review(replies)["result"]
    assert result["coverage"] == "VACUOUS"
    assert result["lenses"]["died"] == LENS_ORDER
    assert result["raised"] == 0 and result["confirmed"] == []


def test_a_lens_that_throws_is_a_dead_lens() -> None:
    """pipeline() drops an item whose stage throws to null. That is a dead lens like any other."""
    replies = everyone_returns() | {"lens:population": "__throw__"}
    result = review(replies)["result"]
    assert result["coverage"] == "PARTIAL"
    assert result["lenses"]["died"] == ["population"]


def test_a_lens_that_ran_nothing_is_dead_not_clean() -> None:
    """The quiet failure: an agent that completed and returned an empty result. An empty
    `checks_run` is silence, and an empty findings list from silence is not a result."""
    replies = everyone_returns() | {"lens:missing-set": lens(checks=[])}
    result = review(replies)["result"]
    assert result["coverage"] == "PARTIAL"
    assert result["lenses"]["died"] == ["missing-set"]


@pytest.mark.parametrize("checks", [[""], ["   "], [None], [3], ["ab"], "ls docs", None])
def test_a_check_that_is_blank_or_not_a_string_does_not_count_as_a_check(checks: Any) -> None:
    """`items` has no `minLength` in a schema nobody enforces here: `[""]` would otherwise be a lens
    that 'ran' something."""
    replies = everyone_returns() | {"lens:runtime": lens(checks=checks)}
    result = review(replies)["result"]
    assert result["coverage"] == "PARTIAL"
    assert result["lenses"]["died"] == ["runtime"]


def test_a_lens_that_saw_an_empty_diff_reviewed_nothing() -> None:
    """Once an increment lands, `origin/main...<sha>` is empty. A lens that reports it saw no files
    looked at nothing, whatever it says it ran."""
    replies = everyone_returns() | {"lens:docs-vs-tree": lens(diff_files=0)}
    result = review(replies)["result"]
    assert result["coverage"] == "PARTIAL"
    assert "empty diff" in result["not_run"]["docs-vs-tree"][0]
    assert result["lenses"]["died"] == []


def test_an_unrun_probe_is_partial_even_though_every_lens_returned() -> None:
    """A runtime lens that could not build its KB returned - and checked nothing that matters."""
    replies = everyone_returns() | {"lens:runtime": lens(not_run=["could not build a KB: no uv"])}
    result = review(replies)["result"]
    assert result["coverage"] == "PARTIAL"
    assert result["lenses"]["died"] == []
    assert result["not_run"] == {"runtime": ["could not build a KB: no uv"]}


@pytest.mark.parametrize(
    "reply",
    [
        {"diff_files": 3, "checks_run": ["rg -n x src"], "not_run": []},
        {"diff_files": 3, "checks_run": ["rg -n x src"], "not_run": [], "findings": None},
        {"diff_files": 3, "checks_run": ["rg -n x src"], "not_run": [], "findings": "none"},
        {"diff_files": 3, "checks_run": ["rg -n x src"], "findings": []},
        {"diff_files": 3, "checks_run": ["rg -n x src"], "not_run": {"a": 1}, "findings": []},
        {"diff_files": 3, "checks_run": ["rg -n x src"], "not_run": [4], "findings": []},
        {"checks_run": ["rg -n x src"], "not_run": [], "findings": []},
        {"diff_files": "3", "checks_run": ["rg -n x src"], "not_run": [], "findings": []},
        {"diff_files": -1, "checks_run": ["rg -n x src"], "not_run": [], "findings": []},
        "no problems found",
        [],
        {},
    ],
)
def test_a_lens_reply_the_schema_forbids_is_a_dead_lens(reply: Any) -> None:
    """The schema is enforced by the runtime, not by this file. If it ever is not, a reply with no
    `findings` must not read as a lens that found nothing."""
    result = review(everyone_returns() | {"lens:runtime": reply})["result"]
    assert result["coverage"] == "PARTIAL"
    assert result["lenses"]["died"] == ["runtime"]


@pytest.mark.parametrize(
    "bad",
    [
        {"severity": "medium", "file": "a.py", "evidence": "x ran"},
        {"claim": "  ", "severity": "medium", "file": "a.py", "evidence": "x ran"},
        {"claim": "c", "severity": "critical", "file": "a.py", "evidence": "x ran"},
        {"claim": "c", "severity": "low", "file": "a.py", "evidence": ""},
        {"claim": "c", "severity": "low", "file": "a.py", "evidence": "x ran", "line": "12"},
    ],
)
def test_a_malformed_finding_makes_the_whole_lens_unusable(bad: dict[str, Any]) -> None:
    replies = everyone_returns() | {"lens:runtime": lens([finding(), bad])}
    result = review(replies)["result"]
    assert result["coverage"] == "PARTIAL"
    assert result["lenses"]["died"] == ["runtime"]
    assert result["raised"] == 0


# --- refuters and the judge --------------------------------------------------------------------


def test_a_finding_whose_refuter_died_is_unrefuted_not_dropped() -> None:
    replies = everyone_returns() | {
        "lens:runtime": lens([finding("pnk sync deletes a file")]),
        "refute:runtime-1": "__dead__",
    }
    result = review(replies)["result"]
    assert result["coverage"] == "PARTIAL"
    assert [f["id"] for f in result["unrefuted"]] == ["runtime-1"]
    assert "refuter died" in result["unrefuted"][0]["reason"]
    assert result["confirmed"] == [] and result["refuted"] == []
    assert result["raised"] == 1


def test_a_refutation_without_a_command_is_not_a_check() -> None:
    """ "I reasoned about it" is not a check. A verdict that ran nothing neither kills the finding
    nor lets it through: it is unrefuted."""
    replies = everyone_returns() | {
        "lens:runtime": lens([finding()]),
        "refute:runtime-1": verdict(True, commands=[]),
    }
    result = review(replies)["result"]
    assert [f["id"] for f in result["unrefuted"]] == ["runtime-1"]
    assert result["refuted"] == []
    assert result["coverage"] == "PARTIAL"


@pytest.mark.parametrize(
    "reply",
    [
        verdict(True, commands=[""]),
        verdict(True, commands=[None]),
        verdict(True, commands="ls docs"),
        {**verdict(True), "refuted": "false"},
        {**verdict(True), "refuted": None},
        {**verdict(True), "basis": "hunch"},
        {k: v for k, v in verdict(True).items() if k != "basis"},
        {**verdict(True), "observed": "   "},
        "refuted",
        {},
    ],
)
def test_a_verdict_the_schema_forbids_is_no_verdict(reply: Any) -> None:
    """`refuted: "false"` is truthy; a refuter that wrote the word must not kill the finding."""
    replies = everyone_returns() | {
        "lens:runtime": lens([finding()]),
        "refute:runtime-1": reply,
    }
    result = review(replies)["result"]
    assert result["coverage"] == "PARTIAL"
    assert [f["id"] for f in result["unrefuted"]] == ["runtime-1"]
    assert result["refuted"] == [] and result["confirmed"] == []


def test_a_refuted_finding_is_listed_whole_and_the_pass_is_clean() -> None:
    """A finding a refuter killed is reported with everything it was raised with - severity, file,
    line, evidence - and what the refuter ran, and it needs no judge."""
    replies = everyone_returns() | {
        "lens:runtime": lens([finding("a claim the disk contradicts", "high")]),
        "refute:runtime-1": verdict(True),
    }
    out = review(replies)
    result = out["result"]
    assert result["coverage"] == "CLEAN"
    killed = result["refuted"][0]
    assert killed["id"] == "runtime-1" and killed["severity"] == "high"
    assert killed["file"] == "src/pinakes/sync.py" and killed["line"] == 12
    assert killed["evidence"] == "ran pnk sync; it printed 0 removed"
    assert killed["basis"] == "checked" and killed["refuter_commands"] == ["ls -la docs"]
    assert killed["observed"] == "the directory lists the file"
    assert "judge" not in labels(out)


def test_a_refutation_that_rests_on_uncertainty_says_so() -> None:
    """The refuter is told to default to refuted when unsure. That default must not be able to hide
    a high finding behind a bare 'refuted': the basis travels with it."""
    replies = everyone_returns() | {
        "lens:runtime": lens([finding("data loss", "high")]),
        "refute:runtime-1": verdict(True, basis="uncertain"),
    }
    killed = review(replies)["result"]["refuted"][0]
    assert killed["severity"] == "high" and killed["basis"] == "uncertain"


def test_a_survivor_the_judge_confirms_is_a_finding() -> None:
    out = review(one_survivor({"rulings": [ruling("runtime-1", real=True, severity="high")]}))
    result = out["result"]
    assert result["coverage"] == "FINDINGS"
    assert [f["id"] for f in result["confirmed"]] == ["runtime-1"]
    assert result["confirmed"][0]["severity_as_ruled"] == "high"
    judge = next(c for c in out["calls"] if c["label"] == "judge")
    assert "id=runtime-1" in judge["prompt"] and "pnk sync deletes a file" in judge["prompt"]


def test_a_dead_judge_leaves_survivors_unjudged_and_nothing_confirmed() -> None:
    result = review(one_survivor("__dead__"))["result"]
    assert result["coverage"] == "PARTIAL"
    assert [f["id"] for f in result["unjudged"]] == ["runtime-1"]
    assert result["confirmed"] == []


def test_a_judge_that_throws_is_a_dead_judge_and_loses_nothing() -> None:
    """The judge is awaited directly, outside pipeline() and parallel(), so an unguarded throw -
    a budget ceiling, or six stalled attempts - ends the run with the error and every lens result
    with it. A mutation that removed the guard survived the first version of this file."""
    out = review(one_survivor("__throw__"))
    assert out["ok"], out.get("error")
    result = out["result"]
    assert result["coverage"] == "PARTIAL"
    assert [f["id"] for f in result["unjudged"]] == ["runtime-1"]
    assert result["raised"] == 1 and result["checks"]["runtime"]


def test_a_judge_that_rules_on_only_some_survivors_leaves_the_rest_unjudged() -> None:
    replies = everyone_returns() | {
        "lens:runtime": lens([finding("first"), finding("second")]),
        "refute:*": verdict(False),
        "judge": {"rulings": [ruling("runtime-1", real=True)]},
    }
    result = review(replies)["result"]
    assert result["coverage"] == "PARTIAL"
    assert [f["id"] for f in result["confirmed"]] == ["runtime-1"]
    assert [f["id"] for f in result["unjudged"]] == ["runtime-2"]


@pytest.mark.parametrize("order", [(True, False), (False, True)])
def test_two_rulings_on_one_id_that_disagree_leave_it_unjudged(order: tuple[bool, bool]) -> None:
    """Whichever ruling came first must not decide: a judge contradicting itself has not ruled."""
    rulings = [ruling("runtime-1", real=r) for r in order]
    result = review(one_survivor({"rulings": rulings}))["result"]
    assert result["coverage"] == "PARTIAL"
    assert [f["id"] for f in result["unjudged"]] == ["runtime-1"]
    assert result["conflicting_rulings"] == ["runtime-1"]
    assert result["confirmed"] == [] and result["not_real"] == []


def test_two_rulings_on_one_id_that_agree_count_once() -> None:
    rulings = [ruling("runtime-1"), ruling("runtime-1")]
    result = review(one_survivor({"rulings": rulings}))["result"]
    assert result["coverage"] == "FINDINGS"
    assert [f["id"] for f in result["confirmed"]] == ["runtime-1"]
    assert result["conflicting_rulings"] == []


@pytest.mark.parametrize(
    "bad",
    [
        {"id": "runtime-1", "severity": "high", "rationale": "x"},
        {"id": "runtime-1", "real": None, "severity": "high", "rationale": "x"},
        {"id": "runtime-1", "real": "false", "severity": "high", "rationale": "x"},
        {"id": "runtime-1", "real": True, "severity": "critical", "rationale": "x"},
        {"id": "runtime-1", "real": True, "severity": "high", "rationale": "  "},
        {"real": True, "severity": "high", "rationale": "x"},
        "runtime-1 is real",
    ],
)
def test_a_ruling_the_schema_forbids_is_no_ruling(bad: Any) -> None:
    """A ruling with no `real` must not put the finding on the not-real list, and `real: "false"`
    is truthy and must not confirm it."""
    result = review(one_survivor({"rulings": [bad]}))["result"]
    assert result["coverage"] == "PARTIAL"
    assert [f["id"] for f in result["unjudged"]] == ["runtime-1"]
    assert result["confirmed"] == [] and result["not_real"] == []
    assert len(result["ignored_rulings"]) == 1


def test_a_ruling_for_an_id_nobody_raised_is_reported_not_swallowed() -> None:
    rulings = [ruling("runtime-1"), ruling("invented-9")]
    result = review(one_survivor({"rulings": rulings}))["result"]
    assert result["coverage"] == "FINDINGS"
    assert result["ignored_rulings"] == [{"reason": "id matches no survivor", "id": "invented-9"}]


def test_a_judge_that_echoes_the_brackets_around_an_id_is_still_read() -> None:
    result = review(one_survivor({"rulings": [ruling("[runtime-1]")]}))["result"]
    assert [f["id"] for f in result["confirmed"]] == ["runtime-1"]
    assert result["unjudged"] == []


def test_a_judge_ruling_a_finding_not_real_is_listed_and_the_pass_is_clean() -> None:
    result = review(one_survivor({"rulings": [ruling("runtime-1", real=False, severity="low")]}))[
        "result"
    ]
    assert result["coverage"] == "CLEAN"
    assert [r["id"] for r in result["not_real"]] == ["runtime-1"]
    assert result["confirmed"] == []


def test_confirmed_findings_never_hide_a_dead_lens() -> None:
    """Precedence: a pass with findings and a dead lens is PARTIAL, not FINDINGS - the gap is the
    more important fact, and the findings are still in `confirmed`."""
    replies = one_survivor({"rulings": [ruling("runtime-1")]}) | {"lens:docs-vs-tree": "__dead__"}
    result = review(replies)["result"]
    assert result["coverage"] == "PARTIAL"
    assert [f["id"] for f in result["confirmed"]] == ["runtime-1"]


def test_a_lens_that_raises_more_than_the_cap_has_the_rest_listed_not_dropped() -> None:
    """parallel() refuses more than 4,096 thunks and takes the whole lens with it; the cap keeps the
    lens and says what it did not refute."""
    many = [finding(f"claim {i}") for i in range(25)]
    replies = everyone_returns() | {"lens:runtime": lens(many), "refute:*": verdict(True)}
    out = review(replies)
    result = out["result"]
    assert result["raised"] == 25
    assert sum(1 for c in out["calls"] if c["label"].startswith("refute:")) == 20
    assert len(result["refuted"]) == 20 and len(result["unrefuted"]) == 5
    assert all("cap of 20" in f["reason"] for f in result["unrefuted"])
    assert result["coverage"] == "PARTIAL"
    assert any("over the cap" in line for line in out["logs"])


# --- what is launched, in what order, on which model -------------------------------------------


def test_slow_lenses_are_launched_first() -> None:
    """The runtime lens builds a KB and runs a command; it reports last and is the first thing a
    session limit cuts. Launched first, it gets a slot first."""
    out = review(everyone_returns())
    assert labels(out)[:4] == [f"lens:{key}" for key in LENS_ORDER]


def test_refuters_start_without_waiting_for_the_other_lenses() -> None:
    """pipeline(), not a barrier: the docs-vs-tree lens returns at once with a finding while the
    runtime lens is still working, and its refuter must start before the runtime lens finishes."""
    replies = everyone_returns() | {
        "lens:docs-vs-tree": lens([finding("a stale claim")]),
        "refute:docs-vs-tree-1": verdict(True),
    }
    out = review(replies, delays={"lens:runtime": 60})
    by_label = {c["label"]: c for c in out["calls"]}
    assert by_label["refute:docs-vs-tree-1"]["started"] < by_label["lens:runtime"]["finished"]


def test_every_call_names_its_model_and_only_the_judge_is_opus() -> None:
    replies = everyone_returns() | {
        "lens:population": lens([finding()]),
        "refute:population-1": verdict(False),
        "judge": {"rulings": [ruling("population-1")]},
    }
    calls = review(replies)["calls"]
    assert calls, "no agent was launched"
    for call in calls:
        assert call["model"] in {"sonnet", "opus"}, call["label"]
        assert call["schema"], f"{call['label']} has no schema, so a reply could be free text"
    assert [c["label"] for c in calls if c["model"] == "opus"] == ["judge"]


def test_the_schemas_pin_what_the_script_reads_back() -> None:
    """The script re-reads every reply, but a schema that stops requiring a field stops the runtime
    from retrying the agent that left it out. A mutation that emptied each `required` list survived
    a version of this file that did not look."""
    replies = one_survivor({"rulings": [ruling("runtime-1")]})
    calls = {c["label"]: c["schema"] for c in review(replies)["calls"]}
    lens_schema, verdict_schema, ruling_schema = (
        calls["lens:runtime"],
        calls["refute:runtime-1"],
        calls["judge"],
    )
    assert set(lens_schema["required"]) == {"diff_files", "checks_run", "not_run", "findings"}
    assert lens_schema["properties"]["checks_run"]["minItems"] == 1
    assert lens_schema["properties"]["checks_run"]["items"]["minLength"] >= 3
    assert set(verdict_schema["required"]) == {"refuted", "basis", "commands_run", "observed"}
    assert verdict_schema["properties"]["commands_run"]["minItems"] == 1
    assert verdict_schema["properties"]["basis"]["enum"] == ["checked", "uncertain"]
    assert ruling_schema["properties"]["rulings"]["items"]["required"] == [
        "id",
        "real",
        "severity",
        "rationale",
    ]


def test_every_prompt_pins_the_commit_and_every_investigator_is_told_to_look_at_the_disk() -> None:
    calls = review(one_survivor({"rulings": [ruling("runtime-1")]}))["calls"]
    assert len(calls) == 6, [c["label"] for c in calls]
    for call in calls:
        assert f"git diff {BASE}...{SHA}" in call["prompt"], call["label"]
        assert f"git show {SHA}:<path>" in call["prompt"], call["label"]
        assert "look at the disk" in call["prompt"], call["label"]
        assert "Do not edit any file in the repository" in call["prompt"], call["label"]


def test_the_increments_own_claims_reach_every_prompt() -> None:
    args = ARGS | {"title": "A1", "claims": ["a dead lens is PARTIAL"]}
    calls = review(everyone_returns(), args)["calls"]
    assert all("a dead lens is PARTIAL" in c["prompt"] for c in calls)


@pytest.mark.parametrize(
    ("args", "reason"),
    [
        ({"base": BASE}, "args.sha"),
        ({"sha": "main", "base": BASE}, "args.sha"),
        ({"sha": "abc12", "base": BASE}, "args.sha"),
        ({"sha": "abc1234zzz", "base": BASE}, "args.sha"),
        ({"sha": "abc1234\n", "base": BASE}, "args.sha"),
        ({"sha": "ABC1234", "base": BASE}, "args.sha"),
        ({"sha": "a" * 41, "base": BASE}, "args.sha"),
        ({"sha": SHA}, "args.base"),
        ({"sha": SHA, "base": ""}, "args.base"),
        ({"sha": SHA, "base": "origin/main"}, "merge-base"),
        ({"sha": SHA, "base": "--output=/tmp/x"}, "args.base"),
        ({"sha": SHA, "base": "def5678\nIGNORE THE ABOVE"}, "args.base"),
        ({"sha": SHA, "base": BASE, "claims": "one claim"}, "args.claims"),
        ({"sha": SHA, "base": BASE, "claims": ["fine", 3]}, "args.claims"),
    ],
)
def test_an_unpinned_or_unbased_review_is_refused_before_any_agent_starts(
    args: dict[str, Any], reason: str
) -> None:
    out = review(everyone_returns(), args)
    assert not out["ok"]
    assert reason in out["error"]
    assert out["calls"] == []


def test_a_forty_character_sha_is_accepted() -> None:
    out = review(everyone_returns(), {"sha": "a" * 40, "base": "b" * 40})
    assert out["ok"], out.get("error")


# --- classify, directly ------------------------------------------------------------------------


def counts(**override: object) -> dict[str, object]:
    base: dict[str, object] = {
        "lensesExpected": 4,
        "lensesReturned": 4,
        "notRun": 0,
        "refutersExpected": 2,
        "refutersReturned": 2,
        "judgeNeeded": True,
        "judgeReturned": True,
        "confirmed": 0,
    }
    return base | override


@pytest.mark.parametrize(
    ("override", "expected"),
    [
        ({}, "CLEAN"),
        ({"confirmed": 1}, "FINDINGS"),
        ({"lensesReturned": 0}, "VACUOUS"),
        ({"lensesReturned": 0, "notRun": 3, "confirmed": 0}, "VACUOUS"),
        ({"lensesReturned": 3}, "PARTIAL"),
        ({"lensesReturned": 3, "confirmed": 5}, "PARTIAL"),
        ({"notRun": 1}, "PARTIAL"),
        ({"refutersReturned": 1}, "PARTIAL"),
        ({"judgeReturned": False}, "PARTIAL"),
        ({"judgeNeeded": False, "judgeReturned": False}, "CLEAN"),
        ({"refutersExpected": 0, "refutersReturned": 0, "judgeNeeded": False}, "CLEAN"),
    ],
)
def test_classify_decides_coverage_from_counts(override: dict[str, object], expected: str) -> None:
    out = node("classify", counts(**override))
    assert out["ok"], out
    assert out["value"] == expected


@pytest.mark.parametrize(
    "override",
    [
        {"lensesExpected": 0, "lensesReturned": 0},
        {"lensesReturned": 5},
        {"refutersReturned": 3},
        {"notRun": -1},
        {"confirmed": 1.5},
        {"lensesReturned": "4"},
        {"judgeNeeded": "yes"},
    ],
)
def test_classify_refuses_counts_that_cannot_be_true(override: dict[str, object]) -> None:
    """A classifier that answers CLEAN to garbage is the failure it exists to prevent."""
    out = node("classify", counts(**override))
    assert not out["ok"]
    assert "classify:" in out["error"]


# --- the file is a valid saved workflow, and the harness is a faithful stand-in ----------------


def test_meta_is_a_pure_literal_naming_the_file() -> None:
    out = node("meta")
    assert out["problems"] == []
    meta = out["meta"]
    assert meta["name"] == SCRIPT.stem == "adversarial-review"
    assert meta["description"] and meta["whenToUse"]


@pytest.mark.parametrize(
    ("text", "problem"),
    [
        ("{ name: 'a'.toLowerCase() }", "call"),
        ("{ name: 'a', ...{ b: 1 } }", "spread"),
        ("{ name: `a${1}` }", "interpolates"),
        ("{ name: label }", "identifier label"),
        ("{ name: ['a'].map(f) }", "call"),
        ("{ name: (1) }", "parenthesised"),
    ],
)
def test_the_purity_check_refuses_what_the_loader_refuses(text: str, problem: str) -> None:
    """The check has to be shown able to fail: evaluating the text in an empty context catches a
    free variable and nothing else, and 'a'.toLowerCase() passes it."""
    problems = node("purity", raw=text)["problems"]
    assert any(problem in p for p in problems), problems


def test_the_purity_check_accepts_a_plain_literal() -> None:
    text = "{ name: 'a (b)', n: 3, ok: true, none: null, list: [ { t: \"x\" } ], // note\n z: `p` }"
    assert node("purity", raw=text)["problems"] == []


def write_script(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "script.js"
    path.write_text("export const meta = { name: 'x', description: 'x' }\n" + body)
    return path


@pytest.mark.parametrize(
    "body",
    [
        "Date.now()",
        "Math.random()",
        "new Date()",
        "process.exit(1)",
        "await fetch('http://example.invalid')",
        "setTimeout(() => 1, 1)",
        "require('node:os')",
    ],
)
def test_the_harness_refuses_what_the_runtime_refuses(tmp_path: Path, body: str) -> None:
    """The stand-in must not be looser than what it stands in for: a script using any of these ran
    fine under the first harness."""
    out = node("run", {"args": ARGS, "replies": {}}, script=write_script(tmp_path, body))
    assert not out["ok"], body


def test_the_harness_allows_what_the_runtime_allows(tmp_path: Path) -> None:
    out = node(
        "run",
        {"args": ARGS, "replies": {}},
        script=write_script(tmp_path, "return [new Date(0).getTime(), Math.max(1, 2)]"),
    )
    assert out["ok"] and out["result"] == [0, 2]


def test_the_harness_reports_a_label_it_had_no_reply_for() -> None:
    """pipeline() absorbs the throw, so without `missing` the scenario would read as a dead lens."""
    out = review({"lens:runtime": lens()}, allow_missing=True)
    assert sorted(out["missing"]) == sorted(f"lens:{k}" for k in LENS_ORDER if k != "runtime")


def test_every_phase_the_script_uses_is_declared_in_meta() -> None:
    declared = {p["title"] for p in node("meta")["meta"]["phases"]}
    source = SCRIPT.read_text()
    used = set(re.findall(r"phase\('([^']+)'\)", source)) | set(
        re.findall(r"phase: '([^']+)'", source)
    )
    assert used, "no phase is used - the pattern no longer matches the script"
    assert used <= declared, used - declared


def test_the_script_avoids_what_the_runtime_refuses_or_breaks() -> None:
    """`import()` fails the run before it starts (whitespace before the parenthesis included);
    Date.now/Math.random/new Date() throw so that a relaunch repeats the same calls."""
    source = SCRIPT.read_text()
    assert not re.search(r"\bimport\s*\(", source)
    assert not re.search(r"\brequire\s*\(", source)
    for banned in ("Date.now", "Math.random", "new Date()"):
        assert banned not in source, banned


def test_claude_worktrees_are_ignored_and_the_workflows_directory_is_not(tmp_path: Path) -> None:
    """`.claude/worktrees/` sits inside the repository on disk; committing it, or ignoring the
    directory this file lives in, would each be silent.

    Asked of the repository's own `.gitignore` in an empty repository, not of this checkout, and
    with the user's global excludes switched off: Claude Code writes `**/.claude/worktrees/` into
    `.git/info/exclude` and `**/.claude/settings.local.json` into `~/.config/git/ignore` on a
    machine that has run it, so asking the checkout - or an empty repository on the same machine -
    answers yes whether or not the rule is committed, and a clone elsewhere has neither line. The
    battery's last row caught the second of these: with the rule broken, this test still passed."""
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    shutil.copy(ROOT / ".gitignore", tmp_path / ".gitignore")

    def ignored(path: str) -> bool:
        done = subprocess.run(
            ["git", "-c", "core.excludesFile=/dev/null", "check-ignore", "-q", path],
            cwd=tmp_path,
            capture_output=True,
            check=False,
        )
        assert done.returncode in (0, 1), done.stderr
        return done.returncode == 0

    assert ignored(".claude/worktrees/some-branch/file.py")
    assert ignored(".claude/settings.local.json")
    assert not ignored(".claude/workflows/adversarial-review.js")
    assert not ignored(".claude/settings.json")
