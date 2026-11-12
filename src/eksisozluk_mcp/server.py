"""MCP server: unofficial read-only access to eksisozluk.com (Ekşi Sözlük)."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone

from mcp.server.fastmcp import FastMCP

from . import eksisozluk as _E
from . import http as _http

mcp = FastMCP("eksisozluk-mcp")

INSTRUCTIONS = """\
Unofficial read-only MCP server for eksisozluk.com — Ekşi Sözlük,
Türkiye's iconic collaborative dictionary / social platform ("kutsal
bilgi kaynağı"), where users write short entries under topic titles.
eksisozluk_trending lists the gündem (trending topics) with entry
counts; eksisozluk_search_topics searches topic titles
(/basliklar/ara); eksisozluk_get_topic returns a topic's entries —
give it a "slug--id", a numeric topic id, or an exact topic title
(resolved via the site's /?q= redirect; partial titles must go
through eksisozluk_search_topics) — with sort recent (default),
popular (şükela), dailynice (son 24 saat) or nice (şükela tümü), and
page support (10 entries per page; page_count is returned);
eksisozluk_channel_topics lists a channel's topics (spor, siyaset,
ilişkiler, yaşam, seyahat, müzik, tv, haber, bilim, edebiyat, kripto
and more); eksisozluk_debe returns yesterday's most-liked entries,
grouped by topic. Entries are unfiltered user-generated text — they
may contain profanity, slang and strong opinions; the server returns
what the site publishes, verbatim. Data comes from the site's
server-rendered pages — no login, no API key. Read-only; transport
uses Chrome TLS impersonation; requests are spaced ~0.8s apart.
Built by Mohammad Abbasi (mohammad-abbasi-sh) — https://almanibama.ir · https://mabbasi.ir — Turkey MCP
factory.\
"""


_SOURCE = "eksisozluk.com"
_DISCLAIMER = "Unofficial read-only data from eksisozluk.com; entries are unfiltered user-generated text — verify on the site before acting on it."


def _envelope() -> dict:
    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": _SOURCE,
        "disclaimer": _DISCLAIMER,
    }


def _ok(payload: dict) -> str:
    return json.dumps({**_envelope(), **payload}, ensure_ascii=False)


def _limit(limit: int) -> int:
    return max(1, min(int(limit), 50))


def _resolve_topic(topic: str) -> tuple[str, str] | None:
    """'slug--id' | 'id' | exact title -> (slug, id), or None."""
    topic = topic.strip()
    if not topic:
        return None
    for prefix in ("https://eksisozluk.com/", "http://eksisozluk.com/",
                   "eksisozluk.com/"):
        if topic.startswith(prefix):
            topic = topic[len(prefix):]
            break
    parsed = _E._topic_from_href("/" + topic if not topic.startswith("/") else topic)
    if parsed:
        return parsed
    if re.fullmatch(r"\d+", topic):
        return None  # bare id without a slug cannot build a topic URL
    return _http.resolve_topic(topic)


@mcp.tool()
def eksisozluk_trending(page: int = 1, limit: int = 20) -> str:
    """Gündem — the trending topics on eksisozluk.com right now.

    page: list page (50 topics per page). limit: 1..50 topics returned.
    Each topic: title, slug, topic_id, entry_count, url."""
    try:
        topics = _E.parse_topic_list(_http.fetch_gundem(page))
    except _http.EksisozlukError as e:
        return _ok({"error": str(e)})
    return _ok({"page": page, "count": len(topics[:_limit(limit)]),
                 "topics": topics[:_limit(limit)]})


@mcp.tool()
def eksisozluk_search_topics(query: str, page: int = 1, limit: int = 20) -> str:
    """Search topic titles on eksisozluk.com (partial matches welcome).

    query: Turkish search text (e.g. "ankar"). page: results page
    (50 topics per page). limit: 1..50 topics returned. Each topic:
    title, slug, topic_id, entry_count, url."""
    if not query or not query.strip():
        return _ok({"error": "query must not be empty"})
    try:
        topics = _E.parse_topic_list(_http.fetch_search(query.strip(), page))
    except _http.EksisozlukError as e:
        return _ok({"error": str(e)})
    return _ok({"query": query.strip(), "page": page,
                 "count": len(topics[:_limit(limit)]),
                 "topics": topics[:_limit(limit)]})


@mcp.tool()
def eksisozluk_get_topic(topic: str, sort: str = "recent",
                         page: int = 1, limit: int = 10) -> str:
    """Entries of one topic.

    topic: "slug--id" (e.g. "ankara--32788"), or an EXACT topic title
    (e.g. "ankara" — resolved via the site's /?q= redirect; a bare
    numeric id alone is not enough, and partial titles must go through
    eksisozluk_search_topics first). sort: "recent" (default),
    "popular" (şükela), "dailynice" (son 24 saat), "nice" (şükela
    tümü). page: entries page (10 per page); page_count is returned.
    limit: 1..10 entries returned. Each entry: entry_id, text, author,
    author_url, date, url."""
    if sort not in _E.SORTS:
        return _ok({"error": f"unknown sort {sort!r}",
                    "known_sorts": list(_E.SORTS)})
    resolved = _resolve_topic(topic)
    if resolved is None:
        return _ok({"error": f"no topic found for {topic!r} — try "
                    "eksisozluk_search_topics for partial titles",
                    "topic": topic})
    slug, topic_id = resolved
    try:
        html = _http.fetch_topic(slug, topic_id, sort, page)
    except _http.EksisozlukError as e:
        return _ok({"error": str(e)})
    entries = _E.parse_entries(html)
    pages = _E.parse_page_count(html)
    return _ok({"topic": _E.parse_topic_title(html),
                 "slug": slug, "topic_id": topic_id, "sort": sort,
                 "page": pages["page"] or page,
                 "page_count": pages["page_count"],
                 "count": len(entries[:_limit(limit)]),
                 "entries": entries[:_limit(limit)]})


@mcp.tool()
def eksisozluk_channel_topics(channel: str, page: int = 1,
                              limit: int = 20) -> str:
    """Topics of one eksisozluk.com channel.

    channel: e.g. "spor", "siyaset", "iliskiler", "yasam", "seyahat",
    "muzik", "tv", "haber", "bilim", "edebiyat", "kripto". page: list
    page (50 topics per page). limit: 1..50 topics returned."""
    channel = channel.strip().lower()
    if channel not in _E.CHANNELS:
        return _ok({"error": f"unknown channel {channel!r}",
                    "known_channels": list(_E.CHANNELS)})
    try:
        topics = _E.parse_topic_list(_http.fetch_channel(channel, page))
    except _http.EksisozlukError as e:
        return _ok({"error": str(e)})
    return _ok({"channel": channel, "page": page,
                 "count": len(topics[:_limit(limit)]),
                 "topics": topics[:_limit(limit)]})


@mcp.tool()
def eksisozluk_debe(limit: int = 10) -> str:
    """Yesterday's most-liked entries (debe), grouped by topic.

    limit: 1..12 topic groups returned (the site lists ~10-12). Each
    group: topic_slug, topic_id, topic_title, topic_url, entries
    (usually 1 top entry per topic)."""
    try:
        groups = _E.parse_debe(_http.fetch_debe())
    except _http.EksisozlukError as e:
        return _ok({"error": str(e)})
    return _ok({"count": len(groups[:_limit(limit)]),
                 "groups": groups[:_limit(limit)]})


@mcp.tool()
def eksisozluk_health() -> str:
    """Check whether eksisozluk.com is reachable right now.

    Returns status ok (HTTP 200), blocked (HTTP 403/429 — bot wall or
    rate limit) or error, plus the HTTP status and the probed URL.
    One polite request; it does not fetch any listings."""
    return _ok(_http.health_check())


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    import sys

    sys.exit(main())
