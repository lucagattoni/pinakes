# X3 — every section of every `plans/` file, classified by reading its body

**Written 20260825 12:52 UTC against `main` at `5175f56`.** This discharges **X3** in
[`20260825_0749-exposure-and-silent-status.md`](20260825_0749-exposure-and-silent-status.md) and is
the input **X2** needs. **It proposes work and takes no decision.**

## What was done, and why it is not the sweep that came before

The earlier sweep **classified each `##` section by reading its *heading*** and sent only the
LIVE/MIXED-looking ones for a real read. **Nine of twenty files were dropped unread.** This pass read
**all twenty files in full** — the nine could not be identified after the fact, and a superset cannot
inherit that error. **317 sections were classified, every one by reading its body**, then two
adversaries re-checked the result in both directions: *is what reads live really live*, and *is what
reads closed really closed*.

**93 heading/body mismatches were found.** That number is the finding. A heading is a status *claim*,
and in this directory the claim is wrong in roughly one section in six.

## Three of this sweep's own claims did not survive checking

Recorded first, because the same discipline that produced the list is what caught them.

1. **The `requires_pinakes` floor item was closed on a false basis.** The reader wrote *"no pre-pass
   exists, no floor test exists"*. Both exist — `manifest.py:381 _check_required_version` and
   `tests/test_manifest_compat.py:80`. **The adversary's overturn stands and the item is back on the
   list.**
2. **`expand` was not built and gated before `reach` was computed.** The clause was written 20260804
   10:19, the probe recorded at 16:49, and `expand` shipped 20260805 09:17; `reach=8` meets its floor
   of 8. **That BLOCKED item is discharged and off the list.**
3. **"No friction fragment ever came from the dogfooding KB" is false** — it produced the `pnk init`
   adoption fix that shipped in 0.14.0.

**F3's four stale citations in `docs/KB-UPDATES.md` did hold**, verbatim, at lines 37/63/76/77/78.

## The headline

The sweep is one commit stale and its basis moved: `main` is now c23359f, not c2c69cb, and a plan the sweep never saw landed — `plans/20260825_1240-run-pinakes-sweep.md`, fifteen defects found by *running* Pinakes (three high, none found by reading), plus D-36/D-37 untaken; the same merge answered D-35, unblocking § X7 in the exposure plan. Those are now the top of the worklist and displace everything the sweep ranked first. Three of the sweep's own claims did not hold when I checked them: (1) the reader's basis for closing the `requires_pinakes` floor item — "no pre-pass exists, no floor test exists" — is false (`manifest.py:381 _check_required_version`, `tests/test_manifest_compat.py:80`), so the adversary's overturn stands and that item is back on the list; (2) the reader's claim that `expand` was built and gated before `reach` was ever computed is false (clause written 20260804 10:19, probe recorded 16:49, `expand` shipped 20260805 09:17), and reach=8 meets its floor of 8, so that BLOCKED item is discharged and is off the list; (3) "no friction fragment ever came from the dogfooding KB" is false — it produced the `pnk init` adoption fix that shipped in 0.14.0. F3's four stale citations in `docs/KB-UPDATES.md` did hold, verbatim, at lines 37/63/76/77/78.

## Actionable — what is genuinely outstanding

Ranked as the sweep ranked it, after both adversaries. **`user-decision` means a stop, not a task.**

| # | Where | What | Status | Blocked on | Owner |
|---|---|---|---|---|---|
| 1 | `plans/20260825_1240-run-pinakes-sweep.md` — *S2 — `pnk doctor` reports a KB fully healthy after a sync silently dropped a document* | A sync `IntegrityError: UNIQUE constraint failed: documents.path` leaves the row at `state='deleted'` with sidecar and source intact on disk; the document is unfindable and `doctor` exits 0 — make doctor detect it. | **LIVE** | nothing | **coder** |
| 2 | `plans/20260825_1240-run-pinakes-sweep.md` — *S3 — `pnk serve` reuses one `sqlite3.Connection` across OS threads* | Give `serve` a per-thread connection: `serve.py:109-137` caches one `store.connect_ro` handle on the instance, and any pause over ~10 s between MCP calls (the normal agent session shape) fires a SQLite cross-thread error — back-to-back calls never do. | **LIVE** | nothing | **coder** |
| 3 | `plans/20260825_1240-run-pinakes-sweep.md` — *S1 — `pnk sync` aborts the entire index on one unreadable file* | Handle `PermissionError` in the walk: `sync.py hash_file` is a bare `path.read_bytes()`, so one `chmod 000` file raises an unhandled traceback, exits 1, and builds no index database at all — nothing else in the KB becomes reachable. | **LIVE** | nothing | **coder** |
| 4 | `plans/20260825_1240-run-pinakes-sweep.md` — *S4 — a KB name that is not valid TOML bricks the KB at creation, silently* | Escape at render in `template.py:_render` (settled between two sessions — not reject at `init`): a name containing `"`, `\` or a non-tab control character makes `init` exit 0 printing *created* while every later command exits 1, and `pnk init` refuses to repair it. Needs no flag — the directory name reaches the same path via `init.py:355 root.name`. | **LIVE** | nothing | **coder** |
| 5 | `plans/20260825_0749-exposure-and-silent-status.md` — *X7 — line 3's three layers (D-35 answered 20260825 12:37)* | Build the decided three-layer gate in `tools/status_header_gate.py`: layer 1 unchanged (`line3 == __version__`), layer 2 NEW/offline/hard (compare against the *Published versions* row tail imported from `release_order_gate.py` SEQUENCES — marker required/forbidden/red, row unreadable = hard fail), layer 3 the PyPI simple-index query as its own soft CI job. Read the section, not the memory of it — this is not what the plan first proposed. | **LIVE** | nothing — D-35 answered, explicitly unblocked | **coder** |
| 6 | `plans/20260825_1240-run-pinakes-sweep.md` — *Medium — six (S5, S6, S7, S8, S9)* | Five accept-then-mishandle defects: `--sidecars-only` with `--index-only` writes a sidecar while reporting all zeros; the *moved without its sidecar* message fires on ordinary deletion naming a file that no longer exists; the failure ledger never clears even when the document is repaired, and its remediation text is wrong; `-k -1` is a raw negative-slice bound returning 19 passages and `-k -100` prints *no passages matched* at exit 0; `pnk ask -k -1` raises an unhandled `ValueError` traceback from `deep/estimate.py:456`. The plan asks whoever builds them to say whether S1/S5/S6/S8/S9 are one fix or five. | **LIVE** | nothing | **coder** |
| 7 | `plans/20260825_1240-run-pinakes-sweep.md` — *D-36 — `pnk link` detaches a trailing comment from an alias-reference line* | Decide: defect to fix, or a missing bounds row in `docs/MANIFEST.md` plus a pinning test. `sameTags: *commontags  # comment` splits into two lines with the comment orphaned. Not on MANIFEST.md:307-319's ten exclusions; MANIFEST.md:303 promises comments survive and VERIFICATION.md:282 pins it; none of the six anchor/alias tests covers it. Bears on the sidecar byte-identity invariant — read `docs/INVARIANTS.md` first. | **LIVE** | the user's decision; then splits planner (MANIFEST row) / coder (fix or test) | **user-decision** |
| 8 | `plans/20260825_1240-run-pinakes-sweep.md` — *D-37 — what should S6's state *mean*?* | Decide what *source gone, sidecar present* means — a move whose other half has not been seen yet, or a deletion. Choosing the wording is implementation; choosing the meaning is not. | **LIVE** | the user's decision | **user-decision** |
| 9 | `plans/20260805_1313-decisions-init-titles-and-grammar.md` — *Compatibility: it sets a `requires_pinakes` floor, explicitly* | Reinstated by the adversary and confirmed by me: this decision's *Required* clause is undischarged and in unrecorded conflict with D-11/D-6. Nothing in Pinakes ever makes a KB carrying `[chunking] headings` or `metadata` declare a floor — `init.py` never writes `requires_pinakes`, and `upgrade.py:1264` only prints, never writes (D-11, pinned by `test_requires_pinakes_is_never_written`). The user-visible consequence is the exact misdiagnosis the field was built to prevent: a 0.6.0–0.12.x build opening such a KB reports *unknown key*. Decide whether the decision is withdrawn or discharged. | **UNCLEAR** | Needs the user to reconcile this decision against D-11 and D-6; neither document cites the other. What would settle it: a written ruling on whether a hand-set non-template key must carry a floor, and if so which surface writes it. | **user-decision** |
| 10 | `plans/20260804_1844-decision-parent-child-arity.md` — *The decision* | Requirement 3 is open and its trigger has fired: *if the ceiling is alarming, the immediate-parent variant is the arm to measure*. The ceiling was measured at 53.42 `parent-child` rows/chunk, 94.7% of all stored edges, +113.4% index growth. No immediate-parent arm exists — `tools/graph_matrix.py` LEGS has seven legs and none is one; `grep -rE 'immediate.parent\|immediate_parent' src/ tools/ tests/` returns one prose line in `tests/test_edges.py:1162`. Requirements 1 and 2 are discharged. Tracked in this file alone. | **LIVE** | nothing mechanical — the retrospective hands the decision to the planner and no planner document picks it up. Caveat: the +113.4% figure is from a deliberately adversarial synthetic corpus; the two real corpora measured 4.95 rows/chunk and 0. | **user-decision** |
| 11 | `plans/20260731_1202-open-corrections.md` — *`pnk init`'s gitignore warning is the only thing keeping a KB's `.pinakes/` out of a repository, and E5 raised what is in there* | A stop, not a task. The `init` half shipped as X1 (`init.py:122 _ignored_by_git`, `:303 pinakes_tracked`); the recurring `doctor` check did not — `grep -n gitignore src/pinakes/doctor.py` returns only unrelated prose at :1178. Required text is undecided and an implementer may not choose it. | **BLOCKED** | D-31 (does doctor carry a recurring check), D-32 (WARN vs OK-with-a-note), D-33 (ignored here vs for everyone) — all still '✅ Recommendation:' blocks, none taken | **user-decision** |
| 12 | `plans/20260807_2143-docs-audit-findings.md` — *Medium — 13 findings / Low — 27 findings* | 34 documentation findings are still open and every one reproduces on today's tree — I re-grepped the exact quoted strings, not the line numbers. Six are closed and five of those say so nowhere in their own section. Five filed under `# Low` are rated medium by the file's own re-verification (`docs/CLI.md:468`, `GUIDE.md:190/285/535`, `VERIFICATION.md:27`); three of those are GUIDE output fences that do not match what the commands print, on a site published on every push to `main`. | **LIVE** | nothing | **planner** |
| 13 | `plans/20260804_1016-template-release.md` — *F3 — `docs/KB-UPDATES.md` §3 case 1 describes something that never happened* | Four rotted code citations assigned to T4; T4 shipped in 0.20.0 without them. Verified still wrong: `store.py:205` at KB-UPDATES.md lines 37 and 78, `doctor.py:205` at 63, `sidecar.py:35,106` at 76, `_toml.py:184` at 77. Real locations today: `store.py:250 _check_schema_version`, `doctor.py:236 _template`, `sidecar.py:54/304`, `_toml.py:214`. Note the §3 citation was already re-derived once and has rotted again. F3's headline claim is separately closed — KB-UPDATES.md:56-61 now withdraws it — so the heading no longer describes what is open. | **LIVE** | nothing | **planner** |
| 14 | `plans/20260804_1016-template-release.md` — *D-8 — Is `pnk adopt` in this release?* | The only decision in this file nobody answered, and the disagreement it exists to end is still running: `docs/graph/PINAKES_APPROACH.md:420` assigns `pnk adopt` to the template release while `docs/README.md:28` files it under *What is still a proposal*. The template release closed at 0.22.0 with both documents standing. Either drop the APPROACH row or add the work. | **LIVE** | nothing | **planner** |
| 15 | `plans/20260727_1543-v0.2.md` — *Decisions taken (decision 12) / I7c — The completeness audit, staging, and all-or-nothing commit* | An orphaned deferral whose trigger fired. Decision 12 and I3b both say the `word_coverage` floor and the paid re-extraction loop land in v0.3 *fitted on a real distribution*. 0.3.0 shipped without them; `extract/audit.py`'s docstring still opens *report-only in this release* and `floors.toml` carries no `word_coverage` key. The real paid output the deferral waited for has existed since the human-gated run of 20260729. `grep -rn 're-extraction loop' plans/ docs/` hits this file only — no ROADMAP row, no STATUS row, no owner. Schedule it or record a decline. | **LIVE** | nothing — but it will not resurface on its own | **planner** |
| 16 | `plans/20260805_1313-decisions-init-titles-and-grammar.md` — *What this does not decide* | Whether to re-run the graph gate after 0.13.0's chunker fix is unanswered anywhere — not in `plans/`, `CHANGELOG.md` or `docs/STATUS.md`. Not academic: the gate's null verdict was measured on an index where all 106 806 chunks had an empty `heading_path`, and the corpus's committed manifest still carries no `headings` key. Costed at ~2 h CPU embedding plus a `schema_version` 3 rebuild, and carries the anti-circularity discipline in full. | **LIVE** | nothing mechanical; it is a decision with a cost, and there is no written trigger to point at | **user-decision** |
| 17 | `plans/20260803_2239-corpus-probe-run.md` — *Conversion rules — mechanical, reviewable, and biased against yourself* | A live re-run hazard, re-confirmed in code: `tools/build_rfc_corpus.py:434-451 write_golden_set` overwrites `<out>/eval/questions.yaml` unconditionally on every build (called at :505), and `tools/reachable_ceiling_probe.py:1030` hardcodes `root / "eval" / "questions.yaml"` with no `--questions` flag (argparse at :991-1012 defines only `--kb`, `--fake`, `--drop`, `--json`). The named better fix is giving the probe a `--questions` flag. The conversion this section originally governed is done; the hazard is not. | **LIVE** | nothing to add the flag; the runbook's *if the run is re-scoped* wording makes the wider rewrite proposed rather than scheduled | **coder** |
| 18 | `plans/20260821_0745-mutation-harness.md` — *(H1 preamble — invisible to a `##` sweep)* | Two named fields were specified-as-decisions and never built: `expect_green` (T4's *control that had to stay green* column) and a per-mutant zero-kill allowance. `grep -rn expect_green` hits only this plan; `tools/mutate.py:1199` has the batch-level `--allow-zero-kills` only; `tools/batteries/README.md` documents `file`/`old`/`new`/`kills` and no green control. Nothing in CHANGELOG or docs records a decision either way. Every `##` section of this file is closed-built — this is the only residue and a heading grep cannot reach it. | **LIVE** | the plan calls both 'decisions, not omissions' and nothing since records a decision | **user-decision** |
| 19 | `plans/20260825_0749-exposure-and-silent-status.md` — *X5a/b/c, X6 — write the four conventions down* | Four conventions this repository has re-derived and never written down, plus the invisible-handoff item. Listed at build-order row 7, blocked on nothing, planner-owned. | **LIVE** | nothing | **planner** |
| 20 | `plans/20260825_0749-exposure-and-silent-status.md` — *X7 doc half — `docs/RELEASING.md` sweep row, `docs/VERIFICATION.md:787`* | Two documentation debts D-35 named explicitly: `docs/RELEASING.md` never asks for the hold marker at all (a release cut by following it verbatim produces the false line — the marker is 0-for-2), and `tools/status_header_gate.py`'s docstring lines 1 and 10-13 are already literally false on today's tree (*'The invariant holds with no exception window'* — there is one, used deliberately three times). The docstring half is owed regardless of what was decided. | **LIVE** | the RELEASING sweep row waits on X7's marker shape being chosen; the false docstring waits on nothing | **planner** |
| 21 | `plans/20260825_1240-run-pinakes-sweep.md` — *Low — five* | Symlink loop invisible to `sync` and `doctor` (verifier downgraded high→low: a loop resolves to no content, ordinary Unix semantics); `-k 0` silently ignored on `search` and `ask`; `--source-type` accepts any string unvalidated so a typo reads as an empty KB; `confidence_reason` reports *nothing matched the filters* when no filters were given. | **BLOCKED** | the plan's own build order puts these behind S1-S9 | **coder** |
| 22 | `plans/20260807_2143-docs-audit-findings.md` — *(audit header — the deferred ROADMAP review)* | A deferral whose trigger fired and which no section carries, so it is invisible to a section-by-section sweep: the audit defers a full review of `docs/ROADMAP.md` *until after T2*. T2 shipped in 0.18.0. `docs/README.md:58` still records the review as 'still owed'. | **LIVE** | nothing — the trigger fired at 0.18.0 | **planner** |
| 23 | `plans/20260731_1202-open-corrections.md` — *`tools/fragments.py` validates the fragments it reads and never the document it writes* | A residual open question hides inside a CLOSED item. After *CLOSED 20260824 00:35* sits '**Left open deliberately: widening the body rule.** … Widening is two different decisions … **Neither is taken.**' Genuinely unbuilt: `fragments.py` sets `opened = None` after checking only the first non-blank line under a `###` heading, so the fourth bare-paragraph body shape is unreachable by the rule. Anyone treating the section as closed loses this. | **UNCLEAR** | No written trigger and no owner, so I cannot tell whether this is DEFERRED, CLOSED-REJECTED or an unfiled live item. What would settle it: the planner stating which of the two widenings (if either) is wanted. | **user-decision** |
| 24 | `plans/20260801_0749-realism-corpus.md` — *The dogfooding KB* | `pinakes-kb` was created 20260804 and never used — one commit, an empty `docs/`, no `.pinakes/` (D-14 leg 1). `retro.d/` holds only its README. CORRECTION to the sweep, which I verified: its claim that 'no friction fragment ever came from it' is false — the one time it was used it produced the `pnk init` adoption fix that shipped in 0.14.0, credited to three sites including the dogfooding KB. The item stays live because the ongoing practice has not happened, not because dogfooding yielded nothing. | **BLOCKED** | needs the user's own material; an agent cannot discharge it | **user-decision** |
| 25 | `plans/20260804_1016-staged-channel-gates.md` — *What "not scheduled" means operationally* | The clause defines its own tripwire — *two entries exist and are deliberate; if a third appears, that is the drift this rule exists to catch* — and at least six PPR/`[ner]` mentions now exist across `docs/`. The substantive rule still holds: none is a build plan, increment or numbered item, and `docs/ROADMAP.md:2410` says so explicitly. Only the enumeration is falsified. | **UNCLEAR** | A genuine reading dispute the adversary declined to overturn. Narrow reading of clause 1 ('a build plan, an increment, or a numbered item'): the tripwire has not fired. Broad reading ('Nothing else is written until a gate passes'): it has. `docs/ROADMAP.md` was created after this plan and restates the rule while adding an entry. What would settle it: the planner ruling which reading binds, in one line. | **planner** |
| 26 | `plans/20260804_1016-staged-channel-gates.md` — *Gate 1 — PPR (`graph_channel = "ppr"`) / The gate / The corpus the measurement needs* | Not runnable. Clause 1 is P2 — *`expand` is licensed on* — and it is false: G5's gate ran 20260804 22:52 with 0 improved, 3 regressed, p=1.0000, so `expand` ships `off` (`manifest.py:85`) and `"ppr"` is not an accepted value (`manifest.py:77`). The corpus clause fails independently: the heading floor is 50% of chunks carrying a non-empty `heading_path` and the RFC corpus scores 0%. `docs/ROADMAP.md:2400` already records that G5's result licenses neither PPR nor `[ner]`. | **BLOCKED** | P2 (`expand` never earned its default), plus no corpus meeting the heading-coverage floor — and the 300-RFC corpus 'lived locally and died with the machine' per CHANGELOG 0.13.0 | **planner** |
| 27 | `plans/20260804_1016-staged-channel-gates.md` — *Gate 2 — the `[ner]` extra and `mentions` edges / N4 / N5* | Unbuilt at every level, not merely ungated: no `[ner]` extra in `pyproject.toml`, no `mentions` kind in `edges.py:101 ALL_KINDS` or the `store.py:176` schema CHECK, no `LegSpec` for it in `graph_matrix.py`, and no script implementing N5's bridging-pair pre-count. N4 — is a model-derived edge set a `schema_version` bump and a coherence field — is unanswered anywhere in the repository, and the plan says answer it before deriving a single edge. | **BLOCKED** | N2 (no channel is licensed on, so `mentions` edges are inert by construction and the gate is unmeasurable). The adversary noted these read better as DEFERRED than BLOCKED, since N2 has no live path to being satisfied. | **planner** |

## Heading-vs-body mismatches — the input X2 needs

**Each row is a proposed heading suffix in this repository's own existing convention** — `T6`/`T8` in
[`20260804_1016-template-release.md`](20260804_1016-template-release.md) already carry
`· **CLOSED <date>, <disposition>**` in the `###` heading itself. So X2 is conformance, not redesign.

**Do not apply a row without reading the section.** Two of the earlier sweep's findings were withdrawn
after checking, and *the most strongly worded one was the wrong one*.

### `plans/20260804_1016-template-release.md`

**Heading:** T1 — The version archive and the template-drift gate

**Proposed suffix:** · **CLOSED 20260807, built in 0.17.0**

**Why:** The worst entry in the repository: heading and body agree it is unbuilt, and the body is a complete unbuilt-work spec — file list, gate legs (i)-(vii), test table, exit criteria — in forward tense throughout. Only CHANGELOG 0.17.0 says otherwise. `templates/notes/_versions/`, `templates/_versions.toml` and `tools/template_drift_gate.py` all exist. This is the exact near-miss CLAUDE.md records for 20260824 and 20260825.

### `plans/20260804_1016-template-release.md`

**Heading:** T4 — `pnk upgrade --apply`

**Proposed suffix:** · **CLOSED 20260808, built in 0.20.0**

**Why:** No shipped marker anywhere, and the body carries a premise that is now false — *D-2b makes every positive path unreachable from `notes`, one archived version, so no diff exists*. Two versions are archived (1.1 and 1.2) since 0.24.0, and the 1.1→1.2 bump adds a key and a `[budget]` money hunk. An agent would rebuild `--apply` and fixture it around a falsified premise.

### `plans/20260804_1016-template-release.md`

**Heading:** T7 — `pnk templates`, and a template declares its own files

**Proposed suffix:** · **CLOSED 20260808, built in 0.21.0**

**Why:** No shipped marker, and the body still opens *`pnk templates` is a command nobody has decided on … This increment invents a CLI surface* — which O-1, 1500 lines earlier in the same file, marked ACCEPTED on 20260804 10:30. An agent either stops to ask for a decision already taken or rebuilds a shipped command (`docs/CLI.md:81`).

### `plans/20260804_1016-template-release.md`

**Heading:** T3 — `pnk upgrade`, print only

**Proposed suffix:** · **CLOSED 20260807, built in 0.19.0**

**Why:** Body opens *Depends on T1, T2. What lands. A new command.* The only evidence it shipped is two clauses buried ~1300 and ~1400 lines in. `src/pinakes/upgrade.py` is 1200+ lines already on `main`.

### `plans/20260804_1016-template-release.md`

**Heading:** T5 — `vector_tier = "sqlite-vec"` stops lying

**Proposed suffix:** · **CLOSED 20260808, built in 0.20.1**

**Why:** Future-tense spec heading, no status marker; the shipped note is a mid-body blockquote. A rebuild would likely re-introduce the two-caller `resolve_tier` design the build itself rejected.

### `plans/20260804_1016-template-release.md`

**Heading:** D-4 — What happens to `vector_tier = "sqlite-vec"` before the tier exists? (F5)

**Proposed suffix:** · **CLOSED 20260808, answered — option A, shipped as T5**

**Why:** A bare question with no ✅, unlike D-2b/D-10/D-11/D-12 four lines away. The TAKEN blockquote sits 40 lines into the body, after the options table and after the words *Recommendation: A*. A `grep '^### D-'` returns it as live and re-opens a decision the user took.

### `plans/20260804_1016-template-release.md`

**Heading:** D-5 — Where does the pre-`--apply` manifest go? (D-1 = B, settled by implication — so this is live)

**Proposed suffix:** · **CLOSED 20260808, both halves built in 0.20.0**

**Why:** The only heading in the file that asserts liveness in its own text. Body is an unresolved recommendation table and never records that both A and C were built — `upgrade.py:1116,1130` (`pinakes.toml.orig`) and `:1193-1200` (the `ManifestError` restore).

### `plans/20260804_1016-template-release.md`

**Heading:** F5 — `vector_tier = "sqlite-vec"` is accepted today and silently does nothing

**Proposed suffix:** · **CLOSED 20260808, fixed in 0.20.1**

**Why:** Present-tense live defect in both heading and body. `manifest.py:52` has read `VECTOR_TIERS = ("auto", "numpy")` since 0.20.1 and the value is refused at load.

### `plans/20260804_1016-graph-remainder-reentry.md`

**Heading:** (every `##` and `###` — The one precondition, restated so it cannot be skipped; Part 1; A; B; C; D; E; F; Part 2 — Re-entry order)

**Proposed suffix:** · **CLOSED 20260805, entirely discharged — G3/G5/G6 shipped in 0.11.0**

**Why:** The whole file is discharged and says so nowhere, and heading and body agree — so no heading/body check catches it. The probe passed 20260804 (9 liftable against a floor of 7), `SCHEMA_VERSION` is 3, `CREATE TABLE edges` exists at `store.py:172`, `docs/STATUS.md:390` says all six increments landed. A freshly-cleared agent that follows this file re-runs a ~2 h CPU probe and re-plans a released increment.

### `plans/20260729_0256-links-and-graph.md`

**Heading:** Baseline — `main` at `d56bb35`, 20260803 22:18

**Proposed suffix:** · **CLOSED 20260805, superseded — G3/G5/G6 shipped in 0.11.0**

**Why:** Reads as an inert record a heading sweep skips, but the body holds live marching orders: *G3 is the next increment to build*, *G3 — Ready to build*, *Do not start any of them*. Both failure modes fire: dropped as RECORD, or obeyed and a landed increment rebuilt.

### `plans/20260729_0256-links-and-graph.md`

**Heading:** G3 — The node model and the edge set (`schema_version` 3)

**Proposed suffix:** · **CLOSED 20260805, built in 0.11.0**

**Why:** No status marker in a file where G1, G2, G4 and G5 all carry ✅, so the absence reads as *not built*. Body reads live at the top (*This increment starts*) and closed at the bottom (*Resolved 20260804 10:16*). An agent would start a `schema_version` 3 bump that shipped.

### `plans/20260729_0256-links-and-graph.md`

**Heading:** G6 — Edge-hub reporting, verification, and the graph release cut

**Proposed suffix:** · **CLOSED 20260805, built in 0.11.0**

**Why:** No ✅ where its siblings have one, so it reads as the outstanding final increment, with an eight-step verification list and *The cut*. Both are done — CHANGELOG 0.11.0 and `docs/VERIFICATION.md:765`.

### `plans/20260729_0256-links-and-graph.md`

**Heading:** G2 — Per-question outcomes, the grown golden set, one re-baseline ✅ landed 20260801 12:14

**Proposed suffix:** · **CLOSED 20260804, its stop lifted by the RFC corpus measurement**

**Why:** Heading says landed; body says *Outcome: the precondition failed … G3 does not start*. That stop was lifted 20260804 and superseded by 0.11.0. The section note says the spec is left as written, but the stop instruction reads as current.

### `plans/20260729_0256-links-and-graph.md`

**Heading:** G5 — The expansion channel, default off, and its gate ✅ built; gate run 20260804 22:52, did not pass

**Proposed suffix:** · **CLOSED 20260805 for the gate; the `parent-child` arity measurement it names is tracked in plans/20260804_1844-decision-parent-child-arity.md**

**Why:** The reverse trap. Reads fully closed, but carries a precondition never met — a measured `parent-child` ceiling before the gate ran, with the `--drop parent-child` arm inert by construction on a corpus with no `heading_path`. The gate ran anyway, so the trigger looks spent when the arity decision is still open.

### `plans/20260729_0256-links-and-graph.md`

**Heading:** Two releases, three cuts

**Proposed suffix:** · **CLOSED 20260805, the graph release cut as 0.11.0**

**Why:** Reads as a neutral count; body says *One cut remains … it is blocked, not pending* and *the name stays in CLAUDE.md's unbuilt-work table until it does*. The cut happened and the name was correctly dropped; an agent reconciling CLAUDE.md would try to re-add it.

### `plans/20260729_0256-links-and-graph.md`

**Heading:** (closure banner at line 6 — `> ## ✅ CLOSED 20260805 — both releases shipped. Nothing here is live.`)

**Proposed suffix:** unblockquote it, or repeat it as a bare `##`

**Why:** The single most load-bearing status line in the file is inside a blockquote, so it begins `> ## ` and `grep '^## '` misses it entirely — returning instead `## Baseline`, `## The open track is G3`, `### G3` and `### G6`, all of which read live. Its own forward pointer is also stale: it names the template-release plan as *the live plan*.

### `plans/20260821_0745-mutation-harness.md`

**Heading:** What it is / Tests / What it does not do / Exit criteria / (all five `##`)

**Proposed suffix:** · **CLOSED 20260822, built and released in 0.27.0**

**Why:** Every `##` body reads as an unbuilt plan with no closure marker anywhere; the status line sits in the H1 preamble, which `grep '^## '` never returns. `## What it is` additionally describes a *per-increment* battery — a framing 0.29.0 reversed; following it now means writing a throwaway battery in a scratchpad, the exact loss 0.29.0 fixed.

### `plans/20260731_2128-source-walk-containment.md`

**Heading:** The rule that is only half implemented / What to build / Tests / Three measured defects

**Proposed suffix:** · **CLOSED 20260801, built in 0.7.1**

**Why:** All six `##` headings are present-tense or imperative and the file's discharge note sits only in its `#` title. `## What to build` and `## Tests` read as an unstarted increment, and all eleven test names in the table already exist in `tests/test_sync.py`.

### `plans/20260731_1202-open-corrections.md`

**Heading:** Live

**Proposed suffix:** · **one item live, one CLOSED 20260824 — read each body**

**Why:** The file's own canonical failure, now doubly wrong. The preamble 27 lines above says *None live.* (false — one is), while the heading holds two `###` items of which one is closed in its body (false the other way). An agent reading the preamble skips the only live item; one grepping `^## ` reports two and can start rebuilding checks that shipped in 0.30.1.

### `plans/20260731_1202-open-corrections.md`

**Heading:** `tools/fragments.py` validates the fragments it reads and never the document it writes

**Proposed suffix:** · **CLOSED 20260824 00:35, built in 0.30.1 — one widening question left open in the body**

**Why:** Sits under `## Live` and reads as an unfixed defect; the closure is 47 lines in, after five present-tense paragraphs. `fragments.py:214 document_problems` and the shared `prospective()` are on `main`.

### `plans/20260811_0720-decisions-gates-and-corrections.md`

**Heading:** D-15 / D-16 / D-17 / D-18 — open correction: …

**Proposed suffix:** · **CLOSED 20260811, all four decided and built in 0.22.0**

**Why:** The words *open correction* name each item's origin, not its status, and D-18 is additionally phrased as an unanswered question (*is `pnk init` transactional?*). A grep for 'open' across `plans/` returns four live corrections that shipped fourteen days ago. D-18 is the row a previous sweep flagged and then withdrew — check before acting.

### `plans/20260811_0720-decisions-gates-and-corrections.md`

**Heading:** D-19 / D-20 — proposal: …

**Proposed suffix:** · **CLOSED 20260811, both built in 0.22.0**

**Why:** *proposal* reads as untaken. Both shipped: `release.yml:115-124` creates the GitHub release, and `--backend` exists at `cli.py:100` / `init.py:252`. An agent would re-surface them to the user as open decisions.

### `plans/20260811_0720-decisions-gates-and-corrections.md`

**Heading:** Build order

**Proposed suffix:** · **CLOSED 20260811, fully built out at 0.22.0**

**Why:** A six-row ordered queue each *its own branch, its own landing*. All six rows are CHANGELOG 0.22.0 entries and the release cut 20260811 08:26. An agent looking for what to build next starts at row 1.

### `plans/20260805_1721-metadata-as-retrieval-context.md`

**Heading:** 3 · The agreed order of work

**Proposed suffix:** · **CLOSED 20260807, the screen returned no-go — 2e and 2f cancelled**

**Why:** The table marks every row terminal, but four lines below it the prose still reads *2a, 2b and 2c have shipped; 2d and 2e remain, then the run.* An agent following the prose builds 2d (already `main` at `f253556`, released 0.16.0) and then takes the `schema_version` 4 bump at 2e — the one irreversible step the screen was inserted to decline. The contradiction is six lines apart.

### `plans/20260805_1721-metadata-as-retrieval-context.md`

**Heading:** What 2d builds — written 20260806 20:41, with 2a, 2b and 2c on `main`

**Proposed suffix:** · **CLOSED 20260807, built in 0.16.0**

**Why:** Six numbered imperatives with no closure sentence anywhere, including *Flip `metadata = "prefix"`, `pnk sync --rebuild`*. Rebuilding it burns a 45-minute rebuild. Every item is on `main`.

### `plans/20260805_1721-metadata-as-retrieval-context.md`

**Heading:** 2d's pre-registration — written 20260806 05:30, before the screen has been run

**Proposed suffix:** · **CLOSED 20260807 — the screen ran: 6 improved, 6 regressed, 84 unchanged, no-go**

**Why:** The heading states in its own text that the screen has not run. The body is entirely future-tense and never corrected. The outcome is recorded only in §0, 500 lines above.

### `plans/20260805_1721-metadata-as-retrieval-context.md`

**Heading:** The experiment

**Proposed suffix:** · **CLOSED 20260807, declined — `schema_version` 4 was never taken**

**Why:** Presented as a taken decision (*DECIDED 20260806 03:55 by the user: both channels, at `schema_version` 4 … every existing KB rebuilds once*) with no marker that it was later declined. `store.py:28` still reads `SCHEMA_VERSION: Final = 3`.

### `plans/20260805_1721-metadata-as-retrieval-context.md`

**Heading:** 4 · Decisions already taken — settled, not to be relitigated

**Proposed suffix:** · **one row overtaken 20260807 — *Which channel is injected* was declined by the 2d screen**

**Why:** The heading forbids reopening, so a reader takes the `schema_version` 4 row as binding and takes an irreversible bump the screen declined. It also quotes a *p < 0.05* sign test that never ran — the screen used a deliberately looser criterion.

### `plans/20260805_1721-metadata-as-retrieval-context.md`

**Heading:** The identity gap 2f must close — recorded 20260806 20:41

**Proposed suffix:** · **CLOSED — 2f cancelled; the gap closed twice, in 0.16.0 and 0.21.1**

**Why:** Assigns work to an increment that was cancelled, with no note of either. `tools/two_leg_gate.py` (0.16.0) closed the two-leg half and `tools/graph_gate.py:200` the three-leg half.

### `plans/20260805_1721-metadata-as-retrieval-context.md`

**Heading:** 7 · Work in flight — none. Everything here has landed and shipped in 0.12.0

**Proposed suffix:** · **correct the release to 0.14.0 and strike the open-corrections claim**

**Why:** Two errors in one heading-plus-body. The heading misdates 0.14.0 work to 0.12.0, and the body tells a fresh agent that `open-corrections.md` *has been empty since 20260805 22:18* — verified false at line 950; that file has live items, one of them the only thing CLAUDE.md marks as scheduled.

### `plans/20260805_1721-metadata-as-retrieval-context.md`

**Heading:** 1 · Facts established, with evidence — do not re-derive these

**Proposed suffix:** · **every `file:line` has moved a third time — locate by symbol, never by line**

**Why:** The heading says the facts are settled with evidence, inviting edits by line number. `manifest.py:59`→87, `search.py:512`→535, `chunk.py:631`→653, `sync.py:2005`→2080 and 2374. Only the section's own instruction — locate by symbol — is usable. I confirmed there are now two `.embed(` sites on the indexing path, not the one §2 claims.

### `plans/20260811_1358-deep-release.md`

**Heading:** E6 — the measurement run · unblocked; follows E4

**Proposed suffix:** · **CLOSED 20260821, BUILT — the run is done, €0.2131 spent, published in 0.25.3**

**Why:** The only increment heading in the file without a ✅ BUILT stamp, so it reads as the next thing to build. Rebuilding it spends real money re-running a measurement that already published 29.75x / 50.92x / 22.35x, and could lower a ceiling the run deliberately did not lower.

### `plans/20260811_1358-deep-release.md`

**Heading:** D-27 / D-23 / D-28 (✅ TAKEN headings whose bodies read open)

**Proposed suffix:** · **body superseded — the heading's answer is the taken one**

**Why:** The reverse trap, and it bites exactly the agent that follows this repo's own rule to read the body. D-27's body says *This is the one open item the planner would take alone if pressed*; D-23's ends on an unresolved user preference for option C; D-28's says *if A is chosen, §5 and E4's exit criteria both change*. Acting on any of them contradicts shipped code (`loop.py:245/528`, `_ask_arguments`).

### `plans/20260811_1358-deep-release.md`

**Heading:** E2 — the estimator for a round · ✅ BUILT 20260811 / E3 — the client, and the allowlist entry · ✅ BUILT 20260811

**Proposed suffix:** · **released in 0.24.0 — the *Not released* note in the body is superseded**

**Why:** Both bodies say *Not released. On `main`, unreleased, deliberately*. An agent could conclude there is uncut work on `main` and cut a release for modules that shipped in 0.24.0. E2's body additionally re-opens the `[deep]` key set that D-29/D-30 answered.

### `plans/20260807_2143-docs-audit-findings.md`

**Heading:** `docs/DESIGN.md:715` · `docs/GUIDE.md:3` · `docs/GUIDE.md:93` · `docs/KB-UPDATES.md:24` · `docs/MEASUREMENT-RUN.md:168` · `docs/STATUS.md:303`

**Proposed suffix:** · **CLOSED 20260823, fixed — see § Re-verified 20260823**

**Why:** Six findings are closed and five say so nowhere in their own section — the closure lives only in a table near the top. Applying the stated Fix for `DESIGN.md:715` or `KB-UPDATES.md:24` writes a *new* false claim into a published doc, because both bodies rest on `pnk upgrade` being unbuilt and it shipped in 0.19.0. `GUIDE.md:3`'s Fix would *lower* the currency stamp by twelve releases.

### `plans/20260807_2143-docs-audit-findings.md`

**Heading:** Medium — 13 findings / Low — 27 findings / Where they are

**Proposed suffix:** · **counts as of 20260807 — 6 fixed, 34 remain; five `# Low` are rated medium today**

**Why:** A planner budgeting *13 medium* plans ~50% more work than exists and reads four already-fixed sections as untouched; one triaging by divider deprioritises five findings the file itself now calls medium. `Where they are` still charges `docs/STATUS.md` with a finding a CI gate closed on 20260811.

### `plans/20260804_1844-decision-parent-child-arity.md`

**Heading:** The decision

**Proposed suffix:** · **requirements 1 and 2 CLOSED 20260804; requirement 3 LIVE — the ceiling fired and no arm exists**

**Why:** Reads as a closed decision, reinforced by the file's title and *DECIDED by the planner*. The earlier sweep skipped it on exactly that basis and lost the file's only outstanding work. Note the standing correction is itself wrong: X3 and `RETROSPECTIVES.md:7381` say the open item is *a measured ceiling required before G5's gate runs* — that was discharged the same day. The live item is requirement 3, a different thing.

### `plans/20260804_1844-decision-parent-child-arity.md`

**Heading:** Why not the alternatives / The standing risk this leaves

**Proposed suffix:** · **the *Immediate parent only* row is not a rejection — its conditional fired 20260804 22:39**

**Why:** Both read as pure rationale with nothing to act on. The first says the immediate-parent variant *is the right thing to measure if the ceiling proves alarming*; the second's stated reason for not mitigating (*nobody has measured one*) expired the same day. Filed under CLOSED-REJECTED, the one action both call for never happens.

### `plans/20260804_1844-decision-parent-child-arity.md`

**Heading:** The question

**Proposed suffix:** · **CLOSED 20260804, answered by § The decision and by `graph/edges.py:374-405`**

**Why:** The mirror error. A sweep hunting open questions flags it LIVE and may re-open a settled design question, or spends a review pass on the one section in the file with nothing in it.

### `plans/20260803_2239-corpus-probe-run.md`

**Heading:** The gap this file closes / The run / What is reported / What this run must not do / Before the numbers mean anything

**Proposed suffix:** · **CLOSED 20260804 — the probe ran; results in plans/20260804_1442-decision-g3-go.md and docs/STATUS.md**

**Why:** The file carries no closure marker of any kind — no banner, no ✅, no date-stamped result — and every heading and body is future tense for a measurement that completed. The single highest re-run risk in the plan set. The one section showing the run happened is buried under a heading that reads pre-run.

### `plans/20260801_0749-realism-corpus.md`

**Heading:** Precondition — settle the licence before fetching anything

**Proposed suffix:** · **CLOSED 20260801 14:02, licence cleared under both TLP regimes**

**Why:** Purely imperative (*Do not commit a single RFC until this is written down*) with no closure in the section; the closure sits two sections *earlier*. A `grep '^## '` returns it as live and an agent re-does a legal review already relied on to publish a public repo.

### `plans/20260801_0749-realism-corpus.md`

**Heading:** Measured — the licence and the structure (20260801 14:02) / The measurement — and a prediction to make before running it

**Proposed suffix:** · **CLOSED 20260804 — the corpus was built 08:00 and the filled table is at docs/STATUS.md:513-524**

**Why:** Opposite traps in one file. The first reads closed but its body says *no repo has been created* — true when written, false since 20260804 — and hands off three decisions. The second still carries `?` in every RFC cell, so an agent re-runs a corpus comparison whose answers are recorded.

### `plans/20260804_1442-decision-g3-go.md`

**Heading:** What starts, in order

**Proposed suffix:** · **CLOSED 20260805, G3/G5/G6 all shipped in 0.11.0**

**Why:** Lists three increments as work about to begin (*Preconditions met*). Heading and body agree with each other and both are stale. Nothing in the file records the release.

### `plans/20260731_0602-decision-ruamel-yaml.md`

**Heading:** (preamble, lines 6-9) Built by L5b and L5c … L5c is decision 19 alone

**Proposed suffix:** · **L5c CLOSED unbuilt — decision 19 shipped inside L5b in 0.5.0**

**Why:** The correction landed in the Decisions table (commit `d9e0d46`) and was left standing in the preamble — which is what a heading-level read gives. An agent goes to build a `read()`-time refusal that 0.5.0 already ships.

### `plans/20260731_0602-decision-ruamel-yaml.md`

**Heading:** Two lessons, for `retro.d/` when L5b lands

**Proposed suffix:** · **CLOSED 20260731 — L5b landed 11:27 and the lesson is spliced at docs/RETROSPECTIVES.md:2165**

**Why:** Reads as pending work conditioned on a future event. An agent writes a duplicate `retro.d/` fragment for a retrospective spliced 25 days ago, or treats the file as an increment still in flight.

### `plans/20260727_1543-v0.2.md`

**Heading:** I9 — Docs sweep, template, CI, 0.2.0

**Proposed suffix:** · **CLOSED 20260729, re-scoped and shipped in 0.4.0 — 0.2.0 cut early after I5**

**Why:** An agent grepping headings treats 0.2.0 as this plan's terminal release and either tries to satisfy the exit criterion `pinakes.__version__ == "0.2.0"` against a 0.30.3 package, or concludes the build order is unfinished. Actual mapping: I1-I5→0.2.0, I6a→0.2.2, I6b/I7a/I7b/I7c→0.3.0, I8/I9→0.4.0.

### `plans/20260727_1543-v0.2.md`

**Heading:** Verification of the whole

**Proposed suffix:** · **CLOSED 20260729 as a lookup — docs/VERIFICATION.md is the resolved mapping**

**Why:** Reads as the authoritative verification table. 61 of its 98 test paths did not resolve at I9, so an agent concludes 62% of the release's guarantees are untested and re-implements tests that exist under other names.

### `plans/20260727_1543-v0.2.md`

**Heading:** Ground rules (apply to every increment)

**Proposed suffix:** · **superseded 20260728 — assign the next version from `main`, never from this plan**

**Why:** Present tense, imperative, nothing marked stale; the supersession is buried at the end of a long bullet five bullets down. CHANGELOG.md:3431 records an I6a worktree nearly assigning a release number from the plan.

### `plans/20260727_1543-v0.2.md`

**Heading:** I7c — The completeness audit, staging, and all-or-nothing commit

**Proposed suffix:** · **CLOSED 20260729, report-only half built in 0.3.0 — the re-extraction loop was deferred and never shipped**

**Why:** Reads as a shipped completeness audit, so an agent assumes low-coverage pages trigger paid re-extraction. They do not — `extract/audit.py` still says *report-only in this release* and `floors.toml` carries no `word_coverage` floor. The promised loop is the orphaned deferral on the actionable list.

### `plans/20260727_1543-v0.2.md`

**Heading:** Decisions taken

**Proposed suffix:** · **CLOSED 20260728 — except decision 12, whose deferral to v0.3 was never honoured**

**Why:** Reads as pure history so it is never opened, hiding a scoped, justified piece of work (the paid re-extraction loop) deferred to a release that has since shipped without it and now has no owner. Same shape as the arity plan's `## The decision`, which the earlier sweep dropped.

### `plans/20260725_1317-v0.1.md`

**Heading:** What is now stale above this line

**Proposed suffix:** · **this correction layer is itself stale — PyPI publishing has worked for 49 releases**

**Why:** The section built to stop staleness has gone stale. It says *PyPI trusted publishing is still unconfigured*; `docs/STATUS.md:1196` counts 49 versions published through 0.30.2. An agent might 'fix' a pipeline that works.

### `plans/20260725_1317-v0.1.md`

**Heading:** Verification of the whole (not just the parts)

**Proposed suffix:** · **the paid-import gate never shipped in v0.1 — it exists now as tools/paid_path_gate.py (0.1.1)**

**Why:** Asserts the paid-import invariant was CI-gated from v0.1; this same file's stale table says *Never shipped … nothing enforced it until 0.1.1*. It also names `tests/test_quickstart.py`, which does not exist — the test is `tests/test_cli_search.py:163`.

### `plans/20260725_1317-v0.1.md`

**Heading:** Ground rules (apply to every increment) / I7 / I9 / I10 / I13 / I8a / I11

**Proposed suffix:** · **historical spec — falsified in detail by the file's own stale table; verify against `src/` before quoting**

**Why:** Six increment specs read as authoritative for what shipped and are individually wrong: `--offline` is claimed on `doctor` (it is not — `_doctor_arguments` adds only `--kb`/`--prune`); `--created-after/-before` are quoted as CLI flags (the shipped pair is `--modified-*`); `pinakes_search`'s filter set names a nonexistent column and `FastMCP`, removed by mcp 2.0.0; `pair()` is said to return `DuplicateIdError` when it raises `DuplicateIdsError`; `pnk doctor`'s check list omits four shipped checks. Ground rules additionally says `__version__` stays `0.0.0`.

## What X2 applied, and what it left

**X2 is built (20260825 13:20).** The 53 dispositions above became **100 heading edits across 17
files** — a disposition naming several headings was expanded per real heading line — and every one
was re-read against its section body before being written.

**Two things the adversarial pass caught that would have damaged the tree, both worth keeping:**

1. **20 of the 100 entries named the wrong file.** Nineteen would have failed loudly at zero
   occurrences; **`## Live` would have applied *successfully* to the wrong text**, because the file
   it was misfiled under also has that heading. Resolution was done by searching `plans/` for an
   exact full-line match rather than by trusting any agent's label.
2. **Five `old_line` strings are not unique across `plans/`.** `## Ground rules (apply to every
   increment)` is a target in **both** `20260727_1543-v0.2.md` and `20260725_1317-v0.1.md` **with
   different replacements**; `## Tests` likewise in the mutation-harness and source-walk plans. **A
   repo-wide string replace would have silently corrupted them.** The apply keys on `(file, line)`.

**Seven dispositions were overturned for writing a false claim**, and three shared one shape:
`CLOSED 20260823` dated a docs-audit fix to the pass that *noticed* it rather than the commit that
made it — sixteen days late, and in one case erasing the very gap the entry had discovered.

**The residual, stated rather than left to be found.** The readers flagged **93** heading/body
mismatches; the synthesis proposed dispositions for **53**. **The remaining ~40 carry no
disposition and were not applied** — they were consolidated or judged not to need one, and that
judgement has not been re-checked. A heading-only sweep of `plans/20260729_0256-links-and-graph.md`
still returns `## The open track is G3 — and what the parallel run taught`, which reads live and has
no disposition. **The file's closure banner now covers it** — unblockquoted, so `grep '^## '`
returns it for the first time — but the section heading itself is unmarked.

## Corrections owed — factual errors found while reading

**These are not heading dispositions. Each is a claim that is wrong on the tree as it stands.**

- `docs/README.md:58` is stale and it is an entry point a freshly-cleared session reads first: it says the docs-audit plan holds '**39 open documentation corrections**' and '**One is fixed**'. The plan's own 20260823 pass says 6 fixed and 34 remain. It also still records the `docs/ROADMAP.md` review as 'still owed' — correct, but the trigger (T2) fired at 0.18.0, so it should read as due rather than deferred.
- `plans/20260807_2143-docs-audit-findings.md` contradicts itself on its own arithmetic: line 17 says 'Still open — this file | **40**' and the `# Medium — 13` / `# Low — 27` dividers sum to 40, while line 44 says 'Open at the audit | 39' against 'Fixed since | 6' and 'Remaining | **34**'. 39 − 6 = 33. The 34 is right and the 39 is wrong. A planner reconciling counts burns a pass hunting a 40th finding that was never missing.
- `plans/20260805_1721-metadata-as-retrieval-context.md:950` states '`plans/20260731_1202-open-corrections.md` has been empty since 20260805 22:18'. Verified false: that file's own § Live says it refilled from E5 and it currently holds two `###` items, one of which forwards to the only plan CLAUDE.md marks as carrying scheduled work. Same section's heading misdates 0.14.0 work to 0.12.0.
- `plans/20260731_1202-open-corrections.md:37` reads '**None live.**' while the file holds one genuinely live item. The routing table (`docs/README.md`) says 'One live item' and is right — so the file an implementer opens is the one that is wrong.
- The same file's gitignore item contradicts itself four lines apart: a sentence saying 'The paragraph below calling this a strengthening rather than a hole … is wrong on that point' immediately precedes the paragraph making that claim. The wrong paragraph was left standing rather than rewritten, so reading either alone gives the opposite conclusion about urgency. Its 'What is true' paragraph is also superseded by X1 without saying so, and it cites `cli.py:133` for a branch now at `:134`.
- `plans/20260805_1721-metadata-as-retrieval-context.md` §2 says the vector channel 'has a single injection point … the only `.embed(` call on the indexing path'. Verified false: `grep -n '\.embed(' src/pinakes/sync.py` returns **two**, at :2080 and :2374. The code comment at `sync.py:2364-2365` repeats the false uniqueness claim verbatim. Behaviour is correct (both honour `inject`); the claim is not, in the plan and in the source comment.
- `plans/20260825_0749-exposure-and-silent-status.md` § X3 and `docs/RETROSPECTIVES.md:7381` both say the arity plan's `## The decision` holds 'a measured ceiling required before G5's gate runs'. That ceiling was measured twice on 20260804 (21:05 and 22:39) and the gate ran at 22:52. Acting on the stated reason re-runs an existing measurement and still misses the actual open item, requirement 3. Correct the reason, keep the item.
- `plans/20260811_1358-deep-release.md`'s closure block says E1-E7 'shipped across **0.24.0 to 0.26.0**'. E1 shipped in 0.23.0; `docs/STATUS.md:391` has it right. The same file's header (line 15) says 'All eight decisions were taken' while the plan holds ten (D-21 to D-30) — a reader stopping at the header under-counts the decisions this plan is the authority for. Its §3 also attributes the never-MCP gate to 'E5's gate'; it landed at E3 (`b337290`), and E5's own note in the same file says so.
- `plans/20260804_1016-staged-channel-gates.md` asserts in its header that 'Citations re-confirmed at `d06ef7e` … all four `STATUS` line numbers here still resolve'. That sentence is now false — `docs/STATUS.md:260`→392, `:312`/`:342`/`:383`→`:506`/`:597`+ — as are its `src/` citations (`eval.py:574`→707, `search.py:333`→405). Same false-confirmation sentence appears in `plans/20260804_1016-graph-remainder-reentry.md:44`. The `docs/graph/` citations in both still resolve exactly.
- `plans/20260804_1016-staged-channel-gates.md` calls `plans/20260804_1016-template-release.md` 'a sibling scratchpad proposal, not a repository plan'. It is a committed repository plan, closed at 0.22.0. The same file says of the per-kind edge census that 'No tool prints this today' — CHANGELOG 0.9.0 shipped exactly that four hours after the file's stamped revision, and the claim survived two later planner reviews.
- `plans/20260804_1016-template-release.md` carries four falsified measurements that other rows depend on: F2's 'No template drift has ever added or removed a key' is false since notes@1.2 adds `daily_eur` (which gives D-11's `requires_pinakes` recommendation path a real input for the first time); the repeated 'one archived version, so no diff is reachable from `notes`' is false since 0.24.0; M3's `[budget]` diff is superseded by today's `per_operation_eur = 2.00`; and its Risks table says `notes@1.0` denotes six contents where D-2b/F1/T1 all say eleven, and cites `tests/test_store.py:93` as a test that no longer exists. The plan also under-counts its own wrong measurements at eight; `docs/README.md:51` has the corrected total, ten.
- Outside `plans/`: `docs/CLI.md`'s `pnk templates` example output still prints 'notes 1.1' six lines above a `--json` paragraph that correctly says 'notes@1.2'; and `docs/ROADMAP.md:2500-2503` still says 'the last step is still the user's own edit, and will be until the next template bump' — that bump landed in 0.24.0.
- `docs/KB-UPDATES.md` §9's cost table leaves '`pnk upgrade` + `--apply` + `tomlkit`' unstruck and closes 'The remaining two … Neither is assigned'. Both are built (0.19.0 and 0.20.0), and only one row is unstruck, so the prose's 'two' has no referent. A planner reading §9 concludes `pnk upgrade` is unbuilt.
- `plans/20260801_0102-links-and-graph-log.md`'s 20260731 20:43 row points at 'open-corrections item 9'. That file has no numbering — `grep -n 'item 9'` returns nothing. The pointer cannot be followed.
- `plans/20260731_0602-decision-ruamel-yaml.md:119` points at 'the increment-shaped blind spot **CLAUDE.md** already records'; no such text is in CLAUDE.md or `docs/BUILDING.md` today — it lives only in `docs/RETROSPECTIVES.md:1376,1525`. The same file's decision item 3 names `test_comments_in_the_sidecar_survive_a_rewrite`; the real test is `tests/test_sidecar.py:470 test_comments_survive_a_rewrite`.
- `plans/20260804_1442-decision-g3-go.md` is absent from `docs/README.md`'s routing table while both its sibling decision records have rows. The G3 go/no-go decision is reachable only from links inside other plans.
- `plans/20260801_0749-realism-corpus.md` says of the RFC corpus 'Not a golden set. It has no questions and no baseline.' An RFC golden set now exists — 110 questions frozen 20260806 at `tools/rfc_corpus/questions.yaml`, released in 0.16.0 — but on a *different* RFC corpus (the `--era modern` band), not the 300-document `pinakes-corpus-rfc`. Two RFC corpora exist and the plan names one. Three records also disagree on that corpus's size: 300 (20260804), 600 (20260808 gate run), 980-built/644-accepted (20260805 rebuild).
- `docs/DESIGN.md` no longer states the 'unbuilt work is named, never numbered' rule anywhere (`grep -n 'never numbered' docs/DESIGN.md` → no match), yet the docs-audit finding for `DESIGN.md:763` cites '§8 of this same file states the rule at lines 1153-1155'. The rule now lives only at `docs/README.md:137-155`, whose carve-out list does not include DESIGN.md — so the three offending sites at `DESIGN.md:72,238,907` still violate it. Fix the finding's citation, not just the sites.
- `plans/20260825_1240-run-pinakes-sweep.md` records a harness defect worth acting on beyond this sweep: a verifier that returns **no verdict** was classified into the *refuted* bucket by a default branch, and a real finding was nearly buried. 'Whatever consumes a verifier's output must distinguish *refuted* from *unverified*.' The same distinction applies to any future adversarial pass this repository runs.

## Open questions — **no longer every one a stop.** Thirteen bullets: **ten settled, two deferred behind written triggers, one still open**

> **Read the bullets, not this heading** — that is this file's own finding, and it applies to this
> file. **The ten settled** are seven answered by the user 20260825 18:16, two that turned out to be
> already ruled elsewhere on `main`, and one declined. **The single remaining stop is the last
> bullet, and it is not a decision**: two external repositories were never fetched and no reviewer ran
> a gate, so no user answer closes it — only doing it does. Every bullet now carries its disposition
> inline; **four did not until 20260825 23:23**, and this banner claimed otherwise while they sat
> unmarked, which is the defect this file exists to catch, committed by the pass that wrote the
> banner.

- **✅ ANSWERED 20260825 18:16 — option C: `pnk doctor` asks BOTH questions (tracked *and* ignored), UNCONDITIONALLY.** Not the `ls-files`-first shortcut an earlier pass proposed — that silently downgraded a WARN to OK on exactly the loose-folder KB where `pnk init` had just printed the warning, which was its only behavioural effect. D-31, D-32, D-33 — does `pnk doctor` carry a recurring `.pinakes/` exposure check; is it a WARN or an OK-with-a-note; is the scope 'ignored here' or 'ignored for everyone'. **Two corrections to this bullet as it stood:** the blocked item in `plans/20260731_1202-open-corrections.md` is no longer *the only remaining* one (that file now holds four live items), and *rows 2-6* of the exposure plan's build order is wrong — rows 2, 3, 4 and 7 are BUILT; only rows 5 and 6 were blocked. The build is queued coder work.
- **✅ ANSWERED 20260825 18:16 AND BUILT: promises only, ratified, plus the bounded audit.** D-34 — does `docs/VERIFICATION.md` map every test, or promises only? *Promises only*, with *promise* now defined in the preamble: a user-visible guarantee, a named invariant, or a gate's own correctness. **The audit was run rather than promised** and found 14 of `tests/test_serve.py`'s 31 tests unrowed — two of them security boundaries — now rowed under a new *The MCP server boundary (I13)*. **No longer 'new and unscheduled'.**
- **✅ ANSWERED 20260825 18:16 — option E, WHICH THIS BULLET'S TWO OPTIONS DO NOT CONTAIN.** Derive the bound from a **generative round-trip corpus** and set the free `ruamel` options. **Option E was invented by the adversarial pass and appears in no earlier plan, and the first pass's recommendation was OVERTURNED** — so anyone building from the two options named below gets the wrong answer. Hand-enumeration of this bound has now failed four times, including the adversary's own first attempt. Read `20260825_1803-open-decisions.md` § *D-36 + D-37*, never this line. (The original question: is the `pnk link` alias-comment detachment a defect to fix, or a missing bounds row plus a pinning test? It bears on the sidecar byte-identity invariant, so it was never a free choice.)
- **✅ ANSWERED 20260825 18:16 — option E, ALSO INVENTED BY THE ADVERSARIAL PASS.** Gate the move hint on the **orphaned sidecar**, not the mint count. The original discriminator fails on delete-one-add-one — the ordinary git-hook batch shape — and on an ambiguity branch the first pass never found; the adversary measured the replacement at 5/5 against the original's 3/5. **This was the only decision blocking queued work** (S6, in the sweep's S5–S9 batch), so that batch now runs to completion. Read the decision, not this line. (The original question: what should 'source gone, sidecar present' mean — a move whose other half has not been seen, or a deletion?)
- **✅ ANSWERED 20260825 18:16 — E+F.** The 20260805 clause is CLOSED-**superseded** (its premise failed: nothing writes the floor — D-6 and D-11 decided that away on either side of it) and folded into `docs/KB-UPDATES.md` §8 beside the older general question, D-6 and D-11 cross-cited. The user-facing remedy was never missing: `docs/GUIDE.md` § *Troubleshooting* already answers the collaborator case. Coder half owed: `_toml.py`'s unknown-key message must offer the second hypothesis and point at MANIFEST.md. The `requires_pinakes` floor for `[chunking] headings`/`metadata`, and its unrecorded conflict with D-11 ('--apply never writes it') and D-6 ('init never stamps it'). Settled by: a ruling on whether a hand-set non-template key must carry a floor, and if so which surface writes it. Until then a 0.6.0-0.12.x build opening such a KB reports 'unknown key' — the exact misdiagnosis the field exists to prevent.
- **✅ ANSWERED 20260825 18:16 — CLOSED, and the trigger did NOT fire.** The conditional's antecedent is measured false on every *real* corpus: 4.95 rows/chunk here, 3.80 over 300 real specifications, 0 of 300 reaching the synthetic 53.42. That 53.42 came from a purpose-built worst-shape corpus. Transitive stays as built; no arm is owed; nothing in `src/` changes. The `parent-child` immediate-parent arm (arity requirement 3). The trigger fired at 53.42 rows/chunk and +113.4% index growth, `RETROSPECTIVES.md:3568-3572` hands the decision to the planner, and no planner document picks it up. Complicating it: the alarming figure comes from a deliberately adversarial synthetic corpus, while the two real corpora measured 4.95 rows/chunk and 0 — so how urgent it is turns on a judgement about real corpus shape nobody has made in writing.
- **✅ ANSWERED 20260825 18:16 — run it, LATER, as its own three-leg gate.** Split from the arity question (that split is what let arity close for free) and carrying **no** immediate-parent eighth leg. Cost ~2.4 h, not ~2 h. Blocks nothing, expected result another null, `expand` stays `off` either way. Unscheduled. Whether to re-run the graph gate now that 0.13.0's `headings = "numbered"` exists. Costed at ~2 h CPU plus a `schema_version` 3 rebuild. The gate's null verdict rests on an index where every chunk had an empty `heading_path`, and the corpus's committed manifest still carries no `headings` key.
- **❌ DECLINED 20260825 18:16.** Measured: the field is in two commits and no code; 0 of 136 mutants across six batteries asks for a green control; `load_battery` rejects no unknown key, so one written today would be parsed, ignored and reported to nobody. Two of T4's five filled entries are not expressible as a green control at all. It is also not the guard for the one hole the README says nothing catches. Whether `expect_green` and a per-mutant zero-kill allowance are still wanted in `tools/mutate.py`, or were tacitly dropped when 0.29.0 made batteries committed artifacts. The plan calls them 'decisions, not omissions'; nothing since records a decision.
- **⏸ DEFERRED 20260825 18:16, with a trigger and an owner — not declined.** The deciding fact is new: the loop **cannot fire on this corpus**, and the floor is not why — `SCANNED_PAGE_FRACTION = 0.10` admits a document only when ≥10% of its pages are *below* the yield floor, which is exactly the condition the audit uses to *exempt* a page. Measured over all 18 readable fixtures, every document the paid path accepts without `--force` has ≤1 auditable page. The trigger's first term is **free** to evaluate (run `survey_free_yield` over a real corpus) and its home is `src/pinakes/extract/audit.py`'s docstring — read by whoever would build it — not a roadmap row read by a sweeper. Whether the paid re-extraction loop (decision 12 / I7c) should be scheduled or formally declined. Its named precondition — real paid output to fit a `word_coverage` floor against — has been satisfied since 20260729 and nothing owns it.
- **✅ RULED 20260825 18:41 — it has NOT fired, and the clause was the defect.** Clause 1 counted permitted entries and its count was false when written: `docs/DESIGN.md` had carried a third entry of the same shape since 20260729, five days earlier. It now forbids a **class** — no plan, no increment, no numbered item, no version number — and states that index/routing/survey/naming entries are permitted and uncounted. `docs/ROADMAP.md` is obedience, not drift. Whether the staged-channel-gates 'not scheduled' tripwire has fired. Turns entirely on which reading of clause 1 binds; `docs/ROADMAP.md` was created after the plan and restates the rule while adding an entry, which is either obedience or drift.
- **✅ ALREADY RULED ON `main`, and this bullet was a false signpost.** `docs/ROADMAP.md` § *The template release — T1 shipped in 0.17.0* states the trigger and then answers it: *"A corpus above the threshold is not enough; one exists and nobody searches it interactively. So the release name stays in the unbuilt-work table."* The first conjunct is satisfied — a **106,806-chunk** KB exists, 2× the threshold — so only the user can fire the second. **Everyone who stopped at "not checkable from here" stopped one grep short.** Whether D-13's T6 trigger has fired. Not checkable from this repository — it depends on a real KB's chunk count and felt search latency, neither of which is recorded here. The code-side status (tier unbuilt, value refused at `manifest.py:66`) is verified.
- **⏸ DEFERRED 20260825 18:41, with a trigger, an owner (the user) and the implementation named.** It is the **setext-plus-indentation pair, not widening 1** — widening 1 reaches one section written 20260725, cannot reach the class that shipped, and needs three carve-outs not two (without a column-0 restriction it reports 3001 violations on today's CHANGELOG). Both target classes measure **zero** live instances today. Whether the fragments.py 'widening the body rule' residue is deferred, rejected, or an unfiled live item. It has no trigger and no owner.
- **🛑 STILL OPEN — and this is the ONE genuine stop left in this list.** It is not a decision, so no user answer closes it; it closes only by fetching the repos and running the gates. Not checkable from here, and it bounds several verdicts above: the external repos `pinakes-kb` (private) and `pinakes-corpus-rfc` were not fetched, so every claim about the dogfooding KB's or the RFC corpus's *current* state rests on in-repo records whose newest entry is 20260811. CHANGELOG 0.13.0 says the 300-document corpus 'died with the machine'; that could be neither confirmed nor refuted. Separately, no reviewer ran `./check.sh`, `pytest` or any gate — every 'built' verdict rests on reading source, CHANGELOG entries and STATUS rows, and no fix was reverted to watch its supposed pinning test go red.

## Files with nothing live

**Verified, not assumed.** Everything in these is built, answered, rejected or deferred:

- `plans/20260725_1317-v0.1.md`
- `plans/20260729_0256-links-and-graph.md`
- `plans/20260804_1442-decision-g3-go.md`
- `plans/20260804_1016-graph-remainder-reentry.md`
- `plans/20260731_2128-source-walk-containment.md`
- `plans/20260731_0602-decision-ruamel-yaml.md`
- `plans/20260811_1358-deep-release.md`
- `plans/20260801_0102-links-and-graph-log.md`
- `plans/20260805_1721-metadata-as-retrieval-context.md`
- `plans/20260811_0720-decisions-gates-and-corrections.md`
- `plans/20260727_1543-v0.2.md (everything built or rejected EXCEPT decision 12's orphaned re-extraction-loop deferral, listed as actionable)`

**An empty list is not *nothing to do*.** `docs/README.md`'s own convention says a closed plan is a
historical record, and `CLAUDE.md` says to read an empty list as *nobody has run Pinakes lately* —
which on 20260825 produced fifteen defects in one afternoon
([`20260825_1240-run-pinakes-sweep.md`](20260825_1240-run-pinakes-sweep.md)).

## What bounds this sweep

**Two external repositories were not fetched** — `pinakes-kb` (private) and `pinakes-corpus-rfc`. Every
claim here about the dogfooding KB's or the RFC corpus's *current* state rests on in-repo records, and
those records are the thing this sweep exists to distrust. **Anything turning on their live state is
marked UNCLEAR above rather than resolved.**
