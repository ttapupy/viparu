#!/usr/bin/env bash
# Explicit per-user GTK 4 installation. Never run automatically from the build.
set -euo pipefail

usage() {
    cat <<'EOF'
Usage: ./install-gtk.sh [--link|--copy|--update|--uninstall|--status|--help]

  --link       Link both user CSS files to libadwaita.css, plus assets (first-run default).
  --copy       Install a self-contained copy of those three entries instead.
  --update     Refresh this installation, retaining its mode (also the default).
  --uninstall  Remove managed entries and restore the original backups.
  --status     Show the active installation without changing anything.

Existing overrides are backed up before the first installation. Later updates
and uninstall refuse to overwrite entries changed by the user or another tool.
GTK 3, GNOME Shell, settings.ini and GSettings are not changed. Do not use sudo.
EOF
}

fail() { printf 'Error: %s\n' "$*" >&2; exit 1; }
exists() { [[ -e "$1" || -L "$1" ]]; }

# Traditional GTK theme CSS must not replace libadwaita's complete widget layout.
install_source() {
    case "$1" in
        gtk.css|gtk-dark.css) printf '%s/libadwaita.css\n' "$source_dir" ;;
        assets) printf '%s/assets\n' "$source_dir" ;;
    esac
}

[[ $# -le 1 ]] || { usage >&2; exit 2; }
action=${1:---update}
case "$action" in
    --help|-h) usage; exit 0 ;;
    --link|--copy|--update|--uninstall|--status) ;;
    *) usage >&2; exit 2 ;;
esac

for tool in readlink cp mv ln cmp diff mktemp; do
    command -v "$tool" >/dev/null || fail "Required command not found: $tool"
done

theme_dir=$(dirname -- "$(readlink -f -- "${BASH_SOURCE[0]}")")
source_dir="$theme_dir/gtk-4.0"
config_home=${XDG_CONFIG_HOME:-"$HOME/.config"}
state_home=${XDG_STATE_HOME:-"$HOME/.local/state"}
[[ "$config_home" = /* && "$state_home" = /* ]] || fail 'XDG directories must be absolute paths.'
[[ ! -L "$config_home/gtk-4.0" ]] || fail 'gtk-4.0 is a directory symlink; resolve that installation first.'
config_dir=$(readlink -m -- "$config_home/gtk-4.0")
state_dir=$(readlink -m -- "$state_home/vintage-pop-art-unified/gtk-4.0")
entries=(gtk.css gtk-dark.css assets)
managed=false
if [[ -d "$state_dir/installed" && -f "$state_dir/config-dir" ]]; then
    [[ $(cat -- "$state_dir/config-dir") == "$config_dir" ]] || fail "Installation state belongs to a different config directory: $state_dir"
    managed=true
fi

# Compare symlinks without following them, including dangling links after a move.
# For copies, also detect edited CSS and added/changed/removed asset files.
same_entry() {
    local actual=$1 recorded=$2
    if [[ -L "$recorded" ]]; then
        [[ -L "$actual" ]] && [[ $(readlink -- "$actual") == "$(readlink -- "$recorded")" ]]
    elif [[ -d "$recorded" ]]; then
        [[ -d "$actual" && ! -L "$actual" ]] && diff -qr -- "$recorded" "$actual" >/dev/null
    else
        [[ -f "$actual" && ! -L "$actual" ]] && cmp -s -- "$recorded" "$actual"
    fi
}

check_managed_entries() {
    local name
    for name in "${entries[@]}"; do
        if exists "$config_dir/$name" && ! same_entry "$config_dir/$name" "$state_dir/installed/$name"; then
            fail "Changed or replaced since installation: $config_dir/$name. Preserve your changes before continuing."
        fi
    done
}

if [[ "$action" == --status ]]; then
    printf 'GTK 4 config: %s\n' "$config_dir"
    if "$managed"; then
        printf 'Mode: %s\nTheme: %s\n' "$(cat -- "$state_dir/mode")" "$(cat -- "$state_dir/theme-dir")"
        for name in "${entries[@]}"; do
            if ! exists "$config_dir/$name"; then
                printf '  %s: missing\n' "$name"
            elif same_entry "$config_dir/$name" "$state_dir/installed/$name"; then
                if [[ -L "$config_dir/$name" && ! -e "$config_dir/$name" ]]; then
                    printf '  %s: managed link, target missing\n' "$name"
                else
                    printf '  %s: managed\n' "$name"
                fi
            else
                printf '  %s: changed or replaced\n' "$name"
            fi
        done
        if [[ -L "$config_dir/gtk.css" ]]; then
            printf 'CSS target: %s\n' "$(readlink -- "$config_dir/gtk.css")"
        fi
        printf 'Original backups: %s/previous\n' "$state_dir"
    else
        printf 'Not installed by this script. Existing user overrides, if any, are unmanaged.\n'
    fi
    exit 0
fi

(( EUID != 0 )) || fail 'Run this script as your desktop user, without sudo.'
if "$managed"; then
    check_managed_entries
fi

if [[ "$action" == --uninstall ]]; then
    "$managed" || { printf 'Nothing is installed by this script.\n'; exit 0; }
    mkdir -p -- "$config_dir"
    for name in "${entries[@]}"; do
        rm -rf -- "$config_dir/$name"
        if exists "$state_dir/previous/$name"; then
            mv -- "$state_dir/previous/$name" "$config_dir/$name"
            printf 'Restored: %s\n' "$config_dir/$name"
        fi
    done
    rm -rf -- "$state_dir/installed"
    rm -- "$state_dir/config-dir" "$state_dir/mode" "$state_dir/theme-dir"
    rmdir -- "$state_dir/previous" "$state_dir" 2>/dev/null || true
    printf 'GTK 4 overrides removed. Restart affected applications.\n'
    exit 0
fi

[[ "$source_dir" != "$config_dir" ]] || fail 'Theme source and config directory must differ.'
[[ -f "$source_dir/libadwaita.css" ]] || fail "Missing $source_dir/libadwaita.css; build the theme first."
[[ -d "$source_dir/assets" ]] || fail 'Missing GTK 4 assets; build the theme first.'

mode=link
if [[ "$action" == --copy ]]; then
    mode=copy
elif [[ "$action" == --update ]] && "$managed"; then
    mode=$(cat -- "$state_dir/mode")
fi
[[ "$mode" == link || "$mode" == copy ]] || fail "Unknown recorded mode: $mode"
if ! "$managed" && { exists "$state_dir/previous" || exists "$state_dir/installed"; }; then
    fail "Incomplete installation state at $state_dir; original backups were preserved."
fi

umask 077
mkdir -p -- "$config_dir" "$state_dir"
staging=$(mktemp -d "$state_dir/.install.XXXXXX")
trap 'rm -rf -- "$staging"' EXIT
trap 'printf "Installation interrupted; original backups are at %s/previous\n" "$state_dir" >&2' ERR
mkdir -- "$staging/new"
for name in "${entries[@]}"; do
    source_file=$(install_source "$name")
    if [[ "$mode" == link ]]; then
        ln -s -- "$source_file" "$staging/new/$name"
    else
        cp -aL -- "$source_file" "$staging/new/$name"
    fi
done

if ! "$managed"; then
    mkdir -- "$state_dir/previous"
    for name in "${entries[@]}"; do
        if exists "$config_dir/$name"; then
            cp -a -- "$config_dir/$name" "$state_dir/previous/$name"
            printf 'Backed up: %s\n' "$config_dir/$name"
        fi
    done
fi

for name in "${entries[@]}"; do
    rm -rf -- "$config_dir/$name"
    cp -a -- "$staging/new/$name" "$config_dir/$name"
    printf 'Installed (%s): %s\n' "$mode" "$config_dir/$name"
done
rm -rf -- "$state_dir/installed"
mv -- "$staging/new" "$state_dir/installed"
printf '%s\n' "$config_dir" > "$state_dir/config-dir"
printf '%s\n' "$theme_dir" > "$state_dir/theme-dir"
printf '%s\n' "$mode" > "$state_dir/mode"
printf 'Original backups: %s/previous\nRestart affected applications to reload the theme.\n' "$state_dir"
