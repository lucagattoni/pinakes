- **`tools/deep_reservation.py report` could print a plausible wrong factor and say nothing.** A
  ledger call left *unresolved* — reserved, with neither a reconciliation nor a void — is priced at
  its **reservation** by `Call.effective_eur`, which is right for a budget guard and wrong for a
  measurement: it landed in a column headed `spent`. Deleting one reconciliation line from the real
  measurement ledger moved the published synthesis figure from **29.75× to 4.40×**, silently, at
  exit 0, while `pnk budget` on the identical ledger warns loudly about exactly that money. The
  report now counts how each call settled, marks an unsettled branch, and says how to close it —
  and a *voided* call stays settled, because it is closed at zero for never having billed. Three
  more in the same pass: an unreadable transcript aborted the whole report rather than being
  skipped, losing every other run's reconciliation after the money was spent (reproduced with a
  truncated file, a zero-byte one, a top-level JSON list, and a macOS AppleDouble sidecar that
  `transcript.paths()` globs); the fallback branch name was the literal `"unknown"`, which is a
  *real* branch, so stray JSON was folded into the uncalibrated loop's published statistics; and
  the "defensive" reads were neither, silently truncating `"calls": 3.9` into a published call
  count. **The tool now has 27 tests, mutation-verified 10/10**, having had none at all.
