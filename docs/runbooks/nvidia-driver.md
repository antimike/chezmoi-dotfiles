---
summary: NVIDIA driver on zbook: current state, the deferred 595 -> 615 upgrade (trade-offs, procedure, checks) and rollback
status: current (upgrade planned, not done)
updated: 2026-10-24
---

# NVIDIA driver

Read [display-session-recovery.md](display-session-recovery.md) first: its rollback card (console login, multi-user
boot) is the way back if the graphical session does not start.

## Current state (checked 2026-10-23)
- Quadro T1000 (Turing), NVIDIA driver **595.80** from **RPM Fusion nonfree** (`akmod-nvidia`,
  `xorg-x11-drv-nvidia*`; first installed by `dnf` transaction 7, 2026-06-20). The kernel module is NVIDIA's
  **open** module (`modinfo -F license nvidia`: `Dual MIT/GPL`; GSP firmware in `/lib/firmware/nvidia/595.80/`),
  so 615 (open modules only) is no module-flavour switch (checked 2026-10-24). akmods builds the kernel module
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
- **Security (checked 2026-10-23):** NVIDIA's September 2026 GPU display driver bulletin (a_id 5861) covers R595; per
  ASEC's summary (NVIDIA's page returned 403 to the fetch, so not read first-hand) the fixed Linux versions are
  **595.91.07** (R595) and **615.71.09** (R615), for CVE-2026-47511/47581/47591. **595.80 is affected**; 615.78.08 is
  fixed; RPM Fusion has no 595.91.07, and the rollback build 595.58.03 is affected too. Typically local-attack flaws
  (privilege escalation, denial of service); CVSS and vector not confirmed. Sources: NVIDIA bulletins 5861, 5821;
  asec.ahnlab.com/en/95681.
- Available: **615.78.08** in `rpmfusion-nonfree-updates` (a new branch, not a point release). 595.80 is no longer
  in the repos; the only older build left is **595.58.03** (`rpmfusion-nonfree`, the Fedora 44 release repo).

## Plan: upgrade 595.80 -> 615.x (deferred, MH 2026-10-23)
**When:** deferred by MH (2026-10-23): the last NVIDIA upgrade on this machine was very disruptive and had to be
rolled back, and D61 (no suspend while docked) is acceptable meanwhile. A security fix does apply (above):
not an emergency on a single-user laptop, so MH planned it for **2026-10-24** (a quiet day). Do it as a change of its own, so a fix or regression can be put on the right cause. At a quiet time, not before
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
1. `sudo etckeeper commit "before nvidia 615"`; note `dnf history list | head -3`. Check `sudo dnf versionlock
   list`. Then back up the installed build (next section): RPM Fusion drops superseded builds, so without it the only
   rollback target is whatever older build the release repo still has.
2. Read the 615 release notes (suspend, explicit sync, Turing regressions). **Done 2026-10-24** (secondary
   sources and NVIDIA's 615 forum thread; NVIDIA's own notes page not read): **no** mention of the sync-FD resume
   bug or explicit sync. 615.71.09: `NVreg_UseKernelSuspendNotifiers=1` **on by default** (a different suspend
   path; the likeliest thing to change docked-resume behaviour, either way), a fix for resume after a hibernate,
   open kernel modules only. 615.78.08 (2026-10-07): SELinux/systemd-suspend handling in `nvidia.ko`, >2 GiB page
   tables, a Wayland HDR-metadata crash, Vulkan latency. No Turing or hybrid-laptop regressions reported in the
   thread. The upgrade set resolves to 615.78.08 for every installed package plus a new `nvidia-kmod-common`
   (provided by `xorg-x11-drv-nvidia`).
3. Remove the version lock if set; `sudo dnf upgrade --refresh 'akmod-nvidia' 'xorg-x11-drv-nvidia*' 'nvidia-*'`.
4. Wait for the module build: `sudo akmods --force` if unsure; then `modinfo -F version nvidia` shows 615.x and
   `modinfo -F signer nvidia` the local key. Do not reboot before this.
5. Reboot. Checks: `nvidia-smi`; GDM on all screens; a docked NVIDIA-first SwayFX or Hyprland login (whichever is
   the daily driver); `sway-perf measure <label>` for a comparison with the earlier runs; several suspends while
   docked with kitty open, each followed by `journalctl -k -b | grep semsurf` and a look at kitty.
6. Record the result here and in the open item.

## Backup of the installed build (done 2026-10-24 for 595.80)
`rpmrebuild` (Fedora repo) repackages installed packages from the rpm database and the files on disk; the
akmods-built kernel module RPM is already kept in `/var/cache/akmods/nvidia/`. Commands as run on 2026-10-24
(dnf transaction 28 installed `rpmrebuild-2.21-2.fc44`; the rest as the user, no sudo):

```
sudo dnf install -y rpmrebuild
mkdir -p ~/.local/state/nvidia-rollback/595.80
cd ~/.local/state/nvidia-rollback/595.80
# installed set, for the record
rpm -qa --qf '%{nevra}\n' | grep -E '^(akmod-nvidia|nvidia-|xorg-x11-drv-nvidia)' | sort > packages.txt
# no output = every file matches its package, so the rebuilt RPMs carry the original contents
rpm -V $(cat packages.txt)
# x86_64 packages (nvidia-modprobe was rebuilt first, alone, as a test, with the same rpmrebuild command)
for p in $(rpm -qa --qf '%{name}-%{version}-%{release}.%{arch}\n' | grep -E '^(akmod-nvidia|nvidia-|xorg-x11-drv-nvidia)' | grep -v '^nvidia-modprobe' | sort); do rpmrebuild --batch --directory="$PWD" "$p" > "rebuild-$p.log" 2>&1 && echo "ok $p" || echo "FAIL $p"; done
# the kernel module, as akmods built it
cp -p /var/cache/akmods/nvidia/kmod-nvidia-7.0.12-201.fc44.x86_64-595.80-1.fc44.x86_64.rpm x86_64/
# i686 packages: rpm 6.0.1 lists no i686 among its compatible build archs, so drop the spec's BuildArch and pass
# --target (setarch i686, or --target alone, both fail with "No compatible architectures found for build")
for p in xorg-x11-drv-nvidia-cuda-libs-595.80-1.fc44.i686 xorg-x11-drv-nvidia-libs-595.80-1.fc44.i686; do rpmrebuild --batch --change-spec-preamble='sed -e "/^BuildArch:/d"' --additional=--target=i686 --directory="$PWD" "$p" > "rebuild-$p.log" 2>&1 && echo "ok $p" || echo "FAIL $p"; done
# check: each RPM's file digests, modes and paths equal the installed package's
for f in x86_64/*.rpm i686/*.rpm; do nevra=$(rpm -qp --qf '%{name}-%{version}-%{release}.%{arch}' "$f" 2>/dev/null); a=$(rpm -qp --qf '[%{filedigests} %{filemodes} %{filenames}\n]' "$f" 2>/dev/null | sort | sha256sum); b=$(rpm -q --qf '[%{filedigests} %{filemodes} %{filenames}\n]' "$nevra" | sort | sha256sum); [ "$a" = "$b" ] && echo "match $nevra" || echo "DIFF $nevra"; done
sha256sum x86_64/*.rpm i686/*.rpm > SHA256SUMS
```

Result: 14 RPMs (389 MB; 12 x86_64 incl. the kmod, 2 i686), all `match`; Epoch 3 kept; scriptlets identical; the
only `Requires` difference is explicit `/bin/sh` lines for the scriptlets (harmless). The RPMs are unsigned
(`localpkg_gpgcheck = 0` on this host, so dnf installs them). The kmod RPM only fits kernel 7.0.12-201; for
another kernel, akmods rebuilds it from the restored `akmod-nvidia` + `kmodsrc`. For a later build, replace
`595.80` and the kmod file name.

## Rollback
- **Session does not start, but a console does** (`Ctrl+Alt+F3`): GNOME or the Intel-only panel may still work
  (the driver failing leaves Intel). **First choice: the local 595.80 backup** (section above):
  `cd ~/.local/state/nvidia-rollback/595.80 && sha256sum -c SHA256SUMS && sudo dnf downgrade ./x86_64/*.rpm
  ./i686/*.rpm`, then `modinfo -F version nvidia` (595.80), reboot. Packages 615 added that 595.80 lacks (e.g.
  `nvidia-kmod-common`) may then need `sudo dnf remove`. `sudo dnf history undo <id>` (the upgrade's transaction)
  goes back to the old packages only if they are still downloadable, which **595.80 is not**; without the backup the
  target is
  `sudo dnf downgrade 'akmod-nvidia-3:595.58.03*' 'xorg-x11-drv-nvidia*-3:595.58.03*'` (adjust to what
  `dnf list --showduplicates akmod-nvidia` offers), then `sudo akmods --force`, check `modinfo -F version
  nvidia`, reboot.
- **Module did not build or is unsigned** (`modprobe nvidia` fails; `journalctl -b -u akmods`; `dmesg | grep -i
  'module verification'`): `sudo akmods --force --kernels "$(uname -r)"`; for a key problem, `mokutil
  --list-enrolled` should show the akmods key.
- **No console either:** GRUB `e`, add `systemd.unit=multi-user.target` (rollback card in
  [display-session-recovery.md](display-session-recovery.md)), then as above.
- `/etc` changes (modprobe, if any were made): `sudo etckeeper vcs log --oneline`, then checkout.
