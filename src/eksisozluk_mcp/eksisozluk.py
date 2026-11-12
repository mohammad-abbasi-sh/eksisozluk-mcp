"""Stdlib parsing for eksisozluk.com (Ekşi Sözlük — "kutsal bilgi kaynağı").

Verified live 2026-11-12 against real pages (fixtures in tests/):
- Topic list (/basliklar/gundem, /basliklar/kanal/<name>,
  /basliklar/ara?SearchText=<q>): a <ul class="topic-list partial">
  with ~50 <li> items (plus 1-2 ad/script <li>s, skipped). Each topic
  is <a href="/<slug>--<id>[?a=popular]">title <small>count</small></a>
  — the anchor tag itself may span lines, so patterns use \\s+.
  List pagination: ?p=2 (gündem, kanal, ara).
- Topic page (/<slug>--<id>): <h1 id="title"> is the topic title;
  entries are <li data-id="<entry-id>"> inside <ul id="entry-item-list">,
  10 per page. Each entry: <div class="content"> text with <br/> line
  breaks; footer has <a class="entry-author" href="/biri/<nick>"> and
  <a class="entry-date permalink" href="/entry/<id>">date</a> (date text
  like "28.03.1999 ~ 20.11.2005 22:40" — first date = creation, second
  after ~ = last edit). Entry pagination: the pager carries
  data-currentpage / data-pagecount attributes (e.g. starbucks: 888).
  Sort modes: default (recent), ?a=popular (şükela), ?a=dailynice
  (son 24 saat), ?a=nice (şükela tümü).
- Search resolve (/?q=<exact title>): 302 to /<slug>--<id> for an exact
  topic title; 404 when no topic has that exact title. Partial matches
  do NOT resolve — use /basliklar/ara for those.
- Debe (/debe, "dünün en beğenilen entry'leri"): 10-12 topic groups; each
  group is headed by an <h1 id="title" data-slug="..." data-id="...">
  (topic title in its <span itemprop="name">) followed by a
  <ul id="entry-item-list"> with that topic's top entries. Groups and
  ULs are zipped by order.

Content note: entries are unfiltered user-generated text — they may
contain profanity, slang and strong opinions. The server returns what
the site publishes, verbatim; nothing is censored or rewritten.
"""
from __future__ import annotations

import html as _html
import re

BASE = "https://eksisozluk.com"

_WS = re.compile(r"\s+")

# Channels seen on the site's own navigation (2026-11-12). The parser
# accepts any channel slug — the site 404s unknown ones — but the tool
# validates against this list for a friendly error.
CHANNELS = (
    "spor", "siyaset", "iliskiler", "yasam", "seyahat", "muzik", "tv",
    "haber", "bilim", "edebiyat", "kripto", "teknoloji", "sinema",
    "oyun", "saglik", "tarih", "felsefe", "mizah",
)

SORTS = ("recent", "popular", "dailynice", "nice")
_SORT_PARAM = {"recent": None, "popular": "popular",
               "dailynice": "dailynice", "nice": "nice"}


def sort_param(sort: str) -> str | None:
    """URL `a=` value for a sort name, or None for the default (recent)."""
    return _SORT_PARAM[sort]


def _clean(text: str | None) -> str:
    if not text:
        return ""
    return _WS.sub(" ", _html.unescape(text)).strip()


def _strip_tags(fragment: str) -> str:
    return _clean(re.sub(r"<[^>]+>", " ", fragment))


def _topic_from_href(href: str) -> tuple[str, str] | None:
    """'/slug--12345?a=popular' -> (slug, '12345'); None if no --id."""
    m = re.match(r"/([^/]+?)--(\d+)(?:[?#].*)?$", href.strip())
    if not m:
        return None
    return m.group(1), m.group(2)


def parse_topic_list(page_html: str) -> list[dict]:
    """Topic rows from a gündem / kanal / ara list page.

    Returns [{title, slug, topic_id, entry_count, url}], in page order,
    deduped by topic_id. Ad/script <li>s (no --id link) are skipped.
    """
    m = re.search(
        r'<ul class="topic-list partial"[^>]*>(.*?)</ul>', page_html, re.S
    )
    segment = m.group(1) if m else page_html
    topics: list[dict] = []
    seen: set[str] = set()
    for href, inner in re.findall(
        r'<a\s+href="([^"]+)"[^>]*>(.*?)</a>', segment, re.S
    ):
        parsed = _topic_from_href(href)
        if not parsed:
            continue
        slug, topic_id = parsed
        if topic_id in seen:
            continue
        seen.add(topic_id)
        count_m = re.search(r"<small>([\d.,]+)</small>", inner)
        title = _strip_tags(
            re.sub(r"<small>.*?</small>", "", inner, flags=re.S)
        )
        if not title:
            continue
        topics.append({
            "title": title,
            "slug": slug,
            "topic_id": topic_id,
            "entry_count": (
                int(count_m.group(1).replace(".", "").replace(",", ""))
                if count_m else None
            ),
            "url": f"{BASE}/{slug}--{topic_id}",
        })
    return topics


def _entry_from_chunk(entry_id: str, chunk: str) -> dict | None:
    content_m = re.search(
        r'<div class="content">(.*?)</div>', chunk, re.S
    )
    if not content_m:
        return None
    text = content_m.group(1)
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = _html.unescape(text)
    # Collapse horizontal whitespace; keep single newlines as paragraph
    # breaks, and drop blank lines.
    lines = [" ".join(ln.split()) for ln in text.split("\n")]
    text = "\n".join(ln for ln in lines if ln)
    author_m = re.search(
        r'<a\s+class="entry-author"\s+href="/biri/([^"]+)">([^<]+)</a>',
        chunk,
    )
    date_m = re.search(
        r'<a\s+class="entry-date permalink"\s+href="/entry/\d+">([^<]+)</a>',
        chunk,
    )
    return {
        "entry_id": entry_id,
        "text": text,
        "author": author_m.group(2) if author_m else None,
        "author_url": (
            f"{BASE}/biri/{author_m.group(1)}" if author_m else None
        ),
        "date": _clean(date_m.group(1)) if date_m else None,
        "url": f"{BASE}/entry/{entry_id}",
    }


def parse_entries(page_html: str) -> list[dict]:
    """Entries from a topic page or a debe page.

    Collects every <ul id="entry-item-list"> on the page (a topic page
    has one; /debe has one per topic group) and returns all entries in
    page order. Entries without a content div are skipped.
    """
    entries: list[dict] = []
    for ul in re.findall(
        r'<ul id="entry-item-list"[^>]*>(.*?)</ul>', page_html, re.S
    ):
        parts = re.split(r'<li[^>]*?data-id="(\d+)"[^>]*>', ul)
        # parts: [pre, id1, body1, id2, body2, ...]
        for i in range(1, len(parts) - 1, 2):
            entry = _entry_from_chunk(parts[i], parts[i + 1])
            if entry is not None:
                entries.append(entry)
    return entries


def parse_topic_title(page_html: str) -> str | None:
    """Topic title from <h1 id="title">, or None."""
    m = re.search(r'<h1[^>]*id="title"[^>]*>(.*?)</h1>', page_html, re.S)
    return _strip_tags(m.group(1)) if m else None


def parse_page_count(page_html: str) -> dict:
    """Entry pagination from the pager div.

    Returns {"page": current, "page_count": total} — both None when the
    page carries no pager (e.g. a topic with a single page).
    """
    m = re.search(
        r'class="pager"[^>]*data-currentpage="(\d+)"[^>]*'
        r'data-pagecount="(\d+)"',
        page_html,
    )
    if not m:
        m = re.search(
            r'data-pagecount="(\d+)"[^>]*data-currentpage="(\d+)"',
            page_html,
        )
        if not m:
            return {"page": None, "page_count": None}
        return {"page": int(m.group(2)), "page_count": int(m.group(1))}
    return {"page": int(m.group(1)), "page_count": int(m.group(2))}


def parse_debe(page_html: str) -> list[dict]:
    """Yesterday's most-liked entries, grouped by topic.

    Returns [{topic_slug, topic_id, topic_title, entries: [...]}] — one
    group per topic, in page order. Each group is headed by an
    <h1 id="title" data-slug="..." data-id="..."> carrying an anchor
    to /<slug>--<id> and a <span itemprop="name"> title, followed by
    its own <ul id="entry-item-list">. Headers and entry lists are
    zipped by order (the page renders one header per group, each
    followed by its list).
    """
    headers = []
    for h1 in re.findall(r'<h1[^>]*id="title"[^>]*>(.*?)</h1>', page_html, re.S):
        link_m = re.search(r'href="(/[^"]+--\d+)"', h1)
        title_m = re.search(
            r'<span[^>]*itemprop="name"[^>]*>(.*?)</span>', h1, re.S
        )
        if not link_m or not title_m:
            continue
        parsed = _topic_from_href(link_m.group(1))
        if not parsed:
            continue
        slug, topic_id = parsed
        headers.append((slug, topic_id, _strip_tags(title_m.group(1))))
    lists = re.findall(
        r'<ul id="entry-item-list"[^>]*>(.*?)</ul>', page_html, re.S
    )
    groups: list[dict] = []
    for (slug, topic_id, title), ul in zip(headers, lists):
        parts = re.split(r'<li[^>]*?data-id="(\d+)"[^>]*>', ul)
        entries = []
        for i in range(1, len(parts) - 1, 2):
            entry = _entry_from_chunk(parts[i], parts[i + 1])
            if entry is not None:
                entries.append(entry)
        if entries:
            groups.append({
                "topic_slug": slug,
                "topic_id": topic_id,
                "topic_title": _clean(title),
                "topic_url": f"{BASE}/{slug}--{topic_id}",
                "entries": entries,
            })
    return groups
