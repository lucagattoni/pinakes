# A review that reported less than it found — the 20260830 red-`main` incident, closed

**`main` is green and every row of this file's build order is ✅ done** (the last, 20260831 22:17
UTC). The H1 read *"`main` is red on the clock"* until 20260831 22:36 — an unqualified
present-tense status claim, first line of a file `CLAUDE.md` and `docs/README.md` both route a
cleared session to. **The filename keeps its original words on purpose**: both entry points link
it, and renaming a file to fix a sentence breaks the links that make the sentence findable.
**Read on for what this file carries** — the 22 findings and their verdicts, the selector rule,
and the six wrong claims of one day — not for the incident it is named after.

**Written 20260830 09:27 UTC against `main` at `3712a7f`.** Two things happened while nobody was
looking, four days apart, and neither is visible from a commit. **This file exists because the only
other record of them was `RESUME.md`, which [`docs/BUILDING.md`](../docs/BUILDING.md) calls *"a
convenience, never a carrier"* — excluded from git, invisible to every other checkout, and unable to
tell anyone it exists.**

> ## ✅ CLOSED — every blocker in this file is discharged
> **This banner read *"one decision is the user's and it blocks everything … nothing lands"* until
> 20260831.** It was wrong by 20260830: the suite went green in `b59e58f`, **0.31.0 published**, and
> twelve merges landed after it. `./check.sh` exits 0 and the four once-failing files give
> **249 passed, 1 skipped, 0 failed**. **Read this file for §§ *The 22 nobody has ever checked*
> — now **CHECKED**, 20260831: four confirmed, eight pointing at files that no longer exist, one
> still open, and the ratio is the lesson — *Five defects of one shape* and the `TZ=UTC` trap.
> Not for the incident it is named after. **Build order row 5, the last open row, is closed.**

## 1. ✅ CLOSED — `main`'s test suite was red, and no commit did it

**Measured 20260830 09:0x UTC on a clean checkout of `3712a7f`: `./check.sh` exits 1,
`25 failed, 2331 passed, 4 skipped`.** Every other gate passes — this is the whole of it:

| Gate | |
|---|---|
| `ruff check`, `ruff format --check` | ✅ |
| `pyright` strict | ✅ 0 errors, 0 warnings, 0 informations |
| **`pytest`** | ❌ **25 failed** |
| `fragments --check`, `markdown_link_gate`, `release_order_gate`, `status_header_gate`, `shared_file_overlap --strict` | ✅ |
| `make docs` (`mkdocs --strict`) | ✅ |

**The cause is the calendar.** `src/pinakes/budget/prices.toml` carries `as_of = "20260728 16:31"`.
`src/pinakes/manifest.py:880` and `:893` default `max_price_age_days` to **30**. The table went
stale at **20260827 16:31**. The product then says so itself, correctly:

    error: pinakes's bundled prices.toml is dated '20260728 16:31', older than the
    configured max_price_age_days (30).

The estimator refuses to price, `cost_eur` comes back `None`, `pnk ask --deep` exits 1.

| Failing file | count |
|---|---|
| `tests/test_cli_ask.py` | 18 |
| `tests/test_extract_claude.py` | 5 |
| `tests/test_doctor.py` (the price-table row asserts `OK`, gets `WARN`) | 1 |
| `tests/test_pdf_trace.py` | 1 |

**Proved by experiment, not inferred.** Advancing `as_of` to today and re-running those four files
gives **`249 passed, 1 skipped, 0 failed`**; restoring the committed date brings all 25 back. The
tree was restored and `__pycache__` cleared; `git status` clean.

**CI's green was a lie of omission, and it is no longer even stale — it has gone red.** The green
was dated **20260826 11:51** with nothing run since. **The prediction this paragraph used to make
has since been measured, and it was wrong in every particular except the cause.** Run
`33304454176` on `b9fb71e` (pushed 20260830 09:35 UTC) **failed on the `check (light pdf)` leg** at
09:39:07Z — *not* the `[light,pdf,claude]` leg this file named — while `check (light pdf claude)`
and `check (light)` were **cancelled by fail-fast** rather than finishing, so the predicted "green
`docs` job beside one green and one red matrix leg" did not happen either. Every failing assertion
in that log is the `prices.toml` refusal, verbatim, which is the half that held.

**Settled 20260830 14:18 by a second red run — every matrix leg fails, and which one *reports* is a
race.** Run `33316335921` (merge of the planner's document work) failed on **`check (light)`**, while
`check (light pdf)` and `check (light pdf claude)` were the cancelled pair — the exact inverse of
run `33304454176` an hour earlier. **So the `[light]` leg does not stay green**, and this file's
original guess that its `skipif` guards would spare it is false: `[light]` carries **19** of the 25,
skipping six behind the extras. **Fail-fast means the named leg identifies nothing except which
runner lost the race**, and reading a leg name as scope would understate the fix by six tests.
**Both runs' documentation jobs were green throughout** — `markdown-links`, `status-header`,
`link-density`, `build`, `template-drift`, `traversal-caps` and every `eval` job — which is what
makes the failure attributable to the calendar rather than to anything that landed.

**A green run is a claim about the moment it ran** — this repository has written that sentence before and had not yet
met a case where the tree did not change at all. It has now met one, and then guessed the shape of
its own failure wrong while standing next to it.

**The irony is load-bearing and belongs in the record.** `tools/status_header_gate.py:52` rejects a
wall-clock staleness check with *"a wall-clock staleness check fails on a quiet weekend with no code
change"* — **and cites `prices.toml` as the precedent for not adding one.** `prices.toml`'s own age
then failed the suite after a quiet four days with no code change. The precedent invoked to avoid
the failure mode is the thing that exhibited it.

**And the design already decided this should not be a build gate.** `docs/DESIGN.md` §5 chose a
runtime refusal plus a `doctor` WARN precisely so staleness would not gate a build. **25 tests then
asserted the un-stale path without pinning a clock, and the suite became the gate the design
refused.** That is the defect: not the constant, and not the table's age, but tests that inherit
today's date and assert an outcome that depends on it.

### The decision

**Three remedies. Only one stops it recurring, and the choice is not free either way.**

| | What it does | For | Against |
|---|---|---|---|
| **A. Re-measure the vendor prices and bump `as_of`** | the honest refresh | the table is *supposed* to be current; every EUR figure the project prints becomes true again | needs real vendor numbers, so it is not a keystroke; and **it resets the timer rather than removing it** — the same 25 tests break again 30 days later |
| **B. Raise `max_price_age_days`** | moves the cliff | one line, no measurement | **weakens a deliberate guard.** The whole point is that a stale table must not silently price a paid run. Raising it trades a correct refusal for a quiet suite |
| **C. Pin the clock in the affected tests** ⭐ | the tests stop inheriting today's date | **the only option that stops recurrence.** It also restores `DESIGN.md` §5's intent — staleness stays a runtime refusal and a `doctor` WARN, and stops being a build gate nobody chose | a `tests/` change, so it is the **coder's**; and it must not pin so hard that a genuinely stale table stops being caught — the refusal itself still needs a test |

### 🛑 NARROWED 20260830 09:40 — C is a *correction*, not a preference, and it needs no decision

**Two peers found what makes this smaller than the table above suggests, and every citation below
was verified by the planner rather than relayed:**

- **`docs/DESIGN.md:811`, verbatim:** *"Staleness is deliberately **not** a CI gate: a wall-clock
  check would fail a quiet weekend with no code change at all."*
- **`src/pinakes/doctor.py:1571`** says it again in its own docstring — *"deliberately never a CI
  gate"*.
- **`tests/test_doctor.py:596-598`** asserts `Status.OK` from a check that reads the wall clock.
  **That test *is* the CI gate the design forbids**, and it failed on the exact scenario both
  sentences name.
- **`tests/test_deep_loop.py:153-154` already carries the cure and says why** — a `prices()` helper
  returning the shipped table with `as_of=NOW`, docstringed *"so staleness is never why a test
  fails"*. `test_doctor.py` never adopted it.

**So option C restores a decision the project already took, using a pattern already in the tree.**
It is a defect fix and it does not need the user. **A and B remain worth doing on their own merits,
and neither is needed to unblock CI.**

**✅ SHIPPED IN 0.31.0 — this paragraph described the state until 20260830.** What needed the user was the bigger half, and it is done: `docs/RELEASING.md` § *Before you start* step 3 now refreshes the table at every release, and `as_of` was re-stamped for the first time in that release. The paragraph is kept because the *mechanism* it describes is why the step exists. `git log --follow src/pinakes/budget/prices.toml`
shows `as_of` was written **once, at creation, and never refreshed**, and `docs/RELEASING.md`
mentions prices **zero times**. So **every installed copy refuses paid estimates 30 days after each
release**, and the remedy the error itself prints — *"Upgrade pinakes to refresh the bundled
prices"* — names a release step **that does not exist**. A shipped defect with a documentation half
(`docs/RELEASING.md`, planner-owned) and a numbers half nobody can invent. **It recurs every 30 days
until a release step exists.**

**Scope correction worth keeping:** it is **25 tests across four files**, not one. `test_doctor.py`
is the only one asserting the WARN directly; the 18 in `test_cli_ask.py` fail one layer in, where
the estimator refuses to price — **the design working as intended**, seen through tests that assumed
it never would.

## 2. A five-lens review of the planner's own work reported less than it found

**Workflow `wf_1075a32b-c8f`, 20260826. 52 agents, 26 errored on a session limit.** 51 findings
raised; **21 verified — 15 survived, 6 refuted; 30 never verified at all.**

**A second review died the same way within hours.** The coder's S16 pass — 19 agents, 17 dead —
returned a literal `{"raised":0,"confirmed":[],"refuted":[]}`. **Two independent instances in one
day is the contract, not bad luck**: a dead agent becomes `null`, `.filter(Boolean)` erases it, and
the pass reports a clean bill it never earned. Seven findings were recovered from its transcripts.

**Both are recoverable the same way, and that is a procedure rather than a warning: the agents'
transcripts survive on disk.** And **`tools/review_ledger.py` (on `main`) exits 1 on a pass that did
not finish — it would have caught both before either result was read.**

**A third hole was the planner's own and had nothing to do with the limit.** The workflow capped one
lens at `.slice(0, 12)` when it had raised **16**, and **logged nothing**. The four were recovered by
reading the journal; **three were real.** *A workflow that bounds coverage must `log()` what it
dropped.*

**Where the findings live** — durable, outside the repo, and outside any session's scratch:

    ~/.claude/projects/-Users-luca-Code-repos-github-lucagattoni-Pinakes/
      8f4c86d5-a2cf-4d2c-ad0a-eddcd74e9465/subagents/workflows/wf_1075a32b-c8f/
        journal.jsonl        one {"type":"result"} line per completed agent
        SURVIVED.md          the 15 that survived refutation, with locators and verify-commands
        PAIRED-RESULT.txt    the workflow's own paired output

**Of the 15 that survived, one is fixed.** The rest are live on `3712a7f`.

### The anatomy of the death, and why the intuition about it is backwards

**Measured by the `optimize-adversarial-review-tokens` session from the run's own 52 `agent-*.jsonl`
transcripts, deduplicated by `requestId`; cost in price-units
(`input x1 + cache_write x1.25 + cache_read x0.1 + output x5`), a ratio model and not currency.**
The planner re-derived the journal accounting independently and takes the per-agent costs on the
method stated; **the distinction is recorded because it is this document's own subject.**

| | |
|---|---|
| Agents / requests / cost | **52 · 749 · 10 185 819 price-units** |
| Journal | `started 52`, `result 26`, `failed 26` — **yield 26/52 = 50%** |
| **The five `Find` lenses** | **71.4% of the entire run** (18.3 + 14.2 + 14.0 + 13.7 + 11.2%), 455 of 749 requests, **73–97 requests each at 187k–250k context** |
| The other 47 | none above **1.7%** |
| Session-limit deaths | **26**, all inside **11:55:26–11:55:47** — a 21-second window |
| Of those, dead at request 1, zero context | **18** |
| **Combined cost of all 26 dead agents** | **4.69%** |

**The intuition is backwards, and that is the finding.** A reader who hears "26 agents died on a
session limit" guards the dead agents. **They cost 4.69% between them and 18 of them never ran at
all.** The loss is the **71.4% that succeeded** — five deep document reviews, each a *session* rather
than a subagent task, whose findings the verify stage then never consumed. **Narrowing the five
lenses buys more than capping the forty-seven verifiers**, and the run was shaped the other way.

**`wf_1075a32b-c8f.json` records `"status": "completed"` beside `agentCount: 52`.** Half the fan-out
was gone and nothing in the artefact says so — because `parallel()`/`pipeline()` resolve a dead agent
to `null`, `.filter(Boolean)` erases it, and a script that reads its own empty result as clean will
return one. **The authoring reference's *"no silent caps: `log()` what was dropped"* rule was written
for deliberate truncation and does not cover being killed** — and this run managed both, since the
planner's own `.slice(0, 12)` silently discarded four raised findings on top of it.

**The recovery window is narrower than the failure window, and that is a design gap rather than an
oversight.** `resumeFromRunId` is documented **same-session-only**. The thing that killed the run —
a session limit — is also what ends the session that could resume it. **The 26 cached results were
recoverable only from the transcripts on disk**, which is how all seven of the coder's findings and
all four of the `.slice()` casualties came back.

### Confirmed by hand on 20260830, and none of them a typo

**Four of the five rows below carried no disposition until 20260831 22:36**, so only row 1 read as
fixed and the rest read as live. **All five are fixed and landed** — build-order row 3 records the
per-row evidence — **except `docs/VERIFICATION.md:198`, which is genuinely still open.** This is
the two-register shape `CLAUDE.md` names, one level in: the heading is an accurate dated record,
and the rows under it were the register nobody updated.

| Where | Defect |
|---|---|
| `docs/STATUS.md:20`, `:366`, `:1210` | **A bare `\|` inside a code span truncates the row on GitHub — and only on GitHub.** GFM splits the row on the bare pipe *before* inline code is parsed, then **silently drops the overflow to match the header's column count**, so the table still shows the right number of cells and looks intact. **14, 286 and 2 860 characters are discarded.** The 2 860 is the whole per-release commentary from 0.22.0 down to 0.4.1 — including the 0.20.1 warning that a KB setting `vector_tier = "sqlite-vec"` **stops loading entirely**. The published mkdocs site renders all three correctly and in full. **Fixed 20260830**, with the full population and the matrix below |
| `docs/BUILDING.md:172` | *"the changelog fragment written in `d9fe1a9` carried 'wrong for twelve hours'"* — **at `d9fe1a9` it does not.** The phrase lived only at `29856b9`; `ef1465a` corrected it *before* the merge. The sha in the sentence is wrong |
| `plans/20260825_1240-run-pinakes-sweep.md:417` | *"the reasoning is also in `src/pinakes/pairing.py`'s docstring"* — `grep -ci cycle src/pinakes/pairing.py` is **0** on `main`. True only on the coder's **unlanded** branch |
| `docs/VERIFICATION.md:787`, `:282` | **✅ Fixed 20260831 22:36 — both, and the fix is to stop citing lines.** `:282` is cited by `plans/20260825_1240` for *"comments survive a rewrite"*; on `main` that row is *"unknown keys inside a link entry survive it"*, and the promise wanted lives one row above. It now cites the **row text and its test**, so nothing below it can move it again. `:787` was already discharged by layer 2 (`plans/20260825_0749` build-order row 10). **The pairing recorded in this cell was itself wrong** — `:282` was never the empty-tag/hub row, and the over-long-path row is `:299` today, not `:787`. A locator-rot finding whose own locators had rotted |
| `plans/20260825_1252-plans-sweep-findings.md:87` (row 11) | **a thirteenth stale row the reconciliation missed** — says D-31/32/33 *"none taken"* and `user-decision` when they were answered 20260825 18:16. `docs/README.md:55` says the opposite about the same item |

### The pipe defect is a class, and no escape fixes both renderers

**Raised as three lines. Measured across every markdown file in the repository, it is fourteen, in
two halves that break *opposite* renderers.** Both were fixed 20260830; the matrix is kept because
the obvious fix is the wrong one.

| Source, inside a code span **in a table row** | GitHub | mkdocs / the published site |
|---|---|---|
| `` `paid\|transcripts` `` — a bare pipe | ❌ **row truncated, text destroyed** | ✅ correct |
| `` `paid\\|transcripts` `` — the "obvious" escape | ✅ correct | ❌ **renders a literal backslash** |
| `` `paid&#124;transcripts` `` — an entity | ❌ literal `&#124;` | ❌ literal `&#124;` |
| `<code>paid&#124;transcripts</code>` — raw HTML | ✅ | ✅ |
| **No pipe in the span at all** ⭐ | ✅ | ✅ |

**So the finding's own wording — *"unescaped"* — invites the fix that breaks the site.** Escaping was
already the repo's convention in four published places, and
[the live CLI page](https://lucagattoni.github.io/pinakes/CLI/) was serving `--backend st\|light`,
**backslash and all, to every reader**. Half A destroys text on GitHub; half B disfigures the site.
Both were live at once, in the same repository, under opposite conventions.

**The fix taken is the last row — keep the pipe out of the code span** — rather than raw HTML, because
it needs no `md_in_html`, and because rewriting `--clear-cache[=paid|transcripts]` to name its three
real values corrected a **second** defect nobody had raised: `cli.py`'s `nargs="?" const="all"` makes
`all` a valid value, and the old text omitted it.

> **The distinction that makes this diagnosable: `\|` behaves differently in a table row than in
> prose, and only the table row diverges.** GFM's *table* parser consumes the backslash before inline
> parsing; there is no table parser in prose, so both renderers leave `\|` alone. That is why
> `docs/RELEASING.md:187` and `docs/STATUS.md:1140` — `grep` commands where `\|` is **correct BRE
> alternation** — are right as they stand and must not be "fixed". **The same three characters are a
> defect in one context and required syntax in the other.**

**And this document exhibited the defect while documenting it.** The 22-row table above was generated
with pipe-escaping but not backtick-balancing, so a truncated locator left a code span open — the
same class, self-inflicted, inside the section describing it. Regenerated.

**And the `STATUS.md` one nearly went into this file backwards.** It was first written here as *"a
rendering defect on the published site, and `mkdocs --strict` exits 0 on it"*. **Both halves were
wrong.** Rendering it proved mkdocs is the renderer that gets it *right*; GitHub is the one that
loses the text. `mkdocs --strict` exits 0 because **there is nothing for it to complain about** — not
because it is blind. **A gate cannot catch a defect that does not exist in the artefact it builds**,
and the real finding is the divergence: this repository's documents are read in two renderers, CI
checks one, and the public one is the other.

**The `BUILDING.md` one is the argument for independent verification, because the author confirmed
it as true twice.** Checking `29856b9` while the sentence names `d9fe1a9`. **Four measurements of
that one string failed first**: a line-based `grep` (the phrase was wrapped across a newline), a
`tr '\n' ' '` pass (indentation left multiple spaces), a shell-loop quoting artifact that returned
`0` for a file that contained it, and finally reading the wrong sha. **Three independent agents got
it right.** *The author is not a reliable verifier of the author's own text* — and a shell one-liner
composed in the moment is not a reliable instrument for checking prose.

## What item 1 actually costs

**This section exists because the row above it was wrong for two hours.** It said the
`test_doctor.py` fix "Unblocks `./check.sh`". **It unblocks 1 of 25.** Both live peers found the
same thing independently and within minutes of each other; the planner then verified the mechanism
rather than relaying it, and it is sharper than either report.

**There is nothing to fix in the estimator.** `src/pinakes/budget/estimate.py:82`'s
`assert_prices_fresh` is *already pure*, and says so:

> `now` is an explicit `YYYYMMDD HH:MM` string, never the wall clock: staleness is checked against
> whatever the caller supplies, which is what keeps every estimator pure and deterministic under
> test.

**The impurity is in the callers, and there are four unconditional ones:**

| Call site | |
|---|---|
| `src/pinakes/cli.py:874` | `now = datetime.now(UTC).strftime(...)` — no seam |
| `src/pinakes/cli.py:1259` | `now=datetime.now(UTC)` — no seam |
| `src/pinakes/extract/claude.py:649` | `now=datetime.now(UTC).strftime(...)` — no seam |
| `src/pinakes/doctor.py:1586` | `age = (datetime.now(UTC) - as_of).days` — the WARN path |
| `src/pinakes/cli.py:667` | `now or datetime.now(UTC)` — the only one that already has a seam |

> 🛑 **That table is true and it points at the wrong fix. It is kept because being wrong this way is
> the subject of this document.** The planner established the four call sites and inferred *"so add
> seams to them"*. The coder then falsified the inference without disputing a single fact in it:
> **`tests/test_cli_ask.py` drives real `main([...])` — 45 times — so there is no `now` to inject.**
> Adding a seam to all three unseamed call sites would not make **one** of its 18 failures
> reachable. Every clause was true and the conclusion did not follow, because the population the
> argument was over — *the failing tests* — had never been examined.

**The seam has to be the price table, not the clock — and the repository already does this twice:**

| Existing pattern | |
|---|---|
| `tests/test_deep_loop.py:152` | `Prices(as_of=NOW, usd_per_eur=…, models=load_prices().models)`, docstringed *"so staleness is never why a test fails"* |
| `tests/test_extract_claude.py:145` | the same helper, independently |

**So this is a test-side change, which is also why it needs no decision.** No production seam, no
new parameter, no `src/` edit at all.

**And the defect's own cause was written down beside it, as an assumption.**
**[Discharged 20260830 by `240e121`/`b59e58f`; the tense below is that of the incident.]** `test_the_price_table_is_reported_with_its_date` no longer reads the wall clock — it builds a fresh `Prices` and monkeypatches `doctor_module.load_prices`, and its docstring now says *"Neither compares the wall clock against the committed `as_of`, because staleness is deliberately not a CI gate."* Its sibling was corrected in the same change. **Read this section as the reasoning behind build-order row 1, which is ✅ BUILT — not as work owed.** At the time:
`tests/test_doctor.py`'s failing `test_the_price_table_is_reported_with_its_date` asserted
`Status.OK` from the real table and the real clock. **One function below it**, its sibling
`test_a_stale_price_table_warns_and_names_the_setting` ages the *table* rather than the clock, and
says why:

> *"**The shipped table is current by construction**, so the *table* is aged rather than the clock:
> … freezing the clock would test a mock rather than the comparison."*

**That premise is now false, in the file the fix lands in.** So the fix is symmetric: the failing
test pins a *fresh* table exactly as its sibling pins an aged one — **and the sibling's docstring is
corrected in the same change**, or the fix leaves behind the very assumption that produced the
defect.

**So the 25 failures are two mechanisms, not one.** `test_doctor.py`'s single failure is the
**WARN**; the other 24 (`test_cli_ask.py` 18, `test_extract_claude.py` 5, `test_pdf_trace.py` 1) go
through the **refusal**, which is the design working exactly as intended, seen through tests that
assumed it never would.

**The count depends on your extras, and this is why two sessions measured it differently all
morning without either being wrong:** a worktree with the extras installed reproduces **all 25**; a
`[light]`-only checkout shows **19** and skips the other six behind their `skipif` guards.

## Nothing was watching for this, and a CI watcher would not have been

**The standing guidance is to arm a background watcher over `gh run list` and emit on every terminal
non-success.** One was armed here. **It could not have caught this**, and the reason generalises:

> **A run-watcher fires on failing *runs*. It is silent about a tree that goes red without a run.**

Between 20260826 11:51 and 20260830 09:35 **nothing was pushed**, so nothing ran, so there was
nothing to fail. The repository was broken for **three days** in a state no watcher of that shape can
observe: `main`'s last run was green, and it stayed green, and it was wrong. **The green was not
stale in the ordinary sense of "an older commit" — it was a correct measurement of a tree that had
since changed meaning without changing content.**

**What would have caught it, in the order they would have fired:**

| | |
|---|---|
| **A scheduled run** (cron on `main`) | would have gone red on 20260827, three days earlier. **It is also the thing `DESIGN.md:811` is wary of** — until item 1 lands. Afterwards a nightly run cannot go red on staleness, because nothing in the suite reads the clock any more, so the objection dissolves and the schedule becomes safe |
| **The release step** (item 2) | catches it at each release, which is the path that actually reaches users |
| **A watcher over the artefact rather than the run** | the general form of the standing rule — *verify the artefact, never the run's own status* — applied to a tree instead of a release |

**Nothing automatic catches it for a user who does not upgrade, and nothing should**: the runtime
refusal *is* the intended behaviour there. **The defect was never that Pinakes refused. It was that
the suite asserted it never would, and that no release had ever moved the date it refuses from.**

## The 22 nobody has ever checked

**30 of the 51 raises were never verified.** Deduplicated against the 14 that item 4 already covers,
**22 distinct findings remain, and no one has ever looked at any of them.** They are listed here
because the sole record was a `journal.jsonl` in a session directory — the precise failure this
document exists to stop. Severity is **as raised**, by an agent whose claim was never tested: three
HIGH, seven MEDIUM, twelve LOW. **Read the column as "what an unverified agent asserted", never as a
defect count.**

| Sev | File | Locator | What the text says |
|---|---|---|---|
| HIGH | `plans/20260825_1252-plans-sweep-findings.md` | line 81 (Actionable row 5) | \| 5 \| `plans/20260825_0749-exposure-and-silent-status.md` — *X7 — line 3's three layers (D-35 answered … |
| HIGH | `retro.d/20260826_0632-the-queues-describe-the-tree.md` | line 47 | **MEDIUM — I invented a duration inside a pass about unmeasured claims.** I wrote *"fourteen hours"* for … |
| MEDIUM | `retro.d/20260826_0702-one-fix-falsified-six-documents.md` | line 1 and line 3 — "six documents" | "## One code change falsified six documents…" / "The moment it landed, **six documents were false** — and … |
| MEDIUM | `plans/20260731_1202-open-corrections.md` | line 118 — "**D-35 layer 2 is in build**" | **The 0.30.3 tag is taken and still pending**, so of the three gates on it, this one is now discharged: * … |
| HIGH | `retro.d/20260826_0632-the-queues-describe-the-tree.md` | lines 47–53 | "I wrote *\"fourteen hours\"* for how long the table said `S2 · LIVE`, four times across four files, and … |
| MEDIUM | `tools/batteries/README.md` | line 33 — "The covered files change 1–13 times in 30 days — **except `sync.py` at 39**" | "The covered files change 1–13 times in 30 days — except `sync.py` at 39, which was this paragraph's own … |
| MEDIUM | `plans/20260825_0749-exposure-and-silent-status.md` | line 617, build-order row 9 — "**LAYER 2 BUILT 20260826**, landed `6a77f3c` … 54 mutants, … | "LAYER 2 BUILT 20260826, landed `6a77f3c`: … **54 mutants, 0 survived**" |
| LOW | `retro.d/20260826_0702-one-fix-falsified-six-documents.md` | line 3 — "The moment it landed, **six documents were false**" (and the table at lines 5–10 … | "`make release-check` became a real gate in `674eda6`. The moment it landed, **six documents were false** … |
| LOW | `plans/20260825_1252-plans-sweep-findings.md` | lines 65–68 — "But eight rows have no build-order row anywhere … **12, 13, 14, 17, 22, 24, … | "eight rows have no build-order row anywhere, and for those this table is still the register — 12, 13, 14 … |
| LOW | `retro.d/20260826_1130-the-procedure-guaranteed-the-fragment-was-never-reviewed.md` | line 44 — "three of the nine disagreed with their own filename" | "Every fragment **heading** I typed by hand, and three of the nine disagreed with their own filename" |
| LOW | `retro.d/20260826_0702-one-fix-falsified-six-documents.md` | line 18 — "Here it was about twenty minutes and nothing published inside it" | "There is always a window. Here it was about twenty minutes and nothing published inside it, but that is … |
| LOW | `plans/20260825_0749-exposure-and-silent-status.md` | line 618, build-order row 10 — "**BUILT 20260826 07:24 UTC**" | "~~**X7 doc half**~~ — **BUILT 20260826 07:24 UTC.** `docs/RELEASING.md`'s line-3 sweep row now **asks fo … |
| MEDIUM | `docs/BUILDING.md` | line 179-180, "its last section is headed *CHANGED BY THIS INCREMENT, OPENED BY NOBODY*" | `python3 tools/review_ledger.py <increment>`, landing separately; its last section is headed *CHANGED BY … |
| MEDIUM | `plans/20260825_1252-plans-sweep-findings.md` | line 83 (Actionable row 7, rewritten and re-landed today), "VERIFICATION.md:282 pins it"; … | MANIFEST.md:303 promises comments survive and VERIFICATION.md:282 pins it |
| LOW | `retro.d/20260826_0638-a-gate-that-could-not-fail.md` | line 33, "Nine of the eleven tests supply `--repo` and `--expect-version`" | Nine of the eleven tests supply `--repo` and `--expect-version`, so the defaults are a region no fixture … |
| LOW | `retro.d/20260826_0659-the-half-a-gate-cannot-see.md` | line 24, "which of release_order_gate.py's **two** docs/STATUS.md sequences carries R … | `PUBLISHED_ROW` names which of `release_order_gate.py`'s **two** `docs/STATUS.md` sequences carries `R`. |
| LOW | `plans/20260825_1240-run-pinakes-sweep.md` | line 449 and 460: "docs/MANIFEST.md:307-319 lists ten exclusions" / "refuted against MA … | docs/MANIFEST.md:307-319 lists ten exclusions … a block-style-reflow finding was refuted against MANIF … |
| LOW | `docs/README.md` | line 61, "`docs/STATUS.md:303`, the `0.15.1` row out of release order" | One is fixed, and it is the one to read before leaving the rest: `docs/STATUS.md:303`, the `0.15.1` row o … |
| MEDIUM | `plans/20260825_1803-open-decisions.md` | line 592, the bullet beginning "**CORRECTION — `docs/GUIDE.md:797` does NOT miss this case … | The row reads: \| \unknown key(s)\ in a KB you did not edit \| The same cause, on a KB that declares * … |
| LOW | `plans/20260825_1803-open-decisions.md` | line 150, the bullet beginning "**The hold's public description is currently ACCURATE and … | - **The hold's public description is currently ACCURATE and live — closing an item the brief left unverif … |
| LOW | `plans/20260825_1803-open-decisions.md` | line 146, the bullet beginning "**CORRECTION to the brief: \"0.6.0 (MINOR) is the last rel … | - **CORRECTION to the brief: … 0.18.0 (20260807 22:37) opens its notes with "**`pnk doctor` now says *how … |
| LOW | `docs/STATUS.md` | line 308, `> # 🚫 Unbuilt work is named, never numbered` | > # 🚫 Unbuilt work is named, never numbered |

**Recovered by differencing the 51 raises against the 15 in `SURVIVED.md` and the 14 in item 4.**
Six of the 51 were refuted and are harmless to re-check; the extraction cannot tell which six, so
this list is an upper bound on work and a lower bound on nothing.

### ✅ CHECKED 20260831 22:17 UTC — 21 of the 22, one by one

**Four are real. Eight point at files that no longer exist.** The severities above are *as raised*,
by agents whose claims were never tested; measured against the tree they ran about **5:1 against**.
The section's own caveat — *an upper bound on work and a lower bound on nothing* — was right, and
this is what the bound was hiding.

**The single largest class is not a defect class at all.** Every cited `retro.d/2026082x-*.md`
fragment was consumed into `docs/RETROSPECTIVES.md` at a release, so **eight of the 22 were
unverifiable at their stated locator from the day the list was written**. `retro.d/` holds three
files, all 20260830. **A locator into a fragment directory has a shelf life of one release** — the
next list like this one should cite `docs/RETROSPECTIVES.md` and a quoted phrase, never a
`retro.d/` path and a line number.

| # | Locator as raised | Verdict |
|---|---|---|
| 1 | `20260825_1252` :81, Actionable row 5 — X7 | **CONFIRMED.** Layers 1 and 2 *are* built — `status_header_gate.py` `_check_hold_marker`, `PUBLISHED_ROW`, the `SEQUENCES` import. **Layer 3 is not**: nothing in `ci.yml` or `release.yml` queries the index. The row still reads *"Build the decided three-layer gate … LIVE"*, which sends a coder to rebuild layers 1–2 |
| 2, 5 | `retro.d/20260826_0632` :47 and :47–53 — *"fourteen hours"* | **ONE finding, not two, and already discharged.** Dead locator; the text lives at `docs/RETROSPECTIVES.md:8039` and **self-corrects there**: two hours for S2, twelve for the eleven decision rows, plus why the figure is not re-derivable |
| 3, 8, 11 | `retro.d/20260826_0702` :1, :3, :18 | **Dead locator** ×3 |
| 4 | `20260731_1202` :118 — *"D-35 layer 2 is in build"* | **CONFIRMED.** It is **built**, `6a77f3c`. The same sentence's *"the 0.30.3 tag is taken and still pending"* is stale twice over — 0.30.3 was never published and 0.31.0 was |
| 6 | `tools/batteries/README.md` :33 | **PARTLY CONFIRMED.** The *1–13* range still holds for covered files. The three named exceptions are rolling-window figures that have rolled: `sync.py` 39→**17**, `cli.py` 52→**29**, `doctor.py` 36→**23** (measured 20260831). **Freeze them as dated rather than re-measuring** — otherwise the paragraph is stale again next month |
| 7 | `20260825_0749` :617, row 9 — *"54 mutants, 0 survived"* | **REFUTED, and re-derivable.** At `6a77f3c` the two batteries that commit touched held **12 + 42 = 54**. They hold 12 + 45 = 57 today, which is why it read as unverifiable: the claim is true of the tree it was made against, not of this one |
| 9 | `20260825_1252` :65–68 — the eight rows with no build-order row | **✅ CLOSED 20260831 22:28 UTC — all eight dispositioned.** Four **parked** in the sweep plan's § *Decided work with an owner and no build order* (12 as one unit, 13, 17, 22); two **not queueable by an agent** (14 is *which release owns `pnk adopt`*, 24 needs the user's material); two **re-marked ⏸ DEFERRED** (26, 27 — eval-gated, *never scheduled*). **Correcting this cell's own first reading:** it said four were *already* parked there, which was false — the four rows in that section were different work entirely, and reading a section's row count is not reading its rows |
| 10, 15, 16 | `retro.d/20260826_1130` :44, `…_0638` :33, `…_0659` :24 | **Dead locator** ×3 |
| 12 | `20260825_0749` :618, row 10 — *"BUILT 20260826 07:24 UTC"* | **REFUTED.** `docs/RELEASING.md:170`'s line-3 sweep row does ask for the marker, with `R`, the naming rule and layer 2's four outcomes |
| 13 | `docs/BUILDING.md` :179–180 | **Already discharged.** `tools/review_ledger.py:818` prints *CHANGED BY THIS INCREMENT, OPENED BY NOBODY*, and the *"landing separately"* phrasing the finding quoted is gone |
| 14 | `20260825_1252` :83 — *"VERIFICATION.md:282 pins it"* | **Locator drift; the claim holds.** :282 is a symlink-link row now. The comment pins are at **:264** and **:347** |
| 17 | `20260825_1240` :449/:460 — *"MANIFEST.md:307–319 lists ten exclusions"* | **REFUTED.** Counted: still exactly **ten** |
| 18 | `docs/README.md` :61 — *"`docs/STATUS.md:303`, the `0.15.1` row"* | **Locator drift, inside a note recording a 20260811 fix.** `STATUS.md:303` is a `---` now. Cosmetic |
| 19 | `20260825_1803` :592 — *"`docs/GUIDE.md:797` … IS this case"* | **Locator drift; the claim holds.** The row is at **:804** and reads as quoted |
| 20 | `20260825_1803` :150 — *"the hold's public description is ACCURATE and live"* | **CONFIRMED stale.** The published site serves **`Latest release: 0.31.0`** (curled 20260831). It served 0.30.3 with the ⏸ qualifier when the bullet was written |
| 21 | `20260825_1803` :146 — the 0.18.0 correction | **REFUTED.** The correction is right: 0.18.0's `### Changed` opens with *"`pnk doctor` now says how far your template has drifted"* |
| 22 | `docs/STATUS.md` :308 | **Not actionable as recorded.** The line matches verbatim, so the locator is live — but the table truncated the raise, and what was alleged is unrecoverable. **A register that truncates the claim keeps the finding and loses the finding** |

**A near-miss worth keeping, because the instrument was mine.** The published `STATUS` page shows
**two** different *Latest release* strings. The second is inside a quoted incident narrative at
`docs/STATUS.md:1131`, not a competing claim — checked before reporting it. A `grep -o` over a
rendered page is a claim about a string, never about a page.

**And one the tool said itself**, unprompted, when asked whether the batteries still hold:
*"Every anchor resolves. That is not a green run: a `kills` selector renamed away is caught by the
baseline, which needs pytest, and an anchor that still matches while the code around it moved is
caught by nothing."*

**What was owed from this pass is done, 20260831 22:28 UTC**, none of it re-raising anything above.
Item 1's row now reads *layers 1–2 BUILT, layer 3 only* with an explicit *do not rebuild layers
1–2*; item 4's two stale sentences are corrected (0.30.3 was never published, D-35 layer 2 is built
at `6a77f3c`) and the neighbouring S-queue list gained S16's ✅; item 20's bullet is restamped
rather than rewritten, because it is a dated evidence record and only the word *currently* was ever
wrong; item 9 is closed above. **Item 6 is the one that could not be done here** —
`tools/batteries/README.md` must carry a third battery's name in the *implementer's own commit* for
`tests/test_batteries.py` to pass, so the replacement paragraph was **dictated to the coder**
(§ *Content mine, keystrokes yours*) with the figures **frozen to a stated 20260801–20260901
window** and the *"no invariant has a battery"* claim corrected: two batteries mutate
`docs/INVARIANTS.md` territory and say so in their own headers, which is true of the filenames and
false of the coverage.

## Five defects of one shape, and the rule that would have caught them

**20260830 produced five wrong claims across three sessions. Every one was a valid inference from a
true measurement, and every one was wrong about something nobody had written down.** None would
have been caught by any gate in this repository, because a gate reads an artefact and each of these
was a defect in *what the artefact was taken to be about*.

| The measurement, true in every case | The thing never stated |
|---|---|
| four unconditional `datetime.now(UTC)` call sites exist in `src/` | **the failing tests** — they drive real `main([...])`, so no seam at those sites is reachable |
| the row truncates, losing 2 860 characters | **which renderer** — and the escape that fixes GitHub renders a literal backslash on the published site |
| `check (light pdf)` is the failing CI leg | **which leg lost a fail-fast race** — read as scope, it understates the fix by six tests |
| 34 of 64 review waves produced no commit | **"produced no commit"** — the filter silently included every wave that correctly found nothing, which is the *success* condition |
| `release_order_gate` exits 1 | **which tree** — a worktree with an unlanded sweep, asserted about `main`, freezing two sessions |

**The first draft of the rule was *"name the population"*, and the reviewing peer refuted it as
ceremony**: applied to every claim it becomes a sentence everyone writes and nobody reads, and *a
rule that fires on everything selects nothing*. The refinement is theirs and it is sharper, because
in all five the population was **constructed rather than pointed at** — a filter, a query, a
checkout, a leg chosen by a race. Nobody misnamed a set they could point to.

> ### 🧭 When a claim rests on a set you selected or an instrument you chose, state the selector beside the claim
>
> **Not what the set contains — how it was chosen.** `git rev-parse HEAD` beside a test result. The
> filter predicate beside a ratio. The worktree path beside a gate's exit status. The renderer beside
> a rendering claim.
>
> **The test of the rule is that it exposes the flaw without anyone having to be clever:** writing
> *"waves that produced no commit"* beside *"34 of 64"* makes the error visible on the page.

**`or an instrument you chose` is the planner's addition** to the peer's wording, and it is what
extends the rule to the pipe defect: nothing was *selected* there — a renderer was *used*, and the
claim inherited its behaviour. Both halves are the same failure at different distances from the
data.

**The hardest case is the one where no choosing happened.** The peer's own words, and the most
useful sentence in the exchange: *"I did not choose 'waves with no commit' as a proxy for waste; I
chose it because it was the only thing the corpus could count. The selector was imposed by the
instrument."* **The planner's gate claim is the same** — no decision was taken to measure a worktree
instead of `main`; the measurement happened where the session was standing. **An
instrument-imposed selector is the hardest kind to notice, because there was never a moment of
choosing to look back on.**

### `TZ=UTC git log --date=format:` does not give UTC, and the repo already has a record it broke

**`CLAUDE.md` requires every timestamp to be UTC and says *read the clock, never compose it* — but
the obvious way to read a past stamp out of git is wrong, and silently.** `git log --date=format:`
formats with **the committer's recorded offset**, so `TZ=UTC` in front of it changes nothing.

Measured on `2209014`, one commit, four ways:

| | |
|---|---|
| `TZ=UTC … --date=format:'%Y%m%d %H:%M'` | `20260830 15:58` ❌ |
| `TZ=UTC … --date=format-local:'%Y%m%d %H:%M'` | `20260830 14:58` ✅ |
| `--format=%cI` (raw) | `2026-08-30T15:58:27+01:00` |
| `TZ=UTC … --date=iso-strict-local` | `2026-08-30T14:58:27Z` ✅ |

**`format-local` is the fix**, and `%cI` is the honest raw form when you want the offset visible.

**This is not hypothetical — the repository already carries a record it broke.**
`plans/20260825_1803-open-decisions.md:367` quotes its own source command as
`--date=format:'%Y%m%d %H:%M UTC'` and records *"both 20260825 13:42"*. Re-measured: `c23359f` is
`2026-08-25T13:42:55+01:00`, so **the true UTC is 12:42**. The number is right for the machine and
the label is wrong, which is the worst of the two failures — a stamp that is an hour out *and*
carries the word `UTC` beside it.

**Found by the coder, who nearly wrote a composed stamp into a handoff on the strength of it, and
checked instead.** The planner promised to record it 20260830 and did not — this section exists
because the promise was kept a day late after the coder asked whether it had landed. **A rule the
project states and a mechanism that defeats it, both in the tree, and nothing gates the difference.**

### Where the neighbourhood audit fails: inside corrections

**`docs/README.md` requires auditing the neighbourhood, not the diff. It has now failed identically
twice, and both times the failing edit was itself a correction.**

| | |
|---|---|
| `7961b89` | fixing a row count in `docs/VERIFICATION.md`'s scope paragraph left the same number standing two paragraphs down. Its own message names the cause: *"this repo's own 'audit the neighbourhood, not the diff' rule failing inside a change that was itself a correction."* |
| **20260830** | the planner corrected a false churn claim in `tools/batteries/README.md` and did not read three lines up, where *"Nine batteries … Seven under `tools/`"* had been wrong since 20260826. Ten and eight. |

**The pattern is not carelessness and a reminder will not fix it.** The coder's sentence for it,
which is the most useful thing anyone said about the day: **the state of mind that produces a careful
fix is the state of mind that is done looking.** A correction arrives with its own sense of
completion — the defect is identified, the edit is precise, the diff is small — and that feeling is
exactly what an audit has to survive.

**The strongest evidence is that the refutation was in hand and filed as housekeeping.** A stale
proposal in an abandoned worktree held `Seven → Eight` for that same sentence — a correction written
on 20260826 that was *already wrong when written*. It was reported as evidence the worktree was safe
to delete. **It was evidence that restating the number is the defect**, and neither session read it
that way until the number was measured. Its author says so plainly rather than letting it pass, and
that is why the fix names `ls tools/batteries/*.toml` instead of writing *Ten*.

**So the practical form of the rule is narrower than "audit the neighbourhood":** *when the edit you
are making is itself a correction, read the surrounding paragraphs before you are finished, because
that is the case where you will not want to.*

### A sixth instance, and the rule's first return

**The refinement was itself fitted to an unexamined population, which is the sixth case.** Its
author built it from the four instances that were *selections* and it therefore missed the fifth,
where nothing was selected and a renderer was simply used — the gap the `or an instrument you chose`
clause closes. **A rule about generalising from an unexamined sample, generalised from an unexamined
sample.** Recorded because it is the cheapest possible demonstration that the failure is structural
rather than careless.

**Then its author applied it to their own report, and it returned something better than an error.**
The whole token analysis is denominated in a cost model — `input ×1.0, cache-write ×1.25, cache-read
×0.1, output ×5.0` — which was stated in a footer without saying which weights were *sourced*.
**The output ratio is** — `prices.toml` carries `claude-opus-5` at `$5.00`/`$25.00` per MTok, so
×5.0 is measured, and the planner re-derived that from the committed file rather than accepting it.
**The two cache multipliers were never verified against anything**; "standard" was doing the work
that evidence should.

So they were bounded rather than defended:

| cost model | context transmission | generation |
|---|---|---|
| as published | 85.3% | 14.7% |
| cheaper reads (0.08) | 83.0% | 16.9% |
| dearer reads (0.125) | 87.3% | 12.6% |
| 1h-TTL write (2.0) | 86.8% | 13.1% |
| dearer output (×10) | 74.4% | 25.6% |
| most hostile (read 0.05, write 1.0) | 76.7% | 23.2% |

**The headline moves between 74.4% and 87.3% and never comes near flipping**, so the *ranking* of
that report's recommendations does not depend on the unverified weights — only their precise sizes
do. **The finding survived; the claim got a boundary.**

**That is the return worth advertising when this rule is proposed.** A rule that only ever finds
errors gets resented and quietly dropped. This one's first application to a *correct* piece of work
converted an unstated assumption into a stated bound, which is what makes it worth the sentence it
costs.

**Attribution, stated because this document is about claims being traceable:** the refinement is the
`optimize-adversarial-review-tokens` session's; the counter-case that killed the 34-of-64 figure was
the coder's, not that session's own insight, and it asked not to be credited for it; the table and
the instrument clause are the planner's. **Nothing in this section has been proposed for `CLAUDE.md`
yet** — that file is 87 lines over its own guideline and has an extraction diff already waiting on
the user, so a new rule goes to them beside it rather than ahead of it.

## Build order

| # | Item | Blocked on | Owner |
|---|---|---|---|
| 1 | ✅ **BUILT 20260830 `b59e58f`.** ~~C — stop the suite reading the wall clock~~, `test_deep_loop.py:153`'s existing `prices()` pattern being the model. **Needs no decision: it restores `DESIGN.md:811`.** **It is not a one-file fix: `test_doctor.py` is 1 of the 25** — see § *What item 1 actually costs* | nothing | coder |
| 2 | ✅ **BUILT 20260830**, `docs/RELEASING.md` § *Before you start* step 3, and first applied in 0.31.0. ~~The release step that refreshes `prices.toml`~~ — it has never existed, so every install refuses paid estimates 30 days after each release. Doc half `docs/RELEASING.md` (planner); the numbers need re-measuring (**user**) | **the user**, for the numbers | planner + user |
| 3 | ✅ **DONE 20260830** — all five fixed and landed. ~~The five confirmed defects above~~ | nothing — but `check.sh` is red until **item 1** (this row used to say item 2, which was wrong: item 2 is the recurrence cure, not the unblock) | planner (all five are planner-owned documents) |
| 4 | ✅ **DONE 20260830** — 14 verified, adversarially refuted, 12 fixed, 1 already fixed, 1 fix killed by its own skeptic. ~~The other 14 unfixed survivors in `SURVIVED.md`~~ | nothing, same caveat | planner |
| 5 | ✅ **DONE 20260831 22:17 UTC — 21 of 22 dispositioned, 4 confirmed, 8 dead locators, 1 still open** (the eight-rows list). Verdicts per finding in § *CHECKED 20260831*, with what each one now owes. ~~A **targeted** verification pass over the never-verified findings — **not** `resumeFromRunId`, which is same-session-only. **30 raises were never verified; deduplicated against the 14 that item 4 covers, 22 distinct items remain**, enumerated in § *The 22 nobody has ever checked*~~ | — | planner |

**The corpus rule does not apply.** Nothing here touches chunking, fusion, reranking or the
confidence signal.
