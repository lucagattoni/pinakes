- **A sequence permitted to lag may now be at most two releases behind.** The ceiling for a lagging
  sequence was that sequence's own newest entry — an echo of the document being checked — so deleting
  its newest paragraph dropped the ceiling with it and the deletion hid itself. That is the defect
  refused at the *lower* bound (a derived start) surviving four lines away at the upper one.
  `MAX_VERIFICATION_LAG = 2` is declared, not derived: *verify the artifact, never the run status* is
  the rule STATUS's *Published on PyPI* list exists to record, so two behind is one unverified cut
  plus one slip, while three means verification has stopped happening. The failure names **both**
  causes and picks neither, because an entry deleted and an entry not yet written are
  indistinguishable from the documents. **What it buys, exactly:** not detection of a deletion, but a
  bound on how far the echo can drift silently — at a legitimate lag of 1, one deletion is still
  invisible.
