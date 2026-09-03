- **A repaired document stops being reported as failed, and `pnk doctor`'s remedy is no longer
  false.** Nothing ever deleted from the `failures` table, so a document the user fixed and
  re-indexed stayed listed forever — `doctor` insisting it *"is not searchable"* while `pnk search`
  returned it, under the advice *"Fix them and re-run `pnk sync`"*, which is exactly what the user
  had just done. It also never de-duplicated: three syncs of one broken document left three rows,
  so the count reported was a count of *attempts* wearing the clothes of a count of problems. The
  table now answers *what is wrong with this KB now*. A document that indexes cleanly clears its
  own entry, a removed one takes its entry with it, and a document held because it is **unreadable**
  keeps its entry — nothing about it was verified this run, so its recorded failure is still the
  last honest thing anyone knew about it.
