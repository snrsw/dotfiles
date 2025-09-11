dotfiles
===

# setup
setup way after download dotfiles. For example, see https://qiita.com/ucan-lab/items/c1a12c20c878d6fb1e21.
## Xcode
```
xcode-select --install
```

## Homebrew
```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
```
brew update
```

## ghq, peco
```console
brew install ghq
```
```console
git config --global ghq.root ~/src
```
```console
brew install peco
```

## zsh
### prezto
```
git clone --recursive https://github.com/sorin-ionescu/prezto.git "${ZDOTDIR:-$HOME}/.zprezto"
```
```
setopt EXTENDED_GLOB
for rcfile in "${ZDOTDIR:-$HOME}"/.zprezto/runcoms/^README.md(.N); do
  ln -s "$rcfile" "${ZDOTDIR:-$HOME}/.${rcfile:t}"
done
```
```
exec $SHELL -l
```

### theme
- iceberg: https://github.com/cocopon/iceberg.vim/
- font: fira mono, 14pt
  - `brew install --cask font-fira-mono-nerd-font`
- 90%

### tools
```
brew install eza bat
```

## git/github

```
brew install gh
```
```
gh auth login
```

### check
```
ssh github.com
```

## mise
```
brew install mise
```

## Docker

```
brew install orbstack
```

## Python

## VScode

```
brew install --cask visual-studio-code
```

## clip board

https://github.com/Clipy/Clipy

## google cloud cli
```
brew install --cask google-cloud-sdk
```
```
gcloud init
```

## aws cli
```
brew install awscli
```
```
aws configure
```

## claude code
```
curl -fsSL https://claude.ai/install.sh | zsh
```

## codex
```
brew install codex
```

## Others

* 1password: https://1password.com/jp/downloads/mac/
* 1password for chrome: https://chromewebstore.google.com/detail/1password-%E2%80%93-password-mana/aeblfdkhhhdcdjpifhhbdiojplfjncoa?hl=ja
