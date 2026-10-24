#!/usr/bin/env python3
"""Generate the shared SCSS palette from color-palette.json (standard library only)."""

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def unique_pairs(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError(f"Duplicate palette key: {name}")
        result[name] = value
    return result


def render_palette(source):
    colors = json.loads(source, object_pairs_hook=unique_pairs)
    if not isinstance(colors, dict) or not colors:
        raise ValueError("The palette must be a nonempty JSON object.")
    lines = [
        "// Generated from color-palette.json by scripts/palette.py.",
        "// Edit the JSON for colors, scss/_roles.scss for their assignments.",
        "",
    ]
    sass_names = set()
    for name, color in colors.items():
        if not re.fullmatch(r"[a-z][a-z0-9_]*", name):
            raise ValueError(f"Invalid SCSS variable name: {name!r}")
        # Sass treats underscores and hyphens as the same character.
        sass_name = name.replace("_", "-")
        if sass_name in sass_names:
            raise ValueError(f"Colliding SCSS variable name: {name!r}")
        sass_names.add(sass_name)
        if not isinstance(color, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
            raise ValueError(f"Expected a #RRGGBB color for {name!r}, got {color!r}")
        lines.append(f"${name}: {color.upper()};")
    return "\n".join(lines) + "\n"


def generate(check=False):
    output = ROOT / "color-palette.scss"
    content = render_palette((ROOT / "color-palette.json").read_text(encoding="utf-8"))
    if check:
        if not output.is_file() or output.read_text(encoding="utf-8") != content:
            raise ValueError("color-palette.scss is stale; run python3 scripts/palette.py")
    else:
        output.write_text(content, encoding="utf-8")
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify without writing")
    args = parser.parse_args()
    try:
        output = generate(check=args.check)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Palette generation failed: {error}\n")
    print(f"{'Checked' if args.check else 'Generated'} {output.name}")


if __name__ == "__main__":
    main()
