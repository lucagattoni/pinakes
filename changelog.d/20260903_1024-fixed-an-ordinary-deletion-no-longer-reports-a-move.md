- **Deleting a document no longer makes `pnk sync` claim it moved and was re-minted.** Every
  ordinary deletion printed *"moved without its sidecar, so a new id was minted: docs/x.md"* —
  three claims, all false, on the commonest operation there is: nothing moved, nothing was minted,
  and the path it named no longer existed. The hint is now gated on an **orphaned sidecar**, which
  is what actually separates a move from a deletion: delete a document properly and its sidecar
  goes with it, leaving nothing behind to report. The sentence itself no longer asserts a mint
  either, because the other half of a move need not arrive in the same run — deleting only the file
  and leaving the sidecar mints nothing, and is still a state worth reporting.
