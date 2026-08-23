- **`tools/fragments.py --check` now reads the document `--apply` writes, not only the fragments
  going into it.** It parsed every pending fragment and asserted nothing about the result, so a
  splice could leave `CHANGELOG.md` malformed with every gate in this repository green — and had:
  `## [0.28.3]` carried `### Fixed` twice consecutively with a bare paragraph for a body, and one
  `### Changed` further down did the same, all three passing `--check` with exit 0. Two rules on
  the assembled document: a heading never repeats consecutively (both streams), and an entry opens
  with a `- ` list item (`changelog` only — `retro.d/` is free-form prose carrying its own `##`).
  Run against the unrepaired document the gate reports exactly those three and exits 1; against
  `main` at 0.30.0, zero. `--apply` validates the spliced text **before** writing it and therefore
  before deleting the fragments it consumed, because a malformed document found afterwards is found
  with its cause already gone. Scanning skips fenced blocks and the fence may be indented — measured
  20260823, `CHANGELOG.md`'s only fenced block sits two spaces inside a bullet and the file has no
  column-zero fence at all, so the first draft skipped nothing in the document it most needs to
  read. Closes the open-corrections item opened at 0.30.0.
