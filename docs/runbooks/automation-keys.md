# Automation keys (systemd credentials)

Keys that unattended user services use instead of the YubiKey (D74). Today: one GitHub deploy key per repo that
`sync-repos` pushes. The restic password for `claude-transcripts-backup` is the next candidate (chz-6w5).

## How it works

- The private key lives encrypted at `~/.config/credstore.encrypted/<name>` (mode 0600), made by user-scoped
  `systemd-creds --user`. It decrypts only as `hseldon`, on zbook: bound to the user and to the host key
  `/var/lib/systemd/credential.secret` (root-only) **and the TPM2** (`host+tpm2`; MH's root check, 2026-11-03). An
  unprivileged encrypt goes through the `io.systemd.Credentials` service, which picks the key type itself (`auto`
  here), so only the root check below shows the binding.
- The unit imports it with `ImportCredential=<glob>`; systemd decrypts it into the unit's private
  `$CREDENTIALS_DIRECTORY` (`/run/user/1000/credentials/<unit>/`, tmpfs) for that run and removes it when the unit
  stops. A missing credential is not an error.
- **What it protects against:** the file is useless off this machine (a copied file, a restic snapshot, a stolen disk).
  **What it does not:** any process running as `hseldon` can decrypt it (`systemd-creds --user decrypt`, below), so
  against same-user malware it is no better than a 0600 file. The limit there is the key's scope: a deploy key can
  push to one repo only.
- `sync-repos` maps a repo to its key by the origin's repository name: `git@host:owner/claude-state.git` uses
  `sync-repos.claude-state`. With the key present it sets `GIT_SSH_COMMAND='ssh -i <key> -o IdentitiesOnly=yes -o
  IdentityAgent=none'` for that repo and logs `using deploy key for <repo>`; without it, ssh uses the YubiKey through
  gpg-agent as before.

| Credential | Used by | GitHub key |
|---|---|---|
| `sync-repos.claude-state` | `sync-repos.service` (`ImportCredential=sync-repos.*`) | deploy key `sync-repos@zbook` on `antimike/claude-state`, write access |

## New key (or a new repo for sync-repos)

```
sync-repos-deploy-key ~/.claude/projects      # any repo dir with a GitHub origin
```

It runs `ssh-keygen -t ed25519 -N ''` in a `mktemp -d` under `$XDG_RUNTIME_DIR` (tmpfs; swap is zram, so the plaintext
never reaches disk), encrypts the private half with `systemd-creds --user --name=sync-repos.<repo> encrypt`, deletes
the plaintext, keeps the public half at `~/.ssh/deploy-keys/sync-repos.<repo>.pub` and prints it with the GitHub URL.
Add it there as a deploy key with **Allow write access** (one deploy key per repo is GitHub's rule; a second machine
gets its own key). Then check:

```
systemctl --user start sync-repos.service
journalctl --user -u sync-repos -n 20         # expect "using deploy key for ..." and "pushed ..."
```

For another service, the same by hand: `systemd-creds --user --name=<name> encrypt <plaintext> ~/.config/credstore.encrypted/<name>`,
then `ImportCredential=<name>` in the unit and read `$CREDENTIALS_DIRECTORY/<name>`. The name given to `--name` must
match the file name the unit imports, or decryption fails ("Name in credential doesn't match expectations").

## Rotate

1. `sync-repos-deploy-key --force ~/.claude/projects` (replaces the credential and the `.pub`).
2. On GitHub, add the new public key, then delete the old deploy key.
3. Run the check above.

Rotate after a suspected leak, and after anything that makes the credential undecryptable: a reinstall, a lost
`/var/lib/systemd/credential.secret` or a TPM clear. There is deliberately no backup (not in `pass`, not in the GPG
keyring): the key is disposable, and a new one takes two minutes.

## Export a plaintext copy

```
systemd-creds --user --name=sync-repos.claude-state decrypt \
  ~/.config/credstore.encrypted/sync-repos.claude-state ~/some/path/key
chmod 600 ~/some/path/key
```

Works only as `hseldon` on zbook. Delete the copy when done (or rotate, if it went anywhere else).

## Check what the credential is bound to (needs root)

An unprivileged encrypt ignores `--with-key`, so comparing header IDs only works with root-made references. The first
16 decoded bytes name the key type:

```
cred=~/.config/credstore.encrypted/sync-repos.claude-state
hdr() { base64 -d <"$1" | head -c16 | xxd -p; }
for k in host host+tpm2; do
  echo probe | sudo systemd-creds --uid=hseldon --with-key=$k --name=probe encrypt - /tmp/p-$k.cred
  sudo chown "$USER" /tmp/p-$k.cred; echo "$k: $(hdr /tmp/p-$k.cred)"
done
echo "real: $(hdr $cred)"; rm /tmp/p-*.cred
```

The line that matches `real:` is the binding.
