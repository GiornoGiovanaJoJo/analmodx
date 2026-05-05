# P1 — итерация 3 (OPcache tune + gzip 5 + img dimensions)

Время: 2026-05-04 ~18:35–19:15 UTC.

## Бэкапы (Приложение №3)

- `php.ini.bak.20260504T184408Z` (на сервере + `php_ini_before.txt` локально).
- nginx vhost — backup-копия 20260504T185224Z уже существует с прошлой итерации.
- Бэкап-снапшот БД (32 MB) от итерации 1 покрывает откат всех изменений в `site_htmlsnippets`/`site_templates`.

## Найдено в инфраструктуре (полезное для отчёта)

- Сайт обслуживается **PHP 7.4.33** через `mod_fcgid` (FastPanel `FcgidWrapper`), а не PHP 8.2 (8.2 — это CLI/php-fpm для других задач).
- Per-site `php.ini`: `/var/www/m_trud_ru_usr/data/php-bin/m-trud.ru/php.ini`.
- Apache MPM: `prefork` (PHP-блокирующий, нормально для fcgid).
- На уровне PHP 7.4 OPcache был включён (`enable=1`, `memory=128M`, `revalidate_freq=2`), hit rate **98.3%**, num_cached_scripts=958. Хорошее состояние, но retal_cache_ttl=120 заставляет stat'ить файлы.

## Изменения

### `/var/www/m_trud_ru_usr/data/php-bin/m-trud.ru/php.ini`

```
+ ; >>> P1 opcache tuning (cursor 2026-05-04) >>>
+ opcache.memory_consumption=192
+ opcache.interned_strings_buffer=16
+ opcache.validate_timestamps=1
+ opcache.revalidate_freq=60
+ opcache.fast_shutdown=1
+ opcache.save_comments=1
+ realpath_cache_size=4096k
+ realpath_cache_ttl=600
+ ; <<< P1 opcache tuning (cursor 2026-05-04) <<<
```

`apache2ctl graceful` — без ошибок. Подтверждено `phpinfo`: `memory_consumption=192`, `interned_strings_buffer=16`, `revalidate_freq=60`, `realpath_cache_ttl=600`, free_memory ~ 171 MB запас.

### nginx vhost: `gzip_comp_level 1 → 5`

Сжатие CSS на `/manager/templates/default/css/index.css` (288 KB):
- было gzip ratio 23.3% (~67 KB)
- стало gzip ratio **18.4%** (~53 KB)
- **-21% к gzip-объёму без brotli**.

### MODX chunks (CLS-defense: `width`/`height` у `<img>`)

`<img>` без размеров → теперь 28 из 36 на главной с `width="..." height="..." decoding="async"`:

| chunk id | имя | правка |
|---|---|---|
| 32 | getres_mainTpl | 450×450 + decoding=async |
| 33 | getres_mainTpl_Firth | 600×600 + decoding=async + fetchpriority=high |
| 102 | tpl.readycard.item | 450×450 + decoding=async |
| 132 | header_2 | logo 221×74 (+fetchpriority=high), mobile-logo 40×41, vk-icon 25×25 |
| 133 | TopMenu_2 | vk-icon 25×25 |
| 96 | side-menu | 4 thumb-картинки 228×228 |
| 139 | cardCategories | 450×450 |

После очистки `core/cache/resource/web` главная отдаёт 28 `<img>` с явными размерами.

### Brotli — НЕ включён (ABI-mismatch)

В Debian-репо доступны `libnginx-mod-http-brotli-{static,filter}`, собранные под `nginx-abi-1.22.1-7`, а на сервере `nginx 1.28.0` (mainline-репо). Установка из дистрибутива блокируется `unmet dependencies`. Чтобы включить brotli:
1. либо собрать `ngx_brotli` динамически под mainline 1.28 (требует `gcc/make`/build-deps + `nginx -V` reproducible build);
2. либо подождать обновлённого mainline-пакета с brotli (некоторые сборщики его уже включают);
3. либо включить **gzip_static** для предкомпрессии — у нас уже включено.

Решено отложить brotli; gzip 5 + gzip_static дают приемлемый эффект без риска.

### CLS — частично решён

| Pages | CLS BEFORE | CLS AFTER |
|---|---:|---:|
| `/info/news` | (было 0) | **0.000** |
| `/production/paper-bags` | (было 0) | **0.000** |
| `/` (homepage) | 0.519 | **0.519** |

CLS на главной зафиксирован Lighthouse как `<div class="row-new categories-index grid-col-4 mobile-slider owl-carousel owl-theme">` — это **owl.carousel.js** инициализирует слайдер на 5 блоках главной и сдвигает контент. Я попытался зарезервировать высоту через `min-height` в `<style>` чанка `head` (id=1), но `:not(.owl-loaded)` в Lighthouse-simulate не успевает «защитить» layout до момента LCP. CSS-блок откачен.

Корректное решение требует:
- добавить inline-разметку `style="min-height: …px"` каждому конкретному слайдеру в шаблоне id=1 (значения замерить на mobile/desktop) или
- заменить `.mobile-slider` на CSS `display: grid; grid-template-columns: repeat(4, 1fr);` без owl-carousel (минус JS, плюс zero CLS).

Это **архитектурная правка** — не вмещается в безопасный режим этого спринта; описано в отчёте отдельным пунктом для следующего этапа.

## Эффект

### Lighthouse desktop

| Метрика | BEFORE (audit) | AFTER iter3 |
|---|---:|---:|
| **Performance** | n/a | **92** ⭐ (KPI ≥92 ✅) |
| FCP | 688 ms | 760 ms |
| LCP | 1398 ms | **1332 ms** |
| TBT | 596 ms | **0 ms** |
| CLS | 0.066 | 0.065 |
| SI | 1639 ms | 2012 ms |

### Lighthouse mobile

| Метрика | BEFORE | AFTER iter3 |
|---|---:|---:|
| Performance | n/a | 51 (KPI 65-70: ниже, см. CLS-блокер) |
| FCP | 2545 | **2026** |
| LCP | 7101 | **5749** |
| TBT | **3210** | **106** (-97%) |
| CLS | 0.519 | 0.519 (остаётся owl-carousel) |
| SI | 6031 | **5165** |

Десктоп **попал в KPI ≥92**. На мобайл performance подпёрло CLS — без архитектурной замены owl-carousel дальше двигаться сложно.

## Что вне MODX/nginx остаётся (план)

1. **CLS на главной**: заменить `mobile-slider` на CSS-grid (≈3-4 правки в шаблоне id=1 + 5 чанках; сразу даёт CLS → ~0).
2. **Brotli**: пересобрать `ngx_brotli` под nginx 1.28.0 или дождаться mainline-package.
3. **Главная в `sitemap.xml`**: переход на Sitemap Index (см. `p1_iteration_report.md`).
4. **221 «коробка 1174»**: soft-delete после согласования.
5. **MySQL `innodb_buffer_pool_size`**: подобрать под нагрузку.
6. **Перенос `Deny from`/UA-блоков из `.htaccess` на nginx**.
7. **Метрика/Вебмастер дашборды (P3)**: нет доступа.

## Артефакты

- `artifacts/changes/iter3/php_ini_before.txt`, `php_ini_after.txt`, `php_ini.diff`
- `artifacts/changes/iter3/vhost_after_iter3.conf`
- `artifacts/lh_iter3_FINAL/{desktop,mobile}.json`
- `/opt/cursor/artifacts/smoke_test_after_iter3.mp4` — smoke-видео (десктоп + мобильный режим, burger-меню, portfolio, contacts)
- `/opt/cursor/artifacts/home_mobile_after_iter3.png` — скриншот главной mobile-viewport
