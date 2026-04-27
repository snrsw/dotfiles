{
  description = "Home Manager configuration";

  inputs = {
    # Specify the source of Home Manager and Nixpkgs.
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    home-manager = {
      url = "github:nix-community/home-manager";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    brew-nix = {
      url = "github:BatteredBunny/brew-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    llm-agents.url = "github:numtide/llm-agents.nix";
  };

  outputs =
    {
      nixpkgs,
      home-manager,
      brew-nix,
      llm-agents,
      ...
    }:
    let
      system = "aarch64-darwin";
      username = builtins.getEnv "USER";

      overlays = [
        brew-nix.overlays.default
        llm-agents.overlays.default

        (final: prev: {
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
        modules = [ ./home.nix ];
        extraSpecialArgs = {
          inherit username;
        };
      };

      formatter.${system} = pkgs.nixfmt-rfc-style;
    };
}
