"""Rendering a manifest: what a user's own text may contain, and still round-trip (S4).

`_render` interpolates into TOML. Every variable this build supplies lands inside a basic string
except `embedding_dim`, so a value carrying a `"` or a `\\` used to close or escape that string and
write a `pinakes.toml` no parser could read — while `pnk init` exited 0 and printed *created*.
The KB was bricked at the moment of creation and there was no repair: `pnk init` refuses a directory
that is already a KB, so the remedy surface was empty and recovery meant hand-editing TOML.

**These tests are about the mechanism, not about `--name`.** The fix is a `finalize` hook on the
Jinja template, so the property under test is *every interpolated value is either made safe or
refused*, and the tests that matter most are the ones that would still pass if someone re-broke
`--name` alone: the controls at the bottom of this file.

**"Or refused" is not a hedge — it is a class the first pass of this file missed.** A lone
surrogate has no TOML representation raw or escaped, so there is nothing for an escaper to
produce; it used to reach `Path.write_text` and leave a zero-byte manifest behind. Escaping is
what most values need. Some need a message.
"""

import tomllib
from pathlib import Path

import pytest

from pinakes import template
from pinakes.errors import TemplateError
from pinakes.init import init
from pinakes.manifest import load

#: The three classes S4 named — `"`, `\`, and control characters other than tab — opened out into
#: eleven values. The eight control characters are four with a single-letter TOML escape (`\n`,
#: `\r`, `\b`, `\f`) and four with none, which must take `\uXXXX`, so both arms of the escaper are
#: exercised. `backslash` is the verifier's widening (a Windows-style path is far likelier than a
#: quoted name) and `both at once` is the pair. A `str` here is a *user's KB name*: it reaches
#: `render_manifest` through `pnk init --name`, and through `root.name` when no flag is passed.
CLASSES: dict[str, str] = {
    "double quote": 'Bob\'s "Special" KB',
    "backslash": r"C:\notes\kb",
    "both at once": r'C:\a"b\\c',
    "newline": "two\nlines",
    "carriage return": "a\rb",
    "nul": "a\x00b",
    "bell": "a\x07b",
    "backspace": "a\x08b",
    "form feed": "a\x0cb",
    "unit separator": "a\x1fb",
    "delete": "a\x7fb",
}


def _context(**overrides: object) -> dict[str, object]:
    """A context covering `CONTEXT_KEYS`, so a render exercises the template itself.

    A bare `{"name": ...}` would raise `UndefinedError` on the second variable, which is a
    different test — the one at the bottom of this file.
    """
    context: dict[str, object] = dict.fromkeys(template.CONTEXT_KEYS, "x")
    context["embedding_dim"] = 384
    context.update(overrides)
    return context


@pytest.mark.parametrize("value", CLASSES.values(), ids=list(CLASSES))
def test_a_name_in_any_class_the_sweep_named_renders_a_manifest_that_parses(value: str) -> None:
    """The headline: the rendered file is TOML, and the name survives it unchanged.

    Parsing and round-tripping are asserted together deliberately. Escaping that produced valid
    TOML holding the *wrong* name would satisfy either one alone, and it is the shape an
    over-eager escape function actually fails in — `\\\\` written where `\\` was meant reads as
    correct until someone compares the value.
    """
    rendered = template.render_manifest("notes", _context(name=value))

    assert tomllib.loads(rendered)["kb"]["name"] == value


@pytest.mark.parametrize("value", CLASSES.values(), ids=list(CLASSES))
def test_init_writes_a_kb_that_load_can_open_whatever_the_name_holds(
    tmp_path: Path, value: str
) -> None:
    """End to end, because the unit above cannot see the write.

    `load` is the gate every other command goes through, so a KB it can open is a KB that is not
    bricked. This is the assertion that fails on `main` before the fix — with a `TOMLDecodeError`
    out of `load`, not with a wrong value.
    """
    result = init(tmp_path / "kb", name=value, now="20260902 11:29")

    assert load(result.root).kb.name == value


def test_a_tab_is_left_raw_rather_than_escaped(tmp_path: Path) -> None:
    """The one control character a basic string may carry, and why S4 names three classes not four.

    An earlier reading of S4 counted four and included tab. TOML allows it raw, so escaping
    it would rewrite a legal byte — and a test that merely round-tripped would not notice, because
    `\\t` round-trips too. This asserts the *byte on disk*, which is the only thing that can tell
    the two apart.
    """
    result = init(tmp_path / "kb", name="a\tb", now="20260902 11:29")

    written = (result.root / "pinakes.toml").read_text(encoding="utf-8")
    assert 'name     = "a\tb"' in written
    assert "\\t" not in written
    assert load(result.root).kb.name == "a\tb"


def test_a_backslash_path_that_stays_valid_toml_still_reads_back_unchanged() -> None:
    """The case where the manifest parses and means something else — found by the mutation pass.

    Every value in `CLASSES` carrying a backslash carries one TOML *rejects* too:
    `C:\\notes\\kb` holds `\\k`, which is not a legal escape, so dropping the backslash arm of
    `_TOML_ESCAPES` makes `tomllib` refuse the file. That is loud, and the tests above catch it
    by parsing alone.

    `C:\\notes` is the quiet one. Its only backslash sequence is `\\n`, which **is** legal — so
    without escaping it parses cleanly and reads back as `C:`, a newline, and `otes`. `pnk doctor`
    would call that KB healthy under a name nobody typed. Nothing in this file reached that case
    until the battery's *a backslash is left raw* row died on a `TOMLDecodeError` instead of on
    an equality — the same
    mutant passing for the wrong reason.
    """
    value = "C:\\notes"

    rendered = template.render_manifest("notes", _context(name=value))

    assert tomllib.loads(rendered)["kb"]["name"] == value


def test_an_ordinary_name_is_left_byte_for_byte_alone() -> None:
    """The control against over-escaping: a name with nothing to escape is not rewritten.

    Without this, an escape function that quoted every character would pass every round-trip test
    in this file — `tomllib` would unescape it back — while making every manifest on disk
    unreadable to the human who has to edit it.
    """
    rendered = template.render_manifest("notes", _context(name="research notes"))

    assert 'name     = "research notes"' in rendered


def test_the_embedding_dimension_stays_a_bare_integer() -> None:
    """The only variable interpolated *outside* a quoted string — why `finalize` tests type.

    `dim = {{ embedding_dim }}` has no string to be safe inside. An escape hook that stringified
    what it touched would write `dim = "384"`, which parses as TOML and then fails `manifest.load`
    much later, in a command that has nothing to do with `init`.
    """
    rendered = template.render_manifest("notes", _context(name="kb"))

    assert "dim      = 384" in rendered
    assert tomllib.loads(rendered)["embedding"]["dim"] == 384


def test_the_directory_name_reaches_the_same_escaping_with_no_flag_at_all(tmp_path: Path) -> None:
    """`--name` is not the surface; it is one of two ways in.

    `init` falls back to `root.name`, so a directory a user created with a quote in its name
    reaches the identical path. A fix guarded at the flag would leave this one open, and it is the
    half nobody would think to type.
    """
    awkward = tmp_path / 'a"b'
    result = init(awkward, now="20260902 11:29")

    assert load(result.root).kb.name == 'a"b'


def test_every_context_variable_is_escaped_not_only_the_name() -> None:
    """The mechanism claim, stated as a test.

    The fix is a `finalize` hook, so it covers every `{{ ... }}` rather than one variable. Nothing
    in this build routes user text into `rerank_model`, which is exactly why this test exists: it
    pins the property that makes the *next* variable safe without anyone remembering to escape it.
    """
    rendered = template.render_manifest("notes", _context(name="kb", rerank_model='a"b'))

    assert tomllib.loads(rendered)["rerank"]["model"] == 'a"b'


def test_both_sides_of_an_upgrade_diff_escape_identically() -> None:
    """`pnk upgrade` renders the recorded version and the installed one and diffs them.

    Escaping on one side only would put a `[kb] name` hunk in every report for every KB whose name
    contains a quote — and under the all-or-nothing conflict rule that makes `--apply` refuse.
    Both go through `_render`, and this is what says so.
    """
    context = _context(name='a"b')

    installed = template.render_manifest("notes", context)
    archived = template.render_archived("notes", "1.2", context)

    assert 'name     = "a\\"b"' in installed
    assert 'name     = "a\\"b"' in archived


def test_a_variable_this_build_does_not_supply_still_raises_a_message_not_a_traceback() -> None:
    """Regression control on `StrictUndefined`, which the `finalize` hook now runs in front of.

    `finalize` is called on the value of every expression *before* Jinja converts it to a string —
    so it is handed the `StrictUndefined` itself, and what it does with that decides whether the
    raise survives.

    **Most wrong hooks are safe by accident, and the review pass measured which.** `str(value)`
    and a truthiness test both raise `UndefinedError` on the undefined themselves, so neither
    swallows anything; `isinstance(value, str)` is `False` for it, so `_toml_basic` returns it
    untouched and Jinja raises when it stringifies. Only a hook that returns something *without
    ever touching* the undefined — a constant, a sentinel, a caught exception — turns this precise
    `TemplateError` back into the traceback the arm was written to prevent. That narrow shape is
    what this test guards, and an earlier version of this docstring named the two safe ones
    instead.
    """
    with pytest.raises(TemplateError) as raised:
        template.render_manifest("notes", {"name": "kb"})

    assert "needs a variable this build does not supply" in str(raised.value)


def test_a_name_holding_an_unpaired_surrogate_is_refused_before_anything_is_created(
    tmp_path: Path,
) -> None:
    """The one value class escaping cannot rescue, and the state it used to leave behind.

    TOML admits `%x80-D7FF` and `%xE000-10FFFF` raw and skips the surrogate gap, and `\\uXXXX`
    must name a Unicode scalar value — so U+D800-U+DFFF has no representation either way.
    Unescaped it reached `Path.write_text`, which **creates and truncates before the UTF-8
    encoder raises**: a zero-byte `pinakes.toml`, a directory `init` then refuses as *already a
    KB*, and a raw traceback. That is S4's own end state, reproduced by S4's own fix.

    The assertion on `exists()` is the load-bearing half. A refusal that still left the directory
    behind would satisfy the `raises` alone while leaving the KB exactly as bricked.
    """
    root = tmp_path / "kb"

    with pytest.raises(TemplateError):
        init(root, name="kb-\udcff-name", now="20260902 11:29")

    assert not root.exists()


def test_the_refusal_names_the_code_point_and_never_echoes_the_value(tmp_path: Path) -> None:
    """A name that carries an unpaired surrogate can carry an ANSI escape beside it.

    This message is printed to a terminal, so it identifies the character by code point rather
    than by showing it. Echoing the value would make the remedy for one unprintable-byte problem
    into a delivery mechanism for another.
    """
    with pytest.raises(TemplateError) as raised:
        init(tmp_path / "kb", name="kb-\udcff-\x1b[31m", now="20260902 11:29")

    message = f"{raised.value} {raised.value.remedy}"
    assert "U+DCFF" in message
    assert "\udcff" not in message
    assert "\x1b" not in message


def test_a_context_value_that_is_not_a_string_is_escaped_rather_than_passed_through() -> None:
    """The guard is an allow-list, and this is the half that used to be missing.

    It read *not a `str`*, so anything that was not one went out untouched — and Jinja calls
    `str()` on whatever `finalize` returns, so declining to inspect a value is declining to make
    it safe. A `Path` carrying a quote wrote the same unparseable manifest S4 exists to prevent.
    No call site in this build supplies one; the mechanism claim is what makes it a defect.
    """
    rendered = template.render_manifest("notes", _context(name=Path('a"b')))

    assert tomllib.loads(rendered)["kb"]["name"] == 'a"b'


@pytest.mark.parametrize(
    ("character", "escape"),
    [("\b", "\\b"), ("\f", "\\f"), ("\n", "\\n"), ("\r", "\\r")],
    ids=["backspace", "form feed", "newline", "carriage return"],
)
def test_the_four_reserved_escapes_are_written_as_letters_not_code_points(
    tmp_path: Path, character: str, escape: str
) -> None:
    """The only assertion in this file that four entries of `_TOML_ESCAPES` can fail.

    `\\b`, `\\f`, `\\n` and `\\r` each have a single-letter TOML escape *and* fall under the
    `\\uXXXX` fallback, which shadows them: drop any of the four and the manifest still parses and
    still round-trips the exact value. Measured — every round-trip test in this file stays green.
    So the four lines were unobservable, which is the standard this increment already used to
    delete the `bool` exclusion, applied here by a review pass rather than by its author.

    What separates them is the bytes a human opens: `name = "a\\nb"` against
    `name = "a\\u000ab"`. That is the assertion, in the same shape as the tab control above,
    because a `read_text` of the file is the only instrument that can see it.
    """
    value = f"a{character}b"

    result = init(tmp_path / "kb", name=value, now="20260903 09:00")

    written = (result.root / "pinakes.toml").read_text(encoding="utf-8")
    assert f'name     = "a{escape}b"' in written
    assert f"\\u{ord(character):04x}" not in written
    assert load(result.root).kb.name == value
