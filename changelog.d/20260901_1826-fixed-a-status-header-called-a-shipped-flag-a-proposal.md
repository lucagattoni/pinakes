- **`docs/KB-UPDATES.md` no longer opens by calling a shipped command a proposal.** Its status
  header read *"What remains a proposal is `--apply`"*; `pnk upgrade --apply` shipped in **0.20.0**
  and five places already said so, including that same file's §1, §2, §9 and its own §9 table
  (*"Every row in this table is now built"*), plus
  [`docs/README.md`](https://github.com/lucagattoni/pinakes/blob/main/docs/README.md) and
  [`docs/STATUS.md`](https://github.com/lucagattoni/pinakes/blob/main/docs/STATUS.md). §1 even
  wrote *"(see the header above)"* while the header contradicted it. The header is now **rewritten
  to the current state rather than corrected by a further appended sentence** — which is how it
  broke: four releases each added a clause to the end, and the stalest clause stayed first.
  `Status: mostly proposal` is now `Status: mostly built`.
- **`docs/README.md` no longer sources `pnk adopt` from a section that has never mentioned it.**
  Its `KB-UPDATES.md` row said what remains a proposal is *"the rest of §8's shape — `pnk adopt`"*.
  `KB-UPDATES.md` §8 is *Open questions* and proposes no such command: `git log -S'pnk adopt' --
  docs/KB-UPDATES.md` is **empty over the whole history**, so the name was never there to lose. The
  §8 that proposes it belongs to a different document —
  [`docs/graph/PINAKES_APPROACH.md`](https://github.com/lucagattoni/pinakes/blob/main/docs/graph/PINAKES_APPROACH.md)
  §8, *ClaudeKB: the first fleet* — whose release-mapping table carries `§8` in a **From** column
  meaning its own sections. A section number was read out of one document's table and written into
  a cell about another. Both rows now name the right note; `pnk adopt` is still unimplemented
  (`grep -rn '"adopt"' src/` returns 0 where `"upgrade"` returns `cli.py:1799`) and D-8, *which
  release owns it*, is still unanswered.
