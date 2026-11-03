---
summary: Which GPG key is used for what, how git signing is configured, the expired old key, and how to verify
status: current
updated: 2026-10-18
---

# GPG and signing

## Keys

| Key | Use | State |
|---|---|---|
| `9F049F34C91F801DEDF87BBF7C1F6727C99C6EA5` (long ID `7C1F6727C99C6EA5`) | **The key for all GPG operations here**: `pass`, git tag/commit signing, `gpg --clearsign` | Valid to 2028. Sign/encrypt/auth subkeys live on the YubiKey. Signing subkey `CBB477956A6230FF`, encryption subkey `9E8772C7F6336E16`. |
| `AEB43E83657EFBEDB5D61B2862716B9F210A3233` (long ID `62716B9F210A3233`) | Former personal signing key | **Expired 2026-03-06.** Extend or retire (open item); keyring also holds other old keys to clean up. |

## Configuration (as of 2026-10-15)

- `git config --global user.signingkey 9F049F34…` (in `~/.gitconfig`, which is **not yet chezmoi-managed**; merging it with the employer-era repo's `dot_gitconfig.tmpl` is part of Phase 0 of [../plans/boco-merge.md](../plans/boco-merge.md)).
- `~/.gnupg/gpg.conf` has `default-key 9F049F34…` (unmanaged). `gpg-agent.conf` has `enable-ssh-support`; SSH to GitHub uses the YubiKey through the agent socket. Since 2026-10-18 it also sets `no-allow-external-cache` (D51): pinentry never reads or stores passphrases in gnome-keyring.
- `tag.gpgsign = true`, `commit.gpgsign = false`. So annotated tags need the YubiKey; ordinary commits do not.
- `.chezmoi.yml.tmpl` carries the key as `gpg.keys.signing` (not yet consumed by any template).
- The `pass` store (`~/.password-store/.gpg-id`) is encrypted to the same key.

## Verify

```sh
gpg --list-secret-keys --keyid-format long          # card stubs show "ssb>"
gpg --card-status | grep -E 'Signature|Encryption'  # fails "No such device" if unplugged
git -C <repo> tag -s -m test tmp-test && git -C <repo> tag -v tmp-test; git -C <repo> tag -d tmp-test
```
Symptom of an unplugged key: `gpg: selecting card failed: No such device`, SSH `Permission denied (publickey)`, `unable to sign the tag`.

Same symptoms with the key plugged in (`lsusb` shows it) mean pcscd owns the reader. `~/.gnupg/scdaemon.conf`
(managed) sets `disable-ccid` (go through pcscd, not scdaemon's own USB driver) and `pcsc-shared` (gsd-smartcard and
Chromium keep the card open, so an exclusive connect fails with `sharing violation`). Found 2026-10-17, after a reboot
in which pcscd was socket-activated. Restart scdaemon after changing it: `gpgconf --kill scdaemon`. Debug with
`gpg-connect-agent 'SCD GETINFO reader_list' /bye` (empty = no reader) and a `debug-level guru` + `log-file` run.

**PIN asked on every GPG/SSH use: fixed 2026-11-02 (chz-1fv).** The card's policy was not the cause (`ykman openpgp
info`: PIN for signature "Once", touch off, 3 tries left), nor USB autosuspend, nor pcscd restarts. A `debug-level guru`
log showed scdaemon itself (GnuPG 2.4) selecting the YubiKey's **PIV** applet on every `KEYINFO --list`, i.e. at the
start of every operation; the YubiKey clears the OpenPGP "PIN verified" state on an applet switch. `scdaemon.conf` now
sets `disable-application piv` (the PIV applet is empty here; other tools can still use it). Verified: two decrypts a
minute apart, Chromium open, one PIN prompt. The earlier Chromium/OpenSC hypothesis (2026-10-23) was not needed. The
PIN is still asked after an unplug, a `gpgconf --kill scdaemon`, or running `ykman` (it switches applets too). Test:
`echo hi | gpg -ear 9F049F34C91F801DEDF87BBF7C1F6727C99C6EA5 | gpg -d`, twice a minute apart.

A "system keyring" unlock prompt on GPG/SSH use is gnome-keyring, not GPG: see D51 and the keyring item in
[../plans/wayland-desktop.md](../plans/wayland-desktop.md), "Functional daily driver"; diagnose with `keyring-check`. After a `gpg-agent.conf`
change: `gpg-connect-agent reloadagent /bye`; check with `gpgconf --list-options gpg-agent | grep external-cache`.
