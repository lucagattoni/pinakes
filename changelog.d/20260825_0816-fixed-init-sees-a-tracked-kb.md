- **`pnk init` now reports a `.pinakes/` that git is already **tracking**, a state the ignore check
  was structurally unable to see.** `git check-ignore` consults the index, so it answers *not
  ignored* for a tracked path — and the detector's probes are **opaque random tokens**, which by
  construction no pattern targets and nothing ever adds to the index. So the check could answer
  only *"would a new file here be ignored?"*, never *"is anything in there tracked right now?"*
  The two come apart in the case that costs the most: a KB committed before its ignore rule existed
  reads as **protected** from the moment the rule is added, while every `git commit -a` keeps
  republishing `.pinakes/deep/`, which holds the user's **verbatim questions**. Reproduced end to
  end — a correct `.gitignore` over three committed files, and `init` printed nothing. The fix is a
  second *question*, not a different probe: `git ls-files` over the index, reported as its own
  state with its own remedy, because an ignore rule governs files git has not seen and a tracked
  file is already past it. **The remedy's order is load-bearing and is stated rather than implied**
  — where no rule is in place the line must be added *before* `git rm -r --cached .pinakes`, since
  measured, the reverse puts the files straight back on the user's next `git add`. The printed text
  says the removal is from git's index and not from disk (verified by running it — the files stay
  readable), and claims nothing about commits already pushed.
