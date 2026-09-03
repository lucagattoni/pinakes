# Retrospective fragments

One file per increment's retrospective, spliced into `docs/RETROSPECTIVES.md` at release time by
`python3 tools/fragments.py --stream retrospectives --apply`.

Same reason as [`changelog.d/`](../changelog.d/README.md): every increment writes to this document,
so it is one of the two files most likely to be edited twice in an hour.

## Naming

    retro.d/YYYYMMDD_HHMM-<slug>.md

`YYYYMMDD_HHMM` is when the fragment was written, **UTC** — **read the clock, never compose it**
(`date -u "+%Y%m%d_%H%M"`). Fragments written before 20260804 11:32 carry a local time and keep it.
Same prefix as `changelog.d/`, plans and branches; `tools/fragments.py`
strips it before reading the slug.

The slug is lowercase-with-hyphens, with no category prefix — a retrospective is free-form prose
rather than one of a fixed vocabulary. Name it for the increment:
`retro.d/20260729_0336-i7d-recorded-fixtures.md`.

## Contents

The whole section, including its own `##` heading with the timestamp the file's own rules require:

    ## I7d — Recording the fixtures (20260729 03:36)

    **HIGH — …**

**The heading's stamp is a *copy* of the filename's prefix — one reading of the clock, written
twice.** Not a second reading, and not the time you finished writing: `20260729_0336-` and
`(20260729 03:36)` are the same four digits by construction. **Composing it instead is the failure
this rule exists to stop**, and it is not a rounding error — on 20260826 three headings were typed
from memory in one morning, out by 1 minute, 2 minutes and **3 hours 30 minutes**, in fragments
whose own subject was measurement discipline. The largest drifts furthest precisely because nothing
prompts you to look. **`date -u "+%Y%m%d_%H%M"` once; paste it into both places.**

**The opening is `## ` exactly — two hashes, one space, and nothing before them.** `python3
tools/fragments.py --check` refuses anything else. The three near misses are refused because each
would break the spliced document a different way — measured 20260901 against the renderer that
builds the site, and re-derived independently before this was written:

| what you saved | what `docs/RETROSPECTIVES.md` would show |
|---|---|
| `' ## A lesson'` (one leading space) | a **paragraph** under the previous fragment's heading — your lesson, filed as somebody else's incident |
| `'\t## A lesson'` (a leading tab) | a **code block**, heading text and all |
| `'##A lesson'` (no space) | a correct heading that `tools/markdown_link_gate.py` cannot see, so nothing may link to it |

One leading space is enough: Python-Markdown is stricter here than CommonMark, which would allow
three.

**Save the file as UTF-8 without a byte-order mark.** The mark is invisible in an editor, and
`render` splices it into the middle of the document, where it belongs to nothing.

Fragments are spliced **before** the design-review-passes section, which stays at the foot.

**Never quote a retired sentence contiguously.**
`tests/test_docs_quote_the_shipped_sentences.py` asserts that a sentence this build can no longer
print appears nowhere in `docs/`, `README.md` or `src/` — and splicing puts this fragment inside
`docs/RETROSPECTIVES.md`, which that gate `rglob`s. **`retro.d/` itself is not searched**, so the
branch that writes the fragment is green through `./check.sh`, and the failure surfaces at the
release, in the splice, several commits after its cause — landing on whoever cuts the release
rather than on whoever wrote the fragment. A retrospective *about* rewriting a sentence is exactly
the fragment most likely to quote the old one. Quote the halves separately, or describe it, and say
in-line why it is broken up so the next editor does not helpfully rejoin it. Same mechanism as the
link rule below: the constraint comes from where the text ends up, not from where it is written.
Found 20260903, twice in one increment — once in a fragment, once in a `src/` comment that escaped
only because of where the line happened to wrap.

**Never link to another fragment by filename.** Splicing puts every fragment into one
`docs/RETROSPECTIVES.md`, where a sibling's filename no longer resolves — and `docs/` is published,
so `mkdocs build --strict` fails the build rather than shipping a dead link. Link to the *heading*
instead, with the anchor the site will generate:

    ([*measured the launcher, not the work*](#measure_sync_cpupy-measured-the-launcher-not-the-work-20260805-1737))

**The example above is indented on purpose.** `README.md` is not a fragment: it is never spliced,
so the gate resolves its links from `retro.d/`, where that anchor does not exist — written as a
live link it would turn `main` red, from the file explaining how to avoid exactly that. The rule
above is about a real reference in a real fragment; keep the illustration indented or code-spanned.

The same applies to `changelog.d/`. It shipped anyway, three times: caught at 0.12.0's cut by
`make docs`, then twice on 20260902, **both on `main`** — where the next release cut would have
failed the docs build. That nothing saw it was structural rather than an oversight: inside
`retro.d/` the sibling's filename resolves to a real file, so the link is only wrong once the body
has moved. **Gated since 20260902**: `tools/markdown_link_gate.py` resolves a fragment's relative
targets from `docs/RETROSPECTIVES.md`, so it is red in `./check.sh` on the branch, before the
splice.

**Write it as a live link.** The gate resolves a `#…` target against the destination document's
headings **plus every pending fragment's**, which is where the body is going, so the form that is
correct after splicing is now correct before it. A slug two files both contribute is refused rather
than guessed at — the anchor the site generates would depend on splice order, so rename one
heading. There are no such collisions today.

**This instruction was the opposite until 20260902, and the reversal is dated rather than
overwritten.** The gate used to resolve `#…` against the fragment's *own* headings, so the correct
form was red in `retro.d/` and green only after splicing, and this file told you to degrade the link
to a code span. **Measured 20260901 11:16 UTC**: the first fragment to follow that instruction
literally turned `main` red at `b6be317` (14 jobs green, 1 red) and blocked three branches at once —
`check.sh` runs this gate under `set -e`, so everything after it stops running and you get no result
for the remaining checks either. A rule that reverses is worth a date; the four links written under
it were restored when it changed.
