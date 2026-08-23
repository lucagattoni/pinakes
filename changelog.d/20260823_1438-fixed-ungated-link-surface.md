- **Eleven broken links, and three code spans that render as wreckage, on the Markdown surface no
  gate reads.** `mkdocs build --strict` resolves every link in `docs/`, and `mkdocs.yml` excludes
  `CLAUDE.md` and `docs/README.md` by design because they point at `plans/`, `tools/` and
  `changelog.d/` — paths a site build cannot resolve. Nothing else in the repo resolves a link, so
  `CHANGELOG.md`, `plans/**` and the fragment READMEs were checked by nothing. `CHANGELOG.md`
  carried three links to `../docs/…`, which resolves *above* the repository root, and one anchor
  that rotted when a re-measurement renamed the heading it cited — 0.7.0's entry pointed at
  *measured 20260801 12:14* after that section became *yes, measured 20260804*. It is repointed
  rather than reworded, because `docs/STATUS.md` still carries both columns and the entry's own
  numbers are still on the page it names. `plans/20260729_0256-links-and-graph.md` cited a
  repo-root `STATUS.md` that has never existed. And six quotations in
  `plans/20260807_2143-docs-audit-findings.md` rendered as live links to paths that resolve only
  from `docs/`; they are now code spans, not repointed paths — correcting a path *inside* a
  quotation would falsify the quotation, and quoting verbatim is that document's whole method.
- **A backslash does not escape a backtick inside a code span, and three places assumed it does.**
  `docs/RETROSPECTIVES.md` is published, and one of its lines has been rendering as a broken run of
  `<code>` tags on the site for weeks — with `mkdocs build --strict` green throughout, because
  `--strict` resolves links and never asks whether a span renders as intended. Two siblings in
  `plans/` had the same defect. All three now use double-backtick spans, which is how CommonMark
  carries an inner backtick. Four other backslash-backtick uses in the repo are a code span holding
  a single backslash, are correct, and are untouched.
