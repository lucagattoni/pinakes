"""`tools/batteries/` — the committed mutation batteries still describe the code they name.

A battery is a claim: *break this line, and this named test dies.* Committing one
(`tools/batteries/README.md`) makes the claim outlive the increment that measured it, and a claim
that outlives its measurement is exactly the thing this repository keeps finding rotted — a
`docs/GUIDE.md` whose commands no longer ran, a verification table where 61 of 98 test paths did not
resolve, a template version that meant different bytes in every commit.

So the batteries are read by something. Each test here answers one way a committed battery can stop
saying anything, and **none of them is a substitute for running it** — that is
`python3 tools/mutate.py tools/batteries/<name>.toml`, and it is what proves the named test actually
dies. These are the cheap half: they cost no subprocess and run inside `./check.sh`.

**What none of them can see:** an anchor that still resolves while the code around it moved, so the
mutant would be KILLED about a property nobody tests any more. Nothing detects that. It is why a
mutant's `name` says what the breakage *is* rather than what the edit does.
"""

import re
import tomllib
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
BATTERIES = REPO / "tools" / "batteries"

#: `tests/test_x.py::test_y` — the same form `docs/VERIFICATION.md` uses, and the only one a
#: selector takes here. `tests/test_x.py` alone is a legal pytest selector but is deliberately not
#: accepted: a mutant that names a whole file names no assertion.
SELECTOR = re.compile(r"^(tests/[\w/]+\.py)::(\w+)$")


def _batteries() -> list[tuple[Path, dict[str, Any]]]:
    return [
        (path, tomllib.loads(path.read_text(encoding="utf-8")))
        for path in sorted(BATTERIES.glob("*.toml"))
    ]


def _mutants() -> list[tuple[Path, int, dict[str, Any]]]:
    return [
        (path, index, mutant)
        for path, data in _batteries()
        for index, mutant in enumerate(data.get("mutant", []), start=1)
    ]


def _selectors_of(mutant: dict[str, Any]) -> list[str]:
    kills = mutant["kills"]
    return [kills] if isinstance(kills, str) else list(kills)


def _defined_in(path: Path) -> set[str]:
    return set(re.findall(r"^def (\w+)", path.read_text(encoding="utf-8"), re.MULTILINE))


def test_the_directory_is_not_empty_and_every_battery_carries_mutants() -> None:
    """The control. Every other test here iterates a glob, so a glob that matched nothing — a
    renamed directory, a changed suffix — would make all of them vacuously green. That is the
    `false_abstain: 0.0` shape this project keeps finding in its own gates."""
    found = _batteries()
    assert found, f"no batteries under {BATTERIES}; the directory or the suffix has moved"
    assert len(_mutants()) > 50, f"only {len(_mutants())} mutants parsed across {len(found)} files"
    for path, data in found:
        assert data.get("mutant"), f"{path.name} declares no [[mutant]] — delete it or fill it in"


def test_every_mutant_names_the_four_keys_mutate_needs() -> None:
    missing: list[str] = []
    for path, index, mutant in _mutants():
        absent = [key for key in ("file", "old", "new", "kills") if key not in mutant]
        if absent:
            missing.append(f"{path.name}[{index}]: missing {', '.join(absent)}")
        elif mutant["old"] == mutant["new"]:
            missing.append(f"{path.name}[{index}]: `old` and `new` are identical")

    assert not missing, "malformed committed batteries:\n  " + "\n  ".join(missing)


def test_every_anchor_still_resolves_exactly_once_in_the_file_it_names() -> None:
    """The one that fires during a refactor, and the message says what to do about it.

    `tools/mutate.py` refuses on 0 matches and on 2 rather than guessing, so a stale anchor can
    never produce a false KILLED or a false SURVIVED — but only when someone runs the battery. This
    is what makes a stale anchor visible in the commit that staled it instead of months later.
    """
    stale: list[str] = []
    for path, index, mutant in _mutants():
        target = REPO / str(mutant["file"])
        if not target.is_file():
            stale.append(f"{path.name}[{index}] {mutant['file']}: the target no longer exists")
            continue
        count = target.read_text(encoding="utf-8").count(str(mutant["old"]))
        if count != 1:
            stale.append(
                f"{path.name}[{index}] {mutant['file']}: the anchor occurs {count} times, and it "
                f"must occur exactly once — {mutant.get('name', '')}"
            )

    assert not stale, (
        "committed mutation batteries name code that has moved. **Repair the anchor first** — "
        "0 matches means re-anchoring on the property, 2 means widening by one stable neighbouring "
        "line (tools/batteries/README.md, § When an anchor rots). Delete the mutant only when the "
        "property it breaks is genuinely gone, and say so in the section:\n  " + "\n  ".join(stale)
    )


def test_every_kills_selector_resolves_to_a_test_that_exists() -> None:
    """The rot `python3 tools/mutate.py --check-anchors` deliberately cannot see.

    A renamed test makes a battery unrunnable, and `mutate.py` does catch it — at the baseline, one
    subprocess in. Selectors here have a known shape, so resolving them costs a regex.
    """
    unresolved: list[str] = []
    for path, index, mutant in _mutants():
        for selector in _selectors_of(mutant):
            match = SELECTOR.match(selector)
            if match is None:
                unresolved.append(f"{path.name}[{index}]: {selector!r} is not `tests/x.py::test_y`")
                continue
            file, name = match.group(1), match.group(2)
            if not (REPO / file).is_file():
                unresolved.append(f"{path.name}[{index}]: {file} does not exist")
            elif name not in _defined_in(REPO / file):
                unresolved.append(f"{path.name}[{index}]: {file} does not define {name}")

    assert not unresolved, (
        "committed batteries name tests that do not exist. A mutant whose selector cannot be "
        "collected is refused at the baseline, so the battery does not run at all:\n  "
        + "\n  ".join(unresolved)
    )


def test_no_file_is_claimed_by_two_batteries() -> None:
    """One file, one battery — so an increment touching it again has one place to add to.

    Two batteries mutating one file is how two increments end up maintaining two sets of mutants
    for it that drift apart, which is the failure committing them was chosen to avoid.
    """
    claims: dict[str, set[str]] = {}
    for path, _, mutant in _mutants():
        claims.setdefault(str(mutant["file"]), set()).add(path.name)

    shared = {file: names for file, names in claims.items() if len(names) > 1}
    assert not shared, "a file may be claimed by exactly one battery:\n  " + "\n  ".join(
        f"{file}: {', '.join(sorted(names))}" for file, names in sorted(shared.items())
    )


def test_every_battery_is_named_for_a_file_it_actually_mutates() -> None:
    """The naming rule as a check rather than a paragraph: the target path, `/` → `-`, extension
    dropped. It is what makes *which battery does this file belong to* answerable by looking."""
    misnamed: list[str] = []
    for path, data in _batteries():
        stems = {
            str(mutant["file"]).rsplit(".", 1)[0].replace("/", "-")
            for mutant in data.get("mutant", [])
        }
        if path.stem not in stems:
            misnamed.append(
                f"{path.name}: mutates {', '.join(sorted(stems))} and is named for none of them"
            )

    assert not misnamed, (
        "a battery is named for its primary target — the path, `/` → `-`, extension dropped "
        "(tools/batteries/README.md):\n  " + "\n  ".join(misnamed)
    )


def test_a_committed_battery_omits_pytest_and_takes_the_default() -> None:
    """One less thing in a long-lived file that can rot. A battery needing another runner may keep
    the key; this asserts none currently does, so the day one appears is the day it is argued."""
    declared = [path.name for path, data in _batteries() if "pytest" in data]
    assert not declared, (
        "these committed batteries pin their own pytest command: "
        + ", ".join(declared)
        + ". The default `uv run --frozen pytest` is one fewer thing to keep current — keep the "
        "key only with a reason, and update this test with it."
    )
