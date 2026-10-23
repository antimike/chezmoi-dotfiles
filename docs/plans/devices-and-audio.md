---
summary: Design and review pass for audio (PipeWire/WirePlumber, media control) and device hotplug (monitors, audio outputs, Bluetooth, removable drives, Wi-Fi) on the Wayland desktop
status: planned; design review first, no config changed
updated: 2026-10-23
---

# Devices and audio plan

Part of the SwayFX daily driver ([wayland-desktop.md](wayland-desktop.md), step 5). Compositor-agnostic where possible:
helpers run under the shared `wm-helpers-wayland.target`. **Goal (MH, 2026-10-17):** as much automatic device handling
as possible; pickers (rofi or fuzzel) for the cases that need a choice. MH had trouble getting audio right on a previous
machine and settled on playerctl; the ecosystem has moved since, so this starts with a review.

## Current state (checked 2026-10-17)

- Audio: PipeWire 1.6.7 + WirePlumber 0.5.14 + `pipewire-pulseaudio` (Fedora default). `easyeffects` config is in
  chezmoi; the i3 config has a `pulsemixer` exec entry (`home/.chezmoitemplates/i3/exec.d/pulsemixer.yaml`).
- `playerctl` is **not installed**, though the i3 media keys call it.
- Bluetooth: bluez 5.86; no GUI or picker installed (`blueman` 2.4.6 is in Fedora updates).
- Removable media: `udisks2` and `udiskie` 2.6.2 installed.
- Network: NetworkManager 1.56, `nm-applet` installed; a `networkmanager-dmenu` config is in chezmoi.
- MH's older tooling in `~/Source/antimike/i3-config-mbp/bin/`: `set-pulseaudio-volume.bash`, `misc/set-player-volume.bash`,
  `widgets/rofi-mediaplayer`, `widgets/rofi-wifi`; playerctl examples in `antimike/i3-python`.

## Audio

| Layer | Current standard | Notes |
|---|---|---|
| Server | PipeWire + WirePlumber 0.5 | WirePlumber 0.5 config is SPA-JSON (`~/.config/wireplumber/wireplumber.conf.d/*.conf`), replacing 0.4's Lua; old guides are often wrong. |
| Volume / default device CLI | `wpctl` (WirePlumber) | `pactl` still works through pipewire-pulse; prefer `wpctl` in new scripts. |
| Mixer UI | `pavucontrol` 6.2 (GTK4); `pwvucontrol` (not packaged); `pulsemixer` (TUI) | |
| Graph / routing | `qpwgraph`, `helvum` | Debugging only. |
| Media control | **playerctl** (MPRIS) + `playerctld` daemon (tracks the most recently active player) | Still the standard; waybar's `mpris` module shows the current player. Replaces the fixed `$mediaplayer cmus` in the i3 config. |
| Effects | easyeffects 8.2 (config already in chezmoi) | |

**Auto-switching outputs:**
- **Aux cable in the headphone jack:** on most laptops the jack is a *port* of the same ALSA card as the speakers, and
  WirePlumber switches ports on jack detection by itself. Check on zbook with `wpctl status` before and after plugging.
  If the jack shows as a separate sink, add a WirePlumber priority rule.
- **New USB or Bluetooth audio device becomes the default:** pipewire-pulse can load `module-switch-on-connect`
  (configured in `pipewire-pulse.conf.d`); WirePlumber otherwise restores the last user choice. Check it on zbook.
- Volume/mute keys run `wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%+` (and so on) and feed the OSD.

## Monitors

- **Known monitors:** kanshi profiles, matched by make/model/serial, set mode, position, scale and which workspaces go
  where (kanshi's `exec` can run `swaymsg` commands).
- **Unknown monitors:** a final kanshi profile with a `*` output criterion (enable at the preferred mode, place right
  of the laptop panel). A script then saves the current layout as a new kanshi profile, after any manual arrangement in
  `wdisplays`.
- niri and Hyprland have their own output config (Hyprland: `monitor = , preferred, auto, 1` as the fallback); kanshi
  may not be needed there.
- **GPU wiring matters:** on zbook some external ports are on the NVIDIA card (see "GPUs" in
  [wayland-desktop.md](wayland-desktop.md)). Monitors on those ports need the NVIDIA DRM device in the compositor's
  device list.

## Bluetooth

- **Known devices:** pair and `trust` once; bluez reconnects trusted devices when they announce themselves. Set
  `AutoEnable=true` (`/etc/bluetooth/main.conf`, system-level) so the adapter powers on at boot. Audio profiles are
  WirePlumber's job.
- **New devices:** a rofi/fuzzel picker over `bluetoothctl` (scan, pair, trust, connect). Small community scripts exist
  (for example `rofi-bluetooth`, not packaged); writing our own around `bluetoothctl` is about as much work and fits the
  theming. `blueman` provides a tray applet as a fallback.

## Removable drives

- `udiskie` (installed) as a session unit: automount plus notifications, mounting through udisks2 to
  `/run/media/$USER/<label>`. Symlink a designated directory (for example `~/media`) to it.
- **Known drives at fixed paths:** udisks can't choose mount points per device. Options:
  - `/etc/fstab` entries by UUID with `noauto,nofail,x-udisks-auth` and a chosen mount point (system-level, via a sudo installer);
  - or a udev rule.
- **Unknown drives: notify, then mount (MH, 2026-10-17; D43).** Automounting unknown drives would mount untrusted
  filesystems. udiskie runs with automount off for them and shows a notification with a mount action; known drives
  (by UUID) mount automatically at their fixed paths. udisks mounts with `nosuid,nodev` either way.

## Wi-Fi

- `networkmanager-dmenu` (config already in chezmoi) supports rofi and fuzzel: connect, VPN, toggles. Check it is
  installed; compare with MH's `rofi-wifi` script.
- `nm-applet --indicator` for the waybar tray, **only if the nm-applet lag test clears it** (open item; see
  [../runbooks/home-network.md](../runbooks/home-network.md) and the bar item in [wayland-desktop.md](wayland-desktop.md)).

## Steps (not scheduled)

1. Review: `wpctl status` on zbook (jack, HDMI audio, Bluetooth), current WirePlumber state; decide the auto-switch rules.
2. playerctl + playerctld, media keys, waybar `mpris`.
3. kanshi profiles + the unknown-monitor fallback + "save layout as profile" script.
4. Bluetooth picker; `AutoEnable`.
5. udiskie unit (notify-then-mount for unknown drives, D43) + fixed paths for known drives.
6. Wi-Fi picker (networkmanager-dmenu), tray applet.
