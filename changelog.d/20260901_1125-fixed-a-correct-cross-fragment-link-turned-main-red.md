- **`main` is green again.** A cross-fragment anchor link in
  `retro.d/20260901_0713-the-rule-i-quoted-had-been-deleted.md` turned CI red at `b6be317` — 14 jobs
  green, one red. The link was **correct**: it targets a sibling fragment's heading, which resolves
  once `tools/fragments.py --apply` splices both into `docs/RETROSPECTIVES.md`, exactly as
  `docs/RETROSPECTIVES.md:4034` already links to `:3945` in that form with `mkdocs --strict` passing.
  `tools/markdown_link_gate.py` resolves a `#…` target against the fragment's own headings only, so
  it is red before splicing and green after. The link is code-spanned as an interim measure and
  restored when build-order row 14 teaches the gate the splice destination.
- **Both fragment READMEs now carry the caveat.** `retro.d/README.md` *instructs* writers to use the
  anchor form, and the first fragment to follow it literally broke the build; `changelog.d/README.md`
  repeats the instruction. Each now says to code-span the anchor until row 14 lands, with the
  measurement.
- **Four of the eight rows parked in `plans/20260825_1240-run-pinakes-sweep.md` were already done** —
  the docs audit, the `KB-UPDATES.md` §3 citations, the `test_review_pass_gate.py` rows and the
  `--questions` flag, two of them finished before the table was written. Each remaining row now
  carries a one-command liveness check to run before building it.
