# Pinakes — project instructions

Rationale: [`docs/DESIGN.md`](docs/DESIGN.md); [`docs/README.md`](docs/README.md) routes every other
fact to its one home. **Status lives in `plans/`; the block below only points. This file stays under
150 lines and 2,700 words** (`wc -l -w CLAUDE.md`) — a new rule displaces an old one.

## 🧭 A cleared context does not know its own role — settle that first

**Before any tool call that writes:**

1. **Name your role** (coder, planner, other) from what the **user** said in *this* session — never
   from the repo, the previous session or the work in flight. **If you cannot, ask, and do nothing
   until they answer**; *Working mode* does **not** override this.
2. **Ask every live peer theirs** (`ListAgents`, `SendMessage`), stating your role and file set, and
   wait before touching a shared path. Both wrong guesses fail silently
   ([BUILDING § Settle your role](docs/BUILDING.md#settle-your-role-before-anything-else)).
3. **Then act inside the ownership table**, re-checking at the moment of landing.

## 🛑 Land with `tools/land.py` — never `git merge` by hand

    python3 tools/land.py <branch>            # merge, verify, push
    python3 tools/land.py <branch> --cleanup  # ... and remove the worktree and both branches

**`git merge <branch>` from inside that branch's own worktree merges it into itself** — "Already up
to date", a successful push, nothing landed: the one rule here that fails silently, hence the one
with an executable guard ([RELEASING § Landing a branch](docs/RELEASING.md#landing-a-branch), and
`--cleanup-only` for a branch that landed earlier).

## Working mode — autonomous by default

- **Run to completion** — next increment from the live plan: build, land, write fragments, repeat;
  stop when the user takes control back, not at a boundary, **unless development is paused (below)**.
- **Cutting the release is the planner's, and so is the handover** — the ownership table wins. An
  implementer's increment ends at the fragments: it lands, proposes planner-owned text, no release.
- **A choice you can take, you take** — weigh the options in the open and say which and why; needing
  an answer to proceed is the bar for asking. **An undecided question in a plan is a stop, not a
  guess**: *how* to build what a plan specifies is yours, *what* it should have specified is not.
- **Iterate: build → adversarially review → fix → re-review until a pass finds nothing**, a commit per pass.
- **At each increment boundary, judge whether the context should be cleared. If so, finish the
  handoff, say so, and stop** — clearing is the user's command. **Write the handover before you
  stop, in the same branch as the work**; an implementer *proposes* its planner-owned rows as diffs
  ([BUILDING § Hand over before you stop](docs/BUILDING.md#hand-over-before-you-stop)).

## What is live right now

- **⏸ DEVELOPMENT IS PAUSED, except option A** (this overrides *Working mode*): pick up no other
  row; resume the rest only on the user's word. Releases are not held (lifted 20260904). The way
  back in: [the pause handover](plans/20260904_1027-development-paused-handover-and-evidence.md).
- **Option A** ([its plan](plans/20261018_2354-option-a-review-coverage-and-claude-md.md)): A0–A3
  landed; **A4, the PATCH release carrying A, is the planner's and remains** (§ 2 status, § 8 handover).
- **Option B** ([plan](plans/20261019_0817-option-b-dogfooding-on-ramp.md)): designed, not built; build paused.
- **The live build order**: [§ 3 of this plan](plans/20260901_1148-clear-the-user-facing-list.md).
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

## Documentation has one owner

**The planner owns every document in this repo. No other agent edits one — it proposes.**

| | |
|---|---|
| **Planner-only** | `docs/**`, `plans/**`, **any `README.md`, at any depth**, `CLAUDE.md`, `CHANGELOG.md` |
| **Yours to write** | `changelog.d/` and `retro.d/` fragments; docstrings and comments in `src/`, `tests/`, `tools/` |
| **One narrow exception** | `docs/VERIFICATION.md`: add **only** the row a test you wrote requires — `tests/test_verification.py` hard-fails without it |

**Propose as `git diff <sha> -- <file>` against a named commit**, never an edit
([BUILDING § Proposing](docs/BUILDING.md#proposing-a-change-to-a-document-you-do-not-own)). Text
that must land in *your* commit is dictated by the planner and pasted unchanged — **ask, do not
draft** ([§ Content mine](docs/BUILDING.md#content-mine-keystrokes-yours)).

**README and DESIGN.md are version-free** — no version number or "as of vX" claim in their prose.
**Read the seven rules in [docs/README § Conventions](docs/README.md#conventions) before any docs
change.** `docs/` is published on every push to `main`: run `make docs` before landing one.
**Every date carries a time, in UTC** (`YYYYMMDD HH:MM`); new files in `plans/`, `changelog.d/` and
`retro.d/` are named `YYYYMMDD_HHMM-<rest>.md`. **Read the clock, never compose it**; stamps before 20260804 11:32 stay local.

## 🚫 Unbuilt work is named, never numbered

**A version number belongs to a release when it is cut — never before.** Never write `v0.4` for
something unbuilt — in docs, `--help`, an error message or a code comment (increment IDs like `I7b`
stay). The rule: [docs/README § Conventions](docs/README.md#conventions); a name stays until its
release's **final** cut.

| Name | What it is |
|---|---|
| **the template release** | Template ecosystem, `pnk upgrade`, the `sqlite-vec` tier |
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
increment, `./check.sh` run bare with its own exit status read, **after your last commit**
(`land.py` refuses a tree no gate certified), mutate the assertions, adversarial review, fragments,
then `tools/land.py`; never batch increments; read the build order out of `plans/`, never "the
newest file". **Read [`docs/INVARIANTS.md`](docs/INVARIANTS.md) before touching a sidecar, the
ledger, the index schema or a paid client** — ULID permanence, sidecar byte-identity, `docs/` is the
user's, `.pinakes/` disposable, append-only ledger, `Decimal` money, `schema_version` — each fails silently.

**Tooling:** uv only (never pip, poetry or a hand-managed venv); Python 3.13+; `ty` is a pre-check,
never the gate. **Core dependencies stay light**: nothing pulling torch enters `[project.dependencies]`.

## Landing work: always push, always release

**Nothing is done until it is pushed to `origin/main` (then `git pull --ff-only` the primary
checkout) and, when it completes a unit of work, tagged by the planner** ([`RELEASING`](docs/RELEASING.md)
holds the MINOR / PATCH / MAJOR rule):

- **Before merging, run `python3 tools/shared_file_overlap.py --fetch --strict`** and *read* the
  merged state of the files it names — **a clean auto-merge is not a correct merge.** It **cannot
  see a peer**: intersect file sets with every live branch yourself ([RELEASING § Landing beside a
  peer](docs/RELEASING.md#landing-beside-a-peer)).
- **A tag publishes to PyPI**, which never accepts a version twice: `make release-check` runs
  **before the push**, never after, and **before that tag read `minimum-python`'s conclusion in the
  CI run for the commit you tag** — the one leg on the declared floor, run only on `main`.

## Changing retrieval

Any change to chunking, fusion weights, reranking or the confidence signal must be justified by the
golden-set eval (`recall@k`, MRR, false-abstain rate), with before and after numbers in the commit
message. **Name the corpus that can license it:** `tests/demo-kb`'s golden set is a regression guard,
not a licensing instrument — a claimed improvement needs the RFC corpus (`tools/build_rfc_corpus.py`)
or another corpus whose improvable pool has been **re-measured, not remembered**
([DESIGN § What a corpus can license](docs/DESIGN.md#73-what-a-corpus-can-license)).

<!-- Provenance. Role rule: the user, 20260823. Working mode: the user, 20260808 04:39 (stop at a clear-context boundary 20260811 15:37). Ownership table: the user, 20260801 01:24. Pause: the user, 20260904 10:21, to review the process against the analysis "Framing, Not Roles" (artifact 2c7961ec); option A resumed 20261018. Until A3 (20261019) the live block was ~265 lines of incident narrative: `git show f1804ea:CLAUDE.md`. -->
