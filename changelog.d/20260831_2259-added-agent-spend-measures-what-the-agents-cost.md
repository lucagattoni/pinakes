- **`tools/agent_spend.py` measures what the agents working on this repository actually spend**,
  reading only their own transcripts — no network, no API calls, nothing written. Four subcommands:
  `models` (requests, price-units and estimated dollars per model), `boot` (the fixed context a
  session re-transmits on every request), `workflows` (workflow agent outcomes and how the losses
  are distributed), `rewrites` (mid-session full cache re-writes, bucketed by idle gap). It prints
  only counts, models and identifiers — never prompt or response text — so its output can be pasted
  into a public document.
- **It exists because two properties of the transcript format silently corrupt any naive sum**, and
  both were got wrong on the first pass at this data. One API response is written as **several**
  lines that repeat the same `requestId` and an identical `usage` block, so summing per line
  inflates spend **2.14×**; and `output_tokens` is a **running partial**, so taking a request's
  first line undercounts output **1.7755×**. `tests/test_agent_spend.py` pins both against synthetic
  transcripts, and reads nothing from `~/.claude`, so it says the same thing on a machine that has
  never run an agent.
- **`--scope` selects the population, and every subcommand prints which one it read.**
  `main`, `subagent` and `workflow` **partition** the corpus and `all` (the default) is their
  union — a property a test asserts, so a split can be quoted without leaving the tool. The default is `all` deliberately — a main-loop-only file list cannot
  contain a subagent transcript, so it answers questions about fan-outs with a zero that looks like
  a finding.
- **`workflows` ignores runs that are still writing** (`--settle-minutes`, default 60) and says how
  many it set aside. An agent that has not returned yet is indistinguishable from one that was
  lost, so a workflow read mid-flight reports healthy agents as losses — measured live, the
  unguarded count was 159 orphans against the settled 157.
- **A model off the rate card reports no dollars rather than a guessed price**, and the rate card
  states its own provenance and cache date in the source. An estimate over transcripts is never a
  bill, and the code says so where the number is produced.
