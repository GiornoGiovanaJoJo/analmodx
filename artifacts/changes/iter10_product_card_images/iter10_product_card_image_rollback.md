# Iter10 — rollback fixed dimensions from product-card thumbnails

Дата: 2026-05-10.

## Причина

После iter9 на страницах категорий товаров карточки начали выглядеть растянутыми. По коду проблема была в глобальном чанке карточки товара:

- `tpl.readycard.item` / chunk `102`

В него в iter9 были добавлены:

```html
width="450" height="450" decoding="async"
```

Этот чанк используется массово на страницах категорий (`/production/boxes/3`, `/production/boxes/korobki-s-ruchkami`, `/production/paper-bags` и др.), поэтому правка затронула все товарные сетки.

## Что сделано

Точечно откатил только изображения в `tpl.readycard.item` к виду до iter9:

```html
<img data-src="[[#[[+id]].CardReadyImg_1:phpthumbon=`w=450&h=450&zc=1&f=webp`]]" alt="[[+pagetitle]]" class="lazyload">
```

Не трогал:

- homepage top category CLS-fix (`getres_mainTpl`, `getres_mainTpl_Firth`);
- самописную carousel-логику;
- `cardCategories`;
- robots/sitemap/прочие SEO-файлы.

## Бэкап

Перед правкой создан server backup:

```text
/root/backups/m-trud_iter10_product_card_images_20260510T104114Z/
```

Локальные артефакты:

- `backup_manifest.json`
- `chunk_102_before.tsv`
- `chunk_102_after.tsv`

## Проверка кода/HTML

Проверены страницы:

- `/production/boxes/3`
- `/production/boxes/korobki-s-ruchkami`
- `/production/boxes/korobki-na-magnite`
- `/production/paper-bags`
- `/production/folders`

Результат по `.ready-card-item img`:

```text
with_attrs = 0
```

То есть у товарных карточек больше нет `width`, `height`, `decoding` из iter9.

Главная осталась с отдельной защитой размеров для верхних категорий.

## Smoke

```json
{
  "pages_crawled": 15,
  "links_checked": 201,
  "broken_count": 0,
  "broken_sample": []
}
```
