## A fixture named for a scenario it did not build (20260903 10:24)

**HIGH — a test can be green, correctly named, and modelling a different world.** S6 — `pnk sync`
announcing *"moved without its sidecar, so a new id was minted"* on every ordinary deletion — was
covered by a test called
`test_rename_plus_edit_without_the_sidecar_is_reported_as_such`. The name is accurate about the
intent. The fixture passed `()` for the walk's sidecars.

A file moved without its sidecar leaves **two** halves on disk: the new path carrying no sidecar,
and the old path's sidecar carrying no document. Passing no sidecars at all models something else
entirely — a file moved *and* its sidecar deleted, which is indistinguishable from deleting one
document and creating another. The test therefore asserted the hint fired in a state where firing
is wrong, and it passed, because the code fired the hint on **every** vanished path. The fixture
and the defect agreed with each other, and the agreement read as coverage.

**The check that would have caught it is not "is this tested?" but "does the fixture build the
state the name describes?"** Two seconds of reading the scenario against the assertion, which is
the reading nobody does on a green test.

**The same increment showed the second half of it.** Nothing anywhere asserted the *sentence*
`pnk sync` prints for this case — the pairing tests pinned the predicate and stopped there, so the
gate could have been fixed in `pairing.py` while `sync.py` went on printing the false sentence, and
every test would have stayed green. **A predicate and the words it produces are two surfaces, and
pinning one is not pinning the other.** Both are pinned now.
