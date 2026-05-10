#!/usr/bin/env python3
"""Final mobile LCP/CLS hardening for homepage top category row.

- Make top homepage category images eager (`src`) with explicit dimensions.
- Bump carousel CSS/JS asset versions to avoid immutable-cache reuse.
- Add a mobile min-height guard for the top category cards via uploaded CSS.
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


def defaults_file(config: str) -> str:
    handle = tempfile.NamedTemporaryFile("w", delete=False)
    handle.write(
        "[client]\n"
        f"user={config_value(config, 'database_user')}\n"
        f"password={config_value(config, 'database_password')}\n"
        f"host={config_value(config, 'database_server')}\n"
        "default-character-set=cp1251\n"
    )
    handle.close()
    os.chmod(handle.name, 0o600)
    return handle.name


def mysql_scalar(defaults: str, db: str, query: str) -> str:
    return subprocess.check_output(["mysql", "--defaults-extra-file=" + defaults, "-N", "-B", db, "-e", query]).decode(
        "cp1251"
    )


def fetch(defaults: str, db: str, prefix: str, table: str, column: str, row_id: int) -> str:
    hex_text = mysql_scalar(defaults, db, f"SELECT HEX({column}) FROM {table} WHERE id={row_id}").strip()
    return bytes.fromhex(hex_text).decode("cp1251")


def main() -> None:
    config = CONFIG.read_text(encoding="utf-8", errors="ignore")
    db = config_value(config, "dbase")
    prefix = config_value(config, "table_prefix")
    defaults = defaults_file(config)
    try:
        chunk32 = fetch(defaults, db, prefix, f"{prefix}site_htmlsnippets", "snippet", 32)
        chunk33 = fetch(defaults, db, prefix, f"{prefix}site_htmlsnippets", "snippet", 33)
        head = fetch(defaults, db, prefix, f"{prefix}site_htmlsnippets", "snippet", 1)
        footer = fetch(defaults, db, prefix, f"{prefix}site_htmlsnippets", "snippet", 3)

        variants = [
            (
                32,
                chunk32,
                '<img width="450" height="450" decoding="async" data-src="[[+tv.ImgForMainPage:phpthumbon=`w=450&h=450&zc=1&f=webp`]]" alt="[[+pagetitle]]" class="lazyload">',
                '<img width="450" height="450" decoding="async" fetchpriority="high" src="[[+tv.ImgForMainPage:phpthumbon=`w=450&h=450&zc=1&f=webp`]]" alt="[[+pagetitle]]" class="lazyload">',
            ),
            (
                33,
                chunk33,
                '<img width="600" height="600" decoding="async" data-src="[[+tv.ImgForMainPage:phpthumbon=`w=600&h=600&f=webp`]]" alt="[[+pagetitle]]" class="lazyload">',
                '<img width="600" height="600" decoding="async" fetchpriority="high" src="[[+tv.ImgForMainPage:phpthumbon=`w=600&h=600&f=webp`]]" alt="[[+pagetitle]]" class="lazyload">',
            ),
        ]
        rows: list[tuple[str, str, int, str]] = []
        for chunk_id, text, old, new in variants:
            if new not in text:
                if old not in text:
                    raise SystemExit(f"chunk {chunk_id} eager image needle not found")
                text = text.replace(old, new, 1)
            rows.append((f"{prefix}site_htmlsnippets", "snippet", chunk_id, text))

        head = head.replace("css/mt-mobile-carousel.css?v=20260510", "css/mt-mobile-carousel.css?v=20260510b")
        footer = footer.replace("js/mt-mobile-carousel.js?v=20260510", "js/mt-mobile-carousel.js?v=20260510b")
        rows.append((f"{prefix}site_htmlsnippets", "snippet", 1, head))
        rows.append((f"{prefix}site_htmlsnippets", "snippet", 3, footer))

        sql_lines = []
        for table, column, row_id, value in rows:
            sql_lines.append(f"UPDATE {table} SET {column}=UNHEX('{value.encode('cp1251').hex()}') WHERE id={row_id};")
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
    for rel in ["resource/web", "includes/elements", "context_settings", "db/objects/modChunk", "db/objects/modTemplate"]:
        path = cache_root / rel
        if path.exists():
            shutil.rmtree(path)
            print(f"removed {path}")
    print("mobile LCP/CLS hardening applied")


if __name__ == "__main__":
    main()
