#!/usr/bin/env python3
"""Build Viparu locally, or build standalone color variants without activating them."""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from palette import ROOT, generate
from theme_variants import copy_project, generate_variant, load_variants


def compiler_command():
    environment = os.environ.copy()
    compiler = shutil.which("sassc")
    if not compiler:
        local = ROOT / ".build-tools/usr/bin/sassc"
        if not local.is_file():
            raise RuntimeError("sassc / LibSass is required. On Ubuntu: sudo apt install sassc")
        compiler = str(local)
        directories = sorted({str(path.parent) for path in
                              (ROOT / ".build-tools/usr/lib").glob("*/libsass.so*")})
        if directories:
            previous = environment.get("LD_LIBRARY_PATH")
            if previous:
                directories.append(previous)
            environment["LD_LIBRARY_PATH"] = os.pathsep.join(directories)
    return compiler, environment


def collect_assets(stylesheets, root=ROOT):
    """Resolve every CSS image before publishing; copy only referenced Yaru assets."""
    assets = {}
    for destination, content in stylesheets.items():
        css = re.sub(r"/\*.*?\*/", "", content.decode("utf-8"), flags=re.DOTALL)
        for url in re.findall(r"url\(\s*[\"']?([^\"')\s]+)", css):
            if ":" in url or Path(url).is_absolute():
                raise ValueError(f"Non-local theme asset in {destination}: {url}")
            target = (root / destination).parent / url
            target = target.resolve()
            if not target.is_relative_to(root):
                raise ValueError(f"Asset escapes the theme directory: {url}")
            version = Path(destination).parts[0]
            if version in ("gtk-3.0", "gtk-4.0") and url.startswith("assets/"):
                source = root / "scss/yaru" / version / url
                if not source.is_file():
                    source = root / url
            else:
                source = target
            if not source.is_file():
                raise ValueError(f"Missing theme asset for {destination}: {source}")
            assets[target] = source.read_bytes()
    return assets


def build(root, compiler, environment):
    generate(root=root)
    generate_variant(root)
    subprocess.run(
        [sys.executable, "-B", str(root / "gnome-shell/prepare_sources.py")],
        cwd=root, check=True, timeout=30,
    )
    # All compilation and asset resolution must succeed before publication.
    with tempfile.TemporaryDirectory(prefix="viparu-") as directory:
        staging = Path(directory)
        styles = {
            "gtk-3.0/gtk.css": "scss/gtk-3.0.scss",
            "gtk-4.0/gtk.css": "scss/gtk-4.0.scss",
            "gtk-4.0/libadwaita.css": "scss/libadwaita-4.0.scss",
            "gnome-shell/gnome-shell.css": "gnome-shell/gnome-shell.scss",
        }
        built = {}
        for destination, source in styles.items():
            output = staging / destination
            output.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                [compiler, "-t", "expanded", "-I", str(root / "common"),
                 str(root / source), str(output)],
                cwd=root, env=environment, check=True, timeout=60,
            )
            built[destination] = output.read_bytes()
        # Dark requests deliberately receive the same fixed hybrid appearance.
        for version in ("gtk-3.0", "gtk-4.0"):
            built[f"{version}/gtk-dark.css"] = built[f"{version}/gtk.css"]
        assets = collect_assets(built, root)
        for path, content in assets.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        for destination, content in built.items():
            path = root / destination
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            print(f"Built {root.name}/{destination}", flush=True)
        print(f"Resolved {len(assets)} local theme assets", flush=True)


def validate_output_directories(paths):
    """Reject unsafe output roots before any existing variant is replaced."""
    for path in paths:
        if path.is_symlink():
            raise ValueError(f"Refusing to replace theme output symlink: {path}")
        if path.exists() and not path.is_dir():
            raise ValueError(f"Theme output must be a directory: {path}")


def build_variants(keys=None):
    """Stage complete, independently rebuildable themes; leave local CSS untouched."""
    variants = load_variants(ROOT)
    keys = list(variants) if keys is None else list(keys)
    for key in keys:
        if key not in variants:
            raise ValueError(f"Unknown theme variant: {key!r}")
    destination = ROOT / "dist/themes"
    targets = [destination / variants[key]["name"] for key in keys]
    output_directories = [destination.parent, destination, *targets]
    validate_output_directories(output_directories)
    compiler, environment = compiler_command()
    destination.mkdir(parents=True, exist_ok=True)
    # Do not replace previously usable outputs unless every requested build succeeds.
    with tempfile.TemporaryDirectory(prefix=".variants-", dir=destination.parent) as directory:
        staging = Path(directory)
        for key in keys:
            theme = staging / variants[key]["name"]
            copy_project(theme, key, ROOT)
            build(theme, compiler, environment)
        # Recheck every target together: a late invalid target must not leave
        # earlier variants replaced. This is not a multi-directory transaction.
        validate_output_directories(output_directories)
        for key, target in zip(keys, targets):
            if target.exists():
                shutil.rmtree(target)
            (staging / variants[key]["name"]).replace(target)
    return targets


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--variants", action="store_true",
                           help="Build all standalone themes in dist/themes without changing local CSS")
    selection.add_argument("--variant", metavar="ID",
                           help="Build one standalone variant in dist/themes without changing local CSS")
    args = parser.parse_args()
    try:
        if args.variants or args.variant:
            for theme in build_variants([args.variant] if args.variant else None):
                print(f"Standalone theme: {theme.relative_to(ROOT)}")
        else:
            compiler, environment = compiler_command()
            build(ROOT, compiler, environment)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"Theme build failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
