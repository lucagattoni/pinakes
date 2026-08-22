- **The release-order gate reads STATUS's *Published on PyPI* prose — the sixth sequence.**
  `docs/RELEASING.md` named that list as one of the five places a release stales and said this gate
  decides where the new entry goes, while no pattern in the gate matched it: the procedure
  delegated the decision to a check that could not read the document. The list had been mis-ordered
  since 20260821 — `0.25.1 → 0.25.3 → 0.25.2 → 0.25.4`, wrong on SemVer *and* on verification time
  — through every green run since. Two supporting rules come with it: a sequence that began later
  carries **its own floor** (this one starts at 0.16.0), and this list **may lag** the release
  sequences, because an entry is held back until it has been verified from the index — but it may
  never **lead** them, which would claim the index has a release nothing else records.
