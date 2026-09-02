## The gate I ran was not the gate CI runs, and the gap is where the defect was (20260902 10:26)

`./check.sh` exited **0** on the release branch. `main` went **red** on the same tree.

Not a flake, and not a different commit. My local run skipped **128 tests** because this machine has
neither the `[pdf]` nor the `[claude]` extra installed, and CI's `check` job is a three-leg matrix
over `[light]`, `[light,pdf]` and `[light,pdf,claude]`. The failure was in
`tests/test_pdf_trace.py` — inside the skipped set, by construction.

**The defect it found was real and had been dormant for a month.** A test asserts
`reservation.cost_eur == estimate.per_request_eur`, and that comparison **straddles the ledger's
write-time quantisation**: `accountant.py:193` multiplies the EUR estimate back by the rate,
`ledger.py:139` quantises on write at `1e-6` `ROUND_HALF_UP`, `ledger.py:127` divides back on read.

| rate | `per_request_eur × r` | quantised | read back | equal |
|---|---|---|---|---|
| `1.1596` (seeded) | `0.3535000000000000000000000000` | no-op | `…3083822` | **yes** |
| `1.08` (the original seed) | `0.3535000000000000000000000000` | no-op | `…8148148` | **yes** |
| `1.159` (2026-09-01 ECB) | `0.3534999999999999999999999999` — one short | snaps **up** | `…5452977` | **no** |

So the assertion had never held *by construction*. It held because two successive rates happened to
make the round trip land exactly on the quantum. Refreshing that constant — a step
`docs/RELEASING.md` requires at every release — is what falsified it.

**And I published a different mechanism before checking this one.** I read
`cost_eur = cost_usd / usd_per_eur`, assumed `cost_usd` was the summed USD, and wrote up an
arithmetic-ordering story — `(a/r)+(b/r)` against `(a+b)/r` — in three documents and a commit
message. It is a coherent account that predicts the observed digits, which is exactly why it
survived my own reading. A peer reproduced the real route and refuted it. The fix I recommended on
the strength of it would have removed the `…9999` from *this fixture* and left the assertion false
for 66% of a 40 000-case sweep; restricted to `requests == 1` it does hold, which is the trap,
because the fixture is `requests == 1` and so is any sweep someone writes to check it.

**The rule I am taking from that: an explanation that fits the numbers is a hypothesis, and the
discriminating step is reading the code path that produces them, not the code path that would.**

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
