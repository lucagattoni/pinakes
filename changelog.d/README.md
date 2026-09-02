# Changelog fragments

One file per change, spliced into `CHANGELOG.md` at release time by
`python3 tools/fragments.py --stream changelog --apply`.

**Write a fragment instead of editing `CHANGELOG.md`.** Several agents work in this repo at once,
and `CHANGELOG.md` is the one file every piece of work must touch. Two agents cannot conflict in
separate files, so the conflict class stops existing rather than being managed
(`tools/shared_file_overlap.py` reports the collisions that remain elsewhere).

## Naming

    changelog.d/YYYYMMDD_HHMM-<category>-<slug>.md

`YYYYMMDD_HHMM` is when the fragment was written, **UTC** — **read the clock, never compose it**
(`date -u "+%Y%m%d_%H%M"`). Fragments written before 20260804 11:32 carry a local time and keep it;
converting a recorded timestamp invents precision nobody measured. It orders `ls` chronologically
and dates a fragment without opening it, and
it is the same prefix plans and branches carry. `tools/fragments.py` strips it before reading the
category, so it never becomes part of the slug.

`<category>` is one of Keep a Changelog's six — `added`, `changed`, `deprecated`, `removed`,
`fixed`, `security` — and it lives in the **filename** so it cannot drift from the content.
`<slug>` is lowercase-with-hyphens. `ls changelog.d/` is then a readable summary of everything
unreleased.

    changelog.d/added-record-claude-fixtures.md
    changelog.d/fixed-refusal-reason-discarded.md

## Contents

The entry body only — no `### Added` heading, which the assembler writes from the filename. Write
it exactly as it should read in the changelog, starting with `- **The short claim.**`.

The rule that has not changed: **the fragment lands in the same commit as the code it describes.**

## Links: absolute, or wrong in one of the two places

A fragment is written in `changelog.d/` and read from `CHANGELOG.md` at the repo root, and **a
relative link cannot be correct in both.** `tools/markdown_link_gate.py` resolves a fragment's
`docs/GUIDE.md` as `changelog.d/docs/GUIDE.md` and fails the branch; writing `../docs/GUIDE.md` to
satisfy it breaks the link at splice time instead, because the spliced text lands at the root.

**Use an absolute `https://github.com/lucagattoni/pinakes/blob/main/…` URL** — the one form correct
in both places. (`CHANGELOG.md` uses both styles today: 6 absolute blob URLs and 9 working relative
links outside `docs/`. The relative ones resolve because they were written *into* the assembled file,
not into a fragment — which is exactly the difference this section is about.) Found
20260825 by the gate, on a fragment whose links were right for where the text was going and wrong
for where it was sitting.

**A cross-fragment anchor goes in a live link.** `tools/markdown_link_gate.py` resolves `#…` from
the document the body is spliced into — `CHANGELOG.md` here — plus every pending fragment in this
stream, so the form that is correct after splicing is correct before it too. This said the opposite
until 20260902; `retro.d/README.md` keeps the measurement and the date.

**The two streams splice to different depths, and this is the one place their rules differ.** A
retro fragment lands in `docs/RETROSPECTIVES.md`; a changelog fragment lands in `CHANGELOG.md` at
the repository root. So `../docs/DESIGN.md` is the correct spelling from *inside* `changelog.d/` and
climbs out of the repository once the body has moved. The gate refuses it, and says so.

**And never link to another fragment by filename**, for the reason
[`retro.d/README.md`](../retro.d/README.md) gives: splicing puts every fragment into one document,
where a sibling's filename no longer resolves. Link to the *heading* instead. **Gated since 20260902** — the same arm resolves a fragment's relative targets from `CHANGELOG.md`, so a sibling filename is red on the branch rather than at the release cut.
