# paths

export PATH="$HOME/.local/bin:$PATH"

# tools

## mise

eval "$(mise activate bash)"

## fzf

source <(fzf --zsh)

# terminal

## alias

alias cat='bat'

alias ls='eza --icons --git'
alias la='eza -T -L 1 -a -l --icons'
alias lt='eza -T -L 3 -a --icons'
alias lta='eza -T -L 3 -a -l --icons'

alias repos='cd $(ghq root)/$(ghq list | fzf)'
alias getrepo='ghq get'

alias workspace='cd $(ghq root)/$(ghq list | fzf) && code --add .'

alias gcps='gcloud config set project $(gcloud projects list --format="value(projectId)" | fzf) && echo -e "\nYour current config is:\n" && gcloud config list'

alias beep='afplay /System/Library/Sounds/Glass.aiff'

## theme

if [[ -s "${ZDOTDIR:-$HOME}/.zprezto/init.zsh" ]]; then
  source "${ZDOTDIR:-$HOME}/.zprezto/init.zsh"
fi
