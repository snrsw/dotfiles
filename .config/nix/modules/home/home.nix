{ config, pkgs, ... }:

{
  # Home Manager needs a bit of information about you and the paths it should
  # manage.
  home.username = "snrsw";
  home.homeDirectory = "/Users/snrsw";

  # This value determines the Home Manager release that your configuration is
  # compatible with. This helps avoid breakage when a new Home Manager release
  # introduces backwards incompatible changes.
  #
  # You should not change this value, even if you update Home Manager. If you do
  # want to update the value, then make sure to first check the Home Manager
  # release notes.
  home.stateVersion = "25.11"; # Please read the comment before changing.

  # The home.packages option allows you to install Nix packages into your
  # environment.
  home.packages = with pkgs; [
    # # Adds the 'hello' command to your environment. It prints a friendly
    # # "Hello, world!" when run.
    # pkgs.hello
    # Essentials
    curl
    fish
    tmux
    vscode
    codex
    gemini-cli
    claude-code
    gh
    raycast
    # VCS
    git
    ghq
    # Altenatives
    bat
    eza
    # Search
    fzf
    # Shell plugins
    oh-my-posh
    # Container
    orbstack
    k9s
    # # It is sometimes useful to fine-tune packages, for example, by applying
    # # overrides. You can do that directly here, just don't forget the
    # # parentheses. Maybe you want to install Nerd Fonts with a limited number of
    # # fonts?
    # (pkgs.nerdfonts.override { fonts = [ "FantasqueSansMono" ]; })
    # (nerdfonts.override { fonts = [ "JetBrainsMono" ]; })
    nerd-fonts.jetbrains-mono

    # # You can also create simple shell scripts directly inside your
    # # configuration. For example, this adds a command 'my-hello' to your
    # # environment:
    # (pkgs.writeShellScriptBin "my-hello" ''
    #   echo "Hello, ${config.home.username}!"
    # '')
  ];

  # Home Manager is pretty good at managing dotfiles. The primary way to manage
  # plain files is through 'home.file'.
  home.file = {
    # # Building this configuration will create a copy of 'dotfiles/screenrc' in
    # # the Nix store. Activating the configuration will then make '~/.screenrc' a
    # # symlink to the Nix store copy.
    # ".screenrc".source = dotfiles/screenrc;

    # # You can also set the file content immediately.
    # ".gradle/gradle.properties".text = ''
    #   org.gradle.console=verbose
    #   org.gradle.daemon.idletimeout=3600000
    # '';
  };

  # Home Manager can also manage your environment variables through
  # 'home.sessionVariables'. These will be explicitly sourced when using a
  # shell provided by Home Manager. If you don't want to manage your shell
  # through Home Manager then you have to manually source 'hm-session-vars.sh'
  # located at either
  #
  #  ~/.nix-profile/etc/profile.d/hm-session-vars.sh
  #
  # or
  #
  #  ~/.local/state/nix/profiles/profile/etc/profile.d/hm-session-vars.sh
  #
  # or
  #
  #  /etc/profiles/per-user/snrsw/etc/profile.d/hm-session-vars.sh
  #
  home.sessionVariables = {
    # EDITOR = "emacs";
  };

  # ghostty from brew-nix
  programs.ghostty = {
    enable = true;
    package = pkgs.brewCasks.ghostty;
    enableFishIntegration = true;
    settings = {
      font-family = "JetBrainsMono Nerd Font Mono";
      font-size = 14;
      theme = "Iceberg Dark";
      auto-update-channel = "tip";
    };
  };

  programs.vscode = {
    enable = true;
    profiles.default = {
      userSettings = {
        # Theme
        "workbench.colorTheme" = "Moonlight II";
        "workbench.iconTheme" = "material-icon-theme";

        # Editor
        "files.autoSave" = "afterDelay";
        "editor.formatOnSave" = true;
        "files.trimTrailingWhitespace" = true;
        "files.insertFinalNewline" = true;
        "files.trimFinalNewlines" = true;

        # GitHub Copilot
        "github.copilot.enable" = {
          "*" = true;
          "plaintext" = false;
          "markdown" = true;
          "scminput" = false;
        };
        "github.copilot.nextEditSuggestions.enabled" = true;

        # Claude
        "claudeCode.preferredLocation" = "sidebar";

        # Terminal (Nix fish)
        "terminal.integrated.fontFamily" = "JetBrainsMono Nerd Font";
        "terminal.integrated.fontSize" = 14;
        "terminal.integrated.defaultProfile.osx" = "fish";
        "terminal.integrated.profiles.osx" = {
          "fish" = {
            "path" = "/Users/snrsw/.nix-profile/bin/fish";
          };
        };
      };
    };
  };

  programs.fish = {
    enable = true;
    shellAbbrs = {
      cat = "bat";
      ls = "eza --icons --git";
      la = "eza -T -L 1 -a -l --icons";
      lt = "eza -T -L 3 -a --icons";
      lta = "eza -T -L 3 -a -l --icons";
      repos = "cd $(ghq root)/$(ghq list | fzf)";
      getrepo = "ghq get";
      workspace = "cd $(ghq root)/$(ghq list | fzf) && code --add .";
      gcps = ''gcloud config set project $(gcloud projects list --format="value(projectId)" | fzf) && echo -e "\nYour current config is:\n" && gcloud config list'';
      beep = "afplay /System/Library/Sounds/Glass.aiff";
    };
    interactiveShellInit = ''
      # Nix PATH
      fish_add_path /nix/var/nix/profiles/default/bin
      fish_add_path ~/.nix-profile/bin

      # Antigravity
      fish_add_path ~/.antigravity/antigravity/bin

      # oh-my-posh
      oh-my-posh init fish --config 'bubblesextra' | source
    '';
  };

  programs.direnv = {
    enable = true;
    nix-direnv.enable = true;
  };

  # Let Home Manager install and manage itself.
  programs.home-manager.enable = true;
}
