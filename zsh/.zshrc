# If you come from bash you might have to change your $PATH.
# export PATH=$HOME/bin:/usr/local/bin:$PATH

export ZSH="$HOME/.oh-my-zsh"

ZSH_THEME="agnosterzak"

plugins=(
    git
    archlinux
    zsh-autosuggestions
    zsh-syntax-highlighting
)

source $ZSH/oh-my-zsh.sh

# Check archlinux plugin commands here
# https://github.com/ohmyzsh/ohmyzsh/tree/master/plugins/archlinux

# Display Pokemon-colorscripts
# Project page: https://gitlab.com/phoneybadger/pokemon-colorscripts#on-other-distros-and-macos
#pokemon-colorscripts --no-title -s -r #without fastfetch
if command -v pokemon-colorscripts >/dev/null && command -v fastfetch >/dev/null && [[ -f "$HOME/.config/fastfetch/config-pokemon.jsonc" ]]; then
    pokemon-colorscripts --no-title -s -r | fastfetch -c "$HOME/.config/fastfetch/config-pokemon.jsonc" --logo-type file-raw --logo-height 10 --logo-width 5 --logo -
fi

# fastfetch. Will be disabled if above colorscript was chosen to install
#fastfetch -c $HOME/.config/fastfetch/config-compact.jsonc

# Set-up icons for files/directories in terminal using lsd
alias ls='lsd'
alias l='ls -l'
alias la='ls -a'
alias lla='ls -la'
alias lt='ls --tree'

# Set-up FZF key bindings (CTRL R for fuzzy history finder)
source <(fzf --zsh)

HISTFILE=~/.zsh_history
HISTSIZE=10000
SAVEHIST=10000
setopt appendhistory

# ── App Aliases (background, silent) ────────────────────────────────────────
alias zalo='(/usr/bin/google-chrome-stable --profile-directory=Default --app-id=khmlcabibblfpfhmkfpaiblbijoggmaa > /dev/null 2>&1 &)'
alias chrome='(google-chrome-stable > /dev/null 2>&1 &)'
alias discord='(discord > /dev/null 2>&1 &)'
alias teamviewer='(teamviewer > /dev/null 2>&1 &)'
alias teams='(/usr/bin/google-chrome-stable --profile-directory=Default --app-id=cifhbcnohmdccbgoicgdjpfamggdegmo > /dev/null 2>&1 &)'
alias thunar='(thunar > /dev/null 2>&1 &)'
alias idea='(idea > /dev/null 2>&1 &)'
alias outlook='(/usr/bin/google-chrome-stable --profile-directory=Default --app-id=faolnafnngnfdaknnbpnkhgohbobgegn > /dev/null 2>&1 &)'
alias onedrive='(/usr/bin/google-chrome-stable --profile-directory=Default --app-id=pggjokkjodepmjbddgblmfheclnpjmod > /dev/null 2>&1 &)'
alias obs='(obs > /dev/null 2>&1 &)'
alias dbeaver='(dbeaver > /dev/null 2>&1 &)'
alias postman='(postman > /dev/null 2>&1 &)'
alias minecraft='(legacy-launcher > /dev/null 2>&1 &)'
