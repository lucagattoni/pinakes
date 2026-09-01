## A section number is only meaningful inside its own document (20260901 18:26)

**A cross-document reference lost its document and kept its number.** `docs/README.md` described
what `KB-UPDATES.md` still leaves unbuilt as *"the rest of §8's shape — `pnk adopt`"*.
`KB-UPDATES.md` §8 is *Open questions*, and it has never contained `pnk adopt` — not in the
current file and not in any commit, which `git log -S` settles in one command. The §8 that
proposes the command is `docs/graph/PINAKES_APPROACH.md`'s, and the reason the number travelled
is visible in that file: its release-mapping table has a **From** column whose cells read `§3`,
`§8`, `R1 R6` — *its own* sections. Someone read `the template release ⚠️ | `pnk adopt` … | §8`
and carried `§8` into a sentence about a different note. **The bare `§N` form is what made it
portable.** A reference that had read *PINAKES_APPROACH §8* could not have been misfiled.

**Two registers agreed with each other and neither was checked against the tree.** The dangling
`§8` had been repeated between `docs/README.md` and my own draft rewrite of the
`KB-UPDATES.md` header — I was about to propagate it into a *second* file, sourced from the first,
because the first was a document I trust. What broke the loop was not scepticism about the claim.
It was checking whether the string was in the file at all: `grep -n 'pnk adopt' docs/KB-UPDATES.md`
returned only the line I had just written. **The selector was proven able to fire** — the same
pattern across the repo returns eight other hits — so the empty result was a result.

**And the header that prompted all this failed by accretion, not by error.** Every clause in
`KB-UPDATES.md`'s status header was true when it was written; four releases each appended one, and
the reader meets them in the order they were added rather than the order they matter. The final
clause said `--apply` remains a proposal; it had shipped two releases before, and §1 of the same
file cited *"the header above"* as agreeing with it. **An append-only status line degrades even
when nobody writes anything false into it** — which is the case for rewriting to the current state
rather than layering a correction, and the reason that convention exists.
