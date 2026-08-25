- **`pnk init` now asks git whether `.pinakes/` is really ignored, instead of searching the
  `.gitignore` for a string.** The old check was `".pinakes/" not in gitignore.read_text()`, and a
  substring test is not git's ignore semantics: measured 20260825, it was wrong in **both**
  directions. It warned about `.pinakes` and `.pin*`, which git does ignore — and it stayed
  **silent** for `!.pinakes/` and for a commented-out `#.pinakes/`, which git does not. The silent
  half is the one that cost something: the string is present in a commented line, so it read as
  protection, and `.pinakes/` — the index, the spend ledger and every deep transcript, which is
  the first thing under `.pinakes/` to hold your **verbatim question** — was left tracked with no
  warning at all. Commenting a line out to debug something and re-running `init` is enough to
  reach it. The question is now put to `git check-ignore`, and it is asked as *is an **arbitrary**
  path under `.pinakes/` ignored* rather than *are these files ignored*: the probes are opaque
  random paths that only a rule covering the directory itself can match, with two more under
  `cache/extract/` and `deep/`. Asking about named files instead would have been its own defect —
  an ordinary `.gitignore` carrying `*.db` and `*.json` ignores every file the first draft probed
  while leaving `index.db-wal` tracked, and in WAL mode that holds megabytes of verbatim document
  text. Outside a git repository the same probes run against a throwaway repository holding your
  `.gitignore`, so there is one definition of the answer rather than two that can disagree; only a
  machine with no `git` at all falls back to reading the file, and it then asks whether a whole
  line names the directory rather than whether the string appears somewhere in it. The check still
  fires only for a `.gitignore` that was already there, as it always did. Whether `pnk doctor`
  should re-check this on every run, and whether that is a warning or a note, is untouched and
  still undecided.
