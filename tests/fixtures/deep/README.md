# Deep-loop response fixtures

One file per branch `deep/client.py` can take. Each is a *script*: the responses (and transport
failures) one call sequence receives, in order. `tests/test_deep_client.py` replays them through the
`Transport` seam, so every branch — every reservation, every ledger pair, every refusal — is
exercised with `anthropic` not installed at all.

The format is `tests/fixtures/claude/README.md`'s, deliberately unchanged: same `name` / `branch` /
`why` / `provenance` / `responses` shape, same `kind: "error"` replay entries. Two fixture sets with
two formats would be two replayers.

## Every body here is **authored**, and that is a statement about the whole set

**Nothing on this path has been called for real yet.** E6 is the increment that spends, under
[`docs/MEASUREMENT-RUN.md`](../../../docs/MEASUREMENT-RUN.md), and it is the one that may replace
these with recordings — the extractor's set went the same way, and recording it corrected the
authored bodies in five ways no passing test could have revealed
([`../claude/README.md`](../claude/README.md)).

So each file's `provenance.why_not_recorded` says why *that* body cannot be recorded today, and the
honest reading of the set is narrow: **an authored body proves the branch exists, is reachable, and
does what the plan says when it is reached.** It proves nothing about what the API returns.

Two of them would stay authored even after E6, for the reason the extractor's equivalents did:

| File | Why a recording is not obtainable, ever |
|---|---|
| `answer-citing-a-passage-it-never-saw` | The model disobeying a `maximum` its own request declared. It cannot be asked for — and the check it drives is what stops invented evidence being printed with a citation beside it |
| `decompose-over-cap` | Likewise for `maxItems`: the second check exists precisely because the first one is the API's, not ours |

**The two injection fixtures are the ones worth reading twice**, because each is what a
*successful* prompt injection looks like on the wire — which in both cases is nothing much.

| File | What a steered model actually produced | Why that is all it could produce |
|---|---|---|
| `injected-subproblem` (E4) | A badly chosen search question | The decomposition schema has one field and that field is an array of plain strings. There is no property in it for a path, a filter or a KB selector, so a steered model has nowhere to put one |
| `answer-obeying-an-injected-link-instruction` (E7) | A sentence saying a `links` entry should be added | `deep/suggest.py` derives suggestions from *citations*, and a citation is a passage number the response schema bounds. Nothing reads the answer's prose, so obeying the instruction reaches no further than saying so |

No real knowledge-base content appears here, and none ever will: this repository is public
(`CLAUDE.md`), and every question and passage in these bodies was written for the purpose.

## Format

```json
{
  "name": "…", "branch": "…", "why": "…",
  "provenance": {"kind": "authored", "why_not_recorded": "…"},
  "responses": [
    {"kind": "response", "stop_reason": "end_turn", "model": "…", "content": [ … ], "usage": { … }},
    {"kind": "error", "class": "status", "status": 429},
    {"kind": "error", "class": "timeout"}
  ]
}
```

A recorded fixture carries `{"kind": "recorded", "at": "YYYYMMDD HH:MM", "model": "…",
"source": "…"}` instead — `at` in UTC, read off the clock and never composed.

A script that runs out of entries is a test bug, and the replayer says so rather than returning
something plausible.
