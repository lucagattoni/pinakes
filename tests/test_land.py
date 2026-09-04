"""`tools/land.py`, driven as a subprocess — one test per branch.

A subprocess rather than an import, for the reason `tests/test_status_header_gate.py` gives: it
exercises the same artifact a human runs, argument parsing included, with no `sys.path` surgery.

The assertion that matters is **not** "landing works". It is that landing *refuses* when the default
branch did not move — the silent failure the script exists for. A branch merged into itself prints
"Already up to date", the push prints "Everything up-to-date", and nothing landed. A suite that only
exercised the happy path would pass with the guard deleted, which is this project's recurring defect
class: an assertion satisfied by something other than the property it names. So every failing branch
asserts the **stated reason**, not merely a non-zero exit.
"""

import subprocess
import sys
from pathlib import Path

import pytest

TOOL = Path(__file__).parent.parent / "tools" / "land.py"


def git(*args: str, cwd: Path) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def land(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), *args], cwd=cwd, capture_output=True, text=True, check=False
    )


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A primary checkout on `main`, with a real `origin` it can push to."""
    origin = tmp_path / "origin.git"
    git("init", "--bare", "--initial-branch=main", str(origin), cwd=tmp_path)

    root = tmp_path / "checkout"
    git("clone", str(origin), str(root), cwd=tmp_path)
    git("config", "user.email", "test@example.invalid", cwd=root)
    git("config", "user.name", "Test", cwd=root)
    (root / "README.md").write_text("base\n", encoding="utf-8")
    git("add", "-A", cwd=root)
    git("commit", "-m", "base", cwd=root)
    git("push", "-u", "origin", "main", cwd=root)
    return root


def certify(root: Path, branch: str) -> str:
    """Write the marker `./check.sh` writes when it passes, for the tree landing `branch` produces.

    **The merged tree, not the branch's**, because that is what the guard checks and the two differ
    whenever `main` has moved — measured at two of the four merges before this guard existed.
    Every landing test calls this, because a landing without it is now correctly refused: the
    fixture builds the state a real branch is in after a green gate, rather than working around the
    guard it is supposed to be exercising.
    """
    tree = git("merge-tree", "--write-tree", "main", branch, cwd=root).splitlines()[0].strip()
    common = Path(git("rev-parse", "--git-common-dir", cwd=root))
    markers = (common if common.is_absolute() else root / common) / "pinakes-gate-markers"
    markers.mkdir(parents=True, exist_ok=True)
    (markers / tree).write_text("certified by the test suite\n", encoding="utf-8")
    return tree


def make_branch(root: Path, name: str) -> Path:
    """A feature branch with one commit, in its own linked worktree — the real shape."""
    worktree = root.parent / name
    git("worktree", "add", "-q", "-b", name, str(worktree), "main", cwd=root)
    (worktree / f"{name}.md").write_text("work\n", encoding="utf-8")
    git("add", "-A", cwd=worktree)
    git("commit", "-m", f"add {name}", cwd=worktree)
    certify(root, name)
    return worktree


def test_landing_moves_the_default_branch_and_pushes(repo: Path) -> None:
    make_branch(repo, "feature")
    before = git("rev-parse", "main", cwd=repo)

    result = land("feature", cwd=repo)

    assert result.returncode == 0, result.stderr
    after = git("rev-parse", "main", cwd=repo)
    assert after != before
    assert git("rev-parse", "origin/main", cwd=repo) == after, (
        "push not verified against the remote"
    )
    assert (repo / "feature.md").exists(), "the branch's content is not on the default branch"


def test_refuses_when_the_default_branch_did_not_move(repo: Path) -> None:
    """The whole point. An already-merged branch is refused, not reported as landed."""
    make_branch(repo, "feature")
    assert land("feature", cwd=repo).returncode == 0
    landed = git("rev-parse", "main", cwd=repo)

    result = land("feature", cwd=repo)

    assert result.returncode == 1
    assert "did not move" in result.stderr, result.stderr
    assert "landed nothing" in result.stderr, "the reason must name what actually happened"
    assert git("rev-parse", "main", cwd=repo) == landed, "a refused landing must change nothing"


def test_merges_in_the_primary_checkout_even_when_invoked_from_the_feature_worktree(
    repo: Path,
) -> None:
    """The mistake this replaces: `cd <worktree> && git merge` merges the branch into itself."""
    worktree = make_branch(repo, "feature")
    before = git("rev-parse", "main", cwd=repo)

    result = land("feature", cwd=worktree)

    assert result.returncode == 0, result.stderr
    assert git("rev-parse", "main", cwd=repo) != before, "landed nothing from inside the worktree"
    assert git("rev-parse", "origin/main", cwd=repo) == git("rev-parse", "main", cwd=repo)


def test_refuses_to_merge_the_default_branch_into_itself(repo: Path) -> None:
    result = land("main", cwd=repo)
    assert result.returncode == 1
    assert "into itself" in result.stderr, result.stderr


def test_refuses_an_unknown_branch(repo: Path) -> None:
    result = land("never-existed", cwd=repo)
    assert result.returncode == 1
    assert "no local branch" in result.stderr, result.stderr


def test_refuses_a_dirty_primary_checkout(repo: Path) -> None:
    """Landing on top of uncommitted work would silently fold it into the merge."""
    make_branch(repo, "feature")
    (repo / "README.md").write_text("edited but not committed\n", encoding="utf-8")

    result = land("feature", cwd=repo)

    assert result.returncode == 1
    assert "uncommitted changes" in result.stderr, result.stderr
    assert git("rev-parse", "main", cwd=repo) == git("rev-parse", "origin/main", cwd=repo)


def test_cleanup_removes_the_worktree_and_both_copies_of_the_branch(repo: Path) -> None:
    """Deleting one copy leaves the branch there for the next `git branch -a`."""
    worktree = make_branch(repo, "feature")
    git("push", "-u", "origin", "feature", cwd=worktree)

    result = land("feature", "--cleanup", cwd=repo)

    assert result.returncode == 0, result.stderr
    assert not worktree.exists(), "worktree survived"
    assert "feature" not in git("branch", cwd=repo), "local ref survived"
    assert not git("ls-remote", "--heads", "origin", "feature", cwd=repo), "remote ref survived"


def test_cleanup_does_not_run_when_the_landing_was_refused(repo: Path) -> None:
    """Nothing is destroyed on a path that landed nothing."""
    worktree = make_branch(repo, "feature")
    assert land("feature", cwd=repo).returncode == 0

    result = land("feature", "--cleanup", cwd=repo)

    assert result.returncode == 1
    assert worktree.exists(), "a refused landing destroyed the worktree"
    assert "feature" in git("branch", cwd=repo), "a refused landing deleted the branch"


def test_cleanup_only_removes_a_branch_that_landed_earlier(repo: Path) -> None:
    """The normal flow: land, watch CI, clean up later. Re-running `--cleanup` refuses by then."""
    worktree = make_branch(repo, "feature")
    git("push", "-u", "origin", "feature", cwd=worktree)
    assert land("feature", cwd=repo).returncode == 0

    refused = land("feature", "--cleanup", cwd=repo)
    assert refused.returncode == 1, "landing twice must still refuse"

    result = land("feature", "--cleanup-only", cwd=repo)

    assert result.returncode == 0, result.stderr
    assert not worktree.exists(), "worktree survived"
    assert "feature" not in git("branch", cwd=repo), "local ref survived"
    assert not git("ls-remote", "--heads", "origin", "feature", cwd=repo), "remote ref survived"


def test_cleanup_only_refuses_a_branch_whose_content_never_landed(repo: Path) -> None:
    """The guard that matters here: 'looks merged' is not 'landed'. Nothing may be destroyed."""
    worktree = make_branch(repo, "feature")

    result = land("feature", "--cleanup-only", cwd=repo)

    assert result.returncode == 1
    assert "has not landed" in result.stderr, result.stderr
    assert worktree.exists(), "an unlanded branch's worktree was destroyed"
    assert "feature" in git("branch", cwd=repo), "an unlanded branch was deleted"


def test_cleanup_only_and_cleanup_are_alternatives(repo: Path) -> None:
    make_branch(repo, "feature")
    result = land("feature", "--cleanup", "--cleanup-only", cwd=repo)
    assert result.returncode == 1
    assert "alternatives" in result.stderr, result.stderr


def uncertify(root: Path) -> None:
    """Remove every marker, putting the repo in the state a branch is in before `./check.sh`."""
    common = Path(git("rev-parse", "--git-common-dir", cwd=root))
    markers = (common if common.is_absolute() else root / common) / "pinakes-gate-markers"
    for marker in markers.glob("*"):
        marker.unlink()


def test_a_branch_no_gate_has_certified_is_refused_and_nothing_moves(repo: Path) -> None:
    """The refusal this guard exists for, and it must leave the repository untouched.

    Two sessions landed over a red gate on 20260904, hours apart, both quoting the rule at each
    other the same day: one committed after *printing* a failing exit status, the other put the
    gate in a pipeline and read `tail`'s status. Neither was ignorance of the rule, which is this
    project's threshold for replacing a convention with a gate.
    """
    make_branch(repo, "feature")
    uncertify(repo)
    before = git("rev-parse", "main", cwd=repo)

    result = land("feature", cwd=repo)

    assert result.returncode != 0
    assert "no ./check.sh run has certified" in result.stderr, result.stderr
    assert git("rev-parse", "main", cwd=repo) == before, "the refusal still merged"
    assert git("rev-parse", "origin/main", cwd=repo) == before, "the refusal still pushed"


def test_certifying_the_branch_alone_is_not_enough_when_the_default_branch_moved(
    repo: Path,
) -> None:
    """The hole a marker keyed to the branch would leave, and it is not hypothetical.

    `git merge --no-ff` combines the branch with a `main` that may have moved, and the result is
    then neither side's tree. Measured over the four merges before this guard existed: **two of the
    four differed from their branch tip.** So a gate run on the branch alone certifies a tree that
    never lands, and the guard would pass while something nobody checked reached `origin/main` —
    the "a clean auto-merge is not a correct merge" case, with the guard asleep in exactly the
    situation it exists for.
    """
    make_branch(repo, "first")
    make_branch(repo, "second")
    assert land("first", cwd=repo).returncode == 0

    # `second` was certified against the old `main`. That tree is real and it is stale: landing now
    # merges `first`'s commit in too, so what lands is a tree nothing has ever run a gate over.
    uncertify(repo)
    branch_tree = git("rev-parse", "second^{tree}", cwd=repo)
    common = Path(git("rev-parse", "--git-common-dir", cwd=repo))
    markers = (common if common.is_absolute() else repo / common) / "pinakes-gate-markers"
    markers.mkdir(parents=True, exist_ok=True)
    (markers / branch_tree).write_text("a gate run on the branch alone\n", encoding="utf-8")
    before = git("rev-parse", "main", cwd=repo)

    result = land("second", cwd=repo)

    assert result.returncode != 0, "a stale branch-tree marker was accepted"
    assert "has moved" in result.stderr, result.stderr
    assert git("rev-parse", "main", cwd=repo) == before

    # ...and certifying the tree the merge actually produces is what lets it through.
    certify(repo, "second")
    assert land("second", cwd=repo).returncode == 0


def test_cleanup_only_does_not_need_a_gate(repo: Path) -> None:
    """It lands nothing, so there is no tree to certify — and requiring one would block tidying up
    a branch whose own landing was gated when it happened."""
    make_branch(repo, "feature")
    assert land("feature", cwd=repo).returncode == 0
    uncertify(repo)

    result = land("feature", "--cleanup-only", cwd=repo)

    assert result.returncode == 0, result.stderr


def test_there_is_no_flag_that_skips_the_gate(repo: Path) -> None:
    """The absence is the feature, so it is asserted rather than left to be noticed.

    A flaky or environmental red now blocks a landing — a suite killed by machine contention did
    exactly that on the night this was written, correctly. The first person to meet that at 3am
    will want `--no-gate`, and the reason it does not exist is that the rule being skippable is
    what put this guard here. An override would be the same hole with a name.
    """
    make_branch(repo, "feature")
    uncertify(repo)

    for flag in ("--no-gate", "--skip-gate", "--force"):
        result = land("feature", flag, cwd=repo)
        assert result.returncode != 0, f"{flag} was accepted"
        assert git("rev-parse", "main", cwd=repo) == git("rev-parse", "origin/main", cwd=repo)
    assert "There is no override" in land("feature", cwd=repo).stderr
