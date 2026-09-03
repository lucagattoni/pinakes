## A green battery inherits its author's framing (20260903 10:48)

**MEDIUM — the mutants a fix's author can imagine are the failure modes that author already
guarded against.** Row 7's battery section ran 39 mutants and killed 38. Every one of the 38 was
written by the person who had just written the fix, and every one died to a test that same person
had just written. That is a closed loop, and it reads as proof.

The 39th is the one worth keeping. It widened S6's gate from `document.path in orphaned_documents`
to the looser `document.path in sidecar_by_document`, and it **survived** — which looks like a
missing assertion and was not one. Applied against the full suite it was green on 2398 tests: an
*equivalent* mutant. The predicate I had introduced as the fix does not, at that program point,
constrain anything the looser one does not.

Three things went wrong at once, and only the first is the kind a gate catches.

1. **The mutant was equivalent.** Not a finding.
2. **Its `kills` selector named a test of a different function** — `_orphans`, which never reaches
   that gate. `tools/batteries/README.md` says the selector is the half that historically rots;
   here it was wrong on the day it was written, and a SURVIVED row hid it, because a row that
   survives never exercises its selector.
3. **The justification I wrote for withdrawing it was false.** I wrote that control reaches that
   line only for a document being soft-deleted, so its path is necessarily absent from
   `after.files`. The conclusion is true. The reasoning assumes exactly what it needs to prove,
   and two routes do leave a *present* path unhandled and drop it into that loop. What actually
   closes the case is a three-step argument about `claimed_by_id`: both routes require the id to
   be claimed by a sidecar beside a present file, and every such sidecar is reached by one of two
   `handled_ids.add(sidecar.id)` sites before the vanished-path loop runs.

**Number 3 was caught by a peer trying to refute the withdrawal, and failing.** They built a
present-path counterexample, ran it against both the real module and a mutated copy — anchor
asserted to match once, `__pycache__` cleared, `pinakes.pairing.__file__` checked so that a null
result could not have come from importing the unmutated file — and got an empty result from both.
The refutation failed; the argument it was aimed at was replaced anyway, because attacking it is
what exposed that it had never been load-bearing.

*Lesson: a battery written by the author of the fix measures the author's imagination, not the
code. Its green is evidence that the fix does what its author meant, never that what they meant
was right. Two cheap things buy back most of the gap — run a surviving mutant against the whole
suite before believing it is a finding, since an equivalent mutant and a missing assertion are
byte-identical in the report; and have someone who did not write the fix try to refute the
reasoning rather than re-read the diff, because the reasoning is where the author's framing is
load-bearing and the diff is where it is invisible.*

*Second-order: a SURVIVED row never runs its own selector, so a battery's survivors are exactly
the rows whose second half is unverified. The one place the report cannot check itself is the one
place it asks to be believed.*

See [`tools/batteries/src-pinakes-pairing.toml`](https://github.com/lucagattoni/pinakes/blob/main/tools/batteries/src-pinakes-pairing.toml),
which carries the withdrawn row's reasoning in place of the row.
