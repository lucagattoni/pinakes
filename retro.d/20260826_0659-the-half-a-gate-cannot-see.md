## D-35 layer 2 — the half a gate cannot see, and a gate I ran wrong (20260826 06:59)

**HIGH — I ran `uv run ruff check . | tail -1` between edits, and it reported `tail`'s exit
status.** A failing checker read as a pass, and it hid a real `E501` for two edits. This is not a
new lesson anywhere: `check.sh` exists *because* of exactly this, says so in its own header
comment, and `CLAUDE.md` carries it as a standing rule — *a gate is only a gate when its exit
status is what the next command reads*. Nothing false was ever claimed, because `./check.sh` runs
its gates bare and is what ran before each commit. **The generalisable part is where the defect
lived: not in the project's gates, which are correct, but in the ad-hoc command I typed to check my
work between them.** A rule written about `check.sh` was read as being about `check.sh`. Piping any
checker into `head`, `tail`, `grep` or `tee` to read its output is the same mistake wherever it
happens, and the safe habit is `cmd > log 2>&1; echo $?` — the exit status first, the output after.

**HIGH — the property worth gating was the one no existing check could ever have failed on.** D-35's
own reasoning is the durable part: an index-based rule can require the marker when a version is
*absent* from PyPI, and can never require its *removal* once the version is present. Removal is
green by construction — in the header gate (its `SHAPE` stops at the closing `**`), in the
release-order gate (no sequence reads line 3's tail), and in the index rule itself. **When choosing
what to build, "which direction of this property is currently unfalsifiable?" locates the gap
faster than "what is broken?"** — the broken direction usually already has a check; the
unfalsifiable one has never had a chance to fail.

**MEDIUM — the mutant that proves it is the one the real tree cannot show.** `PUBLISHED_ROW` names
which of `release_order_gate.py`'s **two** `docs/STATUS.md` sequences carries `R`. Repoint it at the
other one — the *Published on PyPI* prose, forty lines away — and: the real tree stays green,
because both sequences have the same newest entry today; the test asserting the sequence resolves
stays green, because the prose sequence exists; and every other test stays green. Only a fixture
whose prose is absent kills it. **Reading the wrong one of those two is a recorded failure in this
repository** — it is how the row drifted four releases while the gate reported every one of them
present, *in the sequence next door*. A mutant whose kill requires a fixture is exactly the mutant
worth committing, and the reasoning beside it is the part that is not re-derivable.

**MEDIUM — the gate dictated remedy text it could not hold true.** Its failure message told the
operator to write *"landed on `main`, NOT tagged and NOT on PyPI"*. **`NOT tagged` is a claim about
git that goes false at the tag**, while the version is still unpublished and the *Published
versions* row may legitimately still lag — so the gate would have been green over a marker it had
itself dictated and which had become half-false. The qualifier now names the index only. The rule:
**a check may only prescribe text whose truth it can keep checking**; anything else it suggests is
a claim it has quietly delegated to a human and stopped watching.

**LOW, stated before the build rather than discovered after it — layer 2's green is narrower than it
looks.** `docs/RELEASING.md` permits the *Published versions* row to lag a release, because an entry
is held back until it is verified from the index. So after a successful publish `line3 > R` still
holds and layer 2 stays green over a marker that has become false. It enforces the marker's removal
**at the moment the row is updated, not at the moment of publication**; the publication window is
layer 3's, which is soft and not built. This is written into the tool's docstring, not only here,
because the next person to over-read this gate's green will be reading the tool.
