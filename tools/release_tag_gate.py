"""`make release-check` — the tag about to be pushed, gated rather than printed.

**Why this exists.** `CLAUDE.md` sends a release operator here *before* an irreversible publish,
and the target's own help string promised it *"verifies the git tag you are about to push matches
`pinakes.__version__`"*. Until 20260826 the recipe was three `echo`s: it read `__version__`,
printed it, printed `v$version`, printed the command to run. **There was no comparison and no
failure path, so it could not fail and therefore verified nothing** — while every document in the
repository treated it as the last check before a version PyPI will never accept twice
(`plans/20260731_1202-open-corrections.md`, raised 20260825 19:02).

**The tag must already exist locally when this runs, and that is the point.** A gate that compares
"the tag" while silently passing when there is no tag to compare is the same defect one layer out.
So the release procedure creates the tag first and pushes it second, with this gate in between:
the tag is a local, deletable object at that moment, and pushing it is the step that reaches the
publishing workflow. *"Run it before the tag"* means before the **push** — the irreversible half.

**Four legs, and each one is a mistake that already has a cost.**

1. **No release-shaped tag points at `HEAD`, or more than one does.** Absence is the leg this
   whole target lacked: a check that reports success with nothing to compare is the defect, not
   an omission. Two tags means one verified commit publishing two versions.
2. **The tag does not name `pinakes.__version__`.** `release.yml` refuses this as well — *after*
   the push, in a workflow run somebody has to go and read.
3. **The tag is lightweight, or its annotation is empty.** `gh release create --notes-from-tag`
   would have nothing to read, and that step runs *after* `uv publish`.
4. **The tag is already on the remote, or the remote could not be reached.** The first means this
   is not a pre-flight at all — PyPI has had the version and will not take it back. The second is
   a question the gate could not ask, and it must not answer it.

**Leg 4 is what makes *"never after"* checkable instead of remembered.** Re-running this once the
tag is pushed is red, by construction, and says why.

**Deliberately not in `check.sh`.** `HEAD` carries no release tag on an ordinary commit, so leg 1
would be red on every commit in the repository. Its correctness is held by
`tests/test_release_tag_gate.py`, which `check.sh` runs through `pytest` like any other test.

`--repo`, `--expect-version` and `--remote` exist for those tests, which build a real repository
with a real (local, bare) remote rather than faking git. With no flags it reads this repository
and `pinakes.__version__`, which is the run `make release-check` performs.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

from pinakes import __version__

REPO = Path(__file__).resolve().parent.parent

RELEASE_TAG = re.compile(r"^v\d+\.\d+\.\d+$")
"""Anchored, and three components exactly. `v0.30` and `v0.30.3-rc1` are not release tags here:
`release.yml` triggers on `v*` and compares against `__version__`, which is always `x.y.z`."""


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=False
    )


def _fail(message: str) -> int:
    print(f"release-tag: {message}", file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="release_tag_gate", description=__doc__)
    parser.add_argument(
        "--repo",
        type=Path,
        default=REPO,
        help="the repository to check (default: this one; tests point this at a temporary clone)",
    )
    parser.add_argument(
        "--expect-version",
        default=__version__,
        help="the version the tag must name (default: pinakes.__version__)",
    )
    parser.add_argument(
        "--remote",
        default="origin",
        help="the remote the tag must not be on yet (default: origin)",
    )
    args = parser.parse_args(argv)
    repo: Path = args.repo
    expected: str = args.expect_version
    remote: str = args.remote
    wanted = f"v{expected}"

    # Leg 1 — a tag exists, and exactly one does.
    points_at = _git(repo, "tag", "--points-at", "HEAD")
    if points_at.returncode != 0:
        return _fail(f"cannot read tags in {repo}: {points_at.stderr.strip()}")
    tags = [line for line in points_at.stdout.split() if RELEASE_TAG.match(line)]
    if not tags:
        return _fail(
            f"no release tag points at HEAD in {repo}. This gate cannot pass on an absent tag — "
            f"a check that reports success with nothing to compare is what it replaced. Create "
            f"the tag first, then run this, then push: "
            f"git tag -a {wanted} -m '...' && make release-check && git push {remote} {wanted}"
        )
    if len(tags) > 1:
        return _fail(
            f"{len(tags)} release tags point at HEAD — {', '.join(sorted(tags))}. One commit "
            f"publishes one version; delete the ones that are not {wanted} before pushing"
        )
    tag = tags[0]

    # Leg 2 — it names the version this tree will publish.
    if tag != wanted:
        return _fail(
            f"the tag at HEAD is {tag}, but pinakes.__version__ is {expected}, so the tag to "
            f"push is {wanted}. Either the version bump was missed (docs/RELEASING.md step 2) or "
            f"the tag was mistyped. release.yml refuses this too — after the push, not before"
        )

    # Leg 3 — `gh release create --notes-from-tag` has something to read, and it runs after the
    # upload, where a failure costs a hand-made release rather than a version.
    kind = _git(repo, "cat-file", "-t", tag)
    if kind.returncode != 0:
        return _fail(f"cannot read the object {tag} names: {kind.stderr.strip()}")
    if kind.stdout.strip() != "tag":
        return _fail(
            f"{tag} is a lightweight tag. release.yml creates the GitHub release with "
            f"--notes-from-tag, which has no annotation to read: git tag -d {tag} && "
            f"git tag -a {tag} -m '...'"
        )
    message = _git(repo, "tag", "-l", "--format=%(contents)", tag)
    if message.returncode != 0:
        return _fail(f"cannot read {tag}'s annotation: {message.stderr.strip()}")
    if not message.stdout.strip():
        return _fail(
            f"{tag} is annotated with an empty message, and --notes-from-tag would publish a "
            f"release with no notes: git tag -d {tag} && git tag -a {tag} -m '...'"
        )

    # Leg 4 — this is a pre-flight, and it says so when it is not.
    remote_tag = _git(repo, "ls-remote", "--tags", remote, f"refs/tags/{tag}")
    if remote_tag.returncode != 0:
        return _fail(
            f"cannot reach {remote} to ask whether {tag} is already published: "
            f"{remote_tag.stderr.strip() or 'no such remote'}. This gate does not pass on a "
            f"question it could not ask — the answer it wanted is the irreversible one"
        )
    if remote_tag.stdout.strip():
        return _fail(
            f"{tag} is already on {remote}, so this is running after the tag rather than before "
            f"it. The publishing workflow has already had it and PyPI never accepts a version "
            f"twice; verify the artifact instead (docs/RELEASING.md, 'Verify it happened')"
        )

    subject = message.stdout.strip().splitlines()[0]
    print(
        f"release-tag: {tag} is annotated ({subject!r}), points at HEAD, agrees with "
        f"pinakes.__version__ {expected}, and is not yet on {remote}."
    )
    print(f"release-tag: nothing else stands before the publish. Next: git push {remote} {tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
