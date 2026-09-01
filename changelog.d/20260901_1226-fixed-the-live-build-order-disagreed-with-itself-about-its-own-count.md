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
  which split that row.
