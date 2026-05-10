#!/usr/bin/env python3
"""Apply iter9 carousel changes on the production MODX host.

Run on the server as root:
    python3 /tmp/deploy_iter9.py
"""
from __future__ import annotations

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


def make_mysql_defaults(config_text: str) -> str:
    handle = tempfile.NamedTemporaryFile("w", delete=False)
    handle.write(
        "[client]\n"
        f"user={config_value(config_text, 'database_user')}\n"
        f"password={config_value(config_text, 'database_password')}\n"
        f"host={config_value(config_text, 'database_server')}\n"
        "default-character-set=utf8mb4\n"
    )
    handle.close()
    os.chmod(handle.name, 0o600)
    return handle.name


def mysql_scalar(defaults_file: str, database: str, query: str) -> str:
    return subprocess.check_output(
        ["mysql", "--defaults-extra-file=" + defaults_file, "-N", "-B", database, "-e", query]
    ).decode("utf-8")


def update_function_js() -> None:
    path = ROOT / "js/function.js"
    text = path.read_text(encoding="utf-8", errors="ignore")
    old = """  function owlInitialize() {
   if ($(window).width() < 500) {
      $('.mobile-slider').owlCarousel(
      {
        items: 1,
        autoHeight : true,
        lazyLoad : true,
        navigation: true,
      }
    );
   }else{
       $('.mobile-slider').trigger('destroy.owl.carousel');
   }
}
"""
    new = """  function owlInitialize() {
   var legacyMobileSliders = $('.mobile-slider').not('[data-mt-carousel]');
   if ($(window).width() < 500) {
      legacyMobileSliders.owlCarousel(
      {
        items: 1,
        autoHeight : true,
        lazyLoad : true,
        navigation: true,
      }
    );
   }else{
       legacyMobileSliders.trigger('destroy.owl.carousel');
   }
}
"""
    if new in text:
        return
    if old not in text:
        raise SystemExit("function.js owlInitialize target not found")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def fetch_row(defaults_file: str, database: str, table: str, column: str, row_id: int) -> str:
    hex_text = mysql_scalar(defaults_file, database, f"SELECT HEX({column}) FROM {table} WHERE id={row_id}").strip()
    return bytes.fromhex(hex_text).decode("utf-8", errors="replace")


def apply_db_updates(config_text: str) -> None:
    database = config_value(config_text, "dbase")
    prefix = config_value(config_text, "table_prefix")
    defaults_file = make_mysql_defaults(config_text)
    try:
        rows = {
            "template1": fetch_row(defaults_file, database, f"{prefix}site_templates", "content", 1),
            "head": fetch_row(defaults_file, database, f"{prefix}site_htmlsnippets", "snippet", 1),
            "footer": fetch_row(defaults_file, database, f"{prefix}site_htmlsnippets", "snippet", 3),
            "ready": fetch_row(defaults_file, database, f"{prefix}site_htmlsnippets", "snippet", 102),
            "cat": fetch_row(defaults_file, database, f"{prefix}site_htmlsnippets", "snippet", 139),
        }

        old_wrap = '<div class="row-new categories-index grid-col-4 mobile-slider">'
        new_wrap = '<div class="row-new categories-index grid-col-4 mobile-slider" data-mt-carousel="home">'
        if new_wrap not in rows["template1"]:
            count = rows["template1"].count(old_wrap)
            if count != 3:
                raise SystemExit(f"expected 3 homepage mobile-slider wrappers in template 1, got {count}")
            rows["template1"] = rows["template1"].replace(old_wrap, new_wrap)

        css_line = '<link rel="stylesheet" href="css/mt-mobile-carousel.css?v=20260510" type="text/css">'
        if css_line not in rows["head"]:
            needle = '<link rel="stylesheet" href="css/style.css?v=17" type="text/css">'
            if needle not in rows["head"]:
                raise SystemExit("head stylesheet needle not found")
            rows["head"] = rows["head"].replace(needle, needle + "\n" + css_line, 1)

        new_fn_line = '<script defer src="js/function.js?v=20260510-carousel"></script>'
        mt_js_line = '<script defer src="js/mt-mobile-carousel.js?v=20260510"></script>'
        if mt_js_line not in rows["footer"]:
            old_fn_line = '<script defer src="js/function.js"></script>'
            if old_fn_line in rows["footer"]:
                rows["footer"] = rows["footer"].replace(old_fn_line, new_fn_line + "\n" + mt_js_line, 1)
            elif new_fn_line in rows["footer"]:
                rows["footer"] = rows["footer"].replace(new_fn_line, new_fn_line + "\n" + mt_js_line, 1)
            else:
                raise SystemExit("footer function.js script needle not found")

        old_ready = (
            '<img data-src="[[#[[+id]].CardReadyImg_1:phpthumbon=`w=450&h=450&zc=1&f=webp`]]" '
            'alt="[[+pagetitle]]" class="lazyload">'
        )
        new_ready = (
            '<img width="450" height="450" decoding="async" '
            'data-src="[[#[[+id]].CardReadyImg_1:phpthumbon=`w=450&h=450&zc=1&f=webp`]]" '
            'alt="[[+pagetitle]]" class="lazyload">'
        )
        if new_ready not in rows["ready"]:
            if old_ready not in rows["ready"]:
                raise SystemExit("ready card img needle not found")
            rows["ready"] = rows["ready"].replace(old_ready, new_ready, 1)

        old_cat = (
            '<img class="adaptive-img lazyload"  alt="[[+pagetitle]]" '
            'data-src="[[#[[+id]].CardImg_1:phpthumbon=`w=450&h=450&zc=1&f=webp`]]">'
        )
        new_cat = (
            '<img class="adaptive-img lazyload" width="450" height="450" decoding="async" '
            'alt="[[+pagetitle]]" data-src="[[#[[+id]].CardImg_1:phpthumbon=`w=450&h=450&zc=1&f=webp`]]">'
        )
        if new_cat not in rows["cat"]:
            if old_cat not in rows["cat"]:
                raise SystemExit("category card img needle not found")
            rows["cat"] = rows["cat"].replace(old_cat, new_cat, 1)

        updates = [
            (f"{prefix}site_templates", "content", 1, rows["template1"]),
            (f"{prefix}site_htmlsnippets", "snippet", 1, rows["head"]),
            (f"{prefix}site_htmlsnippets", "snippet", 3, rows["footer"]),
            (f"{prefix}site_htmlsnippets", "snippet", 102, rows["ready"]),
            (f"{prefix}site_htmlsnippets", "snippet", 139, rows["cat"]),
        ]
        sql_lines = []
        for table, column, row_id, value in updates:
            sql_lines.append(f"UPDATE {table} SET {column}=UNHEX('{value.encode('utf-8').hex()}') WHERE id={row_id};")

        sql_file = tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8")
        sql_file.write("\n".join(sql_lines))
        sql_file.close()
        os.chmod(sql_file.name, 0o600)
        try:
            with open(sql_file.name, "rb") as stdin:
                subprocess.run(["mysql", "--defaults-extra-file=" + defaults_file, database], stdin=stdin, check=True)
        finally:
            os.unlink(sql_file.name)
    finally:
        os.unlink(defaults_file)


def set_ownership() -> None:
    subprocess.run(
        [
            "chown",
            "m_trud_ru_usr:m_trud_ru_usr",
            str(ROOT / "css/mt-mobile-carousel.css"),
            str(ROOT / "js/mt-mobile-carousel.js"),
            str(ROOT / "js/function.js"),
        ],
        check=False,
    )


def refresh_modx_cache() -> None:
    script = ROOT / "cache_refresh_iter9.php"
    script.write_text(
        "<?php\n"
        "define('MODX_API_MODE', true);\n"
        "require dirname(__FILE__) . '/index.php';\n"
        "$modx->getService('error','error.modError');\n"
        "$ok = $modx->cacheManager->refresh();\n"
        "echo $ok ? \"cache_refresh_ok\\n\" : \"cache_refresh_unknown\\n\";\n",
        encoding="utf-8",
    )
    try:
        subprocess.run(
            ["su", "-s", "/bin/bash", "-c", f"php {script}", "m_trud_ru_usr"],
            check=False,
        )
    finally:
        try:
            script.unlink()
        except FileNotFoundError:
            pass


def main() -> None:
    if not ROOT.exists():
        raise SystemExit(f"webroot not found: {ROOT}")
    config_text = CONFIG.read_text(encoding="utf-8", errors="ignore")
    update_function_js()
    apply_db_updates(config_text)
    set_ownership()
    refresh_modx_cache()
    print("iter9 carousel deployment applied")


if __name__ == "__main__":
    main()
