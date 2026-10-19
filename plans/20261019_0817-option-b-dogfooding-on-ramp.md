# Option B — the dogfooding on-ramp: what "started" means, and the command that gets there

**Written 20261019 08:17 UTC by the planner session, at the user's instruction; revised 20261019 08:50
UTC after two independent, read-only adversarial reads, whose findings are folded in where they apply
rather than layered on.** **DESIGN ONLY.** Nothing here is built, and **the pause stands for the
build**: the user resumed option A
([`plans/20261018_2354-option-a-review-coverage-and-claude-md.md`](20261018_2354-option-a-review-coverage-and-claude-md.md))
and asked for *"then plan option B's dogfooding on-ramp"* — a plan, not a build. Increments B0–B4
start only when the user lifts the pause for them (§ 9). **Do not pick one up because this file
exists.**

## 1. The instruction, and what it left open

Row 21 of [`plans/20260901_1148-clear-the-user-facing-list.md`](20260901_1148-clear-the-user-facing-list.md)
records the user's instruction of 20260902: *"build the on-ramp this week — a checklist and a
one-command start."* That row also records what was missing: **"no plan states what the command does,
what the checklist checks, or what 'started' means"**, and *Working mode* forbids guessing what the
plans have not decided. This file decides those three things, marks the decisions that are not the
planner's to take (§ 4), and says what each increment must prove (§ 6).

*"This week" was the user's word, was recorded and not converted into a date, and is now seven weeks
old.* That is itself evidence about the on-ramp: see § 7.

**Why it is written now and not after A lands.** Option A's plan says option B is *"written after A
lands, not folded into it"*; this file is written while A2–A4 are open. That is the planner's
judgement, not an instruction: the user's words were *"then plan option B"* and, on 20261019,
*"coordinate with A2, be autonomous unless you need me"*. It touches no file the option A session reported editing (A3's file set is open, so A3 re-checks
`docs/README.md` when it lands), adds no
code, and lifts nothing. If the user wants it held back until A4, it can be reverted whole.

## 2. What is true today

Read or run on 20261019 from about 08:00 UTC, as read-only planning evidence in scratch directories —
nothing was added to this repository by it. A number here moves when the thing it counts moves, so
re-read before quoting it. B0 (§ 5) is the record; this table is what the design was built on.

| Fact | Source |
|---|---|
| The dogfooding KB `pinakes-kb` is a **private sibling repository** with **one commit** (20260804), an **empty `docs/`**, **no `.pinakes/`**, and a clean working tree except an untracked `.DS_Store`. A `.venv` exists (modified 13 October); its contents were not inspected | `git log`, `ls`, `git status` in the sibling checkout |
| That KB is **stale against the product it dogfoods**: `uv.lock` pins `pinakes` **0.7.1**, `pyproject.toml` asks for `pinakes[light]>=0.7.1`, the manifest is stamped `notes@1.0` with `provider = "fastembed"` under `[embedding]`. The published release is **0.32.6** and the template this build stamps is `notes@1.2` | `uv.lock`, `pyproject.toml`, the first lines of `pinakes.toml` there; `pnk --version` and `pnk init` here |
| **First-use friction has a record, and every entry in it has a recorded closure.** `FRICTION.md` in the RFC corpus holds **ten entries** written 20260803–04 against 0.7.1. [`plans/20260731_1202-open-corrections.md`](20260731_1202-open-corrections.md)'s Closed table disposes of all ten (`docs/STATUS.md` points there): **#1** the Guide leads with `uv init` or `uvx`; **#2** `init` adopts a populated directory and never overwrites; **#3** the `[light]` error names the manifest edit, not the 2 GB install; **#4** a throttled progress line **on a terminal**; **#5** `sync completeness`, a WARN whose remedy is `pnk sync`, replaced a FAIL that prescribed `--rebuild`; **#6** `sync`'s own stamp and the price clock moved to UTC to match the lock; **#7** the Guide row says same-host locks are reclaimed; **#8** `[chunking] headings = "numbered"`, opt-in, plus a heading-coverage check; **#9** a `titles` check that reports and never warns, the filename fallback kept on purpose; **#10** `doctor` strips the KB root from paths and **leaves paths outside the KB — the model cache, a linked KB — as printed, by decision**. What is **not** on record is any run of those closures on a terminal, or of the path from nothing to a used KB | `FRICTION.md` there; `plans/20260731_1202-open-corrections.md` Closed table; `docs/STATUS.md:558`. *An earlier draft of this row said six of the ten were unchecked; a reviewer found the table and it was right.* |
| **What the rehearsal on 0.32.6 (§ 3.5) is consistent with, and does not show:** #1 — `uv add "pinakes[light]"` in an empty directory exits 2 with *No `pyproject.toml` found*; **the Guide warns about it and README § Quickstart (lines 74–75) still opens with `uv add`**, so the README is the half the closure did not reach. #4 — a captured, non-terminal run printed nothing while it worked, which is what a terminal-only progress line predicts; a terminal was not tried. #8, #9 — fine on Markdown (`7133 of 7137 chunks carry a heading path`, `all 65 titles are the author's`); the plain-text corpus both entries are about was not run. #10 — the model-cache path printed, as decided | the rehearsal; `README.md:74-75`; `docs/GUIDE.md:42` |
| The pieces of an on-ramp exist **scattered**: the Guide covers Python 3.13+, the extras and their disk cost (`[light]` ~100 MB, `[st]` ~2 GB), the one-time ~1.4 GB weight download, `uv init`, adopting a populated directory, the backend flag and the `.mcp.json` entry; `pnk init` prints the three steps after it runs. **No document walks them in order, and none says what counts as *used*** | `docs/GUIDE.md` §§ Install (36–85), Your first KB (87–190), Using it from an agent (607–639) |
| A **fresh** `pnk init --backend light` on 0.32.6, then `pnk doctor`, exits **0** with **five WARNs** before the first sync (both model revisions unpinned, *index not built*, *not a git repository*, price table 44 days old) and **six** after it (*index not built* goes; *no fitted calibration thresholds* and *no authored links* arrive). The price-table WARN follows **the release's age, not the KB**, and its own remedy says to upgrade; the user *can* clear it by adding `max_price_age_days` to `[budget]` (the stamped manifest does not carry the key; the default is 30), which changes a safety setting, so the checklist says so rather than hiding it | the rehearsal; `docs/MANIFEST.md:201` |
| **`pnk upgrade` cannot compare a `notes@1.0` KB**: *"cannot compare: notes@1.0 is not in this build's archive"*, exit 3, `--apply` writes nothing. The Guide documents it, says it was re-run against 0.28.1 on a KB created before the archive existed, and gives the route: `pnk init` on a throwaway directory and diff its `pinakes.toml` against yours | `docs/GUIDE.md:743-763` |
| **`pnk doctor` is not safe to relay.** Its `titles` line prints up to three document **paths** when titles are still minted from filenames (`doctor.py:845-851`); a FAIL can carry a path outside the KB (`doctor.py:140`); and the `OK model cache: weights resolve under …` line is emitted **unconditionally** after the backend loaders (`doctor.py:349`), so it is no evidence that weights are present — the evidence is the `embedding` and `reranker` lines, which load offline and FAIL when the cache is empty. `doctor` has no `--json` and exits 1 on a FAIL | `src/pinakes/doctor.py` |
| Sync mints a sidecar **beside every document, inside the KB**, and `roots` / `include` must stay inside the KB. **A KB over this repository's own `docs/` would therefore commit ~65 sidecars into a public repository**, or has to live in a copy | `docs/MANIFEST.md:78-94` and `:340` |

## 3. The design

### 3.1 What "started" means

**A ladder, not a boolean — and the command is never green on an empty KB, nor on a probe that could
not have failed.** The lesson is the one option A's review workflow met: an instrument that reports
success because nothing went wrong, when nothing was exercised, is the failure — the shape that
workflow calls `VACUOUS` ([plan § 3](20261018_2354-option-a-review-coverage-and-claude-md.md)).

| Verdict | Means | Exit |
|---|---|---|
| **INDEXED** | `pnk doctor` has no FAIL; the index holds **as many active documents as the tool's own count of indexable files** (below, where a count match is shown to be necessary and not sufficient); and the **probe passed** | 0 |
| **NOT READY** | A blocking check failed: no `pnk` for the KB (§ 3.3), its installed `pinakes` older than the checkout the tool lives in, the manifest's `provider` not installed, weights absent, a `doctor` FAIL or a `doctor` that printed no status lines, a refused or failed `--sync`, a search that raised, or the path is not a KB. **Anything the tool cannot classify is NOT READY with the reason named; it never turns an unexpected state into INDEXED.** `pinakes-kb` is expected to be here (its lock pins 0.7.1; the version installed in its `.venv` was not inspected) | 10 |
| **NO MATERIAL YET** | The environment works, `docs/` holds **no indexable file** and the index holds **no active document**. The state of a healthy fresh `pnk init`. Said plainly as *waiting on the user*, never as success | 11 |
| **NOT INDEXED YET** | The tool's count of indexable files and the index's count of active documents differ, or the index is missing — **including files deleted since the last sync**. Without `--sync` this is where the tool stops and says which command is next | 12 |
| **NOT PROBED** | The counts agree, and either the index holds **no more chunks than `final_k`** (default 8, `docs/MANIFEST.md:155`) — top-k membership is then guaranteed, only rank 1 informs, at chance 1 in the number of documents, and the tool declines to call that a pass — or **no sentence of eight words or more occurs exactly once on disk** (lists, tables, short notes) | 13 |
| **PROBE FAILED** | The counts agree, a probe was possible, and the document did not come back first. The case the probe exists for | 14 |

**Precedence: the first matching row wins, in the order NOT READY, NO MATERIAL YET, NOT INDEXED YET, NOT PROBED, PROBE FAILED, INDEXED.** Codes 10–14 collide with nothing `pnk` (0–3, `cli.py`), `uv` (0–2) or Python (1, 2) use for failure.

**"Indexable" is counted conservatively, and a count match is necessary, not sufficient.** The tool
globs the manifest's `include` minus `exclude` (read with `tomllib`) and compares the count with
`doctor`'s `index: N active documents` line. It duplicates logic `sync` owns, so a glob that disagrees
with the walk gives NOT INDEXED YET and never INDEXED. **It does not prove the index is current:**
delete one file and add another and the counts still agree, and the probe samples one document.
INDEXED means *the counts agree and one sampled document ranks first*. Currentness is `pnk sync`'s
own report, which `--sync` prints.

**The probe.** A sentence of at least eight words, taken **from the file on disk and not from the
index** (an index-sourced sentence would pass whatever was or was not indexed), verified to occur
**exactly once** across the indexable files, used as the query. It passes when the first hit is that
document; the tool reads the hit's path and prints nothing of it. **B2 measures the pass rate over
every document of the rehearsal corpus and of `tests/demo-kb` before shipping the rule**, and changes
the rule — more candidates, a looser rank — only on that distribution, never on this file's guess. A
probe that fails on healthy documents is a flaky instrument, and a flaky instrument gets disabled.

**"Started", the milestone, is wider than the command can see**, and the command must not claim what
it cannot observe: INDEXED **plus** (a) a dated line in the KB's friction file — *friction*, *used,
nothing to report*, or *not used* — and (b) the KB attached to an agent over MCP. The command
**prints** (a) and (b) as open items; it does not tick them. The three-way line matters: a null log
must tell *no friction* from *no use*, and only the user can attest which.

### 3.2 The checklist — `docs/DOGFOODING.md`, planner-owned

One document, five parts, each a list of things that are true or false rather than advice. Its
content is fixed by B0's measurements, not by this file.

1. **The machine.** What is already in the Guide, in order and once: Python 3.13 through `uv`, never
   the system interpreter; the extra and its disk cost; **the one-time weight fetch — which command,
   measured**, because `doctor` runs offline and will FAIL on an empty cache; **the WARNs a KB shows
   before and after its first sync, and which are expected**, so a first user does not read a normal
   report as a broken one; and the price-table WARN with the `max_price_age_days` choice stated.
2. **The material.** *What* goes in is the user's (D-B5). What the checklist fixes: text the user
   would search again within a week; **nothing that cannot sit in a private repository**; the KB is
   its own private repository; `.pinakes/` ignored before the first sync; sidecars committed.
3. **The first sync.** What it costs per megabyte on this machine (§ 3.5), the progress line a
   terminal shows, and the recovery from an interrupted first sync (`sync completeness` → `pnk sync`,
   never `--rebuild`).
4. **Use.** `pnk search`, `pnk ask`, and the `.mcp.json` entry — **with the PATH question settled**:
   the Guide's snippet runs a bare `pnk`, and in a `uv` project `pnk` lives in the project's
   `.venv/bin`, which an agent harness does not have on its `PATH` (B0 measures; until then this is
   a suspicion, not a finding). **Five real questions the user actually had this week, written into
   `eval/questions.yaml` before any measurement**, because a question set written after the result
   is not a test.
5. **Recording friction.** The format `FRICTION.md` used — *the exact command, what the docs led me
   to expect, what happened* — kept in the KB's own repository. **Sanitise before anything reaches
   this repository** (`retro.d/`): no home paths, no hostnames, no document text, no titles from the
   private KB. This repository is public.

### 3.3 The command — `tools/dogfood_start.py`

**A developer tool in this repository, not a `pnk` subcommand** (D-B1). One invocation, idempotent,
safe to re-run after adding material:

    uv run python tools/dogfood_start.py <kb-path> [--create] [--backend light|st] [--sync] [--pnk <command>] [--verbose]

**Which `pnk` runs is the KB's own** (D-B8): the tool runs `<kb-path>/.venv/bin/pnk` **directly**, with
`--kb <kb-path>`, or the command named by `--pnk`. It does **not** use `uv run`, which the second
review measured: with `--frozen` it still syncs the environment (creates a missing `.venv`,
reinstalls a stale package); with `--no-sync` it can fall through to whatever `pnk` is first on
`PATH`; `--project` does not set the working directory; and uv's own failures exit 1 and 2, the codes
`pnk` uses. So INDEXED is a claim about one named executable — the environment a `uv`-project
`.mcp.json` entry would use (B0 settles which command the entry runs). A KB with no such executable
is **NOT READY**, with the Guide's two commands (`uv init && uv add "pinakes[light]"`); a `pinakes`
older than the checkout the tool lives in (its `pnk --version` is the floor — the installed version,
not the lock) is **NOT READY** with the upgrade command. The tool never resolves, installs or
fetches.

| Step | What it does | What it will not do |
|---|---|---|
| 1 | Find or create the KB: `--create` runs **this checkout's** `pnk init` (it only stamps files) with the stated backend, and the verdict is then NOT READY — the new KB has no environment yet — naming the next command; without `--create` a path that is not a KB is **NOT READY**, not an invitation | Create anything without `--create` |
| 2 | Environment: the KB's own interpreter and `pinakes` version, the installed extra against the manifest's `provider`, weights read from `doctor`'s `embedding` and `reranker` lines | Trust `doctor`'s `OK model cache` line (§ 2), or touch the network |
| 3 | `pnk doctor`, parsed by **status prefix only**: it prints each check's **name and status** (`WARN price table`) and drops the detail text. Expected WARNs are named as expected | Relay `doctor`'s detail text by default: it contains document paths and out-of-KB paths (§ 2). `--verbose` is the human's opt-in |
| 4 | Count indexable files (§ 3.1). None → **NO MATERIAL YET** | Succeed on none |
| 5 | With `--sync`, run `pnk sync`, print the time per megabyte it measured. **Refuses first** unless `doctor`'s `machine-driven spend` line is OK and, inside a git repository, `.pinakes/` is ignored | Run `--rebuild`, `--force-unlock` or `doctor --prune`, pass `--extract`, or run `ask --deep`. The embedding backends here cannot spend; the paid paths are `[extraction]` and `--deep`, and the tool reaches neither |
| 6 | The probe and the verdict (§ 3.1), then the open checklist items | Print a title, a path or a sentence of the KB by default |

It **never edits a document, never commits, never pushes, and never touches a repository other than
the one it was pointed at.** It is a thin orchestrator over `pnk` and imports nothing from
`src/pinakes`. `tools/` is not part of the wheel — 0.27.0 verified that by reading the wheel (78
entries, none under `tools/`, `docs/RELEASING.md`) — and B2 verifies it again rather than assuming
it. It runs under the `.python-version` interpreter (`uv run python …`): on the maintainer's machine
the system `python3` is Xcode's 3.9, which already failed `./check.sh` once for a tool that needs
3.10+.

**What a B2 builder is told, because the review of this file found them missing.** The `pnk` command
prefix is **injectable**, so the tests substitute a stub that prints canned `doctor`, `search` and
`sync` output — the repository's suite already skips tests whose prerequisites are absent (`CLAUDE.md`
records 126 skipped in the 0.32.6 `minimum-python` run, without breaking down why), and a tool whose
tests all need model weights cannot be tested where it matters; one real-weights test follows that
skip pattern. **Scenarios that need a real KB environment use a fixture helper** that builds a
throwaway `uv` project pinned to this checkout (an editable path dependency): `pnk init`, the
`tests/demo-kb` copy and the docs copy have no `pyproject.toml` or `.venv` of their own, so without it
each reads NOT READY. A KB "older than the checkout" is built with the stub, which reports an older
`--version`. The tests add their row to `docs/VERIFICATION.md` (the one
document an implementer may touch, and only for a test they wrote).

**B0 may shrink it.** Steps 2 and 5 were sketched against first-use failures that § 2 shows already
closed. If B0 confirms the closures hold on a terminal and on a killed sync, what remains is the
verdict, the probe and leak-safe output. **Build the smaller thing the measurement leaves, not the one
this table sketches.**

### 3.4 What neither half does

No new product surface, no new `pnk` command, no MCP tool, no manifest key. No change to retrieval
(so the golden-set rule in `CLAUDE.md` § *Changing retrieval* does not apply). **No agent reads the
user's material**: the user runs the command, on their machine, and its output is names, statuses
and counts. A builder may help with the *environment* (the lock, the manifest hand-diff) and never
opens `docs/`. Friction entries are written by the user, or by an agent beside them from output the
user pastes; an agent is never pointed at the private repository to harvest them.

### 3.5 Rehearsal — this repository's own docs as the acceptance corpus

The command needs a corpus that is real, structured, public and larger than `tests/demo-kb`.
`docs/` plus `plans/` plus `CLAUDE.md` is **65 documents, 4.3 MB** (largest: `RETROSPECTIVES.md`
961 KB), and **can** be used because a throwaway **copy** carries its own sidecars (D-B4). Run on
20261019 from 08:13 UTC, `pnk` 0.32.6, `--backend light`, model weights already in the Hugging Face
cache, an Apple-silicon laptop, a scratch KB; the script (`b_rehearsal.py`) lives in the planner's
scratchpad and is not committed. The repository was only read.

| Step | Result |
|---|---|
| `pnk init --backend light` | 0.1 s, exit 0; prints the three `Next:` lines |
| `pnk doctor`, 65 documents and no index | exit 0, 1.6 s, **five WARNs** (§ 2) |
| `pnk sync`, the first | **338 s** wall, exit 0, `65 indexed`, **7,137 chunks** — about 79 s per MB of source. Two lines of output, both at the end; nothing while it ran. The run was captured and not a terminal |
| `pnk doctor`, after | exit 0, 1.0 s, **six WARNs** (§ 2). `OK titles: all 65 titles are the author's`; `OK heading coverage: 7133 of 7137 chunks (100%)` |
| `pnk search`, four queries | 3.0–3.2 s each, exit 0, up to eight hits **with the chunk text**. Judged by the planner against what it knows of the repository, not against a golden set: the document that owns the answer was in the top eight for **three** queries (ranks 1, 2 and 5/7) and **absent for one** — *"who owns CLAUDE.md and which documents may an implementer edit"* did not return `CLAUDE.md`'s own *Documentation has one owner*. Not investigated; a seed for the user's five real questions and **not a retrieval measurement** |

**What this changes in the design.** (1) A first sync of a realistic corpus takes minutes, not the
hours the 0.7.1 record shows, so the checklist's time figure is a measured rate with a caveat.
(2) **`pnk search` prints chunk text, so an agent running it against a private KB puts that text into
a stored transcript** — which is why § 3.3 prints names, statuses and counts and nothing else.
(3) A fresh install of a release more than 30 days old shows the price-table WARN; option A's A4 cut
refreshes `prices.toml` (`docs/RELEASING.md` § *Before you start*, step 3), and it will recur. Whether a
WARN that follows the release's age should fire at all on a backend that cannot spend is a product
question, listed here and **not** taken: the pause forbids it.

## 4. Decisions

| # | Decision | Taken by | Choice | Why — and what reverses it |
|---|---|---|---|---|
| **D-B1** | Where the start command lives | planner | `tools/dogfood_start.py`, not a `pnk` subcommand | Row 21 is about **this maintainer's** dogfooding. A subcommand is permanent surface (the naming table makes changes breaking), needs `docs/CLI.md`, the Guide, tests and a MINOR release, and the pause forbids deciding product surface. *Reverses when* a second person asks to start a KB this way — then promote the **verdict and probe** only. If B0 empties the command, drop it; do not promote it |
| **D-B2** | What the command may call success | planner | Six verdicts, distinct exit codes, success only when the index matches the files and a probe that could fail has passed | § 3.1. A command that exits 0 on an empty KB, or on a probe that returns every chunk, is the "ran, measured nothing" defect option A exists to remove from the review fan-out; it is not reintroduced one level over |
| **D-B3** | What the command may change | planner | Nothing unless `--create` / `--sync`; never a document, a commit or a rebuild | The user's documents are the user's ([`docs/INVARIANTS.md`](../docs/INVARIANTS.md)); a rebuild is the destructive remedy entry #5 warned about |
| **D-B4** | Acceptance corpus | planner | A throwaway **copy** of this repository's `docs/`, `plans/`, `CLAUDE.md` | An in-place KB mints ~65 sidecars into a public repository (§ 2). The copy costs a re-copy before each run; `pnk sync` is incremental, so that is cheap |
| **D-B5** | **Which material starts the private KB** | **the user** | **Not decided by anyone** | An agent cannot choose it and must not read candidates to choose. *Needed:* **one folder of your own Markdown or text, ten documents or more, that you would search again within a week.** B3 waits on it |
| **D-B6** | How `pinakes-kb` is brought up to date | **the user** | **Recommend keeping its id and history, and bringing it up by hand** | The KB id is permanent by rule, the KB has one commit and no content, and `pnk upgrade` **cannot** compare `notes@1.0` (§ 2), so the route is the Guide's: hand-diff its `pinakes.toml` against a fresh `pnk init`, then bump the lock. *Cost, stated:* that is the whole of it — an empty KB exercises the hand-diff and a lock bump and **nothing else**, so it is not a test of `pnk upgrade` or of an upgrade over an index and sidecars; the Guide already records the `notes@1.0` message re-run against 0.28.1. *The alternative is a re-stamp,* equally cheap and fresher, at the price of the id: with no links and no documents it loses nothing real, and it is the user's call whether the rule is worth keeping in letter for an empty KB |
| **D-B7** | Lift the pause | **the user** | **Recommend yes for B0 and B1 now; ask again for B2, B3 and B4 once B0 has read** | B0 and B1 are measurement and a document; B2 is code whose size B0 decides, and B3 and B4 depend on the user's material and time, not on the planner |
| **D-B8** | Which `pnk` the command runs | planner | The KB's own executable, run directly (`<kb>/.venv/bin/pnk` or `--pnk`), with the checkout's version as the floor | § 3.3. Running this checkout's `pnk` against a KB whose environment is 0.7.1 would print INDEXED for an environment that cannot serve the index; and `uv run` was measured to sync, to fall through to another `pnk`, and to share exit codes 1 and 2 with `pnk` |

## 5. Increments

| # | What | Owner | Needs | Done when |
|---|---|---|---|---|
| **B0** | **Verify the ten recorded closures where a closure can fail, on 0.32.6, each on a small corpus:** the first sync on a **terminal** (progress line); a **killed** first sync, then `pnk doctor` (`sync completeness`, no FAIL, no `--rebuild`); a plain-text sample with `headings = "numbered"`, and its titles; the one-time weight fetch on an empty cache (**which command**); the `.mcp.json` entry in a `uv` project (bare `pnk`); the README's `uv add` line. Output: a table in this file, `HOLDS` / `FAILS` / `CHANGED` / `NOT TESTABLE`, each with the output quoted. The 300-document runs are **not** repeated. B0 verifies the closures; it does not rediscover them | planner | D-B7 (yes) | Every row carries a quoted output. Its size is not estimated here: each item is stated on ten documents on purpose |
| **B1** | `docs/DOGFOODING.md` and a routing row, from B0's table. Includes the expected-WARN list | planner | B0 | The document's every claim carries a measured output, or says *unstated* |
| **B2** | `tools/dogfood_start.py`, tests with the fixture helper and the injectable stub (§ 3.3), a mutation battery, a `changelog.d/` fragment, a `docs/VERIFICATION.md` row. Scope after B0 (§ 3.3) | builder | B0, a second yes | § 6 passes, **including the probe's measured pass rate and its negative control** |
| **B3** | First run on `pinakes-kb`: bring its environment up (D-B6), point it at the user's folder, first sync, five real questions into `eval/questions.yaml` | **the user**; a builder for the environment only | D-B5, D-B6, B1, B2 | The verdict is **INDEXED** and the user ran it |
| **B4** | Friction entries, **written by the user** and sanitised before they reach `retro.d/` (§ 3.2 part 5), as findings arise; **and the stop-loss in § 7 evaluated** | the user; planner for the fragment | B3 | A dated entry or a dated *not used* line per week |

## 6. Acceptance for B2 — what has to be shown, not asserted

1. **Every verdict, with its exit status and output quoted**, each built on the fixture helper or
   the stub of § 3.3: an empty `pnk init` KB → NO MATERIAL YET (11); files on disk and no sync, and
   separately a synced KB with one document deleted → NOT INDEXED YET (12); a KB whose installed
   `pinakes` is older than the checkout (the stub reports an older `--version`), a path with no
   executable, and a `--create` run that has just stamped a KB → NOT READY (10); a copy of
   `tests/demo-kb`, which has **more chunks than `final_k`** → INDEXED (0); a two-document KB, and a
   KB of short notes with no sentence of eight words occurring once → NOT PROBED (13); a synced KB
   whose probe document's text is then **replaced on disk with unrelated text of at least eight
   words, the file count unchanged** → PROBE FAILED (14); and this repository's docs copy (§ 3.5) →
   INDEXED with the time per megabyte.
2. **The probe is a positive control with a measured pass rate:** over every document of the
   rehearsal corpus and `tests/demo-kb`, the share whose own sentence returns it first is recorded in
   B2's retrospective before the rule is fixed.
3. **Nothing from the KB leaks by default, including through `doctor`.** A fixture KB holding a
   `.txt` file (so the `titles` line prints a path) and a forced FAIL that carries an out-of-KB path:
   the default output contains **no path, title or sentence of any document and no home directory**.
   A test on the output, not a promise in a docstring.
4. **It never touches the network**, and a stub `pnk` that records its argv shows it never passed
   `--rebuild`, `--extract` or `--deep`, and ran `--sync` only when asked, and never passed `--force-unlock` or `--prune`.
5. **Mutation battery** per `tools/batteries/README.md`, **calibrated by an outsider's mutants**, not
   only the author's: A1's first battery killed 22 of 22 and a reviewer who then wrote 62 mutants of
   its own saw 50 survive ([the option A plan](20261018_2354-option-a-review-coverage-and-claude-md.md),
   its handover section).
6. Adversarial review before landing, and a read of the CI logs after.

## 7. The honest risk: this could become shelfware

**The bottleneck was never the tooling.** The sweep classed the dogfooding KB as *needs the user's own
material* (row 24), the user overrode the classification with an instruction to build the on-ramp,
and seven weeks later the KB still has an empty `docs/`. A checklist and a command lower the cost of
starting; **they do not supply the reason to start.** The plan says so rather than letting a finished
on-ramp read as finished dogfooding.

**Two stop-losses, because the stall that is on record happened before any first run.**

- **Before B3.** If **four weeks after the user lifts the pause for B0–B1** D-B5 is still unanswered,
  record *no material chosen* and stop. The clock starts at an event the user controls and the
  planner can date; it does not start at B3, which waits on the very answer being measured.
- **After B3.** If **four weeks after its first sync** the KB shows fewer than ten indexed documents
  (the tool counts) or no dated line in the friction file (the **user** attests which of *friction*,
  *used, nothing to report* and *not used* it is — the tool cannot see whose documents they are),
  record that dogfooding **did not happen**, which is a different finding from *dogfooding found
  nothing* and the only honest reading of a null — and stop building on-ramps.

The cost of B0 and B1 is not estimated here (§ 5); the cost the stop-losses protect is the next
on-ramp.

## 8. Constraints that bind

- **This repository is public.** The private KB's content, titles, paths and sentences never enter it,
  in a plan, a fixture, a fragment or a test. Vet every file before staging (`CLAUDE.md` § *This
  repository is PUBLIC*, and the global PRIMARY CHECK). § 2 states only structural facts about the
  private KB — a commit count and date, an empty folder, a pinned version, a template stamp, a
  provider name — that the plans in this repository already record or that carry no content.
- **Ownership.** `docs/DOGFOODING.md`, this file and the routing row are planner-owned; B2's code,
  tests, battery, fragment and `VERIFICATION.md` row are the builder's; the builder **proposes** any
  other document change as a diff against a named commit.
- **Instruction files.** This file does not edit `CLAUDE.md`. Its pause bullet reads *"paused, except
  option A"* and gains its pointer to this plan in **A3**, which regenerates that block with the diff
  shown to the user first. Option A's plan § 9 still says option B is *not designed yet* and
  written after A lands. It is **not** on the edit list option A's session reported, so it is stale
  once this lands: the planner corrects it after A2 is on `origin/main` (or option A's session adds
  it, if it agrees), and until then `docs/README.md`'s rows and that section disagree.
- **Unbuilt work is named, never numbered.** Nothing here is assigned a version.
- **Landing** is `tools/land.py`, with `./check.sh` run the way A0 and A1 ran it
  (`PATH="$PWD/.venv/bin:$PATH" env -u PYTHONDONTWRITEBYTECODE ./check.sh`, status read from a log).
- **A release is not needed for B1; B2 adds a `tools/` file that does not ship**, and the 0.27.0
  precedent says to verify its absence from the wheel (`docs/RELEASING.md`).

## 9. What the user is asked

1. **Lift the pause for B0 and B1?** (D-B7) — recommended yes. B2, B3 and B4 are asked about
   separately, after B0 has read.
2. **D-B5: name the folder** that starts `pinakes-kb`. Until then B3 cannot start and the command can
   only ever say NO MATERIAL YET, or NOT READY while the lock is old.
3. **D-B6: how to bring `pinakes-kb` up to date** — keep the id and update by hand (recommended), or
   re-stamp.

Nothing else in this file needs the user. **Not done and not decided here:** whether each recorded
closure still holds on a terminal and on a killed sync (B0), the content of the checklist beyond
§ 3.2's skeleton (B1), and whether B2 survives B0 at its sketched size.
