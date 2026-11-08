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
# Without lsd, keep plain ls usable in a TTY or a partial install.
if command -v lsd >/dev/null; then
    alias ls='lsd'
    alias lt='ls --tree'
fi
alias l='ls -l'
alias la='ls -a'
alias lla='ls -la'

# Set-up FZF key bindings (CTRL R for fuzzy history finder)
if command -v fzf >/dev/null; then
    source <(fzf --zsh)
fi

HISTFILE=~/.zsh_history
HISTSIZE=10000
SAVEHIST=10000
setopt appendhistory

# ── App Launchers (background, silent) ──────────────────────────────────────
# Functions, unlike aliases ending in `)`, accept arguments such as `idea .`.
# The `function` keyword also keeps re-sourcing safe in shells with old aliases.
function _launch_bg { ( "$@" > /dev/null 2>&1 & ) }
function zalo { _launch_bg /usr/bin/google-chrome-stable --profile-directory=Default --app-id=khmlcabibblfpfhmkfpaiblbijoggmaa "$@"; }
function chrome { _launch_bg command google-chrome-stable "$@"; }
function discord { _launch_bg command discord "$@"; }
function teamviewer { _launch_bg command teamviewer "$@"; }
function teams { _launch_bg /usr/bin/google-chrome-stable --profile-directory=Default --app-id=cifhbcnohmdccbgoicgdjpfamggdegmo "$@"; }
function thunar { _launch_bg command thunar "$@"; }
function idea { _launch_bg command idea "$@"; }
function outlook { _launch_bg /usr/bin/google-chrome-stable --profile-directory=Default --app-id=faolnafnngnfdaknnbpnkhgohbobgegn "$@"; }
# Keep `onedrive` available for the native sync client.
function onedrive-web { _launch_bg /usr/bin/google-chrome-stable --profile-directory=Default --app-id=pggjokkjodepmjbddgblmfheclnpjmod "$@"; }
function obs { _launch_bg command obs "$@"; }
function dbeaver { _launch_bg command dbeaver "$@"; }
function postman { _launch_bg command postman "$@"; }
function minecraft { _launch_bg command legacy-launcher "$@"; }
function parsecd { _launch_bg command parsecd "$@"; }
function drawing { _launch_bg command drawing "$@"; }
