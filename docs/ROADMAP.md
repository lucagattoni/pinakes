# Roadmap — the whole story, in order

**Audience: a human catching up.** One page: what has shipped, in what order, why, and what is left.
Everything here is a *narrative view* over records that live elsewhere — it owns no fact of its own.

| If you want | Read |
|---|---|
| the authority on whether something is built | [STATUS.md](STATUS.md) |
| the full, exact record of a release | [CHANGELOG.md](https://github.com/lucagattoni/pinakes/blob/main/CHANGELOG.md) |
| what to build next, step by step | [`plans/`](https://github.com/lucagattoni/pinakes/tree/main/plans) |
| which file owns which fact | [docs/README.md](https://github.com/lucagattoni/pinakes/blob/main/docs/README.md) |
| this page | the shape of it all, without reading the other four |

**About the dates.** Timestamps up to **20260804 11:32 are local** (Europe/Rome); from there on they
are **UTC**. They are recorded as they were written and never converted — converting invents
precision nobody measured.

---

## Where things stand right now — 20260823 13:59 UTC

- **52 releases in 29 days.** [`0.1.0`](#010--the-engine--20260725-1527) on 20260725;
  [`0.29.1`](#0291--the-instruction-file-extracted-to-its-own-guideline--20260823-1359)
  on 20260823.
- **Latest on PyPI: `0.29.0`**, confirmed by installing it from the index rather than by reading a
  green workflow ([STATUS § Published on PyPI](STATUS.md#published-on-pypi)) — and by opening the
  published wheel, because a matching version string says nothing about whether the release's own
  subject is inside it. **0.28.1 adds a third form of that check, for the claim the other two cannot
  reach.** Opening a wheel proves a subject is *present*; the inverted check proves a developer tool
  is *absent*; but *"no code path changed"* — written into four of the last six releases — is a
  claim about **everything that did not move**, which no single-artifact check can carry. So the two
  published wheels were unpacked and compared: `diff -r` returns one line, `__version__`, with the
  other 72 of 73 files byte-identical, template payload included. It costs two downloads, and it
  verifies from the index what the commit message had until now asserted from the repo diff.
  **0.25.1 is the sharpest case this project has had of that distinction**:
  every release from 0.22.0 on installed cleanly and reported the right version while
  `pnk ask --deep` could not make one successful call. Every release from `0.2.2` on is published —
  **forty-four**, counted from the index rather than from this list's previous number — and read from
  `https://pypi.org/simple/pinakes/`, the endpoint installers use, because for minutes after an
  upload the `json` endpoint and uv's cache still report the previous version while `simple/` already
  carries the files. Checking `json` first says *the upload failed*, which is this project's recorded
  failure mode and would be exactly the wrong conclusion. **0.27.0's and 0.27.1's artifact checks both ran inverted**: their subjects are
  developer tools, so each published wheel was opened to confirm the `tools/` entries are **absent**
  from its 78 files, which is exactly what *"it ships in no wheel"* claims. Reading
  `pinakes/deep/suggest.py` out of the wheel was 0.26.0's check, whose subject did ship in it.
- **Three of the four named releases have shipped; the fourth is a trigger rather than a queue.** The links release across
  [`0.5.0`](#050--links-you-can-walk--20260731-1127)–[`0.6.0`](#060--links-you-can-write--20260801-1051),
  the graph release in [`0.11.0`](#the-graph-release--shipped-0110). **The template release has
  shipped every increment it scheduled** — T1 to T5 and T7 across 0.17.0–0.21.0, cutting more than
  once by D-9 — **and both of its gated increments are now answered**, so what is left under that
  name is a trigger rather than a queue. **The deep release is complete as of
  [`0.26.0`](#0260--a-paid-run-tells-you-what-it-learned-about-your-kb--20260822-0132)**: its plan
  landed 20260811 with all eight decisions taken the same day, two more followed at E3's boundary,
  and **all seven increments are built** — the free question surface, the estimator, the paid
  client, the loop, the run transcript, the measurement run, and E7's printed suggestions, so a
  `--deep` run now ends by offering the `links[]` entries its own citations propose. **It did not
  answer against the live API until [`0.25.1`](#0251--pnk-ask---deep-works-against-the-live-api--20260821-0717), which is E6's first
  finding rather than a separate defect**: both response schemas carried keywords structured
  outputs refuses, so every call `400`d before it billed, and no fixture-driven test could have
  seen it. **The name left the unbuilt-work table at 0.26.0** (D-9), and the one thing D-25
  deferred — `--write-suggestions` — is **not planned**.
- **Is document metadata retrieval context? Measured, and the answer was no — on one corpus, through
  one channel**
  ([`plans/20260805_1721-metadata-as-retrieval-context.md`](https://github.com/lucagattoni/pinakes/blob/main/plans/20260805_1721-metadata-as-retrieval-context.md),
  closed 20260807). The investigation ran to its own pre-registered end. Its screen injected
  `title > heading path` into the text that is **embedded**, rebuilt a 195-document / 43 353-chunk
  RFC corpus, and scored a frozen 110-question golden set: **6 questions improved, 6 regressed, 84
  unchanged**. The criterion — fixed in writing before the run — was strictly more improvements than
  regressions, so the answer is no.
  **What that bought is what it was for.** `schema_version` 4 is not taken, and **PDF layout
  heuristics and paid LLM title inference stay unapproved** — two expensive pieces of work, killed
  by one measurement rather than argued about. The screen existed to make exactly that call before
  the irreversible step, and it did.
  **What it does not say.** Only the *vector* channel was injected; reaching the lexical channel was
  the schema bump the screen priced and declined. So the claim is *"vector-only injection does not
  help on this corpus"*, not *"metadata is worthless"*. Re-opening it needs a **corpus**, not a new
  idea about the prefix: this one's `lexical` and `simple-lookup` questions are saturated at 1.00,
  which puts all its power in `paraphrase`.
  Shipped in [`0.16.0`](#0160--metadata-injection-measured-and-answered--20260807-1139) anyway,
  because they are useful whatever the answer: `[chunking] metadata` (default `off`, so you can
  measure it on *your* corpus), `tools/two_leg_gate.py`, and five silent-failure fixes the
  increment's own adversarial review found in it.
- **[The graph release](#the-graph-release--shipped-0110) shipped — and its channel is `off`.**
  Blocked for three days on a *corpus*, not on code; the RFC corpus cleared the reachability
  precondition, and then the retrieval gate improved **0** multi-hop questions and regressed **3**
  (p = 1.0000). `schema_version` 3 means **every existing KB rebuilds once**.
- ⚠️ **`0.11.0`'s verdict is narrower than it reads** — three of the seven edge kinds derived
  **zero** edges on the corpus it was gated against. **0.12.0 ships the check that reports it**, so a
  future corpus cannot repeat it silently.
- **[The template release](#the-template-release--t1-shipped-in-0170) has shipped everything it
  scheduled** — plan written, reviewed, four decisions taken, then **T1 as `0.17.0`** and **T2 as
  `0.18.0`**: template versions now mean something, a gate keeps them meaning it, and `pnk doctor`
  reports how far a KB has drifted rather than only that it has; **T3 as `0.19.0`**, `pnk upgrade`
  printing the lines themselves; **T4 as `0.20.0`**, `--apply` writing the ones that fit; **T5 as
  `0.20.1`**, refusing a vector tier that is not built rather than accepting it silently; and **T7 as
  `0.21.0`**, `pnk templates` and a template declaring its own `files`. **Its two gated increments
  were answered on 20260811**: **T8 is a no-go** — the gate was run and fails leg 3, because every
  divergence in every admissible KB is a manifest value — and **T6 is deferred behind a written
  trigger**, not abandoned. `main` has moved far enough that the plan's Baseline block must be re-run
  before any `file:line` in it is trusted.
- **[One open correction](#open-corrections--one-live)** — the list emptied for the second time when
  all four were decided and built in 0.22.0, and **refilled the next day from E5**: `pnk init`'s
  gitignore warning is printed once, and E5 put the user's verbatim question under `.pinakes/`. It
  emptied once before, on 20260805, and refilled twice within three days then too.
  It refills from *use*, and by five different routes: two
  entries came from **building** 2d and are invisible from reading the code, one from **reading**
  under adversarial review, one was **created** by the increment that closed another, and one came
  from **generalising a fix** — asking where else the defect just repaired still lives.
- **🛑 Nothing is scheduled — for the first time.** Every named body of work is shipped or gated:
  the open-corrections list holds one live *decision*, T6 waits on a **trigger** (a queried KB past
  ~50 000 chunks *with* felt latency), the staged graph channels wait on a **corpus**, and
  **[the deep release](#the-deep-release--the-loop-shipped-in-0240) closed at
  [`0.26.0`](#0260--a-paid-run-tells-you-what-it-learned-about-your-kb--20260822-0132)** —
  [`plans/20260811_1358-deep-release.md`](https://github.com/lucagattoni/pinakes/blob/main/plans/20260811_1358-deep-release.md),
  written 20260811 13:58, **all ten decisions taken, all seven increments built**. **Read that as
  *the next thing to build has not been planned yet*, never as *finished*** — the same reading this
  page's open-corrections list has earned three times over. Part 5 below is where the candidates
  are, and planning is now the work rather than an interruption to it.

---

## The table

Shipped releases first, oldest to newest. **Every release number links to its expanded section
below.** Rows with no number and no date are **not built** — the project's rule is that a version
number belongs to a release only when it is cut
([why](https://github.com/lucagattoni/pinakes/blob/main/CLAUDE.md), STATUS
[§ Release roadmap](STATUS.md#release-roadmap)).

| Release | Date | Title | What it is |
|---|---|---|---|
| **[0.1.0](#010--the-engine--20260725-1527)** | 20260725 15:27 | The engine | • ULIDs, sidecars, manifest, SQLite index<br>• `pnk init` / `sync` / `search`<br>• BM25 + vector + rerank, confidence signal<br>• Markdown and text only |
| **[0.1.1](#011--research-and-plumbing--20260727-1452)** | 20260727 14:52 | Research and plumbing | • 14 graph-RAG investigations under [`docs/graph/`](graph/README.md)<br>• `Makefile`, CI free-path gate<br>• No behaviour change |
| **[0.1.2](#012--the-readme-told-the-truth--20260727-1525)** | 20260727 15:25 | The README told the truth | • Four README claims contradicted the code<br>• `[light]` install path fixed |
| **[0.1.3](#013--the-first-retrospective--20260727-1540)** | 20260727 15:40 | The first retrospective | • What v0.1 taught ([RETROSPECTIVES.md](RETROSPECTIVES.md))<br>• Three rules promoted into `CLAUDE.md` |
| **[0.1.4](#014--the-pdf-build-order--20260727-2119)** | 20260727 21:19 | The PDF build order | • `plans/…-v0.2.md`, I1–I9<br>• Four adversarial review passes before any code |
| **[0.2.0](#020--pdfs-free-path--20260728-1405)** | 20260728 14:05 | PDFs, free path | • `pypdfium2` extractor + layout pipeline<br>• 19-fixture synthetic PDF corpus<br>• Extraction cache, page provenance<br>• `[pdf]` / `[claude]` extras |
| **[0.2.1](#021--one-fact-one-home--20260728-1654)** | 20260728 16:54 | One fact, one home | • `docs/` restructured: [GUIDE](GUIDE.md), [CLI](CLI.md), [MANIFEST](MANIFEST.md), [STATUS](STATUS.md)<br>• Three stale claims fixed |
| **[0.2.2](#022--the-silent-skip-named--20260728-1849)** | 20260728 18:49 | The silent skip, named | • A file matching no `include` glob is now reported<br>• Budget core lands, inert |
| **[0.3.0](#030--it-can-spend-money--if-you-ask--20260729-0417)** | 20260729 04:17 | It can spend money — if you ask | • Paid Claude-vision extractor for scanned PDFs<br>• Ledger, caps, reservation/reconciliation<br>• Paid-path allowlist + four gates<br>• [`pnk budget`](CLI.md#pnk-budget) |
| **[0.4.0](#040--citing-a-page--20260729-0532)** | 20260729 05:32 | Citing a page | • `docs/paper.pdf:p7` citations, CLI and MCP<br>• [`pnk doctor`](CLI.md#pnk-doctor) text-yield check<br>• [VERIFICATION.md](VERIFICATION.md) + its gate |
| **[0.4.1](#041--the-sidecar-that-ate-itself--20260729-0748)** | 20260729 07:48 | The sidecar that ate itself | • A sidecar that would not parse was overwritten by a fresh one — losing a permanent ULID<br>• Data-loss bug live since v0.1 |
| **[0.5.0](#050--links-you-can-walk--20260731-1127)** | 20260731 11:27 | Links you can walk | • [`pnk links`](CLI.md#pnk-links) + `pinakes_links` traversal<br>• Reverse-scan of partner KBs<br>• Second synthetic corpus<br>• `ruamel.yaml`: sidecars round-trip properly |
| **[0.6.0](#060--links-you-can-write--20260801-1051)** | 20260801 10:51 | Links you can write | • [`pnk link`](CLI.md#pnk-link) authors a link<br>• `pnk doctor` reports link coverage as a ratio<br>• `[kb] requires_pinakes`<br>• Retrieval made deterministic |
| **[0.7.0](#070--the-measurement-that-said-no--20260801-1240)** | 20260801 12:40 | The measurement that said no | • Per-question eval artifact, stable ids<br>• Golden set 41 → 74 questions<br>• **Deliverable was a number: [the gate could not be reached on the demo KB](STATUS.md#can-the-graph-releases-gate-be-reached--yes-measured-20260804)** — the RFC corpus cleared it on 20260804 |
| **[0.7.1](#071--the-walk-stays-in-the-kb--20260801-1342)** | 20260801 13:42 | The walk stays in the KB | • `[sources] include` could escape the KB and mint sidecars outside it<br>• Three defects, all live before 0.5.0 |
| **[0.8.0](#080--our-key-not-the-sdks--20260804-0840)** | 20260804 08:40 | Our key, not the SDK's | • **Breaking (paid path):** `PINAKES_ANTHROPIC_API_KEY`, no fallback<br>• Budget defaults raised<br>• STATUS header pinned by a gate<br>• 16 doc claims corrected |
| **[0.9.0](#090--a-site-and-a-name--20260804-1228)** | 20260804 12:28 | A site, and a name | • Docs published to a MkDocs site<br>• 31 dead links found and fixed<br>• Repo renamed → project is **Pinakes**<br>• ⚠️ First upload **refused** — the rename broke trusted publishing; [since fixed](STATUS.md#published-on-pypi) |
| **[0.10.0](#0100--you-can-see-it-working--20260804-1335)** | 20260804 13:35 | You can see it working | • `pnk sync` shows live progress on a terminal<br>• `pnk doctor` no longer tells an interrupted sync to `--rebuild`<br>• Sync timestamps are UTC<br>• ✅ Released and on PyPI |
| **[0.11.0](#the-graph-release--shipped-0110)** | 20260805 07:14 | The graph release | • Structural edges at `schema_version` 3 — **every existing KB rebuilds once**<br>• `pnk doctor` reports the highest-degree hubs<br>• **The expansion channel ships `off`** — its gate improved 0 and regressed 3 |
| **[0.12.0](#0120--the-check-that-would-have-caught-it--20260805-1802)** | 20260805 18:02 | The check that would have caught it | • `pnk doctor` reports heading-path coverage<br>• Missing-backend error names an installed alternative<br>• `pnk doctor` stops printing `$HOME`<br>• `tools/measure_sync_cpu.py` |
| **[0.13.0](#0130--plain-text-can-carry-a-heading-path--20260805-2101)** | 20260805 21:01 | Plain text can carry a heading path | • `[chunking] headings = "numbered"`<br>• Measured on 980 real RFCs, 314/314 modern<br>• A `[chunking]` edit is no longer a silent no-op<br>• `tools/build_rfc_corpus.py` |
| **[0.14.0](#0140--the-tool-stops-crying-wolf--20260805-2222)** | 20260805 22:22 | The tool stops crying wolf | • Heading coverage WARNs only for `markdown` at 0%<br>• `pnk init` adopts a directory with content<br>• A `titles` nudge, never a warning<br>• The sync loop stays serial — measured |
| **[0.15.0](#0150--a-document-says-what-it-is-called--20260805-2248)** | 20260805 22:48 | A document says what it is called | • A Markdown `# ` heading becomes the title<br>• Fence-aware, `##` excluded, Markdown only<br>• No migration — existing titles are never rewritten |
| **[0.15.1](#0151--one-clock--20260806-0051)** | 20260806 00:51 | One clock | • The last three naive-local timestamps are UTC<br>• `pnk init`'s `created`, the paid extractor's pricing, `doctor`'s price age<br>• Pinned by a test running at UTC+14<br>• `CLAUDE.md` 273 → 191 lines, into two new documents |
| **[0.16.0](#0160--metadata-injection-measured-and-answered--20260807-1139)** | 20260807 11:39 | Metadata injection, measured and answered | • **6 improved, 6 regressed, 84 unchanged** — no-go<br>• `schema_version` stays 3; PDF layout heuristics and paid title inference stay unapproved<br>• `[chunking] metadata`, default `off`<br>• `tools/two_leg_gate.py`<br>• Five silent-failure fixes its own review found |
| **[0.17.0](#0170--a-template-version-that-means-something--20260807-2055)** | 20260807 20:55 | A template version that means something | • `notes` 1.0 → **1.1**; **every existing KB now WARNs** in `pnk doctor`<br>• A check live since 0.1 that could never fire<br>• Template content archived under `_versions/`, SHA-256 ledger<br>• `tools/template_drift_gate.py` — seven legs, `check.sh` + CI<br>• `pnk init --template` refuses a non-single-component name<br>• *The template release, interim cut (D-9)* |
| **[0.18.0](#0180--the-drift-warning-says-something-you-can-act-on--20260807-2237)** | 20260807 22:37 | The drift warning says something you can act on | • Drift reported as a **computed line count**, both sides rendered<br>• Template against template — your own tuning cannot appear<br>• `cannot compare` on every KB that exists, with an honest remedy<br>• `same manifest` instead of a misleading `0 lines differ`<br>• An unsupplied variable is a message, not a traceback<br>• *The template release, interim cut (D-9)* |
| **[0.19.0](#0190--what-the-template-changed-in-your-own-file--20260808-0418)** | 20260808 04:18 | What the template changed, in your own file | • `pnk upgrade` — the diff itself, hunk by hunk<br>• **applies cleanly / already applied / conflicts**, and *already applied* is why a later `--apply` cannot duplicate a key<br>• Writes nothing; exit **`3`** is new and means *no baseline*<br>• `cannot compare` on every KB that exists, same wording as `pnk doctor`<br>• Five adversarial passes: 30 → 22 → 13 → 6 → 1<br>• *The template release, interim cut (D-9)* |
| **[0.20.0](#0200--adopting-the-change-after-you-have-seen-it--20260808-0541)** | 20260808 05:41 | Adopting the change, after you have seen it | • `pnk upgrade --apply` — writes the hunks that fit, refuses the whole run if any conflicts<br>• The **only** thing that rewrites a `pinakes.toml` after `pnk init`<br>• A `[budget]` cap applies like any other change — and both commands print it first, with both values (D-10)<br>• Never writes `[kb] requires_pinakes`; it names the keys and leaves the floor to you (D-11)<br>• A conflict now carries two codes: `0` reporting, `1` applying<br>• Five adversarial passes: 5 → 2 → 2 → 3 → 0<br>• *The template release, interim cut (D-9)* |
| **[0.20.1](#0201--a-tier-that-is-not-built-stops-being-accepted--20260808-0641)** | 20260808 06:41 | A tier that is not built stops being accepted | • `vector_tier = "sqlite-vec"` is **refused at load time** — it was accepted and silently ignored<br>• A KB setting it **stops loading entirely**, on every command; the fix is `vector_tier = "auto"` and changes nothing else<br>• Silent on all four surfaces before this: `sync`, `search`, the index's `meta`, `pnk doctor`<br>• A **PATCH with a documented config break**, deliberately (D-12), on 0.7.1's precedent<br>• The value returns when the tier does — D-4 taken as option A (T5)<br>• `meta`'s tier now comes from `search.resolve_tier()`, not a literal<br>• *The template release, interim cut (D-9)* |
| **[0.21.0](#0210--a-template-says-what-it-installs--20260808-1015)** | 20260808 10:15 | A template says what it installs | • `pnk templates` — name, version, description, `--json`; **no `--kb`**, the answer is a property of the install<br>• **CLI-only, decided 20260808** — no `pinakes_*` tool: creation has no MCP surface, so it would list templates its caller cannot use<br>• `template.toml` gains `files = [...]`; **absent still means the historical two**<br>• An entry naming `_versions/`, writing outside the KB, or reading outside the template is refused — all checked before anything is written<br>• The drift gate folds `files` into its hash, closing a hole this increment opened; every hash published before 0.21.0 is unchanged<br>• A damaged template is an `unreadable` row, not a traceback<br>• *The template release, interim cut (D-9)* |
| **[0.21.1](#0211--a-damaged-template-says-so-and-the-gate-reads-what-it-was-chunked-under--20260810-0148)** | 20260810 01:48 | A damaged template says so, and the gate reads what it was chunked under | • Two open corrections closed — the two of six that could be **taken** rather than decided<br>• `graph_gate.py` compares `chunking`: two legs chunked differently are two corpora<br>• A damaged template install is a message on **five** functions, not the two the record named<br>• `TemplateNotInstalledError` — *absent* and *damaged* had been merged into one wrong sentence by the fix itself<br>• A template read error no longer prints where pinakes is installed<br>• Five passes; the last two found only wrong *claims* |
| **[0.22.0](#0220--eight-decisions-and-two-of-them-were-never-decisions--20260811-0826)** | 20260811 08:26 | Eight decisions, and two of them were never decisions | • **T8 closed as a no-go, T6 deferred behind a written trigger** — both gates of the template release answered<br>• **The open-corrections list is empty**, for the second time in its life<br>• `pnk init --backend st\|light`; `init` validates before it writes<br>• `--rebuild` re-chunks paid documents from the cache, and **never spends**<br>• The release workflow creates the release — the step it never had, misdiagnosed six times<br>• **Two of the four corrections were unchecked assumptions, not forks** |
| **[0.22.1](#0221--a-release-sweep-is-table-shaped--20260811-1226)** | 20260811 12:26 | A release sweep is table-shaped | • **Documentation only — no code path changed**<br>• This file's two prose blocks said 0.21.0 while every table in it said 0.22.0<br>• `docs/README.md`'s plan table had **no row** for the plan `CLAUDE.md` calls live — a missing row has no wrong text to find<br>• `RELEASING.md` gains the two checks that catch the class: grep the *superseded* version, and read `ls plans/` against the routing table<br>• Recorded: the 20260807 audit's **40 corrections are untouched** |
| **[0.22.2](#0222--the-release-history-reads-in-order-and-a-gate-keeps-it-that-way--20260811-1348)** | 20260811 13:48 | The release history reads in order, and a gate keeps it that way | • **A row can be complete, correct, and in the wrong place.** Five release rows were out of order across three sequences — `docs/ROADMAP.md`'s release table and its per-release sections both read `0.20.0, 0.22.0, 0.22.1, 0.21.1, 0.21.0, 0.20.1`, and `docs/STATUS.md` put `0.15.1` after `0.16.0` and `0.20.1` after `0.22.1`. Every one is wrong on **both** readings, SemVer and release time. Nothing could see it: ordering is a property of the *sequence*, not of any row, and every check here reads rows — the tables were complete, every anchor resolved and `mkdocs build --strict` was green. **`0.21.0`'s sweep inserted its section one position too early and the next three used that same slot**, so after the first error the tail read strictly newest-first and each following sweep matched the coherent pattern around its own edit. Only the join between the ascending head and the descending tail was wrong, and no sweep's diff touched that line. The `0.15.1` instance was already in the 20260807 audit, verified, and sat unworked for four days while three sweeps added three more. **`tools/release_order_gate.py` now gates all five sequences** in `check.sh` and CI — direction declared per sequence rather than inferred, since a scrambled file would otherwise elect its own answer, and a sequence below a count floor fails rather than passes, because an empty sequence is sorted by definition. Also: ROADMAP's Part 4 heading claimed it ends at `0.10.0` while holding every release through `0.22.1`. **No code path changed** — no `schema_version`, no rebuild |
| **[0.23.0](#0230--pnk-ask-exists-and-it-will-not-pretend-to-answer-you--20260811-1525)** | 20260811 15:25 | `pnk ask` exists, and it will not pretend to answer you | • `pnk ask` — the same evidence and filters as `pnk search`, plus **what answering would take**: one call at `high`/`medium`, decomposition at `low`, *cannot be told* uncalibrated<br>• Every run says **no answer was synthesised** — passages are not an answer<br>• **Nothing prints `--deep`**, which is not built: it is a usage error, not a flag that parses and apologises<br>• `search`'s own notice had advertised `pnk ask --deep`, in the sentence whose test is named for not doing that<br>• `--json` adds `answer: null` and an `escalation` block — one schema whether or not a loop ever runs<br>• The free-path gate covers the command **from the increment that creates it**, by matching its output<br>• Also: the deep-release plan and its eight decisions, and `tools/release_order_gate.py`<br>• *The deep release, interim cut (D-9)* — E2 to E7 are still to come |
| **[0.24.0](#0240--pnk-ask---deep-answers--20260811-2224)** | 20260811 22:24 | `pnk ask --deep` answers | • **`pnk ask --deep`** — the loop: one synthesis call when confident, decompose-search-answer-refold when not, stopping at sufficiency<br>• An **uncalibrated** KB runs it with no early stop and names the bound that ended the run (D-22 E)<br>• Priced and refused before the first call against all three `[budget]` windows at once; `confirm_above_eur` put once; every call reconciled<br>• A paid run that produced no answer **exits 1**<br>• **Default caps raised** — `per_operation_eur` 2.00, `daily_eur` 6.00 — because even a one-round loop exceeded the old one (D-30); `notes` is **1.2**, and an existing KB keeps what it stamped<br>• `[deep] model` and `max_rounds`, settable and unstamped (D-29)<br>• E2's estimator and E3's client ship here<br>• **Two money defects fixed in both paid clients** — a Ctrl-C, and a failure after the response arrived, each voiding a call that may have billed<br>• A gate for docs that quote command output<br>• *The deep release, interim cut (D-9)* — E5 to E7 are still to come |
| | | **[Open corrections](#open-corrections--one-live)** | • **One live** — `pnk init`'s gitignore warning is printed once, and E5 put the user's verbatim question under `.pinakes/`. Its required text is undecided, so it is a decision rather than a task<br>• Six on 20260808, two closed in 0.21.1, four in 0.22.0<br>• **Two of the last four were never forks — they were unchecked assumptions**, refuted by running the code they described<br>• Five routes in: building, reading, shipping, generalising a fix, and reviewing a new surface — none finds the others'<br>• An empty list means nobody has run Pinakes lately |
| | | **[The graph release, staged](#the-graph-release-staged--gates-only-not-scheduled)** | • PPR channel, the `[ner]` extra<br>• Gate-only: no implementation plan exists, by design<br>• Not scheduled |
| **[0.25.0](#0250--a-paid-run-leaves-a-record-of-what-it-was-asked--20260812-0531)** | 20260812 05:31 | a paid run leaves a record of what it was asked | • **The run transcript** — `.pinakes/deep/<operation_id>.json`, written by every `pnk ask --deep` that returns and named in the output and in `--json`<br>• The ledger stores no query text and still does: this is a *second* file, which is what makes a `pnk budget` row explicable after the fact<br>• Filed under the `operation_id` the ledger groups by; the name is validated as a ULID<br>• The stored `answer` object is the one `--json` prints, **from one renderer**; `--json` gains `answer.call_ids` and a `transcript` path<br>• **Protected like a paid cache entry** — nothing sweeps it, `--rebuild` and `--clear-cache` leave it — and removed only by **`--clear-cache=transcripts`**, a *store* rather than a third authorisation<br>• Written for a run that **returned**, answer or not; a refusal, a decline and an `abort` halt write none<br>• *The deep release, interim cut (D-9)* — E6 and E7 are still to come |
| **[0.25.1](#0251--pnk-ask---deep-works-against-the-live-api--20260821-0717)** | 20260821 07:17 | `pnk ask --deep` works against the live API | • **It never had.** Every answer call carried `integer` `minimum`/`maximum` and every decompose call an array `maxItems`; structured outputs accepts neither, so the API returned `400` **before the request billed**<br>• Every `--deep` invocation in 0.22.0–0.25.0 failed, at a cost of €0.00 — the accountant reserved, refused and voided exactly as designed<br>• The citation bound is **kept, not dropped**: `enum: [1..passages]` states what `minimum`/`maximum` stated, so E4's two halves both survive<br>• The subproblem cap has no such form and moves to the prompt body and `parse_subproblems`, which were always its real enforcement<br>• **Found by E6's measurement run on its first real call** — the fixtures could not have caught it, because the `Transport` seam means no test ever sent a schema to the API<br>• The gate is a recursive shape assertion over both builders against the documented unsupported keywords<br>• *The deep release, fix (D-9)* — E6 and E7 are still to come |
| **[0.25.2](#0252--the-guidance-carries-its-own-lessons--20260821-1447)** | 20260821 14:47 | the guidance carries its own lessons | • **Documentation only** — the recurring lessons routed into `docs/BUILDING.md` (mutation-harness discipline, gate exit status, the CI-matrix leg check, two plan-reading rules) and RETROSPECTIVES' own § *Start here* (four new rows)<br>• `CLAUDE.md` § *Changing retrieval* names which corpus can license a change; the live-plan block slims to pointers, the E6 status moving into the plan itself<br>• A committed mutation harness, `tools/mutate.py`, proposed in `plans/` |
| **[0.25.3](#0253--the-deep-loop-is-measured--20260821-2234)** | 20260821 22:34 | the deep loop is measured | • **E6 is built** — the measurement run published the over-reservation factor: **29.75×** on the cheap `synthesis` branch, **50.92×** and **22.35×** on the two loop branches, for €0.2131 against a €5.1836 worst case<br>• Every `deep/estimate.py` constant carries its measurement and the command that produced it; **none lowered**, the corpus being synthetic<br>• Six defects in `tools/deep_reservation.py`, which had no tests — now 27, mutation-verified 10/10<br>• Two defects in the runbook's own step (c) |
| **[0.25.4](#0254--what-the-mutation-battery-cannot-reach--20260821-2249)** | 20260821 22:49 | what the mutation battery cannot reach | • **Documentation only** — BUILDING § 4 names the mutation step's own blind spot, with 0.25.3's rewrapped-command case (`4d5debf`)<br>• The lesson filed as a retrospective entry<br>• 0.25.3's section on this page moved out of Part 5, where its sweep had landed it |
| **[0.26.0](#0260--a-paid-run-tells-you-what-it-learned-about-your-kb--20260822-0132)** | 20260822 01:32 | a paid run tells you what it learned about your KB | • **E7 — printed suggestions.** Two documents cited in support of one answer is a fact nothing records; the run prints the `links[]` entries that observation proposes, to paste and commit<br>• **It prints; it never writes** — `--write-suggestions` is deferred (D-25 A) and unplanned<br>• `rel: co-cited`, `origin: deep`, the sidecar named on the block's first line; `--json` carries the same fragment verbatim<br>• **A document cannot talk the model into suggesting a link** — suggestions come from *citations*, and a citation is a passage number the schema bounds<br>• Both endpoints re-checked against what the run cited, resolved through `pnk link`'s own containment check<br>• **Four defects the tests could not see**, three found by mutating — including a surviving *control* mutant, and a containment test satisfied by absence<br>• **DESIGN §9's risk row, false since E4**, corrected<br>• *The deep release, **final** cut (D-9) — the name leaves the unbuilt-work table* |
| **[0.27.0](#0270--the-mutation-step-gets-its-guard--20260822-0619)** | 20260822 06:19 | the mutation step gets its guard | • **`tools/mutate.py`** — the per-increment mutation battery, run by a tool rather than by hand. `docs/BUILDING.md` § 4 was the procedure's one *silently-failing* step<br>• Each written rule is a refusal: tracked-and-committed target, anchor matched **exactly once** before the first write, `__pycache__` cleared either side, never `-x`, restore in a `finally` with its bytes verified, **zero kills exits non-zero**<br>• **Five ways a run can lie that the rules did not cover, all measured** — a skipped test exits 0 like a passing one; an already-red selector kills everything; `SIGTERM`/`SIGHUP`/`SIGQUIT` skip `finally`; `PYTEST_ADDOPTS` smuggles in `-x`; `PYTHONPYCACHEPREFIX` hides the cache<br>• pytest's `<error>` tag covers a collection failure **and** a setup/teardown failure, which are opposite events — conflating them threw away real kills<br>• **25 mutants against its own guards, 25 killed.** Three rounds of that found four clauses no battery-driven test could reach<br>• *A developer tool — it ships in no wheel and changes nothing for any KB* |
| **[0.27.1](#0271--the-gates-read-what-they-were-cited-for--20260822-0704)** | 20260822 07:04 | the gates read what they were cited for | • **The release-order gate reads a sixth sequence** — STATUS's *Published on PyPI* prose, which `RELEASING.md` had delegated to it while no pattern matched it<br>• That list had been mis-ordered since 20260821, through every green run<br>• It may **lag** the other five (an entry is held back until verified from the index) and may never **lead** them — an exemption without a direction is a hole<br>• **A fragment opening with a `---` front-matter fence is refused** — three 0.24.0 fragments carried one and `--apply` published all three<br>• No code path changed: no `schema_version`, no rebuild |
| **[0.27.2](#0272--the-install-is-a-region-no-test-reached--20260822-1001)** | 20260822 10:01 | the install is a region no test reached | • **`pnk serve` was dead on every fresh install of all 38 published releases** — `mcp>=1.28` uncapped, and mcp 2.0.0 dropped `mcp.server.fastmcp` 3.5 h before Pinakes first published<br>• 31 green tests never saw it: they run against a **locked** mcp, and 37 `--frozen` CI invocations never resolve the dependency at all<br>• **`tools/wheel_import_gate.py`** installs the built wheel and imports all **57** modules, so the next module is covered without anyone remembering<br>• It runs **in front of `uv publish`** — a dependency major arrives with no commit here, and PyPI never takes a version back<br>• `anthropic` and `sentence-transformers` measured, deliberately **not** capped — the remedy is testing the resolve, not capping on reflex<br>• Three adversarial rounds, each finding defects in the previous round's **remedies**; 47 mutants, 0 survivors |
| **[0.28.0](#0280--the-port-was-four-lines-the-gate-was-not--20260823-0138)** | 20260823 01:38 | the port was four lines, the gate was not | • **`pnk serve` runs on `mcp` 2.x** — `FastMCP` → `MCPServer`, and the requirement's `<2` cap becomes a `>=2` floor<br>• The four tool schemas are **byte-identical** across the move, captured from a live session on each and committed at `tools/mcp_tool_schemas.json`<br>• `serverInfo.version` now carries **Pinakes'** version; every release to 0.27.2 advertised the *mcp library's* (`1.28.1`)<br>• **The handshake both workflows used was a coin flip** — three JSON-RPC lines and a closed stdin answered `tools/list` 5/10, 1/10, 2/10 and 1/10 across the protocol versions; `make smoke` was red on every run<br>• `tools/mcp_handshake_gate.py` drives mcp's own client, and CI checks the advertised version against the **wheel's filename**<br>• Two adversarial rounds, 24 findings, **every one in the remedies rather than the port**; 29 mutants, 0 survivors |
| **[0.28.1](#0281--a-gate-audited-against-itself--20260823-0206)** | 20260823 02:06 | a gate audited against itself | • **A lagging sequence may now be at most two releases behind** — its ceiling was its own newest entry, so deleting that entry hid the deletion<br>• **Two Parts may not claim the same versions** — Part ranges are read from the headings, so twenty characters appended to `# Part 5` legitimised a misfiled section<br>• **The Part floor is the real count** — at one below it, demoting the last heading passed exactly<br>• No code path changed: no `schema_version`, no rebuild |
| **[0.28.2](#0282--the-guides-commands-were-re-run-against-the-build-that-ships-them--20260823-0247)** | 20260823 02:47 | the Guide's commands were re-run against the build that ships them | • **`docs/GUIDE.md` claimed every command on it was run against `0.2.0`** — twenty-six releases back, on the published site<br>• **Nine output blocks had drifted**: `notes@1.1` against a shipped `1.2`, a `You get:` tree missing two files `init` writes, `€0.26`/`€1.69` estimates against a live `€0.20`/`€1.33`<br>• **Three separate places said only one surface can spend** — `pnk ask --deep` has been the second since 0.24.0<br>• `docs/CLI.md` had the same class of defect and is fixed with it<br>• **Two blocks deliberately not re-run, and the page now says which** — the paid transcript and the two-KB walkthrough<br>• No code path changed: no `schema_version`, no rebuild |
| **[0.28.3](#0283--a-gate-that-could-not-see-the-list-next-door--20260823-0310)** | 20260823 03:10 | a gate that could not see the list next door | • **A seventh sequence** — STATUS's *Published versions* row, four releases behind through green runs of every gate<br>• **The gate reported those releases present, and they were — in the sequence next door**, forty lines up in the same file<br>• **A `within` anchor** scopes a pattern to one region, since the row is a table cell and not a run of lines; two matches are refused rather than resolved to the first<br>• **The row may never lag the prose beside it** — a relation beats a bound: 29 commits sat green with the row already wrong, the relation fires 11 commits earlier, 0 false positives over 53<br>• 11 mutants, 11 killed; no code path changed |
| **[0.29.0](#0290--the-batteries-were-kept-and-one-caught-what-four-green-gates-missed--20260823-1250)** | 20260823 12:50 | the batteries were kept, and one caught what four green gates missed | • **91 mutants committed** under `tools/batteries/`, one file per target, all 91 killed<br>• **The docstring that decided this was an assumption**: measured, 78 of 81 anchors still resolved a day to a week later, and all three failures were *refusals*<br>• **`--check-anchors`** resolves anchors against the working tree in milliseconds; `tests/test_batteries.py` gates anchors, selectors, double claims and a declared count<br>• **A resolvability gate, not a regression gate** — nothing runs a battery automatically<br>• **Two of its own mutants were killed about nothing**, one of them a `SyntaxError` reading KILLED in a batch reporting `0 errored`; a compile refusal now precedes the first write<br>• **A battery caught what four green gates and two review passes missed**<br>• A cleared context settles its own role, and its peers', before it writes<br>• no code path changed |
| **[0.29.1](#0291--the-instruction-file-extracted-to-its-own-guideline--20260823-1359)** | 20260823 13:59 | the instruction file, extracted to its own guideline | • **274 → 220 lines**, five sections moved to the page that owns them, **nothing lost** — 112 removed lines traced to a home<br>• The plan-status bullets were **duplicates**, deleted rather than moved: the routing table already had them<br>• **Every defect the review found was about the neighbourhood, not the content** — a per-file agent cannot audit what lies outside its file<br>• A duplicated rule had **already drifted**: README named the deep release as live, three releases late<br>• Four dead links written while creating pointers — `CLAUDE.md` is not in the built site, so `mkdocs --strict` cannot see them<br>• **Stops at 220, not 150**, and says so<br>• no code path changed |
| | | **[The deep release](#the-deep-release--the-loop-shipped-in-0240)** ✅ **complete 0.26.0** | • `pnk ask --deep` — the budgeted agentic loop, **built and shipped in [0.24.0](#0240--pnk-ask---deep-answers--20260811-2224)**<br>• The last paid entry point; the allowlist is complete at two<br>• **All seven increments are done** — the free surface, the estimator, the client, the loop, the run transcript, the measurement run and the printed suggestions<br>• **E6 published the over-reservation factor** — 29.75x on the cheap synthesis branch, 50.92x and 22.35x on the two loop branches, with every constant measured and none lowered; it was the only increment that spends real money, under `docs/MEASUREMENT-RUN.md`<br>• **E7 shipped in [0.26.0](#0260--a-paid-run-tells-you-what-it-learned-about-your-kb--20260822-0132)** — a run ends by printing the `links[]` entries its own citations propose; `--write-suggestions` is deferred (D-25 A) and **not planned** |
| | | **[The template release](#the-template-release--t1-shipped-in-0170)** | • Template ecosystem, `pnk upgrade`, `sqlite-vec` tier<br>• **T1 shipped in 0.17.0, T2 in 0.18.0, T3 in 0.19.0, T4 in 0.20.0, T5 in 0.20.1, T7 in 0.21.0**<br>• **T8 closed 20260811 — gate run, fails leg 3: every divergence in every real KB is a manifest value**<br>• **T6 deferred behind a written trigger** — a queried KB past ~50 000 chunks *with* felt latency<br>• The name stays here (D-9): T6 can still return |

---

# Part 1 · The engine — `0.1.x`

Five releases in three days. One of them shipped code.

## 0.1.0 — The engine · 20260725 15:27

Ten increments, all at once, because there was nothing to be incremental against yet.

**What it gave you**

- [`pnk init`](CLI.md#pnk-init) — stamps a KB from a template, mints its permanent ULID.
- [`pnk sync`](CLI.md#pnk-sync) — walks your documents, mints a sidecar per file, builds
  `.pinakes/index.db`.
- [`pnk search`](CLI.md#pnk-search) — BM25 + vector cosine + RRF fusion + optional local rerank.
- [`pnk serve`](CLI.md#pnk-serve) — MCP surface for an agent.

**The decisions that never changed after this**

- **Your documents are the truth; the index is derived.** `.pinakes/` is disposable
  ([DESIGN § 2](DESIGN.md#2-anatomy-of-a-kb), [§ 3](DESIGN.md#3-storage)).
- **ULIDs are permanent.** Never renumbered, never regenerated, no migration machinery — ever.
- **Unknown manifest keys are a hard error**, not a silent default
  ([MANIFEST.md](MANIFEST.md), [DESIGN § 2.1](DESIGN.md#21-the-manifest--pinakestoml)).
- **An error carries a remedy**, not just a message.
- **Exit codes are a contract**: 0 success, 1 operational failure, 2 usage error
  ([CLI § Exit codes](CLI.md#exit-codes)).

**What it could not do:** PDFs, links, spending money.

→ The pipeline itself: [DESIGN § 4.1](DESIGN.md#41-the-free-pipeline-every-query-0). The sync
algorithm that keeps a KB from corrupting:
[DESIGN § 6.4](DESIGN.md#64-sync-semantics-the-part-that-silently-corrupts-a-kb-if-left-vague).

## 0.1.1 — Research and plumbing · 20260727 14:52

No behaviour change — the wheel's code is identical to [`0.1.0`](#010--the-engine--20260725-1527).

- **~3,000 lines of graph-RAG research** landed under [`docs/graph/`](graph/README.md): LightRAG,
  Microsoft GraphRAG, Graphiti, HippoRAG 2, fast-graphrag, Graph-R1, LinearRAG, MiniRAG and more,
  plus [`PINAKES_APPROACH.md`](graph/PINAKES_APPROACH.md) synthesising them into a gated build order.
  Six adversarial passes (27 → 7 → 8 → 5 → 1 → 0 findings).
- **A `Makefile`** where every target wraps what CI actually runs.
- **The free-path CI gate** — promised in the v0.1 plan and never shipped, because the item sat in a
  section no increment owned.

→ What the literature actually supports: [graph/GRAPH_RAG.md](graph/GRAPH_RAG.md). Three of those
projects **may never be copied from** for licence reasons — flagged in
[graph/README.md](graph/README.md).

## 0.1.2 — The README told the truth · 20260727 15:25

An audit against the shipped CLI found the README was the only surface overclaiming.

- `pnk ask --deep` was described as existing. It did not, and did not for another seventeen days — it [shipped in `0.24.0`](#0240--pnk-ask---deep-answers--20260811-2224), on 20260811.
- Install lines pointed at a PyPI package that returned 404.
- The headline diagram showed a `.pdf` — the one file type v0.1 could not read.

This is where the rule *"verify docs by running the commands they show"* comes from. The
`[light]`-install trap it found stayed a caveat for eleven releases and is
[a flag as of 0.22.0](STATUS.md#the-light-backend-is-a-flag-on-pnk-init) — `pnk init --backend
light`, after two of the two real KBs stamped from `notes` made the same manual edit for the same
reason. The [GUIDE](GUIDE.md#choosing-a-backend) leads with it.

## 0.1.3 — The first retrospective · 20260727 15:40

Findings from v0.1, and three rules promoted into `CLAUDE.md`:

- Verify a release the way a stranger would — `git tag -l`, `gh release list` — never by believing
  the CHANGELOG. (The [procedure](RELEASING.md) grew out of this.)
- **Never `git merge` from inside the feature worktree.** Three commands report success and nothing
  lands.
- The README describes what ships, checked by running it.

→ Every finding since: [RETROSPECTIVES.md](RETROSPECTIVES.md).

## 0.1.4 — The PDF build order · 20260727 21:19

- [`plans/20260727_1543-v0.2.md`](https://github.com/lucagattoni/pinakes/blob/main/plans/20260727_1543-v0.2.md)
  — I1–I9, reviewed over **four adversarial passes** before a line was written.
- The *read the clock, never compose a timestamp* rule, after four invented `HH:MM` stamps landed in
  the future.

---

# Part 2 · PDFs, and the first money — `0.2.0` → `0.4.1`

## 0.2.0 — PDFs, free path · 20260728 14:05

Five increments (I1–I5) — [the ledger](STATUS.md#v02-increment-ledger).

- **The extractor seam** — a protocol plus a lazy registry, so core stays torch-free and
  extractor-free. `[pdf]` and `[claude]` become opt-in extras.
- **A synthetic hard-case PDF corpus** — 19 committed fixtures across seven strata (two-column,
  tables, running heads, ligatures, scanned, pathological, baseline). Ground truth is hand-written
  from each fixture's *spec*, never from an extractor's output, which would only prove an extractor
  agrees with itself.
- **The layout pipeline** — characters → blocks → columns → reading order, with running-head
  suppression and hyphenation joining. No PDF library, no filesystem.
- **The extraction cache**, and page provenance in the index.

→ How to actually index a PDF: [GUIDE § Indexing PDFs](GUIDE.md#indexing-pdfs) — **and note it is
[off by default](STATUS.md#caveat-pdfs-are-off-by-default-but-no-longer-silently)**, which
[`0.2.2`](#022--the-silent-skip-named--20260728-1849) is about. Quality methodology:
[DESIGN § 7.1](DESIGN.md#71-pdf-extraction-quality).

## 0.2.1 — One fact, one home · 20260728 16:54

The docs were restructured for continuous development: landing an increment should edit **one** file.

- New: [`GUIDE.md`](GUIDE.md), [`CLI.md`](CLI.md), [`MANIFEST.md`](MANIFEST.md),
  [`STATUS.md`](STATUS.md),
  [`docs/README.md`](https://github.com/lucagattoni/pinakes/blob/main/docs/README.md).
- **[`STATUS.md`](STATUS.md) becomes the only place in the repo that says what is built.**
- [`DESIGN.md`](DESIGN.md) becomes rationale only. README becomes deliberately **version-free**, so
  it cannot drift again.

→ The routing table this produced — *where does a fact live* — is in
[docs/README.md](https://github.com/lucagattoni/pinakes/blob/main/docs/README.md), and it is what
tells you which file to edit when something lands.

## 0.2.2 — The silent skip, named · 20260728 18:49

[`0.2.0`](#020--pdfs-free-path--20260728-1405) shipped PDF ingest as its headline feature while the
template stamped `include = ["**/*.md", "**/*.txt"]`. So the real first-run experience was: drop in a
PDF, run sync, read `0 indexed`, get no hint why.

- **`pnk sync` now names what it skipped**, grouped by extension, with the exact glob to add.
- Only files Pinakes *could* index are reported — a wrong hint is worse than none.
- **The budget core lands, inert**: pure logic, nothing calls it, so nothing can spend.

An adversarial review found seven more defects in the fix itself, two of which handed the silence
straight back. This release is also where the **mutation-testing rule** was adopted: break the guard
on purpose, watch the right test fail, restore.

→ The gap that remains: a template change reaches **new KBs only**, so a KB created before this one
never sees the explanation. That is
[KB-UPDATES § 3](KB-UPDATES.md#3-the-gap-is-live-not-theoretical), and closing it is
[the template release](#the-template-release--t1-shipped-in-0170) — whose
[`0.17.0`](#0170--a-template-version-that-means-something--20260807-2055) makes the divergence
*detectable*; adopting it still needs `pnk upgrade`.

## 0.3.0 — It can spend money — if you ask · 20260729 04:17

The first release with a paid code path. Four increments (I6a–I7c);
[why it was held until then](STATUS.md#cut-as-030--20260729-0417).

**What can spend, and only this**

- `pnk sync` with `[extraction] backend = "claude-vision"`, or `--extract=claude-vision`.
- Nothing else. Ever. It is an **enumerated allowlist** (`.paid-path-allowlist`), held by four gates
  — the decisive one runs the whole free path in a fresh subprocess and asserts no paid client ever
  reached `sys.modules`.

**What stands behind the money**

- Every call reserved before it is made, reconciled from the response's own usage.
- Caps that **refuse** rather than overspend. An append-only ledger; a correction is another record.
- Every free check runs before any paid one — including refusing a PDF whose text layer is already
  healthy.

**Measured live, 20260729, for €0.43** —
[the run](STATUS.md#the-measurement-run-has-been-done--20260729-0317-043)

| | Result |
|---|---|
| Scanned-PDF quality, paid path | **1.000** on every metric |
| Same, free path | **0.000** |
| Reservation accuracy | Over-reserved **11.5×** — wrong in the safe direction |
| The refusal branch | Fired for real, on a real document |

→ The design: [DESIGN § 5 Cost control](DESIGN.md#5-cost-control). The trade-off measured:
[DESIGN § 7.2](DESIGN.md#72-what-bypassing-layoutpy-on-the-paid-path-actually-costs). Day-to-day:
[GUIDE § Watching what it costs](GUIDE.md#watching-what-it-costs) and
[`pnk budget`](CLI.md#pnk-budget). To re-run the measurement yourself:
[MEASUREMENT-RUN.md](MEASUREMENT-RUN.md).

## 0.4.0 — Citing a page · 20260729 05:32

- **`path:page` citations** — `docs/paper.pdf:p7`, or `:p7-8` across a page break, on the CLI and MCP
  alike. The `p` is deliberate: `:12-480` already meant character offsets.
- **[`pnk doctor`](CLI.md#pnk-doctor) text yield** — reports pages below the fitted floor **per page,
  not per document**, because a 200-page report with eight scanned inserts is exactly the document
  worth knowing about.
- **[VERIFICATION.md](VERIFICATION.md)** — every promise, and the test that holds it, with a gate
  asserting each named test exists. It replaced the v0.2 plan's table, **61 of whose 98 test
  references did not resolve**.

→ Why offsets address the *extraction* and not the file:
[DESIGN § 4.6](DESIGN.md#46-chunking-and-tokens).

## 0.4.1 — The sidecar that ate itself · 20260729 07:48

A patch, but the most serious bug the project has had.

- A sidecar that failed to parse was dropped from the walk. The document then looked new. The mint
  path wrote a **fresh sidecar over it** — destroying its permanent ULID and every authored link.
- `pnk sync` reported success. `pnk doctor` afterwards reported everything healthy, because the
  evidence had been overwritten by the thing that destroyed it.
- **Present since v0.1.** `0.4.1` is the first release without it.

→ **`0.4.0` and earlier can still do this** — never pin one
([STATUS § Published on PyPI](STATUS.md#published-on-pypi)). The pairing algorithm it broke:
[DESIGN § 6.4](DESIGN.md#64-sync-semantics-the-part-that-silently-corrupts-a-kb-if-left-vague).

---

# Part 3 · Links — `0.5.0` → `0.7.1`

The links release was deliberately cut **twice**: an interim MINOR once the traversal surface worked,
and a final one once authoring landed. The design it implements is
[DESIGN § 6.2 Cross-KB links](DESIGN.md#62-cross-kb-links); the build order is
[`plans/20260729_0256-links-and-graph.md`](https://github.com/lucagattoni/pinakes/blob/main/plans/20260729_0256-links-and-graph.md).

## 0.5.0 — Links you can walk · 20260731 11:27

- **[`pnk links`](CLI.md#pnk-links)** — what a document connects to and what connects to it. Depth
  capped at 3 server-side, fan-out capped, no query language, ever.
- **`pinakes_links`** on the MCP surface — the same traversal, for the agent this project calls its
  primary caller.
- **Reverse-scan** — `pnk sync` reads a partner KB's *committed sidecars* (never its index) and
  records what links into this one.
- **A second synthetic corpus** (`tests/partner-kb`, 21 documents) and a gate keeping both corpora
  sparse.
- **`ruamel.yaml` replaces `pyyaml`.** Comments, quoting and blank lines now survive a rewrite — and
  a silent corruption stops: under YAML 1.1 `country: NO` was read as `False` and written back as
  `false`.

**A cross-KB neighbour is terminal at any depth.** This KB holds a partner's links pointing *back*
at it, never the partner's internal ones — so expanding through one shows a systematically
incomplete slice no caller could distinguish from the whole.

→ Walk two KBs yourself:
[GUIDE § Following links between two KBs](GUIDE.md#following-links-between-two-kbs). The round-trip
guarantee and its **bounds**: [MANIFEST.md](MANIFEST.md) and [VERIFICATION.md](VERIFICATION.md). Why
ruamel:
[the decision record](https://github.com/lucagattoni/pinakes/blob/main/plans/20260731_0602-decision-ruamel-yaml.md).

## 0.6.0 — Links you can write · 20260801 10:51

- **[`pnk link <source> <target> --rel REL`](CLI.md#pnk-link)** — writes one entry into the source
  document's own sidecar and nothing else. Aliases and `self` are resolved to ULIDs **before**
  anything reaches disk, which is what makes a link mean the same thing on someone else's machine.
- **It never mints a sidecar.** A source without one is refused, with `pnk sync` as the remedy.
- **`[kb] requires_pinakes`** — a manifest can declare the oldest Pinakes that can read it, so an
  out-of-date build says so instead of reporting a typo.
- **Retrieval made deterministic.** Every tiebreak resolved to the SQLite rowid, which the schema
  says has no identity across rebuilds — so two indexes over identical sources could answer
  differently. Measured: 1 question in 41 moved. Ordering is now total; **no scored number changed**,
  which is what a tie-break-only fix should do.

→ The full reproducibility measurement:
[STATUS § Is the evaluation reproducible?](STATUS.md#is-the-evaluation-reproducible--measured-20260801-0035).
What `requires_pinakes` does and does not close:
[KB-UPDATES § 4](KB-UPDATES.md#4-compatibility-posture).

## 0.7.0 — The measurement that said no · 20260801 12:40

**This release's deliverable is a number, not a feature.**

The graph release turns its expansion channel on only if enough multi-hop questions *improve*. An
improvement can only come from a question that fails today.

| | Required | Measured |
|---|---|---|
| Multi-hop questions failing today | ≥ 7 | **1** |
| Of those, reachable without authored edges | ≥ 7 | **1** |

**So [the graph release](#the-graph-release--shipped-0110) stopped here.** No
`schema_version` bump, no forced rebuild for every KB in existence, for an edge table whose channel
could never be licensed.

Two findings behind that number, both of which outlive it:

- **`tests/demo-kb` has no tags and one flat directory** — so exactly *one* derived edge kind can
  cross a document boundary. Any result on this corpus is a claim about one directory.
- **The retrieval funnel already sees the whole corpus.** 30 candidates against ~30 chunks. A failing
  question here is a *ranking* failure, not a recall failure a channel could fix.

Also shipped: per-question eval outcomes as a committed artifact, stable question ids, and the golden
set grown 41 → 74 with a `simple-lookup` control class.

→ The full measurement, with every figure:
[STATUS § Can the graph release's gate be reached?](STATUS.md#can-the-graph-releases-gate-be-reached--yes-measured-20260804).
Current retrieval scores: [STATUS § Measured numbers](STATUS.md#measured-numbers). The multi-hop
design being tested: [DESIGN § 4.3](DESIGN.md#43-multi-hop-without-paying-for-it).

## 0.7.1 — The walk stays in the KB · 20260801 13:42

`roots` had to stay inside the KB. `include` was validated nowhere.

- A `..` pattern **indexed files outside the KB and minted sidecars beside them**.
- An absolute pattern produced a bare traceback with no remedy.
- A **symlinked directory** carried the walk out with no `..` and no absolute path anywhere.

All three live since before [`0.5.0`](#050--links-you-can-walk--20260731-1127). `pinakes.toml` is
committed and shared — cloning a KB and running sync ran *its author's* `include` against *your*
tree.

→ The increment:
[`plans/20260731_2128-source-walk-containment.md`](https://github.com/lucagattoni/pinakes/blob/main/plans/20260731_2128-source-walk-containment.md).
The field it hardened: [MANIFEST.md](MANIFEST.md).

---

# Part 4 · Hardening, publishing, and every release since — `0.8.0` onward

## 0.8.0 — Our key, not the SDK's · 20260804 08:40

**Breaking, for anyone running the paid extractor.**

- `anthropic.Anthropic()` was constructed without `api_key`, so the SDK read `ANTHROPIC_API_KEY` out
  of whatever environment it was handed. On a machine where any other tool exports it, the paid path
  had **a live key nobody aimed at it**.
- The variable is now `PINAKES_ANTHROPIC_API_KEY`, passed explicitly, with **no fallback** — a
  fallback would restore the whole defect silently.
- Budget defaults raised: `per_operation_eur` 0.05 → 0.30, `monthly_eur` 5.00 → 30.00. The old
  per-operation cap admitted **zero** rounds of any multi-call paid operation.
- A gate now pins [STATUS.md](STATUS.md)'s own header to `__version__` — it had drifted for four
  consecutive releases while every table below it was updated.
- **Sixteen documentation claims corrected** against the code, including the GUIDE saying twice that
  *"nothing here spends money, and nothing can"* three lines below the row instructing
  `--extract=claude-vision`.

→ The defaults and their validation: [MANIFEST.md](MANIFEST.md). What actually bounds spend:
[DESIGN § 5](DESIGN.md#5-cost-control) and [MEASUREMENT-RUN.md](MEASUREMENT-RUN.md).

## 0.9.0 — A site, and a name · 20260804 12:28

**Documentation only — no code path changed.**

- **[lucagattoni.github.io/pinakes](https://lucagattoni.github.io/pinakes/)** — MkDocs Material over
  the existing `docs/`, deployed on every push to `main`, built `--strict` on every PR. The strict
  build found and fixed **31 dead links and anchors**.
- Nothing in `docs/` moved: those filenames are load-bearing in code.
- **The project is `Pinakes`; everything you can type is `pinakes`.** The repository moved to
  [github.com/lucagattoni/pinakes](https://github.com/lucagattoni/pinakes). No identifier changed.

⚠️ **And then the upload was refused — 20260804 12:33. It is fixed; 0.9.0 is on PyPI.**

- Renaming the repository broke PyPI **trusted publishing**, which matches on the exact repository
  name. The OIDC token claimed `repository: lucagattoni/pinakes` while the registered publisher
  still said `Pinakes`, so PyPI answered *"valid token, but no corresponding publisher"*.
- **Nothing had been uploaded**, so the version was never burned — the same tag published once a
  project owner corrected the publisher on pypi.org and the failed job was re-run.
- **This is the release that taught the project how a good publish hides.** Three separate caches
  each said the upload had failed when it had not: the JSON endpoint still named `0.8.0` an hour
  later; `/simple/` listed no file **even cache-busted**; and `uvx --refresh` answered
  *unsatisfiable* from uv's own cache until `--no-cache`. What settles it is the workflow's
  `Publish to PyPI` log, which prints one `Uploading …` line per file and cannot be cached.
- The direction matters: a false *"it did not publish"* invites re-cutting a version PyPI will
  never accept twice.

→ The standing record: [STATUS § Published on PyPI](STATUS.md#published-on-pypi). The verification
step this rewrote: [RELEASING.md](RELEASING.md). Working install lines:
[GUIDE § Install](GUIDE.md#install).

## 0.10.0 — You can see it working · 20260804 13:35

✅ **Released and published** — tagged `v0.10.0`, on PyPI at 20260804 13:39 UTC.

- **`pnk sync` shows live progress on a terminal.** A CPU-only embedding run measured at ~2.4
  documents/minute — 300 documents ran over **two hours with nothing printed**, making a slow sync
  and a hung one look identical. One self-overwriting line, throttled to ~1/second, only on a real
  tty and only without `-q`.
- **[`pnk doctor`](CLI.md#pnk-doctor) no longer tells an interrupted first sync to `--rebuild`** — a
  remedy that would discard every embedding the interrupted run had already written. It now says
  `pnk sync`, which continues incrementally.
- **Sync timestamps are UTC**, matching the lock's. They disagreed by the local offset, in the one
  place a user weighs before `--force-unlock`ing a possibly-live sync.
- The GUIDE's first install command **did not work in a bare directory** (`uv add` needs a
  `pyproject.toml`; a KB has none), and troubleshooting offered only the destructive lock remedy.

→ [GUIDE § Install](GUIDE.md#install) and [GUIDE § Troubleshooting](GUIDE.md#troubleshooting) carry
the corrected text. The locking model: [DESIGN § 6.5 Concurrency](DESIGN.md#65-concurrency).

---

## 0.12.0 — The check that would have caught it · 20260805 18:02

- **[`pnk doctor`](CLI.md#pnk-doctor) reports what share of chunks carry a heading path, and warns
  when a whole source type carries none.** The RFC realism corpus indexed **106 806 chunks with not
  one heading path** and nothing said so — and that is what bounds 0.11.0's expansion-channel gate:
  `in-section`, `parent` and `child` all derive from `heading_path`, so **three of the seven edge
  kinds derived zero edges on the corpus the gate was measured against**. A graph result on such a
  corpus reads as *"structure does not help"* when what it measured is *"the structure was never
  extracted"*.
- **The missing-backend error names an installed alternative** instead of prescribing the ~2 GB
  `sentence-transformers` install to someone who deliberately chose `[light]`. It checks with
  `find_spec` and never by loading the backend — a check must not have the side effects of the thing
  it checks.
- **`pnk doctor` no longer prints the operator's home directory**, in the one command whose output
  is the natural thing to paste into an issue. A path genuinely outside the KB is left as printed.
- **`tools/measure_sync_cpu.py`** — the cores-busy instrument the open sync-CPU item requires before
  anything about that loop may change. **The measurement itself has not been taken.**

Two of the three retrospectives this release earned are about tests rather than code, and both are
the same defect wearing different clothes: an assertion that was satisfied by something other than
the property it named. The sampler watched the launched pid, so `-- uv run pnk sync` measured `uv`
and would have reported **0.0 cores for a saturated core** — not a broken-looking number, a
finding-looking one. And a test comparing two *differently rounded* renderings of one value passed
locally and on two CI legs, failing only on the third.

→ [RETROSPECTIVES.md](RETROSPECTIVES.md) carries all three.

---

## 0.13.0 — Plain text can carry a heading path · 20260805 21:01

- **`[chunking] headings = "numbered"`** reads a dotted-decimal outline (`1.`, `1.1.`, `2.`) into
  `heading_path` for the `text` source type. Opt-in and off by default. Until now every type but
  `markdown` recorded no `heading_path` at all — which is what left a 300-RFC corpus with 106 806
  chunks and none, and so bounds [0.11.0's gate](#the-graph-release--shipped-0110): `in-section`,
  `parent` and `child` all derive from it and derived **zero** edges there.
- **It refuses rather than guesses.** `1.` at line start is also an ordered list, so acceptance is
  decided over the whole document, and a document whose outline does not walk cleanly yields **no**
  headings rather than a partial labelling. The floor is therefore exactly the previous behaviour.
- **Measured against 980 real RFCs**, in rounds that doubled each time and re-ran every earlier fix:
  644 accepted, and **314 of 314 modern-era documents — 100% at every round size**. Two thirds of
  all rejections are documents with no numbered sections at all.
- **A `[chunking]` edit is no longer a silent no-op.** An incremental sync re-chunks a document only
  when the document changed, so editing any `[chunking]` key applied nothing and said nothing. The
  index now records what it was built under; `pnk sync` names the key that moved and
  [`pnk doctor`](CLI.md#pnk-doctor) reports `chunking coherence`.
- **`tools/build_rfc_corpus.py`** builds the realism corpus from a script instead of one machine.

The release's three retrospectives are all the same shape: something reported success while the
thing it named had not happened. A guard that could not fire. A warning that cleared itself without
the fix being applied. And two plausible predicate rules that the corpus refused — each removed a
false positive and took genuine documents with it.

→ [RETROSPECTIVES.md](RETROSPECTIVES.md), and the measurement in
[§5.4](https://github.com/lucagattoni/pinakes/blob/main/plans/20260805_1721-metadata-as-retrieval-context.md).

---

## 0.14.0 — The tool stops crying wolf · 20260805 22:22

Three changes with one theme: **a signal nobody can act on is worse than no signal**, because it
teaches the reader to skip the ones that matter.

- **[`pnk doctor`](CLI.md#pnk-doctor)'s heading coverage WARNs only for `markdown` at 0%** — the one
  case a user can fix. A KB holding a single `.py` file used to warn on every run forever, with a
  remedy amounting to *"a limit of the tool"*. The rest is reported OK with a note that separates
  three facts previously wearing the same 0%: `text` *can* carry a heading path, `text` with the
  grammar already on means those documents were **offered and refused**, and `code`/`pdf` cannot
  today.
- **[`pnk init`](CLI.md#pnk-init) adopts a directory that already has content.** Cloning a repo and
  initialising inside it is how a KB actually starts, and a `.git`, a `README.md` and a
  `pyproject.toml` made that *"not empty"*. The blanket refusal is gone; what replaces it is
  narrower and stronger — **init never overwrites a file that is already there**. An adopted
  `.gitignore` missing `.pinakes/` is flagged with the line to add, because that directory holds
  the index and the spend ledger.
- **A `titles` check** counts documents still carrying the title minted from their filename — the
  `title: rfc9110` problem. A nudge, never a warning: both committed corpora are at 100%, and the
  filename fallback is deliberate. Inference stays rejected — an RFC's first line is
  `Internet Engineering Task Force (IETF)`.

**And one question closed by measuring instead of arguing.** The first sync was suspected of using
one core of ten. It uses **five**: peak 5.0, mean 4.8, over 55 RFCs and 16 557 chunks under
`fastembed`. The loop is serial and the backend beneath it is not, so the document loop **stays
serial** — a pool sized `os.cpu_count() - 1` would have been nine workers where there was room for
two. The instrument proved itself in the same run: `uv run` sat at 0.0% while its child sustained
491.9%, which is exactly the 0.0-cores answer the pre-fix tool would have reported and nobody would
have questioned.

→ [RETROSPECTIVES.md](RETROSPECTIVES.md).

---

## 0.15.0 — A document says what it is called · 20260805 22:48

- **A Markdown document is titled by its own `# ` heading.** `rfc9110-notes.md` opening on
  `# HTTP Semantics` is now titled *HTTP Semantics* rather than *"rfc9110 notes"*.

**This began as a correction, not a feature.** The record said `sync` mints from the filename *"when
the document has no Markdown H1"* — implying it read one otherwise. It never did: `skeleton()` was
called without `title=` at both call sites, and `title=` appeared nowhere in `sync.py`. The claim
survived because the two forms usually differ only in capitalisation — `# Access restrictions`
sitting beside `title: access restrictions` reads exactly as though the heading was used, when the
value is the stem with its hyphens swapped for spaces.

That is the same shape as the chunking diagnosis corrected in 0.13.0: **a fallback described for a
mechanism that was never running.** Both were found by checking what the code does rather than what
the note says.

An H1 is structure, not inference — which is what keeps this distinct from the first-line heuristic
that remains rejected, since an RFC's first line is `Internet Engineering Task Force (IETF)`.
Markdown only, fence-aware, `##` excluded. **No migration:** titles are minted only when a sidecar
is created, so every existing KB keeps what it has, and `title` stays the user's field.

---

## 0.15.1 — One clock · 20260806 00:51

- **Every timestamp Pinakes writes is UTC.** The last three naive-local sites are gone: `pnk init`
  stamped `[kb] created` from the machine's wall clock, the paid extractor priced a document against
  a local `now`, and `pnk doctor`'s price-age check subtracted a naive local clock from a price
  table whose `as_of` is authored in UTC.

**A mixed scheme is worse than a consistent local one**, which is why this is a fix and not a
tidy-up. `sync`, `lock`, the ledger and the accountant were already UTC, so the three remaining
sites meant two stamps written into the same index no longer shared a zero point. None of them
failed loudly: a KB minted in Europe and read in California simply disagreed about when it was made.
`is_stale()` was the same defect one layer up — the code compared a UTC value correctly while its
docstring said local, a mismatch invisible on a UTC machine and silent everywhere else.

**Pinned by a test that fails on a naive clock, not merely on a wrong one.** It runs under
`TZ=Pacific/Kiritimati` — UTC+14, chosen because the naive stamp lands on a *different date* for ten
hours of every day, so the failure is loud rather than a rounding minute.

**`[budget] timezone` is untouched and is not an exception.** It decides where a *daily* or
*monthly* window starts for a user who wants their cap to reset at local midnight; the ledger still
stores UTC and converts at read time, so no local time is ever written to disk.

Also documentation, in the same release: `CLAUDE.md` went from 273 lines to 191, with the increment
procedure moving to [`BUILDING.md`](BUILDING.md) and the silently-failing contracts to
[`INVARIANTS.md`](INVARIANTS.md). **INVARIANTS is an index, not a copy** — eight of its nine facts
already had owners, so each row links its owner and only the five rules nothing else states are
written out. The relocation's real cost was its **pointers**: 21 references across the tree named
`CLAUDE.md` for content that had moved, and 13 of them sat in `src/` and `tests/`, which a
docs-only change does not look like it touches. A grep for the moved *wording* finds none of them —
the sweep has to run on the source file's own name.

## 0.16.0 — Metadata injection, measured and answered · 20260807 11:39

- **The investigation closed with a number.** Are `title` and `heading_path` retrieval context, or
  display metadata? Injected into the text that is **embedded**, over a 195-document /
  43 353-chunk RFC corpus, scored against a blind-authored, frozen 110-question golden set:
  **6 questions improved, 6 regressed, 84 unchanged.** The criterion — strictly more improvements
  than regressions — was fixed in writing before the run. It is not met.

**What the no-go bought, and it is the point of the whole exercise.** `schema_version` stays at 3,
and **PDF layout heuristics and paid LLM title inference stay unapproved** — both were gated on this
showing movement. A cheap screen was inserted *ahead of* the irreversible schema bump precisely so
the expensive work could die on evidence rather than on argument, and that is what happened.

**Read it as narrowly as it was measured.** Only the **vector** channel was injected. Reaching the
lexical channel is the schema bump the screen priced and declined, so the claim is *"vector-only
injection does not help on this corpus"* — not *"metadata is worthless"*. What would re-open it is a
**corpus**, not another idea about the prefix: this one's `lexical` and `simple-lookup` questions
are saturated at 1.00, which puts all of its statistical power in `paraphrase`.

**Why a null was believable at all — the controls, not the number.** Both legs were proven to be the
same corpus (one sha256 over all 43 353 chunk texts, equal); the injection was proven to have
reached the vectors (mean cosine **0.8398**, zero unchanged); the uninjected index was proven to
still reproduce the frozen baseline, **110 rows of 110**, twice. Chunk texts are byte-identical
between the legs by construction, so without the second control a silent no-op and a true null
would have produced identical artifacts — and the conclusion would have been drawn from nothing
having happened.

**Shipped anyway, because they are useful whatever the answer.** `[chunking] metadata`, default
`"off"`, so a KB whose questions are *not* solved by BM25 plus a reranker can measure this rather
than inherit the verdict; turning it on is reported as drift, applied by `pnk sync --rebuild`, and a
prefix that would not fit the model's window is refused per document instead of being silently
truncated off the longest chunks. And `tools/two_leg_gate.py`, which refuses to compare two eval
legs differing in anything but one named header key — `graph_gate.check_identity` compared five
fields and not `chunking`, so two legs chunked differently compared clean. **That gap in the
three-leg gate stayed open until 0.21.1**, which closed it as an open correction; the tense here is
past because of that release, not because 0.16.0 fixed it.

**Five silent-failure fixes came out of the increment's own adversarial review**, and the sharpest
is worth stating because it falsified a claim the increment itself had written. The option was put
in `[chunking]` rather than `[retrieval]` *because* `[chunking]` is recorded in the index and so
cannot flip unnoticed. True of the mechanism; false of every index that existed. Identity keys
absent from an index read as *unknown, never drifted* — the rule that stops an upgrade demanding a
rebuild of every KB — and this key is absent from every index built before 0.16.0, with only a
`--rebuild` ever stamping it. So on a pre-existing KB the flip was completely silent: no drift,
nothing re-embedded, and `pnk doctor` printing `OK  chunking coherence` over vectors with no prefix
in them. Absence is now read as `off` for this one key, on the ground that no release which could
have written such an index was able to inject anything. The other four: `--rebuild` carried a
paid-extracted document's *vectors* forward while stamping the current settings over the index; the
fix for that shipped without the truncation guard and with a commit that could publish a document
holding chunks and no vectors; `python -m pinakes.eval` would score an index its manifest no longer
describes; and a title edit under injection left the vectors carrying the old title with nothing
saying so.

---

## 0.17.0 — A template version that means something · 20260807 20:55

*The template release, interim cut — T1 of T1–T4, T7. Per D-9 the release cuts more than once, so
the name stays in the unbuilt-work table until the final cut.*

- **A check that had never been able to fire, for eleven releases.** `pnk doctor` has compared the
  KB's recorded template reference against the installed one since `0.1`. `notes` declared
  `version = "1.0"` in every commit since it was written, while the files that version denotes
  changed in ten later ones. So every KB recorded `notes@1.0`, the installed template was also
  `notes@1.0`, and the check printed `OK` — over eleven different template contents. `notes` is now
  **1.1**, and the comparison finally discriminates.

**The user-visible effect is the intended one, and it is not small.** Every KB in existence now
prints `WARN template: KB says notes@1.0, installed is notes@1.1`. Nothing is applied
automatically, no KB needs changing, and **the WARN does not change `pnk doctor`'s exit code** —
only a `FAIL` does — so no CI that runs it turns red. `pnk upgrade` (T3) is what diffs; applying
a change is still the user's own edit.

**Why the archive had to come first.** A KB records a *reference*, never the content. Without a
copy of what a version meant, nothing on the machine can answer *what was `notes@1.1`?* — which is
why `pnk upgrade` could never have worked, whatever the version string said. Template content is
now archived under `src/pinakes/templates/<name>/_versions/<version>/`, travels in the wheel, and
`templates/_versions.toml` records each file's SHA-256. **`1.0` is deliberately not archived**: it
denotes eleven different contents, so any single answer would be wrong for ten of them, and a diff
computed from the wrong base is worse than no diff.

**A convention nobody followed became a gate.** `tools/template_drift_gate.py` runs seven legs in
`check.sh` (0.12 s) and as its own `template-drift` CI job, so editing a template without bumping
its version is a red build. It **reports which mode it ran in every time**: its git-history leg
needs a full clone and says so when it has been skipped, because a skip is not a pass. Its own
review found the gate committing the defect it exists to catch — a relative `--templates` made it
report `all legs green` over a tree it had never looked at — and the leg now checks both halves
against `origin/main`.

**Also:** `pnk init --template` refuses a name that is not a single path component. `notes/../notes`
and `../templates/notes` both resolved to a real template before, and `notes/eval` raised a bare
`FileNotFoundError`. Harmless while every directory under the package root was a template — but
with the archive present, `--template notes/_versions/1.1` would have stamped a KB from a version
nobody released. And `[tool.ruff] extend-exclude` now keeps the project's own formatter away from
the archived bytes: `check.sh` runs `ruff format` repo-wide and ruff rewrites Python inside
Markdown fences, so the formatter had write access to the very bytes the ledger freezes.

No `schema_version` bump, so no rebuild.

---

## 0.18.0 — The drift warning says something you can act on · 20260807 22:37

*The template release, interim cut — T2 of T1–T4, T7. Per D-9 the release cuts more than once, so
the name stays in the unbuilt-work table until the final cut.*

- **0.17.0 made every KB in existence start warning; this makes the warning useful.** Where the
  recorded and installed versions are both archived, `pnk doctor` renders **both** through one
  context and reports how many lines separate them.
- **Template against template, never template against manifest** — and that is the design point, not
  an implementation detail. Both sides are generated, so nothing you wrote is in either: a value you
  tuned that the template *renders* is identical on both sides and cancels, and a literal you edited
  enters neither, because neither side is your file. A report mixing the two could not tell a
  template change from your own tuning, and would present the second as the first.
- **On every KB that exists today it says `cannot compare`**, and that is the honest answer rather
  than a gap. `notes@1.0` denotes eleven different template contents, so it is deliberately not
  archived — a diff from the wrong base is worse than no diff. The remedy names the comparison
  available now (`pnk init` a throwaway directory and diff its `pinakes.toml` against yours) and
  **promises nothing a later release can't keep**: an earlier draft said the comparison becomes
  automatic from the next bump, which is false for exactly the people who read it most, because an
  unarchived version's content is gone rather than pending.
- **A bump that leaves the manifest alone reports `same manifest`, never `0 lines differ`.** A
  template version covers four files and this comparison reads one of them. Of the ten commits
  between `notes@1.0` and `1.1`, **five touched only the starter golden set** — so two identical
  manifests under two different versions is the ordinary case, and `0 lines differ` would have been
  true of the manifest and read as *nothing changed*.
- **A template needing a variable this build cannot supply is a message, not a traceback.**
  `jinja2.UndefinedError` is not a `PinakesError`, so it reached the terminal as a stack trace; it
  now names the template, the version and the variable, and in `pnk doctor` it is one `WARN` row
  rather than the end of the report.
- **The variables this build supplies stopped being written down twice.**
  `tools/template_drift_gate.py` leg (vi) asserts every archived version renders, and it had its own
  copy of the key set; it now builds from `template.CONTEXT_KEYS`, the same union the product
  renders through. The failure that avoids is the gate staying green while `pnk doctor` raises on
  the KB in front of it.
- **Two of five mutants survived the first mutation pass, and neither was a bug in the code.** One
  test asserted the right property without ever calling the function under test; the other made only
  substitution edits, and one line replaced by another is still one line on each side of a diff — so
  it was invariant under the very implementation it existed to reject. Both are recorded in
  [RETROSPECTIVES.md](RETROSPECTIVES.md).

No `schema_version` bump, so no rebuild.

## 0.19.0 — What the template changed, in your own file · 20260808 04:18

*The template release, interim cut — T3 of T1–T4, T7. Per D-9 the release cuts more than once, so
the name stays in the unbuilt-work table until the final cut.*

- **`pnk upgrade` prints the lines themselves.** 0.17.0 made every KB warn, 0.18.0 said how far it
  had drifted; this says *what changed* — the diff between the template version your KB records and
  the one installed, both rendered from the archive through one context, so nothing you wrote
  appears in it as a change.
- **Each change is then placed against your manifest, and there are three answers, not two.**
  *applies cleanly*, *already applied* — you adopted it by hand, or a newer `pnk init` wrote it —
  and *conflicts*. The middle one is not a curiosity: calling it "clean" is what would make a later
  `--apply` insert lines that are already there, duplicating a key and failing the file's own
  re-parse.
- **It writes nothing**, and the test that says so compares the path set, the bytes and the mtimes
  of every file *and directory* under the KB. The first version compared bytes alone and the
  increment's own named mutation survived it.
- **Exit `3` is new and means *no baseline*** — the comparison could not be made and no action of
  yours would make it possible. Distinct from `1`, which means something is wrong and it is yours to
  fix, and from `0`, which a script reads as *up to date*. **Every KB in existence gets `3`**,
  because `notes@1.0`'s content was never archived; the message is `pnk doctor`'s, to the word,
  because two surfaces disagreeing about one KB is worse than either wording.
- A conflict exits `0`. The command writes nothing, so it has nothing to fail at.

**Five adversarial passes, finding 30 → 22 → 13 → 6 → 1**, and the shape of that curve is the
finding worth keeping. Passes 2 and 3 each found that a *previous pass's fixes* were wrong or
untested; pass 4 found the tooling that had silently lost six of them. Four separate fixes were
described as "pinned by test X" while reverting them left the suite green. **A claim that a fix is
pinned is a claim about a failing test** — recorded in [RETROSPECTIVES.md](RETROSPECTIVES.md), with
the classes ranked by what they cost.

No `schema_version` bump, so no rebuild.

## 0.20.0 — Adopting the change, after you have seen it · 20260808 05:41

- **`pnk upgrade --apply` writes the hunks that fit.** 0.19.0 printed what the template changed;
  this adopts it. Every hunk that *applies cleanly* is written, every one that is *already applied*
  is skipped and counted, and **one conflicting hunk refuses the whole run** — a half-upgraded
  manifest with no record of which half is worse than an unupgraded one.
- **It is the only thing in Pinakes that rewrites a `pinakes.toml` after `pnk init`**, and stating
  the count is the rule: a reviewer checks it by counting write sites. What makes the exception
  narrow enough to hold is that the write is bounded by the report — **nothing reaches the file
  that was not on screen first**.
- **A `[budget]` default applies like any other change (D-10), and the consent path is what pays
  for it.** A spending cap that would move is printed with the old value *and* the new one, under
  its own heading, by `pnk upgrade` and `pnk upgrade --apply` alike — and **only** when one really
  would move, so its absence is information too. The applier has no `[budget]` predicate and no
  second flag; a later reader who adds one has reversed a decision rather than tightened a rule.
- **It never writes `[kb] requires_pinakes` (D-11).** When applied hunks introduce keys it names
  them and says you may want a floor. It suggests no number: nothing in the repository maps a
  manifest key to the release that introduced it, so a printed `>=x.y.z` would be a guess wearing a
  decimal point.
- **The recoveries, each of which is a refusal before the first byte:** the previous manifest goes
  to `pinakes.toml.orig`, named in the output with the warning that nothing ignores it; the result
  is re-read and the original restored if it will not load; a held sync lock, a manifest whose line
  endings disagree, and an existing backup are each refused, leaving the KB byte-identical. A
  symlinked manifest is written **through**, not replaced — `sidecar.write` had learned that first
  and the new writer had not inherited it.
- **A conflict now carries two exit codes and that is the point.** `0` from `pnk upgrade`, which
  writes nothing and so has nothing to fail at; `1` from `pnk upgrade --apply`, which was asked for
  a write it could not make.
- **Nothing changes for a KB recording `notes@1.0`** — still `cannot compare`, still exit `3`,
  still nothing written. Adoption starts working at the *next* template bump.

**Five adversarial passes, finding 5 → 2 → 2 → 3 → 0**, and what they found is the part worth
keeping: **every defect in pass 1 was a property of the *write*** — line-splitting, symlinks,
permissions, a dotted key named by its first segment — because the test surface had been built from
a plan about placement and consent, and none of those notice what happens to a file's inode. Pass 2
found a *correct* function reused one scope too wide: `Hunk.section` is the table a hunk **starts**
in, so a hunk adding a new table had every one of its keys credited to the preceding one — after
`[budget]`, that is a false spending-cap heading, and every consent test passed. Pass 3 found the
first two fixes unfinished; pass 4 found nothing in the code and three false claims in documents the
increment never opened.

No `schema_version` bump, so no rebuild.

---

## 0.20.1 — A tier that is not built stops being accepted · 20260808 06:41

- **`vector_tier = "sqlite-vec"` is refused at load time.** It named a tier that does not exist in
  any release, and was accepted anyway. What that bought a user who set it: `pnk sync` stamped
  `numpy` into the index's `meta` whatever the manifest said, `search` never read the field at all,
  and `pnk doctor` reported nothing — **silent on all four surfaces there were to check**.
- **A KB setting it now stops loading entirely — every command, not only search.** That is the cost,
  it is stated rather than softened, and it is why the release notes lead with it. The fix is one
  line, `vector_tier = "auto"`, and it changes nothing about how that KB behaves: it was already
  getting the NumPy tier. The error names the tiers that are built and points at `docs/STATUS.md`.
- **A PATCH carrying a documented config break, deliberately** (D-12, taken 20260804), on this
  project's own **0.7.1** precedent — a release that hard-errored a manifest which previously
  loaded, on the reasoning that the previous behaviour *was* the defect. It holds exactly here.
- **The value is not cancelled.** It returns in the increment that builds the tier; `VECTOR_TIERS`
  says so where the removal is, so nobody reads the removal as a decision against `sqlite-vec`.
- **D-4 taken as option A**, and the evidence was not in the plan that asked the question: three
  lines below `VECTOR_TIERS`, `graph_channel` already refuses `"ppr"` for the same reason — *a
  manifest that can ask for a mode the code does not implement is a setting that silently does
  nothing*. A plan's open decision is what the *plan* has not settled, which is not the same as what
  the repository has not settled.
- **The index's `vector_tier` is written from a resolver, not a literal.** `search.resolve_tier()`
  is now the single answer to which tier ran; `sync` had hardcoded `"numpy"` beside a parsed field
  nothing consumed.

No `schema_version` bump, so no rebuild.

---

## 0.21.0 — A template says what it installs · 20260808 10:15

- **`pnk templates` lists what this build can stamp a KB from.** Name, version, description, and
  `--json` carrying the `notes@1.1` reference a manifest records. Until now `template.available()`
  was reachable from exactly one place — the error raised when `pnk init --template` names something
  that does not exist — so the way to discover what was installed was to get something wrong first.
- **It takes no `--kb`, and that is a decision rather than an omission.** The listing is a property
  of the *install*, identical wherever it runs. Which template a given KB is on is a different
  question, and `pnk upgrade` answers it.
- **CLI-only — the MCP question O-1 left open, decided 20260808.** There is no `pinakes_*` tool for
  the listing. The server's four tools all answer about content in a KB it was pointed at; there is
  no `init`, no mutation, no KB-creation path at all. A template tool would therefore name things
  its caller cannot act on, and would be the first tool on that surface reporting machine state from
  *outside* the served KBs — which `docs/DESIGN.md` §4.7 states as a boundary, not a convenience.
- **A template declares the files it writes: `files = [...]`.** It replaces the hardcoded
  `README.md` / `eval/questions.yaml` pair. **An absent key still means exactly those two** — every
  template in existence declares nothing, so absent has to keep meaning what it always did; an
  explicit `files = []` is a different statement and copies nothing.
- **Four refusals, and every entry is checked before any entry is written**, so a bad declaration
  never leaves a half-stamped KB. An entry naming `_versions/` is refused because containment cannot
  catch it — the path lands *inside* the KB, and what is wrong with it is provenance, not escape:
  an archived version is the frozen record of what a reference *meant*.
- **Writing outside the KB and reading outside the template are two layers, and neither covers the
  other.** An escaping destination reads from inside the template; an escaping source writes to
  inside the target. The plan's rule sentence named only the first while its test list required the
  second, so both were built.
- **The drift gate folds `files` into its content hash, closing a hole this increment opened.**
  `template.toml` is otherwise excluded from that hash, deliberately — hashing the file that
  declares the version would make every bump change the hash by construction, so *a version bumped
  with no content change* could never be detected. That exclusion was priced when the file held only
  a name, a version and a description. `files` decides what a KB is stamped with, so it would have
  sat outside the very check the archive exists to provide. Only the list is folded in; an absent
  key contributes nothing, so **every hash published before 0.21.0 is byte-identical** and no ledger
  row needed migrating.
- **A damaged template is named, not fatal.** One template directory without a readable
  `template.toml` used to abort the whole listing as a traceback, reporting nothing about the
  templates that read perfectly. It is now an `unreadable` row beside the good ones, with a line
  naming what to reinstall and exit `1`. The underlying defect in `template.describe` reaches
  `init`, `doctor` and `upgrade` too and stays open — what is fixed is the blast radius this command
  introduced.

No `schema_version` bump, so no rebuild.

---

## 0.21.1 — A damaged template says so, and the gate reads what it was chunked under · 20260810 01:48

**Two open corrections, and they are the two of six that could be *taken* rather than decided.**
Both had a stated required text; the four left behind each need a fork picked, which is why they
are still open (Part 5).

**`tools/graph_gate.py` compares the `chunking` block.** It checked `k`, `embedding`, `rerank`,
`ranking` and `retrieval` and not the block `eval.header` records so a leg can say what it was built
under. Two legs chunked differently are not one corpus with noise — they are two corpora, so rows
paired on `id` were produced by searching different texts, and the rechunk is reported as whatever
was under test. Measured: `max_tokens` 510 against 480 moves 63 of 1 858 chunk texts on one RFC.
This is the gate that licensed the graph channel's default. Nothing under `chunking` is excepted,
which is the one place it differs from `tools/two_leg_gate.py` and differs deliberately: there
`chunking.metadata` *is* the independent variable, here it is `graph_channel`.

**A damaged template install is a message rather than a traceback — on five functions, not the two
the record named.** `render_manifest`, `declared_files` and `copy_extras` held the identical
unguarded read, so closing only `describe` and `render_archived` would have left the defect three
functions away. `jinja2.TemplateSyntaxError` needed its own arm because it is raised by
`Template(...)`, not by `render`, where the existing handler sat.

**The fix then came within one handler of opening its own replacement.** Making the failure a
`PinakesError` routed it into an `except` that `pnk doctor` and `pnk upgrade` already had — one
answering *"is not installed here"*, which sends the owner of a present-but-damaged template to
install what they already have. Nothing went red: both surfaces still returned WARN and exit 3, and
the existing tests cover the absent case, which still worked. `TemplateNotInstalledError` splits
them, with a test on each surface. **A traceback is loud and a wrong sentence is quiet**, so this
was a downgrade that read as an upgrade.

A third pass found the `OSError` arm printing the install's absolute path: `OSError.__str__` appends
its `filename`, and doctor's de-homing cannot help because it strips the *KB* root, which a template
is outside by construction. The same defect class as the closed home-directory leak, one module
away.

**Five review passes, and the last two found only claims rather than code** — a comment asserting a
fixture discriminated a mutant one function after measuring that it does not, and a changelog
fragment describing a subset of its own commit. The test for the path leak was green for the wrong
reason twice before it could fail: first with an injected error carrying no `filename`, then with
one whose `strerror` made the code short-circuit before ever reaching the leaking branch.

## 0.22.0 — Eight decisions, and two of them were never decisions · 20260811 08:26

**Both gates of the template release answered, and the open-corrections list emptied.** Six
increments, each landed separately.

**T8 is closed as a no-go and T6 is deferred behind a written trigger.** T8's gate was run and
fails on leg 3: every divergence in every admissible KB is a manifest value, which the gate itself
defines as a preset rather than a template. Waiting cannot move that — re-opening needs a different
*kind* of KB — so the gate's own redirect was taken instead, and it became `pnk init --backend`.
T6 defers because a passing gate could not answer what it would buy: performance is measured on an
unlabelled 100k-chunk corpus and equivalence only at demo-kb scale, by the plan's own statement.
The trigger is written down: a KB that is actually queried crossing ~50 000 chunks *with* felt
latency.

**Two of the four open corrections were never forks — they were unchecked assumptions**, and this
is the durable finding. The `pnk init` item rejected the full fix as unavailable, believing
containment could not be judged before the target existed; `lands_inside` resolves the parent and
`resolve()` is non-strict, so it can. The paid-rebuild item called re-chunking a paid call; the
extraction cache lives under `.pinakes/` and survives `--rebuild`, so the text is free. **Both were
refuted by running the code they described**, after standing for days.

| Decision | What shipped |
|---|---|
| D-18 | `pnk init` validates a template's declaration before it creates anything — a refusal leaves no directory, and for an *adopted* directory leaves the user's files untouched |
| D-16 | `--apply` records the reference on the `same manifest` outcome and says so first — consent, the shape D-10 already took for `[budget]` |
| D-17 | An eval header records the tier that *ran* beside the one that was *asked for*; no existing value changes |
| D-15 | `--rebuild` re-chunks a paid document from the extraction cache, and when the cache is cold keeps its chunks and records the index as inhomogeneous. **A rebuild never spends** |
| D-20 | `pnk init --backend st\|light`, and three copies of a false claim that `init` "cannot see which extra you installed" |
| D-19 | The release workflow creates the GitHub release — the step it never had |

**The release step is the sharpest of the six.** `docs/STATUS.md` recorded "the workflow failed to
create the release" at six consecutive releases; no workflow in this repository's history ever
contained a release-creating step, and `docs/RELEASING.md` step 8 had always said to create it by
hand. One document's routine step was the other's anomaly for six releases, and each restatement
re-confirmed the *symptom* — which is equally consistent with both explanations. Reading the
workflow once settled it.

**Three tests in this release were green for the wrong reason and were caught by mutation, not by
reading**: a path-leak assertion satisfied because the code short-circuited before the leaking
branch, a `-k` filter that selected nothing and printed "125 deselected", and a flag assertion
satisfied by the shell comment explaining the flag.

## 0.22.1 — A release sweep is table-shaped · 20260811 12:26

**Documentation only — no code path changed.** With every plan built out and the open-corrections
list empty, the first question of the next session was what the repo says about itself. **This file
said `0.21.0`.**

- **Its tables were right and its prose was wrong, which is the worst arrangement.** The release
  table carried a `0.22.0` row, Part 4 carried the full `0.22.0` write-up, and § *Open corrections*
  said *none live*. But `## Where things stand right now` was stamped **20260808 06:41** — *30
  releases in 14 days*, *latest on PyPI `0.21.0`*, the template release *part-shipped, T1 to T4* —
  and § *The template release* still read **"T4 and T7 are still to come"** about increments that
  had shipped on 20260808. A reader checking one claim against another would have found agreement
  five places out of six.
- **A release sweep is table-shaped, and that is why it missed.** The row being added points at
  itself, so a table gets written every time. A paragraph summarising *all* releases has no row to
  add, so nothing in the act of cutting a release makes it obvious — five consecutive sweeps updated
  every enumeration in the file and left both summaries behind.
- **The second instance had no wrong text to find at all.** `docs/README.md`'s plan-routing table —
  the table whose entire job is to say which plan is live — had **no row** for
  `plans/20260811_0720-decisions-gates-and-corrections.md`, the plan `CLAUDE.md` names as the live
  build order and the authority for eight decisions. The plan was written, its six increments were
  built and landed, and the index of plans never learned it existed. **A missing row is invisible to
  every check that reads rows**; only asking *"is everything that exists listed here?"* finds it.
- **Both fixed, and the class is now checked rather than remembered.**
  [RELEASING.md](RELEASING.md)'s sweep table gains two steps: **grep the tree for the version you
  just superseded** — which does not care whether the stale claim is in a table or a paragraph — and
  **read `ls plans/` against the routing table**, which is the only thing that finds an absence.
  `CLAUDE.md`'s live-plan pointer now says its build order is built out and names what the next body
  of work needs, which is a plan.
- **What the audit turned up on the way.** The 20260807 documentation audit's **40 corrections have
  never been worked** — the file has one commit, the one that created it — and that audit explicitly
  deferred a full review of `docs/ROADMAP.md` until after T2, which shipped in 0.18.0. Neither is
  visible from any release's own sweep.

Verified against the index rather than the CHANGELOG: **34 releases in 17 days**, 26 versions on
PyPI, every one from `0.2.2` on.

---

## 0.22.2 — The release history reads in order, and a gate keeps it that way · 20260811 13:48

**A row can be complete, correct, and in the wrong place.** Five release rows were out of order
across three sequences:

| Sequence | Read |
|---|---|
| `docs/ROADMAP.md` — the release table | `0.20.0, 0.22.0, 0.22.1, 0.21.1, 0.21.0, 0.20.1` |
| `docs/ROADMAP.md` — the per-release sections | `0.20.0, 0.22.1, 0.22.0, 0.21.1, 0.21.0, 0.20.1` |
| `docs/STATUS.md` — the release roadmap | `0.15.1` after `0.16.0`; `0.20.1` after `0.22.1` |
| `CHANGELOG.md` | checked and clean, headings and link definitions both |

Every misplacement is wrong on **both** readings — SemVer and release time — so no ordering
convention made any of them right.

**Nothing could see it.** Ordering is a property of the *sequence*, not of any row in it, and every
check this project owns reads rows: the tables were complete, every anchor resolved, `mkdocs build
--strict` was green, and a reader checking any single row found it correct.

**How it happened, from the six release commits.** `0.20.1` was appended correctly (`2da0e07`).
`0.21.0` (`96b3b35`) then inserted its section one position too early — after `0.20.0`'s rather
than after `0.20.1`'s — and the next three sweeps (`c83e877`, `df832fe`, `93c20ab`) each used that
same slot. **The tail was locally self-consistent at every step**: after the first error it read
strictly newest-first, so each following sweep saw a coherent pattern around its own edit and
matched it. Only the join between the ascending head and the descending tail was wrong, and no
sweep's diff ever touched that line. The `0.15.1` instance was already in the
[20260807 audit](https://github.com/lucagattoni/pinakes/blob/main/plans/20260807_2143-docs-audit-findings.md),
verified against PyPI upload times, and sat unworked for four days while three sweeps added three
more.

**The fix is a gate** — `tools/release_order_gate.py`, in `check.sh` and CI's `build` job, on the
threshold this project already applies to a checklist that has missed something repeatedly. Two
design points are why it will still work in a year:

- **Direction is declared per sequence, never inferred.** Inferring it from whichever way most
  adjacent pairs agree would let a badly scrambled file elect its own answer and pass.
- **A sequence below a count floor fails rather than passes.** An empty sequence is sorted by
  definition, so a pattern that silently stops matching — a reformatted table, a changed heading
  style — is how a check like this dies quietly.

It was watched failing before it was trusted: against the pre-fix tree it names all nine
misorderings and exits 1, CI scrambles a copy and asserts both the exit and the stated reason, and
three mutations of its core were each killed by exactly the test that should kill it.

Also here: ROADMAP's **Part 4 heading claimed `0.8.0` → `0.10.0`** while holding every release
through `0.22.1`, twelve past its own stated range — now `0.8.0` onward, a form that cannot go
stale at a cut. `docs/RELEASING.md` gains the rule the gate enforces: **append after the newest one
that is there, found by reading it, never by repeating last time's position — read the sequence,
not the neighbourhood.**

**No code path changed**: no `schema_version`, no rebuild, nothing different for any KB.

## 0.23.0 — `pnk ask` exists, and it will not pretend to answer you · 20260811 15:25

**The deep release's first cut.** Its plan landed earlier the same day, all eight of its decisions
were taken the same day, and E1 — the free half of `pnk ask` — is built.

**What the command is for.** `pnk search` answers *what is in the KB about this*. `pnk ask` answers
*what it would take to answer this*: the same pipeline, the same filters, the same cited passages,
plus the size of the job. One synthesis call when retrieval came back confident; decomposition into
subquestions and a search for each when it did not; and, on a KB with no fitted
`[retrieval.confidence]`, **nothing can tell** — with the one sentence that would fix it. That last
case is not an edge case: it is **every KB the template stamps**, because thresholds fitted on
someone else's corpus are not a calibration, so the block ships commented out. The decision taken
for it (D-22) was to run anyway, bounded by the spending caps rather than by the signal, and to say
which bound would end a run — rather than refuse the release's headline feature on the default
template.

**Every run says that no answer was synthesised.** Nothing free can synthesise one, and someone
typing `ask` expects an answer — so the line that says *this is evidence, not a conclusion* is not
decoration, it is the difference between an honest retrieval surface and one that invites a reader
to mistake evidence for a conclusion.

**And nothing printed anywhere names `--deep`.** The paid loop is E4 and does not exist. A flag that
parses and then apologises is exactly the defect [`0.20.1`](#0201--a-tier-that-is-not-built-stops-being-accepted--20260808-0641)
fixed for `vector_tier = "sqlite-vec"` — the fix there was to refuse the *value*, not to keep
accepting it with an apology — and a flag merely advertised is the same lie one layer out. So
`--deep` is a usage error until it works. The sharpest instance was in the code this increment
replaced: `pnk search`'s escalation notice advertised `pnk ask --deep`, neither a command nor a
flag, **in the very sentence whose test is named for not naming a command that does not exist**. It
now names `pnk ask`, which you can type.

**`--json` is `pnk search`'s payload plus `answer: null` and an `escalation` block** — `branch`,
`work`, `cost_eur` (null until E2's estimator exists; a wrong number would be worse than none) and
`remedy` — so a consumer parses one schema whether or not a paid loop ever runs.

**The free-path gate covers the new command from the increment that creates it**, before any paid
module exists, and covers it by *matching its output*: no module row in `tests/test_paid_path.py`
could tell that call from `pnk search`'s, so a row would have stayed green with the call deleted.
A test asserting no ledger is written after `pnk ask` cannot fail today and says so in its own
docstring — it is a tripwire for E4, which adds a paid loop to this same command through the same
`_retrieve`.

Also in this release: the deep-release plan itself with its eight decisions, `tools/release_order_gate.py`
(five ordered sequences, gated in `check.sh` and CI), and two STATUS corrections about a wedged CI
run.

**No `schema_version` bump, no rebuild, no paid code, no new dependency, and no allowlist entry** —
E1 adds none. *The deep release, interim cut (D-9): the name stays in the unbuilt-work table until
E7.*

## 0.24.0 — `pnk ask --deep` answers · 20260811 22:24

**The deep release's second cut, and the thing it is named for.** E4 — the loop — is built, and
E2's estimator and E3's paid client, on `main` and unreleased since earlier the same day, ship with
it. Neither could be released alone: a module nothing can reach carries no user-visible change.

**Confidence sizes the work; it does not authorise it** (D-28). Typing `--deep` *is* the decision to
spend, so the flag always answers — what the signal changes is the price. A `high` or `medium`
question takes the cheap branch, one synthesis call over the passages the free retrieval already
found. A `low` one takes the loop: decompose the question against what earlier rounds established,
search for each subproblem, answer from the merged evidence, re-fold the memory to a fixed budget,
and ask §4.2 whether that is now enough — stopping the moment it is.

**An uncalibrated KB runs the same loop with no early stop, and says so** (D-22 option E). The step
that would end it early is the signal it does not have — and no KB stamped from the template has
one, because thresholds fitted on someone else's corpus are not a calibration. So the run is bounded
by `[deep] max_rounds` and by the caps instead, the output names which of them ended it, and the
honest cost of not calibrating is stated rather than hidden: the same question, answered, for up to
six calls instead of one.

**Every bound is checked before the first call.** The whole operation is priced, refused against all
three `[budget]` windows *at once* with the exact manifest edit that would admit it, and
`confirm_above_eur` is put once — it defaults to `0.01`, so every `--deep` run prompts and `--yes`
is how cron answers. Then each call is reserved and reconciled individually against the response's
own usage. A halt mid-loop honours `[budget] on_exceed` (D-23 option A): `partial` returns what the
completed rounds established, labelled; `abort` returns nothing and still leaves the ledger correct.
A paid run that produced no answer **exits 1** — the money is accounted for, but a command asked a
question and answered none must not report success to a script.

**The default caps rise, and that is the part an existing KB will feel** (D-30). At the shipped
widths a three-round loop reserves €1.6872 worst case and even a *one*-round loop reserves €0.5624,
so the old `per_operation_eur = 0.30` refused the release's headline feature on every KB the
template stamps — D-22 option A's outcome, explicitly rejected, arriving through the caps instead of
through the signal. `per_operation_eur` is now `2.00` and `daily_eur` `6.00`; raising the first
alone would have done nothing, because all three windows are checked before every call and nothing
warns that a lower one binds. The `notes` template is **1.2**. **A default reaches new KBs only**:
an existing KB stamped its own caps, keeps them, and meets a refusal that carries the number, the
key and the value — `pnk upgrade` reports the change and will not apply it, because the manifest is
the user's.

**`[deep]` arrives with two keys** (D-29), `model` and `max_rounds`, settable but deliberately
**unstamped** — an unknown key is a hard error, so a manifest carrying `[deep]` cannot be read at
all by an older Pinakes. The template ships the section commented out with its defaults written in.

**Two money defects were found on the way, and both were in code that predates E4.** A
`KeyboardInterrupt` while a request is in flight **voided** the reservation — EUR 0 recorded for a
call the server may well have billed — because `KeyboardInterrupt` is not an `Exception` and fell
past every handler into the ledger's `finally`, whose default is to void an unclosed call. The paid
PDF extractor had the same hole, and worse, since I7b. Separately, anything raising between a
response arriving and its reconciliation being written voided too; that gap is the only place
`response_received()` is not inert, and nothing reached it. Both are fixed in both clients, both
have tests that fail against the old code, and the first was found by working an exit criterion
nobody had tested.

**And a gate for documentation that quotes command output.** E1 rewrote `pnk search`'s escalation
notice and left `GUIDE.md` showing the sentence it had replaced; E4 rewrote the same sentence and
left the same block stale again. A fenced block showing an older build's output is correct Markdown
with working links, so no existing check could see it. `tests/test_docs_quote_the_shipped_sentences.py`
holds a retirement list — a sentence this build can no longer print must appear nowhere in `docs/`,
`README.md` or `src/`.

**No `schema_version` bump and no rebuild.** **Interim MINOR: the release name stays in the
unbuilt-work table** (D-9) — E5's transcript, E6's measurement run and E7's printed suggestions are
still to come.

## 0.25.0 — a paid run leaves a record of what it was asked · 20260812 05:31

**The ledger stores no query text, and that is deliberate** (DESIGN § 5). It is also why, until this
release, nothing on disk could say what a `pnk budget` row was *for*: the row has a cost, a call
count and an `operation_id`, and no question. A cron run's `--json` answered that and then vanished
when the pipe closed.

E5 adds the second file. `.pinakes/deep/<operation_id>.json` is written by every `pnk ask --deep`
that returns, named in the output and in `--json`, and holds the question, the filters as the user
typed them, the confidence reading that chose the branch, the prompt and schema versions that
produced the prose, and the answer with its citations. **The ledger's rule is unchanged** — this is
a second file beside it, not a wider ledger, and INVARIANTS says so in its own row.

**Filed under the `operation_id` the ledger groups its calls by**, so a row and its transcript meet
without searching, and the name is validated as a ULID: `Accountant` mints one, but it is also a
*parameter*, and a caller-supplied path component must never name a directory above `.pinakes/deep/`.

**The answer object is the one `--json` prints, from one renderer.** Two copies would have been two
shapes free to drift while both stayed valid JSON. `--json` gained `answer.call_ids` — the ledger's
join key — and a top-level `transcript` path with it.

**Protected exactly as a paid cache entry is, and removed by one thing.** Nothing sweeps it,
`--rebuild` leaves it, and `pnk sync --clear-cache` — bare or `=paid` — clears the extraction cache
whole and does not touch it. `--clear-cache=transcripts` is the target that removes it, and it names
a **store** rather than a third authorisation: the two existing values both clear the whole cache
and differ only in what they permit, so layering a third onto that axis would have meant
`=transcripts` also emptying the cache — destroying more than the flag names. INVARIANTS'
disposability row now names three protected things rather than two.

**Written for a run that *returned*, answer or not.** A run that decomposed into nothing made its
calls and produced no prose, and that is the case a record is worth most in: nothing on screen
explains the row. A refusal, a decline and an `on_exceed = "abort"` halt write none — `abort`'s whole
meaning is that the rounds already paid for are discarded (D-23), and a file holding what it
discarded would hand back what the setting withholds.

**Two things the review passes found are worth carrying forward.** A test claimed the temp file was
`.tmp` rather than `.json` and proved it by *planting* a `.tmp` file — which proves the glob ignores
`.tmp` files and nothing about what the writer names its temporaries; it kept passing under the
mutation. And a `git checkout <file>` used to undo a mutation reverted a real, uncommitted edit with
it — twice, the second time while proving a gate row discriminates. Both are in
[RETROSPECTIVES.md](RETROSPECTIVES.md).

**No `schema_version` bump and no rebuild.** **Interim MINOR: the release name stays in the
unbuilt-work table** (D-9) — E6's measurement run and E7's printed suggestions are still to come.

---

## 0.25.1 — `pnk ask --deep` works against the live API · 20260821 07:17

**It never had.** E4 shipped the loop, E5 the transcript, and every test of both was green — but
`answer_schema` emitted `{"type": "integer", "minimum": 1, "maximum": passages}` and
`subproblems_schema` emitted an array `maxItems`, and structured outputs accepts neither. The API
returned `400` on every `--deep` call from 0.22.0 through 0.25.0. It cost users nothing: the refusal
arrives **before** the request bills, and the accountant reserved, refused and voided each time,
which is the one part of this story that worked exactly as written.

**E6's measurement run found it on the first real call it made** — the increment whose whole purpose
is to spend real money and compare the result against what the fixtures claim. That is the case
[MEASUREMENT-RUN.md](MEASUREMENT-RUN.md) closes with, arriving on schedule: *a finding that
contradicts the fixtures outranks the release schedule.*

**The citation bound is kept, not dropped.** E4 specified it in two halves on purpose — the schema
asks for `1..passages`, `parse_answer` checks it again where the value is read — and the API refuses
the form the schema half was written in. `enum: [1..passages]` is accepted and honoured, and states
exactly what `minimum`/`maximum` stated, so both halves survive intact. Under a parser-only bound a
stray citation would be a `SchemaFailureError` on a call that had already billed; here it stays
unreachable. The subproblem cap had no such escape — structured outputs has no supported
array-length keyword — so it now lives in the prompt body and `parse_subproblems`. It never was
anywhere else: the API rejected that schema outright, so `maxItems` was never enforcing anything.

**Why four releases of green tests missed it, which is the part worth keeping.** Every test drives
the loop from recorded fixtures through the `Transport` seam — a good seam, and the reason the whole
loop can be tested with `anthropic` absent. What it also guarantees is that **no test has ever sent
a schema to the API**, and the schema is the one field the API validates and a fixture cannot
exercise. A seam introduced for testability defines a region the tests cannot reach, and that region
needs its own gate. This one is a recursive shape assertion over both builders against the keywords
structured outputs documents as unsupported: no key, no network, no fixture, and it would have
failed at E4 on the branch that introduced the defect.

Verified against the live API on both branches before release — one synthesis call, and a six-call
loop run exercising decompose, sub-answer and synthesis — so both schemas are proven by a real
request rather than by a recorded one.

**`SCHEMA_VERSION` is 2. No `schema_version` bump and no rebuild** — that constant names the deep
response shape, not the index's, and is recorded into the transcript rather than validated against.
**PATCH: the release name stays in the unbuilt-work table** (D-9) — E6 and E7 are still to come.

## 0.25.2 — the guidance carries its own lessons · 20260821 14:47

**Documentation only — no code path changed.** Six failure classes in `docs/RETROSPECTIVES.md`
recurred after being written down; the guidance that runs now carries them where the work happens.
`docs/BUILDING.md` gains the mutation-harness discipline (commit before mutating — `git checkout`
restores to the last commit and has silently reverted uncommitted fixes six times — every anchor
asserted to match exactly once, `__pycache__` cleared between mutants, no `-x`, and one
known-catchable kill before a run's silence means anything), the gate-exit-status rule, the
CI-matrix leg check, and two rules for reading a plan. RETROSPECTIVES' own § *Start here* gains
four rows — mutation passes, measurement tools, test seams, review fixes — so the two thirds of
the file written since 20260801 is reachable from its entry point again. `CLAUDE.md` § *Changing
retrieval* names which corpus can license a change (`tests/demo-kb`'s improvable pool cannot clear
p < 0.05 even on a perfect sweep), and its live-plan block slims to pointers — the deep plan's E6
status now lives in the plan itself, and `docs/README.md`'s routing rows carry what the block
dropped. `plans/` gains a proposal for a committed mutation harness, `tools/mutate.py` — the
`land.py` precedent applied to the second class of failure that reports success.

**PATCH: documentation and one docstring. The only wheel diff is the `__version__` string; the changed docstring is in `tools/`, outside the wheel.**

## 0.25.3 — the deep loop is measured · 20260821 22:34

**E6, the only increment that spends real money, is built.** Steps (a)–(e) of
[MEASUREMENT-RUN.md](https://github.com/lucagattoni/pinakes/blob/main/docs/MEASUREMENT-RUN.md), refusal probe included, against
`claude-opus-5` on synthetic corpora, for **€0.2131** of a €5.1836 worst case.

| Branch | Runs | Calls | Reserved | Spent | Over-reservation |
|---|---|---|---|---|---|
| `synthesis` — the common case | 5 | 5 | €1.0500 | €0.0353 | **29.75×** |
| `decomposition` — calibrated loop | 2 | 6 | €2.7600 | €0.0542 | **50.92×** |
| `unknown` — uncalibrated loop | 2 | 11 | €2.7600 | €0.1235 | **22.35×** |

Every constant in `deep/estimate.py` now carries its measurement and the command that produced it
— 3.99×, 2.51×, 8.93×, 1.50×, 2.48× on the five input constants and **12.12× on `MAX_TOKENS`**,
which carries most of the whole-run ratio because output bills at five times input and is two
thirds of a round's price. **None was lowered**: the corpus is synthetic, which is E6's own exit
criterion and `PAGE_TOKEN_CEILING`'s binding precedent.

**The better-calibrated branch is the more over-reserved one**, which is the signal working rather
than a defect: a reservation must cover `max_rounds`, and calibration is exactly what lets a run
stop before reaching them. A single blended figure would have hidden it — the argument D-28 made
before any of this was measured.

**Six defects in the instrument that publishes the numbers**, which had no tests at all and whose
`--json` had never once run. The sharpest: a ledger call left *unresolved* was priced at its
**reservation** and printed under a header claiming `reconciled ledger spend`, so deleting one
reconciliation line moved the published synthesis figure from 29.75× to 4.40×, silently, at exit 0
— while `pnk budget` on the identical ledger warns loudly about exactly that money. It now reports
how each call settled and marks a branch it cannot vouch for. `tools/deep_reservation.py` has 27
tests, **mutation-verified 10/10**.

**Two defects in the runbook**, both caught by the free pre-flight it prescribes one paragraph
earlier: step (c)'s third `no-answer` question scores `medium` and buys the *cheap* branch while
being recorded as a loop measurement, and its stated reason — that a `no-answer` question cannot
stop early — is false, since both calibrated runs stopped at sufficiency. **And an earlier partial
run's 19.0× and 16.5× are withdrawn**, not corrected: their KBs were reaped from `/tmp`, so nothing
on disk ever supported them.

**No `schema_version` bump, no rebuild, and no product behaviour changed** — `tools/` ships in no
wheel. **Interim PATCH: the release name stays in the unbuilt-work table** (D-9) — E7, printed
suggestions, is the only increment left.

## 0.25.4 — what the mutation battery cannot reach · 20260821 22:49

**Documentation only.** `docs/BUILDING.md` § 4 now names the limit of its own mutation step — a
defect with no assertion anywhere — with 0.25.3's worked case: a `textwrap` reflow of a comment
run flattened a `\`-continued shell command onto one line, legal to `ruff`, invisible to
`pyright`, read as prose by a diff review (`4d5debf`, caught by the E6-close adversarial pass
before the tag). The rule it leaves: a prose tool's output over text carrying load-bearing
whitespace is re-read as the thing it is — a command, a table, an indent — never as prose. The
same landing files the lesson as a retrospective entry, and moves 0.25.3's own section on this
page out of Part 5, where its sweep's `startswith("## ")` scan had placed it — a prefix match
steps over every `# `, so the Part 5 boundary was invisible to it. The "complete, correct, and in
the wrong place" class, one release after it was written into the release procedure — and this
time with its mechanism identified from the script rather than guessed.

**PATCH: docs and fragments only; the wheel diff is the `__version__` string.**

## 0.26.0 — a paid run tells you what it learned about your KB · 20260822 01:32

**The deep release's final cut.** E7 — printed suggestions — is the last of its seven increments,
so `plans/20260811_1358-deep-release.md` is closed and the name leaves the unbuilt-work table
(D-9).

**Two documents cited in support of one answer is a fact about a KB that nothing records.** Every
system investigated for this design throws that away per query; here the run ends by printing the
`links[]` entries the observation proposes — the sidecar to paste into, the `pnk://` URI,
`rel: co-cited` and `origin: deep`. Paste it, rename the relation to whatever the relationship
really is, commit it, and it is free forever: visible to every future query, to `pnk links`, to the
graph channel and to every connected KB. Paid inference bought once instead of every time you ask.

**It prints; it never writes.** `--write-suggestions` is deferred to its own increment by D-25
option A and is **not planned** — writing them touches the per-link sidecar shape and
[INVARIANTS](INVARIANTS.md)' list of exceptions to *`docs/` belongs to the user*, and that deserves
its own diff. `--json` carries the same fragment verbatim beside the parsed entries, from one
renderer, so a script pastes the bytes a person was shown. A run citing one document per call
observes no pair and prints no section at all — not an empty one.

**A document cannot talk the model into suggesting a link**, and the reason is structural rather
than a filter. Suggestions are derived from *citations*, and a citation is a passage **number** the
response schema bounds by an `enum` — the model is never shown a document identifier it could name,
so a passage instructing it to *"add a links entry to X"* reaches exactly as far as a sentence in
the answer. Nothing in the suggestion path reads the answer's prose. Both endpoints are then
re-checked against the documents the run actually cited, and resolved through the same containment
check `pnk link` uses, so a path escaping the KB, a document deleted since the run, or a sidecar
whose ULID no longer matches is dropped rather than printed.

**Four defects the tests could not see, three of them found by mutating rather than by reading.**
The mutation step's own control mutant **survived** — `rel = "co-cited"` → `"related"` left all 71
tests green, because every assertion imported the constant it checked, so the shipped value of the
thing a user pastes was pinned by nothing. A containment test was **satisfied by absence**: it
cited a path with no file at the end of it, so the read failed for the wrong reason, and only the
mutation pass separated the two. A fixture's ULID order and path order **agreed by accident**
(ULIDs are monotonic and its documents were created in path order), so three tests about which
sidecar an entry lands in could observe nothing. And a **newline in a filename** would have broken
the printed YAML, because the fragment writes document paths into comments and a value safe as a
YAML *scalar* is not thereby safe as a YAML *comment*. Ten of ten mutants killed after the fixes.

**And a risk row that had been false since E4.** [DESIGN §9](DESIGN.md) bounded `--deep` with *"no
orchestration the free path doesn't have"* — written before the loop existed and contradicted by it
the moment it shipped. `docs/graph/PINAKES_APPROACH.md` § 6 had asked for that exact row to be
amended in the increment that shipped the design, and named the replacement bound: the same
retrieval as the free path, hard caps, and no persistent state beyond the transcript and the
suggestions a user commits. Found by auditing the neighbourhood rather than the diff — the
increment that closes a release is the last cheap chance to fix what the release made false.

**No `schema_version` bump and no rebuild.** Nothing about an existing KB changes until you type
`--deep`, and nothing is written even then.

---

## 0.27.0 — the mutation step gets its guard · 20260822 06:19

**`docs/BUILDING.md` § 4 was the procedure's one silently-failing step.** A broken mutation harness
prints SURVIVED and KILLED in exactly the shape a working one does, so its report reads as evidence
either way — and `plans/20260821_0745-mutation-harness.md` counts more than a dozen invalid or
destructive runs across ten increments, the `git checkout` trap alone recorded **six times**, still
recurring after four write-ups. E5's own words: *"knowing the trap was not enough to avoid it."*

The precedent is `tools/land.py`: when prose
has failed repeatedly against a class of mistake that fails *silently*, the rule stops being a rule
and becomes a tool. `tools/mutate.py` takes a TOML battery of `[[mutant]]` rows — `file`, `old`,
`new`, `kills` — and turns every written rule into a refusal: the target must be **tracked** by git
and match `HEAD`; the anchor must occur **exactly once**, checked across the whole battery before
the first write; `__pycache__` is cleared after the write *and* after the restore; pytest never sees
`-x`; an invalid mutant is its own outcome rather than a kill; the restore happens in a `finally`
and its bytes are verified; and **a batch where nothing died exits non-zero**, because a run with no
kills is a broken harness and not a clean bill.

**Five ways a run can lie that the written rules did not cover**, each measured while building it,
each the harness reporting confidently on a question it never asked. A **skipped** test exits 0 —
byte for byte the SURVIVED signal — and Pinakes skips on a missing extra as a matter of course, so a
battery aimed at a `pdf`, `paid` or `model` selector in a `[light]` checkout would have reported
every mutant unpinned. An **already-red** selector reports KILLED for every mutant aimed at it,
including the ones nothing catches; both are caught by one pre-flight run per selector, before any
file is touched. **`SIGTERM`, `SIGHUP` and `SIGQUIT`** end a process without unwinding, so a
`try/finally` restore is not a restore — `SIGINT` already raises, which is why the hazard is
invisible to anyone who only tests with Ctrl-C. **`PYTEST_ADDOPTS`** is inherited, so `-x` in the
operator's shell narrows a two-test kill to one. **`PYTHONPYCACHEPREFIX`** moves every `.pyc` into a
mirrored tree the clearing cannot reach, and is refused rather than guessed at.

**The T3 trap was reproduced before it was fixed, and that is what made its test honest.** A
same-length mutant (`min` → `max`) written in the same wall-clock second as the previous compile
passes every test 6 times out of 6, because CPython validates a `.pyc` on
`(mtime-to-the-second, size)`. The obvious test — assert the same-length mutant is KILLED end to
end — goes green on a slow machine with the invalidation deleted, because the second boundary is
crossed anyway. Two tests replace it: one asserts no bytecode cache **exists** during a mutation,
which has no clock in it at all; the other forges the stale condition with `os.utime` and watches
the mutant vanish.

**pytest's `<error>` tag covers two opposite events.** A *collection* error is the invalid mutant —
nothing ran. A *setup or teardown* error is a real node the mutant broke on the way in or out, and
in this repository fixtures build indexes, manifests and KBs out of `src/`, so fixture-mediated
detection is the common shape. Treating both alike reported a mutant that tripped a fixture *and*
failed a plain assertion as *"the mutant did not run"*, tallied `0 killed`. They are told apart
structurally now — a collection failure carries no `line` attribute — rather than by matching
pytest's message text. **The reviewer who found it also proposed routing setup errors into KILLED,
and an independent skeptic rejected that remedy while confirming the defect**: no assertion fired,
so nobody may write *"pinned by test X"*, and the fix would have manufactured the false green the
tool exists to prevent.

**Verified the only way it could be: run against its own guards.** 25 mutants, each disarming one
refusal, **25 killed**, each by the test named beside it — and three separate rounds of that found
four clauses no battery-driven test could reach, every one surfacing as a SURVIVED row rather than
a failure. Twice, the thing that was stale was the *battery's own selector* rather than the code: a
SURVIVED row is a claim about a **pair**, and either half can be wrong.

**A developer tool.** It ships in no wheel and changes nothing for any KB — no code path, no
`schema_version`, no rebuild. What it does not do stays manual and is refused rather than
approximated: cross-file mutants, generated operators, and mutating a test file, where a mutant in
the file its own selector runs can make that test vacuous.

## 0.27.1 — the gates read what they were cited for · 20260822 07:04

**A document naming a tool as the authority for something is a claim about that tool's coverage —
and it is exactly the kind of claim written once and never re-read.** `docs/RELEASING.md`'s sweep
table names five places a release stales. One is STATUS's *Published on PyPI* prose. Its *where the
new entry goes* row answers: `python3 tools/release_order_gate.py` decides it. No pattern in that
gate matched the list, so the procedure delegated a placement decision to a check that could not
read the document, and the green line `5 sequences in release order` was read as covering a list it
had never opened. It drifted, as delegated-to-nobody things do: `0.25.1 → 0.25.3 → 0.25.2 →
0.25.4`, wrong on SemVer **and** on verification time, surviving every green run from 20260821.

**The sixth sequence carries two rules the obvious version would have got wrong.** Its own count
floor, because the list begins at 0.16.0 and the shared floor of 25 would fail it for being *short*
rather than for being *unread*. And permission to **lag** the other five — an entry here is written
from evidence, held back until the claim has been verified *from* the index, so between a release
landing and its verification the list is legitimately one entry short. Demanding agreement would
turn an intended, documented window red, and a gate people switch off during a documented window is
not a gate. But the exemption is a **direction, not a hole**: the list may lag every other sequence
and may never lead one, because a verification paragraph for a release the CHANGELOG has never
heard of is a claim about the index that nothing else records. The first draft had the exemption
and no direction, and no input could tell a working exemption from a missing one.

**What the exemption costs is written in the gate.** Because a missing newest entry is legal, an
entry written in a shape the pattern does not match is indistinguishable from one not yet written —
silently unchecked rather than reported. The floor catches wholesale pattern rot; it does not catch
a single mis-shaped newest entry. Undocumented limits get trusted past.

**And a second gate, in the same family.** `tools/fragments.py` has always taken a fragment's
category from its **filename**, so a `---` / `category: added` / `---` fence inside a fragment was
inert and nothing objected to it — while `--apply` spliced it into the target verbatim, because a
body is copied unchanged by design. Three fragments written for 0.24.0 carried one, and all three
fences are still published in `CHANGELOG.md`. Only the *opening* fence is refused: a `---` further
down a body is a legitimate horizontal rule, and a check written as `"---" in body` would look
correct and be wrong.

**Not fixed here**, and both proposals rather than edits: the three fences already published in
`CHANGELOG.md`, and `docs/STATUS.md`'s claim that no workflow has ever contained a release-creating
step, which sits eleven lines above its own correction.

**No code path changed** — no `schema_version`, no rebuild, and nothing about any existing KB.

## 0.27.2 — the install is a region no test reached · 20260822 10:01

**`pnk serve` had never worked on a fresh install, in any published version.** `pyproject.toml`
pinned `mcp>=1.28` with no ceiling. mcp 2.0.0 removed `mcp.server.fastmcp` and reached PyPI at
13:45Z on 20260728 — **three and a half hours before Pinakes published its own first version** at
17:16Z. Every one of the 38 releases on the index has shipped a command that exits with an
unhandled `ModuleNotFoundError` and no remedy.

**Nothing in this repository could see it, and the reasons are worth naming separately.**
`tests/test_serve.py` has 31 tests and they were all green — against `uv.lock`'s pinned mcp 1.28.1.
All 37 CI invocations are `--frozen`, so CI has never resolved this dependency. The one job that
*does* resolve fresh, `build`, exercised `pnk --version`, `pnk init` and two data files, and never
imported the module. `pnk doctor` has 18 checks and no MCP check, so it exits 0 on a broken
install. Every instrument was working and every one was pointed somewhere else.

**It was not found by a test, a gate or a review.** It was found by installing the product to
answer the question *what should we build next*. `docs/BUILDING.md` warns that a test seam defines
a region no test reaches; here **the region no test reached was the install itself.**

**The cap is the small half.** `mcp>=1.28,<2` stops the bleeding and buys the port its own
increment. What closes the class is `tools/wheel_import_gate.py`: it installs the built wheel into
an isolated environment, discovers the installed package's modules from the filesystem and imports
**all 57** — so a module added later is covered without anyone remembering the step exists, which
is precisely what did not happen for `pinakes.serve`. It refuses four ways a walk can report a pass
it did not earn: run against a source tree, walked nothing, a stale allowance, or an allowance
excusing the wrong module. `pkgutil.walk_packages` was rejected because its `onerror` default
swallows an import failure, so one broken `__init__.py` would hide everything beneath it.

**It runs in front of `uv publish`, and that placement is the argument.** A dependency's major
arrives with **no commit in this repository**: `ci.yml` runs on push and pull_request, so `main`
can be green on Monday, the break can publish on Wednesday, and a tag on Thursday would carry it to
an index that never takes a version back. In front of the publish step a failure costs a deleted
tag and nothing else.

**Two siblings were measured and deliberately not capped.** `anthropic` resolves fresh to 1.0.0 and
`sentence-transformers` to 6.0.0; both were checked at the level that matters — not just
constructors but the response-model fields, because `extract/claude.py` consumes
`response.model_dump()` as a dict and a renamed `Usage` field would compute a cost of **0**,
disabling the spending guard with no exception. Both are compatible. **The remedy for the class is
testing the resolve, not capping on reflex** — a ceiling on `[st]`, the default backend, would
change the install contract for every user to prevent a break that does not exist.

**Three adversarial rounds, and the pattern is the finding: each round's defects were in the
previous round's remedies.** The allowance was keyed on the library, so `--allow-missing pypdfium2`
would have excused `pinakes.serve`; it is `MODULE:LIBRARY` now. The *"can still fail"* step was
satisfiable by an environment where `--with` installed nothing, because both branches printed the
same headline — it greps the specific failure now. `exit 1` → `exit 0` survived in five places, one
of them in front of `uv publish`. `make smoke` exited **0 while printing a traceback**, because
`pnk serve | grep -q` returns grep's status. 47 mutants, 0 survivors.

**What the leg still cannot see, stated so it is not trusted past:** import-time breaks only, on
the install states CI runs. A dependency that keeps its module layout and changes a signature
passes everything here. `[st]` is resolved fresh by nothing, because torch is ~2 GB. And `ci.yml`
runs on push and pull_request, so a third party's release is caught at the next push or tag rather
than when it happens.

## 0.28.0 — the port was four lines, the gate was not · 20260823 01:38

**`pnk serve` runs on `mcp` 2.x.** `serve.py` moves from `mcp.server.fastmcp.FastMCP` — removed
outright in 2.0.0, which is what left the command dead on every fresh install up to 0.27.1 — to its
successor `mcp.server.mcpserver.MCPServer`, and the requirement moves from `mcp>=1.28,<2` to
`mcp>=2`. The cap was 0.27.2's outage fix and was always going to be lifted by the increment that
ported the code. Nothing replaces it: a cap is a guess about a release nobody has seen, and what
catches a dependency's next major is resolving fresh and running the thing.

**The four `pinakes_*` tool schemas are byte-identical across the move** — captured from a live
session on each library and diffed before anything landed, then committed at
`tools/mcp_tool_schemas.json` — so no client sees a different tool. The one wire difference is
`serverInfo.version`: `FastMCP` took no `version=` and filled the field with the **`mcp` library's**
own version, so every release up to 0.27.2 told a client asking which Pinakes it was talking to that
it was `1.28.1`.

**The port was four lines. The gate it broke was the increment.** The handshake in both workflows
was three JSON-RPC lines written into `pnk serve` with stdin closed immediately. `mcp` 1.28.1
drained that queue before shutting down; 2.0.0 does not, and the flake is not about the protocol —
ten runs at each version the library accepts answered `tools/list` 5/10, 1/10, 2/10 and 1/10. Both
workflows would have gone red four runs in five on a server that works, and `make smoke` — the
pre-tag check a maintainer actually runs, and the third copy nobody looked at — was red on **every**
run. That handshake had been written the same morning, in 0.27.2, *to catch the `mcp` outage*, against
the behaviour of the version it was about to lose.

`tools/mcp_handshake_gate.py` drives `mcp`'s own client, which holds the session open until it has
its answers, and checks two things the piped version could not: that `serverInfo.version` is what
the built **wheel's filename** says, and that the tools listed match the committed snapshot exactly.
Against a fresh resolve that snapshot is what turns a future `mcp` reshaping the published contract
into a red run rather than a silent change to every client's view.

**Two adversarial rounds, 24 findings between them, every one of them in the remedies rather than
the port.** Round one found a landmine in the release's own path: the version test compared against
`importlib.metadata.version("pinakes")`, reaching for an independence that does not exist inside a
checkout — `[tool.hatch.version]` reads the same file and `uv run` does not refresh dist-info — so
bumping `__version__` to cut this release would have reddened two tests, blaming the defect the
increment had just fixed. Round two found the first round's own fixes applied to some call sites and
not all: comment-stripping added to `release.yml`'s pins and not the Makefile's, the positive
exit-status rule applied to both workflows and not to `make smoke`. 29 mutants, 0 survivors.

## 0.28.1 — a gate audited against itself · 20260823 02:06

**A gate that reads a constant out of the document it polices can be made to elect its own answer**,
and `tools/release_order_gate.py` did it four times. Three were found by review and one by an
adversarial audit pointed at a single question: *for every constant this gate uses, where does its
value come from?*

**The lagging ceiling.** A sequence allowed to lag is required to be complete only up to its own
newest entry — and that ceiling was `max(versions)`, the sequence's own contents. Deleting its
newest paragraph dropped the ceiling with it and the deletion hid itself: the same defect refused at
the *lower* bound, surviving four lines away at the upper one. `MAX_VERIFICATION_LAG = 2` is
declared, and the number is not a tuning knob: *verify the artifact, never the run status* is the
rule that list exists to record, so two behind is one unverified cut plus one slip, and three means
verification has stopped happening. **What it buys, exactly:** not detection of a deletion, but a
bound on how far the echo can drift — at a legitimate lag of 1, one deletion is still silent. The
failure names both causes and picks neither, because the documents cannot tell a deleted entry from
an unwritten one.

**The Part ranges.** These are read out of the `# Part N` headings, which is *why* the mapping
cannot drift from the document — so they cannot be declared without reintroducing the drift the
check exists to catch. Appending ``— `0.8.0` onward`` to `# Part 5 · What is not built` therefore
made a release section filed under it "correctly placed": twenty characters, exit 0, and the only
trace was a passing report line changing `holding no releases: Part 5` to `none`. The echo stays;
the freedom is removed. **Two Parts may not claim the same version, and the Parts must ascend** —
`# Part 4` declaring `` `0.8.0` onward `` is now what stops `# Part 5` doing so. Not theoretical:
Part 4's heading once claimed `0.8.0` → `0.10.0` while holding everything through `0.22.1`, and was
fixed by widening the heading.

**The Part floor** sat at four against a real count of five, so demoting `# Part 5` to `## Part 5`
passed it *exactly* while handing every section beneath to Part 4, whose range holds everything. A
floor one below the truth is a floor with a bypass.

**The ladder this leaves**, and it is the release's one transferable sentence: **declare** a
constant rather than deriving it; **bound** it when it must be derived; **constrain** it when it
must be read from the thing it polices; **delete the field** when none of those can keep it honest.

**No code path changed** — no `schema_version`, no rebuild, and nothing about any existing KB.

## 0.28.2 — the Guide's commands were re-run against the build that ships them · 20260823 02:47

**`docs/GUIDE.md` opened with *"Every command here was run against 0.2.0 (20260728 16:40); the
output shown is real."*** It was published on the site, it was the sentence a reader uses to decide
whether to trust the other eight hundred lines, and it had been wrong for **twenty-six releases** —
the whole of this project's life bar four days.

**Nine output blocks had drifted behind it**, and the two most misleading were the ones a reader
would act on:

| block | said | says |
|---|---|---|
| `pnk templates` | `notes  1.1` | `notes  1.2` |
| `pnk init` (both) | `from notes@1.1` | `from notes@1.2` |
| the `You get:` tree | three entries | plus the `README.md` and `eval/questions.yaml` `init` really writes |
| `pnk ask -k 2` | `€0.26` | `€0.20` |
| `pnk ask`, uncalibrated | `€1.69` | `€1.33` |
| the budget refusal | `€1.69`, `decomposition` branch | `€1.38`, `unknown` branch, and the closing line it had dropped |
| `pnk upgrade` caps | `0.05 → 0.30` | `0.30 → 2.00`, plus `daily_eur: not set → 6.00` |
| `cannot compare` | ships `notes@1.1` | ships `notes@1.1, notes@1.2` |

**The two estimates went stale in a single release and stayed wrong for exactly that long.**
`deep/estimate.py` was re-measured against the live API in
[`0.25.3`](#0253--the-deep-loop-is-measured--20260821-2234) and has not changed since, so the guide's
figures were correct when written and falsified by one commit four weeks later.

**Four prose claims went with them, and the worst was repeated three times: that only one surface
in Pinakes can spend money.** `pnk ask --deep` has been the second since
[`0.24.0`](#0240--pnk-ask---deep-answers--20260811-2224). The Guide asserted it under *Watching what
it costs* and again in *Troubleshooting*, and described `per_operation_eur` as bounding one
`pnk sync` when it bounds one whole **command**, a deep run's every round included.
`docs/CLI.md` already said *"the second of two that can spend"* — **the neighbourhood is what made
the Guide's version findable**, which is the argument for auditing it rather than the diff.

**And the neighbourhood carried the same class of defect.** `docs/CLI.md` said *"Today `cannot
compare` is what every KB in existence gets"* — true when written, false since
[`0.17.0`](#0170--a-template-version-that-means-something--20260807-2055) archived `notes@1.1` — plus
three stale `notes@1.1` example outputs. Fixed in the same change, with the release attribution
checked by `git describe --contains` rather than assumed.

**Two blocks were deliberately not re-run, and the page now says so where they appear.** The paid
`--deep` transcript would cost real money to reproduce, so it is kept, labelled a `0.24.0` run, and
the one figure that has since moved is named. Re-running the two-KB link walkthrough would change
every ULID in the section without making a single sentence truer. **The distinction is between an
output nobody re-ran and an output nobody re-ran *and did not say so*** — only the second is a
defect.

**The adversarial pass found its own error in the fix.** The first draft of that label said the paid
block's command *"is now quoted at €0.20"* — the figure measured at `-k 2`. The block passes no
`-k`, and at the default passage count it quotes **`€0.21`**. One cent, and exactly the invented
precision the label existed to prevent: two invocations collapsed into one number. Caught by
re-reading the command the block actually shows rather than the one measured beside it.

**What no gate could see.** `./check.sh` proves the release sequences agree across five documents,
`mkdocs --strict` proves every link resolves, and the template gate proves the template matches its
archive. **None of them reads a sentence claiming a command was run.** A stale document rots fastest
exactly where it was most specific — a quoted output block pins a number, a version string and a
wording at once, and any one of the three moving falsifies it, while the paragraphs around it stay
true.

**No code path changed** — no `schema_version`, no rebuild, and nothing about any existing KB.

## 0.28.3 — a gate that could not see the list next door · 20260823 03:10

**`docs/STATUS.md` carries the published-version history twice** — as *Published on PyPI* prose, one
paragraph per release, and as a *Published versions* row enumerating every version in a single table
cell. They record the same event. `tools/release_order_gate.py` read the first and could not reach
the second, and the row **fell four releases behind — 0.27.0, 0.27.2, 0.28.0, 0.28.1 — through green
runs of every gate in this repository**, after being repaired once for exactly this on 20260822.

**The arrangement is the most misleading one available.** The check and the list it cannot see sit
in the same file, under the same heading, forty lines apart. So the gate reported each of those
releases present — and each *was* present, in the sequence next door. Nothing was lying; the
question was never asked.

**Reaching it needed a mechanism the other six did not.** Every other sequence is a run of lines. The
row is one line holding the whole enumeration, with about twenty more version numbers in prose after
it: a line-anchored pattern cannot get inside, and an unanchored one would sweep up the prose and
read a sorted list as unsorted. A `Sequence` may now declare a **`within`** anchor — one regex
capturing the region the pattern is then run inside. A `within` matching nothing yields an empty
sequence and trips the floor; one matching **twice** is refused outright rather than resolved to the
first, which would splice two lists into a sequence sorted only by accident.

**And the row may never lag the prose beside it — a relation where the sixth sequence had only a
bound.** `newest_may_lag` grants latency against the release documents, because an entry is written
only once the release is verified from the index. But it granted that latency against everything,
including the list recording the very same verification. Measured over every commit on `main`
carrying both lists:

| row lags `CHANGELOG` by | commits | the lag bound alone |
|---|---|---|
| 0 | 92 | green ✓ |
| 1 | 25 | **green, row wrong** |
| 2 | 4 | **green, row wrong** |
| 3+ | 10 | red |

**29 commits inside the silent window, and both recorded drifts escalated through it** rather than
starting past it. The `not_behind` relation fires at `c4b52ab` on 20260812 — **11 commits and 10
days before** the bound reaches 3 — with **0 false positives across 53** commits where it holds.

**Both are kept, and one test asserts both fire.** The bound still catches a drift where *both* lists
are forgotten together, which the relation cannot see; pinning them with a single test is what stops
the next reader deleting the one that looks redundant.

**The transferable sentence: a relation to something that must move with it beats a bound on how far
it may drift**, wherever two records describe one event. A bound asks *how wrong is this allowed to
get*; a relation asks *is this still true of its pair*, and only the second notices on the first
commit.

**Two rules from earlier releases landed on their next case here.** The floor is **not** derived from
the row it polices — but it is also not the literal 41, because `check_membership` skips a sequence
whose floor already failed, and a too-high floor would report *the pattern stopped matching* without
ever naming which release went missing. **Declared-not-derived settles where a number comes from,
not what it should be.** And the first `not_behind` guard-test fed the validator only real
constants, so it passed whether or not the refusal existed — **E7's tautology, caught by its author
before review**; the validator is now a function a test can hand a deliberately bad sequence.

**11 mutants, 11 killed.** **No code path changed** — no `schema_version`, no rebuild, and nothing
about any existing KB.

## 0.29.0 — the batteries were kept, and one caught what four green gates missed · 20260823 12:50

**73 mutants written across six increments existed only in session scratchpads.** They are now
`tools/batteries/`, one file per target, and a fourth battery covers `tools/mutate.py` itself:
**91 mutants, 91 killed, 0 survived, 0 errored** against the tree they describe.

**The prose this reverses is the tool's own.** `tools/mutate.py` shipped in 0.27.0 saying *"a
battery is a per-increment working file, not a portable artifact"*, in a paragraph whose actual
subject was where the `pytest` key lives. Nothing had measured it, and it then decided the question
for two months by being read rather than by being right —
`plans/20260821_0745-mutation-harness.md` enumerates what it deliberately left open, and persistence
is not among them. The measurement took twenty minutes: of **81 mutants**, **78 anchors still
resolved exactly once** a day to a week later, and every one that broke was one whose own code had
changed. **The three failures were refusals** — named, counted, exit 1, target untouched — so the
cost of keeping a battery is a maintenance prompt and never a false `KILLED` or `SURVIVED`. An
argument about whether a claim outlives its proof would not have resolved; *what does being wrong
cost?* did.

**And that measurement was aimed at the half that had never broken.** `docs/RETROSPECTIVES.md`
already recorded which half rots, twice in one increment: a `SURVIVED` row is a claim about a
*pair*, and it was the **selector** that went stale. The gate resolves both.

**What is committed is not the proof.** Re-deriving forty-one mutants against a gate is an
afternoon. It is the reasoning about *which mutants were worth writing* — and the durable channel
for that already existed: a per-mutant table can go in a `retro.d/` fragment, and RETROSPECTIVES has
exactly **one**, against 93 commits that speak of a mutation pass. The channel existed, worked, and
was used once.

**Two of this increment's own mutants were killed about nothing.** Both repaired anchors widened
`old` from one line to two and left `new` at the line it used to replace. One deleted a neighbouring
keyword argument as well as flipping the flag it names; the other deleted `starts_at` and duplicated
`minimum=15,` — `keyword argument repeated`, a **`SyntaxError` at import**, which arrives as an
ordinary assertion failure because this module is imported *inside* the test rather than at
collection. It read **KILLED**, in a batch reporting `0 errored`. A confident row about a question
nobody asked, produced by the tool, in its own corpus, on the first day. `mutate.py` now refuses a
Python mutant that does not compile, before the first write; `ast.parse` would not have caught it —
it accepts `f(a=1, a=2)` and `compile()` does not — so a test pins that discrimination. It earned
itself within the hour, catching two more staled by a refactor in the same session.

**A battery then caught what four green gates and two review passes missed.** Running them at the
final sha reported **17 killed, 1 SURVIVED** — exit 0, which is what `report()` does with a survivor.
The survivor's test asserted `code == 1` and nothing else, so inverting the very condition that
chooses between its two diagnostic messages left it green: a test whose entire subject is a message,
pinning only an exit status, written the same day it quoted the rule it breaks. The suite was green
and `./check.sh` was green twice. That is the demonstrated catch this mechanism needed, at n=1,
inside the increment that built it.

**What it is, said precisely.** `tests/test_batteries.py` gates that every anchor **resolves**, that
every `kills` selector names a test that exists, that no file is claimed by two batteries, and that
each battery carries the `mutants = N` it declares — 0.05s, inside `./check.sh`. It does **not** gate
that the mutants still die: nothing runs a battery automatically, and `mutate.py` exits 0 on a
survivor by design. **It is a resolvability gate, not a regression gate**, and the denominator is
stated beside it: four targets, all under `tools/`, **no module under `src/`**, no invariant covered.

**Also in this release: a cleared context settles its own role before it writes anything.** Take it
from what the *user* said in this session — never from the repo, the previous session, or the work
in flight — ask every live peer theirs, and if you cannot determine it, ask and **block**. Both
failure directions are silent and 20260823 produced both within hours.

**No code path changed** — no `schema_version`, no rebuild, and nothing about any existing KB.

## 0.29.1 — the instruction file, extracted to its own guideline · 20260823 13:59

**`CLAUDE.md` went from 274 lines to 220, and nothing was lost.** Its own hygiene rule 6 makes
crossing ~150 lines the trigger to extract sections and leave pointers; the file had crossed it by
83%. Five sections of detail moved to the page that owns them, each leaving behind a pointer that
**states the fact** a reader would otherwise open the sub-doc for, rather than merely saying a
sub-doc exists:

| Destination | What it received |
|---|---|
| [`RELEASING.md` § Landing a branch](RELEASING.md#landing-a-branch) | what `land.py` refuses, and why `--cleanup` deletes both copies of a branch |
| [`INVARIANTS.md` § The paid path's key is its own](INVARIANTS.md#the-paid-paths-key-is-its-own) | why the key rule is enforced in code rather than by machine hygiene |
| [`BUILDING.md` § Proposing a change to a document you do not own](BUILDING.md#proposing-a-change-to-a-document-you-do-not-own) | the propose-as-a-diff procedure, and why the cost is accepted |
| `DESIGN.md` § 7.3 | the corpus-power numbers — `sign_test(4, 0)` = 0.0625, and why a power limit is not a mechanism limit |

**The plan-status bullets were deleted as duplicates rather than moved.** `README.md`'s routing table
already carried them, in more depth than `CLAUDE.md` had. **`ROADMAP.md` and `STATUS.md` were not
touched by the extraction at all** — `tools/release_order_gate.py` parses five ordered sequences out
of them, and an inserted heading re-parents every release section below it.

**Every defect the review pass found was about the neighbourhood, not the content.** Four agents
wrote four destination sections; each did its own job correctly — right anchor, every fact carried,
no heading renamed. The review then found five defects, and all five were about what the surrounding
text still claimed: two provenance notes describing what their file held *before* it was extended,
a routing row describing the pre-extraction layout, a pointer aimed at `CLAUDE.md`'s now-compressed
text, and a new section duplicating a rule `README.md` already owned. **A per-file agent structurally
cannot follow *audit the neighbourhood, not the diff*, because the neighbourhood is outside its
file** — and the routing table, the page that most needed editing, had been assigned to nobody.

**The duplicate had already drifted, which is the concrete harm *one fact, one home* exists to
prevent.** `README.md` § Conventions still named **the deep release** as live unbuilt work — it left
that table at 0.26.0, its final cut, three releases earlier, while `CLAUDE.md`'s copy had been
correct all along.

**Four dead links, written while creating pointers whose entire purpose is to be followed.**
`CLAUDE.md` sits at the repository root, so a relative `](RELEASING.md#…)` resolves to
`/RELEASING.md`, which does not exist. **`mkdocs build --strict` cannot see this class**, because
`CLAUDE.md` is not part of the built site — nothing checks its outbound links. The check that found
them parses every `](path.md#anchor)` and slugs every heading in the target, and it belongs in any
future extraction.

**It stops at 220, not 150, and says so.** Everything with a genuine home elsewhere has moved;
going further would mean deleting rules the user set. Rule 6 calls the guardrail *"the trigger to
extract sections and leave pointers — not a hard cap that justifies deleting information."*
Reporting the shortfall is the outcome the rule asks for.

**No code path changed** — no `schema_version`, no rebuild, and nothing about any existing KB.

# Part 5 · What is not built

## Open corrections — one live

**It emptied for the second time at 0.22.0 (20260811) and refilled the next day, from E5.** It had
emptied once before on 20260805 22:18, refilled on 20260807 and again on 20260808. **An empty list
means nobody has run Pinakes lately, never that it is finished** — three emptyings, three refills
within days.

**The live one:** `pnk init`'s gitignore warning is the only thing keeping a KB's `.pinakes/` out of
a repository, it is printed once at creation, and E5 put the user's **verbatim question** in there.
Not a new class of exposure — an unprotected `.pinakes/` already commits `index.db`, which holds
every chunk of every document — so it is a warning to strengthen rather than a hole to close. Its
*required* text is undecided (whether `pnk doctor` carries the check, and at what level), which makes
it a decision rather than a task. Owned by
[`plans/20260731_1202-open-corrections.md`](https://github.com/lucagattoni/pinakes/blob/main/plans/20260731_1202-open-corrections.md),
which carries every one of them, closed, with what each cost to answer.

**The six arrived five different ways, and that is the useful part of the count** — described by
what they are rather than by number, since closing two renumbered the rest. Two came from
*building* 2d and neither was visible from reading the code that held it, the pattern every entry
had followed until 20260808. **The damaged-template traceback** broke it, found by T3's adversarial
*reading*. **The `same manifest` gap** was not found at all but *created*, by T4, in the increment
that closed the item standing there before it. **The eval header's `vector_tier`** came from T5
asking where else the defect it had just fixed still lives, and finding it two files away in code
T5 never touched. **`pnk init`'s half-created KB** came from T7 building a new surface and asking
what it inherited: the manifest is written before the template's declared files are validated, so a
refused declaration leaves a directory holding a manifest and no extras. It is pre-existing — *any*
failure after that write does it — and T7 only added one more way to reach it.

**All four were answered on 20260811** ([the decision record](https://github.com/lucagattoni/pinakes/blob/main/plans/20260811_0720-decisions-gates-and-corrections.md))
**and all four shipped in 0.22.0**: a protected paid document is re-chunked from the extraction
cache when warm; `--apply` restamps `[kb] template` on the `same manifest` outcome and says so
first; an eval header records both the configured tier and the resolved one; and `pnk init`
validates everything before it writes anything.

**Two of the four were not forks at all — they were unchecked assumptions.** The `init` item called
the full fix unavailable and the paid-rebuild item called re-chunking a paid call, and running the
code refuted both: `lands_inside` works against a target that does not exist, and the extraction
cache survives `--rebuild`. **An item that reads as a decision may only be something nobody ran.**

**Closing one of the two nearly opened its replacement.** Guarding the template reads turned a raw
`OSError` into a `PinakesError`, which routed the failure into an `except` that `pnk doctor` and
`pnk upgrade` already had — one answering *"is not installed here"*, about a template sitting right
there and merely damaged. Nothing went red: both surfaces still returned WARN and exit 3. It is the
same shape as the `same manifest` gap above, caught inside its own increment this time.

**The list refills from *use*.** An empty one means nobody has run Pinakes lately, never that it is
done.

**Nine items closed since 20260804**, and the pattern in them is worth more than the count:

| closed in | what |
|---|---|
| `0.10.0` | the interrupted-sync trio |
| `0.12.0` | the `[light]` backend error · `pnk doctor`'s home-directory leak · heading-coverage *detection* |
| `0.13.0` | **numbered plain-text headings** as `[chunking] headings` · the **silent `[chunking]` no-op** that building it exposed |
| `0.14.0` | the sync-CPU question **answered by measuring** · heading coverage's **permanent WARN** narrowed · `pnk init` **adopting** a directory with content · the `titles` nudge |

**Four of the nine were opened by the work that closed something else** — and one item's original
diagnosis turned out to be wrong and was corrected rather than quietly dropped: the Markdown heading
grammar never failed to match RFC numbering, it was **never run**, because `chunk.py` dispatches on
source type and a `.txt` file took `_plain_blocks`, which set `heading_path=None` unconditionally.
Nothing failed to match because nothing was tried.

> The list refills from use. An empty one means nobody has run Pinakes lately, never that it is
> finished.

## The graph release — shipped 0.11.0

✅ **Shipped in 0.11.0** (20260805 07:14), with its channel `off`. Blocked for three days on a
corpus, not on code; the corpus cleared the *reachability* precondition — and then the retrieval gate, run
20260804 22:52, did not pass. `expand` defaults `off` ([the numbers](STATUS.md#did-the-expansion-channel-earn-its-default--no-measured-20260804-2252)). 
**The finding is worth more than the feature.** The reachability probe found 9 failing multi-hop
questions reachable within two hops; the retrieval instrument lifted **none** of them, and the
channel displaced three answers the existing fusion already had. `reachable ≠ retrievable`, by 9
against 0.

**What it adds:** structural edges derived at sync time (sibling, parent/child, in-section,
co-located, shared-tag), an expansion channel behind `graph_channel` (default off), and
`schema_version` 3 — which forces a rebuild for every KB in existence. That forced rebuild is why
the gate was measured *before* the schema change rather than after it.

**Why it stopped, and what restarted it:** its gate was measured in
[`0.7.0`](#070--the-measurement-that-said-no--20260801-1240) and could not be reached on
`tests/demo-kb` — 1 of 18 multi-hop questions failing where 7 were needed. Re-measured on the
300-RFC corpus on 20260804: **12 failing, 9 reachable without authored edges**, against a
precondition of 7 and 7 —
[the numbers](STATUS.md#can-the-graph-releases-gate-be-reached--yes-measured-20260804),
[the decision](https://github.com/lucagattoni/pinakes/blob/main/plans/20260804_1442-decision-g3-go.md).

**What has already shipped from it:** G1 (reproducibility) and G4 (`requires_pinakes`) in
[`0.6.0`](#060--links-you-can-write--20260801-1051); G2 (the evaluation artifact and the measurement
itself) in [`0.7.0`](#070--the-measurement-that-said-no--20260801-1240); **G3, G5 and G6 all landed
in `0.11.0`**, so nothing from this build order is outstanding.

**One caveat that bounded the build, and its cause was not what was first recorded:** every chunk in
the 300-RFC corpus had an empty `heading_path`. Not because a grammar failed to match RFC section
numbering — because none was ever run: `chunk.py` dispatched on *source type*, and every type but
`markdown` took `_plain_blocks`, which sets `heading_path=None` unconditionally. So `in-section` and
`parent-child` derived **zero** edges and were never exercised, and `sibling` derived 106 506 that
changed no outcome. All six kinds were built anyway — that zero was a question for G5's gate, which
carried a `--drop sibling` arm to answer it, not a reason to drop a kind on evidence from a corpus
whose chunker had never been asked. `0.13.0` gave plain text a numbered-heading grammar — opt-in,
and that corpus's committed manifest does not ask for it, so re-running against it as published
reproduces these numbers rather than replacing them.

→ The design it would implement: [graph/PINAKES_APPROACH.md](graph/PINAKES_APPROACH.md). The build
order:
[`plans/20260729_0256-links-and-graph.md`](https://github.com/lucagattoni/pinakes/blob/main/plans/20260729_0256-links-and-graph.md).

### The corpus exists — built 20260804 08:00

[`pinakes-corpus-rfc`](https://github.com/lucagattoni/pinakes-corpus-rfc) — 300 RFCs, connected by
BFS over `obsoletes`/`updates`, structured by working group, tagged from the RFC Editor's own
keywords. It lives **outside this repo** by design
([`plans/20260801_0749-realism-corpus.md`](https://github.com/lucagattoni/pinakes/blob/main/plans/20260801_0749-realism-corpus.md)).

| | demo-kb | RFC corpus |
|---|---|---|
| documents | 30 | **300** |
| carrying an authored link | 27% | **53.3%** |
| worst out-degree | 2 | **86** |
| chunks | 60 | **106,806** |
| chunks with a heading path | most | **0** |

**It falsified a design premise.** *"Authored links are sparse, precious signal"* is half right:
median out-degree is **1**, but one real human-authored hub (RFC 8996 updates 86 documents in one
header) is a shape the frozen `2.0` weight was never designed for.

**It also found two things about Pinakes, not about the corpus** — the silent structural-chunking
failure above, and that 300 documents / 20 MB is already **2× past** the NumPy vector tier's 50,000
threshold ([DESIGN § 3.1](DESIGN.md#31-vector-search-what-the-tiers-actually-buy)).

→ The full comparison table:
[STATUS § The realism corpus exists](STATUS.md#the-realism-corpus-exists-and-it-falsified-a-design-premise--built-20260804-0800).

### What it settled, and what it did not — 20260804 22:52

**Settled.** Structural edges can be derived, stored and walked at corpus scale: 107,411 edges over
106,806 chunks, and the channel costs **1.02×** query latency, so the "slow at query time" risk did
not materialise. `sibling` is 99.2% of the graph's mass and is **inert in both gauges** — dropping
it changes neither reachability nor retrieval.

**Not settled — and this is the honest bound on the headline.** Three of the seven edge kinds
(`in-section`, `parent`, `child`) derived **zero** edges, because not one of the 106,806 chunks
carried a `heading_path` — the chunker was never asked for one on `.txt`, as the section above
records. Nothing failed to match because nothing was tried, which is why tightening a grammar would
have fixed nothing. So the verdict is *"the edge kinds that worked did not help this corpus"*, never
*"graph structure does not help"*. The `--drop parent-child` arm the arity decision added could say
nothing at all here, by construction.

**What would change it**, in the order the project would try them — **the first two have shipped:**

1. ✅ **Detect the silence** — `pnk doctor` reports the share of chunks carrying a `heading_path`
   (0.12.0). Detection only, as scoped; extending the grammar was left a separate decision.
2. ✅ **Make the three inert kinds derivable** — `[chunking] headings = "numbered"` gives plain text
   a heading path (0.13.0). It is **opt-in**, so it reaches a corpus only when asked: the published
   RFC corpus's manifest does not set it, while `tools/build_rfc_corpus.py` stamps it for a corpus
   built fresh. **What remains is re-running the gate against a corpus that has sections**, which
   nobody has done; the re-entry checklist is
   [`plans/20260804_1016-graph-remainder-reentry.md`](https://github.com/lucagattoni/pinakes/blob/main/plans/20260804_1016-graph-remainder-reentry.md).
3. **A different channel design.** Explicitly *not* a more expensive one — G5's result licenses
   neither PPR nor the `[ner]` extra, and the pre-commitment said so before the number was known.

> **The honesty constraint held.** The questions were frozen before the probe existed and were never
> re-authored to produce failures. Nothing was tuned after the result: no weight moved, no threshold
> was revisited. `expand-in-degree` was the one leg that lifted anything, and it is **reported, never
> gated** — noticing the best-performing leg after seeing the numbers is exactly the exploratory
> fitting the pre-commitment forbids.

## The graph release, staged — gates only, not scheduled

The PPR (personalized PageRank) channel and the `[ner]` extra. **There is deliberately no
implementation plan** — a written plan for work that may never ship creates pressure to build it.

What exists is
[`plans/20260804_1016-staged-channel-gates.md`](https://github.com/lucagattoni/pinakes/blob/main/plans/20260804_1016-staged-channel-gates.md):
what measurement would justify each, and what would refuse it. Decided 20260804: **PPR's gate does
not run at all on a corpus below the heading-coverage floor** — the absent input is half its
personalization vector, not one edge kind of seven.

→ The recipe and its counter-evidence:
[graph/PINAKES_APPROACH.md](graph/PINAKES_APPROACH.md) and [graph/GRAPH_RAG.md](graph/GRAPH_RAG.md).

## The deep release — the loop shipped in 0.24.0

**`pnk ask --deep`** — the budgeted agentic loop that escalates when free retrieval is not enough,
writing its discoveries back into sidecars.

▶ **✅ Complete as of [`0.26.0`](#0260--a-paid-run-tells-you-what-it-learned-about-your-kb--20260822-0132).** E1 to E4 landed on 20260811; `pnk ask --deep` answers,
bounded by `[deep]` and `[budget]`, in [`0.24.0`](#0240--pnk-ask---deep-answers--20260811-2224); E5's run transcript followed in
[`0.25.0`](#0250--a-paid-run-leaves-a-record-of-what-it-was-asked--20260812-0531), E6's measurement run in
[`0.25.3`](#0253--the-deep-loop-is-measured--20260821-2234), and E7's printed suggestions in
[`0.26.0`](#0260--a-paid-run-tells-you-what-it-learned-about-your-kb--20260822-0132). **The name
left the unbuilt-work table at that final cut** (D-9). This block stays here beside the graph
release's, which is also shipped: Part 5 holds the *named bodies of work*, and moving a completed
one would break every anchor that points at it.

- The **last paid entry point**: E3 added `src/pinakes/deep/client.py` to the allowlist, with
  [DESIGN § 1](DESIGN.md#1-what-this-is) and [INVARIANTS.md](INVARIANTS.md), in one commit. **The
  allowlist is complete at two entries**, and E4 is what first reached the second.
- **E5's transcript shipped in [`0.25.0`](#0250--a-paid-run-leaves-a-record-of-what-it-was-asked--20260812-0531)** — under
  `.pinakes/deep/<operation_id>.json`, spared by the sweep like a paid cache entry because it cost
  money to produce (D-26 A), removed only by `--clear-cache=transcripts`. Its other half was already
  closed: `pnk budget` shows `ask` operations beside `sync` ones, verified at E4 rather than assumed,
  and nothing in `budget/` had to move.
- **E6's measurement run shipped in [`0.25.3`](#0253--the-deep-loop-is-measured--20260821-2234)** —
  the only increment that spends real money, under [MEASUREMENT-RUN.md](MEASUREMENT-RUN.md). It
  calibrated E2's constants against real calls on a synthetic corpus, measured both branches, and
  published the over-reservation factor: **29.75x**, **50.92x** and **22.35x**, with no ceiling
  lowered.
- **E7's printed suggestions shipped in
  [`0.26.0`](#0260--a-paid-run-tells-you-what-it-learned-about-your-kb--20260822-0132)**, the final
  cut. `--write-suggestions` is deferred to its own increment (D-25 A) and is **not planned**,
  because writing them changes the per-link sidecar shape and adds to INVARIANTS' exceptions to
  *`docs/` belongs to the user*.
- **Nothing under this name is left to build.** The one design finding worth carrying into
  `--write-suggestions` is in the plan's E7 status block: a guard whose input is built by its own
  validator is not a guard, and its test is a tautology in test clothing.
- **A plan exists as of 20260811 13:58** —
  [`plans/20260811_1358-deep-release.md`](https://github.com/lucagattoni/pinakes/blob/main/plans/20260811_1358-deep-release.md).
  Seven increments, **eight decisions taken 20260811 14:17 and two more at E3's boundary**. It had
  been described as "planned" since [`0.1.2`](#012--the-readme-told-the-truth--20260727-1525) with
  no plan behind the word — and correcting the README's claim that it *existed* was that release's
  whole point.
- **Two measurements in that plan changed what this section used to imply, and one of them cost
  money to answer.** The budget machinery was already built and proven by the paid extractor, so
  this release added the loop and not the machinery. And the confidence signal that
  [§ 4.2](DESIGN.md#42-escalation--free-path-first) makes the escalation gate **ships commented out**
  in the `notes` template, so no KB a user creates has one — which made the *uncalibrated* branch
  the one a stock KB takes, and under the old `per_operation_eur = 0.30` even a one-round loop was
  refused. D-30 raised the defaults; D-22 is why the run happens at all, bounded by the caps rather
  than by the signal and saying which bound ended it.

→ The escalation model it implements:
[DESIGN § 4.2 Escalation — "free path first"](DESIGN.md#42-escalation--free-path-first). What the
command does: [CLI § `pnk ask --deep`](CLI.md#pnk-ask---deep).

## The template release — T1 shipped in 0.17.0

▶ **Every scheduled increment has shipped, and both gates are answered.** T1 as
[`0.17.0`](#0170--a-template-version-that-means-something--20260807-2055), T2 as
[`0.18.0`](#0180--the-drift-warning-says-something-you-can-act-on--20260807-2237), T3 as
[`0.19.0`](#0190--what-the-template-changed-in-your-own-file--20260808-0418), T4 as
[`0.20.0`](#0200--adopting-the-change-after-you-have-seen-it--20260808-0541), T5 as
[`0.20.1`](#0201--a-tier-that-is-not-built-stops-being-accepted--20260808-0641) and T7 as
[`0.21.0`](#0210--a-template-says-what-it-installs--20260808-1015) — then **T8 closed as a no-go and
T6 deferred behind a written trigger**, both in
[`0.22.0`](#0220--eight-decisions-and-two-of-them-were-never-decisions--20260811-0826). Per D-9 the
release cuts more than once, so the name stays here until the final cut — **which T6 could still
be.** *(The heading above still says T1 because renaming it would move this section's anchor, which
three links and the published site resolve.)*

**What it adds:** the template ecosystem, `pnk upgrade`, and the `sqlite-vec` tier.

**The problem it solves:** a template change reaches **new KBs only**. The PDF-glob explanation
shipped in [`0.2.2`](#022--the-silent-skip-named--20260728-1849) appears in no KB created before it
— so existing KBs stay PDF-blind permanently unless their owner edits the manifest by hand.
[`0.6.0`](#060--links-you-can-write--20260801-1051)'s `requires_pinakes` closed the *diagnosis*;
**0.17.0 makes the divergence detectable** and **0.18.0 makes it measurable** — though not on a KB
recording `notes@1.0`, whose content was never archived, which is every KB that exists today.
`pnk upgrade` (T3) prints the lines themselves and **`--apply` (T4) adopts them** — the hunks that
fit, after printing every one of them, refusing the whole run if any conflicts. **What remains
missing is not adoption but a baseline**: a KB recording `notes@1.0` has no archived content to
adopt against, so for every KB that exists today the last step is still the user's own edit, and
will be until the next template bump.

**State:** the plan
([`plans/20260804_1016-template-release.md`](https://github.com/lucagattoni/pinakes/blob/main/plans/20260804_1016-template-release.md))
is written, adversarially reviewed (36 findings), and its four open decisions were taken by the user
on 20260804. **T1 to T5 and T7 are done** — T5 shipped in 0.20.1, refusing `vector_tier = "sqlite-vec"`
instead of accepting and ignoring it and taking D-4 as option A; T7 shipped in 0.21.0 with
`pnk templates` and a template's own `files = [...]`.

**Both gated increments were answered on 20260811** (D-13 and D-14 in
[`plans/20260811_0720-decisions-gates-and-corrections.md`](https://github.com/lucagattoni/pinakes/blob/main/plans/20260811_0720-decisions-gates-and-corrections.md)).
**T8 — a second template — is closed as a no-go.** Its gate was run and fails leg 3: every
divergence in every admissible KB is a manifest value. Leg 2 fails too — the only owner-chosen
divergences are `[embedding] provider` and `[rerank] provider`, two settings for **one** reason (a
`[light]` install). More KBs of the same kind cannot move leg 3, so it is closed rather than left
gated, and **the gate's own redirect was taken instead** — a divergence that is a missing default in
`notes` means changing `notes`, not forking it, which is `pnk init --backend st|light` in 0.22.0.
**T6 — the `sqlite-vec` tier — is deferred rather than abandoned, and the reason is the gate, not
the cost.** Nothing blocks it technically (the precondition corpus already exists, and this
interpreter loads extensions). But performance is measured on an unlabelled ≥100k-chunk corpus while
*equivalence* is measured on `tests/demo-kb` at ~30 documents, so **nothing in a passing gate shows
the two tiers agree at 100k** — a pass would license the tier on half the evidence. Its trigger,
written before the fact so it is a trigger and not a mood: **a KB that is actually queried crosses
~50 000 chunks *and* its search latency is a felt problem.** A corpus above the threshold is not
enough; one exists and nobody searches it interactively. So the release name stays in the
unbuilt-work table.
T4 in turn left two things behind: it **created** an open correction — `--apply` writes nothing on
the *same manifest* outcome, so that KB can never record the new reference — and it found two of the
plan's own test specifications unable to measure what they named. T5 found an eighth: the plan asks
that both `sync` and `search` call the tier resolver *and* admits two paragraphs later that with one
tier there is nothing to discriminate.

⚠️ Its measurements are recorded *as of a named commit*, not as properties — `main` moved twice
during the session that wrote it. **Re-run its Baseline block before trusting any line number in
it.**

→ The problem stated in full, with all four drift axes: [KB-UPDATES.md](KB-UPDATES.md) — especially
[§ 2](KB-UPDATES.md#2-the-four-drift-axes), [§ 5 `pnk upgrade`](KB-UPDATES.md#5-pnk-upgrade) and
[§ 6 Detecting template drift](KB-UPDATES.md#6-detecting-template-drift). The vector tier it would
add: [DESIGN § 3.1](DESIGN.md#31-vector-search-what-the-tiers-actually-buy). Templates:
[DESIGN § 6.1](DESIGN.md#61-templates).

---

## How this project builds

Useful context for reading anything above. The rules themselves live in
[`CLAUDE.md`](https://github.com/lucagattoni/pinakes/blob/main/CLAUDE.md), the procedures they point
at in [BUILDING.md](BUILDING.md) and [RELEASING.md](RELEASING.md).

- **One increment at a time.** Own worktree, own branch, tests in the same commit, `./check.sh`
  green, then a **fresh adversarial review** of the diff before it merges. Findings are their own
  commit, and the ones worth keeping become [retrospectives](RETROSPECTIVES.md).
- **Green is not enough.** For the most safety-critical assertions, the source is mutated on purpose
  to confirm the *right* test fails. Tests written by the reasoning that wrote the code inherit its
  blind spots.
- **Unbuilt work is named, never numbered.** For months `v0.3` meant the links release; then `0.2.2`
  shipped and the next MINOR *was* `0.3.0`. One number meant two releases, and either reading would
  have renumbered ~60 committed references ([STATUS § Release roadmap](STATUS.md#release-roadmap)).
- **Complete work never sits in `[Unreleased]`.** Hence the release cadence in the table above
  ([RELEASING.md](RELEASING.md)).
- **`CHANGELOG.md` and `RETROSPECTIVES.md` are never edited directly** — a change drops a fragment in
  [`changelog.d/`](https://github.com/lucagattoni/pinakes/blob/main/changelog.d/README.md) or
  [`retro.d/`](https://github.com/lucagattoni/pinakes/blob/main/retro.d/README.md), spliced at
  release time. Several agents work here at once, and a clean auto-merge is not a correct merge.
- **Every promise has a test, and the table naming them is gated** —
  [VERIFICATION.md](VERIFICATION.md).
