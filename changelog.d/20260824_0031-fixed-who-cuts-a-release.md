- **Four documents told an implementer to write files the ownership table forbids it.** `CLAUDE.md`
  § *Documentation has one owner* makes `docs/**`, `plans/**`, `README.md`, `CLAUDE.md` and
  `CHANGELOG.md` planner-only, unconditionally. Four other places contradicted it: § *Working mode*
  said an increment ends at *"cut the release"*; `docs/RELEASING.md` addressed *"the agent cutting
  it"* without ever saying who that is, while directing them into three planner-only documents;
  `docs/README.md`'s landing checklist handed its reader **STATUS, CLI, MANIFEST, GUIDE and
  DESIGN**; and `docs/BUILDING.md` § *Hand over before you stop* mandated five planner-only writes
  *"landed in the same branch as the work"*. **No rule was added** — the restriction already existed
  and was already obeyed, measured across eight release commits (each writing five to seven
  planner-only documents) and six implementer commits (none writing any). The four sentences that
  denied it are corrected instead. The handover rule (the user, 20260811 15:37) is **not** weakened:
  it still lands in the increment's own branch, as proposals rather than edits.
