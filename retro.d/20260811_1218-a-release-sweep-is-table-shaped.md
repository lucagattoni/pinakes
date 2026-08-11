## A release sweep is table-shaped, and a narrative is not a row — 20260811 12:18 UTC

**What happened.** With every plan built out and the open-corrections list empty, the first check of
the next session was *what does the repo say about itself*. `docs/ROADMAP.md` said 0.21.0. Its
release table carried a `0.22.0` row, its per-release section carried the full `0.22.0` write-up,
and its open-corrections section said *none live, all four shipped in 0.22.0* — but the two prose
blocks that state the project's position, `## Where things stand right now` (stamped **20260808
06:41**) and `## The template release`, were three releases behind. One of them still said **"T4 and
T7 are still to come"** about increments that had shipped on 20260808 and 20260808.

**Why it survived five sweeps.** The landing checklist asks which *file* to edit, and the file was
edited — every time. What a sweep naturally finds is the row it is adding: a table has one line per
release, so the release being cut points straight at its own row. A paragraph that summarises *all*
releases has no row to add, so nothing in the act of cutting a release makes it obvious. **The
per-release sections and the tables were correct at every commit; only the summaries were wrong** —
which is the worst arrangement, because a reader checking one against the other finds agreement in
five places out of six.

**The second instance is sharper.** `docs/README.md`'s plan-routing table — the table whose whole
job is to tell a session which plan is live — had **no row at all** for
`plans/20260811_0720-decisions-gates-and-corrections.md`, the plan `CLAUDE.md` names as the live
build order and the authority for eight decisions. The plan was written, its six increments were
built and landed, and the index of plans never learned it existed. **A missing row is invisible to
every check that reads rows**; only asking *"is everything that exists listed here?"* finds it, and
that question is not part of landing an increment.

**What generalises.** *"Update the doc"* and *"update the doc's summary of itself"* are different
actions, and only the first is prompted by the work. A document that both **enumerates** and
**summarises** will drift at the summary, in the direction of the last release that bothered to
rewrite prose. Two checks are worth adding to a landing:

- **Grep the docs for the *previous* version number** after a release, not just for the fields the
  checklist names. `grep -rn "0\.21\.0" docs/` would have found both ROADMAP blocks in seconds.
- **Ask what is missing, not only what is wrong.** The routing table's defect had no wrong text to
  find. Reading `ls plans/` against the table is a ten-second check that no diff review performs,
  because nothing in a diff is absent.

**And the check found more than it was looking for.** Auditing the neighbourhood surfaced that the
20260807 audit's **40 documentation corrections have never been worked** — the file has one commit,
the one that created it — and that the same audit deferred a full review of `docs/ROADMAP.md` until
after T2, which shipped in 0.18.0. Neither is visible from any release's own sweep either.
