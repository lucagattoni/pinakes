# The provider is part of what a model is: P1 and P2 (P1 released in 0.32.9, P2 in 0.33.0)

**Audience: the agent building it. Goal: executor.** Written 20261102 10:10 UTC, the day the user
resumed development ("officially resume from now") and chose to start with P1.

## Evidence

Two findings from the public benchmark repository, [README § The same Pinakes on its other
provider](https://github.com/lucagattoni/pinakes-datasets-benchmark/blob/deb2329/README.md#the-same-pinakes-on-its-other-provider)
(commit `deb2329`), each re-read against this repository's `main` at `dee3f04`:

1. **A stored threshold is accepted by the other reranker provider.** `confidence_of`
   (`src/pinakes/search.py`) accepts `[retrieval.confidence]` when `fitted_for` equals
   `reranker.info().fingerprint()`, which is `model@revision` (`ModelInfo.fingerprint`, `embed.py`)
   and names neither the provider nor the scale. sentence-transformers scores lie in 0 to 1,
   fastembed's are raw logits. Reproduced 20261031 23:43 UTC and 20261102 09:08 UTC: changing only
   `[rerank] provider`, and then also `[embedding] provider` with `pnk sync --rebuild`, left the
   thresholds applied, and a `high` became `low` with no warning. On 1,140 answerable and 154 null
   held-out questions the sentence-transformers thresholds on fastembed scores labelled 26.7% of
   the answerable ones low (1.3% with fastembed's own); the other way round everything was `high`.
2. **fastembed ignores `revision`.** `embed.py` passes sentence-transformers the revision and passes
   fastembed none; `_FastembedBackend.info` and `_FastembedReranker.info` still return the
   manifest's. Measured 20261031 23:44 UTC: asked for the oldest of 31 commits, fastembed 0.9.1
   loaded the newest. So `docs/MANIFEST.md`'s "pin it once settled" pins files under
   sentence-transformers only. The index's mismatch check runs under both providers and compares the
   manifest with the manifest as recorded at build time, never the files that loaded.

## P1: a revision under fastembed is a label (built in this branch)

Scope: say what is true, today, without adding surface. No new check name, flag or key.

- `src/pinakes/doctor.py`: `_revision_check`, called by `_backends`. Under fastembed an unset
  revision is still a `WARN`, but the remedy no longer says "pin it": it says Pinakes passes none and
  names `sentence-transformers`. A revision set under fastembed is a `WARN` ("a label, not a pin"),
  not `OK`. Every other provider is unchanged.
- `src/pinakes/calibrate.py` docstring: the scale is the provider's, and `fitted_for` records
  neither.
- `docs/MANIFEST.md` (`[embedding]`, `[retrieval.confidence]`, `[rerank]`) and `docs/DOGFOODING.md`
  (the WARN row): the same facts, dated.
- `docs/GUIDE.md` and `docs/CLI.md`: "same default models" and "ids identical" now say the files
  behind an id are not the same. `docs/README.md`: this plan's row.
- Tests: `tests/test_doctor.py::test_an_unpinned_fastembed_model_is_not_told_to_pin_a_revision`,
  `::test_a_revision_set_under_fastembed_is_reported_as_a_label_and_not_ok`,
  `::test_each_fastembed_model_is_judged_by_its_own_revision`,
  `::test_each_section_is_judged_by_its_own_provider`,
  `::test_the_other_providers_keep_the_advice_to_pin_and_the_ok_for_a_pin`,
  `::test_a_built_in_backend_that_knows_no_revision_gets_the_placeholder`,
  `::test_a_pinned_sentence_transformers_model_is_ok`,
  `::test_a_fastembed_label_is_printed_from_the_manifest_and_not_the_backend`,
  `::test_a_pinned_sentence_transformers_line_is_printed_from_the_manifest_and_not_the_backend`,
  `::test_an_unset_fastembed_revision_stays_unset_whatever_the_backend_reports` and
  `::test_the_model_cache_line_appears_once`; rows in `docs/VERIFICATION.md`; mutants appended to
  `tools/batteries/src-pinakes-pairing.toml` (which already claims `doctor.py`).
- Out of scope, deliberately, and left for a later row: the threshold identity (P2); the template
  line `# revision = "…" # pin the HF commit sha once you are settled; pnk doctor reports the current
  one` in `src/pinakes/templates/notes/pinakes.toml.j2` and `_versions/1.1`, `_versions/1.2`, which
  gives the same futile advice at its source and says "reports the current one" where `pnk doctor`
  prints a placeholder for a built-in backend (changing a template needs a version bump); and the
  docstring at `tests/test_eval.py:1752`, "real cross-encoders emit logits", which is true of
  fastembed only.

## P2: the provider in the threshold identity (released in 0.33.0 at 20261102 23:09 UTC; D-1, D-2 and D-4 ruled by the user, 20261102 19:58 UTC)

**The user ruled on 20261102 19:58 UTC ("Take my lean"): D-1 strict, D-4 the provider inside the `fitted_for`
string (`provider:model@revision`), D-2 a MINOR release with a "Breaking" entry that names the
one-line fix; D-3 is yes.** The table is kept as the record of what was weighed, and of what each
cost, measured on `dee3f04`:

| # | Decision | Options | Leaning, and why it is not mine to take |
|---|---|---|---|
| D-1 | What an old `fitted_for` (no provider) does | **Strict:** the provider enters the fingerprint, an old value reads `unknown` until re-fitted. **Legacy-tolerant:** new fits write the provider, an old value is accepted as today and `pnk doctor` warns | Strict: it makes the documented "`unknown` rather than a wrong number" true. It breaks every calibrated manifest once |
| D-2 | Release class (`docs/RELEASING.md`: a breaking change to the public API or the CLI contract is a MAJOR, the highest wins) | Is "existing thresholds read `unknown` once" breaking? | Permanent surface and irreversible once published: the user's |
| D-3 | Does it count as changing "the confidence signal" (`CLAUDE.md` § Changing retrieval)? | Yes: golden-set before and after on `tests/demo-kb` | Yes. Expected: identical labels, once the demo KB's `fitted_for` carries its provider |
| D-4 | The spelling | `provider:model@revision` inside `fitted_for`, or a separate `provider` key under `[retrieval.confidence]` | A key is permanent surface (`CLAUDE.md`): the user's |

### What each choice touches (read 20261102 against `5a431dc`: by reading, not by running)

- **`ModelInfo.fingerprint()` (`embed.py:45-47`) has three callers and feeds nothing but `fitted_for`.**
  `calibrate.py:127` writes it. `search.py:656` compares it: a mismatch is `unknown`, exit 0.
  `doctor.py:1111` compares it: a mismatch is a **`FAIL`** (`doctor.py:1114-1121`), so `pnk doctor` exits 1
  (only once the index is built and the reranker loads offline). `manifest.py:827` reads `fitted_for` as an
  opaque string, the index's coherence check does not use it, and nothing parses it, so a `provider:`
  prefix needs no delimiter rule.
- **A new manifest key is refused by every older Pinakes.** `_toml.py`'s `done()` rejects unknown keys, so a
  manifest carrying one cannot be loaded at all by an earlier release; a prefix inside the string loads and
  reads as a mismatch.
- **Hand-written sites if the provider enters the string** (each verdict from reading the surrounding code):

| Site | After the change |
|---|---|
| `tests/demo-kb/pinakes.toml:39` | mismatch, **loud in CI only**: `pnk doctor --kb tests/demo-kb` exits 1 (`ci.yml`, "Health check") and `pinakes.eval` regresses `confidence_coverage` against `baseline.json`; pytest does not see it |
| `tests/test_cli_ask.py:56` (`FINGERPRINT`, spelled out on purpose) | loud: 23 tests take the confident and unconfident KB fixtures |
| `tests/test_embed.py:202-203`, `tests/test_eval.py:1712` and `:1716`, `tests/test_search.py:397` | loud |
| `tests/test_search_reproducibility.py:146` and `tools/eval_reproducibility_gate.py:159` | **silent**: they plant `fitted_for = "coarse-reranker@v1"` over the demo's literal, which still satisfies their `before in text` check, so every question reads `unknown` and the tests pass (their own comments name this failure). Fix them and assert the labels are not constant |
| `tools/reachable_ceiling_probe.py:950` | raises `SystemExit` (its count is not 1) if the demo literal is edited |
| `tools/build_rfc_corpus.py:261` | **silent**: the generated KB's confidence reads `unknown`; `tests/test_build_rfc_corpus.py:416` compares `fitted_for` with the rerank model's name and passes until the generator is edited |
| the three `notes` templates, line 39 (a comment) | stale text; changing a template needs a version bump and `tools/template_drift_gate.py` is red without one. Fold the template's `# revision = "…"  # pin the HF commit sha…` advice into the same bump |
| `tests/conftest.py:108` and `tests/test_cli_upgrade.py:50` | **not affected**: the first never equalled the fingerprint (it is only parsed), the second is a synthetic template fixture |

- **Release-class precedent for D-2, read from `CHANGELOG.md`:** breaking changes shipped as MINOR in 0.5.0
  (duplicate keys and others refused) and 0.8.0 (the paid-extractor key renamed, no fallback), and as PATCH
  in 0.7.1 (an escaping `include` pattern became a load error) and 0.20.1 ("Breaking, and deliberately in a
  patch": `vector_tier = "sqlite-vec"` refused). No 1.x has ever been cut. Under legacy-tolerant nothing that
  worked stops working. Under strict, `pnk doctor` exits 1 on every calibrated KB until it is re-fitted (one
  line to edit if the provider is known). `tests/demo-kb` is the only calibrated manifest in this repository;
  the public RFC corpus has its thresholds commented out; private KBs: unstated.
- **A third option for D-1, considered and rejected:** accept an old value unless its numbers cannot belong to
  the active scale. It covers one direction only: negative thresholds cannot be sentence-transformers', but its
  0 to 1 thresholds are valid logits, and that direction (26.7% of answerable questions labelled low) is the
  one measured.

Files that mention `fitted_for` on `dee3f04` (32; read each before deciding which change):
`src/pinakes/{calibrate,doctor,embed,manifest,search,template}.py`; the templates
`src/pinakes/templates/notes/pinakes.toml.j2` and `_versions/1.1`, `_versions/1.2`;
`tests/demo-kb/pinakes.toml` (thresholds fitted under fastembed: `low_below = -5.4213`,
`high_above = -3.5016`); `tests/` (`conftest`, `test_build_rfc_corpus`, `test_cli_ask`,
`test_cli_upgrade`, `test_doctor`, `test_embed`, `test_eval`, `test_manifest`, `test_search`,
`test_search_reproducibility`); `tools/` (`build_rfc_corpus`, `eval_reproducibility_gate`,
`reachable_ceiling_probe`); `docs/` (`CLI`, `DESIGN`, `MANIFEST`, `VERIFICATION`); and history that
does not change (`CHANGELOG`, `RETROSPECTIVES`, older plans).

## Built / not built

| Row | State |
|---|---|
| P1 | landed on `main` at `5a431dc` and released in 0.32.9 (published 20261102 15:15 UTC) |
| P2 | released in 0.33.0 (strict, the provider inside the string, template `notes@1.3`), on `main` as `7aba9ac` and on PyPI since 20261102 23:09 UTC. D-3 measured: the published 0.32.9 on the old manifest and this change on the new one agree on all 74 golden questions in every field (labels 54 `high`, 14 `medium`, 6 `low`; `confidence_coverage` 1.0) |
