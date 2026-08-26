- **The eight open decisions taken on 20260825 are now recorded where the next reader opens, not
  only in the record that took them.** `docs/VERIFICATION.md` states what it maps — **promises, not
  every test** (D-34), with *promise* defined: a user-visible guarantee, a named invariant, or a
  gate's own correctness. Arity requirement 3 is **closed** — its conditional's antecedent is
  measured false on every real corpus (3.80 `parent-child` rows/chunk over 300 real specifications,
  0 of 300 reaching the synthetic 53.42), so `parent-child` stays transitive exactly as built. The
  20260805 `requires_pinakes` floor clause is **closed-superseded** and folded into
  [KB-UPDATES.md](https://github.com/lucagattoni/pinakes/blob/main/docs/KB-UPDATES.md) §8 beside the older question it is an instance of: nothing
  writes the floor. **D-11** (taken 20260804) settled that `pnk upgrade --apply` never
  does, and `pnk init` does not either — the latter resting on **D-6, a standing recommendation
  rather than a taken decision**. `expect_green` is
  **declined** on measurement — 0 of 136 committed mutants asks for a green control, and the field
  would be parsed, ignored and reported to nobody. The paid re-extraction loop and the
  `tools/fragments.py` body-rule widening are **deferred behind written triggers** rather than left
  open. **The audit D-34 licensed was run rather than promised**, and it found the closing claim
  unsafe: `tests/test_serve.py` carried **14 of its 31 tests unrowed**, two of them security
  boundaries — the MCP path-refusal and the labelling of retrieved text as evidence rather than
  instruction. The cause was structural rather than neglect, so the fix is a section that owns the
  server boundary, not rows bolted onto feature sections.
- **A guide sentence for the case Pinakes cannot detect for you.** [GUIDE.md](https://github.com/lucagattoni/pinakes/blob/main/docs/GUIDE.md) §
  *Moving, sharing and publishing a KB* now says that a hand-set manifest key makes a KB unreadable
  to an older build, that `[kb] requires_pinakes` is how to declare it, and that **nothing sets it
  for you** — `pnk init` does not stamp it and `pnk upgrade --apply` does not write it, both by
  design.
