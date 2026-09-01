## I broke the table I was adding a row to, twice in one day (20260901 20:36)

**A row appended before the right anchor is not in the table.** I inserted two rows immediately
before the paragraph that follows the § 3 build order — which put them **after the blank line that
ends the table**. Markdown then reads them as a second, headerless table. The rows were correct, the
cell count was correct, every pipe was escaped, and the result rendered as two tables where the
build order is supposed to be one.

**What caught it was counting, not reading.** `awk` over the section printed a line number for
every table row: `…168, 169, 171, 172`. The gap at 170 is the whole finding. Reading the file would
not have shown it — a blank line between two table rows looks like nothing, and both halves render.
The check that works is *is the sequence contiguous*, which is a property of the sequence and not of
any row, and every check I habitually run reads rows.

**That is the second table-structure defect here today and the first had the same shape**: an
unescaped `|` inside a code span in a measurement row, where GFM splits cells *before* inline
parsing, so a pipe inside backticks still ends a cell. Both are invisible to a reader, invisible to
the link gate, invisible to `mkdocs build --strict`, and fatal to the thing the table is for.
**Nothing in this repository checks that a table is well-formed** — not `check.sh`, not CI. The
counting one-liner is not a gate; it is what I happened to run.

**And the file this happened in is the plan about registers decaying.** Its own § 0 note records
that a register decayed inside the plan about registers decaying, within four hours of landing. This
is the same file, six hours later, decaying structurally rather than numerically while I added a row
ruling how careful other people should be with headings.

**Postscript, same hour, worse.** Ruling on that table's row 15 I told the coder to write
`unreleased, 20260823 ·` into a battery section. The gate it describes **shipped in 0.30.0** — the
coder checked, refused the instruction, and gave me the ancestry. I re-derived it rather than accept
it: `v0.30.0` is the earliest tag containing `6d7c9e3`, and `v0.29.0` is not, so the selector
discriminates. My instruction would have written *unreleased* over a released property in the one
file whose job is recording which release shipped which property.

**I had the convention in front of me and read the wrong half of it.** `tools/batteries/README.md`
says sections *name the release that shipped the property*, and only unshipped work says
`unreleased, YYYYMMDD`. The bare date `20260823` is raw material for both spellings, and it reads as
unreleased-ish precisely because the unreleased form is the one that carries a date — the version
form carries none. That is the coder's observation, and it is the useful part.

**The rule I take from it:** a non-conformance does not tell you which conforming form it should
have been. I inferred the target from the shape of the defect instead of from the fact — and the
fact was one `git merge-base --is-ancestor` away, in a repository whose standing rule is that a
peer's claim is not evidence until checked. The peer checked mine.
