# Beads (bd) Performance — Cross-Project Reference

## Two backend modes

Beads supports two Dolt backends, set at `bd init` time:

- **Embedded mode** (default): Dolt engine is compiled into `bd`; no separate process. Every `bd` invocation opens and closes the DB from scratch. No external binary needed.
- **Server mode** (`bd init --server`): A persistent `dolt sql-server` process serves all connections over a MySQL-compatible socket. `bd` commands are thin clients. Requires the `dolt` binary (install via Chezmoi `run_onchange_install-dolt.sh.tmpl`).

**Server mode is strongly preferred for interactive use.** It eliminates the cold-read class of slowness entirely (see below) and supports concurrent access from multiple processes.

## Root cause of slow `bd` commands

Embedded mode has two compounding slowness classes:

**Class 1 — Cold page-cache reads.** Every `bd` invocation starts the Dolt engine fresh. After a WSL2 restart or OS page-cache eviction, all reads from `.beads/embeddeddolt/` go to the VHD directly. First commands can be 5-30s even with a small journal. Subsequent commands are fast (cache warm). Server mode eliminates this: the `dolt sql-server` process keeps its buffer pool warm in memory permanently.

**Class 2 — Journal bloat.** Dolt appends all writes to a chunk journal (`embeddeddolt/<DB>/.dolt/noms/vvvv...`). Every read scans the journal. As the journal grows, reads slow down (seen: 30s for `bd label list-all` with a 27MB journal). Even in batch mode, every write grows the journal — with a daily cleanup window, up to 24h of writes can accumulate mid-session. Server mode reduces (not eliminates) this because the server caches hot data in memory and avoids full journal scans on each connection.

Two compounding factors within Class 2:
1. **Journal bloat** — uncompacted writes pile up in the journal file
2. **Commit history** — each auto-commit adds objects to the oldgen chunk store (`oldgen/*.darc`); reads walk chunk pointers through all history. 523 commits → 8.3MB oldgen → 5-12s cold reads on WSL2 VHD.

## Server mode setup

```bash
# Install dolt (required; not bundled with bd)
chezmoi apply   # triggers run_onchange_install-dolt.sh.tmpl

# Export current issues (if migrating from embedded mode)
bd export --output /tmp/$(basename $PWD)-issues.jsonl

# Re-init in server mode (--force if .beads/ already exists)
bd admin reset
bd init --server --stealth --non-interactive

# Restore issues
bd import /tmp/$(basename $PWD)-issues.jsonl

# Re-apply config (see below)
bd config set dolt.auto-commit batch
bd config set no-push true
bd config set no-git-ops true   # if .beads/ is a nested git repo
```

**Server start/stop** (after migration):
```bash
bd dolt start    # start server for this project
bd dolt stop     # stop it
bd dolt status   # check server state
```

**direnv integration** — add to `.envrc` in the project directory:
```bash
# Start the Dolt server on directory entry; no-op if already running.
bd dolt status &>/dev/null || bd dolt start
export BEADS_DOLT_PASSWORD="$(pass show beads/<project> 2>/dev/null)"
```

**On-exit shutdown**: direnv has no native "on leave" hook. The server is lightweight and dies naturally on WSL2 restart. For explicit shutdown, use `bd dolt stop` manually or add a zsh `chpwd` hook (fragile; not recommended).

## Recommended configuration

Set once per project after `bd init`:

```bash
bd config set dolt.auto-commit batch   # no per-write commits
bd config set no-push true             # suppress Dolt SQL auto-push (git-level sync handles backup)
```

**`dolt.auto-commit = batch`**: writes accumulate in Dolt working set; committed only by `bd dolt commit`. Prevents per-write commit explosion.

**`no-push = true`**: suppresses the Dolt SQL server's auto-push after commits. If a Dolt SQL remote is misconfigured (wrong repo), this also prevents spurious push errors. The outer `.beads/` git repo handles backup sync to the configured `sync.remote`.

## Automated maintenance (systemd timer + bd-track)

`bd-track` (at `~/.local/bin/bd-track`) encapsulates the full maintenance workflow.

**One-time project setup:**
```bash
# In the project directory:
bd-track init-project --no-git-ops --install-systemd
# --no-git-ops: recommended when .beads/ is a nested git repo
# --install-systemd: creates a single shared systemd user timer (idempotent)
# Additional projects: bd-track init-project --path ~/Source/Other --days 14
```

This writes `~/.config/bd-track/repos.yaml` (multi-project registry) and installs
`~/.config/systemd/user/bd-track-cleanup.{service,timer}` if not already present.
The timer fires daily (`Persistent=true` catches up missed runs on WSL2 wake).

**Manual cleanup:**
```bash
bd-track cleanup               # defaults: --days 7
bd-track cleanup --days 14 --project-dir ~/Source/Other
bd-track cleanup --skip-commit # skip dolt commit if working set is clean
```

**What cleanup does:**
1. `bd dolt commit` — seals the day's batch into one commit
2. `bd compact --days N --force` — squashes commits older than N days; keeps oldgen small
3. `bd gc --skip-decay --force` — compacts the journal into `.darc` chunk tables

Cleanup logs go to `~/.cache/bd-track/cleanup.log` (1MB rotating, 3 backups).

**Per-repo cadence config** (`~/.config/bd-track/repos.yaml`):
```yaml
global:
  check_interval: daily   # systemd OnCalendar value
repos:
  - path: /home/user/Source/<project>
    commit_cadence: 1d    # how often to commit
    compact_days: 7       # rolling history window
```

The timer fires at `check_interval`; per-repo cadence is enforced by checking
`~/.cache/bd-track/cleanup-state.json` (last_run timestamps) in the service script.

## Emergency recovery (already slow)

```bash
bd flatten --force                     # nuclear: squash all history to 1 commit
bd gc --skip-decay --force             # compact journal after flatten
```

After `bd flatten`, reads drop to <0.5s (warm cache) and stay near 1-2s cold. Then configure batch mode + the daily cron above to prevent recurrence.

## Gotchas

- **`bd gc` alone doesn't fix history-driven slowness.** It compacts the journal but preserves all commits. Oldgen stays large. Use `bd compact --days N` first.
- **Server mode requires the `dolt` binary** — it's not bundled with `bd`. Embedded mode works without it. Install via `chezmoi apply` (see `run_onchange_install-dolt.sh.tmpl`).
- **`bd dolt status` errors in embedded mode** — commands like `bd dolt start/stop/status/show` are no-ops in embedded mode; they return `not supported in embedded mode`. This is expected.
- **Fast reads right after gc/flatten are misleading.** OS page cache is warm; cold reads (after WSL2 restarts or cache eviction) will be slower. Benchmark with a cold cache by running after a `sudo sysctl vm.drop_caches=3`.
- **Batch mode + hard kill = uncommitted working set.** SIGTERM/SIGHUP flush pending commits automatically. A hard kill leaves writes unsynced until the next `bd dolt commit`.
- **Dolt SQL remote vs git sync remote are independent.** `sync.remote` in config.yaml is the git-level remote for the `.beads/` repo. The Dolt SQL remote (set via `bd dolt remote add`) is a separate Dolt-native push target. If these diverge or the SQL remote points to the wrong repo, set `no-push = true` and rely on git-level sync.
- **`bd dolt remote add` requires full URI syntax**, not SSH shorthand: use `git+ssh://git@github.com/user/repo` not `git@github.com:user/repo`.
