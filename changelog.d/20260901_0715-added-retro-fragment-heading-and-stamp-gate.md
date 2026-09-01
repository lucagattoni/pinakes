- **`tools/fragments.py --check` refuses a `retro.d/` fragment that carries no `##` heading of its
  own, or whose heading's `(YYYYMMDD HH:MM)` is not the filename's own prefix.** A headingless
  fragment was not malformed once spliced — it was *absorbed*, landing under whichever fragment
  sorted before it and reading as that incident's lesson, in a document that stayed correct
  markdown while every gate stayed green. The stamp arm holds the existing rule that the heading's
  time is a **copy** of the filename's, never a second reading of the clock. Fragments predating
  the naming rule have no prefix to copy and owe the heading only; `changelog.d/` is untouched.
