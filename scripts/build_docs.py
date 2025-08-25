#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from typing import Dict, Any
from importlib.machinery import SourceFileLoader

from jinja2 import Environment, FileSystemLoader, select_autoescape

# Import help constants from the CLI so docs stay in sync (script has no .py extension)
repo_root = Path(__file__).resolve().parent.parent
mel_path = repo_root / "mel"
mel = SourceFileLoader("mel_module", str(mel_path)).load_module()  # type: ignore


def build() -> int:
    templates_dir = repo_root / "templates"
    docs_dir = repo_root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    shared: Dict[str, Any] = {
        "HELP_HEADER": mel.HELP_HEADER,
        "HELP_BASIC": mel.HELP_BASIC,
        "HELP_ADVANCED": mel.HELP_ADVANCED,
        "HELP_FOOTER": mel.HELP_FOOTER,
    }

    pages = [
        ("index.html.j2", "index.html"),
        ("config.html.j2", "config.html"),
        ("explained.html.j2", "explained.html"),
        ("about.html.j2", "about.html"),
    ]

    for src_name, out_name in pages:
        tpl = env.get_template(src_name)
        html = tpl.render(**shared)
        (docs_dir / out_name).write_text(html, encoding="utf-8")
        print(f"✓ Built {out_name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(build())


