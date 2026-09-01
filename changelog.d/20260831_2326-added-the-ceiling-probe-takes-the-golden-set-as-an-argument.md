- **`tools/reachable_ceiling_probe.py --questions <path>` measures a golden set that is not the
  measured KB's own.** Omitted, it resolves to `<kb>/eval/questions.yaml` exactly as before, so
  every recorded run stays reproducible byte-for-byte. It exists because
  `tools/build_rfc_corpus.py` copies the repository's `tools/rfc_corpus/questions.yaml` over
  `<out>/eval/questions.yaml` on **every** build, unconditionally — correct by design, since the
  repository copy is the source of truth — which left the probe with no route to re-measure a set
  a rebuild had replaced except to put the old file back where the next build overwrites it again.
- **The flag is deliberately combinable with `--fake`**, unlike `--kb`. That pair is refused
  because `--fake` builds its own corpus and would have to report one corpus's numbers under
  another's name; a golden set is honoured whichever corpus is underneath, so there is nothing to
  discard. `src/pinakes/eval.py` and `tools/graph_matrix.py` already carried this flag under this
  name with this default — the probe was the one that did not.
