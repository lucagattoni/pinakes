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
