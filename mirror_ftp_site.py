"""
Однократное зеркалирование FTP в локальную папку (с докачкой: пропуск файлов того же размера).
Учётные данные только из переменных окружения: FTP_HOST, FTP_USER, FTP_PASS
Дополнительно: FTP_MIRROR_DIR — путь назначения
Пример (PowerShell):
  $env:FTP_HOST='...'; $env:FTP_USER='...'; $env:FTP_PASS='...'; python mirror_ftp_site.py
"""
from __future__ import annotations

import os
import sys
import time
from ftplib import FTP, error_perm

# Долгие ответы на больших файлах (изображения каталога)
FTP_TIMEOUT_SEC = 7200
RETR_RETRIES = 5


def ftp_file_size(ftp: FTP, name: str) -> int | None:
    try:
        s = ftp.size(name)
        return int(s) if s is not None else None
    except Exception:
        return None


def download_file(ftp: FTP, name: str, path: str) -> int:
    last_err: Exception | None = None
    for attempt in range(1, RETR_RETRIES + 1):
        try:
            with open(path, "wb") as out:
                ftp.retrbinary("RETR " + name, out.write)
            return os.path.getsize(path)
        except (TimeoutError, OSError) as e:
            last_err = e
            if os.path.isfile(path):
                try:
                    os.remove(path)
                except OSError:
                    pass
            print(f"RETRY {attempt}/{RETR_RETRIES} {name}: {e}", file=sys.stderr)
            time.sleep(min(5 * attempt, 60))
    raise last_err  # type: ignore[misc]


def download_tree(ftp: FTP, local_dir: str) -> tuple[int, int]:
    """Рекурсивно скачивает текущий каталог FTP в local_dir. Возвращает (файлов, байт)."""
    os.makedirs(local_dir, exist_ok=True)
    files_count = 0
    bytes_count = 0
    lines: list[str] = []
    ftp.retrlines("LIST", lines.append)

    entries: list[tuple[bool, str]] = []
    for line in lines:
        parts = line.split(None, 8)
        if len(parts) < 9:
            continue
        name = parts[8]
        if name in (".", ".."):
            continue
        is_dir = line[0] == "d"
        entries.append((is_dir, name))

    for is_dir, name in entries:
        path = os.path.join(local_dir, name)
        if is_dir:
            try:
                ftp.cwd(name)
            except error_perm as e:
                print(f"SKIP dir (no access): {name} ({e})", file=sys.stderr)
                continue
            fc, bc = download_tree(ftp, path)
            files_count += fc
            bytes_count += bc
            ftp.cwd("..")
        else:
            try:
                rs = ftp_file_size(ftp, name)
                if rs is not None and os.path.isfile(path):
                    ls = os.path.getsize(path)
                    if ls == rs and rs > 0:
                        print(f"SKIP (same size {rs}) {path}")
                        files_count += 1
                        bytes_count += ls
                        continue
                sz = download_file(ftp, name, path)
                bytes_count += sz
                files_count += 1
                print(f"OK {sz} B  {path}")
            except error_perm as e:
                print(f"SKIP file: {name} ({e})", file=sys.stderr)

    return files_count, bytes_count


def main() -> None:
    host = os.environ.get("FTP_HOST")
    user = os.environ.get("FTP_USER")
    password = os.environ.get("FTP_PASS")
    out_root = os.environ.get("FTP_MIRROR_DIR", os.path.join(os.path.dirname(__file__), "m-trud_site_mirror"))

    if not all([host, user, password]):
        print("Задайте FTP_HOST, FTP_USER, FTP_PASS", file=sys.stderr)
        sys.exit(1)

    print(f"Mirror to: {out_root}")
    ftp = FTP(host, timeout=FTP_TIMEOUT_SEC)
    ftp.login(user, password)
    ftp.set_pasv(True)
    ftp.cwd("/")

    fc, bc = download_tree(ftp, out_root)
    ftp.quit()
    print(f"Done. Files: {fc}, total ~{bc / (1024 * 1024):.2f} MiB")


if __name__ == "__main__":
    main()
