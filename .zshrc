# paths
typeset -U path PATH
path=(
  /opt/homebrew/bin(N-/)
  /opt/homebrew/sbin(N-/)
  /usr/bin
  /usr/sbin
  /bin
  /sbin
  /usr/local/bin(N-/)
  /usr/local/sbin(N-/)
  /Library/Apple/usr/bin
)

# mise
eval "$(mise activate bash)"

## go
export PATH=$(go env GOPATH)/bin:$PATH

## cargo
source $HOME/.cargo/env

## bun
export BUN_INSTALL="$HOME/Library/Application Support/reflex/bun"
export PATH="$BUN_INSTALL/bin:$PATH"
export VOLTA_HOME="$HOME/.volta"
export PATH="$VOLTA_HOME/bin:$PATH"

## java
export PATH="/opt/homebrew/opt/openjdk/bin:$PATH"

# alias
if [[ $(command -v bat) ]]; then
  alias cat='bat'
fi

if [[ $(command -v eza) ]]; then
  alias ls='eza --icons --git'
  alias la='eza -T -L 1 -a -l --icons'
  alias lt='eza -T -L 3 -a --icons'
  alias lta='eza -T -L 3 -a -l --icons'
fi

alias repos='cd $(ghq root)/$(ghq list | peco)'
alias getrepo='ghq get'

alias workspace='cd $(ghq root)/$(ghq list | peco) && code --add .'

alias gcps='gcloud config set project $(gcloud projects list --format="value(projectId)" | peco) && echo -e "\nYour current config is:\n" && gcloud config list'

alias beep='afplay /System/Library/Sounds/Glass.aiff'

alias todo='cd ~/src/github.com/snarisawa/todo && code .'

# settings
source "${ZDOTDIR:-$HOME}/.zprezto/init.zsh"

export EDITOR=/usr/local/bin/code

## Google Cloud SDK
source "$(brew --prefix)/share/google-cloud-sdk/path.zsh.inc"
source "$(brew --prefix)/share/google-cloud-sdk/completion.zsh.inc"


# Created by `pipx` on 2024-10-29 08:29:51
export PATH="$PATH:$HOME/.local/bin"

fpath+=~/.zfunc; autoload -Uz compinit; compinit

zstyle ':completion:*' menu select
export PATH="/opt/homebrew/opt/mysql-client@8.0/bin:$PATH"
alias claude="$HOME/.claude/local/claude"

