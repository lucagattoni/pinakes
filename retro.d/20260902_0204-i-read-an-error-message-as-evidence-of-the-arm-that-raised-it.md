## I read an error message as evidence of the arm that raised it (20260902 02:04)

I ruled that closing a hole in a fragment gate was not new process, because *"the sibling stream
already gates this"*. The evidence was three filenames through `changelog.d`: the canonical one
passed, a typo'd prefix and a prefix-less one were both refused, and the refusal said **"filename
must be `YYYYMMDD_HHMM-<category>-<slug>.md`"**. Prefix gate, plainly.

There is no prefix gate. It is a **category** gate, and one more fixture separates them:
`fixed-a-thing.md` — no prefix at all, but its head *is* a category — is **accepted**, while
`banana-a-thing.md` is refused. A malformed prefix is refused there only *incidentally*, by shifting
the first hyphen-separated token out of the six allowed categories. The message names the whole
convention because the convention is what the author wanted the reader to go and read; it is not a
statement about which arm fired.

**Two refusals confirmed a mechanism that one more row would have falsified**, and the missing row
was cheap and obvious in hindsight: hold "prefix-less" fixed and vary only whether the head is a
category. I varied two things at once in every fixture I wrote, so no comparison in the set could
isolate either.

I have a rule that a null result proves nothing until the selector is shown able to fire, and I
applied it that same hour to someone else's work. **This is its mirror and I did not recognise it: a
refusal proves nothing about *which* arm refused.** A firing selector and a firing gate are the same
problem — output that is consistent with the hypothesis is not evidence for it unless something in
the set could have come out the other way.

The peer who found it did the thing I had not: constructed the case where the two hypotheses
disagree, rather than adding another case where they agree.

**And a second slip in the same edit, from the same family.** I wrote `20260902 00:35` into three
places, composed from my previous clock read rather than taken from the clock. The machine had slept
about ninety minutes; the real time was `02:04`. Every stamp I write carries a rule saying read the
clock, never compose it — and the failure mode is not forgetting the rule, it is *believing you
already know the answer* well enough not to check. Which is exactly what the error message did to me
one paragraph up.

**The rule.** When output is consistent with what you expect, ask what the *other* hypothesis would
have produced, and go and build that case. If nothing in your fixture set could have come out the
other way, you have collected agreement, not evidence.
