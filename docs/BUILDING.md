# Building an increment

**Audience: the agent building it. Goal: executor.** Follow it in order. This is the procedure that
runs *before* [Cutting a release](RELEASING.md); the rules about when to release are in
[`CLAUDE.md`](https://github.com/lucagattoni/pinakes/blob/main/CLAUDE.md).

Extracted from `CLAUDE.md` on 20260806 00:00, when that file crossed its own size guardrail — as
`RELEASING.md` was on 20260801. Nothing was dropped in the move. **Which plan is live stays in
`CLAUDE.md`**, because it changes every few days and this procedure does not.

## Read the build order out of `plans/`

**Never "the newest file" there.** That directory also holds shipped plans, an iteration log,
standalone increments, re-entry checklists and decision records;
[`docs/README.md`](https://github.com/lucagattoni/pinakes/blob/main/docs/README.md) has the table
that tells them apart, and `CLAUDE.md` names the one that is live.

## One increment at a time

Never batch increments; each is a separate, bisectable landing:

1. Own worktree, branch `YYYYMMDD_HHMM-i<N>-<slug>`.
2. Implement the increment **with its tests** — tests ship in the increment that introduces the
   behaviour, never deferred.
3. Green before review: run `./check.sh` (or `make check`) — every gate under `set -e`, so a
   failure is a non-zero exit rather than a line in a log that a pipe then swallows. It formats
   Python **inside Markdown fences** too: a docs-only commit can still fail the gate.
   **Then break the code on purpose.** Mutate the 3–5 most safety-critical assertions, confirm the
   *right* test fails for the *right reason*, restore. **"Mutation-verified" is a per-assertion
   claim, never a per-commit one.** Worked cases: [RETROSPECTIVES.md](RETROSPECTIVES.md) § *Start
   here* → "claim a test is mutation-verified".
4. **Retrospective review** — a fresh adversarial pass over the increment's own diff, repeated
   until clean. Findings and fixes are their **own commit**. Anything worth keeping gets a
   [`retro.d/`](https://github.com/lucagattoni/pinakes/blob/main/retro.d/README.md) fragment; trivia
   stays in the commit message.
5. **A `changelog.d/` fragment in the same commit as the code** — never an edit to `CHANGELOG.md`
   itself
   ([`changelog.d/README.md`](https://github.com/lucagattoni/pinakes/blob/main/changelog.d/README.md)).
6. Land it: `python3 tools/land.py <branch> --cleanup`. **Never `git merge` by hand** — from inside
   the branch's own worktree that merges the branch into itself and reports success three times over
   ([`CLAUDE.md`](https://github.com/lucagattoni/pinakes/blob/main/CLAUDE.md)).

Which documents an increment touches, and in what order: [`docs/README.md` § Landing a new
increment](https://github.com/lucagattoni/pinakes/blob/main/docs/README.md#landing-a-new-increment).

## Hand over before you stop

**Context dies with the session; disk survives.** So the handover is part of the increment, landed
in the same branch as the work — never a follow-up, because the pointers an increment falsifies are
exactly the ones the *next* session opens first. Set by the user 20260811 15:37, alongside the rule
that a boundary needing a context clear is a **stop** rather than an offer
([`CLAUDE.md` § Working mode](https://github.com/lucagattoni/pinakes/blob/main/CLAUDE.md)).

| Where | What goes stale the moment the increment lands |
|---|---|
| **`CLAUDE.md`'s live-plan pointer** | "Build E1 next" — the first thing any session in this repo reads |
| **`docs/README.md`'s plan-routing row** | the same claim, for whoever opens `docs/` first |
| **The plan itself** | mark the increment built, and record what shipped *beside* what the section asked for — including anything the next increment needs that only this one learned |
| **The plan's baseline / measurement block** | which of its rows this increment just falsified, and how far `file:line` moved. Every plan here has drifted this way; the template release's did about thirty times in four days |
| **[STATUS.md](STATUS.md)** | the surface row — `on `main`, unreleased` between landing and release, then the version |

**A pointer nothing links to is not a handover.** Verify by opening what a fresh session opens —
`CLAUDE.md`, then `docs/`, then the plan — not by trusting that you wrote it down somewhere. A
*missing* row has no wrong text to find, so no diff review and no grep reaches it; only the question
does ([RELEASING.md](RELEASING.md), 20260811).
