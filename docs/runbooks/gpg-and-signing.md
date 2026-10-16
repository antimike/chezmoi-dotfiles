---
summary: Which GPG key is used for what, how git signing is configured, the expired old key, and how to verify
status: current
updated: 2026-10-15
---

# GPG and signing

## Keys

| Key | Use | State |
|---|---|---|
| `9F049F34C91F801DEDF87BBF7C1F6727C99C6EA5` (long ID `7C1F6727C99C6EA5`) | **The key for all GPG operations here**: `pass`, git tag/commit signing, `gpg --clearsign` | Valid to 2028. Sign/encrypt/auth subkeys live on the YubiKey. Signing subkey `CBB477956A6230FF`, encryption subkey `9E8772C7F6336E16`. |
| `AEB43E83657EFBEDB5D61B2862716B9F210A3233` (long ID `62716B9F210A3233`) | Former personal signing key | **Expired 2026-03-06.** Extend or retire (open item); keyring also holds other old keys to clean up. |

## Configuration (as of 2026-10-15)

- `git config --global user.signingkey 9F049F34…` (in `~/.gitconfig`, which is **not yet chezmoi-managed**; merging it with the employer-era repo's `dot_gitconfig.tmpl` is part of Phase 0 of [../plans/boco-merge.md](../plans/boco-merge.md)).
- `~/.gnupg/gpg.conf` has `default-key 9F049F34…` (unmanaged). `gpg-agent.conf` has `enable-ssh-support`; SSH to GitHub uses the YubiKey through the agent socket.
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
