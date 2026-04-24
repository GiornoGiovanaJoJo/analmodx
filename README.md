# Аудит m-trud.ru (MODX)

## Development environment

This repository stores audit artifacts and lightweight tooling used to validate the target website.

### 1) Install Python dependencies

```bash
python3 -m pip install -r requirements.txt
```

### 2) Run the environment sanity check

```bash
python3 scripts/dev_env_check.py --max-pages 20
```

Expected result: JSON output with `broken_count: 0` and zero exit code.

### 3) Preview local artifacts (optional)

```bash
python3 -m http.server 8080
```

Then open: `http://127.0.0.1:8080/` and browse files in `artifacts/`.

Дата аудита: 24.04.2026  
Формат: технический SEO + performance + разметка + URL/боты + черновая проверка manager

## Что было запрошено

- Аудит `m-trud.ru` (MODX) по направлениям:
  - 404 и склейки URL
  - боты
  - performance (ориентир: ~46/100)
  - мусор в шаблонах
  - изображения (WebP/JPG, lazy-load)
  - микроразметка
- Подготовка подробного ТЗ/плана оптимизации (чистка, бандлы, кэш).

## Ключевые выводы

### 1) 404 / склейки URL

- При корректной резолюции ссылок (с учетом `<base href="https://m-trud.ru/">`) и краулинге:
  - проверено ~`1811` внутренних ссылок;
  - `broken_count = 0`.
- Проверка sitemap:
  - в `sitemap.xml` найдено `1341` URL;
  - выборочно проверено `800` URL;
  - все `200 OK`.
- Источник шума в 404/логах:
  - URL с двойными слешами (`//`) и промежуточным `index.php?q=`;
  - параметр `q` (`?q=abc`) дает `404`;
  - часть query-параметров (`utm_*`, `ysclid`, `fbclid`) отдается с `200`, что расширяет мусорный crawl.

Примеры:
- `https://m-trud.ru/production/paper-bags// -> 301 -> https://m-trud.ru/index.php?q=production/paper-bags/`
- `https://m-trud.ru/production//paper-bags -> 301 -> https://m-trud.ru/index.php?q=production/paper-bags`
- `https://m-trud.ru/index.php?q=production/paper-bags -> 301 -> https://m-trud.ru/production/paper-bags`
- `https://m-trud.ru/production/paper-bags?q=abc -> 404`

### 2) Боты

- `robots.txt` очень большой и содержит много `Disallow` по параметрам.
- Это частично помогает, но не закрывает все сценарии:
  - мусорные query могут продолжать появляться в отчетах;
  - при `200` на части параметризованных URL остаются дубли документов для краулеров.

### 3) Performance

По локальному Lighthouse (headless, mobile/desktop):

- Mobile:
  - FCP: `3.18s`
  - LCP: `4.82s`
  - TBT: `1704ms` (критично)
  - TTI: `9.69s`
- Desktop:
  - FCP: `0.69s`
  - LCP: `1.40s`
  - TBT: `596ms`
  - CLS: `0.07`

Основные потери:
- тяжелая работа JS на main thread (высокий TBT);
- изображения (next-gen formats, oversized);
- часть render-blocking ресурсов.

### 4) Шаблоны / мусор фронта

По главной странице:
- внешние скрипты: `19`
- inline script-блоки: `11`
- link/css-ресурсы: `36`
- DOM узлы: `1164`
- элементы с inline-style: `37`

Наблюдаются legacy jQuery-плагины и дробление ресурсов, что повышает стоимость поддержки и тормозит mobile.

### 5) Изображения

В выборке краулинга:
- найдено `3223` вхождений `img`;
- ссылки на `.webp`: `94`;
- ссылки на `.jpg/.jpeg`: `64`;
- lazy-load: `2439` (используется активно).

По главной:
- у `36/36` изображений нет явных `width/height`;
- `3` изображения без `alt`.

### 6) Микроразметка

- На главной:
  - JSON-LD script: `3`
  - Microdata `itemscope`: `70`
  - `og:title` присутствует
- База разметки есть, но нужен контроль консистентности и валидности по типам страниц.

### 7) MODX manager

- Выполнена проверка страницы входа `https://m-trud.ru/manager/`.
- В сохраненном HTML отражается форма логина (`Войти | Мастерская труда`), полноценный доступ к внутренним разделам manager в рамках этого прогона не подтвержден.
- Поэтому аудит внутренних чанков/элементов manager ограничен внешними и сетевыми фактами.

## ТЗ / План оптимизации

## Этап 1 (P1, 1-3 дня) — URL-нормализация и отсечение мусора

1. Нормализовать URL на nginx/MODX:
   - схлопывание множественных `/` в один `/`;
   - полный 301 с `index.php?q=*` на clean URL;
   - единая политика trailing slash.
2. Зафиксировать canonical-политику для параметризованных URL.
3. Настроить фильтры на явный бот-мусор (`?q=`, мусорные паттерны) и rate-limit.
4. В Метрике:
   - сегменты “боты/не боты”;
   - дашборд по 404-паттернам (`//`, `index.php?q=`, query-хвосты).

## Этап 2 (P1/P2, 3-7 дней) — Performance и бандлы

1. Разделить бандлы (critical / non-critical), подключить `defer/async`.
2. Удалить неиспользуемые legacy JS/CSS из шаблонов/чанков.
3. Снизить JS-нагрузку для mobile (цель: TBT < 300-400ms).
4. Оптимизировать LCP-элемент (preload/fetchpriority/image format).

## Этап 3 (P2, 5-10 дней) — изображения, кэш, schema

1. Массово перевести ключевые изображения в WebP/AVIF.
2. Добавить `width/height` и контроль `alt`.
3. Уточнить кэш-политику:
   - долгий cache-control для версионированной статики;
   - ревизия MODX-кэша и прогрева.
4. Провести валидацию Schema.org по шаблонам (категории, карточки, статьи, контакты).

## Артефакты, собранные в этом диалоге

Все артефакты положены в `artifacts/`:

- `artifacts/lh-desktop.json` — результат Lighthouse desktop.
- `artifacts/lh-mobile.json` — результат Lighthouse mobile (первый прогон).
- `artifacts/lh-mobile2.json` — результат Lighthouse mobile (повторный прогон).
- `artifacts/manager-welcome.html` — сохраненный HTML страницы manager после попытки входа.
- `artifacts/m-trud-audit.canvas.tsx` — canvas-отчет аудита.
- `artifacts/terminal-logs/` — текстовые логи ключевых запусков краулинга/проверок.

Дополнительно в папке присутствовал файл:
- `audit_mtrud.md` (существовал до этого шага, не удалялся).

## Что использовалось в процессе

- HTTP-краулинг и анализ HTML (`requests`, `BeautifulSoup`) для:
  - проверки внутренних ссылок;
  - проверки sitemap;
  - анализа изображений, schema, ссылочной структуры.
- Локальный Lighthouse через `npx lighthouse` для performance-метрик.
- Проверка технических URL-паттернов (редиректы, `index.php?q`, `//`, query).

## Ограничения аудита

- Полноценный интерактивный браузерный сценарий внутри manager (с навигацией по разделам MODX) в этом прогоне не подтвержден.
- Performance-метрики получены в лабораторном режиме (Lighthouse), не заменяют полевые данные CWV из CrUX/реальных пользователей.

## Рекомендуемый следующий шаг

1. Дать серверный доступ к nginx-конфигу и MODX-шаблонам/чанкам.
2. Внедрить Этап 1 (URL-нормализация) и сразу перепроверить 404-отчеты Метрики через 48-72 часа.
3. После этого делать Этап 2 (бандлы/JS) и Этап 3 (media/schema/cache) с контрольными Lighthouse/CWV-срезами.
