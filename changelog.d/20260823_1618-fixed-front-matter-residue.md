- **Five blocks of front-matter residue were rendering as headings, two of them on the published
  site.** A splice long ago left `---` / `category: <x>` / `---` in the assembled documents. That is
  not inert text: `---` after a *blank* line is a thematic break, but after a *text* line it
  underlines that line into a **setext H2** — so each block rendered as a rule followed by a heading
  titled `category: added`, `category: changed` or `category: lesson`.
  `lucagattoni.github.io/pinakes` was serving two of them, with real permalink anchors, and
  `mkdocs build --strict` was green throughout: a spurious heading is not a broken link. Three in
  `CHANGELOG.md` under `## [0.24.0]` and two in `docs/RETROSPECTIVES.md`, all removed.
- **Three changelog entries had lost their bullet, and the residue was what had been separating
  them.** Each `---` block in `CHANGELOG.md` sat immediately before an entry body written as a bare
  paragraph, so deleting the residue alone would have run three entries together. They are restored
  as `- ` items with their continuations indented; no prose changed.
