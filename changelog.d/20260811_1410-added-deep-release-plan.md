- **The deep release has a plan.**
  [`plans/20260811_1358-deep-release.md`](https://github.com/lucagattoni/pinakes/blob/main/plans/20260811_1358-deep-release.md) —
  `pnk ask` and `pnk ask --deep` in seven increments, with **eight open decisions, every one of
  which blocks an increment**, so nothing in it is buildable until they are taken. It had been
  described as "planned" since `0.1.2` with no plan behind the word. Two of its measurements change
  what the older documents imply: the budget machinery is **already built and proven by the paid
  extractor**, so this release adds the loop and not the machinery; and `[retrieval.confidence]`
  **ships commented out**, so the escalation gate DESIGN § 4.2 depends on exists on **no KB a user
  creates** — which is what most of the open decisions are about. `CLAUDE.md`, `docs/README.md` and
  `docs/ROADMAP.md` all said the deep release had no plan; all three now name it.
