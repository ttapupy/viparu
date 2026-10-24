#!/usr/bin/env python3
"""Build the self-contained GTK 3/4 and GNOME Shell theme without activating it."""

import os
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
            raise RuntimeError(
                "sassc / LibSass is required to compile the theme sources. "
                "On Ubuntu: sudo apt install sassc"
            )
        compiler = str(local)
        libraries = sorted((ROOT / ".build-tools/usr/lib").glob("*/libsass.so*"))
        directories = sorted({str(path.parent) for path in libraries})
        if directories:
            previous = environment.get("LD_LIBRARY_PATH")
            if previous:
                directories.append(previous)
            environment["LD_LIBRARY_PATH"] = os.pathsep.join(directories)
    return compiler, environment


def main():
    try:
        compiler, environment = compiler_command()
        generate()
        subprocess.run(
            [sys.executable, "-B", str(ROOT / "gnome-shell/prepare_sources.py")],
            cwd=ROOT, check=True, timeout=30,
        )
        # Compile everything before replacing any loadable CSS file.
        with tempfile.TemporaryDirectory(prefix="vintage-pop-art-unified-") as directory:
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
                    [compiler, "-t", "expanded", str(ROOT / source), str(output)],
                    cwd=ROOT, env=environment, check=True, timeout=60,
                )
                built[destination] = output.read_bytes()
            # A single fixed hybrid appearance is intentional, including when an
            # application requests its dark variant. Shell is always dark.
            for version in ("gtk-3.0", "gtk-4.0"):
                built[f"{version}/gtk-dark.css"] = built[f"{version}/gtk.css"]
            for destination, content in built.items():
                path = ROOT / destination
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
                print(f"Built {destination}", flush=True)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"Theme build failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
