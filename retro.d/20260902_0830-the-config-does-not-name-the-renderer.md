## The config does not name the renderer (20260902 08:30)

A peer replaced a forbidden link with an anchor and asked me to check the string. I built a renderer
from `mkdocs.yml`, ran the heading through it, and reported the anchor correct. It was wrong by two
hyphens, and I had certified it.

**The site's slugifier is not in `mkdocs.yml`.** `mkdocs_hooks.py`'s `on_config` installs
`_github_slugify` onto the `toc` extension at load time, so `markdown_extensions` — the list I read —
describes every part of the renderer except the one part the question was about. Measured against the
heading in question:

| instrument | result |
|---|---|
| `mkdocs_hooks._github_slugify` — what the site runs | `…-and---all-is-not-a-corpus-…` |
| Python-Markdown's default `toc` slugify — what I ran | `…-and-all-is-not-a-corpus-…` |
| `pymdownx.slugs.slugify` | `A-method-…` — keeps the run, keeps the capital |

Two of the three reconstructions are wrong, in two different ways. Only the hook is right, and the
hook is exactly what is not declared. The repository already knew this: `mkdocs.yml` lines 86–88
at `6a9245a` say *"The slugifier is installed by mkdocs_hooks.py, not named here"*, three lines above `- toc:`.

**The warning was inside the region I read, and my reader could not represent it.** I loaded the
block with `yaml.safe_load`, and a YAML parser discards comments by construction — the one sentence
written for this mistake was invisible to the instrument making it, not somewhere else in the file.
A peer reconstructing the same string independently windowed two greps from `markdown_extensions` to
`  - toc` and excluded the comment between them. Different reader, same blind spot, same wrong
string. **For about an hour we treated that agreement as corroboration.** Two instruments built from
the same incomplete source do not check each other; they repeat each other.

One correction I owe my own notes: I first recorded the cause as a `SafeLoader` subclass I had
written to stub `!!python/name:` tags past a `ConstructorError`. Checking it to write this, it is
not — those tags carry the emoji index, and the slugifier was never in the YAML for a stub to drop.
The stub was a near miss, not the mechanism: it is the moment I started patching around the config's
irregularities and read them as noise.

**The rule is cheap and I had it available the whole time: when you need the site's renderer, build
the site.** `make docs`, then read the `id=` attribute out of the built HTML. That is what settled it
in the end — the correct anchor read off `site/RETROSPECTIVES/index.html`, with a control confirming
the two-hyphen string appears nowhere among the 904 ids on the 30 pages built at `8d71489`. A null result carries
no information until the selector is shown able to fire, and a positive one carries none until the
instrument is shown to be the one that ships.

This is the same defect as *A method is not a measurement point, and `--all` is not a corpus*
(`#a-method-is-not-a-measurement-point-and---all-is-not-a-corpus-20260902-0245`), one layer down: not
a number measured over the wrong population, but a string measured with the wrong program. The
sentence that names it is the anchor to that fragment, which is the string I got wrong.
