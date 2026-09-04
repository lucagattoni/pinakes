- **`pnk doctor` no longer reports `none` about a paid document it could not read.** On Python
  3.14, a paid-extracted document that had become unreachable — moved behind a directory the
  process may not traverse, or reached through a symlink into one — was silently dropped from
  *both* `paid extraction stale` and `paid extraction unreadable`, so the health check answered
  `none` for a document whose staleness nothing could decide. It is now named under `paid
  extraction unreadable`, with the `chmod +r` remedy, which is what Python 3.13 already did.
