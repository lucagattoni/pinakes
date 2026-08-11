# Open corrections

**Audience: an implementing agent. Goal: executor.** Every live item names the file, the current
text and the required text. Nothing here is a judgement call — if an item reads as a question, that
is a defect in this file; say so rather than choosing.

Restructured 20260801 11:30, after the 0.6.0 release: **nine of the original twelve items were
already closed**, most of them as a side effect of the work that closed something else. A list where
two thirds of the entries are done is one nobody reads to the bottom, so the live items are first and
the closed ones are a table.

**Documentation items are no longer here.** Since the ownership decision (20260801 01:24,
`CLAUDE.md`) every `docs/**`, `plans/**`, `README.md`, `CLAUDE.md` and `CHANGELOG.md` correction is
the planner's, and this file held six. They were closed as part of that ownership, not by an
implementer. What remains below is code and tooling.

**It was empty on 20260805 22:18, for the first time since 20260731. It refilled on 20260807, and
again on 20260808 — six live items, and the six arrived five different ways.** **They are described
here by what they are, never by their number**, because closing two of them renumbered the rest and
a paragraph keyed to positions would have been silently wrong the moment it was true of nothing.

*The chunking-blind graph gate* and *`--rebuild` never re-chunking a protected paid document* both
came out of *building* 2d and are invisible from reading the code that contains them, which is the
pattern every entry this list had ever held until 20260808. **The damaged-template traceback broke
it**: found by T3's adversarial review, by reading, on a surface T3 only inherited. **The
`same manifest` gap is a third way again** — it was not found, it was *created*, by the increment
that closed the item standing here before it: T4 resolved the CRLF item (preserve a uniform
convention, refuse a mixed one — closed below) and opened this one in the same breath. **The eval
header's `vector_tier` is a fourth**: T5 fixed a defect in one file and then asked where else that
defect class lives, which found it two files away in code T5 never touched. **`pnk init`'s
half-created KB is a fifth**: T7 built a new surface and asked what it *inherited* rather than what
it introduced — which surfaced something `pnk init` has been capable of leaving since it existed,
and that no increment had reason to look at until one added a new way to trigger it. Building,
reading, shipping, generalising from a fix, and reviewing what a new surface inherits each find a
different class, and none of them finds the others'.

**Three live. Four were live at 0.21.1 (20260810 01:48), all four were answered on 20260811
07:20, and `pnk init` (D-18) is built and closed below.** Each
had stalled on the same thing — its *required* text was "choose between these two defensible
answers", which an implementer may not do — so the list had converged on decisions rather than
fixes. [`20260811_0720-decisions-gates-and-corrections.md`](20260811_0720-decisions-gates-and-corrections.md) takes all four, and every item below now carries a
**Decided** line naming its answer. **They are executable again**; the wall is gone.

**Two of the four were stalled behind a false premise rather than a genuine fork**, which is worth
more than the decisions themselves: item 4 called the full fix unavailable and item 1 called
re-chunking a paid call, and *both were refuted by running the code they describe* —
`lands_inside` works against a target that does not exist, and the extraction cache survives
`--rebuild`. **An item that reads as a decision may only be an unchecked assumption**, so run the
check before escalating one here.

Closing the traceback item also came within one handler of opening the next one. The fix turned a
raw `OSError` into a `PinakesError`, which routed the failure into an `except` two other commands
already had — one answering it *"is not installed here"*, about a template sitting right there.
**A correction can create the item that replaces it**, which is how the `same manifest` gap above
got here. This one was caught inside the same increment and is recorded in the retrospective.

The list refills from use, so an empty one means nobody has run Pinakes lately, never that it is
finished. Note what is **not** here: **both releases in
[`20260729_0256-links-and-graph.md`](20260729_0256-links-and-graph.md) have shipped** — the links
release in 0.5.0–0.6.0, the graph release in 0.11.0 — so that plan is closed and nothing here
unblocks it. What the graph release's own gate established is narrower than it looks, and the
closed `strategy = "structural"` item below is why: `expand` ships `off` because it did not earn its
default *on a corpus where three of the seven edge kinds derived zero edges*.

---

## Live

### 1 · `--rebuild` never re-chunks a protected paid document

**File:** `src/pinakes/sync.py`, `_copy_forward_protected_document`.
**Current:** the chunks of a paid-extracted document are copied verbatim from the index being
replaced, so a change to `[chunking] headings`, `max_tokens` or `overlap` does not reach it —
while `set_meta` stamps the current settings over the whole index.
**Required:** either re-chunk such a document on a rebuild, or record that the index is
inhomogeneous so the drift report can say so.

**Decided 20260811 (D-15, [`20260811_0720-decisions-gates-and-corrections.md`](20260811_0720-decisions-gates-and-corrections.md)): re-chunk from the extraction cache when it is warm;
when it is cold, copy forward as today and record the index as inhomogeneous. Never a paid call on
a rebuild.**

**The "or accept a paid call" half was a false premise, and measuring it is what unblocked this.**
The cache lives at `manifest.state_dir / "cache" / "extract"` and **survives `--rebuild`** — rebuild
builds `index.db.new` beside the old and swaps atomically, and nothing deletes the cache directory.
So `cache.peek(...)` returns the extracted text for free in the common case. A rebuild that spends
money is refused on its own ground: `--rebuild` is the remedy `pnk doctor` prints, and a remedy that
can cost money is not a remedy.

**The `metadata` half of this was closed in 0.16.0** — vectors are now recomputed rather than
copied, since embedding is free and the chunk texts are already in hand. The chunking half is what
remains, and it predates the injection option by three releases.


### 2 · `--apply` writes nothing on the *same manifest* outcome, so that KB can never stop drifting

**File:** `src/pinakes/cli.py`, `run_upgrade` (`applying = args.apply and report.outcome is
Outcome.DRIFTED`).
**Current:** a template bump that leaves the rendered manifest byte-identical produces no hunks and
reports `same manifest`. `--apply` therefore does nothing at all — **including the `[kb] template`
restamp** — so the KB goes on recording the old reference, `pnk doctor` goes on warning, and the
user has no command that records the new one. It is reachable: of the ten commits between
`notes@1.0` and `1.1`, five touched only the starter golden set.

**Not a defect of T4's implementation — T4 specifies `--apply` in terms of hunks and there are
none.** Writing the reference anyway would be behaviour the plan does not describe, so the
conservative reading was taken deliberately and pinned by
`tests/test_cli_upgrade.py::test_same_manifest_under_apply_writes_nothing`.

**Decided 20260811 (D-16, [`20260811_0720-decisions-gates-and-corrections.md`](20260811_0720-decisions-gates-and-corrections.md)): `--apply` restamps `[kb] template` on this outcome,
and the printed report says it wrote the reference with no hunks to show.** Consent rather than
refusal — the same shape D-10 already took for `[budget]`: the write is announced before it happens.
The alternative leaves a KB recording a stale reference, warning forever, with no command that can
fix it.

⚠️ **`tests/test_cli_upgrade.py::test_same_manifest_under_apply_writes_nothing` pins the opposite.**
It is replaced by a test of the new property, not deleted quietly, and the commit names the
behaviour that changed.

**Recorded 20260808 by T4's third review pass**, in the increment that created it.

### 3 · An eval outcome records the vector tier it was *configured* with, not the one that ran

**File:** `src/pinakes/eval.py` (`"vector_tier": settings.vector_tier` in the outcomes header) and
`tools/reachable_ceiling_probe.py`, which copies the line.
**Current:** the header records the manifest's string, so a KB on the default writes
`"vector_tier": "auto"` — which `tools/rfc_corpus/outcomes.json` does today. `auto` is a request to
choose, not a tier, so the field does not answer the question a measurement artifact exists to
answer: *which tier produced these numbers?* T5 fixed exactly this in the index's `meta`, where the
literal is now `search.resolve_tier(manifest)`'s return.

**It bites at T6, not now.** T6's gate compares NumPy-tier and `sqlite-vec`-tier latency and memory
at ≥ 100k chunks. Two such runs on a manifest set to `auto` would produce headers identical in the
one field that distinguishes them.

**Decided 20260811 (D-17, [`20260811_0720-decisions-gates-and-corrections.md`](20260811_0720-decisions-gates-and-corrections.md)): record both.** `vector_tier` keeps its meaning — what
the manifest asked for — and the resolver's return is recorded beside it, in `eval.py` and in
`tools/reachable_ceiling_probe.py`, which copies the line. **No existing value changes**, so
re-running a committed artifact shows no movement where no measurement moved. Recording only the
resolved tier is defensible and simpler, since nothing consumes the field; an artifact that appears
to move when nothing did is the cost that decided it.

**Recorded 20260808 by T5's first review pass**, which found it by asking where else the same
defect class lives.

---

## Closed — recorded so nobody reopens them

| Was | Closed by |
|---|---|
| `pnk init` wrote `pinakes.toml`, `docs/` and `.gitignore` before it knew the template's `files` declaration was legal, so a refusal left a directory that is *almost* a KB — which a second `pnk init` then refuses **as** one. Pre-existing: any failure after that write did it, and T7 only added a new way to reach it | 0.22.0 (D-18). All three checks — declaration shape, the `_versions` rule, and both containment layers — run before the first byte. **The item had rejected this as unavailable**, believing containment could not be judged before the target existed; `lands_inside` resolves the *parent* and `resolve()` is non-strict, so against a path never created `README.md` lands inside and `../escape.md` does not. The narrow hoist stayed rejected for the item's own reason. `copy_extras` split into `validate_extras` and a copy, with `validated=` defaulting to checking anyway so no other caller silently gets an unchecked copy. Guarantee stated as **validated before writing, never atomic** — a symlinked ancestor can still change between check and write. The review pass added the case every test was blind to: a refusal against a directory being *adopted*, where the property is not "root does not exist" but "the user's files are untouched" |
| `graph_gate.check_identity` was blind to `chunking` — it compared `k`, `embedding`, `rerank`, `ranking` and `retrieval` and not the block `5993521` added to `eval.header` so a leg could say what it was built under. Two legs chunked differently are two corpora, so rows paired on `id` were produced by searching different texts and the rechunk was reported as whatever was under test — on the gate that licensed the graph channel's default | 0.21.1. The whole block, with **nothing excepted** — which is the one place it differs from `tools/two_leg_gate.py`, and deliberately: there `chunking.metadata` *is* the independent variable, here it is `graph_channel`. Both tests are built so that copying two_leg_gate's exception list across fails. A block absent from all three legs still compares equal and passes, as the five fields beside it do: the gate already refuses legs not produced by the binary under test, and requiring it would refuse the graph release's own archived artifacts |
| A damaged template install escaped as a traceback, on two surfaces | 0.21.1, and on **five** functions rather than the two this item named — `render_manifest`, `declared_files` and `copy_extras` held the identical unguarded read, so fixing only `describe` and `render_archived` would have left the defect three functions away. `jinja2.TemplateSyntaxError` needed its own arm because it is raised by `Template(...)` and not by `render`, where the existing `UndefinedError` handler sits. **The fix then nearly opened its own replacement**: making the failure a `PinakesError` routed it into `doctor` and `upgrade`'s existing `except`, which answers *"is not installed here"* — advice that sends the owner of a *present but damaged* template to install what they already have. `TemplateNotInstalledError` splits them, with a test on each surface. A third pass found the `OSError` arm printing the install's absolute path, since `OSError.__str__` appends its `filename` and doctor's de-homing strips the *KB* root, which a template is outside by construction |
| CRLF was invisible to the placement predicate, and only `--apply` could be hurt by it — `Path.read_text` opens with universal newlines, so a CRLF manifest is already `\n`-only by the time `hunks` sees it, which is right for a *report* and would have written LF lines into a CRLF file | 20260808, in T4, and the fork it named resolves to **both**. A **uniform** convention is preserved, because a CRLF manifest is an ordinary Windows file and rewriting it is a change nobody asked for; a **mixed** one is refused, because it is already two tools disagreeing and picking a winner silently rewrites lines the user never touched. The report path is unaffected either way, since reporting reads. **A third case the item had not named turned up in review**: `str.splitlines()` also breaks on `\u2028`, `\u2029` and `\x85`, all three legal in a TOML comment — so the report and the writer would disagree about *which lines the file has*. Refused, for the same reason |
| Every document was titled by its filename — all 300 RFC sidecars read `title: rfc9110` rather than *"HTTP Semantics"*, so search results were unreadable, and nothing reported it | 20260805 22:18. `pnk doctor`'s `titles` check counts documents still carrying the minted title, with a sample. **Always OK, never a warning**, and that is the decision rather than timidity: the filename fallback was kept deliberately, so warning would fire on every uncurated KB — most of them, and both committed corpora at **100%**. The first-line heuristic stays **rejected** — an RFC's first line is `Internet Engineering Task Force (IETF)`, so inference mints confidently wrong titles at scale into sidecars the user then commits, and a plausible wrong title is harder to notice than a visibly wrong one. The check and the minter share one `minted_title()`, because a second copy of the rule would fail silently toward reporting nothing |
| `pnk init` could not adopt a directory that already had content — a `.git`, a `README.md` and a `pyproject.toml` made it *"not empty"*, and *"clear this one first"* is alarming about a directory holding the documents you meant to index. **Hit three times independently** | 20260805 22:11. The blanket emptiness test is gone; what replaces it is narrower and stronger — **`init` never overwrites a file that is already there**, so nothing is left for an emptiness test to protect. Adopted files are left byte-identical and named in the output. **The decision as written said to *refuse* any file `init` would write that already exists; implemented literally that refuses on `README.md` and `.gitignore`, which a real repository always has, so adoption would still have been impossible in the exact case the item exists for.** The intent — do not destroy the user's files — is honoured by never overwriting and reporting instead. Two things are called out rather than silently handled: an adopted `.gitignore` missing `.pinakes/` is flagged with the line to add, and `--ci` is refused (an explicit request, so doing nothing would be worse) **before anything is created** — a gap the removed guard had been holding, found by an existing test |
| The heading-coverage check WARNed forever on `code` and `pdf`, which can never carry a heading path — so a KB holding one `.py` file warned on every run with a remedy amounting to *"a limit of the tool"* | 20260805 21:56, as the user decided. **WARN only when `markdown` is at 0%** — the one case a user can fix, where the chunker reads ATX headings and found none, so the corpus is being silently size-sliced. Everything else is reported **OK with a note**, because an un-actionable warning that cannot be cleared is how doctor output stops being read at all, which costs the actionable warnings too. The note now separates three facts that wore the same 0%: `text` **can** carry one (set `[chunking] headings`), `text` with the key **already set** means the grammar was offered those documents and *refused* them, and `code`/`pdf` cannot today. It also corrects a claim 0.13.0 falsified — the old remedy still said non-Markdown types cannot carry a heading path *whatever the document contains* |
| The first sync might be using one core of ten and nobody had measured which — 300 documents over two hours, with `sync.py` embedding one document at a time in a serial loop | **Measured 20260805 21:45, and the answer is no.** 55 modern RFCs (16 557 chunks) rebuilt under `fastembed`: **peak 5.0 cores, mean 4.8 of 10**, over 1 451 samples and 1 497 s. The loop is serial and the backend underneath it is not — ONNX Runtime is already using half the machine. **So the item's own fork resolves to *do not parallelise*:** *"the backend already saturates the machine → the loop is fine, and the win is a bigger batch, not processes"*. Stacking a pool on top would hit exactly what the item warned against — two workers would consume ~9.6 of 10 cores and anything beyond that oversubscribes. **The measurement also vindicated its own instrument in the field:** in the same process tree `uv run` sat at **0.0%** while its child sustained **~490%**, which is precisely the 0.0-cores answer the pre-fix tool would have reported. **Bounded: `fastembed` only** — `sentence-transformers` needs the 2 GB `[st]` extra and stays unmeasured, so nothing here licenses a claim about it |
| A `[chunking]` edit was a silent no-op until `--rebuild` — an incremental sync re-chunks a document only when *the document* changed, so a manifest-only edit reported every file `unchanged`, applied nothing, and said nothing | 20260805 20:20. The index records the `[chunking]` settings it was built under; `pnk sync` names the key that moved and points at `--rebuild`, and `pnk doctor` reports it as `chunking coherence`. **Absence reads as unknown, never as drifted**, so upgrading demands no rebuild of any existing KB. The retrospective is the part worth keeping: the first draft wrote the identity at the end of *every* sync, so the warning fired once and the index then claimed a coherence it did not have — `pnk doctor` reporting OK over chunks built the old way. **A warning that clears itself without the fix being applied is worse than no warning.** Found by running the command a second time; no test asserted persistence, because that only fails on the second invocation |
| Numbered plain-text headings were not detected, so a rigidly sectioned `.txt` corpus was chunked size-based however structural the manifest read — which is what left the 300-RFC corpus with 106 806 chunks and not one `heading_path`, and so bounds the graph release's gate | `[chunking] headings = "numbered"`, 20260805. Opt-in, `text` only, a **new key** so `strategy` stays inert and `structural` gains no retroactive meaning. **The design is that it refuses rather than guesses:** five line-level clauses and then an outline walk over the whole document, and if the walk fails anywhere that document yields **no headings at all** — exactly the pre-grammar behaviour, never a partial labelling. The predicate was written in full *before any corpus was consulted*, and the tests are written against its clauses rather than against a corpus. Golden set unmoved as predicted (`recall@k` 0.9394, MRR 0.8806, both sides). **The RFC measurement this row left outstanding has since been taken**: 20260805 in doubling rounds to 980 documents — 644 accepted overall, **314 of 314** on the modern band — and exercised end to end on 20260806, when 2c captured a golden-set baseline over a 195-document corpus built at `headings = "numbered"` ([§5.4](20260805_1721-metadata-as-retrieval-context.md)) |
| `pnk doctor` printed the operator's home directory — absolute paths in the one command whose output is the natural thing to paste into an issue | Landed 20260805 (`293bf37`). A `_de_homed` helper strips the KB root's prefix from any message or remedy `doctor.py` forwards. The scope is what makes it right: `store.py`, `sidecar.py` and `ledger.py` all build their text from an absolute path because `manifest.root` is resolved, so the fix sits at the forwarding boundary rather than in each raiser. A path genuinely **outside** the KB — the model cache, a linked KB, a packaged `prices.toml` — is left exactly as printed |
| The `[light]` first-sync error prescribed the 2 GB install to a user who chose `[light]` — `sentence-transformers` missing, `fastembed` sitting right there, and the message offered only the torch install the extra exists to avoid | Landed 20260805 17:31 (`43cef55`). `BackendMissingError` takes an `alternative`; `embed.py` finds it with `find_spec` and **never by loading it**, the same reasoning `CLAUDE.md` pins for the paid extractor — a check must not have the side effects of the thing it checks. When an alternative exists the remedy names only the manifest edit, per this item's own test. Its retrospective is the durable part: the pre-existing test looked environment-independent and was not — it blocked only `sentence_transformers`, leaving this checkout's transitively-installed `fastembed` genuinely importable, so both tests now monkeypatch `find_spec` and **name their precondition instead of inheriting `site-packages`** |
| `strategy = "structural"` degraded to size-based chunking in silence — a 300-RFC corpus indexed **106 806 chunks with every `heading_path` empty**, and nothing said so. Three of the seven edge kinds derive from `heading_path`, so they derived **zero** edges on the corpus the graph release's gate was measured against | Detection shipped 20260805 (`_heading_coverage` in `doctor.py`). **This item's own diagnosis was wrong and is corrected here:** it said the Markdown heading grammar "is Markdown-shaped; RFC section numbering is not, so nothing matches", which describes a regex failing to match. What actually happens is `chunk.py:131` — `blocks = _markdown_blocks(text) if kind == "markdown" else _plain_blocks(text)`. `_markdown_blocks` is **never called** for a `.txt` file, and `_plain_blocks` sets `heading_path=None` unconditionally (`chunk.py:254`). **Nothing failed to match because nothing was tried**, which is why tightening a grammar would have fixed nothing. Its evidence line — *"`grep heading src/pinakes/doctor.py` returns nothing"* — has been false since G6, and its `chunk.py` line numbers describe the tree as it was. The remaining half, an opt-in grammar for numbered plain text, **shipped in 0.13.0** — its own row in this table, *"Numbered plain-text headings were not detected"* |
| `pnk doctor`'s model-coherence remedy destroyed an interrupted sync's work — a first sync killed mid-run leaves `meta` with no embedding identity, which read as a model *mismatch* and printed `pnk sync --rebuild`, discarding every embedding already written | 20260804 13:21. `search.py` raises a new `IncompleteIndexError` only when **none** of the identity keys are present; `doctor.py` reports it as its own check, `sync completeness`, WARN, remedy `pnk sync`. A *partial* `meta` falls through to `CoherenceError` — a missing key never equals the expected value — so it can never land in the benign branch. Write order deliberately unchanged: moving the identity write earlier would let a half-built index claim coherence with a model it was only partly embedded under |
| The sync lock's timestamp was UTC while every other stamp was local — identical format, no marker, different clocks, so in summer a lock taken 30 seconds ago read as two hours old | 20260804 13:21. `sync.py`'s `stamp` and `_estimate_only`'s price clock both use `datetime.now(UTC)`, matching `lock.py`. Pinned by tests that run under a non-UTC timezone — the first draft used the file's own `run()` helper, which hardcodes `now=`, and would have passed whichever clock the code used |
| The first sync was multi-hour and completely silent — ~2.4 documents/minute, 300 documents over two hours with no output, so "working" was indistinguishable from "hung" | 20260804 13:21. `SyncOptions.progress` is called `(done, total)` after each document; the CLI wires a throttled, self-overwriting line on a TTY when not `--quiet`. An adversarial review caught the closing newline firing only at `done >= total`, so a `[budget]` cap or any early exit left a `\r`-terminated line for the report to print onto — `finish()` is now called unconditionally in a `finally` |
| `uv add "pinakes[light]"` failed in the one place a KB user runs it — a knowledge-base directory has no `pyproject.toml`, so the documented install line exits `No pyproject.toml found` | 20260804 13:10. `docs/GUIDE.md` leads with the two forms that work in a bare directory — `uv init` first, or `uvx` with no install at all. The plain `uv add` lines stay, since a KB inside an existing project is the other real case |
| Same-host lock reclaim was documented in `pnk doctor` and not in the GUIDE, which offered only `--force-unlock` — the destructive remedy — for a symptom the safe path already handles | 20260804 13:10. The GUIDE's troubleshooting row now says a lock left by a dead process **on this host is reclaimed automatically** by re-running `pnk sync`, and bounds `--force-unlock` to another host. It also says to check the process rather than the age, because the lock's clock is UTC and an older KB's manifest is local |
| `corpus-probe-run.md` required a per-kind edge census and no tool emitted one | Shipped 20260804. `edge_census()` reads the count off the same in-memory `Graph` the traversal walks — no re-query, no parallel computation — and always returns every kind, **including the zeroes**, since a kind absent from the output is indistinguishable from a kind at zero. Its own review caught the first version counting hub buckets of one, which would have made `co-located` and `shared-tag` unable to report 0 on any populated corpus — the exact case it exists to surface |
| `docs/STATUS.md`'s header was not gated and drifted four releases — it read `0.4.1` while the roadmap, the PyPI table and `__version__` all said `0.7.1` | `tools/status_header_gate.py`, 20260803 22:43. Parses line 3 for the exact `**Latest release: x.y.z**` shape and compares it against `pinakes.__version__`; a missing, moved or reformatted line fails as loudly as a wrong version. Wired into `check.sh` with its own CI job carrying a negative check |
| `tools/link_density_gate.py` died with a `ValueError` on a non-canonical root — every `/tmp` path on macOS, and running it against a copy is exactly what an executor is told to do | 0.7.1. `census` resolves the root once, so the denominator and the `relative_to` share one base |
| `tools/fragments.py` spliced **two `### Added` headings** into one section, and filed a `Fixed:` entry under `Added` — silent, and it lands in an artifact that cannot be re-uploaded | Fixed with a test (`tests/test_fragments.py`). `_merge_into_section` reuses an existing `### Category` heading, bounded to the anchor's own section so an older release's heading is never written into |
| The local source walk escaped the KB: a `..` in `[sources] include` minted sidecars outside it, an absolute pattern was a bare `NotImplementedError`, and a symlinked directory carried the walk out with no `..` anywhere. Live since before 0.5.0 | 0.7.1, as its own increment. **A fourth defect was found by a test written to pin *correct* behaviour** — a legal `..` landing inside the KB kept the `..` in the document key, so one file reachable two ways indexed once and failed twice |
| `sidecar.py`'s docstring overstated the 1.1 → 1.2 fix | Now says *"three of the four"*, and that `0755` becomes int **755** |
| `CHANGELOG.md` `[0.5.0]` stated one break twice, once over-broadly | One statement, carrying the *uniformly-keyed nested mapping* precision |
| `docs/MANIFEST.md`'s `rel` row credited the user, not `pnk link` | Fixed on the L6 branch |
| `docs/STATUS.md`'s verified-install claim omitted the manifest edit | Rewritten and re-verified against **0.6.0** from the index, 20260801 11:10 |
| Both 🚫 rows listed link-coverage reporting, which shipped in v0.1 | Moot: the links-release row left both tables at the final cut |
| The plan's baseline said 0.4.0 and a stale `main` | Re-baselined at `6421cb1`, 20260801 |
| The verification table named two tests that do not exist | Repointed; `tests/test_verification.py` green |
| L6 named two tests L5b already owned | L6 shipped with distinct names |
| The iteration log was out of chronological order | Sorted, and now in `20260801_0102-links-and-graph-log.md` — 25 rows, verified sorted |
| L6 review 7's freshness test never entered the freshness branch | Review 8b closed it the other way; the prescribed fix would now pin behaviour review 8 replaced |
| L7 shipped without two of its four Docs items | Both fixed before the 0.6.0 tag. **The rule it earned:** the last step before declaring an increment done is to re-read its own Docs list and grep for each sentence the plan quotes |

---

## Not to be fixed — recorded so nobody tries

- **A sidecar carrying its own `%YAML 1.1` directive** is parsed at 1.1, so `country: NO` becomes
  `False`. Frozen in 0.5.0; a `changelog.d/` fragment already recorded it.
- **An integral `!!float`** keeps its tag and gains quotes on rewrite. Same fragment.
- **A uniformly non-string-keyed nested mapping** is accepted and coerced. A stated residual in
  `docs/MANIFEST.md`'s bounds table, not a defect.
- **The `v0.5.0` tag annotation** says "Three breaking changes". Tag annotations are not cleanly
  rewritable and the tag is published; the release body and CHANGELOG are the corrected records.
- **A raw NUL byte reaches user-facing output** from a hand-written `[[links.kb]] path` using the
  `\u0000` escape — unreachable from `argv`, which cannot carry one. Sanitising the path into the
  message would cost the *name what the author wrote* property L6 review 9 exists to protect.
