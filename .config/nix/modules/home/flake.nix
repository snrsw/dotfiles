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
  };

  outputs =
    {
      nixpkgs,
      home-manager,
      brew-nix,
      ...
    }:
    let
      system = "aarch64-darwin";
      username = builtins.getEnv "USER";

      overlays = [
        brew-nix.overlays.default

        (final: prev: {
          git-wt = final.buildGoModule rec {
            pname = "git-wt";
            version = "0.15.0";

            src = final.fetchFromGitHub {
              owner = "k1LoW";
              repo = "git-wt";
              rev = "v${version}";
              hash = "sha256-A8vkwa8+RfupP9UaUuSVjkt5HtWvqR5VmSsVg2KpeMo=";
            };

            vendorHash = "sha256-K5geAvG+mvnKeixOyZt0C1T5ojSBFmx2K/Msol0HsSg=";
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
