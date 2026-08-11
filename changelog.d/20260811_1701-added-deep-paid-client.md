- **The deep release's paid client, and the second — and last — entry on the allowlist.**
  `src/pinakes/deep/client.py`, added in the same commit as its `.paid-path-allowlist` line, with
  DESIGN § 1 and INVARIANTS: the gate refused the commit until the line was there, which is the gate
  working rather than the gate asserted. It builds the two calls a round is made of — decompose, and
  answer — through a `Transport` seam identical in shape to the extractor's, so
  `tests/test_deep_client.py` drives every branch with `anthropic` **not installed**. `anthropic` is
  imported inside the transport, the key is `PINAKES_ANTHROPIC_API_KEY` resolved explicitly, and a
  missing one now names the command that wanted to spend rather than the extractor.

  **Two structural defences against the injection risk § 5 of the plan names**, both properties of
  the wire format rather than checks bolted on after. A subproblem comes back as a plain string and
  the schema has no other field it could come back in — no path, no filter, no KB selector — so the
  worst a steered model can do is choose a bad search question. And an answer cites **passage
  numbers**, positions in the block that was sent, so a citation naming evidence the call never had
  is refused rather than dropped: dropping would leave prose whose support had silently disappeared
  while the remaining numbers still made it look sourced.

  **`pnk serve` must never load it**, and that is now a gate (DESIGN § 4.3: an MCP loop would spend
  the *operator's* money on the *caller's* question). It lands with the module because an assertion
  cannot name a module that does not exist, and it carries a planted-import negative control,
  because "the name is absent" is also true of a run that imported nothing.

- **What every paid client obeys now lives in one module.** `src/pinakes/paid.py` — the key's name,
  the SDK's retries being off, whether a failed call *billed*, and how a reconciliation is computed.
  Four rules, each of which fails **silently** when a second copy drifts, and a second paid entry
  point is exactly where the copies would have appeared. It is deliberately **not** on the
  allowlist: it imports no client (it is handed the caller's already-imported module), so the gate
  scans it like any other file and would refuse an `import anthropic` added to it.
