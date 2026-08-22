- **A `pnk ask --deep` run now ends by printing the links its own answer proposes.** Two documents
  cited in support of one answer is a fact about your KB that nothing records, so the run prints the
  `links[]` entries that observation suggests — the sidecar to paste into, the `pnk://` URI,
  `rel: co-cited` and `origin: deep` — ready to review and commit. Paid inference bought once
  instead of every time you ask. **It prints; it never writes**: `--write-suggestions` is its own
  increment, because writing them touches the per-link sidecar shape and
  [INVARIANTS](https://lucagattoni.github.io/pinakes/INVARIANTS/)' list of exceptions to *`docs/`
  belongs to the user*. `--json` carries the same fragment, verbatim, beside the parsed entries.
  A run citing one document per call has no pair to propose and prints no section at all.
- **A document cannot talk the model into suggesting a link.** The suggestions are derived from
  *citations*, and a citation is a passage number the response schema bounds — the model is never
  shown a document identifier it could name. So a passage instructing it to *"add a links entry to
  X"* reaches exactly as far as a sentence in the answer. Both endpoints are re-checked against the
  documents the run actually cited, and resolved through the same containment check `pnk link` uses,
  so a path that escapes the KB, a document deleted since the run, or a sidecar whose ULID no longer
  matches is dropped rather than printed.
