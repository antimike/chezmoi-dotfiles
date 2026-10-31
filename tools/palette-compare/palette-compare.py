#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml", "rich", "rich-argparse"]
# ///
"""Compare palette generators (matugen, wallust) on wallpapers as terminal palettes.

Runs each generator setting on each picture, turns the result into a 16-colour terminal palette
(background, foreground, color0-15, written as a kitty .conf), and scores it next to the live kitty
palette (the hand-made Blazer baseline):

  tc fails    style pairs below --min, by tools/term-contrast's own checks (its palette, fsh,
              autosuggest, git and less sources; the module is loaded from its path, not copied)
  fg/bg       WCAG contrast of the foreground on the background
  accent min  lowest contrast of colours 1-6 on the background
  distinct    smallest OKLab distance (x100) between two of colours 1-6; under ~8 two accents
              are hard to tell apart in a diff or a listing
  hues        how many of colours 1-6 sit within 45 degrees (OKLCH) of the hue their ANSI name
              promises (red, green, yellow, blue, magenta, cyan) with some chroma; git, ls and
              compiler errors rely on that

Settings compared (--settings picks some):
  matugen       matugen image --source-color-index 0, dark mode; base16 mapped to ANSI as
                base16-shell does (color1 = base08 red, color2 = base0B green, ...)
  wallust       wallust run, default backend, colour space and palette
  wallust-k     the same with --check-contrast
  wallust-ansi  --check-contrast --colorspace lchansi --palette ansidark16 (wallust's mode that
                keeps the tty colour order)

Generators run in a throwaway XDG config and cache home with terminal sequences off, so the live
terminals, ~/.config and ~/.cache are untouched. Output in --out: one kitty .conf per picture and
setting, summary.json, and index.html (the contact sheet; open it in a browser).

Usage:
  tools/palette-compare/palette-compare.py                       # the amo library (amo list)
  tools/palette-compare/palette-compare.py ~/Pictures/a.jpg --settings matugen,wallust-ansi
  tools/palette-compare/palette-compare.py --out /tmp/pc && xdg-open /tmp/pc/index.html
"""

from __future__ import annotations

import argparse
import html
import importlib.util
import itertools
import json
import math
import os
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from logging import getLogger
from pathlib import Path
from types import ModuleType

import yaml
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table
from rich_argparse import RawDescriptionRichHelpFormatter

logger = getLogger(__name__)

TERM_CONTRAST = (
    Path(__file__).resolve().parent.parent / "term-contrast/term-contrast.py"
)
TC_SOURCES = ("palette", "fsh", "autosuggest", "git", "less")

# base16-shell's ANSI mapping: color0-15 from base00-0F.
BASE16_ANSI = ["base00", "base08", "base0b", "base0a", "base0d", "base0e", "base0c", "base05",
               "base03", "base08", "base0b", "base0a", "base0d", "base0e", "base0c", "base07"]  # fmt: skip
ANSI_PRIMARIES = {
    1: "#ff0000",
    2: "#00ff00",
    3: "#ffff00",
    4: "#0000ff",
    5: "#ff00ff",
    6: "#00ffff",
}
HUE_TOLERANCE = 45.0
MIN_CHROMA = 0.03

SETTINGS = {
    "matugen": ["--source-color-index", "0"],
    "wallust": [],
    "wallust-k": ["--check-contrast"],
    "wallust-ansi": [
        "--check-contrast",
        "--colorspace",
        "lchansi",
        "--palette",
        "ansidark16",
    ],
}

WALLUST_TEMPLATE = (
    '{"background":"{{background}}","foreground":"{{foreground}}","colors":['
    + ",".join(f'"{{{{color{i}}}}}"' for i in range(16))
    + "]}\n"
)

RGB = tuple[int, int, int]


class HelpFormatter(
    argparse.ArgumentDefaultsHelpFormatter, RawDescriptionRichHelpFormatter
):
    """Preserve description/epilog whitespace, show defaults, and style with Rich."""


@dataclass
class Score:
    tc_fails: int
    fg_bg: float
    accent_min: float
    distinct: float
    hues: int


@dataclass
class Entry:
    picture: str
    setting: str
    background: str
    foreground: str
    colors: list[str]
    score: Score | None = None
    error: str = ""


def get_cli_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=HelpFormatter)
    parser.add_argument(
        "pictures", nargs="*", type=Path, help="pictures to compare (default: amo list)"
    )
    parser.add_argument(
        "--settings",
        default=",".join(SETTINGS),
        help="comma-separated generator settings to run",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path.home() / ".cache/palette-compare",
        help="output directory (kitty confs, summary.json, index.html)",
    )
    parser.add_argument(
        "--min", type=float, default=3.0, help="term-contrast minimum ratio"
    )
    parser.add_argument(
        "--loglevel",
        "-l",
        default="INFO",
        type=lambda v: v.strip().upper(),
        help="Logging verbosity (DEBUG, INFO, WARNING, ERROR).",
    )
    return parser.parse_args()


def setup_logger(args: argparse.Namespace) -> None:
    logger.addHandler(RichHandler(level=args.loglevel, console=Console(stderr=True)))
    logger.setLevel(args.loglevel)


def load_term_contrast() -> ModuleType:
    spec = importlib.util.spec_from_file_location("term_contrast", TERM_CONTRAST)
    if spec is None or spec.loader is None:
        sys.exit(f"palette-compare: cannot load {TERM_CONTRAST}")
    module = importlib.util.module_from_spec(spec)
    # dataclasses resolves annotations through sys.modules, so register before executing.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# --- colour maths -------------------------------------------------------------------------------


def rgb(hex_colour: str) -> RGB:
    h = hex_colour.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def oklab(c: RGB) -> tuple[float, float, float]:
    def linear(v: int) -> float:
        v /= 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

    r, g, b = (linear(v) for v in c)
    lms = (
        0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b,
        0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b,
        0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b,
    )
    l_, m_, s_ = (math.copysign(abs(v) ** (1 / 3), v) for v in lms)
    return (
        0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
        1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
        0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_,
    )


def chroma_hue(c: RGB) -> tuple[float, float]:
    _, a, b = oklab(c)
    return math.hypot(a, b), math.degrees(math.atan2(b, a)) % 360


def hue_gap(h1: float, h2: float) -> float:
    d = abs(h1 - h2) % 360
    return min(d, 360 - d)


def score(tc: ModuleType, styles: list, palette, minimum: float) -> Score:
    bg = palette.background
    accents = [palette.colors[i] for i in range(1, 7)]
    nominal = {i: chroma_hue(rgb(h))[1] for i, h in ANSI_PRIMARIES.items()}
    hues = 0
    for i, colour in zip(range(1, 7), accents):
        c, h = chroma_hue(colour)
        hues += c >= MIN_CHROMA and hue_gap(h, nominal[i]) <= HUE_TOLERANCE
    return Score(
        tc_fails=sum(r.ratio < minimum for r in tc.check(palette, styles)),
        fg_bg=round(tc.contrast(palette.foreground, bg), 2),
        accent_min=round(min(tc.contrast(c, bg) for c in accents), 2),
        distinct=round(
            100
            * min(
                math.dist(oklab(a), oklab(b))
                for a, b in itertools.combinations(accents, 2)
            ),
            1,
        ),
        hues=hues,
    )


# --- generators ---------------------------------------------------------------------------------


def run(cmd: list[str], env: dict[str, str]) -> str:
    logger.debug("%s", " ".join(cmd))
    return subprocess.run(
        cmd, check=True, text=True, capture_output=True, env=env
    ).stdout


def run_matugen(
    picture: Path, args: list[str], work: Path, env: dict[str, str]
) -> dict:
    config = work / "matugen.toml"
    config.write_text("[config]\n\n[templates]\n")
    out = run(["matugen", "image", str(picture), "-c", str(config), "--dry-run", "-q",
               "-m", "dark", "-j", "hex", *args], env)  # fmt: skip
    base16 = json.loads(out)["base16"]
    colour = {k: v["dark"]["color"] for k, v in base16.items()}
    return {
        "background": colour["base00"],
        "foreground": colour["base05"],
        "colors": [colour[k] for k in BASE16_ANSI],
    }


def run_wallust(
    picture: Path, args: list[str], work: Path, env: dict[str, str]
) -> dict:
    target = work / "wallust.json"
    target.unlink(missing_ok=True)
    (work / "wallust/templates").mkdir(parents=True, exist_ok=True)
    (work / "wallust/templates/palette.json").write_text(WALLUST_TEMPLATE)
    (work / "wallust/wallust.toml").write_text(
        f'[templates]\npalette = {{ template = "palette.json", target = "{target}" }}\n'
    )
    run(
        [
            "wallust",
            "run",
            "-q",
            "-s",
            "-n",
            "-d",
            str(work / "wallust"),
            *args,
            str(picture),
        ],
        env,
    )
    data = json.loads(target.read_text())
    data["colors"] = [c.lower() for c in data["colors"]]
    data["background"], data["foreground"] = (
        data["background"].lower(),
        data["foreground"].lower(),
    )
    return data


def generate(setting: str, picture: Path, work: Path, env: dict[str, str]) -> dict:
    runner = run_matugen if setting.startswith("matugen") else run_wallust
    return runner(picture, SETTINGS[setting], work, env)


# --- output -------------------------------------------------------------------------------------


def write_conf(path: Path, data: dict) -> None:
    lines = [f"background {data['background']}", f"foreground {data['foreground']}"]
    lines += [f"color{i} {c}" for i, c in enumerate(data["colors"])]
    path.write_text("\n".join(lines) + "\n")


def picture_metrics(picture: Path) -> dict:
    info = picture.parent / "info.yaml"
    if not info.exists():
        return {}
    files = (yaml.safe_load(info.read_text()) or {}).get("files", {})
    metrics = files.get(picture.name, {}).get("metrics", {})
    return {
        k: metrics[k]
        for k in ("lightness", "chroma", "hue_name", "hue_spread")
        if k in metrics
    }


def sample_html(entry: Entry) -> str:
    c = entry.colors
    words = ["red", "green", "yellow", "blue", "magenta", "cyan"]
    normal = " ".join(
        f'<span style="color:{c[i]}">{w}</span>' for i, w in enumerate(words, 1)
    )
    bright = " ".join(
        f'<span style="color:{c[i + 8]}">{w}</span>' for i, w in enumerate(words, 1)
    )
    swatches = "".join(
        f'<span class="sw" style="background:{x}" title="color{i} {x}"></span>'
        for i, x in enumerate(c)
    )
    return (
        f'<div class="term" style="background:{entry.background};color:{entry.foreground}">'
        f"<div>{swatches}</div>"
        f"<div>text on background {html.escape(entry.background)}</div>"
        f"<div>{normal}</div><div>{bright}</div>"
        f'<div><span style="color:{c[8]}"># comment, autosuggestion (8)</span></div>'
        f'<div><span style="color:{c[1]}">- removed line</span> '
        f'<span style="color:{c[2]}">+ added line</span> '
        f'<span style="color:{c[4]}">dir/</span> <span style="color:{c[2]}">exec*</span></div>'
        "</div>"
    )


def score_html(entry: Entry) -> str:
    if entry.error:
        return f'<td colspan="5" class="bad">{html.escape(entry.error)}</td>'
    s = entry.score
    cells = [
        (s.tc_fails, s.tc_fails == 0),
        (s.fg_bg, s.fg_bg >= 7),
        (s.accent_min, s.accent_min >= 3),
        (s.distinct, s.distinct >= 8),
        (f"{s.hues}/6", s.hues == 6),
    ]
    return "".join(
        f'<td class="{"ok" if good else "bad"}">{v}</td>' for v, good in cells
    )


def write_html(
    path: Path, baseline: Entry, entries: list[Entry], pictures: list[Path]
) -> None:
    head = "<tr><th>setting</th><th>sample</th><th>tc fails</th><th>fg/bg</th><th>accent min</th><th>distinct</th><th>hues</th></tr>"

    def row(e: Entry) -> str:
        sample = sample_html(e) if not e.error else ""
        return f"<tr><td>{html.escape(e.setting)}</td><td>{sample}</td>{score_html(e)}</tr>"

    body = [f"<h2>Baseline</h2><table>{head}{row(baseline)}</table>"]
    for picture in pictures:
        metrics = ", ".join(f"{k} {v}" for k, v in picture_metrics(picture).items())
        rows = "".join(row(e) for e in entries if e.picture == str(picture))
        body.append(
            f"<h2>{html.escape(picture.parent.name)}</h2>"
            f'<p class="meta">{html.escape(metrics)}</p>'
            f'<img src="file://{html.escape(str(picture))}" loading="lazy">'
            f"<table>{head}{rows}</table>"
        )
    path.write_text(
        "<!doctype html><meta charset=utf-8><title>Palette compare</title><style>"
        "body{font-family:sans-serif;background:#f4f4f4;color:#111;margin:16px}"
        "img{max-width:480px;display:block;margin:8px 0}"
        "table{border-collapse:collapse;margin-bottom:24px}td,th{padding:4px 8px;vertical-align:top;border-bottom:1px solid #ccc}"
        ".term{font-family:monospace;padding:8px;line-height:1.5;min-width:440px}"
        ".sw{display:inline-block;width:22px;height:14px;margin-right:2px}"
        ".ok{color:#176b2c}.bad{color:#b3261e;font-weight:bold}.meta{color:#555}"
        "</style><h1>Palette compare</h1>"
        "<p>Thresholds (red = below): tc fails 0, fg/bg 7, accent min 3, distinct 8, hues 6/6. "
        "Sample: color0-15 swatches, then colours 1-6, bright 9-14, colour 8, diff and ls lines.</p>"
        + "".join(body)
    )


def print_table(console: Console, baseline: Entry, entries: list[Entry]) -> None:
    table = Table(
        title="palette-compare (tc fails at the --min ratio)", title_justify="left"
    )
    for col in (
        "picture",
        "setting",
        "tc fails",
        "fg/bg",
        "accent min",
        "distinct",
        "hues",
    ):
        table.add_column(col)
    for e in [baseline, *entries]:
        if e.error:
            table.add_row(
                Path(e.picture).parent.name,
                e.setting,
                "[red]error[/red]",
                "",
                "",
                "",
                "",
            )
            continue
        s = e.score
        table.add_row(Path(e.picture).parent.name if e.picture else "-", e.setting,
                      str(s.tc_fails), f"{s.fg_bg:.2f}", f"{s.accent_min:.2f}",
                      f"{s.distinct:.1f}", f"{s.hues}/6")  # fmt: skip
    console.print(table)


def amo_pictures() -> list[Path]:
    out = subprocess.run(
        ["amo", "list"], check=True, text=True, capture_output=True
    ).stdout
    return [Path(line) for line in out.splitlines() if line.strip()]


def main() -> None:
    args = get_cli_arguments()
    setup_logger(args)
    settings = [s.strip() for s in args.settings.split(",") if s.strip()]
    unknown = [s for s in settings if s not in SETTINGS]
    if unknown:
        sys.exit(
            f"palette-compare: unknown setting(s) {', '.join(unknown)}; known: {', '.join(SETTINGS)}"
        )
    pictures = [p.expanduser().resolve() for p in args.pictures] or amo_pictures()
    if not pictures:
        sys.exit("palette-compare: no pictures (amo list is empty)")

    tc = load_term_contrast()
    styles = [style for name in TC_SOURCES for style in tc.SOURCES[name]()]
    args.out.mkdir(parents=True, exist_ok=True)

    live = tc.load_palette(tc.KITTY_CONF, "live kitty")
    baseline = Entry("", "live kitty (Blazer)", tc.hexs(live.background), tc.hexs(live.foreground),
                     [tc.hexs(c) for c in live.colors], score(tc, styles, live, args.min))  # fmt: skip

    entries: list[Entry] = []
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        env = os.environ | {
            "XDG_CONFIG_HOME": str(work / "config"),
            "XDG_CACHE_HOME": str(work / "cache"),
        }
        for picture, setting in itertools.product(pictures, settings):
            logger.info("%s: %s", picture.parent.name, setting)
            try:
                data = generate(setting, picture, work, env)
            except (subprocess.CalledProcessError, KeyError, ValueError) as e:
                detail = (
                    e.stderr.strip().splitlines()[-1]
                    if isinstance(e, subprocess.CalledProcessError) and e.stderr
                    else str(e)
                )
                logger.error("%s: %s failed: %s", picture.parent.name, setting, detail)
                entries.append(Entry(str(picture), setting, "", "", [], error=detail))
                continue
            conf = args.out / f"{picture.stem}.{setting}.conf"
            write_conf(conf, data)
            palette = tc.load_palette(conf, f"{picture.stem} {setting}")
            entries.append(Entry(str(picture), setting, data["background"], data["foreground"],
                                 data["colors"], score(tc, styles, palette, args.min)))  # fmt: skip

    (args.out / "summary.json").write_text(
        json.dumps([asdict(e) for e in [baseline, *entries]], indent=2) + "\n"
    )
    write_html(args.out / "index.html", baseline, entries, pictures)
    print_table(Console(), baseline, entries)
    logger.info("contact sheet: %s", args.out / "index.html")


if __name__ == "__main__":
    main()
