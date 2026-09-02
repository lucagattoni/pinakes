- **A measurement behind a live ruling was taken over the wrong population, and is corrected
  wherever it was written.** The build order's row 14 justified what a retro fragment's *second*
  `## ` heading owes by counting fragments that carry one. It reported **116 fragments, exactly
  one**; the real figures are **129 paths and 239 distinct versions, of which two**. The count had
  been taken over the live `retro.d/` directory, which every release empties by splicing into
  `docs/RETROSPECTIVES.md` — so it described the fragments written since the last release, not the
  corpus the ruling reasoned about. The pending changelog entry carrying the same number is
  corrected with it. **The ruling is unchanged:** the second of the two fragments stamps neither of
  its headings, and is not a pre-convention artefact to set aside — 10 of 126 fragments have an
  unstamped first heading, scattered to 20260831 — so it is ordinary non-compliance and licenses
  nothing. One deliberately-stamped instance still licenses the existence of a later stamp and not a
  monotonicity rule.
- **The Markdown link gate and the renderer that builds the site disagree about what a heading is,
  in four shapes of five** — rowed, not yet fixed. `tools/markdown_link_gate.py` matches headings
  with CommonMark's up-to-three-leading-spaces rule; Python-Markdown, which renders the site,
  refuses even one. So ` ## x`, `  ## x` and `\t## x` give the gate an anchor the site never
  renders — a link to one **passes the gate** and resolves to nothing — while `##x` is a real
  heading the gate cannot see, so nothing may link to it. Inside `docs/` this is caught by
  `mkdocs build --strict`; outside it, in `CLAUDE.md`, `plans/`, `changelog.d/` and `retro.d/`,
  nothing catches it — and those files are the gate's entire stated reason to exist.
