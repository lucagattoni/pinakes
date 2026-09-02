"""Rendering a manifest: what a user's own text may contain, and still round-trip (S4).

`_render` interpolates into TOML. Every variable this build supplies lands inside a basic string
except `embedding_dim`, so a value carrying a `"` or a `\\` used to close or escape that string and
write a `pinakes.toml` no parser could read — while `pnk init` exited 0 and printed *created*.
The KB was bricked at the moment of creation and there was no repair: `pnk init` refuses a directory
that is already a KB, so the remedy surface was empty and recovery meant hand-editing TOML.

**These tests are about the mechanism, not about `--name`.** The fix is a `finalize` hook on the
Jinja template, so the property under test is *every interpolated value is safe*, and the tests that
matter most are the ones that would still pass if someone re-broke `--name` alone: the controls at
the bottom of this file.
"""

import tomllib
from pathlib import Path

import pytest

from pinakes import template
from pinakes.errors import TemplateError
from pinakes.init import init
from pinakes.manifest import load

#: One value per class the sweep named, plus the two the verifier widened it with. A `str` here is
#: a *user's KB name*: it reaches `render_manifest` through `pnk init --name`, and through
#: `root.name` when no flag is passed at all.
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
    so it is handed the `StrictUndefined` itself. A hook that stringified its argument, or that
    tested truthiness rather than type, would swallow the raise here and turn a precise
    `TemplateError` back into the traceback this arm was written to prevent.
    """
    with pytest.raises(TemplateError) as raised:
        template.render_manifest("notes", {"name": "kb"})

    assert "needs a variable this build does not supply" in str(raised.value)
