{ config, pkgs, username, ... }:


{
  # Home Manager needs a bit of information about you and the paths it should
  # manage.
  home.username = username;
  home.homeDirectory = "/Users/${username}";

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
    tmux
    vscode
    llm-agents.codex
    llm-agents.gemini-cli
    llm-agents.claude-code
    raycast
    comma
    # VCS
    ghq
    git-secrets
    git-wt
    # Altenatives
    bat
    eza
    # Search
    fzf
    duckdb
    # Shell plugins
    oh-my-posh
    # Container
    orbstack # kubectl is included
    k9s
    kubecolor
    # Cloud
    awscli2
    google-cloud-sdk
    azure-cli
    # Neovim
    ripgrep
    fd
    lazygit
    stylua
    nil
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

  programs.git = {
    enable = true;
    settings = {
      extraConfig = {
        init.defaultBranch = "main";
        pull.rebase = true;
        push.autoSetupRemote = true;
      };
    };
  };

  programs.gh = {
    enable = true;
    settings = {
      git_protocol = "ssh";
      editor = "vim";
    };
  };

  programs.delta = {
    enable = true;
    enableGitIntegration = true;
    options = {
      navigate = true;
      line-numbers = true;
      side-by-side = true;
    };
  };

  # ghostty from brew-nix
  programs.ghostty = {
    enable = true;
    package = pkgs.brewCasks.ghostty;
    enableFishIntegration = true;
    settings = {
      font-family = "JetBrainsMono Nerd Font Mono";
      font-size = 14;
      theme = "Github Light Default";
      background-opacity = 0.9;
      keybind = "global:cmd+backquote=toggle_quick_terminal";
    };
  };

  programs.vscode = {
    enable = true;
    profiles.default = {
      extensions = with pkgs.vscode-extensions; [
            github.copilot
            github.github-vscode-theme
            ms-python.python
            pkief.material-icon-theme
            ms-vscode-remote.remote-containers
            ms-azuretools.vscode-containers
          ] ++ pkgs.vscode-utils.extensionsFromVscodeMarketplace [
            {
              name = "moonlight";
              publisher = "atomiks";
              version = "0.11.1";
              sha256 = "0klbgjwx9hvjlri604j6i9scj005wbw31h7dxw5zzrnnlcxx2wb1";
            }
            {
              name = "nix";
              publisher = "bbenoist";
              version = "1.0.1";
              sha256 = "0zd0n9f5z1f0ckzfjr38xw2zzmcxg1gjrava7yahg5cvdcw6l35b";
            }
          ];
      userSettings = {
        # Theme
        "workbench.colorTheme" = "GitHub Light";
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
            "path" = "/Users/${username}/.nix-profile/bin/fish";
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
      worktrees = "git wt $(git wt | tail -n +2 | fzf | awk '{print $(NF-1)}')";
      workspace = "cd $(ghq root)/$(ghq list | fzf) && code --add .";
      gcps = ''gcloud config set project $(gcloud projects list --format="value(projectId)" | fzf) && echo -e "\nYour current config is:\n" && gcloud config list'';
      awsps = ''export AWS_PROFILE=$(aws configure list-profiles | fzf) && echo -e "\nSelected AWS Profile: $AWS_PROFILE"'';
      k8sctx = ''kubectl config use-context $(kubectl config get-contexts -o name | fzf) && echo -e "\nCurrent context:" && kubectl config current-context'';
      beep = "afplay /System/Library/Sounds/Glass.aiff";
      kubectl = "kubecolor";
    };

    interactiveShellInit = ''
      # Nix PATH
      fish_add_path /nix/var/nix/profiles/default/bin
      fish_add_path ~/.nix-profile/bin

      # oh-my-posh
      oh-my-posh init fish --config 'bubblesextra' | source

      # gcloud
      if test -f ~/.nix-profile/share/google-cloud-sdk/path.fish.inc
        source ~/.nix-profile/share/google-cloud-sdk/path.fish.inc
      end

      # aws cli completion
      if type -q aws_completer
        complete -c aws -f -a '(begin; set -lx COMP_SHELL fish; set -lx COMP_LINE (commandline); aws_completer | sed \'s/ $//\'; end)'
      end

      # aws profile completion for --profile flag
      complete -c aws -l profile -f -a '(aws configure list-profiles 2>/dev/null)'

      # kubectl context completion
      if type -q kubectl
        complete -c kubectl -l context -f -a '(kubectl config get-contexts -o name 2>/dev/null)'
        complete -c kubectl -n "config use-context" -f -a '(kubectl config get-contexts -o name 2>/dev/null)'
      end

      # git wt
      git wt --init fish | source
    '';

    loginShellInit = ''
      # gh cli - gh-triage extension
      if not gh extension list | grep -q "k1LoW/gh-triage"
        gh extension install k1LoW/gh-triage
      end

      # gh cli - gh-dash extension
      if not gh extension list | grep -q "dlvhdr/gh-dash"
        gh extension install dlvhdr/gh-dash
      end
    '';
  };

  programs.direnv = {
    enable = true;
    nix-direnv.enable = true;
  };

  programs.neovim = {
    enable = true;
    defaultEditor = true;
    vimAlias = true;
    viAlias = true;
  };

  xdg = {
    enable = true;
    dataFile."gh-triage/default.yml".source = ./gh-triage/default.yml;
    configFile."nvim/init.lua".source = ./nvim/init.lua;
  };

  # Let Home Manager install and manage itself.
  programs.home-manager.enable = true;
}
