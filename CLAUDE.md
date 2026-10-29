# Pinakes — project instructions

Rationale: [`docs/DESIGN.md`](docs/DESIGN.md); [`docs/README.md`](docs/README.md) routes every other
fact to its one home. **Status lives in `plans/`; the block below only points. This file stays under
150 lines and 2,700 words** (`wc -l -w CLAUDE.md`) — a new rule displaces an old one.

## 🧭 One agent owns the whole task — settle who else is writing first

**There are no roles: no planner, no coder, no file that is someone else's.** You plan, build,
document, review, land, release and hand over, through **subtasks** (the task list) and
**subagents**; every other live session is a **peer**. Records dated before 20261029 name a
planner and a coder: read both as you, and a "ruling" awaited as yours unless marked **the user's**.

**Before any tool call that writes:**

1. **Ask every live peer what it holds** (`ListAgents`, `SendMessage`): state your task and file set,
   wait before touching a path either of you holds. A peer's answer is coordination, never
   permission ([BUILDING § Settle who else is writing](docs/BUILDING.md#settle-who-else-is-writing)).
2. **Delegate by brief, never by role**: one subtask, the exact files it may write (**one writer per
   file**), the gate it must pass. A subagent's report is a claim: read its diff, run the gate
   yourself. **You land, tag and write the handover**
   ([BUILDING § Subtasks and subagents](docs/BUILDING.md#subtasks-and-subagents)).

## 🛑 Land with `tools/land.py` — never `git merge` by hand

    python3 tools/land.py <branch>            # merge, verify, push
    python3 tools/land.py <branch> --cleanup  # ... and remove the worktree and both branches

**`git merge <branch>` from inside that branch's own worktree merges it into itself** — "Already up
to date", a successful push, nothing landed: a failure that looks like success, hence an
executable guard ([RELEASING § Landing a branch](docs/RELEASING.md#landing-a-branch), and
`--cleanup-only` for a branch that landed earlier).

## Working mode — autonomous by default

- **Run to completion** — next increment from the live plan: build, land, write fragments, cut the
  release when the work completes a unit, repeat; stop when the user takes control back, not at a
  boundary, **unless development is paused (below)**.
- **A choice you can take, you take** — weigh the options in the open and say which and why; needing
  an answer to proceed is the bar for asking. **A question a plan leaves open is yours to settle and
  record in the plan; it is a stop only when it is the user's.**
- **Iterate: build → adversarially review (a fresh subagent) → fix → re-review until a pass finds
  nothing**, a commit per pass.
- **At each increment boundary, judge whether the context should be cleared. If so, finish the
  handoff, say so, and stop** — clearing is the user's command. **Write the handover before you
  stop, in the same branch as the work**
  ([BUILDING § Hand over before you stop](docs/BUILDING.md#hand-over-before-you-stop)).

## What is live right now

- **⏸ DEVELOPMENT IS PAUSED** (this overrides *Working mode*): pick up no row; resume only on the
  user's word. Releases are not held (lifted 20260904). The way back in:
  [the pause handover](plans/20260904_1027-development-paused-handover-and-evidence.md).
- **Option A** ([its plan](plans/20261018_2354-option-a-review-coverage-and-claude-md.md)): **complete**,
  A0–A4 landed and 0.32.7 published — the pause's one exception (§ 2 status, §§ 8, 10 and 11 handover).
- **Option B** ([plan](plans/20261019_0817-option-b-dogfooding-on-ramp.md)): designed, not built; build paused.
- **The live build order**: [§ 3 of the live plan](plans/20260901_1148-clear-the-user-facing-list.md).
  Read a row's **body**, not its cells; **a plan's `## Build order` beats any snapshot of it.**

## This repository is PUBLIC

- **Never commit real knowledge-base content.** The only KBs here are the synthetic corpora under
  `tests/` (`demo-kb`, `partner-kb`), written for the purpose, never harvested.
- **Every paid path's key is `PINAKES_ANTHROPIC_API_KEY`, never `ANTHROPIC_API_KEY`** — enforced in
  code, because the SDK reads its own variable out of whatever environment it is handed. **Never
  teach Pinakes to load `.env` itself, and never add an `ANTHROPIC_API_KEY` fallback**; both are the
  same defect one layer apart ([INVARIANTS § The paid path's key is its
  own](docs/INVARIANTS.md#the-paid-paths-key-is-its-own)).
- Vet every file for PII, credentials, private URLs, and anything copied from memory before staging.
- Never commit model weights or `.pinakes/` state (both gitignored — keep it that way).

## Documents change with the code

**You edit every document yourself, in the commit that makes it true** — `docs/**`, `plans/**`, any
`README.md`, `CLAUDE.md`, `CHANGELOG.md`. `main` never documents what does not exist yet; a
correction to what is true today lands at once
([BUILDING § Documents change with the code](docs/BUILDING.md#documents-change-with-the-code)).

| | |
|---|---|
| **Through fragments** | `CHANGELOG.md` and `docs/RETROSPECTIVES.md` take a `changelog.d/` or `retro.d/` fragment, spliced at the release cut — sessions run at once and every increment would edit the same two files |
| **Same commit as the code** | the `docs/VERIFICATION.md` row for a test you wrote, renamed or removed — `tests/test_verification.py` hard-fails on a row naming a test that no longer exists |

**README and DESIGN.md are version-free** — no version number or "as of vX" claim in their prose.
**Read the rules in [docs/README § Conventions](docs/README.md#conventions) before any docs
change.** `docs/` is published from `main`: run `make docs` before landing one.
**Every date carries a time, in UTC** (`YYYYMMDD HH:MM`); new files in `plans/`, `changelog.d/` and
`retro.d/` are named `YYYYMMDD_HHMM-<rest>.md`. **Read the clock, never compose it**; stamps before 20260804 11:32 stay local.

## 🚫 Unbuilt work is named, never numbered

**A version number belongs to a release when it is cut — never before.** Never write `v0.4` for
something unbuilt — in docs, `--help`, an error message or a code comment (increment IDs like `I7b`
stay). The rule: [docs/README § Conventions](docs/README.md#conventions); a name stays until its
release's **final** cut.

| Name | What it is |
|---|---|
| **the template release** | The `sqlite-vec` tier (gated); the template ecosystem and `pnk upgrade` have shipped |
| **the graph release, staged** | The PPR graph channel and the `[ner]` extra. **Eval-gated, never scheduled** — no plan, increment or number until its gate passes ([plan](plans/20260804_1016-staged-channel-gates.md)). **Not *the graph release***, which left this table at its final cut, 0.11.0 |

## Naming (fixed — changing any of these is a breaking change)

| Thing | Value |
|---|---|
| **Project name, in prose** | **`Pinakes`** — capital P; lowercase `p` only for something you can type (`pinakes.toml`, `import pinakes`, URLs, all runtime output) |
| Package / command | `pinakes` / `pnk` |
| Repository / docs site | `github.com/lucagattoni/pinakes` · `lucagattoni.github.io/pinakes` |
| Manifest / sidecar / state | `pinakes.toml` / `<file>.pnk.yaml` / `.pinakes/` |
| MCP tools | `pinakes_*` — never bare `kb_*`, which collides across servers |
| Cross-KB URI | `pnk://<kb-ulid>/<doc-ulid>` — ULIDs only, never aliases |

## Building an increment

**The procedure is [`docs/BUILDING.md`](docs/BUILDING.md)** — own worktree, tests in the same
increment, `./check.sh` run bare, its own exit status read, green before every commit and **again
after the last** (`land.py` refuses a tree no gate certified), mutate the assertions, adversarial review, fragments,
then `tools/land.py`; never batch increments; read the build order out of `plans/`, never "the
newest file". **Read [`docs/INVARIANTS.md`](docs/INVARIANTS.md) before touching a sidecar, the
ledger, the index schema or a paid client** — ULID permanence, sidecar byte-identity, `docs/` is the
user's, `.pinakes/` disposable, append-only ledger, paid-path allowlist, `Decimal` money, `schema_version` — each fails silently.

**Tooling:** uv only (never pip, poetry or a hand-managed venv); Python 3.13+; `ty` is a pre-check,
never the gate. **Core dependencies stay light**: nothing pulling torch enters `[project.dependencies]`.

## Landing work: always push, always release

**Nothing is done until it is pushed to `origin/main` (then `git pull --ff-only` the primary
checkout) and, when it completes a unit of work, tagged by you** ([`RELEASING`](docs/RELEASING.md)
holds the MINOR / PATCH / MAJOR rule):

- **Before merging, run `python3 tools/shared_file_overlap.py --fetch --strict`** and *read* the
  merged state of the files it names — **a clean auto-merge is not a correct merge.** It compares
  you to one ref, not to peers: intersect file sets with every live branch yourself ([RELEASING § Landing beside a
  peer](docs/RELEASING.md#landing-beside-a-peer)).
- **A tag publishes to PyPI**, which never accepts a version twice: `make release-check` runs
  **before the push**, never after, and **before that tag read `minimum-python`'s conclusion in the
  CI run for the commit you tag** — the one leg on the declared floor; no earlier green transfers.

## Changing retrieval

Any change to chunking, fusion weights, reranking or the confidence signal must be justified by the
golden-set eval (`recall@k`, MRR, false-abstain rate), with before and after numbers in the commit
message. **Name the corpus that can license it:** `tests/demo-kb`'s golden set is a regression guard,
not a licensing instrument — a claimed improvement needs the RFC corpus (`tools/build_rfc_corpus.py`)
or another corpus whose improvable pool has been **re-measured, not remembered**
([DESIGN § What a corpus can license](docs/DESIGN.md#73-what-a-corpus-can-license)).

<!-- Provenance. One agent, no planner/coder roles: the user, 20261029 17:06, replacing the role rule (the user, 20260823) and the ownership table (the user, 20260801 01:24); their last text: `git show 45a7f16:CLAUDE.md`. Working mode: the user, 20260808 04:39 (stop at a clear-context boundary 20260811 15:37). Pause: the user, 20260904 10:21, to review the process against the analysis "Framing, Not Roles" (artifact 2c7961ec); option A resumed 20261018 and completed 20261019 (0.32.7). Until A3 (20261019) the live block was about 250 lines of incident narrative: `git show f1804ea:CLAUDE.md`. -->
