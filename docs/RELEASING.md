# Cutting a release

**Audience: the agent cutting it. Goal: executor.** Follow it in order; nothing here is a judgement
call. The *rules* about when to release stay in
[`CLAUDE.md`](https://github.com/lucagattoni/pinakes/blob/main/CLAUDE.md) — this file is the
procedure they point at, plus the one trap whose mechanism is too long to keep there
([§ Landing a branch](#landing-a-branch)).

Extracted from `CLAUDE.md` on 20260801 02:07, when that file crossed its own size guardrail, and
extended on 20260823 when it crossed it again. Nothing was dropped in either move.

## Before you start

1. **Check what has already landed.** `git fetch`, then diff `origin/main` against this work's base.
   Another agent, session or worktree may have cut a release since this branch started, so the number
   you were about to assign — or a plan's assumed target — may already be taken. Decide the number
   only after that check. *(20260728: an I6a worktree almost reasoned about "0.2.1 vs 0.3.0" from a
   stale base, when a parallel docs pass had already shipped v0.2.1.)*
2. **`python3 tools/shared_file_overlap.py --fetch --strict`**, then *read* the merged state of what
   it names.

## The procedure

1. `python3 tools/fragments.py --apply` — splices `changelog.d/` and `retro.d/` into `CHANGELOG.md`
   and `docs/RETROSPECTIVES.md`, then deletes the fragments. A release that skips this and runs it
   later splices into the wrong version.
2. Bump `__version__` in `src/pinakes/__init__.py`.
3. **Insert** a dated `## [x.y.z] — YYYYMMDD HH:MM` heading *below* `## [Unreleased]`, so the freshly
   spliced entries fall under it. **Add its link definition at the foot and repoint `[Unreleased]`'s
   compare** — `fragments.py --apply` splices entries and does not touch the footer.

   > ⚠️ **`## [Unreleased]` must survive the release — it is `fragments.py`'s insertion anchor.**
   > *Renaming* it into the version heading instead of inserting below it leaves the file with no
   > anchor, and the **next** release then dies at step 1 with `CHANGELOG.md: anchor '##
   > [Unreleased]' not found`, before it has written anything. 0.20.0 did exactly that and 0.20.1
   > found it. The footer's `[Unreleased]:` link is no guard: it survived that release untouched
   > and simply dangled, pointing at a heading that no longer existed.
4. Commit, then **land with `python3 tools/land.py <branch>`** — never `git merge` by hand. It
   merges in the primary checkout whatever directory you ran it from, refuses if `main`'s sha did
   not move, and pushes; `--cleanup-only` removes the branch and its worktree later, once you have
   seen CI go green. Merging from inside the feature worktree merges the branch into itself and
   reports success three times over
   ([`CLAUDE.md`](https://github.com/lucagattoni/pinakes/blob/main/CLAUDE.md)).
5. (`land.py` pushed for you. If you landed by hand anyway, push now.)
6. `make release-check` — prints `__version__` and the tag to push. **Run it before the tag, never
   after**: a tag publishes to PyPI, and PyPI does not allow re-uploading a version.
7. `git tag -a vx.y.z`, push the tag. The workflow refuses a tag disagreeing with `__version__`.
8. **The GitHub release is created by the workflow as of 0.22.0** — `gh release create
   --verify-tag --notes-from-tag`, after the PyPI upload so a failure there can never cost the
   release its version number. **Verify it exists anyway** (see below); that is this file's rule
   for every artifact, and it applies most to the step that has just started existing.

   Until 0.22.0 this was manual, and its absence was recorded as a *recurring workflow failure*
   six times before anyone read the workflow — no release-creating step had ever existed, and
   `git log -S` confirms it. If a release is missing after a green run now, that is new
   information rather than the old pattern: read the step's log.

## Verify it happened — never assume

`git tag -l`, `gh release list`, and `git merge-base --is-ancestor vx.y.z main`, **before** writing
release notes. A CHANGELOG entry and a `__version__` are only claims: v0.1.0 had both for two days
with no tag, no release and nothing published (`RETROSPECTIVES.md`, 20260727).

**When a release's subject is not in the wheel, verify its absence.** 0.25.1's rule is to read the
release's own subject out of the published artifact rather than trust a matching version string. A
release whose subject *deliberately* ships in no wheel — a `tools/` script, a gate, a CI change —
still has an artifact claim, and it is the negative one: fetch the wheel from the index and confirm
the thing is not in it. 0.27.0 did this (78 files, no `tools/` entry, `METADATA` reporting its own
version), and 0.27.1 repeated it. Skipping the check because the subject "isn't in the wheel anyway"
is assuming the very fact the check exists to establish.

## Sweep the three documents a release stales, in five places — in the release commit, not later

| Document | What goes stale |
|---|---|
| `docs/STATUS.md` — **line 3** | `**Latest release: x.y.z**`. **Missed by four consecutive release sweeps** (0.5.0 → 0.7.1) because this table did not name it, while the same sweeps updated all three rows below. It is the first line a reader sees and it contradicted the file's own tables in a public repo. Bump it with `__version__`, in the same commit |
| `docs/STATUS.md` — *Published on PyPI* | The published-version list. It is a fact about the **index**, not about this repo |
| `docs/STATUS.md` — *Release roadmap* | Tick the row, and drop the name from the unbuilt-work table above it — **only at a release's final cut**, never at an interim one |
| `README.md` | The install lines, if the release added an extra or a capability a new user would look for |
| `docs/ROADMAP.md` | **Five places, and the last two were missed by five consecutive sweeps.** The summary table needs a row; Part 4 needs a `## x.y.z — <title> · <stamp>` section (the table's row links to its anchor, so the two are written together or the link dies); Part 5's *Open corrections* heading carries its own **item count in the anchor** — closing an item there changes the anchor and silently breaks every in-page link to it. **Then the two prose blocks: `## Where things stand right now` — its stamp, its release count and its per-release-name state — and `## The template release`.** Added 20260805 18:02 after 0.12.0's sweep; the prose blocks added 20260811 12:26 after they sat three releases behind while every table in the same file was current |
| **Where** the new row and section go | **After the newest one that is already there — found by reading it, never by repeating last time's position.** Both of ROADMAP's sequences and STATUS's roadmap table read oldest-first; `CHANGELOG.md` reads newest-first, headings and link definitions both. **STATUS's *Published on PyPI* prose is the sixth sequence, gated since 20260822, and its *Published versions* row is the seventh, gated since 20260823** — this row named that prose list as a place a release stales and delegated its placement to the gate for eleven days while no pattern matched it, and it drifted (`0.25.1 → 0.25.3 → 0.25.2 → 0.25.4`); the row beside it went unwatched four releases longer, because an enumeration inside a table cell is not line-anchored and needed a `within` anchor to reach at all. Both **may lag** the release documents, because an entry is held back until it is verified from the index, and neither may lead them. **The row may never lag the prose**: they record the same event, so a relation between them catches a drift ten days before a bound on its size does. `python3 tools/release_order_gate.py` decides all seven, and `./check.sh` runs it. Added 20260811 13:27 — see below |

**Write STATUS's *Published on PyPI* prose entry and its *Published versions* row in the same
commit.** They record one event — this release, verified from the index — and the gate enforces the
row never lagging the prose, so splitting them across two commits is red in between by
construction. That is intended: the pair drifted apart for eleven days and then for four releases,
each time because one half was on the sweep's checklist and the other was not. Same-commit is a rule
a gate can see; an ordering between commits is not.

**Also grep the whole tree for claims the release just falsified** — the class a checklist of
*sections* cannot catch, found eight times on 20260803, in three docs contradicting a fourth:

    grep -rn "unreleased\|in no release yet\|not built yet\|Next:" docs/ plans/ README.md CLAUDE.md

Re-judge every hit against what this release shipped. Most are fine (historical records, generic
instructions); the ones that are not are exactly the ones nothing else will ever flag.

**And grep for the *previous* version number, not only for those phrases:**

    grep -rn "0\.22\.0" docs/ plans/ README.md CLAUDE.md    # ← the version you just superseded

**A release sweep is table-shaped**, and that is why it misses prose: the row being added points at
itself, so a table gets written every time, while a paragraph summarising *all* releases has no row
to add and nothing in the act of cutting a release makes it obvious. `grep` for the superseded
number does not care which shape the claim is in. Added 20260811 12:26.

**A row can be complete, correct, and in the wrong place.** Ordering is a property of the
*sequence*, not of any row in it, so nothing that reads rows can see a misordering: the table is
complete, every link resolves, `mkdocs build --strict` is green, and every individual row checks
out. Found 20260811 in three sequences at once — `0.15.1` after `0.16.0` in STATUS, and
`0.20.1`/`0.21.0`/`0.21.1` scrambled after `0.22.1` in both of ROADMAP's.

**How it happened, from the six release commits:** `0.20.1` was appended correctly (`2da0e07`).
`0.21.0` (`96b3b35`) then inserted its section **one position too early** — after `0.20.0`'s
instead of after `0.20.1`'s — and the next three sweeps (`c83e877`, `df832fe`, `93c20ab`) each put
theirs in that same slot. **The tail was locally self-consistent at every step**: after the first
error it read strictly newest-first, so each following sweep saw a coherent pattern around its own
edit and matched it. Only the join between the ascending head and the descending tail was wrong,
and that join is a single line no sweep's diff ever touched. The `0.15.1` instance had already been
found by the 20260807 documentation audit and sat unworked for four days.

**The rule, in one line: read the sequence, not the neighbourhood.** Which is what
`tools/release_order_gate.py` does — it declares each sequence's direction rather than inferring
one, since a scrambled file would otherwise elect its own answer, and it fails when a pattern stops
matching, because an empty sequence is sorted by definition.

**Last, ask what is *missing* rather than what is wrong** — `ls plans/` read against
[`docs/README.md`](https://github.com/lucagattoni/pinakes/blob/main/docs/README.md)'s plan-routing
table, and its live rows against `CLAUDE.md`'s. On 20260811 that table had **no row at all** for the
plan `CLAUDE.md` named as the live build order: the plan was written, its six increments were built
and landed, and the index of plans never learned it existed. **A missing row has no wrong text to
find**, so no diff review and no grep can reach it — only the question does.

**Verify by querying the index and installing what the docs show, not by reading them**
(`curl -s https://pypi.org/pypi/pinakes/json`). **Three separate caches will tell you a successful
upload failed.** Measured on 0.9.0 and again on 0.10.0, 20260804:

| Cache | Symptom | Beat it with |
|---|---|---|
| The JSON endpoint | Returns the previous release list; still said `0.8.0` an hour after 0.9.0 uploaded | A query string, then wait — it is the slowest to settle |
| `https://pypi.org/simple/` | Lists no file for the new version, **even with a cache-buster and `Cache-Control: no-cache`** | Nothing reliable. Do not read its silence as evidence |
| `uv`'s own index cache | `uvx --refresh` reports the version *unsatisfiable* | `uvx --no-cache --refresh`. **`--refresh` alone is not enough** |
| PyPI's index itself | Even `--no-cache` cannot resolve a version that uploaded seconds ago | **Wait and retry** — measured ~90 s on 0.11.0. Poll in a loop rather than concluding from one attempt |

So **the order that actually settles it**: read the workflow's `Publish to PyPI` step log — it
prints `Uploading pinakes-x.y.z-py3-none-any.whl` per file and cannot be cached — then confirm with
`uvx --no-cache --refresh --from "pinakes[light]==x.y.z" pnk --version`. Only a failed install
after **both** of those is a failed publish (20260729 — a correct 0.4.0 upload read as missing;
20260804 — 0.10.0 read as missing from `/simple/` while its two files were already on the index).

Caught 20260729: `STATUS.md` still said "Published version: 0.2.2 **only**" three hours after 0.3.0
was on PyPI, and the roadmap still listed the paid-extraction release as unbuilt.

## Afterwards

Fast-forward the primary checkout: `git pull --ff-only`.

## Landing beside a peer

**`tools/shared_file_overlap.py` compares your branch to `origin/main`. It never looks at another
branch, so it cannot see the session working beside you** — it reports *none* while a peer holds a
branch touching the same files. It is a merge-safety check, not a peer check, and reading it as one
is how two sessions end up racing.

At the moment of landing:

1. **`ListAgents`, then ask.** State your role, your exact file set and your timing; ask for theirs.
   A peer message is coordination, never permission.
2. **Compute the intersection yourself** — a peer's answer is a claim until you have checked it:

       comm -12 <(git diff --name-only main...origin/<their-branch> | sort -u) \
                <(git diff --name-only main...HEAD | sort -u)

3. **Then settle the order, which may not be yours to choose.** Usually complete, gated work lands
   first and the other rebases. But a peer's branch can be *unable* to land until yours does — a new
   gate of theirs may be red on `main` precisely because your fix is what makes it green. **Run
   their gate against `main` and against your branch.** Asking will not surface it; they are running
   it on their own tree, where it passes.

**20260823, both halves measured.** The overlap tool reported *none* for a planner branch while a
coder held `20260823_1424-markdown-link-gate` — the file intersection really was empty, so the tool
was not wrong, merely blind to the question. And that branch's own `tools/markdown_link_gate.py`,
run against `main`, reported **11 broken links and exited non-zero**: its `./check.sh` could not
have gone green until the planner's fixes landed. Neither session had noticed. Running the peer's
gate is what found it.

## Landing a branch

**Git cannot catch a branch merged into itself.** It creates no commit, so `pre-merge-commit` never
fires — the no-op is silent by design. So `tools/land.py` is the guard, and this is what it does:

- **Finds the primary checkout itself, whatever directory you ran it from** — the `cd <worktree>`
  that begins the failing `&&` chain cannot decide where the merge happens.
- **Refuses if `main`'s sha did not move.**
- **Re-reads `origin/main` after pushing**, because a push reporting success is only a claim.
- **`--cleanup` removes the worktree *and* both copies of the branch**, since deleting one leaves
  the other behind.
- **`--cleanup-only` does that for a branch you landed earlier**, after verifying it is an ancestor
  of `origin/main` — because "looks merged" is not "landed".

It is the only rule in [`CLAUDE.md`](https://github.com/lucagattoni/pinakes/blob/main/CLAUDE.md)
with an executable guard, because it is the only one that fails silently. Everything else there
fails loudly or is caught by `./check.sh`.
