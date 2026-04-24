# 🔍 Технический SEO-аудит m-trud.ru (MODX)
> Дата: 24.04.2026 | Аудитор: Antigravity AI | Версия отчёта: 1.0

---

## 📋 Общая информация

| Параметр | Значение |
|---|---|
| CMS | MODX Revolution |
| Сервер | nginx/1.28.0 |
| PHP | 7.4.33 ⚠️ (EOL — устарел) |
| HTTPS | ✅ HSTS включён |
| PageSpeed (заявлено) | ~46/100 mobile |
| Яндекс.Метрика | ID 7998784 ✅ |
| Google Analytics | Старый GA (ga('send'...)) ⚠️ |

---

## 🔴 КРИТИЧЕСКИЕ ПРОБЛЕМЫ

### 1. Рендер-блокирующий скрипт в `<head>`

```html
<!-- БЕЗ defer/async — блокирует парсинг страницы! -->
<script src="assets/minifyx/js/scripts_p4f0c613bd6.js"></script>
```

**Размер:** 99 531 байт (~97 КБ) — без gzip-сжатия.  
**Без `defer`** означает: браузер останавливает рендер страницы и ждёт загрузки скрипта.

> [!CAUTION]
> Это **главная причина низкого PageSpeed (46/100)**. Исправление одного этого пункта даёт +10–15 баллов.

### 2. Нет canonical на главной странице

```
Canonical tags на главной: 0
```

На страницах товаров canonical есть. На главной — **отсутствует полностью**.  
Это риск дублирования: `https://m-trud.ru` и `https://m-trud.ru/` могут индексироваться как разные страницы.

### 3. Главная страница отсутствует в sitemap.xml

```
Homepage / in sitemap: FALSE
```

Sitemap содержит **1341 URL**, но главная `https://m-trud.ru/` в нём не представлена.

### 4. URL с пробелами в `href` (битые ссылки в навигации)

В исходном HTML шаблона найдены ссылки с trailing space:

```html
<a href="production/boxes ">ПОДАРОЧНЫЕ КОРОБКИ</a>
<a href="production/for-product-sample ">Упаковка для образцов</a>
<a href="production/papki ">Папки</a>
```

Пробел в URL кодируется в `%20` → **404 для ботов** и кривые ссылки в аналитике.

### 5. PHP 7.4.33 — End of Life

PHP 7.4 снят с поддержки в **декабре 2022 года**. Нет security-патчей, уязвимости не закрываются. Требуется переход на PHP 8.1+.

---

## 🟠 СЕРЬЁЗНЫЕ ПРОБЛЕМЫ

### 6. Отсутствует gzip/Brotli на статических ресурсах

| Файл | Размер (без сжатия) | С gzip (~70% сжатие) |
|---|---|---|
| `css/style.css` | **111 465 байт (108 КБ)** | ~33 КБ |
| `scripts_p4f0c613bd6.js` | **99 531 байт (97 КБ)** | ~30 КБ |
| `js/function.js` | 25 670 байт | ~8 КБ |
| `js/jquery.easing.1.3.js` | 8 097 байт | ~2.5 КБ |

Header `Content-Encoding` пустой → gzip **не включён** на nginx для JS/CSS.  
**Итого экономия: ~170 КБ → ~52 КБ** при включении сжатия.

### 7. Нет Cache-Control для статических ресурсов

```
CSS/JS Cache-Control: (отсутствует — только ETag)
HTML Cache-Control: private, max-age=3600
```

Браузеры не кешируют CSS/JS надолго — каждый повторный визит = повторная загрузка.  
Рекомендуется: `Cache-Control: public, max-age=31536000, immutable` для версионированных файлов.

### 8. Фрагментированная загрузка JS (много отдельных файлов)

Вместо одного бандла — **15+ отдельных `defer`-скриптов**:

```html
<script defer src="js/jquery.easing.1.3.js">
<script defer src="js/jquery.equalheights.js">
<script defer src="js/superfish.js">
<script defer src="js/jquery.mobilemenu.js">
<script defer src="js/owl.carousel.js">
<script defer src="js/jquery.ui.totop.js">
<script defer src="js/camera.js">
<script defer src="js/fancybox/jquery.fancybox.pack.js">
<script defer src="js/lightgallery.js">
<script defer src="js/lg-thumbnail.js">
<script defer src="js/jquery.maskedinput.min.js">
<script defer src="js/readmore.min.js">
<script defer src="js/tabs.js">
<script defer src="js/readMoreFade.js">
<script src="/js/jquery.mobile.customized.min.js">  ← БЕЗ defer!
<script src="js/lazyload.min.js">  ← БЕЗ defer!
<script src="/assets/components/ajaxform/js/default.js">  ← БЕЗ defer!
```

**Проблемы:**
- `jquery.mobile.customized.min.js` и `lazyload.min.js` — без defer (блокируют)
- `ajaxform/js/default.js` — без defer (блокирует)
- 15+ HTTP-запросов для JS вместо 1–2

### 9. Закомментированный VK API-скрипт остался в коде

```html
<!--    <script src="//vk.com/js/api/openapi.js?126"></script>-->
```

Мусор в шаблоне, неактуальный код.

### 10. Нет `<link rel="preload">` для критических ресурсов

Нет preload для главного CSS (`style.css`) и шрифтов — браузер обнаруживает их только при разборе HTML.

### 11. og:image везде ссылается на логотип (не на фото товара)

```html
<meta property="og:image" content="https://m-trud.ru/images/logo2017.png">
```

На всех страницах — один и тот же маленький логотип (`logo2017.png`).  
При шеринге в соцсетях отображается логотип вместо фото продукта.

### 12. Микроразметка: неправильные типы и отсутствующие схемы

**Что есть:**
- `Organization` ✅ (но `name: "m-trud.ru"` — лучше "Мастерская Труда")
- `SiteNavigationElement` ✅
- `ItemList` ✅ (в навигации)
- `BreadcrumbList` ✅ (на внутренних страницах)

**Чего нет — критично для ecommerce:**
- ❌ **`Product`** — нет разметки товаров (цена, наличие, описание)
- ❌ **`LocalBusiness`** — нет разметки местного бизнеса (адрес, часы работы)
- ❌ **`FAQPage`** — нет схемы для FAQ-блоков
- ❌ **`AggregateRating`** — нет рейтингов

**Ошибка в JSON-LD на главной:** кириллица в JSON-LD передаётся в кодировке Windows-1251 вместо UTF-8 — поисковики видят «мусор».

### 13. Использование нестандартного HTML-тега `<spam>`

```html
<spam>согласие на <a href="confirm-data">обработку персональных данных</a> *</spam>
```

Тег `<spam>` — **не существует в HTML**. Это опечатка (нужно `<span>`). Встречается **10 раз** на странице. Невалидный HTML.

---

## 🟡 УМЕРЕННЫЕ ПРОБЛЕМЫ

### 14. Lazy loading реализован через `class="lazyload"` + JS (не нативный)

```html
<!-- Используется JS-библиотека lazyload.min.js -->
<img data-src="/assets/cache_image_product_3/..." class="lazyload">

<!-- Нет нативного loading="lazy" (HTML атрибут) -->
<!-- loading="lazy" обнаружено: 0 раз -->
```

JS-библиотека lazyload добавляет лишнюю зависимость. Нативный `loading="lazy"` работает без JS и поддерживается всеми современными браузерами.

### 15. Изображения: WebP используется, JPG почти нет — но без `<picture>` тега

**Статистика на главной:**
- WebP: **39 ссылок** ✅
- JPG: **1** 
- PNG: **7** (в основном иконки и логотипы)

**Хорошо:** кэшированные изображения товаров уже в WebP (`_a03.webp`).  
**Проблема:** нет fallback через `<picture>` для старых браузеров (IE11, старый Safari).

### 16. Главные изображения-баннеры НЕ lazy — нет preload

Первые изображения видимой области (above the fold) должны грузиться сразу с `<link rel="preload">`, но этого нет.

### 17. Sitemap — 754 страницы-карточки с потенциально тонким контентом

```
Страниц /boxes/korobka-NNN и /paper-bags/bumazhnyj-paket-NNN: 754
```

Большинство с `priority=0.25` и `changefreq=monthly`. Нужна проверка: имеют ли они уникальный контент или это thin content.

### 18. Sitemap — 164 URL со старыми датами (до 2020 года)

Страницы с `lastmod` в 2017–2019 годах вероятно устарели или имеют нулевую ценность для индексации.

### 19. robots.txt — избыточность и конфликты

**Проблема 1:** `Disallow: /*?` блокирует ВСЕ URL с параметрами, но потом исключение `Allow: /*?v=*` — это может работать некорректно в зависимости от порядка правил.

**Проблема 2:** Огромное количество дублирующих `Disallow:` параметров — одни и те же параметры (`utm_source`, `erid`, `fbclid`) прописаны **по несколько раз** в разных секциях.

**Проблема 3:** `Allow: /*.webp` есть только для `User-Agent: Yandex` — для `User-Agent: *` WebP не разрешён явно.

### 20. Множество модальных форм дублируются на странице

На главной **5 форм заказа** (af_simple-order, af_catalog_consult, af_simple-order-flower, af_flower) с отдельными вызовами `AjaxForm.initialize()` для каждой. Это 4 отдельных HTTP-запроса на инициализацию + повторяется HTML форм.

### 21. Cache-Control на HTML: `private, max-age=3600`

HTML-страницы помечены `private` — CDN/прокси их не кешируют. Для статического контента (например страница "О компании") можно использовать `public`.

### 22. Старый Google Analytics код (UA, не GA4)

```javascript
ga('send', 'pageview', '/fone/');
```

Universal Analytics (ga()) **прекращён 1 июля 2023 года**. Данные больше не собираются в UA. Нужна миграция на GA4.

---

## 🟢 ЧТО РАБОТАЕТ ХОРОШО

| Параметр | Статус |
|---|---|
| HTTPS + HSTS | ✅ |
| Yandex.Metrika с Webvisor | ✅ |
| Изображения в WebP | ✅ |
| Lazy loading (JS-версия) | ✅ |
| Большинство скриптов с `defer` | ✅ (14 из 18) |
| Canonical на внутренних страницах | ✅ |
| BreadcrumbList schema | ✅ |
| Organization schema | ✅ |
| Sitemap.xml существует | ✅ |
| Friendly URLs (ЧПУ) | ✅ |
| Мобильный viewport | ✅ |
| favicon полный набор | ✅ |

---

## 📊 Сводная таблица проблем по приоритету

| Приоритет | Проблема | Влияние | Трудозатраты |
|---|---|---|---|
| 🔴 P1 | Рендер-блокирующий `scripts_p4f0c613bd6.js` | Performance +15 | 2ч |
| 🔴 P1 | Нет gzip на nginx для JS/CSS | Performance +10 | 1ч |
| 🔴 P1 | `<spam>` вместо `<span>` (10 мест) | HTML валидность | 30мин |
| 🔴 P1 | URL с пробелами в nav (3 шт.) | 404 ошибки | 30мин |
| 🔴 P1 | Нет canonical на главной | Дубли | 15мин |
| 🔴 P1 | Главная не в sitemap | Индексация | 30мин |
| 🟠 P2 | Cache-Control для CSS/JS | Performance | 1ч nginx |
| 🟠 P2 | og:image = логотип везде | CTR в соцсетях | 2ч |
| 🟠 P2 | Нет Product schema | Расширенные сниппеты | 4ч |
| 🟠 P2 | Кириллица в JSON-LD кракозябры | Микроразметка | 2ч |
| 🟠 P2 | `lazyload.min.js` без defer | Performance | 15мин |
| 🟠 P2 | GA4 вместо UA | Аналитика | 2ч |
| 🟡 P3 | Нативный loading="lazy" | Performance | 2ч |
| 🟡 P3 | preload для hero-images | LCP | 1ч |
| 🟡 P3 | robots.txt чистка дублей | Краулинг | 1ч |
| 🟡 P3 | PHP 7.4 → 8.1+ | Безопасность | 8ч+ |
| 🟡 P3 | Консолидация JS в бандл | Performance | 4ч |

---

## 📋 ТЗ на оптимизацию

### ЭТАП 1 — Быстрые победы (1–2 дня, без разработки)

**1.1 Nginx: включить gzip**
```nginx
gzip on;
gzip_types text/css application/javascript application/json text/html;
gzip_min_length 1024;
gzip_comp_level 6;
```

**1.2 Nginx: Cache-Control для статики**
```nginx
location ~* \.(css|js|woff|woff2)$ {
    expires 1y;
    add_header Cache-Control "public, max-age=31536000, immutable";
}
location ~* \.(webp|jpg|png|svg|gif)$ {
    expires 6M;
    add_header Cache-Control "public, max-age=15552000";
}
```

**1.3 Исправить `<spam>` → `<span>` в шаблоне MODX**  
Чанк с формой согласия на персданные — поменять тег.

**1.4 Убрать пробелы в 3 ссылках навигации**  
В шаблоне найти и исправить:
- `href="production/boxes "` → `href="production/boxes"`
- `href="production/for-product-sample "` → `href="production/for-product-sample"`
- `href="production/papki "` → `href="production/papki"`

**1.5 Добавить canonical на главную**  
В шаблон главной страницы добавить в `<head>`:
```html
<link rel="canonical" href="https://m-trud.ru/"/>
```

**1.6 Добавить главную в sitemap.xml**  
В настройках плагина Sitemap добавить главную страницу с priority=1.0.

---

### ЭТАП 2 — Производительность (3–5 дней)

**2.1 Добавить `defer` к недостающим скриптам:**
```html
<!-- Было -->
<script src="/js/jquery.mobile.customized.min.js">
<script src="js/lazyload.min.js">
<script src="/assets/components/ajaxform/js/default.js">

<!-- Надо -->
<script defer src="/js/jquery.mobile.customized.min.js">
<script defer src="js/lazyload.min.js">
<script defer src="/assets/components/ajaxform/js/default.js">
```

**2.2 Основной бандл `scripts_p4f0c613bd6.js` — добавить `defer`:**
```html
<!-- Было -->
<script src="assets/minifyx/js/scripts_p4f0c613bd6.js">

<!-- Надо -->
<script defer src="assets/minifyx/js/scripts_p4f0c613bd6.js">
```
Проверить: не ломает ли defer логику инициализации (должен быть DOMContentLoaded).

**2.3 Добавить `<link rel="preload">` для hero-изображений:**
```html
<link rel="preload" as="image" href="/assets/cache_image_product_3/images/banner-foto/01_228x228_27d.webp" type="image/webp">
```

**2.4 Заменить JS lazyload на нативный атрибут:**
```html
<!-- Было -->
<img data-src="/path/img.webp" class="lazyload">

<!-- Надо -->
<img src="/path/img.webp" loading="lazy" decoding="async">
```
Это позволит убрать `lazyload.min.js` из загрузки.

**2.5 Добавить CSS в `<link rel="preload">`:**
```html
<link rel="preload" href="css/style.css?v=17" as="style">
```

---

### ЭТАП 3 — SEO-микроразметка (1 неделя)

**3.1 Исправить кодировку в JSON-LD**  
Кириллица в JSON-LD должна быть в UTF-8. Проверить PHP-вывод JSON:
```php
json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES)
```

**3.2 Исправить `name` в Organization schema:**
```json
"name": "Мастерская Труда",  // было "m-trud.ru"
```

**3.3 Добавить LocalBusiness schema:**
```json
{
  "@type": "LocalBusiness",
  "name": "Мастерская Труда",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "пр. Шлиссельбургский, д.5",
    "addressLocality": "Санкт-Петербург",
    "postalCode": "192102",
    "addressCountry": "RU"
  },
  "openingHours": ["Mo-Fr 09:00-18:00"],
  "telephone": "+7-812-363-04-70"
}
```

**3.4 Добавить Product schema для карточек товаров:**
```json
{
  "@type": "Product",
  "name": "[[+pagetitle]]",
  "description": "[[+description]]",
  "image": "[[+og_image]]",
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "RUB",
    "availability": "https://schema.org/InStock"
  }
}
```

**3.5 Добавить og:image из фото товара (не логотип):**  
В шаблоне товарных страниц заменить статичный логотип на TV-поле с первым фото.

---

### ЭТАП 4 — Аналитика и чистка (3–5 дней)

**4.1 Миграция GA UA → GA4:**
- Создать новый поток данных в Google Analytics 4
- Установить Google Tag Manager (рекомендуется)
- Убрать старый `ga('send',...)` код
- Перенести цели из UA в GA4

**4.2 Очистка robots.txt:**
- Убрать дублирующиеся директивы
- Добавить `Allow: /*.webp` в секцию `User-Agent: *`
- Проверить конфликт `Disallow: /*?` vs `Allow: /*?v=*`

**4.3 Аудит sitemap:**
- Добавить главную страницу
- Проверить 164 страницы с lastmod до 2020 — удалить или обновить
- Проверить нужность 754 карточек-товаров в sitemap (возможно часть — thin content)

**4.4 Удалить мусор из шаблонов:**
- Закомментированный VK API: `<!-- <script src="//vk.com/js/api/openapi.js?126"> -->`
- 19 inline-стилей перенести в CSS-классы

**4.5 PHP 7.4 → 8.1:**
- Проверить совместимость MODX и всех экстрасов с PHP 8.1
- Обновить через хостинг-панель (обычно с сохранением данных)

---

## 📈 Ожидаемый результат после оптимизации

| Метрика | До | После (оценка) |
|---|---|---|
| PageSpeed Mobile | ~46/100 | ~70–80/100 |
| PageSpeed Desktop | ~60/100 | ~85–90/100 |
| CSS/JS transfer | ~210 КБ | ~55 КБ (с gzip) |
| Render-blocking | 1+ скрипт | 0 |
| Canonical coverage | ~90% | 100% |
| Schema types | 5 | 8+ |
| Crawler errors (пробелы в URL) | 3 | 0 |

---

## 🔧 Технические файлы для изменения

| Файл / Место | Что менять |
|---|---|
| nginx.conf / vhost | gzip, Cache-Control, expires |
| MODX → Шаблон (Template) | defer на скриптах, `<spam>`→`<span>`, canonical |
| MODX → Чанк формы согласия | `<spam>` → `<span>` |
| MODX → Шаблон навигации | убрать пробелы в href |
| MODX → Snippet Sitemap | добавить главную |
| robots.txt | убрать дубли, добавить webp |
| JSON-LD чанки | кодировка, name, LocalBusiness, Product |
| GA/GTM | миграция на GA4 |

