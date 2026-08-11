- **An eval artifact records both the vector tier that was *asked for* and the one that *ran*.**
  `vector_tier` keeps its meaning — the manifest's own string — and `vector_tier_resolved` is added
  beside it. A KB on the default wrote `"vector_tier": "auto"`, and `auto` is a request to choose
  rather than a tier, so the header could not answer the question a measurement artifact exists to
  answer: which tier produced these numbers? **No existing value changes**, so re-running a
  committed artifact shows no movement where no measurement moved. `tools/reachable_ceiling_probe.py`
  copies this block and is updated with it, with a test that fails if the two ever disagree — the
  copy is why the field went stale there in the first place.
