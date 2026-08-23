## The ungated link surface, and three instruments that lied (20260823 14:38)

**HIGH — a regex cannot gate Markdown links, and both agents on this repo built one first.** The
coder's first scan reported 82 broken links inside `docs/`, a surface `mkdocs --strict` guarantees
clean; it had blanked inline code with `re.S`, so one unbalanced backtick in a 2 616-backtick file
swallowed every heading after it. Mine then reported 18 where the true number was 11 — twice, for
two different reasons. **Rendering answers the question directly: if a link is inside a code span
the parser emits no `<a>` at all.** No stripping, no heuristics, no reimplementation of block
parsing. The final instrument is `markdown.markdown()` plus this repo's own `_github_slugify`, run
through the same `uv run --no-project --with-requirements requirements-docs.txt` invocation
`make docs` uses, so it cannot drift from the site.

**HIGH — a control leg validates only the behaviours it exercises, and a green one is not a clean
bill.** The coder's control caught its `re.S` bug. Mine did not catch either of mine: 485 links
across `docs/`, zero broken, green — while the instrument was wrong twice. `docs/` contains no
links to a *directory*, so `Path.is_file()` rejecting `docs/graph/` and `../plans/` was never
exercised; that produced six false positives. And `docs/` has no indented code block containing a
link, so treating one as prose was never exercised either. **The second false positive produced a
wrong edit before it was caught**: `retro.d/README.md:37` sits in a four-space block and is the
README *teaching fragment authors what to write* — a bare `#anchor`, which resolves only once the
fragment is spliced into `docs/RETROSPECTIVES.md`. It was repointed at `../docs/RETROSPECTIVES.md`
before the surrounding prose was read, turning an instructional example into one that teaches the
wrong form. Reverted. **Read what a line is for before fixing what a tool says about it.**

**MEDIUM — an adversarial pass that overturns nothing has said nothing.** Re-verifying the
20260807 audit's 39 findings against `c45ffa8` ran eleven agents plus an adversary per cluster,
each prompted to refute every *already fixed* verdict, since that is the direction that silently
drops a verified defect. **The adversary overturned zero. Hand-checking all seven afterwards found
one false**: `docs/DESIGN.md:711` asked to drop two phrases and only one had gone — *a manifest and
a template drift silently* still stands while `doctor.py` prints the drift it denies. The adversary
was prompted for exactly that shape, *corrected in one place while an equivalent claim survives*,
and upheld it anyway. **A zero from a checker is a claim about the checker.** The same pass also
corrected two predictions made from reading the code without reading the document: `DESIGN.md:715`
and `KB-UPDATES.md:24` were called *more wrong than before* on the grounds that `pnk upgrade` had
since shipped, when both had in fact been rewritten and are genuinely fixed.

**MEDIUM — `mkdocs --strict` is a link gate, not a rendering gate.** It resolved every link in
`docs/RETROSPECTIVES.md` for weeks while one of its lines rendered as a broken run of `<code>` tags
on the published site. The defect class — a backslash-escaped backtick inside a code span, which
CommonMark does not honour — produces *valid* HTML that is simply not the HTML anyone intended, so
nothing that checks structure can see it. Catching it needs a rendering comparison, which is a
different check from link resolution and was found only because a link fix forced the line through
a parser.
