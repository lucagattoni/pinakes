- **`pnk init` now asks git whether `.pinakes/` is really ignored, instead of searching the
  `.gitignore` for a string.** The old check was `".pinakes/" not in gitignore.read_text()`, and a
  substring test is not git's ignore semantics: measured 20260825, it was wrong in **both**
  directions. It warned about `.pinakes` and `.pin*`, which git does ignore — and it stayed
  **silent** for `!.pinakes/` and for a commented-out `#.pinakes/`, which git does not. The silent
  half is the one that cost something: the string is present in a commented line, so it read as
  protection, and `.pinakes/` — the index, the spend ledger and every deep transcript, which is
  the first thing under `.pinakes/` to hold your **verbatim question** — was left tracked with no
  warning at all. Commenting a line out to debug something and re-running `init` is enough to
  reach it. `git check-ignore` is now asked about the three paths the warning is actually about,
  and every one of them must be ignored: `check-ignore` exits 0 when *any* argument matches, so a
  rule naming only the ledger would otherwise read as full protection while the index stayed
  tracked. The probes are paths *inside* the directory rather than the bare `.pinakes`, because
  `git check-ignore .pinakes` reports *not ignored* for the canonical `.pinakes/` pattern whenever
  the directory is absent from disk — and at `init` time it always is. Outside a repository, where
  there is nothing to ask, a deliberately small fallback asks whether a **whole line** names the
  directory, with or without its trailing slash. Whether `pnk doctor` should re-check this on
  every run, and whether that is a warning or a note, is untouched and still undecided.
