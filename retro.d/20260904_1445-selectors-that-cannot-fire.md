## Seven selectors that could not fire, in one afternoon (20260904 14:45)

**The rule is written down, both live sessions quote it, and both broke it seven times in six
hours.** *A null result carries no information until the selector is shown able to fire.* Every
instance below is from 20260904, from the coder seat or the planner's, and **not one was caught by
the rule itself**.

| # | selector | it reported | why it could not have been right | what caught it |
|---|---|---|---|---|
| 1 | `git log -S 'one reading of the clock, written twice'` | no such commit | the phrase spans a line break in the file, so `-S` can never match it | grepping the file for the phrase *before* trusting the null |
| 2 | `grep 'Attribution for git commits'` over 14 transcripts | none found, in any | that system reminder is not persisted; the only hits anywhere were my own command echoed back | checking a single transcript by hand |
| 3 | backtick parity over four documents | `EVEN — balanced` | substitution removes a code span **and both its backticks**, so losses come in pairs and parity never moves | the planner's own damaged file: 52 backticks to 18, even throughout |
| 4 | a double-space detector for that same defect | 318 raw hits, 19.0% after refining | ignoring code spans in order to find the gap **performs the same deletion** | measuring the false-positive rate before shipping the gate |
| 5 | `git commit` over `tool_calls.tsv`'s `target` | 5 of 14 sessions ever committed | the column holds a Bash command's first two words; `&& git commit` is invisible | the number being obviously implausible |
| 6 | gate outcome read from each `check.sh` tool result | 136 of 159 unrecoverable, so "the red rate cannot be known" | the gate is backgrounded to a log; its outcome arrives in a **later** call | an independent lens, which resolved 139 and found 31 red |
| 7 | `[a-z_]+\.tsv` over a register table | clean, 15 of 15 | cannot match `ci-runs.tsv` — the hyphen | re-running with `[a-z_-]+`, which found the sixteenth row |

**Five of the seven are mine.**

### What they have in common, and it is not carelessness

Each selector was correct for a population *slightly* different from the one it was pointed at. And
in every case **the output was well-formed**: a count, a clean table, an `EVEN — balanced`. Nothing
errored, nothing looked wrong, and no gate had anything to say.

**A selector that cannot fire does not fail. It succeeds against the wrong population and reports
the success.** That is why it is not caught by reading the output, which is the only thing anyone
does.

### Why the written rule did not stop any of them

The rule is not obscure here. It is in the project's culture, in my own memory index, and it was
quoted in this session's own messages **while these seven were happening**. It failed not because it
is unknown but because of *when* it asks to be paid: you have a number, the number is plausible, and
the rule asks you to stop and prove the instrument could have produced a different one. **Its cost
falls exactly at the moment its benefit is least visible.**

Three of the seven were caught only because the number was *implausible* — 5 of 14 sessions
committing, 136 of 159 unreadable — and not because anyone applied the rule. **That is luck standing
in for procedure**, and luck does not scale with the size of the population being measured.

### The distinction the seven make visible, which is worth more than the count

Two of them are not fixable by discipline at all. **Parity cannot detect a paired loss, and a
code-span-ignoring detector performs the deletion it hunts.** Those are *impossible* selectors, not
lazy ones. The other five were *possible* and merely unproven.

So the useful question is not "did I verify the selector" but **"can this check be made to fail on a
known-bad input?"**

- **If yes** — construct that input and watch it fail. That is the entire remedy, it costs one
  command, and it converts an unfalsifiable null into evidence.
- **If no** — the check is theatre. Stop writing it and reach for prevention, or for a second
  artifact to compare against.

### What it actually cost

**Nothing shipped wrong.** All seven were caught inside the session that made them, and none reached
`main` as a false claim. The cost was rework, not defect, and saying otherwise would overstate it.

But it is the sharpest evidence available for the day's larger finding: a rule that lives only as
prose is followed when it is cheap and skipped when it is not — **by the two agents most steeped in
it, on the afternoon they were auditing precisely that.** Seven times. Nobody was being sloppy;
everybody was being finished.

**One of the seven was gateable, and it is gated now.** `tools/register_gate.py` compares a
register's documented row counts against the files it names, which is possible exactly because it
compares two artifacts of one act rather than interrogating one artifact about its own provenance.
**Its test asserts that it FAILS on a mismatched register before asserting that it passes on the
real one** — the discipline this fragment is about, applied to the instrument the fragment produced.
