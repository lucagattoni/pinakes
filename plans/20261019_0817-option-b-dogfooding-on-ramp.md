# Option B — the dogfooding on-ramp: what "started" means, and the command that gets there

**Written 20261019 08:17 UTC by the planner session, at the user's instruction; revised 20261019 08:50
UTC after two independent, read-only adversarial reads, and again at 20261019 12:25 UTC with B0's results
(§ 5.1); the findings are folded in where they apply rather than layered on.** **DESIGN, WITH B0 RUN
AND B1 WRITTEN.** Nothing is built, and **the pause stands for the build**: the user resumed option A
([`plans/20261018_2354-option-a-review-coverage-and-claude-md.md`](20261018_2354-option-a-review-coverage-and-claude-md.md))
and asked for *"then plan option B's dogfooding on-ramp"* — a plan, not a build. **On 20261019 the
user lifted the pause for B0, a measurement, and B1, a checklist document, and for those two only**;
B2, B3 and B4 start only when the user lifts it for them (§ 9). **Do not pick one up because this
file exists.**

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
| **First-use friction has a record, every entry in it has a recorded closure, and B0 has now run all ten against the published 0.32.7 (§ 5.1).** `FRICTION.md` in the RFC corpus holds **ten entries** written 20260803–04 against 0.7.1, and [`plans/20260731_1202-open-corrections.md`](20260731_1202-open-corrections.md)'s Closed table disposes of all ten (`docs/STATUS.md` points there). **Nine hold as recorded; the tenth, #1, holds in part in the Guide and fails in the README**, whose Quickstart still opens with four bare `uv add` lines. B0 also found four things that no closure covers: `pnk doctor` is not offline and fetched a 1.1 GB reranker, its remedy names a flag `doctor` itself does not have, the Guide's `.mcp.json` snippet runs a `pnk` that is not on the `PATH`, and `uvx --from "pinakes[light]"` and the Guide's own `uv init && uv add` do not resolve on a machine whose newest Python is 3.15 | `FRICTION.md` there; the Closed table; `docs/STATUS.md:558`; § 5.1. *An earlier draft of this row said six of the ten were unchecked; a reviewer found the table and it was right.* |
| The pieces of an on-ramp exist **scattered**: the Guide covers Python 3.13+, the extras and their disk cost (`[light]` ~100 MB, `[st]` ~2 GB), the one-time ~1.4 GB weight download, `uv init`, adopting a populated directory, the backend flag and the `.mcp.json` entry; `pnk init` prints the three steps after it runs. **No document walks them in order, and none says what counts as *used*** | `docs/GUIDE.md` §§ Install (36–85), Your first KB (87–190), Using it from an agent (607–639) |
| A **fresh** `pnk init --backend light`, then `pnk doctor`, exits **0**. On the published **0.32.7**: **four WARNs** before the first sync (both model revisions unpinned, *index not built*, *not a git repository*) and **five** after it (*index not built* goes; *no fitted calibration thresholds* and *no authored links* arrive). On **0.32.6**, whose price table was 44 days old, the rehearsal showed five and six — the extra one is the price-table WARN. The price-table WARN follows **the release's age, not the KB**, and its own remedy says to upgrade; the user *can* clear it by adding `max_price_age_days` to `[budget]` (the stamped manifest does not carry the key; the default is 30), which changes a safety setting, so the checklist says so rather than hiding it | the rehearsal; `docs/MANIFEST.md:201` |
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
   the system interpreter — **and pinned**, because on 20261019 `uvx --from "pinakes[light]==0.32.7"`
   on a machine whose newest interpreter is CPython 3.15 did not resolve (`onnxruntime` ships no
   `cp315` wheel) and worked with `--python 3.13`, so the install line the checklist gives carries
   the pin (§ 5.1 D); the extra and its disk cost; **the weights, measured (§ 5.1 A and B):** the
   first `pnk sync` fetches the embedder (67 MB), the reranker (1.1 GB) arrives with the first command
   that loads it — a `pnk doctor` run did it — and the `--offline` flag `doctor`'s remedy names is not
   a `doctor` flag (`sync`, `search`, `ask`, `links` and `serve` take it); **the WARNs a KB shows before and after its first sync, and which are expected**, so a
   first user does not read a normal report as a broken one; and the price-table WARN, which a release
   clears for 30 days and which adding `max_price_age_days` to `[budget]` also clears, as a decision
   about a safety setting.
2. **The material.** *What* goes in is the user's (D-B5). What the checklist fixes: text the user
   would search again within a week; **nothing that cannot sit in a private repository**; the KB is
   its own private repository; `.pinakes/` ignored before the first sync; sidecars committed.
3. **The first sync.** What it costs on this machine — 16 to 21 chunks a second, which was
   79 to 130 s per MB of Markdown and 310 s per MB of plain text, so the estimate is made in chunks and not
   bytes (§ 3.5, § 5.1); the progress line a terminal shows (`syncing: 3/8 documents (7.0/min)`) and
   a pipe does not; and the recovery from an interrupted first sync, measured (§ 5.1 row 5):
   `pnk doctor` says `sync completeness` and *Run `pnk sync`*, which resumes and keeps every embedding
   — never `--rebuild`.
4. **Use.** `pnk search`, `pnk ask`, and the `.mcp.json` entry — **the PATH question is measured
   (§ 5.1 C):** the Guide's snippet runs a bare `pnk`, which was not found in this shell, under a
   minimal `env -i` shell, or in `~/.local/bin`; `uv tool install --python 3.13 "pinakes[light]"`
   installs an executable that is, and an absolute path does not depend on the `PATH` of whatever
   launches it. Whether a live agent harness launches with the user's `PATH` was **not tested**.
   **Five real questions the user actually had this week, written into
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
is **NOT READY**, with two commands (`uv init --python 3.13 && uv add "pinakes[light]"` — the Guide's own pair fails on a 3.15 machine); a `pinakes`
older than the checkout the tool lives in (its `pnk --version` is the floor — the installed version,
not the lock) is **NOT READY** with the upgrade command. The tool never resolves, installs or
fetches, and it **enforces** that: it sets `HF_HUB_OFFLINE=1` for every `pnk` it runs, because B0
measured (§ 5.1 B) that a plain `pnk doctor` downloaded the 1.1 GB reranker, while the same `doctor`
with that variable fetched nothing and exited 1 with a traceback — which the tool classes as NOT READY
(a `doctor` that printed no status lines) and never relays.

| Step | What it does | What it will not do |
|---|---|---|
| 1 | Find or create the KB: `--create` runs **this checkout's** `pnk init` (it only stamps files) with the stated backend, and the verdict is then NOT READY — the new KB has no environment yet — naming the next command; without `--create` a path that is not a KB is **NOT READY**, not an invitation | Create anything without `--create` |
| 2 | Environment: the KB's own interpreter and `pinakes` version, the installed extra against the manifest's `provider`, whether `doctor`, run offline, prints status lines for `embedding` and `reranker` at all — it FAILs on an absent cache and crashes on a cache missing one model (§ 5.1 A and B) | Trust `doctor`'s `OK model cache` line (§ 2), or reach the network |
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
`sync` output — the repository's suite already skips tests whose prerequisites are absent (`docs/ROADMAP.md`'s
*Where things stand right now* records 126 skipped in the 0.32.6 `minimum-python` run, without
breaking down why), and a tool whose
tests all need model weights cannot be tested where it matters; one real-weights test follows that
skip pattern. **Scenarios that need a real KB environment use a fixture helper** that builds a
throwaway `uv` project pinned to this checkout (an editable path dependency): `pnk init`, the
`tests/demo-kb` copy and the docs copy have no `pyproject.toml` or `.venv` of their own, so without it
each reads NOT READY. A KB "older than the checkout" is built with the stub, which reports an older
`--version`. The tests add their row to `docs/VERIFICATION.md` (the one
document an implementer may touch, and only for a test they wrote).

**B0 has shrunk it** (§ 5.1, § 5.2). Steps 2 and 5 were sketched against first-use failures that
B0 found closed on a terminal and on a killed sync, so what remains is the verdict, the probe, the
offline enforcement and leak-safe output. **Build the smaller thing the measurement leaves, not the
one this table sketches — and § 5.2 asks whether to build it yet.**

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
cache, an Apple-silicon Mac, a scratch KB; the script (`b_rehearsal.py`) lives in the planner's
scratchpad and is not committed. The repository was only read.

| Step | Result |
|---|---|
| `pnk init --backend light` | 0.1 s, exit 0; prints the three `Next:` lines |
| `pnk doctor`, 65 documents and no index | exit 0, 1.6 s, **five WARNs** (§ 2) |
| `pnk sync`, the first | **338 s** wall, exit 0, `65 indexed`, **7,137 chunks** — about 79 s per MB of source. Two lines of output, both at the end; nothing while it ran. The run was captured and not a terminal |
| `pnk doctor`, after | exit 0, 1.0 s, **six WARNs** (§ 2). `OK titles: all 65 titles are the author's`; `OK heading coverage: 7133 of 7137 chunks (100%)` |
| `pnk search`, four queries | 3.0–3.2 s each, exit 0, up to eight hits **with the chunk text**. Judged by the planner against what it knows of the repository, not against a golden set: the document that owns the answer was in the top eight for **three** queries (ranks 1, 2 and 5/7) and **absent for one** — *"who owns CLAUDE.md and which documents may an implementer edit"* did not return `CLAUDE.md`'s own *Documentation has one owner*. Not investigated; a seed for the user's five real questions and **not a retrieval measurement** |

**What this changes in the design.** (1) A first sync of a realistic corpus takes minutes, not the
hours the 0.7.1 record shows, and the stable figure is chunks a second — 21 here (7,137 chunks in 338 s),
16, 17 and 18 in B0 (§ 5.1) — because the same machine took 79 to 130 s per MB of Markdown and 310 s per
MB of plain text.
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
| **D-B5** | **Which material starts the private KB** | **the user** | **Decided by the user, 20261029, before 17:09 UTC: the RFC corpus repository, `pinakes-corpus-rfc`** — public RFC text, which is not the user's own writing the row asked for; recorded as given. B3 stays paused under D-B7 | An agent cannot choose it and must not read candidates to choose. *Needed:* **one folder of your own Markdown or text, ten documents or more, that you would search again within a week.** B3 waits on it |
| **D-B6** | How `pinakes-kb` is brought up to date | **the user** | **Decided by the user, 20261029, before 17:09 UTC: option 3, a re-stamp — a new id and a fresh `notes@1.2` manifest from `pnk init`. The recommendation to keep the id was not taken.** *Sequencing, which is the planner's and not the user's:* do it after the next release is published, so the fresh KB is stamped by the fixed release; `pnk init` refuses a directory that is already a KB, so the old manifest has to be moved aside or the KB made in a new directory | The KB id is permanent by rule, the KB has one commit and no content, and `pnk upgrade` **cannot** compare `notes@1.0` (§ 2), so the route is the Guide's: hand-diff its `pinakes.toml` against a fresh `pnk init`, then bump the lock. *Cost, stated:* that is the whole of it — an empty KB exercises the hand-diff and a lock bump and **nothing else**, so it is not a test of `pnk upgrade` or of an upgrade over an index and sidecars; the Guide already records the `notes@1.0` message re-run against 0.28.1. *The alternative is a re-stamp,* equally cheap and fresher, at the price of the id: with no links and no documents it loses nothing real, and it is the user's call whether the rule is worth keeping in letter for an empty KB |
| **D-B7** | Lift the pause | **the user** | **Taken 20261019, before 12:11 UTC: yes for B0 and B1 only.** **B2 deferred by the user, 20261019, before 13:01 UTC (§ 5.2); B3 and B4 stay paused** | B0 and B1 are a measurement and a document; B2 is code whose size B0 decided, and B3 and B4 depend on the user's material and time, not on the planner |
| **D-B8** | Which `pnk` the command runs | planner | The KB's own executable, run directly (`<kb>/.venv/bin/pnk` or `--pnk`), with the checkout's version as the floor | § 3.3. Running this checkout's `pnk` against a KB whose environment is 0.7.1 would print INDEXED for an environment that cannot serve the index; and `uv run` was measured to sync, to fall through to another `pnk`, and to share exit codes 1 and 2 with `pnk` |

## 5. Increments

| # | What | Owner | Needs | Done when |
|---|---|---|---|---|
| **B0** | ✅ **Ran 20261019 from about 12:13 UTC against the published 0.32.7; results in § 5.1.** *As specified:* **verify the ten recorded closures where a closure can fail, each on a small corpus:** the first sync on a **terminal** (progress line); a **killed** first sync, then `pnk doctor` (`sync completeness`, no FAIL, no `--rebuild`); a plain-text sample with `headings = "numbered"`, and its titles; the one-time weight fetch on an empty cache (**which command**); the `.mcp.json` entry in a `uv` project (bare `pnk`); the README's `uv add` line; and `uvx --from "pinakes[light]"` with and without `--python 3.13` on a machine whose newest interpreter is 3.15 (seen once, 20261019, unresolvable without the pin). Output: a table in this file, `HOLDS` / `FAILS` / `CHANGED` / `NOT TESTABLE`, each with the output quoted. The 300-document runs are **not** repeated. B0 verifies the closures; it does not rediscover them | planner | D-B7 (yes) | Every row carries a quoted output. Its size is not estimated here: each item is stated on ten documents on purpose |
| **B1** | ✅ **Written 20261019 12:43 UTC**: [`docs/DOGFOODING.md`](../docs/DOGFOODING.md) and its routing rows and nav entry, from B0's table. Includes the expected-WARN list | planner | B0 | The document's every claim carries a measured output, or says it was *not run* or is *from the source* |
| **B2** | ⏸ **Deferred by the user, 20261019, before 13:01 UTC — option (c) of § 5.2 — until a real run of the checklist says what hurt.** *As specified:* `tools/dogfood_start.py`, tests with the fixture helper and the injectable stub (§ 3.3), a mutation battery, a `changelog.d/` fragment, a `docs/VERIFICATION.md` row. Scope after B0 (§ 3.3) | builder | B0, and the user's word after a real run of the checklist | § 6 passes, **including the probe's measured pass rate and its negative control** |
| **B3** | First run on `pinakes-kb`: bring its environment up (D-B6), point it at the user's folder, first sync, five real questions into `eval/questions.yaml` | **the user**; a builder for the environment only | D-B5, D-B6, B1 — and B2 if § 5.2 builds it | The user's documents are indexed and the checklist's probe (`docs/DOGFOODING.md` § 5) passed for three of them — **INDEXED**, if B2 exists |
| **B4** | Friction entries, **written by the user** and sanitised before they reach `retro.d/` (§ 3.2 part 5), as findings arise; **and the stop-loss in § 7 evaluated** | the user; planner for the fragment | B3 | A dated entry or a dated *not used* line per week |

### 5.1 B0 — the ten closures, run

**Run 20261019 from about 12:13 UTC against the published `pinakes` 0.32.7**, installed from the index into a
scratch environment on CPython 3.13.16 (`pinakes[light]`), on an Apple-silicon Mac with the model
weights already cached unless a row says otherwise. The harness is `b0_run.py` in the planner's
scratchpad, not committed — its log holds home paths and a hostname, and is quoted de-homed below.
Corpora: eight Markdown documents of this repository (767 chunks) and six public RFC `.txt` files
(387 KB, 2,189 chunks).

| # | The closure | What was run, and what it printed | Verdict |
|---|---|---|---|
| 1 | The Guide leads with `uv init` / `uvx` | `uv add "pinakes[light]"` in an empty directory: exit 2, *No `pyproject.toml` found in current directory or any parent directory*. `docs/GUIDE.md:42` and `:47` warn and give `uv init && uv add "pinakes[light]"` — after listing the same bare `uv add` lines at `:37-39`. **`README.md:74-77` open with four bare `uv add` lines and no warning** | **HOLDS in part in the Guide, FAILS in the README** — and row D shows the Guide's own route failing on a 3.15 machine |
| 2 | `init` adopts a populated directory | A directory holding `README.md`, `.gitignore`, `pyproject.toml` and `docs/a.md`: `pnk init . --name Adopted` exit 0, *left as they were: .gitignore, README.md*, the four files byte-identical afterwards, and *your .gitignore does not ignore `.pinakes/`*. With an existing `.github/workflows/pinakes.yml`, `pnk init . --ci` exit 1, *Nothing has been created* | **HOLDS** |
| 3 | The `[light]` error names the manifest edit | A KB stamped with the default `st` backend, only `[light]` installed: `pnk sync` exit 1, *the `sentence-transformers` backend is not installed. `fastembed` is already installed on this machine — no install needed. Set `provider = "fastembed"` in both `[embedding]` and `[rerank]` in pinakes.toml…* | **HOLDS** |
| 4 | A progress line on a terminal | Eight documents, 767 chunks, 47 s. On a pseudo-terminal (`script -q`): `syncing: 1/8 documents (20.7/min)` … `syncing: 8/8 documents (10.3/min)`, then the two summary lines. Captured, not a terminal: the two summary lines only | **HOLDS** (terminal only, as recorded) |
| 5 | A killed first sync is resumable and `doctor` says so | SIGKILL 12 s into a first sync that takes about 47 s uninterrupted, two sidecars minted: `pnk doctor` exit 0, **no FAIL**, *WARN sync completeness: the index has no embedding identity recorded yet — an earlier `pnk sync` did not finish. → Run `pnk sync`. It resumes incrementally and keeps every embedding already written — no rebuild is needed*. Then `pnk sync`: stderr *took over a stale sync lock left by a process that is no longer running*, `7 indexed, 1 unchanged`; the final `doctor`: no FAIL, `model coherence` OK | **HOLDS** |
| 6 | The lock and the manifest stamp in one zone | While a sync ran: `sync.lock` `"started": "20261019 12:15"`; `pinakes.toml` `created = "20261019 12:15"`; `date -u` 12:15, local time 13:15 | **HOLDS** — both UTC |
| 7 | Same-host lock reclaim is documented | With the killed sync's lock still on disk, `doctor`: *WARN sync lock: held by pid … since 20261019 12:15 → If no sync is running, the next `pnk sync` reclaims it automatically on this host; across hosts use `pnk sync --force-unlock`*; the next sync did | **HOLDS** |
| 8 | Numbered headings on plain text | The six RFC `.txt` files: by default `0 of 2189 chunks carry a heading path (0%)`, with the remedy in the line (*set `[chunking] headings = "numbered"`*); with it, `1865 of 1955 chunks carry a heading path (95%)`, and `parent-child` edges 0 → 4,395. The default stays size-based **by decision**, and `pnk sync` itself says nothing | **HOLDS** |
| 9 | A `titles` check that reports and never warns | The same files: `OK titles: 6 of 6 documents still carry the title minted from their filename: docs/rfc2251.txt, docs/rfc3568.txt, docs/rfc5023.txt and 3 more`; first sidecar `title: rfc8089`. For the Markdown KB, `all 8 titles are the author's` | **HOLDS as designed** — and that line prints **document paths** |
| 10 | Paths in `doctor` | In-KB paths print relative (`docs/rfc2251.txt`). `OK model cache: weights resolve under /Users/<user>/.cache/huggingface/hub` prints the home directory, as decided. The lock line and `doctor` print the **hostname** (*held by pid … on <host>*) | **HOLDS as decided** |
| A | *not a closure* | An empty Hugging Face cache, `pnk doctor`: exit 1, `FAIL embedding: --offline was requested but no model cache exists at <dir>. → Run once without --offline to populate the cache.`, the same for `reranker` — **and on the same run `OK model cache: weights resolve under <the empty dir>`**. `pnk doctor --help` lists `--kb` and `--prune`: **`doctor` has no `--offline` flag** (it is hard-wired offline, `doctor.py:324-325`), while `sync`, `search`, `ask`, `links` and `serve` take one, off by default | **FAILS in part** — the remedy reads as a flag to drop that `doctor` does not have (it means: go online once — `sync` brings the embedder, the reranker comes with the first `doctor`, `search` or `ask`), and the report contradicts itself |
| B | *not a closure* | *(run by hand after the harness: the timings and the traceback were read off the terminal and are not in its log)* `pnk sync` against that empty cache: *Fetching 5 files* in 2 s by its progress bar, 67 MB (the embedder). **Then `pnk doctor`, which is meant to be offline, printed *Fetching 5 files* again, took 11 s, and the cache grew from 67 MB to 1.1 GB** — the reranker. `src/pinakes/embed.py:192` guards `--offline` only by checking that the cache *directory* exists, and fastembed has no `local_files_only`. With `HF_HUB_OFFLINE=1` the same `doctor` fetched nothing (67 MB) and exited 1 with a **traceback**, `ValueError: Could not load model BAAI/bge-reranker-base from any source` | **FAILS** — `doctor` is not offline, and offline it crashes |
| C | the Guide's `.mcp.json` snippet | `command -v pnk` found nothing in this shell, under `env -i PATH=/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin`, or in `~/.local/bin`; the scratch environment's `pnk` is on no `PATH` until it is activated. `uv tool install --python 3.13 "pinakes[light]==0.32.7"`, into scratch directories, *Installed 1 executable: pnk*, and it prints `pinakes 0.32.7`. **Not tested:** a live agent launching the entry | **FAILS as a copy-paste**: the Guide shows `"command": "pnk"` and its own install route, `uv init && uv add`, leaves `pnk` in the project's `.venv/bin` |
| D | *not a closure* | `uvx --from "pinakes[light]==0.32.7" pnk --version`, no pin: exit 1, *No solution found … `onnxruntime>=1.24.2` has no wheels with a matching Python ABI tag (e.g., `cp315`)*; `uv python list` shows CPython 3.15.0 installed here. With `--python 3.13`: `pinakes 0.32.7`, 1.6 s. **The Guide's own route fails too:** in a scratch directory `uv init --bare` wrote `requires-python = ">=3.15"`, and `uv add --no-sync "pinakes[light]"` did not resolve; `uv init --bare --python 3.13` wrote `">=3.13"` and the same `uv add` resolved (61 packages) | **FAILS without the pin** |

**Findings for the user to rule on — none is taken, because the pause forbids it.** Each is a
separate piece of work with its own owner: (F1) README § Quickstart opens with `uv add`, which the
Guide warns does not work in a KB directory — a one-sentence README edit, the planner's *(closed on `main` by e93b4b9, 20261028)*;
(F2) `pnk doctor` downloads the reranker when the cache directory exists, and crashes with a traceback
when it may not — code; (F3) `doctor`'s remedy names an `--offline` flag that `doctor` does not have (it means: go online once —
`sync` brings the embedder, the reranker comes with the first `doctor`, `search` or `ask`), and it prints `OK model cache` beside two FAILs — text and code; (F4) the Guide's `.mcp.json` snippet needs a `pnk` on
the `PATH` and does not say how to get one — docs; (F5) `uvx --from "pinakes[light]"` and the Guide's own
`uv init && uv add` are unsatisfiable on a machine whose newest interpreter is CPython 3.15, because
`onnxruntime` ships no wheel for it — docs now (`--python 3.13`), and an upper-bound or interpreter-pin
decision later; (F6) `doctor` and `sync.lock` print the
machine's hostname and `doctor`'s `titles` line prints document paths, which matters only to whoever
relays that output.

### 5.2 What B0 does to B2

The closures hold, so the first-move protections B2 was sketched around are not needed; what is left
is a **verdict and a probe that cannot be vacuous**, run offline. That is a smaller thing, and the
question is whether to build even that yet.

| Option | What | For | Against |
|---|---|---|---|
| **(a) As sketched** | The tool of § 3.3 with `--create`, `--sync`, the six verdicts and the probe | Row 21's words, *a one-command start*, met literally | The largest; its first-move protections guard failures § 5.1 shows closed; tested against an imagined first run; and under `HF_HUB_OFFLINE=1` a fresh machine's `doctor` crashes (row B), so it says NOT READY until an online run has fetched the weights |
| **(b) Smaller** | The verdict ladder, the probe and the offline enforcement — no `--create`, no `--sync` | Keeps the one thing nothing else gives: a "started" that cannot be green on nothing | Still a tool, a battery, an outsider's mutants and a review for something done once per KB, which the user can approximate by hand with `pnk doctor` and one `pnk search`; same NOT READY-until-the-weights-are-fetched cost as (a) |
| **(c) Defer** | Ship B1 now; do the probe by hand as the checklist says; build B2 only after the first real B3 run says what a person got wrong or skipped | Nothing built for friction that has not happened; the environment problems B0 found are documentation problems the checklist already carries; it is the shape § 7's stop-loss rewards | Does not satisfy *a one-command start* literally; "started" is judged by a person, and the by-hand probe ships before its pass rate is measured — a reviewer's offline check passed 34 of 34 on two scratch KBs (the reviewer's report, not logged), a small sample without a negative control, so § 3.1's "measure before shipping the rule" is not met by (c) |

**Recommended, and taken: (c), with (b) as the next step if a real run shows a step was skipped or misread.** The
evidence is § 5.1: the failures a first user meets are in the README, the `.mcp.json` snippet and the
interpreter pin — words — plus `doctor`'s fetching and crashing, which is product code and not a job for this tool, and § 7's whole argument is that the bottleneck was never the tooling.
(c) costs the user's own instruction, which named a one-command start, and that is said here rather
than hidden.

**Decided by the user, 20261019, before 13:01 UTC: (c).** *"Defer B2, option (c). Keep B2, B3 and B4 paused until a real
run of the checklist says what hurt."* B2 is not built; what the first real run of
[`docs/DOGFOODING.md`](../docs/DOGFOODING.md) says is what decides whether (b) follows.

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

- **Before B3.** If **four weeks after the user lifts the pause for B0–B1** — the lift was 20261019, so
  by 20261116 — D-B5 is still unanswered *(it was answered 20261029, so this one did not fire)*,
  record *no material chosen* and stop. The clock starts at an event the user controls and the
  planner can date; it does not start at B3, which waits on the very answer being measured.
- **After B3.** If **four weeks after its first sync** the KB shows fewer than ten indexed documents
  (counted from `doctor`'s `index:` line) or no dated line in the friction file (the **user** attests which of *friction*,
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
- **Instruction files.** This file does not edit `CLAUDE.md`. Its pause bullet read *"paused, except
  option A"*, and **A3 regenerated that block** (20261019) with a pointer to this plan, the diff shown
  to the user first. Option A's plan § 9 now points here too, and `docs/README.md`'s rows agree.
- **Unbuilt work is named, never numbered.** Nothing here is assigned a version.
- **Landing** is `tools/land.py`, with `./check.sh` run the way A0 and A1 ran it
  (`PATH="$PWD/.venv/bin:$PATH" env -u PYTHONDONTWRITEBYTECODE ./check.sh`, status read from a log).
- **A release is not needed for B1; B2 adds a `tools/` file that does not ship**, and the 0.27.0
  precedent says to verify its absence from the wheel (`docs/RELEASING.md`).

## 9. What the user is asked

1. **B0 and B1 are done** (D-B7, taken 20261019 before 12:11 UTC). **B2 is deferred** — the user chose (c) of
   § 5.2, 20261019, before 13:01 UTC — and B3 and B4 stay paused with it until a real run of the checklist says what hurt.
2. **Rule on the six findings in § 5.1** (F1–F6): which become work, in what order, and when the
   pause lifts for them. Recommended first: F1, F3 and F2, because a first user hits the README
   before anything else and `doctor` downloading 1.1 GB is the only one that costs something.
3. **D-B5: name the folder** that starts `pinakes-kb`. Until then B3 cannot start; and if B2 is built, the
   command can only ever say NO MATERIAL YET, or NOT READY while the lock is old.
4. **D-B6: how to bring `pinakes-kb` up to date** — keep the id and update by hand (recommended), or
   re-stamp.

Nothing else in this file needs the user. **Not done and not decided here:** whether a live agent
harness launches a `.mcp.json` entry with the user's `PATH` (not tested), the reranker's behaviour on a
machine with a partial cache beyond the two cases in § 5.1, and everything in B2, B3 and B4.
