# Iter9 — замена Owl для homepage `.mobile-slider`

## Статус этого пакета

В репозиторий добавлен production-ready пакет для точечной замены Owl Carousel на самописную карусель только для проблемных блоков главной страницы.

Прямого SSH/FTP/MODX-доступа в текущем окружении нет, поэтому этот пакет оформлен как безопасный deploy bundle:

- `production_files/css/mt-mobile-carousel.css`
- `production_files/js/mt-mobile-carousel.js`
- `function_owlInitialize_patch.diff`
- `preview/mt-carousel-preview.html`

## Что нужно развернуть на production

### 1. Бэкап

Перед правками:

```bash
cp /var/www/m_trud_ru_usr/data/www/m-trud.ru/js/function.js \
  /var/www/m_trud_ru_usr/data/www/m-trud.ru/js/function.js.bak.iter9.$(date -u +%Y%m%dT%H%M%SZ)

mysqldump --single-transaction --quick --default-character-set=utf8mb4 \
  <DB_NAME> | gzip > /root/backups/m-trud_iter9_carousel_$(date -u +%Y%m%dT%H%M%SZ).sql.gz
```

Дополнительно экспортировать MODX template/chunk/resource, где находятся homepage wrappers `.mobile-slider`.

### 2. Загрузить новые ассеты

Скопировать:

```text
production_files/css/mt-mobile-carousel.css -> /var/www/m_trud_ru_usr/data/www/m-trud.ru/css/mt-mobile-carousel.css
production_files/js/mt-mobile-carousel.js   -> /var/www/m_trud_ru_usr/data/www/m-trud.ru/js/mt-mobile-carousel.js
```

### 3. Пометить только homepage wrappers

В MODX-источнике главной заменить только три homepage-wrapper:

```html
<div class="row-new categories-index grid-col-4 mobile-slider">
```

на:

```html
<div class="row-new categories-index grid-col-4 mobile-slider" data-mt-carousel="home">
```

Не делать массовую замену по всему сайту: `.mobile-slider` используется на других страницах.

### 4. Обновить `js/function.js`

Применить `function_owlInitialize_patch.diff`.

Смысл правки:

```js
var legacyMobileSliders = $('.mobile-slider').not('[data-mt-carousel]');
```

Owl продолжит работать на всех старых `.mobile-slider`, но не будет оборачивать homepage sliders с `data-mt-carousel`.

### 5. Подключить ассеты с версией

В head после `css/style.css?v=17`:

```html
<link rel="stylesheet" href="css/mt-mobile-carousel.css?v=20260510" type="text/css">
```

В footer/scripts после `js/function.js`:

```html
<script defer src="js/mt-mobile-carousel.js?v=20260510"></script>
```

Если `js/function.js` кэшируется immutable, обновить URL подключения:

```html
<script defer src="js/function.js?v=20260510-carousel"></script>
```

### 6. Очистить кэш MODX

Выполнить `$modx->cacheManager->refresh()` и при необходимости очистить `core/cache/resource/web`.

## Проверка после deploy

```bash
node --check /var/www/m_trud_ru_usr/data/www/m-trud.ru/js/mt-mobile-carousel.js
node --check /var/www/m_trud_ru_usr/data/www/m-trud.ru/js/function.js
curl -I https://m-trud.ru/css/mt-mobile-carousel.css?v=20260510
curl -I https://m-trud.ru/js/mt-mobile-carousel.js?v=20260510
python3 scripts/dev_env_check.py --max-pages 20
```

Browser checks:

- На `/` при mobile `<500px` у трёх помеченных блоков нет `.owl-wrapper` / `.owl-item`.
- Карточка по центру, max-width около 300px.
- Точки серые/красная активная, как раньше.
- Свайп и клик по точкам работают.
- На `>=500px` остаётся сетка.
- На `/production/paper-bags` legacy `.mobile-slider` без `data-mt-carousel` продолжает работать через Owl.

## Rollback

1. Вернуть `js/function.js` из `.bak.iter9.*`.
2. Убрать подключения `mt-mobile-carousel.css/js`.
3. Убрать `data-mt-carousel="home"` из homepage wrappers.
4. Очистить MODX cache.
5. Проверить `/` и `scripts/dev_env_check.py --max-pages 20`.
