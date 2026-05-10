#!/usr/bin/env python3
"""Defer non-critical carousel CSS so mobile LCP is observable."""
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
        def fetch(row_id: int) -> str:
            hex_text = subprocess.check_output(
                [
                    "mysql",
                    "--defaults-extra-file=" + defaults.name,
                    "-N",
                    "-B",
                    db,
                    "-e",
                    f"SELECT HEX(snippet) FROM {prefix}site_htmlsnippets WHERE id={row_id}",
                ]
            ).strip()
            return bytes.fromhex(hex_text.decode("ascii")).decode("cp1251")

        head = fetch(1)
        footer = fetch(3)
        for version in ["20260510", "20260510b", "20260510c"]:
            head = head.replace(
                f'\n<link rel="stylesheet" href="css/mt-mobile-carousel.css?v={version}" type="text/css">',
                "",
            )
            head = head.replace(
                f'<link rel="stylesheet" href="css/mt-mobile-carousel.css?v={version}" type="text/css">\n',
                "",
            )
            head = head.replace(
                f'<link rel="stylesheet" href="css/mt-mobile-carousel.css?v={version}" type="text/css">',
                "",
            )
            footer = footer.replace(
                f"js/mt-mobile-carousel.js?v={version}",
                "js/mt-mobile-carousel.js?v=20260510c",
            )

        sql_lines = [
            f"UPDATE {prefix}site_htmlsnippets SET snippet=UNHEX('{head.encode('cp1251').hex()}') WHERE id=1;",
            f"UPDATE {prefix}site_htmlsnippets SET snippet=UNHEX('{footer.encode('cp1251').hex()}') WHERE id=3;",
        ]
        sql_file = tempfile.NamedTemporaryFile("w", delete=False, encoding="ascii")
        sql_file.write("\n".join(sql_lines))
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
    print("carousel CSS deferred")


if __name__ == "__main__":
    main()
