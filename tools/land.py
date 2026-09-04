"""Land a feature branch on the default branch — from the primary checkout, always.

**Why this exists.** Running `git merge <branch>` from inside that branch's own worktree merges the
branch into itself: git reports *"Already up to date"*, the push reports *"Everything up-to-date"*,
and a tag created there points off the default branch. **Three successful commands and nothing
landed.** It has happened repeatedly in this repository, always the same way — a single `&&` chain
that begins `cd <worktree>` and later contains `git merge`.

**Git cannot catch this on its own.** A branch merged into itself creates no commit, so
`pre-merge-commit` never fires. The no-op is silent by design. So the guard has to be here:

* this script finds the **primary checkout itself** and merges there, whatever directory it was
  invoked from — the wrong-directory mistake becomes unreachable rather than remembered;
* it records the default branch's sha before the merge and **fails loudly if it did not move**,
  which is the assertion the silent no-op would otherwise slip past;
* it re-reads `origin/<default>` after pushing, because a push reporting success is a claim.

It does not remove the need to *choose* to run it. That is the one remaining human step, and it is
one thing to remember rather than a rule to apply in the middle of a command chain.

    python3 tools/land.py <branch>              # merge, verify, push
    python3 tools/land.py <branch> --cleanup    # also remove the worktree and both branch copies
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

DEFAULT_BRANCH = "main"


class LandingError(Exception):
    """A refusal with a remedy. Never raised for a condition the script could fix itself."""


def git(*args: str, cwd: Path | None = None, check: bool = True) -> str:
    """Run a git command and return its stripped stdout."""
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise LandingError(
            f"`git {' '.join(args)}` failed ({result.returncode}):\n{result.stderr.strip()}"
        )
    return result.stdout.strip()


def primary_checkout() -> Path:
    """The main working tree, which is always the first entry `git worktree list` prints.

    Linked worktrees follow it. Reading this rather than trusting the caller's cwd is the whole
    point of the script: it is what makes merging from inside a feature worktree impossible.
    """
    first = git("worktree", "list", "--porcelain").splitlines()
    if not first or not first[0].startswith("worktree "):
        raise LandingError("could not read `git worktree list --porcelain`")
    return Path(first[0][len("worktree ") :])


def ensure_landable(root: Path, branch: str) -> None:
    """Refuse anything that would land nothing, or land it somewhere unexpected."""
    if branch == DEFAULT_BRANCH:
        raise LandingError(
            f"refusing to merge {DEFAULT_BRANCH!r} into itself — pass the feature branch instead."
        )
    if not git("rev-parse", "--verify", "--quiet", f"refs/heads/{branch}", cwd=root, check=False):
        raise LandingError(f"no local branch {branch!r}. `git branch -a` to see what exists.")

    current = git("rev-parse", "--abbrev-ref", "HEAD", cwd=root)
    if current != DEFAULT_BRANCH:
        raise LandingError(
            f"the primary checkout is on {current!r}, not {DEFAULT_BRANCH!r}. "
            f"Switch it before landing: `git -C {root} switch {DEFAULT_BRANCH}`."
        )
    dirty = git("status", "--porcelain", cwd=root)
    if dirty:
        raise LandingError(
            f"the primary checkout has uncommitted changes:\n{dirty}\n"
            "Landing would merge on top of them. Commit or stash first."
        )


MARKER_DIRECTORY = "pinakes-gate-markers"


def gate_markers(root: Path) -> Path:
    """Where `check.sh` records the trees it certified.

    Under `--git-common-dir`, which every linked worktree shares with the primary checkout — the
    gate runs in the branch's worktree and this refusal runs here, so a per-worktree location would
    never be found.
    """
    common = Path(git("rev-parse", "--git-common-dir", cwd=root))
    return (common if common.is_absolute() else root / common) / MARKER_DIRECTORY


def merged_tree(root: Path, branch: str) -> str | None:
    """The tree the merge *will* produce, computed without performing it.

    **Not the branch's tree, and that distinction is the whole guard.** `git merge --no-ff` combines
    the branch with a `main` that may have moved, and the result is then neither side's tree.
    Measured over the four merges before this one: **two of the four differ from their branch tip**
    — so keying the marker to the branch would have let a tree nobody gated reach `origin/main`, in
    exactly the "a clean auto-merge is not a correct merge" case this repository already records.

    `merge-tree --write-tree` writes the result to the object store and prints its hash without
    touching the working tree, the index, or `HEAD`. Checked against those same four merges: it
    predicts the tree the real merge produced in every one.

    `None` when the merge would conflict — there is nothing to certify, and the merge below will
    fail on its own terms with a better message than this function could invent.
    """
    result = git(
        "merge-tree", "--write-tree", DEFAULT_BRANCH, branch, cwd=root, check=False
    ).splitlines()
    return result[0].strip() if result and len(result[0].strip()) == 40 else None


def ensure_gated(root: Path, branch: str) -> None:
    """Refuse to land a tree no `./check.sh` run has certified.

    **Two sessions landed over a red gate on 20260904, hours apart, both quoting the rule at each
    other the same day** — one committed after printing a failing exit status, the other put a gate
    in a pipeline and read `tail`'s status. Neither was ignorance. A convention two informed
    sessions break in a day is one this project replaces with a gate.

    **What this cannot catch, stated here because an unstated hole in a guard is worse than no
    guard**: a tree that was gated, edited, and edited *back* hashes the same and passes; and it
    says nothing about *why* a gate was green, only that one was.

    **There is deliberately no override flag.** A flaky or environmental red now blocks a landing —
    tonight's own suite was killed by contention and would have blocked one, correctly. The first
    person to meet that at 3am will want `--no-gate`, and the reason it does not exist is that the
    rule being skippable is what put this guard here.
    """
    tree = merged_tree(root, branch)
    if tree is None:
        return
    if (gate_markers(root) / tree).is_file():
        return
    branch_tree = git("rev-parse", f"{branch}^{{tree}}", cwd=root)
    moved = (
        ""
        if tree == branch_tree
        else (
            f"\n\n{DEFAULT_BRANCH} has moved, so the merge produces tree {tree[:12]}, which is "
            f"neither {branch}'s tree ({branch_tree[:12]}) nor {DEFAULT_BRANCH}'s. Gating the "
            f"branch alone would certify a tree that never lands. Merge {DEFAULT_BRANCH} into "
            f"{branch} first — then the two coincide and one run covers both."
        )
    )
    raise LandingError(
        f"no ./check.sh run has certified the tree this would land ({tree[:12]}).{moved}\n\n"
        f"Run `./check.sh` in {branch}'s worktree with everything committed, then land again. "
        f"It records each tree it certifies under {gate_markers(root)}.\n\n"
        "There is no override. A gate nobody read is what this refusal exists for, and a flag to "
        "skip it would be the same hole with a name. `--cleanup-only` does not come through here."
    )


def land(branch: str, *, cleanup: bool) -> None:
    root = primary_checkout()
    ensure_landable(root, branch)
    ensure_gated(root, branch)
    print(f"landing {branch} → {DEFAULT_BRANCH} in {root}")

    git("fetch", "--quiet", "origin", cwd=root)
    before = git("rev-parse", DEFAULT_BRANCH, cwd=root)
    git("merge", "--no-ff", "--quiet", branch, "-m", f"Merge branch '{branch}'", cwd=root)
    after = git("rev-parse", DEFAULT_BRANCH, cwd=root)

    # The assertion this script exists for. A branch merged into itself lands here reporting
    # success, having done nothing at all.
    if after == before:
        raise LandingError(
            f"{DEFAULT_BRANCH} did not move ({before[:7]}). The merge reported success and landed "
            f"nothing — {branch!r} was most likely already merged, or is an ancestor of "
            f"{DEFAULT_BRANCH}. Nothing was pushed."
        )
    print(f"  merged: {before[:7]} → {after[:7]}")

    git("push", "--quiet", "origin", DEFAULT_BRANCH, cwd=root)
    remote = git("rev-parse", f"origin/{DEFAULT_BRANCH}", cwd=root)
    if remote != after:
        raise LandingError(
            f"push reported success but origin/{DEFAULT_BRANCH} is {remote[:7]}, not {after[:7]}. "
            "Nothing was cleaned up; investigate before retrying."
        )
    print(f"  pushed: origin/{DEFAULT_BRANCH} at {remote[:7]}")

    if cleanup:
        remove_branch_everywhere(root, branch)
    else:
        print(
            f"  worktree and branch kept. `python3 tools/land.py {branch} --cleanup-only` "
            "removes them once you are satisfied."
        )


def cleanup_only(branch: str) -> None:
    """Remove a branch that landed *earlier* — verifying it landed, rather than assuming it.

    Needed because the normal path leaves the worktree in place: you land, watch CI, then clean up.
    Re-running `land` with `--cleanup` at that point correctly refuses, since the default branch
    cannot move a second time — so without this, the only way to finish was by hand, which is the
    class of mistake this script exists to remove.

    **The safety check is ancestry, not the reflog.** `CLAUDE.md`: before deleting anything, confirm
    its content actually landed rather than that it "looks merged".
    """
    root = primary_checkout()
    if branch == DEFAULT_BRANCH:
        raise LandingError(f"refusing to delete {DEFAULT_BRANCH!r}.")
    sha = git("rev-parse", "--verify", "--quiet", f"refs/heads/{branch}", cwd=root, check=False)
    if not sha:
        raise LandingError(f"no local branch {branch!r}. Nothing to clean up.")

    git("fetch", "--quiet", "origin", cwd=root)
    merged = subprocess.run(
        ["git", "merge-base", "--is-ancestor", sha, f"origin/{DEFAULT_BRANCH}"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if merged.returncode != 0:
        raise LandingError(
            f"{branch!r} ({sha[:7]}) is NOT an ancestor of origin/{DEFAULT_BRANCH} — its content "
            f"has not landed. Refusing to delete it. Land it first: "
            f"`python3 tools/land.py {branch}`."
        )
    print(f"verified landed: {branch} ({sha[:7]}) is an ancestor of origin/{DEFAULT_BRANCH}")
    remove_branch_everywhere(root, branch)


def remove_branch_everywhere(root: Path, branch: str) -> None:
    """Remove the worktree, the local ref and the remote ref — deleting only one leaves it there.

    Safe only because `land` has already verified the default branch moved and the push took: the
    content is on the remote before anything is destroyed.
    """
    for line in git("worktree", "list", "--porcelain", cwd=root).split("\n\n"):
        if f"branch refs/heads/{branch}" in line:
            path = line.splitlines()[0][len("worktree ") :]
            git("worktree", "remove", path, cwd=root)
            print(f"  worktree removed: {path}")
    git("worktree", "prune", cwd=root)

    git("branch", "-D", branch, cwd=root)
    print(f"  local branch deleted: {branch}")

    if git("ls-remote", "--heads", "origin", branch, cwd=root):
        git("push", "origin", "--delete", branch, cwd=root)
        print(f"  remote branch deleted: origin/{branch}")
    git("remote", "prune", "origin", cwd=root)

    if git("rev-parse", "--verify", "--quiet", f"refs/heads/{branch}", cwd=root, check=False):
        raise LandingError(f"local branch {branch!r} survived deletion")
    if git("ls-remote", "--heads", "origin", branch, cwd=root):
        raise LandingError(f"remote branch {branch!r} survived deletion")
    print("  verified gone: worktree, local ref, remote ref")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=f"Merge a feature branch into {DEFAULT_BRANCH} from the primary checkout.",
    )
    _ = parser.add_argument("branch", help="the feature branch to land")
    _ = parser.add_argument(
        "--cleanup",
        action="store_true",
        help="after a verified push, remove the worktree and both copies of the branch",
    )
    _ = parser.add_argument(
        "--cleanup-only",
        action="store_true",
        help="skip the merge: remove a branch that landed earlier, after verifying it is an "
        f"ancestor of origin/{DEFAULT_BRANCH}",
    )
    args = parser.parse_args()
    branch: str = args.branch
    cleanup: bool = args.cleanup
    only: bool = args.cleanup_only

    try:
        if only and cleanup:
            raise LandingError("--cleanup and --cleanup-only are alternatives; pass one.")
        if only:
            cleanup_only(branch)
        else:
            land(branch, cleanup=cleanup)
    except LandingError as exc:
        print(f"land: {exc}", file=sys.stderr)
        return 1
    print("cleaned up." if only else "landed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
