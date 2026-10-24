---
summary: Failsafe runbook for display manager, greeter and compositor changes: preparation, safe test procedure, symptom-by-symptom recovery, rollback
status: current (written before any DM/greeter change; update after the first real use)
updated: 2026-10-23
---

# Display session recovery

Read this **before** installing a compositor, changing the display manager or greeter, or changing GPU/driver
settings. MH has been locked out by such changes before. Plan: [../plans/wayland-desktop.md](../plans/wayland-desktop.md).
NVIDIA driver updates and their rollback: [nvidia-driver.md](nvidia-driver.md).

Baseline on zbook (2026-10-17): GDM is the display manager (`display-manager.service` → `gdm.service`); `lightdm` is
installed but not enabled; sessions offered: GNOME, GNOME Classic, i3; kernel cmdline has `nvidia-drm.modeset=1`.

## Before any change

1. **Confirm a text console works:** `Ctrl+Alt+F3` gives a login prompt; log in with your **password** (not only the
   YubiKey); `Ctrl+Alt+F1`/`F2` returns. If this fails, stop: fix the console first. (Checked 2026-10-17. A zsh
   login on a console points gpg-agent at it, so YubiKey PIN prompts use pinentry-curses there; run `sshstart` once
   back in the GUI, or GUI-side SSH prompts stay on the console.)
2. **Know your fallback session:** GNOME on GDM stays installed and untouched until the new setup has worked for days.
3. **Snapshot `/etc`:** `sudo etckeeper commit "before <change>"` (etckeeper is installed). Rollback is
   `sudo etckeeper vcs log` / `checkout` of the changed files.
4. **Record the baseline:** `systemctl status display-manager`, `ls /usr/share/wayland-sessions /usr/local/share/wayland-sessions`.
5. **One change per reboot:** never change the DM, PAM (e.g. pam-u2f) and GPU settings in the same step.
6. Keep this runbook readable off the machine (phone, or printed). The rollback card at the end is the minimum.
7. Optional second way in: enable `sshd` for the test day and check you can log in from the phone.

## Testing a new display manager without committing to it

Do not `systemctl enable` the new DM first. From a text console:

```
sudo systemctl stop gdm
sudo systemctl start sddm        # or greetd, ly, ...
```

If it works, log in and test each session. If anything goes wrong, from a console: `sudo systemctl stop sddm;
sudo systemctl start gdm`. Only after a successful login and logout, make it the default:
`sudo systemctl enable --force sddm` (`--force` replaces the `display-manager.service` alias). A reboot test follows.

## Symptoms and fixes

| Symptom | Likely cause | What to do |
|---|---|---|
| New session missing from the greeter | `.desktop` entry not where the greeter looks (uwsm installs to `/usr/local/share/wayland-sessions`; some greeters only read `/usr/share`) | Check both directories; check the greeter's session-path setting; GNOME is still there to log in. |
| Black screen **before** the greeter (no login screen) | DM or greeter crashed, or GPU/driver problem | `Ctrl+Alt+F3`, log in, `journalctl -b -u display-manager` (and `-u sddm`/`-u greetd`); roll back: `sudo systemctl enable --force gdm && sudo reboot`. |
| No console either | Graphics stack hangs at boot | At the GRUB menu press `e`, append `systemd.unit=multi-user.target` (or `3`) to the `linux` line, `Ctrl+X`; you get a text login; roll back from there. If GRUB is hidden, hold `Shift` or press `Esc` during boot. |
| Black screen **after** choosing a session, or straight back to the greeter | Compositor failed to start | Console: `journalctl --user -b` (uwsm: `journalctl --user -b -u 'wayland-wm@*'`); GDM also logs to `journalctl -b -u gdm`. Common causes: config error (`sway -C` validates), NVIDIA device in use without `--unsupported-gpu`, wrong `WLR_DRM_DEVICES` path. Log into GNOME meanwhile. |
| SwayFX: all screens black after logging in docked, or after undocking mid-session | NVIDIA renders docked sessions (D59); the laptop panel cannot be lit then, and an experiment in `~/.config/uwsm/env` can black out everything | Re-dock if undocked. Otherwise `Ctrl+Alt+F3` (open the lid to see it), log in, `loginctl terminate-user $USER`, pick GNOME or log in undocked. A plain `chezmoi apply --force ~/.config/uwsm/env` removes manual experiments; `prefer_nvidia_for_external: false` in `~/.config/chezmoi/chezmoi.yml` returns to Intel rendering (D53) |
| Hyprland trial: screens black, or no way to exit | Hyprland (aquamarine) with NVIDIA first (D59 env), or a bad `~/.config/hypr/hyprland.lua` | Keys: `$mod+Shift+Ctrl+e` runs `uwsm stop`. Otherwise `Ctrl+Alt+F3`, log in, `loginctl terminate-user $USER`, pick GNOME or SwayFX. `journalctl --user -b -u 'wayland-wm@*'`; `Hyprland --verify-config -c ~/.config/hypr/hyprland.lua` checks the config; `touch ~/.local/state/hyprland-intel-first` puts Intel first for the next Hyprland login |
| After a resume while docked: externals black (only the panel shows the lock screen), or the whole display freezes after replugging them; `Ctrl+Alt+F3` does nothing | NVIDIA's display engine after a docked resume (2026-10-23; `nvidia-drm … semsurf`, then `Flip event timeout`); D61 now blocks docked suspends | Do **not** replug the monitors: save work on the panel and log out. If frozen: the kernel usually still runs, but SysRq is limited to sync (`kernel.sysrq=16`) and `sshd` is off on zbook, so today only a hard power-off works (open item: enable one of them). Afterwards: `journalctl -b -1 -k | grep -E 'semsurf|Flip event'`; [nvidia-driver.md](nvidia-driver.md). |
| Session starts but no bar, notifications, lock | Helper units not started | `systemctl --user status wm-helpers-wayland.target`, `systemctl --user --failed`. |
| Cannot unlock the lock screen | Locker crashed (Sway shows a solid red screen and stays locked) or PAM issue | From a console, start a new locker in the session and unlock with it: `SWAYSOCK=$(ls /run/user/$UID/sway-ipc.*.sock) swaymsg exec swaylock`. Last resort: `loginctl terminate-session <id>` (loses the session). |
| Login loop on every session (including GNOME) | Home permissions, full disk, or a shell profile that exits/errors | Console: `df -h ~`, check `~/.zprofile`/`~/.profile` for errors (`zsh -lc true`), `ls -ld ~`. |
| Password rejected only in the greeter | PAM change (e.g. pam-u2f) | Console login (if it works there, the greeter's PAM file differs); `sudo etckeeper` rollback of `/etc/pam.d`. |
| Nothing boots to a login at all | | Fedora live USB, mount the root filesystem, revert `/etc` with etckeeper (`git -C /mnt/etc log`/`checkout`) or re-enable GDM with `ln -sf /usr/lib/systemd/system/gdm.service /mnt/etc/systemd/system/display-manager.service`. |

## System-level installs

Everything chezmoi's installers have put outside `$HOME`, and how to remove it. Paths are the zbook ones from
2026-10-17; another host may differ (for example, no `--unsupported-gpu` without the nvidia driver, no `dgpu` link on
a single-GPU host). The per-host records in the fourth column are the truth for this machine. A managed
`chezmoi-system` command to list and undo these is planned ([../open-items.md](../open-items.md)).

| What | Installed by | System paths | Per-host record | Undo |
|---|---|---|---|---|
| GPU symlinks `/dev/dri/igpu`, `dgpu` | `run_onchange_install-udev-dri-symlinks.sh.tmpl` | `/etc/udev/rules.d/61-dri-stable-names.rules` | staged copy in `~/.local/state/chezmoi-system/`; etckeeper | `sudo rm` the rule, `sudo udevadm control --reload` (or etckeeper checkout) |
| COPR repos `swayfx/swayfx`, `sdegler/hyprland` (D45) | `run_onchange_install-packages.sh.tmpl` (`coprs`) | `/etc/yum.repos.d/_copr:copr.fedorainfracloud.org:<owner>:<project>.repo` | etckeeper | `sudo dnf copr remove <owner>/<project>` (after removing its packages) |
| Wayland packages (`packagesWayland`) | `run_onchange_install-packages.sh.tmpl` | rpm-managed | `dnf history` (transaction 19 on zbook) | `sudo dnf history undo 19`, or `dnf remove` selected packages; `sudo dnf swap swayfx sway` keeps a Sway |
| uwsm 0.27.0 and the uwsm GDM entries | `run_onchange_install-uwsm.sh.tmpl` | `/usr/local/{bin,libexec/uwsm,lib/systemd/user,share/uwsm,share/wayland-sessions,share/man,share/doc/uwsm,share/licenses/uwsm}` (51 paths) | `~/.local/state/chezmoi-system/uwsm/v0.27.0/files.txt` | `sudo sh ~/.local/state/chezmoi-system/uwsm/v0.27.0/uninstall.sh` |
| User lingering | `run_onchange_after_enable-linger.sh.tmpl` | `/var/lib/systemd/linger/<user>` | `loginctl show-user <user> -p Linger` | `loginctl disable-linger` |

Removing uwsm or a compositor package never affects the GNOME session; the rollback card below is for login problems.

## Rollback card

```
Ctrl+Alt+F3  -> log in with the password
               (YubiKey/SSH prompts appear here as curses; back in the GUI run  sshstart)
sudo systemctl enable --force gdm && sudo reboot
GRUB: e, add  systemd.unit=multi-user.target  to the linux line, Ctrl+X
sudo etckeeper vcs log --oneline   # then checkout the changed files
```
