import { Callout, Divider, Grid, H1, H2, H3, Pill, Row, Stack, Stat, Table, Text } from "cursor/canvas";

export default function MTrudAuditCanvas() {
  return (
    <Stack gap={20}>
      <H1>Аудит m-trud.ru (MODX)</H1>
      <Text tone="secondary">Дата: 24.04.2026. Источники: краулинг 119 страниц, проверка 1811 ссылок, выборочная валидация 800 URL из sitemap, Lighthouse.</Text>

      <Grid columns={4} gap={12}>
        <Stat label="Проверено URL (sitemap)" value="800" />
        <Stat label="Проверено внутренних ссылок" value="1811" />
        <Stat label="404 в проверенных sitemap/link URL" value="0" tone="success" />
        <Stat label="Ключевой риск" value="URL-нормализация и дубли" tone="warning" />
      </Grid>

      <Callout tone="warning" title="Критичное наблюдение по 404">
        Реальных битых ссылок в корректно разрешенных URL не найдено, но есть технические URL-аномалии (двойные слеши, index.php?q=, query-параметры), которые почти наверняка дают шум в Метрике/логах как 404/мусорные хиты.
      </Callout>

      <Divider />

      <H2>1) 404, склейки URL, боты</H2>
      <Table
        headers={["Проблема", "Факт", "Риск", "Приоритет"]}
        rows={[
          ["Двойные / в URL", "/production/paper-bags// -> 301 -> /index.php?q=production/paper-bags/", "Шум в индексации, 404-переходы в отчётах", "P1"],
          ["Формат index.php?q=", "/index.php?q=production/paper-bags -> 301 -> clean URL", "Дубли адресов, лишние редиректы", "P1"],
          ["//production/... доступен как 200", "//production/paper-bags -> 200", "Потенциальный дубль URL", "P1"],
          ["Параметр q", "?q=abc -> 404", "Боты генерируют 404-хвост", "P2"],
          ["Маркетинг-параметры", "?utm_source, ?ysclid, ?fbclid отдают 200", "Краулинг мусорных URL без каноникал-редиректа", "P2"],
          ["Sitemap", "Первые 800 URL из 1341: все 200", "Сами целевые документы живые", "OK"],
        ]}
      />

      <H3>Что проверить в Метрике/логах в первую очередь</H3>
      <Text>1) Группировка 404 по шаблонам: `//`, `index.php?q=`, `?q=`, случайные query-хвосты.</Text>
      <Text>2) Доля роботов в 404 и в pageview: User-Agent, IP-подсети, аномальный referrer.</Text>
      <Text>3) Топ URL с 301-цепочками и page depth для ботов.</Text>

      <Divider />

      <H2>2) Performance (подтверждение проблемы ~46/100)</H2>
      <Grid columns={3} gap={12}>
        <Stat label="Mobile FCP" value="3.18s" tone="warning" />
        <Stat label="Mobile LCP" value="4.82s" tone="warning" />
        <Stat label="Mobile TBT" value="1704ms" tone="critical" />
      </Grid>
      <Grid columns={3} gap={12}>
        <Stat label="Desktop FCP" value="0.69s" tone="success" />
        <Stat label="Desktop LCP" value="1.40s" tone="success" />
        <Stat label="Desktop TBT" value="596ms" tone="warning" />
      </Grid>

      <Table
        headers={["Источник потерь", "Наблюдение", "Потенциал"]}
        rows={[
          ["JS main-thread", "Высокий TBT на mobile", "Декомпозиция/отложенная загрузка JS, минус 0.5-1.2s TBT"],
          ["Изображения next-gen", "Lighthouse фиксирует экономию ~255-274 KiB", "WebP/AVIF для ключевых изображений"],
          ["Размер и ресайз изображений", "Есть oversized изображения", "Снизить вес + ускорить LCP"],
          ["Render-blocking", "Есть блокирующие CSS/JS", "Сместить non-critical загрузки"],
        ]}
      />

      <Divider />

      <H2>3) Шаблоны и «мусор» в фронте</H2>
      <Table
        headers={["Метрика", "Факт", "Комментарий"]}
        rows={[
          ["Внешние скрипты", "19", "Много legacy jQuery-плагинов"],
          ["Inline script-блоки", "11", "Сложнее кэшировать/поддерживать"],
          ["CSS/Link-тегов", "36", "Признак дробления стилей"],
          ["DOM-узлов на главной", "1164", "Тяжелый DOM для mobile"],
          ["Inline style-атрибуты", "37 элементов", "Вероятный визуальный «мусор» в шаблонах"],
        ]}
      />
      <Text tone="secondary">На главной обнаружены legacy-скрипты (`jquery.easing`, `equalheights`, `mobilemenu`, `fancybox`, `maskedinput`) и единый MinifyX-бандл. Нужен аудит фактического использования скриптов/стилей по шаблонам и чанкам.</Text>

      <Divider />

      <H2>4) Изображения (WebP/JPG, lazy-load)</H2>
      <Table
        headers={["Проверка", "Факт", "Оценка"]}
        rows={[
          ["Всего img в выборке", "3223", "Большой объем медиа"],
          ["Ссылки на .webp", "94", "Используется, но не массово"],
          ["Ссылки на .jpg/.jpeg", "64", "Есть потенциал перевода в modern форматы"],
          ["Lazy-load", "2439 img", "Хорошо внедрено"],
          ["width/height у img на главной", "0/36", "Риск CLS и перерасчёта layout"],
          ["alt на главной", "3 изображения без alt", "SEO/доступность"],
        ]}
      />

      <Divider />

      <H2>5) Микроразметка и SEO-техника</H2>
      <Table
        headers={["Элемент", "Факт", "Комментарий"]}
        rows={[
          ["JSON-LD", "3 script-блока на главной", "Есть база (Organization/Nav)"],
          ["Microdata itemscope", "70 элементов (главная)", "Разметка объемная, нужен аудит консистентности"],
          ["Open Graph", "og:title присутствует", "Соц-превью базово настроены"],
          ["Canonical mismatch", "Не выявлен в краулинге", "Позитивно"],
        ]}
      />
      <Callout tone="warning" title="Риск микроразметки">
        На части страниц в сыром HTML встречается некорректная кодировка текста в JSON-LD (симптом mojibake в выборке). Нужно проверить, что фактическая разметка валидируется в Rich Results Test без ошибок кодировки/структуры.
      </Callout>

      <Divider />

      <H2>ТЗ / План оптимизации</H2>
      <H3>Этап 1 (1-3 дня): срочная техническая чистка</H3>
      <Text>• Нормализация URL на уровне nginx/MODX: единый вид без `index.php?q=`, без двойных слешей, со строгим canonical.</Text>
      <Text>• 301-правила: `//` -> `/`, `index.php?q=*` -> clean URL, унификация slash-политики.</Text>
      <Text>• Фильтрация бот-мусора: 410/444 для очевидных мусорных паттернов, rate-limit по аномальным запросам.</Text>
      <Text>• В Метрике: сегменты «роботы/не роботы», дашборд по паттернам 404.</Text>

      <H3>Этап 2 (3-7 дней): производительность и изображения</H3>
      <Text>• Разобрать MinifyX-бандл на критический и отложенный; загрузка non-critical через `defer`/`async`.</Text>
      <Text>• Вычистить неиспользуемые jQuery-плагины и дубли библиотек в чанках/шаблонах.</Text>
      <Text>• LCP-изображения: WebP/AVIF, `fetchpriority=\"high\"`, preload hero, контроль размеров.</Text>
      <Text>• Добавить `width/height` всем `img`, сохранить lazy-load для offscreen.</Text>

      <H3>Этап 3 (5-10 дней): шаблоны, кэш, микроразметка</H3>
      <Text>• Ревизия MODX-шаблонов/чанков: удаление «мертвого» HTML/inline-style/inline-script.</Text>
      <Text>• Кэш: актуализировать MODX-кэш-политику, TTL, прогрев, кэш статики через nginx (Cache-Control + immutable для версионированных файлов).</Text>
      <Text>• Валидация Schema.org по типам страниц (категория, карточка, статья, контакты), устранение предупреждений.</Text>
      <Text>• Финальный контроль: Lighthouse mobile, отчеты Core Web Vitals, дельта по 404 и бот-трафику.</Text>

      <Divider />

      <Row gap={8}>
        <Pill tone="critical">P1: URL-нормализация и дубль-адреса</Pill>
        <Pill tone="warning">P1: Снижение TBT/LCP на mobile</Pill>
        <Pill tone="info">P2: Чистка шаблонов и бандлов</Pill>
        <Pill tone="success">P2: Доработка изображений и schema</Pill>
      </Row>
    </Stack>
  );
}
