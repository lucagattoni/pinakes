# Clear the user-facing list, then decide whether to add process

**Drafted as a proposal by a read-only survey session 20260901 11:48 UTC; reviewed, revised and
adopted as a plan by the planner 20260901 11:58 UTC, against `main` at `6ae2a6c`.** § 3 is a build
order and its rows are live. **§ 4 is the user's, and two rows do wait on it** — row 18 is blocked on it outright, and row 15's body defers its gate behind it while its *Blocked on* cell reads `nothing`. **Corrected 20260902 07:41; the sentence previously read *"nothing waits on it"*, which was false in both directions and is the register-vs-body split this file rows against elsewhere.** — the build order does not
depend on the answer, which is itself part of the argument in § 4.

**Audience: the planner, the coder and the user. Goal: sequence work that is already decided, row one
item nobody has rowed, and put one standing decision to the user.**

**What the planner changed in review**, each verified rather than accepted:

| # | Change | Why |
|---|---|---|
| 1 | § 2's verification grep replaced | The original was a null over a selector never shown able to fire. The replacement names the population |
| 2 | § 3 row 9 keeps its rank, gains a premise correction | `init.py` **does** defend at creation; the row is about drift, and it is stronger when it survives someone opening the file |
| 3 | § 4 gains a third reading and a conflict-of-interest note | Both options assume the ratio measures process appetite. It may measure queue position |
| 4 | § 2's sizing measured, then **the measurement was itself refuted** | The planner's first correction compared battery-file lines against gate-source lines and double-counted mutants. The survey session refuted it; § 2 carries the corrected version and says so |
| 5 | § 2's verb corrected: `check.sh` **names** eleven gates and runs ten | `wheel_import_gate` needs `uv build` and a network resolve; CI's `build` job runs it |
| 6 | § 3 row 3 (cut the release) gained an explicit stop | A session reported the user holding the release; that hold is written in no document, and a tag publishes to PyPI irreversibly |

**M1 was re-run by the planner and its counts are exact** — 11 gates, 4 with a battery, 7 without —
**but its verb was not**: `check.sh` *names* eleven and runs ten (§ 2). A looser sweep of `file =` keys also returns batteries for `mcp_handshake_gate`,
`release_tag_gate`, `review_ledger`, `mutate` and `reachable_ceiling_probe` — correctly excluded,
because `check.sh` does not invoke them.

**What this file does not do.** It re-decides nothing. It opens no finding that
[`20260825_1240-run-pinakes-sweep.md`](20260825_1240-run-pinakes-sweep.md) already carries, and it
does not restate that plan's rows — after the register audit landed in `d441f48`, every open row
there carries its own dated measurement and is better evidence than a summary of it would be. **Only
§ 2 is new.** The rest is order, and one question.

---

## 0. What was measured, and when

**Each row is a measurement I ran, not a claim inherited from a register.** The register audit that
landed at `d441f48` is why this list is short: rows 4–14 of the sweep plan were re-measured at
20260901 11:35 UTC by the planner and I have not duplicated that work.

| # | Measurement | Result | How |
|---|---|---|---|
| M1 | Custom gates `check.sh` invokes, vs. gates with a mutation battery | **7 of 11 have no battery** | `grep -oE 'tools/[a-z_]+\.py' check.sh` ∩ `file =` keys across `tools/batteries/*.toml`, on `c621d08` |
| M2 | Insertions by area, `51a34bb` → `b6be317` | `src/` **928 of 16,909 — 5.5%**; `docs/`+`plans/` 7,677 | `git diff --numstat`, non-merge window since 20260824 04:07 |
| M3 | Register corpus size over the same window | `docs/` 20,110 → 22,786 (+13%); `plans/` 10,883 → 15,631 (**+44%**) | `git show <sha>:<path> \| wc -l` at both ends |
| M4 | Retro fragments ever added, judged by row 12's gate as written on its branch | 107 files, 91 judged, **18 would fail, 0 false positives** | each file read at its own adding commit via `git log --diff-filter=A` |
| M5 | Pending fragments — **pinned to a sha, because this is the one measurement that moves** | **16 at `9cc9bc1`: 5 `changelog.d/` + 11 `retro.d/`**, of which **9** `retro.d/` carry a `20260901_` stamp | `git ls-tree -r --name-only 9cc9bc1 -- changelog.d retro.d \| grep -v README`, re-run 20260901 12:26 UTC |

**M1 is the only one that produces a work item.** M2–M4 are context for § 4 and nothing depends on
them being acted upon. **M5 is the only one that decays**, because the fragment directories change with
every landing — which is why it names a sha, and why § 3 row 3 now cites it instead of restating its
numbers. Row 3 restated them four times on this file's own landing day and every restatement
disagreed with M5 *and* with the tree: M5 said 11, row 3 said 15 twice and 10, and the tree held 16.
**A register decayed inside the plan about registers decaying, within four hours of landing.**

---

## 1. Why this plan is about order and not about findings

**The product is finished against every plan it has; the queue that keeps it correct is what
stopped.** Every named release has shipped, failed its own measurement honestly and ships off, or
waits behind a written trigger. There is no feature backlog by construction — that is a
finished-product signature, not a stall.

Against that: **the published 0.31.1 carries eight reproduced user-facing defects, found by running
Pinakes on 20260825, decided the same day, and still unbuilt.** They are rows 4, 5, 6, 9 and 10 of
the sweep plan's build order, each re-measured 20260901 11:35 UTC. Two are the sharp kind — S1
indexes *nothing* when one file is unreadable, S4 reports a bricked KB as created with exit 0.

**So the work is already decided, already owned and already rowed. What it lacks is a position in
front of everything else.** That is all § 3 supplies.

---

## 2. ENG-1 — seven of eleven gates have never been mutation-tested

**Recorded in no plan and no queue, which is why it is here rather than in the sweep plan's table.**
I measured it because a survey raised it (M1), and it is the highest-leverage unrowed item in the
repository.

`check.sh` names eleven custom gates and **runs ten of them**: `wheel_import_gate.py` is named at
`check.sh:57-65` and deliberately not run there, because it needs `uv build` and a network resolve, so
CI's `build` job and `release.yml` run it instead. Four of the eleven have a mutation battery. Seven
do not, and the count is unaffected by where the eleventh runs:

| Gate | Battery? | What it enforces |
|---|---|---|
| `paid_path_gate.py` | **none** | the two-entry paid-path allowlist — **the only invariant that costs real money** |
| `traversal_cap_gate.py` | **none** | the link-traversal bound |
| `link_density_gate.py` | **none** | the link-density bound |
| `eval_reproducibility_gate.py` | **none** | that a published eval number can be re-derived |
| `shared_file_overlap.py` | **none** | the pre-merge overlap check every landing is told to run |
| `template_drift_gate.py` | **none** | that the stamped template matches the shipped one |
| `wheel_import_gate.py` | **none** | that the built wheel imports without an extra |
| `fragments.py`, `markdown_link_gate.py`, `release_order_gate.py`, `status_header_gate.py` | ✅ | — |

**This repository's own rule is that a gate is only evidence once something has shown it can kill**
— *"a mutation pass is evidence only if the harness is shown to kill"*, and *"a run with no kills is
a broken harness, not a clean bill"*. By that rule seven of these eleven are unverified until
somebody checks, and nobody has checked.

**A correction to my own framing, because it changes what "do `paid_path_gate` first" means.**
[`docs/INVARIANTS.md:24`](../docs/INVARIANTS.md) says **four** gates enforce the paid path, and that
*"the one that matters runs the whole free path in a fresh subprocess and asserts no paid client
reached `sys.modules`"* — that is `tests/test_paid_path.py` with `tests/free_path_run.py`, not
`tools/paid_path_gate.py`. So the grep gate is not the strongest enforcement and should not be
described as though it were.

**It does not weaken the item; it widens it.** No battery names *any* paid-path file — not the
gate, and not the subprocess test that INVARIANTS calls the one that matters. **The strongest
assertion protecting the money invariant has never been shown able to fail.** Do that one first,
then the gate. **Verify it with a selector that names its population**, not with a grep that returns nothing:

    grep -rln 'PINAKES_ANTHROPIC_API_KEY' src/
      -> src/pinakes/paid.py, src/pinakes/errors.py, src/pinakes/deep/loop.py

Those three files are the paid path. None is a `file =` key in any battery. Stated that way a future
zero carries information; stated as `... | grep -i paid` it cannot, because nothing shows the
selector could ever have fired.

**Scope discipline, because this is the exact shape § 4 wants to freeze.** This is not new process.
It adds no gate, no rule and no register — it asks whether seven gates that already exist do
anything. **Batteries are appended to the target's existing battery file, never started as a second
file** ([`tools/batteries/README.md`](../tools/batteries/README.md)), and
`tests/test_batteries.py` fails if that is got wrong.

**Sizing, measured — and the planner's first version of this paragraph was wrong.** It claimed
`template_drift_gate` at 684 lines was beyond anything ever batteried here, and the survey session
refuted it with one command: **`tools/release_order_gate.py` is 797 lines and carries a full battery**
(458 lines, 45 mutants). 684 is *below* the existing precedent, not beyond it. The planner's mutant
counts were also doubled by an anchor matching both `[[mutant]]` and `name = ` in the same block —
batteries run **128-458 lines and 8-45 mutants** (median 179 and 15; 211 mutants across 11 batteries),
and nothing here has 90.

So the conclusion inverts: **do not split `template_drift_gate` — size it against `release_order_gate`,
the closest and larger precedent.** Roughly 400-450 battery lines, 40-odd mutants, about two sessions.
The other six sit between `status_header_gate` (268 source → 144, 12 mutants) and `fragments.py` (598
→ 207, 20), so one session each holds for them. The original "roughly one session each" was still
wrong for the seventh; it was corrected for a reason that did not survive checking, and the corrected
number stands on the precedent instead.

**The honest expectation is that most of these seven gates kill their mutants, and that the exercise
returns confirmation rather than defects. That expectation is the reason to do it, not a reason to
skip it** — if a gate does not kill, everything it has ever certified is unsupported, including
past releases.

---

## 3. Proposed build order

**All of this is coder work and none of it needs a decision.** Rows 1–6 are the sweep plan's own
rows; the column names their number there rather than restating them. **This table proposes an
order, not new work** — the sweep plan remains the owner of every row it already carries.

| # | Item | Sweep row | Blocked on | Why here |
|---|---|---|---|---|
| 1 | Row 14 — teach `markdown_link_gate` the splice destination, both arms; restore the two code-spanned links | 14 | nothing | A correct link is currently degraded on `main` and both fragment READMEs carry a caveat contradicting their own instruction. Live incoherence in the tree beats everything else. |
| 2 | Row 12 — the retro heading + stamp gate | 12 | nothing | Finished and pushed on its branch; landing it is cheaper than carrying it. **M4 is the evidence it earns its place:** 18 of 91 historical fragments would fail it and none is a false positive. |
| 3 | **Cut the release — ASK FIRST** | — | rows 1–2, **and an explicit user go-ahead** | The fragments **M5** counts are pending while `[Unreleased]` reads empty, which is itself misleading. **It is a MINOR, not a patch — measured at `6ae2a6c` 20260901 12:05 UTC.** (The number is deliberately not written here: *a version number belongs to a release when it is cut, never before*, and `docs/RELEASING.md` names none either.) Of M5's five `changelog.d/` fragments, two are **Added** (`agent-spend-measures-what-the-agents-cost`, `the-ceiling-probe-takes-the-golden-set-as-an-argument`) and three are **Fixed**, so the SemVer table gives MINOR. **The counts live in M5 and are deliberately not restated here** — an earlier version of this cell restated them four times and disagreed with M5 and with the tree every time. `__version__` is `0.31.1` and `## [Unreleased]` is **empty**, which makes the document say nothing is pending while the tree holds every fragment M5 counts — the exact trap `docs/RELEASING.md` exists for. **Do not cut this without asking.** A session on 20260901 recorded the release as held by the user (*"still uncut, as you set it"*), and that hold appears in no document in this repository — so it cannot be verified from the tree and must not be inferred away by this row. A tag publishes to PyPI and PyPI never accepts a version twice: this is the only row here that cannot be undone. **State plainly in the release notes that this release reaches no user of `pnk`** — the rename crash people would feel is already out in 0.31.1; this is two dev tools, a docs-audit closure and a gate unblock. **The cost of holding, stated because it points the other way:** M5's nine `20260901_`-stamped `retro.d/` fragments are records of that day's own wrong diagnoses — five instances of one failure across three sessions — and they reach `docs/RETROSPECTIVES.md` only at a cut. Every day held is a day the published retrospectives omit the day that produced the most of them. That argues for cutting; it does not argue for cutting without asking. Planner-owned. |
| 4 | **S1** — `PermissionError` aborts the whole walk | 4 | nothing | The worst failure mode in the list: one unreadable file and **nothing is indexed at all**. |
| 5 | **S4** — escape at render in `template.py` | 5 | nothing | Silent, permanent, and `init` refuses to repair it. Exit 0 on a bricked KB. |
| 6 | **D-37's build** — gate the move hint on the orphaned sidecar | 9 | nothing | Fires on **every ordinary deletion, on every `pnk sync`**, claiming an id was minted when none was. Highest frequency of anything in the list. |
| 7 | **S5–S9** — the accept-then-mishandle batch | 6 | nothing | Five inputs accepted and then mishandled. Whoever builds it should decide up front whether it is one fix or five, and say which in the commit. |
| 8 | The four Low classes | 10 | rows 4–7 | `-k 0` becoming the default page size, mistyped `--source-type` returning nothing, the wrong `confidence_reason`, a symlink loop reported healthy. |
| 9 | **The `.pinakes/` questions in `doctor`** (D-31/D-32/D-33, option C, unconditional) | exposure 5–6 | nothing | **Ranks with S1 and S4 on severity, not below them:** since the deep release the index holds users' verbatim questions, only `init` ever asks whether `.pinakes/` is committed, and it asks once. A KB that starts leaking *after* init is never warned while `doctor` reports clean. **Checked before ranking it:** `init.py:122-156` does defend at creation — it writes a `.gitignore` and asks git via `check-ignore` rather than text-scanning, the scan it replaced having been measured wrong in both directions on 20260825. So the exposed population is KBs whose ignore state **drifted after init**, not every KB. That is a lower frequency than S1 or S4 and a worse, irreversible consequence — keep it level with them, not above. **And that defence is itself batteried** (`tools/batteries/src-pinakes-init.toml`, 14 mutants, one of them targeting the `check-ignore` diagnostic), so row 9 is narrower *and* better defended than the draft said — which is the version worth landing, because it is the one that survives being checked |
| 10 | **ENG-1 · `paid_path_gate` battery first**, then the remaining six | — new | nothing | § 2. Split per gate; each is its own commit. |
| 11 | Row 11 — the FX guard, two parts | 11 | nothing | Already scoped, including the sentence the commit must carry. |
| 12 | Row 13 — the vacuous verifier | 13 | nothing | Small; pin the empty-input case as non-zero. |
| 13 | **The BOM arm covers only one stream** — widen it to `changelog.d/`, and nothing else | — new | row 12 | Raised by the coder 20260901, while reviewing row 12, and **outside row 12 as scoped** — recorded, not widened into it. Row 12's BOM check returns early on `stream.name != "retrospectives"`, so a changelog fragment saved with a byte-order mark still splices the mark into `CHANGELOG.md` with no gate seeing it. **The consequence is not cosmetic, which is why this is a row and not a note:** the mark precedes the leading `- `, so `'\ufeff- **claim**'.startswith('- ')` is `False` and the entry's first bullet renders as a **paragraph** — the same failure mode as one leading space in a retro fragment, in the other stream. **Take it right after row 14** while `fragments.py` is open, or later; it blocks nothing and the release does not wait on it. Its own commit and its own review pass — do not fold it into row 12, which is already under review. |
| 14 | **A retro fragment's *second* `## ` heading is spliced unvalidated** — require the form, not the value | — new | row 12 | Found by the coder's row-12 review pass 7 and **deliberately not fixed there**: not a regression, and the obvious rule would have refused a real released fragment. **Corrected 20260902 00:05 — this row first read *116 fragments, exactly one*, and both numbers were wrong.** Re-measured from the object store (`git rev-list <rev> --objects`, `cat-file` on every blob) rather than from the log, because a log-keyed probe reads a consumed fragment at its *deletion* commit and skips it silently: **126 fragment paths, 233 distinct versions, `unreadable: 0`**, and **two** carry two column-0 `## ` headings. **CORRECTED AGAIN 20260902 02:44 — the first correction named a method but no measurement point.** It said `--all`, which is not a corpus: it is every ref any branch happens to hold at the instant it runs, so it counted unlanded work and had drifted to 132 paths / 243 versions within the hour. **The selector is now pinned — `origin/main` at `7751f96`, landed history only** — and both of this row's denominators are the same 126, where they were 129 and 126 from two different populations. The qualitative result is unchanged: exactly **two**, the same two files. **Only one of the two is evidence.** `retro.d/20260805_1907-a-guard-that-could-not-fire.md` stamps its second heading `19:15` against a filename prefix of `1907`, **on purpose**, recording a second moment inside one incident. `retro.d/20260823_0233-a-gate-can-be-green-on-the-list-next-door.md` stamps **neither** heading — and it is *not* pre-convention, which was the obvious way to set it aside and is false: **10 of 126 fragments carry an unstamped first heading, scattered across the whole timeline to 20260831**, so stamping never became universal and there is no cohort boundary to put it behind. It is an instance of the ~8% non-compliance row 12's gate exists to stop, not a deliberate choice about second headings, so it licenses nothing here. **n=1 stands.** **Ruled 20260901, planner:** a second heading must carry a parenthesised `YYYYMMDD HH:MM` stamp ending the heading, in the same spelling as the first; it **need not equal the filename prefix** and **nothing constrains its value**. One instance licenses the *existence* of a later stamp and does not license a monotonicity rule, so none is written. **The 116-and-one measurement was the planner's, taken over the live directory and stated as a fact about the corpus** — the same defect this plan rows against others — and was caught by the coder, who found the second fragment. `retro.d/README.md` gains the sentence at the same time — planner-owned, dictated, not drafted. |
| 15 | `tools/batteries/tools-markdown_link_gate.toml:26` — a bare date where the format reserves a version | — new | nothing | One comment, one line: `# 20260823 · …` conforms to neither form `tools/batteries/README.md` reserves. Of the tree's 30 battery sections, 19 use `unreleased, YYYYMMDD ·` and 8 use `X.Y.Z ·`; this is the only one matching neither. **The correct header is `0.30.0 · `, not `unreleased, 20260823 · `** — `tools/markdown_link_gate.py` was added in `6d7c9e3` (20260823 15:44) and **shipped**: `v0.30.0` is the earliest tag containing it and `v0.29.0` does not, so the selector discriminates. The planner instructed `unreleased` here and was **wrong**; writing it would have replaced a bare-date non-conformance with a false claim, in the one file whose job is recording which release shipped which property. Caught by the coder, re-verified independently before the correction was written. **The bare date is both spellings' raw material** — it reads as unreleased-ish precisely because the unreleased form is the one carrying a date, and the version form carries none. **And the gate that would catch it is deliberately refused for now** — nothing gates the section format, adding a check *is* new process, and § 4 is a live decision in front of the user. Recorded as a refusal rather than an oversight; propose it again if § 4 comes back B or *neither*. |
| 16 | **`tools/markdown_link_gate.py` and the renderer disagree about what a heading is** — four shapes of five | — new | nothing | `_HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")` implements CommonMark's up-to-three-spaces rule. Python-Markdown 3.10.3 — **the renderer that builds the site**, measured 20260902 via `uv run --no-project --with-requirements requirements-docs.txt` — refuses even one. Only `'## x'` agrees. For `' ## x'`, `'  ## x'` and `'\t## x'` the gate **registers an anchor the site never renders** (paragraph, paragraph, code block), so a link to one **passes the gate** and resolves to nothing; for `'##x'` the reverse — a real H2 the gate cannot see, so nothing may link to it. **Scope is the whole point:** inside `docs/`, `mkdocs build --strict` catches it, but the gate's own docstring says it exists for *"the Markdown the docs site never sees"* — `CLAUDE.md`, `plans/`, `changelog.d/`, `retro.d/` — and **there nothing catches it at all**. Row 12's `^## \S` closes it for retro fragments only, one directory of four. Found while ratifying the row-12 branch's `retro.d/README.md` text, whose own (correct) claim that `'##x'` is invisible to the gate is the half of the divergence that was already known; the other three shapes were not. **Not folded into row 12** — different tool, and that branch was finished. |
| 17 | **One character in a filename silently exempts a fragment from the stamp gate** — narrow the exemption | — new | row 12 | Found by the coder's row-12 pass 8. The stamp arm exempts a fragment when `_STAMP = re.compile(r"^\d{8}_\d{4}-")` fails to match the stem, so `20260901-0710-x.md` — hyphen for the underscore — is **exempted entirely**, reproduced with a control (`20260901_0710-x.md` refused, exit 1; the typo accepted, exit 0). **CORRECTED 20260902 02:04 — the first ruling's basis was false.** It read: *"`changelog.d` already refuses both that shape and a prefix-less one, so `retro.d` is the stream that omits the check."* `changelog.d` has **no prefix gate**; it has a **category** gate, and the decisive case separates them: `fixed-a-thing.md` — no prefix at all, head *is* a category — is **accepted**, while `banana-a-thing.md` is refused. A malformed prefix is refused there only *incidentally*, by shifting the first token out of `(added, changed, deprecated, removed, fixed, security)`. **Nothing in this repo gates a fragment's prefix format.** The planner tested three names, read the category arm's error text — which names the whole convention — as evidence of a prefix arm, and never tested the one case separating the hypotheses. Found by the coder. **§ 4 still does not hold it, on a basis that does not depend on the sibling:** row 12's decided property is *the stamp is the filename's*, a **copy relation**, and an exemption one substituted character triggers means the gate does not check that relation. Closing it implements row 12's decided scope rather than adding scope; § 4 restricts inventing rules, not shipping a decided gate with a known bypass. Row 15's refusal is still not a precedent — that gated battery section format, where there was no defect. **RE-RULED 20260902 02:04, planner:** exempt only a stem that **does not begin with a digit at all**; a stem beginning with a digit is claiming to be dated and must match `^\d{8}_\d{4}-` exactly or be refused naming the prefix. The first ruling said *8 digits*, which the coder improved on evidence. Licensed by measurement over every fragment path that ever existed — `retro.d` 126 total / 17 unprefixed, `changelog.d` 177 / 35, and **0 of those 52 begin with 8 digits**; all are pre-convention names (`l5b-…`, `added-…`). So it breaks nothing in 303 fragments and preserves the prefix-less acceptance `body_of`'s docstring records as deliberate. **The *8 digits* form left a residual and the residual named for it was the wrong string.** `2026090_0710-x` is **already refused today** by `_SLUG` (`^[a-z0-9]+(?:-[a-z0-9]+)*$`), because a failed `_STAMP` strip leaves the underscore in the stem: any malformed prefix keeping its underscore is caught already, and the typo escapes precisely *because* a hyphen removes it. The real residual was the all-hyphen shapes — `2026090-0710-x`, `202-0710-x` — and **the no-leading-digit rule leaves none**. Re-measured over all 303 paths: of the 52 with no canonical prefix, **0 begin with 8 digits and 0 begin with any digit**, control 251 of 303 stems do begin with one. **Its one real cost, chosen rather than discovered:** a name like `5-lessons.md` becomes refused — correct, since every new fragment owes a prefix, and 0 historical files are affected. Pre-existing either way: Python's `\d` matches Unicode decimal digits. |
| 18 | **No fragment gate validates that a filename's date is a date** — DEFERRED behind § 4, measured not guessed | — new | **§ 4** | Raised by the coder against row 17: `20261345_9999-x.md` begins with 8 digits and matches `^\d{8}_\d{4}-`, so under row 17's ruling it would demand its heading carry `(20261345 99:99)` — and would pass if it did. **Measured before ruling, four names through `changelog.d`'s format gate:** `20260901_0710` exit 0, `20261345_9999` (month 13, day 45, 99:99) exit 0, `20260230_2500` (Feb 30, 25:00) exit 0, `99999999_9999` exit 0. **Shape only; neither stream validates a date.** So row 17 leaves the two halves consistent rather than disagreeing, and the absurd case is acceptable: the gate's subject is *the stamp is the filename's*, a copy check, not a calendar check — a wrong-but-possible date (`20260901_0710` written on the 2nd) is equally uncaught, and impossibility is that same class made visible. **Deferred, and the new-process argument does hold here.** **CORRECTED 20260902 02:04:** this row first justified the split by *"row 17 was exempt because the sibling stream already had the check"* — and that sibling claim was false (see row 17). **The discriminator that survives is a different one: is the check the *decided property*, or a *different* property?** Row 12's decided property is *the stamp is the filename's*, a copy relation, so closing the exemption implements it. Calendar validity is a **different property** — nothing about a copy relation — so it is genuinely new, and § 4 holds it. Same treatment as row 15. Two questions that look identical get opposite answers on that, not on whether the sibling does it and not on whether the change is small. Propose again if § 4 returns B or *neither*. |
| 19 | **An unclosed raw-HTML block in a fragment absorbs every heading after it** — widen the checker beyond headings | — new | row 12 | Found by the coder's row-12 pass 9, and **outside row 12 as scoped**. A fragment carrying an unclosed `<div class="note">` passes every arm: `fragments.py --check` returns **exit 0, *"all well-formed"***, and `--apply` splices it. **Re-measured independently by the planner 20260902 07:50 under `mkdocs.yml`'s own extension list** (`admonition, attr_list, md_in_html, tables, footnotes, pymdownx.*`): two source `## ` headings render as **one** `<h2>`, the following fragment's heading and prose becoming literal text inside the div. **`md_in_html` does not rescue it** — the count is identical under Python-Markdown defaults, so this is not an extension misconfiguration. **The absorbing fragment is itself perfectly well-formed**, which is why no heading arm can ever see it: the damage is to the *next* fragment's rendering, not its own, and row 12's `^## \S` is the wrong shape of check for it. The coder further measured that the protected `## Design review passes` footer is absorbed and that `anchors_of` still mints all four anchors, leaving `markdown_link_gate` green on two headings the site does not have — **that half is the coder's measurement; the planner's fixture carried no footer and did not reproduce it.** Its own commit and its own review pass. |
| 20 | `tools/batteries/src-pinakes-pairing.toml:369` — a header conforming to neither form, on ASCII rules | — new | nothing | Sibling of row 15, found by the coder 20260902. The header reads `# unreleased, 20260831 - S16's residue…` — a hyphen where the convention has `·` — and its rules are ASCII `# ----` rather than `# ────`. **Verified by the planner: across `tools/batteries/`, 56 box-drawing rules against 6 ASCII**, so this file is the outlier on both counts. **This is why row 15's census needed a selector at all** — a `─`-delimited census cannot see this section, which is exactly how one tree yields 30 sections and 32 sections with neither count being wrong. Take it with row 15 or after it; blocks nothing. |

**Rows 4–9 are the list § 4 refers to as "the user-facing list".** It is empty when those six land.

**What this order deliberately puts last:** the G5 re-run, the ROADMAP review, X7 layer 3, D-36,
`_toml.py`'s message and `pageyield.py`'s example. Each is real; none reaches a user of `pnk`.

---

## 4. The decision for the user — a process moratorium

**This is the only thing in this file that is not already decided, and it is not an agent's to
take.** It is put here because M2 and M3 measure a ratio that nobody has ruled on.

**The evidence, stated with its selector.** Over `51a34bb` → `b6be317` (20260824 04:07 → 20260901
11:16 UTC), `src/` took **928 of 16,909 inserted lines — 5.5%** (M2), while `docs/` grew 13% and
`plans/` grew **44%** (M3). Both halves are true simultaneously: individual findings genuinely
closed, *and* the corpus grew 7,424 lines net. **A count of commits is not offered** — a commit
tally varies with how finely a session slices its work, and a path-filtered `git log` returns a
different number again through history simplification.

**A third reading, which neither option below states.** The ratio may be measuring **queue position,
not process appetite.** Across that window the code work was decided-but-unstarted and the document
work was unblocked, and agents write what is available to write. If that is what happened, freezing
the register layer does not cause S1 to be built — only building S1 does — and the ratio corrects
itself when § 3 rows 4-9 land. This reading argues that **§ 3 is sufficient and § 4 is unnecessary**.
It is not offered as a fourth option because it is an argument about whether to decide at all, and
because it is not free of assumption either: it predicts the ratio falls once the queue drains, which
nobody has tested.

**Conflict of interest, stated because the recommendation is not neutral.** Option A validates the
measurement its author spent the morning producing, and the author said so when handing the draft
over. That does not make A wrong — it is genuinely the only zero-cost reversible option — but the
user should weigh it knowing the recommender benefits from its adoption.

### The options

| | **A · Freeze the register layer** | **B · Freeze nothing** | **C · Actively consolidate** |
|---|---|---|---|
| **What it means** | No new register, no new rule in `CLAUDE.md`, no new gate that is not closing a defect that already shipped — until § 3 rows 4–9 are done | Carry on; judge each addition on its merits as now | Collapse the four queues into one as a scheduled piece of work |
| **For** | Costs nothing, reversible in a sentence, and directly targets the measured ratio. Leaves every existing gate running | Nothing is refused on a rule rather than on merit. The newest process — `RELEASING.md` step 3 — caught a stale FX rate that had shipped in a wheel for a month | Attacks the actual cause of the disorientation, which the repo has already diagnosed precisely |
| **Against** | A freeze is blunt: it would have refused step 3, which paid for itself. Needs an explicit carve-out for a gate closing a shipped defect | Is the status quo, and the status quo produced the ratio. Nothing changes | More writing, into the corpus that is already up 44%. **The last attempt produced a fifth register rather than one.** Spends a week on the map while the territory is stalled |
| **Cost** | zero | zero | ~1 week, planner |
| **Reversible** | yes, immediately | n/a | no |

### Recommendation — **A, with the carve-out written into the rule**

**Recommended because it is the only option that changes the measured ratio at zero cost and can be
lifted in one sentence.** The carve-out is what makes it survivable: *a gate that closes a defect
which already shipped is not new process.* Step 3 would have passed that test — it was written
because a stale rate shipped. ENG-1 passes it too, which is why § 3 rows it rather than deferring it.

**C is not recommended now**, and the reason is evidential rather than aesthetic: the diagnosis is
already written down in several places, and acting on it while the engine is stalled means the map
grows again. It becomes the right answer once § 3 rows 4–9 are empty.

**B is a legitimate answer** and would be the right one if the ratio were an artifact of a single
unusual week. It is not offered as a strawman: three days of that window were silent, so the ratio
is measured over five working days, and one week is a thin base for a standing rule.

**The exit condition, so the freeze cannot become permanent by inattention:** it lifts when § 3
rows 4–9 have landed. That is a checkable state, not a date.

---

## 5. What comes after — and why it is not scheduled here

**Dogfooding is the highest-yield activity this repository has on record, and it cannot be
scheduled by an agent.** Every user-facing defect in § 3 came from one sweep of *running* Pinakes on
20260825. Two of the three gated futures need the same input to fire: T6 wants "a KB that is
actually queried" past ~50,000 chunks with felt latency, and the dogfooding KB `pinakes-kb` has one
commit, dated 20260804, untouched since.

**It is the user's material, so the user is the trigger.** It is named here so that an empty build
order is not misread — [`docs/README.md`](../docs/README.md) already warns that an empty list means
*the next thing to build has not been planned yet*, never *nothing to do*.

**One honest note about the gated futures, because it changes what re-measuring is worth:** the G5
re-run will not revive the graph channel. PPR's own gate requires a channel shipping default-on, and
the plan predicts another null in advance — so a null re-run leaves PPR exactly where it is.
Reviving it needs a different mechanism or corpus, not another measurement. The re-run is still
worth doing if the goal is to retire the question honestly; it is not worth doing if the goal is to
unblock the graph work.

---

## 6. Also owed by the user, and not by anyone here

Listed for completeness; none blocks § 3.

| Decision | State |
|---|---|
| The `CLAUDE.md` extraction (`475b452`) | Pushed, unmerged, marked *do not land without the user*. **Measured 20260901 12:35 UTC: `main` is 114 commits ahead, and `git merge-tree` reports a real content conflict in `CLAUDE.md`** (`docs/README.md` merges clean). A rebase is not optional and not mechanical — the conflict is the status block the proposal deletes, which `main` has since rewritten |
| ~~`pnk adopt` — which release owns it, or drop it~~ **REASSIGNED TO PLANNER 20260902 07:41** | **Corrected 20260901 12:35 UTC: it *does* appear in a top-level routing document** — [`docs/README.md:29`](../docs/README.md) names it, correctly, as part of what "is still a proposal". The earlier claim that it appears in none was wrong. **This row was misfiled and sat here 29 days for no reason.** The decision's own founding sentence ([`plans/20260804_1016-template-release.md:523`](20260804_1016-template-release.md)) reads *"Flagged so the planner can either drop the APPROACH row or add the work"* — it names the planner, and the same file's line 304 puts D-8 among *"recommendations the planner may still overrule"*, in contrast to D-9 beside it which does say *"it is the user's"*. Both actions it names are edits to `docs/**`, which the ownership table already makes planner-only. What is true: no release owns it, and it is unimplemented — `grep -rn '"adopt"' src/` returns 0 where the same selector returns `cli.py:1799` for `"upgrade"` |
| ~~The `fable` clause in the user's global `~/.claude/CLAUDE.md`~~ | **CLOSED — verified present 20260901 12:35 UTC**, `~/.claude/CLAUDE.md:42`: *"nothing reaches Fable either, which bills at 2x Opus"*. It was reported done and the report was right; this row existed because nobody had opened the file |
| ~~`--autocompact 150000`~~ **STRUCK 20260902 07:41 — not a decision** | **Unverifiable from this repo**, and the flag does not exist under that name. One mention in `RESUME.md`, no plan, no commit. The live setting is `autoCompactWindow` in `~/.claude/settings.json` and reads **300000** — measured 20260901 12:35 UTC, twice the number this row is named for. Whatever decision this row records, it is not about a value anything currently reads. **So it is not the user's and not anyone's: there is nothing to decide.** Kept struck rather than deleted so the row is not re-derived from the same absent source a third time |

---

## 7. What this plan does not claim

- **It does not claim § 3's order is the only correct one.** Rows 4–9 could be built in any order;
  what is argued is that they precede rows 10–12, and that row 9 belongs with rows 4–5 rather than
  below them.
- **It does not restate the sweep plan's evidence.** Where this file and that one disagree about a
  row's state, **the sweep plan wins** — it carries the dated measurement and this file carries a
  summary of it.
- **It adds no finding except ENG-1.** Everything else here has an owner already.
- **Its own status claims decay.** Every row states where to check rather than asking to be
  believed; a register that is read is the one that stays true.
