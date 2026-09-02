## The gate I ran was not the gate CI runs, and the gap is where the defect was (20260902 10:26)

`./check.sh` exited **0** on the release branch. `main` went **red** on the same tree.

Not a flake, and not a different commit. My local run skipped **128 tests** because this machine has
neither the `[pdf]` nor the `[claude]` extra installed, and CI's `check` job is a three-leg matrix
over `[light]`, `[light,pdf]` and `[light,pdf,claude]`. The failure was in
`tests/test_pdf_trace.py` — inside the skipped set, by construction.

**The defect it found was real and had been dormant for a month.**
`estimate.per_request_eur` computes `(input_usd/r + output_usd/r) / requests`;
`reservation.cost_eur` computes `(input_usd + output_usd) / r`. A test asserts the two are
**equal**. They are not the same expression, and in 28-digit `Decimal` they need not agree:

| rate | `(a/r)+(b/r)` | `(a+b)/r` | equal |
|---|---|---|---|
| `1.1596` (seeded) | `0.3048464987926871334943083822` | same | **yes** |
| `1.159` (2026-09-01 ECB) | `…5452976` | `…5452977` | **no** |

So the assertion had never held *by construction*. It held because one constant happened to make two
different routes round to the same 28th digit. Refreshing that constant — a step `docs/RELEASING.md`
requires at every release — is what falsified it.

**Three things follow, and only the first is about me.**

**A skip is not a pass, and a green local gate is a claim about the legs that ran.** `./check.sh`
prints its skip count; I read the exit status and not the count. The honest form of "green locally"
is "green on the one leg my machine can run".

**A test whose truth depends on an unmentioned constant is not pinned to what it claims.** Nothing in
`test_pdf_trace.py` names `usd_per_eur`, so nothing warned that changing it could break the
assertion — and nothing warns now that a future refresh could make it pass again for the same bad
reason. A second rate in the test is what turns a coincidence into a pin.

**The order of discovery is worth keeping.** The artifact was verified — installed from the index,
wheel opened, subject found inside it — *before* CI went red. **A verified artifact and a green
`main` are two claims**, and it is possible, as here, to have only the first. Neither substitutes
for the other, and a release note that reports one as though it were both is the error this record
exists to prevent.
