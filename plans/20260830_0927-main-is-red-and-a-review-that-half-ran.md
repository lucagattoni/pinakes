# `main` is red on the clock, and a review that reported less than it found

**Written 20260830 09:27 UTC against `main` at `3712a7f`.** Two things happened while nobody was
looking, four days apart, and neither is visible from a commit. **This file exists because the only
other record of them was `RESUME.md`, which [`docs/BUILDING.md`](../docs/BUILDING.md) calls *"a
convenience, never a carrier"* — excluded from git, invisible to every other checkout, and unable to
tell anyone it exists.**

> ## 🛑 ONE DECISION IS THE USER'S AND IT BLOCKS EVERYTHING
> `./check.sh` cannot go green until it is taken, so **nothing lands** — not a fix, not the release.
> It is § *The decision* below.

## 1. `main`'s test suite is red, and no commit did it

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

**CI is green on `3712a7f` and that green is a lie of omission** — it is dated **20260826 11:51** and
**nothing has run since**. A re-run today goes red on the `[light,pdf,claude]` leg. The `[light]` leg
should stay green (those tests carry `skipif` guards on the extras), so the next push produces a
green `docs` job beside one green and one red matrix leg. **A green run is a claim about the moment
it ran** — this repository has written that sentence before and had not yet met a case where the
tree did not change at all.

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

**The planner's reading, offered and not taken:** **C, and A on its own merits whenever the numbers
are re-measured.** They are not alternatives — C fixes the suite, A fixes the prices, and B alone
buys 30 days by making the product worse. **But A-then-C and C-then-A differ in what is red in
between, and only the user can say whether a spend-affecting constant may be refreshed without a
re-measurement.** Until this is answered, `./check.sh` is red and nothing lands.

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

### Confirmed by hand on 20260830, and none of them a typo

| Where | Defect |
|---|---|
| `docs/STATUS.md:20`, `:366`, `:1210` | **An unescaped `\|` inside a code span truncates the row on GitHub — and only on GitHub.** Rendered through GitHub's own API, `pnk sync`'s third cell ends at `` `--clear-cache[=paid `` : **`transcripts]` and everything after it is gone**, the code span left unterminated. GFM splits the row on the bare pipe and then **silently drops the overflow to match the header's column count**, so the table still shows three cells and looks intact. **The published mkdocs site renders the same line correctly, in full** — verified in `site/status/index.html`. Same source, two renderers, **one of them losing content in the place this public repo is actually browsed** |
| `docs/BUILDING.md:172` | *"the changelog fragment written in `d9fe1a9` carried 'wrong for twelve hours'"* — **at `d9fe1a9` it does not.** The phrase lived only at `29856b9`; `ef1465a` corrected it *before* the merge. The sha in the sentence is wrong |
| `plans/20260825_1240-run-pinakes-sweep.md:417` | *"the reasoning is also in `src/pinakes/pairing.py`'s docstring"* — `grep -ci cycle src/pinakes/pairing.py` is **0** on `main`. True only on the coder's **unlanded** branch |
| `docs/VERIFICATION.md:787`, `:282` | both citations point at unrelated rows (`:787` an over-long-path row; `:282` an empty-tag/hub row) |
| `plans/20260825_1252-plans-sweep-findings.md:87` (row 11) | **a thirteenth stale row the reconciliation missed** — says D-31/32/33 *"none taken"* and `user-decision` when they were answered 20260825 18:16. `docs/README.md:55` says the opposite about the same item |

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

## Build order

| # | Item | Blocked on | Owner |
|---|---|---|---|
| 1 | **The price-table decision** — A, B or C above | **the user** | user → coder |
| 2 | The remedy it chooses | item 1 | coder (C or B), planner (A's write-up) |
| 3 | The five confirmed defects above | nothing — but `check.sh` is red until item 2 | planner (all five are planner-owned documents) |
| 4 | The other 14 unfixed survivors in `SURVIVED.md` | nothing, same caveat | planner |
| 5 | A **targeted** verification pass over the 30 unverified findings — **not** `resumeFromRunId`, which is same-session-only | items 3-4, so it does not re-raise what is already fixed | planner |

**The corpus rule does not apply.** Nothing here touches chunking, fusion, reranking or the
confidence signal.
