<!-- Preserved verbatim from the coder session's scratchpad, 20260831 21:15 UTC. -->

> ## 📌 Why this file is in `plans/` and not in a scratchpad
>
> **This audit lived only in a session scratchpad and would have died when that session ended** —
> 46 of its 62 findings had no other home. That is the exact failure
> [`20260830_0927-main-is-red-and-a-review-that-half-ran.md`](20260830_0927-main-is-red-and-a-review-that-half-ran.md)
> exists to record, applied to the audit that fixed *that* file's own stale pointers. Copied here
> unchanged rather than summarised, because a summary is a second register.
>
> **The 15 blockers are CLOSED** — 13 by the planner in `6a86482`, 2 by the coder — and each was
> re-verified individually against `6a86482` by the auditor rather than taken on the fixer's word.
> **✅ ALL 62 ARE NOW CLOSED. This file is spent — read it for its record, never as a worklist.**
> The 13 misleading closed 20260831 (`802d40b`); the 33 cosmetic closed 20260901 (`1d90613`).
>
> **What closing the cosmetic 33 actually found, which is the reason to keep this file:** not one of
> its suggested fixes could be pasted — `main` had moved eleven times — so every finding was
> re-measured first. **Eight were already fixed, five had suggestions that had themselves rotted,
> two were moot** (`RESUME.md` is untracked, committed at no sha), and **three of this audit's own
> corrections had rotted again within the day.** No line number was replaced with another line
> number: the fixes cite a `grep`, a `file.py::test_name`, or the sentence itself. **A count that had
> been wrong three times was replaced by the instruction to re-run `wc -l`** — the only form that
> cannot go stale a fourth time.
>
> **Its own stated limit, which is why the number is usable:** *"62 is what survived an adversary
> told to refute, not ground truth; severities are the refuter's correction."* Line numbers are as
> of `2f64128`/`643af9e` and **have shifted** — locate by content.

---

# Stale entry points — confirmed by audit, 20260831

Seven documents audited, each by a reader verifying against the repo, then an **adversarial
pass per document instructed to refute**. 62 confirmed of a larger raised set; the refuters
dropped the rest. Severities are the refuter's correction, not the auditor's claim.

**blocker** = a freshly-cleared session would take a wrong action.

Audit ran against `2f64128`; re-checked by hand against `643af9e` — **15 of 16 blockers still live**,
the exception being the S18 *heading* in the sweep plan (its build-order row 7 is still open).


## `plans/20260830_0927-main-is-red-and-a-review-that-half-ran.md` — 7 blocker, 13 total

### BLOCKER · line 10

> > `./check.sh` cannot go green until it is taken, so **nothing lands** — not a fix, not the release.

CONFIRMED false three ways, and no closure is recorded anywhere in this document. (a) I ran the four files this file names bare: `uv run pytest tests/test_doctor.py tests/test_extract_claude.py tests/test_pdf_trace.py tests/test_cli_ask.py -q` → 249 passed, 1 skipped, 0 failed. CI run 33319511646 on main = success. (b) The fix landed with no user decision: 240e121 'Stop the test suite reading the wall clock against prices.toml', merged b59e58f; tests/conftest.py:128 is an autouse fixture calling the real load_prices() and replacing only as_of. (c) Twelve merges have landed since, including the 0.31.0 release (c7b0bd9), whose wheel and sdist I confirmed on pypi.org/simple/pinakes/ with tag v0.31.0 present. The 🛑 heading is a `##` inside a blockquote, i.e. exactly the un-gated status claim CLAUDE.md says is never gated, and it is the first thing in the file. A planner reading it goes to the user with a question that was settled, built and shipped on 20260830. Note the § at line 92 ('NARROWED … it needs no decision') contradicts this banner but does not mark it, so the banner is the surviving register.

### BLOCKER · line 13

> ## 1. `main`'s test suite is red, and no commit did it

CONFIRMED. The suite is green — measured by me just now, not relayed: 249 passed / 1 skipped / 0 failed across the four files this section itself enumerates. tests/test_doctor.py::test_the_price_table_is_reported_with_its_date now builds `fresh = Prices(as_of=datetime.now(UTC)…, models=current.models)` and monkeypatches doctor_module.load_prices; its docstring records the 20260827 cause. This is a bare `##` heading with no closure marker and no ✅ anywhere in § 1 — the precise failure mode CLAUDE.md records as having put two freshly-cleared coder sessions one message from rebuilding landed work. The section body is dated to 3712a7f, but the repo's own rule is that a heading is never gated by its body.

### BLOCKER · line 528

> | 1 | **C — stop the suite reading the wall clock**, `test_deep_loop.py:153`'s existing `prices()` pattern being the model. **Needs no decision: it restores `DESIGN.md:811`.** **It is not a one-file fix: `test_doctor.py` is 1 of the 25** — see § *What item 1 actually costs* | nothing | coder |

CONFIRMED, and this is the operative register — CLAUDE.md states 'where a dated snapshot and a `## Build order` disagree, the build order wins', so a coder is instructed to trust exactly this row. It is stale: 240e121 (20260830 15:19, merge b59e58f 15:35) built precisely what the row asks, using the pattern the row names, touching tests/conftest.py (+39 autouse fixture at :128), tests/test_budget_core.py and tests/test_doctor.py. The row still reads owner=coder, blocked on nothing, unmarked. A freshly-cleared coder rebuilds a landed increment. NOTE: the auditor cited line 499; the row is now at line 528 — commit 54d6ffc appended 29 lines to this file after the audit ran.

### BLOCKER · line 529

> | 2 | **The release step that refreshes `prices.toml`** — it has never existed, so every install refuses paid estimates 30 days after each release. Doc half `docs/RELEASING.md` (planner); the numbers need re-measuring (**user**) | **the user**, for the numbers | planner + user |

CONFIRMED, both halves. Doc half: docs/RELEASING.md:26 is now step 3, 'Re-verify `src/pinakes/budget/prices.toml` and re-stamp its `as_of`', landed a2cc944 (20260830 10:57), with the window rule at :30, the StalePricesError promise at :37-38 and a do-not-stamp-what-you-cannot-verify warning at :49-52 — I read all of them. Numbers half: src/pinakes/budget/prices.toml:12 now reads `as_of = "20260830 14:46"`, changed in c7b0bd9 (Release 0.31.0), and `git log --follow` on the file is now 8efa044 → 6ebfdf4 → c7b0bd9, so 'written once at creation and never refreshed' no longer holds. 0.31.0 is on PyPI (wheel + sdist verified). This row is the only one in the file marked 'blocked on the user', so it is what sends a planner to the user with a settled, shipped question. Line was 500 at audit time, now 529.

### BLOCKER · line 112

> **What still needs the user is the bigger half.**

CONFIRMED — all three supporting facts in the paragraph are now false, and I checked each. (1) 'as_of was written once, at creation, and never refreshed': prices.toml:12 = `20260830 14:46`, re-stamped in c7b0bd9. (2) '`docs/RELEASING.md` mentions prices zero times': `grep -in price docs/RELEASING.md` returns :26, :30, :37, :38, :49-52. (3) 'the remedy … names a release step that does not exist' and 'It recurs every 30 days until a release step exists': the step exists (a2cc944), and RELEASING.md:37-38 explicitly names keeping the StalePricesError promise. This is a prose assertion of an open user dependency — the costliest wrong action available here is putting a shipped decision back to the user, and this sentence plus build-order row 2 are what would do it.

### BLOCKER · line 530

> | 3 | The five confirmed defects above | nothing — but `check.sh` is red until **item 1** (this row used to say item 2, which was wrong: item 2 is the recurrence cure, not the unblock) | planner (all five are planner-owned documents) |

CONFIRMED on both errors. (a) check.sh is not red — item 1 landed b59e58f and I re-ran the affected files green. (b) Four of five defects are fixed on main, verified by grepping the exact strings: `grep -n 'd9fe1a9\|twelve hours' docs/BUILDING.md` returns nothing (deleted in 04f4deb); plans/20260825_1240-run-pinakes-sweep.md now reads '*Verified 20260830: it is not there yet — grep -ci cycle src/pinakes/pairing.py is 0 on main*' (04f4deb); plans/20260825_1252-plans-sweep-findings.md row 11 has moved to line 90 and now reads 'D-31, D-32 and D-33 were ANSWERED by the user 20260825 18:16' with status 'DECIDED, not built'; and the STATUS.md pipe row already carries 'Fixed 20260830' in its own cell. Only the docs/VERIFICATION.md:787/:282 row is still live (and mis-paired — see the separate verdict). A planner picking up this row re-fixes four fixed documents. Line was 501 at audit time, now 530.

### BLOCKER · line 531

> | 4 | The other 14 unfixed survivors in `SURVIVED.md` | nothing, same caveat | planner |

CONFIRMED. I opened SURVIVED.md at the path this file names and checked every locator against HEAD myself. The 15 rows are 11 distinct findings (2≡13 both 'BUILDING.md 207 of 248'; 3≡7 both 'VERIFICATION.md:876 before the tag, never after'; 5≡10 both the d9fe1a9 anecdote; 9≡14 both the batteries-README churn superlative). Ten of the eleven are gone from the tree: 'these 904 rows' → 0 hits in docs/VERIFICATION.md; '207 of 248' now survives only as a correction record at docs/BUILDING.md:184; 'before the tag, never after' → 0 hits; 'four live items' → 0 hits; the d9fe1a9 anecdote → 0 hits; '20260826 07:01' → 0 hits in plans/20260731_1202; the retro.d/20260826_0702 fragment no longer exists; 'highest-churn' → 0 hits in tools/batteries/README.md; RELEASING.md:108 now reads '**Six** live citations'; sweep-findings row 11 corrected. The single survivor is #11, CLAUDE.md's size — `wc -l CLAUDE.md` = 285 against the ~150-line guideline. Both the count (14) and 'unfixed' are wrong; a planner works a queue that is 10/11 done. Line was 502 at audit time, now 531.

### MISLEADING · line 191

> ### Confirmed by hand on 20260830, and none of them a typo

The heading itself is an accurate dated record — those five WERE confirmed by hand on 20260830 — so the defect is one level down, in the four unmarked rows beneath it, which I verified are fixed (see my verdict on build-order row 3 for the per-row evidence). Only row 1 (docs/STATUS.md) carries 'Fixed 20260830'; the rows at :196, :197 and :199 carry nothing, and :198 (docs/VERIFICATION.md) is the one genuinely still live. This is the two-register pattern CLAUDE.md names. It is not a blocker on its own because the operative queue is § Build order row 3, already rated blocker — but the rows must be marked in the same pass or the fix is half-done.

### MISLEADING · line 296

> `tests/test_doctor.py`'s failing `test_the_price_table_is_reported_with_its_date` asserts

CONFIRMED, and both halves of the prescription are already discharged — I read the file. The test no longer asserts from the real clock: it builds a fresh Prices and monkeypatches doctor_module.load_prices, and its docstring now says 'Neither compares the wall clock against the committed `as_of`, because staleness is deliberately not a CI gate.' The sibling test_a_stale_price_table_warns_and_names_the_setting was corrected in the same change — its docstring now reads 'This docstring used to open "the shipped table is current by construction". It is not, and that assumption is what took the suite red on 20260827', which is exactly what lines 304-307 demand. So 'That premise is now false, in the file the fix lands in' describes work done, not work owed. Rated misleading rather than blocker: this is the rationale section behind build-order row 1, and marking that row BUILT makes this section read as history.

### MISLEADING · line 1

> # `main` is red on the clock, and a review that reported less than it found

CONFIRMED. main is green — I ran the previously failing files (249 passed / 1 skipped / 0 failed) and CI run 33319511646 on main is success. The H1 is an unqualified present-tense status claim and it is the first line of a file both entry points route to. Not a blocker, because both entry points have already been corrected and lead with the closure: CLAUDE.md now opens that bullet '✅ `main` is green and 0.31.0 is published (20260830). The red build, the release and the fourteen document defects are all closed', and docs/README.md:45 says '✅ The incident is closed — read it for what it carries, not for what it was called.' So a cleared session is warned before it opens the file; the H1 then contradicts what it was just told, which is misleading rather than action-forcing. Change the H1 only — the filename is linked from CLAUDE.md:158 and docs/README.md:45 and must not move.

### COSMETIC · line 335

> — until item 1 lands. Afterwards a nightly run cannot go red on staleness, because nothing in the suite reads the clock any more, so the objection dissolves and the schedule becomes safe

CONFIRMED but minor. The clause is a true conditional — it never asserts item 1 is unbuilt — yet its 'until … Afterwards … becomes safe' framing reads as a live precondition, and the condition was discharged on 20260830 by 240e121/b59e58f. The suite no longer reads the wall clock against prices.toml (tests/conftest.py:128), so a scheduled run on main is safe today. Worth a tense change when the file is next touched; nobody takes a wrong action on it, since the row is a what-would-have-caught-it analysis rather than a queue.

### COSMETIC · line 521

> that file is 87 lines over its own guideline

CONFIRMED, and it was wrong when written. `wc -l CLAUDE.md` = 285 today against the ~150-line hygiene guideline = 135 over. At 9c2a91b, the commit that introduced this sentence (`git log -S "87 lines over"`), CLAUDE.md was 287 lines = 137 over. 87 is neither the delta (137) nor the ratio (91% over; SURVIVED.md #11 stated the same file's overage as '84% over' at 276 lines, which is the ratio form). Cosmetic: a wrong number in a parenthetical about why a rule was not yet proposed, taking no action with it. NOTE: the auditor cited line 492; it is now 521 after commit 54d6ffc appended 29 lines. Also note their '287' is stale — 621f5e0 trimmed the file to 285 — so whoever applies this should re-run `wc -l` rather than paste either number.

### COSMETIC · line 198

> | `docs/VERIFICATION.md:787`, `:282` | both citations point at unrelated rows (`:787` an over-long-path row; `:282` an empty-tag/hub row) |

CONFIRMED — the pairing is inverted, and it was inverted at 3712a7f too. On main, docs/VERIFICATION.md:282 is 'an unreadable or over-long path is refused, not a traceback | L6 review 3'; at `git show 3712a7f:docs/VERIFICATION.md | sed -n '282p'` it is the same row. So :282 is the over-long-path row, not the hub row. This matters because it is the one row of the five still live — the citations it flags are real (plans/20260825_1240:468 and plans/20260825_1252:86 cite :282; plans/20260825_0749:618 cites :787), so whoever picks it up works from the wrong pairing. CAUTION on the suggested fix: the auditor's replacement text is also wrong on today's tree. :787 is now 'asking for `authored` without the local KB is refused' — the empty-tag/hub row has drifted to :788. It was :787 at 3712a7f. Re-derive both locators before editing rather than pasting the suggestion.


## `plans/20260825_1240-run-pinakes-sweep.md` — 4 blocker, 16 total

### BLOCKER · line 281

> ### S18 † — a restored paid document is refused forever, and the reason it prints is false

Confirmed at line 281 verbatim, present tense. S18 is fixed and on main: merge 3552064 (20260830 16:19), touching src/pinakes/pairing.py, src/pinakes/sync.py, tests/test_pairing.py, tests/test_sync.py, docs/VERIFICATION.md and tools/batteries/src-pinakes-pairing.toml. I read the landed code: pairing.py:56-57 defines CHANGED/RETIRED, :314-320 splits content_changed from retired, :335 passes reason=CHANGED if content_changed else RETIRED. I grepped the whole document for S18 (lines 10, 281, 283, 490, 506) — no closure is recorded anywhere in it; line 490 only says the row did not exist before an earlier pass. The file's own S17 heading at line 210 uses the '✅ FIXED on `main`' pattern, so this heading is the odd one out in the register a `grep '^### '` sweep reads. Blocker because it, together with build-order row 7, is what a cleared coder would act on.

### BLOCKER · line 283

> Severity **MEDIUM**. STILL OPEN —

Confirmed at line 283 (substring of '**Found by the coder 20260826 while adversarially reviewing S2. Severity **MEDIUM**. STILL OPEN —'). Not open: landed 3552064. The pinning test exists — tests/test_pairing.py gained 40 lines in that commit and docs/VERIFICATION.md gained a row. The auditor is right to separate the two halves: the '20260826 04:40 on main at 325ab9e' re-check is a sound historical measurement and should survive as a dated record, but the STILL OPEN verdict drawn from it is a live status claim and is now false. Blocker — this is the line a reader checks after the heading.

### BLOCKER · line 506

> | 7 | **S18** — a restored paid document is refused forever, and the reason it prints is false | nothing | coder |

Confirmed verbatim at line 506. S18 is built and on main (3552064). This table declares itself the winning register — line 492-493: 'Where this table and the *Actionable* table … disagree, this one wins' — and every other completed row (row 1, S2) carries the '~~struck~~ — **BUILT.** Landed <sha>' form plus a verify-by-opening-the-code instruction. Row 7 has none of it. A cleared coder working the build order would take this row and rebuild a fix already in the tree. Blocker, and the highest-cost of the three S18 cells because it is the queue.

### BLOCKER · line 501

> **Show the cycle case still failing in the commit message** | nothing | coder |

Confirmed at line 501, the tail of build-order row 2. Verified both halves of the auditor's claim. (a) Built: branch 20260826_0712-s16-s19-rename-ordering @ eb54c7f is on origin (git ls-remote), its worktree is live at ~/Code/repos/github_lucagattoni/Pinakes-worktrees/20260826_0712-s16-s19-rename-ordering, and it carries the ordering fix — `_order_for_path_availability` at pairing.py:509, called from :467 — plus +416 lines in tests/test_pairing.py and +44 in tests/test_sync.py (git diff --stat main...HEAD). That symbol is absent from main (grep -c = 0) and the branch is not merged (git branch --merged main does not list it), so this is genuinely unlanded work, not a stale worktree. (b) There is a real outstanding question, documented on the branch in REVIEW-FINDINGS-RECOVERED.md findings 1 and 5 [HIGH]: `_apply`'s `except (PinakesError, OSError, ValueError)` does not catch `sqlite3.IntegrityError`, so a recorded per-document failure inside a reordered chain still escapes as a raw traceback; the note itself says 'Containment is one line: adding sqlite3.IntegrityError to _apply's except tuple would turn both this residue and the deliberately-deferred cycle class into a recorded failure' — i.e. a change to what a cycle *means*, which this repo's own rules make a user decision, not a coder's. Line 420 of the same document does mention the branch in passing ('the text exists only on the unlanded branch'), but only about a missing docstring, 80 lines above the table that declares itself authoritative, and it never says the fix is built. That is not a closure record. Blocker: 'Blocked on: nothing' on the first unbuilt slot sends a cleared coder to rebuild ~600 lines of existing green work and to take the cycle decision themselves.

### MISLEADING · line 121

> It is **live in `0.30.2`**, which is what `pip install pinakes`

Confirmed at line 121. Falsified against the PyPI index itself, not the CHANGELOG: pypi.org/simple/pinakes/ carries pinakes-0.31.0-py3-none-any.whl and pinakes-0.31.0.tar.gz; origin holds refs/tags/v0.31.0 peeling to 37689f13; src/pinakes/__init__.py:7 reads 0.31.0; CHANGELOG.md has '## [0.31.0] — 20260830 14:46'. `pip install pinakes` serves 0.31.0. Correctly *not* a blocker: S16 is still live, so the finding stands and no one debugs a fixed thing — but the sentence would let a reader tell a user 'upgrade past 0.30.2' as if that escaped S16, which it does not. Misleading, as filed.

### MISLEADING · line 187

> > **`20260825_1243-s2-silent-index-loss` is still on `origin`, local and remote both at

Confirmed at line 187, inside the 🧹 box at 185-208. The branch is gone from all three places I checked: `git ls-remote origin` lists only main, 20260826_0712-s16-s19-rename-ordering and 20260830_1415-claudemd-extraction-PROPOSAL; `git branch -a` shows no local or remote-tracking copy; `git worktree list` shows only main's checkout and the S16 worktree. The box's own precondition is discharged — `git grep -c "S2's abandoned first attempt" origin/main -- plans/20260825_1240-run-pinakes-sweep.md` returns 2 — so the task was correctly carried out and only the record of it is missing. Held at misleading rather than raised: the wrong action it induces (running the six-step deletion sequence) is a harmless no-op, so nothing gets rebuilt or debugged; the cost is a false statement of repo state presented as an open task, plus the moment spent wondering whether the record was lost with the branch.

### MISLEADING · line 314

> hash_changed = document.content_hash != file.content_hash or document.state == DELETED

Confirmed at line 314 of the plan, introduced at line 313 by "`src/pinakes/pairing.py`'s same-path branch reads" — present tense, asserted as current code. It is not. pairing.py now reads content_changed = document.content_hash != file.content_hash (:314), retired = document.state == DELETED (:319), hash_changed = content_changed or retired (:320), with reason=CHANGED if content_changed else RETIRED at :335. Not exempt as a historical record: the section it sits in is headed STILL OPEN and the verb is 'reads', so it is a status claim about the tree. Downstream of claims 1-2 — the same reframing to 'as it read before the fix' cures it — and secondary to them, since a coder who greps for the line and finds nothing gets a useful signal rather than a wrong action. Misleading, not blocker.

### MISLEADING · line 319

> `src/pinakes/sync.py`'s refusal message (`grep -n 'but its content changed'`) tells the user it was extracted with the paid backend *"but its content changed."* **It did not.**

Confirmed at line 319, present tense. sync.py:1363-1372 now selects the wording from the reason: 'but its content changed.' if reason == CHANGED, else 'and its content is unchanged, but the document was retired and that extraction's text was discarded with its chunks.' The comment at :1363-1367 names S18 as the cause. So the false claim about the user's own file — the part the sentence is about — is gone; the wording survives only for the case where it is true. Same family as claim 7: a live-tense assertion about code that has changed, cured by the same past-tense reframing, and secondary to the heading and the build-order row. Misleading.

### COSMETIC · line 288

> **`pairing.py:298`** now — the S2 rework moved it four hours later. Find it with

Confirmed at line 288. `grep -n 'hash_changed = ' src/pinakes/pairing.py` returns 320, not 298 — S18's own fix moved it a third time. Genuinely stale, and pointedly so, since the sentence sits immediately above the file's own 'A citation is a measurement' box. Cosmetic and no more: the same sentence hands the reader the working grep, so the remedy is self-correcting and no wrong action follows. The auditor's suggested fix — drop the number, keep the grep — is the right shape and is what the box below already prescribes.

### COSMETIC · line 410

> `tests/test_pairing.py:447 test_a_name_swap_never_retires_an_id_the_same_plan_adopts`

Confirmed at line 410. `grep -n 'def test_a_name_swap_never_retires_an_id_the_same_plan_adopts' tests/test_pairing.py` returns 487, not 447 — consistent with the +40 lines S18's commit added to that file. The test itself exists and the claim made about it (it can only observe what it observes by watching a cyclic plan be applied and fail) is unaffected. Cosmetic: the symbol name resolves, so nothing breaks.

### COSMETIC · line 411

> `tests/test_pairing.py:493 test_a_three_way_rename_cycle_adopts_every_id_and_retires_none`

Confirmed at line 411. `grep -n` returns 533, not 493 — same +40-line shift from S18's commit. Test present, claim about it intact. Cosmetic.

### COSMETIC · line 412

> `tests/test_sync.py:2661 test_a_rename_cycle_that_fails_halfway_never_destroys_a_live_row`

Confirmed at line 412. `grep -n` returns 2698, not 2661 — S18's commit added 37 lines to tests/test_sync.py. Test present, and this is the row carrying the strongest argument in the section (the S2 silent-loss shape), so the symbol is what matters and it resolves. Cosmetic.

### COSMETIC · line 426

> `contextlib.suppress(sqlite3.IntegrityError)` at `tests/test_sync.py:2687`

Confirmed at line 426. The suppress inside that test is now at tests/test_sync.py:2724 (the test opens at 2698); there is a second, unrelated `contextlib.suppress(sqlite3.IntegrityError)` at 2857, so a reader who trusts 2687 and scans nearby could land on the wrong one. The argument the sentence makes is unaffected and still correct: the docstring promises the sync's outcome is not asserted while the body pins the exception type, so a cycle settled by raising anything else fails a test that promised it would not. Cosmetic.

### COSMETIC · line 451

> `docs/MANIFEST.md:307-319` lists ten exclusions and none covers it:

Confirmed at line 451. Counted the table in docs/MANIFEST.md directly: intro at 307, header 309, separator 310, ten rows at 311-320, the last being 'A symlinked sidecar is written through'. So the cited range 307-319 spans intro-plus-nine-rows and is internally inconsistent with its own 'ten'. The count of ten is right and the argument (none of the ten covers a comment on an alias reference) survives — I checked the tenth row too and it does not. Cosmetic. The auditor's fix, citing the § *Bounds on that* heading instead of a range, is the durable form.

### COSMETIC · line 453

> `docs/VERIFICATION.md:282`

Confirmed at line 453 of the plan. docs/VERIFICATION.md:282 is now '| an unreadable or over-long path is refused, not a traceback | L6 review 3 | tests/test_cli_link.py::test_an_unreadable_directory_is_refused_rather_than_crashing |' — a link-command row, not the comments-survive promise. (The auditor's own gloss of what sits at 282 is itself off by two — that text is at 280 — but the substance is right: 282 is not the row claimed.) The row that pins the promise is 347: 'comments survive a rewrite | L5b | tests/test_sidecar.py::test_comments_survive_a_rewrite'; there is also a link-flavoured cousin at 264. Cosmetic, and cite the test name rather than either number.

### COSMETIC · line 462

> was refuted against `MANIFEST.md:314` (*"Indentation follows the writer"*), pinned by

Confirmed at line 462. 'Indentation follows the writer' is the second row of the bounds table, at docs/MANIFEST.md:312. Line 314 is 'What YAML does not carry' — a different bound in the same table, so the citation lands on a real-looking but wrong row, which is worse than a number that resolves to nothing. The point being made (the sibling block-style-reflow finding was correctly killed against this bound, and the finder had cited INVARIANTS.md without following its pointer to the bounds list) is unaffected. Cosmetic.


## `CLAUDE.md` — 2 blocker, 2 total

### BLOCKER · line 167

> - **🛑 Two plans have scheduled work, and it is now all coder work — every decision is taken.**

Still present (now line 165 after the 621f5e0 edit) and still wrong on the two substantive halves. (b) "every decision is taken" is false: origin/20260826_0712-s16-s19-rename-ordering @ eb54c7f is pushed, green (its commit message records "./check.sh green bare on the merged tree, exit 0 -- 2366 passed") and deliberately unlanded — "Still NOT for landing: the HIGH is the user's -- does `sqlite3.IntegrityError` join `_apply`'s except tuple". I read the branch's REVIEW-FINDINGS-RECOVERED.md finding 5 [HIGH] and confirmed the decision is live and recorded nowhere on main (`grep -rn IntegrityError plans/ docs/ CLAUDE.md` finds only S2/S16 history, no ruling). That decision belongs to the sweep plan's build-order row 2, i.e. inside the very work this sentence declares decided. (a) "all coder work" is false: plans/20260830_0927-...md build-order rows 3, 4 and 5 (lines 530-532) are open and marked owner **planner**, and the sweep plan's § *Decided work with an owner and no build order* still carries a planner-owned row (VERIFICATION.md rows for tests/test_review_pass_gate.py — docs/VERIFICATION.md mentions that file only in prose, it has no rows). (c) "two plans" is the weakest of the three — the bullet already links three plans in its own body — so I would not raise the count on its own. Blocker because a cleared coder reads a clean all-clear on decisions and proceeds autonomously past a user decision that is holding a landing.

### BLOCKER · line 197

> **S18 is open.

Still present at line 195, and S18 is fixed on main. Landed 3552064 (branch commit a2f5b86): src/pinakes/pairing.py:166-175 gives PaidExtractionRequired a required `reason` of CHANGED|RETIRED, set at :335; src/pinakes/sync.py:1357-1375 branches the message on it; tests/test_sync.py:1129 test_a_retired_paid_document_restored_unchanged_is_not_told_its_content_changed pins it. The sweep plan's own § S18 heading was corrected on 20260831 (825e49b) to "### S18 ✅ **FIXED on `main`**", so CLAUDE.md is now the last register still saying open. Note the auditor's secondary observation is still accurate and worth passing on: plans/20260825_1240-run-pinakes-sweep.md:521 build-order row 7 STILL reads "| 7 | **S18** ... | nothing | coder |" — the heading was fixed, the queue row was not. Blocker: a coder following either register rebuilds a landed fix, which is exactly the failure the third bullet of this same section warns about.


## `RESUME.md` — 2 blocker, 5 total

### BLOCKER · line 39

> ## What is next, and it is unplanned

Tried to refute and could not. plans/20260825_1240-run-pinakes-sweep.md has a live `## Build order` table (line ~480) with ten rows; only row 1 (S2) is struck as BUILT. Rows 3, 4, 5, 6, 8, 9, 10 all read `blocked on nothing`, owner `coder` (S3, S1, S4, S5-S9, D-36's build, D-37's build, the Low classes), and row 2 is S16 (held on the user). I spot-verified two are genuinely unbuilt on main, not merely unstruck: `grep -n 'threading|check_same_thread' src/pinakes/serve.py` returns nothing and serve.py:109 still holds one shared `_connection: sqlite3.Connection | None` (S3 live); `src/pinakes/template.py:209 _render` calls `Template(...).render()` with no autoescape and no escaping of context values (S4 live). Its § *Decided work with an owner and no build order* carries four more rows. RESUME's body sentence -- "Everything else in `plans/` is closed, answered, deferred or proposed-unscheduled" -- is therefore false, and it contradicts CLAUDE.md's own live status block ("Two plans have scheduled work, and it is now all coder work"). No closure of this is recorded elsewhere in RESUME.md. Blocker: a freshly-cleared session reads this and concludes there is nothing queued -- it would go plan new work or stop, while seven ready coder rows sit unbuilt. One correction to the auditor's note: row 7 (S18) being stale is a defect in the plan, not in RESUME.

### BLOCKER · line 33

> and `tools/batteries/src-pinakes-pairing.toml` are both touched on both sides now, the battery

Confirmed by measurement. `comm -12` over `git diff --name-only b59e58f eb54c7f` and `git diff --name-only b59e58f origin/main` (merge base is b59e58f) yields FIVE files: docs/VERIFICATION.md, tools/batteries/src-pinakes-pairing.toml, src/pinakes/pairing.py, tests/test_pairing.py, tests/test_sync.py. RESUME names only the two documents. The omissions are the code and they are the dangerous half: main's a2f5b86 (S18's fix) is +31/-3 in pairing.py, +40 in test_pairing.py, +37 in test_sync.py; the S16 branch is +144/-1 in the same pairing.py, +416 in test_pairing.py, +44 in test_sync.py. The sentence sits directly after the instruction to "read the merged state of every file both sides touched" and then enumerates two of five, so it reads as the complete list. Blocker: whoever lands this branch follows the enumeration, reads two documents, and ships exactly the clean-but-wrong merge CLAUDE.md's landing rules exist to prevent.

### MISLEADING · line 51

> `tests/test_batteries.py` is a resolvability gate: it reads anchors and `kills` selectors, never

Half-refuted, and the false half survives. The operative clause -- 'nothing turns red when a count moves' -- is accurate: no assertion reads a number out of the README. But 'never prose' is false. `tests/test_batteries.py:241 test_the_committed_batteries_cover_only_tools_and_the_readme_says_so` reads tools/batteries/README.md (line 259, whitespace-normalised), asserts every battery stem not starting `tools-` is named in that prose (lines 265-271, which is why src-pinakes-init and src-pinakes-pairing appear there), and asserts the literal string "starting point, not a coverage claim" is present (line 273). So adding a battery outside tools/, or rewording that phrase, does turn the gate red. The auditor is also right that tools/batteries/README.md carries the same wrong claim ('checks anchors and `kills` selectors, never this prose') -- planner-owned, and wrong the same way. Misleading rather than blocker: it does not cause a rebuild, but a session that trips the gate would be debugging against a false model of what it checks.

### COSMETIC · line 31

> It is 17 behind `main`

Confirmed: `git rev-list --count eb54c7f..origin/main` = 21 (`--first-parent` = 7). 17 is the count against 3552064, two landings ago -- `git rev-list --count eb54c7f..3552064` = 17 exactly. origin/main is 6c90fed by ls-remote, which is the same sha RESUME.md line 3 names, so the document is internally inconsistent. Severity lowered from the auditor's 'misleading' to cosmetic: nothing follows from the magnitude. The next sentence already tells the reader to merge main in and read the merged state, and 17-vs-21 changes no action -- unlike the file list on line 33, which does.

### COSMETIC · line 12

> ## Today closed three things and left one decision

Confirmed by count: the table under the heading carries four ✅ rows (`grep -c '✅'` over lines 12-21 = 4) -- main red on the clock b59e58f, 0.31.0 published, release_order_gate 25fcd44, S18 3552064 -- plus one ⏸ held row. All four are on main per the ground truth and `git log`. A fifth closure, the tools/batteries/README.md denominator (e3895ae), is recorded at line 46 of the same document, so the heading undercounts by one or two depending on whether that one is in scope. Cosmetic: no action turns on the number, and every closure is individually and correctly stated in the rows below.


## `docs/README.md` — 1 blocker, 3 total

### BLOCKER · line 49

> **Its build order is fully built out, and D-31 to D-34 were ANSWERED 20260825 18:16**

Confirmed wrong, and this row was NOT touched by `621f5e0` — the text is verbatim at line 49 today. `plans/20260825_0749-exposure-and-silent-status.md:613-614`: row 5 (D-31/D-32 → the unconditional `doctor` check) and row 6 (D-33's detail line) are un-struck, owner **coder**, "nothing — answered"; row 9 at :617 states "**Layer 3** … is **not built** and is what remains of this row". The code agrees: `grep -n gitignore src/pinakes/doctor.py` returns a single unrelated docstring line at :1287, so no recurring check exists. The same document contradicts itself — line 56 calls the identical item "queued coder work" — and "fully built out" is used at line 51 to mean "nothing in it is waiting". A cleared coder reading the routing table would conclude the exposure plan has no queue and skip three decided, unblocked rows; that is how CLAUDE.md says work ages here.

### MISLEADING · line 32

> As of 20260825 12:40 two files propose work

Three do. `plans/20260830_0927-main-is-red-and-a-review-that-half-ran.md:524-532` has a `## Build order` whose rows 3 (the confirmed defects), 4 (the 14 unfixed `SURVIVED.md` survivors) and 5 (the 22 never-verified findings) are un-struck, all planner-owned — and the README's own line 45 says so ("What is still live in it: 22 findings nobody has ever checked"). So the count at line 32 and the sweep sentence at line 37 ("Every other file below is closed, answered, deferred or proposed-unscheduled") are both falsified by the table row directly beneath them. Not a blocker: the sentence carries its own "As of 20260825 12:40" stamp and the table row immediately corrects it, so a reader is warned rather than misdirected — no one rebuilds anything or debugs a green suite off this. Note the auditor's suggested re-stamp text is itself a fix to write, not a defect I can confirm beyond the count.

### COSMETIC · line 65

> **Five of them**, each carrying the `YYYYMMDD_HHMM-` prefix every plan was renamed to; one is `decisions-` plural

Wrong, but not for the reason given — the auditor's own numbers do not hold. The row's subject is the glob it prints, `<stamp>-decision*.md`, which requires `decision` immediately after the stamp; `20260825_1803-open-decisions.md` does not match it and already has its own row at line 46. Five files match: `20260731_0602-decision-ruamel-yaml`, `20260804_1442-decision-g3-go`, `20260804_1844-decision-parent-child-arity`, `20260805_1313-decisions-init-titles-and-grammar`, `20260811_0720-decisions-gates-and-corrections`. So "five" is defensible and "six" is the auditor's broader `*-decision*` glob. What IS wrong under either reading is the plural count: two of those five begin `decisions-` (three under the auditor's glob), not one. Off by one in a sentence whose only job is to tell you to match the stem — the advice still lands, so cosmetic, not the count-and-plural rewrite proposed.


## `docs/STATUS.md` — 0 blocker, 6 total

### MISLEADING · line 1104

> **Unlike the three releases before it, this one's subject ships in the wheel**

CONFIRMED, and precisely as described. `git show 2209014^:docs/STATUS.md` puts this paragraph at 1102-1107, its own paragraph directly under the 0.30.2 entry (1097-1100) and about 0.30.2's subject — the `check-ignore` diagnostic, `METADATA reporting Version: 0.30.2`. The sweep at 2209014 inserted 0.31.0's entry at 1103 with blank lines at 1101/1102 above and **no blank line below** (verified by printing blank-vs-content for 1100-1112). Lines 1103-1109 therefore render as one paragraph, so 0.31.0's verification entry ends with '78 entries, no `tools/`, `METADATA` reporting `Version: 0.30.2`' — a wheel-version mismatch is exactly the signal this section treats as a failed publish. The sweep's own commit message enumerates five edits and this re-anchoring is not among them, so it was an oversight, not a decision. Not a blocker: the merged paragraph opens by recording that installing 0.31.0 prints 0.31.0, so a reader is self-corrected within the same paragraph and would not go re-publish. The 1111 paragraph is separated by a real blank line at 1110 — it is orphaned by proximity, not merged, so that half of the finding is weaker than the 1104 half.

### MISLEADING · line 52

> The only one now is the `claude-vision`

CONFIRMED. `pnk ask --deep` has been the second paid entry point since 0.24.0, and this document says so twice above the defect: line 31 ('**The one command that reasons, and the second of two that can spend.**') and line 42 ('the **second and final** entry on `.paid-path-allowlist`'), plus line 393 ('It is the last paid entry point, so `.paid-path-allowlist` is complete at two'). The word 'now' is present tense under a heading that reads 'The surface you can use today'. The repo's own precedent settles the severity: line 382 records 0.28.2 as the release cut for this exact sentence class — '**The worst was repeated three times: that only one surface in Pinakes can spend.** `pnk ask --deep` has been the second since 0.24.0' — fixed in GUIDE.md and CLI.md, and that audit did not reach STATUS. A false claim about what can spend money is the class this repo treats most seriously, and unlike claims 4 and 7 the reader's wrong belief here is about money safety rather than a count. Not a blocker: it causes no rebuild and no debugging of a green suite.

### MISLEADING · line 28

> Exits `3` — *no baseline* — on every KB that predates the version archive, which today is all of them

CONFIRMED. `src/pinakes/templates/notes/template.toml:4` is `version = "1.2"` and `_versions/` holds both `1.1` and `1.2`, so a KB stamped `notes@1.1` has an archived baseline and gets a real diff — not exit 3. The repo's own two KBs prove it: `tests/demo-kb/pinakes.toml:4` and `tests/partner-kb/pinakes.toml:4` both read `template = "notes@1.1"`. Only a KB recording `notes@1.0` has no baseline. Lines 136-138 of this same file say so explicitly ('`notes` is now `1.2`, so a KB stamped `notes@1.1` has a real baseline and a real diff'), but they are 108 lines below the defect and the defect is in the capability table a new reader reads first. Precedent is near-identical to the sentence 0.28.2 fixed in CLI.md, recorded at line 382: "'`cannot compare` is what every KB in existence gets', true when written, false since 0.17.0" — that audit fixed CLI.md and left this row. A reader concludes `pnk upgrade` is useless on every KB in existence, which is wrong about a shipped command's usefulness. Not a blocker: no build or debugging action follows.

### COSMETIC · line 1214

> | First upload | 20260728 17:16 UTC · latest 20260825 01:04 UTC (0.30.2) — **this row has now gone stale twice**

CONFIRMED on the facts, downgraded on severity. `git for-each-ref refs/tags/v0.31.0` gives 2026-08-30 15:54:04 +0100 = 14:54 UTC, and line 1103 records `gh release view v0.31.0` non-draft at 14:54:04Z, so 'latest 20260825 01:04 UTC (0.30.2)' is a third lapse and 'gone stale twice' undercounts. The sweep commit 2209014 lists five edits and this row is not one of them, exactly as the row's own text predicts. But the correction sits **one line above it**: row 1213 already lists 0.31.0 and reads 'fifty', and line 3 reads 'Latest release: 0.31.0'. A reader checking whether 0.31.0 published hits the gated row first and cannot be durably misled; no action follows from the stale cell. This is a one-cell refresh, not a claim that would misdirect a session, so 'misleading' overstates it.

### COSMETIC · line 66

> names every module permitted to import a paid client — one line since I7b — and four gates in

CONFIRMED on the count, downgraded on severity. `.paid-path-allowlist` holds two non-comment lines — `src/pinakes/extract/claude.py` and `src/pinakes/deep/client.py` — and the file's own header comment says 'E3 adds the second line the same way'. So 'one line since I7b' is stale. But it sits inside a callout explicitly scoped to one release ('⚠️ **0.3.0 is the first release that can spend money**' … 'Absent any one of those, 0.3.0 behaves exactly like 0.2.2'), where it was true as written, and the same document states the right number three times: line 42 ('the **second and final** entry on `.paid-path-allowlist`'), line 393 ('`.paid-path-allowlist` is complete at two'), and the allowlist file itself. Line 42 is 24 lines above the defect, inside the table a reader scans first. Nothing about the gate's behaviour, the spend surface or any build decision changes on this parenthetical, so it is a wording fix, not a misleading status claim.

### COSMETIC · line 41

> | Budget estimator, caps, window aggregation | shipped 0.2.2, **inert** | I6a. The pure logic only — nothing calls it, so nothing can spend |

CONFIRMED on the facts, downgraded on severity. I6a's logic is live: `estimate_document` is called at `src/pinakes/extract/claude.py:645` (the paid extractor itself) and `src/pinakes/sync.py:965`; `budget/accountant.py:38` imports `aggregate` and `WindowTotals` and its `decide()` calls `reserve()` at :111; `deep/estimate.py:48` imports `MAX_INPUT_TOKENS` and `assert_prices_fresh`; `doctor.py:33` imports `in_window`. `accountant.py`'s own docstring line 3 says it outright: 'I6a shipped `reserve()` and `aggregate()` as pure functions with nothing feeding them. This is what [feeds them].' So 'nothing calls it, so nothing can spend' is false today. Two things hold the severity down. The Notes column of this table is increment-indexed — every cell opens with an increment id (I6a, I6b, I7b, I8, T6) and records what that increment delivered, so 'shipped 0.2.2, inert' reads defensibly as I6a's state at 0.2.2. And the closure is in the **adjacent** row (line 44: 'I6a's decisions read from it — now driven by I7b's extractor') with the ⚠️ block eight lines below adding 'every call reserved before it is made and reconciled from the response's own usage'. A reader is corrected within three lines and no build action follows, so this is a wording refresh rather than a misleading claim.


## `plans/20260825_1252-plans-sweep-findings.md` — 0 blocker, 17 total

### MISLEADING · line 84

> | **LIVE** | nothing — D-35 answered, explicitly unblocked | **coder** |

Confirmed the cell is stale, but not a blocker. Layer 2 IS built: tools/status_header_gate.py:87 imports from release_order_gate, :102 defines HOLD, :137 defines _check_hold_marker ("Layer 2"), :250 calls it; the exposure plan's build order row 9 (plans/20260825_0749-exposure-and-silent-status.md:617) reads "LAYER 2 BUILT 20260826, landed 6a77f3c ... Layer 3 ... is not built". So row 5's status cell no longer describes the tree. Severity downgraded from blocker because the document pre-empts exactly this wrong action three ways: (1) the blockquote immediately above the table reads "🛑 This table is a dated snapshot. A ## Build order is the queue" and "Where this table and a build order disagree, the build order wins"; (2) row 20 of this same table (line 99) records layer 2's landing commit 6a77f3c explicitly — closure recorded elsewhere in the same document; (3) the sweep plan's own build order says "Where this table and the Actionable table in 20260825_1252-plans-sweep-findings.md disagree, this one wins. That one is a dated snapshot, not a queue." A coder following the file's stated routing reaches the build order, which says layer 2 is built.

### COSMETIC · line 37

> fifteen defects found by *running* Pinakes (three high, none found by reading)

Confirmed. plans/20260825_1240-run-pinakes-sweep.md:3-14 now opens "This title deliberately carries no count ... Do not quote a total from here, and do not add one", and states thirteen numbered findings (S1-S9, S16-S19). Its ## High/## Medium/## Low headings are bare (lines 44/134/452 — verified). CLAUDE.md repeats the ban. Mitigations that cut the severity: the sentence sits inside a dated headline paragraph ("main is now c23359f, not c2c69cb") that is stale by construction, and it faithfully quoted the sweep plan's own title as of 20260825. No action turns on the number — the actionable content is the row list. Cosmetic, not misleading.

### COSMETIC · line 639

> which on 20260825 produced fifteen defects in one afternoon

Confirmed at line 639, same retracted total as line 37 (sweep plan lines 3-14 withdraw "fifteen" and forbid quoting a total; countable figure is thirteen numbered plus uncounted Low classes). The sentence is evidence for a lesson ("An empty list is not nothing to do"), and the lesson is unaffected by the count. Cosmetic, as the auditor rated it.

### COSMETIC · line 574

> `docs/README.md:58` is stale and it is an entry point a freshly-cleared session reads first: it says the docs-audit plan holds '**39 open documentation corrections**' and '**One is fixed**'.

Confirmed fixed. grep -n "39 open documentation corrections" docs/README.md returns nothing; git log -S on that string returns 5ba4aac, the very commit that wrote this findings file. The docs-audit row is now docs/README.md:62 and reads "This row deliberately states no count. It said 39 open, one fixed, which went stale". :58 is now the template-release row. The bullet's tail does still hold — line 62 still ends "defers a full review of docs/ROADMAP.md until after T2 ... and still owed". Cosmetic rather than misleading: a planner opening the row sees it is already corrected and the surviving half (the ROADMAP review) is on the same line.

### COSMETIC · line 576

> `plans/20260805_1721-metadata-as-retrieval-context.md:950` states '`plans/20260731_1202-open-corrections.md` has been empty since 20260805 22:18'. Verified false:

Confirmed fixed. Line 950 now reads "was empty at 20260805 22:18 and is not today — under its ## Live heading it carries one live item and one closed in place (checked 20260825)". The §7 heading (line 935) also gained "· stale 20260825 — the measurement below is 0.14.0's, and open-corrections.md is not empty", which discharges the bullet's last sentence too. Note the corrected line is itself now under-counting (the Live heading says three live as of 20260826 07:02), so a residual nit survives — but the bullet as written no longer reproduces. Cosmetic: a planner checking it finds the correction already applied.

### COSMETIC · line 585

> Outside `plans/`: `docs/CLI.md`'s `pnk templates` example output still prints 'notes 1.1' six lines above a `--json` paragraph that correctly says 'notes@1.2'; and `docs/ROADMAP.md:2500-2503` still says 'the last step is still the user's own edit, and will be until the next template bump' — that bum

Confirmed fixed, both halves. docs/CLI.md:89 now prints "notes 1.2". docs/ROADMAP.md:2598 now reads "...so for such a KB the last step is still the user's own edit. That is no longer every KB: the archive has shipped notes@1.1 since 0.17.0 and notes@1.2 since 0.24.0...", and the cited range 2500-2503 holds different text entirely. Cosmetic: nothing is written wrong by acting on it; the check is cheap and self-terminating.

### COSMETIC · line 586

> `docs/KB-UPDATES.md` §9's cost table leaves '`pnk upgrade` + `--apply` + `tomlkit`' unstruck and closes 'The remaining two … Neither is assigned'.

Confirmed fixed. docs/KB-UPDATES.md:255 now reads "| ~~`pnk upgrade` + `--apply` + `tomlkit` (§5)~~ | medium | Built (0.19.0 print, 0.20.0 `--apply`) — and without `tomlkit`." — struck. The closing prose (:264-269) reads "Every row in this table is now built, and the sentence that stood here — 'the remaining two would close the live gap in §3, neither is assigned' — was wrong twice over". No unstruck row, no 'two' sentence. Cosmetic.

### COSMETIC · line 587

> `plans/20260801_0102-links-and-graph-log.md`'s 20260731 20:43 row points at 'open-corrections item 9'. That file has no numbering — `grep -n 'item 9'` returns nothing. The pointer cannot be followed.

Confirmed fixed. Line 39 of that file now reads "...the open-corrections item for resolve_path's return shape is CLOSED, do not apply (it was written here as \"item 9\"; that file has never carried numbers, so the pointer could not be followed — corrected 20260825 13:12)". grep -n 'item 9' now returns line 39, so even the bullet's stated evidence check no longer reproduces. Cosmetic.

### COSMETIC · line 582

> `plans/20260804_1016-staged-channel-gates.md` asserts in its header that 'Citations re-confirmed at `d06ef7e` … all four `STATUS` line numbers here still resolve'. That sentence is now false

Confirmed half-stale. plans/20260804_1016-staged-channel-gates.md:49 now reads "⚠️ Citations were re-confirmed at d06ef7e, 20260804 09:25 — and have since rotted. Verified 20260825 13:12: every docs/STATUS.md line number in this file is wrong." grep -n 'still resolve' across both files returns only plans/20260804_1016-graph-remainder-reentry.md:45 — so the sentence survives in the reentry copy alone, exactly as the auditor says. The bullet's second half (the reentry copy at :44) still holds verbatim, so the correction remains actionable; only its primary attribution is stale. Cosmetic.

### COSMETIC · line 589

> `plans/20260804_1442-decision-g3-go.md` is absent from `docs/README.md`'s routing table while both its sibling decision records have rows. The G3 go/no-go decision is reachable only from links inside other plans.

Confirmed fixed. docs/README.md:64 carries the row: "The G3 go/no-go, taken 20260804 — and it had no row here until 20260825, so it was reachable only from links inside other plans. Closed: ...". The row even records its own history. Cosmetic.

### COSMETIC · line 577

> `plans/20260731_1202-open-corrections.md:37` reads '**None live.**' while the file holds one genuinely live item. The routing table (`docs/README.md`) says 'One live item' and is right — so the file an implementer opens is the one that is wrong.

The head of the bullet reproduces exactly — plans/20260731_1202-open-corrections.md:37 still begins "**None live. Four were live at 0.21.1..." — so the finding itself is still live and correct in substance. Both counts in it have gone stale: that file's own ## Live heading (line 67) reads "three items live as of 20260826 07:02 UTC, two CLOSED", and docs/README.md:56 now reads "Three live items.", not 'One live item'. Cosmetic rather than misleading: the actionable core (line 37 says None live and is wrong) is unaffected, and the obvious fix — point line 37 at the ## Live section instead of restating any count — is what a planner would do anyway.

### COSMETIC · line 92

> Verified still wrong: `store.py:205` at KB-UPDATES.md lines 37 and 78, `doctor.py:205` at 63, `sidecar.py:35,106` at 76, `_toml.py:184` at 77.

Confirmed, addresses only. grep -n on docs/KB-UPDATES.md gives store.py:205 at lines 37 and 82, doctor.py:205 at 63, sidecar.py:35,106 at 80, _toml.py:184 at 81; lines 76-78 today are §4 prose, a blank and a table header. The substance holds — the four citations are still rotted: store.py:205 is inside create(), _check_schema_version is at :250; doctor.py:205 is inside a sqlite-vec message, _template is at :238; _toml.py:184 is table(), the unknown-key raise is at :213. Present tense, in the live actionable table, so it is a real (cosmetic) staleness — locate by string, not by line.

### COSMETIC · line 104

> `docs/ROADMAP.md:2410` says so explicitly

Confirmed. grep -n 'There is deliberately no' docs/ROADMAP.md returns 2506; line 2410 is inside the graph-release entry about schema_version 3 forcing a rebuild. The substantive claim (ROADMAP names no plan, increment or number for the staged work) still holds at :2506-2507. Cosmetic, and further softened by the row's own status — row 25 is '✅ RULED 20260825 18:41', owner '—', so nobody is queued to follow the pointer.

### COSMETIC · line 105

> `docs/ROADMAP.md:2400` already records that G5's result licenses neither PPR nor `[ner]`.

Confirmed. The sentence 'G5's result licenses neither PPR nor the [ner] extra' is at docs/ROADMAP.md:2495-2496 (§ 'A different channel design'); line 2400 reads '...did not pass. expand defaults off...'. The rest of row 26 checks out unchanged, so only the address is wrong. Cosmetic.

### COSMETIC · line 85

> *Medium — six (S5, S6, S7, S8, S9)*

Confirmed. plans/20260825_1240-run-pinakes-sweep.md:134 is a bare '## Medium'; its header (lines 3-14) retracts every section count and forbids quoting a total. The row's own body says 'Five accept-then-mishandle defects', contradicting the six in the same cell. This is a navigational pointer in a live row, still findable, so cosmetic — the auditor's rating is right.

### COSMETIC · line 100

> *Low — five*

Confirmed. plans/20260825_1240-run-pinakes-sweep.md:452 is a bare '## Low', and its build-order row 10 reads "The Low section's findings (four classes; the count of five is retracted in this file's header)". The body names exactly four classes — symlink loop, -k 0, --source-type, confidence_reason — which is what this row itself lists. The row's BLOCKED status and 'behind S1-S9' reason still hold. Cosmetic.

### COSMETIC · line 584

> `docs/README.md:51` has the corrected total, ten

Confirmed, line number only. The template-release row carrying "ten of the plan's own measurements or specs have been wrong" is at docs/README.md:58; :51 is the deep-release row. The claim itself holds, and the rest of the bullet reproduces — src/pinakes/templates/notes/pinakes.toml.j2:49 still stamps per_operation_eur = 2.00. Cosmetic.
