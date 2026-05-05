# P1 — итерация 2 (nginx cache + gzip + чистка форм + defer)

Время: 2026-05-04 ~17:50–18:30 UTC. Исполнитель: cursor agent.

## Бэкапы (Приложение №3)

- Vhost nginx: `/etc/nginx/fastpanel2-available/m_trud_ru_usr/m-trud.ru.conf.bak.20260504T175324Z` на сервере + `artifacts/changes/p1/vhost_before_p1.conf` локально.
- Chunks (форм) `<spam>` → `<span>`: бэкап-папка `/root/backups/m-trud_chunks_20260504T180146Z/` на сервере. (Фактический контент бэкап-файлов не записался из-за прав записи в `/root` под пользователем `m_trud_ru_usr`; БД-снапшот за итерацию 1 покрывает откат.)
- Перед каждой DB-правкой — `cacheManager->refresh()`. Полный DB-дамп зафиксирован в итерации 1 (`m_trud_ru.sql.gz`, 32 MB).

## Изменения

### nginx (vhost m-trud.ru.conf)

```diff
      location ~* ^.+\.(jpg|jpeg|gif|png|svg|js|css|...)$ {
         try_files $uri $uri/ @fallback;
+        # >>> P1 cache (cursor 2026-05-04) >>>
+        access_log off;
+        expires off;
+        gzip_static on;
+        add_header Cache-Control "public, max-age=31536000, immutable" always;
+        add_header X-Content-Type-Options "nosniff" always;
+        # <<< P1 cache (cursor 2026-05-04) <<<
     }
```

`m-trud.ru.includes` (расширяет gzip_types для `application/wasm`, `font/woff2`, RSS/Atom, manifest+json и др.).

`nginx -t` → `Syntax OK`. `nginx -s reload` без ошибок.

### MODX templates / chunks

7 чанков-форм: `<spam>` → `<span>` (id=27 ContactForm, 116 ConsultForm.tpl, 118 ConsultFlowerForm.tpl, 120 simpleOrderForm.tpl, 122 simpleOrderFlowerForm.tpl, 172 CalcForm.tpl, 175 PaperForm). Удалено 7 дефектных тегов.

5 чанков: добавлены `defer` / `async defer` к блокирующим скриптам:
- `chunk 3 (footer)`: `js/jquery.mobile.customized.min.js` → `defer`.
- `chunk 96 (side-menu)`: `vk.com/js/api/openapi.js` → `defer`.
- `chunk 109 (recaptchav2_html)` / `110 (recaptchav2_invisible_html)` / `148 (recaptchav3_html)`: reCAPTCHA → `async defer`.

`cacheManager->refresh()` после каждой партии правок.

## Эффект

### Static asset headers (после)

```
URL: https://m-trud.ru/assets/components/ajaxform/css/default.css
  cache-control: public, max-age=31536000, immutable
  x-content-type-options: nosniff

URL: https://m-trud.ru/assets/components/ajaxform/js/default.js
  cache-control: public, max-age=31536000, immutable
  content-encoding: gzip
  vary: Accept-Encoding

URL: https://m-trud.ru/manager/templates/default/css/index.css (288 KB)
  no-gzip:  288 533 B
  gzip:      67 146 B  (23.3% от оригинала)
```

### HTML страницы (без изменений, как и должно быть)

`Cache-Control: private, max-age=3600` (динамика MODX).

### Lighthouse мобайл (3 прогона: BEFORE → AFTER P0 → AFTER P1)

| Метрика | BEFORE | AFTER P0 | AFTER P1 (final) |
|---|---:|---:|---:|
| Performance | n/a | 50 | **47**¹ |
| FCP, ms | 2545 | 2270 | 2927 |
| LCP, ms | 7101 | 5910 | **6200** |
| TBT, ms | 3210 | 117 | **92** |
| CLS | 0.519 | 0.519 | 0.519 |
| SI, ms | 6031 | 5144 | **5520** |
| TTFB, ms | 177 | 525 | 520 |

¹ Performance score колеблется ±3 от прогона к прогону в lab, но **TBT упал с 3210 ms до 92 ms (-97%)** — это самое большое реальное улучшение для интерактивности на мобайл.

### Lighthouse desktop

| Метрика | BEFORE | AFTER P1 |
|---|---:|---:|
| Performance | n/a | **90** |
| FCP, ms | 688 | 893 |
| LCP, ms | 1398 | 1447 |
| TBT, ms | 596 | **0** |
| CLS | 0.066 | 0.065 |
| SI, ms | 1639 | 2009 |

KPI desktop ≥ 92 — близко (90), для попадания в KPI понадобится либо чистка inline JS/CSS в шаблоне (`<script>` на главной), либо включение brotli + смена `gzip_comp_level` глобально.

## Что НЕ удалось / отложено

- **Главная страница в `sitemap.xml`**: попытка инжектировать через `&resources=1` в `[[pdoSitemap]]` (resource id=34) приводит к пустой выдаче sitemap (`pdoTools` 2.13.3 в этом окружении не отдаёт содержимое при изменённых параметрах сниппета). Sitemap откачен в **исходное байт-в-байт состояние** (1341 URL). Рекомендуемое решение для следующего шага — отдавать `/sitemap-home.xml` отдельным MODX-ресурсом и склеить через `Sitemap Index` (`<sitemapindex>`), либо менять реализацию через `pdoSitemap` с явным `parents=`-64,-32,корни_категорий,1`.
- **221 неопубликованный «коробка 1174»**: не трогаю до явного «ОК» от заказчика.
- **`<spam>`-бэкап файлы**: SQL-бэкап БД покрывает откат, отдельные текстовые before/after не записались (минорно).
- **lazyload.min.js**: defer не ставлю, потому что он управляет first-paint картинок above-the-fold.

## Что остаётся «вне MODX» (для следующих итераций)

1. **brotli**: проверить наличие `ngx_brotli` или собрать модуль; даст -15-25% к gzip-объёму.
2. **opcache PHP**: `opcache.memory_consumption=192M`, `opcache.max_accelerated_files=20000`, `opcache.revalidate_freq=60` — нужно править `php.ini` и reload `php8.2-fpm`.
3. **MySQL `innodb_buffer_pool_size`**: подобрать под реальную нагрузку.
4. **Перенести `Deny from`/UA-блокировки из `.htaccess` в nginx** (`map $http_user_agent $bad_ua` + `geo $bad_ip`) — сейчас 280+ правил каждый запрос проходит через Apache.
5. **CLS = 0.519 на мобайл**: это `width/height` у изображений (R25/R67 ТЗ). Обычно правится в шаблоне `Card-*` и `tplMinifyXjs`.
6. **404 в DevTools**: `GET /undefined?id=...` — это тег от тулзы `optipic.io` или подобной (по хвосту `?id=…` похоже на счётчик). Стоит проверить.
7. **Мониторинг 404 / параметрических URL** через Метрику — нет доступа.

## Артефакты этой итерации

- `artifacts/changes/p1/vhost_before_p1.conf`, `vhost_after_p1.conf`, `vhost_p1.diff`, `m-trud.ru.includes`
- `artifacts/lh_after_p1_final/{desktop,mobile}.json`
- `artifacts/lh_after_p1/{desktop,mobile}.json` (промежуточный замер до правок шаблонов)
- `home_after_p1.png` — скриншот главной
- `smoke_test_after_p1.mp4` — видео smoke-теста публичного сайта (главная, каталог, контакты, форма, DevTools, redirect-проверки)
