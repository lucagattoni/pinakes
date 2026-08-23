## When a constant cannot be declared, constrain it (20260823)

The echo class — *a gate reading a constant out of the document it polices* — turned up **four
times in one gate**, and the interesting part is that the same remedy did not work every time.

| Echo | Exploit | Remedy |
|---|---|---|
| sequence start = its own oldest entry | delete the oldest row; the start moves and hides it | **declare** it |
| lagging ceiling = its own newest entry | delete the newest entry; the ceiling drops with it | **bound** how far it may lag |
| Part range = its own heading | append a range to `# Part 5` and a misfiled section is legal | **constrain** it |
| Part count floor = one below the truth | demote `# Part 5`; the floor passes exactly | raise it to the real count |

**The third could not be declared, and that is the lesson.** Reading Part ranges out of the headings
is *why* the mapping cannot drift from the document — replacing them with a table in the tool would
reintroduce the drift the gate exists to catch. So the echo had to stay and be made unexploitable
instead: two Parts may not claim the same version, and the Parts must ascend. `# Part 4` declaring
`` `0.8.0` onward `` is then precisely what stops `# Part 5` declaring it.

**Declare, bound, constrain — in that order of preference.** Declaring is strongest and cheapest
when the value is genuinely external. Bounding admits the echo and limits its travel. Constraining
leaves the echo and removes the *freedom* that made it exploitable. Reaching for the first when only
the third is available produces a table nobody updates.

**A floor one below the truth is a floor with a bypass.** `PARTS_MINIMUM` was 4 against 5 real
Parts, so demoting the last heading passed it *exactly* while handing every section beneath to the
open-ended Part above. Floors here are written as "this only ever holds, because things are never
removed" — which is an argument for setting them **at** the count, not below it. A floor with slack
is a floor someone can stand in.

**And a test that asserts a sentence asserts only that something went wrong.** Three instances in
one increment, each found by mutation and none by reading:

- a range-form test asserting a *failure* — satisfied by breaking the form entirely
- placement fixtures guarded by `assert "reads ascending" not in stderr` — satisfied by a reworded
  message, and by a second failure appearing beside the one under test
- an ordering test asserting `"must ascend with the document"` — satisfied with the comparison
  reversed, because a different, correctly-ordered pair then fires and prints the same words

The positive form in each case: assert **exactly one** failure and **which** one — the pair, the
Parts, the versions. `failures_of()` exists for that.

**On the audit itself.** These were found by four independent lenses over the landed gate, each
finding then handed to a separate agent told to refute it — not by re-reading the diff. Two of the
four lenses found nothing. The two exploits came from the lens that was asked one question only:
*for every constant this gate uses, where does its value come from?*
