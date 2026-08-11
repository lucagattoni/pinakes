- **The roadmap's narrative said 0.21.0 while its tables said 0.22.0.** `docs/ROADMAP.md`'s
  *Where things stand right now* block was stamped **20260808 06:41** and claimed *30 releases in 14
  days*, *latest on PyPI `0.21.0`*, and the template release *part-shipped — T1 to T4*; its
  § *The template release* still read **"T4 and T7 are still to come"**. Three releases had shipped
  since. **The 0.22.0 sweep updated the file's tables and per-release sections and left its prose**,
  which is the shape of the miss: a release sweep is table-shaped, and a narrative block is not a
  row. Now current — **33 releases in 17 days**, latest `0.22.0` (verified against the index, not
  the CHANGELOG) — and both template-release gates are stated where the section that describes them
  is, with T8's failing leg and T6's written trigger rather than "neither is scheduled".
- **`docs/README.md`'s plan table had no row for the plan `CLAUDE.md` calls live.**
  `plans/20260811_0720-decisions-gates-and-corrections.md` is the authority for eight decisions and
  the routing table a session is told to read never listed it — so the two entry points disagreed
  about what exists. It has a row now, and the template-release row no longer says its two gated
  increments *remain*. Also recorded there: the 20260807 audit's **40 documentation corrections are
  untouched**, and that audit deferred a full review of `docs/ROADMAP.md` until after T2, which
  shipped in 0.18.0 and is still owed.
