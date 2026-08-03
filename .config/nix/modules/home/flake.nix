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
    # prv: private "Pull-Request like View" CLI. Fetch over SSH (private repo);
    # keep its own nixpkgs pin so the node_modules FOD hash stays valid.
    prv.url = "git+ssh://git@github.com/snrsw/prv";
    llm-agents.url = "github:numtide/llm-agents.nix";
    nix-claude-code.url = "github:ryoppippi/nix-claude-code";
    nix-index-database.url = "github:nix-community/nix-index-database";
    nix-index-database.inputs.nixpkgs.follows = "nixpkgs";
    # nixGL: wraps GUI apps so they find the host's OpenGL driver. Needed only
    # on a non-NixOS distro, where the driver lives outside the Nix store.
    nixgl = {
      url = "github:nix-community/nixGL";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    {
      nixpkgs,
      home-manager,
      brew-nix,
      crit,
      prv,
      llm-agents,
      nix-claude-code,
      nix-index-database,
      nixgl,
      ...
    }:
    let
      lib = nixpkgs.lib;
      username = builtins.getEnv "USER";

      systems = [
        "aarch64-darwin"
        "x86_64-linux"
      ];
      isDarwin = system: lib.hasSuffix "darwin" system;

      # Tools with no nixpkgs package, installed from an upstream release
      # archive. Asset naming is not uniform — `mo` ships .zip on darwin but
      # .tar.gz on linux — so record the exact asset name and unpacked hash
      # per system rather than deriving either.
      moAsset = {
        aarch64-darwin = {
          name = "mo_v0.20.1_darwin_arm64.zip";
          hash = "sha256-MUUOR2sHdNUJXpHHeyQYFyRWX1Fm6DbQybJeh8CQHZc=";
        };
        x86_64-linux = {
          name = "mo_v0.20.1_linux_amd64.tar.gz";
          hash = "sha256-RQ2ZZcN0MARlrdxKswfIDNaXoDbR7QNpHrCJ5xh25Ew=";
        };
      };
      newrelicAsset = {
        aarch64-darwin = {
          name = "newrelic-cli_0.111.7_Darwin_arm64.tar.gz";
          hash = "sha256-qb09bIWrYX1bTTzLJ+vVDYGvyeI8z4vULzPSKgYfdOI=";
        };
        x86_64-linux = {
          name = "newrelic-cli_0.111.7_Linux_x86_64.tar.gz";
          hash = "sha256-9gxpOrDqCqrCrOnIzPN5csfJLAD5bKYHh3Iv2KRl4wY=";
        };
      };

      overlaysFor =
        system:
        [
          nix-claude-code.overlays.default
        ]
        # brew-nix exposes Homebrew casks, which exist only on darwin.
        ++ lib.optionals (isDarwin system) [ brew-nix.overlays.default ]
        ++ [
          (final: prev: {
            # llm-agents.nix dropped its blueprint-based `overlays` output;
            # expose its packages under `pkgs.llm-agents.<name>` ourselves to
            # keep home.nix's `llm-agents.codex` / `llm-agents.gemini-cli` refs working.
            llm-agents = llm-agents.packages.${final.stdenv.hostPlatform.system} or { };

            crit = crit.packages.${final.stdenv.hostPlatform.system}.default;
            prv = prv.packages.${final.stdenv.hostPlatform.system}.default;

            direnv = prev.direnv.overrideAttrs (_: { doCheck = false; });

            mo = final.stdenv.mkDerivation rec {
              pname = "mo";
              version = "0.20.1";

              src = final.fetchzip {
                url = "https://github.com/k1LoW/mo/releases/download/v${version}/${moAsset.${final.stdenv.hostPlatform.system}.name}";
                hash = moAsset.${final.stdenv.hostPlatform.system}.hash;
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
                url = "https://github.com/newrelic/newrelic-cli/releases/download/v${version}/${newrelicAsset.${final.stdenv.hostPlatform.system}.name}";
                hash = newrelicAsset.${final.stdenv.hostPlatform.system}.hash;
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
        ]
        # VS Code 1.129 moved the bundled ripgrep (`@vscode/ripgrep-universal`,
        # introduced in 1.122) into `node_modules.asar.unpacked` on darwin, but
        # nixpkgs' generic.nix still chmods it under plain `node_modules`, so the
        # darwin build fails with:
        #   chmod: cannot access '.../@vscode/ripgrep-universal/bin/darwin-arm64/rg'
        # Point the chmod at the real path. The path is inside the macOS .app
        # bundle, so this override is darwin-only — linux ships plain vscode.
        # Drop it once nixpkgs chmods the darwin ripgrep under
        # node_modules.asar.unpacked.
        ++ lib.optionals (isDarwin system) [
          (final: prev: {
            vscode = prev.vscode.overrideAttrs (_: {
              postPatch = ''
                chmod +x "Contents/Resources/app/node_modules.asar.unpacked/@vscode/ripgrep-universal/bin/darwin-arm64/rg"
              '';
            });

            # terminal-browser: not in nixpkgs and ships no flake. Upstream
            # installs it with a shell script that fetches one prebuilt tarball,
            # and that script refuses anything but Apple Silicon macOS, so the
            # package is darwin-only. Bump version and hash together; there is
            # no release asset on GitHub, the artifact lives on their own host.
            terminal-browser = final.stdenv.mkDerivation rec {
              pname = "terminal-browser";
              version = "0.3.3";

              src = final.fetchzip {
                url = "https://terminal-browser.sh/install/dl/stable/v${version}/terminal-browser-darwin-arm64.tar.gz";
                hash = "sha256-xXxX/80RrTDNHj7MHMuDenkqOfefulHspJV8BzhwaNY=";
              };

              # `bin/terminal-browser` derives its resource root from its own
              # location (`dirname $0/..`), so the tree has to stay intact and
              # $out/bin must hold the real script. A symlink there would make
              # the root resolve to $out and the electron app would go missing.
              installPhase = ''
                runHook preInstall
                mkdir -p "$out"
                cp -R . "$out/"
                chmod +x "$out/bin/terminal-browser"
                runHook postInstall
              '';

              # The payload is a signed Mach-O binary plus an Electron app
              # bundle. Stripping them invalidates the signature, which arm64
              # macOS refuses to run, so skip fixup entirely.
              dontFixup = true;

              meta = {
                description = "A browser that runs directly inside your existing terminal";
                homepage = "https://github.com/zenbu-labs/terminal-browser";
                platforms = [ "aarch64-darwin" ];
              };
            };
          })
        ];

      pkgsFor =
        system:
        import nixpkgs {
          inherit system;
          overlays = overlaysFor system;
          config.allowUnfree = true;
        };

      mkHome =
        system:
        home-manager.lib.homeManagerConfiguration {
          pkgs = pkgsFor system;
          modules = [
            ./home.nix
            (if isDarwin system then ./darwin.nix else ./linux.nix)
            nix-index-database.homeModules.default
          ];
          extraSpecialArgs = {
            inherit username nixgl;
            # crit's Claude Code plugin lives in the same repo as the CLI; reuse
            # the flake input's source so it stays in sync with `nix flake update crit`.
            critPluginSrc = "${crit}/integrations/claude-code";
            critRev = crit.rev or "";
          };
        };
    in
    {
      homeConfigurations =
        # Explicit per-system targets, so either platform's config can be
        # evaluated (or built, given a builder) from the other machine.
        lib.listToAttrs (
          map (system: {
            name = "${username}@${system}";
            value = mkHome system;
          }) systems
        )
        // {
          # Bare `$USER` follows the machine you are on, keeping one switch
          # command for both platforms. The flake already reads $USER, so
          # evaluation is impure either way.
          ${username} = mkHome builtins.currentSystem;
        };

      formatter = lib.genAttrs systems (system: (pkgsFor system).nixfmt-rfc-style);
    };
}
