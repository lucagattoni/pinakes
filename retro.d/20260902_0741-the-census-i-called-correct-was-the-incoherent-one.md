## The census I called correct was the one mixing selectors (20260902 07:41)

Reviewing a branch's commit messages, I raised that `6bc8078` had replaced a correct census with a
false one: an earlier pass had written *"28 of the tree's 30 battery sections carry the prefix"*, and
the later commit said 27, of which 19 and 8. I filed it as a regression — a right number made wrong.

The coder re-measured and refuted it, and I re-derived it independently rather than accept the
refutation on report. At `5329d24^`, over 11 battery files: counting sections delimited by box-drawing
`# ────` rules gives **30 total, 27 carrying (19 + 8), 3 not**. Also accepting ASCII `# ----` rules
gives **32 total, 28 carrying, 4 not**.

So `6bc8078` is exactly right under the strict selector. The sentence I called correct — *28 of 30* —
is the one that matches **no selector at all**: its 28 comes from the loose count and its 30 from the
strict one. I had promoted an incoherent pair over a coherent one because the incoherent pair was
older, and "a later commit changed a number" is a shape that reads as regression before it is checked.

**Neither census stated its selector, and that is the whole defect** — the same one I had landed a
retro fragment about ninety minutes earlier: *A method is not a measurement point, and `--all` is not a corpus*
(`#a-method-is-not-a-measurement-point-and---all-is-not-a-corpus-20260902-0245`).
I wrote the rule and then failed to apply it to the very next thing I looked at, in a review whose
purpose was to catch exactly this.

Why the selector is load-bearing here rather than pedantic: the coder found
`tools/batteries/src-pinakes-pairing.toml:369` uses ASCII rules, and across `tools/batteries/` there
are **56 box-drawing rules against 6 ASCII**. A `─`-delimited census is therefore structurally blind
to that file. The two counts are not rounding of one another; they see different trees.

**The rule this leaves:** when two measurements of one set disagree, do not assume the older is the
baseline. Ask which selector each used first — the disagreement is usually the population, not the
arithmetic, and the number that survives is the one whose selector was stated.
