- **The deep release's estimator: what one `pnk ask --deep` would cost, before the first call**
  (E2). `pinakes.deep.estimate` prices both branches the loop can take — `estimate_synthesis` for
  the one-call cheap branch a confident question takes, `estimate_round` x `max_rounds` for the
  decomposition loop, and `estimate_operation` for whichever the confidence signal already chose.
  Pure: no client, no I/O, no wall clock, `Decimal` end to end and never quantised (the ledger does
  that, once). It refuses a stale price table and a request that would not fit the model's
  documented context window — the second one reachable from a manifest alone, unlike the PDF
  path's, so its remedy names `[retrieval] final_k` and `[chunking] max_tokens` rather than
  reporting a defect. The question's own text is priced too, against a stated character ceiling —
  it arrives as an argv string with no length limit and rides in every call of a run. Nothing is
  wired to the CLI yet: `pnk ask`'s escalation line still prints its sentence without a number
  until the increment that has a `[deep]` section to read.
- **A round is priced as two calls, not as one input.** The plan's formula counts a round's input
  once, and a round makes two calls — so counting it once under-prices every round by everything
  the second call also carries: the memory, the question and the prompt. That is the direction a
  budget may never be wrong in. Both calls are
  priced at the same worst case instead, which also gives `per_call_eur` the property the per-call
  reservation needs: whichever of the two is about to run, one number bounds it.
- **`tools/measure_passage_tokens.py`** — the offline half of the measurement behind the two
  per-passage ceilings. A chunk is sized in the embedding model's tokenizer and billed in the
  vendor's, and the conversion cannot be measured without spending; this measures the character
  width the two share.
  Over 2,424 chunks of the committed corpora at `max_tokens = 510`, the widest real chunk holds 4.27
  characters per embedding token, which the shipped ceiling of 3 vendor tokens per chunk token
  clears by 2.1x. It also reports the longest citation envelope a passage is wrapped in — 220
  characters, which is what set the per-passage envelope constant after a first draft guessed
  "under 120" and was wrong.
