## A row can be complete, correct, and in the wrong place (20260811 13:27)

**HIGH — five release rows were out of order in three sequences, and nothing could see it.**
`docs/ROADMAP.md`'s release table and its per-release sections both read
`0.20.0, 0.22.0, 0.22.1, 0.21.1, 0.21.0, 0.20.1`; `docs/STATUS.md`'s roadmap table put `0.15.1`
after `0.16.0` and `0.20.1` after `0.22.1`. Every misplacement is wrong on **both** readings —
SemVer and release time — so no ordering convention made them right. `CHANGELOG.md` was checked
and is clean, headings and link definitions both.

**Ordering is a property of the sequence, not of any row in it.** That is why nothing caught it:
the tables are complete, every anchor link resolves, `mkdocs build --strict` is green, and a reader
checking any single row finds it correct. Every check this project owns reads rows.

**How it happened, recovered from the six release commits.** `0.20.1` was appended correctly
(`2da0e07`). `0.21.0` (`96b3b35`) then inserted its section one position too early — after
`0.20.0`'s rather than after `0.20.1`'s — and the next three sweeps (`c83e877`, `df832fe`,
`93c20ab`) each used that same slot.

| Commit | Release | Section tail after it |
|---|---|---|
| `d429a2c` | 0.20.0 | `… 0.19.0 0.20.0` |
| `2da0e07` | 0.20.1 | `… 0.20.0 0.20.1` ✅ |
| `96b3b35` | 0.21.0 | `… 0.20.0 0.21.0 0.20.1` ← the first error |
| `c83e877` | 0.21.1 | `… 0.20.0 0.21.1 0.21.0 0.20.1` |
| `df832fe` | 0.22.0 | `… 0.20.0 0.22.0 0.21.1 0.21.0 0.20.1` |
| `93c20ab` | 0.22.1 | `… 0.20.0 0.22.1 0.22.0 0.21.1 0.21.0 0.20.1` |

**The tail was locally self-consistent at every step, which is the whole lesson.** After the first
error it read strictly newest-first, so each following sweep saw a coherent pattern around its own
edit and matched it — reproducing the error is what *reading the neighbourhood carefully* produced
here. Only the join between the ascending head and the descending tail was wrong, and that join is
a single line no sweep's diff ever touched. **Read the sequence, not the neighbourhood.**

**It had already been found and left.** The 20260807 documentation audit's finding
`docs/STATUS.md:303` names the `0.15.1` row exactly, with PyPI upload times as evidence. It sat
unworked for four days, and in that window three more sweeps added three more misplaced rows. A
verified finding nobody schedules is worth what an unverified one is.

**The fix is a gate, not a checklist item** — `tools/release_order_gate.py`, in `check.sh` and CI,
on the threshold this project already applies (`status_header_gate.py`: a checklist missed it four
times). Two design points are the reason it will still work in a year:

- **Direction is declared per sequence, never inferred.** Inferring it from whichever way most
  adjacent pairs agree would let a badly scrambled file elect its own answer and pass.
- **A sequence shorter than a floor is a failure, not a pass.** An empty sequence is sorted by
  definition, so a pattern that silently stops matching — a reformatted table, a changed heading
  style — is exactly how this class of gate dies quietly. A test asserts the real documents clear
  that floor, so a reformat goes red in the commit that does it.

**Watched failing before it was trusted**: run against the pre-fix tree it names all nine
misorderings and exits 1; CI scrambles a copy and asserts both the exit and the stated reason.
