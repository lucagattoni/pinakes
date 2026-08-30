## One code change falsified six documents, and the owner of the code could not fix any of them (20260826 07:02)

`make release-check` became a real gate in `674eda6`. The moment it landed, **six documents were
false** — and none of them was in the coder's file set.

| Document | What it said |
|---|---|
| `docs/README.md` | *"`make release-check` **runs no gate at all**"* |
| `docs/ROADMAP.md` ×3 | the same claim, at `:124`, `:185`, `:2274` |
| `plans/20260731_1202-open-corrections.md` | the item itself, `🛑 LIVE` |
| `docs/STATUS.md`, `CLAUDE.md` | *"before the tag, never after"* — now *before the **push*** |

**MEDIUM — two rules this repository holds simultaneously cannot both be satisfied, and nobody had
said so.** *Keep docs in sync with code — in the same change* is a standing rule and calls stale docs
a **severe** defect. *Documentation has one owner* says no other agent edits a document; it proposes.
For any coder change that falsifies a document, **the same-change rule is unsatisfiable by
construction** — the person who knows the change cannot write the document, and the person who owns
the document is a separate session. There is always a window. Here it was about twenty minutes and
nothing published inside it, but that is scheduling luck, not a property of the mechanism.

**The tension resolves in favour of ownership, and the cost should be named rather than absorbed.**
The mitigations that actually worked, both of them cheap: the coder **enumerated the falsified
documents in the same message that announced the landing** — five of the six, each with a line
number, before being asked — and the planner ran the sweep as the next increment rather than
batching it. Neither is written down anywhere as the procedure. **What makes the window survivable is
the handover listing the damage, not the ownership rule being relaxed.**

**LOW — the counted anchor did not bite, and it was worth checking rather than assuming.**
`docs/RELEASING.md` warns that Part 5's *Open corrections* heading carries its own item count in its
anchor, so closing an item breaks every in-page link. Checked: the heading is a bare
`## Open corrections` at `ROADMAP.md:2255` and the counts live in prose at `:102`, `:122` and `:186`.
**Corrected 20260830**: every one of those numbers was right at `c111645^` and wrong the instant
`c111645` landed — the commit that added this fragment shifted `ROADMAP.md` by a line. `:124` was
never a count, so the third is `:122`, not `:124` plus the shift.
The warning describes a hazard that is not present in the current text — **true when written, and
now a trap for whoever believes it and works around a problem that is not there.**

**LOW — five citations were the reason not to renumber, and they were verified rather than
relayed.** The coder's diff deliberately kept steps 6–8 numbered as they were, because five live
citations name *"`docs/RELEASING.md` step 8"* — `CHANGELOG.md`, `docs/STATUS.md`, `docs/ROADMAP.md`,
`.github/workflows/release.yml`, `tests/test_check_script.py`. All five were grepped before the diff
was accepted. **Renumbering is the invisible half of a documentation edit**: nothing goes red, and
every citation is off by one.
