- **`tools/markdown_link_gate.py` resolves a fragment's links from the document its body is spliced
  into**, not from the directory the file sits in. `retro.d/` and `changelog.d/` are consuming
  directories, so every link in a fragment has two resolutions and only the second one is published
  — and they disagree in exactly the case both fragment READMEs forbid. `[x](20260902_0245-….md)`
  names a real sibling inside `retro.d/` and a file that never existed inside `docs/`. **That form
  reached `main` twice on 20260902** (`2fd47bc` 07:44, `394939d` 08:03 UTC) and would have failed
  the next release build; nothing saw it, because no pre-splice instrument could. The gate is now
  red on the branch instead.
- **A `#…` anchor into a sibling fragment's heading is accepted**, which is the form both READMEs
  prescribe and the form the gate used to refuse. The anchor universe is the destination document's
  headings plus every pending fragment's; a slug two files both contribute is **refused** rather
  than guessed at, because the anchor the site generates would depend on splice order. The
  instruction to degrade these links to code spans is withdrawn from both READMEs, dated rather
  than overwritten, and the four links written under it are restored.
- **The two streams splice to different depths, and the gate knows it.** A retro fragment lands in
  `docs/RETROSPECTIVES.md`; a changelog fragment lands in `CHANGELOG.md` at the repository root. So
  `../docs/DESIGN.md` is correct from inside `changelog.d/` and climbs out of the repository once
  the body has moved.
