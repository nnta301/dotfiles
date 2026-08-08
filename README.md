<div align="center">

# 🏗️ Arch Linux Dotfiles

**Personal override layer for Arch Linux + JaKooLit Hyprland ecosystem**

![Arch Linux](https://img.shields.io/badge/Arch_Linux-1793D1?style=for-the-badge&logo=arch-linux&logoColor=white)
![Hyprland](https://img.shields.io/badge/Hyprland-58E1FF?style=for-the-badge&logo=hyprland&logoColor=black)
![Neovim](https://img.shields.io/badge/Neovim-57A143?style=for-the-badge&logo=neovim&logoColor=white)
![Zsh](https://img.shields.io/badge/Zsh-F15A24?style=for-the-badge&logo=zsh&logoColor=white)
![Fcitx5](https://img.shields.io/badge/Fcitx5_🇻🇳_Bamboo-4EAA25?style=for-the-badge)

</div>

---

## 📐 Architecture Philosophy

This repo does **not** track the entire Hyprland configuration. Instead, it acts as a
**personal override layer** that sits on top of
[JaKooLit's upstream Hyprland dotfiles](https://github.com/JaKooLit/Arch-Hyprland).

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: JaKooLit Upstream (NOT tracked here)                  │
│  └─ Core Hyprland config, Waybar, themes, scripts, animations   │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: This Repo — Personal Overrides                        │
│  ├─ hypr/   → UserConfigs/ only (hardware + input method)       │
│  ├─ zsh/    → .zshrc with Oh-My-Zsh + all personal aliases      │
│  └─ nvim/   → Full LazyVim config (independent of WM)           │
└─────────────────────────────────────────────────────────────────┘
```

**Why this approach:**
- ✅ Always receive upstream bug fixes and theme updates from JaKooLit
- ✅ Personal configs are version-controlled separately, small and focused
- ✅ Clean reinstall: run upstream script → apply this overlay → done

---

## 📋 Contents

- [System Summary](#-system-summary)
- [3-Step Reinstall Workflow](#-3-step-reinstall-workflow)
- [Repository Structure](#-repository-structure)
- [Hyprland UserConfigs — Key Overrides](#-hyprland-userconfigs--key-overrides)
- [Keybindings](#-keybindings)

---

## 💻 System Summary

| Component | Choice |
|---|---|
| **Distro** | Arch Linux (rolling release) |
| **Window Manager** | Hyprland via [JaKooLit/Arch-Hyprland](https://github.com/JaKooLit/Arch-Hyprland) |
| **Terminal** | Kitty |
| **Shell** | Zsh + Oh-My-Zsh (theme: agnosterzak) |
| **Editor** | Neovim (LazyVim distribution) |
| **Status Bar** | Waybar (managed by JaKooLit upstream) |
| **Input Method** | Fcitx5 + Bamboo (Vietnamese — Tiếng Việt) |
| **Audio** | PipeWire |
| **Dotfiles Manager** | GNU Stow |

---

## 🚀 3-Step Reinstall Workflow

### Step 1 — Run JaKooLit Upstream Install

> ⚠️ **Do this first.** This creates the full Hyprland environment including
> core configs, Waybar, themes, and all dependencies.

```bash
git clone --depth=1 https://github.com/JaKooLit/Arch-Hyprland.git ~/JaKooLit-Arch
cd ~/JaKooLit-Arch
chmod +x install.sh
./install.sh
```

This populates `~/.config/hypr/` with the upstream default configs.
Log in to Hyprland at least once to verify it works before proceeding.

---

### Step 2 — Patch Deprecated Dispatchers (if needed)

> ℹ️ Only required if Hyprland throws deprecation warnings about `togglesplit`,
> `pseudotile`, or `vfr`. Check [JaKooLit's issue tracker](https://github.com/JaKooLit/Arch-Hyprland/issues)
> to see if the upstream has been updated first.

```bash
# Comment out deprecated keybind dispatchers
sed -i '/togglesplit/s/^/#/' ~/.config/hypr/UserConfigs/UserKeybinds.conf
sed -i '/pseudotile/s/^/#/'  ~/.config/hypr/UserConfigs/UserKeybinds.conf

# Comment out deprecated misc option
sed -i '/^\s*vfr\s*=/s/^/#/' ~/.config/hypr/hyprland.conf
```

---

### Step 3 — Apply Personal Override (This Repo)

```bash
# Clone this repo
git clone https://github.com/nnta301/dotfiles.git ~/dotfiles
cd ~/dotfiles

# Run the setup script (handles stowing + JaKooLit compatibility)
chmod +x setup.sh
./setup.sh

# — OR — apply manually with stow:
# Remove upstream's default UserConfigs so our symlink can take its place
rm -rf ~/.config/hypr/UserConfigs
stow hypr      # → ~/.config/hypr/UserConfigs/ (our overrides)
stow zsh       # → ~/.zshrc
stow nvim      # → ~/.config/nvim/
```

After stowing, log out and back in (or restart Hyprland with `SUPER + M`).

---

## 📁 Repository Structure

```
dotfiles/
├── 📄 .gitignore                  ← Excludes secrets, caches, nvim lock file
├── 📄 README.md                   ← This file
├── 📄 pkglist.txt                 ← Package list for reference
├── 📄 setup.sh                    ← One-shot setup script
│
├── 📂 hypr/                       ← Stow package: Hyprland UserConfigs ONLY
│   └── .config/hypr/
│       └── UserConfigs/           ← Replaces upstream's defaults
│           ├── LaptopDisplay.conf     ← eDP-1 scale 1 (hardware fix)
│           ├── Startup_Apps.conf      ← exec-once = fcitx5 -d
│           ├── ENVariables.conf       ← Fcitx5 env vars (Qt + X11)
│           ├── UserKeybinds.conf      ← Personal keybindings
│           ├── UserSettings.conf      ← Personal Hyprland settings
│           ├── UserAnimations.conf    ← Animation preferences
│           ├── UserDecorations.conf   ← Decoration preferences
│           ├── WindowRules.conf       ← Window rules
│           ├── WorkSpaceRules.conf    ← Workspace rules
│           └── Laptops.conf           ← Lid-close behaviour
│
├── 📂 zsh/                        ← Stow package: Shell (primary)
│   └── .zshrc                     ← Oh-My-Zsh + lsd + fzf + app aliases
│
├── 📂 nvim/                       ← Stow package: Neovim (LazyVim)
│   └── .config/nvim/
│       ├── init.lua
│       ├── lazyvim.json
│       ├── stylua.toml
│       └── lua/
│           ├── config/            ← autocmds, keymaps, lazy, options
│           └── plugins/           ← custom plugin specs
│
└── 📂 scripts/                    ← Utility scripts
    └── cleanup.sh                 ← Pacman cache + orphan + journal cleanup
```

> 💡 `lazy-lock.json` is excluded from tracking by `.gitignore` to avoid
> noisy diffs on every `:Lazy update`. Add it back intentionally if you want
> pinned exact plugin versions.

---

## 🔧 Hyprland UserConfigs — Key Overrides

### `LaptopDisplay.conf` — Monitor Scale

```conf
# Disables upstream's 1.5× HiDPI scale for eDP-1
monitor = eDP-1, preferred, auto, 1
```

This overrides JaKooLit's default which may set a fractional scale. `1` = 100%,
correct for this display without blurry XWayland apps.

---

### `Startup_Apps.conf` — Fcitx5 Autostart

```conf
exec-once = fcitx5 -d
```

Launches the Fcitx5 daemon in the background on Hyprland startup, required for
Vietnamese input (Bamboo engine) to work across all applications.

---

### `ENVariables.conf` — Input Method Environment

```conf
env = QT_IM_MODULE, fcitx
env = XMODIFIERS, @im=fcitx
```

> ⚠️ **`GTK_IM_MODULE` is intentionally absent.** GTK4 dropped support for
> `GTK_IM_MODULE` — setting it causes regressions in GTK4 apps. Fcitx5 handles
> GTK4 integration automatically via its D-Bus portal.

---

## ⌨️ Keybindings

> These are set in `UserConfigs/UserKeybinds.conf` and may differ from JaKooLit defaults.

| Shortcut | Action |
|---|---|
| `SUPER + Q` | Open terminal (Kitty) |
| `SUPER + C` | Close window |
| `SUPER + E` | Open file manager |
| `SUPER + R` | Open app launcher |
| `SUPER + V` | Toggle floating |
| `SUPER + M` | Exit Hyprland |
| `SUPER + [1–0]` | Switch workspace |
| `SUPER + SHIFT + [1–0]` | Move window to workspace |
| `SUPER + Arrow Keys` | Move focus |
| `SUPER + SHIFT + Arrow Keys` | Move window |
| `Print` | Full screenshot |
| `SUPER + SHIFT + S` | Region screenshot |
| `XF86Audio*` | Volume control |
| `XF86MonBrightness*` | Brightness control |

---

## 📜 License

Personal configuration — free to use and adapt.

---

<div align="center">

*Made with ❤️ on Arch Linux*

</div>
