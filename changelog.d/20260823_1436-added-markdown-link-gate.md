- **Every relative link and heading anchor now resolves in the Markdown the docs site never sees.**
  `mkdocs build --strict` resolves internal links, and it was the only thing that did — it reads
  `docs/` alone, and `exclude_docs` drops `docs/README.md` even from that. `CLAUDE.md`, the root
  `README.md`, `CHANGELOG.md`, all of `plans/`, the `changelog.d/` and `retro.d/` READMEs and the
  routing table itself were checked by nothing, and held **eleven broken links** when measured —
  five dead as authored, including three in `CHANGELOG.md` pointing at `../docs/…` from the
  repository *root*, which resolves above the repository. `tools/markdown_link_gate.py` runs in
  `./check.sh` and in its own `ci.yml` job; it is stdlib-only, so the CI job needs no `uv` and no
  install. A link inside a code span or a fenced block is never resolved, so a document that
  **quotes** another document's links is not asked to corrupt the quotation to satisfy the gate.
