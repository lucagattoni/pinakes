- **A partner KB you cannot read is no longer reported as one that does not exist.** `pnk doctor`,
  `pnk link` and `pnk sync`'s link scan all described a linked KB sitting behind a directory this
  process may not traverse as `no such directory` — the identical wording they use for a partner
  that is genuinely gone, and the one answer a user can check and find false. All three now name
  the permission (`cannot be read: Permission denied`), and a partner that really is absent still
  says so. On Python 3.13 the message was already correct, so this is 3.14 catching up rather than
  a change of behaviour.
