#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["rich", "rich-argparse"]
# ///
"""Check that terminal colour styles stay legible against kitty's palette.

Loads a kitty palette (the live config by default, or any kitty theme by name or file), collects the
colours that the shell and CLI tools actually use, and reports every foreground/background pair whose
WCAG contrast ratio is below --min.

Style sources:
  palette      the 16 ANSI colours against the background (colour 0 is exempt: "black" is a
               background colour in a dark theme; anything *drawing text* in colour 0 is caught
               by the other sources)
  fsh          fast-syntax-highlighting styles: the plugin is sourced in a clean zsh, then the
               deployed override file (~/.config/zsh/fsh-styles.zsh) if present
  autosuggest  zsh-autosuggestions (ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE, plugin default fg=8)
  ls           LS_COLORS and EZA_COLORS from an interactive zsh
  less         the -D colour options in $LESS
  git          git's colour defaults, overridden by `git config color.*`
  p10k         *_FOREGROUND / *_BACKGROUND from ~/.p10k.zsh

Bold is not brightened (kitty draws bold in the same colour). Colours 16-255 are the fixed xterm
cube and grey ramp; truecolour values are used as given.

Usage:
  tools/term-contrast/term-contrast.py                      # live kitty config
  tools/term-contrast/term-contrast.py --theme Blazer --theme "Tokyo Night"
  tools/term-contrast/term-contrast.py --conf ~/.config/kitty/current-theme.conf --all
Exits 1 if any pair fails.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from logging import getLogger
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table
from rich.text import Text
from rich_argparse import RawDescriptionRichHelpFormatter

logger = getLogger(__name__)

HOME = Path.home()
KITTY_CONF = HOME / ".config/kitty/kitty.conf"
FSH_DIR = (
    HOME / ".local/share/zinit/plugins/zdharma-continuum---fast-syntax-highlighting"
)
FSH_OVERRIDES = HOME / ".config/zsh/fsh-styles.zsh"
P10K = HOME / ".p10k.zsh"

NAMES = ["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"]
LESS_LETTERS = {"k": 0, "r": 1, "g": 2, "y": 3, "b": 4, "m": 5, "c": 6, "w": 7}
LESS_TYPES = {
    "B": "binary chars", "C": "control chars", "E": "errors", "M": "mark", "N": "line numbers",
    "P": "prompt", "R": "rscroll", "S": "search", "W": "unread", "d": "bold", "k": "blink",
    "s": "standout", "u": "underline",
}  # fmt: skip

# git's built-in colours (git-config(1)), keyed by config name. color.diff.whitespace is left out: it
# paints a background behind whitespace, so there is no text to read.
GIT_DEFAULTS = {
    "color.diff.meta": "bold",
    "color.diff.frag": "cyan",
    "color.diff.old": "red",
    "color.diff.new": "green",
    "color.diff.commit": "yellow",
    "color.diff.oldMoved": "bold magenta",
    "color.diff.newMoved": "bold cyan",
    "color.status.added": "green",
    "color.status.changed": "red",
    "color.status.untracked": "red",
    "color.status.branch": "green",
    "color.status.nobranch": "red",
    "color.status.unmerged": "red",
    "color.status.remoteBranch": "red",
    "color.branch.current": "green",
    "color.branch.remote": "red",
    "color.branch.upstream": "blue",
    "color.decorate.branch": "bold green",
    "color.decorate.remoteBranch": "bold red",
    "color.decorate.tag": "bold yellow",
    "color.decorate.stash": "bold magenta",
    "color.decorate.HEAD": "bold cyan",
    "color.decorate.grafted": "bold blue",
    "color.grep.filename": "magenta",
    "color.grep.linenumber": "green",
    "color.grep.separator": "cyan",
    "color.grep.match": "bold red",
}

# A colour reference before it is resolved against a palette:
# ("idx", n) | ("rgb", (r, g, b)) | ("fg",) | ("bg",)  -- the last two are the terminal defaults.
Ref = tuple
RGB = tuple[int, int, int]


class HelpFormatter(
    argparse.ArgumentDefaultsHelpFormatter, RawDescriptionRichHelpFormatter
):
    """Preserve description/epilog whitespace, show defaults, and style with Rich."""


@dataclass
class Palette:
    name: str
    background: RGB
    foreground: RGB
    colors: list[RGB]  # 0..15

    def resolve(self, ref: Ref) -> RGB:
        kind = ref[0]
        if kind == "fg":
            return self.foreground
        if kind == "bg":
            return self.background
        if kind == "rgb":
            return ref[1]
        n = ref[1]
        if n < 16:
            return self.colors[n]
        if n < 232:  # 6x6x6 cube
            n -= 16
            steps = [0, 95, 135, 175, 215, 255]
            return (steps[n // 36], steps[(n // 6) % 6], steps[n % 6])
        v = 8 + 10 * (n - 232)
        return (v, v, v)


@dataclass
class Style:
    source: str
    name: str
    fg: Ref = ("fg",)
    bg: Ref = ("bg",)
    raw: str = ""


@dataclass
class Result:
    style: Style
    ratio: float
    names: list[str] = field(default_factory=list)


def get_cli_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=HelpFormatter)
    parser.add_argument(
        "--theme",
        action="append",
        default=[],
        help="kitty theme name (kitten themes); repeatable",
    )
    parser.add_argument(
        "--conf",
        action="append",
        default=[],
        type=Path,
        help="kitty .conf file; repeatable",
    )
    parser.add_argument(
        "--min",
        type=float,
        default=3.0,
        help="minimum contrast ratio (WCAG 3.0 = large text / UI)",
    )
    parser.add_argument(
        "--all", action="store_true", help="list every style, not only failures"
    )
    parser.add_argument(
        "--sources",
        default="palette,fsh,autosuggest,ls,less,git,p10k",
        help="comma-separated style sources to check",
    )
    parser.add_argument(
        "--loglevel",
        "-l",
        default="WARNING",
        type=lambda v: v.strip().upper(),
        help="Logging verbosity (DEBUG, INFO, WARNING, ERROR).",
    )
    return parser.parse_args()


def setup_logger(args: argparse.Namespace) -> None:
    logger.addHandler(RichHandler(level=args.loglevel, console=Console(stderr=True)))
    logger.setLevel(args.loglevel)


def run(cmd: list[str]) -> str:
    logger.debug("run: %s", shlex.join(cmd))
    return subprocess.run(cmd, check=True, text=True, capture_output=True).stdout


# --- palettes ----------------------------------------------------------------------------------

KITTY_LOADER = """
import json, sys
from kitty.config import load_config
o = load_config(sys.argv[-1])
rgb = lambda c: [c.red, c.green, c.blue]
print(json.dumps({"background": rgb(o.background), "foreground": rgb(o.foreground),
                  "colors": [rgb(getattr(o, f"color{i}")) for i in range(16)]}))
"""


def load_palette(conf: Path, name: str) -> Palette:
    """Load a kitty config through kitty itself, so includes and defaults resolve as kitty sees them."""
    data = json.loads(run(["kitty", "+runpy", KITTY_LOADER, str(conf)]))
    return Palette(
        name,
        tuple(data["background"]),
        tuple(data["foreground"]),
        [tuple(c) for c in data["colors"]],
    )


def theme_palette(theme: str, tmp: Path) -> Palette:
    conf = tmp / f"{re.sub(r'[^A-Za-z0-9]+', '_', theme)}.conf"
    conf.write_text(run(["kitten", "themes", "--dump-theme", theme]))
    return load_palette(conf, f"theme: {theme}")


# --- colour parsing ------------------------------------------------------------------------------


def hex_rgb(value: str) -> RGB:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def zsh_colour(value: str) -> Ref | None:
    """A colour in zsh's highlight syntax (fg=VALUE): name, number or #hex."""
    value = value.strip().lower()
    if value in ("", "default", "none"):
        return None
    if value.startswith("#"):
        return ("rgb", hex_rgb(value))
    if value.isdigit():
        return ("idx", int(value))
    if value in NAMES:
        return ("idx", NAMES.index(value))
    logger.warning("unknown zsh colour %r", value)
    return None


def parse_zsh_style(source: str, name: str, spec: str) -> Style:
    style = Style(source, name, raw=spec)
    for part in spec.split(","):
        key, _, val = part.partition("=")
        if key == "fg" and (ref := zsh_colour(val)):
            style.fg = ref
        elif key == "bg" and (ref := zsh_colour(val)):
            style.bg = ref
    return style


def parse_sgr(source: str, name: str, spec: str) -> Style:
    """An SGR parameter list as in LS_COLORS ("01;38;5;214")."""
    style = Style(source, name, raw=spec)
    codes = [int(c) for c in spec.split(";") if c.isdigit()]
    reverse = False
    i = 0
    while i < len(codes):
        c = codes[i]
        target = "fg" if c == 38 else "bg"
        if c in (38, 48) and i + 2 < len(codes) and codes[i + 1] == 5:
            setattr(style, target, ("idx", codes[i + 2]))
            i += 3
            continue
        if c in (38, 48) and i + 4 < len(codes) and codes[i + 1] == 2:
            setattr(style, target, ("rgb", tuple(codes[i + 2 : i + 5])))
            i += 5
            continue
        if 30 <= c <= 37:
            style.fg = ("idx", c - 30)
        elif 90 <= c <= 97:
            style.fg = ("idx", c - 90 + 8)
        elif 40 <= c <= 47:
            style.bg = ("idx", c - 40)
        elif 100 <= c <= 107:
            style.bg = ("idx", c - 100 + 8)
        elif c == 7:
            reverse = True
        i += 1
    if reverse:  # the default colours swap too
        fg = {("fg",): ("bg",)}.get(style.fg, style.fg)
        bg = {("bg",): ("fg",)}.get(style.bg, style.bg)
        style.fg, style.bg = bg, fg
    return style


def git_colour(word: str) -> Ref | None:
    word = word.lower()
    if word in ("normal", "default", "reset"):
        return ("fg",)
    if word.startswith("#"):
        return ("rgb", hex_rgb(word))
    if word.isdigit():
        return ("idx", int(word))
    if word in NAMES:
        return ("idx", NAMES.index(word))
    if word.startswith("bright") and word[6:] in NAMES:
        return ("idx", NAMES.index(word[6:]) + 8)
    return None  # an attribute (bold, ul, ...)


def parse_git(name: str, spec: str) -> Style:
    style = Style("git", name, raw=spec)
    colours = [ref for w in spec.split() if (ref := git_colour(w)) is not None]
    if colours:
        style.fg = colours[0]
    if len(colours) > 1:
        style.bg = colours[1] if colours[1] != ("fg",) else ("bg",)
    return style


# --- style sources -------------------------------------------------------------------------------


def zsh(script: str, *, interactive: bool = False) -> str:
    return run(["zsh", "-fic" if interactive else "-fc", script])


def fsh_styles() -> list[Style]:
    plugin = FSH_DIR / "fast-syntax-highlighting.plugin.zsh"
    if not plugin.exists():
        logger.warning("fast-syntax-highlighting not found at %s", FSH_DIR)
        return []
    overrides = (
        f"source {shlex.quote(str(FSH_OVERRIDES))}" if FSH_OVERRIDES.exists() else ":"
    )
    out = zsh(
        f"source {shlex.quote(str(plugin))}; {overrides}; "
        'for k v in ${(kv)FAST_HIGHLIGHT_STYLES}; do [[ $k == ${FAST_THEME_NAME}* ]] && print -r -- "$k"$\'\\t\'"$v"; done',
        interactive=True,
    )
    styles = []
    for line in out.splitlines():
        key, _, spec = line.partition("\t")
        if key.endswith(("-path", "secondary")) or not spec or spec == "none":
            continue
        styles.append(parse_zsh_style("fsh", key, spec))
    return styles


def autosuggest_styles() -> list[Style]:
    out = zsh(
        'print -r -- "${ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE-}"', interactive=True
    ).strip()
    return [parse_zsh_style("autosuggest", "suggestion", out or "fg=8")]


def ls_styles() -> list[Style]:
    out = run(
        ["zsh", "-ic", 'print -r -- "$LS_COLORS"; print -r -- "${EZA_COLORS-}"']
    ).splitlines()
    styles = []
    for var, value in zip(("LS_COLORS", "EZA_COLORS"), out + ["", ""]):
        for entry in value.split(":"):
            key, _, spec = entry.partition("=")
            if spec and spec not in ("0", "00"):
                styles.append(parse_sgr("ls", f"{var}:{key}", spec))
    return styles


def less_styles() -> list[Style]:
    styles = []
    for token in shlex.split(os.environ.get("LESS", "")):
        for opt in token.split("$"):
            opt = opt.lstrip("-")
            if not opt.startswith("D") or len(opt) < 3:
                continue
            kind, colours = opt[1], opt[2:]
            style = Style("less", f"-D{kind} ({LESS_TYPES.get(kind, '?')})", raw=opt)
            refs = []
            for ch in colours:
                if ch.lower() in LESS_LETTERS:
                    refs.append(
                        ("idx", LESS_LETTERS[ch.lower()] + (8 if ch.isupper() else 0))
                    )
                elif ch == "-":
                    refs.append(None)
            if refs and refs[0]:
                style.fg = refs[0]
            if len(refs) > 1 and refs[1]:
                style.bg = refs[1]
            styles.append(style)
    return styles


def git_styles() -> list[Style]:
    specs = dict(GIT_DEFAULTS)
    try:
        out = run(["git", "config", "--global", "--get-regexp", r"^color\..*\..*"])
    except subprocess.CalledProcessError:
        out = ""  # no colour settings
    for line in out.splitlines():
        key, _, value = line.partition(" ")
        specs[key] = value
    return [parse_git(k, v) for k, v in specs.items()]


def p10k_styles() -> list[Style]:
    if not P10K.exists():
        return []
    out = zsh(
        f"source {shlex.quote(str(P10K))} >/dev/null 2>&1; "
        'for k in ${(M)${(k)parameters}:#POWERLEVEL9K_*GROUND}; do print -r -- "$k"$\'\\t\'"${(P)k}"; done'
    )
    params = dict(line.partition("\t")[::2] for line in out.splitlines())
    styles = []
    for key, value in sorted(params.items()):
        if key.endswith("_FOREGROUND") and value:
            style = parse_zsh_style(
                "p10k", key.removeprefix("POWERLEVEL9K_"), f"fg={value}"
            )
            bg = params.get(
                key.removesuffix("_FOREGROUND") + "_BACKGROUND"
            ) or params.get("POWERLEVEL9K_BACKGROUND")
            if bg and (ref := zsh_colour(bg)):
                style.bg = ref
            styles.append(style)
    return styles


def palette_styles() -> list[Style]:
    return [
        Style("palette", f"color{i}", fg=("idx", i), raw=f"color{i}")
        for i in range(1, 16)
    ]


SOURCES = {
    "palette": palette_styles,
    "fsh": fsh_styles,
    "autosuggest": autosuggest_styles,
    "ls": ls_styles,
    "less": less_styles,
    "git": git_styles,
    "p10k": p10k_styles,
}


# --- contrast ------------------------------------------------------------------------------------


def luminance(rgb: RGB) -> float:
    def channel(c: int) -> float:
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: RGB, b: RGB) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def hexs(rgb: RGB) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def check(palette: Palette, styles: list[Style]) -> list[Result]:
    """Contrast per style, grouping styles of one source that resolve to the same colour pair."""
    grouped: dict[tuple, Result] = {}
    for style in styles:
        fg, bg = palette.resolve(style.fg), palette.resolve(style.bg)
        key = (style.source, fg, bg)
        if key in grouped:
            grouped[key].names.append(style.name)
        else:
            grouped[key] = Result(style, contrast(fg, bg), [style.name])
    return sorted(grouped.values(), key=lambda r: r.ratio)


def report(
    console: Console,
    palette: Palette,
    results: list[Result],
    minimum: float,
    show_all: bool,
) -> int:
    failures = [r for r in results if r.ratio < minimum]
    shown = results if show_all else failures
    title = f"{palette.name}: background {hexs(palette.background)}, {len(failures)} below {minimum:g}:1"
    if not shown:
        console.print(f"[green]✓[/green] {title}")
        return 0
    table = Table(title=title, title_justify="left", show_lines=False)
    for col in ("source", "ratio", "sample", "fg", "bg", "styles"):
        table.add_column(col, overflow="fold")
    for r in shown:
        fg, bg = palette.resolve(r.style.fg), palette.resolve(r.style.bg)
        names = ", ".join(r.names[:3]) + (
            f" (+{len(r.names) - 3})" if len(r.names) > 3 else ""
        )
        ratio = Text(f"{r.ratio:.2f}", style="red" if r.ratio < minimum else "green")
        sample = Text(" Sample ", style=f"{hexs(fg)} on {hexs(bg)}")
        table.add_row(r.style.source, ratio, sample, f"{hexs(fg)} {ref_label(r.style.fg)}",
                      f"{hexs(bg)} {ref_label(r.style.bg)}", f"{names}  [dim]{r.style.raw}[/dim]")  # fmt: skip
    console.print(table)
    return len(failures)


def ref_label(ref: Ref) -> str:
    return {
        "idx": lambda: f"({ref[1]})",
        "rgb": lambda: "",
        "fg": lambda: "(fg)",
        "bg": lambda: "(bg)",
    }[ref[0]]()


def main() -> None:
    args = get_cli_arguments()
    setup_logger(args)
    console = Console()

    styles: list[Style] = []
    for name in args.sources.split(","):
        try:
            found = SOURCES[name.strip()]()
        except subprocess.CalledProcessError as e:
            logger.error("%s: %s failed: %s", name, shlex.join(e.cmd), e.stderr.strip())
            continue
        logger.info("%s: %d styles", name, len(found))
        styles += found

    with tempfile.TemporaryDirectory() as tmp:
        palettes = [load_palette(c.expanduser(), f"conf: {c}") for c in args.conf]
        palettes += [theme_palette(t, Path(tmp)) for t in args.theme]
        if not palettes:
            palettes = [load_palette(KITTY_CONF, f"live: {KITTY_CONF}")]

    failed = sum(
        report(console, p, check(p, styles), args.min, args.all) for p in palettes
    )
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
