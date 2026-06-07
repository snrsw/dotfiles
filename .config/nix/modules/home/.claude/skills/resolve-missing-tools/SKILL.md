---
name: resolve-missing-tools
description: Resolve a tool that isn't installed on this Nix/home-manager-managed machine. Use whenever a command is missing — "command not found", "X: command not found", "X is not installed", a CLI not on PATH, or you need a one-off tool to finish a task. Run it ephemerally with comma (`, <tool>`) instead of a global install; add it to home.nix only if it's needed permanently.
---

# Resolve Missing Tools

This machine is managed by Nix + home-manager. Packages come from
`home.nix`, not from system package managers.

**Never install tools globally** with `brew install`, `npm i -g`,
`pip install --user`, `cargo install`, or `nix profile install`. They escape
the declarative config and create drift.

## Ad-hoc / one-off — use comma

To run a tool you don't have installed, prefix it with `,` (comma). It fetches
the package from nixpkgs and runs it without installing anything:

```sh
, <tool> [args...]
# examples
, cowsay hello
, jq . data.json
, http GET https://example.com
```

Useful flags:
- `comma -p <cmd>` — print which package provides the command (don't run it).
- `comma -s <cmd>` — open a shell that has the tool available.

In a **non-interactive / agent** context, an ambiguous command name makes comma
open an interactive picker, which will hang. So when a name might map to several
packages, run `comma -p <cmd>` first to see the options. Then run it
**deterministically** — bypass the picker entirely by invoking the chosen package
directly instead of letting comma guess:

```sh
nix run nixpkgs#<package> -- <cmd> [args...]   # e.g. nix run nixpkgs#imagemagick -- convert in.png out.jpg
```

Single-match commands run directly with `, <cmd>` and no prompt.

## Permanent / repeated need — add to home.nix

If the tool will be used more than once, **do not** keep reaching for comma —
add it to `home.packages` in `.config/nix/modules/home/home.nix`, then apply with
the canonical switch command (run from `.config/nix/modules/home`):

```sh
home-manager switch --flake .#$USER --impure
```

Propose the home.nix edit to the user — don't silently change their config.

## If comma reports a missing database

```
Warning: Nix-index database does not exist ...
```

means the home config hasn't been switched since the nix-index setup landed. The
fix is to run the canonical switch command from the section above. But a
`home-manager switch` is an infrastructure change — **propose it to the user and
get approval; don't auto-run it**, especially in a non-interactive context. The
database is the prebuilt nix-index DB managed by home.nix (`programs.nix-index` +
`programs.nix-index-database.comma`).
