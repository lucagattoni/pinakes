- **A sync that fails on a rename cycle no longer leaves a document retired behind it.** Renaming
  two documents past each other, or in a chain, made `pnk sync` plan a soft delete for an id it also
  adopted; the plan's outcome then depended on which action was applied last. The index was left
  with one document retired and another describing the wrong file, while `pnk doctor` reported
  every row OK. The cycle itself still fails — `documents.path` is UNIQUE and two adoptions cross —
  but it now fails with the index untouched rather than partly rewritten. `pairing` decides whether
  an id is ending or moving from the whole walk, before anything is applied, which is also what
  stops a rename chain re-minting an id its sidecar already carried.
