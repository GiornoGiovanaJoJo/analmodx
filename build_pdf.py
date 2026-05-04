# -*- coding: utf-8 -*-
"""
Build m-trud_audit_consolidated.pdf from _extracted.json + static analysis sections.
Run: python build_pdf.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from typing import Any, List

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

BASE = os.path.dirname(os.path.abspath(__file__))
OUT_PDF = os.path.join(BASE, "m-trud_audit_consolidated.pdf")
JSON_PATH = os.path.join(BASE, "_extracted.json")


def register_fonts() -> None:
    font_dir = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")
    mapping = [
        ("Arial", "arial.ttf"),
        ("Arial-Bold", "arialbd.ttf"),
        ("Arial-Italic", "ariali.ttf"),
        ("Arial-BoldItalic", "arialbi.ttf"),
        ("Consolas", "consola.ttf"),
    ]
    for name, fn in mapping:
        path = os.path.join(font_dir, fn)
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Font not found: {path}")
        pdfmetrics.registerFont(TTFont(name, path))
    pdfmetrics.registerFontFamily(
        "Arial",
        normal="Arial",
        bold="Arial-Bold",
        italic="Arial-Italic",
        boldItalic="Arial-BoldItalic",
    )


def esc(s: Any) -> str:
    if s is None:
        return ""
    t = str(s)
    return (
        t.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def is_code_like(text: str) -> bool:
    t = text.strip()
    if not t:
        return False
    if t.startswith("<"):
        return True
    if t.startswith(".") and "{" in t:
        return True
    if re.match(r"^[.#][\w\-]+\s*\{", t):
        return True
    if t.startswith("  ") and "<" in t:
        return True
    if "{" in t and "}" in t and ":" in t and ("px" in t or "color" in t or "font" in t):
        return True
    return False


def load_json() -> dict:
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def make_styles() -> dict:
    base = getSampleStyleSheet()
    styles = {
        "Title": ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontName="Arial-Bold",
            fontSize=18,
            leading=22,
            alignment=TA_CENTER,
            spaceAfter=12,
        ),
        "Subtitle": ParagraphStyle(
            "Subtitle",
            parent=base["Normal"],
            fontName="Arial",
            fontSize=11,
            leading=14,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#333333"),
            spaceAfter=18,
        ),
        "H1": ParagraphStyle(
            "H1",
            parent=base["Heading1"],
            fontName="Arial-Bold",
            fontSize=14,
            leading=18,
            spaceBefore=14,
            spaceAfter=8,
            outlineLevel=0,
        ),
        "H2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontName="Arial-Bold",
            fontSize=12,
            leading=15,
            spaceBefore=10,
            spaceAfter=6,
            outlineLevel=1,
        ),
        "H3": ParagraphStyle(
            "H3",
            parent=base["Heading3"],
            fontName="Arial-Bold",
            fontSize=11,
            leading=14,
            spaceBefore=8,
            spaceAfter=4,
        ),
        "Body": ParagraphStyle(
            "Body",
            parent=base["Normal"],
            fontName="Arial",
            fontSize=10,
            leading=13,
            alignment=TA_JUSTIFY,
            spaceAfter=4,
        ),
        "BodyMono": ParagraphStyle(
            "BodyMono",
            parent=base["Code"],
            fontName="Consolas",
            fontSize=8.5,
            leading=10,
            leftIndent=6,
            spaceAfter=3,
        ),
        "TOC0": ParagraphStyle(
            "TOC0",
            fontName="Arial",
            fontSize=11,
            leading=14,
            firstLineIndent=0,
            leftIndent=20,
            spaceBefore=2,
        ),
        "TOC1": ParagraphStyle(
            "TOC1",
            fontName="Arial",
            fontSize=10,
            leading=13,
            firstLineIndent=0,
            leftIndent=36,
            spaceBefore=1,
        ),
    }
    return styles


class TocDocTemplate(SimpleDocTemplate):
    def __init__(self, filename, **kw):
        self._heading_seq = 0
        SimpleDocTemplate.__init__(self, filename, **kw)

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            st = flowable.style.name
            txt = flowable.getPlainText()
            if st == "H1":
                self.canv.bookmarkPage(f"h1-{self._heading_seq}")
                self.notify("TOCEntry", (0, txt, self.page))
                self._heading_seq += 1
            elif st == "H2":
                self.notify("TOCEntry", (1, txt, self.page))


def add_heading(story: list, styles: dict, level: str, text: str) -> None:
    story.append(Paragraph(esc(text), styles[level]))


def add_body(story: list, styles: dict, text: str) -> None:
    if not (text or "").strip():
        return
    story.append(Paragraph(esc(text), styles["Body"]))


def dump_docx_paragraphs(story: list, styles: dict, paragraphs: list) -> None:
    for p in paragraphs:
        style_name = p.get("style") or "Normal"
        text = p.get("text") or ""
        if style_name.startswith("Heading 1"):
            add_heading(story, styles, "H1", text)
        elif style_name.startswith("Heading"):
            add_heading(story, styles, "H2", text)
        elif is_code_like(text):
            story.append(
                Preformatted(text, styles["BodyMono"], maxLineLength=120)
            )
        else:
            add_body(story, styles, text)


def dump_docx_tables(story: list, styles: dict, tables: list) -> None:
    for ti, table in enumerate(tables):
        if not table:
            continue
        add_heading(story, styles, "H3", f"Таблица {ti + 1}")
        w = max(len(r) for r in table)
        data: List[List[Any]] = []
        for row in table:
            cells = []
            for c in row:
                cells.append(Paragraph(esc(c or ""), styles["Body"]))
            while len(cells) < w:
                cells.append(Paragraph("", styles["Body"]))
            data.append(cells)
        t = Table(data, repeatRows=1, hAlign="LEFT")
        t.setStyle(
            TableStyle(
                [
                    ("FONT", (0, 0), (-1, -1), "Arial", 8),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        story.append(t)
        story.append(Spacer(1, 8))


def dump_sheet(story: list, styles: dict, sheet_name: str, rows: list) -> None:
    add_heading(story, styles, "H2", f"Лист: {sheet_name}")
    if not rows:
        add_body(story, styles, "(пусто)")
        return
    max_cols = max((len(r) for r in rows), default=0)
    data: List[List[Any]] = []
    for row in rows:
        out_row = []
        for j in range(max_cols):
            val = row[j] if j < len(row) else None
            if val is None or val == "":
                out_row.append(Paragraph("", styles["Body"]))
            else:
                out_row.append(Paragraph(esc(val), styles["Body"]))
        if any(
            (row[j] if j < len(row) else None) not in (None, "")
            for j in range(max_cols)
        ):
            data.append(out_row)
    if not data:
        add_body(story, styles, "(нет непустых строк)")
        return
    col_widths = [(A4[0] - 4 * cm) / max_cols] * max_cols
    t = Table(data, colWidths=col_widths, repeatRows=0, hAlign="LEFT")
    t.setStyle(
        TableStyle(
            [
                ("FONT", (0, 0), (-1, -1), "Arial", 7.5),
                ("GRID", (0, 0), (-1, -1), 0.2, colors.lightgrey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 10))


def part2_analysis(story: list, styles: dict) -> None:
    add_heading(story, styles, "H1", "Часть II. Аналитика и сопоставление")
    add_heading(story, styles, "H2", "2.1 ТЗ Кузнецова (HTML) и внутренний аудит (README / audit_mtrud.md, 24.04.2026)")

    rows = [
        ["Тема", "ТЗ Кузнецова (HTML)", "Внутренний аудит"],
        [
            "Невалидный тег <spam>",
            "P0: заменить на span, label for/id",
            "Подтверждено на главной (аналитика xlsx)",
        ],
        [
            "Структура ul/li, ul в span",
            "P0: пересборка меню",
            "Согласуется с PSI-доступностью (нет main, списки)",
        ],
        [
            "img без src, lazy",
            "P0: placeholder src + data-src",
            "Главная: нет width/height → CLS; lazy через класс",
        ],
        [
            "Дубли id (catalog_form)",
            "P0: уникальные id",
            "Совпадает с рисками JS",
        ],
        [
            "min=\"\", pattern email",
            "P0–P1",
            "Дополняет чистку форм",
        ],
        [
            "font/align, void-слэши",
            "P2–P3",
            "Мусор в шаблонах MODX",
        ],
        [
            "Пробелы в href",
            "—",
            "audit_mtrud: production/boxes и др.",
        ],
        [
            "Render-blocking JS",
            "—",
            "scripts_p4f0c613bd6.js без defer",
        ],
        [
            "MODX Login Extra (object injection)",
            "—",
            "Dashboard warning (аналитика)",
        ],
        [
            "PHP 7.4 EOL, gzip/Brotli",
            "—",
            "audit_mtrud.md",
        ],
    ]
    tbl = Table([[Paragraph(esc(c), styles["Body"]) for c in r] for r in rows], colWidths=[4.2 * cm, 5.3 * cm, 5.3 * cm])
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0e0e0")),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONT", (0, 0), (-1, -1), "Arial", 8),
            ]
        )
    )
    story.append(tbl)
    story.append(Spacer(1, 10))

    add_heading(story, styles, "H2", "2.2 PageSpeed (Кузнецов) и внутренний аудит")
    rows2 = [
        ["Тема", "Кузнецов (PSI docx)", "Внутренний аудит (аналитика / Lighthouse)"],
        ["CLS", "0.52 — высокий", "0.519 mobile — критично"],
        ["LCP", "4.2 с", "6.2 с mobile — хуже в лаборатории"],
        ["Размеры img", "Нет размеров", "36/36 без width/height на главной"],
        ["Блокирующий JS/CSS", "scripts_… общий", "4 файла без defer/async перечислены"],
        ["Кэш статики", "Долгий max-age", "План P1: Cache-Control immutable"],
        ["Заголовки безопасности", "CSP, COOP, HSTS…", "audit: HSTS есть; CSP и др. — доработка"],
        ["jQuery 1.9.1", "Устаревшие библиотеки", "Legacy-стек MODX"],
        ["Sitemap / главная", "—", "Главная не в sitemap (audit)"],
        ["robots.txt", "—", "Дубли, конфликт Disallow/Allow по query"],
    ]
    tbl2 = Table([[Paragraph(esc(c), styles["Body"]) for c in r] for r in rows2], colWidths=[3.8 * cm, 5.5 * cm, 5.5 * cm])
    tbl2.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0e0e0")),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONT", (0, 0), (-1, -1), "Arial", 8),
            ]
        )
    )
    story.append(tbl2)
    story.append(Spacer(1, 10))

    add_heading(story, styles, "H2", "2.3 Сводка: этап → фокус → стоимость (из «план работ»)")
    rows3 = [
        ["Этап", "Сумма, ₽", "Фокус"],
        ["P0 (срочно)", "15 000", "Login extra, URL-политика nginx/MODX, canonical для query"],
        ["P1", "15 000", "defer JS, вынести inline, CLS/img, <spam>, href, DB cache, Cache-Control"],
        ["P2", "8 000", "Lazy нативный, LCP preload, schema JSON-LD, robots/sitemap"],
        ["P3", "3 000", "Lighthouse по расписанию, дашборды Метрики, чек-лист релиза"],
        ["Итого", "41 000", "Ожидаемый mobile 46–47 → 65–80"],
    ]
    tbl3 = Table([[Paragraph(esc(c), styles["Body"]) for c in r] for r in rows3], colWidths=[3.5 * cm, 2.5 * cm, 8.8 * cm])
    tbl3.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0e0e0")),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                ("FONT", (0, 0), (-1, -1), "Arial", 9),
            ]
        )
    )
    story.append(tbl3)


def part3_answers(story: list, styles: dict) -> None:
    add_heading(story, styles, "H1", "Часть III. Ответы на вопросы из листа «доп вопросы»")

    blocks = [
        (
            "Вопрос 1. На каком этапе исправляется Canonical?",
            (
                "Краткий ответ: в этапе P0–P1, сразу после URL-нормализации и вместе с политикой query-параметров.",
                "Пояснение: в «план работ» P0 уже указано «жёстко определить canonical для query-URL» (301 на канон или canonical + noindex). Отдельно необходимо проставить rel=\"canonical\" в <head> на всех страницах, где его нет — в первую очередь главная, листинги и страницы с фильтрами (лист «Canonical» и audit_mtrud: на главной canonical = 0).",
                "Стоимость: входит в смету P0/P1 (15 000 + 15 000 ₽), отдельной строки не требуется.",
            ),
        ),
        (
            "Вопрос 2. Уязвимость доступа в админскую панель",
            (
                "Краткий ответ: публичный URL /manager/ — нормальная схема для MODX, но риск брутфорса снижается сочетанием мер; отдельно — срочно обновить Login Extra (предупреждение PHP Object Injection на dashboard).",
                "Что делаем: (1) по возможности сменить путь manager в конфигурации MODX; (2) ограничить доступ к /manager/ по IP в nginx или через security-плагин; (3) убрать из robots.txt строку Disallow: /manager/ — она лишь подсвечивает путь (лист «сео дырки»). Плюс 2FA, сложные пароли, fail2ban.",
                "Стоимость: обновление extra и базовая защита — в P0 (15 000 ₽).",
            ),
        ),
        (
            "Вопрос 3. HTML-ошибки (файл ТЗ Кузнецова) — совпадают с вашей информацией?",
            (
                "Краткий ответ: да, по сути P0–P2 из docx совпадают с выводами внутренней аналитики (<spam>, структура списков, формы, img, id).",
                "Дополнения нашего аудита: пробелы в href, четыре конкретных блокирующих скрипта, предупреждение по Login Extra, отсутствие gzip/Brotli на части статики, PHP 7.4 EOL — этого в HTML-TZ Кузнецова нет.",
                "Стоимость: работы по HTML — в P1 «гигиенические дефекты».",
            ),
        ),
        (
            "Вопрос 4. Рекомендации PageSpeed (файл Кузнецова) — совпадают?",
            (
                "Краткий ответ: да, направления совпадают: CLS, LCP, размеры и форматы изображений, минификация/бандлы, кэш, preconnect, lazy для below-the-fold, безопасность, legacy jQuery.",
                "Различия: у Кузнецова LCP 4.2 с и CLS 0.52; в проработке программистов зафиксированы LCP 6.2 с и CLS 0.519 — это разные срезы Lighthouse, но одна проблема. Внутренний план добавляет явный список из 4 render-blocking файлов, sitemap/robots, DB cache MODX.",
                "Стоимость: P1 + P2 по смете.",
            ),
        ),
        (
            "Вопрос 5. Новый robots.txt и рекомендация «noindex в meta, а не Disallow для закрытых от индекса страниц» — нормально?",
            (
                "Краткий ответ: да, рекомендация корректна с точки зрения SEO: Disallow в robots.txt запрещает краулинг (Google может не видеть страницу и не применить noindex с URL), а meta robots noindex в HTML явно запрещает индексацию, когда страница доступна краулеру.",
                "План: упростить robots.txt (убрать дубли, согласовать правила для User-agent, разрулить конфликт Disallow: /*? и Allow: /*?v=*). Для мусорных и служебных URL — canonical/301 или meta noindex по смыслу. Disallow: /manager/ убрать (см. вопрос 2).",
                "Стоимость: P2 (8 000 ₽) — блок robots/sitemap.",
            ),
        ),
        (
            "Вопрос 6. Боковое меню: на части страниц при переходе меню сворачивается — корректно ли?",
            (
                "Краткий ответ: для UX каталога обычно ожидают, что активная ветка остаётся раскрытой; непоследовательное поведение — баг или разные шаблоны.",
                "Диагностика: сравнить шаблоны/чанки страниц «сворачивающих» (оригинальные, крафт, бумага тишью и перечисленные в xlsx) с эталоном «конструкции коробок → на магните»; проверить JS, который выставляет классы open/active и data-атрибуты текущего раздела.",
                "Стоимость: включить в P1 «чистка фронта» без отдельной строки; при необходимости оценить дополнительно после 2–4 часов анализа.",
            ),
        ),
    ]

    for title, paras in blocks:
        add_heading(story, styles, "H2", title)
        for p in paras:
            add_body(story, styles, p)
        story.append(Spacer(1, 8))


def part4_plan(story: list, styles: dict) -> None:
    add_heading(story, styles, "H1", "Часть IV. Уточнённый план P0–P3 и чек-лист релиза")

    add_heading(story, styles, "H2", "P0 — срочно")
    for line in [
        "Обновить Login Extra (уязвимость PHP Object Injection).",
        "URL: схлопывание //, 301 с index.php?q=* на чистый URL, единая политика слеша в конце.",
        "Canonical: rel=\"canonical\" на главной и типовых шаблонах; политика для URL с utm и прочими query (канон на чистый URL или 301).",
        "Безопасность входа: рассмотреть смену пути manager, ограничение по IP, убрать Disallow: /manager/ из robots.",
    ]:
        add_body(story, styles, f"• {line}")

    add_heading(story, styles, "H2", "P1 — performance baseline и чистка фронта")
    for line in [
        "defer/async для четырёх блокирующих скриптов (или пересборка MinifyX).",
        "Вынести inline JS/CSS в версионированные файлы; инвентаризация legacy-плагинов.",
        "width/height для ключевых изображений; исправить <spam>, пробелы в href.",
        "Включить и протестировать cache_db в MODX; Cache-Control для статики.",
        "Боковое меню: унифицировать поведение раскрытия (см. вопрос 6).",
    ]:
        add_body(story, styles, f"• {line}")

    add_heading(story, styles, "H2", "P2 — изображения, schema, robots/sitemap")
    for line in [
        "Нативный loading=\"lazy\" + decoding=\"async\" где уместно; LCP: preload + fetchpriority=\"high\".",
        "Унификация микроразметки (предпочтительно JSON-LD), валидация по типам страниц.",
        "robots.txt: без дублей, согласованные правила; sitemap: добавить главную, актуализировать lastmod.",
    ]:
        add_body(story, styles, f"• {line}")

    add_heading(story, styles, "H2", "P3 — контроль качества")
    for line in [
        "Регламентный Lighthouse mobile/desktop.",
        "Дашборды Метрики: 404 по паттернам, доля параметрических URL, боты/не боты.",
    ]:
        add_body(story, styles, f"• {line}")

    add_heading(story, styles, "H2", "Чек-лист перед релизом шаблонов")
    for line in [
        "Нет критичных ошибок валидатора по меню и формам (P0).",
        "Нет malformed href; нет <spam>; уникальные id.",
        "Canonical присутствует на главной и в шаблонах листингов/карточек.",
        "Schema проходит Rich Results Test на выборке URL.",
        "Статика с долгим кэшем; HTML без лишнего inline-мусора.",
        "/manager/ защищён по политике заказчика (IP / смена URL / мониторинг).",
    ]:
        add_body(story, styles, f"☐ {line}")

    story.append(Spacer(1, 12))
    add_heading(story, styles, "H2", "Заключение")
    add_body(
        story,
        styles,
        "Итоговая смета по проработке: 41 000 ₽ (P0 15 000 + P1 15 000 + P2 8 000 + P3 3 000). "
        "Ожидаемый эффект: рост mobile Lighthouse с ~46–47 до порядка 65–80 при глубине внедрения; существенное снижение CLS после фиксации размеров изображений и стабилизации вёрстки; снижение шума 404 в Метрике после нормализации URL.",
    )


def build_story(data: dict, styles: dict) -> list:
    story: list = []

    # Title
    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph(esc("Аудит m-trud.ru"), styles["Title"]))
    story.append(
        Paragraph(
            esc("Сводный отчёт: полные данные источников, сопоставление с аудитом 24.04.2026, ответы на вопросы клиента"),
            styles["Subtitle"],
        )
    )
    story.append(
        Paragraph(
            esc(
                "Дата PDF: 27.04.2026. Источники: ТЗ Кузнецова (HTML), ТЗ Кузнецова (PageSpeed), "
                "проработка от программистов (xlsx); опора: README.md, audit_mtrud.md."
            ),
            styles["Body"],
        )
    )
    story.append(PageBreak())

    # TOC
    toc = TableOfContents()
    toc.levelStyles = [styles["TOC0"], styles["TOC1"]]
    story.append(Paragraph(esc("Оглавление"), styles["H1"]))
    story.append(toc)
    story.append(PageBreak())

    # --- Part I ---
    add_heading(story, styles, "H1", "Часть I. Полное извлечённое содержимое источников")

    docx_keys = [k for k, v in data.items() if v.get("type") == "docx"]
    xlsx_key = next((k for k, v in data.items() if v.get("type") == "xlsx"), None)

    html_key = next((k for k in docx_keys if "HTML" in k or "html" in k.lower()), docx_keys[0] if docx_keys else None)
    psi_key = next((k for k in docx_keys if k != html_key), None)

    if html_key:
        add_heading(story, styles, "H2", f"1.1 Документ: {html_key}")
        dump_docx_paragraphs(story, styles, data[html_key]["paragraphs"])
        dump_docx_tables(story, styles, data[html_key].get("tables") or [])
        story.append(PageBreak())

    if psi_key:
        add_heading(story, styles, "H2", f"1.2 Документ: {psi_key}")
        dump_docx_paragraphs(story, styles, data[psi_key]["paragraphs"])
        dump_docx_tables(story, styles, data[psi_key].get("tables") or [])
        story.append(PageBreak())

    if xlsx_key:
        sheets = data[xlsx_key].get("sheets") or {}
        add_heading(story, styles, "H2", f"1.3 Файл: {xlsx_key}")
        order = ["аналитика", "план работ", "Canonical", "сео дырки", "доп вопросы"]
        for name in order:
            if name in sheets:
                dump_sheet(story, styles, name, sheets[name])
        for name, rows in sheets.items():
            if name not in order:
                dump_sheet(story, styles, name, rows)
        story.append(PageBreak())

    part2_analysis(story, styles)
    story.append(PageBreak())
    part3_answers(story, styles)
    story.append(PageBreak())
    part4_plan(story, styles)

    return story


def main_fixed() -> None:
    register_fonts()
    styles = make_styles()
    data = load_json()

    class DocWithFooter(TocDocTemplate):
        def __init__(self, *a, **kw):
            TocDocTemplate.__init__(self, *a, **kw)

        def handle_pageEnd(self):
            self.canv.saveState()
            self.canv.setFont("Arial", 8)
            w, _h = self.pagesize
            self.canv.drawCentredString(w / 2, 1.2 * cm, f"Стр. {self.canv.getPageNumber()}")
            self.canv.restoreState()
            super().handle_pageEnd()

    doc = DocWithFooter(
        OUT_PDF,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2.2 * cm,
    )
    story = build_story(data, styles)
    doc.multiBuild(story)


if __name__ == "__main__":
    try:
        main_fixed()
    except Exception as e:
        print("Error:", e, file=sys.stderr)
        raise
    print("OK:", OUT_PDF, "size=", os.path.getsize(OUT_PDF))
