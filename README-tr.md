# eksisozluk-mcp 🇹🇷

mcp-name: io.github.mohammad-abbasi-sh/eksisozluk-mcp

eksisozluk.com için resmi olmayan **salt okunur** MCP sunucusu — Ekşi Sözlük, Türkiye'nin ikonik işbirlikçi sözlüğü ve sosyal platformu ("kutsal bilgi kaynağı"); kullanıcılar başlıklar altında kısa entry'ler yazar. Gündem başlıkları, başlık araması, şükela sıralamalı entry'ler, kanallar ve dünün en beğenilen entry'leri (debe).

> Mohammad Abbasi tarafından "Turkey MCP factory" (Sepehr tarzı pipeline) kapsamında geliştirildi. eksisozluk.com veya Ekşi Sözlük ile bağlantılı değildir.

**İçerik notu:** entry'ler filtrelenmemiş kullanıcı üretimidir — argo, küfür ve sert görüşler içerebilir. Sunucu, sitenin yayınladığını olduğu gibi, sansürsüz döndürür.

## Yapay zekâ ajanları için

MCP istemci yapılandırmanıza ekleyin (stdio):

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

Veya yerelde çalıştırın: `python -m eksisozluk_mcp.server` (`mcp<2`, `curl-cffi` gerekir).

## Araçlar

| Araç | Açıklama |
|------|----------|
| `eksisozluk_trending` | Gündem — şu anki trend başlıklar; `page` (sayfa başına 50), `limit` 1..50; başlık, slug, topic_id, entry sayısı, URL |
| `eksisozluk_search_topics` | Başlık araması (kısmi eşleşme olur) — `query` Türkçe metin (örn. "ankar"); `page`, `limit` 1..50 |
| `eksisozluk_get_topic` | Bir başlığın entry'leri — `topic`: "slug--id" (örn. "ankara--32788") veya TAM başlık (sitenin /?q= yönlendirmesiyle çözülür); `sort` ("recent" / "popular" şükela / "dailynice" son 24 saat / "nice" şükela tümü); `page` (sayfa başına 10, page_count döner); `limit` 1..10 |
| `eksisozluk_channel_topics` | Bir kanalın başlıkları — `channel`: "spor", "siyaset", "iliskiler", "yasam", "seyahat", "muzik", "tv", "haber", "bilim", "edebiyat", "kripto" vb.; `page`, `limit` 1..50 |
| `eksisozluk_debe` | Dünün en beğenilen entry'leri (debe), başlığa göre gruplu; `limit` 1..12 grup |
| `eksisozluk_health` | eksisozluk.com erişilebilir mi kontrolü (ok / blocked / error) |

Örnek çıktı (`eksisozluk_get_topic` / ankara, 2026-11-12):

```json
{"topic": "ankara", "topic_id": "32788", "sort": "recent",
 "page": 1, "page_count": 3621,
 "entries": [{"entry_id": "3820", "author": "zomzom",
  "date": "28.03.1999 ~ 20.11.2005 22:40",
  "text": "yapay kent. baskent olmasaydi boktan bi yer olacakti muhakkak.",
  "url": "https://eksisozluk.com/entry/3820"}]}
```

## Nasıl çalışır?

eksisozluk.com sayfalarını tamamen sunucu tarafında oluşturur — giriş yok, API anahtarı yok, oturum çerezi yok. Başlık listeleri `<ul class="topic-list partial">` satırlarıdır (`<a href="/<slug>--<id>">başlık <small>sayı</small></a>`, sayfa başına 50, `?p=2` sayfalama). Başlık sayfaları `<ul id="entry-item-list">` içinde sayfa başına 10 entry listeler (`<li data-id>`, `<div class="content">`, yazar bağlantısı `/biri/<nick>`, tarih bağlantısı `/entry/<id>`); sayfalayıcı `data-pagecount` taşır (ankara: 3.621 sayfa; starbucks: 888). Sıralama: `?a=popular` (şükela), `?a=dailynice` (son 24 saat), `?a=nice` (şükela tümü). Arama kutusunun tam-başlık araması (`/?q=<başlık>`) yalnızca tam eşleşmede başlığa 302 yönlendirir, yoksa 404 döner — kısmi eşleşmeler `/basliklar/ara?SearchText=` üzerinden yapılır. Debe (`/debe`) dünün en beğenilen entry'lerini başlığa göre gruplar; her grup bir `<h1 id="title">` ile başlar. Taşıma katmanı Chrome TLS taklidi kullanır (`curl-cffi`, `chrome120` ve rotasyon); istekler ~0,8 sn arayla yapılır; her şey salt okunurdur.

## Kurulum

```bash
uvx eksisozluk-mcp==0.1.0   # doğrudan çalıştır (uv gerekir)
# veya
pip install eksisozluk-mcp==0.1.0
eksisozluk-mcp    # MCP sunucusunu stdio üzerinde başlatır
```

## Testler

```bash
python -m venv .venv && .venv/bin/pip install -e .
.venv/bin/python -m unittest discover -s tests -v
```

Çevrimdışı testler kayıtlı fixture'larla çalışır (2026-11-12'de çekilen gerçek sayfalar); canlı testler eksisozluk.com'a bağlanır. Derleme anında testler yeşildi (sayılar için repoya bakın); ayrıca bir MCP stdio smoke testi vardır.

## Yol haritası

- Yazar sayfaları (`/biri/<nick>` — yazarın son entry'leri)
- Entry altındaki yorumlar (yorum)
- "tarihte bugün" başlıkları

## Lisans

MIT — bkz. [LICENSE](LICENSE).

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
