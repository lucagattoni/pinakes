# Pinakes documentation

**Everything in this directory is published** to
[lucagattoni.github.io/pinakes](https://lucagattoni.github.io/pinakes/) by
[`.github/workflows/docs.yml`](../.github/workflows/docs.yml) on every push to `main`. The site is a
*view* over these files, never a second copy — which is why nothing was moved to build it: these
filenames are load-bearing in code (`tools/fragments.py` writes `RETROSPECTIVES.md`,
`tools/status_header_gate.py` and CI parse `STATUS.md`, `tests/test_verification.py` reads
`VERIFICATION.md`). Chapter numbers live in `mkdocs.yml`'s `nav` and are applied by JavaScript, so
the Markdown here stays clean for GitHub. Two files sit outside the set above: `index.md` is the
site's landing page and nothing else links to it, and **this file is excluded from the site** — it
is the agent-facing routing table, and MkDocs will not accept it and `index.md` in one directory
anyway.

| Doc | Answers |
|---|---|
| [**GUIDE.md**](GUIDE.md) | *How do I use this?* Install, first KB, PDFs, search, hooks, MCP, troubleshooting |
| [**CLI.md**](CLI.md) | *What does this flag do?* Every command, every flag, exit codes |
| [**MANIFEST.md**](MANIFEST.md) | *What goes in `pinakes.toml`?* Every manifest and sidecar field, with defaults |
| [**MEASUREMENT-RUN.md**](MEASUREMENT-RUN.md) | *How were the paid extractor's quality numbers obtained, and how do I re-run them?* The runbook, its steps and its euros |
| [**STATUS.md**](STATUS.md) | *Does this exist yet?* Shipped vs planned, the increment ledger, measured numbers |
| [**ROADMAP.md**](ROADMAP.md) | *What happened, in what order, and what is left?* Every release with a plain-language expansion, then the unbuilt work and what blocks it. **Human-facing, and it owns no fact** — a narrative view over STATUS, CHANGELOG and `plans/`, which stay authoritative |
| [**VERIFICATION.md**](VERIFICATION.md) | *What holds this promise?* Every claimed property and the test that checks it — `tests/test_verification.py` asserts each one exists |
| [**INVARIANTS.md**](INVARIANTS.md) | *What must never break?* The contracts that fail **silently** — ULIDs, the sidecar round-trip, the ledger, the paid-path allowlist. Each names the file owning its detail; only the implementation rules nothing else states are written out there |
| [**BUILDING.md**](BUILDING.md) | *How do I build one increment?* Worktree, tests, `check.sh`, mutation, adversarial review, fragments, `land.py` — the procedure that runs before [RELEASING.md](RELEASING.md) |
| [**DESIGN.md**](DESIGN.md) | *Why is it built this way?* Architecture, storage, sync semantics, concurrency, trade-offs |
| [**RETROSPECTIVES.md**](RETROSPECTIVES.md) | *What did we learn?* Per-increment findings, and the design's own review passes |
| [**KB-UPDATES.md**](KB-UPDATES.md) | *What happens to a KB somebody already has when Pinakes changes?* Design note — **part built**: `requires_pinakes` (G4, 0.6.0) and template-drift **detection** (§6's gate, 0.17.0), `pnk doctor` reporting **how far** a template has drifted (T2, 0.18.0), **`pnk upgrade`**, which prints the lines themselves (T3, 0.19.0), and **`--apply`**, which adopts the hunks that fit (T4, 0.20.0). What is still a proposal is the rest of §8's shape — `pnk adopt`, and anything that reaches beyond `pinakes.toml` |
| [**graph/**](graph/) | Graph-retrieval research shaping the links and graph releases — thirteen investigations plus the synthesis |

Build plans live in [`plans/`](../plans/); the release history is [`CHANGELOG.md`](../CHANGELOG.md).
`plans/` holds more than one kind of file. **As of 20260825 12:40 two files propose work: the
exposure plan and the run-Pinakes sweep, both at the top of the table.** The exposure plan's § X1 is
**built and landed** and its **D-35 was answered 20260825 12:37**, which unblocks § X7; D-31 to D-34
were **answered 20260825 18:16**, with every other open question, in the open-decisions file at the top
of the table. The sweep carries sixteen confirmed defects and two now-answered
decisions. Every other file below is closed,
answered, deferred or proposed-unscheduled — so **an empty-looking `plans/` still means the next thing
to build has not been planned yet, never *nothing to do***; Part 5 of [ROADMAP.md](ROADMAP.md) holds
the candidates for what comes after the exposure plan. Never take "the newest
file here" for the build order:

| File | What it is |
|---|---|
| [`20260825_1803-open-decisions.md`](../plans/20260825_1803-open-decisions.md) | **Every open decision in the repository, evaluated — and ALL EIGHT TAKEN BY THE USER 20260825 18:16.** **Two of the taken options (D-36 E, D-37 E) were invented by that pass's adversary and appear in no earlier plan, and D-36's first-pass recommendation was overturned** — so a reader working from the sweep plan's options list gets the wrong answer. Read the decision, never a memory of the options. Eight clusters, fifteen questions, each analysed against the tree and then attacked by a dedicated adversary. **Seven of the eight recommendations changed after that second pass**, which is the argument for it. **Read § *Read this before acting on any row* first**: four of the eight turned out to be partly or wholly **answered already on `main`** — the dominant failure here is not *undecided*, it is *decided where nobody looks*. **Six of the eight block nothing**; only D-37 blocks work already queued. Carries the ordering, the per-option pros and cons, what would change each answer, and a closing section on the two claims this pass got wrong about itself — one an adversary's timezone error, one the planner's row count |
| [`20260825_1252-plans-sweep-findings.md`](../plans/20260825_1252-plans-sweep-findings.md) | **Every section of every file in `plans/` classified by reading its *body* — 317 sections, 20 files, and 93 heading/body mismatches.** Discharges X3. **A heading in this directory is wrong about one section in six**, which is why the earlier heading-only sweep dropped nine files and lost the arity plan's only outstanding work. Carries **53 proposed heading dispositions** (the input X2 needs), **19 corrections owed** — factual claims wrong on the tree, including one in this very table — and **13 open questions — as of 20260825 18:16, eleven are answered, one is deferred behind a written trigger, and one is still a stop.** The stop is the last one, and it is not a decision: two external repositories were never fetched and no reviewer ran a gate. **This row states no other count deliberately** — the ones above it went stale within a day. **Read § *Three of this sweep's own claims did not survive checking* first**: the pass that produced the list also caught itself three times. **Two external repositories were not fetched**, so anything turning on the dogfooding KB's or the RFC corpus's live state is marked UNCLEAR rather than resolved |
| [`20260825_1240-run-pinakes-sweep.md`](../plans/20260825_1240-run-pinakes-sweep.md) | **Sixteen defects found by *running* Pinakes — fifteen across seven surfaces, none by reading it, plus S16 from the adversarial review of a fix** — each re-run from a clean directory by a verifier told to refute it; five refuted and dropped. **Three high**: `sync` meeting one unreadable file raises an unhandled `PermissionError` and builds **no index at all**, so nothing in the KB is reachable; `doctor` exits **0** on a KB where a sync `IntegrityError` left a document at `state='deleted'` with sidecar and source intact; `serve` caches one `sqlite3.Connection` across OS threads, firing on **any pause over ~10 s** and never on back-to-back calls. **Six medium**, including a KB name that is not valid TOML bricking the KB at creation with **exit 0**, unrepairable by any `pnk` command and needing no flag. **D-36 and D-37 were ANSWERED 20260825 18:16, both on options the adversarial pass invented.** **Read its § Provenance before acting on a row** — the markers are not uniform, and one finding was recovered after a verifier returned *no verdict* and a classifier defaulted it to *refuted*. **The paid-path invariant survived** adversarial testing, measured from a stripped subprocess |
| [`20260825_0749-exposure-and-silent-status.md`](../plans/20260825_0749-exposure-and-silent-status.md) | **Its build order is fully built out, and D-31 to D-34 were ANSWERED 20260825 18:16** (see the open-decisions file at the top of this table — two taken options were invented by that pass's adversary and appear in no earlier plan). Two subjects, one failure: what Pinakes promises about `.pinakes/`, and status claims nothing gates. **§ X1 is BUILT** (`35cdc79`) — read it for what shipped and for the two constraints the increment had to correct in this plan. The measurement behind it: the 0.30.2 detector reports **protected** for a repository that is actively committing the user's verbatim questions, because its probes are opaque tokens and so are never in the index. A correct `.gitignore` does not untrack an already-tracked file, and **nothing in Pinakes says so anywhere**. D-31 (does `pnk doctor` carry a recurring check), D-32 (WARN vs OK-with-a-note), D-33 (ignored *here* vs *for everyone*) are E5's reserved decisions, restated because M2 inverts the argument; D-34 (does `docs/VERIFICATION.md` map every test or promises only) is new and unscheduled. Part 2 carries the `plans/` restructure, the sweep that read 11 of 20 files, and four conventions this repository has re-derived and never written down |
| [`20260811_1358-deep-release.md`](../plans/20260811_1358-deep-release.md) | **Closed at 0.26.0 — every increment built.** `pnk ask` and `pnk ask --deep`: seven increments, E1 to E7, and **all ten decisions (D-21 to D-30) are taken — eight on 20260811 14:17 and two more at E3's boundary, and it is the authority for every one of them**, with the rejected options kept and costed. **E1 to E6 are built: `pnk ask` free ([CLI](CLI.md#pnk-ask)), the round estimator, the paid client, the loop — so [`pnk ask --deep`](CLI.md#pnk-ask---deep) answers, bounded and budgeted — and the [run transcript](CLI.md#the-transcript) every paid run leaves under `.pinakes/deep/`. E6 — the measurement run, and the only increment that spends real money — is **built**: it published the over-reservation factor (**29.75×** on the cheap synthesis branch, **50.92×** and **22.35×** on the two loop branches), gave every E2 constant its measurement, and lowered no ceiling. Its status block carries the four things it learned that the plan did not anticipate; [MEASUREMENT-RUN.md](MEASUREMENT-RUN.md) is the procedure and now records what the run settled. **E7 — printed suggestions — shipped in 0.26.0, the final cut**, so the release name left the unbuilt-work table there (D-9): a `--deep` run now ends by printing the `links[]` entries its own citations propose ([Suggested links](CLI.md#suggested-links)), and `--write-suggestions` stays deferred and **unplanned** (D-25 A). **Two status blocks to read before touching the deep path**: E6's, before trusting any fixture-backed claim, and E7's, before adding a guard — *a guard whose input is built by its own validator is not a guard, and its test is a tautology*.** Two of its measurements change what the older documents imply: the budget machinery is **already built** (so this adds the loop, not the machinery), and `[retrieval.confidence]` **ships commented out**, so the escalation gate DESIGN § 4.2 depends on exists on no KB a user creates — which is why E4 raised the default `[budget]` caps (D-30): the uncalibrated branch is the one a stock KB takes, and under the old `per_operation_eur = 0.30` even a one-round loop was refused. Written against `main` at `106d01f` — **re-run its § 2 before trusting a `file:line`** |
| [`20260811_0720-decisions-gates-and-corrections.md`](../plans/20260811_0720-decisions-gates-and-corrections.md) | **The authority for all eight decisions in it** — **no longer the *newest* taken record: [`20260825_1803-open-decisions.md`](../plans/20260825_1803-open-decisions.md) at the top of this table took fifteen questions on 20260825 18:16** — both template-release gates and all four open corrections. Where an older plan below still reads as undecided, **this file supersedes it**. Its § Build order **is fully built out as of 0.22.0**, so nothing in it is waiting — the live build order is now the deep-release plan above. **Read its § *What was checked first* before re-opening any item**: two of the four corrections had stalled on premises that were simply false, and running the code refuted both |
| [`20260805_1721-metadata-as-retrieval-context.md`](../plans/20260805_1721-metadata-as-retrieval-context.md) | **Closed 20260807 — answered.** Are `title` and `heading_path` retrieval context or display metadata? Measured: injecting them into the embedded text moved 6 questions up and 6 down on a 195-document corpus, so the `schema_version` 4 bump was not taken and PDF layout heuristics and paid title inference stay unapproved. **Read its §0**; the rest is the record of how, including the frozen golden set (`tools/rfc_corpus/questions.yaml`, 110 questions — **never reword or renumber one**; `id` pairs a before row with an after row) and `[chunking] metadata`, shipped default `off`. What it measured is *vector-only* injection on one corpus — the both-channel form was never tested, so it does not say metadata is worthless. **What would re-open it is a corpus, not an idea about the prefix**: this one's `lexical` and `simple-lookup` classes are saturated at 1.00, so all its power sat in `paraphrase` |
| [`20260729_0256-links-and-graph.md`](../plans/20260729_0256-links-and-graph.md) | **Closed.** Both its releases shipped — the links release in 0.5.0–0.6.0, the graph release in 0.11.0 (G3, G5, G6). G5's gate ran, did **not** pass, and `graph_channel` ships `off`: nothing in it is live, and the staged channels below are **not** licensed by that result |
| [`20260801_0102-links-and-graph-log.md`](../plans/20260801_0102-links-and-graph-log.md) | That plan's iteration log: how it was reached, never what to do |
| [`20260731_2128-source-walk-containment.md`](../plans/20260731_2128-source-walk-containment.md) | A standalone increment, shipped in 0.7.1 — outside both releases above |
| [`20260731_1202-open-corrections.md`](../plans/20260731_1202-open-corrections.md) | Numbered corrections for the implementing agent; items are closed in place, never deleted. **Three live items.** (1, added by E5) `pnk init`'s gitignore-warning question. **It is no longer a decision — D-31, D-32 and D-33 were ANSWERED by the user 20260825 18:16** (`pnk doctor` asks both questions, tracked *and* ignored, **unconditionally**), so it is queued coder work; the authority is [`20260825_1803-open-decisions.md`](../plans/20260825_1803-open-decisions.md), not the exposure plan's original framing. **(2 and 3, added 20260825 19:02, both coder-owned)** `make release-check` **runs no gate at all** — three `echo`s behind a help string promising it verifies the tag, and it is what `CLAUDE.md` sends you to run before an irreversible publish; and `pageyield.py` justifies `SCANNED_PAGE_FRACTION` with an example the constant refuses, **at two sites**, and that plan's § X1 supersedes this item's *"not urgent"*: the hazard it did not consider is measured, silent and unrecoverable. **Also read § X2 there before trusting this file's `## Live` heading** — an item's closure can sit in its body, and that has now cost two near-rebuilds. The list emptied on 20260805 and at 0.22.0 and **refilled within days both times**: an empty list means *nobody has run Pinakes lately*, never *finished* |
| [`20260801_0749-realism-corpus.md`](../plans/20260801_0749-realism-corpus.md) | The RFC corpus and the dogfooding KB — both live **outside** this repo |
| [`20260804_1016-template-release.md`](../plans/20260804_1016-template-release.md) | **Closed as of 0.22.0** — the template release: the ecosystem, `pnk upgrade`, the `sqlite-vec` tier. Reviewed (36 findings) and revised, its four decisions taken 20260804. **Every scheduled increment is shipped: T1 in 0.17.0, T2 in 0.18.0, T3 in 0.19.0, T4 in 0.20.0, T5 in 0.20.1, T7 in 0.21.0 — and both gated increments were answered 20260811: T8 is a no-go (its gate was run and fails leg 3), T6 is deferred behind a written trigger** (a queried KB past ~50 000 chunks *with* felt latency), **so the release name stays in the unbuilt-work table.** Re-run its Baseline block first, and read each increment's landing commits — **ten** of the plan's own measurements or specs have been wrong, T4 finding two, T5 one and T7 two |
| [`20260804_1016-graph-remainder-reentry.md`](../plans/20260804_1016-graph-remainder-reentry.md) | What must be re-verified about G3/G5/G6 **if** the blocking measurement is ever passed — a re-entry checklist, not a plan |
| [`20260804_1016-staged-channel-gates.md`](../plans/20260804_1016-staged-channel-gates.md) | The **gates** for the PPR channel and the `[ner]` extra — what measurement would justify each, and what would refuse it. Deliberately not implementation plans |
| [`20260803_2239-corpus-probe-run.md`](../plans/20260803_2239-corpus-probe-run.md) | How the second headroom measurement is run against that corpus, and the conversion contract that keeps its frozen questions frozen |
| [`20260807_2143-docs-audit-findings.md`](../plans/20260807_2143-docs-audit-findings.md) | **The open documentation corrections from the 20260807 audit** — a worklist for the planner, **not a build plan**. **This row deliberately states no count.** It said *39 open, one fixed*, which went stale; and the plan itself now disagrees with its own arithmetic — line 17 says **40** still open, while its summary table gives 39 at audit minus 6 fixed = **33**, and its `# Medium — 13` / `# Low — 27` dividers sum to 40 against that stated 39. **Read the plan's own § *Re-verified 20260823* for the live tally; do not quote a number from here.** Resolving the contradiction needs counting the sections and is filed as a correction in [`20260825_1252-plans-sweep-findings.md`](../plans/20260825_1252-plans-sweep-findings.md). Each names the file, line, claim, truth, evidence and fix; each was verified by a second agent prompted to refute it. **One is fixed, and it is the one to read before leaving the rest**: `docs/STATUS.md:303`, the `0.15.1` row out of release order, closed 20260811 13:27. It sat verified and unworked for four days while three release sweeps added **four more** misplaced rows in the same class — the cost of a finding grows after it is verified, and `tools/release_order_gate.py` is what now stops that one recurring. The doctor-adjacent ones are cheaper after T2 (shipped 0.18.0), and the three currency headers are restamped last. It also **defers a full review of `docs/ROADMAP.md` until after T2** — out of scope for the audit itself, and still owed |
| [`20260821_0745-mutation-harness.md`](../plans/20260821_0745-mutation-harness.md) | **Shipped 0.27.0.** A committed mutation harness, `tools/mutate.py`: the `land.py` precedent applied to the mutation step, the procedure's other silently-failing class (more than a dozen invalid runs recorded, six of them the identical `git checkout` trap). The plan's status block records what shipped *beside* what it asked for — five ways a run can lie that it did not name, all measured, all now refusals. **Read it before writing a battery**, and `tools/mutate.py`'s own docstring for the format. **The plan never decided whether a battery is kept**; that was settled by measurement afterwards and batteries are now committed — [`tools/batteries/README.md`](https://github.com/lucagattoni/pinakes/blob/main/tools/batteries/README.md) owns the convention, the naming and what to do when an anchor rots |
| [`20260804_1442-decision-g3-go.md`](../plans/20260804_1442-decision-g3-go.md) | **The G3 go/no-go, taken 20260804 — and it had no row here until 20260825**, so it was reachable only from links inside other plans. **Closed**: its § *What starts, in order* lists G3/G5/G6 as about to begin and all three shipped in 0.11.0; nothing in the file records the release |
| [`<stamp>-decision*.md`](../plans/) | A decision record — rationale, not instructions. **Five of them**, each carrying the `YYYYMMDD_HHMM-` prefix every plan was renamed to; one is `decisions-` plural, so match the stem rather than a literal `decision-` |
| `20260725_1317-v0.1.md`, `20260727_1543-v0.2.md` | **Shipped — with one exception the plan's own heading names and this row used to omit.** Historical build orders, still cited by `check.sh` and `tools/paid_path_gate.py`. **`v0.2` is shipped across 0.2.0–0.4.0 *except decision 12*, whose paid re-extraction loop has never shipped and is DEFERRED** — its trigger lives in `src/pinakes/extract/audit.py`'s docstring, where the person who would build it reads, rather than in a roadmap row a sweeper reads |

**Two of these documents are written to indirectly.** `CHANGELOG.md` and `RETROSPECTIVES.md` are the
files every piece of work touches, so a change adds a fragment to
[`changelog.d/`](../changelog.d/README.md) or [`retro.d/`](../retro.d/README.md) and
`python3 tools/fragments.py --apply` splices them at release time. **Never edit either document
directly.** Reading them, note that anything unreleased is still sitting in its fragment directory.

---

## Where does a fact live?

**One fact, one home.** Each row is the *only* place that fact belongs; everywhere else links to it.
When an increment lands, this table says which file to edit — usually exactly one.

| Fact | Home | Everywhere else |
|---|---|---|
| Whether a feature is built yet | **STATUS.md** | links to it — never restates a version. [ROADMAP.md](ROADMAP.md) retells it for a human and is **derived**: correct STATUS first, then sweep ROADMAP, never the reverse |
| What a command or flag does | **CLI.md** | `--help` is authoritative; CLI.md adds when and why |
| A manifest or sidecar field, its default, its validation | **MANIFEST.md** | DESIGN gives the rationale and links here |
| How to accomplish a task | **GUIDE.md** | README links to it |
| Why a design decision was taken, and what it costs | **DESIGN.md** | — |
| Which code paths are allowed to spend money | **`.paid-path-allowlist`** + [INVARIANTS.md](INVARIANTS.md) | DESIGN §1 gives the rationale; `check.sh`, CI and `tests/test_paid_path.py` read the file itself |
| A measured number (recall, latency, false-confidence) | **STATUS.md** | cited with its date wherever quoted |
| What changed in a release | **CHANGELOG.md** | written as a `changelog.d/` fragment; spliced at release |
| What an increment taught us | **RETROSPECTIVES.md** | written as a `retro.d/` fragment; spliced at release |
| How to run the human-gated paid measurement | **MEASUREMENT-RUN.md** | STATUS carries the numbers it produced, with their date |
| What is going to be built, and in what order | **`plans/`** | STATUS.md carries the shipped/planned state only |
| How to cut a release, step by step | **[`RELEASING.md`](RELEASING.md)** | `CLAUDE.md` carries the *rules* about when; this is the procedure — and, since 20260823, the `land.py` trap's mechanism ([§ Landing a branch](RELEASING.md#landing-a-branch)), which CLAUDE.md points at rather than states |
| How to build one increment, step by step | **[`BUILDING.md`](BUILDING.md)** | `CLAUDE.md` names which plan is live; this is the procedure |
| A contract that fails silently when broken | **[`INVARIANTS.md`](INVARIANTS.md)** | the detail stays with its owner (DESIGN, MANIFEST, VERIFICATION, CLI) — INVARIANTS lists and links, and states only the implementation rules nothing else does |
| Which test holds a given promise | **VERIFICATION.md** | a plan's own table records what was *predicted*, never what exists |

The README is deliberately **version-free**: it describes what Pinakes *is*, never what release you
are on. That is why it does not go stale.

## Landing a new increment

The docs are built so an increment touches few files. **Steps 1 to 5 are planner-only** — they are
all `docs/**`, so an implementer *proposes* them as a `git diff` against a named commit rather than
editing them (`CLAUDE.md` § *Documentation has one owner*). Step 6 onward is anyone's. In rough
order:

1. **STATUS.md** — flip the increment's row. Merged to `main` but not in a release is **"on `main`,
   unreleased"**, not "shipped": installing from a tag and installing from `main` are different
   answers to "can I use this yet". Move its capability out of "not built" only when a user can
   actually reach it. If it changed a measured number, update it *with the date you measured it*.
2. **CLI.md** — move the surface out of "Planned", or add its flags to the command's table.
3. **MANIFEST.md** — add any new manifest or sidecar key, with its default.
4. **GUIDE.md** — fill the stub if the increment made a task possible that wasn't before.
5. **DESIGN.md** — only if the *rationale* changed. A new flag alone is not a design change.
6. **A [`changelog.d/`](../changelog.d/README.md) fragment** — one file, named
   `<category>-<slug>.md`, in the same commit as the code. **Never an edit to `CHANGELOG.md`**:
   it is the one file every increment would otherwise touch, and two agents cannot conflict in
   separate files.
7. **VERIFICATION.md** — if the increment shipped a test that holds a promise, it gets a row. The
   gate walks from this table to the tests, so it catches a row naming a test that does not exist
   and **cannot** catch a shipped guarantee with no row: 0.7.1 shipped seventeen containment tests
   and added none (found 20260804, rows added then).
8. **A [`retro.d/`](../retro.d/README.md) fragment** if the increment's review found something
   worth keeping — a real defect, or a fact expensive to rediscover. Same reason, same rule:
   never edit `RETROSPECTIVES.md` directly. Trivia stays in the commit message.

`plans/20260727_1543-v0.2.md` carries a DESIGN.md amendment table assigning each spec edit to the increment that
makes it true. **Amendments land with their increment, never in advance** — a spec describing
unbuilt behaviour is the failure mode the project's README rule exists to prevent. DESIGN sections
still awaiting an amendment carry a dated note saying so.

**Before assigning a release number, check what has already landed on `main`**
([RELEASING.md § Before you start](RELEASING.md#before-you-start)).
Another session or worktree may have cut a release since your branch started, so the number you were
about to use — or the one a plan assumes — may already be taken. `plans/20260727_1543-v0.2.md` assumed it would cut
`0.2.0` at I9; `0.2.0` shipped after I5 and `0.2.1` after that.

And **do not write a number for the release after this one** — name it (see Conventions below). That
is what stops the next plan from assuming a number that a parallel session has already spent.

## Conventions

> ### 🚫 Unbuilt work is named, never numbered
>
>
> **A version number belongs to a release when it is cut — never before.** Refer to unbuilt work by
> name: **the template release**. (A name leaves this list at its release's *final* cut — the
> paid-extraction release became 0.3.0, the links release 0.5.0 + 0.6.0, the graph release 0.11.0
> — **but *the graph release, staged* is a different name and is still live**, because that cut never
> covered the PPR channel or the `[ner]` extra; both are eval-gated and neither has a plan —
> and **the deep release left it at 0.26.0**, its final cut (D-9): `pnk ask --deep` is built,
> measured and complete, including E7's printed suggestions. `--write-suggestions` is deferred and
> **unplanned** — when it is planned it needs a name of its own, not the old one.) Never write
> `v0.4` for something that does not exist — not in docs, not in `--help`, not in an error message,
> not in a code comment. The live names are kept in [`CLAUDE.md`](../CLAUDE.md); this is the rule,
> not the list.
>
> Decided 20260729 00:09, after `v0.3` came to mean two different releases at once and picking either
> meaning would have renumbered ~60 committed references. Full rationale and the current mapping:
> [STATUS.md § Release roadmap](STATUS.md#release-roadmap).
>
> Historical records (`CHANGELOG.md`, `RETROSPECTIVES.md`, `plans/`, the dated research in `graph/`)
> keep the numbers they were written with and carry a header note pointing at STATUS.md.

- **Every date carries a time**: `YYYYMMDD HH:MM`, **UTC**. Several entries land per day, and a
  bare date loses their order and hides how fresh a "verified" claim is. UTC since 20260804 11:32;
  timestamps written before that are local and stay local, because converting one invents precision
  nobody measured.
- **Read the clock; never compose a timestamp.** Run `date -u "+%Y%m%d %H:%M"` and paste the result;
  derive a past one from `git log`, never from memory. Session context carries a date and never a
  time, so an invented `HH:MM` lands in the future about half the time.
- **Docs describe what ships.** Anything unbuilt is labelled with the increment or release that will
  bring it. Check by *running the commands a doc shows*, install line included — an audit at 0.1.2
  found four README claims contradicting the code while the CLI and CHANGELOG were correct.
- **Every change and every decision is audited for its neighbourhood, not its diff.** Before landing
  it, re-read what surrounded or depended on it and ask four questions of each: is it **consistent**
  with the other docs, does its **logic** still hold, has it been **superseded** by a decision taken
  since, and is it **outdated** against the code, the index or the clock. Whatever made the line you
  came to fix go stale almost certainly reached its neighbours too.

  **A decision's neighbourhood is not prose** — it is every table, increment body, release
  structure, roadmap row and invariant that assumed the decision it replaces. Superseding in the
  record and leaving the tables is how a plan comes to say two things at once. Measured 20260731:
  of nine decisions in the `ruamel.yaml` swap, three rippled into tables the deciding pass never
  opened, and an adversarial pass found them.
- **Name the audience and the goal before writing a line.** Audience: a **human**, an **agent**, or
  **both**. Goal: **reference** (answers "why" or "what is true") or **executor** (something acts on
  it). The two axes decide the form, and getting them wrong is the commonest defect here.

  | Doc | Audience | Goal |
  |---|---|---|
  | `README.md`, `GUIDE.md` | human | orientation / executor |
  | `CLI.md`, `MANIFEST.md`, `STATUS.md`, `VERIFICATION.md` | both | reference |
  | `DESIGN.md`, `plans/decision-*.md` | both | reference — rationale only |
  | `CLAUDE.md`, `plans/<plan>.md` | agent | **executor** |
  | `changelog.d/`, `retro.d/` fragments | agent | executor |

  An **executor** doc is imperative, self-sufficient, and names exact files, symbols and predicates:
  the agent reading it has no access to whoever wrote it. A **reference** doc may argue, measure and
  survey. **Rationale in an executor doc is noise; an instruction in a reference doc is a defect** —
  compacting L5b on 20260731 moved decision 23's resolver predicate into the decision record and
  left the increment unbuildable from its own text.
- **Rewrite to the current state; do not layer corrections.** A doc that grows by appending
  "actually, that was wrong" makes every reader traverse the archaeology to learn what is true now.
  State each claim correctly once and delete what it replaced — git holds the history. Measured
  20260731: `plans/20260731_0602-decision-ruamel-yaml.md` reached 297 lines, 156 of them three layers of
  correction, and collapsed to 110 with nothing load-bearing lost.
- **Compact on a schedule, not when it hurts.** Review every doc against these conventions monthly,
  alongside the `CLAUDE.md` hygiene pass. Cut recaps, summaries of other sections, superseded
  reasoning, and any sentence that re-argues what another file owns. Keep what a future
  implementation needs: decisions, measured numbers, and instructions. A section far larger than its
  siblings is the signal — L5b hit 247 lines against a 52-line median for other increments.

  The cost of skipping it, measured 20260729: a one-line PyPI correction was asked for, and the
  same sweep found five more — a release still listed as unbuilt in two tables, an install block
  missing the last two releases' headline capability, a README sentence implying a feature that is
  not built, a runbook still described as producing numbers the project "admits it lacks" after the
  run had happened, and a design note saying "no increment assigned" for work a plan had since
  assigned. Each was a single edit; none would have been found by reading the diff.
- `make check` formats Python **inside Markdown fences**, so a docs-only commit can fail the gate.
- **A link out of `docs/` is written absolute; a link inside it stays relative.** `plans/`,
  `CLAUDE.md`, `changelog.d/` and `tools/` have no page on the site, so a relative `../plans/x.md`
  renders on GitHub and dangles on the site. Write
  `https://github.com/lucagattoni/pinakes/blob/main/plans/x.md`, which works in both. `make docs`
  runs `--strict` and fails on the difference, and so does the `docs` workflow on every PR.
- **Heading anchors are GitHub's, on both surfaces.** `mkdocs_hooks.py` installs GitHub's slug
  algorithm because neither Python-Markdown's default nor pymdownx's matches it, and every
  cross-document anchor here was written against GitHub. Never renumber or rename a heading to fix
  a site link — that fixes the site by breaking the copy people already read.
