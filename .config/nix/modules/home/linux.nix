{ config, pkgs, username, nixgl, ... }:

# Linux-only half of the home configuration, targeting a NON-NixOS distro with
# the Nix package manager installed (standalone home-manager). Everything
# platform-neutral lives in home.nix; darwin.nix is this file's counterpart.

{
  home.homeDirectory = "/home/${username}";

  targets.genericLinux = {
    # Not NixOS: this makes home-manager set up XDG_DATA_DIRS and friends, so
    # installed .desktop entries show up in the distro's app launcher.
    enable = true;

    # The graphics driver is not in the Nix store either, so a store-built GUI
    # app cannot find libGL and dies at startup. nixGL injects the host driver
    # at run time. `mesa` covers Intel and AMD; switch to "nvidia" (or
    # "mesaPrime"/"nvidiaPrime" on a hybrid laptop) on an NVIDIA box.
    nixGL = {
      packages = nixgl.packages.${pkgs.stdenv.hostPlatform.system};
      defaultWrapper = "mesa";
    };
  };

  home.packages = with pkgs; [
    # orbstack is darwin-only and bundles kubectl; on Linux the container
    # runtime and kubectl are separate packages.
    podman
    kubectl
    # Clipboard bridges for helix and yazi. Ship both and let helix pick — the
    # right one depends on whether the session is Wayland or X11, which is a
    # run-time fact, so clipboard-provider is deliberately left unset here.
    wl-clipboard
    xclip
  ];

  # NixOS handles fontconfig globally; standalone home-manager must opt in, or
  # udev-gothic-nf stays invisible to every application.
  fonts.fontconfig.enable = true;

  programs.ghostty.package = config.lib.nixGL.wrap pkgs.ghostty;
  programs.vscode.package = config.lib.nixGL.wrap pkgs.vscode;

  programs.vscode.profiles.default.userSettings = {
    "terminal.integrated.defaultProfile.linux" = "fish";
    "terminal.integrated.profiles.linux" = {
      "fish" = {
        "path" = "/home/${username}/.nix-profile/bin/fish";
      };
    };
  };

  # No afplay outside macOS; the terminal bell needs no extra package.
  programs.fish.shellAbbrs.beep = "printf '\\a'";
}
