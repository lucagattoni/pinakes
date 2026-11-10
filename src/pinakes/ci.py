"""`pnk init --ci` — the GitHub Actions workflow that keeps a published KB fresh (§6.3, I6b).

DESIGN §6.3 designed this in v0.1 and v0.1 never built it, so I6b builds it here — in the increment
that needs it to force the free backend, because writing a modification to an unbuilt writer is the
same defect as writing a hook around an unbuilt flag.

**The workflow forces `--extract=pypdfium2`, exactly as the git hooks do** (`hooks.py`'s docstring
carries the full reasoning). A CI job is the most non-interactive caller there is: it has no
terminal to answer a `confirm_above_eur` prompt from, and no CI job in this project ever holds an
API key. Sharing `hooks.FREE_BACKEND_FLAG` rather than repeating the string is deliberate — two
literals are two places for the forced backend to drift.

The cache key is keyed on the sources, so a run that changes nothing restores `.pinakes/` and syncs
nothing. `ledger.jsonl` lives in that same directory and is restored with it; CI cannot spend, so
it cannot add to it either.

**The health check follows a step that loads the models online.** `pnk doctor` loads models
`--offline` and downloads none, and `pnk sync` loads only the embedder (nothing at all while the KB
has no documents), so on a runner whose model cache is cold the health check failed on `FAIL
reranker`. One `pnk search` brings the embedder and the reranker into the cache, whether or not the
KB has documents, and the weights are cached under the manifest's hash so a run that changes no
model downloads nothing. Measured 20261110 21:57 to 21:58 UTC on an empty model cache, both with 30
documents and with none: `doctor` exited 1 before the search and 0 after it. The search's output is
discarded, because it prints passage text and an Actions log can be public.

**The workflow installs `pinakes[light,pdf]`, which is fastembed**, so it works for a KB whose
manifest names `provider = "fastembed"` in both `[embedding]` and `[rerank]` (`pnk init --backend
light` writes that). On the default `sentence-transformers` manifest its sync fails with
"backend not installed" when the KB has documents, and its search step fails the same way when
it has none.
"""

from pathlib import Path

from pinakes.errors import InitError
from pinakes.hooks import FREE_BACKEND_FLAG

WORKFLOW_PATH = Path(".github") / "workflows" / "pinakes.yml"

_CACHE_KEY = "pinakes-${{ runner.os }}-${{ hashFiles('docs/**', 'pinakes.toml') }}"

#: The weights live under `~/.cache/huggingface` (`HF_HOME` unset on a runner), keyed on the
#: manifest because it names the models. A prefix of its own, so that restoring the index never
#: restores the weights or the other way round.
_MODELS_CACHE_KEY = "pinakes-models-${{ runner.os }}-${{ hashFiles('pinakes.toml') }}"

WORKFLOW = f"""\
# Installed by `pnk init --ci`. Keeps the index fresh for a published KB.
#
# This workflow runs `pnk sync {FREE_BACKEND_FLAG}`: CI is non-interactive and must never spend.
# Paid extraction stays a deliberate `pnk sync` a human runs.
#
# It installs `pinakes[light,pdf]`, which is fastembed: the manifest must name `provider =
# "fastembed"` in both `[embedding]` and `[rerank]` (`pnk init --backend light` writes that).
name: pinakes

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5

      - name: Restore the index
        uses: actions/cache@v4
        with:
          path: .pinakes
          key: {_CACHE_KEY}
          restore-keys: pinakes-${{{{ runner.os }}}}-

      - name: Restore the model weights
        uses: actions/cache@v4
        with:
          path: ~/.cache/huggingface
          key: {_MODELS_CACHE_KEY}
          restore-keys: pinakes-models-${{{{ runner.os }}}}-

      - name: Sync
        run: uvx --from 'pinakes[light,pdf]' pnk sync {FREE_BACKEND_FLAG}

      # `pnk doctor` loads models offline and downloads none, and `pnk sync` loads only the
      # embedder: this search is what brings the models into the cache before the health check.
      # Its output is discarded: a search prints passage text, and an Actions log can be public.
      - name: Load the models
        run: uvx --from 'pinakes[light,pdf]' pnk search warm-up -k 1 > /dev/null

      - name: Health check
        run: uvx --from 'pinakes[light,pdf]' pnk doctor
"""


def write_workflow(root: Path) -> Path:
    """Write the workflow into `root`, refusing to overwrite an existing one.

    An existing workflow may be hand-edited — the same trust rule `install-hooks` applies to a
    foreign git hook, for the same reason.
    """
    path = root / WORKFLOW_PATH
    if path.exists():
        raise InitError(
            f"{path} already exists.",
            remedy="Delete it first if you want the generated workflow; it is never overwritten.",
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(WORKFLOW, encoding="utf-8")
    return path
