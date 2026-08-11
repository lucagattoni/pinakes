- **`pnk upgrade --apply` records the new template reference when the two versions render an
  identical manifest.** A template bump touching only files the manifest does not contain — its
  README, its starter golden set — produces no hunks, and `--apply` used to do nothing at all on
  that outcome, **the `[kb] template` restamp included**. The KB went on recording the old
  reference, `pnk doctor` went on warning, and no command existed that could clear it. Reachable
  rather than theoretical: of the ten commits between `notes@1.0` and `1.1`, five touched only the
  golden set. `--apply` now records the reference and changes nothing else, and **says so before it
  writes** — the same consent path a `[budget]` change already takes. `pnk upgrade` without
  `--apply` still writes nothing, on this outcome as on every other.
