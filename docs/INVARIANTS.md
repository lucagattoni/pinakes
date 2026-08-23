# Invariants that must not be broken

**Audience: any agent changing code here. Goal: executor.** Every one of these fails *silently* when
broken — a regenerated ULID, a sidecar that still parses, a €0 record for money that left the
account. That is why they are a list and not a convention.

Extracted from [`CLAUDE.md`](https://github.com/lucagattoni/pinakes/blob/main/CLAUDE.md) on
20260806 00:00, when that file crossed its own size guardrail — as `RELEASING.md` was on 20260801 —
and extended on 20260823 when it crossed it again. Nothing was dropped in either move: each
invariant below names the file that owns its detail, the rules **no other file states** are written
out in full further down, and [§ The paid path's key is its own](#the-paid-paths-key-is-its-own)
carries the one whose reasoning CLAUDE.md no longer has room for.

## The invariants, and who owns the detail

| Invariant | Detail lives in |
|---|---|
| **Document and KB ULIDs are permanent** — never renumber, never regenerate. Every inbound link depends on them, and there is no migration machinery by design | [MANIFEST.md](MANIFEST.md) — the `id` rows |
| **An unknown key in a sidecar round-trips byte-identically** — stronger and more testable than "untouched", which was true of the dict and false of the file. The invariant is **bounded**, and **each exclusion is pinned by a test** — the authoritative list, because a bound stated only in prose cannot notice the library moving under it | [VERIFICATION.md § The sidecar round-trip](VERIFICATION.md#the-sidecar-round-trip-l5b) and [MANIFEST.md](MANIFEST.md)'s bounds table are authoritative; [DESIGN.md](DESIGN.md) §2.2 gives the rationale |
| **`docs/` belongs to the user** — never modify source documents, never delete a sidecar without an explicit `--prune`-style flag plus a printed list | The two narrow exceptions are [below](#rules-that-live-only-here) |
| **`.pinakes/` is disposable except `ledger.jsonl`, any cache entry a paid backend wrote, and any deep-run transcript** — a rebuild must preserve spend history; a paid cache entry and a transcript are both derived state that cost real money to derive. The automatic sweep spares all three, and destroying one takes an explicit target: `--clear-cache=paid` for a cache entry, `--clear-cache=transcripts` for a transcript | [DESIGN.md](DESIGN.md) §3, [CLI.md](CLI.md#pnk-sync) |
| **A deep-run transcript is KB-local and never leaves `.pinakes/`** — it holds the question and the model's prose about this KB's documents, so it lives with the state that is already gitignored, and no command sends its contents anywhere else. **It does not loosen [DESIGN.md](DESIGN.md) §5's rule that the ledger stores no query text and no document content** — that rule is unchanged, and the transcript is a second file rather than a wider ledger | [CLI.md](CLI.md#pnk-ask---deep), [DESIGN.md](DESIGN.md) §5 |
| **The ledger is append-only** — correct a record by appending another (`pnk budget --resolve`), never by editing | [DESIGN.md](DESIGN.md) §5 |
| **The free path stays free — paid entry points are an enumerated allowlist.** Exactly these may spend: `pnk sync` with `[extraction] backend = "claude-vision"` or `--extract=claude-vision`; `pnk ask --deep`. Each goes through the §5 accountant, and each has exactly one module permitted to import a client — `extract/claude.py` and `deep/client.py`, **the two entries, and the list is now complete.** What they share lives in `src/pinakes/paid.py`, which is *not* exempt: it imports no client, so the gate scans it like any other file. **Adding an entry point edits [`.paid-path-allowlist`](https://github.com/lucagattoni/pinakes/blob/main/.paid-path-allowlist), DESIGN §1 and this page in the same commit.** Four gates enforce it; the one that matters runs the whole free path in a fresh subprocess and asserts no paid client reached `sys.modules` | [DESIGN.md](DESIGN.md) §1 |
| **Money is `Decimal` end to end, quantised only once — at ledger-write time** | [DESIGN.md](DESIGN.md) §5, [MANIFEST.md](MANIFEST.md) |
| **Index schema changes bump `schema_version` and require a rebuild. Never write a migration** | [DESIGN.md](DESIGN.md) §3 |

## Rules that live only here

These are implementation rules, not restatements — nothing else in the tree says them.

- **Sidecars go through `ruamel.yaml` round-trip at YAML 1.2 — never `pyyaml`**, which is dev-only
  and gated by an AST scan plus a runtime check. `write()` reconciles known keys *into* the loaded
  document; it never renders a fresh one. Values must be JSON-encodable, keys strings.
- **The two exceptions to `docs/` belonging to the user**, both narrow: a paid PDF extraction (or
  `--force` discarding one) additively rewrites that document's own sidecar with
  `provenance.extraction` (DESIGN §2.2) — no other key, never on a free extraction; and a
  user-invoked authoring command writes `links[]` to the source document's own sidecar.
- **A `void` ledger record needs proof the call never billed** — written only when a
  `response_received` flag is false, never from a bare `finally`, which would record €0 for money
  that already left the account. Under-counting is the one direction a budget may never be wrong in.
- **Never probe a backend's availability by loading it** — `is_backend_installed` answers through
  `find_spec`; `load_extractor` runs the factory, which imports the client.
- **Convert a TOML float via `Decimal(str(value))`, never `Decimal(value)`**, which reproduces
  float's binary imprecision instead of the decimal a human wrote:
  `Decimal(0.05) != Decimal("0.05")`.

## The paid path's key is its own

**Every paid path reads `PINAKES_ANTHROPIC_API_KEY`, and the rule is enforced in code** —
[`paid.py: resolve_api_key`](https://github.com/lucagattoni/pinakes/blob/main/src/pinakes/paid.py),
bound to its own surface by each of the two entry points (`extract/claude.py`, `deep/client.py`), so
a refusal names the command the user actually typed rather than the layer that refused.

**Machine hygiene cannot enforce it.** The SDK reads its own variable out of whatever environment it
is handed, so on a machine where another tool exports `ANTHROPIC_API_KEY` the paid path would find a
live key nobody aimed at it (measured 20260804). A name only Pinakes uses, passed explicitly, is what
makes supplying the key a deliberate act rather than a property of a tidy machine.

The key lives in `.env` (gitignored by pattern) and is passed per command:
`uv run --env-file .env pnk …`. **Never teach Pinakes to load `.env` itself, and never add an
`ANTHROPIC_API_KEY` fallback** — both are the same defect, one layer apart.

**The invocation form is not what bounds spend.** [DESIGN.md](DESIGN.md) §5's caps and the paid-path
allowlist above are; `uv run --env-file` only decides which process sees the key. See
[MEASUREMENT-RUN.md](MEASUREMENT-RUN.md).
