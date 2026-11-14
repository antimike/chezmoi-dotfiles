# Encrypted amontillado library (git-annex + gcrypt)

Machine setup for amontillado's NSFW library: keys, the two encrypted remotes, adding and removing machines,
restore. amontillado itself never runs git, git-annex, gpg or gcrypt; it decided the design and keeps an overview
([its `docs/version-control.md`](https://github.com/antimike/amontillado/blob/main/docs/version-control.md); the
reasoning is its `docs/design.md`, "git-annex libraries: decisions" 1-5). This runbook is the step-by-step part, which
amontillado's decision 2 placed with the dotfiles (chz-iqp, 2026-11-13).

## Layout

The NSFW root (`$XDG_DATA_HOME/amontillado/library-nsfw` unless the config moves it) is a git-annex repository:
`info.yaml` files and thumbnails in git, images annexed. It leaves the machine only encrypted, through two remotes:

| Remote | Holds | Encryption |
|---|---|---|
| `github`: `gcrypt::git@github.com:antimike/<repo>.git`, a **private** GitHub repository | git: info files, thumbnails, record names, the git-annex branch (every image's hash and location), commit messages | git-remote-gcrypt: GitHub sees a few opaque files |
| `ssd`: a `directory` special remote on the PortableSSD | the images | git-annex `encryption=hybrid`: file names are HMACs, contents GPG/AES |

Every participant key can read both. The other setup amontillado names, one `type=gcrypt` special remote (ssh host or
local path) holding git and images together, keeps nothing on GitHub; `annex-gcrypt` does not cover it.

**Why not git-crypt** (amontillado decision 1, re-checked with MH 2026-11-13): `git annex init` writes `* filter=annex`
into `.git/info/attributes`, which outranks a `filter=git-crypt` in `.gitattributes`, so info files were pushed in
plaintext, silently (fails open, into history, unlike every gcrypt mistake below, which fails closed); and even
working, git-crypt leaves the paths (record names describe the picture), the thumbnails unless listed, the git-annex
branch (each image's SHA-256 identifies a known Wallhaven image) and commit messages readable.

## Tools

- `git-annex` and `git-remote-gcrypt`: package map, `base` target (`home/.chezmoidata/packages.yaml`).
- `annex-gcrypt` (`~/.local/bin`): every per-clone step below; `annex-gcrypt --help`. Tested by
  `tools/annex-gcrypt-test/annex-gcrypt-test` (run it after a git-annex, gcrypt or gpg upgrade).

**What chezmoi automates (item 7, MH 2026-11-13):** the packages and the helper only. Nothing library-specific goes in
the global gitconfig. The shared settings live in the library itself: `.annex-gcrypt` (committed, git config format)
names the two remotes and lists the participants, and `annex-gcrypt setup` / `sync` write them into each clone's
`.git/config`. Per-machine steps (keys, the drive's mount point) stay manual.

## Keys

**One OpenPGP key per machine, plus an offline backup key** (amontillado decision 3). Separate keys, not subkeys of one
key: OpenPGP encrypts to one encryption subkey per key, so per-machine subkeys could not all be recipients.

A machine key, in the normal keyring:

```sh
gpg --quick-gen-key "amontillado $(hostname -s)" default default never   # Ed25519 + Cv25519
gpg --list-secret-keys --with-colons "amontillado $(hostname -s)" | awk -F: '/^fpr/ {print $10; exit}'
```

Give it a passphrase (gpg-agent caches it; each push signs the manifest, so expect one prompt per cache period). It is
not the YubiKey key: the YubiKey stays the git signing key, and `annex-gcrypt` overrides it per remote (see "Failure
modes").

The offline backup key, made in a throwaway keyring on tmpfs:

```sh
export GNUPGHOME=$(mktemp -d -p "$XDG_RUNTIME_DIR")
gpg --quick-gen-key "amontillado backup" default default never           # a strong passphrase
gpg --export --armor "amontillado backup" > amontillado-backup.pub.asc
gpg --export-secret-keys --armor "amontillado backup" > /run/media/$USER/<drive>/amontillado-backup.sec.asc
gpgconf --kill all; rm -rf "$GNUPGHOME"; unset GNUPGHOME
gpg --import amontillado-backup.pub.asc                                  # public half into the normal keyring
```

Keep the secret half off the PortableSSD (that drive holds the encrypted images) and off every machine: the `Backups`
stick, a second stick, or paper (`paperkey`, not installed; ask). Note the fingerprint in `pass` beside the
passphrase.

### Public keys

Every machine needs **every participant's public key** before its first clone: gcrypt verifies the manifest's
signature, and a clone without the signer's key fails with `Can't check signature: No public key`. It also encrypts
each push to all of them. Export on one machine, import on the other:

```sh
gpg --export --armor <fpr> <fpr> ... > participants.asc    # public keys only: safe on any stick
gpg --import participants.asc
```

No trust settings are needed (tested).

## Create the remotes (once per library)

1. On GitHub: a **private** repository, empty, with no branch protection (gcrypt force-pushes; the repository holds one
   rewritten branch).
2. In the root, if it is not a git-annex repository yet: `git init`, then amontillado's `.gitattributes` from its
   version-control.md ("A git-annex root": images annexed, thumbnails in git, one pattern per line, and the
   `info.yaml merge=amo-info` lines), commit.
3. With the PortableSSD mounted and every participant's public key imported:

```sh
annex-gcrypt init --url gcrypt::git@github.com:antimike/<repo>.git \
  --directory /run/media/$USER/PortableSSD/amontillado/library-nsfw \
  <zbook fpr> <backup fpr>
```

It commits `.annex-gcrypt`, runs `git annex init`, configures the clone, creates `ssd` (encrypted to the first key;
`initremote` ignores `keyid+=`, so the rest are added with `enableremote`), copies the images, makes the first
(explicit) force push and runs `check`.

4. amontillado's side, per clone: `on_change: amo hook git-commit` in its config if amo should commit its own changes
   (amontillado's version-control.md, "The on_change hook").

## Day to day

```sh
annex-gcrypt sync
```

`git annex pull github` (fetch and merge, info files through the `amo-info` driver), re-apply the participants from
the pulled `.annex-gcrypt`, `git annex push ssd` (skipped with a notice when the drive is not mounted), then `git push
--force github <branch> git-annex`, refused if `check` finds a problem. Use it instead of `git annex sync`, which
cannot push here (`require-explicit-force-push` refuses its implicit force) and would copy to the drive only.

Freeing space: `git annex drop <record>` once `git annex whereis` shows a copy on `ssd`. amo indexes dropped images and
tells you to `git annex get` them when needed.

**Push cost** (measured 2026-11-13, gcrypt 1.5's git backend, 19 KB thumbnails): a push uploads about twice the new
git data, not the whole history; once more than 25 packs have piled up (about every 25 pushes) gcrypt repacks and
re-uploads everything (2,000 records ≈ 40 MB ≈ 16 s
at the router's 20 Mbit/s up). The man page's "entire repository history with each push" overstates it. Images never
go through gcrypt.

## Adding a machine

1. On the new machine: make its key (above), import every participant's public key, export its own public key.
2. On a machine with access, with the drive mounted: `gpg --import <new>.asc`, then `annex-gcrypt add-key <new fpr>`
   (`enableremote ssd keyid+=` re-encrypts the cipher only, not the images; the participants change is committed and
   force-pushed; the manifest is re-encrypted to everyone, so the new key reads the whole history).
3. Import the new key on every other machine; their next `sync` picks up the new list from `.annex-gcrypt` (a sync
   without the key refuses with "public keys missing").
4. On the new machine: `annex-gcrypt clone gcrypt::git@github.com:antimike/<repo>.git <root> --directory <mount>`,
   then `git annex get .` (or only what it should hold).

## Removing a machine

`annex-gcrypt remove-key <fpr>` from another machine: drops it from `.annex-gcrypt` and the special remote's cipher,
and the next push is encrypted without it. **This is not a revocation**: the removed machine keeps every pack it
fetched and the special remote's cipher, so it can still read what it had and the images already on the drive. Real
revocation (a lost or compromised machine) is a new GitHub repository and a new special remote, filled from a
surviving clone with `annex-gcrypt init` on new names, then the old ones deleted.

## Restore on a fresh machine

Same as step 4 of "Adding a machine" when the machine's key is a participant. With the **backup key only** (every
machine lost): import its secret half and every participant's public key into a keyring, `annex-gcrypt clone ... --key
<backup fpr> --directory <mount>`, `git annex get .` (tested). Then make a machine key and `add-key` it, so the backup
key goes back offline.

The clone's git remote must not have the special remote's name (`clone -o ssd` makes `enableremote` refuse);
`annex-gcrypt clone` renames `origin` to the name in `.annex-gcrypt`.

## Failure modes (found rehearsing, 2026-11-13)

`annex-gcrypt setup`/`sync` prevent all of these; they matter when working with plain git commands.

| Mistake | Effect | Recovery |
|---|---|---|
| A clone without `gcrypt-participants` pushes | gcrypt encrypts to that machine's key only ("encrypt to your default key" in its man page); everyone else gets `Failed to decrypt manifest` | that machine sets the participants and pushes again (with a new commit: an unchanged push does not rewrite the manifest); nothing is lost |
| Hidden recipients (gcrypt's default) with Curve25519 keys | gpg logs an ECDH error trying another recipient's packet and exits 2, gcrypt aborts: every participant but one is locked out. RSA keys do not do this (tested) | `gcrypt-publish-participants true` (shows the key ids to GitHub, as git-annex already does for the special remote) |
| A push signed with a non-participant key (the global YubiKey `user.signingkey`) | every machine rejects the manifest ("Only accepting signatories") | `remote.github.gcrypt-signingkey <machine fpr>`, push again |
| A plain push from a stale clone | every gcrypt push is a force push: the other machine's commits vanish from the remote | `require-explicit-force-push` (pushes need `--force`); always pull first (`sync` does) |
| A first plain push refused | gcrypt has recorded a remote id, and the next push aborts with "Repository not found ... but repository ID is set" | `git config --unset remote.github.gcrypt-id`, then `git push --force` |
| `enableremote ssd keyid+=...` without `directory=` | `Specify directory=` | pass the drive's path (`add-key` does) |
