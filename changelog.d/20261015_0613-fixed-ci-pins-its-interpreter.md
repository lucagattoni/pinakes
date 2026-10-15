- **CI no longer follows the newest CPython.** `.github/workflows/ci.yml` sets `UV_PYTHON: "3.14"`
  at the workflow level, so every `uv` call — `uv sync --frozen`, and the `--isolated --no-project
  --with` resolves that `--frozen` does not protect — runs the interpreter the last green run used;
  `minimum-python` overrides it with `"3.13"` at the job level and still asserts what it got.
  Nothing pinned an interpreter before, so when CPython 3.15.0 was released on 2026-10-09 the next
  push (a one-line docs change) turned five jobs red in `uv sync --frozen`: `onnxruntime`, which
  `fastembed` and therefore every `[light]` leg depends on, ships no `cp315` wheel. A `.python-version`
  would also have fixed it and was not chosen: it changes every developer's interpreter, this changes
  CI's. Developer tooling — it ships in no wheel.
