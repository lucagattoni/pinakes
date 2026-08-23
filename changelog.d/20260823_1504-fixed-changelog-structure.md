- **`CHANGELOG.md` carried a repeated section heading and two entries that were not entries.**
  `## [0.28.3]` had `### Fixed` twice consecutively, and its body — like one `### Changed` body
  further down — was a bare paragraph rather than the `- **claim.**` bullet
  [`changelog.d/README.md`](https://github.com/lucagattoni/pinakes/blob/main/changelog.d/README.md)
  requires. Both are structural, both render as something other than what was meant, and
  `python3 tools/fragments.py --check` exits `0` on both — **it validates pending fragments, never
  the document it splices them into**, so nothing in this repo has ever read the assembled file.
  The prose is unchanged: the duplicate heading is removed and the two bodies are bulleted, with
  their continuation paragraphs indented. Found while checking a release precedent, not by a gate.
