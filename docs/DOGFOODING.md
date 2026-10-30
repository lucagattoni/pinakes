# Starting a KB you will actually use

**Audience: someone starting a first real knowledge base with Pinakes — in practice its maintainer, the
first time. Goal: from nothing to a KB that holds your own documents, answers from them, and has told
you what went wrong on the way.** Every claim below was run against the **published `pinakes` 0.32.7** on
20261019, from about 12:13 UTC, on CPython 3.13.16 and an Apple-silicon Mac — except the figures marked
as taken on 0.32.6, and the claims marked *from the source* or *not run*; the evidence, row by row, is
[§ 5.1 of the option B plan](https://github.com/lucagattoni/pinakes/blob/main/plans/20261019_0817-option-b-dogfooding-on-ramp.md).
Where something was **not** run, it says so. This is a checklist, not a tutorial: [the Guide](GUIDE.md)
says how each command works.

## 1. The machine

1. **Install `pnk` where your shell can find it, on the interpreter this project declares.**

    ```bash
    uv tool install --python 3.13 "pinakes[light]"
    pnk --version
    ```

    - **Pin `--python 3.13`.** On a machine whose newest Python is 3.15, `uvx --from "pinakes[light]"`
      did not resolve — *`onnxruntime>=1.24.2` has no wheels with a matching Python ABI tag (e.g.,
      `cp315`)* — and worked in 1.6 s with the pin.
    - **Not `uv add`, in a KB directory.** `uv add "pinakes[light]"` exits 2 there (*No `pyproject.toml`
      found*), and the README's Quickstart opened with it when this was measured; it has since
      been changed to say where `uv add` can be run. The Guide's route then was `uv init && uv
      add …`, and it **failed on that same machine** (the Guide and the README now say `uv
      init --python 3.13`, [Guide § Install](GUIDE.md#install)): `uv init` wrote
      `requires-python = ">=3.15"`, and `uv add "pinakes[light]"` then did not resolve. **`uv init --python
      3.13` is the route that works:** it wrote `requires-python = ">=3.13"` and a `.python-version` of 3.13
      (and, being plain `uv init`, a git repository, a `README.md` and `src/`), and the same `uv add`
      resolved — with `--no-sync`, so nothing was installed. The `--bare` variant resolves too but writes
      no `.python-version`, so a later `uv sync` picks 3.15 and fails. The project's `pnk` would live in
      `.venv/bin`, off your `PATH` *(from how uv installs; not run)*.
    - **Tell `pnk init` which extra you installed** (`--backend light`). A KB stamped for the default
      backend, with only `[light]` installed, stops on the first sync and names the two-line manifest
      edit that fixes it.
2. **Weights come down on first use, and you do not choose the moment.** Measured on 0.32.7 with an empty
   Hugging Face cache: the first `pnk sync` fetched the embedder (67 MB, 2 s by its progress bar); a later
   `pnk doctor` — which is meant to be offline — fetched the **reranker (1.1 GB, 11 s)**. **That is
   fixed on `main` and is in no published release yet:** an offline load now asks fastembed for local
   files only, so `doctor` prints a FAIL line for a model that is not cached and downloads nothing
   (reproduced against an empty temporary cache with the network forbidden; not run against real
   weights). Until that is released, be online for the first `sync` and for the first command that loads
   the reranker: `doctor` was measured; by the source so do `search`, `ask` and an agent's first `serve`
   tool call (not run). A `doctor` on a cache that does not exist yet prints two FAILs ending *“Run once
   without --offline to populate the cache”*. `doctor` is hard-wired offline and has no such flag; `sync`,
   `search`, `ask`, `links` and `serve` take `--offline`, off by default, so the line means *go online
   once*: `sync` brings the embedder, and the reranker comes with the first `search` or `ask` (and, on
   every published release up to 0.32.8, with `doctor`). The cache
   lives where `doctor`'s `model cache` line says; budget about **1.2 GB** for the light pair (the
   Guide's ~1.4 GB is the default backend's).

## 2. The material

- **What goes in is yours to choose; this page only fixes what must be true.** Text you would search
  again within a week; enough of it that a search does not simply return everything (more than the
  eight results `final_k` returns — ten ordinary documents do it); **nothing that cannot sit in a
  private repository**.
- **The KB is its own private repository.** `pnk init my-kb --name "My notes" --backend light`, or
  `pnk init . --name "My notes" --backend light` inside one you already have — measured, that left
  `README.md`, `.gitignore` and `pyproject.toml` byte-identical, and warned when `.gitignore` did not
  ignore `.pinakes/`. A fresh `pnk init` ships a `.gitignore` that covers `.pinakes/`; **in a
  directory you adopt, add the line yourself before the first sync.**
- **Commit the sidecars** `sync` writes beside each document (`<file>.pnk.yaml`): they hold the
  permanent ids.
- **Plain text with a numbered outline needs one setting, before the first sync.** A `.txt` corpus is
  chunked by size unless `[chunking] headings = "numbered"` is set: `0 of 2189 chunks carry a heading
  path` by default and `1865 of 1955 chunks carry a heading path (95%)` with it, on six public RFCs —
  the only plain text tried. The grammar reads a dotted-decimal outline and, if its walk fails, gives
  that document no headings at all ([MANIFEST](MANIFEST.md)). `doctor` reports the 0% and names the
  setting; `sync` says nothing; changing it afterwards needs `pnk sync --rebuild`, per `doctor`'s remedy
  text (not run).
- **A `.txt` file's title is its filename** (`title: rfc8089`); edit `title` in the sidecar. Markdown
  takes its heading.

## 3. The first sync

```bash
pnk sync --kb my-kb
```

- **Estimate in chunks, not bytes, and expect a range.** The same machine ran **16 to 21 chunks a
  second**: 7,137 chunks of this repository's Markdown (4.3 MB) took 338 s on 0.32.6 — 21 a second,
  79 s per MB; 767 chunks of Markdown (360 KB) took 47 s on 0.32.7 — 16 a second, 130 s per MB, the gap
  from 21 not explained; 2,189 chunks of plain text (387 KB) took 120 s — 18 a second,
  310 s per MB. Weights already cached.
- **On a terminal** you see `syncing: 3/8 documents (7.0/min)`. **In a pipe or an agent session you
  see nothing until the two summary lines.**
- **An interrupted sync loses nothing.** Killed 12 s into a first sync that takes about 47 s uninterrupted,
  `pnk doctor` exited 0 with
  no FAIL and *WARN sync completeness … Run `pnk sync`. It resumes incrementally and keeps every
  embedding already written*; the next `pnk sync` printed *took over a stale sync lock left by a
  process that is no longer running* and finished. **Never `--rebuild` for this.**

## 4. What a healthy `pnk doctor` prints

Exit 0 is healthy: **a WARN is not a failure.** On the published 0.32.7 a fresh KB showed **four** WARNs
before its first sync and **five** after it. (On 0.32.6, whose price table was 44 days old, the same
check showed five and six — the extra one is the last row.)

| WARN | When | What to do |
|---|---|---|
| `embedding` and `reranker`: revision unpinned | always | pin `revision` in `pinakes.toml` once you are settled |
| `index: not built yet` | before the first sync only | `pnk sync` |
| `git hooks: not a git repository` | until the KB is one **and** `pnk install-hooks` has run — *from the source:* after `git init` alone it reads `0 of 3 installed` | `doctor` says freshness is git-triggered and a loose folder needs a manual or cron `pnk sync`; `pnk install-hooks` installs the hooks ([Guide](GUIDE.md)) — not run here |
| `calibration: no fitted thresholds` | after the first sync | honest, not a fault: `confidence` reports `unknown` until you fit thresholds against a golden set |
| `links: none authored` | after the first sync | `pnk link` when you have links to record |
| `price table: … N days old` | when the release is more than 30 days old | upgrade `pinakes`; adding `max_price_age_days` to `[budget]` also clears it (from the manifest reference, not run), as a decision about a safety setting |

**`doctor` prints things that must not be pasted anywhere public**: the model-cache path (your home
directory), the sync lock's hostname, and — when titles are still filenames — up to three document
paths. See § 6.

## 5. Check that it worked

**“Started” means three things, and only the first two can be checked by a command:**

1. `pnk doctor` reports `index: N active documents` with N equal to the number of files your
   `include` patterns select.
2. **The probe passes for three documents.** Take a sentence of eight words or more that occurs exactly
   once in the whole KB (a repeated one would give a false miss — reasoned, not run), run `pnk search --kb my-kb "<the sentence>"`, and look at the first hit: it should be that
   document. A search over a KB whose whole index is eight chunks or fewer returns every chunk and
   proves nothing. **This probe has not been measured for its pass rate** — treat a miss as a finding
   to record (§ 6), not as proof the KB is broken. `pnk search` prints chunk text, so do not run it
   inside an agent session against material that must stay private.
3. **A dated line in the friction file** (§ 6) saying one of *friction*, *used, nothing to report* or
   *not used*. A null log must tell *no friction* from *no use*, and only you can say which.

Attaching the KB to an agent (§ 6) belongs to “started” in the option B plan; it was not tested live.

## 6. Use it, and record what went wrong

- `pnk search` takes `--kb`; so does `pnk ask`, which was not run here (per `--help` it is free without
  `--deep`).
- **Attach it to an agent** with `.mcp.json`, using the absolute path of `pnk`:

    ```json
    {
      "mcpServers": {
        "pinakes": { "command": "/absolute/path/to/pnk", "args": ["serve", "/path/to/my-kb"] }
      }
    }
    ```

    `command -v pnk` prints the path. [The Guide's snippet](GUIDE.md#using-it-from-an-agent) now
    shows the absolute path too; it used to say `"command": "pnk"`, and before `pnk` was
    installed with `uv tool`, a bare `pnk` was not found on the
    `PATH` of any shell tried. After `uv tool install` it is on the `PATH` only if uv's tool directory is
    (`uv tool install` printed a warning that its directory was not on the `PATH` and named `uv tool
    update-shell` as the fix — the fix itself not run). The absolute path is a
    precaution, not a measured need, and **whether a live agent launches the entry with your `PATH` was
    not tested.** An agent attached this way sees chunk text from `pinakes_search` and whole documents from
    `pinakes_get` (from the source, not run): attach only a KB you are content to show it.
- **Write five real questions you had this week into `eval/questions.yaml` before measuring anything**,
  because a question set written after the result is not a test.
- **Keep a `FRICTION.md` in the KB's own repository.** One entry per surprise: the exact command, what
  the docs led you to expect, what happened. Start it with the dated line from § 5. [The RFC corpus's
  record](https://github.com/lucagattoni/pinakes-corpus-rfc/blob/HEAD/FRICTION.md) of ten entries, written
  against 0.7.1, is the model — every one has a recorded closure since.
- **Before anything reaches the public repository** (as a `retro.d/` fragment): strip home paths,
  hostnames, document text, document titles and document paths. This repository is public; yours is
  not, and that is the point of keeping the log there first.
