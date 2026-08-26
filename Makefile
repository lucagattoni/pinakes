# pinakes — task runner.
#
# Every target wraps the command CI actually runs (.github/workflows/ci.yml, and docs.yml for the
# two docs targets), so a green `make check` locally means the same thing it means on the runner.
# `--frozen` everywhere: the lockfile is the contract, and a target that silently re-resolves it
# would hide the drift CI would catch.
#
# `check` is the gate; check.sh remains its shell entrypoint (git hooks and docs reference it).

.DEFAULT_GOAL := help
SHELL := /bin/sh
DEMO_KB := tests/demo-kb
# mkdocs is deliberately not a project dependency — it would pull a docs toolchain into the
# environment `check` and the release wheel resolve. `--no-project` runs it from an ephemeral one.
DOCS := uv run --no-project --with-requirements requirements-docs.txt mkdocs

.PHONY: help install check fmt fmt-check lint types types-fast test test-model eval demo doctor \
        budget corpus pdf-eval build smoke clean release-check docs docs-serve

help:  ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install:  ## Sync the dev environment (light extra — CI's minimum leg; add --extra pdf/claude for the others)
	uv sync --frozen --extra light

check:  ## Every gate, stopping at the first failure — run before every commit
	./check.sh

fmt:  ## Reformat (covers Python blocks inside Markdown — that is not a typo)
	uv run --frozen ruff format .

fmt-check:  ## Formatting gate only
	uv run --frozen ruff format --check .

lint:  ## Lint gate only
	uv run --frozen ruff check .

types-fast:  ## ty — fast pre-check, never the gate (docs/RETROSPECTIVES.md, I1)
	uv run --frozen ty check --extra-search-path stubs .

types:  ## pyright strict — the type gate
	uv run --frozen pyright

test:  ## Unit tests (model-backed tests excluded)
	uv run --frozen pytest -q

test-model:  ## Model-backed tests — downloads weights to HF_HOME on first run
	uv run --frozen pytest -q -m model

demo:  ## Index the synthetic demo KB
	uv run --frozen pnk sync --kb $(DEMO_KB)

doctor:  ## Health-check the demo KB
	uv run --frozen pnk doctor --kb $(DEMO_KB)

budget:  ## Show the demo KB's spend ledger (free: it only reads)
	uv run --frozen pnk budget --kb $(DEMO_KB)

eval:  ## Golden-set evaluation against the baseline (needs `make demo` first)
	uv run --frozen python -m pinakes.eval $(DEMO_KB)

corpus:  ## Regenerate tests/pdf-corpus/ in place — review with `git diff` before committing
	SOURCE_DATE_EPOCH=1785181219 uv run --frozen python3 tests/pdf-corpus/generate.py

pdf-eval:  ## Extraction-quality baseline + floor-drift check against tests/pdf-corpus (needs [pdf])
	uv run --frozen python -m pinakes.extract.quality tests/pdf-corpus \
		--check-floors src/pinakes/extract/floors.toml

build:  ## Build wheel and sdist
	uv build

# `pnk --version` alone is what this was, and it is the shape of check that let `pnk serve` ship
# dead in every release from the first to 0.27.1: `--isolated --no-project` resolves *fresh*, and
# `--version` touches no dependency. This target runs **the same two gates the two workflows run**,
# against the same freshly-resolved wheel — one implementation, three call sites, so a fix to
# either gate reaches all three and none of them can drift into checking something weaker.
# Deliberately without `timeout`, which CI has and macOS does not: locally a hang is a person's
# Ctrl-C, in CI it is a burnt job budget, and `tools/mcp_handshake_gate.py` carries its own
# 30-second ceiling either way.
#
# **The handshake was three JSON-RPC lines written here and stdin closed, until 20260822.** Two
# separate defects lived in that shape and both were measured, not reasoned about. The first: the
# output went through `grep -q`, which closes the pipe on its first match, so `pnk serve` died on a
# broken pipe, dumped an ExceptionGroup, and `make` exited **0** — the target reporting success off
# a crashed server. The second, found when `mcp` 2.0.0 arrived: 2.x does not drain a queued request
# before shutting down on EOF, so `tools/list` was answered **2 runs in 10** against 10 in 10 under
# 1.28.1. Driving the session with `mcp`'s own client removes both — the client holds the
# connection open until it has its answers, and the gate's exit status is this recipe line's.
smoke: build  ## Install the built wheel in isolation and exercise it — what release does
	uv run --isolated --no-project --with dist/*.whl pnk --version
	rm -rf /tmp/pinakes-smoke && mkdir -p /tmp/pinakes-smoke
	uv run --isolated --no-project --with dist/*.whl pnk init /tmp/pinakes-smoke/kb
	uv run --isolated --no-project --with dist/*.whl python tools/wheel_import_gate.py \
		--require pinakes.serve --min-modules 50 \
		--allow-missing pinakes.extract.pdfium:pypdfium2
	uv run --isolated --no-project --with dist/*.whl python tools/mcp_handshake_gate.py \
		--kb /tmp/pinakes-smoke/kb \
		--expect-version "$$(basename dist/*.whl | cut -d- -f2)"
	@echo "smoke: the built wheel installs, imports every module and answers an MCP handshake."

# Four legs, each named in the tool's docstring with what it costs: a release tag points at HEAD
# (and exactly one does), it names pinakes.__version__, it is annotated with a message
# `gh release create --notes-from-tag` can read, and it is **not already on origin** — which is
# what makes CLAUDE.md's "before the tag, never after" checkable instead of remembered.
#
# It ran for the life of this target as three `echo`s: no comparison and no failure path, so it
# could not fail and therefore verified nothing, while CLAUDE.md sent an operator here as the last
# check before a version PyPI never takes back (plans/20260731_1202-open-corrections.md).
#
# **Deliberately not in check.sh**: HEAD carries no release tag on an ordinary commit, so leg 1
# would be red on every commit in the repository. tests/test_release_tag_gate.py holds it instead
# — and pins this recipe, because a target describing a check it does not run is what it replaced.
release-check:  ## Gate the annotated tag at HEAD — run it after `git tag -a` and before the push
	uv run --frozen python3 tools/release_tag_gate.py

docs:  ## Build the docs site into site/ — --strict, exactly what the docs workflow runs
	$(DOCS) build --strict

docs-serve:  ## Preview the docs site at http://127.0.0.1:8000 with live reload
	$(DOCS) serve

clean:  ## Remove build artifacts and caches (never touches .pinakes/ or the lockfile)
	rm -rf dist build site .pytest_cache .ruff_cache
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
