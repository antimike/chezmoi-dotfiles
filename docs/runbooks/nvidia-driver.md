---
summary: NVIDIA driver on zbook: current state, the deferred 595 -> 615 upgrade (trade-offs, procedure, checks) and rollback
status: current (upgrade planned, not done)
updated: 2026-10-23
---

# NVIDIA driver

Read [display-session-recovery.md](display-session-recovery.md) first: its rollback card (console login, multi-user
boot) is the way back if the graphical session does not start.

## Current state (checked 2026-10-23)
- Quadro T1000 (Turing), proprietary driver **595.80** from **RPM Fusion nonfree** (`akmod-nvidia`,
  `xorg-x11-drv-nvidia*`; first installed by `dnf` transaction 7, 2026-06-20). akmods builds the kernel module
  locally for each kernel and signs it for **Secure Boot** (enabled) with the local MOK key (`modinfo -F signer
  nvidia`: `zbook-…`).
- Kernel 7.0.12-201.fc44. The older installed kernels (6.14 fc40, 6.19 fc42) have no module for this driver, so
  booting one is **not** a driver rollback.
- `/etc/modprobe.d/nvidia.conf`: `NVreg_DynamicPowerManagement=0x02` only. `/proc/driver/nvidia/params`:
  `PreserveVideoMemoryAllocations: 2`, `TemporaryFilePath: ""`. `nvidia-suspend/resume.service` are enabled but
  skip themselves (exec condition) on this driver.
- **Known bug:** intermittent `nvidia-drm … Failed to register auto-value-update on pre-wait value for sync FD
  semaphore surface` on resume; NVIDIA-rendered clients then break (black text in kitty under SwayFX, kitty hung
  under Hyprland), and with Intel rendering the **externals stay black** after a docked resume; a replug then
  timed out NVIDIA's flips (`Flip event timeout on head 1`) and froze the display stack (2026-10-23). So D61: no
  suspend while docked. Detail and counts: [../open-items.md](../open-items.md), "black text in kitty".
- Available: **615.78.08** in `rpmfusion-nonfree-updates` (a new branch, not a point release). 595.80 is no longer
  in the repos; the only older build left is **595.58.03** (`rpmfusion-nonfree`, the Fedora 44 release repo).

## Plan: upgrade 595.80 -> 615.x (deferred, MH 2026-10-23)
**When:** deferred by MH (2026-10-23): the last NVIDIA upgrade on this machine was very disruptive and had to be
rolled back, and D61 (no suspend while docked) is acceptable meanwhile. Not urgent unless a security fix applies:
check NVIDIA's security bulletins for the 595 branch before deciding (not checked yet). Do it as a change of its own, so a fix or regression can be put on the right cause. At a quiet time, not before
something important.

**Trade-offs** (Claude, 2026-10-23):
- For: NVIDIA ships security fixes several times a year; recent branches are where Wayland explicit-sync and
  suspend fixes land, so 615 may fix the sync-FD bug (not checked: read the 615 release notes first; if they list
  the bug, the upgrade moves up the queue).
- Against "always latest": new NVIDIA branches often fix one Wayland/suspend bug and add another; the module is
  rebuilt per kernel, so a bad driver/kernel pair can leave the NVIDIA card (and the externals, which are all on
  it, D53) unusable until fixed. Recoverable (below), but not free.
- Rule: take driver updates **through RPM Fusion only** (never NVIDIA's `.run` installer, which fights the
  packages), and treat a **branch** change as a tested change, not a routine update.

**Until then: keep routine upgrades from pulling 615.** A plain `sudo dnf upgrade` installs it today. Either
exclude it each time (`sudo dnf upgrade --exclude='*nvidia*'`), or lock the version (dnf5's built-in versionlock):
`sudo dnf versionlock add 'akmod-nvidia' 'xorg-x11-drv-nvidia*' 'nvidia-*'`, undone with `sudo dnf versionlock
delete …` before the upgrade (`sudo dnf versionlock list` shows the locks). Kernel updates still need a module
build for 595.80; akmods does that at boot, and the package must stay installed for it.

**Procedure:**
1. `sudo etckeeper commit "before nvidia 615"`; note `dnf history list | head -3`.
2. Read the 615 release notes (suspend, explicit sync, Turing regressions).
3. Remove the version lock if set; `sudo dnf upgrade --refresh 'akmod-nvidia' 'xorg-x11-drv-nvidia*' 'nvidia-*'`.
4. Wait for the module build: `sudo akmods --force` if unsure; then `modinfo -F version nvidia` shows 615.x and
   `modinfo -F signer nvidia` the local key. Do not reboot before this.
5. Reboot. Checks: `nvidia-smi`; GDM on all screens; a docked NVIDIA-first SwayFX or Hyprland login (whichever is
   the daily driver); `sway-perf measure <label>` for a comparison with the earlier runs; several suspends while
   docked with kitty open, each followed by `journalctl -k -b | grep semsurf` and a look at kitty.
6. Record the result here and in the open item.

## Rollback
- **Session does not start, but a console does** (`Ctrl+Alt+F3`): GNOME or the Intel-only panel may still work
  (the driver failing leaves Intel). `sudo dnf history undo <id>` (the upgrade's transaction) goes back to the
  old packages only if they are still downloadable, which **595.80 is not**; so the realistic target is
  `sudo dnf downgrade 'akmod-nvidia-3:595.58.03*' 'xorg-x11-drv-nvidia*-3:595.58.03*'` (adjust to what
  `dnf list --showduplicates akmod-nvidia` offers), then `sudo akmods --force`, check `modinfo -F version
  nvidia`, reboot.
- **Module did not build or is unsigned** (`modprobe nvidia` fails; `journalctl -b -u akmods`; `dmesg | grep -i
  'module verification'`): `sudo akmods --force --kernels "$(uname -r)"`; for a key problem, `mokutil
  --list-enrolled` should show the akmods key.
- **No console either:** GRUB `e`, add `systemd.unit=multi-user.target` (rollback card in
  [display-session-recovery.md](display-session-recovery.md)), then as above.
- `/etc` changes (modprobe, if any were made): `sudo etckeeper vcs log --oneline`, then checkout.
