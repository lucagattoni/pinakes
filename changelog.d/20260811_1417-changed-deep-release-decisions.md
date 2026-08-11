- **All eight of the deep release's open decisions are taken** (D-21 to D-28, 20260811 14:17), so
  its plan is now a build order rather than a question list and **E1 is buildable**. The two that
  shape the rest: **confidence sizes the work, it does not authorise it** — `pnk ask --deep` always
  answers, and a question the free path is already confident about costs **one** synthesis call
  instead of a decomposition loop; and **an uncalibrated KB runs anyway**, bounded by the round cap
  and `per_operation_eur` rather than by the absent signal, with the output naming which bound
  ended the run. Also settled: bare `pnk ask` never spends, one model rather than two, a
  budget-halted run follows the existing `[budget] on_exceed`, the transcript lives at
  `.pinakes/deep/<operation_id>.json` protected like a paid cache entry, suggestions are printed
  now and written later, and `--deep` accepts every `pnk search` filter.
