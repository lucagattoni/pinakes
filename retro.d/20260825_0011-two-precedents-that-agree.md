## Two precedents that agree are not a pattern (20260825 00:11)

**HIGH — a decision arrived pre-framed by two real precedents, and the framing was refuted by the
three it did not mention.** The question was whether the owed release was `0.31.0` or `0.30.1`. It
was handed over as a genuine fork with evidence on both sides: *`0.27.0` was MINOR for a new tool
file; `0.28.3` was PATCH for extending an existing one; `0.27.0`'s precedent is a new file, this is
not.* Every clause of that is true. It is also **the two cases out of ten that agree with each
other**, and the criterion it implies — *new file versus existing file* — appears **nowhere** in the
governing SemVer rule, which says `MINOR = new skill, command, capability, or feature` and
`PATCH = bug fix, doc update, or dependency/component change`.

Measured across the ten tooling-only releases (those whose `src/` diff is `__init__.py` alone):

| Claim | Verdict |
|---|---|
| new tool file ⇒ MINOR | **refuted.** `0.22.2` shipped a brand-new `tools/release_order_gate.py` as PATCH; `0.27.2` shipped a brand-new `tools/wheel_import_gate.py` as PATCH, *with* an `### Added` section |
| an `### Added` section ⇒ MINOR | **refuted.** Seven PATCH releases carry one; `0.18.0` is a MINOR carrying none |
| existing tool ⇒ PATCH | 4 of 4 — and the set is **not vacuous**, which is the check that mattered |

**The load-bearing check was whether that last row was an artefact of confounding.** If all four had
been ordinary bug fixes *to* a tool, the axis would have been "fixes are PATCH" and would have said
nothing about adding a capability to an existing tool. It was not: **`0.27.1` added a brand-new
refusal to `tools/fragments.py` — this same file — and was cut PATCH under `### Fixed`**, and
`0.28.1` did the same to `release_order_gate.py`. The one apparent counterexample, `0.29.0` putting
`--check-anchors` on the existing `mutate.py` under a MINOR, is confounded: that release's headline
was five new battery files and `--check-anchors` is not among its `Added` bullets.

**The generalisation is about the shape of the offer, not about versioning.** A framing assembled
from two agreeing examples is the most persuasive form a wrong answer takes here, because no
sentence in it is false. The defence is not scepticism about the examples — they survive checking —
it is **enumerating the population they were drawn from**. The test set is the one you did not
choose.

**MEDIUM — the categorisation was the real question, and the implementer is the worst-placed judge
of it.** The fragment was named `added-…`, and `changelog.d/README.md` makes the filename
authoritative for the assembler. But it was chosen by the session that had just built the thing,
labelling its own increment — the position with the least distance on whether what it built is a
feature. The entry was re-filed under `### Fixed` on grounds independent of the version choice, so
the reasoning does not close on itself: it closes an item from a **corrections** plan, its body is a
defect narrative, and it is replayed against history to show it would have caught two past defects,
which is a fix with a regression test. A PATCH carrying `### Added` has happened once in the modern
convention (`0.27.2`); this does not make it twice.

**MEDIUM — `%an` cannot distinguish the agents in this repository, and the commit body can.** All
1029 commits are authored `Luca Gattoni <…>`, committer identical. Measuring those fields and
generalising to *"git cannot answer who wrote this"* was wrong, and it was wrong in the specific way
this repository keeps rediscovering: **the instrument was named after what it was hoped to answer
rather than after what it reads.** The trailers are not uniform — 20+ distinct `Claude-Session` ids
and four `Co-Authored-By` models — and they are in `%B`, which no identity-field query touches.

    git show -s --format='%B' <sha> | grep Claude-Session

That turns *"was this closing note written by the session that did the work, or by a later one
reconstructing it?"* into a checkable question, which is precisely the class behind the two defects
closed the day before: a closing note crediting a mechanism three days older than the defect, and a
message asserting a peer's work had not landed. Both were written by someone reconstructing, and
nothing in the repository could say so.

**MEDIUM — a section heading is a status claim, and no gate reads it.** A `###` item in
`plans/20260731_1202-open-corrections.md` sits under `## Live` while its own body, 26 lines down,
carries `**CLOSED 20260824 00:35**`. `grep '^## '` — how anyone triages that file — returns *Live*
and stops. **It cost a real collision**: a coder session read it as live and was minutes from
rebuilding a landed increment. The convention it should follow already exists two files away —
`T6` and `T8` in `plans/20260804_1016-template-release.md` carry `· **CLOSED <date>,
<disposition>**` in the `###` heading itself — so the repair is conformance rather than design.
**Not done yet, deliberately:** the item is *partial*, not closed (the body-rule widening is
explicitly untaken), so moving it into `## Closed — recorded so nobody reopens them` would file an
undecided design question under a heading promising the opposite.

**LOW, and it recurred twice in one session — a gate is only a gate when its exit status is what
the next command reads.** `make docs 2>&1 | tail -12` followed by `echo "DOCS_EXIT=${PIPESTATUS[0]}"`
printed `DOCS_EXIT=` — empty. The value read was the pipeline's, not the build's. Both instances
were caught and re-run bare, so what actually gated the release was `./check.sh` and `make docs`
redirected to a log with `$?` read directly. The rule was already written, in `CLAUDE.md`, and had
been read that same session. **A rule that is known and still broken twice in four hours is a rule
whose failure mode is invisible at the moment of committing it**, which is the argument for the
redirect-and-read-`$?` form being the only form ever typed, rather than the one used when it seems
to matter.

**LOW — a count word and the list beside it drift independently.** `docs/STATUS.md` held two
instances of `forty-seven` and exactly one was wrong: the other sits inside `0.30.0`'s own
published-verification entry, where it was accurate when written. A `replace_all` would have
silently falsified a historical record. Same family as the `| head` truncation that shipped a broken
anchor a day earlier — **the edit whose anchor matches more than once is the one that needs the
count taken first.**

**LOW — a peer renaming itself is indistinguishable from a peer dying.** This session's name changed
from `pinakes-d1` to `pinakes-7c` mid-work. A coder session correctly observed that `pinakes-d1` had
left `ListAgents`, correctly inferred a usage-limit kill, and wrote a careful handover describing a
release as *stranded mid-cut* — while it was still moving. Nothing was lost, because the branch had
been committed and pushed at every step, which is the actual defence. But `ListAgents` cannot
distinguish *gone* from *renamed*, so a peer's absence is evidence about the listing and not about
the peer.

**LOW, and found by a number that failed to move — `tools/markdown_link_gate.py` reads
`git ls-files`, so a file that is written but not yet staged is invisible to it.** A full
`./check.sh` run immediately after writing this very fragment reported `84 ungated file(s), 301
link(s)` — byte-identical to the run before the fragment existed. Staging it and re-running gave
`85`. **So the ordinary sequence — write a fragment, run the gate, commit — produces a green that
says nothing whatsoever about the new file**, and the first thing to actually read it is CI, after
the push. It is the same sentence as the item this release is about, one directory over: *a green
signal is only evidence about the thing it actually measures*, and here the thing measured is the
index rather than the working tree. Nothing was wrong with the fragment; the gate simply had not
been shown it. **`git add` before the last gate run, not after** — which is also the only ordering
under which the gate's answer describes the commit about to be made.
