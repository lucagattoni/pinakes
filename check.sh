#!/bin/sh
# Every gate, in order, stopping at the first failure. Run this before every commit.
#
# Exists because `uv run pyright | tail -1 && git commit` reports the *tail* exit status, so a
# failing checker looks green. Two commits landed that way before this script did.
set -e
uv run --frozen ruff format --check .
uv run --frozen ruff check .
# --extra-search-path stubs/: two stubs live there for two different reasons. pypdfium2 ships no
# py.typed marker (stubs/pypdfium2.pyi covers it for pyright); ruamel.yaml *does* ship one, and is
# stubbed anyway because `load`/`dump` take an untyped `stream` that pyright strict will not accept
# at the call sites (L5b, decision 20). ty has no pyproject-level stubPath equivalent yet, so it
# needs the same path named on its own command line, or it hard-errors on a [light]-only checkout
# where pypdfium2 isn't installed — unlike pyright, which only warns (I2,
# docs/RETROSPECTIVES.md).
uv run --frozen ty check --extra-search-path stubs .
uv run --frozen pyright
uv run --frozen pytest -q -rs

# paid-path allowlist, gates 1 and 2 (I7a): every path in .paid-path-allowlist exists, and no file
# under src/ outside that list imports a paid-API client. Replaces the unconditional grep that
# lived only in CI's build job — unconditional admits no exceptions, so it would have turned main
# red the moment I7b adds `import anthropic` to the one module allowed to have it.
#
# Plain `python3`, not `uv run`: the script is stdlib-only and imports nothing from this project,
# which is what lets CI's build job run it without installing the package first.
python3 tools/paid_path_gate.py

# extras-not-core (I1), reused as the allowlist's gate 3: pypdfium2/anthropic must never enter
# [project.dependencies] — a light core install is torch-free by design, and a PDF extractor is
# opt-in (docs/DESIGN.md §4.5). Also asserted from the other side by
# tests/test_packaging.py::test_extractors_stay_extras, which is how CI gets it. (That name was
# `test_paid_and_pdf_clients_stay_out_of_core` here and in tests/test_paid_path.py until
# 20260822 — a test that has never existed under either file's history. Nothing resolves a
# test path written in a comment, which is the whole reason docs/VERIFICATION.md is gated.)
#
# `sed 's/#.*//'` because this reads a *range of lines*, not a list of requirements: without it a
# comment inside the block that merely mentions a library fails the gate. Found 20260822, by a
# comment above `mcp` explaining why anthropic was measured and deliberately *not* capped — the
# gate read the word and reported the library as a core dependency. Requirement strings here carry
# no `#`, so stripping comments removes false positives and no true ones — a **constraint** this
# gate now depends on, not just an observation: a PEP 508 direct URL carrying a `#sha256=` fragment
# would be truncated here. None exists, and the parsed-side test named above never had the problem
# either way, because it reads the requirement list rather than the lines.
if awk '/^dependencies = \[/,/^\]/' pyproject.toml | sed 's/#.*//' \
    | grep -qiE 'pypdfium2|anthropic'; then
    echo "pypdfium2 or anthropic found inside [project.dependencies] — they must stay extras" >&2
    exit 1
fi

# Gate 4 — the free path never imports a paid client, observed at runtime rather than grepped —
# runs inside `pytest` above (tests/test_paid_path.py). It is named here because it is the gate
# that actually matters and the one a reader of this file would otherwise assume is missing; it
# skips with a printed reason when pinakes[claude] is absent, and CI's [light,pdf,claude] leg is
# where it is meaningful.

# wheel-import: **deliberately not here, and named so nobody reads its absence as an oversight.**
# `tools/wheel_import_gate.py` imports every module of an *installed* Pinakes against a freshly
# resolved dependency set — which needs `uv build` and a network resolve, and this script must stay
# offline-capable and fast. It runs in CI's `build` job, the only job that resolves anything: every
# other `uv` invocation in `ci.yml` carries `--frozen`; `release.yml` carries the same two checks
# in front of `uv publish`. That is exactly how `mcp` 2.0.0 removing
# `mcp.server.fastmcp` left `pnk serve` dead on every fresh install from the first PyPI release to
# 0.27.1 with every gate here green — a local `./check.sh` cannot see a dependency resolve, and
# nothing it runs ever will.

# corpus-regenerates (I2): the sixteen text-layer fixtures must reproduce byte-identically from
# their own committed generator, and the three scanned ones within the pixel tolerance.
# SOURCE_DATE_EPOCH exported here explicitly — belt and suspenders alongside the generator's own
# fallback when unset (plans/20260727_1543-v0.2.md, I2): neither should be the only thing standing between a
# regeneration and a fresh CreationDate rewriting every fixture.
#
# The text-layer half always runs — `--skip-scanned` drops the only fixtures needing pypdfium2 and
# Pillow — so a [light]-only checkout still gets the gate. Only the *scanned half* skips, printing
# its reason, which is what the plan asks for.
SOURCE_DATE_EPOCH=1785181219 uv run --frozen pytest -q \
    tests/test_pdf_corpus.py::test_regeneration_is_reproducible
if uv run --frozen python3 -c "import pypdfium2, PIL" 2>/dev/null; then
    SOURCE_DATE_EPOCH=1785181219 uv run --frozen pytest -q \
        tests/test_pdf_corpus.py::test_scanned_regeneration_within_tolerance
else
    echo "corpus-regenerates (scanned half): skipped — pinakes[pdf] and/or Pillow not installed"
fi

# pdf-quality (I3b): the extraction-quality baseline must not drift beyond tolerance, and neither
# fitted floor may drift from a fresh re-fit — a gate, never a one-time ceremony (plans/20260727_1543-v0.2.md).
# Skips with its reason when pinakes[pdf] is absent (I1's own exit criterion: green under
# `--extra light` alone), never silently — `make pdf-eval` is the same command CI runs as its own
# job, in this commit, not deferred the way the draft plan would have left it until I9.
if uv run --frozen python3 -c "import pypdfium2" 2>/dev/null; then
    make pdf-eval
else
    echo "pdf-quality: skipped — pinakes[pdf] not installed"
fi

# prices-toml-parses (I6a): `as_of` must exist and parse as `YYYYMMDD HH:MM` — a build-time gate,
# never a staleness check (a wall-clock gate would fail a quiet weekend with no code change;
# staleness is a `pnk doctor` WARN and a runtime refusal instead, docs/DESIGN.md §5). This only
# ever catches a *malformed* file, which a code change could actually introduce.
uv run --frozen python3 -c "
import sys
from datetime import datetime
from pinakes.budget.prices import load_prices

prices = load_prices()
try:
    datetime.strptime(prices.as_of, '%Y%m%d %H:%M')
except ValueError as exc:
    print(
        f'prices.toml: as_of {prices.as_of!r} does not parse as YYYYMMDD HH:MM: {exc}',
        file=sys.stderr,
    )
    sys.exit(1)
"

# traversal-cap (L3): a walk asked for more than it may have gets less, and is told so. Drives the
# *shipped* core at depth=99 and adjacent_k=10000 against a 500-wide, 12-deep fixture graph and
# checks three things — the depth cap, the fan-out cap, and that `truncated` reports a cap that
# bit. A unit test proves the clamp works today; this proves nobody has turned a `min()` into a
# pass-through since, which is cheap to do by accident and expensive to notice, because the failure
# is a slow query and an enormous answer rather than an exception.
uv run --frozen python3 tools/traversal_cap_gate.py

# link-density (L1): authored links in the two committed corpora stay sparse — a ceiling on
# density, a ceiling on any one document's degree, and at least one intra-KB link per corpus.
# One author writes the corpus, its links and (later) the questions that traverse them, so a
# quietly over-linked fixture would make cross-KB traversal look easy and the graph release's eval
# look better than any real corpus ever will.
#
# Reads the committed sidecars, never an index — which is what lets it run here at all, and what
# makes the number it enforces the same population `pnk doctor` reports to a user (L7). Those two
# numbers disagreeing by three is how 0.4.1's data-loss bug was found; keeping them the same
# population is not tidiness.
#
# `uv run` rather than plain `python3`: it needs ruamel.yaml — the same library the product reads
# sidecars with, so the gate counts the same population it enforces. (It read through PyYAML until
# L5b; on a library the product no longer uses it would have counted sidecars the product now
# refuses.) Unlike the paid-path gate, nothing has to run this before the package is installed.
uv run --frozen python3 tools/link_density_gate.py

# eval-reproducibility (G1): the golden set answers the same way however the index was built. The
# graph release's gate reads per-question movement as evidence about *retrieval*, so movement caused
# by a rebuild is not noise, it is a wrong answer — and until G1 every tiebreak in the pipeline
# resolved to `chunks.id`, the rowid, which store.py says has no identity across rebuilds. Measured
# then: one golden-set question in 41 already differed between an incremental sync and a --rebuild.
#
# Offline and about a second, on a deliberately tie-heavy fake backend, so it needs no weights and
# no network. It sweeps four ways of reaching the same corpus state — a document edited, added,
# removed, renamed — because each takes a different path through sync.py and the tests cover one.
uv run --frozen python3 tools/eval_reproducibility_gate.py

# status-header: docs/STATUS.md line 3 — `**Latest release: x.y.z**` — must name
# pinakes.__version__. It drifted for four consecutive releases while the same sweeps updated
# every table below it (plans/20260731_1202-open-corrections.md, 20260803); a checklist missed it four times,
# which is this project's threshold for turning the item into a gate. Only the version is gated,
# never the `last reviewed` date beside it — a wall-clock staleness check fails on a quiet
# weekend with no code change, the same reasoning recorded at prices-toml-parses above.
#
# **There IS an exception window, and this comment denied it until 20260826.** `__version__` means
# *landed on `main`* (D-35, taken by the user 20260825 12:37), so between a release commit landing
# and its tag reaching PyPI, line 3 names a version `pip install` cannot get — deliberately, three
# times, once for fourteen minutes. Layer 2 of the gate makes the line say so: with R = the newest
# entry of STATUS's *Published versions* row, `line3 > R` requires the hold marker, `line3 == R`
# forbids it, and a row it cannot read is a hard failure rather than a skip. Offline, because R is
# a committed file — which is what keeps this invocation in a script whose own comment demands it
# stay offline-capable.
#
# This line is byte-pinned by tests/test_check_script.py; the comment is not.
uv run --frozen python3 tools/status_header_gate.py

# release-order: the six ordered release sequences in CHANGELOG.md, docs/ROADMAP.md and
# docs/STATUS.md read in release order, AND every per-release section in ROADMAP sits under the
# Part whose declared range holds its version. The second half was added 20260822 after 0.27.1's
# section landed inside `# Part 5 · What is not built` with all six sequences green — the sequence
# was still sorted, because sorting says nothing about location. 0.25.3 did the same and 0.25.4
# fixed it once already. The Part ranges are read out of the `# Part N` headings themselves rather
# than from a mapping kept beside them. And every release at or after a sequence's DECLARED start
# must appear in it: order is a property of the pairs, membership a property of the set, and a
# deleted row leaves every surviving pair sorted. The start is a constant, never the sequence's own
# oldest entry — deriving it would let a deleted first row move the start and hide itself. The sixth is STATUS's *Published on PyPI* prose, added
# 20260822: docs/RELEASING.md named that list as a place a release stales and said this gate decides
# where the new entry goes, while no pattern here matched it — so the procedure delegated the
# decision to a check that could not read the document, and the list had been mis-ordered since
# 20260821 through every green run. A sweep adds one row to each, and a row added in the wrong
# position is invisible to everything else here — the table is complete, every link resolves and
# mkdocs is green, because ordering is a property of the sequence and not of any row. Four
# consecutive sweeps put their section in the same slot while the correct slot moved (docs/
# RELEASING.md), and one instance sat in the 20260807 audit unworked for four days, which is this
# project's threshold for turning a convention into a gate.
#
# Plain `python3`, not `uv run`: stdlib only and imports nothing from this project, so CI's build
# job can run it without installing the package.
python3 tools/release_order_gate.py

# changelog/retrospective fragments are well-formed. Cheap, offline, and it fails *here* rather
# than at release time — `--apply` deletes the fragments it consumed, so a malformed one found then
# would be found with the evidence already gone.
python3 tools/fragments.py --check

# markdown-links: every relative link and heading anchor resolves in the Markdown the docs site
# never sees. `mkdocs build --strict` resolves internal links, and it is the only thing that does —
# it reads `docs/` alone (`mkdocs.yml` `docs_dir`) and `exclude_docs` drops `docs/README.md` even
# from that. So `CLAUDE.md`, the root `README.md`, `CHANGELOG.md`, all of `plans/`, the
# `changelog.d/` and `retro.d/` READMEs and the routing table itself are checked by nothing.
# Measured 20260823, before this gate existed: eleven broken, five dead as authored — three in
# `CHANGELOG.md` pointing at `../docs/...` from the repository *root*, which resolves above the
# repository, and one citing a `docs/STATUS.md` heading that a re-measurement had renamed. Four
# more had been fixed in `CLAUDE.md` that same morning, which is the recurrence rate that turns a
# convention into a gate here.
#
# **A link inside a code span or a fenced block is never resolved.** A document that *quotes*
# another document's link would otherwise be told its quotation is broken, and the only way to
# satisfy the gate would be to corrupt the quote — `plans/20260807_2143-docs-audit-findings.md`
# quotes six.
#
# The heading-slug algorithm is GitHub's, duplicated from `mkdocs_hooks.py` so the gate and the
# published site cannot disagree about what an anchor is;
# `tests/test_markdown_link_gate.py::test_the_gate_and_the_site_slugify_every_heading_in_the_repository_identically`
# holds the two copies against every heading in the repository. Path case is compared against the
# real directory listing rather than delegated to `Path.exists()`, which answers `True` on macOS
# for a link that 404s on GitHub and fails on CI's ubuntu runner.
#
# Plain `python3`, not `uv run`: stdlib-only and imports nothing from this project, so CI's build
# job can run it without installing the package.
python3 tools/markdown_link_gate.py

# shared-file overlap: which files this branch touches that the default branch has touched too.
# Deliberately NOT --strict and NOT --fetch here: several agents work in this repo at once, so
# overlap is common and normal mid-development, and a routine `./check.sh` must stay offline-capable
# and fast. It reports; the landing checklist runs `--fetch --strict` before a merge, which is the
# moment the answer can still change what you do.
python3 tools/shared_file_overlap.py

# No NUL byte in a tracked text file. git calls such a file **binary**: no diff, no review, and
# `grep` skips it silently — so a document can go wrong in a way this project's whole process
# (read the diff, grep for the sentence) cannot see. Caught 20260801, in a bullet warning about
# raw NUL bytes reaching output, written with a raw NUL byte in it.
python3 - <<'NULSCAN'
import pathlib, subprocess, sys
TEXT = {".md", ".py", ".toml", ".yaml", ".yml", ".sh", ".txt", ".cfg", ".ini", ".json",
        ".lock", ".pyi", ".gitignore", ".gitattributes", ""}
tracked = subprocess.run(["git", "ls-files", "-z"], capture_output=True, check=True).stdout.split(b"\0")
bad, scanned = [], 0
for name in filter(None, tracked):
    path = pathlib.Path(name.decode())
    # An **allowlist** of text suffixes, not a denylist of binary ones: the first draft excluded
    # png/jpg/pdf and was immediately caught by a committed .ttf. A denylist of binary formats is
    # never finished.
    if not path.is_file() or path.suffix not in TEXT:
        continue
    scanned += 1
    if b"\0" in path.read_bytes():
        bad.append(str(path))
if bad:
    sys.exit("nul-scan: NUL byte in tracked text file(s): " + ", ".join(bad))
print(f"nul-scan: {scanned} text file(s) scanned, no NUL byte.")
NULSCAN

# template drift (T1): a template version number means the bytes it denotes. `pnk doctor` has
# compared a KB's recorded template reference against the installed one since 0.1 and has never
# once been able to fire — `notes` said `version = "1.0"` in every commit while the files that
# version denotes changed in ten later ones, so every KB in existence recorded a reference that
# matched and meant something different. The rule "bump the version when you change the template"
# existed and was silently not followed, which is this project's threshold for replacing a
# convention with a gate.
#
# `uv run` rather than plain `python3`: it renders every archived version through jinja2 (leg vi)
# using `pinakes.init`'s own default constants, so the variables the gate supplies cannot drift
# from the ones `pnk init` actually passes. Nothing has to run this before the package is installed.
#
# Leg (vii) needs git history and says so when it has none — a skip is not a pass, and the gate
# names which mode it ran in every time. CI gives this gate's own job `fetch-depth: 0` for that
# reason; every other checkout in `ci.yml` is shallow and would silently lose the leg.
uv run --frozen python3 tools/template_drift_gate.py

echo "all gates green"
