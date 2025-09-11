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
- font: menlo, 13pt
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
