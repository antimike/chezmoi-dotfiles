---
summary: Failsafe runbook for display manager, greeter and compositor changes: preparation, safe test procedure, symptom-by-symptom recovery, rollback
status: current (written before any DM/greeter change; update after the first real use)
updated: 2026-10-25
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
| Hyprland: screens black, or no way to exit | A bad `~/.config/hypr/hyprland.lua`, or the GPU order (Intel first by default, D60; NVIDIA first only with `hyprland_render_gpu: nvidia`) | Keys: `$mod+Shift+Ctrl+e` runs `uwsm stop`. Otherwise `Ctrl+Alt+F3`, log in, `loginctl terminate-user $USER`, pick GNOME or SwayFX. `journalctl --user -b -u 'wayland-wm@*'`; `Hyprland --verify-config -c ~/.config/hypr/hyprland.lua` checks the config; `chezmoi apply --override-data '{"hyprland_render_gpu":"intel"}' ~/.config/uwsm/env-hyprland` restores Intel first for the next Hyprland login |
| Hyprland (riced) crashes, freezes or looks wrong; "Hyprland plugins skipped" notification | A compositor plugin (D66: plugins load in the riced profile, and in work only when promoted); or the plugins were built for an older Hyprland (skipped, not loaded) | Log into **Hyprland (work)** instead: no unpromoted plugin loads there. Crash report: `~/.cache/hyprland/hyprlandCrashReport<pid>.txt` (a plugin's `.so` in the backtrace names it); `coredumpctl list Hyprland`. Drop the plugin from its `profiles` in `.chezmoidata/hyprland.yaml` and `chezmoi apply`. After a Hyprland update: `chezmoi apply` in a terminal of a fresh Hyprland session rebuilds, then `hyprctl reload`. Triage a plugin without risking the session: `tools/hypr-nested` |
| After a resume while docked: externals black (only the panel shows the lock screen), or the whole display freezes after replugging them; `Ctrl+Alt+F3` does nothing | NVIDIA's display engine after a docked resume (2026-10-23; `nvidia-drm … semsurf`, then `Flip event timeout`); D61 now blocks docked suspends | Do **not** replug the monitors: save work on the panel and log out. If frozen (the kernel usually still runs): **SysRq REISUB**, the clean way: hold **Alt**; press and release **Fn+Home** (the built-in keyboard's SysRq) while still holding Alt; then press **R**, **E**, **I**, **S**, **U**, **B** a second or two apart, still holding Alt (holding Fn+Home and the letter together does not register on this keyboard; tested 2026-10-23). Needs `kernel.sysrq` 244 or more (252 since 2026-11-10), installed by chezmoi. For a full freeze, see "Hard freeze triage" below. Holding the power key is a **hard** power-off on zbook (HP's firmware, ~5 s; logind cannot see a long press: tested 2026-10-23), so only as a last resort. `sshd` is off (deferred). Afterwards: `journalctl -b -1 -k | grep -E 'semsurf|Flip event'`; [nvidia-driver.md](nvidia-driver.md). |
| Session starts but no bar, notifications, lock | Helper units not started; or a compositor started without uwsm (a non-uwsm GDM entry: `systemctl --user list-units 'wayland-wm*'` is empty; those entries are hidden since 2026-10-25) | `systemctl --user status wm-helpers-wayland.target`, `systemctl --user --failed`. |
| Cannot unlock the lock screen | Locker crashed (Sway shows a solid red screen and stays locked) or PAM issue | From a console, start a new locker in the session and unlock with it: `SWAYSOCK=$(ls /run/user/$UID/sway-ipc.*.sock) swaymsg exec swaylock`. Last resort: `loginctl terminate-session <id>` (loses the session). |
| Cannot unlock hyprlock (Hyprland) | PAM issue, or hyprlock hung | From a console (`Ctrl+Alt+F3`, log in): `pkill -USR1 hyprlock` unlocks the session (tested on a headless sway, `tools/lock-screen-test`). If hyprlock crashed instead (Hyprland's "lockscreen app died" screen), log out from the console: `loginctl terminate-session <id>`. hyprlock's log: `$XDG_RUNTIME_DIR/lock-screen-hyprlock.log`. |
| Login loop on every session (including GNOME) | Home permissions, full disk, or a shell profile that exits/errors | Console: `df -h ~`, check `~/.zprofile`/`~/.profile` for errors (`zsh -lc true`), `ls -ld ~`. |
| Password rejected only in the greeter | PAM change (e.g. pam-u2f) | Console login (if it works there, the greeter's PAM file differs); `sudo etckeeper` rollback of `/etc/pam.d`. |
| Nothing boots to a login at all | | Fedora live USB, mount the root filesystem, revert `/etc` with etckeeper (`git -C /mnt/etc log`/`checkout`) or re-enable GDM with `ln -sf /usr/lib/systemd/system/gdm.service /mnt/etc/systemd/system/display-manager.service`. |

## Hard freeze triage

For a freeze where nothing on screen responds: no key binds, no `Ctrl+Alt+F3`, mouse frozen (2026-11-05 and
2026-11-10, both docked Hyprland; chz-42c). The goal is evidence for the next time, so do the steps in order and
**write down what happened at each one**.

1. **Is the kernel alive?** Ping zbook from the phone. zbook's wired address (192.168.8.x, behind the GL-AR750S) is not
   reachable from the home Wi-Fi (double NAT, the router's own Wi-Fi is off: [home-network.md](home-network.md)), but
   zbook's Wi-Fi stays joined to the home AP as the fallback route, so ping that address. Find it in the home AP's app
   (client list), or note it ahead of time: `ip -4 -br addr show wlp112s0` (DHCP, so it can change). Answers = the
   kernel and network stack run, the display stack is wedged. No answer = a deeper hang (or the Wi-Fi is down; not
   conclusive alone). Not yet tested.
2. **SysRq dumps, then a clean reboot.** Hold **Alt**, tap **Fn+Home** (the built-in keyboard's SysRq), keep holding
   Alt, then press each letter a second or two apart:
   - **W**: blocked (D-state) tasks; **L**: backtraces of all CPUs (`kernel.sysrq=252` allows both, since 2026-11-10;
     244 did not).
   - **S** (sync), wait ~5 s, then **B** (reboot); or the full **R E I S U B** after W and L.
   - **No reaction to S/B either** (no disk light, no reboot) = the kernel is hard-hung: write it down, then hold the
     power key (a hard power-off on zbook).
   - A detected soft or hard lockup panics and reboots by itself after 10 s (`kernel.softlockup_panic`,
     `hardlockup_panic`, `panic=10`), so a reboot nobody asked for after a freeze is that.
3. **After the reboot**, collect (newest boot is `-b -1` from the frozen one):
   - `journalctl -b -1 -k | grep -A50 -i sysrq`: the W/L dumps, if the S sync got them to disk.
   - `sudo ls -l /var/lib/systemd/pstore/`: the kernel log at a panic or oops (EFI pstore, since 2026-11-10; empty
     after a freeze that never panicked).
   - `journalctl -b -1 -n 50 -o short-precise`: the last lines before the freeze (journald syncs every 15 s now).
   - `~/.cache/hyprland/` (crash reports), `coredumpctl list`.
   - Hyprland's own log in the journal: chz-mfl. mongod's AVC flood used to bury everything: chz-8jq.
4. Record the findings on chz-42c's follow-up (or a new bead): time, docked or not, which step answered.

**pstore risk notes** (MH, 2026-11-10): the kernel writes the EFI variables only at a panic or oops (~10 KB each);
`systemd-pstore` moves them into `/var/lib/systemd/pstore/` at the next boot and deletes them from NVRAM. Watch for
firmware trouble (setup or boot menu misbehaving, boot entries lost): undo with `sudo grubby --update-kernel=ALL
--remove-args=efi_pstore.pstore_disable=0` (and drop it from `/etc/default/grub`), or the HP BIOS's NVRAM reset. Until
the next boot, a crash log sits in NVRAM outside LUKS (kernel addresses, device IDs, paths from audit lines). kdump is
declined for now (reserved RAM, LUKS + btrfs capture initramfs, debuginfo); add it only if pstore captures are too thin.

## System-level installs

Everything chezmoi's installers have put outside `$HOME`, and how to remove it. Paths are the zbook ones from
2026-10-17; another host may differ (for example, no `--unsupported-gpu` without the nvidia driver, no `dgpu` link on
a single-GPU host). The per-host records in the fourth column are the truth for this machine. A managed
`chezmoi-system` command to list and undo these is planned ([../open-items.md](../open-items.md)).

| What | Installed by | System paths | Per-host record | Undo |
|---|---|---|---|---|
| GPU symlinks `/dev/dri/igpu`, `dgpu` | `run_onchange_install-udev-dri-symlinks.sh.tmpl` | `/etc/udev/rules.d/61-dri-stable-names.rules` | staged copy in `~/.local/state/chezmoi-system/`; etckeeper | `sudo rm` the rule, `sudo udevadm control --reload` (or etckeeper checkout) |
| COPR repos `swayfx/swayfx`, `sdegler/hyprland` (D45) | `run_onchange_install-packages.sh.tmpl` (`coprs`) | `/etc/yum.repos.d/_copr:copr.fedorainfracloud.org:<owner>:<project>.repo` | etckeeper | `sudo dnf copr remove <owner>/<project>` (after removing its packages) |
| Wayland packages (`packages.yaml`, target `wayland`) | `run_onchange_install-packages.sh.tmpl` | rpm-managed | `dnf history` (transaction 19 on zbook) | `sudo dnf history undo 19`, or `dnf remove` selected packages; `sudo dnf swap swayfx sway` keeps a Sway |
| uwsm 0.27.0 and the uwsm GDM entries | `run_onchange_install-uwsm.sh.tmpl` | `/usr/local/{bin,libexec/uwsm,lib/systemd/user,share/uwsm,share/wayland-sessions,share/man,share/doc/uwsm,share/licenses/uwsm}` (51 paths) | `~/.local/state/chezmoi-system/uwsm/v0.27.0/files.txt` | `sudo sh ~/.local/state/chezmoi-system/uwsm/v0.27.0/uninstall.sh` |
| User lingering | `run_onchange_after_enable-linger.sh.tmpl` | `/var/lib/systemd/linger/<user>` | `loginctl show-user <user> -p Linger` | `loginctl disable-linger` |
| logind lid and power key | `run_onchange_install-logind-power.sh.tmpl` | `/etc/systemd/logind.conf.d/50-chezmoi-power.conf` | staged copy in `~/.local/state/chezmoi-system/`; etckeeper | `sudo rm` it, `sudo systemctl reload systemd-logind` |
| SysRq mask 252 (REISUB + W/L/T/M dumps) | `run_onchange_install-sysrq.sh.tmpl` | `/etc/sysctl.d/90-sysrq.conf` | staged copy in `~/.local/state/chezmoi-system/`; etckeeper; `cat /proc/sys/kernel/sysrq` | `sudo rm` it, `sudo sysctl kernel.sysrq=16` |
| Lockup panics, journald sync, EFI pstore (chz-42c) | `run_onchange_install-freeze-diagnostics.sh.tmpl` | `/etc/sysctl.d/91-freeze-panic.conf`, `/etc/systemd/journald.conf.d/50-chezmoi-sync.conf`, `systemd-pstore.service` enabled, kernel argument `efi_pstore.pstore_disable=0` (every BLS entry and `/etc/default/grub`) | staged copies in `~/.local/state/chezmoi-system/`; etckeeper; `sysctl kernel.panic`, `systemctl is-enabled systemd-pstore`, `cat /proc/cmdline` | `sudo rm` both files, `sudo sysctl kernel.softlockup_panic=0 kernel.hardlockup_panic=0 kernel.panic=0`, `sudo systemctl reload systemd-journald`, `sudo systemctl disable systemd-pstore`, `sudo grubby --update-kernel=ALL --remove-args=efi_pstore.pstore_disable=0` |
| hyprpm headers and plugin builds (D66) | `run_after_hyprpm-plugins.sh.tmpl` (hyprpm, sudo) | `/var/cache/hyprpm/<user>/` (headers, repos, `.so` files) | stamp `~/.local/state/chezmoi-system/hyprpm/built-for`; `hyprpm list` | `hyprpm remove <url>` per repo, `hyprpm purge-cache`, `rm` the stamp |
| "Hyprland (riced)" session entry (D66) | `run_onchange_install-uwsm.sh.tmpl` (`.chezmoidata/uwsm.yaml` sessions) | `/usr/local/share/wayland-sessions/hyprland-riced-uwsm.desktop` | uwsm's `files.txt` (the uwsm row) | drop it from `uwsm.yaml` and apply, or the uwsm uninstall |

Removing uwsm or a compositor package never affects the GNOME session; the rollback card below is for login problems.

## Rollback card

```
Ctrl+Alt+F3  -> log in with the password
               (YubiKey/SSH prompts appear here as curses; back in the GUI run  sshstart)
sudo systemctl enable --force gdm && sudo reboot
GRUB: e, add  systemd.unit=multi-user.target  to the linux line, Ctrl+X
sudo etckeeper vcs log --oneline   # then checkout the changed files
```
