## The ungated Markdown surface, and two checkers that were confidently wrong (20260823 14:36)

**HIGH — a checker with no control leg reports plausible nonsense, and reads as authoritative.**
The first draft of `tools/markdown_link_gate.py` reported **82 broken links inside `docs/`** — a
surface `mkdocs build --strict` guarantees is clean. The cause was a one-flag mistake: inline code
spans were blanked with `re.S`, so in `docs/ROADMAP.md` (2616 backticks, zero fences) a single
unbalanced backtick swallowed every heading after it. Nothing about the output looked wrong —
missing anchors, real filenames, plausible slugs. It was caught **only** because the scan was run
over a corpus whose correct answer is known independently of the checker. Run a new checker against
a surface something else already guarantees, before believing anything it says about the surface
nothing guarantees.

**HIGH — a control leg validates only the behaviours its corpus exercises.** A peer wrote an
independent scanner over the same surface and got 18 where this one got 12. All six extras were
its bug: it resolved targets with `Path.is_file()`, so every link to a *directory* failed —
`docs/graph/`, `../plans/`, `../retro.d/` — each correct as authored, since GitHub renders a
directory link as a listing. Its control leg over `docs/` stayed **green** throughout, because
that corpus contains no directory links. So the two lessons are halves of one: a checker with no
control reports nonsense, and a green control certifies only what it covered. Both instruments
were wrong, in different directions, and each was found by something the other did not do.

**HIGH — a false positive gets acted on, so the skips matter as much as the catches.** The count
was reported as twelve and was **eleven**. `retro.d/README.md:37` sits in a four-space **indented
code block** — neither this checker nor the peer's stripped those — and it is the README's own
example teaching fragment authors which anchor form to write. The peer repointed it before reading
what the block was for, turning an instructional example into one that teaches the *wrong* form,
then reverted. Nobody argues with a false positive the way they argue with a false negative; they
fix it, and the fix damages the document. **A link checker's skip list is a correctness surface.**

**HIGH — when a cheap instrument is suspect, do not argue about it: render, and measure the gap.**
The right response to "a regex cannot parse Markdown" was not to defend the regex or to take the
dependency, but to build the renderer once as an **oracle** and compare. Python-Markdown over all
114 tracked files emits 894 links; the extractor now finds every one of them and invents **zero**,
the single difference being a bare `<https://…>` autolink that is external and never resolved
anyway. That measurement is what licenses staying stdlib-only — `./check.sh` and the CI job need no
install and no network — and it is kept as a test that runs wherever the docs toolchain is present
and skips with its reason where it is not. The argument was unresolvable; the measurement took one
command.

**MEDIUM — a false negative is the failure mode a link checker actually has.** The second bug in
this one forbade newlines in link text, which silently skipped every link whose text wraps — in a
repository that wraps prose at 100 columns, and where `CLAUDE.md` wraps seven of them. A false
positive gets argued with; a false negative is a clean bill nobody earned. The control leg cannot
see it, because a control proves the absence of false positives only. The gate therefore counts the
link syntax it saw and **fails on anything it could not parse**, rather than skipping it.

**MEDIUM — the two documents most worth gating are the two the gate cannot fix.** All eleven
findings sat in planner-owned files (`CHANGELOG.md`, `plans/`, `retro.d/README.md`), so the gate
was buildable and the defects it found were not — by the same ownership rule that makes the split
work. Coordination, not escalation: the findings went over as a list with evidence and line
numbers, and the fixes landed on the other side of the boundary while this branch built the gate.

**LOW — six of the eleven were quotations, and that is a design constraint rather than noise.**
`plans/20260807_2143-docs-audit-findings.md` quotes other documents' links verbatim; they are
correct relative to `docs/` and dead relative to `plans/`, and *correcting the path would falsify
the quotation*. A gate that flagged them could only be satisfied by corrupting the quote. Code-span
a quoted link and it is inert — which the audit file already did in one place before anyone asked.
