"""Live tests for eksisozluk_mcp — real requests to eksisozluk.com.

Requires network (plain HTTP 200; transport uses curl-cffi Chrome
impersonation). The server is polite by design (~0.8s between
requests), so this file takes ~15s. Run:
    python -m unittest discover -s tests -v

Gündem topics rotate, so tests assert structure and sane ranges,
not exact topic lists — except the pinned topic (ankara--32788),
which is a stable long-lived topic; the test only asserts the page
still parses to entries with a large page count.
"""
import unittest

from eksisozluk_mcp import eksisozluk as E
from eksisozluk_mcp import http as H


class TestLiveLists(unittest.TestCase):
    def test_gundem(self):
        topics = E.parse_topic_list(H.fetch_gundem())
        self.assertGreaterEqual(len(topics), 10)
        self.assertTrue(all(t["title"] and t["url"] for t in topics))

    def test_channel_spor(self):
        topics = E.parse_topic_list(H.fetch_channel("spor"))
        self.assertGreaterEqual(len(topics), 10)

    def test_search_ankar(self):
        # The site's own search is relevance-ranked (it stems/fuzzy-matches:
        # "ankar" returns "akıl fikir" topics), so assert structure, not
        # substring matches — the endpoint demonstrably returns 50 topics.
        topics = E.parse_topic_list(H.fetch_search("ankar"))
        self.assertGreaterEqual(len(topics), 1)
        self.assertTrue(all(t["title"] and t["url"] for t in topics))


class TestLiveTopic(unittest.TestCase):
    def test_ankara_by_slug_id(self):
        html = H.fetch_topic("ankara", "32788")
        entries = E.parse_entries(html)
        self.assertEqual(E.parse_topic_title(html), "ankara")
        self.assertEqual(len(entries), 10)
        self.assertGreaterEqual(E.parse_page_count(html)["page_count"], 1000)

    def test_resolve_exact_title(self):
        resolved = H.resolve_topic("ankara")
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved, ("ankara", "32788"))

    def test_resolve_missing_title(self):
        self.assertIsNone(H.resolve_topic("zzzqqqxxyyww"))

    def test_popular_sort(self):
        html = H.fetch_topic("ankara", "32788", sort="popular")
        self.assertEqual(len(E.parse_entries(html)), 10)


class TestLiveDebe(unittest.TestCase):
    def test_debe(self):
        groups = E.parse_debe(H.fetch_debe())
        self.assertGreaterEqual(len(groups), 1)
        self.assertGreaterEqual(
            sum(len(g["entries"]) for g in groups), 1
        )


class TestLiveHealth(unittest.TestCase):
    def test_health_ok(self):
        result = H.health_check()
        self.assertEqual(result["status"], "ok", result)


if __name__ == "__main__":
    unittest.main()
