## E6 — A seam the tests never crossed (20260812 06:41)

**CRITICAL — `pnk ask --deep` has never worked against the live API, and 0.22.0 through 0.25.0 all
ship it.** The first real `--deep` call E6 made returned a 400 before it billed anything:

    output_config.format.schema: For 'integer' type, properties maximum, minimum are not supported

`deep/client.py: answer_schema` emits `{"type": "integer", "minimum": 1, "maximum": passages}` on
every answer call, and structured outputs does not accept numerical constraints. A second probe
found `subproblems_schema`'s `maxItems` is refused the same way, so the decompose call was broken
too — fixing the answer call alone would not have produced a working loop.

**The lesson is about the seam, not the schema.** E3 introduced `Transport` so the whole loop could
be driven from recorded fixtures with `anthropic` absent, and E4 and E5 were both tested that way,
green throughout. That is a good seam and it bought real things. What it also did was guarantee that
**no test in the suite has ever sent a schema to the API** — the one field the API validates and the
fixtures cannot. A fixture asserts what we believe a response looks like; it cannot assert that the
request was acceptable. Every layer above the seam was correct, which is exactly why nothing went
red: the defect lived in the only inch of the path the seam removes.

The generalisation: **a seam introduced for testability defines a region the tests cannot reach, and
that region needs its own gate.** For this one the gate is cheap and fixture-free — assert the two
schema builders emit no keyword on structured outputs' documented unsupported list. It would have
failed at E4, on a branch that was green.

**Three things behaved exactly as designed and are worth recording, because a bad failure is where
you find out.** The accountant reserved, refused and voided: the failed call billed €0.0000, so a
run of 400s cannot consume a budget. The error surfaced the API's own sentence rather than a
paraphrase, which is what made the cause obvious in one read. And the blast radius was genuinely
bounded to the one path — `pnk search`, `pnk ask` without `--deep`, and the paid extractor were all
untouched, because none of them shares this client.

**Running the instrument found two bugs in the instrument.** `tools/deep_reservation.py count`
filtered its token-count payload to `model`/`system`/`messages`, dropping `output_config` — so it
measured `PROMPT_TOKENS` with the schema excluded, a fraction of the real figure. And
`QUESTION_TOKENS` differenced an arbitrary 200-word probe, so it returned ~200 by construction: it
measured the probe, not the question ceiling. Both would have published a wrong constant with no
symptom. **A measurement probe is code and earns the same adversarial pass as anything else** — two
of five constants were measured wrong on the first run, and reading the script is what found
neither; running it is.
