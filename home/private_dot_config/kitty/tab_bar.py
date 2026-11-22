"""kitty tab bar: round powerline tabs with a left cap, and a mode pill on the right.

kitty's powerline style draws only the separator after each tab, so the strip's left end is
square; with tab_bar_margin_width it shows. This draws the cap, then hands every tab to
kitty's own draw_tab_with_powerline (chz-8bg.12, MH's pick over a waybar-style custom bar,
2026-11-21). Colours: the theme engine (amontillado templates/kitty.mustache).

While a keyboard mode is active (window mode on kitty_mod+r, or a multi-key prefix such as
kitty_mod+p for hints), a pill on the right lists its keys: ( NAME ▸ keys ). The keys come
from the mode's own keymap as kitty parsed it from kitty.conf, so they cannot drift; LABELS
only shortens the actions. kitty redraws the bar on every mode change (chz-8bg.14). The
keymap is kitty-internal: if reading it fails, the pill shows the mode name alone.

kitty loads this file once per process: restart kitty (not reload) after changing it.
"""

from __future__ import annotations

from collections.abc import Iterable

from kitty.fast_data_types import Screen, get_boss, get_options
from kitty.tab_bar import (
    DrawData,
    ExtraData,
    TabBarData,
    as_rgb,
    draw_tab_with_powerline,
)
from kitty.types import human_repr_of_single_key
from kitty.utils import color_as_int, log_error

LEFT_CAP = ""  # the mirror of the round style's separator
RIGHT_CAP = ""
DIVIDER = ""

# Pill names: named modes, then multi-key prefixes by their first key.
MODE_NAMES = {"window": "WINDOW"}
PREFIX_NAMES = {"p": "HINTS", "a": "OPACITY"}

# Action (as written in kitty.conf, matched by prefix) -> short label.
LABELS = (
    ("resize_window reset", "equal"),
    ("resize_window", "resize"),
    ("move_window", "move"),
    ("layout_action rotate", "rotate"),
    ("toggle_layout stack", "zoom"),
    ("pop_keyboard_mode", "exit"),
    ("kitten hints --type path --program", "path"),
    ("kitten hints --type path", "open path"),
    ("kitten hints --type linenum", "file:line"),
    ("kitten hints --type hyperlink", "link"),
    ("kitten choose-files --mode=dir", "dir"),
    ("kitten choose-files", "file"),
    ("set_background_opacity +", "more"),
    ("set_background_opacity -", "less"),
    ("set_background_opacity default", "default"),
    ("set_background_opacity", "opaque"),
)
KEY_NAMES = {"escape": "esc", "equal": "=", "enter": "⏎", "minus": "-", "plus": "+"}
ARROWS = {"left", "right", "up", "down"}
VIM_ORDER = "hjkl"


def label_for(action: str) -> str:
    for prefix, label in LABELS:
        if action.startswith(prefix):
            return label
    if action.startswith("kitten hints --type "):
        return action.split()[3]
    return action.split()[0]


def key_name(human: str) -> str:
    *mods, key = human.split("+")
    key = KEY_NAMES.get(key, key)
    return ("⇧" if "shift" in mods and len(mods) == 1 else "+".join(mods + [""])) + key


def vim_rank(char: str) -> int:
    return VIM_ORDER.index(char) if char in VIM_ORDER else len(VIM_ORDER)


def join_keys(keys: list[str]) -> str:
    """'h','j','k','l' -> 'hjkl'; '⇧h','⇧j' -> '⇧hj'; arrows dropped when letters exist."""
    letters = [k for k in keys if k.lstrip("⇧") not in ARROWS]
    keys = letters or keys
    if (
        keys
        and all(len(k.lstrip("⇧")) == 1 for k in keys)
        and len({k[0] == "⇧" for k in keys}) == 1
    ):
        shift = "⇧" if keys[0].startswith("⇧") else ""
        chars = sorted((k.lstrip("⇧") for k in keys), key=vim_rank)
        return shift + "".join(chars)
    return "/".join(keys)


def mode_hints(keymap: dict, kitty_mod: int) -> str:
    groups: dict[str, list[str]] = {}
    for key, defs in keymap.items():
        label = label_for(defs[-1].definition)
        groups.setdefault(label, []).append(
            key_name(human_repr_of_single_key(key, kitty_mod))
        )
    exit_keys = groups.pop("exit", None)
    parts = [f"{join_keys(keys)} {label}" for label, keys in groups.items()]
    if exit_keys:
        parts.append(exit_keys[0])
    return " · ".join(parts)


def active_mode(os_window_id: int) -> tuple[str, str] | None:
    """(name, hints) for the active OS window's current keyboard mode, or None."""
    boss = get_boss()
    stack = boss.mappings.keyboard_mode_stack
    tm = boss.active_tab_manager
    if not stack or tm is None or tm.os_window_id != os_window_id:
        return None
    mode = stack[-1]
    name = MODE_NAMES.get(mode.name, mode.name.upper())
    try:
        if mode.sequence_keys:
            first = chr(mode.sequence_keys[0].key)
            name = PREFIX_NAMES.get(first, "kitty_mod+" + first)
        return name, mode_hints(mode.keymap, get_options().kitty_mod)
    except (AttributeError, IndexError, KeyError, TypeError, ValueError) as e:
        # kitty internals moved: keep the bar drawing, name only.
        log_error(f"tab_bar.py: mode pill keys unavailable: {e!r}")
        return name, ""


def draw_segments(
    screen: Screen, segments: Iterable[tuple[str, int, int]], default_bg: int
) -> None:
    segs = list(segments)
    screen.cursor.fg, screen.cursor.bg = segs[0][2], default_bg
    screen.draw(LEFT_CAP)
    # The cursor carries the last tab's font style (bold italic when it is active): set ours.
    screen.cursor.italic = False
    for i, (text, fg, bg) in enumerate(segs):
        screen.cursor.fg, screen.cursor.bg = fg, bg
        screen.cursor.bold = i == 0  # the mode name
        screen.draw(text)
        nxt = segs[i + 1][2] if i + 1 < len(segs) else default_bg
        screen.cursor.fg, screen.cursor.bg = bg, nxt
        screen.draw(DIVIDER if i + 1 < len(segs) else RIGHT_CAP)


def draw_mode_pill(draw_data: DrawData, screen: Screen, after: int) -> None:
    mode = active_mode(draw_data.os_window_id)
    if mode is None:
        return
    name, hints = mode
    room = screen.columns - after - 2  # a gap after the tabs; the last cell stays blank
    name_text = f" {name} "
    fixed = len(name_text) + 2  # caps
    if fixed > room:
        return
    segments = [(name_text, draw_data.active_fg, draw_data.active_bg)]
    if hints and fixed + 4 <= room:  # divider, spaces and at least one character
        hint_text = f" {hints} "
        if fixed + 1 + len(hint_text) > room:
            hint_text = hint_text[: room - fixed - 3] + "… "
        segments.append((hint_text, draw_data.inactive_fg, draw_data.inactive_bg))
    width = 2 + sum(len(t) for t, _, _ in segments) + len(segments) - 1
    colours = [
        (t, as_rgb(color_as_int(fg)), as_rgb(color_as_int(bg)))
        for t, fg, bg in segments
    ]
    screen.cursor.x = screen.columns - 1 - width
    draw_segments(screen, colours, as_rgb(color_as_int(draw_data.default_bg)))


def draw_tab(
    draw_data: DrawData,
    screen: Screen,
    tab: TabBarData,
    before: int,
    max_title_length: int,
    index: int,
    is_last: bool,
    extra_data: ExtraData,
) -> int:
    if screen.cursor.x == 0:
        tab_fg, tab_bg = screen.cursor.fg, screen.cursor.bg
        screen.cursor.fg = tab_bg
        screen.cursor.bg = as_rgb(int(draw_data.default_bg))
        screen.draw(LEFT_CAP)
        screen.cursor.fg, screen.cursor.bg = tab_fg, tab_bg
        # The padding cell the powerline draw adds itself only at x == 0.
        screen.draw(" ")
    end = draw_tab_with_powerline(
        draw_data, screen, tab, before, max_title_length, index, is_last, extra_data
    )
    # kitty erases from the cursor to the line's end after the last tab: the pill goes last
    # and leaves the cursor after itself. Not in the measuring pass (for_layout).
    if is_last and not extra_data.for_layout:
        draw_mode_pill(draw_data, screen, screen.cursor.x)
    return end
