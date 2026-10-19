"""`.claude/workflows/adversarial-review.js`, run with stub hooks by `review_workflow_harness.mjs`.

**The defect these tests exist to catch is a review that cannot say whether anyone looked.** The
runtime returns `null` for an agent that died and the documented idiom for collecting a fan-out is
`.filter(Boolean)`, so the obvious script turns a dead agent into an absent finding: 17 of 19 agents
died on a session limit once and the run returned `{"raised":0,"confirmed":[],"refuted":[]}`. Every
test that kills something therefore asserts the *stated reason* and not only the verdict, and
`test_a_complete_pass_is_clean` exists as the control without which no "PARTIAL" below would mean
anything - a script that always answers PARTIAL passes every other test in this file.

The harness runs the script file itself, so these tests exercise its control flow - which lens
starts first, what is counted before what is filtered, which model each call names. They cannot
exercise the real fan-out; that was run once by hand.

Node is required. Locally a machine without it skips the file; under `CI` a runner without it
fails, so an image change cannot turn this gate into a skip that nobody reads.
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

pytestmark = pytest.mark.skipif(
    NODE is None and not os.environ.get("CI"),
    reason="node is not installed; the review workflow is a JavaScript file and is run with it",
)

LENS_ORDER = ["runtime", "missing-set", "population", "docs-vs-tree"]
SHA = "abc1234"
ARGS: dict[str, Any] = {"sha": SHA, "base": "origin/main"}


def node(mode: str, payload: object = None) -> dict[str, Any]:
    done = subprocess.run(
        [NODE or "node", str(HARNESS), mode],
        input=json.dumps(payload) if payload is not None else None,
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 0, done.stdout + done.stderr
    out: dict[str, Any] = json.loads(done.stdout)
    return out


def review(replies: dict[str, Any], args: dict[str, Any] | None = None) -> dict[str, Any]:
    return node("run", {"args": ARGS if args is None else args, "replies": replies})


def lens(
    findings: list[dict[str, Any]] | None = None,
    not_run: list[str] | None = None,
    checks: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "checks_run": ["rg -n foo src"] if checks is None else checks,
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


def verdict(refuted: bool, commands: list[str] | None = None) -> dict[str, Any]:
    return {
        "refuted": refuted,
        "commands_run": ["ls -la docs"] if commands is None else commands,
        "observed": "the directory lists the file",
    }


def ruling(id_: str, real: bool = True, severity: str = "high") -> dict[str, Any]:
    return {"id": id_, "real": real, "severity": severity, "rationale": "reproduced it"}


def everyone_returns() -> dict[str, Any]:
    return {f"lens:{key}": lens() for key in LENS_ORDER}


def labels(out: dict[str, Any]) -> list[str]:
    return [c["label"] for c in out["calls"]]


# --- the control, then the deaths --------------------------------------------------------------


def test_a_complete_pass_is_clean() -> None:
    """The control. Every lens returned and nothing was raised: CLEAN, with nothing said missing."""
    out = review(everyone_returns())
    assert out["ok"], out
    result = out["result"]
    assert result["coverage"] == "CLEAN"
    assert result["lenses"]["died"] == []
    assert result["lenses"]["returned"] == LENS_ORDER
    assert result["unrefuted"] == [] and result["unjudged"] == [] and result["not_run"] == {}
    assert "NOT a clean pass" not in result["note"]


def test_a_dead_lens_is_partial_not_clean() -> None:
    """The 20260825 failure in one agent: a lens returned null, `.filter(Boolean)` would erase it,
    and the remaining three found nothing. That must not read as a clean bill."""
    replies = everyone_returns() | {"lens:runtime": "__dead__"}
    result = review(replies)["result"]
    assert result["coverage"] == "PARTIAL"
    assert result["lenses"]["died"] == ["runtime"]
    assert result["lenses"]["returned"] == ["missing-set", "population", "docs-vs-tree"]
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


def test_an_unrun_probe_is_partial_even_though_every_lens_returned() -> None:
    """A runtime lens that could not build its KB returned - and checked nothing that matters."""
    replies = everyone_returns() | {"lens:runtime": lens(not_run=["could not build a KB: no uv"])}
    result = review(replies)["result"]
    assert result["coverage"] == "PARTIAL"
    assert result["lenses"]["died"] == []
    assert result["not_run"] == {"runtime": ["could not build a KB: no uv"]}


# --- refuters and the judge --------------------------------------------------------------------


def test_a_finding_whose_refuter_died_is_unrefuted_not_dropped() -> None:
    replies = everyone_returns() | {
        "lens:runtime": lens([finding("pnk sync deletes a file")]),
        "refute:runtime-1": "__dead__",
    }
    result = review(replies)["result"]
    assert result["coverage"] == "PARTIAL"
    assert [f["id"] for f in result["unrefuted"]] == ["runtime-1"]
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


def test_a_refuted_finding_is_listed_and_the_pass_is_clean() -> None:
    """A finding a refuter killed is reported as refuted, with what the refuter saw - and it needs
    no judge, so no Opus call is made."""
    replies = everyone_returns() | {
        "lens:runtime": lens([finding("a claim the disk contradicts")]),
        "refute:runtime-1": verdict(True),
    }
    out = review(replies)
    result = out["result"]
    assert result["coverage"] == "CLEAN"
    assert [r["id"] for r in result["refuted"]] == ["runtime-1"]
    assert result["refuted"][0]["observed"] == "the directory lists the file"
    assert "judge" not in labels(out)


def test_a_survivor_the_judge_confirms_is_a_finding() -> None:
    replies = everyone_returns() | {
        "lens:runtime": lens([finding("pnk sync deletes a file")]),
        "refute:runtime-1": verdict(False),
        "judge": {"rulings": [ruling("runtime-1", real=True, severity="high")]},
    }
    out = review(replies)
    result = out["result"]
    assert result["coverage"] == "FINDINGS"
    assert [f["id"] for f in result["confirmed"]] == ["runtime-1"]
    assert result["confirmed"][0]["severity_as_ruled"] == "high"
    judge = next(c for c in out["calls"] if c["label"] == "judge")
    assert "runtime-1" in judge["prompt"] and "pnk sync deletes a file" in judge["prompt"]


def test_a_dead_judge_leaves_survivors_unjudged_and_nothing_confirmed() -> None:
    replies = everyone_returns() | {
        "lens:runtime": lens([finding()]),
        "refute:runtime-1": verdict(False),
        "judge": "__dead__",
    }
    result = review(replies)["result"]
    assert result["coverage"] == "PARTIAL"
    assert [f["id"] for f in result["unjudged"]] == ["runtime-1"]
    assert result["confirmed"] == []


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


def test_a_repeated_ruling_id_puts_a_finding_on_one_list_only() -> None:
    """The judge contradicting itself must not put one finding on both lists."""
    replies = everyone_returns() | {
        "lens:runtime": lens([finding()]),
        "refute:runtime-1": verdict(False),
        "judge": {"rulings": [ruling("runtime-1", real=True), ruling("runtime-1", real=False)]},
    }
    result = review(replies)["result"]
    assert [f["id"] for f in result["confirmed"]] == ["runtime-1"]
    assert result["not_real"] == []


def test_a_judge_ruling_a_finding_not_real_is_listed_and_the_pass_is_clean() -> None:
    replies = everyone_returns() | {
        "lens:runtime": lens([finding()]),
        "refute:runtime-1": verdict(False),
        "judge": {"rulings": [ruling("runtime-1", real=False, severity="low")]},
    }
    result = review(replies)["result"]
    assert result["coverage"] == "CLEAN"
    assert [r["id"] for r in result["not_real"]] == ["runtime-1"]
    assert result["confirmed"] == []


def test_confirmed_findings_never_hide_a_dead_lens() -> None:
    """Precedence: a pass with findings and a dead lens is PARTIAL, not FINDINGS - the gap is the
    more important fact, and the findings are still in `confirmed`."""
    replies = everyone_returns() | {
        "lens:docs-vs-tree": "__dead__",
        "lens:runtime": lens([finding()]),
        "refute:runtime-1": verdict(False),
        "judge": {"rulings": [ruling("runtime-1")]},
    }
    result = review(replies)["result"]
    assert result["coverage"] == "PARTIAL"
    assert [f["id"] for f in result["confirmed"]] == ["runtime-1"]


# --- what is launched, in what order, on which model -------------------------------------------


def test_slow_lenses_are_launched_first() -> None:
    """The runtime lens builds a KB and runs a command; it reports last and is the first thing a
    session limit cuts. Started first, it is also the first to finish."""
    out = review(everyone_returns())
    assert labels(out)[:4] == [f"lens:{key}" for key in LENS_ORDER]


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


def test_every_prompt_pins_the_commit_and_every_investigator_is_told_to_look_at_the_disk() -> None:
    replies = everyone_returns() | {
        "lens:runtime": lens([finding()]),
        "refute:runtime-1": verdict(False),
        "judge": {"rulings": [ruling("runtime-1")]},
    }
    calls = review(replies)["calls"]
    assert len(calls) == 6, labels({"calls": calls})
    for call in calls:
        assert f"git diff origin/main...{SHA}" in call["prompt"], call["label"]
        assert "look at the disk" in call["prompt"], call["label"]
        assert "Do not edit any file in the repository" in call["prompt"], call["label"]


def test_the_increments_own_claims_reach_every_prompt() -> None:
    args = ARGS | {"title": "A1", "claims": ["a dead lens is PARTIAL"]}
    calls = review(everyone_returns(), args)["calls"]
    assert all("a dead lens is PARTIAL" in c["prompt"] for c in calls)


@pytest.mark.parametrize(
    ("args", "reason"),
    [
        ({"base": "origin/main"}, "args.sha"),
        ({"sha": "main", "base": "origin/main"}, "args.sha"),
        ({"sha": "abc12", "base": "origin/main"}, "args.sha"),
        ({"sha": SHA}, "args.base"),
        ({"sha": SHA, "base": ""}, "args.base"),
    ],
)
def test_an_unpinned_or_unbased_review_is_refused_before_any_agent_starts(
    args: dict[str, Any], reason: str
) -> None:
    out = review(everyone_returns(), args)
    assert not out["ok"]
    assert reason in out["error"]
    assert out["calls"] == []


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


# --- the file is a valid saved workflow --------------------------------------------------------


def test_meta_is_a_pure_literal_naming_the_file() -> None:
    meta = node("meta")["meta"]
    assert meta["name"] == SCRIPT.stem == "adversarial-review"
    assert meta["description"] and meta["whenToUse"]


def test_every_phase_the_script_uses_is_declared_in_meta() -> None:
    declared = {p["title"] for p in node("meta")["meta"]["phases"]}
    source = SCRIPT.read_text()
    used = set(re.findall(r"phase\('([^']+)'\)", source)) | set(
        re.findall(r"phase: '([^']+)'", source)
    )
    assert used, "no phase is used - the pattern no longer matches the script"
    assert used <= declared, used - declared


def test_the_script_avoids_what_the_runtime_refuses_or_breaks() -> None:
    """`import()` fails the run before it starts; Date.now/Math.random/new Date() throw so that a
    relaunch repeats the same calls."""
    source = SCRIPT.read_text()
    for banned in ("import(", "Date.now", "Math.random", "new Date()", "require("):
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
