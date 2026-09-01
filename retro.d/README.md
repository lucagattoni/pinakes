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

Fragments are spliced **before** the design-review-passes section, which stays at the foot.

**Never link to another fragment by filename.** Splicing puts every fragment into one
`docs/RETROSPECTIVES.md`, where a sibling's filename no longer resolves — and `docs/` is published,
so `mkdocs build --strict` fails the build rather than shipping a dead link. Link to the *heading*
instead, with the anchor the site will generate:

    ([*measured the launcher, not the work*](#measure_sync_cpupy-measured-the-launcher-not-the-work-20260805-1737))

The same applies to `changelog.d/`. Caught at 0.12.0's cut, by `make docs` and not before: nothing
in `./check.sh` resolves a link that only becomes wrong at splice time, so the fragment was green on
its own branch.

**⚠️ Until build-order row 14 lands, write that anchor in a code span rather than as a live link.**
The form above is right about the *destination* — `docs/RETROSPECTIVES.md:4034` links to `:3945` this
way and `mkdocs --strict` passes — but `tools/markdown_link_gate.py` resolves a `#…` target against
the fragment's **own** headings, so a cross-fragment anchor is red in `retro.d/` and green only after
splicing. Name the sibling's title in prose and put the anchor in backticks; make it a link once the
gate learns the destination. **Measured 20260901 11:16 UTC**: the first fragment to follow this
instruction literally turned `main` red at `b6be317` (14 jobs green, 1 red) and blocked three
branches at once — `check.sh` runs this gate under `set -e`, so everything after it stops running and
you get no result for the remaining checks either.
