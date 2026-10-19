## A3 — what the status block held that nothing else did (20261019 09:34)

**`CLAUDE.md` lost about 250 lines of status narrative at A3, and the test of the move was not
whether the facts were still true but whether each one had a home.** Before it was deleted every
bullet was traced to the document that owns its facts, and the text was found there by `grep`
(whitespace-normalised, because a phrase wrapped across two lines is invisible to a plain one).
Two bullets were not moved at all: **they were wrong**. The full pre-A3 text is
`git show f1804ea:CLAUDE.md`.

| Pre-A3 bullet | Where its facts live |
|---|---|
| The pause, the analysis's one-line conclusions, its *do not* list, the user's lifting of the release hold | `plans/20260904_1027-development-paused-handover-and-evidence.md` — **the note at its top was written at A3**, because those lines had no other home; the *do not* list is also in `plans/20261018_2354-option-a-review-coverage-and-claude-md.md` § 1 |
| The live build order and the option-E answer | `plans/20260901_1148-clear-the-user-facing-list.md` §§ 3–4 |
| *Every published release offers to delete a permanent ULID* | **Superseded**: fixed and published in 0.32.3 — `docs/ROADMAP.md`, `docs/STATUS.md`, `CHANGELOG.md`, live plan row 30. The bullet said *in no published wheel* while the release was out |
| *0.32.6 is cut* | `CHANGELOG.md`, `docs/ROADMAP.md` (*Where things stand right now* carries the `minimum-python` counts), `docs/STATUS.md` |
| *Row 31 is NOT fixed by 0.32.3* | **Superseded**: row 37 cut 0.32.4, which closed it. The bullet was the most severe thing open in the file for the six weeks after it was shipped |
| The 0.32.2 timing rule for the three registers | `docs/RELEASING.md` § *Sweep the three documents* |
| 0.32.0's red `main` and the ECB constant | `CHANGELOG.md`, `plans/20260830_0927-main-is-red-and-a-review-that-half-ran.md`, `docs/RELEASING.md` § *Before you start* step 3 |
| *Two plans have scheduled work* — owners, answered decisions, S16–S19 | `plans/20260825_1803-open-decisions.md`, `plans/20260825_1240-run-pinakes-sweep.md`, `docs/README.md`'s routing rows |
| *A status claim is never gated* | `docs/BUILDING.md` § *Read the build order out of `plans/`*, third bullet — **moved there at A3**, it had no other home |

### Three lessons the block held and nothing else did

**1. A reading can be accurate and still about the wrong thing — the interpreter edition.** A
`.venv` pins its interpreter once created, and a fresh worktree creates a new one, which takes the
newest interpreter installed: `pyvenv.cfg` said 3.13 in the primary checkout and 3.14 in a
worktree made minutes earlier (measured 20260904 08:40). That one rule explained every reading
taken on 20260903–04, **including two that reached `CLAUDE.md` and were wrong** — when the primary
venv's interpreter symlink dangled both directories reported 3.14.7, and when 3.14.7 was absent
from the machine both reported 3.13.15. Since 20261015 `.python-version` pins local development
and `UV_PYTHON` pins CI. **The durable half is that the directory was never the evidence: pass
`--python` explicitly and print `sys.version` in the run that produces the number.** Every finding
pinned that way survived all four revisions of the paragraph; the one claim made from an unpinned
`uv run --frozen` was the one that was wrong.

**2. A null result is about its population (20260903 14:20).** The planner ran the published
`pnk doctor` on both interpreters, watched it finish, and wrote into row 28 that it does not crash
on 3.13. True measurement, wrong population: the KB had no sidecar for the unreachable document, so
the loop whose body raises (`doctor.py:420` at v0.32.2) was never entered. Against a KB where the document had
been indexed it dies there. `rglob` itself raises on neither version, so the walk looks safe and
the `stat` inside it is not. **Do not accept a null result here with the sidecar absent.** This is
*Seven selectors that could not fire* with an instance that entry does not hold.

**3. The first run being green is not the leg having never failed.** The `minimum-python` leg's
first run in this repository (run 33765944569 at `934190c`) was green and was read in its log:
CPython 3.13.15 and the same pass and skip counts as the local run, which is what showed it ran a
suite and not a no-op. It then failed once — run 33853409534 at `1d42e42d`, 20260904 08:26 — and
the block read as though it never had. That was found in the harvested CI data
(`plans/20260904-process-review-data/ci-runs.tsv`), not by anyone re-reading the file.

### Why the block became pointers

One of its bullets alone was corrected five times in three days (its own count), and every instance was about who owns what or who must decide what — the one thing a
cleared session reads it to learn. The file's growth, 76
lines on 20260725 to 455 on 20260904, is `plans/20260904_1027-…` § 3.2. The block's own figures
disagreed with that series and with each other: it gave 302 for the moment the analysis called the
file too long where § 3.2 measures 410, and it said 427 for two hours while the file was already
459. **A count in prose has no column to check.**
**Three slimming passes each grew back within days — and the likely reason, an inference rather
than a measurement, is that each kept a summary, and a summary of a plan is a second register of
its facts.** The rebuilt block is four pointers, a size line that
names `wc -l -w` instead of a number, and the rule that where a snapshot and a `## Build order`
disagree the build order wins. It holds nothing that can become false when a plan changes, except
one clause — which increments of option A remain — and that is the one the handover rule in
`docs/BUILDING.md` already lists as a place an increment falsifies.
