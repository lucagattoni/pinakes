## The fix for a loud crash was a silent deletion, and only a probe said so (20260902 09:27)

S1 read as a one-line fix: `hash_file` lets `PermissionError` escape the walk, so catch it and skip
the file. The crash is loud, the traceback is ugly, and skipping is obviously kinder.

It is not. `pair()` decides what to do with an indexed document by whether the walk still reports
its path — absence means gone. A walk that skips an unreadable file therefore emits `SoftDelete`:
the row retired, its chunks deleted, `pnk sync` printing `1 removed` and exiting about something
else entirely. **A `chmod 000` would have removed the document from search.** The obvious fix turns
a loud crash into silent index loss, which is the shape this repository ranks worst, and it would
have shipped green.

Nothing in the plan said this. It was found by writing eleven lines of throwaway script that built
an `IndexSnapshot` and a `WalkSnapshot` by hand and printed what `pair()` returned — before a line
of the fix existed. The whole finding cost one tool call.

**The rule that generalises: when a fix changes what a downstream consumer is told, ask the consumer
before writing the fix.** Not after, and not by reading it. Reading `pair()` would have worked too —
the vanished-path loop is right there — but reading is what produced the one-line plan in the first
place. The probe answered a question I already believed I knew the answer to, which is the only kind
of question worth spending a tool call on.

## The fix's own first output was a command that destroys a ULID

Running it printed `orphaned sidecar (kept; remove with pnk doctor --prune): docs/c.md.pnk.yaml`
for a document sitting on disk, readable sidecar and all. `_orphans` derives orphanhood from the
walked file set, and the unreadable document had just left it. Following that remedy deletes the
sidecar, and with it a permanent id that other KBs may link to.

It was found by *running* the fix on a real KB with the real `[light]` backend, not by reading the
diff — the diff is three lines and every one of them is correct. This is the seam rule paying out:
unit tests prove a component honours a parameter, and only running proves what the user is told.

## An exit 0 from an instrument that never reached its population

`pnk doctor` was checked against an unreadable document and came back clean — exit 0, no traceback.
The conclusion "doctor is fine" was one keystroke away and would have been wrong.

The row had been marked `extraction_backend='claude'`, and the only paid backend name is
`claude-vision`. So `recorded_is_paid` was false, the loop body never ran, and the unguarded
`hash_file` was never reached. The tell was in the output and easy to skim past: `paid extraction
not requested: none`. With the real name substituted, `doctor` died in a `PermissionError`
traceback.

That is the fourth time in two days a null result nearly became a finding here. The others were a
`grep` pattern with a lookahead the tool rejected, a `sed` range using `\b` that BSD `sed` does not
support, and a `grep 'walk_sources('` over `tests/` that returned nothing because the call site
aliases it to `real_walk`. **Same shape every time: the instrument could not reach what it claimed
to have checked, and its silence read as an answer.** A control that must fire is the cheapest
insurance in this repository, and it is still not automatic for me.
