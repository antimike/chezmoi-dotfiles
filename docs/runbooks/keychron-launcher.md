---
summary: Remap keys on the Keychron Q3 Pro with the Keychron Launcher (WebHID in Chromium), the udev rule it needs, and backing up the layout
status: current
updated: 2026-10-22
---

# Keychron Launcher: remapping the Q3 Pro

The keymap lives in the keyboard's own memory. The Keychron Launcher (`launcher.keychron.com`, built on VIA) edits it
from Chromium through WebHID; no file on the computer is read at runtime. An exported layout JSON is a backup only.

## Prerequisite: raw HID access (done 2026-10-21)

By default `/dev/hidrawN` is root-only, so Chromium cannot open the keyboard. The udev rule
`/etc/udev/rules.d/70-keychron-hidraw.rules` (installed by `home/run_onchange_install-udev-keychron.sh.tmpl`, sudo on
`chezmoi apply`) gives the logged-in user access (`uaccess`) to Keychron devices, USB vendor `3434`. It matches **USB
only**: over Bluetooth the device stays root-only, which is fine because the Launcher remaps over the cable.

Check, with the cable connected: `ls -l /dev/hidraw*` and `getfacl /dev/hidrawN` for the Keychron one (find it with
`grep -l 3434 /sys/class/hidraw/*/device/uevent`) should list `user:<you>:rw-`.

## Open task: mic key → F20 (MH, when convenient)

Found 2026-10-21 (`sudo libinput debug-events --show-keycodes`): the Q3 Pro's mic-icon key sends a **Super+C macro**
(Windows dictation), not a mic key. xkb maps **F20** to `XF86AudioMicMute`, which the shared wm fragment already binds
to `~/.local/bin/volume mic-mute`, so F20 makes it work in i3 and SwayFX with no config change. The laptop keyboard's
own mic key sends `KEY_MICMUTE` and already works. (The Q3 Pro's screenshot key sends `KEY_SYSRQ`, i.e. Print; no remap
needed.)

1. Connect the keyboard with its USB cable and set its mode switch to cable.
2. In Chromium open `launcher.keychron.com`, click Connect, pick the Q3 Pro in the browser's device prompt.
   Not listed or "failed to open": check the prerequisite above.
3. In the keymap view, select the layer that matches the keyboard's Mac/Windows switch (a base and an Fn layer per
   position; the Windows layers if the key sends Super+C).
4. Click the mic key and choose **F20** (F13-F24 are usually under a "Special"/"Function" tab; otherwise enter
   `KC_F20` as a custom keycode). Changes are written to the keyboard immediately.
5. Test: press it; the mic-mute notification appears (`wpctl get-volume @DEFAULT_AUDIO_SOURCE@` shows `[MUTED]`).
   Press again to unmute.
6. Back up: export the layout JSON from the Launcher (its save/export option; assumed from VIA, not yet checked) and
   put it in the repo outside `home/` (for example `hardware/keychron-q3-pro.layout.json`; not deployed, no secrets).
7. Tick the open item in [../open-items.md](../open-items.md).

## Restoring

A reset keyboard (factory reset, firmware flash) loses the remap: import the backed-up JSON in the Launcher, or redo
step 4.
