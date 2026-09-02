## The one surface a later pass cannot fix is the one nobody reviews (20260902 07:34)

**MEDIUM — three pushed commit messages on this branch carry four false sentences between them, and
a commit message is the only artefact here that cannot be corrected in place.** Every review pass on this branch has
read the diff. Pass 9 read the *messages*, and found that the surface holding this increment's
reasoning — the surface a future reader reaches for when asking why a line is the way it is — had
never been checked by anything.

| commit | the sentence | measured |
|---|---|---|
| `0e424c7` | `markdown-links: 113 files, 375 links` | the gate on that exact tree says **114** files. The link count is right |
| `2914b09` | "All five test names they name resolve" | the three `docs/VERIFICATION.md` cells that commit added name **11** distinct tests |
| `2914b09` | "`startswith("## ")` shipped in eight of them and the pass-3 lookaround in three" | over the population it names — every commit from `50dd420` to `6bc8078` — **5** and **2** |
| `f1de4c1` | the mutant "is killed by the negative assertion rather than the positive one" | it dies at the **positive** one, `tests/test_fragments.py:1005`, and pytest never reaches the negative |

**And the pass that wrote this fragment put two more onto the same unfixable surface, within the
hour.** Both were caught by re-reading my own diff before landing, which is the only reason they are
here as a record and not as a fifth and sixth row somebody finds next week:

| commit | the sentence | measured |
|---|---|---|
| `f48e1cf` | the unclosed-`<div>` fixture renders "**one** `<h2>` where the source has four" | the source has **three** `## ` headings. The four is `anchors_of`'s count, which includes the `# ` heading — two instruments, one number, and I carried the number from the wrong one |
| `bc68475` | "four of them carry a false sentence", of commit messages | four *sentences* across **three** messages; `2914b09` carries two. The table underneath it has always been right, and the sentence summarising the table was not |

Neither is a hard number to check. Both were written in a commit whose subject is other people's
false counts, and both survived the writing of that commit. **A pass that is looking outward does
not look at itself**, and the cheapest defence found so far is a mechanical one: before landing,
re-read your own diff for every number in it and re-derive each, treating your own prose exactly as
you would treat a claim raised by a lens.

The fourth is the one with a lesson beyond arithmetic. **The false sentence was in the test's own
docstring first, and the commit message copied it** — *"The negative assertion is the load-bearing
one"*, written from reading the two assertions rather than from applying the mutant to them. Both
would fail against a stripped message; only the first one reached reports. So the claim was not a
slip made in a hurry at commit time: it was a plausible reading of the code that nobody executed,
duplicated into a surface where it could no longer be edited. The docstring is corrected in this
increment; the commit message is not correctable.

The third is the sharpest, because it was *corrected once already and not by that route*. `04497a9`
replaced the selector — "every commit from `50dd420` to `6bc8078`" was a range nobody had examined —
and re-measured over full history, getting 4 and 1. It never re-derived 8 and 3 over the original
population, so it left a false pair standing while reporting that it had fixed the sentence
containing them. **Replacing a claim's population is not checking its numbers.** Three populations
here, three answers — 8/3 written, 5/2 true for that population, 4/1 true for the one that replaced
it — and only the first is wrong.

**LOW — and one of the thirteen findings did not survive being checked, which is the reason the rule
exists.** A reviewer reported that `6bc8078` had replaced a *correct* census — pass 5's "28 of the
tree's 30 battery sections carry the prefix" — with a false 27/19. Measured at `5329d24^`, the tree
pass 5 was describing: **30 sections, 27 carrying** (19 `unreleased, YYYYMMDD ·` and 8 `X.Y.Z ·`).
`6bc8078` was right. Pass 5's 28-of-30 is the pair that matches no single selector.

**And the reason it matches none is a section every census so far has silently dropped.** Count a
section as a comment line sandwiched between two `# ─────` rules and there are 30. Accept ASCII
hyphens as rule characters too and there are **32** — because
`tools/batteries/src-pinakes-pairing.toml:369` draws its rules with `-` and writes
`# unreleased, 20260831 - S16's residue…`, a hyphen where the convention has `·`. It is
non-conforming twice over, it predates this branch, and **it is still non-conforming at this
branch's tip**. Under the loose selector the pre-fix tree reads 28 of 32. So pass 5's *28* is right
about one population and its *30* about the other, and the two numbers in one sentence come from
two different questions.

**This is one class with the fragment landed beside it, not two.** `retro.d/` also carries *A method is not a measurement point, and `--all` is not a corpus*
(`#a-method-is-not-a-measurement-point-and---all-is-not-a-corpus-20260902-0245`),
written the same night about the same defect — a number stated without the selector that produced
it. Read them together: that one names the rule, this one is the rule failing in the hands of the
reviewer applying it.

This started as a bare path in prose, because when it was written the branch was twelve commits
behind the file it cites and a link would have been red on its own gate. Green at the moment of
landing beat the better reference. It is a link now that both are on `main`, and the reason is not
tidiness: `tools/markdown_link_gate.py` reads `retro.d/`, so **a path in prose is unchecked text
and a link is a gated reference** — this one goes red if either fragment is ever renamed, and the
prose version would have gone quietly stale. Ruled by the planner.

**The lesson is not "measure more".** All three parties — the writer, the corrector, and the
reviewer who called the correction wrong — ran a count. Each ran a *different* count and none said
which. **A census of a corpus with two spellings of its own delimiter has two answers, and the one
you get is chosen by the regex you happened to write.** Naming the selector is what makes two
measurements comparable; it is also what makes a disagreement resolvable instead of a standoff.

**What to do about a false sentence that is already pushed.** It cannot be amended — the branch is
shared and the sha is cited in this fragment and in `docs/VERIFICATION.md` rows. So the correction
lives here, in the retrospective, which is the only append-only record of the same events. That is
weaker than a fix and it is what is available. The stronger move is upstream: **a commit message
asserting a count is asserting something checkable, and nothing on this branch checked one until the
ninth pass.** Reading the message alongside the diff costs one command and would have caught all
four before they were pushed.
