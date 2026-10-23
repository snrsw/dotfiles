#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FLAKE_DIR="$REPO_ROOT/.config/nix/modules/home"
DAEMON_SOCKET="/nix/var/nix/daemon-socket/socket"
NIX_DAEMON_BIN="/nix/var/nix/profiles/default/bin/nix-daemon"
NIX_STORE_BIN="/nix/var/nix/profiles/default/bin/nix-store"
NIXBLD_USERS=10

# Nix uses a large stack while evaluating flakes. Raise the soft limit when
# the container permits it; the hard limit must be raised by the container
# runtime (or an administrator), so do not make startup fail when it cannot.
if [ "$(ulimit -Hs)" -ge 61440 ] 2>/dev/null; then
  ulimit -Ss 61440
fi

# Bind /nix to a path under the home volume so the store survives a
# container rebuild (only /home/coder is persisted, not /nix itself).
if ! mountpoint -q /nix; then
  sudo mkdir -p /nix /home/coder/nix
  sudo mount --bind /home/coder/nix /nix
fi

# Determinate Nix installs the daemon configuration for multi-user builds, but
# minimal containers may not contain the system group/accounts it expects.
# Make this idempotent so a fresh container can be bootstrapped repeatedly.
ensure_build_users() {
  if ! getent group nixbld >/dev/null; then
    sudo groupadd --system nixbld
  fi

  for n in $(seq 1 "$NIXBLD_USERS"); do
    user="nixbld$n"
    if ! getent passwd "$user" >/dev/null; then
      sudo useradd --system --gid nixbld --no-create-home --shell /usr/sbin/nologin "$user"
    fi
    sudo usermod --append --groups nixbld "$user"
  done
}

ensure_build_users

if [ "${1:-}" = "--gc" ]; then
  sudo "$NIX_STORE_BIN" --gc
  shift
fi

# Determinate Nix's multi-user store needs nix-daemon running, but
# containers without systemd (e.g. Coder workspaces) never auto-start it.
daemon_healthy() {
  [ -S "$DAEMON_SOCKET" ] && nix store ping --store daemon >/dev/null 2>&1
}

if ! daemon_healthy; then
  # A previous daemon can leave the socket behind after the process dies.
  # Remove only that exact socket before asking the daemon to bind it again.
  if [ -S "$DAEMON_SOCKET" ]; then
    sudo rm -f -- "$DAEMON_SOCKET"
  fi

  echo "nix-daemon not running, starting it..."
  sudo "$NIX_DAEMON_BIN" --daemon &
  disown

  for _ in $(seq 1 30); do
    [ -S "$DAEMON_SOCKET" ] && break
    sleep 1
  done

  if ! daemon_healthy; then
    echo "error: nix-daemon did not start (no socket at $DAEMON_SOCKET)" >&2
    exit 1
  fi
fi

export NIX_REMOTE=daemon

if [ "${1:-}" = "--daemon-only" ]; then
  exit 0
fi

# -b backup: any pre-existing unmanaged file (e.g. fish's default
# config.fish, created before home-manager ever ran) is renamed aside
# instead of aborting the switch.
if command -v gh >/dev/null 2>&1 && GH_TOKEN="$(gh auth token 2>/dev/null || true)" && [ -n "$GH_TOKEN" ]; then
  export NIX_CONFIG="access-tokens = github.com=$GH_TOKEN"
fi

nix run home-manager/master -- switch --flake "$FLAKE_DIR" --impure -b backup
