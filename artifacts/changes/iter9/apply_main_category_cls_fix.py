#!/usr/bin/env python3
"""Add explicit dimensions to homepage top category images in MODX chunks 32/33."""
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


def mysql_defaults(config_text: str) -> str:
    handle = tempfile.NamedTemporaryFile("w", delete=False)
    handle.write(
        "[client]\n"
        f"user={config_value(config_text, 'database_user')}\n"
        f"password={config_value(config_text, 'database_password')}\n"
        f"host={config_value(config_text, 'database_server')}\n"
        "default-character-set=cp1251\n"
    )
    handle.close()
    os.chmod(handle.name, 0o600)
    return handle.name


def mysql_scalar(defaults: str, db: str, query: str) -> str:
    return subprocess.check_output(["mysql", "--defaults-extra-file=" + defaults, "-N", "-B", db, "-e", query]).decode(
        "cp1251"
    )


def fetch_snippet(defaults: str, db: str, prefix: str, chunk_id: int) -> str:
    hex_text = mysql_scalar(defaults, db, f"SELECT HEX(snippet) FROM {prefix}site_htmlsnippets WHERE id={chunk_id}").strip()
    return bytes.fromhex(hex_text).decode("cp1251")


def main() -> None:
    config_text = CONFIG.read_text(encoding="utf-8", errors="ignore")
    db = config_value(config_text, "dbase")
    prefix = config_value(config_text, "table_prefix")
    defaults = mysql_defaults(config_text)
    try:
        rows = {
            32: fetch_snippet(defaults, db, prefix, 32),
            33: fetch_snippet(defaults, db, prefix, 33),
        }

        old_32 = (
            '<img data-src="[[+tv.ImgForMainPage:phpthumbon=`w=450&h=450&zc=1&f=webp`]]" '
            'alt="[[+pagetitle]]" class="lazyload">'
        )
        new_32 = (
            '<img width="450" height="450" decoding="async" '
            'data-src="[[+tv.ImgForMainPage:phpthumbon=`w=450&h=450&zc=1&f=webp`]]" '
            'alt="[[+pagetitle]]" class="lazyload">'
        )
        old_33 = (
            '<img data-src="[[+tv.ImgForMainPage:phpthumbon=`w=600&h=600&f=webp`]]" '
            'alt="[[+pagetitle]]" class="lazyload">'
        )
        new_33 = (
            '<img width="600" height="600" decoding="async" '
            'data-src="[[+tv.ImgForMainPage:phpthumbon=`w=600&h=600&f=webp`]]" '
            'alt="[[+pagetitle]]" class="lazyload">'
        )

        if new_32 not in rows[32]:
            if old_32 not in rows[32]:
                raise SystemExit("chunk 32 image needle not found")
            rows[32] = rows[32].replace(old_32, new_32, 1)
        if new_33 not in rows[33]:
            if old_33 not in rows[33]:
                raise SystemExit("chunk 33 image needle not found")
            rows[33] = rows[33].replace(old_33, new_33, 1)

        sql_lines = []
        for chunk_id, snippet in rows.items():
            sql_lines.append(
                f"UPDATE {prefix}site_htmlsnippets SET snippet=UNHEX('{snippet.encode('cp1251').hex()}') WHERE id={chunk_id};"
            )
        sql_file = tempfile.NamedTemporaryFile("w", delete=False, encoding="ascii")
        sql_file.write("\n".join(sql_lines))
        sql_file.close()
        os.chmod(sql_file.name, 0o600)
        try:
            with open(sql_file.name, "rb") as stdin:
                subprocess.run(["mysql", "--defaults-extra-file=" + defaults, db], stdin=stdin, check=True)
        finally:
            os.unlink(sql_file.name)
    finally:
        os.unlink(defaults)

    cache_root = ROOT / "core/cache"
    for rel in ["resource/web", "includes/elements", "context_settings"]:
        path = cache_root / rel
        if path.exists():
            shutil.rmtree(path)
            print(f"removed {path}")
    print("main category image dimensions applied")


if __name__ == "__main__":
    main()
