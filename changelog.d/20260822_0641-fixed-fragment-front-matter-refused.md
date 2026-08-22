- **A changelog or retrospective fragment that opens with a `---` front-matter fence is refused.**
  The category has always lived in the filename, so a fence inside a fragment was inert and nothing
  objected to it — while `--apply` spliced it into the target document verbatim. Three fragments
  written for 0.24.0 did exactly that, and all three fences are still published in `CHANGELOG.md`.
  Only the *opening* fence is refused: a `---` further down a body is a horizontal rule, and bodies
  are spliced unchanged by design.
