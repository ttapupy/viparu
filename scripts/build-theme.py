#!/usr/bin/env python3
"""Build the self-contained Viparu GTK/Shell theme without activating it."""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from palette import ROOT, generate


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


def collect_assets(stylesheets):
    """Resolve every CSS image before publishing; copy only referenced Yaru assets."""
    assets = {}
    for destination, content in stylesheets.items():
        css = re.sub(r"/\*.*?\*/", "", content.decode("utf-8"), flags=re.DOTALL)
        for url in re.findall(r"url\(\s*[\"']?([^\"')\s]+)", css):
            if ":" in url or Path(url).is_absolute():
                raise ValueError(f"Non-local theme asset in {destination}: {url}")
            target = (ROOT / destination).parent / url
            target = target.resolve()
            if not target.is_relative_to(ROOT):
                raise ValueError(f"Asset escapes the theme directory: {url}")
            version = Path(destination).parts[0]
            if version in ("gtk-3.0", "gtk-4.0") and url.startswith("assets/"):
                source = ROOT / "scss/yaru" / version / url
                if not source.is_file():
                    source = ROOT / url
            else:
                source = target
            if not source.is_file():
                raise ValueError(f"Missing theme asset for {destination}: {source}")
            assets[target] = source.read_bytes()
    return assets


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    try:
        compiler, environment = compiler_command()
        generate()
        subprocess.run(
            [sys.executable, "-B", str(ROOT / "gnome-shell/prepare_sources.py")],
            cwd=ROOT, check=True, timeout=30,
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
                    [compiler, "-t", "expanded", "-I", str(ROOT / "common"),
                     str(ROOT / source), str(output)],
                    cwd=ROOT, env=environment, check=True, timeout=60,
                )
                built[destination] = output.read_bytes()
            # Dark requests deliberately receive the same fixed hybrid appearance.
            for version in ("gtk-3.0", "gtk-4.0"):
                built[f"{version}/gtk-dark.css"] = built[f"{version}/gtk.css"]
            assets = collect_assets(built)
            for path, content in assets.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            for destination, content in built.items():
                path = ROOT / destination
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
                print(f"Built {destination}", flush=True)
            print(f"Resolved {len(assets)} local theme assets", flush=True)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"Theme build failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
