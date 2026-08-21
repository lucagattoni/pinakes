- **Every constant that prices `pnk ask --deep` now carries its measurement, and none was
  lowered.** E6's measurement run, against the live API on synthetic corpora: `PROMPT_TOKENS`
  1,500 against 376 measured (3.99×), `QUESTION_TOKENS` 1,000 against 399 (2.51×),
  `PASSAGE_ENVELOPE_TOKENS` 250 against 28 (8.93×), `VENDOR_TOKENS_PER_CHUNK_TOKEN` 3 against 2
  (1.50×), `CARRIED_MEMORY_TOKENS` 4,000 against 1,612 (2.48×), and `MAX_TOKENS` 8,000 against a
  widest-observed 660 (12.12×). **Whole-run over-reservation, per branch: 29.75× on the cheap
  synthesis branch, 50.92× on the calibrated loop, 22.35× on the uncalibrated one** — against the
  paid extractor's 11.5×. `MAX_TOKENS` carries most of it, because output bills at five times
  input and is two thirds of a round's price. **A ceiling is never lowered to a measurement taken
  on synthetic data**, and `max_tokens` is the one where that refusal matters most: it truncates
  rather than bills, so a ceiling near the observed mean would cut a long answer off mid-sentence.
