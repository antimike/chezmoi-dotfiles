---
summary: Parked side quest (D50): a Lua keybinding manifest with lazy.nvim-style units; MH's proposal, Claude's review, open questions
status: parked (side quest, D50); design discussion only, nothing built
updated: 2026-10-18
---

# Keybinding manifest (side quest)

Parked by [D50](../decisions.md) on 2026-10-18: the functional SwayFX daily driver comes first, and this is spare-time
work. It may replace the YAML design in [D42](../decisions.md) (all apps) and the format part of D33 (zsh); until it is
picked up again, D42 and D33 stay drafts. The YAML design it would replace is in
[wayland-desktop.md](wayland-desktop.md), "Keybinding manifest" and "i3 syntax as the manifest's language".

Its one functional goal, looking up a binding, is met in the meantime by the **cheat sheet** below, without a manifest.

## Interim: cheat sheet and `swindings`

- **Cheat sheet (main lookup tool, part of the D50 checklist):** a script reads `swaymsg -t get_config`, expands
  `set $var` lines, tracks `mode` blocks and pipes "chord → description" lines into fuzzel or rofi `-dmenu`. It reads
  the running config, so it cannot drift. Descriptions come from a comment convention in the template (e.g.
  `## Close notification` on the line above a `bindsym`); without one, the command string is shown. Parsing here is
  fine: the plan rejected parsing configs only as the *source of truth* for a manifest.
- **wlr-which-key** is a leader-key launcher (menus that run actions), not a lookup tool. Exporting the existing
  chords into it would add a second set of bindings for the same actions. Leader menus come with this side quest.
- **[`swindings`](https://github.com/sondalex/swindings)** (found by MH, 2026-10-18): a Sway keybinding browser that
  parses bindings from the config; low adoption. Worth a try, maybe a fork for MH's own needs, but not the primary
  lookup tool. Not yet evaluated. Also seen: `sway-preview-keys` (shows the current mode's bindings; not evaluated).

## MH's proposal (2026-10-18)

1. **Lua instead of YAML** for the manifest. Benefits: easier integration with the Neovim config; tables that read like
   JSON but can hold functions ("JSON plus functions", the reason Neovim uses it); access to an existing ecosystem,
   e.g. reuse or port lazy.nvim/Neovim logic to reconcile definitions, resolve dependencies and deep-merge per-package
   keymaps into one global keymap, flagging duplicates and shadowed chords as they occur. Costs: another runtime
   dependency, and the freedom of a full language can make configs harder to keep clean, not easier. Cue or Jsonnet
   were considered with similar trade-offs; Lua preferred because Neovim already needs it and its config is Lua, so
   there are fewer idioms and runtimes to know.
2. **nvim:** the "catalog only" mode for nvim in D42 is pointless: which-key already makes every nvim binding
   discoverable and searchable in the only context where they matter. nvim belongs in the manifest only if the manifest
   can drive the real nvim config. Since plugins and LazyVim define their own bindings out of sight, a compromise:
   the manifest covers only bindings the user creates in Lua files under `~/.config/nvim`, does not claim to be
   complete, and optionally a build-time check reports collisions with LazyVim or plugin bindings.
3. **A lightweight Lua "package manager" with lazy.nvim-like syntax:** packages of functionality (the "targets" of the
   package map refactor, [open-items.md](../open-items.md#detail-package-map-refactor)) with their own config;
   keybindings defined per package (a `sway` package, a `hyprland` package, ...) and deep-merged into one resolved
   keymap from the packages chosen for the host.

## Claude's review (2026-10-18)

**nvim: leave it out of the manifest entirely**, including user-defined bindings.
- Collisions inside nvim are already reported by `:checkhealth which-key` (overlapping and duplicate maps), which sees
  plugin and LazyVim bindings a manifest never would.
- The collision that matters crosses layers: kitty or the compositor grabbing a chord before nvim sees it. That needs
  only the set of chords nvim really has, from a headless `nvim_get_keymap()` dump, not nvim entries in the manifest.
- User bindings are split between `keymaps.lua` (easy to generate) and plugin specs' `keys = {}`, which also drive
  lazy-loading; generating those couples the manifest to the plugin specs.
- So the manifest covers the layers above nvim (compositor, which-key menus, kitty, zsh), and a check script compares
  them with the nvim dump.

**Lua: yes, on two conditions.** The arguments that hold: one language MH already knows; a real merge-and-check step
instead of Go templates (the plan already said to resolve outside templates); computed bindings (per-compositor
variants, families like workspaces 1-10). Functions cannot end up in a sway config, so they only help while resolving.
1. **The resolver outputs plain JSON, and every template reads only that JSON.** The JSON is the contract and the
   diffable artifact. However clever the Lua gets, its output is flat data that can be reviewed.
2. **Where the resolver runs** (chezmoi cannot read Lua as data):
   - *At render time*, `{{ output "nvim" "-l" ... | fromJson }}`. `nvim -l` gives LuaJIT (Lua 5.1, the dialect of the
     nvim config; the system `lua` is 5.4), `vim.tbl_deep_extend` and `vim.json`, and no new dependency. But a fresh
     machine has no nvim yet (mise installs it), so the first `chezmoi apply` breaks, which D48 forbids unless guarded.
   - *Before commit*, with the resolved JSON committed (**Claude's pick**): a pre-commit hook regenerates it and fails
     if it is stale; templates read it with `include`. Applying needs no Lua at all, a fresh machine cannot break,
     and the output shows in every diff. Cost: per-host conditions must be data (`targets = { "wayland" }`), not
     functions, so a Go template can filter them; the resolver checks every known host profile for conflicts.

**The "package manager": no, for now.**
- Units are worth having and cheap: a Lua file returning `{ name, targets, keys = {...} }`. lazy.nvim's merge logic is
  not worth porting (it solves plugin-spec problems this does not have); a merge that flags duplicates and shadowed
  chords is about 40 lines.
- Do not couple it to the package map refactor: one unit file declaring both packages and keys would move D32 to Lua
  too, and D32 is an unapproved draft. Leave room for a `packages = {}` field; joining them later is its own decision.

**Cue** fits the problem well (unification turns two actions on one chord into an error with no check code), but
"one language fewer" wins for a personal repo.

**Kept from the existing plan:** generate, never parse; i3 syntax as the binding notation; the per-compositor
translation table keyed on i3 command strings; seeding from the rendered i3 config; the byte-identical acceptance
check (which also covers moving `.i3.keys` out of `i3.yaml`). The open question of whether chezmoi deep-merges data
files goes away.

## Open questions (for when the side quest resumes)

1. Resolve before commit with the JSON committed (Claude's pick), or at render time via `nvim -l`?
2. nvim left out completely, with only the cross-layer collision check (Claude's pick), or MH's compromise (manifest
   generates user-defined nvim bindings)?
3. Do keybinding units and package-map targets ever share files? Needs D32 settled first.
4. Should the cheat sheet's comment convention become the manifest's `desc` field, so the side quest can seed
   descriptions from it?
