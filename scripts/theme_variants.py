"""Shared variant identities and clean source snapshots for builds/releases."""

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "README.md", "USAGE.md", "DEVELOPMENT.md", "THIRD_PARTY.md", "LICENSE", "screenshot.png",
    "index.theme", "install-gtk.sh", "color-palette.json", "color-palette.scss",
    "theme-variants.json", "theme-variant",
)
DIRECTORIES = (
    "assets", "common", "gnome-shell", "gtk-3.0", "gtk-4.0", "licenses",
    "scripts", "scss", "tests",
)


def load_variants(root=ROOT):
    variants = json.loads((root / "theme-variants.json").read_text(encoding="utf-8"))
    if not isinstance(variants, dict) or not variants:
        raise ValueError("theme-variants.json must be a nonempty object")
    palette = json.loads((root / "color-palette.json").read_text(encoding="utf-8"))
    names = set()
    for key, variant in variants.items():
        if not re.fullmatch(r"[a-z][a-z0-9-]*", key):
            raise ValueError(f"Invalid variant ID: {key!r}")
        required = {"name", "sidebar_base", "sidebar_hover"}
        if (not isinstance(variant, dict) or not required.issubset(variant)
                or set(variant) - required - {"shell_accent", "shell_toggle_bg", "shell_toggle_fg", "sidebar_selection"}):
            raise ValueError(f"Invalid variant definition: {key}")
        name = variant["name"]
        if not isinstance(name, str) or not re.fullmatch(r"Viparu-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*", name):
            raise ValueError(f"Invalid theme name: {name!r}")
        if name in names:
            raise ValueError(f"Duplicate theme name: {name}")
        names.add(name)
        for role in ("sidebar_base", "sidebar_hover", "shell_accent", "shell_toggle_bg", "shell_toggle_fg", "sidebar_selection"):
            if role not in variant:
                continue
            color = variant[role]
            if not isinstance(color, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", color) or color not in palette:
                raise ValueError(f"Unknown palette color for {key}/{role}: {color!r}")
    return variants


def selected_variant(root=ROOT):
    key = (root / "theme-variant").read_text(encoding="utf-8").strip()
    variants = load_variants(root)
    if key not in variants:
        raise ValueError(f"Unknown selected theme variant: {key!r}")
    return key, variants[key]


def generate_variant(root=ROOT):
    key, variant = selected_variant(root)
    assignments = (
        "// Generated from theme-variants.json and theme-variant; do not edit.\n"
        f"$gp-sidebar-base: ${variant['sidebar_base']};\n"
        f"$gp-sidebar-hover-color: ${variant['sidebar_hover']};\n"
    )
    if "shell_accent" in variant:
        assignments += f"$gp-shell-accent-override: ${variant['shell_accent']};\n"
    if "shell_toggle_bg" in variant:
        assignments += f"$gp-shell-toggle-bg: ${variant['shell_toggle_bg']};\n"
    if "shell_toggle_fg" in variant:
        assignments += f"$gp-shell-toggle-fg: ${variant['shell_toggle_fg']};\n"
    if "sidebar_selection" in variant:
        assignments += f"$gp-sidebar-selection-bg: ${variant['sidebar_selection']};\n"
    (root / "scss/_variant.scss").write_text(assignments, encoding="utf-8")
    name = variant["name"]
    (root / "index.theme").write_text(
        "[Desktop Entry]\nType=X-GNOME-Metatheme\n"
        f"Name={name}\n"
        "Comment=Unified GTK and GNOME Shell theme with light content and dark chrome\n\n"
        f"[X-GNOME-Metatheme]\nGtkTheme={name}\n",
        encoding="utf-8",
    )
    return key


def project_files(root=ROOT):
    files = []
    for name in FILES + DIRECTORIES:
        source = root / name
        if source.is_symlink() or not source.exists():
            raise ValueError(f"Missing package input or unsupported symlink: {name}")
        paths = sorted(source.rglob("*")) if source.is_dir() else [source]
        for path in paths:
            relative = path.relative_to(root)
            if any(part.startswith(".") or part == "__pycache__" for part in relative.parts):
                continue
            if path.suffix in (".pyc", ".pyo"):
                continue
            if path.is_symlink():
                raise ValueError(f"Symlinks are not allowed in package inputs: {relative}")
            if path.is_file():
                files.append(path)
    return sorted(files)


def copy_project(destination, key, root=ROOT):
    if key not in load_variants(root):
        raise ValueError(f"Unknown theme variant: {key!r}")
    for source in project_files(root):
        target = destination / source.relative_to(root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    (destination / "theme-variant").write_text(key + "\n", encoding="utf-8")
