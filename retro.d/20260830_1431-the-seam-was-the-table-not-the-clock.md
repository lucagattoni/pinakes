## Unblocking the clock-red suite: the seam was the table, not the clock (20260830 14:31)

**MEDIUM — a true observation pointed at a fix that would have reached none of the failures.**
The impurity was real and was enumerated correctly: four unconditional `datetime.now(UTC)` reads in
callers (`cli.py:874`, `cli.py:1259`, `extract/claude.py:649`, `doctor.py:1586`), against one
existing seam at `cli.py:667`. The inference — *so add seams to the other three* — did not follow.
`tests/test_cli_ask.py` drives real `main([...])`, so there is no `now` to inject, and seaming all
three would have made **zero** of its 18 failures reachable. Every clause was true; the population
the argument was about, *the failing tests*, had never been examined. The seam that works is the
**price table**, which the repository already did twice
(`tests/test_deep_loop.py`, `tests/test_extract_claude.py`) without either helper being noticed by
the pass that enumerated the clock reads.

**MEDIUM — the fix is a fake, so the honest version fakes exactly one field.** An autouse fixture
that returned a synthetic price table would have taken the committed `prices.toml` out of the
suite's reach entirely. Calling the real `load_prices()` and replacing only `as_of` leaves every
model price, the FX rate and the parse of the committed file on the real path: a defect in any of
them still fails the same tests. The remaining unreachable inch was named before it was accepted —
and then **measured**, not argued: with `as_of = "28 July 2026"` committed, the suite is still red
in 7 places. Nothing was lost from the catch. What was lost was the *sentence*, since all seven are
subprocess gates that report a free-path failure rather than an unparsable timestamp, so
`test_prices_are_installed_package_data` — which already asserts the format of every other field in
that file — now parses `as_of` too.

**MEDIUM — a review finding is a hypothesis until a control runs, and two of mine died there.**
The adversarial pass over this fix raised two gaps: no test pins the CLI refusal on a stale table,
and nothing notices a malformed committed `as_of`. Both were plausible, self-consistent and
directly implied by the change. **Both were wrong on inspection.**
`test_cli_ask.py::test_a_price_it_cannot_compute_leaves_the_free_command_working` already pins both
halves of the refusal and its docstring already says a stale table takes that branch; the malformed
case is caught seven ways. Written up unchecked, the pass would have added a duplicate test and a
`docs/VERIFICATION.md` row for a promise already rowed. **The review's output was one line, and its
value was the two things it stopped.**

**LOW — "the fix is green" is three claims when CI is a three-leg matrix.** Fail-fast names whichever
leg loses the race, so a run summary reports one leg and hides two. Each leg was run separately
rather than inferred: `[light]` 2234 passed / 126 skipped, `[light,pdf]` 2352 / 8,
`[light,pdf,claude]` 2356 / 4 — and the six tests that only the extras can reach are exactly the
six a `[light]`-only checkout skips, which is why two sessions counted 19 and 25 all morning
without either being wrong.

**And the defect's own cause was sitting in the file the fix lands in, written as an assumption.**
`test_a_stale_price_table_warns_and_names_the_setting`'s docstring opened *"the shipped table is
current by construction"* — one function below the test that failed because it is not. The
correction lands in the same change, or the fix leaves the premise that produced the defect
in place. **A docstring is a claim with a shelf life and nothing checks it.**
