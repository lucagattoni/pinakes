## Planning the exposure question — a check that cannot see the case it is for (20260825 07:55)

**HIGH — the 0.30.2 gitignore detector reports `protected` for a repository that is committing the
user's verbatim questions, and the reason is the fix that made it correct.** The detector probes
**opaque random tokens** under `.pinakes/`, chosen on 20260825 so that no realistic pattern could
target them — which had been a real regression when three *named* files were covered by an ordinary
`*.db`/`*.json` pair. But a path that does not exist cannot be in the index, and
`git check-ignore` consults the index: on a *tracked* path it answers **not ignored**, and only
`--no-index` answers **ignored**. So the probes can ask exactly one question — *would a new file
here be ignored?* — and never the other one — *is anything in there tracked right now?*

Measured, not reasoned: a repository with `.pinakes/{deep/op1.json,ledger.jsonl,index.db}`
committed, then a **correct** `.gitignore` added, still lists all three in `git ls-files`, still
commits the edited transcript under `git commit -a` — and `_ignored_by_git` returns `True`.

**The general shape, and it is the fourth instance in two days: a fix that removes a false positive
can install a permanent blind spot, and nothing reports the trade.** The opacity that made the
detector right about patterns is exactly what makes it blind to the index. Neither property was
written down, so the boundary was invisible to review.

**MEDIUM — a correct `.gitignore` does not untrack an already-tracked file, and Pinakes says so
nowhere.** `grep -rniE "rm --cached|untrack|already[ -]tracked|already in the index"` over
`*.py *.md *.toml *.sh *.yaml` returns only `tools/template_drift_gate.py`, `tools/mutate.py`
and a retrospective about the **wheel**. This matters because `init.py` already states the rule it
breaks — *"the printed remedy must never instruct an action that would not change the verdict"* —
and for a tracked-and-unignored KB, *"add this line"* flips the verdict to protected while changing
nothing about the exposure.

**HIGH — a section heading is a status claim, and it produced the same collision twice in two days.**
`plans/20260731_1202-open-corrections.md` carries an item under `## Live` whose body says
`CLOSED 20260824 00:35` twenty-six lines below its own `**Decided.**` line. On 20260824 a coder
session read it as live and was about to rebuild a landed increment. **On 20260825 a second,
freshly-cleared coder session did the identical thing and offered to build it again.** Both times
the save was a peer message; neither time was it a gate. `grep '^## '` returns *Live* and stops.

**MEDIUM — `sed -i '' "s/X\bY/"` on macOS silently matches nothing, and a success message computed
before the operation will not notice.** Renumbering four colliding decision IDs, the loop printed
*"7 line(s) rewritten"* — which was `grep`'s **pre**-count, not `sed`'s result. BSD `sed` does
not implement `\b`. The file was unchanged and the log said otherwise. Reading the file back
afterwards is what caught it; `perl -pi -e` is what fixed it. **A count taken before an operation
describes the input, never the outcome.**

**HIGH — the proposed fix for that blind spot failed in the blind spot's own direction, and two
sessions caught it only by running it.** The first draft specified `git ls-files -- .pinakes`, with a
**relative** pathspec. Run from a subdirectory of a repository that is tracking three files under
`.pinakes/`, it returns **`rc=0` with zero rows** — and a genuinely clean repository returns
**`rc=0` with zero rows** as well. `pnk init` can be run from anywhere, so the two states are
reachable, identical at runtime, and the wrong one reads as *safe*. The absolute pathspec returns
three rows from the same directory. **A check that answers *clean* because it was asked the wrong
question is exactly what the increment it corrects existed to remove**, so the fix has to make the
pathspec structural — build it from the resolved root, and test it **from a subdirectory**, because
the failing case is invisible from the root.

**MEDIUM — a remedy whose steps are right and whose order is wrong fails silently.** In a repository
with no ignore line, `git rm -r --cached .pinakes` followed by an ordinary `git add -A` puts the file
**straight back in the index** (measured: one file, immediately). The ignore line has to come first.
The reverse order looks like it worked and reverts on the user's next `add`.

**HIGH — knowing a hazard is not what avoids it; running the command bare is.** The boundary table
above was first read through `... 2>&1 | head -3`, which reported the outside-a-repository case as
`rc=0` instead of `128` — the pipe's status, not git's. **This repository had already recorded that
exact hazard, twice, and the session that walked into it had read the entry that morning, within the
hour.** The entry is therefore restated in its stronger form: *the rule does not fire on
recognition. The only thing that separates a real exit status from a plausible one is running the
gate bare and reading `$?`.*

**HIGH — the plan wrote a constraint from a measurement taken in the wrong place.** § X1 required
the tracked-check's pathspec to be absolute *and* prescribed the test that would prove it: *"run it
from a subdirectory — the case that fails is invisible from the root."* The property is real. **The
prescribed test cannot fail**, because `_ask_git` passes `cwd=root` to `subprocess.run`
(`init.py:94`) and every call site passes `root` — so the process cwd never reaches git and a
relative `.pinakes` resolves against `root` regardless. The reproduction behind the constraint was a
*shell* fact, run with `cwd=<subdir>`, a state this code never produces. **It was promoted to a
claim about a code path without anyone opening that code path's cwd.**

**The domain nobody examined was the instrument.** Every other item here is a claim whose population
went unstated; this one is a *test* whose ability to observe anything went unstated. The argument for
the property was sound and stays sound — the absolute form survives as defence. What was wrong was
the belief that a named test would pin it. **A prescribed test is a claim about a failing test, and
whoever prescribes it owes the same evidence as whoever writes it.** The increment's own
retrospective carries the mutation run that settled it, and the finding is recorded there rather
than here.

**MEDIUM — the planner produced the day's own lesson while writing the plan about it.** I told a
coder that 36 unrowed `test_fragments.py` tests were a gap to fill. It counted the population
instead: **2023 tests defined, 1106 named in `docs/VERIFICATION.md`, 917 with no row** — and the
document's own scope section says it maps *promises to tests*, naming six modules that predate the
table. A gap of 917 cannot all be holes. The coder declined, correctly, and cited *a peer message is
coordination, never permission*. **Two honest counts of that same population differed by twelve
(1106/917 against 1094/929) purely because the matching rule differed, and neither number carries
its rule.**

**LOW — `zsh` does not word-split unquoted parameter expansions, so `set -- $pair` inside a
`for` loop passes one argument, not two.** The anchor assertion caught it before any write. Worth
keeping only because the assertion is the reason: the guard that looked like ceremony was the thing
that turned a silent no-op into a stop.
