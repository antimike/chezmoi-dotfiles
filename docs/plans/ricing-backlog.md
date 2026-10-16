---
summary: Backlog of non-essential zbook improvements (ricing, security, resume) with done/open state
status: living checklist
updated: 2026-10-15
---

# Backlog (aesthetic and quality-of-life work)

Merged from MH's scratch notes; "[x]" = done as part of the Claude Code migration ([../log/migration-steps.md](../log/migration-steps.md)).
Sway work has its own plan: [sway.md](sway.md).

## Claude tooling
- [x] Editor preferences (vi mode), skills, home-rolled tooling (`bd-track`), beads install (dolt, uv, bun, bd)
- [x] Migrate Claude projects to new repos; review and migrate project memory
- [ ] Plugins: evaluate claude-mem and other memory plugins (deferred; see [../open-items.md](../open-items.md))
- [ ] Assess whether beads is still the best tool, and recent changes affecting configuration
- [ ] `claude-sandbox` repo: clone and set up (`claude-config` is done)

## Ricing
- [ ] Background images (systemd timer exists for the X11 session; Wayland version in [sway.md](sway.md))
- [ ] Neovim config migration (part of [boco-merge.md](boco-merge.md), Phase 2)
- [ ] Wayland-compatible i3 replacement: Sway ([sway.md](sway.md))
- [ ] Compositor, status bar / tray, notification daemon (dunst chosen)
- [ ] Kitty config update and assessment
- [ ] Investigate browser options
- [ ] Nix config derivations (exploration notes exist in the reference clone's `docs/`)

## Permissions and security
- [ ] Passwordless `sudo` with the YubiKey
- [ ] New SSH keys for GitHub and other services (GitHub already works via the YubiKey; others open)
- [ ] Review contents of GPG backups; see also [../runbooks/gpg-and-signing.md](../runbooks/gpg-and-signing.md)

## Chezmoi
- [x] Migration branch work merged to `main` (D26 in [../decisions.md](../decisions.md))
- [ ] Templatize all machine-specific logic ([boco-merge.md](boco-merge.md) Guards)

## Resume
- [x] Resume repos cloned and pushed
- [ ] Assess and begin building out the new resume
