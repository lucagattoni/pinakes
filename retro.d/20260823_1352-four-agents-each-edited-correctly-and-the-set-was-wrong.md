## Extracting CLAUDE.md — four agents each edited correctly, and the set was wrong (20260823 13:52)

**HIGH — every defect in this increment was a *neighbourhood* defect, and none was a content defect.**
Four agents wrote four destination sections in four files. Each one did its own job correctly: right
heading, right anchor, every source fact carried, matching voice, no existing heading renamed. The
review then found **five defects, and all five were about what the surrounding text already claimed**:

| Where | What it still said |
|---|---|
| `docs/RELEASING.md:3-5` | *"the traps … stay in `CLAUDE.md`"* — one had just moved into this file |
| `docs/RELEASING.md:7` | *"Extracted … 20260801 … Nothing was dropped"* — a provenance note now silently covering content added 20260823 |
| `docs/INVARIANTS.md:6-9` | described the file's **two** structures; there were now three |
| `docs/README.md:83` | the routing table still described the pre-extraction layout |
| `docs/BUILDING.md:168` | pointed at `CLAUDE.md`'s text, which is now the *compressed* version |

`docs/README.md` § Conventions has said *audit the neighbourhood, not the diff* since it was written.
**A per-file agent cannot follow that rule, because the neighbourhood is the thing outside its
file** — and the one file that most needed editing, the routing table, was assigned to nobody and so
was the only `docs/` page absent from the diff. If work is fanned out per file, **something has to
own the seams**, and it is not any of the writers.

**HIGH — the extraction nearly created a second home for a rule, which is the failure it exists to
prevent.** A section was written into `RELEASING.md` for *naming unbuilt work* — and
`docs/README.md` § Conventions **already owned that rule in full**, including the same date, the same
`STATUS.md` pointer and the same historical-records carve-out. Worse than duplication: the pointers
formed a loop in which no file admitted README held it. README said the live names are in
`CLAUDE.md`; the new section said the rule and the table live in `CLAUDE.md`; `CLAUDE.md` pointed at
the new section. **A reader following the pointer from `CLAUDE.md` would never reach the copy that
actually owns the rule**, and the two could drift with every command reporting success. The section
was deleted and `CLAUDE.md` now points at README. *Before writing a destination, grep for the fact —
a relocation into a fact's existing home is a duplication, not a move.*

**MEDIUM — and checking that duplicate turned up a stale claim nobody was looking for.**
`docs/README.md` § Conventions still named **the deep release** as live unbuilt work. It left that
table at 0.26.0 — its final cut — three releases ago, and `CLAUDE.md`'s own table had been correct
all along. The duplicate was not merely redundant; **the two copies had already drifted**, which is
the concrete form of the harm "one fact, one home" is stated to prevent.

**MEDIUM — four dead links, written while creating pointers whose entire purpose is to be followed.**
`CLAUDE.md` sits at the repository root, so a relative `](RELEASING.md#…)` resolves to `/RELEASING.md`,
which does not exist. Four were written that way. **`mkdocs build --strict` cannot catch this class**:
`CLAUDE.md` is not part of the built site, so its outbound links are checked by nothing. The check
that found them is three lines of Python — parse every `](path.md#anchor)` out of the file, slug
every heading in the target, compare — and it belongs in any future extraction.

**LOW — the honest outcome is 220 lines, not 150.** The guideline is ~150 and this file is at 220
after everything with a genuine home elsewhere was moved. Going further would mean deleting rules
the user set, and rule 6 says explicitly that the guardrail is *"the trigger to extract sections and
leave pointers — not a hard cap that justifies deleting information."* **Reporting the shortfall is
the correct outcome; compressing past it would have been the defect the rule warns about.** What
remains is dense by construction: a role rule, an ownership table, a naming table where every row is
a breaking change, and four sections of user-set working mode.
