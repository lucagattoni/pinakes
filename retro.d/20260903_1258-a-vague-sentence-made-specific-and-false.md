## A vague sentence made specific, and false (20260903 12:58)

**MEDIUM — the fix made the message more precise, which is normally the improvement, and that is
how it got worse.** The retrieval confidence reason used to say *"nothing matched the filters"*
even when no filter had been passed. Row 8 split it, and the unfiltered arm became *"this KB has
no active documents to search"*.

That sentence is false whenever an active document produced **zero chunks**. `_allowed_chunks`
joins `chunks` to `documents`, so an empty result means *no active document produced a chunk*, not
*no active document*. A whitespace-only file syncs cleanly — `chunk_document` returns nothing for
it, the row is written `active` regardless — and the user is then told their KB is empty while
`pnk doctor` counts the document.

**The old sentence was unhelpful; the new one was wrong, and confidently.** An unhelpful message
sends a user to look around. A specific false one sends them to look at the wrong thing, and it
carries the authority of having been thought about. When a message is being made more specific, the
question to ask is not *is this clearer* but **what does the code actually know here** — and the
answer was: less than the sentence claimed, because the emptiness of a join is evidence about the
join, not about either table.

The comment beside the first fix reasoned explicitly about soft-deleted documents and never
considered the zero-chunk state, which is the shape of the error: **the justification enumerated
the states its author had thought of, and read as an enumeration of the states that exist.** The
probe now asks the `documents` table the question the join cannot answer.
