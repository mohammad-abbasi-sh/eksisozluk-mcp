# eksisozluk-mcp 🇹🇷

mcp-name: io.github.mohammad-abbasi-sh/eksisozluk-mcp

Unofficial **read-only** MCP server for eksisozluk.com — Ekşi Sözlük, Türkiye's iconic collaborative dictionary and social platform ("kutsal bilgi kaynağı"), where users write short entries under topic titles. Trending topics (gündem), topic search, entries with şükela sorting, channels, and yesterday's most-liked entries (debe).

> Built by Mohammad Abbasi as part of the "Turkey MCP factory" (Sepehr-style pipeline). Not affiliated with eksisozluk.com or Ekşi Sözlük.

**Content note:** entries are unfiltered user-generated text — they may contain profanity, slang and strong opinions. The server returns what the site publishes, verbatim; nothing is censored or rewritten.

## For AI agents

Add to your MCP client config (stdio):

```json
{
  "mcpServers": {
    "eksisozluk": {
      "command": "uvx",
      "args": ["eksisozluk-mcp==0.1.0"]
    }
  }
}
```

Or run locally: `python -m eksisozluk_mcp.server` (needs `mcp<2`, `curl-cffi`).

## Tools

| Tool | Description |
|------|-------------|
| `eksisozluk_trending` | Gündem — trending topics right now; `page` (50/page), `limit` 1..50; title, slug, topic_id, entry_count, url |
| `eksisozluk_search_topics` | Search topic titles (partial matches welcome) — `query` Turkish text (e.g. "ankar"); `page`, `limit` 1..50 |
| `eksisozluk_get_topic` | Entries of one topic — `topic` as "slug--id" (e.g. "ankara--32788") or an EXACT topic title (resolved via the site's /?q= redirect); `sort` ("recent" / "popular" şükela / "dailynice" son 24 saat / "nice" şükela tümü); `page` (10/page, page_count returned); `limit` 1..10 |
| `eksisozluk_channel_topics` | Topics of one channel — `channel` e.g. "spor", "siyaset", "iliskiler", "yasam", "seyahat", "muzik", "tv", "haber", "bilim", "edebiyat", "kripto"; `page`, `limit` 1..50 |
| `eksisozluk_debe` | Yesterday's most-liked entries (debe), grouped by topic; `limit` 1..12 groups |
| `eksisozluk_health` | Check whether eksisozluk.com is reachable (ok / blocked / error) |

Example output (`eksisozluk_get_topic` / ankara, 2026-11-12):

```json
{"topic": "ankara", "topic_id": "32788", "sort": "recent",
 "page": 1, "page_count": 3621,
 "entries": [{"entry_id": "3820", "author": "zomzom",
  "date": "28.03.1999 ~ 20.11.2005 22:40",
  "text": "yapay kent. baskent olmasaydi boktan bi yer olacakti muhakkak.",
  "url": "https://eksisozluk.com/entry/3820"}]}
```

## How it works

eksisozluk.com serves its pages fully server-rendered — no login, no API key, no session cookies. Topic lists are `<ul class="topic-list partial">` rows (`<a href="/<slug>--<id>">title <small>count</small></a>`, 50 per page, `?p=2` pagination). Topic pages list 10 entries per page in `<ul id="entry-item-list">` (`<li data-id>` with a `<div class="content">`, author link `/biri/<nick>`, date link `/entry/<id>`); the pager carries `data-pagecount` (ankara: 3,621 pages; starbucks: 888). Sort modes are `?a=popular` (şükela), `?a=dailynice` (son 24 saat), `?a=nice` (şükela tümü). The search box's exact-title lookup (`/?q=<title>`) 302-redirects to the topic only for an exact title and 404s otherwise — partial matches go through `/basliklar/ara?SearchText=`. Debe (`/debe`) groups yesterday's most-liked entries by topic, each headed by an `<h1 id="title">`. Transport uses Chrome TLS impersonation (`curl-cffi`, `chrome120` with rotation); requests are spaced ~0.8s apart; everything is read-only.

## Install

```bash
uvx eksisozluk-mcp==0.1.0   # run directly (needs uv)
# or
pip install eksisozluk-mcp==0.1.0
eksisozluk-mcp    # starts the MCP server on stdio
```

## Tests

```bash
python -m venv .venv && .venv/bin/pip install -e .
.venv/bin/python -m unittest discover -s tests -v
```

Offline tests run on recorded fixtures (real pages fetched 2026-11-12); live tests hit eksisozluk.com. Tests green at build time (see repo for counts) plus an MCP stdio smoke test.

## Roadmap

- Author pages (`/biri/<nick>` — an author's recent entries)
- Entry comments (yorum) under an entry
- "tarihte bugün" (on this day) topics

## License

MIT — see [LICENSE](LICENSE).

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
