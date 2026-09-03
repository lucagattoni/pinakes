## A two-way selector that can only fall one way (20260903 15:23)

**What happened.** Verifying the published 0.32.3 fix for the `--prune` bug, the check was
`grep -qi 'orphan' && echo "ORPHAN REPORTED" || echo "the id is safe"`. On the fixed wheel
`pnk doctor` printed `OK   orphaned sidecars: none`. The word *orphaned* is in that line, so the
selector matched, and the harness printed **`** ORPHAN REPORTED — a live document's id is offered
to --prune **`** about a release that had just been shown correct — with the output it had misread
printed two lines above the verdict.

**Why it is not a typo.** The selector had two branches and only one of them could ever be reached
by evidence. `grep -q` matching is a claim; `grep -q` *not* matching is the absence of a claim, and
the `||` branch spends it as though it were the opposite claim. So every failure mode of the
instrument — a wrong pattern, a command that died early, an empty string, a renamed message —
lands in the same branch as a genuine pass. `&&`/`||` on a matcher is a **one-way** test wearing
the shape of a two-way one, and it is the shape most of my quick verification snippets have.

**Why nothing caught it.** The check ran, printed, and exited 0. There is no gate for *the
measurement was performed and the number was typed anyway*, because the checking step is present.
It was caught only because the surrounding two lines of raw output happened to be printed beside
the verdict, and a human-shaped read of them disagreed. Had the harness been tidier — verdict only,
no evidence — it would have shipped a false negative about the most severe bug of the day, in the
direction that says *still broken*, which is the direction that gets acted on.

**The fix, and it generalises past this check.** State both expected forms and refuse to guess when
neither appears:

    if   printf '%s' "$out" | grep -qE 'WARN +orphaned sidecars: [1-9]'; then  verdict=BROKEN
    elif printf '%s' "$out" | grep -qE 'OK +orphaned sidecars: none';    then  verdict=FIXED
    else                                                                       verdict=INCONCLUSIVE
    fi

Three outcomes, not two. `INCONCLUSIVE` is the one that carries the information the `||` branch was
destroying: *the instrument did not recognise what it was looking at*. It is also the branch that
fires when someone rewords the message, which is when a silent selector is most likely to be wrong
and least likely to be doubted.

**The rule.** A selector deciding between two states must be able to *see* both. Write the positive
pattern and the negative pattern, and make the fall-through say so — never `match && A || B`. This
sits directly beside two rules already written down here: *a null result carries no information
until the selector is shown able to fire*, and *a claim resting on an instrument you chose must
state the selector*. This is the third face of the same coin, and the cheapest to check: read your
own snippet and ask which branch a broken instrument lands in. If the answer is "the good one", the
snippet cannot fail visibly.

**Two more instrument failures in the same twenty minutes, both of which printed a clean-looking
pass.** A hand-written `pinakes.toml` was refused for a missing key, so the crash probe never
reached the crash. And with the embedding backend absent, `pnk sync` exited before the walk it was
built to exercise, printing *no PermissionError* having tested nothing — the same class as a fixture
whose sidecar is missing, so the loop that raises is never entered. **Three in one session says the
failure mode is the harness, not the day**: every one of them stopped short of the code under test
and reported the absence of a symptom as the absence of the defect.
