"""kitty tab bar: the built-in round powerline tabs, plus a round left cap on the first tab.

kitty's powerline style draws only the separator after each tab, so the strip's left end is
square; with tab_bar_margin_width it shows. This draws the cap, then hands every tab to
kitty's own draw_tab_with_powerline (chz-8bg.12, MH's pick over a waybar-style custom bar,
2026-11-21). Colours: the theme engine (amontillado templates/kitty.mustache).
kitty loads this file once per process: restart kitty (not reload) after changing it.
"""

from kitty.fast_data_types import Screen
from kitty.tab_bar import (
    DrawData,
    ExtraData,
    TabBarData,
    as_rgb,
    draw_tab_with_powerline,
)

LEFT_CAP = ""  # the mirror of the round style's separator


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
    return draw_tab_with_powerline(
        draw_data, screen, tab, before, max_title_length, index, is_last, extra_data
    )
