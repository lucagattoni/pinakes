# The measurement runs

**There are two paid paths, and each has one thing it cannot prove about itself.** Both are
measured here, under one setup and one key:

| Run | What only real calls can settle | Increment |
|---|---|---|
| **[The extractor run](#the-extractor-run)** | how well the paid extractor *reads a page* | I7b, run 20260729 03:17 for €0.43 |
| **[The deep-loop run](#the-deep-loop-run)** | how far `pnk ask --deep`'s *reservation* sits above real spend | E6 |

They spend on different things and answer different questions, so run the one you need rather than
both. What they share is [§ Setting up](#setting-up).

**Neither can ever be a repo gate**, because both need a real key and real money — which is exactly
why they are written down here with their steps and their euros rather than described as "measured
somewhere". [STATUS.md](STATUS.md) carries what each one settled.

> **Fixture provenance is a different job, and it is done separately.** Four branches now carry
> bodies captured from the live API by
> [`tools/record_claude_fixtures.py`](https://github.com/lucagattoni/pinakes/blob/main/tools/record_claude_fixtures.py), and every fixture
> declares its own provenance
> ([`tests/fixtures/claude/README.md`](https://github.com/lucagattoni/pinakes/blob/main/tests/fixtures/claude/README.md)). To re-record a branch,
> use that tool rather than this runbook — the two spend on different things and answer different
> questions.

## Setting up

Shared by both runs.

**A measurement KB with the caps raised explicitly.** The shipped defaults refuse a single slice —
that is correct behaviour, and raising them deliberately is the first step of the measurement, not
an obstacle to work around.

**The key.** Put it in `.env` at the repo root as **`PINAKES_ANTHROPIC_API_KEY`**, never
`ANTHROPIC_API_KEY` — `.env` and `.env.*` are gitignored, and `.env.example` records the shape.
(It recorded the *wrong* name from 0.8.0's rename until 20260807; if your `.env` predates that,
rename the variable or the extractor refuses.) This repo is public, so a key that is merely
*untracked* is one
`git add -A` from being published; ignoring it by pattern is what makes that impossible rather than
merely unlikely.

**Nothing loads `.env` automatically, and that is deliberate.** Pinakes has no `.env` support and
should not get any: a tool that can spend money must not pick up credentials from a file nobody
pointed it at, or the same `pnk sync` means different things depending on which directory you ran
it from. Pass it explicitly at the call site, exactly as every other spend control in this project
is explicit:

```bash
uv sync --frozen --extra light --extra pdf --extra claude

# every paid command below is run through --env-file; nothing else needs it
uv run --env-file .env pnk --version      # sanity check: the key is only read when a call is made
```

Verify it actually arrives before spending anything on the assumption that it did:

```bash
uv run --frozen --env-file .env python -c "
import os; key = os.environ.get('PINAKES_ANTHROPIC_API_KEY', '')
print('key reaches the process:', bool(key), '| length:', len(key))
print('stray ANTHROPIC_API_KEY in env:', bool(os.environ.get('ANTHROPIC_API_KEY')))
"
```

**A stray `ANTHROPIC_API_KEY` in your shell is expected on a developer machine and is not a
problem here** — `paid.py: resolve_api_key` refuses to read it, which is the whole reason that
rule exists (CLAUDE.md). The line above reports it so that a run is never debugged against the
wrong key.

> `PINAKES_ALLOW_SPEND` is **not** part of either recipe. It is a pytest condition and never a
> product guard; putting it in a CLI recipe is what would turn it into one. The product's own
> opt-in is already explicit — `[extraction] backend`, `--extract=`, `--deep`, and the accountant.

## The extractor run

### What it costs

About **€4.23 worst case** (priced 20260729 against the shipped `prices.toml`), and typically well
under half that — worst case assumes every request hits `max_tokens`, and five pages of prose
produce roughly half of it.

| Step | Documents | Pages | Worst case |
|---|---|---|---|
| (a) `--estimate-only` over one page | 1 | 1 | €0 — counts tokens, generates nothing |
| (b) one real 5-page extraction | 1 | 5 | €0.33 |
| (c) the scanned stratum | 3 | 10 | €1.30 |
| (d) the free-vs-paid delta | 4 twins + 1 control | 28 | €2.60 |

Re-price it before running — `prices.toml` moves:

```bash
uv run --frozen python -c "
from datetime import datetime
from pinakes.budget.estimate import estimate_document
from pinakes.budget.prices import load_prices
prices = load_prices()
est = estimate_document(pages=5, model='claude-opus-5', prices=prices,
                        now=datetime.now().strftime('%Y%m%d %H:%M'), max_price_age_days=3650)
print(f'one 5-page slice: EUR {est.total_eur:.4f} worst case')
"
```

### The measurement KB

```bash
pnk init /tmp/measure-kb
cd /tmp/measure-kb
```

Then edit `/tmp/measure-kb/pinakes.toml`:

```toml
[sources]
include = ["**/*.pdf"]                # init deliberately does not stamp this

[extraction]
backend = "claude-vision"
model   = "claude-opus-5"

[budget]
confirm_above_eur = 5.00              # raised so the run is not a wall of prompts
per_operation_eur = 5.00
daily_eur         = 5.00
monthly_eur       = 5.00
```

### The run

Copy the corpus documents in as you go, one step at a time, and check `pnk budget` between steps.

**(a) Fix the input half of the constant — a token count, not a generation.**

```bash
cp <repo>/tests/pdf-corpus/baseline-1p.pdf docs/
uv run --env-file <repo>/.env pnk sync --estimate-only
```

Record the measured input tokens. Compare against `budget/estimate.py`'s `PAGE_TOKEN_CEILING`
(6,000/page) and `PROMPT_TOKENS` (**700** — measured at 571 on 20260729 and rounded up; the
original estimate of 300 understated it by 1.9×, in the *unsafe* direction) — if the real figure is
far below, the reservation is over-conservative and the constant can be tightened, which is this
step's entire purpose. **Compare against the measurement, not against a re-derivation.**

**(b) Fix the output half — one real 5-page extraction.**

```bash
cp <repo>/tests/pdf-corpus/baseline-12p.pdf docs/     # priced per slice; K = 5
uv run --env-file <repo>/.env pnk sync
uv run --env-file <repo>/.env pnk budget
```

Then check, in order:

- `response.model` against the requested alias, with `startswith` — the recorded value is in the
  cache entry's `per_page_provenance`.
- the **thinking/effort pair** in `extract/claude.py` — confirmed or replaced against what the run
  actually shows. If a `<thinking>` fragment ever reaches a page's text, the leak guard turned it
  into a schema retry, and `pnk budget` will show the extra calls.
- `pnk doctor`'s `completeness` line, which is the audit's first real output.

**(c) The scanned stratum — what the paid path exists for.**

```bash
cp <repo>/tests/pdf-corpus/scanned*.pdf docs/
uv run --env-file <repo>/.env pnk sync
```

Score it with `make pdf-eval`'s metrics against the corpus's hand-authored ground truth, and record
the numbers in DESIGN §9 **with date, model, and euros actually spent**, labelled as measured on
synthetic rasters.

**(d) The free-vs-paid delta — decision 10's justification.**

The five text-layer twins **`plans/20260727_1543-v0.2.md` §I2 names** — one per stratum where `layout.py` does
real work, plus the 12-page baseline as a control — each needing `--force` because they are healthy
by design and the paid path correctly refuses to spend on them otherwise. The scanned and
pathological strata supply no twin: a raster is not a text-layer twin, and the pathological
fixture's whole job is to raise.

```bash
cp <repo>/tests/pdf-corpus/{two-column-a,tables-bordered,headers-repeating,ligatures-a,baseline-12p}.pdf docs/
uv run --env-file <repo>/.env pnk sync --force
```

Record the per-metric delta beside the free numbers. This is the one measurement that says whether
bypassing `layout.py` on the paid path costs anything — running-head handling and reading order are
the two stages it skips.

### Afterwards

1. **`prices.toml`** gains the measured per-page constant and its `measured_on`.
2. **DESIGN §9** gains the scanned-quality numbers, with date, model and euros.
3. **DESIGN §7.1** gains the free-vs-paid delta.
4. **`tests/fixtures/claude/`** — **four branches were recorded live on 20260729 03:36** and the
   README already carries per-fixture provenance, so the remaining work is *re-recording* those
   four with `tools/record_claude_fixtures.py` and checking whether any still-authored branch has
   become recordable.
5. **STATUS.md** gains what this run measured. (Its "output quality is not yet measured" claim was
   already dropped when the half-recording landed.)

If the run contradicts the fixtures anywhere, that finding is worth more than the release schedule:
it is the only evidence that can reach the assumption every branch test rests on.

## The deep-loop run

**What only real calls can settle is the gap between what a round *reserves* and what it *spends*.**
E2's constants are ceilings chosen without measurement, deliberately: a reservation has to be made
*before* the call it pays for, so every one of them was set above a guess. This run replaces the
guesses with numbers and publishes the ratio between them — the equivalent of the **11.5×** the
extractor's first live call over-reserved.

**It is two halves, and only one of them spends.**

| Half | Instrument | Cost | What it settles |
|---|---|---|---|
| **Input** | `messages.count_tokens` | **€0** | `PROMPT_TOKENS`, `QUESTION_TOKENS`, `PASSAGE_ENVELOPE_TOKENS`, `VENDOR_TOKENS_PER_CHUNK_TOKEN`, `CARRIED_MEMORY_TOKENS` |
| **Output** | real `pnk ask --deep` runs | see below | `MAX_TOKENS`, `CALLS_PER_ROUND`, both branches' real spend, the over-reservation factor |

**Token counting is free** — "free to use but subject to requests per minute rate limits", on a
pool independent of message creation (2,000 RPM at the Start tier). So every *input* constant is
measured exactly, at no cost, and the euros go only where nothing else can answer. This is not a
new idea here: `prices.toml`'s own header records the extractor's input constants as "7
`count_tokens` calls, 1/2/5-page slices", and
[`tools/measure_passage_tokens.py`](https://github.com/lucagattoni/pinakes/blob/main/tools/measure_passage_tokens.py)
was written naming this run as the thing that would replace its assumed half.

### The measurement KB

**It is `tests/demo-kb`, copied.** Nothing needs authoring, and three properties it already has are
exactly the three this run requires.

> **Rebuild it rather than looking for the last one.** A KB under `/tmp` is reaped — these were
> gone after nine days, taking every transcript and every ledger row with them, and with them the
> evidence for a factor that had already been published. Rebuilding is free and takes a minute, so
> the cost of the loss is only that the number has to be re-measured; the cost of *not noticing*
> is publishing a figure nothing on disk supports. `report` will happily print a different factor
> over whatever records survive, without saying that is what it is doing.

- **It is synthetic by construction** — its golden set says so in its first line. E6's exit
  criterion is that every constant is recorded as measured on synthetic data, so the corpus has to
  actually be synthetic, not merely non-private.
- **It carries fitted `[retrieval.confidence]`.** A KB without them reports `unknown` for every
  question (D-22), and `unknown` takes the loop — so on a fresh KB **the synthesis branch is
  unreachable and half this run cannot be measured at all.**
- **Its golden set reaches both branches by construction.** A `lexical` or `simple-lookup` question
  scores `high` and buys one synthesis call; a `no-answer` question scores `low` and buys the loop.
  Verified on the copy before spending anything:

```bash
SP=/tmp/measure-deep
cp -R <repo>/tests/demo-kb   "$SP/measure-kb"   && rm -rf "$SP/measure-kb/.pinakes"
cp -R <repo>/tests/partner-kb "$SP/partner-kb"  && rm -rf "$SP/partner-kb/.pinakes"
uv run --frozen pnk sync --kb "$SP/partner-kb"   # index the partner first, so the cross-KB link resolves
uv run --frozen pnk sync --kb "$SP/measure-kb"

# free, and it proves both branches are reachable before a euro moves
uv run --frozen pnk ask --kb "$SP/measure-kb" --json "How long do items stay in quarantine?" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['confidence'], d['escalation']['branch'], d['escalation']['cost_eur'])"
uv run --frozen pnk ask --kb "$SP/measure-kb" --json "What is the Institute's parking policy?" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['confidence'], d['escalation']['branch'], d['escalation']['cost_eur'])"
```

Expect `high synthesis 0.21` and `low decomposition 1.38`. **If the first prints `unknown`, stop** —
the thresholds did not survive the copy, and every run after that would price the expensive branch.

**Run that probe over *every* question you are about to pay for, not the two above.** It is free
and it is the only thing that says which branch a question actually buys. Measured 20260821: of
the three `no-answer` questions step (c) used to name, one — *"Which software does the catalogue
run on?"* — scores **`medium`**, which takes the **cheap** branch. Running the list as written
bought a synthesis call and filed it as a loop measurement. Step (b) already warns that a `calls`
of `2` means the branch was mis-selected; this is the same defect inverted, and nothing caught it
because the questions were chosen before `[retrieval.confidence]` was fitted and never re-checked
against it.

Then append the caps, raised deliberately and each just above the worst case it has to clear, so a
cap can still catch a runaway. **Two of the four are now the shipped default** — D-30 raised
`per_operation_eur` to 2.00 and `daily_eur` to 6.00 in 0.24.0, which is why the 20260821 run
completed the whole plan on both KBs with no `[budget]` section at all. The block is still worth
stamping for the two that differ: `confirm_above_eur` (the shipped 0.01 prompts on every run, which
`--yes` also answers) and `monthly_eur` (the shipped 30.00 is five times what this plan needs):

```toml
[budget]
confirm_above_eur = 2.00     # > one loop run's EUR 1.3764 ceiling, so the run is not a wall of prompts
per_operation_eur = 2.00     # > that same per-run ceiling
daily_eur         = 6.00     # > the whole plan's EUR 5.1836 worst case
monthly_eur       = 6.00     # this KB exists for one run; no reason to allow a second
timezone          = "UTC"
on_exceed         = "abort"
```

### What it costs

**€5.1836 worst case** for the plan below, and the *point of the run* is that real spend lands far
under it. Worst case assumes every call hits `MAX_TOKENS = 8_000` output and the full input ceiling.

| Step | Runs | Worst case each | Subtotal |
|---|---|---|---|
| (a) input constants via `count_tokens` | — | €0 | **€0** |
| (b) the cheap branch — `high` questions | 5 | €0.2109 | €1.0544 |
| (c) the loop — `no-answer` questions | 3 | €1.3764 | €4.1292 |
| (d) the refusal path — cap below the estimate | 1 | €0 — refused before any call | **€0** |

Re-price before running; both `prices.toml` and the KB's own `final_k` / `[chunking] max_tokens`
move the figure:

```bash
uv run --frozen python -c "
from datetime import datetime, timezone
from pinakes.deep.estimate import estimate_operation, SYNTHESIS, DECOMPOSITION
from pinakes.budget.prices import load_prices
prices = load_prices(); now = datetime.now(timezone.utc).strftime('%Y%m%d %H:%M')
for branch in (SYNTHESIS, DECOMPOSITION):
    est = estimate_operation(branch=branch, max_rounds=3, final_k=5, chunk_max_tokens=120,
                             model='claude-opus-5', prices=prices, now=now, max_price_age_days=3650)
    print(f'{branch:15s} EUR {est.total_eur:.4f} worst case')
"
```

### The run

Check `pnk budget` between steps, exactly as the extractor run does.

**(a) The input constants — free, and done first.** Nothing here generates a token, so run it
before deciding whether to spend at all: if a ceiling is already far above what a real request
carries, that is the over-reservation showing up before any money moves.

```bash
uv run --frozen --env-file <repo>/.env python3 tools/deep_reservation.py count \
    --kb "$SP/measure-kb" --questions "$SP/measure-kb/eval/questions.yaml"
```

Compare each measurement against `deep/estimate.py`'s constant. **A ceiling is never lowered to a
measurement taken on synthetic data** — `PAGE_TOKEN_CEILING`'s comment is the precedent and it is
binding here (E6's exit criterion). What a low measurement buys is the *published factor*, not a
smaller constant.

**(b) The cheap branch — five `high` questions, one paid call each.**

```bash
for q in "How long do items stay in quarantine?" \
         "What temperature and humidity are the stacks held at?" \
         "What resolution are master images captured at?" \
         "Which kinds of name get an authority record of their own?" \
         "When does an enquiry become a paid service?"; do
  uv run --env-file <repo>/.env pnk ask --kb "$SP/measure-kb" --deep --yes --json "$q" > "$SP/synthesis-$RANDOM.json"
done
uv run --env-file <repo>/.env pnk budget --kb "$SP/measure-kb"
```

Then check, in order:

- `answer.branch` is `synthesis` and `answer.calls` is **1** on every one. A `2` means the branch
  was mis-selected and the run measured the wrong thing.
- `response.model` against the requested alias, with `startswith` — the same check the extractor
  run makes, for the same reason.
- every run left a transcript at `.pinakes/deep/<operation_id>.json` (E5), and `pnk budget` shows
  one `ask` row per `call_id` it names.

**(c) The loop — and it takes two KBs, not one.**

**Only two of the calibrated KB's `no-answer` questions score `low`.** Use those, and take the
round cap from the *uncalibrated* KB, for the reason below:

```bash
# the calibrated KB, `low` -> the `decomposition` branch
for q in "What is the Institute's parking policy?" \
         "How much does a reader's ticket cost?"; do
  uv run --env-file <repo>/.env pnk ask --kb "$SP/measure-kb" --deep --yes --json "$q" > "$SP/loop-$RANDOM.json"
done

# the uncalibrated partner, `unknown` -> the same price, no early stop
uv run --env-file <repo>/.env pnk ask --kb "$SP/partner-kb" --deep --yes --json \
    "How much does a reader's ticket cost?" > "$SP/loop-unknown-$RANDOM.json"

uv run --env-file <repo>/.env pnk budget --kb "$SP/measure-kb"
uv run --env-file <repo>/.env pnk budget --kb "$SP/partner-kb"
```

**Why not three questions on the one KB, as this step used to say.** The old argument was that
`no-answer` questions cannot stop early — nothing in the corpus answers them, so the sufficiency
gate would have to run to the round cap, which is the worst case the reservation was sized for.
**Measured 20260821, that is false.** Both `decomposition` runs stopped at **sufficiency**, after
2 rounds and after 1 round of 3: a gate reading a calibrated signal is perfectly willing to
conclude that enough has been established *about a question the corpus cannot answer*. So on a
calibrated KB the round cap is not reachable by choosing a harder question.

**The branch that does reach it is `unknown`**, on a KB with no `[retrieval.confidence]` at all —
`tests/partner-kb`, which has none by design. D-22 gives it no early stop, so it ends at the round
cap or the budget and says which. It is priced identically to `decomposition` (the missing signal
changes when a run *stops*, never what a round *costs*), which is what makes it a valid instrument
for the loop's worst case rather than a different measurement.

Check on every run that `answer.stopped_by` names a loop bound rather than the budget, and that
`answer.partial` and `answer.label` say which one ended it (D-22). Expect `sufficient` on the
calibrated pair and `round-cap` — or `no-new-subproblems`, a third terminator neither this document
nor D-22 had named — on the uncalibrated one.

**(d) The refusal path — free, and it proves the cap is real.**

Lower `per_operation_eur` below the loop branch's estimate and re-ask a `no-answer` question. The
run must refuse **before its first call**, leaving no ledger row and no transcript (D-23 and E5's
rule that a run which never returned writes none).

```bash
# per_operation_eur = 1.00, below the EUR 1.3764 the loop branch reserves
uv run --env-file <repo>/.env pnk ask --kb "$SP/measure-kb" --deep --yes "What is the Institute's parking policy?"
uv run --env-file <repo>/.env pnk budget --kb "$SP/measure-kb"   # unchanged from step (c)
```

**(e) Publish the factor.** The join is the one E5 left behind — `transcript.call_ids()` against
`sync.ledger_spend()`:

```bash
uv run --frozen python3 tools/deep_reservation.py report --kb "$SP/measure-kb"
```

### Afterwards

1. **`deep/estimate.py`** — every constant gains its measurement, the command that produced it, and
   the word *synthetic*. No constant is lowered.
2. **`prices.toml`** gains nothing from this run: it prices models, and this run measured a loop.
3. **DESIGN §5** gains the over-reservation factor for every branch, with date, model and euros
   actually spent.
4. **STATUS.md** gains what this run measured.
5. **The retrospective** carries the spend for the whole run, and any constant whose measurement
   contradicted its own comment.

### What it settled — run 20260821, €0.2131

Done in full on 20260821 against `claude-opus-5`: steps (a) through (e), the refusal probe
included. **€0.2131** of the €5.1836 worst case, which is itself the headline result.

| Constant | Reserved | Measured | Factor |
|---|---|---|---|
| `PROMPT_TOKENS` | 1,500 | 376 | 3.99× |
| `QUESTION_TOKENS` | 1,000 | 399 | 2.51× |
| `PASSAGE_ENVELOPE_TOKENS` | 250 | 28 | 8.93× |
| `VENDOR_TOKENS_PER_CHUNK_TOKEN` | 3 | 2 | 1.50× |
| `CARRIED_MEMORY_TOKENS` | 4,000 | 1,612 | 2.48× |
| `MAX_TOKENS` (output) | 8,000 | 660 widest of 22 calls | 12.12× |

| Branch | Runs | Calls | Reserved | Spent | Over-reservation |
|---|---|---|---|---|---|
| `synthesis` — the common case | 5 | 5 | €1.0500 | €0.0353 | **29.75×** |
| `decomposition` — calibrated loop | 2 | 6 | €2.7600 | €0.0542 | **50.92×** |
| `unknown` — uncalibrated loop | 2 | 11 | €2.7600 | €0.1235 | **22.35×** |

Three things in that second table are worth reading twice. **The calibrated loop is the *most*
over-reserved**, because a reservation must cover `max_rounds` and calibration is exactly what
lets a run stop before reaching them — the uncalibrated branch is the least over-reserved because
it spends the rounds it reserved. **`MAX_TOKENS` carries most of the ratio**, since output bills
at five times input and is two thirds of a round's price. And **no constant was lowered**: the
corpus is synthetic, which is E6's exit criterion and `PAGE_TOKEN_CEILING`'s binding precedent.

**An earlier partial run published 19.0× and 16.5×.** Those are superseded, and not because they
were mis-computed: their KBs were reaped from `/tmp` before anyone re-ran `report`, so no surviving
transcript or ledger row supports them. Treat them as withdrawn rather than as a second data point.

**Both branches are reported separately and the cheap one is named as the common case.** A single
blended figure would hide the whole return on having a calibrated signal — one call against
`2 × max_rounds` — which is the reason D-28 chose this shape.
