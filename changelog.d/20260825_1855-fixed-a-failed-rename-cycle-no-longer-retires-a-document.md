- **A sync no longer plans one document's id into two places at once.** Renaming two documents past
  each other, renaming them in a chain, or moving one document's sidecar onto another all made
  `pnk sync` build a plan that both kept an id where it was and carried it somewhere else. Which
  half won depended only on which action was applied last: a document could leave `pnk search` with
  nothing recorded and the command exiting 0, and a rename chain could re-mint an id its sidecar
  already carried. `pairing` now decides whether an id is ending, staying or moving from the whole
  walk before anything is applied, so no plan retires an id it also adopts and no plan places one id
  at two paths. **Renaming two documents past each other still fails** — `documents.path` is UNIQUE
  and two adoptions cross — and that is left to its own fix; what changed is that the plan reaching
  the database is no longer self-contradictory.
