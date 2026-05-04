# AGENTS.md

## Cursor Cloud specific instructions

This is a Python-based technical SEO audit & tooling repository for `m-trud.ru`. There is no web application to build or deploy — only Python scripts and static artifacts.

### Key services / scripts

| Script | Purpose | How to run |
|---|---|---|
| `scripts/dev_env_check.py` | Crawls `m-trud.ru` and checks for broken links (primary sanity check) | `python3 scripts/dev_env_check.py --max-pages 20` |
| `build_pdf.py` | Generates a consolidated PDF report (Windows-only, requires `reportlab` and Windows fonts) | `python build_pdf.py` |
| `mirror_ftp_site.py` | Mirrors the remote FTP site locally (requires `FTP_HOST`, `FTP_USER`, `FTP_PASS` env vars) | `python mirror_ftp_site.py` |

### Running the environment check

```bash
python3 scripts/dev_env_check.py --max-pages 20
```

Expected: JSON with `broken_count: 0` and exit code 0. This requires live network access to `https://m-trud.ru/`. Typical runtime is 60-90 seconds for 20 pages.

### Previewing artifacts

```bash
python3 -m http.server 8080
```

Then browse `http://127.0.0.1:8080/artifacts/`.

### Gotchas

- `build_pdf.py` requires `reportlab` (not in `requirements.txt`) and Windows fonts (`C:\Windows\Fonts`). It will not work on Linux without font path modifications.
- `mirror_ftp_site.py` requires FTP credentials via environment variables and is not needed for normal development.
- There is no linter or test framework configured in this repository. The `dev_env_check.py` script serves as the primary validation mechanism.
- `requirements.txt` only lists `requests` and `beautifulsoup4`.
