## S18 — the obvious fix would have shipped the defect it claimed to fix (20260830 15:15)

**HIGH — the right answer was written down, one layer down, and taking it would have been wrong.**
`sync.py:2190` already handles this case beautifully: it decides from the sidecar's own recorded
`content_hash` rather than from a cache miss, peeks the extraction cache, reuses paid text for free
when it is warm, and raises the honest `PaidExtractionUnavailableError` when it is not.
`docs/DESIGN.md:1036` names that as the required outcome. So the obvious fix was to stop `pairing.py`
pre-empting it — emit `Reembed` and let the layer with more information decide. **Every sentence of
that is true and the change would have introduced a Decision 9 violation.**

What stopped it was reading `_paid_survivor_in_current_index` instead of trusting its name: it
selects `WHERE id = ? AND state = 'active'`, so a **revived** row gets no index-side protection at
all. The only remaining guard is `sync.py:2190`, which reads the *sidecar's* provenance — and
`WalkedSidecar` carries `path`, `document_path`, `id`, `file_hash` and nothing else, so `pair()`
cannot distinguish a document the cache could revive from one a free backend would silently
downgrade. **The fix that removes a false claim would have shipped a silent one**, under a commit
message about honesty.

**That turned an implementation choice into a decision with a price, which is the user's and not
mine.** Three options with a real trade-off — honest reason only, route to the extractor, or widen
`WalkedSidecar` to carry provenance — were put to the user with the cost of each. **They took the
first, 20260830**: the reason is corrected and nothing else moves. The cost is stated rather than
buried, here and in `docs/DESIGN.md`'s row: a user whose extraction cache is warm still pays for
text their machine already holds.

**The distinction that made it a stop rather than a judgement call is worth keeping.** Choosing
*how* to implement what a plan specifies is an implementer's; choosing *what* it should have
specified is not. The plan said the fix "must keep the paid-protection clause and stop conflating
retired with changed" — all three options do exactly that, and they differ only in whether a warm
cache may spare the user money. That is a question about spending, and no amount of reading the
code answers it.

**MEDIUM — a census cannot see a reason, so nothing but an assertion on the reason catches it.**
`describe()` returns `{"PaidExtractionRequired": 1}` whether the plan says the content changed or
the row was retired, and both are one action either way. The mutant that inverts the precedence —
`RETIRED if retired else CHANGED` — is therefore invisible to every structural check in the module,
and it fails in the direction that matters: a user whose file genuinely *did* change is told nothing
about it did. It is the obvious implementation, and it is the one a reader would write.

**MEDIUM — a field is not a message.** The defect was never in a field; it was in a sentence a user
reads. So the claim is pinned twice: a unit test on which reason the plan carries, and a
`test_sync.py` test that drives a real delete-and-restore and asserts what is printed. The unit test
alone would have passed against a build whose `sync` still said "content changed" for both reasons —
the seam rule applied to a string rather than to a transport.

**LOW — the reproduction that made all of this cheap was six lines and one changed field.** The same
inputs with `state=ACTIVE` give `Skip` and protection; with `state=DELETED` they give
`PaidExtractionRequired`. A control that differs in exactly one field is worth more than a paragraph
of reasoning about what the branch does, and it is what let the fix be scoped in minutes rather than
argued.
