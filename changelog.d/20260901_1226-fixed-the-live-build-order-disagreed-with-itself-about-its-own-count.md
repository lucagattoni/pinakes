- **The live build order disagreed with itself, four hours after it landed.**
  [`plans/20260901_1148-clear-the-user-facing-list.md`](https://github.com/lucagattoni/pinakes/blob/main/plans/20260901_1148-clear-the-user-facing-list.md)
  stated the number of pending fragments five times and no two agreed: its own measurement M5 said
  11, row 3 said 15 twice, 10 once and 5 once, and the tree held 16. The cause was structural rather
  than careless — **M5 was keyed to `HEAD` while M1–M4 each named a sha**, so the one measurement
  that moves with every landing was the one nothing pinned, and row 3 restated its numbers instead of
  citing it. M5 now names `9cc9bc1`, row 3 cites M5 and restates nothing, and a clause that conflated
  "`retro.d/` fragments" with "records of 20260901" is now the quantity it meant. Also fixed in the
  same file: a sentence beginning *"That expectation"* whose antecedent had been deleted in review,
  and an unescaped `|` inside a code span in the M3 row, which GFM reads as a column delimiter and
  which split that row. **And § 6's table of decisions owed by the user was wrong in three of its
  four rows**, none of which had been checked against anything: `pnk adopt` was said to appear in no
  top-level routing document when `docs/README.md` names it; the `fable` clause was carried as
  *reported done, verify* when it has been present in that file all along; and the
  `--autocompact 150000` row is named for a flag that does not exist, against a live setting
  (`autoCompactWindow`) that reads twice that number. A table of open questions had itself gone
  unread.
