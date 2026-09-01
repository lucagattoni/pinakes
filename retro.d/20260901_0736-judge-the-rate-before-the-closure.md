## Build the instrument that can call a fan-out wrong before you read what it found (20260901 07:36)

A fan-out re-measured 34 open documentation findings and proposed **2** closures. I could not have
judged those 2 from their own text — every closure arrives with a named commit and a passing grep,
which is exactly what a wrong closure also looks like. So before reading any of them I measured
something the fan-out could not influence: **how much each audited file had changed since the
audit's own baseline.**

| File | Commits since `c45ffa8` | Findings | Closed |
|---|---|---|---|
| `docs/VERIFICATION.md` | **42** | 2 | **2** |
| `docs/CLI.md` · `docs/KB-UPDATES.md` | 4 | 9 · 4 | 0 |
| `docs/GUIDE.md` · `docs/DESIGN.md` | 2 · 1 | 5 · 6 | 0 |
| `MANIFEST` · `MEASUREMENT-RUN` · both `README`s | **0** | 9 | **0** |

**Both closures landed in the single most-churned file, and every byte-identical file closed
nothing.** A prior built before the verdict, from git rather than from the findings, turned two
unfalsifiable claims into two predicted ones. Had a closure come back for `docs/MANIFEST.md` —
**0 commits, byte-identical** — it would have had to explain how a document nobody edited stopped
being wrong, and no per-finding judge could have asked that: each sees one finding, and the rate is
the thing no single finding contains.

**The cheap general form:** when delegated work returns a verdict you cannot check directly, find a
*second* measurement of the same population that the delegates did not produce, and check the two
against each other. Here it cost one `git log --oneline <range> -- <file> | wc -l` per file.

---

**Three smaller things, all self-inflicted, all caught by measuring.**

- **35 findings, 35 refuter agreements, zero disagreement — and it was fine.** My own rule from an
  hour earlier says a suspiciously clean result is a reason to check the harness. I checked. The
  refuters had run 263 commands between them and their reasoning showed independent re-reproduction.
  **The uniformity was real agreement, which is what the rule is for: it says *check*, not
  *disbelieve*.** A clean result that survives the check is stronger than one nobody questioned.
- **My check for "did the refuters do any work?" returned zero, and the zero was mine.** I summed
  the length of each verdict's `evidence` field; the schema names that field `why`. Every length was
  0 and I was one inference from reporting a rubber-stamp harness. What caught it was printing the
  key list beside the values in the same command. **This is the null-selector rule, hit within the
  hour by the agent that had just written it down** — and the operational half held: printing the
  keys is the `ls` before the grep.
- **`make docs 2>&1 | tail -15` then `echo $?` reads `tail`. Twice in one session.** The repo's
  own rule says run a gate bare. Both times the real status happened to be 0, so nothing broke and
  nothing would have told me if it had. **A gate misread as green is indistinguishable from a gate
  that is green** — which is the entire reason the rule exists, and no reason at all to relax it.

---

**A number can be wrong in two places for weeks while three routes to it all agree.** This audit
recorded `39` findings in a heading and a table cell. Counting says **40**, and so do the
`# Medium — 13` / `# Low — 27` dividers, and so does 34 open + 6 closed. A correction filed
20260825 had already reasoned it out — *"the 34 is right and the 39 is wrong"* — and the two cells
still said 39 today, because the correction was filed in a third register and nothing read it back.
**Filing a correction is not making one**, and the register that receives a correction is the least
likely place anyone will look for it.

**The rule that falls out is narrower than "remove counts", and a peer sharpened it while this was
being written.** Landing beside me, it checked its own new rows in the same file against my decision
and found they were exempt — every digit in them belonged to *one dated measurement* rather than to
the tree:

> **A count of what is in the tree today decays silently; a dated measurement of something that
> happened once does not, because the tree changing cannot make it false.** Take out the first kind.
> The second kind is why a record can carry numbers at all.

That distinction is the difference between `test_eval.py carries 32 rows` — false within weeks of
being written, twice — and *three headings out by 1 minute, 2 minutes and 3 hours 30 minutes on
20260826*, which will be true forever. **Both are numbers in a document; only one of them is a
claim about now.**
