- **`docs/STATUS.md`'s headline can no longer claim a hold that is over, or hide one that is not.**
  `pinakes.__version__` means *landed on `main`*, so there is a legitimate window in which line 3
  names a version `pip install` cannot get — on a page published on every push. The gate now reads
  `R`, the newest entry of that file's *Published versions* row: `line3 > R` **requires** the hold
  marker, `line3 == R` **forbids** it, `line3 < R` is always red, and a row it cannot read is a
  hard failure rather than a skip. The marker is a parsed shape whose qualifier must name `R` —
  the version `pip install` actually gets — because a qualifier is a claim about the index and an
  unchecked claim about the index is how line 3 came to need a gate.
- **The half that could never have been caught otherwise is the *removal*.** A marker left behind
  after a successful publish was green in every check this repository has: the header gate's shape
  stops at the closing `**`, none of the release-order gate's seven sequences reads line 3's tail,
  and an index-based rule can only fire on a version that is *absent*. It would have stood
  indefinitely with every gate passing.
