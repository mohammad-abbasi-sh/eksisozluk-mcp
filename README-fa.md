# eksisozluk-mcp 🇹🇷

mcp-name: io.github.mohammad-abbasi-sh/eksisozluk-mcp

سرور MCP غیررسمی و **فقط‌خواندنی** برای eksisozluk.com — «اکشی سوزلوک»، فرهنگ لغت مشارکتی و پلتفرم اجتماعی نمادین ترکیه («منبع مقدس دانش») که کاربران زیر هر عنوان، ورودی‌های کوتاه (entry) می‌نویسند. عنوان‌های داغ (گوندم)، جست‌وجوی عنوان، ورودی‌ها با مرتب‌سازی شوکلا، کانال‌ها و محبوب‌ترین ورودی‌های دیروز (دِبه).

> ساختهٔ محمد عباسی در چارچوب «کارخانهٔ MCP ترکیه» (خط لوله به سبک سپهر). وابسته به eksisozluk.com یا اکشی سوزلوک نیست.

**نکتهٔ محتوا:** ورودی‌ها متن تولیدشده توسط کاربران و بدون فیلتر هستند — ممکن است شامل الفاظ رکیک، عامیانه و نظرات تند باشند. سرور همان چیزی را که سایت منتشر می‌کند، بدون سانسور برمی‌گرداند.

## برای ایجنت‌های هوش مصنوعی

به پیکربندی کلاینت MCP خود اضافه کنید (stdio):

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

یا به‌صورت محلی اجرا کنید: `python -m eksisozluk_mcp.server` (نیازمند `mcp<2` و `curl-cffi`).

## ابزارها

| ابزار | توضیح |
|------|-------|
| `eksisozluk_trending` | گوندم — عنوان‌های داغ همین حالا؛ `page` (۵۰ عنوان در هر صفحه)، `limit` ۱ تا ۵۰؛ عنوان، slug، شناسهٔ موضوع، تعداد ورودی، URL |
| `eksisozluk_search_topics` | جست‌وجوی عنوان‌ها (تطابق جزئی هم قبول است) — `query` متن ترکی (مثلاً «ankar»)؛ `page` و `limit` ۱ تا ۵۰ |
| `eksisozluk_get_topic` | ورودی‌های یک موضوع — `topic`: به‌صورت «slug--id» (مثلاً «ankara--32788») یا عنوان دقیق (از طریق ریدایرکت `/?q=` سایت پیدا می‌شود)؛ `sort` ‏(«recent» / ‏«popular» شوکلا / ‏«dailynice» ۲۴ ساعت اخیر / ‏«nice» شوکلا همهٔ زمان‌ها)؛ `page` (۱۰ ورودی در هر صفحه، page_count برگردانده می‌شود)؛ `limit` ۱ تا ۱۰ |
| `eksisozluk_channel_topics` | عنوان‌های یک کانال — `channel`: ‏«spor»، ‏«siyaset»، ‏«iliskiler»، ‏«yasam»، ‏«seyahat»، ‏«muzik»، ‏«tv»، ‏«haber»، ‏«bilim»، ‏«edebiyat»، ‏«kripto» و غیره؛ `page` و `limit` ۱ تا ۵۰ |
| `eksisozluk_debe` | محبوب‌ترین ورودی‌های دیروز (دبه)، گروه‌بندی‌شده بر اساس موضوع؛ `limit` ۱ تا ۱۲ گروه |
| `eksisozluk_health` | بررسی در دسترس بودن eksisozluk.com (ok / blocked / error) |

خروجی نمونه (`eksisozluk_get_topic` / آنکارا، ۲۰۲۶-۱۱-۱۲):

```json
{"topic": "ankara", "topic_id": "32788", "sort": "recent",
 "page": 1, "page_count": 3621,
 "entries": [{"entry_id": "3820", "author": "zomzom",
  "date": "28.03.1999 ~ 20.11.2005 22:40",
  "text": "yapay kent. baskent olmasaydi boktan bi yer olacakti muhakkak.",
  "url": "https://eksisozluk.com/entry/3820"}]}
```

## نحوهٔ کار

eksisozluk.com صفحات را کاملاً در سمت سرور می‌سازد — بدون ورود، بدون کلید API و بدون کوکی نشست. فهرست عنوان‌ها سطرهای `<ul class="topic-list partial">` هستند (`<a href="/<slug>--<id>">عنوان <small>تعداد</small></a>`، ۵۰ عدد در هر صفحه، صفحه‌بندی با `?p=2`). صفحات موضوع در `<ul id="entry-item-list">` در هر صفحه ۱۰ ورودی فهرست می‌کنند (`<li data-id>` با `<div class="content">`، پیوند نویسنده `/biri/<nick>`، پیوند تاریخ `/entry/<id>`)؛ صفحه‌بندی `data-pagecount` دارد (آنکارا: ۳٬۶۲۱ صفحه؛ استارباکس: ۸۸۸). حالت‌های مرتب‌سازی: `?a=popular` (شوکلا)، `?a=dailynice` (۲۴ ساعت اخیر)، `?a=nice` (شوکلا همهٔ زمان‌ها). جست‌وجوی عنوان دقیق (`/?q=<عنوان>`) فقط در صورت تطابق دقیق به موضوع ریدایرکت ۳۰۲ می‌دهد و در غیر این صورت ۴۰۴ برمی‌گرداند — تطابق‌های جزئی از طریق `/basliklar/ara?SearchText=` انجام می‌شوند. دبه (`/debe`) محبوب‌ترین ورودی‌های دیروز را بر اساس موضوع گروه‌بندی می‌کند؛ هر گروه با یک `<h1 id="title">` شروع می‌شود. لایهٔ انتقال از جعل TLS کروم استفاده می‌کند (`curl-cffi`، ‏`chrome120` با چرخش)؛ درخواست‌ها با فاصلهٔ حدود ۰٫۸ ثانیه انجام می‌شوند؛ همه‌چیز فقط‌خواندنی است.

## نصب

```bash
uvx eksisozluk-mcp==0.1.0   # اجرای مستقیم (نیازمند uv)
# یا
pip install eksisozluk-mcp==0.1.0
eksisozluk-mcp    # راه‌اندازی سرور MCP روی stdio
```

## تست‌ها

```bash
python -m venv .venv && .venv/bin/pip install -e .
.venv/bin/python -m unittest discover -s tests -v
```

تست‌های آفلاین روی فیکسچرهای ضبط‌شده اجرا می‌شوند (صفحات واقعی گرفته‌شده در ۲۰۲۶-۱۱-۱۲)؛ تست‌های زنده به eksisozluk.com وصل می‌شوند. در زمان ساخت، تست‌ها سبز بودند (برای تعداد به ریپو نگاه کنید)؛ به‌علاوه یک تست smoke از نوع MCP stdio وجود دارد.

## نقشهٔ راه

- صفحات نویسنده (`/biri/<nick>` — ورودی‌های اخیر یک نویسنده)
- نظرات (yorum) زیر هر ورودی
- عنوان‌های «tarihte bugün» (در چنین روزی)

## مجوز

MIT — نگاه کنید به [LICENSE](LICENSE).

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
