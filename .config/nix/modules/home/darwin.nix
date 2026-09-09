{ pkgs, username, ... }:

# macOS-only half of the home configuration. Everything platform-neutral lives
# in home.nix; linux.nix is this file's counterpart.

{
  home.homeDirectory = "/Users/${username}";

  home.packages = [
    pkgs.raycast
    # orbstack bundles kubectl, so no separate kubectl entry is needed here.
    pkgs.orbstack
    # Claude Desktop app only (no bin/claude wrapper to avoid conflict with claude-code CLI)
    (pkgs.brewCasks.claude.overrideAttrs (old: {
      installPhase = ''
        mkdir -p "$out/Applications/Claude.app"
        cp -R . "$out/Applications/Claude.app"
      '';
    }))
    pkgs.brewCasks.codex-app
    pkgs.brewCasks.cotypist
    # Apple Silicon macOS only upstream, so it cannot move to home.nix.
    pkgs.terminal-browser
    # orca is packaged per platform in flake.nix (DMG here, AppImage on linux);
    # it stays out of home.nix because the linux side is nixGL-wrapped.
    pkgs.orca
  ];

  # nixpkgs has no darwin ghostty build; take the cask.
  programs.ghostty.package = pkgs.brewCasks.ghostty;

  # pbcopy/pbpaste.
  programs.helix.settings.editor.clipboard-provider = "pasteboard";

  programs.vscode.profiles.default.userSettings = {
    "terminal.integrated.defaultProfile.osx" = "fish";
    "terminal.integrated.profiles.osx" = {
      "fish" = {
        "path" = "/Users/${username}/.nix-profile/bin/fish";
      };
    };
  };

  programs.fish.shellAbbrs.beep = "afplay /System/Library/Sounds/Glass.aiff";
}
