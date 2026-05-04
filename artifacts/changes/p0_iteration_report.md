# P0 — итерация 1 (URL-нормализация + базовый кэш MODX)

Время: 2026-05-04 ~16:35 UTC. Исполнитель: cursor agent.

## Backups (Приложение №3, гарантия возврата)

- DB dump: `/root/backups/m-trud_20260504T162752Z/m_trud_ru.sql.gz` (32 MB) + копия в `/workspace/artifacts/baseline/server_backup/`.
- Webroot snapshot: `/root/backups/m-trud_20260504T162752Z/webroot_code.tar.gz` (3.3 GB, with media) и `webroot_source_only.tar.gz` (1.2 GB, без media/cache).
- nginx vhost + Apache `/etc/apache2` снапшоты: `/root/backups/m-trud_20260504T162752Z/conf/`.
- `.htaccess` сохранён рядом как `.htaccess.bak.20260504T163447Z` на сервере; копия + diff — в `/workspace/artifacts/changes/`.
- `robots.txt` и `sitemap.xml` зафиксированы в `/workspace/artifacts/baseline/`.

## Что сделано в этой итерации

1. `.htaccess` (Apache, обслуживается за nginx-прокси на 127.0.0.1:81):
   - `?q=*` на не-`index.php` URL → `301` на тот же путь без `q=` (вместо текущего `404`).
   - Любые `//` (и `///`) в URI → `301` в один хоп через `THE_REQUEST`.
   - Добавлены безопасные заголовки `X-Content-Type-Options: nosniff` и `Referrer-Policy: strict-origin-when-cross-origin`.
   - Apache `apache2ctl -t` → `Syntax OK`.
2. MODX System Settings (через MODX API под пользователем `m_trud_ru_usr`):
   - `cache_db`: 0 → 1.
   - `cache_resource`: 0 → 1.
   - `compress_css`: 0 → 1.
   - `compress_js`: 0 → 1.
   - `cache_handler` оставлен `xPDOFileCache` (без изменений).
   - `$modx->cacheManager->refresh()` — кэш очищен и прогрет.

## Проверка «до/после»

### URL-нормализация

| URL | До | После |
|---|---|---|
| `/index.php?q=production/paper-bags` | 301 → clean | 301 → clean (без изменений) |
| `/production/paper-bags?q=foo` | **404** | **301 → /production/paper-bags** |
| `/?q=foo` | 200 | **301 → /** |
| `/production//paper-bags` | 301 → `/index.php?q=…` (1 hop, через MODX) | 301 → `/production/paper-bags` (1 hop) |
| `/production///paper-bags` | (3 hops) | 301 → `/production/paper-bags` (1 hop) |
| `/production/paper-bags//` | 301 → `/index.php?q=…/` (1 hop) | 301 → `/production/paper-bags` (2 hops, конечный URL чистый) |
| `/index.php` | 301 → `/` | 301 → `/` |
| `https://www.m-trud.ru/` | 301 → apex | 301 → apex |
| `/some-broken-url-xyz` | 404 | 404 |

### Headers на `/`

`x-content-type-options: nosniff`, `referrer-policy: strict-origin-when-cross-origin`, `strict-transport-security` (был), `cache-control: private, max-age=3600` (от MODX, был).

### Эффект кэша MODX (TTFB апекса)

```
До: ~0.86s   (прогон в 16:34Z)
После прогрева: 0.47–0.52s  (≈-40%)
```

(см. также `lh-mobile2.json`/`lh-desktop.json` baseline).

## Найдено в процессе (требует согласования, НЕ исправлено сейчас)

- 221 неопубликованный ресурс с пустым `alias`/`uri` (одинаковый pagetitle «коробка 1174», parent=0, published=0, deleted=0). Они не отдают 200, но засоряют кэш-карту, лог `cache.refresh()` и потенциально мусорят menu/builder. Рекомендация: согласовать массовый soft-delete (`deleted=1`).
- В `.htaccess` блок `Deny from` ~280 строк адресов и `mod_rewrite` блок UA. Эффективнее эти правила вынести на nginx (см. список ниже «Что вне MODX»).

## Что **вне MODX** ещё нужно сделать (план следующих итераций)

1. **nginx (FastPanel vhost `/etc/nginx/fastpanel2-sites/m_trud_ru_usr/m-trud.ru.conf`):**
   - Перенести редирект `//` → `/`, блокировки UA/IP (сейчас в `.htaccess`) на уровень nginx — так не нагружаем PHP/Apache.
   - Долгий `Cache-Control: public, max-age=31536000, immutable` для версионированной статики (`*.js?v=...`, `*.css?v=...`, `/assets/cache_image/*`, `/assets/cache_image_product_3/*`, фавиконы, шрифты). Сейчас static-локейшен есть, но без `expires`/`add_header Cache-Control`.
   - Добавить `gzip_min_length 1024`, расширить `gzip_types` на `application/xml`, `application/rss+xml`, `application/manifest+json`, `application/wasm`. (`gzip_comp_level 1` мало — поднять до 5).
   - Включить brotli (если установлен модуль) или хотя бы предкомпрессию gzip для статики (`gzip_static on`).
   - HTTP/2 уже включён (`http2 on`). Можно включить `http2_push_preload off` (по умолчанию off — оставить).
2. **Apache `httpd` бэкенд (127.0.0.1:81):** убедиться, что `mod_deflate`, `mod_expires`, `mod_headers` включены — `apache2ctl -M` (на следующем шаге).
3. **PHP / OPcache:** при доступе к php.ini рекомендую `opcache.enable=1, opcache.memory_consumption=192M, opcache.max_accelerated_files=20000, opcache.validate_timestamps=1, opcache.revalidate_freq=60`.
4. **MySQL:** проверить `query_cache_type` (на 8.x уже нет), `innodb_buffer_pool_size` ~ 25-50% RAM сервера.
5. **Sitemap:** добавить главную страницу (сейчас её нет в `sitemap.xml`), пересмотреть `lastmod`. Это правится из MODX в плагине `GoogleSiteMap` — задача следующей итерации.
6. **Очистить «коробка 1174» x221** (массовый soft-delete) — после согласования с заказчиком.
7. **Метрика/Вебмастер:** доступа нет; запросить у заказчика для дашбордов (404, query-share, bot/no-bot).
8. **Login Extra:** в установленных пакетах **отсутствует** (см. инвентарь — `Login` package not found). Пункт ТЗ «Обновить уязвимый Login Extra» закрыт по факту: устанавливать заново имеет смысл только если он реально нужен фронтовой логике (на m-trud.ru фронтового логина не наблюдается).

## Артефакты этой итерации

- `/workspace/artifacts/changes/htaccess_before_p0.txt`
- `/workspace/artifacts/changes/htaccess_after_p0.txt`
- `/workspace/artifacts/changes/htaccess_p0.diff`
- `/workspace/artifacts/baseline/server_backup/m_trud_ru.sql.gz`
- `/workspace/artifacts/baseline/server_backup/conf/`
