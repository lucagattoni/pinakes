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

#: `tests/test_x.py::test_y`, or `tests/test_x.py::TestClass::test_y`. A bare `tests/test_x.py`
#: is a legal pytest selector and is deliberately refused: a mutant naming a whole file names no
#: assertion. The class form is not hypothetical — `tests/test_extract_quality.py::TestCorpusGate`
#: holds six, and they are the tests that die when the extraction floors move.
SELECTOR = re.compile(r"^(tests/[\w/]+\.py)::(\w+)(?:::(\w+))?$")


def _batteries(directory: Path | None = None) -> list[tuple[Path, dict[str, Any]]]:
    """`directory` exists for the control at the foot of this file, which points every check here
    at a directory built to violate all of them."""
    return [
        (path, tomllib.loads(path.read_text(encoding="utf-8")))
        for path in sorted((directory or BATTERIES).glob("*.toml"))
    ]


def _mutants(directory: Path | None = None) -> list[tuple[Path, int, dict[str, Any]]]:
    return [
        (path, index, mutant)
        for path, data in _batteries(directory)
        for index, mutant in enumerate(data.get("mutant", []), start=1)
    ]


def _selectors_of(mutant: dict[str, Any]) -> list[str]:
    kills = mutant["kills"]
    return [kills] if isinstance(kills, str) else list(kills)


def _defined_in(path: Path) -> set[str]:
    """Every `def` and `class` name, at any indentation.

    `tests/test_verification.py` anchors at column 0 because it resolves module-level test
    functions only. A battery may name a class method, so this accepts an indented `def` — and
    `class` too, since the middle segment of a three-part selector is a class.
    """
    text = path.read_text(encoding="utf-8")
    return set(re.findall(r"^\s*(?:def|class) (\w+)", text, re.MULTILINE))


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
        # `read_bytes().decode()`, not `read_text()`: the latter translates newlines, so on a
        # CRLF target this gate would report an anchor resolving that `tools/mutate.py`'s own
        # `_decoded` — which does not translate — refuses. Two implementations of one check must
        # read the same bytes or the cheap one is worse than none.
        count = target.read_bytes().decode("utf-8").count(str(mutant["old"]))
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
            file = match.group(1)
            names = [part for part in match.groups()[1:] if part]
            if not (REPO / file).is_file():
                unresolved.append(f"{path.name}[{index}]: {file} does not exist")
                continue
            defined = _defined_in(REPO / file)
            for name in names:
                if name not in defined:
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
        stems: set[str] = set()
        for mutant in data.get("mutant", []):
            flat = str(mutant["file"]).replace("/", "-")
            stems.add(flat.rsplit(".", 1)[0])
            # The documented tie-break, for the day two targets flatten to one stem —
            # `src/pinakes/extract/floors.py` and `floors.toml` already do. The loser keeps its
            # extension, and this is the check that has to accept that spelling.
            stems.add(flat)
        if path.stem not in stems:
            misnamed.append(
                f"{path.name}: mutates {', '.join(sorted(stems))} and is named for none of them "
                f"(a `YYYYMMDD_HHMM-` prefix does not belong on a battery — it is named "
                f"for what it covers, not when it was written)"
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


def test_no_battery_targets_a_file_under_tests() -> None:
    """`mutate.py` refuses a `tests/` target in both modes, so a battery carrying one is committed,
    green in CI, and impossible to run. This is the only structural refusal the tool makes that
    this gate would otherwise not mirror."""
    inside: list[str] = []
    for path, index, mutant in _mutants():
        if str(mutant["file"]).startswith("tests/"):
            inside.append(f"{path.name}[{index}]: {mutant['file']}")

    assert not inside, (
        "mutating a test stays manual, and `tools/mutate.py` refuses the whole battery for it — a "
        "mutant in the file its own selector runs can make that test vacuous, and no printed "
        "outcome would say so:\n  " + "\n  ".join(inside)
    )


def test_every_battery_declares_how_many_mutants_it_carries() -> None:
    """The inventory. Nothing else here is a count, so without it a battery can shrink to one
    mutant with every other property green — and the sanctioned repair for a property that has
    genuinely gone is to delete its mutant, which makes shrinking the cheapest path to green during
    a refactor. `tools/mutate.py`'s `load_battery` enforces the number; this enforces that there
    is one."""
    undeclared = [path.name for path, data in _batteries() if "mutants" not in data]
    assert not undeclared, (
        "these batteries declare no `mutants = N`, so nothing notices if rows disappear: "
        + ", ".join(undeclared)
    )
    wrong = [
        f"{path.name}: declares {data['mutants']}, carries {len(data['mutant'])}"
        for path, data in _batteries()
        if data.get("mutants") != len(data.get("mutant", []))
    ]
    assert not wrong, "declared inventory does not match:\n  " + "\n  ".join(wrong)


def test_the_committed_batteries_cover_only_tools_and_the_readme_says_so() -> None:
    """A coverage index with a hidden denominator is the thing this repository keeps catching.

    Seven batteries over seven primary targets. Five are under `tools/`; **two modules under `src/`
    have one** — `src-pinakes-init.toml` since 20260825, and `src-pinakes-pairing.toml` the same
    day, which is also the first battery to span two files. No invariant in `docs/INVARIANTS.md`
    has one. That is a starting point rather than a coverage claim, and the README has to say the
    number out loud — if this test fails because a new area arrived, the sentence there needs
    updating too.

    **This docstring is itself the thing the test guards against**, and it had gone stale: it read
    *"Four batteries over four primary targets, every one under `tools/`"* while five were on disk
    and one of them was under `src/`. The assertion below moved on; the sentence explaining it did
    not.
    """
    primaries = {path.stem for path, _ in _batteries()}
    # Whitespace-normalised: the sentence wraps, and a substring probe that breaks on a re-wrap
    # would fail for a reason having nothing to do with what it is asserting.
    readme = " ".join((BATTERIES / "README.md").read_text(encoding="utf-8").lower().split())

    # `src/` finally has one (20260825, `src-pinakes-init.toml`), which is the event this test's
    # first form was written to catch. Requiring *all under tools/* would now mean deleting the
    # assertion to add a battery, so it asks the durable question instead: whatever lies outside
    # `tools/` has to be named here, and a new area cannot arrive without the sentence moving.
    unnamed = sorted(
        stem for stem in primaries if not stem.startswith("tools-") and stem not in readme
    )
    assert not unnamed, (
        f"battery/batteries outside tools/ that the README does not name: {unnamed} — update the "
        "denominator paragraph in tools/batteries/README.md, or the directory reads as a coverage "
        "claim with a hidden denominator"
    )
    assert "starting point, not a coverage claim" in readme, (
        "tools/batteries/README.md must state what the corpus does NOT cover; without it the "
        "directory reads as a coverage claim with a hidden denominator"
    )


# ---------------------------------------------------------------------------------------------
# The control: every check above, pointed at a directory built to trip it
# ---------------------------------------------------------------------------------------------
#
# Each `tools/*_gate.py` carries a `test_ci_runs_…_and_proves_it_can_fail` sibling, because a gate
# nobody has watched fail is indistinguishable from one that cannot. This gate has no such sibling
# available: it is a pytest module rather than a command line in `check.sh`, so there is no
# invocation to pin, and `tools/mutate.py` refuses a target under `tests/`, so a mutation battery
# cannot reach it either. This is the substitute — a directory violating every property at once,
# and the assertion that each check finds its own violation there.

BROKEN = '''\
mutants = 3

[[mutant]]
name = "the anchor is not in the file"
file = "tools/mutate.py"
old = """this string does not appear in mutate.py at all"""
new = """nor does this"""
kills = "tests/test_mutate.py::test_check_anchors_resolves_every_anchor_and_runs_nothing"

[[mutant]]
name = "the selector names a test nobody wrote"
file = "tools/mutate.py"
old = """def check_anchors("""
new = """def check_anchors_renamed("""
kills = "tests/test_mutate.py::test_this_test_has_never_existed"

[[mutant]]
name = "a target under tests/, which mutate.py refuses outright"
file = "tests/test_mutate.py"
old = """def mutate("""
new = """def mutate_renamed("""
kills = "tests/test_mutate.py::test_check_anchors_resolves_every_anchor_and_runs_nothing"
'''


def test_every_check_here_fails_on_a_directory_built_to_break_it(tmp_path: Path) -> None:
    broken = tmp_path / "batteries"
    broken.mkdir()
    _ = (broken / "tools-mutate.toml").write_text(BROKEN, encoding="utf-8")
    _ = (broken / "not-named-for-any-target.toml").write_text(
        BROKEN.replace("mutants = 3", "mutants = 99"), encoding="utf-8"
    )

    parsed = _batteries(broken)
    rows = _mutants(broken)
    assert (len(parsed), len(rows)) == (2, 6), "the fixture itself did not load"

    stale = [
        row
        for _, _, row in rows
        if (REPO / str(row["file"])).is_file()
        and (REPO / str(row["file"])).read_bytes().decode("utf-8").count(str(row["old"])) != 1
    ]
    assert stale, "the anchor check would not notice an anchor that is not in the file"

    unresolved: list[str] = []
    for _, _, row in rows:
        for selector in _selectors_of(row):
            match = SELECTOR.match(selector)
            assert match is not None, selector
            if match.group(2) not in _defined_in(REPO / match.group(1)):
                unresolved.append(selector)
    assert unresolved, "the selector check would not notice a test that does not exist"

    assert [row for _, _, row in rows if str(row["file"]).startswith("tests/")], (
        "the tests/-target check would not notice a battery mutate.py refuses to run"
    )

    claims: dict[str, set[str]] = {}
    for path, _, row in rows:
        claims.setdefault(str(row["file"]), set()).add(path.name)
    assert any(len(names) > 1 for names in claims.values()), (
        "the double-claim check would not notice two batteries claiming one file"
    )

    misnamed = [
        path.name
        for path, data in parsed
        if path.stem
        not in {
            candidate
            for row in data["mutant"]
            for candidate in (
                str(row["file"]).replace("/", "-").rsplit(".", 1)[0],
                str(row["file"]).replace("/", "-"),
            )
        }
    ]
    assert misnamed == ["not-named-for-any-target.toml"], misnamed

    miscounted = [path.name for path, data in parsed if data["mutants"] != len(data["mutant"])]
    assert miscounted == ["not-named-for-any-target.toml"], miscounted
