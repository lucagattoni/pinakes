# Decision — `parent-child` stays transitive, and its cost is measured before G5

**Audience: the coder and the planner. Goal: executor.** DECIDED by the planner, 20260804 18:44,
raised by G3's implementer as a spec defect rather than worked around — which is what the go
decision asked for.

## The question · **CLOSED 20260804, answered by § The decision and by `graph/edges.py::_hierarchy_edges` — and the cost it calls unmeasured was measured 20260804 21:05**

`parent-child` derives from a `heading_path` prefix relation within one document. Its **arity was
never specified.** G3 built it transitively: every ancestor path joined to every descendant path, so
a section with *a* chunks above a subsection with *d* chunks yields *a·d* rows. Measured on
plausible document shapes, that is **5.8×–53.5× the chunk count**.

It did not bite on the RFC realism corpus — but only because every chunk there has an empty
`heading_path`, so `parent-child` derived **zero edges**. The cost is real and unmeasured.

## The decision · **ALL THREE REQUIREMENTS CLOSED.** Requirements 1 and 2 closed 20260804 (ceiling measured 21:05; the `--drop parent-child` arm shipped in 0.11.0). **Requirement 3 CLOSED by the user 20260825 18:16 UTC (recorded here 18:41): its antecedent is measured false on every real corpus, so the conditional never fires and `parent-child` stays transitive exactly as built**

**Keep it transitive, as built.** Three additions, none of them code today:

1. **A measured ceiling is required before G5's gate runs.** Derive against a corpus whose chunker
   actually populates `heading_path` and record `parent-child` edges per chunk, wall-clock, and
   index growth. **The only corpus this has run against derived zero of them**, so every number
   above is a projection.
2. **`parent-child` becomes a second G5 arm**, beside `--drop sibling`. `select_kinds(drop=[...])`
   already makes it a flag.
3. **If the ceiling is alarming, the immediate-parent variant is the arm to measure** — not a
   change to make first and measure afterwards.

> ### ✅ Requirement 3 — CLOSED. Taken by the user **20260825 18:16 UTC**; recorded here 18:41
>
> **A conditional whose antecedent is false closes without deciding anything.** Requirement 3 reads
> *"**If** the ceiling is alarming…"*, and the ceiling is measured **not** alarming on every real
> corpus: **4.95** `parent-child` rows/chunk on this repository's own documents, **3.80** across 300
> real technical specifications re-chunked through the real `chunk_document` and the real fastembed
> tokenizer, and **0 of those 300** reaching the synthetic **53.42**. The 53.42 figure is real but it
> comes from a **purpose-built worst-shape corpus**, which is what it was built to be — it bounds the
> shape, it does not describe one anybody has.
>
> **What this closes, and what it does not.** It closes the *cost* question. `parent-child` **stays
> transitive**, unchanged, and **no immediate-parent arm is owed**. It decides **nothing** about
> retrieval quality: the arm was never rejected on quality and is not rejected here.
>
> **The misreading that kept this open for 21 days.** *"It would be deciding a retrieval question on
> a cost argument"* — in *Why not the alternatives* below — governs **adopting** immediate-parent-only
> as the default. It does **not** forbid *declining to measure* it. Reading it as a bar to closing
> bundled this requirement to the G5 gate re-run, and the two are independent.
>
> **What would re-open it:** a real corpus measuring an alarming `parent-child` ceiling. The
> antecedent is a measurement, so it can fire later; this closes the requirement, not the question.

## Why transitive

**It is what was measured.** `tools/reachable_ceiling_probe.py`'s predicate is

    def _is_prefix(a: str, b: str) -> bool:
        return a != b and (b.startswith(a + " > ") or a.startswith(b + " > "))

— **any** ancestor, in **both** directions, not the immediate parent. The 12-failing/9-liftable
figure that unblocked the graph release
([`20260804_1442-decision-g3-go.md`](20260804_1442-decision-g3-go.md)) was produced under that
relation. Narrowing the shipped edge set to immediate-parent-only would mean **the measurement no
longer describes what ships**, and it narrows it in the direction that costs reach: at depth 2 a
grandparent is one hop away transitively and two hops away immediately, and 2 hops is the whole
budget the precondition was measured against.

**And arity is a retrieval-quality question, in the same class as `sibling`.** The go decision
refused to let a reachability ceiling choose the kind set, and sent that question to G5's gate. The
same reasoning applies here, for the same reason: a ceiling gauge cannot rank, and an argument
cannot measure.

## Why not the alternatives · **the *Immediate parent only* row is not a rejection — and its conditional did NOT fire on any real corpus (3.80 rows/chunk over 300 real specifications; the 53.42 that looked like a firing was a purpose-built worst-shape corpus). Requirement 3 closed by the user 20260825 18:16**

| Option | Why not |
|---|---|
| **Immediate parent only** | Cheap and tempting, but it changes the relation the probe measured and shortens reach at exactly the depth the precondition tested. It would be deciding a retrieval question on a cost argument. It is the right thing to *measure* if the ceiling proves alarming — as an arm, not as a default |
| **Hub the hierarchy** | Contradicts APPROACH §3, which keeps hierarchy unhubbed on purpose. `in-section` is already the per-document heading hub; adding a second hub over the same structure changes the node model to solve a row-count problem |
| **Cap the arity** | An arbitrary truncation, silent by construction, in the one kind whose whole content is structure. A cap that fires is indistinguishable from a corpus that has no deep nesting |

## What is already true, and needs no work

* **The arity is visible, not implicit.** `tests/test_edges.py::test_the_hierarchy_row_count_is_pinned_because_it_is_the_product_of_two_sections`
  pins the row count as a product, so a change to the relation fails a test that names why.
  `test_hierarchy_matches_the_naive_prefix_predicate` pins equivalence with the naive form.
* **Derivation is linear in chunks**, quadratic only in a document's *distinct heading paths* — the
  implementation looks ancestors up rather than testing every chunk pair. The row *count* is the
  concern here, never the derivation time.
* **The per-kind census reports it**, so an explosion is a number in the report rather than a
  surprise in the index size.

## The standing risk this leaves · **no longer a guess — measured 20260804 22:39 at 53.42 `parent-child` rows/chunk and +113.4% index growth on a worst-shape corpus; requirement 1 is discharged**

**A corpus with deep heading nesting and large sections could make `parent-child` the dominant
kind**, on a `pnk sync` that already runs from three git hooks. That is stated rather than mitigated,
because mitigating it now means choosing a shape for the relation before anyone has measured one.
Requirement 1 is what converts it from a guess into a number.
