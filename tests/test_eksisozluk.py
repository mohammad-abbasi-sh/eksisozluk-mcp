"""Offline tests for eksisozluk_mcp — recorded Ekşi Sözlük fixtures, no network.

Fixtures recorded 2026-11-12 from eksisozluk.com (plain HTTP 200):
- gundem.html: trending topics (/basliklar/gundem) — 50 topics
- kanal.html: channel topics (/basliklar/kanal/spor) — 50 topics
- ara.html: topic search (/basliklar/ara?SearchText=ankar) — 50 topics
- topic.html: topic page (ankara--32788) — 10 entries, 3621 pages
- bigtopic.html: topic page (starbucks--85715) — 888 pages
- debe.html: yesterday's most-liked entries (/debe) — 12 groups, 12 entries

Run: python -m unittest discover -s tests -v
"""
import os
import unittest

from eksisozluk_mcp import eksisozluk as E

FIX = os.path.join(os.path.dirname(__file__), "fixtures")


def _read(name: str) -> str:
    with open(os.path.join(FIX, name), encoding="utf-8") as f:
        return f.read()


class TestTopicList(unittest.TestCase):
    def test_gundem_fifty_topics(self):
        topics = E.parse_topic_list(_read("gundem.html"))
        self.assertEqual(len(topics), 50)

    def test_gundem_first_topic(self):
        t = E.parse_topic_list(_read("gundem.html"))[0]
        self.assertEqual(t["title"], "oktay kaynarca'nın türkiyeliyim açıklaması")
        self.assertEqual(t["slug"], "oktay-kaynarcanin-turkiyeliyim-aciklamasi")
        self.assertEqual(t["topic_id"], "7838517")
        self.assertEqual(t["entry_count"], 259)
        self.assertEqual(
            t["url"],
            "https://eksisozluk.com/oktay-kaynarcanin-turkiyeliyim-aciklamasi--7838517",
        )

    def test_gundem_all_have_counts_and_urls(self):
        for t in E.parse_topic_list(_read("gundem.html")):
            self.assertIsInstance(t["entry_count"], int)
            self.assertGreater(t["entry_count"], 0)
            self.assertTrue(t["url"].startswith("https://eksisozluk.com/"))
            self.assertIn("--", t["url"])

    def test_kanal_spor(self):
        topics = E.parse_topic_list(_read("kanal.html"))
        self.assertEqual(len(topics), 50)
        self.assertEqual(
            topics[0]["title"], "12 kasım 2026 şampiyonlar ligi yayın ihalesi"
        )
        self.assertEqual(topics[0]["topic_id"], "8154962")
        self.assertEqual(topics[0]["entry_count"], 17)

    def test_ara_search(self):
        topics = E.parse_topic_list(_read("ara.html"))
        self.assertEqual(len(topics), 50)
        self.assertEqual(topics[0]["title"], "allah akıl fikir versin")
        self.assertEqual(topics[0]["topic_id"], "55951")
        self.assertEqual(topics[0]["entry_count"], 60)


class TestEntries(unittest.TestCase):
    def setUp(self):
        self.html = _read("topic.html")
        self.entries = E.parse_entries(self.html)

    def test_ten_entries(self):
        self.assertEqual(len(self.entries), 10)

    def test_first_entry(self):
        e = self.entries[0]
        self.assertEqual(e["entry_id"], "3820")
        self.assertEqual(e["author"], "zomzom")
        self.assertEqual(e["author_url"], "https://eksisozluk.com/biri/zomzom")
        self.assertEqual(e["date"], "28.03.1999 ~ 20.11.2005 22:40")
        self.assertEqual(e["url"], "https://eksisozluk.com/entry/3820")
        self.assertTrue(e["text"].startswith("yapay kent."))

    def test_entry_text_keeps_paragraph_breaks(self):
        self.assertIn("\n", self.entries[0]["text"])

    def test_all_entries_have_text_and_author(self):
        for e in self.entries:
            self.assertTrue(e["text"])
            self.assertIsNotNone(e["author"])
            self.assertTrue(e["url"].startswith("https://eksisozluk.com/entry/"))

    def test_topic_title(self):
        self.assertEqual(E.parse_topic_title(self.html), "ankara")

    def test_page_count_ankara(self):
        pages = E.parse_page_count(self.html)
        self.assertEqual(pages["page"], 1)
        self.assertEqual(pages["page_count"], 3621)

    def test_page_count_starbucks(self):
        pages = E.parse_page_count(_read("bigtopic.html"))
        self.assertEqual(pages["page_count"], 888)

    def test_no_pager(self):
        pages = E.parse_page_count("<html><body>no pager here</body></html>")
        self.assertIsNone(pages["page"])
        self.assertIsNone(pages["page_count"])


class TestDebe(unittest.TestCase):
    def setUp(self):
        self.groups = E.parse_debe(_read("debe.html"))

    def test_twelve_groups(self):
        self.assertEqual(len(self.groups), 12)

    def test_first_group(self):
        g = self.groups[0]
        self.assertEqual(
            g["topic_title"],
            "galatasaraylı oyuncuların bedelli sırasındaki pozu",
        )
        self.assertEqual(g["topic_id"], "4635336")
        self.assertEqual(g["topic_slug"],
                         "galatasarayli-oyuncularin-bedelli-sirasindaki-pozu")
        self.assertEqual(len(g["entries"]), 1)

    def test_first_entry(self):
        e = self.groups[0]["entries"][0]
        self.assertEqual(e["entry_id"], "47761575")
        self.assertEqual(e["author"], "bulunan balik nemo")

    def test_total_entries(self):
        total = sum(len(g["entries"]) for g in self.groups)
        self.assertEqual(total, 12)


class TestSorts(unittest.TestCase):
    def test_sort_params(self):
        self.assertIsNone(E.sort_param("recent"))
        self.assertEqual(E.sort_param("popular"), "popular")
        self.assertEqual(E.sort_param("dailynice"), "dailynice")
        self.assertEqual(E.sort_param("nice"), "nice")

    def test_channels_known(self):
        for ch in ("spor", "siyaset", "iliskiler", "yasam", "muzik", "haber"):
            self.assertIn(ch, E.CHANNELS)


if __name__ == "__main__":
    unittest.main()
