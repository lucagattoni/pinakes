- **A damaged template install is a message, never a traceback.** Every read of a template's own
  files was unguarded, so an incomplete or third-party install raised something that is not a
  `PinakesError` and the CLI printed a stack trace: a `_versions/<v>/` without its
  `pinakes.toml.j2` gave `FileNotFoundError`, an unreadable file `PermissionError`, a non-UTF-8 one
  `UnicodeDecodeError`, a malformed `template.toml` a `tomllib.TOMLDecodeError`, and an unclosed
  `{{` a `jinja2.TemplateSyntaxError` — which `_render` never saw, because it is raised by
  `Template(...)` rather than by `render`. All five now name the template, the version and the file.
  The correction covers `describe`, `declared_files`, `render_manifest`, `render_archived` and
  `copy_extras`: the record named the first two, and shipping those alone would have left the same
  defect three functions away.
- **`pnk doctor` and `pnk upgrade` no longer call a damaged template an uninstalled one.** Both
  answered any failure to read one with *"is not installed here"* and a remedy about installing it
  — correct while the only thing reaching that handler was a template genuinely absent, and wrong
  the moment guarding the reads above routed a *damaged* one into it, since it sends the owner to
  install what is already there. `TemplateNotInstalledError` separates the two, and each command
  now reports an unreadable template as unreadable and names the file.
- **A template read error no longer prints where pinakes is installed.** `OSError.__str__` appends
  the filename it carries, so a read failure with no `strerror` put an absolute path into the text
  `pnk doctor` forwards — the command whose output is the natural thing to paste into an issue.
  Its existing de-homing cannot cover this: that strips the *KB* root, and a template lives outside
  the KB by construction.
