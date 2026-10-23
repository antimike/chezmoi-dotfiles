---
summary: zbook's home network (wired through a GL-AR750S repeater, Wi-Fi fallback), the router's firmware history and pitfalls, NetworkManager commands, and how to diagnose a slow link
status: current
updated: 2026-10-23
---

# Home network

Source: MH's router session of 2026-10-22/23 (report `~/router-session-report.10232026.md`, unmanaged; it holds the
exact BSSIDs, MACs and ISP addresses, which stay out of this public repo). Confirmed facts unless marked
**hypothesis**. Decisions: D55-D57 in [../decisions.md](../decisions.md). Open work: [../open-items.md](../open-items.md),
"Home network".

## Layout (since 2026-10-23 14:05)

```
ISP ─ home AP (Wi-Fi, 192.168.4.0/22; 2.4 + 5 GHz, same SSID)
        └─ 5 GHz ─ GL-AR750S "Slate" in repeater mode (LAN 192.168.8.0/24, router 192.168.8.1)
                      └─ Ethernet ─ USB-C hub (RTL8153, enp59s0u2u1) ─ zbook (DHCP 192.168.8.129)
zbook's own Wi-Fi (wlp112s0) to the home AP on 5 GHz: fallback route only
```

- Double NAT (home AP + router); harmless for now. The router's own Wi-Fi networks (main and guest, both radios) are
  **off**.
- Default route: "Wired connection 2" (metric 100, `ipv4/ipv6.never-default no`); Wi-Fi metric 600.
- Measured: laptop → router 0.9 ms; router → home AP 3.5 ms, 0% loss; via router ~40 Mbit/s down, 37 up. The laptop's
  own 5 GHz Wi-Fi did 81-86 down, 38.5 up. The cap is the router's 5 GHz client link (rx 65 Mbit/s, VHT-MCS 1, one
  spatial stream, signal -69..-72 dBm), not its CPU; moving the router closer to the AP should raise it (open item).

### Video calls and bufferbloat (measured 2026-10-23, wired path, ping to 1.1.1.1 at 5/s)

| Load | Avg | Max | Jitter (mdev) | Loss |
|---|---|---|---|---|
| Idle, 60 s | 3.9 ms | 25 ms | 2.5 ms | 0% |
| Download saturated (~40 Mbit/s) | 47 ms | 120 ms | 22 ms | 0% |
| Upload saturated (~36 Mbit/s) | **189 ms** | **355 ms** | **68 ms** | 0% |

The router hop stays under 1 ms during an upload, so the queue is beyond the router: its 5 GHz uplink or the home
AP/ISP. A call needs only about 2-4 Mbit/s each way, so on an otherwise idle link it gets the idle numbers (far inside
Microsoft's Teams targets); a large upload during a call (cloud sync, a big push, a video upload) breaks it. Fix: SQM
(cake) on the router's WAN, shaped a little below the measured rates (open item). Re-run: `ping -q -i 0.2 -c 100
1.1.1.1` alongside `head -c 150000000 /dev/zero | curl -s -o /dev/null -X POST --data-binary @-
https://speed.cloudflare.com/__up` (downloads: `__down?bytes=25000000`, larger sizes are refused).

## Why: Wi-Fi + Bluetooth on one radio

zbook's Intel AX200 does Wi-Fi and Bluetooth on one radio. On **2.4 GHz** the two time-share airtime, and a continuous
Bluetooth audio stream (Birdbox, A2DP) starves Wi-Fi: 12.5% loss and 135 ms average to the gateway, Chromium waiting
seconds for first bytes (66% of request time; an empty `generate_204` took 3 s), and in the other direction MX Keys lag
and repeated keys. On 5 GHz with the same audio stream: 0% loss, 2.7 ms. Power save was A/B-tested and is **not** the
main cause. After a suspend, wpa_supplicant rejoined the stronger 2.4 GHz BSS; hence the 5 GHz lock on the laptop's
profile (D57) and `wifi-band-watch`, which notifies on any join below 5 GHz.

## NetworkManager commands

```sh
# router as the default route (current) / revert to Wi-Fi
nmcli connection modify "Wired connection 2" ipv4.never-default no ipv6.never-default no
nmcli connection modify "Wired connection 2" ipv4.never-default yes ipv6.never-default yes
nmcli connection up "Wired connection 2"       # after either
# emergency: drop the wired link; Wi-Fi takes the default route at once
nmcli connection down "Wired connection 2"
# remove the laptop's 5 GHz lock (see D57 for when)
nmcli connection modify "<home SSID>" 802-11-wireless.band ""
# test routes through the router without reconnecting: add /32 routes to the profile, then
nmcli device reapply enp59s0u2u1
```

## Diagnosing a slow link

1. Band and signal: `iw dev wlp112s0 link` (freq < 5000 = 2.4 GHz), `iw dev wlp112s0 get power_save`.
2. Gateway ping: `ping -c 40 <gateway>`; jitter (mdev) above ~20 ms or any loss on a LAN hop is the link.
3. Router hop: `ssh root@192.168.8.1 'iw dev wlan-sta0 link'` (rate and MCS), or LuCI → Status → Overview.
4. Browser: `chrome://net-export` gives a NetLog; time to first byte dominating = network, not Chromium. The log
   contains browsing metadata: delete it afterwards.
5. **Kernel TCP metrics cache:** a bad link leaves inflated RTTs (1-5.6 s seen) in `ip tcp_metrics show`, which seed
   long retransmission timeouts for new connections to those hosts even after the link recovers. Flush with
   `sudo ip tcp_metrics flush all`.

## Router: GL.iNet GL-AR750S-EXT

- 3 GbE ports (1 WAN, 2 LAN), USB-A, microSD, **micro-USB 5 V power (≥ 2 A)**, no power button; side button = reset,
  side slider = programmable toggle. Radios: QCA9887 802.11ac 5 GHz (**1 stream**), QCA9560 2.4 GHz. NOR 16 MB + NAND.
- Firmware: **GL 4.3.25** (`glinet_gl-ar750s-nor-nand`), base **OpenWrt 22.03.4**, past upstream end of life (exact
  date unverified): no upstream security fixes (D56). The `.tar` matched GL's HTTPS SHA256
  (`41146b67…5d9fd0`); GL does not appear to sign images (unverified).
- Repeater (WAN) on the 5 GHz radio, band set to 5G in the repeater settings (gear icon, Internet page).

### Firmware pitfalls (this unit)

- Factory reset: hold reset ~10 s after boot; the power LED flashes, then faster; the reset happens on release.
  U-Boot: hold reset while powering on (~5 LED flashes, per GL docs).
- GL 3.101's web upgrader rejects 4.x `.tar` files ("Incorrect firmware format"). Upgrade chain that worked:
  **3.101 → 3.105 → 3.216 → 4.3.25**, all through the web UI.
- This unit's U-Boot is pepe2k's "U-Boot 1.1.4 modification": its failsafe page writes NOR images only (≤ 16 MB) and
  rejects the 18.6 MB NAND 4.x `.img`. GL's bootloader upgrade is "very dangerous… no way to restore it": avoided.
- A temporary static NetworkManager profile (e.g. for U-Boot at 192.168.1.1) needs `autoconnect yes` and a higher
  `autoconnect-priority` (and the DHCP profile's autoconnect off meanwhile): when the router's reboot drops carrier, NM
  activates the autoconnect profile, not the one brought up by hand.
- `nmcli connection up <con> ap <BSSID>` fails with "no device found" when the BSSID is not in the current scan, and
  with "device not compatible" once the profile has a band lock.
- Recovery images: the 4.3.25 `.tar`/`.img` in `~/Downloads` (keep if wanted; the 3.x ones can go).

## Router next steps (MH's list; tracked as one open item)

1. VPN client on the router (ProtonVPN WireGuard), the slider as its toggle, kill switch; measure throughput (the MIPS
   CPU may cap WireGuard below 40 Mbit/s).
2. Laptop to router over Wi-Fi instead of the cable, so the router can sit nearer the AP. Caveats: the AX200 is back in
   use (must stay on 5 GHz, else the Bluetooth problem returns); the router has one 5 GHz radio, so serving the laptop
   and the upstream on it halves throughput. Compare: a longer cable, moving the router with this cable, powerline or
   MoCA, a USB Bluetooth dongle (internal radio Wi-Fi only).
3. Firmware updates: GL auto-upgrade or a reminder (monthly timer + notification); long-term, upstream OpenWrt
   (signed images, current fixes; check the AR750S on the OpenWrt Table of Hardware) with a manual repeater
   (`travelmate` or a wwan interface).
4. Scheduled reboot (set the time zone first; flagged in the panel).
5. Personal media server: decide the architecture first (the router's CPU and RAM are small; a Pi or small x86 box
   behind it may serve better).
6. Evaluate: DNS rebinding protection, encrypted DNS, DDNS, IPv6 (no DHCPv6 on the LAN now), IGMP snooping, firewall
   rules (WAN side closed), GoodCloud (default: off), plugins (weigh attack surface and RAM).
7. Hardening: confirm time zone, GoodCloud off, unused apps/VPN off, toggle set to none, UPnP off, no WAN admin or port
   forwards (only the Wi-Fi shutdown is verified); admin password in `pass`; SSH key, password login off, SSH on LAN
   only; config backup (GL System → Backup or LuCI) in an encrypted place; static DHCP lease for zbook.
