dotfiles
===

# Setup Instructions

## Install Nix package manager

```shell
curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install
```

## Clone this repository

```shell
git clone https://github.com/snrsw/dotfiles.git ~/src/github.com/snrsw/dotfiles
cd ~/src/github.com/snrsw/dotfiles
```

## Apply Home Manager configuration

```shell
nix run home-manager/master -- switch --flake .config/nix/modules/home/ --impure
```

# Daily Usage

## Update Home Manager configuration

```shell
nix flake update --flake .config/nix/modules/home/
```

## Re-apply Home Manager configuration

```shell
nix run home-manager/master -- switch --flake .config/nix/modules/home/ --impure
```

# Developer Instructions

## Fetch VSCode extension SHA256

```shell
nix-prefetch-url --type sha256 https://marketplace.visualstudio.com/_apis/public/gallery/publishers/{{ PUBLISHER }}/vsextensions/{{ NAME }}/{{ VERSION }}/vspackage
