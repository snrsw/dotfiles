{
  description = "Home Manager configuration";

  inputs = {
    # Specify the source of Home Manager and Nixpkgs.
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    home-manager = {
      url = "github:nix-community/home-manager";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    # brew-api carries the Homebrew cask data; track it directly so
    # `nix flake update brew-api` keeps casks (e.g. cotypist) current.
    brew-api = {
      url = "github:BatteredBunny/brew-api";
      flake = false;
    };
    brew-nix = {
      url = "github:BatteredBunny/brew-nix";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.brew-api.follows = "brew-api";
    };
    # crit: browser-based markdown/diff review tool (Go CLI). Upstream ships a
    # flake; follow our nixpkgs and expose its package via an overlay below.
    crit = {
      url = "github:tomasz-tomczyk/crit";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    llm-agents.url = "github:numtide/llm-agents.nix";
    nix-claude-code.url = "github:ryoppippi/nix-claude-code";
    nix-index-database.url = "github:nix-community/nix-index-database";
    nix-index-database.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs =
    {
      nixpkgs,
      home-manager,
      brew-nix,
      crit,
      llm-agents,
      nix-claude-code,
      nix-index-database,
      ...
    }:
    let
      system = "aarch64-darwin";
      username = builtins.getEnv "USER";

      overlays = [
        brew-nix.overlays.default
        llm-agents.overlays.default
        nix-claude-code.overlays.default

        (final: prev: {
          crit = crit.packages.${final.system}.default;

          direnv = prev.direnv.overrideAttrs (_: { doCheck = false; });

          mo = final.stdenv.mkDerivation rec {
            pname = "mo";
            version = "0.20.1";

            src = final.fetchzip {
              url = "https://github.com/k1LoW/mo/releases/download/v${version}/mo_v${version}_darwin_arm64.zip";
              hash = "sha256-MUUOR2sHdNUJXpHHeyQYFyRWX1Fm6DbQybJeh8CQHZc=";
              stripRoot = false;
            };

            installPhase = ''
              install -Dm755 mo $out/bin/mo
            '';
          };

          newrelic-cli = final.stdenv.mkDerivation rec {
            pname = "newrelic-cli";
            version = "0.111.7";

            src = final.fetchzip {
              url = "https://github.com/newrelic/newrelic-cli/releases/download/v${version}/newrelic-cli_${version}_Darwin_arm64.tar.gz";
              hash = "sha256-qb09bIWrYX1bTTzLJ+vVDYGvyeI8z4vULzPSKgYfdOI=";
              stripRoot = false;
            };

            installPhase = ''
              install -Dm755 newrelic $out/bin/newrelic
            '';
          };

          git-wt = final.buildGoModule rec {
            pname = "git-wt";
            version = "0.25.0";

            src = final.fetchFromGitHub {
              owner = "k1LoW";
              repo = "git-wt";
              rev = "v${version}";
              hash = "sha256-QdyONDVokpOaH5dI5v1rmaymCgIiWZ16h26FAIsAHPc=";
            };

            vendorHash = "sha256-O4vqouNxvA3GvrnpRO6GXDD8ysPfFCaaSJVFj2ufxwI=";
            subPackages = [ "." ];
            ldflags = [ "-s" "-w" ];
          };

          roots = final.buildGoModule rec {
            pname = "roots";
            version = "0.4.1";

            src = final.fetchFromGitHub {
              owner = "k1LoW";
              repo = "roots";
              rev = "v${version}";
              hash = "sha256-ACMRfWY/lhc3C/KVhuUyS1rgkSHGWPxZrmYt+pXupJI=";
            };

            vendorHash = "sha256-uxcT5VzlTCxxnx09p13mot0wVbbas/otoHdg7QSDt4E=";
            subPackages = [ "." ];
            ldflags = [ "-s" "-w" ];
          };
        })
      ];

      pkgs = import nixpkgs {
        inherit system overlays;
        config.allowUnfree = true;
      };
    in
    {
      homeConfigurations.${username} = home-manager.lib.homeManagerConfiguration {
        inherit pkgs;
        modules = [
          ./home.nix
          nix-index-database.homeModules.default
        ];
        extraSpecialArgs = {
          inherit username;
          # crit's Claude Code plugin lives in the same repo as the CLI; reuse
          # the flake input's source so it stays in sync with `nix flake update crit`.
          critPluginSrc = "${crit}/integrations/claude-code";
          critRev = crit.rev or "";
        };
      };

      formatter.${system} = pkgs.nixfmt-rfc-style;
    };
}
