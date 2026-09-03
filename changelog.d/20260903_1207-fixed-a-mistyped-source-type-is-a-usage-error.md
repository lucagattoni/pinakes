- **A mistyped `--source-type` is refused instead of quietly matching nothing.** `pnk search
  --source-type markdwon` used to run the whole query, match no rows, print *"no passages
  matched."* and exit 0 — a typo and an honestly empty result were the same output, so the user's
  next move was to doubt the KB rather than the flag. The set of source types is closed, not a
  convention: `SOURCE_TYPES` in `pinakes.chunk` names every value `source_type()` can return, and a
  value outside it provably cannot match a row in any KB, before the query runs. So it is now an
  argparse error, exit 2, naming the four that work. `--source-type pdf` on a KB with no PDFs still
  returns nothing and still exits 0 — that answer is true.
