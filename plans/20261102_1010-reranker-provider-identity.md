# The provider is part of what a model is: P1 (built) and P2 (stopped, the user's)

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

## P2: the provider in the threshold identity (**STOP: D-1, D-2 and D-4 are the user's**)

Do not build P2 until the user has ruled on those three. What each costs, measured on `dee3f04`:

| # | Decision | Options | Leaning, and why it is not mine to take |
|---|---|---|---|
| D-1 | What an old `fitted_for` (no provider) does | **Strict:** the provider enters the fingerprint, an old value reads `unknown` until re-fitted. **Legacy-tolerant:** new fits write the provider, an old value is accepted as today and `pnk doctor` warns | Strict: it makes the documented "`unknown` rather than a wrong number" true. It breaks every calibrated manifest once |
| D-2 | Release class (`docs/RELEASING.md`: a breaking change to the public API or the CLI contract is a MAJOR, the highest wins) | Is "existing thresholds read `unknown` once" breaking? | Permanent surface and irreversible once published: the user's |
| D-3 | Does it count as changing "the confidence signal" (`CLAUDE.md` § Changing retrieval)? | Yes: golden-set before and after on `tests/demo-kb` | Yes. Expected: identical labels, once the demo KB's `fitted_for` carries its provider |
| D-4 | The spelling | `provider:model@revision` inside `fitted_for`, or a separate `provider` key under `[retrieval.confidence]` | A key is permanent surface (`CLAUDE.md`): the user's |

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
| P1 | built on branch `20261102_1004-revision-under-fastembed`; on `main` after landing |
| P2 | not started; waiting for D-1, D-2 and D-4 |
