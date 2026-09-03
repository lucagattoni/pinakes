# Status — what ships today

**Latest release: 0.32.3** — ⏸ **landed on `main`; `pip install pinakes` still gets 0.32.2.** · last reviewed 20260903 14:38

> **This file is the only place in the repo that says what is built.** Every other doc describes
> *how* something works or *why* it was designed that way, and links here for whether you can use it
> yet. When an increment lands, flip its row below — no other doc should need a version edit.
>
> "Shipped" below means **released**; an increment merged to `main` but not yet in a release says so
> explicitly. Installing from a tag and installing from `main` are different answers to "can I use
> this yet", and this file is where that difference has to be visible.

---

## The surface you can use today

| Command | State | Notes |
|---|---|---|
| `pnk init` | shipped | one template (`notes`); `--ci` writes the workflow (0.3.0). **0.32.1:** a KB name holding a `"`, a `\` or a control character is escaped where the manifest is rendered instead of bricking it, and a name TOML cannot represent at all is refused before anything is created |
| `pnk sync` | shipped | `--rebuild`, `--scan-links`, `--sidecars-only`, `--index-only`, `--extract`, `--force`, `--clear-cache` (bare, `=all`, `=paid`, `=transcripts`). **0.32.2:** `--sidecars-only --index-only` is refused rather than silently writing into `docs/`; an ordinary deletion no longer reports a move and a mint; and a document you repair clears its own row in the failure ledger instead of being listed forever. **0.32.3:** it no longer crashes on Python 3.13 for an unreachable symlink, a mistyped `--source-type` is a usage error, and an empty KB stops blaming filters nobody passed. **Still open, and not fixed here:** a `[sources]` root the process cannot read enumerates nothing, so every document under it is removed from the index at exit 0 |
| `pnk search` | shipped | BM25 + vector + rerank, metadata filters, `--json`. **0.32.2:** `-k` below 1 is a usage error at the parser on this surface and on `pnk ask` — including `-k 0`, which was falsy and silently meant *use the default* |
| `pnk doctor` | shipped | environment, coherence, orphans, links, hooks, cache, heading coverage, edge hubs. **0.32.2:** the failures it lists are the ones still wrong, so its *“Fix them and re-run `pnk sync`”* remedy is no longer false advice to someone who just did that. **0.32.3:** a document present on disk but unreachable is no longer called an orphaned sidecar — so `--prune` is no longer offered a permanent id — and `doctor` no longer crashes on Python 3.13, the interpreter on which its own remedy was unreachable |
| `pnk install-hooks` | shipped | the three-hook split; all three force `--extract=pypdfium2` (0.3.0) |
| `pnk serve` | shipped | MCP: `pinakes_search`, `pinakes_get`, `pinakes_links`, `pinakes_list_kbs` |
| `pnk budget` | shipped 0.3.0 | I6b. Day/month/operation spend, `--resolve` for an unknown outcome |
| `pnk links` | shipped 0.5.0 | L4. What a document connects to and what connects to it: `--rel`, `--direction`, `--depth`, `--query`, `--json` |
| `pnk link` | shipped 0.6.0 | L6. Writes one `links[]` entry into the source document's own sidecar. Targets: a `pnk://` URI, `<alias>:<path>`, or a path in this KB |
| `pnk upgrade` | shipped 0.19.0 | T3. Prints the template diff and says, hunk by hunk, whether each change still fits your manifest. Exits `3` — *no baseline* — only on a KB stamped `notes@1.0`, which predates the version archive. **This read *"every KB that predates the version archive, which today is all of them"* until 20260831**, false since `notes` reached `1.2`: `_versions/` holds `1.1` and `1.2`, so a KB stamped `notes@1.1` gets a real diff — as both KBs in this repository do |
| `pnk upgrade --apply` | shipped, T4 | Writes the hunks that apply cleanly, `[budget]` included, after printing them; refuses the whole run if any conflicts. **The only thing in Pinakes that rewrites a `pinakes.toml` after `pnk init`.** Backs the file up to `pinakes.toml.orig`, prints any spending cap that would move with both values, and never writes `[kb] requires_pinakes` |
| `pnk ask` | shipped 0.23.0 | E1. The question surface, free: cited evidence, the confidence line, and **what answering would take** — one synthesis call at `high`/`medium`, decomposition and repeated search at `low`, and *cannot be told* on an uncalibrated KB. It never synthesises an answer and says so on every run. Every `pnk search` filter; `--json` adds `answer` (`null` until `--deep` fills it) and an `escalation` block. **Since E4 it also prices the run it offers** — the same estimate `--deep` is checked against, computed from package data, spending nothing, and degrading to no number rather than failing when the price table cannot be read |
| `pnk ask --deep` | shipped 0.24.0, **working since 0.25.1** | E4. **The one command that reasons, and the second of two that can spend.** The free retrieval is round 0: its confidence chooses the branch and its passages are the cheap branch's evidence. `high`/`medium` costs **one** synthesis call; `low` runs the loop — decompose, search each subproblem, answer from the merged evidence, re-fold, ask whether that is enough — and stops the moment it is; `unknown` runs the same loop with **no early stop** and names the bound that ended it. Priced and refused before the first call against all three `[budget]` windows at once, confirmed once, reserved and reconciled per call. Exit `1` when a paid run produced no answer. **Since 0.25.0 (E5) every paid run writes a transcript** — `.pinakes/deep/<operation_id>.json`, named in the output and in `--json`: the ledger stores no query text, so this is the only place on disk that says what a `pnk budget` row was for. Protected like a paid cache entry (nothing sweeps it, `--rebuild` and `--clear-cache` leave it) and removed only by `pnk sync --clear-cache=transcripts`. **Since 0.26.0 (E7) a run ends by printing the `links[]` entries its own citations propose** — two documents cited in support of one answer, offered as a sidecar fragment to paste and commit ([Suggested links](CLI.md#suggested-links)). It **prints and never writes**; `--write-suggestions` is deferred and unplanned (D-25 A). A run citing one document per call proposes nothing and prints no section |

| Capability | State | Notes |
|---|---|---|
| Markdown / text / code ingest | shipped | |
| **PDF ingest, free path** | shipped | `pypdfium2`, needs `pinakes[pdf]`. **Off by default — see the caveat below** |
| Extraction cache | shipped | `.pinakes/cache/extract/` |
| Page provenance (`page_start`/`page_end`) | shipped | in the index since 0.2.0, and surfaced in results on both surfaces since I8 |
| Extraction quality scoring | shipped | `make pdf-eval` against `tests/pdf-corpus/` |
| **PDF ingest, paid path** (scanned PDFs) | shipped 0.3.0 | I7b. `claude-vision` is a real extractor, **measured against the live API 20260729** — 1.000 on every metric over the synthetic scanned stratum, where the free path scores 0.000 ([DESIGN §9](DESIGN.md#9-known-risks)) |
| Budget estimator, caps, window aggregation | shipped 0.2.2, **live since I7b** | I6a. The pure logic alone — **nothing called it at 0.2.2**. `estimate_document` is called from I7b's extractor and `sync.py` now, and I6a's rest is read across the tree: I6b's accountant drives `reserve()` and `aggregate()`, `pnk doctor` reads `in_window`, and the deep estimator reads its ceilings |
| Deep paid client | shipped 0.24.0, reached by `--deep` | E3. `src/pinakes/deep/client.py` — the **second and final** entry on `.paid-path-allowlist`, and the module that builds a round's two calls: decompose, and answer. Reached by `pnk ask --deep` since E4, which builds its transport only once the caps have admitted the run. Two structural defences ship with it — a subproblem is a plain string because the schema has no other field it could be, and an answer cites **passage numbers**, so a citation naming evidence the call never had is refused. `pnk serve` never loading it is now a gate. `src/pinakes/paid.py` holds what both paid clients obey; it is deliberately **not** allowlisted, because it imports no client |
| Deep-round estimator | shipped 0.24.0 | E2. What one `pnk ask --deep` would cost, before the first call: the cheap branch's single synthesis call, a loop round, and `max_rounds x` a round for the whole operation. Pure — no client, no I/O, no wall clock. It waited on `main` for E4, which is what first made `--deep` real, and both cut in 0.24.0. **The free `pnk ask` calls it too**, to price the run it offers — which is why a free command reaches `pinakes.deep.estimate` and still never `pinakes.deep.client`, asserted in a fresh subprocess. At the shipped defaults the cheap branch is EUR 0.2627 and a three-round loop EUR 1.6872 — which is why E4 raised `per_operation_eur` to 2.00 and `daily_eur` to 6.00 (D-30): under the old 0.30 even a **one-round** loop was refused, on every KB the template stamps. **Every constant it prices with was measured against the live API in E6 and none was lowered** — 3.99x to 12.12x above their ceilings ([below](#the-deep-loop-measurement-run-has-been-done--20260821-02131)) |
| Budget ledger, `pnk budget`, the accountant | shipped 0.3.0 | I6b. `ledger.jsonl`, the reservation/outcome protocol, and I6a's decisions read from it — now driven by I7b's extractor |
| `path:page` citations | shipped | I8. `docs/paper.pdf:p7` / `:p7-8`, on the CLI and MCP alike; `pnk doctor` names the pages with no text layer |
| Cross-KB links (`pnk link`, `pnk links`, `pinakes_links`) | **shipped 0.6.0** — `pnk sync` records what other KBs link into this one (`--scan-links`), `pnk links` and `pinakes_links` traverse (0.5.0), `pnk link` authors, and `pnk doctor` reports link coverage as a ratio and resolves cross-KB targets (0.6.0) | 0.5.0 · 0.6.0 |
| Sidecar round-trip | **shipped 0.5.0** — `ruamel.yaml` in round-trip mode at YAML 1.2: comments, quoting, block scalars and blank lines survive a rewrite, and an unknown key's value is no longer reinterpreted | 0.5.0 |
| Template ecosystem | **shipped 0.21.0** — `pnk init --template`, `pnk upgrade` and `--apply`, the archive and its drift gate, and `pnk templates` to list what is installed. A template declares the files it writes (`files = [...]`). **Both gated increments are answered as of 20260811**: a second template is a **no-go** (its gate was run — every divergence in every real KB is a manifest value, which is a preset and not a template), and the `sqlite-vec` tier is **deferred behind a written trigger** rather than abandoned | the template release |
| `sqlite-vec` tier | **not built, and gated rather than scheduled** (T6) — `vector_tier = "sqlite-vec"` is **refused at load time** rather than accepted and ignored (T5). A KB setting it was already getting the NumPy tier; `vector_tier = "auto"` is the fix | the template release |

⚠️ **0.3.0 is the first release that can spend money — and it will not, unless you ask it to.**
Every earlier version had no paid code path at all. The first was the `claude-vision`
extractor, and reaching it takes a deliberate act: `EXTRACTION_BACKEND_DEFAULT` is `pypdfium2`, so
a KB spends only when its manifest says `[extraction] backend = "claude-vision"` or a command
carries `--extract=claude-vision`, **and** a real `PINAKES_ANTHROPIC_API_KEY` is in the environment. Absent
any one of those, 0.3.0 behaves exactly like 0.2.2. **There are two paid entry points today, not one** — `pnk ask --deep` has been the second since 0.24.0, and this paragraph read *"the only one now is the `claude-vision` extractor"* until 20260831 22:36. That is the sentence class 0.28.2 was cut to fix in `GUIDE.md` and `CLI.md`; the audit behind it never reached this file.

What stands behind that rather than merely asserting it: an enumerated allowlist
(`.paid-path-allowlist`) with four gates, the decisive one running the whole free path in a fresh
subprocess and asserting no paid client ever reaches `sys.modules`; every call reserved before it is
made and reconciled from the response's own usage; and caps that refuse rather than overspend.
Measured live on 20260729, the reservation over-reserved **11.5×** — wrong in the safe direction.
See [DESIGN §5](DESIGN.md#5-cost-control) and `pnk budget`.

Since I7a (0.3.0) that is enforced rather than asserted: `.paid-path-allowlist`
names every module permitted to import a paid client — two lines, since I7b and E3 — and four gates in
`check.sh` and CI hold it, the decisive one running the whole free path in a fresh subprocess and
asserting no paid client reached `sys.modules`. It found two real leaks the day it landed: both
`pnk doctor` and `pnk sync` reported a backend's availability by *loading* it, so a KB configured
for `claude-vision` imported `anthropic` on commands that cannot spend (fixed in the same
increment; no version ever shipped able to spend from them).

### Metadata injection: measured, answered, and shipped `off` — 0.16.0

**The investigation that ran for two days ended in a number.**
[`plans/20260805_1721-metadata-as-retrieval-context.md`](https://github.com/lucagattoni/pinakes/blob/main/plans/20260805_1721-metadata-as-retrieval-context.md)
asked whether `title` and `heading_path` are retrieval context. 0.16.0 is what it produced, and the
answer is **no — through one channel, on one corpus**.

| | |
|---|---|
| What was injected | `title > heading path`, section numbers stripped, into the text that is **embedded**. `chunks.text`, `char_start` and `char_end` untouched |
| Corpus | 195 RFCs, **43 353 chunks**, rebuilt in 44 min 45 s with 0 failures |
| Instrument | 110 questions, **authored blind** by six agents who had not read this repository, frozen and calibrated before any injection code existed |
| Result | **6 improved, 6 regressed, 84 unchanged** over 96 answerable questions, at `rerank = "none"` |
| Criterion, fixed in writing beforehand | strictly more improvements than regressions — **not met** |

**So `schema_version` stays at 3, and two expensive things are not being built:** PDF layout
heuristics and paid LLM title inference were both gated on this measurement showing movement. The
screen existed to make that call *before* the irreversible schema bump, and it did.

**Read the result as narrowly as it was measured.** Only the vector channel was injected; the
lexical channel needs the schema bump the screen declined. The claim is *"vector-only injection does
not help on this corpus"* — **not** *"metadata is worthless"*. What would re-open it is a corpus,
not a new idea about the prefix: this one's `lexical` and `simple-lookup` questions are saturated at
1.00, so all its statistical power sat in `paraphrase`.

**Why the null is trustworthy** — the controls, not the number: both legs proven to be the same
corpus (one sha256 over all 43 353 chunk texts, equal); the injection proven to have reached the
vectors (mean cosine 0.8398, zero unchanged); the uninjected index proven to still reproduce the
frozen baseline 110 rows out of 110. Without the second, a silent no-op and a true null would have
produced identical artifacts.

**`[chunking] metadata` ships anyway, default `"off"`**, so a KB whose questions are not solved by
BM25 plus a reranker can measure it rather than inherit this verdict
([MANIFEST](MANIFEST.md#chunking)). Turning it on is reported as drift and applied by
`pnk sync --rebuild`; a prefix that would not fit the model's window is refused per document rather
than silently truncated.

### Caveat: PDFs are off by default (but no longer silently)

`pnk init` stamps `include = ["**/*.md", "**/*.txt"]`, so PDFs need one manifest edit: add
`"**/*.pdf"` to `[sources] include` ([GUIDE](GUIDE.md#indexing-pdfs)). The generated manifest spells
out the glob and the extra it needs, and since 0.2.2 `pnk sync` names any file it skipped for want
of a pattern instead of reporting `0 indexed` and explaining nothing. It stays off by default
because `init` cannot see whether `pinakes[pdf]` is installed, and a glob stamped without it turns
every PDF into a failed document rather than a skipped one.

⚠️ **A template change reaches new KBs only.** The explanatory line above shipped in 0.2.2 and
appears in no KB created before it — so existing KBs stay PDF-blind permanently unless their owner
edits the manifest by hand. That gap, and what to do about it, is worked through in
[KB-UPDATES.md](KB-UPDATES.md), and two of its three halves are now closed. Its `requires_pinakes`
half **shipped in 0.6.0 (G4)** — a manifest can declare the oldest Pinakes that can read it, so an
out-of-date build says so instead of reporting a typo, closing the *diagnosis*. **Detection shipped
in 0.17.0**: `notes` moved to `1.1`, a CI gate keeps its version honest, and `pnk doctor` now WARNs
on every KB recording an older reference. **Measurement followed in T2**: where both versions are
archived, `pnk doctor` renders them both and reports how many lines separate them — but on a KB
recording `notes@1.0` it reports `cannot compare`, because that version's content was never
archived and never will be, so the KB in front of you is not one it can measure. **`pnk upgrade` shipped in
0.19.0** — it prints *which* lines differ and says, hunk by hunk, whether each change still
fits your manifest. On a KB recording `notes@1.0` it says `cannot compare` for the
same reason `pnk doctor` does, and exits `3`. **`--apply` (T4) closes the last part of this
caveat**: it adopts the hunks that fit, after printing them, refusing the whole run if any
conflicts. **It changes nothing for a KB recording `notes@1.0`** — there is still no baseline to
apply against, so that KB gets `cannot compare` and exit `3` under `--apply` too. Adoption started
working at the next template bump, which **E4 made**: `notes` is now `1.2`, so a KB stamped
`notes@1.1` has a real baseline and a real diff — the raised `[budget]` caps and the commented
`[deep]` block. It is also the first bump where `--apply` has something a user might genuinely
decline, since a cap is a value they may have chosen.

### The `[light]` backend is a flag on `pnk init`

`pnk init --backend light` stamps `fastembed` in **both** `[embedding]` and `[rerank]`; the default
is still `sentence-transformers`. **A flag rather than detection**, because `pinakes.toml` is
portable and committed and stamping the machine's installed extra bakes one author's setup into a
file their collaborators read. On an existing KB, or after omitting the flag, set `provider` in both
blocks by hand before the first sync ([GUIDE](GUIDE.md#choosing-a-backend)).

---

## v0.2 increment ledger

The build order is [`plans/20260727_1543-v0.2.md`](https://github.com/lucagattoni/pinakes/blob/main/plans/20260727_1543-v0.2.md). Each increment is a separate, bisectable
landing with its own tests.

| # | Increment | State |
|---|---|---|
| I1 | Extras, the extractor seam, core-only failure | shipped 0.2.0 |
| I2 | The synthetic hard-case PDF corpus and its generator | shipped 0.2.0 |
| I3a | Extraction core, pure — chars to ordered text | shipped 0.2.0 |
| I3b | The `pypdfium2` adapter, quality metrics, two fitted floors | shipped 0.2.0 |
| I4 | The extraction cache | shipped 0.2.0 |
| I5 | PDF chunking, page provenance, backend-aware sync (`schema_version` 2) | shipped 0.2.0 |
| I6a | Budget core, pure — estimator, reservation, `prices.toml` | shipped 0.2.2, inert **then** — live since I7b (see the surface table above). *The release-history rows below, and `docs/ROADMAP.md`'s 0.2.2 section, keep the bare "inert" on purpose: those record what 0.2.2 added, and it was true of 0.2.2.* |
| I6b | Budget I/O — ledger, prompt, `pnk budget`, hooks that cannot spend | shipped 0.3.0 |
| I7a | The paid-path allowlist gate and the invariant amendments | shipped 0.3.0 |
| I7b | The paid Claude-vision extractor — request shape, validation, retries | shipped 0.3.0 |
| I7c | The completeness audit, staging, all-or-nothing commit | shipped 0.3.0 |
| I8 | `pnk doctor` text yield, `path:page` citations on both surfaces, the three end-to-end traces | shipped 0.4.0 |
| I9 | The verification audit (`docs/VERIFICATION.md` + its gate), the untested-check sweep, README extras, wheel-smoke assertions | shipped 0.4.0 |

**Decided 20260728 17:52 — I6–I9 accumulate, and cut as one MINOR release.** `plans/20260727_1543-v0.2.md`
assumed a single release at I9; 0.2.0 was instead released after I5, correctly, since I1–I5 was
complete, self-contained, user-visible work the project's rule forbids leaving in `[Unreleased]`.
The remaining increments are **not** the same shape: I6a, I6b and I7a are each explicitly partial —
the budget core is pure logic nothing calls, and I6b's own title is "hooks that *cannot* spend".
They therefore stay in `[Unreleased]` until paid extraction is genuinely usable (I7b) and safe
(I7c), and that lands as **one MINOR bump — never a 0.2.x patch**, since a KB that can spend money
is new capability, not a fix. Patch releases in between remain available for work that stands alone
(0.2.1, the documentation restructure, was exactly that).

**Re-argued 20260728 23:42, once I6b was actually built — the decision stands, on a different
reason.** Its original premise was "none adds a capability a user can reach". That is now false in
one place: I6b shipped **`pnk init --ci`**, which writes a working GitHub Actions workflow for a
free KB and is gated on nothing. Held anyway, and the reason is narrow enough to be worth stating,
because it is the only thing keeping this out of a release:

> **`pnk budget` cannot produce a non-zero result on any KB in existence, and no user can change
> that.** It reads a ledger nothing writes until I7b. The project ships honestly-limited surfaces
> elsewhere — `pnk search` reports `confidence: unknown` by default and says why — but that limit
> lifts the moment *a user* calibrates. This one lifts only when *we* ship an increment. Making it
> the headline of a MINOR would ship a command whose output nobody can affect.

**Superseded 20260729 by I7b landing — that reason has now expired, and one narrower one remains.**
A user with a key can run a paid extraction today, so `pnk budget` reports real numbers and nothing
in this release is structurally vacuous any more. What holds it is no longer honesty about an empty
command but **safety**: I7c adds the completeness audit and the all-or-nothing commit, without
which a partially-extracted document can land in the index as though it were whole. Shipping a
spender before the thing that makes its output trustworthy is the wrong order, and it is the only
remaining reason.

The trade is unchanged and still named: `pnk init --ci` waits, and a user who wants it today can
copy the workflow out of [CLI.md](CLI.md#pnk-init).

**Trigger — if I7c slips or is deferred, cut the paid-extraction release immediately**,
documenting the audit's absence plainly. This is a bet on I7c landing soon, not a standing policy,
and it expires if that bet stops paying. (Its *number* is assigned when it is cut, per the naming
rule below — naming a number here is exactly the habit that rule exists to stop.)

### Cut as 0.3.0 — 20260729 04:17

Every reason for holding had expired by the time I7c landed: the budget command was no longer
structurally vacuous (I7b gave it real numbers to report) and the audit that makes a paid
extraction trustworthy was on `main`. The remaining question was never about the code — pushing the
tag publishes to PyPI, which cannot be re-uploaded or truly withdrawn, so it took a human saying
yes. That yes was given on 20260729 and the release was cut the same hour.

**It is a MINOR, never a patch**, and the reason is the ⚠️ above: a KB that can spend money is new
capability. What shipped is I6a–I7c together — the budget core and its ledger, `pnk budget`, the
paid-path allowlist and its four gates, the Claude-vision extractor, and the completeness audit
with all-or-nothing commit — plus the live measurement behind every number in
[DESIGN §9](DESIGN.md#9-known-risks).

**What it deliberately did not include.** `path:page` citations were still index-only and not
surfaced in results; the release therefore read scanned pages it could not yet cite precisely. That
gap was named here rather than discovered by a user, and **I8 closed it** (shipped in 0.4.0).

### The measurement run has been done — 20260729 03:17, €0.43

Steps (a)–(d) of [MEASUREMENT-RUN.md](MEASUREMENT-RUN.md), against the live API with
`claude-opus-5`, for **€0.43** — a tenth of the €4.23 worst case, which is itself a measurement of
how conservative the reservation is.

| What it settled | Result |
|---|---|
| Scanned quality — the reason the paid path exists | **1.000** char recall, order fidelity, word coverage; **0.000** junk. Free path: **0.000** on all four ([DESIGN §9](DESIGN.md#9-known-risks)) |
| The free-vs-paid delta on text-layer twins | Identical on 3 of 4. On a bordered table the paid path reads order **better** (+0.119) and adds **29% junk** ([§7.2](DESIGN.md#72-what-bypassing-layoutpy-on-the-paid-path-actually-costs)) |
| `PROMPT_TOKENS` | Measured 571 against an estimated 300 — **wrong in the unsafe direction**, now 700 |
| `PAGE_TOKEN_CEILING` | Measured ~1,574/page against a 6,000 ceiling. **Deliberately not lowered**: the corpus rasters are synthetic, and a real 300-DPI scan is the case they cannot represent |
| Reservation accuracy | Over-reserved **11.5×** on the first live call ($0.3515 → $0.0306). Safe, and exactly why reconciliation exists |
| The refusal branch | Fired for real. `headers-repeating.pdf` was refused twice, recorded as a document failure, and the other four extracted normally |

### The deep-loop measurement run has been done — 20260821, €0.2131

Steps (a)–(e) of [MEASUREMENT-RUN.md](MEASUREMENT-RUN.md#the-deep-loop-run), against the live API
with `claude-opus-5`, for **€0.2131** — a twenty-fourth of the €5.1836 worst case, which is itself
the result. Synthetic corpora throughout (`tests/demo-kb` and `tests/partner-kb`, copied): that is
E6's exit criterion and the reason no ceiling moved.

| What it settled | Result |
|---|---|
| Over-reservation, `synthesis` — the common case | **29.75×** — €1.0500 reserved, €0.0353 spent, 5 runs of 1 call |
| Over-reservation, `decomposition` — a calibrated loop | **50.92×** — €2.7600 reserved, €0.0542 spent, 2 runs |
| Over-reservation, `unknown` — an uncalibrated loop | **22.35×** — €2.7600 reserved, €0.1235 spent, 2 runs |
| The five input constants | 1.50× to 8.93× above their ceilings, each isolated by differencing real `count_tokens` requests. None lowered |
| `MAX_TOKENS` | 8,000 against a widest-observed **660** across 22 reconciled calls (mean 241) — **12.12×**, and most of the whole-run ratio, since output bills at five times input and dominates a round's price — two thirds under the shipped defaults, and **four fifths** at the measurement KB's narrower `final_k = 5` / `max_tokens = 120` geometry |
| The refusal branch | Fired for real, and **had never been run before**. Refused *before the first call* at exit 1, leaving no ledger row and no transcript — D-23 and E5's rule both hold |
| The runbook | Two defects in one step, both found by the free pre-flight it prescribes one paragraph earlier |
| The instrument | Five defects in `tools/deep_reservation.py`, which had no tests. Its `--json` had never once run |

**The calibrated loop is the most over-reserved, and that is the signal working.** A reservation
must cover `max_rounds`; a calibrated confidence signal is exactly what lets a run stop before
reaching them, so `decomposition` reserves the full loop and usually stops early while `unknown` —
which has no early stop by construction — spends closer to what it reserved. Both are reported
separately because a single blended figure would hide precisely that (D-28), and the cheap branch
is named as the common case.

**An earlier partial run published 19.0× and 16.5×. Those are withdrawn, not corrected** — their
measurement KBs were reaped from `/tmp` before anyone re-ran the report, so no surviving transcript
or ledger row supports them. **A measurement whose substrate lives in `/tmp` has a shelf life**, and
that number outlived it.

## The fixtures are now half recorded — 20260729 03:36, €0.26

The gap the measurement run left open is closed as far as it can be. Four branches — `happy`,
`short-slice`, `refusal`, `truncated` — carry bodies captured from the live API by
[`tools/record_claude_fixtures.py`](https://github.com/lucagattoni/pinakes/blob/main/tools/record_claude_fixtures.py). Every fixture now declares
its own `provenance`, so the set no longer makes one claim about a mixed collection
([the fixture README](https://github.com/lucagattoni/pinakes/blob/main/tests/fixtures/claude/README.md)).

The authored bodies were right about every branch's control flow and wrong about the response shape
in five ways no passing test could have revealed: the API returns the model **alias**
(`claude-opus-5`, not a dated snapshot), a text block carries `citations`, a response carries five
more top-level fields, `usage` carries seven more, and a refusal bills **1** output token rather
than 0. A sixth finding was a defect — a refusal arrives with a structured `stop_details` naming a
`category` and an `explanation`, and the extractor discarded both.

**What remains authored, permanently.** Ten fixtures encode the API *misbehaving* — a body that
violates the schema it was constrained to, a page array short of the slice, a leaked internal tag —
or a failure that cannot be induced without abusing a live service (429, 500, timeout). Each names
its own reason in `provenance.why_not_recorded`. This is not a backlog item: those bodies are
unobtainable by construction, and calling them "not yet recorded" would misdescribe them.

**One open question the recording raised.** `refusal-then-success` models a retry that has never
been observed to succeed — the same bytes refused twice with identical `stop_details`, which is
what a content-policy decision on fixed input should do. If that generalises, the refusal retry
spends a full input billing (~€0.04/slice) for nothing. It is n=1 on one document: enough to
record, not enough to change what the code spends.

✅ **The `0.3` collision is resolved — see [the naming rule](#release-roadmap)
below.** Unbuilt work no longer carries a version number anywhere, so nothing competes for `0.3.0`
and this release can be numbered whenever it is cut.

---

## Release roadmap

> # 🚫 Unbuilt work is named, never numbered
>
> **A version number belongs to a release when it is cut — never before.**
>
> Bodies of work that do not exist yet are referred to **by name**:
>
> | Name | What it is |
> |---|---|
> | **the template release** | Template ecosystem, `pnk upgrade`, the `sqlite-vec` tier |
> | **the graph release, staged** | The PPR graph channel and the `[ner]` extra — **eval-gated, never scheduled**. Not the same name as *the graph release*, which left this table at its final cut, 0.11.0 |
>
> **The deep release left this table at 0.26.0**, its final cut (D-9). `--write-suggestions` is
> deferred and unplanned; when it is planned it needs a name of its own, not the old one.
>
> **Never write `v0.4` for something unbuilt** — not in docs, not in `--help`, not in an error
> message, not in a code comment. Decided 20260729 00:09.
>
> **Why.** For months the docs used `v0.3` to mean the cross-KB links release. Then 0.2.2 shipped and
> the *next* MINOR was numerically 0.3.0 — so one number meant two different releases, and picking
> either one meant renumbering ~60 committed references, research records included. A number
> promised years ahead is a promise about ordering that the ordering itself keeps breaking. A name
> never collides, never needs renumbering, and says what the work *is* rather than when it arrives.
>
> Historical records (`CHANGELOG.md`, `docs/RETROSPECTIVES.md`, `plans/`, the dated research in
> `docs/graph/`) keep the numbers they were written with — they are records of what was decided at a
> time, and rewriting them would falsify that. Each carries a header note pointing here.

Rationale for the ordering is in [DESIGN §8](DESIGN.md#8-delivery-plan).

| Release | Adds |
|---|---|
| **0.2.0** ✅ | Free PDF ingest, extraction cache, page provenance in the index, extraction-quality scoring |
| **0.2.1** ✅ | Documentation restructure — one fact one home; three stale-claim fixes |
| **0.2.2** ✅ | `pnk sync` names files skipped for want of an `include` glob; budget core (inert) |
| **0.3.0** ✅ | Budget machinery, the opt-in paid Claude-vision extractor (I6–I7c) |
| **0.4.0** ✅ | `path:page` citations on both surfaces, `pnk doctor` text yield (I8); the verification table and its gate (I9) |
| **0.4.1** ✅ | A sidecar that will not parse is no longer overwritten by a freshly minted one, and no longer aborts the whole sync — data loss present since v0.1 |
| **0.5.0** ✅ *(the links release, interim)* | `pnk links`, `pinakes_links`, reverse-scan and the sidecar round-trip fix — no `schema_version` bump, so no rebuild. **The release cuts twice** (decision 27): this is the interim MINOR at L5b; the final cut is at L8, and the name stays in the unbuilt-work table until then. **L1 landed:** the partner corpus, sparse authored links in both, and the density gate. **L2 landed:** reverse-scan writes inbound rows and `kb_refs`, with a freshness window and `--scan-links`. **L3–L5 landed:** the bounded traversal core, `pnk links`, and `pinakes_links` on the MCP surface. **L5b landed:** `ruamel.yaml` replaces `pyyaml` in the sidecar, so a rewrite preserves comments, quoting and blank lines — and `country: NO` stops becoming `false` ([decision](https://github.com/lucagattoni/pinakes/blob/main/plans/20260731_0602-decision-ruamel-yaml.md)). |
| **0.6.0** ✅ *(the links release, final)* | `pnk link` authors a link from the command line, and `pnk doctor` reports link coverage as **linked docs / total docs** and resolves each cross-KB target through its `[[links.kb]]` entry (L6–L8). Also `[kb] requires_pinakes` (G4) and the evaluation's tie-ordering fix (G1) — no `schema_version` bump, so no rebuild. **This completes the two-cut release** decision 27 describes: 0.5.0 was the interim MINOR at L5b, this is the final cut, and the name leaves the unbuilt-work table here |
| **0.7.0** ✅ | The evaluation grows a per-question artifact (`eval/outcomes.json`), stable question ids, a validated `kind`, and an empty golden set that skips with a reason instead of failing — plus the demo KB's golden set grown 41 → 74 with a `simple-lookup` control class (G2). **Its deliverable is a measurement:** the graph release's gate could not be reached on `tests/demo-kb`, so G3 and G5 did not start then — the RFC realism corpus cleared it on 20260804 ([above](#can-the-graph-releases-gate-be-reached--yes-measured-20260804)). No `schema_version` bump, so no rebuild |
| **0.7.1** ✅ | `[sources] include` can no longer walk out of the KB or write sidecars outside it — three defects live since before 0.5.0: a `..` pattern indexed files outside and minted sidecars beside them, an absolute pattern was a bare traceback, and a symlinked directory carried the walk out with no `..` anywhere. Plus a document reached by two legal spellings is now one document, and `tools/link_density_gate.py` survives a non-canonical root |
| **0.8.0** ✅ | **Breaking, paid path only:** the Claude-vision extractor's key is `PINAKES_ANTHROPIC_API_KEY` and is passed to the SDK explicitly — no fallback to `ANTHROPIC_API_KEY`, which the SDK used to read out of whatever environment it was handed. Rename the variable in your `.env`. Also `[budget]` defaults raised (`per_operation_eur` 0.05 → 0.30, `monthly_eur` 5.00 → 30.00), a `check.sh` gate pinning `docs/STATUS.md`'s own header to `__version__`, the reachability probe refusing a golden set it cannot measure rather than absorbing it, and sixteen documentation claims corrected against the code. No `schema_version` bump, so no rebuild |
| **0.9.0** ✅ | **Documentation only — no code path changed.** `docs/` is now published as a site at [lucagattoni.github.io/pinakes](https://lucagattoni.github.io/pinakes/), built with `mkdocs build --strict` on every PR and deployed on every push to `main`; the strict build found and fixed 31 dead links and anchors in the existing docs. The repository moved to `github.com/lucagattoni/pinakes` (GitHub redirects the old URL) and prose across the repo now writes the project name **Pinakes**, while every identifier — the PyPI package, `pinakes.toml`, `.pinakes/`, `pinakes[st]`, `pinakes_search`, `requires_pinakes` — stays lowercase and unchanged. Also a per-kind edge census in `tools/reachable_ceiling_probe.py`. No `schema_version` bump, so no rebuild |
| **0.10.0** ✅ | An interrupted first sync no longer reads as a model mismatch: `pnk doctor` reports `WARN sync completeness` with remedy `pnk sync`, instead of `FAIL` with `--rebuild` — which discarded every embedding the interrupted sync had already written. `pnk sync` also prints live progress on a terminal (documents done/total and a rate, one self-overwriting line, silent when piped or `--quiet`), after a 300-document run took over two hours with no output. And `sync.py`'s timestamps are UTC, matching `lock.py`'s — the two used identical formats on different clocks, so a lock taken seconds ago could read hours old. No `schema_version` bump, so no rebuild |
| **0.11.0** ✅ *(the graph release)* | **Breaking for every existing KB: `schema_version` 3, so the first `pnk sync` after upgrading rebuilds the whole index.** There are no migrations, by design; `pnk sync --rebuild` is the remedy the refusal prints, and it is free. What it buys: a derived structural graph — a `nodes`/`edges` table over chunk, document, tag, per-document heading and directory nodes, with every shared-value relation through its hub (G3) — and `pnk doctor` reporting the highest-degree hubs (G6). **The expansion channel (`[retrieval] graph_channel`) ships `off` and its golden-set gate is why** (G5): run on the RFC realism corpus it improved 0 multi-hop questions and regressed 3, licensing p = 1.0000 ([the numbers](#did-the-expansion-channel-earn-its-default--no-measured-20260804-2252)). Nothing was tuned after seeing that. The finding is `reachable ≠ retrievable` — a reachability probe called 9 of those questions liftable and the retrieval instrument lifted none |
| **0.12.0** ✅ | **`pnk doctor` reports heading-path coverage and warns when a whole source type carries none** — the check that would have caught the RFC realism corpus indexing 106 806 chunks with not one heading path, which is what bounds 0.11.0's expansion-channel gate: three of the seven edge kinds derived zero edges on it. Total absence across a source type is the predicate, not a fitted share, and the remedy distinguishes *the chunker cannot extract one for this type* from *this Markdown uses another heading convention*. Also: the missing-backend error names an installed alternative and the two manifest lines to flip, instead of prescribing the 2 GB install a `[light]` user chose to avoid; `pnk doctor` no longer prints the operator's home directory; and `tools/measure_sync_cpu.py` measures how many cores a command keeps busy, sampling the whole process tree because watching the launched pid read 0.0 cores for a one-core load behind `uv run` |
| **0.13.0** ✅ | **Plain text can carry a heading path.** `[chunking] headings = "numbered"` reads a dotted-decimal outline into `heading_path` — opt-in, `text` only, and it **refuses rather than guesses**: the numbers must form a valid outline walk across the whole document, and if the walk fails anywhere that document yields no headings at all rather than a partial labelling. **Measured against 980 real RFCs in doubling rounds** ([§5.4](https://github.com/lucagattoni/pinakes/blob/main/plans/20260805_1721-metadata-as-retrieval-context.md)): 644 accepted overall and **314 of 314 modern-era documents, 100% at every round size**. Two clauses were added from that measurement and two more were tried and rejected by it. Also: a `[chunking]` edit is no longer a silent no-op — the index records what it was built under, and both `pnk sync` and `pnk doctor` say so — and `tools/build_rfc_corpus.py` makes the corpus reproducible instead of local to one machine |
| **0.14.0** ✅ | **`pnk doctor` stops crying wolf, and `pnk init` stops refusing the normal way to start a KB.** Heading coverage now WARNs only for `markdown` at 0% — the one case a user can act on — and reports the rest as OK with a note that separates *`text` can carry one*, *`text` was offered and refused*, and *`code`/`pdf` cannot today*. `pnk init` **adopts a directory that already has content** and never overwrites a file it finds there, so cloning a repo and initialising inside it works; an adopted `.gitignore` missing `.pinakes/` is flagged with the line to add. A new `titles` check counts documents still carrying the filename-minted title — a nudge, never a warning, because both committed corpora sit at 100%. Also settled by measurement rather than argument: **the first sync is not single-core** (peak 5.0, mean 4.8 of 10 under `fastembed`), so the document loop stays serial |
| **0.15.0** ✅ | **A Markdown document is titled by its own `# ` heading.** `sync` had never read one — `skeleton()` was called without `title=` at both sites, so the filename stem always won, and the two usually differ only in capitalisation (`# Access restrictions` beside `title: access restrictions`), which is why it went unnoticed. A file called `rfc9110-notes.md` opening on `# HTTP Semantics` is now titled *HTTP Semantics*. An H1 is an authored marker, not a guess — the first-line heuristic stays rejected. Markdown only, fence-aware, `##` excluded, and **no migration**: titles are minted only when a sidecar is created, so every existing KB keeps what it has |
| **0.15.1** ✅ | **Every timestamp Pinakes writes is UTC — the last three naive-local sites are gone.** `pnk init` stamped `[kb] created` from the machine's wall clock, the paid extractor priced a document against a local `now`, and `pnk doctor`'s price-age check subtracted a naive local clock from a price table whose `as_of` is authored in UTC. `sync`, `lock`, the ledger and the accountant were already UTC, which is what made the remainder a **mixed** scheme rather than a consistent local one — the worse of the two, because two stamps in the same index no longer shared a zero point. Pinned by a test running under `TZ=Pacific/Kiritimati` (UTC+14), where a naive stamp lands on a *different date* for ten hours of every day, so the failure is loud. **`[budget] timezone` is untouched and is not an exception**: it decides where a *daily* or *monthly* window starts, and the ledger still stores UTC and converts at read time. Also documentation: `CLAUDE.md` 273 → 191 lines into [`docs/BUILDING.md`](BUILDING.md) and [`docs/INVARIANTS.md`](INVARIANTS.md), with 21 pointers across the tree re-aimed at the new homes |
| **0.16.0** ✅ | **Is document metadata retrieval context? Measured — and no, through one channel on one corpus.** `title > heading path` injected into the **embedded** text of a 195-document, 43 353-chunk RFC corpus, scored against a blind-authored, frozen 110-question golden set: **6 improved, 6 regressed, 84 unchanged**, against a criterion of *strictly more improvements than regressions* fixed in writing beforehand. **`schema_version` stays at 3**, and PDF layout heuristics and paid title inference — both gated on this — stay unapproved. `[chunking] metadata` ships **default `off`** so another corpus can be measured rather than inherit the verdict, with a per-document refusal instead of the silent truncation an over-long embedding input otherwise gets. Also `tools/two_leg_gate.py`, which refuses to compare two eval legs differing in anything but one named key — `graph_gate` compared five header fields and not `chunking`, so two legs chunked differently compared clean — **the three-leg gate kept that gap until 0.21.1 closed it**. **And five silent-failure fixes its own adversarial review found in it**, the sharpest being that on every index built before this release, turning injection on was completely silent: absent identity keys read as *unknown*, so `pnk sync` reported nothing, nothing re-embedded, and `pnk doctor` printed `OK chunking coherence` over uninjected vectors |
| **0.17.0** ✅ *(the template release, interim)* | **A template version finally means something, and a gate keeps it meaning it.** `pnk doctor`'s template check has existed since 0.1 and could never fire: `notes` declared `version = "1.0"` in every commit since it was written while the files that version denotes changed in ten later ones, so every KB recorded `notes@1.0`, the installed template was also `notes@1.0`, and `doctor` printed `OK` over eleven different template contents. `notes` is now **1.1**, so **every KB in existence now reports `WARN template: KB says notes@1.0, installed is notes@1.1`** — the intended effect, not a side-effect. Nothing is applied automatically and no KB needs changing; the WARN does not change `pnk doctor`'s exit code. A template's content is archived under `src/pinakes/templates/<name>/_versions/<version>/` and travels in the wheel, with `templates/_versions.toml` recording each file's SHA-256 — without it nothing on your machine could say what `notes@1.1` *meant*, which is why `pnk upgrade` could not have worked. **`1.0` is deliberately not archived**: it denotes eleven contents, so any single answer would be wrong for ten of them. `tools/template_drift_gate.py` (seven legs, in `check.sh` and its own `template-drift` CI job) makes editing a template without bumping its version a red build, and reports which mode it ran in because a skip is not a pass. Also `pnk init --template` refuses a name that is not a single path component — `notes/../notes` and `../templates/notes` both resolved to a real template before. No `schema_version` bump, so no rebuild. **The release cuts more than once** (D-9): this is the interim MINOR at T1, and the name stays in the unbuilt-work table until the final cut |
| **0.18.0** ✅ *(the template release, interim)* | **The drift warning every KB now prints says something you can act on.** 0.17.0 made `pnk doctor` WARN on every KB in existence; this makes that WARN useful. Where both versions are archived it renders **both** through one context and reports how many lines separate them — **template against template, never template against manifest**, so nothing you wrote is in either side: a value you tuned that the template *renders* cancels on both, and a literal you edited enters neither, because neither side is your file. A report mixing the two could not tell a template change from your own tuning. **On every KB that exists today it says `cannot compare`**, because `notes@1.0`'s content was never archived and never will be — and the remedy says so, names the comparison available now (`pnk init` a throwaway directory and diff), and **promises nothing a later release cannot keep**: an unarchived version's content is gone, not pending. A bump that leaves the manifest alone reports `same manifest`, never `0 lines differ` — a template version covers four files and this reads one of them, and of the ten commits between `notes@1.0` and `1.1`, five touched only the starter golden set. A template needing a variable this build cannot supply is one `WARN` row naming the version and the variable, not a traceback and not the end of the report. No `schema_version` bump, so no rebuild. **Interim MINOR at T2** (D-9); the name stays in the unbuilt-work table until the final cut |
| **0.19.0** ✅ *(the template release, interim)* | **`pnk upgrade` prints the lines themselves.** 0.17.0 made every KB warn and 0.18.0 said how far it had drifted; this says *what* changed — the diff between the template version your KB records and the one installed, both rendered from the archive through one context, so nothing you wrote appears in it as a change. Each hunk is then placed against your manifest with **three** answers, not two: *applies cleanly*, *already applied* and *conflicts*. It writes nothing. Exit **`3`** is new and means *no baseline* — the comparison could not be made and no action of yours would make it possible — which is what **every KB in existence** gets, because `notes@1.0`'s content was never archived. No `schema_version` bump. **Interim MINOR at T3** (D-9); the name stays in the unbuilt-work table until the final cut. *(This row was missing until 0.20.0's sweep added it — 0.19.0's own sweep updated line 3, the command table and the PyPI list and skipped the ledger.)* |
| **0.20.0** ✅ *(the template release, interim)* | **`pnk upgrade --apply` adopts the changes that fit, after showing you all of them.** It writes every hunk that applies cleanly, skips the ones already in your file, and **refuses the whole run if any hunk conflicts** — a half-upgraded manifest with no record of which half is worse than an unupgraded one. It is the **only thing in Pinakes that rewrites a `pinakes.toml` after `pnk init`**, and it is bounded by what it printed: nothing reaches the file that was not on screen first. **A `[budget]` default applies like any other change** (D-10) — so both commands print any spending cap that would move, with the old value and the new one, under their own heading, and print it **only** when one really would move. Your previous manifest goes to `pinakes.toml.orig`, named in the output together with the warning that nothing ignores it. It re-reads what it wrote and restores the original if it does not load; refuses while a sync holds the KB; refuses a manifest whose line endings are not uniform, preserving a uniformly CRLF one; writes **through** a symlinked manifest rather than replacing it; and keeps the file's own permissions. It **never** writes `[kb] requires_pinakes` (D-11) — it names the keys a hunk introduced and leaves the floor to you, because nothing here maps a manifest key to the release it arrived in. It never syncs or re-chunks; an applied key your index was built under is named, with `pnk sync --rebuild`. A conflict now carries **two** exit codes: `0` from the report, which has nothing to fail at, and `1` from `--apply`, which was asked for a write it could not make. `cannot compare` stays `3` under `--apply`, so **nothing changes for a KB recording `notes@1.0`** — adoption starts working at the next template bump. No `schema_version` bump. **Interim MINOR at T4** (D-9) |
| **0.20.1** ✅ *(the template release, interim)* | **`vector_tier = "sqlite-vec"` stops lying.** The value named a tier that is not built, and was accepted anyway: `pnk sync` stamped `numpy` into the index's `meta` whatever the manifest said, `search` never read the field at all, and `pnk doctor` said nothing — silent on all four surfaces a user could check. It is now **refused at load time**, so a KB setting it stops loading entirely, on every command rather than only on search. **The one-line fix is `vector_tier = "auto"`, and it changes nothing about how that KB behaves** — it was already getting the NumPy tier. The error names the tiers that are built and points here. The value returns when the tier does; its removal is a fix, not a decision against it. Second half: the index's `vector_tier` is written from `search.resolve_tier()`'s return rather than a literal, so one function answers which tier ran. **A PATCH carrying a documented config break, deliberately** (D-12), on this project's own 0.7.1 precedent — the previous behaviour *was* the defect. **D-4 taken as option A at T5**: the judgement it turned on was already settled one line below `VECTOR_TIERS`, where `graph_channel` refuses `"ppr"` for the same reason. No `schema_version` bump |
| **0.21.0** ✅ *(the template release, interim)* | **A template says what it installs, and you can finally ask what is installed.** `pnk templates` lists every template this build can stamp a KB from — name, version, description, `--json` — which until now was reachable only by naming a template that does not exist and reading the error. It takes **no `--kb`**: the answer is a property of the install, not of a KB. **CLI-only, decided 20260808** — no `pinakes_*` tool, because the MCP server answers about the KBs it was pointed at and creation has no MCP surface at all, so such a tool would list templates its caller cannot use. Second half: `template.toml` gains **`files = [...]`**, replacing the hardcoded `README.md` / `eval/questions.yaml` pair — **an absent key still means exactly those two**, so `notes` and every third-party template written against an earlier build behave identically. An entry is refused if it names the `_versions/` archive (containment cannot catch that one: it lands *inside* the KB), if it writes outside the KB, or if it reads outside the template — and every entry is checked before any entry is written, so a bad declaration leaves no half-stamped KB. The drift gate folds `files` into its content hash, closing a hole this increment opened: `template.toml` is otherwise excluded, so the one key deciding what a KB is stamped with would have sat outside the check that exists to stop stamped content changing without a version bump. Absent contributes nothing, so **every hash published before 0.21.0 is unchanged** and no ledger row needed migrating. Also: a damaged template is now named as an `unreadable` row instead of aborting the listing as a traceback. No `schema_version` bump, so no rebuild. **Interim MINOR at T7** (D-9) — **T6 (the `sqlite-vec` tier) and T8 (a second template) are gated, not scheduled**, so the name stays in the unbuilt-work table |
| **0.21.1** ✅ | **A damaged template says so, and a gate reads what its legs were chunked under.** Two open corrections — the two of six that had a stated *required* text and so could be taken rather than decided; the four left each need a fork picked. `tools/graph_gate.py` now compares the `chunking` block, which `eval.header` records so a leg can say what it was built under: two legs chunked differently are **two corpora**, so rows paired on `id` came from searching different texts and the rechunk is reported as whatever was under test — measured, `max_tokens` 510 against 480 moves 63 of 1 858 chunk texts on one RFC, and this is the gate that licensed the graph channel's default. And every read of a template's own files is guarded, on **five** functions rather than the two the record named — `render_manifest`, `declared_files` and `copy_extras` held the identical unguarded read, and `jinja2.TemplateSyntaxError` needed its own arm because it is raised by `Template(...)` and not by `render`. **The fix came within one handler of opening its own replacement**: making the failure a `PinakesError` routed it into an `except` `pnk doctor` and `pnk upgrade` already had, one answering *"is not installed here"* about a template sitting right there and merely damaged — nothing went red, both surfaces still returned WARN and exit 3. `TemplateNotInstalledError` splits them. A third pass found the `OSError` arm printing the install's absolute path, the same class as the closed home-directory leak one module away. No `schema_version` bump, no rebuild |
| **0.22.0** ✅ | **Eight decisions, and two of them were never decisions.** Both gates of the template release are answered — **a second template is a no-go** (its gate was run: every divergence in every real KB is a manifest value, which is a preset), and the `sqlite-vec` tier is **deferred behind a written trigger** rather than abandoned, because a passing gate could not show the tiers agree at 100k. **The open-corrections list is empty for the second time in its life.** `pnk init` validates a template's declaration before it creates anything; `--apply` records the reference on the *same manifest* outcome and says so first; an eval header records the tier that ran beside the one asked for; `--rebuild` re-chunks a paid document from the extraction cache and, when the cache is cold, keeps its chunks and records the index as inhomogeneous — **a rebuild never spends**, counted rather than claimed. New: `pnk init --backend` (`st` or `light`), which is the answer T8's failed gate pointed at. And the release workflow finally creates the GitHub release. **Two of the four corrections had stood behind premises that were simply false**, both refuted by running the code they described. No `schema_version` bump, no rebuild |
| **0.22.1** ✅ | **Documentation only — no code path changed.** `docs/ROADMAP.md`'s two prose blocks said 0.21.0 while every table in the same file said 0.22.0: *Where things stand right now* was stamped 20260808 06:41, and § *The template release* still read "T4 and T7 are still to come" about increments that shipped on 20260808. **A release sweep is table-shaped** — the row being added points at itself, so it is written every time, while a paragraph summarising *all* releases has no row to add. Five sweeps left the summaries behind and every enumeration correct, which is the worst arrangement: a reader checking one against the other finds agreement five places out of six. The second instance had no wrong text to find at all — `docs/README.md`'s plan-routing table had **no row** for `plans/20260811_0720-decisions-gates-and-corrections.md`, the plan `CLAUDE.md` names as the live build order. **A missing row is invisible to every check that reads rows.** Both fixed, `CLAUDE.md`'s live-plan pointer now says its build order is built out, and `docs/RELEASING.md`'s sweep table gained the two checks that would have caught this class: grep the tree for the *previous* version number, and read `ls plans/` against the routing table. Also recorded: the 20260807 audit's **40 documentation corrections are untouched**, and it deferred a full ROADMAP review until after T2 (shipped 0.18.0) that is still owed |
| **0.22.2** ✅ | **A row can be complete, correct, and in the wrong place.** Five release rows were out of order across three sequences — `docs/ROADMAP.md`'s release table and its per-release sections both read `0.20.0, 0.22.0, 0.22.1, 0.21.1, 0.21.0, 0.20.1`, and `docs/STATUS.md` put `0.15.1` after `0.16.0` and `0.20.1` after `0.22.1`. Every one is wrong on **both** readings, SemVer and release time. Nothing could see it: ordering is a property of the *sequence*, not of any row, and every check here reads rows — the tables were complete, every anchor resolved and `mkdocs build --strict` was green. **`0.21.0`'s sweep inserted its section one position too early and the next three used that same slot**, so after the first error the tail read strictly newest-first and each following sweep matched the coherent pattern around its own edit. Only the join between the ascending head and the descending tail was wrong, and no sweep's diff touched that line. The `0.15.1` instance was already in the 20260807 audit, verified, and sat unworked for four days while three sweeps added three more. **`tools/release_order_gate.py` now gates all five sequences** in `check.sh` and CI — direction declared per sequence rather than inferred, since a scrambled file would otherwise elect its own answer, and a sequence below a count floor fails rather than passes, because an empty sequence is sorted by definition. Also: ROADMAP's Part 4 heading claimed it ends at `0.10.0` while holding every release through `0.22.1`. **No code path changed** — no `schema_version`, no rebuild |
| **0.23.0** ✅ *(the deep release, interim)* | **`pnk ask` exists, and it will not pretend to answer you.** The question surface, free: the same pipeline and the same filters as `pnk search`, plus the thing `search` does not say — **what answering the question would take.** One synthesis call at `high`/`medium`, decomposition into subquestions and a search for each at `low`, and *cannot be told from here* on a KB with no fitted `[retrieval.confidence]`, which is **every KB the template stamps** (D-22: it runs anyway, bounded by the caps rather than by the signal, and says so). Every run states plainly that **no answer was synthesised** — passages are not an answer, and `ask` is the easiest place in Pinakes to mistake one for the other. `--json` is `search`'s payload plus `answer: null` and an `escalation` block, so one schema parses whether or not a paid loop ever runs. **Nothing printed anywhere names `--deep`**: a flag that parses and then apologises is the defect `0.20.1` fixed for `vector_tier`, and one merely advertised is the same lie a layer out — so `--deep` is a usage error until E4 builds it, and `pnk search`'s own notice, which had pointed at `pnk ask --deep` in the very sentence whose test is named for not naming a command that does not exist, now names `pnk ask`. The free-path gate covers the new command **from this increment**, before any paid module exists, and covers it by matching its output — no module row could tell that call from `pnk search`'s. Also in this release: the deep-release plan itself and its eight decisions, the release-order gate (`tools/release_order_gate.py`), and two STATUS corrections about a wedged CI run. **No `schema_version` bump, no rebuild, and no paid code** — E1 adds no allowlist entry and no dependency. **Interim MINOR: the release name stays in the unbuilt-work table** (D-9) — E2 to E7 are still to come |
| **0.24.0** ✅ *(the deep release, interim)* | **`pnk ask --deep` answers, and says which bound stopped it.** The loop: round 0 is the free retrieval, its confidence chooses the branch, and `--deep` always answers because typing it *is* the decision to spend (D-28). `high`/`medium` costs **one** synthesis call; `low` decomposes, searches each subproblem, answers from the merged evidence, re-folds what was established and stops the moment that is enough; `unknown` runs the same loop with **no early stop** — the step that would end it is the missing signal — and names the bound that did (D-22 E). Priced before the first call and refused against all three `[budget]` windows at once with the exact manifest edit; `confirm_above_eur` put once; every call reserved and reconciled. A halt mid-loop honours `[budget] on_exceed` (D-23 A), and a paid run that produced no answer **exits 1**. **The default caps rise — `per_operation_eur` 0.30 → 2.00, `daily_eur` 1.00 → 6.00 — because even a one-round loop exceeded the old one** (D-30), so `notes` is **1.2** and every existing KB keeps the caps it stamped and meets a refusal that carries the whole remedy. `[deep]` arrives with `model` and `max_rounds`, settable and unstamped. E2's estimator and E3's client, unreleased since 20260811, ship here. **Two money defects found on the way**: a Ctrl-C mid-request voided a call that may have billed, in *both* paid clients; and a failure between a response arriving and its reconciliation did the same. **No `schema_version` bump and no rebuild.** **Interim MINOR: the release name stays in the unbuilt-work table** (D-9) — E5 to E7 are still to come |
| **0.25.0** ✅ *(the deep release, interim)* | **A paid run leaves a record of what it was asked.** E5: `.pinakes/deep/<operation_id>.json`, written by every `pnk ask --deep` that returns and named in the output and in `--json`. **The ledger stores no query text by design** (DESIGN § 5) and that rule is unchanged — the transcript is a *second* file beside it, which is what makes a `pnk budget` row explicable after the fact and what survives a cron run's pipe closing. It holds the question, the filters as typed, the confidence reading that chose the branch, the prompt and schema versions, and the answer object `--json` prints — **from one renderer, so stdout and disk cannot drift**. Filed under the `operation_id` the ledger groups its calls by, so a row and its file meet without searching; the name is validated as a ULID, so nothing caller-supplied can name a directory above it. **Protected exactly as a paid cache entry is** (INVARIANTS, now three protected things rather than two): nothing sweeps it, `--rebuild` leaves it, and `--clear-cache` — bare or `=paid` — clears the extraction cache whole and does not touch it. **`--clear-cache=transcripts` is the one thing that removes it**, and it names a *store* rather than a third authorisation, because a spelling that also emptied the cache would destroy more than it names. Written for a run that **returned**, answer or not — a refusal, a decline and an `on_exceed = "abort"` halt write none, since `abort` discards the rounds already paid for. `--json` also gains `answer.call_ids`, the ledger's join key. **No `schema_version` bump and no rebuild.** **Interim MINOR: the release name stays in the unbuilt-work table** (D-9) — E6 and E7 are still to come |
| **0.25.1** ✅ *(the deep release, fix)* | **`pnk ask --deep` works against the live API — it never had.** Found by E6's measurement run on the first real call it made: every answer call carried `{"type": "integer", "minimum": 1, "maximum": passages}` and every decompose call an array `maxItems`, and structured outputs accepts neither, so the API returned `400` **before the request billed** — every `--deep` invocation in 0.22.0 through 0.25.0 failed, at a cost of €0.00, and the accountant voided each reservation exactly as designed. The citation bound is **kept, not dropped**: `enum: [1..passages]` states what `minimum`/`maximum` stated and is accepted and honoured, so E4's two halves both survive — the schema constrains what the model may emit, `parse_answer` re-checks it where it is read. The subproblem cap has no such form (structured outputs has no array-length keyword) and now lives in the prompt body and `parse_subproblems`, which were always its real enforcement. **Why four releases of green tests missed it:** every test drives the loop from recorded fixtures through the `Transport` seam, so no test had ever sent a schema to the API — the one field the API validates and a fixture cannot exercise. The gate is now a recursive shape assertion over both builders against the documented unsupported keywords: no key, no network, no fixture. `SCHEMA_VERSION` is **2**; **no `schema_version` bump and no rebuild** — that constant is the deep response shape, not the index's. **The release name stays in the unbuilt-work table** (D-9): E6 and E7 are still to come |
| **0.25.2** ✅ | **Documentation only — the guidance carries the retrospectives' recurring lessons.** `docs/BUILDING.md` gains the mutation-harness discipline (commit before mutating, every anchor asserted to match exactly once, `__pycache__` cleared between mutants, no `-x`, one known-catchable kill first), the gate-exit-status rule, the CI-matrix leg check and two rules for reading a plan; `docs/RETROSPECTIVES.md` § *Start here* gains four rows routing the post-20260801 failure classes; `CLAUDE.md` names which corpus can license a retrieval change and slims its live-plan block to pointers, the deep plan's E6 status moving into the plan itself; `plans/` gains the `tools/mutate.py` proposal |
| **0.25.3** ✅ *(the deep release, interim)* | **E6: the deep loop's reservation is measured.** The run published the over-reservation factor — **29.75×** on the cheap `synthesis` branch, **50.92×** and **22.35×** on the two loop branches — and gave every constant in `deep/estimate.py` its measurement and the command that produced it. **No ceiling was lowered**: the corpus is synthetic, which is E6's own exit criterion. Six defects fixed in `tools/deep_reservation.py`, which had no tests and whose `--json` had never once run; the sharpest priced an *unresolved* ledger call at its reservation under a header claiming `reconciled ledger spend`, moving the published figure from 29.75× to 4.40× at exit 0. It now has 27 tests, mutation-verified 10/10. Two defects fixed in the runbook itself, both found by the free pre-flight it prescribes. **No `schema_version` bump, no rebuild, and no product behaviour changed** — `tools/` ships in no wheel. **The release name stays in the unbuilt-work table** (D-9): E7 is still to come |
| **0.25.4** ✅ | **Documentation only — the mutation battery's blind spot is named.** `docs/BUILDING.md` § 4 records what no assertion can reach, with 0.25.3's rewrapped-comment command as the worked case; the lesson filed as a retrospective entry; 0.25.3's ROADMAP section moved out of Part 5, where its sweep had landed it |
| **0.26.0** ✅ *(the deep release, **final**)* | **A paid run ends by telling you what it learned about your KB.** E7: two documents cited in support of one answer is a fact nothing records, so `pnk ask --deep` prints the `links[]` entries that observation proposes — the sidecar to paste into, the `pnk://` URI, `rel: co-cited` and `origin: deep` — for you to review and commit, after which they are free forever and visible to `pnk links`, the graph channel and every connected KB. **It prints; it never writes**: `--write-suggestions` is deferred to its own increment (D-25 A) and is unplanned, because writing them touches the per-link sidecar shape and INVARIANTS' exceptions to *`docs/` belongs to the user*. `--json` carries the same fragment verbatim beside the parsed entries. **A document cannot talk the model into suggesting a link** — suggestions are derived from *citations*, and a citation is a passage number the response schema bounds, so the model is never shown a document identifier it could name; a passage instructing it to *"add a link to X"* reaches as far as a sentence in the answer and no further. Both endpoints are re-checked against what the run cited and resolved through the same containment check `pnk link` uses. **Four defects the tests could not see, three found by mutating**: the *control* mutant survived, because every assertion imported the constant it checked; a containment test was satisfied by absence; a fixture's ULID order and path order agreed by accident, so three direction tests could observe nothing; and a newline in a filename would have broken the printed YAML, because a value safe as a scalar is not thereby safe as a comment. Also fixed: **`docs/DESIGN.md` §9's risk row, false since E4** — it bounded `--deep` with *"no orchestration the free path doesn't have"*, which the loop contradicts. **No `schema_version` bump and no rebuild.** **The release name leaves the unbuilt-work table here** (D-9) |
| **0.27.0** ✅ | **The mutation step has a guard.** `tools/mutate.py` runs a per-increment battery and refuses every way a mutation run has silently lied here before — an untracked or uncommitted target, an anchor that does not match exactly once, a stale `__pycache__`, `-x` from any of three directions, a selector that skips or is already red, an invalid mutant counted as a kill, a restore that did not take, and a batch where nothing died. **A developer tool: it ships in no wheel and changes nothing for any KB** — no code path, no `schema_version`, no rebuild. Verified the only way it could be, by being run against its own guards: **25 mutants, 25 killed**, each by the test named beside it |
| **0.27.1** ✅ | **Two gates could not see what the procedure said they covered.** `docs/RELEASING.md` names STATUS's *Published on PyPI* list as a place a release stales and says `tools/release_order_gate.py` decides where the entry goes — while no pattern in that gate matched the list. It had drifted (`0.25.1 → 0.25.3 → 0.25.2 → 0.25.4`, wrong on SemVer *and* on verification time) through every green run since 20260821. It is now the **sixth sequence**, with its own count floor because the list begins at 0.16.0, and permission to **lag** the other five — an entry is held back until it is verified from the index — but never to **lead** them. Separately, `tools/fragments.py` now refuses a fragment opening with a `---` front-matter fence: the category has always lived in the filename, so a fence was inert and unobjected-to while `--apply` spliced it into the document verbatim. Three 0.24.0 fragments did exactly that and all three are still published in `CHANGELOG.md`. **No code path changed** — no `schema_version`, no rebuild, and nothing about any KB |
| **0.27.2** ✅ | **`pnk serve` had never once worked on a fresh install.** `mcp` was pinned `>=1.28` with no ceiling; mcp 2.0.0 removed `mcp.server.fastmcp` **3.5 hours before Pinakes' first published version**, so every one of the 38 releases on PyPI shipped a command that dies with an unhandled `ModuleNotFoundError`. Nothing saw it: 31 green tests in `tests/test_serve.py` run against a *locked* mcp 1.28.1, all 37 CI invocations are `--frozen`, and the one job that does resolve fresh never imported the module. **The cap is the small half.** `tools/wheel_import_gate.py` installs the built wheel into an isolated environment and imports **all 57** of its modules, so a module added later is covered without anyone remembering — and it runs **in front of `uv publish`**, because a dependency's major arrives with no commit here and a tag on Thursday would otherwise carry Monday's green to an index that never takes a version back. `anthropic` and `sentence-transformers` were measured and deliberately **not** capped: the remedy for the class is testing the resolve, not capping on reflex |
| **0.28.0** ✅ | **`pnk serve` runs on `mcp` 2.x, and tells a client which Pinakes it is.** `serve.py` moves to `MCPServer` and the requirement's `<2` cap becomes a `>=2` floor; the four `pinakes_*` tool schemas are **byte-identical** across the move, captured from a live session on each library and committed at `tools/mcp_tool_schemas.json`. The one wire difference is `serverInfo.version`, which every release to 0.27.2 filled with the **`mcp` library's** own version because `FastMCP` took no `version=`. **The port was four lines; the gate it broke was the increment** — the handshake in both workflows wrote three JSON-RPC lines and closed stdin, which `mcp` 1.28.1 drained before shutting down and 2.0.0 does not: ten runs at each protocol version answered `tools/list` 5/10, 1/10, 2/10 and 1/10, and `make smoke` was red on every run. `tools/mcp_handshake_gate.py` drives mcp's own client and checks the advertised version against the built **wheel's filename**, never `pnk --version`, which would ask the install under test. Two adversarial rounds found 24 defects, **every one of them in the remedies rather than in the port**; 29 mutants, 0 survivors |
| **0.28.1** ✅ | **The release-order gate, audited against itself.** Four of its own constants were read out of the documents it polices. A lagging sequence's ceiling was its own newest entry, so deleting that entry dropped the ceiling with it — `MAX_VERIFICATION_LAG` bounds how far the list may fall behind, and names both causes without choosing, because a deleted entry and an unwritten one are indistinguishable from the documents. Part ranges are read from the `# Part N` headings, so appending twenty characters to `# Part 5` made a misfiled release section legitimate — two Parts may now not claim the same versions. And the Part floor sat one below the real count, so demoting the last heading passed it exactly. **No code path changed** — no `schema_version`, no rebuild, and nothing about any KB |
| **0.28.2** ✅ | **The Guide's commands were re-run against the build that ships them.** `docs/GUIDE.md` opened by claiming every command on it was run against **0.2.0** — twenty-six releases back, on the published site — and **nine output blocks and four prose claims** had drifted behind that stamp. `pnk templates` and both `pnk init` blocks said `notes@1.1` against a shipped `1.2`; the `You get:` tree omitted the `README.md` and `eval/questions.yaml` that `init` writes; the two `pnk ask` estimates read `€0.26`/`€1.69` against a live `€0.20`/`€1.33`, stale since `deep/estimate.py` was re-measured in 0.25.3. **The worst was repeated three times: that only one surface in Pinakes can spend.** `pnk ask --deep` has been the second since 0.24.0, and `per_operation_eur` was described as bounding one `pnk sync` when it bounds one whole command. `docs/CLI.md` carried the same class of defect — *"`cannot compare` is what every KB in existence gets"*, true when written, false since 0.17.0 — and is fixed in the same change. **Two blocks were deliberately not re-run and now say so**: the paid `--deep` transcript would cost money to reproduce, and re-running the two-KB link walkthrough would change every ULID without making a sentence truer. **No code path changed** — no `schema_version`, no rebuild, and nothing about any KB |
| **0.28.3** ✅ | **The release-order gate reads a seventh sequence: STATUS's *Published versions* row.** It had fallen four releases behind — 0.27.0, 0.27.2, 0.28.0, 0.28.1 — through green runs of every gate here, after being repaired once for exactly this. The gate could not see it: its sixth sequence reads the *Published on PyPI* **prose**, and the row is a table cell forty lines below in the same file under the same heading, so each release was reported present — in the sequence next door. **Reaching it needed a new mechanism**, because the row is the one sequence that is not a run of lines: a `Sequence` may now declare a `within` anchor, one regex capturing the region the pattern runs inside; a `within` matching twice is refused rather than resolved to the first, which would splice two lists into a sequence sorted by accident. **And the row may never lag the prose beside it** — both record the same event, so a *relation* replaces a *bound*: measured over every commit on `main`, the lag bound alone left **29 commits green with the row already wrong**, while the relation fires 11 commits and 10 days earlier with 0 false positives over 53. Both are kept and one test asserts both fire, so neither can be deleted while it is green. **No code path changed** — no `schema_version`, no rebuild, and nothing about any KB |
| **0.29.0** ✅ | **Mutation batteries are committed, and one caught what four green gates missed.** 73 mutants written across six increments existed only in session scratchpads; `tools/batteries/` now holds them one file per target, plus a fourth battery covering `mutate.py` itself — **91 mutants, 91 killed**. The shipped prose this reverses is `tools/mutate.py`'s own — *"a battery is a per-increment working file, not a portable artifact"* — an assumption nobody had measured. Measured: **78 of 81 anchors still resolved exactly once** a day to a week later, and the three that did not **refused**, so the cost of keeping one is a maintenance prompt and never a false certificate. `--check-anchors` answers *do they still hold?* in milliseconds against the **working tree**, and `tests/test_batteries.py` gates anchors, `kills` selectors, double claims and a declared `mutants = N` inside `./check.sh`. **It is a resolvability gate, not a regression gate** — nothing runs a battery automatically, and `mutate.py` exits 0 on a survivor. **Two of this increment's own mutants were killed about nothing**: a repaired anchor whose `new` was left behind produced a `SyntaxError` that read KILLED in a batch reporting `0 errored`, so a compile refusal now runs with the anchor pre-flight. And running the batteries found a test asserting only an exit status about a *diagnostic message* — green suite, green `./check.sh` twice, two review passes, and the battery was the only thing that saw it. Also: **a cleared context settles its own role, and its peers', before it writes anything**. **No code path changed** — no `schema_version`, no rebuild, and nothing about any KB |
| **0.29.1** ✅ | **`CLAUDE.md` extracted to its own guideline: 274 → 220 lines, nothing lost.** Hygiene rule 6 makes crossing ~150 lines the trigger to extract; the file had crossed it by 83%. Five sections of detail moved to the page that owns them — `RELEASING.md` § *Landing a branch*, `INVARIANTS.md` § *The paid path's key is its own*, `BUILDING.md` § *Proposing a change to a document you do not own*, `DESIGN.md` § 7.3 — each leaving a pointer that **states the fact** a reader would otherwise open the sub-doc for. The plan-status bullets were **deleted as duplicates**, not moved: `docs/README.md`'s routing table already carried them in more depth. **A review found five defects and every one was about the neighbourhood, not the content** — two provenance notes still describing what their file held *before* it was extended, a routing row describing the pre-extraction layout, a pointer aimed at the now-compressed text, and a new section duplicating a rule `README.md` already owned. That duplicate had **already drifted**: README named the deep release as live unbuilt work three releases after it left that table. **It stops at 220, not 150** — everything with a home elsewhere has moved, and rule 6 calls the guardrail a trigger to extract, never a cap that justifies deleting. **No code path changed** — no `schema_version`, no rebuild, and nothing about any KB |
| **0.29.2** ✅ | **Eleven broken links, and three code spans rendering as wreckage, on the Markdown surface no gate reads.** `mkdocs build --strict` resolves every link in `docs/`, and `mkdocs.yml` excludes `CLAUDE.md` and `docs/README.md` deliberately — they point at `plans/`, `tools/` and `changelog.d/`, which a site build cannot resolve. **Nothing else in the repo resolves a link**, so `CHANGELOG.md`, `plans/**` and the fragment READMEs were checked by nothing at all. Three of the eleven pointed at `../docs/…`, which resolves *above* the repository root; **one anchor rotted when a re-measurement renamed the heading it cited** — 0.7.0's entry still pointed at *measured 20260801 12:14* after that section became *yes, measured 20260804* — and six were **quotations** of other documents' links, rendering as live links to paths that resolve only from `docs/`. The quotations are **code-spanned, not repointed**: correcting a path inside a quotation would falsify the quotation. Separately, **a backslash does not escape a backtick inside a code span**, and `docs/RETROSPECTIVES.md` — which is published — had been rendering one line as a broken run of `<code>` tags for weeks with `mkdocs build --strict` green throughout, because **`--strict` resolves links and never asks whether a span renders as intended**. **Verified by rendering, not by regex**: two regex scanners produced seven false positives between them, and one produced a *wrong edit* to an instructional example before it was caught. **No code path changed** — no `schema_version`, no rebuild, and nothing about any KB |
| **0.30.0** ✅ | **The Markdown `mkdocs build --strict` never sees now has a gate of its own.** `--strict` resolves every link in `docs/` and is the only thing in the repo that resolves any link; `mkdocs.yml` excludes `CLAUDE.md` and `docs/README.md` deliberately, and `CHANGELOG.md`, `plans/` and the fragment READMEs were never in the build. `tools/markdown_link_gate.py` resolves every relative link and heading anchor there, in `./check.sh` and its own CI job, **stdlib-only and 0.25s** — licensed by a test measuring its extractor against a real renderer over 894 links (0 false positives, 1 harmless false negative on an external autolink). **A quoted link is left alone**, so a document quoting another's links is never asked to corrupt the quotation. It caught a dead link in this very release's own changelog fragment — a path correct in `changelog.d/` and wrong once spliced into `CHANGELOG.md`, the splice-time class nothing in `check.sh` could reach. **`docs/RELEASING.md` § *Landing beside a peer*** records why `tools/shared_file_overlap.py` is not a peer check — it compares to `origin/main`, never to a sibling branch — and that a landing **order can be forced**: a peer's new gate was red on `main` until this release's predecessor landed, found by running their gate rather than by asking. Also fixed: `CHANGELOG.md` carried a repeated `### Fixed` and two non-bullet bodies, which `fragments.py --check` passes because it validates pending fragments and **never the document it splices them into** *(closed in 0.30.1)*. **No code path changed** — no `schema_version`, no rebuild, and nothing about any KB |
| **0.30.1** ✅ | **Nothing in this repository had ever read the document a release writes.** `tools/fragments.py --check` parsed every pending fragment and asserted nothing about the result of `--apply`, so a splice could leave `CHANGELOG.md` malformed with every gate green — and had: `## [0.28.3]` carried `### Fixed` twice consecutively for **twenty-two days**, found by reading a release precedent rather than by any gate. `--check` now validates **the assembly the pending fragments would produce**, through the same `prospective()` that `--apply` calls, so there is no second definition of the splice to drift; a byte-comparison test pins them. Two rules on the assembled document — a heading never repeats consecutively, and a changelog entry opens with a `- ` item — and **the second is changelog-only by construction**, the retrospectives stream carrying no category vocabulary to reach it. Replayed against the trees as they stood, it exits 1 **at the commit that added the fragment**, at 0.6.0 and 0.28.3 alike. **Three defects in the machinery around the rules, each reproduced end to end before repair**: `--apply` spliced entries *inside* fenced code blocks, would have taken a quoted `## [Unreleased]` as its insertion point, and **was not atomic across streams** — refusing on the second wrote the first and deleted its fragments while printing *"Nothing written, no fragment deleted"*. Every stream is now validated before any stream is written. Separately, **five blocks of front-matter residue were rendering as setext `<h2>` headings, two of them on the published site** with live permalink anchors, `mkdocs build --strict` green throughout — a spurious heading is not a broken link. And **four documents told an implementer to write planner-only files**: the restriction already existed and was already obeyed, so no rule was added and the four sentences were corrected. **No code path changed** — no `schema_version`, no rebuild, and nothing about any KB |
| **0.30.2** ✅ | **`pnk init` asks **git** whether `.pinakes/` is ignored, instead of searching the `.gitignore` for a string.** The old check was `".pinakes/" not in gitignore.read_text()`, and a substring test is not git's ignore semantics — measured 20260825, it was wrong in **both** directions. It warned about `.pinakes` and `.pin*`, which git *does* ignore; and it stayed **silent** for `!.pinakes/` and for a commented-out `#.pinakes/`, which git does not. **The silent half is the one that cost something**: commenting a line out to debug and re-running `init` is enough to leave the index, the spend ledger and every deep transcript — the first thing under `.pinakes/` to hold your **verbatim question** — tracked, with no warning at all. The question now goes to `git check-ignore`, asked as *is an **arbitrary** path under `.pinakes/` ignored* rather than *are these named files ignored*. **That distinction is the whole fix, and the first attempt got it wrong**: probing `index.db`, `ledger.jsonl` and `deep/transcript.json` reports **protected** against an ordinary `.gitignore` carrying `*.db` and `*.json`, while `index.db-wal` — megabytes of verbatim document text in WAL mode — stays tracked. **A silent false reassurance replacing a defect that at least made noise**, caught by adversarial review and not by any gate. The reviewer's own proposed fix was also insufficient, and only measurement against `git ls-files --cached` showed it. Outside a repository the same probes run in a throwaway repo, so there is one definition of the answer rather than two that can disagree. **The warning's remedy no longer lies either**: it printed *"add this line"* to users whose `.gitignore` already had it and then negated it — a failure unreachable under the substring test, where the string's presence *was* the verdict. Whether `pnk doctor` re-checks this on every run, and whether that is a WARN or a note, is **untouched and still undecided**. **This one ships in the wheel** — `src/pinakes/init.py` and `cli.py`, unlike a `tools/` gate |
| **0.30.3** ⏸ **on `main`, unreleased** | **`pnk init` now reports a `.pinakes/` that git is already *tracking* — a state the 0.30.2 ignore check was structurally unable to see.** `git check-ignore` consults the index, so it answers *not ignored* for a tracked path; and 0.30.2's probes are **opaque random tokens**, which by construction nothing ever adds to the index. So the check could ask only *would a new file here be ignored* and never *is anything in there tracked right now*. **They come apart in the case that costs most**: a KB committed before its ignore rule existed reads as **protected** the moment the rule is added, while every `git commit -a` keeps republishing `.pinakes/deep/` — the user's **verbatim questions**. Reproduced end to end: a correct `.gitignore` over three committed files, and `init` printed nothing. The fix is a second **question**, not a different probe — `git ls-files` over the index, reported as its own state with its own remedy, and asked **whether or not the `.gitignore` was adopted**, because the state it exists for is usually a repository with no `.gitignore` at all. **The remedy's order is load-bearing**: with no ignore rule, `git rm -r --cached` followed by any `git add -A` puts the file straight back, so the line goes first — and the printed command carries an **absolute** path, because with the KB at `repo/kb/` the relative form fails from the repository root and leaves the KB tracked. The text says the removal is from git's index and **not** from your disk, and claims nothing about commits already pushed. **Two of its three specified constraints were corrections to the plan rather than to the code**: the prescribed subdirectory test could not fail (`_ask_git` pins git's cwd to the KB root — mutated to the relative pathspec, 68 of 69 tests still passed), and `rc=128` had to be asserted against `_tracked_by_git` directly because the reported field is a `bool` that collapses `None` into `False`. **This one ships in the wheel** — `src/pinakes/init.py` and `cli.py` |
| **0.31.0** ✅ | **Eight of its twelve entries are a check that could not fail.** `make release-check` was **three `echo`s** — it printed `__version__` and the tag and compared nothing, while this file and `CLAUDE.md` both called it the last gate before an irreversible publish; it now refuses a tag that is missing, duplicated, lightweight, empty-annotated, disagreeing with `__version__`, or **already on the remote**, and the tag is created *before* it runs and pushed *after*. A review fan-out that lost agents **reported success**: `tools/review_pass_gate.py` exits 1 on a pass that did not finish, and `tools/review_ledger.py` stops the next pass starting from zero. STATUS's headline could claim a hold that was over or hide one that was not — **and the half nothing could have caught was the *removal***; the procedure never asked for the marker, which is why it had never once been written. Its own marker said *"NOT tagged"*, a claim about git where the truth is about the index. **The suite stopped reading the wall clock**: `prices.toml` aged past `max_price_age_days` on 20260827 and took **25 tests** red with no commit touching the tree, four days before anyone looked — the tests now pin a fresh table the way one already pinned an aged one, and `docs/RELEASING.md` gained the price-refresh step whose absence is why `as_of` had **never been refreshed since the file was created**. Two user-facing sync fixes: a sidecar whose id no longer matches the row at its path **stops wedging the index** (it wedged every later `sync` while `doctor` reported healthy at exit 0), and no plan now places one id at two paths — **renaming documents past each other still fails**, deliberately, but the failure now costs nothing where it used to leave a document soft-deleted behind the crash. `pnk doctor` gains a **retired documents** check for a document on disk that `pnk search` cannot see. **No `schema_version` bump and no rebuild**; the `doctor` check and both `sync` fixes ship in the wheel |
| **0.31.1** ✅ | **The release step written to catch a stale price was skipped by the release that wrote it.** `usd_per_eur` in `src/pinakes/budget/prices.toml` held its **seed value `1.08`** from the file's creation on 20260728 until 20260831, while 0.31.0 moved `as_of` forward to `20260830 14:46` above it — the exact falsification `docs/RELEASING.md` § *Before you start* step 3 names, committed **five hours after that step was written**, on the same day, by the release that was its first customer. The ECB euro reference rate for 20260831 is **1.1596**. Every EUR figure Pinakes prints is `cost_usd / usd_per_eur`, so the stale rate **over-stated all of them by 7.4%** — `pnk ask --deep` estimates, the reservations written to the ledger, and `pnk budget` totals — and a EUR cap bit 7.4% early. Nothing overspent; but the ledger records `cost_usd` and the rate on every line *so euros can be re-derived later*, and every line written since 20260728 carries a rate that was never true. **The staleness guard was healthy throughout and guarded the wrong thing**: `max_price_age_days` and `pnk doctor` both key on `as_of`, so re-stamping made the table maximally fresh by every instrument this project owns — an instrument that reads the claim cannot check the claim. `prices.toml` now **names its FX source** in the file rather than in a commit message, because an unnamed source is not re-checkable by the next release. **And nothing in the suite ever asserted the committed rate**: measured over every EUR literal under `tests/`, six of seven pin the rate where the test controls the input, and the seventh — `test_cli_ask.py`, which exists to discriminate €0.21 from €0.26 — was its sole alarm **by accident**, firing when the rate *moves* and never when it is *stale*. That is rowed as two parts deliberately, because decoupling it without replacing the guard would delete the only alarm the rate has had. Also fixed: two `retro.d/` fragments that would have spliced malformed — one carried **no `##` heading at all**, and the retrospectives stream synthesises none, so its bullets would have landed under a different incident's heading. **No code path changed** — no `schema_version`, no rebuild, and nothing about any KB; `prices.toml` ships in the wheel, so an installed copy gets the corrected rate |
| **0.32.0** ✅ | **One file the process could not open ended `pnk sync` with a raw traceback and no index database at all** — every other document in the KB unreachable because of one. `hash_file` let `PermissionError` escape `walk_sources`. The path is now carried out of the walk and reported as a per-document failure with a `chmod +r` remedy, and `report.ok` is `not failures`, so the sync still exits non-zero rather than dropping the file in silence. **The second half is what makes the first safe:** `pair()` reasons from *absence*, so a walk that merely skipped the file would have emitted a `SoftDelete` and **deleted the document from search** on a permission change; the unreadable paths reach `pair()`, which holds each row as a `Skip` before any loop that reasons from absence runs. `pnk doctor` died on the same condition — the remedy `pnk sync` prints sent you to a traceback — and a fourth drift check, `paid extraction unreadable`, now names the document whose staleness could not be decided. An unreadable document's sidecar is no longer listed as orphaned, because that list is printed with `pnk doctor --prune` beside it. The other eleven entries are tooling and documents. |
| **0.32.1** ✅ | **A KB name is escaped where the manifest is rendered, not checked where it is typed — and `pnk init` no longer reports a bricked KB as created.** A name holding a `"`, a `\` or a control character closed or escaped the TOML basic string it was interpolated into, so `pinakes.toml` came out unreadable while `pnk init` exited 0 and printed *created*. **There was no repair path**: `pnk init` refuses a directory that is already a KB, so recovery meant hand-editing TOML. The fix is a `finalize=` hook on the Jinja template, so it covers **every** interpolated value rather than `--name`, and both ways in, since `init` falls back to the directory's own name. **It does not only escape.** An unpaired surrogate — what POSIX makes of any invalid UTF-8 byte in an argument or a filename — has no TOML form raw *and* none escaped, so there is nothing for an escaper to produce; it used to reach `Path.write_text`, which truncates *before* the encoder raises, leaving a **zero-byte manifest** and a directory `init` then refused. That is S4's own end state, and it was found on the branch that fixed S4. It is now refused before anything is created, with a message naming the code point and **never echoing the value**, because a name carrying an unprintable byte can carry an ANSI escape beside it. **What it deliberately does not do:** escaping for TOML discharges what TOML is owed and nothing a terminal, a filename or a log line is owed — `pnk budget` prints `kb.name` raw, and that is rowed rather than built. **No `schema_version` bump and no rebuild**; a KB with an ordinary name is unaffected, and a KB already bricked by this stays bricked, because the fix is at creation. **This one ships in the wheel** — `src/pinakes/template.py`. Everything else in this release is tooling, documents and a red `main`: a money assertion that quantisation cannot hold, green for a month on the value of an exchange rate neither test named. `prices.toml` carries the **2026-09-02** ECB fixing, re-verified at the cut rather than re-stamped |
| **0.32.2** ✅ | **Four reports Pinakes made that were not true — and on three of them it exited 0.** Every ordinary deletion announced *“moved without its sidecar”* and *“a new id was minted”* — quoted in halves here, because the joined sentence is a retired row: nothing moved, nothing was minted, and the path it named no longer existed. The hint is gated on an **orphaned sidecar** now, which is what actually separates a move from a deletion — delete a document properly and its sidecar goes with it — and it reports the state observed rather than the conclusion inferred, because deleting the file alone leaves a sidecar behind and still mints nothing. **`-k` below 1 was `type=int` and nothing else**, so the value travelled to whatever the command reached: `pnk search` used it as a raw negative-slice bound and answered confidently and wrongly — `-k -1` returned every passage but the last at exit 0, `-k -100` returned none and called it *“no passages matched.”* — while `pnk ask` reached the deep estimator and raised an unhandled `ValueError`. One missing check, one surface answering wrongly and one crashing; it is a usage error at the parser now. **`-k 0` is refused too, and that is a deliberate behaviour change**: the width was read as `limit or manifest.retrieval.final_k`, so a falsy `0` silently meant *use the default* — asking for nothing and receiving ten passages. **`pnk sync --sidecars-only --index-only` wrote sidecars into `docs/`**, the one thing `--index-only` exists to promise it will not do, and reported `0 indexed, 0 renamed, 0 metadata-only, 0 unchanged, 0 removed` at exit 0 — every number truthful, the line still a lie, because the count of files written into `docs/` was not among them. Refused. **And nothing ever deleted from the `failures` table**, so a document the user repaired stayed listed forever, `pnk doctor` insisting it *“is not searchable”* while `pnk search` returned it, under the advice *“Fix them and re-run `pnk sync`”* — which is exactly what had just been done. It never de-duplicated either, so three syncs of one broken document left three rows and the count reported was a count of **attempts** wearing the clothes of a count of problems. A document that indexes cleanly clears its own entry, a removed one takes its entry with it, and one held because it is **unreadable** keeps it — nothing about that document was verified this run. **All four ship in the wheel** — `cli.py`, `sync.py`, `pairing.py`, `store.py` and `doctor.py`. **No `schema_version` bump and no rebuild**; a KB not in one of these four states is unaffected |
| **0.32.3** ✅ | **`pnk doctor` offered to delete a permanent id, and both commands crashed on the oldest Python this project claims to support.** One condition produced both: a document present on disk that the process cannot reach, which is what a symlink into a directory lacking `+x` gives you. **The orphan check asked whether the document was a *readable* file**, so a present document was reported `WARN orphaned sidecars: 1` beneath *“Remove with `pnk doctor --prune`”* — and taking that advice deletes the sidecar holding the ULID [`INVARIANTS.md`](INVARIANTS.md) calls permanent. That half is **interpreter-independent** and shipped in every release. **The crash is the half that depended on your interpreter**: `Path.is_file()` and `Path.exists()` propagate `PermissionError` on 3.13 and swallow it on 3.14, `requires-python` is `>=3.13`, and **nothing in this repository had ever run 3.13 in CI** — no `.python-version`, no `setup-python`, and `uv sync --frozen` takes the newest interpreter on the runner, while the `check` matrix varies *extras*. A fresh worktree runs 3.14 and the primary checkout runs 3.13, so one commit answered differently in two directories and a branch gate went green over a merged gate that was red. Nine call sites — six in the source and sidecar walks, two in the cross-KB scan, one in the orphan check — now go through `src/pinakes/paths.py`, whose `False` deliberately means three states rather than one; `.github/workflows/ci.yml` gained a `minimum-python` leg that **asserts** the interpreter it got, and its first run in this repository's history is green, read in its log. **The first fix was incomplete and an adversarial review is what found that** — two private helpers inside `sync.py` that `doctor` and `linkscan` could not reach, so the identical crash survived in both. The other three entries are row 8's low classes: a mistyped `--source-type` is a usage error, an empty KB stops blaming filters nobody passed, and a broken symlink is reported rather than skipped. **No `schema_version` bump and no rebuild** |
| **the graph release** ✅ **shipped 0.11.0** | Structural edges, the expansion channel (`graph_channel`, default off), `schema_version` 3 — eval-gated. All six increments landed: **G1** and **G4** in 0.6.0, **G2** in 0.7.0, **G3**, **G5** and **G6** in 0.11.0. **Its gate ran and did not pass, so `expand` ships `off`** ([the numbers](#did-the-expansion-channel-earn-its-default--no-measured-20260804-2252)) — an eval-gated feature that is built, measured and off by construction, which is the structure working rather than failing. What would change it is a corpus or a different channel design, never a more expensive one ([decision](https://github.com/lucagattoni/pinakes/blob/main/plans/20260804_1442-decision-g3-go.md)) |
| **the deep release** ✅ **completed 0.26.0** | `pnk ask --deep` — the budgeted reasoning loop, across **0.23.0 to 0.26.0**. All seven increments landed: **E1** in 0.23.0, **E2**, **E3** and **E4** in 0.24.0, **E5** in 0.25.0, **E6** in 0.25.3 and **E7** in 0.26.0. It is the last paid entry point, so `.paid-path-allowlist` is complete at two, and its estimator is the only one measured against the live API (over-reserving 22x to 51x, with no ceiling lowered). `--write-suggestions` is the one thing D-25 deferred, and it is **not planned** |
| *the graph release, staged* | PPR graph channel, the `[ner]` extra — each eval-gated, not scheduled |
| *the template release* | Template ecosystem, `pnk upgrade`, the `sqlite-vec` tier |

The order is a dependency order, not a schedule. Anything unreleased may be resequenced; only the
✅ rows are facts.

## Measured numbers

Re-measure and re-date these whenever retrieval or extraction changes; never carry one forward
unverified.

| Metric | Value | Measured |
|---|---|---|
| questions | 74 | 20260801 12:14, demo KB, `[light]` models |
| recall@5 | 0.939 | 20260801 12:14 |
| MRR | 0.881 | 20260801 12:14 |
| rerank precision | 0.849 | 20260801 12:14 |
| false-abstain | 0.015 | 20260801 12:14 |
| **false-confidence** | **0.25** | 20260801 12:14 — one no-answer question in four still gets a confident answer |
| NumPy vector tier | 2.25 ms/query at 50k×384, 77 MB resident | 20260725 13:49 |

Per class, same run: `lexical` 1.00, `simple-lookup` 1.00, `filter` 1.00, `no-answer` 1.00
(abstained correctly), `multi-hop` 0.944, `paraphrase` 0.75.

⚠️ **These numbers moved on 20260801 because the golden set grew from 41 questions to 74, not
because retrieval changed.** G2 added 20 `simple-lookup` questions and 13 single-KB multi-hop ones
and re-baselined once. `eval/baseline-pre-growth.json` preserves the 41-question figures with the
ids they covered, and re-scoring the committed per-question artifact over exactly those 41
reproduces every one of them **byte-identically** — so nothing already in the set moved. The
previous run of record was 20260729 03:23: recall@5 0.909, MRR 0.812, rerank precision 0.758,
false-abstain 0.03. **Those numbers had themselves moved for a non-retrieval reason** — the scorer
was wrong before them: a multi-hop question was scored as a single-shot search of its last hop's
query, `hops_followed` reached no metric, and recall@5 rose 0.879 → 0.909 when the class started
requiring every hop to land.

**Twice now the headline numbers have moved without retrieval changing.** Say which it was, in the
commit and here, or the next reader credits a scorer fix to the ranker.

**Paraphrase is still the only class with real room in it**, and the `multi-hop` class remains close
to ceiling even after tripling in size — 17 of 18. That is a fact about the corpus, not about the
questions: thirty short, topically disjoint documents make "retrieve 5 of 30" undemanding. Nothing
should be tuned against this corpus until it is larger and its documents are less separable. **That
constraint blocked the graph release for three days and was discharged on 20260804**, when the RFC
corpus cleared the reachability precondition and 0.11.0 shipped
([`plans/20260801_0749-realism-corpus.md`](https://github.com/lucagattoni/pinakes/blob/main/plans/20260801_0749-realism-corpus.md)).
It binds every *future* retrieval change the same way — see the second golden set below.

The false-confidence figure is fitted and scored on the same 74-question set (8 of them no-answer,
unchanged by G2's growth — so the calibrated thresholds were re-fitted after it and came back
identical), so treat it as a floor rather than an estimate. Publishing it is the point:
[DESIGN §4.2](DESIGN.md#42-escalation--free-path-first) commits to measuring the heuristic's cost
rather than assuming it away.

### A second golden set, on a corpus that can license a result — frozen 20260806 11:56

Every number above is `tests/demo-kb`'s, and the paragraph above says why nothing should be tuned
against it. **The measurement it cannot carry now has an instrument.** 110 questions over the RFC
band `build_rfc_corpus.py --era modern --count 200` (RFCs 8600-8799, 195 published, **43 353** chunks),
frozen at
[`tools/rfc_corpus/questions.yaml`](https://github.com/lucagattoni/pinakes/blob/main/tools/rfc_corpus/questions.yaml)
with its `before` leg beside it. **Released in 0.16.0**, and it has now been used once: it produced that release's no-go (above). The questions stay frozen — `id` is what pairs a `before` row with an `after` row, so rewording or renumbering one silently unpairs it.

| Metric | Value | |
|---|---|---|
| questions | 110 | 32 lexical, 32 simple-lookup, 32 paraphrase, 14 no-answer, over 96 of the 195 documents |
| recall@5 | 0.9271 | |
| MRR | 0.8767 | |
| rerank precision | 0.8438 | |
| false-abstain | 0.0104 | |
| false-confidence | 0.1429 | fitted on this same set — a floor, see below |
| confidence coverage | 1.0 | |
| **improvable pool** | **15** | 11 paraphrase, 2 lexical, 2 simple-lookup — the number that decides whether a sign test at p < 0.05 is reachable at all |

Per class: `lexical` 1.00, `simple-lookup` 1.00, `no-answer` 1.00, `paraphrase` 0.7812. Measured at
`max_tokens = 414`, `k = 5`, `rerank = "local"`, `graph_channel = "off"` — the artifact records all
four, so a leg produced under different settings is identifiable rather than merely suspect.

**Two things this set is for, and one it is not.** It exists to make the injection experiment
falsifiable, and its questions were written by authors who had not read this repository, before any
injection code existed — fitting a question set to the mechanism it will judge is undetectable
afterwards. It is **not** a claim that retrieval improved: 0.9271 against demo-kb's 0.939 is two
different corpora, not a regression. The false-confidence caveat above applies here in the same
form, for the same reason — the thresholds are fitted on the set that scores them.

### Is the evaluation reproducible? — measured 20260801 00:35

The graph release gates on an exact per-question sign test, so it was worth knowing whether a
question can change its answer for reasons that have nothing to do with retrieval. The golden set
was run against the demo KB, a document edited, the index re-synced incrementally, then rebuilt,
then built again from scratch — comparing **per-question outcomes**, not aggregates, at each step.

| Comparison | Real `[light]` models | A low-dimensional tie-heavy fake |
|---|---|---|
| the same index, evaluated twice | identical | identical |
| an incremental sync vs `--rebuild` | identical | **1 of 41 questions differed** |
| `--rebuild` vs a from-scratch sync | identical | identical |

**The shipped models were reproducible, and only by luck.** 384-dimensional cosines almost never
tie exactly; underneath them every tiebreak in the pipeline resolved to `chunks.id`, the rowid,
which the schema says outright has no identity across rebuilds. So the property held because the
corpus did not exercise it, which is not a property at all.

Ordering is now total on `(documents.path, chunks.ordinal)` at the three places that decide it —
the vector array's row order, the BM25 cut, and hydration — plus a stable `argsort`, which covers a
fourth case the others do not: NumPy's introsort partitions over the whole array, so adding
documents reordered tied entries elsewhere in **500 of 500** random tie-heavy arrays.

**The numbers above did not move.** The real-model golden set scores byte-identically to the
committed baseline before and after, which is what a change that only breaks ties should do — and
is why this increment rewrites no baseline. Held by `tools/eval_reproducibility_gate.py` (a
`check.sh` gate and its own CI job, sweeping four kinds of corpus change),
`tests/test_search_reproducibility.py`, and a CI job that diffs per-question outcomes between
`ubuntu-latest` and `macos-latest` — the half a single machine cannot answer.

### The realism corpus exists, and it falsified a design premise — built 20260804 08:00

**[`pinakes-corpus-rfc`](https://github.com/lucagattoni/pinakes-corpus-rfc)** — 300 RFCs, a
connected cluster closed by BFS over `obsoletes`/`updates` in both directions, structured by
`wg_acronym` and tagged from the RFC Editor's own `keywords`. It lives outside this repo by design
([`plans/20260801_0749-realism-corpus.md`](https://github.com/lucagattoni/pinakes/blob/main/plans/20260801_0749-realism-corpus.md)).

| Measure | demo-kb | partner-kb | RFC corpus |
|---|---|---|---|
| documents | 30 | 21 | **300** |
| carrying an authored link | 27% | 29% | **53.3%** (160/300) |
| worst out-degree | 2 | 3 | **86** |
| relation vocabulary | 2 kinds | 4 kinds | 2 (`updates` 296, `supersedes` 95) |
| chunks | 60 | — | **106 806** |
| chunks with a `heading_path` | most | most | **0** |

**The prediction recorded before any of it ran was right, and by more than expected.** The plan
said the corpus would exceed the 35% density cap and possibly the degree cap of 4. Density is
**53.3%**; worst out-degree is **86** — RFC 8996 *(Deprecating TLS 1.0 and TLS 1.1)* updates 86
documents in one header. Nothing was tuned: every rule was written down before an edge existed.

**The shape matters more than the headline.** Median out-degree is **1**, second-largest is 17. The
corpus is sparse with one real human-authored hub — not uniformly dense. So APPROACH §3's
*"authored links are sparse, precious signal"* is half right: sparse in the median, and carrying a
hub that decision 13's **2.0 undamped** weight was never designed for
([the ⚠️ on G3's weight table](https://github.com/lucagattoni/pinakes/blob/main/plans/20260729_0256-links-and-graph.md)).

**Two findings about Pinakes, not about the corpus:**

- **No heading grammar ran at all** — 0 of 106 806 chunks carried a `heading_path`. Not because a
  Markdown-shaped grammar failed to match RFC section numbering, which is what was first recorded
  here: `chunk.py` dispatched on **source type**, and every type but `markdown` took the plain-text
  path, which sets `heading_path=None` unconditionally. Nothing failed to match because nothing was
  tried, so tightening a grammar would have fixed nothing. Silent. It cost citations their heading
  component, and it meant `in-section`, `parent` and `child` derived **zero** edges here.
  **Fixed in 0.13.0** by `[chunking] headings = "numbered"` — opt-in, so it reaches a corpus only
  when its manifest asks for it. `tools/build_rfc_corpus.py` stamps it; this corpus's committed
  manifest does not carry it, so these figures still describe what a rebuild of it produces.
- **106 806 chunks is 2× past the NumPy vector tier's 50 000 threshold**, and `pnk doctor` says so.
  A 300-document, 20 MB knowledge base reaches the tier ceiling — which is a smaller corpus than
  the ceiling's framing implies.

Ten friction findings from building it are in
[`plans/20260731_1202-open-corrections.md`](https://github.com/lucagattoni/pinakes/blob/main/plans/20260731_1202-open-corrections.md). `pnk doctor`
reports no FAIL and five WARNs.

### Did the expansion channel earn its default? — **no, measured 20260804 22:52**

**No. `expand` ships `off`.** The graph release defaults its channel on only if an exact one-sided
sign test finds enough multi-hop questions improving. Run on the RFC realism corpus, at G5's own
HEAD, against a `schema_version` 3 index rebuilt for it:

| leg | multi-hop | improved | regressed | p |
|---|---|---|---|---|
| `off` | 7/20 | — | — | — |
| `expand`, without authored edges | 4/20 | 0 | **3** | 1.0000 |
| `expand`, all kinds | 4/20 | 0 | **3** | 1.0000 |

**Licensing p = 1.0000** — the more conservative of the two, as both runs bind. Nothing was lifted,
and the channel's extra candidates **displaced three answers two-list fusion already had**.

**The finding is `reachable ≠ retrievable`.** The reachability probe found **9** of those failing
questions reachable within two logical hops without authored edges — the measurement that unblocked
this release ([above](#can-the-graph-releases-gate-be-reached--yes-measured-20260804)). The
retrieval instrument lifts **none** of them. That gap is not a small correction: it is 9 against 0,
and it is exactly why the probe's own docstring says a high ceiling *"proves only that the gate is
not impossible"*. **A reachability precondition is necessary and nowhere near sufficient.**

**`sibling` is now inert in both gauges.** It is 106 506 of the corpus's 107 411 non-transit
structural edges, and `--drop sibling` returns the same 4/20, the same three regressions and the
same p. The reachability probe had already found removing it cost nothing; the retrieval instrument
agrees independently. The harm comes from the document-level path instead — `membership` transit
into `co-located` (262 edges) and `shared-tag` (643) hubs, which pull whole documents' chunks into
the fusion.

**Latency was not the problem.** `off` 2012 ms/query against `expand` 2051 — **1.02×** on a
106 806-chunk index.

Two bounds, both stated rather than worked around. The corpus has `[retrieval.confidence]`
commented out, so **two of the gate's four clauses could not fire on it** and are exercised only by
the synthetic fixtures in `tests/test_graph_channel.py` — a gate whose only fixture is the real
corpus can be tested solely in whichever direction that corpus points. And **no chunk in it carries
a `heading_path`**, so `parent-child` and `in-section` derive zero edges, the `--drop parent-child`
arm is inert by construction, and a "sibling" there is an adjacent arbitrary *size-slice* rather
than an adjacent section. What the arms measured is the value of size-slice adjacency on a corpus
whose structural chunking had silently degraded.

**Nothing was tuned after seeing the number** — no weight moved, no threshold revisited. The
`authored` weight's *measured at G5* marker is discharged as *"measured, and it changed no
outcome"*.

### Can the graph release's gate be reached? — **yes, measured 20260804**

**Yes on a realistic corpus; no on the synthetic one.** The graph release defaults its expansion
channel on only if an exact sign test finds enough multi-hop questions *improving*, and an
improvement can only come from a question that fails today. The precondition: **at least 7 multi-hop
questions fail, and at least 7 of those are channel-reachable within 2 logical hops without authored
edges.** The without-authored figure binds; the with-authored figure records and licenses nothing.

| | Required | `tests/demo-kb` · 20260801 | **RFC realism corpus · 20260804** |
|---|---|---|---|
| multi-hop questions failing today | ≥ 7 | 1 | **12** |
| of those, reachable **without** authored edges | ≥ 7 | 1 | **9** |
| of those, reachable with authored edges | — | 1 | 12 |
| reachable but beyond 2 hops · at-seed only | — | 0 · 0 | 0 · 1 |

**So G3 starts** ([decision](https://github.com/lucagattoni/pinakes/blob/main/plans/20260804_1442-decision-g3-go.md), 20260804 13:50). The measurement was deliberately sequenced
*before* the schema change, so a `schema_version` bump — and a forced rebuild for every KB in
existence — could not happen for an edge table whose channel might never be licensed. G1, G2 and G4
were cut as a release of their own while the answer was still no.

**Three drop runs show the 9 discriminates** rather than counting every document already in reach:
removing `co-located` costs 3 questions, removing `shared-tag` costs 6, and the two sum to exactly
9 — they lift disjoint sets. Removing `sibling` — 106 506 of 107 802 edges — costs nothing. No drop
ever raised the count. Artifacts:
[`pinakes-corpus-rfc/eval/probe`](https://github.com/lucagattoni/pinakes-corpus-rfc/tree/main/eval/probe).

**The bound on all of it: every chunk in the corpus that measurement ran on had an empty
`heading_path`.** The chunker was never asked for one — `chunk.py` dispatched on source type and
every type but `markdown` took the plain-block path — so `in-section` and `parent-child` derived
**zero** edges and were never exercised, and a "sibling" there is an adjacent arbitrary size-slice
rather than an adjacent section. The 9 is therefore a **floor** for a corpus whose chunker works,
and `sibling`'s zero is a question for G5's gate, not a design decision. **0.13.0 shipped the fix
but does not apply it retroactively**: `[chunking] headings = "numbered"` is opt-in, defaults to
`"none"` and is never stamped into a template, and this corpus's committed manifest has no
`headings` key — so re-running the probe against it as published reproduces these figures rather
than measuring a different corpus. Getting heading paths here means adding the key and rebuilding;
a corpus built fresh by `tools/build_rfc_corpus.py`, which does stamp it, carries them from the
start.

**Why the synthetic corpus could never answer this**, which is the finding that outlived the
negative result:


* **`tests/demo-kb` has no tags at all, and one flat directory.** With `mentions` cut, that leaves
  exactly **one** derived edge kind that crosses a document boundary — `co-located`, through a
  single thirty-way directory hub. `shared-tag` derives zero edges for want of any tag;
  `sibling`, `parent`/`child` and `in-section` are intra-document and cannot bridge two evidence
  documents by construction. Any future result on this corpus is a claim about one directory.
* **The retrieval funnel already sees the whole corpus.** The index holds **60 chunks over 30
  documents**, and `candidates_per_source` (30) is applied **once per retrieval source** — lexical
  and vector — so up to 60 of 60 chunks enter fusion before the pipeline cuts to `final_k = 5`. The
  rule for sizing a replacement corpus follows: **chunk count must exceed
  `sources × candidates_per_source`**, not merely `candidates_per_source`. A failing question here
  is a **ranking** failure, not a
  recall failure a channel could fix by reaching further. The probe reports an `at-seed` share
  separately for that reason: under a tie-heavy fake backend, two of three questions it called
  reachable were already among the fused candidates and had traversed no edge at all.

The thirteen new multi-hop questions were authored from corpus structure and **frozen before the
probe ran**. They are not re-authored to produce failures: fitting the question set to the edge set
is the circularity that cutting cross-KB questions removed once already, and it is undetectable
afterwards. Held by `tools/reachable_ceiling_probe.py`, whose own tests pin that it needs no schema
change and that its count moves when an edge kind is removed — a reachability probe answering
"reachable" for everything is the failure mode it exists to avoid.

## Published on PyPI

**[`pinakes` is on PyPI](https://pypi.org/project/pinakes/).** `uv add "pinakes[light]"` installs,
and needs **one manifest edit before it can sync**: `pnk init` stamps
`provider = "sentence-transformers"` whatever extras you have, so a `[light]` install fails with
*"the `sentence-transformers` backend is not installed"* until `provider` is changed to
`"fastembed"` — the edit [README.md](https://github.com/lucagattoni/pinakes/blob/main/README.md) and the [Guide](GUIDE.md#choosing-a-backend)
both call out — **and since 0.12.0 the error itself does too**: when `fastembed` is installed and
`sentence-transformers` is not, the remedy names the alternative and the two `provider` lines to
flip, instead of prescribing the ~2 GB install the `[light]` extra exists to avoid.

Verified 20260805 07:20 against **0.11.0** from the index (`uvx --no-cache --refresh --from "pinakes[light]==0.11.0" pnk --version` → `pinakes 0.11.0`): `init` → edit → `sync` →
`search` returns the document. The earlier claim that it worked unedited was wrong. **0.15.1 has
been verified to install and report its version from the index (20260806 00:58), not to complete
that four-step flow** — the flow is unchanged by this release, but saying so is not the same as
having run it. The first attempt read *unsatisfiable* and the second, 30 s later, returned
`pinakes 0.15.1` — one failed resolve is not a failed publish.

**0.16.0, same standard, 20260807 11:54:** `uvx --no-cache --refresh --from "pinakes==0.16.0" pnk
--version` → `pinakes 0.16.0`. Installs and runs from the index; the four-step flow above was not
re-run. **Checked against the index rather than against the workflow**, which is the whole point:
the publish job had already reported `success` while `https://pypi.org/pypi/pinakes/json` still
served `0.15.1` — a propagation lag that reads exactly like the failure this project has had
before, where a run went green and nothing was published.

**0.17.0, same standard, 20260807 21:22:** `uvx --no-cache --refresh --from "pinakes==0.17.0" pnk
--version` → `pinakes 0.17.0`, on the second attempt; the first read *unsatisfiable* 30 s earlier.
The four-step flow above was not re-run. **Two independent pieces of evidence, because neither
alone is enough**: the `Publish to PyPI` step log prints `Uploading pinakes-0.17.0-py3-none-any.whl`
and `Uploaded pinakes-0.17.0.tar.gz` (a step log cannot be CDN-cached), and the install above
resolves from the index. At the moment both were true, `https://pypi.org/pypi/pinakes/json` — even
with a cache-busting query string — still served an 18-version list ending at 0.16.0. **That
endpoint's silence is not evidence of a failed publish**, and this is the third release where it
has said so.

**0.18.0, same standard, 20260807 22:45:** `uvx --no-cache --refresh --from "pinakes==0.18.0" pnk
--version` → `pinakes 0.18.0`, after one *unsatisfiable* attempt and ~25 s. Same two independent
pieces of evidence: the `Publish to PyPI` step log prints `Publishing 2 files`, `Uploading
pinakes-0.18.0-py3-none-any.whl` and `Uploaded pinakes-0.18.0.tar.gz`, and the install resolves.
And again — **the fourth release running** — `https://pypi.org/pypi/pinakes/json` with a
cache-busting query string reported `latest: 0.17.0` and **zero files for 0.18.0** at the moment
both of the above were already true. It is now the most reliably wrong of the three caches, not an
occasional one.

**0.19.0, same standard, 20260808 04:25:** `uvx --no-cache --refresh --from "pinakes==0.19.0" pnk
--version` → `pinakes 0.19.0`. The `Publish to PyPI` step log prints `Uploading
pinakes-0.19.0-py3-none-any.whl (341.9KiB)` and `Uploaded pinakes-0.19.0.tar.gz`; the install
resolves. **The `json` endpoint reported `latest: 0.18.0` and zero files for 0.19.0 while both were
already true** — the fifth release running, so it is no longer worth consulting.

**Two things this release adds to the standard, because both were nearly missed.** First, the
**GitHub release is a manual step and the workflow's success does not create one**: `Release` went
green, PyPI had both files, and `gh release view v0.19.0` said *release not found* until it was
created by hand. A green workflow is evidence about the upload and about nothing else. Second, the
first attempt to verify the new command's exit code piped it through `grep`, so the shell reported
**grep's** status and printed `exit: 0` for a path that returns `3`. Re-measured without the pipe
against the published wheel: `cannot compare` → **3**, `up to date` → **0**, outside a KB → **1**.

**0.20.0, same standard, 20260808 05:52.** The `Publish to PyPI` step log prints `Uploading
pinakes-0.20.0-py3-none-any.whl (354.2KiB)` and `Uploaded pinakes-0.20.0.tar.gz`;
`uvx --no-cache --refresh --from "pinakes==0.20.0" pnk --version` → `pinakes 0.20.0`, on the second
attempt — the first, seconds after the workflow ended, reported the version *unsatisfiable*, which
is the ~90 s index lag and not a failed upload. Verified against the published wheel rather than the
repo: a KB stamped `notes@1.0` under `--apply` → `cannot compare`, exit **`3`**, manifest
byte-identical, **no `pinakes.toml.orig`**; `pnk upgrade --help` carries `--apply` and the
*writes nothing without --apply* qualifier.

**The manual-release step recurred, for the third time on record**: `Release` green, both files on
PyPI, `gh release view v0.20.0` → *release not found*. Created by hand and re-verified. Twice in
consecutive releases and three times since 20260804 is no longer a caution — **treat "create the
GitHub release" as a step of the procedure that the workflow has never once performed**, and check
it every time before writing anything that says a release shipped.

**0.20.1, same standard, 20260808 06:55.** The `Publish to PyPI` step log prints `Uploading
pinakes-0.20.1-py3-none-any.whl (355.6KiB)` and `Uploaded pinakes-0.20.1.tar.gz`;
`uvx --no-cache --refresh --from "pinakes[light]==0.20.1" pnk --version` → `pinakes 0.20.1`, again
on a retry rather than the first attempt — the same ~90 s index lag, not a failed upload. Verified
against the published wheel rather than the repo, on a KB created by that wheel: `vector_tier =
"sqlite-vec"` → `must be one of 'auto', 'numpy', found 'sqlite-vec'` with the remedy naming this
file and `vector_tier = "auto"`, **exit `1` measured without a pipe**; then the one-line fix →
`pnk sync` indexes, and the index's `meta` records `vector_tier = numpy`.

**0.21.0, same standard, 20260808 10:26.** The `Publish to PyPI` step log prints `Uploading
pinakes-0.21.0-py3-none-any.whl (360.8KiB)` and `Uploaded pinakes-0.21.0.tar.gz`;
`uvx --no-cache --refresh --from "pinakes==0.21.0" pnk --version` → `pinakes 0.21.0` — again on a
retry, the first attempt reading *unsatisfiable* ~60 s earlier. Verified **against the published
wheel rather than the repo**: `pnk templates` prints `notes  1.1  Plain Markdown notes…`, `--json`
carries the `notes@1.1` reference beside the name and version, and a KB created by that wheel still
receives both historical files — `README.md` and `eval/questions.yaml` — with no `_versions/`
anywhere in it, which is the check that `files`' absent-key default did not quietly become "none".

**0.21.1, same standard, 20260810 01:58.** The `Publish to PyPI` step log prints `Publishing 2
files`, `Uploading pinakes-0.21.1-py3-none-any.whl (363.0KiB)` and `Uploaded pinakes-0.21.1.tar.gz`;
`uvx --no-cache --refresh --from "pinakes==0.21.1" pnk --version` → `pinakes 0.21.1`, this time on
the **first** attempt rather than after the ~60 s index lag the last two needed. `v0.21.1` is an
ancestor of `main`.

**0.22.0, same standard, 20260811 08:31 — and the first release this project did not finish by
hand.** The `Publish to PyPI` step log prints `Uploading pinakes-0.22.0-py3-none-any.whl (368.3KiB)`
and `Uploading pinakes-0.22.0.tar.gz`; `uvx --no-cache --refresh --from "pinakes==0.22.0" pnk
--version` → `pinakes 0.22.0`, first attempt. Verified **against the published wheel** rather than
the repo: `pnk init --help` from it shows `--backend {st,light}`, the flag this release adds.

**The GitHub release was created by the workflow** — `gh release view v0.22.0` reports
`by github-actions[bot]`, non-draft, 08:31:33Z. That closes the story below rather than continuing
it: the step D-19 added did on its first run exactly what six releases of hand-creation had been
compensating for. **The rule that found it stands unchanged** — verify the artifact, never the run's
own status — and it is what turned a green `Release` job into the question that got answered.

**0.22.1, same standard, 20260811 12:33 — and the aggregate JSON endpoint lied for a minute.** The
`Publish to PyPI` step log prints `Uploading pinakes-0.22.1-py3-none-any.whl (368.3KiB)` and
`Uploading pinakes-0.22.1.tar.gz (2.0MiB)` at 12:32:17–19Z; `gh release view v0.22.1` reports
non-draft, 12:32:21Z, created by the workflow again. `uvx --no-cache --refresh --from
"pinakes==0.22.1" pnk --version` → **`pinakes 0.22.1`** — but only on the third attempt.

**Which of the three caches disagreed is the useful part.** For two minutes after a confirmed
upload, `https://pypi.org/pypi/pinakes/json` still served `"version": "0.22.0"` and a count of 26,
while **`https://pypi.org/simple/pinakes/` already listed both 0.22.1 artifacts** and
`https://pypi.org/pypi/pinakes/0.22.1/json` already returned `200`. The simple index is what an
installer actually resolves against, so it is the endpoint that answers *is it published*; the
aggregate JSON is a summary and lags. **A first `unsatisfiable` is not a failed publish** (0.15.1
recorded the same thing) — check the simple index before concluding anything, and re-run the
install rather than re-running the release.

**0.22.2, same standard, 20260811 13:54 — and the same lag, resolved by waiting rather than by
doing anything.** `gh release view v0.22.2` reports non-draft, 13:53:00Z, created by
`github-actions[bot]` — the workflow's own step for the third release running. The simple index
listed `pinakes-0.22.2-py3-none-any.whl` and `pinakes-0.22.2.tar.gz` immediately, while
`uvx --no-cache --refresh --from "pinakes==0.22.2" pnk --version` was still `unsatisfiable`; one
retry a minute later returned **`pinakes 0.22.2`**. Exactly what 0.22.1 recorded, now confirmed as
the normal shape rather than an incident: **the simple index answers *is it published*, and the
installer's own resolver is the thing that lags.** `git merge-base --is-ancestor v0.22.2 main`
passes, so the tag names a commit on `main` rather than one off it.

**0.23.0, 20260811 15:42 — no lag at all, and the artifact was checked rather than the version
string.** The publish step's own log prints `Uploading pinakes-0.23.0-py3-none-any.whl (371.0KiB)`
and `Uploading pinakes-0.23.0.tar.gz (2.1MiB)`, which no cache can fabricate;
`gh release view v0.23.0` reports the workflow's own step created it at 15:35:44Z; and
`uvx --no-cache --refresh --from "pinakes[light]==0.23.0" pnk --version` returned **`pinakes
0.23.0`** on the *first* attempt, unlike the last three releases. `git merge-base --is-ancestor
v0.23.0 main` passes.

**0.24.0, 20260811 22:40 — the lag came back, and the artifact check earned its place.** The
publish step's own log prints `Publishing 2 files`, `Uploading pinakes-0.24.0-py3-none-any.whl
(417.0KiB)` and `Uploading pinakes-0.24.0.tar.gz (2.2MiB)`; `gh release view v0.24.0` reports
non-draft, created 22:34:01Z by `github-actions[bot]`, the workflow's own step; and
`git merge-base --is-ancestor v0.24.0 main` passes. `uvx --no-cache --refresh --from
"pinakes==0.24.0" pnk --version` was `unsatisfiable` on the first attempt and returned **`pinakes
0.24.0`** on a retry — the resolver lag 0.22.1 and 0.22.2 recorded, absent at 0.23.0 and back here,
which settles it as *variable* rather than fixed. **Waiting is the remedy; nothing was re-pushed.**

**Then the check that actually matters for this release**, on a second retry after the same lag
under the extra: `uvx --no-cache --refresh --from "pinakes[light]==0.24.0" pnk ask --help` prints
`--deep` and `--yes` **from the index**. That is the release's whole subject, and a matching version
string would have said nothing about whether it was inside the wheel.

**0.25.0, 20260812 05:45 — no lag this time, and the artifact check passed on the first attempt.**
`gh release view v0.25.0` reports non-draft, created 05:36:02Z by the workflow's own step;
`git merge-base --is-ancestor v0.25.0 main` passes; and the index itself carries both files —
`pinakes-0.25.0-py3-none-any.whl` (435 653 bytes) and `pinakes-0.25.0.tar.gz` (2 301 287 bytes),
read from `https://pypi.org/pypi/pinakes/json` rather than from a green workflow. The resolver lag
0.22.1, 0.22.2 and 0.24.0 recorded did **not** appear, which keeps it *variable* rather than fixed.

**The artifact check, on the release's own subject:**
`uvx --no-cache --refresh --from "pinakes[light]==0.25.0" pnk sync --help` prints
`--clear-cache [paid|transcripts]` **from the index**, and
`uvx --no-cache --from "pinakes[light]==0.25.0" python -c "from pinakes.deep import transcript"`
imports the new module and reports `deep` / schema `1`. A matching version string would have said
nothing about whether E5 was inside the wheel — this is what says it.

**0.25.1, 20260821 07:26 — verified on the first attempt, with no resolver lag.**
`gh release view v0.25.1` reports non-draft, created 07:24:30Z by the workflow's own step;
`git merge-base --is-ancestor v0.25.1 main` passes; and `https://pypi.org/pypi/pinakes/json` serves
`0.25.1` as `info.version` and carries both files — `pinakes-0.25.1-py3-none-any.whl` (437 172
bytes) and `pinakes-0.25.1.tar.gz` (2 318 538 bytes). Read from the index, not from a green
workflow.

**The artifact check, on the release's own subject — and this release is the reason that check
exists in the strong form.** `uvx --no-cache --refresh --from "pinakes[light]==0.25.1" pnk
--version` prints `pinakes 0.25.1`, and
`uvx --no-cache --from "pinakes[light]==0.25.1" python -c "..."` reads the schema builders **out of
the published wheel**: `answer_schema(passages=4)` yields
`{'type': 'integer', 'enum': [1, 2, 3, 4]}`, `subproblems_schema()` carries no `maxItems`, and
`SCHEMA_VERSION` is `2`. That is the fix itself, asserted from the index. **A version string would
have been worthless here in a way it has never quite been before**: 0.22.0 through 0.25.0 all
installed cleanly, reported the right version, imported every module — and `pnk ask --deep` could
not make a single successful call in any of them. The whole point of this release is that
*installable* and *working* had come apart, so *installable* is not what gets checked.

**And one check this list had never made: does the published artifact contain the thing the release
is named for?** `uvx --no-cache --from "pinakes[light]==0.23.0" pnk ask --help` prints `pnk ask`'s
full flag surface from the index, not from this checkout. A version number matching is evidence
about *packaging*; it says nothing about whether the increment is inside the wheel. Cheap, and it
belongs in every release that adds a surface.

**0.25.2, same standard, 20260821 22:30:** `gh release view v0.25.2` reports non-draft, created
22:28:25Z by the workflow's own step; the `Publish to PyPI` step log prints both uploads
(`pinakes-0.25.2-py3-none-any.whl`, 426.9 KiB; `pinakes-0.25.2.tar.gz`, 2.2 MiB); and
`uvx --no-cache --refresh --from "pinakes==0.25.2" pnk --version` → `pinakes 0.25.2`, on the
second attempt — the first read *unsatisfiable* 30 s earlier, the documented resolver lag. The
release is documentation only, so the wheel's expected diff from 0.25.1 is the `__version__`
string alone and the artifact check stops at the install; the four-step flow was not re-run.

**0.25.3, same standard, 20260821 22:47:** `gh release view v0.25.3` reports non-draft, created
22:44:07Z by the workflow's own step; the index's `json` endpoint lists both files
(`pinakes-0.25.3-py3-none-any.whl`, 428.0 KiB; `pinakes-0.25.3.tar.gz`, 2291.6 KiB); `v0.25.3` is an
ancestor of `origin/main`; and `uvx --no-cache --refresh --from "pinakes==0.25.3" pnk --version` →
`pinakes 0.25.3`, **on the second attempt** — the first read *unsatisfiable* while the index was
still settling, which is the documented resolver lag and not a failed upload. Thirty-four versions
now carry files.

**0.25.4, same standard, 20260821 22:55:** `gh release view v0.25.4` reports non-draft, created
22:53:57Z by the workflow's own step; the `Publish to PyPI` step log prints both uploads
(`pinakes-0.25.4-py3-none-any.whl`, 428.0 KiB; `pinakes-0.25.4.tar.gz`, 2.2 MiB); and
`uvx --no-cache --refresh --from "pinakes==0.25.4" pnk --version` → `pinakes 0.25.4`, on the
second attempt after the documented resolver lag. Documentation only; the artifact check stops at
the install.

**0.26.0, same standard, 20260822 01:42:** `gh release view v0.26.0` reports non-draft, created
01:38:43Z by the workflow's own step; the `Publish to PyPI` step log prints both uploads
(`pinakes-0.26.0-py3-none-any.whl`, 435.6 KiB; `pinakes-0.26.0.tar.gz`, 2.3 MiB); and
`uvx --no-cache --refresh --from "pinakes==0.26.0" pnk --version` → `pinakes 0.26.0`, **on the
first attempt** — the documented resolver lag did not appear, which is worth recording because
this file's other entries read as though it always does. **And the release's own subject was read
out of the wheel**, which is the check 0.25.1 taught: `pinakes/deep/suggest.py` is present at 354
lines, carrying `REL = "co-cited"`, `ORIGIN = "deep"`, `co_citations`, `propose`, `for_run`,
`_one_line` and the `link.source_sidecar` call that is the containment check — and `cli.py` in the
same wheel carries `_print_suggestions`, `_suggestions_payload` and `suggest_module.for_run`, so
the printed fragment is reachable from the shipped command rather than merely compiled into the
package.

**0.27.0, and the artifact check inverted, 20260822 06:35:** `gh release view v0.27.0` reports
non-draft, created 06:30:05Z by the workflow's own step; the `Publish to PyPI` step log prints both
uploads (`pinakes-0.27.0-py3-none-any.whl`, 435.6 KiB; `pinakes-0.27.0.tar.gz`, 2.3 MiB); and
`uvx --no-cache --refresh --from "pinakes==0.27.0" pnk --version` → `pinakes 0.27.0` — **on the
second attempt**, the first failing as unsatisfiable while the index caught up, which is the lag
0.26.0's entry noted the absence of. **This release's subject cannot be read out of the wheel,
because the claim is that it is not there**: `tools/mutate.py` is a developer tool, and *"it ships
in no wheel"* is a statement about the artifact like any other. So the check ran in the other
direction — the published wheel was fetched from the index and opened: **78 files, and not one
`tools/` entry or any file named `mutate`**, with `METADATA` reporting `Version: 0.27.0`. A
release whose subject is absent from the artifact still has an artifact claim to verify; it is
just the negative one.

**0.27.1, same standard and the same inversion, 20260822 07:13:** `gh release view v0.27.1` reports
non-draft, created 07:10:01Z by the workflow's own step; the index's `json` endpoint lists both
files (`pinakes-0.27.1-py3-none-any.whl`, 435.6 KiB; `pinakes-0.27.1.tar.gz`, 2364.1 KiB);
`v0.27.1` is an ancestor of `origin/main`; and
`uvx --no-cache --refresh --from "pinakes==0.27.1" pnk --version` → `pinakes 0.27.1`, **on the
first attempt, with no resolver lag**. Its subject is two developer gates, so the artifact check ran
inverted as 0.27.0's did: the published wheel was opened to confirm **78 files, no `tools/` entry**,
`METADATA` reporting `Version: 0.27.1`, and the package itself present at 58 `pinakes/*.py` modules
— the negative claim and the positive one together, since "absent" is only evidence if the wheel is
otherwise the wheel it claims to be. Thirty-eight versions now carry files.

**0.27.2, verified late and found missing by the gate that shipped with 0.28.0, 20260823 01:46:**
`gh release view v0.27.2` reports non-draft, created 20260822 10:06:55Z; the index lists both files
(`pinakes-0.27.2-py3-none-any.whl`, 435.6 KiB; `pinakes-0.27.2.tar.gz`, 2395.9 KiB); `v0.27.2` is an
ancestor of `origin/main`; and `uvx --refresh --from "pinakes==0.27.2" pnk --version` →
`pinakes 0.27.2`.

**Its entry was never written, and no check could see that until now.** The release-order gate had
been checking that this list was *sorted*, which it was — a sorted sequence says nothing about what
is absent from it. The membership half landed hours later, and this is the first thing it caught:
one release verified, released and published, with the record of that verification simply missing.
Read it as the reason the check exists rather than as an anomaly — the list is written by hand, at
the end of a release, which is exactly when a step gets skipped.

**0.28.0, and the check its own subject demanded, 20260823 01:46:** `gh release view v0.28.0`
reports non-draft, created 01:43:57Z by the workflow's own step; the index's `json` endpoint lists
both files (`pinakes-0.28.0-py3-none-any.whl`, 436.0 KiB; `pinakes-0.28.0.tar.gz`, 2429.3 KiB);
`v0.28.0` is an ancestor of `origin/main`; and `uvx --refresh --from "pinakes==0.28.0" pnk
--version` → `pinakes 0.28.0`. **The `json` endpoint and `uv`'s cached index both reported `0.27.2`
for several minutes after a successful upload** — `https://pypi.org/simple/pinakes/`, the endpoint
installers actually read, already carried both files with their hashes. A first look at the wrong
endpoint says *the upload failed*, which is this project's recorded failure mode and would have
been the wrong conclusion.

Its subject is `pnk serve` on a fresh install, so the artifact check is the one the release exists
for rather than a version string: a KB was created and served **from the published wheel**, and
`tools/mcp_handshake_gate.py` completed a real MCP session against it — the fresh resolve took
`mcp` 2.0.0, `serverInfo` came back `{"name": "pinakes", "version": "0.28.0"}` over protocol
`2025-11-25`, and all four `pinakes_*` tools matched the committed schemas. **That is the first
published release on which `pnk serve` has been observed working from PyPI at all**, rather than
inferred from a green job. Forty versions now carry files.

**0.28.1, and the first release whose *"no code path changed"* was checked rather than asserted,
20260823 02:19:** `gh release view v0.28.1` reports non-draft, created 02:12:06Z by
`github-actions[bot]`; the `Publish to PyPI` step log prints `Publishing 2 files`, `Uploading
pinakes-0.28.1-py3-none-any.whl (436.0KiB)` and `Uploaded pinakes-0.28.1.tar.gz`;
`https://pypi.org/simple/pinakes/` carries both; `v0.28.1` is an ancestor of `origin/main`; and
`uvx --no-cache --refresh --from "pinakes==0.28.1" pnk --version` → `pinakes 0.28.1`, **on the first
attempt with no resolver lag**. Forty-one versions now carry files.

Its subject is `tools/release_order_gate.py`, so the artifact check inverts the way 0.27.0's and
0.27.1's did — the wheel's 78 files contain no `tools/` entry and the string
`MAX_VERIFICATION_LAG` appears in none of them, which is what *"it ships in no wheel"* claims.
**But the inverted check has a hole this release exposed**: proving a thing is absent from an
artifact says nothing about what *else* moved in it, and *"no code path changed"* is a claim about
presence. So both published wheels were unpacked and compared, and `diff -r` over the two
`pinakes/` trees returns **exactly one line** — `__version__`, `0.28.0` → `0.28.1`. The other
**72 of the 73 files** under `pinakes/` are byte-identical, and `RECORD` agrees: one changed hash,
the rest untouched. **Count the data files, not just the modules.** 58 of the 73 are `.py`; the
remaining 15 are shipped payload — the `notes` template at three versions, `budget/prices.toml`,
`extract/floors.toml` — and those are precisely the files that change a KB without changing a code
path. A diff restricted to modules would have skipped every one of them and still read as proof.
**That is the claim itself, measured from the index rather than from the diff that made it.** A
repository diff can only show what a commit touched; two wheels can show what a *release* shipped,
which is the question the sentence in the CHANGELOG is actually answering. Cheap enough — two
downloads and a `diff` — that every release claiming to change no code path should now carry it.

**0.28.2, and the standard set one release ago being kept, 20260823 02:55:** `gh release view
v0.28.2` reports non-draft, created 02:53:31Z by `github-actions[bot]`; the `Publish to PyPI` step
log prints `Publishing 2 files`, `Uploading pinakes-0.28.2-py3-none-any.whl (436.0KiB)` and
`Uploaded pinakes-0.28.2.tar.gz`; `https://pypi.org/simple/pinakes/` carried both **ten seconds**
after the workflow ended; `v0.28.2` is an ancestor of `origin/main`. Forty-two versions now carry
files.

**The resolver lagged the index, and this is the cleanest measurement of that gap yet.** With
`simple/` already serving both files, `uvx --no-cache --refresh --from "pinakes==0.28.2"` reported
the requirement **unsatisfiable**; the retry seconds later returned `pinakes 0.28.2`. Two endpoints
disagreeing about the same upload, in the same minute, in the direction this project has twice
misread as a failed publish.

Its subject is documentation, so the artifact check inverts as 0.27.0's, 0.27.1's and 0.28.1's did:
the wheel's 78 files contain no `docs/` entry, which is what *"it ships in no wheel"* claims. **And
the two-wheel diff introduced one release ago ran for the second time, on the claim it was built
for.** `0.28.2` says *no code path changed*; `diff -r` over the unpacked `pinakes/` trees of the
published `0.28.1` and `0.28.2` wheels returns **exactly one line** — `__version__`, `0.28.1` →
`0.28.2` — with the other 72 of 73 files byte-identical, template payload included. **A check is
worth what it costs on its second run, not its first**: two downloads and a `diff`, and a sentence
that four of the last seven releases asserted from the repo diff is now measured from the index for
both of the releases that have claimed it since.

**0.28.3, and the first entry the gate required to be written whole, 20260823 03:15:** `gh release
view v0.28.3` reports non-draft, created 03:14:06Z by `github-actions[bot]`;
`https://pypi.org/simple/pinakes/` carried both files ~40 s after the run ended; `v0.28.3` is an
ancestor of `origin/main`; and `uvx --no-cache --refresh --from "pinakes==0.28.3" pnk --version` →
`pinakes 0.28.3` on the second attempt, the first reporting the requirement unsatisfiable seconds
earlier. Forty-three versions now carry files.

Its subject is `tools/release_order_gate.py`, so the artifact check inverts as 0.27.0's, 0.27.1's
and 0.28.1's did — 78 files, no `tools/` entry — and the two-wheel diff ran a third time on the
*no code path changed* claim: `diff -r` over the published `0.28.2` and `0.28.3` `pinakes/` trees
returns **exactly one line**, `__version__`.

**0.29.0, and the first release whose subject a battery of its own is checking, 20260823 12:57:**
`gh release view v0.29.0` reports non-draft, created 12:55:19Z; `https://pypi.org/simple/pinakes/`
carried both files within two minutes of the tag; `v0.29.0` is an ancestor of `origin/main`; and
`uvx --no-cache --refresh --from "pinakes==0.29.0" pnk --version` → `pinakes 0.29.0` **on the second
attempt**, the first reporting the requirement unsatisfiable seconds earlier — the same lag 0.28.3
recorded, and the reason this file reads `simple/` and never the `json` endpoint. Forty-four
versions now carry files.

Its subject is `tools/batteries/` and a test file, so the artifact check inverts as 0.27.0's,
0.27.1's, 0.28.1's and 0.28.3's did: **78 files, no `tools/` entry, no `batteries` entry**, with
`METADATA` reporting `0.29.0` and the shipped `pinakes/__init__.py` agreeing. The two-wheel diff ran
a fourth time on the *no code path changed* claim — `diff -r` over the published `0.28.3` and
`0.29.0` `pinakes/` trees returns **exactly one line**, `__version__`, with the other 72 of 73 files
byte-identical, template payload included.

**0.29.1, and a documentation release verified by what did *not* change, 20260823 14:05:**
`gh release view v0.29.1` reports non-draft, created 14:03:50Z; `https://pypi.org/simple/pinakes/`
carried both files within two minutes; `v0.29.1` is an ancestor of `origin/main`; and
`uvx --no-cache --refresh --from "pinakes==0.29.1" pnk --version` → `pinakes 0.29.1` **on the second
attempt**, the first reporting the requirement unsatisfiable — the third consecutive release to show
that lag, and the reason this file reads `simple/` and never the `json` endpoint. Forty-five versions
now carry files.

Its subject is `CLAUDE.md` and four `docs/` pages, none of which ship, so **the whole artifact claim
is negative** and the two-wheel diff is the *primary* check rather than a supplement: `diff -r` over
the published `0.29.0` and `0.29.1` `pinakes/` trees returns **exactly one line**, `__version__`,
with the other 72 of 73 files byte-identical. The wheel's 78 entries contain **no `tools/`, no
`docs/`, no `batteries` and no `CLAUDE.md`**. A release whose entire content is instructions to
agents is one a user's environment cannot observe, and that is the thing worth recording about it.

**0.29.2, and an index that said no for six minutes, 20260823 15:03:** `gh release view v0.29.2` reports
non-draft, created 14:54:04Z; `v0.29.2` is an ancestor of `origin/main`; and
`uvx --no-cache --refresh --from "pinakes[light]==0.29.2" pnk --version` → `pinakes 0.29.2`.
**The first attempt, six minutes after upload, reported the requirement unsatisfiable and
`https://pypi.org/simple/pinakes/` listed no file for it** — well past the ~90 s this file has
measured before, and long enough to look like a failed publish rather than a lag. It was not: the
workflow's `Publish to PyPI` step log, which cannot be cached, read `Uploading
pinakes-0.29.2-py3-none-any.whl (436.0KiB)` and `Uploaded pinakes-0.29.2.tar.gz` the whole time.
**Reading the index's silence as evidence is the failure this file already warns about, and it was
nearly committed anyway.** Read the step log first; it is the only source with no cache in front of
it. Forty-six versions now carry files.

Its subject is `CHANGELOG.md`, three `plans/` files and `docs/RETROSPECTIVES.md` — **none of which
ship** — so the artifact claim is entirely negative again, and the two-wheel diff is the primary
check: `diff -r` over the published `0.29.1` and `0.29.2` `pinakes/` trees returns **exactly one
line**, `__version__`, with the other 72 of 73 files byte-identical. The wheel's 78 entries contain
**no `tools/`, no `docs/`, no `batteries` and no `CLAUDE.md`**.

**0.30.0, and a gate that shipped in no wheel, 20260823 15:18:** `gh release view v0.30.0` reports
non-draft, created 15:15:41Z; `v0.30.0` is an ancestor of `origin/main`;
`https://pypi.org/simple/pinakes/` carried both files **on the first poll**, unlike 0.29.2's
six-minute lag; and `uvx --no-cache --refresh --from "pinakes[light]==0.30.0" pnk --version` →
`pinakes 0.30.0`. The publish step's own log was read **before** the index either way, because it is
the only source with no cache in front of it. Forty-seven versions now carry files.

Its subject is `tools/markdown_link_gate.py`, a developer gate that is **deliberately not in the
wheel**, so the artifact claim is negative for the third release running: `diff -r` over the
published `0.29.2` and `0.30.0` `pinakes/` trees returns **exactly one line**, `__version__`, with
the other 72 of 73 files byte-identical. The wheel's 78 entries contain **no `tools/`, no `docs/`,
no `batteries` and no `CLAUDE.md`** — a case-insensitive grep for `CLAUDE` matches exactly one
entry, `pinakes/extract/claude.py`, which is the paid extractor module and belongs there. **A count
is not a verdict; the matching entry was opened rather than assumed.**

**This entry and the row above it were written in the same commit because the gate this release
shipped now refuses anything else.** That is the seventh sequence's `not_behind` rule meeting its
first release, from the other side: the previous four times this pair drifted, the prose was
written and the row was not, and every gate stayed green. Writing them apart is now red by
construction — and the rule was added to `docs/RELEASING.md`'s sweep in the same breath, because a
sweep that meets an unexplained red reads it as a bug in the gate rather than as the instruction it
is.

**0.30.1, and a gate that shipped in no wheel, 20260825 00:07:** `gh release view v0.30.1` reports
non-draft, created 00:06:05Z; `v0.30.1` is an ancestor of `origin/main`; and
`uvx --no-cache --refresh --from "pinakes[light]==0.30.1" pnk --version` → `pinakes 0.30.1`,
resolving on the **first** attempt. The publish step's own log was read *before* the index either
way, because it is the only source with no cache in front of it — it prints
`Uploading pinakes-0.30.1-py3-none-any.whl` at 00:06:01Z and `Uploaded pinakes-0.30.1.tar.gz` at
00:06:04Z. Forty-eight versions now carry files.

Its subject is `tools/fragments.py`, a developer gate **deliberately not in the wheel**, so the
artifact claim is negative for the fourth release running. The published wheel's **78 entries
contain no `tools/` entry at all**, and a grep for `fragments` across every entry matches
**nothing** — the thing this release is about is verifiably absent from what a user installs.
`METADATA` reports `Version: 0.30.1`. **The absence was measured by downloading the artifact from
the index and reading its namelist**, never inferred from `pyproject.toml`'s `packages` list, which
is the claim rather than the evidence for it.

**0.30.2, and the first positive artifact claim since 0.26.0, 20260825 01:05:** `gh release view
v0.30.2` reports non-draft, created 01:04:22Z; `v0.30.2` is an ancestor of `origin/main`. The
publish step's own log was read first, as always — it prints
`Uploading pinakes-0.30.2-py3-none-any.whl` at 01:04:18Z. **Forty-nine versions now carry files.**


**Unlike the three releases before it, this one's subject ships in the wheel**, so the claim is
*present* rather than *absent* and had to be checked the other way round: the published
`pinakes/cli.py` contains `grep -n pinakes` **once** and `check-ignore -v` **zero** times — the
positive proves the new diagnostic shipped, and the negative proves the old one did not survive
beside it, which a positive match alone never establishes. `pinakes/init.py` calls `check-ignore`
five times. 78 entries, no `tools/`, `METADATA` reporting `Version: 0.30.2`.

**One negative check returned 1 rather than 0, and the resolution is the part worth keeping.** The
old substring test `".pinakes/" not in gitignore.read_text()` still appears once in the shipped
`init.py`. Reading the neighbouring lines suggests a docstring; that is an eyeball, not a
measurement. It was settled by parsing the wheel's own `init.py` with `ast` and asking whether the
line falls inside a string-literal span — **it does**, and the live assignment in the shipped file
is `gitignore_unprotected = not protected`. So the expected count is 1 and the assertion was
mis-specified, not the artifact. **A grep count is a claim about text; whether that text is code is
a different question, and only a parser answers it.**

**This release was tagged about forty minutes after its release commit landed, deliberately.** A
review found a defect in the landed code — a remedy naming a diagnostic that prints nothing — and
because the tag had not been pushed, the fix was folded into the untagged `## [0.30.2]` section
rather than becoming an 0.30.3 that corrected a release nobody had received. **Landing and
publishing being separate steps is what made that possible**, and it is the reason
[`docs/RELEASING.md`](RELEASING.md) puts `make release-check` before the **push** and never after.
(It read *"before the tag"* until 20260826 07:02 UTC, when the target became a real gate: the tag has to exist
for anything to be compared, and the push is the irreversible half.)

**And the same forty minutes carried a public defect nobody noticed, which is recorded here because
the paragraph above would otherwise leave a false lesson.** Line 3 of this file read
`**Latest release: 0.30.2**` — *unqualified* — from the release commit at 01:49:42 until the tag at
02:03:33, with PyPI still serving 0.30.1 and `docs/` deploying on every push to `main`. That is the
identical defect caught and corrected at 08:27 the same morning, six hours earlier and unseen.
**The hold worked; the document describing it did not.** Verified 20260825 12:37 by
`git show f3c6864:docs/STATUS.md | sed -n '3p'`. The marker this file now carries during a hold had
at that point been produced by the release procedure **zero times out of two** — `docs/RELEASING.md`
did not ask for it — which is why D-35 was answered with an offline gate rather than a convention
([`plans/20260825_0749-exposure-and-silent-status.md`](https://github.com/lucagattoni/pinakes/blob/main/plans/20260825_0749-exposure-and-silent-status.md)).
**That count is closed as of 20260831 23:10: the gate shipped in 0.31.0 and the marker has been
written at every release commit since** — `c7b0bd9` at 0.31.0 and this release's own at 0.31.1,
each removed in the commit that recorded the upload. **The marker's life and the hold are two
different intervals and this file has conflated them before**: 0.31.1's *hold* — the window in
which `pip install pinakes` really did get 0.31.0 — ran 23:01 to 23:10, nine minutes, while the
*marker* stood from the release commit until this sweep removed it, which is longer by however long
verifying the artifact takes. The marker is deliberately the outer interval: it may outlive the
hold, and must never end before it. **Neither was produced by anybody
remembering.** `tools/status_header_gate.py` requires the marker while line 3 leads the *Published
versions* row and forbids it once the row catches up, so the removal — the half nothing could have
caught, and the reason a convention was refused here — is the half that is now mechanical.

**0.31.0, and the first release to refresh the price table, 20260830 14:54:** verified by **installing it** — `uv run --no-project --with "pinakes==0.31.0" python -c "import pinakes; print(pinakes.__version__)"` prints `0.31.0`. `https://pypi.org/simple/pinakes/` carries `pinakes-0.31.0-py3-none-any.whl` and `pinakes-0.31.0.tar.gz`; the `json` endpoint still said `0.30.2` at the moment this was written, which is the lag this row stopped trusting at 0.28.0. `gh release view v0.31.0` reports non-draft, created 14:54:04Z. **Fifty versions now carry files** — and `0.30.3` is deliberately **not** among them: it was prepared on 20260825, never tagged, and its fix ships inside this release.

**0.31.1, and the first artifact check that reads the thing the release was about, 20260831 23:10:** `uvx --no-cache --refresh --from "pinakes==0.31.1" pnk --version` prints `pinakes 0.31.1` — from the index, on the **first** attempt, with no *unsatisfiable* read. `https://pypi.org/simple/pinakes/` carries `pinakes-0.31.1-py3-none-any.whl` and `pinakes-0.31.1.tar.gz`, and enumerates **fifty-one** versions. `gh release view v0.31.1` reports non-draft, non-prerelease, created 23:10:26Z; the upload is stamped 23:10:22Z. **The subject of this release ships in the wheel, so it was checked *in the wheel*:** the published `pinakes/budget/prices.toml` reads `usd_per_eur = "1.1596"` and `as_of = "20260831 22:52"`, and carries the comment naming `api.frankfurter.dev` as the source. 78 entries, no `tools/`, `METADATA` reporting `Version: 0.31.1`. **That check is the point rather than a formality** — a corrected number in the repository and a stale number in the artifact would have been indistinguishable from every other green signal this release had, which is the failure it exists to fix one layer down.

**0.32.0, and the first release whose sweep corrected the instrument that counts it, 20260902 10:07:** `uvx --no-cache --refresh --from "pinakes[light]==0.32.0" pnk --version` prints `pinakes 0.32.0` — from the index, on the first attempt. `https://pypi.org/simple/pinakes/` carries `pinakes-0.32.0-py3-none-any.whl` and `pinakes-0.32.0.tar.gz`, and enumerates **fifty-two** versions — **counted from the index, not incremented from the previous number**, which matters here because the same sweep found `docs/ROADMAP.md`'s release count had been maintained by addition and was one low. `gh release view v0.32.0` reports non-draft, non-prerelease, created 10:06:20Z; the wheel upload is stamped 10:06:59Z and the sdist 10:07:00Z. **The subject ships in the wheel and was checked there:** the published `pinakes/doctor.py` carries the `paid extraction unreadable` drift check and `pinakes/sync.py` the `PermissionError` guard, across 78 entries with `METADATA` reporting `Version: 0.32.0`. **The hold ran two minutes** — landed 10:05, published 10:07 — and the marker stood from the release commit until this sweep removed it.

**0.32.1, verified with a control rather than by reading a green run, 20260903 10:08:** `uvx --no-cache --refresh --from "pinakes[light]==0.32.1" pnk --version` prints `pinakes 0.32.1` — from the index, on the first attempt. `https://pypi.org/simple/pinakes/` enumerates **fifty-three** versions, **counted from the index, not incremented from fifty-two**. `gh release view v0.32.1` reports non-draft, non-prerelease, created 10:07:51Z and published 10:08:36Z; the wheel upload is stamped 10:08:32Z and the sdist 10:08:34Z. **The subject ships in the wheel and was checked there three ways**: `METADATA` reports `Version: 0.32.1`, the published `pinakes/template.py` carries the `finalize=` hook, `_toml_basic` and the surrogate refusal — and, the one that actually discriminates, `pnk init --name 'Bob'\''s "Special" KB'` against the **published** 0.32.1 writes `name = "Bob's \"Special\" KB"`, which `tomllib` parses back to the exact string typed. **The control fires**: the same command against the published **0.32.0** exits 0 and writes `name = "Bob's "Special" KB"`, on which `tomllib` raises `TOMLDecodeError`. A version string in `METADATA` says only that a wheel was built from a tree carrying that number; the control says the defect is gone. **The JSON API said `0.32.0` for the first minute after the upload succeeded** — the simple index and a retry both said otherwise, so a single read of that endpoint would have reported a failed publish that had not failed. **The hold ran 58 seconds** — landed 10:07:34, wheel on the index 10:08:32.

**0.32.2, and the shortest hold this file has recorded, 20260903 13:09:** `uvx --no-cache --refresh --from "pinakes[light]==0.32.2" pnk --version` prints `pinakes 0.32.2` — from the index, on the first attempt. `https://pypi.org/simple/pinakes/` carries `pinakes-0.32.2-py3-none-any.whl` and `pinakes-0.32.2.tar.gz`, and enumerates **fifty-four** versions, **counted from the index rather than incremented from fifty-three**. `gh release view v0.32.2` reports non-draft, non-prerelease, created 13:08:09Z and published 13:08:48Z; the wheel upload is stamped 13:08:41Z and the sdist 13:08:43Z. **The subject ships in the wheel and was checked there two ways**: all four fixed modules are present across 78 entries with `METADATA` reporting `Version: 0.32.2` — `pairing.py` carrying the orphaned-sidecar gate, `sync.py` the replacement sentence, `cli.py` the `-k` floor and `store.py` the failure-ledger clear — and, the one that actually discriminates, `pnk search -k 0` against the **published** 0.32.2 exits **2** with *argument -k: 0 is not a number of passages — it must be 1 or more*, refused at the parser before any KB is looked for. **The control fires**: the same command against the published **0.32.1** accepts `0`, walks past the parser and exits **1** on *no pinakes.toml found* — a different failure, from a later stage, which is what shows the check is reading the fix rather than the version string. **The simple index said nothing about 0.32.2 for the first minute** while the install from that same index had already succeeded, so its silence was again not evidence; it settled to fifty-four on the next read. **The hold ran 47 seconds** — landed 13:07:54, wheel on the index 13:08:41 — the shortest of the four, against 58 seconds for 0.32.1 and two minutes for 0.32.0, on the same measurement both used: the release merge commit's committer time against the upload stamp in the workflow's own log. **The 82 seconds first written here was composed, not measured**, and so was the landing time it was derived from; `git log` is what corrected both.

**This release's CI went red *after* its artifact was verified**, which is the ordering worth recording. **Both** `[pdf]` legs fail in `tests/test_pdf_trace.py` — the file's `pytestmark` skips on `[pdf]` alone, so `check (light pdf)` and `check (light pdf claude)` both run it and fail-fast cancels whichever is slower, which is why the named job differs between runs (`33617680970`, on `fe58be3`, reports the `claude` leg; `33619808323`, on `603fd9b`, the other) — on an assertion that **straddles the ledger's write-time quantisation**. `cost_usd` is not summed USD: `accountant.py:193` multiplies the EUR estimate back by the rate, `ledger.py:139` quantises that on write at `1e-6` `ROUND_HALF_UP`, and `ledger.py:127` divides back on read. At `1.1596` and at the seed `1.08` the round trip lands on exactly `0.3535000000000000000000000000` and quantise is a no-op; at `1.159` it lands on `0.3534999999999999999999999999`, snaps **up** to `0.353500`, and reads back one ULP above the estimate. **The assertion is unholdable in general** — quantise discards the remainder by design, so it fails for 66% of a 40 000-case sweep, and rearranging the arithmetic does not recover it. Nothing published is wrong and the money error is 1E-28 EUR, but **a verified artifact and a green `main` are two claims, and for 44 minutes this release had only the first**. **CLOSED 20260902 10:51** — `cf1f1cb` rewrote both hops to compare at the quantum the ledger actually stores, and CI run `33621593381` on `7255183` is green across all **fifteen** jobs — counted with `gh run view --json jobs`, having first been written here as *sixteen*, a number that was typed rather than measured and that no gate would have caught. **The money path also gained its first mutation battery that day** — `src-pinakes-budget-ledger.toml` (`aeb32f2`), four mutants, four killed; before it no row under `src/pinakes/budget/` appeared in any of the eleven committed batteries. It names its own **seam** rather than hiding it: the trace recomputes the estimate, so a mutation *inside* `estimate_document` moves both sides of the assertion together and can never be killed there. Every row changes **which** number is carried, never a digit of it, and two `tests/test_ledger.py` guards cover the seam without going through the trace.

**The same test carries a second instance of the same class, four lines below the first, and it is latent rather than live.** Hop 4 asserts `reconciliations[0].cost_usd == expected_usd.quantize(reconciliations[0].cost_usd)`. `Decimal.quantize()` with no `rounding=` takes the **context default, `ROUND_HALF_EVEN`**, while production `quantise` (`ledger.py:96`) is `ROUND_HALF_UP` — the test resolves ties one way and the code the other, disagreeing on **1.81%** of a 40 000-case sweep (`178.6789025…` stores as `178.678903` and the test computes `178.678902`). **It has never fired because `5.00` and `25.00` per MTok make per-token USD exactly six decimals** — `5.00/1e6 = 0.000005` — so `expected_usd` is already at the quantum and no rounding happens at all. A finer price reintroduces it: `3.75/MTok` is `0.00000375`, eight decimals. **Both hops are green for the same kind of reason — the value of a constant the test never mentions.** Hop 2's constant was the ECB rate and it moved on 20260902; hop 4's is the model price and it has not moved yet, which `docs/RELEASING.md` § *Before you start* step 3 now makes a matter of time. Both are being fixed in one commit. Found and reproduced by the implementer; the rounding-mode divergence and the exactly-six-decimals explanation are its measurement, confirmed here against `tests/test_pdf_trace.py:356` and `ledger.py:96`.

**The manual-release step recurred a sixth time, and on the sixth someone finally read the
workflow. It was not a failure at all: at that point there was no step that created a release.**
`.github/workflows/release.yml` validated the tag against `__version__`, built, smoke-tested the
wheel and ran `uv publish`. That was the whole job. `grep -rn 'gh release\|action-gh-release'
.github/` returned nothing, and `git log -S` found it never had — **up to 0.22.0, no workflow in
this repository's history had ever contained a release-creating step.** It has one now: see *Ended
at 0.22.0* below, which is this passage's own correction and sat eleven lines under a claim written
in the present tense.

So `Release: success` was honest every time; it did everything it was asked to. What was recorded
here six times as a recurring flake was an **absent feature diagnosed as a broken one**, and the
diagnosis survived five restatements because each one re-confirmed the *symptom* — `gh release view`
→ *release not found* — which is equally consistent with both explanations. Checking harder was
never going to distinguish them; reading the workflow, once, did it in a minute.

**The rule this row exists for still holds and is now better supported**: verify the artifact, never
the run's own status. The job's `success` covers the PyPI upload because that is all it does.

**Ended at 0.22.0**, when the workflow gained the step it had never had. Six is the final count.

**And [`RELEASING.md`](RELEASING.md) step 8 had said *"create the GitHub release"* the whole
time.** The procedure always treated it as a manual step; this file recorded performing that step as
a failure of automation that was never written. Two documents describing one act, one as routine and
one as an anomaly, for six releases — neither wrong on its own, and the contradiction only visible
by reading them together, which nothing prompts you to do.

Every release from 0.20.1 to 0.21.1 was created by hand and all of them exist. **The remedy is a
step, not an investigation** — `gh release create` needs `contents: write`, which this job does not
request, so it is a small change to a path that runs only on a tag. Proposed rather than taken:
automating it is a decision about the release path, and the manual step is working.

### The same rule, inverted: a run that never reported success had already shipped — 20260811 14:21

**The `docs` run for `2f13ddd` finished both its jobs and deployed the site, and then sat at
`in_progress` indefinitely.** Not slow — **wedged**: `updated_at` froze at `14:21:00`, twenty
seconds *before* the deployment it was waiting on succeeded, and it had not moved 15 minutes later.

| What | State | When |
|---|---|---|
| `build` job | success | 14:20:55 |
| `deploy` job | success | 14:21:19 |
| Pages deployment `5852282213` | `waiting → queued → in_progress → **success**` | 14:21:20 |
| The published site | serves the new content, checked with `curl` | — |
| **The run object** | **`in_progress`, `updated_at` 14:21:00** | still, at 14:36 |

**Neither `gh run cancel` nor the documented `force-cancel` escalation could clear it** — both
return **HTTP 500**. GitHub cannot finalise or cancel its own run, so there is nothing to do from
here but wait for it.

**Every earlier entry in this section is about a green run that had not shipped. This is the
mirror**: a run that never went green, over work that shipped correctly. The rule
[`RELEASING.md`](RELEASING.md) states — *verify the artifact, never the run's own status* — is what
made the difference legible in a minute, and it turns out to cut both ways. **A run's status is not
evidence in either direction.** What answered the question was `curl` against the published page and
the deployment's own status history, neither of which depends on the run object being coherent.

**The operational consequence it looked like it would have — and did not.**
[`.github/workflows/docs.yml`](https://github.com/lucagattoni/pinakes/blob/main/.github/workflows/docs.yml)
sets `concurrency: {group: pages, cancel-in-progress: false}`, deliberately, because a cancelled
Pages deploy leaves the site on the previous commit with no failure shown. The obvious inference is
that a run stuck at `in_progress` **holds** that group and the next `docs/` push queues behind it
forever. **That inference was written here as fact, and the next push refuted it within four
minutes**: the run that added this very section went `queued → in_progress → success` at 14:41 and
its content is on the published site, while `31501008522` was still `in_progress` and still is.

**So a wedged run does not hold the concurrency group** — at least not this one, and the mechanism
is not visible from outside. The claim is corrected rather than deleted because the *shape* of the
error is the reusable part: a plausible mechanism, stated as a consequence, in a note whose whole
subject was the danger of trusting a status signal instead of checking. The check took one push and
one `curl`.

| | |
|---|---|
| Published versions | **0.2.2, 0.3.0, 0.4.0, 0.4.1, 0.5.0, 0.6.0, 0.7.0, 0.7.1, 0.8.0, 0.9.0, 0.10.0, 0.11.0, 0.12.0, 0.13.0, 0.14.0, 0.15.0, 0.15.1, 0.16.0, 0.17.0, 0.18.0, 0.19.0, 0.20.0, 0.20.1, 0.21.0, 0.21.1, 0.22.0, 0.22.1, 0.22.2, 0.23.0, 0.24.0, 0.25.0, 0.25.1, 0.25.2, 0.25.3, 0.25.4, 0.26.0, 0.27.0, 0.27.1, 0.27.2, 0.28.0, 0.28.1, 0.28.2, 0.28.3, 0.29.0, 0.29.1, 0.29.2, 0.30.0, 0.30.1, 0.30.2, 0.31.0, 0.31.1, 0.32.0, 0.32.1 and 0.32.2** — fifty-four, counted from `https://pypi.org/simple/pinakes/` rather than from the `json` endpoint this row used to cite, which lags an upload by minutes and is the endpoint the rest of this file stopped trusting at 0.28.0. **This row fell four releases behind twice — most recently 0.27.0, 0.27.2, 0.28.0 and 0.28.1 — because for eleven days nothing could see it. It is now the gate's seventh sequence.** The sixth reads the *Published on PyPI* prose forty lines below; an enumeration inside a table cell is not line-anchored, so reaching this row needed a `within` anchor scoping the match to the leading bold span, and two such spans are refused rather than resolved to the first. **The membership check and the list it could not see sat in the same file under the same heading** — the most misleading arrangement available, since the gate reported each release present, and it was, in the sequence next door. **The rule that closed it is a relation, not a bound**: this row may lag the release documents but may never lag the prose beside it, because the two record the same event. Measured over every commit on `main`, a lag bound alone left 29 commits green with this row already wrong, while the relation goes red 11 commits and 10 days earlier, with zero false positives over 53. Both are kept — the bound still catches a drift where both lists are forgotten together, which the relation cannot see — and a test asserts both fire, so neither can be deleted while it is green. **0.31.1 corrects the USD→EUR rate the whole budget layer divides by** — `1.08`, its seed value, to `1.1596` — so an installed copy prints EUR figures 7.4% lower than 0.31.0 did for the same USD cost, on `pnk ask --deep` estimates, ledger reservations and `pnk budget` alike, and a EUR cap stops biting 7.4% early. `prices.toml` ships in the wheel, so upgrading is the whole of the remedy; **ledger lines already written keep the rate they were written with**, which is the point of recording `cost_usd` beside it. No `schema_version`, no rebuild, and nothing else about any KB. **0.28.3, 0.28.2 and 0.28.1 each change no code path** — for all three, the wheel published before it and the wheel published as it differ in exactly one line, `__version__`, measured from the index rather than from the repo diff — and **0.28.0 moves the `mcp` requirement from a `<2` cap to a `>=2` floor**, so an environment pinning `mcp` 1.x will not resolve it; nothing about any KB changes either way. **0.27.2 caps nothing a KB can see** but is the release on which `pnk serve` first worked from a fresh install at all. **0.27.1 fixes two developer gates and changes no code path** — no `schema_version`, no rebuild, and nothing about any existing KB. **0.27.0 adds `tools/mutate.py`, a developer tool that is deliberately not in the wheel** — verified by opening the published artifact and finding no `tools/` entry in its 78 files — so nothing about any KB changes: no code path, no `schema_version`, no rebuild. **This list had stopped at 0.24.0 and been six releases behind since 20260812**, while the prose above it recorded every one of those six being verified from the index: a fact split across two places in one file, where only one of them is on the release sweep's checklist. **0.26.0 adds printed link suggestions to `pnk ask --deep`** — it prints and writes nothing, so nothing about an existing KB changes: no `schema_version`, no rebuild, and no new key Pinakes writes. **0.25.1 is the one to know about in this range**: `pnk ask --deep` returned `400` on every live call from 0.22.0 until it, at a cost of €0.00 — so a KB that met that failure lost nothing but the attempt. **0.25.0 adds the run transcript** under `.pinakes/deep/`, which the sweep spares and only `--clear-cache=transcripts` removes; 0.25.2 to 0.25.4 are documentation. **0.24.0 adds `pnk ask --deep`**, the second and last paid entry point — opt-in, and nothing about a KB changes until you type the flag. It **raises two default `[budget]` caps and bumps `notes` to 1.2**, which reaches *new* KBs only: an existing KB stamped its own caps, keeps them, and gets a `pnk doctor` WARN plus a `pnk upgrade` hunk it may decline. No `schema_version` bump and no rebuild. **0.23.0 adds `pnk ask`**, a new free command; it changes nothing for an existing KB — no `schema_version`, no rebuild, no paid code, and nothing about `pnk search`'s behaviour beyond one sentence of its escalation notice. **0.22.2 is documentation and one new developer gate** — it changes nothing for any KB: no code path, no `schema_version`, no rebuild. **0.22.1 is documentation only** and changes nothing for any KB: no code path, no `schema_version`, no rebuild. **0.22.0 adds `pnk init --backend` (`st` or `light`)** and a field to the eval artifact's header; everything else in it is a fix, and nothing changes for an existing KB — no `schema_version` bump, no rebuild. A `--rebuild` now re-chunks paid documents from the extraction cache and says so when it could not. **0.21.1 is fixes only** — a damaged template install reports rather than raising, `pnk doctor` and `pnk upgrade` stop calling a present-but-damaged template uninstalled, and a template read error no longer prints where pinakes is installed; nothing about a working KB changes. **0.21.0 adds `pnk templates`** and lets a template declare the files it writes; both are additive, and a KB created by an earlier release is unaffected. **0.20.1 refuses `vector_tier = "sqlite-vec"`**, a value that was accepted and silently ignored: a KB whose `pinakes.toml` sets it **stops loading entirely** on this release, on every command. The fix is one line — `vector_tier = "auto"` — and changes nothing about how that KB behaves, since it was already getting the NumPy tier. This is the one upgrade in this list that can stop a working KB, and it is a PATCH deliberately (D-12). **0.20.0 adds `pnk upgrade --apply`**, the only thing in Pinakes that rewrites a `pinakes.toml` after `pnk init` — it writes the hunks that fit after printing them, backs the file up to `pinakes.toml.orig`, and refuses the whole run if any hunk conflicts. It changes nothing for a KB recording `notes@1.0`, which still gets `cannot compare` and exit `3`. **0.19.0 adds `pnk upgrade`**, which prints what a template changed and wrote nothing; on every KB that predates the version archive it says `cannot compare` and exits `3`. **0.17.0 bumps the `notes` template to 1.1**, so `pnk doctor` WARNs on every KB created before it: a report, not a fault, and `pnk upgrade` (0.19.0) is what reads it — though on a KB recording `notes@1.0` it says `cannot compare` too, because that content was never archived. **0.18.0 makes that WARN say `cannot compare`** with a remedy naming the manual comparison, because `1.0`'s content was never archived — the message is the whole of what changed for an existing KB. **0.11.0 bumps `schema_version` to 3**, so the first `pnk sync` after upgrading rebuilds the whole index — free, and `pnk sync --rebuild` is what the refusal prints. 0.9.0's upload was refused on first attempt — renaming the repository broke PyPI trusted publishing, which matches on the exact repository name — and succeeded once the publisher was corrected. **0.8.0 renames the paid extractor's API key** to `PINAKES_ANTHROPIC_API_KEY`, so a KB driving the paid path from an older `.env` refuses until the variable is renamed. 0.2.0 and 0.2.1 predate publishing and are **not** on PyPI, so pinning either fails. **0.4.0 and earlier can destroy a sidecar's permanent ULID** (see 0.4.1) — 0.4.1 is the first release without it |
| First upload | 20260728 17:16 UTC (0.2.2) · latest 20260903 13:08 UTC (0.32.2) — **this row has now gone stale three times**: four releases by 20260822, reading 0.23.0 while 0.24.0 to 0.26.0 shipped; **ten** by 20260825, reading 0.27.0 while 0.27.1 through 0.30.0 all published; and **two** by 20260831, reading 0.30.2 through both 0.31.0 and 0.31.1. The third is the one that settles the cause: 0.31.0's post-publish sweep updated the gated row directly above and left this one, **in the same table, one line down**. No sequence in `tools/release_order_gate.py` reads it — the row above it is gated and this one is not, which is the whole difference, and three independent sweeps have now demonstrated that proximity is not a substitute for a gate. **0.32.0's sweep updated it in the same commit as the gated row above** — which is what this row has always needed, and still not what a gate produced, so a fourth staleness remains one forgetful sweep away |
| Extras available | `st`, `light`, `pdf`, `claude` — all four |
| `requires-python` | `>=3.13` |

`PUBLISH_TO_PYPI` is now `true` (set 20260728 17:15 UTC), so **every tag publishes from here on**.
**Two caches sit between a successful publish and seeing it**, and both read as "the upload
failed": `https://pypi.org/pypi/pinakes/json` is CDN-cached and still named 0.6.0 minutes after
0.7.0's files were listed on `https://pypi.org/simple/pinakes/`, and **uv keeps its own index
cache** — `uvx --from "pinakes[light]==0.7.0"` reported the version unresolvable until
`--refresh`. Check `/simple/`, and add `--refresh` before concluding anything (20260801 12:43).
Tagging stays safe by construction: version/tag agreement, the build and an isolated wheel smoke
test all run before the upload step is reached.

Install lines are in the [GUIDE](GUIDE.md#install). Installing from git still works and remains what
you want for unreleased work sitting on `main`.
