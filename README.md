dotfiles
===

```shell
curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install
```

```shell
git clone https://github.com/snrsw/dotfiles.git ~/src/github.com/snrsw/dotfiles
cd ~/src/github.com/snrsw/dotfiles
```

```shell
nix run home-manager/master -- switch --flake .config/nix/modules/home/
```
