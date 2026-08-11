# Decision — both gates answered, and the four open corrections unblocked

**Audience: the coder and the planner. Goal: executor.** DECIDED by the user, 20260811 07:20, on
recommendations grounded in the four measurements in § *What was checked first*. Eight decisions:
the two gated increments of the template release, the four live open corrections, and two proposals.

**This record is the authority for all eight.** Where
[`20260804_1016-template-release.md`](20260804_1016-template-release.md) or
[`20260731_1202-open-corrections.md`](20260731_1202-open-corrections.md) describes one of these as
undecided, this file supersedes it.

---

## What was checked first — four measurements, and two of them changed the answer

**None of these is a fact anyone could have inferred from the item that needed it**, which is the
reason this section leads. Two recommendations were drafted one way and rewritten after the check.

| # | Question | Answer, and how |
|---|---|---|
| M1 | Does `lands_inside` work against a target that does not exist yet? | **Yes.** Run directly against a fresh temp path never created: `README.md` → `True`, `../escape.md` → `False`, `eval/questions.yaml` → `True`. It resolves the *parent*, and a non-strict `resolve()` needs no existing directory |
| M2 | Does the extraction cache survive `--rebuild`? | **Yes.** It lives at `manifest.state_dir / "cache" / "extract"` (`manifest.py:250`). `--rebuild` builds `index.db.new` beside the old and swaps atomically (`sync.py:999-1000`); nothing in `sync.py` or `store.py` deletes the cache directory |
| M3 | Is a ≥100k-chunk corpus reachable without a new tool? | **Yes.** `tools/build_rfc_corpus.py --count 300` produces the 106 806-chunk corpus its own docstring records. T6's precondition 1 needs no generator written |
| M4 | Does anything consume the eval header's `vector_tier`? | **No.** No test asserts it and no tool reads it — so changing it breaks nothing, and the choice is about what a measurement artifact should *say*, not about compatibility |

**M1 and M2 each falsified the premise of the item that depended on them.** Open-corrections item 4
rejected the full fix as unavailable, and item 1 framed re-chunking as costing money. Both were
written by people reasoning about the code rather than running it. **Read the sibling function
before the decision table** — the same lesson D-4 earned, met twice more in one sitting.

---

## The eight decisions

### D-13 — T6 (the `sqlite-vec` tier): **deferred, with a named trigger** 🚫 not scheduled

**Not started, and not abandoned.** The precondition is cheaper than the plan assumed (M3), and the
interpreter here loads extensions (`enable_load_extension: OK`, measured 20260808), so nothing
blocks it technically.

**Why defer anyway, and this is the load-bearing reason:** the gate as written cannot answer the
question a pass would be buying. Performance is measured on an unlabelled ≥100k-chunk synthetic
corpus; *equivalence* is measured on `tests/demo-kb` at ~30 documents with the tier forced. T6's own
text states that bound and accepts it — **nothing in a passing gate shows the two tiers agree at
100k**. So a pass licenses a tier on partial evidence, and the missing half needs a labelled large
corpus, which is [`20260801_0749-realism-corpus.md`](20260801_0749-realism-corpus.md)'s territory.

**The trigger, written before the fact so it is a trigger and not a mood: a KB that is actually
queried crosses ~50 000 chunks *and* its search latency is a felt problem.** Not "a corpus exists
above the threshold" — one does already (the 300-RFC corpus), and it is an instrument nobody
searches interactively. The tier is a performance feature, and shipping one without a felt problem
is how a project acquires complexity it never needed.

**What stays true meanwhile:** 0.20.1 already made the config surface honest — `vector_tier =
"sqlite-vec"` is refused at load time rather than accepted and ignored — so no user-facing claim is
waiting on this. **The name stays in `CLAUDE.md`'s unbuilt-work table** (D-9).

### D-14 — T8 (a second template): **no-go, closed** ✅

**The gate was run on 20260808 and fails on leg 3.** Recorded because a failed gate that leaves no
record gets re-run.

| Leg | Verdict | Evidence |
|---|---|---|
| 1 · a second real KB exists and has been used | **passes, not via `pinakes-kb`** | The dogfooding KB the gate names has one commit, an empty `docs/` and no `.pinakes/` — created 20260804, never used. `pinakes-corpus-rfc` (600 documents, synced, its own `FRICTION.md`) carries the leg |
| 2 · diverges in ≥3 settings, each for a stateable reason | **fails** | Diffed against a fresh `notes@1.1` stamp: the only owner-chosen divergences are `[embedding] provider` and `[rerank] provider` — two settings, **one** reason (a `[light]` install). The `[budget]` differences are template drift from `notes@1.0`→`1.1`, not choices |
| 3 · ≥1 divergence not expressible as a manifest value | **fails** | Every divergence in every admissible KB is a manifest value |

**`/Users/luca/pinakes-rfc-corpus` looks like the strongest candidate and is not admissible.** Its
`headings = "numbered"` and `max_tokens = 414` carry written rationales, but
`tools/build_rfc_corpus.py` writes that manifest from a hardcoded `MANIFEST` string — it was never
stamped from `notes`. Those are a tool's settings, not a KB owner's usage.

**Waiting does not help.** More KBs of the same kind cannot move leg 3; re-opening needs a
*different kind* of KB. So T8 is closed rather than left gated, and **the gate's own redirect is
taken instead**: *"a divergence that turns out to be a missing default in `notes` — the correct
action is to change `notes`, not fork it."* Both KBs stamped from `notes` immediately edited the
same two provider keys. That is D-20.

### D-15 — open correction: `--rebuild` and protected paid documents → **re-chunk from the cache when warm; record inhomogeneity when cold**

**The item's binary was false, per M2.** The extracted text is already on disk in
`.pinakes/cache/extract/` and survives the rebuild, so `cache.peek(cache_dir,
content_hash=…, fingerprint=…)` returns it for free in the common case.

* **Warm cache → re-chunk**, so a `[chunking]` edit reaches the document like any other.
* **Cold cache → copy forward as today, and record the index as inhomogeneous** so the drift report
  can say the settings stamped over the index are not true of every document in it.
* **Never a paid call on a rebuild.** Rejected outright: a rebuild that silently spends money
  violates the §5 consent model, and `--rebuild` is the remedy `pnk doctor` prints — a remedy that
  can cost money is not a remedy.

### D-16 — open correction: `--apply` on the `same manifest` outcome → **restamp `[kb] template`, and say so**

`--apply` restamps `[kb] template` when the rendered manifest is byte-identical, and **the printed
report states that it wrote the reference with no hunks to show.**

**The objection is real and is answered by consent rather than by refusal**, which is the same shape
D-10 already took for `[budget]`: the write is announced before it happens. The alternative — a KB
that records a stale reference, warns in `pnk doctor` forever, and has no command that can fix it —
is a dead end the user cannot leave.

⚠️ **`tests/test_cli_upgrade.py::test_same_manifest_under_apply_writes_nothing` pins the opposite
and must be replaced, not deleted quietly.** Its replacement asserts the new property, and the
commit says which behaviour changed and why.

### D-17 — open correction: the eval header's `vector_tier` → **record both**

`vector_tier` keeps its current meaning (**what the manifest asked for**) and the resolver's return
is recorded beside it. Same change in `src/pinakes/eval.py` and
`tools/reachable_ceiling_probe.py`, which copies the line.

**Both, rather than replacing, for one reason that outlives the field:** no existing value changes,
so re-running a committed artifact shows no movement where no measurement moved
(`tools/rfc_corpus/outcomes.json` would otherwise go `auto` → `numpy`). Recording only the resolved
tier is defensible and simpler — nothing consumes the field (M4) — but a measurement artifact that
appears to move when nothing did is a cost this project has paid before.

### D-18 — open correction: is `pnk init` transactional? → **yes: hoist the full validation before any write**

**The item rejected this as unavailable and M1 says it is available.** Declaration shape, the
`_versions` rule, target containment *and* template-source containment all run before `mkdir`.

* **The narrow hoist stays rejected** for the item's own reason: leaving containment behind makes
  the guarantee half-true, which is worse than an honest failure.
* **`init` already does exactly this for `--ci`** —
  `test_ci_refuses_an_existing_workflow_before_creating_anything` pins it, and its docstring records
  that the refusal *"left a half-made KB"* until it was moved. So this makes one guarantee uniform
  rather than inventing a new one.
* **Claim "validated before writing", never "atomic".** A symlinked *ancestor* of the target can
  change between the check and the write, and nothing here closes that. Say so where the guarantee
  is documented.
* Split `copy_extras` into a validate half and a copy half rather than validating twice — two
  callers of one rule is how the two drift apart.

### D-19 — proposal: **automate the GitHub release step**

Add a release-creating step to `.github/workflows/release.yml`, with `contents: write`, **after
`uv publish`** so a failure there can never block publishing.

**Context this closes:** no workflow in this repository's history has ever created a GitHub release
(`git log -S`), and `docs/RELEASING.md` step 8 has always said to create it by hand. `docs/STATUS.md`
recorded doing so as a *recurring workflow failure* six times before anyone read the workflow.

**Decided against keeping it manual, and the reasoning is narrow:** documenting it — done on
20260810 — already banked the whole benefit of the manual option, which was preventing
re-investigation. What remains is toil performed 25 times. The cost is honest: the job's token
broadens beyond `id-token: write`, and there is one more thing whose success must be **verified on
the next real tag rather than assumed** — which is this repository's standing rule anyway.

### D-20 — proposal: `pnk init --backend`, and a false sentence in the GUIDE

**Two things, and only the second is a decision.**

1. **`docs/GUIDE.md:180` is false and is corrected regardless.** It says `pnk init` stamps
   `sentence-transformers` *"because it cannot see which extra you installed"*. It can:
   `importlib.util.find_spec` reports exactly that, and `embed.py` already uses it to name an
   alternative in `BackendMissingError`. The behaviour is fine; the explanation is wrong.
2. **`pnk init` gains `--backend st|light`**, stamping the matching `[embedding]` and `[rerank]`
   providers.

**Detecting the installed extra and stamping it was rejected**, and this is the reasoning that
matters: `pinakes.toml` is portable and committed, so stamping a machine-local fact bakes the
author's install into a file collaborators read, and the KB then fails on a machine carrying the
other extra. An explicit flag records a *choice*; sniffing records an *accident*. The default stays
`sentence-transformers` — a user who omits the flag is where they are today.

---

## Build order

Each is its own increment, its own branch, its own landing —
[`docs/BUILDING.md`](../docs/BUILDING.md), never batched.

| Order | Decision | Why here |
|---|---|---|
| 1 | **D-18** — `init` validates first | Self-contained; the `--ci` precedent is already in the file |
| 2 | **D-16** — `--apply` restamps | Self-contained; replaces one named test |
| 3 | **D-17** — both tiers in the header | Two files, one line each |
| 4 | **D-15** — re-chunk from the cache | The largest, and the only one touching the paid path |
| 5 | **D-20** — `--backend`, and the GUIDE sentence | Touches `init`, so it follows D-18 |
| 6 | **D-19** — the release workflow | Last, so the release it automates is the one cutting this work |

**D-13 and D-14 are records, not builds.** They land with this file.

**Every one of these is a `Fixed`-or-`Added` changelog entry**, so the batch cuts as a MINOR
(`--backend` and the header field are additive) once the last has landed.
