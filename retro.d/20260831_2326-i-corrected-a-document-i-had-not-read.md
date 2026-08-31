## I corrected a document I had not read (20260831 23:26)

- **The first version of this fragment was the defect it now records.** It opened by quoting *"the
  queued row"* as calling this *"a probe silently measuring a question set a rebuild overwrote"*,
  and spent its lead bullet correcting that framing as a size too big. **No plan has ever contained
  that sentence.** `git log --all -S"silently measuring"` returns exactly one commit — the one that
  added the fragment. The row (`plans/20260825_1240-run-pinakes-sweep.md:579`) says the probe
  hardcodes its questions path *"with no way past it"*, which is precisely the framing I claimed it
  lacked. The runbook (`plans/20260803_2239-corpus-probe-run.md:34`) does say *"silently"* — about
  the file being clobbered by the next build, where the silent party is `build_rfc_corpus.py`,
  which overwrites unconditionally and tells no one. **My sentence compressed two documents and
  moved the adverb from the writer onto the reader.** The original text is in `1d5e7ac` and stays
  there; a retraction whose original has been deleted is a claim nobody can check.
- **It came from my own session's handoff table.** The previous coder session's handover, pasted in
  at my start, summarised the row as *"stops a probe silently measuring a question set a rebuild
  overwrote"* — one cell in a three-row table. I read a paraphrase as a quotation, corrected a
  document for it, and put that correction into a retrospective, a commit message and a message to
  the planner **before opening `plans/`**. A handoff table is a lossy summary of a document, and
  the session receiving it cannot tell a paraphrase in one from a citation. The cheap defence is a
  `file:line` in the handoff instead of a summary; the reliable one is opening the file.
- **The ownership rule is what kept it out of `plans/`.** Documents here have one owner, so the
  correction could only be *proposed*. It landed in the two places an implementer writes for itself
  — a fragment and a commit message — and nowhere else. That is the mechanism working, and it is
  worth saying because the rule usually reads as friction.
- **What was actually true, verified rather than asserted:** the probe has recorded the golden
  set's resolved path, `sha256`, question count and multi-hop count in *both* output formats since
  `a6a931b` (20260804 04:13 UTC), three days before the runbook warning and 27 days before the row.
  So nothing was ever misreported, and the row's own scoping — no route to re-measure a replaced
  set — was right all along. Three lines, no guard.
- **Two reviewers found it; neither found the half that mattered.** Both raised it as a fabricated
  quotation, which it is. Going to the row myself, instead of accepting a confirmed verdict, is
  what turned up that **the correction was also substantively wrong** — there was no oversized
  framing to walk back. An adversarial pass that agrees with you about *what* is wrong can still be
  a level short on *why*, and a confirmed finding is a place to start reading, not a conclusion.
- **The same shape twice in ninety minutes, on a denominator this time.** Arguing against gating a
  fragment's heading stamp, I measured *14 of 100* retro fragments whose stamp is not a copy of the
  filename's prefix. The rule is undefined on the sixteen fragments that predate the naming
  convention, so the population is **85, not 101**; the numerator was right and reproduced
  independently, and only the denominator was borrowed. **A ratio is a claim about its
  denominator.** Recounted on the population the rule actually covers, **18 of 85 were wrong at the
  moment they were committed** — which is an argument *for* the gate I had just argued against.
