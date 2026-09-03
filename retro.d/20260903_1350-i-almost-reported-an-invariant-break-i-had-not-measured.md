## I almost reported an invariant break I had not measured (20260903 13:50)

**MEDIUM, and the outcome was fine — which is the reason to write it down.** Mid-fix, one test
failed on 3.14 but not 3.13. The inference came immediately and it was a good one: at the pairing
site, `is_file()` returns False on 3.14 instead of raising, so the document's existing sidecar goes
unread, so pairing sees no sidecar, so it **mints a fresh ULID for a document that already has
one** — ULID permanence, in `docs/INVARIANTS.md`, broken silently and per-interpreter.

Every step of that chain was plausible. The mechanism was real, the failing test was real, and the
conclusion was the most serious class of defect this project recognises. I had a message half
drafted to the planner saying so.

**I ran it instead. There was no duplicate ULID.** 3.14 refuses the document too — via
`SidecarError` rather than `PermissionError`. The real divergence was the error *class and its
remedy*, a genuine defect and a much smaller one.

**The lesson is not "measure before asserting", which was already the rule.** It is *when* the rule
is hardest to follow. The pull to skip the measurement was strongest precisely because the
hypothesis was alarming: an invariant break is urgent, a peer was waiting on an answer, and the
reasoning felt like it had already done the work. Severity creates the impression that speed is the
responsible choice, and a chain of correct-looking steps feels like evidence because each link is
checkable — but the conclusion is only ever as good as the run nobody did.

**So: the more serious the claim, the more it earns a measurement rather than exempting itself from
one.** The escalation-worthy finding is the one to check first, not the one to send first. A
concrete marker for next time — I was about to write the words *"silently mints a second id"*, a
statement about runtime behaviour, without having observed any runtime behaviour. A sentence
describing what the code does at run time and sourced only from reading it is a hypothesis wearing
a report's clothes.

Related: [[the-command-ran-the-number-was-typed]] — there, the measurement happened and the figure
did not come from it. Here the figure would not have come from anything at all.
