- **`-k` below 1 is refused, on both `pnk search` and `pnk ask`.** It was `type=int` and nothing
  else, so the value travelled to whatever the command reached: `search` used it as a raw Python
  negative-slice bound and answered *confidently and wrongly* — `-k -1` returned every passage but
  the last at exit 0, `-k -100` returned none and called it *"no passages matched."* — while `ask`
  reached the deep estimator, which rejected it as an unhandled `ValueError` traceback. One missing
  check, one surface answering wrongly and one crashing. Now a usage error (exit 2) at the parser.
  **`-k 0` is refused too, and that is a deliberate behaviour change**: the width was read as
  `limit or manifest.retrieval.final_k`, so a falsy `0` silently meant *use the default* — asking
  for nothing and receiving ten passages. Anything scripted against `-k 0` now gets an error where
  it used to get default-`k` results.
