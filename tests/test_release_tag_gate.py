"""`tools/release_tag_gate.py`, driven as a subprocess against real git repositories.

A subprocess rather than an import, for the reason `tests/test_status_header_gate.py` gives: it
exercises the same artifact `make release-check` runs, argument parsing included, with no
`sys.path` surgery. And **real repositories rather than a faked git** — every leg of this gate is a
question about a git object (does a tag point at `HEAD`, is it annotated, is it on the remote), so
a stubbed `git` would only ever prove that the stub answers what the test told it to. `--repo` and
`--remote` exist for that: the fixture builds a work repository and a **local bare remote**, so
even leg 4 runs the real `git ls-remote` over a real transport, offline.

**What this gate replaced is the shape these tests are aimed at.** `make release-check` was three
`echo`s with no comparison and no failure path — it printed the tag and exited 0 whatever was
true. A test that only asserted exit 0 on a good tree would have passed against that recipe
unchanged. So **every failing leg asserts the stated reason**, and the mismatch leg asserts *both*
versions appear: a message naming only one version is compatible with comparing that version to
itself.

The one region no fixture reaches is the **default** arguments — the real repository, the real
`pinakes.__version__`, the real `origin`. `test_the_defaults_are_this_repository_and_this_version`
covers it by running the gate with no flags at all.
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest

from pinakes import __version__

ROOT = Path(__file__).parent.parent
TOOL = ROOT / "tools" / "release_tag_gate.py"


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    )
    return result.stdout


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), *args], capture_output=True, text=True, check=False
    )


def gate(
    repo: Path, version: str = "1.2.3", remote: str = "origin"
) -> subprocess.CompletedProcess[str]:
    return run("--repo", str(repo), "--expect-version", version, "--remote", remote)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A work repository with one commit and a **bare local remote** named `origin`.

    Bare and local so `git ls-remote` is the real command over a real transport with no network:
    leg 4 is the one that makes "before the tag, never after" checkable, and mocking it away would
    leave the only leg about an irreversible act untested.
    """
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
    work = tmp_path / "work"
    subprocess.run(["git", "init", "-q", "-b", "main", str(work)], check=True)
    git(work, "config", "user.email", "gate@example.invalid")
    git(work, "config", "user.name", "gate")
    (work / "f.txt").write_text("one\n")
    git(work, "add", "f.txt")
    git(work, "commit", "-qm", "one")
    git(work, "remote", "add", "origin", str(remote))
    git(work, "push", "-q", "origin", "main")
    return work


def test_a_matching_annotated_unpushed_tag_passes(repo: Path) -> None:
    """The state the release procedure is in at the moment it should push: the tag exists, names
    the version, carries notes, and the remote has never seen it."""
    git(repo, "tag", "-a", "v1.2.3", "-m", "pinakes 1.2.3")
    result = gate(repo)
    assert result.returncode == 0, result.stderr
    assert "v1.2.3" in result.stdout
    assert "git push origin v1.2.3" in result.stdout, (
        "a green run must name the one command left to run, or the operator invents it"
    )


def test_no_tag_at_head_fails(repo: Path) -> None:
    """**The half this gate exists for.** The old recipe reported success here — it never asked
    whether there was a tag, so absence and agreement produced identical output."""
    result = gate(repo)
    assert result.returncode == 1
    assert "no release tag points at HEAD" in result.stderr
    assert "cannot pass on an absent tag" in result.stderr
    assert "git tag -a v1.2.3" in result.stderr, "the failure must name the tag to create"


def test_a_tag_that_is_not_release_shaped_does_not_count_as_a_tag(repo: Path) -> None:
    """`nightly` and `v1.2` point at `HEAD` and neither is a version this project publishes.
    Counting them would let any tag satisfy leg 1 and push the failure down to leg 2, where the
    message would be about a mismatch rather than about an absent release tag."""
    git(repo, "tag", "nightly")
    git(repo, "tag", "v1.2")
    git(repo, "tag", "v1.2.3-rc1")
    result = gate(repo)
    assert result.returncode == 1
    assert "no release tag points at HEAD" in result.stderr


def test_two_release_tags_at_head_fail_naming_both(repo: Path) -> None:
    """One commit publishes one version. Two tags on it means the second push publishes a second
    version from bytes that were verified once — and a gate that took the first match would be
    green for whichever one it happened to sort first."""
    git(repo, "tag", "-a", "v1.2.3", "-m", "pinakes 1.2.3")
    git(repo, "tag", "-a", "v1.2.4", "-m", "pinakes 1.2.4")
    result = gate(repo)
    assert result.returncode == 1
    assert "2 release tags point at HEAD" in result.stderr
    assert "v1.2.3" in result.stderr and "v1.2.4" in result.stderr


def test_a_mismatched_tag_fails_naming_both_versions(repo: Path) -> None:
    """The version bump at `docs/RELEASING.md` step 2 was missed, or the tag was mistyped. The
    message must carry **both** numbers: naming only one is compatible with a gate that compares
    a value to itself, which is exactly the shape this replaced."""
    git(repo, "tag", "-a", "v9.9.9", "-m", "pinakes 9.9.9")
    result = gate(repo)
    assert result.returncode == 1
    assert "v9.9.9" in result.stderr, "the failure must name the tag that exists"
    assert "1.2.3" in result.stderr, "the failure must name the version the package states"


def test_a_lightweight_tag_fails(repo: Path) -> None:
    """`git tag v1.2.3` rather than `git tag -a`. It satisfies legs 1 and 2 exactly — right name,
    right commit — and `release.yml`'s `gh release create --notes-from-tag` runs **after**
    `uv publish`, so nothing in front of the irreversible step would ever see it."""
    git(repo, "tag", "v1.2.3")
    result = gate(repo)
    assert result.returncode == 1
    assert "lightweight" in result.stderr
    assert "--notes-from-tag" in result.stderr, "the failure must name what breaks"


def test_an_annotated_tag_with_an_empty_message_fails(repo: Path) -> None:
    """`git tag -a v1.2.3 -m ""` succeeds and produces a real tag object — measured, not assumed.
    It passes the annotated/lightweight test and still leaves `--notes-from-tag` nothing to read,
    which is the same defect one layer in."""
    git(repo, "tag", "-a", "v1.2.3", "-m", "")
    assert git(repo, "cat-file", "-t", "v1.2.3").strip() == "tag", (
        "the fixture must produce a genuine tag object, or this test proves nothing"
    )
    result = gate(repo)
    assert result.returncode == 1
    assert "empty message" in result.stderr


def test_a_tag_already_on_the_remote_fails(repo: Path) -> None:
    """**This is what makes `CLAUDE.md`'s *"before the tag, never after"* checkable.** Everything
    else about this tree is correct — right name, right commit, annotated — and the one thing that
    is wrong is *when* the gate is being run. PyPI has already had the version by now."""
    git(repo, "tag", "-a", "v1.2.3", "-m", "pinakes 1.2.3")
    git(repo, "push", "-q", "origin", "v1.2.3")
    result = gate(repo)
    assert result.returncode == 1
    assert "already on origin" in result.stderr
    assert "after the tag rather than before" in result.stderr


def test_an_unreachable_remote_fails_rather_than_passing(repo: Path, tmp_path: Path) -> None:
    """A gate that cannot ask its question must not answer it. The question leg 4 asks is the only
    one about an irreversible act, so "the remote was down" resolving to green is the worst
    available default."""
    git(repo, "remote", "add", "gone", str(tmp_path / "does-not-exist.git"))
    git(repo, "tag", "-a", "v1.2.3", "-m", "pinakes 1.2.3")
    result = gate(repo, remote="gone")
    assert result.returncode == 1
    assert "cannot reach gone" in result.stderr
    assert "does not pass on a question it could not ask" in result.stderr


def test_the_defaults_are_this_repository_and_this_version() -> None:
    """**The seam's blind spot, covered by running the real thing.** Every test above supplies
    `--repo`, `--expect-version` and `--remote`, so all three defaults are unreached — and a gate
    pointed at the wrong directory, or comparing against a hard-coded version, would pass all of
    them.

    Asserted on what is true in **both** legitimate states of this repository. Between releases
    `HEAD` carries no tag and the run is red on leg 1; at the release commit it carries exactly
    one and the run is green. Both name `v{__version__}` — the red branch tells the operator which
    tag to create, the green branch which to push — so the version wiring is pinned without the
    test depending on whether today happens to be a release day.
    """
    result = run()
    assert f"v{__version__}" in result.stdout + result.stderr, (
        "the no-flag run does not read pinakes.__version__ — the default is wired to something else"
    )
    # **Not `... or result.returncode == 0`.** The first draft wrote it that way, and on the green
    # branch the `or` made the whole assertion unfailable — the exact shape of check this gate
    # replaced. A crash is what the default `--repo` actually risks (a path that resolves to no
    # repository), and a traceback is distinguishable from a refusal in a way an exit code is not:
    # the tool exits 1 for both.
    assert "Traceback" not in result.stderr, (
        f"the no-flag run crashed rather than reporting — the default --repo is wired to "
        f"something that is not a git repository:\n{result.stderr}"
    )
    assert result.returncode in (0, 1), f"unexpected exit {result.returncode}: {result.stderr}"


def _recipe(target: str) -> str:
    """A Makefile target's recipe with comment lines removed.

    `make` hands a recipe line beginning `\\t#` to `/bin/sh`, which ignores it and exits 0 — so
    commenting the gate out leaves every substring assertion below satisfied by the comment while
    the target does nothing. Measured in this repository on 20260822, for `make smoke`.
    """
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    match = re.search(
        rf"^{re.escape(target)}:.*?\n(?P<body>(?:\t.*\n|\n)*)", makefile, re.MULTILINE
    )
    assert match is not None, f"the Makefile has no {target} target"
    return "\n".join(
        line for line in match.group("body").splitlines() if not line.lstrip("\t").startswith("#")
    )


def test_make_release_check_runs_the_gate_rather_than_describing_it() -> None:
    """The defect this whole increment removes was not a missing tool — it was a target whose help
    string promised a check its recipe did not perform. Nothing in the tool's own tests can see
    the recipe, so the recipe is pinned here: the gate is invoked, and it is invoked as the thing
    whose exit status `make` reads."""
    body = _recipe("release-check")
    assert "tools/release_tag_gate.py" in body, "make release-check no longer runs the gate"
    # A recipe line beginning `-` has its exit status **ignored** by make — one character that
    # turns this back into a target that cannot fail, which is precisely what it replaced.
    ignored = [line for line in body.splitlines() if line.lstrip("\t").startswith("-")]
    assert not ignored, f"make is told to ignore the exit status of: {ignored}"
    # No pipe: `gate | tee` reports *tee*'s status, the failure mode check.sh exists for.
    assert "|" not in body, (
        f"release-check pipes the gate's output, losing its exit status: {body!r}"
    )


def test_the_release_check_help_string_and_its_recipe_are_pinned_together() -> None:
    """`make help` prints the `##` string, and that string is what a release operator reads. It
    said *"Verify the git tag you are about to push matches pinakes.__version__"* over three
    `echo`s for the life of the target.

    **No test can check that a help string does not over-promise** — that is a claim about English.
    What it can check is the pair: the string still exists (delete it and `make help` stops listing
    the target at all), and the recipe beside it still runs the gate. Held together in one test so
    neither can move without the other being read. An earlier name for this test asserted the
    unpromising part, which is the kind of claim this repository keeps finding in its own gates."""
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    match = re.search(r"^release-check:.*?##\s*(?P<help>.+)$", makefile, re.MULTILINE)
    assert match is not None, (
        "the release-check target lost its ## help string, so `make help` hides it"
    )
    help_text = match.group("help")
    assert "tag" in help_text.lower()
    assert "tools/release_tag_gate.py" in _recipe("release-check"), (
        "the help string describes a check the recipe does not run — the exact defect this replaced"
    )
