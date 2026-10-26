---
summary: zbook's home network (wired through a GL-AR750S repeater, Wi-Fi fallback), SQM on the router, router access and backups, firmware history and pitfalls, NetworkManager commands, and how to diagnose a slow link
status: current
updated: 2026-10-26
---

# Home network

Source: MH's router session of 2026-10-22/23 (report `~/.claude/projects/-home-hseldon--local-share-chezmoi/reports/router-session-2026-10-23.md`, in the private
`claude-state` repo; it holds the exact BSSIDs, MACs and ISP addresses, which stay out of this public repo). Confirmed facts unless marked
**hypothesis**. Decisions: D55-D57 in [../decisions.md](../decisions.md). Open work: [../open-items.md](../open-items.md),
"Home network".

## Layout (since 2026-10-23 14:05)

```
ISP ─ home AP (Wi-Fi, 192.168.4.0/22; 2.4 + 5 GHz, same SSID)
        └─ 5 GHz ─ GL-AR750S "Slate" in repeater mode (LAN 192.168.8.0/24, router 192.168.8.1)
                      └─ Ethernet ─ USB-C hub (RTL8153, enp59s0u1u1*) ─ zbook (DHCP 192.168.8.129)
zbook's own Wi-Fi (wlp112s0) to the home AP on 5 GHz: fallback route only
```

\* The wired interface name follows the hub's USB port (`enp59s0u2u1` on 2026-10-23, `enp59s0u1u1` on 2026-10-26); check
with `ip route show default`.

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
Microsoft's Teams targets); a large upload during a call (cloud sync, a big push, a video upload) breaks it. **Fixed
2026-10-26 by SQM on the router** (D67; next section). Re-measure with `tools/bufferbloat-check/bufferbloat-check
--duration 60` ([../../tools/README.md](../../tools/README.md)).

### SQM on the router (D67, 2026-10-26)

`tools/bufferbloat-check --duration 60` (60 s per phase, 2 streams, ping to 1.1.1.1 at 5/s; avg / max / jitter):

| Load | Baseline 2026-10-26 | SQM 30/20, SFE on | **SQM 30/20, SFE off (live)** |
|---|---|---|---|
| Download saturated | 66 / 322 / 45 ms, 34.7 Mbit/s | 61 / 222 / 32 ms, 35.5 Mbit/s | **12.7 / 55 / 7.4 ms, 28.7 Mbit/s** |
| Upload saturated | 414 / 1648 / 234 ms, 24.2 Mbit/s | 5.6 / 16 / 1.7 ms, 19.5 Mbit/s | **8.5 / 63 / 7.3 ms, 18.7 Mbit/s** |
| Router CPU idle, download / upload | – | ~60% / ~60% | **3-14% / 25-44%** (softirq 80% / 55-60%) |

Loss was 0% throughout; the router hop stayed at about 1.2 ms. The 2026-10-26 baseline was much worse than the
2026-10-23 one (upload 189 ms avg, 37 Mbit/s): the uplink rate varies (below), so shaper rates are set from the day's
numbers, not the old ones.

- **What runs:** `sqm-scripts` 1.5.2 + `kmod-sched-cake` + `luci-app-sqm` from GL's feeds; queue `sqm.wwan` on
  `wlan-sta0` (the repeater uplink), `cake` with `piece_of_cake.qos`, download 30000 / upload 20000 kbit/s, link layer
  none. Download is shaped on `ifb4wlan-sta0` (ingress redirect). LuCI: Network → SQM QoS.
- **Shortcut-FE is off** (`/etc/init.d/shortcut-fe stop` + `disable`). SFE, GL's flow accelerator, forwards known flows
  before the tc ingress hook, so with it on the download shaper saw about 1 MB of a 266 MB test (upload, on the egress
  qdisc, is unaffected). GL's own init script skips SFE when *GL's* QoS has a queue, but it does not know about
  `sqm-scripts`. The `shortcut_fe` core module stays loaded for `gl_sdk4_tertf` (GL's per-client stats; whether the
  panel's per-client speeds still show is unverified).
- **GL's built-in QoS (`gl_eqos`) stays disabled**: it is per-client HTB rate limiting with no AQM (its `model='cake'`
  value is unused), so it would not fix bloat and would fight SQM.
- **The uplink is the weak part**: the home AP hears the router at about -94 dBm (ACK signal), with failed transmits
  and a last tx rate of 6 Mbit/s, so upload capacity moves around. A fixed shaper only holds while the link stays above
  its rate.
- **The CPU is the ceiling** (MIPS 74Kc, 775 MHz): a saturating download through cake without SFE uses 86-97% of it,
  so about 30 Mbit/s of shaped download is this router's limit whatever the radio does. LuCI and SSH can be slow during
  big downloads.

**Decision point (keep front-of-mind; MH was torn between A, B and C):** option A is live. Revisit when the router
moves nearer the AP, when download speed starts to matter more than download latency, when `bufferbloat-check` shows
latency under load creeping back, or when the router's sluggishness under load gets in the way:

| Option | Change | Gains | Costs |
|---|---|---|---|
| **A (live)** | cake both ways, SFE off, 30/20 | Calls clean in both directions | Router CPU pegged by big downloads; download capped ~29 Mbit/s |
| **B** | SFE back on, upload-only shaping | Full download speed, low CPU, upload still clean | Download peaks ~220-320 ms return (incoming audio/video stutters during big downloads) |
| **C** | A with download 25000 | CPU headroom, so the shaper is not working at the edge | ~4 Mbit/s less download |
| **cake-autorate** | Shaper rate follows measured latency (bash loop pinging reflectors) | Uses the link's good moments instead of a worst-case fixed rate | CPU on a weak router (README warns; unmeasured here); extra ping traffic |
| New router | – | Faster CPU lifts the ~30 Mbit/s ceiling | Money; another firmware to set up |

```sh
R='ssh router'
# A -> B: SFE back on, download shaping off (upload stays shaped)
$R 'uci set sqm.wwan.download=0; uci commit sqm; /etc/init.d/sqm restart; /etc/init.d/shortcut-fe enable; /etc/init.d/shortcut-fe start'
# A -> C
$R 'uci set sqm.wwan.download=25000; uci commit sqm; /etc/init.d/sqm restart'
# SQM off entirely (SFE back on as well, if wanted)
$R 'uci set sqm.wwan.enabled=0; uci commit sqm; /etc/init.d/sqm stop'
# watch the CPU during a test
$R 'top -b -d 5 -n 40 | grep ^CPU'
```

(`download=0` disables shaping in that direction in `sqm-scripts`. Check with `tc qdisc show` that no `ifb4wlan-sta0`
cake remains, and re-measure after any change.)

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
nmcli device reapply enp59s0u1u1    # the wired device; name follows the hub's port
```

## Diagnosing a slow link

1. Band and signal: `iw dev wlp112s0 link` (freq < 5000 = 2.4 GHz), `iw dev wlp112s0 get power_save`.
2. Gateway ping: `ping -c 40 <gateway>`; jitter (mdev) above ~20 ms or any loss on a LAN hop is the link.
3. Router hop: `ssh router 'iw dev wlan-sta0 link'` (rate and MCS), or LuCI → Status → Overview.
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

### Access, hardening and backups (2026-10-26)

- **SSH: key only, LAN only.** dropbear has `PasswordAuth off`, `RootPasswordAuth off`, `Interface lan` (listens on
  192.168.8.1:22 only); the only authorized key is the YubiKey's (`cardno:` comment). `ssh router` (a `Host` entry in the managed
  `~/.ssh/config` pins the YubiKey key, which the global `IdentitiesOnly yes` otherwise hides); a
  failed login with "agent refused operation" is an unanswered YubiKey PIN prompt (the PIN cache expired): retry at
  the screen. Scripted runs: open one master connection (`ssh -o ControlMaster=yes -o ControlPath=$XDG_RUNTIME_DIR/router-ctl
  -o ControlPersist=20m -fN router`; a scratchpad path is too long for the socket) so the PIN is asked once. Without the YubiKey: the web panel (admin password in `pass`, under the router's
  entry) can turn password login back on (LuCI → System → Administration).
- **Audit 2026-10-26, no change needed:** time zone America/Chicago; GoodCloud not running (no `enable` in
  `gl-cloud`; its init script is enabled at boot, left so the panel can manage it); rtty off; UPnP not installed; no
  port forwards; WAN zone input DROP / forward REJECT with stock rules; no VPN client or server; side toggle unset; all
  four router APs off; web admin listens everywhere but WAN DROP keeps it off the home LAN side.
- **No static DHCP lease for zbook** (D68): revisit with the VPN or media server.
- **opkg does not check feed signatures**: GL's `/etc/opkg.conf` lacks `option check_signature` (stock OpenWrt has
  it), though GL signs its feeds (`Packages.sig`, keys in `/etc/opkg/keys/`). Until it is turned on (open item),
  verify by hand after `opkg update`: fetch each feed's `Packages.sig` and run `usign -V -P /etc/opkg/keys -m
  <gunzipped /var/opkg-lists/<feed>> -x <sig>`.
- **Config backups**: `sysupgrade -b` on the router, piped over SSH straight into `gpg -e -r <MH's personal key
  fingerprint>`, so no plaintext lands on zbook. The backup holds the home Wi-Fi PSK and the root password hash. Copies
  (same file, checked by sha256): `~/.local/state/router-backups/` and `backups/router-gl-ar750s/` on both external
  drives (Backups, PortableSSD); not in any git repo. Files: `gl-ar750s-2026-10-26-pre-change` and
  `…-post-sqm.tar.gz.gpg`. Decrypting needs the YubiKey (or the offline subkey backup).
- **What a backup does not restore**: `sysupgrade -b` saves `/etc/config` and the like, not installed packages or
  init-script enablement. After a reflash + restore: `opkg update` (verify as above), `opkg install kmod-sched-cake
  sqm-scripts luci-app-sqm`, `/etc/init.d/shortcut-fe stop; /etc/init.d/shortcut-fe disable`, `/etc/init.d/sqm
  restart`, then `bufferbloat-check`.

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
   CPU may cap WireGuard below 40 Mbit/s, and it now also runs cake without SFE: measure the two together, and
   revisit the SQM options and the static lease, D67/D68).
2. Laptop to router over Wi-Fi instead of the cable, so the router can sit nearer the AP (after any move: re-run
   `bufferbloat-check`, watch the router CPU, re-tune or revisit the SQM options, D67). Caveats: the AX200 is back in
   use (must stay on 5 GHz, else the Bluetooth problem returns); the router has one 5 GHz radio, so serving the laptop
   and the upstream on it halves throughput. Compare: a longer cable, moving the router with this cable, powerline or
   MoCA, a USB Bluetooth dongle (internal radio Wi-Fi only).
3. Firmware updates: GL auto-upgrade or a reminder (monthly timer + notification); long-term, upstream OpenWrt
   (signed images, current fixes; check the AR750S on the OpenWrt Table of Hardware) with a manual repeater
   (`travelmate` or a wwan interface).
4. Scheduled reboot (set the time zone first; flagged in the panel).
5. Personal media server (revisit the static lease, D68): decide the architecture first (the router's CPU and RAM are small; a Pi or small x86 box
   behind it may serve better).
6. Evaluate: DNS rebinding protection, encrypted DNS, DDNS, IPv6 (no DHCPv6 on the LAN now), IGMP snooping, firewall
   rules (WAN side closed), GoodCloud (default: off), plugins (weigh attack surface and RAM).
7. ~~Hardening~~: **done 2026-10-26** (above, "Access, hardening and backups"); the static lease was dropped (D68).
   Left: opkg signature checking (open item).
