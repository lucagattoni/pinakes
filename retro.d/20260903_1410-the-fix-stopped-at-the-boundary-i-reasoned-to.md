## The fix stopped at the boundary I reasoned to, not the one the defect had (20260903 14:10)

**What happened.** The crash arrived from `pnk sync`, so I scoped the fix to the source walk in
`sync.py` and argued the scope was right: that is where a corpus path gets stat-ed, and the other
41 `is_file()`/`exists()` calls in `src/` are about paths Pinakes itself created under `.pinakes/`.
The argument was sound. The scope was wrong. My own adversarial pass found `doctor.py` failing on
the same state, `linkscan.py` returning a wrong answer on it, and — worst of the three — an orphan
check that offered `--prune` for a document sitting on disk, which would have destroyed a permanent
ULID. None of that was visible from where the crash was reported.

**Why.** I derived the boundary from the *symptom's* call path instead of enumerating the
*condition's* reach. The condition is "a corpus path this process cannot stat", and the way to find
its reach is to list every place a corpus path is stat-ed and ask each one what it does with False.
That is a grep and a read, not a deduction — and it is cheaper than the deduction was. Reasoning
from one entry point produces a boundary shaped like the entry point.

**What it cost, and what it nearly cost.** Three commits instead of one, which is nothing. But the
`--prune` bug is interpreter-independent and predates this branch: it was reachable on every
supported Python, and a fix that had stopped where my reasoning stopped would have shipped a
version-independence claim while leaving a data-destroying prompt in place one file away. The
review found it; the reasoning had excluded the file it was in.

**The rule.** When a fix is for a *condition* rather than a line, establish the scope by
enumeration and say so — `grep` the predicate, read each site, record what each does when the
answer is False. Then state the boundary as a set you looked at, not as a category you inferred.
A category is a claim about files you did not open.

**And check what False means at each site before reusing the helper.** Two of the four sites wanted
the new version-independent `is_regular_file`; the orphan check wanted `os.path.lexists`, because
there False means *nothing is here* and it had been reading it as *nothing readable is here*. A
shared helper makes a class of bug go away and a class of bug easy to write: the sites that must
distinguish *absent* from *unreachable* are exactly the ones a sweep will quietly get wrong.
