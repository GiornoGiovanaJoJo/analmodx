# iter8 — безопасная невизуальная правка URL с пробелами

Время: 2026-05-05 ~19:00 UTC.

## Что сделано

Добавлена точечная страховка в `.htaccess` для трёх старых пунктов навигации,
которые в HTML встречаются с завершающим пробелом в `href`:

- `production/boxes `
- `production/for-product-sample `
- `production/papki `

Теперь запросы к URL с закодированным пробелом (`%20`) не заканчиваются Apache
`403`, а уходят `301` на чистый канонический URL.

Правка не меняет HTML, CSS, JS, расположение блоков, поведение меню и визуал
страниц. Это только серверная нормализация ошибочного URL-паттерна.

## Бэкап

Перед заменой `.htaccess` создан серверный бэкап:

`/var/www/m_trud_ru_usr/data/www/m-trud.ru/.htaccess.bak.iter8.20260505T190228Z`

Локальные артефакты:

- `artifacts/changes/iter8/htaccess_before_iter8.txt`
- `artifacts/changes/iter8/htaccess_after_iter8.txt`
- `artifacts/changes/iter8/htaccess_iter8.diff`

## Проверка

`apache2ctl -t` до изменения:

```text
Syntax OK
```

`apache2ctl -t` после изменения:

```text
Syntax OK
```

HTTP-проверка после изменения:

| URL | После |
|---|---|
| `/production/boxes%20` | `301 → https://m-trud.ru/production/boxes` |
| `/production/for-product-sample%20` | `301 → https://m-trud.ru/production/for-product-sample` |
| `/production/papki%20` | `301 → https://m-trud.ru/production/papki` |
| `/production/boxes` | `200` |
| `/` | `200` |

Основной smoke-check репозитория:

```json
{
  "pages_crawled": 15,
  "links_checked": 201,
  "broken_count": 0,
  "broken_sample": []
}
```

Дополнительная невизуальная проверка:

- JSON-LD валиден на 5 проверенных URL (`/`, `/production/paper-bags`, `/production/boxes`, `/info/news`, `/contacts`).
- `sitemap.xml` остаётся рабочим: `200`, `urlset`, 1341 URL.
- `sitemap_index.xml` остаётся рабочим: `200`, включает `sitemap.xml` и `sitemap-extra.xml`.
- `sitemap-extra.xml` отдаёт главную страницу (`https://m-trud.ru/`) и валидный XML.
- `/undefined?cursorcheck` по-прежнему отдаёт `404`; безопасный локальный источник в HTML/локальных JS не найден, поэтому без риска для сторонних скриптов не менялось.

## Откат

```bash
cp /var/www/m_trud_ru_usr/data/www/m-trud.ru/.htaccess.bak.iter8.20260505T190228Z \
  /var/www/m_trud_ru_usr/data/www/m-trud.ru/.htaccess
apache2ctl -t
```
