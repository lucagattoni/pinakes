## A population that could not have contained the thing I was looking for (20260831 22:59)

- **I reported a zero from a population that structurally could not contain a non-zero.** The claim
  was that `claude-fable-5` — which bills at exactly 2.00× `claude-opus-5` — had never been used by
  a fan-out: *"subagent runs: 0; workflow agents: 0 of 868"*. It reached a planner, and it is on
  `origin/main` in `plans/20260831_2242-agent-spend-two-findings.md` as **"an unguarded path, not a
  realised cost."** It is false. Measured with the committed script: **316 fable-5 requests in
  workflow agents and 235 in subagents**, all projects — **551 of 866, or 63.6%**, across 26
  distinct transcripts dated 20260803 and 20260821. The reason I saw zero is that I was counting a
  **main-loop-only** population: subagent transcripts live under `<session>/subagents/` and were
  never in the file list. The query was sound, the domain was never named, and the answer was
  exactly the shape that made it look confirmed.
- **The same session had just written that rule down for someone else.** The document this error
  landed in exists to record that a claim resting on a selected population must state the selector.
  I supplied the zeros for it. **A rule you are enforcing on a peer is not a rule you have applied
  to yourself**, and the direction of the failure — a zero, which reads as *nothing to worry about*
  — is the direction that gets no scrutiny.
- **Committing the script is what found it.** The figures were re-derived by the tool rather than
  recalled, and the fan-out numbers appeared the moment `include_subagents` was a parameter someone
  had to pass rather than an assumption nobody had written down. Two other reported figures did not
  survive the same treatment: the cache-re-write counts (`135 events`, `43,946,201 excess units`)
  reproduce at **no** cutoff time under any population tried — the nearest is Pinakes main-loop,
  which now gives 149 and 45.1M. Those never reached a document; the fable zeros did.
- **Before trusting a cross-file total, test the overlap.** Main-loop and subagent transcripts share
  **0** request ids of 20,156 and 23,685, so the combined totals are sound rather than
  double-counted. That check cost one query and was the difference between a reportable number and
  a plausible one.
- **The fix is a default, not a caveat.** The tool as first landed hardcoded its file list per
  subcommand, so the main-loop-only dollar share a document needs to cite was not reachable by any
  flag — the committed instrument could not reproduce the number the committed document quotes,
  which is the whole failure it was built to end. `--scope {all,main}` now selects it, **defaulting
  to `all`**, and every subcommand prints the population it read. The direction of the default is
  the lesson: the restricted population is the one that must be asked for by name, because a
  restricted list does not announce itself — it just returns a zero.
- **Then I did it again, in the sentence correcting it.** The retraction said the fan-out requests
  sat "across 26 transcripts dated 20260803 and 20260821". The 26 is right — its selector is *all
  projects, subagent and workflow transcripts only, matched on `message.model`*. **The dates are
  wrong.** I printed the first six rows of a 26-row list and read the span off the part I could
  see; the real span is three days, **20260709 · 20260803 · 20260821**. A truncated listing is a
  selected population wearing different clothes, and it went into a commit message.
- **A count is not a measurement until its selector is stated, and the selector fails in both
  directions.** A peer scanning the same corpus got 59 files where I got 33. Neither was careless:
  **59 is every file where the *string* `claude-fable-5` appears; 33 is every file with a line whose
  `message.model` is `claude-fable-5`**, which is exactly the set that billed anything. The 26
  extra files are ones that merely *discuss* it — **including the sessions doing the measuring**.
  Measuring a model by grepping for its name counts your own analysis as data, and the more
  carefully you write about it the larger the number gets.
- **A split that cannot be reproduced does not get published, and the fix is a flag rather than a
  footnote.** 316 workflow-agent and 235 subagent requests were true and unpublishable: `--scope`
  offered `main` and `all` and nothing between, so quoting the split would have meant quoting a
  number the committed instrument could not produce — the defect being corrected, one layer down.
  `main`, `subagent` and `workflow` now **partition** the corpus, asserted by a test rather than by
  arithmetic in a message: on one snapshot, 20,498 + 6,594 + 17,462 = 44,554 = `all`, file sets
  disjoint and their union exact. Run across four invocations instead of one, the same sum is off
  by two — the corpus grows while you measure it, which is why a figure carries the hour it was
  taken.
- **The same failure has a time axis, and the tool had no guard on it.** A peer read a workflow's
  journal while the workflow was still running, saw 8 `started` against 7 `result`, and reported
  the difference as a lost agent. It was the judge, mid-run; the workflow completed **9 of 9**
  minutes later. The reading was correct and the question *when was this read* had not been asked
  — the same defect as *out of what population*, one axis over. My own analysis had controlled for
  it only by **observation** ("the most recent orphaned journal is 20260826, so none is in
  flight"), which is a fact about that afternoon and not a property of the instrument. `workflows`
  now excludes runs whose journal moved in the last `--settle-minutes` (default 60) and **prints
  how many it excluded**, because a silent exclusion is another unstated population. Journal rows
  carry no timestamp of their own — `agentId`, `key`, `result`, `type` — so the guard is the
  file's mtime, and a journal whose age cannot be read counts as settled: the guard drops what it
  can prove is recent, never what it merely cannot date. With the guard the corpus reads 55 runs /
  868 agents / 157 no-terminal-row; without it, 57 / 881 / 159.
