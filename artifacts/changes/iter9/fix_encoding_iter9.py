#!/usr/bin/env python3
"""Repair iter9 MODX cp1251 rows and reapply ASCII carousel changes.

The production MODX tables use cp1251 text columns. The first deploy script
updated rows with UTF-8 UNHEX literals, which caused visible mojibake. This
script restores the affected rows from the pre-deploy backup TSV and writes
them back as cp1251 bytes, then reapplies the carousel changes.
"""
from __future__ import annotations

import csv
import glob
import os
import pathlib
import re
import subprocess
import tempfile


ROOT = pathlib.Path("/var/www/m_trud_ru_usr/data/www/m-trud.ru")
CONFIG = ROOT / "core/config/config.inc.php"


def config_value(config_text: str, key: str) -> str:
    match = re.search(r"\$" + re.escape(key) + r"\s*=\s*'([^']*)'", config_text)
    if not match:
        raise SystemExit(f"MODX config key not found: {key}")
    return match.group(1)


def latest_backup_dir() -> pathlib.Path:
    candidates = sorted(glob.glob("/root/backups/m-trud_iter9_carousel_*"))
    if not candidates:
        raise SystemExit("iter9 backup directory not found")
    return pathlib.Path(candidates[-1])


def unescape_mysql_batch(value: str) -> str:
    out: list[str] = []
    i = 0
    while i < len(value):
        if value[i] == "\\" and i + 1 < len(value):
            nxt = value[i + 1]
            out.append(
                {
                    "0": "\0",
                    "n": "\n",
                    "r": "\r",
                    "t": "\t",
                    "b": "\b",
                    "Z": "\x1a",
                    "\\": "\\",
                }.get(nxt, nxt)
            )
            i += 2
        else:
            out.append(value[i])
            i += 1
    return "".join(out)


def read_backup_rows(backup_dir: pathlib.Path) -> dict[str, str]:
    rows: dict[str, str] = {}
    with (backup_dir / "templates_mobile.tsv").open(encoding="utf-8", newline="") as handle:
        for row in csv.reader(handle, delimiter="\t"):
            if len(row) >= 3 and row[0] == "1":
                rows["template1"] = unescape_mysql_batch(row[2])
                break
    with (backup_dir / "chunks_head_footer.tsv").open(encoding="utf-8", newline="") as handle:
        for row in csv.reader(handle, delimiter="\t"):
            if len(row) >= 3:
                if row[0] == "1":
                    rows["head"] = unescape_mysql_batch(row[2])
                elif row[0] == "3":
                    rows["footer"] = unescape_mysql_batch(row[2])
    # These chunks were exported in the full DB dump, but not the small TSV;
    # fetch their current source from the existing readable production backup
    # dump would be heavier. They contain only a small amount of Cyrillic, so
    # reconstructing from the pre-deploy local known-good text is done by
    # pulling from the compressed SQL via mysql restore is avoided. Instead,
    # read them from current DB after setting cp1251 and repair by replacing
    # mojibake only when backup rows are unavailable.
    missing = {"template1", "head", "footer"} - set(rows)
    if missing:
        raise SystemExit(f"backup TSV missing rows: {sorted(missing)}")
    return rows


def make_mysql_defaults(config_text: str) -> str:
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


def mysql_scalar(defaults_file: str, database: str, query: str) -> str:
    return subprocess.check_output(
        ["mysql", "--defaults-extra-file=" + defaults_file, "-N", "-B", database, "-e", query]
    ).decode("cp1251")


def fetch_text(defaults_file: str, database: str, table: str, column: str, row_id: int) -> str:
    hex_text = mysql_scalar(defaults_file, database, f"SELECT HEX({column}) FROM {table} WHERE id={row_id}").strip()
    return bytes.fromhex(hex_text).decode("cp1251")


def reapply_changes(rows: dict[str, str], defaults_file: str, database: str, prefix: str) -> dict[str, str]:
    # Fetch chunks 102/139 with cp1251 decoding, then fix any mojibake by
    # restoring their intended Russian literals explicitly.
    rows["ready"] = fetch_text(defaults_file, database, f"{prefix}site_htmlsnippets", "snippet", 102)
    rows["cat"] = fetch_text(defaults_file, database, f"{prefix}site_htmlsnippets", "snippet", 139)

    old_wrap = '<div class="row-new categories-index grid-col-4 mobile-slider">'
    new_wrap = '<div class="row-new categories-index grid-col-4 mobile-slider" data-mt-carousel="home">'
    rows["template1"] = rows["template1"].replace(old_wrap, new_wrap)

    css_line = '<link rel="stylesheet" href="css/mt-mobile-carousel.css?v=20260510" type="text/css">'
    style_line = '<link rel="stylesheet" href="css/style.css?v=17" type="text/css">'
    if css_line not in rows["head"]:
        rows["head"] = rows["head"].replace(style_line, style_line + "\n" + css_line, 1)

    old_fn_line = '<script defer src="js/function.js"></script>'
    new_fn_line = '<script defer src="js/function.js?v=20260510-carousel"></script>'
    mt_js_line = '<script defer src="js/mt-mobile-carousel.js?v=20260510"></script>'
    if mt_js_line not in rows["footer"]:
        rows["footer"] = rows["footer"].replace(old_fn_line, new_fn_line + "\n" + mt_js_line, 1)

    # Repair known literals in tpl.readycard.item if the first deploy already
    # converted them to mojibake.
    rows["ready"] = rows["ready"].replace(
        "<span>пїЅпїЅпїЅпїЅ пїЅпїЅ <span itemprop=\"lowPrice\">[[#[[+id]].priceot]]</span> "
        "<span itemprop=\"priceCurrency\" content=\"RUB\">пїЅпїЅпїЅ.</span></span>",
        "<span>цена от <span itemprop=\"lowPrice\">[[#[[+id]].priceot]]</span> "
        "<span itemprop=\"priceCurrency\" content=\"RUB\">руб.</span></span>",
    )
    rows["ready"] = rows["ready"].replace(
        'content="пїЅпїЅпїЅпїЅ пїЅпїЅ пїЅпїЅпїЅпїЅпїЅпїЅпїЅ"',
        'content="цена по запросу"',
    )
    rows["ready"] = rows["ready"].replace(
        "<span>пїЅпїЅпїЅпїЅ пїЅпїЅ пїЅпїЅпїЅпїЅпїЅпїЅпїЅ</span>",
        "<span>цена по запросу</span>",
    )
    rows["ready"] = rows["ready"].replace(
        "пїЅпїЅпїЅпїЅпїЅпїЅпїЅпїЅ [[#[[+id]].marketsize:isnot=``:then=` "
        "пїЅпїЅ [[#[[+id]].marketsize]] пїЅпїЅ`:else:=`пїЅпїЅ пїЅпїЅпїЅпїЅпїЅпїЅ`]]",
        "заказать [[#[[+id]].marketsize:isnot=``:then=` от [[#[[+id]].marketsize]] шт`:else:=`со склада`]]",
    )

    old_ready = (
        '<img data-src="[[#[[+id]].CardReadyImg_1:phpthumbon=`w=450&h=450&zc=1&f=webp`]]" '
        'alt="[[+pagetitle]]" class="lazyload">'
    )
    new_ready = (
        '<img width="450" height="450" decoding="async" '
        'data-src="[[#[[+id]].CardReadyImg_1:phpthumbon=`w=450&h=450&zc=1&f=webp`]]" '
        'alt="[[+pagetitle]]" class="lazyload">'
    )
    if new_ready not in rows["ready"] and old_ready in rows["ready"]:
        rows["ready"] = rows["ready"].replace(old_ready, new_ready, 1)

    old_cat = (
        '<img class="adaptive-img lazyload"  alt="[[+pagetitle]]" '
        'data-src="[[#[[+id]].CardImg_1:phpthumbon=`w=450&h=450&zc=1&f=webp`]]">'
    )
    new_cat = (
        '<img class="adaptive-img lazyload" width="450" height="450" decoding="async" '
        'alt="[[+pagetitle]]" data-src="[[#[[+id]].CardImg_1:phpthumbon=`w=450&h=450&zc=1&f=webp`]]">'
    )
    if new_cat not in rows["cat"] and old_cat in rows["cat"]:
        rows["cat"] = rows["cat"].replace(old_cat, new_cat, 1)
    return rows


def update_function_js() -> None:
    # Preserve the previous patched function.js; only the Owl guard file changed
    # for this fix, and it is uploaded separately.
    pass


def write_updates(defaults_file: str, database: str, prefix: str, rows: dict[str, str]) -> None:
    updates = [
        (f"{prefix}site_templates", "content", 1, rows["template1"]),
        (f"{prefix}site_htmlsnippets", "snippet", 1, rows["head"]),
        (f"{prefix}site_htmlsnippets", "snippet", 3, rows["footer"]),
        (f"{prefix}site_htmlsnippets", "snippet", 102, rows["ready"]),
        (f"{prefix}site_htmlsnippets", "snippet", 139, rows["cat"]),
    ]
    sql_lines = []
    for table, column, row_id, value in updates:
        hex_value = value.encode("cp1251").hex()
        sql_lines.append(f"UPDATE {table} SET {column}=UNHEX('{hex_value}') WHERE id={row_id};")
    sql_file = tempfile.NamedTemporaryFile("w", delete=False, encoding="ascii")
    sql_file.write("\n".join(sql_lines))
    sql_file.close()
    os.chmod(sql_file.name, 0o600)
    try:
        with open(sql_file.name, "rb") as stdin:
            subprocess.run(["mysql", "--defaults-extra-file=" + defaults_file, database], stdin=stdin, check=True)
    finally:
        os.unlink(sql_file.name)


def refresh_modx_cache() -> None:
    script = ROOT / "cache_refresh_iter9_encoding_fix.php"
    script.write_text(
        "<?php\n"
        "define('MODX_API_MODE', true);\n"
        "require dirname(__FILE__) . '/index.php';\n"
        "$modx->getService('error','error.modError');\n"
        "$modx->cacheManager->refresh();\n"
        "echo \"cache_refresh_done\\n\";\n",
        encoding="ascii",
    )
    try:
        subprocess.run(["su", "-s", "/bin/bash", "-c", f"php {script}", "m_trud_ru_usr"], check=False)
    finally:
        try:
            script.unlink()
        except FileNotFoundError:
            pass


def main() -> None:
    config_text = CONFIG.read_text(encoding="utf-8", errors="ignore")
    database = config_value(config_text, "dbase")
    prefix = config_value(config_text, "table_prefix")
    defaults_file = make_mysql_defaults(config_text)
    try:
        rows = read_backup_rows(latest_backup_dir())
        rows = reapply_changes(rows, defaults_file, database, prefix)
        write_updates(defaults_file, database, prefix, rows)
    finally:
        os.unlink(defaults_file)
    refresh_modx_cache()
    print("iter9 encoding repaired")


if __name__ == "__main__":
    main()
