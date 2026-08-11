- **Corrected a claim published twenty minutes earlier.** The note on the wedged `docs` run stated
  as fact that a run stuck at `in_progress` **holds** `docs.yml`'s `concurrency: {group: pages}`, so
  the next `docs/` push would queue behind it. **The next push refuted it in four minutes** — it ran
  and deployed while the wedged run was, and still is, `in_progress`. The correction is kept in
  place rather than deleted because the shape of the error is the reusable part: a plausible
  mechanism stated as a consequence, inside a note whose own subject was the danger of trusting a
  status signal instead of checking one.
