---
category: changed
---

**The default `[budget]` caps rise so `pnk ask --deep` works out of the box**: `per_operation_eur`
0.30 → 2.00 and `daily_eur` 1.00 → 6.00, with the new `[deep] max_rounds` defaulting to 3. At the
shipped widths even a one-round loop prices at EUR 0.5624, so the old cap refused `--deep` on every
KB stamped from the template. `daily_eur` moves with `per_operation_eur` because all three windows
are checked before every call and nothing warns that a lower one binds. The `notes` template is
version **1.2**, and `pnk upgrade` will report the change — **an existing KB keeps the caps it
stamped**, and the refusal names the key, the number and the value that would admit the run.
