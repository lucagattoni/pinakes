- **The live build order gained rows 14 and 15, and one of them is a refusal.** Row 14 rules what a
  retro fragment's *second* `## ` heading owes: a parenthesised `YYYYMMDD HH:MM` stamp ending the
  heading, in the same spelling as the first — **not** the filename's prefix, and with nothing
  constraining its value. The obvious stricter rule would have refused a real released fragment:
  across the **129** fragment paths ever added under `retro.d/` — 239 distinct versions, read from
  the object store — **two** carry two column-0 `## ` headings, and the only one whose author
  stamped them at all made the second stamp differ from the filename prefix deliberately,
  recording a second moment inside one incident. One instance licenses the existence of a later stamp; it does not
  license a monotonicity rule, so none was written.
- **Row 15 fixes a comment and declines to gate it.** One battery section out of thirty conforms to
  neither reserved form for its version slot — it must read `0.30.0 · `, the release that shipped
  the gate, **not** `unreleased, 20260823 · `, which the planner instructed and which would have
  written a false claim into the one file whose job is recording which release shipped what. The comment is rowed for repair; the check that would
  have caught it is **deliberately refused for now**, because adding a gate is new process and
  whether this repo should freeze new process is a decision sitting with the user this minute. It is
  recorded as a refusal rather than left as an oversight, and it may be proposed again once that
  decision lands.
