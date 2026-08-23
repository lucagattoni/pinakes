- **`CLAUDE.md` extracted: 274 → 220 lines, and nothing was lost.** Its own hygiene rule 6 says
  crossing ~150 lines triggers extraction, and the file had crossed it by 83%. Five sections of
  detail moved to the page that owns them, each leaving a pointer that states the fact a reader
  would otherwise open the sub-doc for: [`docs/RELEASING.md` § Landing a
  branch](https://lucagattoni.github.io/pinakes/RELEASING/#landing-a-branch) (what `land.py`
  refuses, and why `--cleanup` deletes both copies of a branch), [`docs/INVARIANTS.md` § The paid
  path's key is its own](https://lucagattoni.github.io/pinakes/INVARIANTS/#the-paid-paths-key-is-its-own),
  [`docs/BUILDING.md` § Proposing a change to a document you do not
  own](https://lucagattoni.github.io/pinakes/BUILDING/#proposing-a-change-to-a-document-you-do-not-own),
  and `docs/DESIGN.md` § 7.3 (the corpus-power numbers). The plan-status detail was **deleted as a
  duplicate**, not moved: `docs/README.md`'s routing table already carried it in more depth.
  `docs/ROADMAP.md` and `docs/STATUS.md` were deliberately not touched — `tools/release_order_gate.py`
  parses five ordered sequences out of them, and an inserted heading re-parents every section below it.
