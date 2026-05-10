#!/usr/bin/env python3
"""Rollback fixed width/height attributes from product-card thumbnails.

The listing cards (`tpl.readycard.item`, chunk 102) use many product photos
with different visual proportions. Explicit `width="450" height="450"`
attributes changed the browser's reserved aspect ratio for every card and made
some thumbnails look stretched in product-category grids. This script restores
the pre-iter9 markup for that chunk only, leaving homepage/category-specific
CLS fixes untouched.
"""
from __future__ import annotations

import os
import pathlib
import re
import shutil
import subprocess
import tempfile


ROOT = pathlib.Path("/var/www/m_trud_ru_usr/data/www/m-trud.ru")
CONFIG = ROOT / "core/config/config.inc.php"


def config_value(text: str, key: str) -> str:
    match = re.search(r"\$" + re.escape(key) + r"\s*=\s*'([^']*)'", text)
    if not match:
        raise SystemExit(f"config key not found: {key}")
    return match.group(1)


def main() -> None:
    config = CONFIG.read_text(encoding="utf-8", errors="ignore")
    db = config_value(config, "dbase")
    prefix = config_value(config, "table_prefix")
    defaults = tempfile.NamedTemporaryFile("w", delete=False)
    defaults.write(
        "[client]\n"
        f"user={config_value(config, 'database_user')}\n"
        f"password={config_value(config, 'database_password')}\n"
        f"host={config_value(config, 'database_server')}\n"
        "default-character-set=cp1251\n"
    )
    defaults.close()
    os.chmod(defaults.name, 0o600)
    try:
        hex_text = subprocess.check_output(
            [
                "mysql",
                "--defaults-extra-file=" + defaults.name,
                "-N",
                "-B",
                db,
                "-e",
                f"SELECT HEX(snippet) FROM {prefix}site_htmlsnippets WHERE id=102",
            ]
        ).strip()
        snippet = bytes.fromhex(hex_text.decode("ascii")).decode("cp1251")

        current = (
            '<img width="450" height="450" decoding="async" '
            'data-src="[[#[[+id]].CardReadyImg_1:phpthumbon=`w=450&h=450&zc=1&f=webp`]]" '
            'alt="[[+pagetitle]]" class="lazyload">'
        )
        restored = (
            '<img data-src="[[#[[+id]].CardReadyImg_1:phpthumbon=`w=450&h=450&zc=1&f=webp`]]" '
            'alt="[[+pagetitle]]" class="lazyload">'
        )
        if current not in snippet:
            if restored in snippet:
                print("chunk 102 already restored")
                return
            raise SystemExit("chunk 102 product image needle not found")

        snippet = snippet.replace(current, restored, 1)
        sql = f"UPDATE {prefix}site_htmlsnippets SET snippet=UNHEX('{snippet.encode('cp1251').hex()}') WHERE id=102;"
        sql_file = tempfile.NamedTemporaryFile("w", delete=False, encoding="ascii")
        sql_file.write(sql)
        sql_file.close()
        os.chmod(sql_file.name, 0o600)
        try:
            with open(sql_file.name, "rb") as stdin:
                subprocess.run(["mysql", "--defaults-extra-file=" + defaults.name, db], stdin=stdin, check=True)
        finally:
            os.unlink(sql_file.name)
    finally:
        os.unlink(defaults.name)

    cache_root = ROOT / "core/cache"
    for rel in ["resource/web", "includes/elements", "context_settings", "db/objects/modChunk", "db/objects/modTemplate"]:
        path = cache_root / rel
        if path.exists():
            shutil.rmtree(path)
            print(f"removed {path}")
    print("product card image attributes restored")


if __name__ == "__main__":
    main()
