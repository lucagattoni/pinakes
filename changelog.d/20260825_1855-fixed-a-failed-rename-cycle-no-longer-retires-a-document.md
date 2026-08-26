- **A sync no longer plans one document's id into two places at once.** Renaming two documents past
  each other, renaming them in a chain, or moving one document's sidecar onto another all made
  `pnk sync` build a plan that both kept an id where it was and carried it somewhere else. Which
  half won depended only on which action was applied last: a document could leave `pnk search` with
  nothing recorded and the command exiting 0, and a rename chain could re-mint an id its sidecar
  already carried. `pairing` now decides whether an id is ending, staying or moving from the whole
  walk before anything is applied, so no plan retires an id it also adopts and no plan places one id
  at two paths. **Renaming documents past each other still fails** — `documents.path` is UNIQUE and
  the adoptions cross — and that is left to its own fix. What changed is that the failure now costs
  nothing: on a pure rename, where nothing is added or deleted in the same sync, the index is left
  exactly as it was, measured across every one of the six ways three documents' names can be
  permuted. Previously the same input committed a retirement first and left a document soft-deleted
  behind the crash.
