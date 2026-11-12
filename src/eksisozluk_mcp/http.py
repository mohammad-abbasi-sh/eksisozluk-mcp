"""HTTP layer for eksisozluk_mcp.

eksisozluk.com answers plain HTTP 200 with no login, no API key and no
session cookies (verified live 2026-11-12: home, gündem, kanal, ara,
topic and debe pages all 200 with plain curl). Transport still uses
curl-cffi Chrome impersonation with fingerprint rotation, the proven
pattern of the other Turkey-factory servers, and requests are kept
gentle (one at a time, ~0.8s apart) and read-only. GET only.

VM note: on this VM outbound HTTPS goes through an egress proxy; the
MCP stdio client spawns servers with a minimal environment (no proxy
variables), so client-spawned runs here need the proxy variables
forwarded (see tests/smoke_mcp.py) or requests die mid-TLS (curl 35,
connection reset). On a normal machine with direct internet this does
not apply.

One site behaviour is documented, not worked around: the search box's
exact-title lookup (/?q=<title>) 302-redirects to the topic only for
an EXACT title match and 404s otherwise — partial matches must go
through /basliklar/ara (SearchText), which the server offers as
eksisozluk_search_topics.
"""
from __future__ import annotations

import time
from urllib.parse import quote, urlencode

from curl_cffi import requests as _r

from . import eksisozluk as _E

BASE = "https://eksisozluk.com"
TIMEOUT = 30.0
MIN_INTERVAL = 0.8  # seconds between requests — be polite

_HEADERS = {
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
}

_last_fetch = 0.0


class EksisozlukError(RuntimeError):
    pass


_PROFILES = ("chrome120", "chrome131", "safari17_0")
_MAX_ATTEMPTS = 2  # one retry with the next profile
_RETRY_BACKOFF = 1.0  # seconds between attempts
_profile_idx = 0  # sticky: profile that last succeeded


def _request(url: str, headers: dict, timeout: float = TIMEOUT,
             allow_redirects: bool = True):
    """GET with fingerprint rotation.

    Starts at the sticky profile (chrome120 on a fresh process), retries
    once with the next profile on HTTP 403/429 or a transport error,
    then returns the last response (so the caller raises the specific
    403/429 error) or raises a network error if every attempt failed
    at the transport. Added 2026-11-10 (fleet audit fix).
    """
    global _profile_idx
    last_exc: Exception | None = None
    for k in range(_MAX_ATTEMPTS):
        profile = _PROFILES[(_profile_idx + k) % len(_PROFILES)]
        try:
            resp = _r.get(url, impersonate=profile, headers=headers,
                          timeout=timeout, allow_redirects=allow_redirects)
        except Exception as e:
            last_exc = e
            if k + 1 < _MAX_ATTEMPTS:
                time.sleep(_RETRY_BACKOFF)
                continue
            raise EksisozlukError(f"network error fetching {url}: {e}") from e
        if resp.status_code in (403, 429):
            if k + 1 < _MAX_ATTEMPTS:
                time.sleep(_RETRY_BACKOFF)
                continue
            return resp
        _profile_idx = (_profile_idx + k) % len(_PROFILES)
        return resp
    raise EksisozlukError(f"network error fetching {url}: {last_exc}") from last_exc


def _get(url: str, allow_redirects: bool = True):
    global _last_fetch
    wait = MIN_INTERVAL - (time.monotonic() - _last_fetch)
    if wait > 0:
        time.sleep(wait)
    try:
        resp = _request(url, _HEADERS, allow_redirects=allow_redirects)
    except EksisozlukError:
        raise
    except Exception as e:
        raise EksisozlukError(f"network error fetching {url}: {e}") from e
    finally:
        _last_fetch = time.monotonic()
    if resp.status_code == 403:
        raise EksisozlukError(
            "eksisozluk.com refused the request (HTTP 403, bot wall) — try again later"
        )
    if resp.status_code == 429:
        raise EksisozlukError(
            "eksisozluk.com rate-limited the request (HTTP 429) — try again later"
        )
    if resp.status_code == 404:
        raise EksisozlukError(
            f"eksisozluk.com returned HTTP 404 for {url} "
            "(unknown topic, channel or page)"
        )
    if resp.status_code not in (200, 302):
        raise EksisozlukError(
            f"eksisozluk.com returned HTTP {resp.status_code} for {url}"
        )
    return resp


def _page_url(path: str, page: int) -> str:
    if page and page > 1:
        sep = "&" if "?" in path else "?"
        return f"{BASE}{path}{sep}p={page}"
    return f"{BASE}{path}"


def fetch_gundem(page: int = 1) -> str:
    """Trending-topics (gündem) list page HTML."""
    return _get(_page_url("/basliklar/gundem", page)).text


def fetch_channel(channel: str, page: int = 1) -> str:
    """One channel's topic-list page HTML (/basliklar/kanal/<name>)."""
    return _get(_page_url(f"/basliklar/kanal/{quote(channel)}", page)).text


def fetch_search(query: str, page: int = 1) -> str:
    """Topic search results page HTML (/basliklar/ara?SearchText=<q>)."""
    path = "/basliklar/ara?" + urlencode({"SearchText": query})
    return _get(_page_url(path, page)).text


def fetch_topic(slug: str, topic_id: str, sort: str = "recent",
                page: int = 1) -> str:
    """One topic's entries page HTML (/<slug>--<id>[?a=<sort>][&p=<n>])."""
    params: dict[str, str] = {}
    param = _E.sort_param(sort)
    if param:
        params["a"] = param
    if page and page > 1:
        params["p"] = str(page)
    query = ("?" + urlencode(params)) if params else ""
    return _get(f"{BASE}/{quote(slug)}--{topic_id}{query}").text


def resolve_topic(title: str) -> tuple[str, str] | None:
    """Resolve an exact topic title to (slug, topic_id).

    GET /?q=<title> with redirects disabled: 302 Location
    /<slug>--<id> for an exact match, 404 when no topic has that
    exact title. Returns None on 404.
    """
    url = f"{BASE}/?" + urlencode({"q": title})
    try:
        resp = _get(url, allow_redirects=False)
    except EksisozlukError as e:
        if "404" in str(e):
            return None
        raise
    if resp.status_code != 302:
        return None
    loc = resp.headers.get("Location", "")
    parsed = _E._topic_from_href(loc)
    return parsed


def fetch_debe() -> str:
    """Yesterday's most-liked entries page HTML (/debe)."""
    return _get(f"{BASE}/debe").text


def health_check() -> dict:
    """One polite probe of the source site.

    Returns {"status": "ok"|"blocked"|"error", "http_status": int|None,
    "url": ..., "detail": ...}. Used by the `eksisozluk_health` tool
    and the daily smoke CI. Added 2026-11-10 (fleet audit fix).
    """
    url = f"{BASE}/"
    try:
        _get(url)
    except EksisozlukError as e:
        msg = str(e)
        if "403" in msg:
            return {"status": "blocked", "http_status": 403, "url": url, "detail": msg}
        if "429" in msg:
            return {"status": "blocked", "http_status": 429, "url": url, "detail": msg}
        return {"status": "error", "http_status": None, "url": url, "detail": msg}
    return {"status": "ok", "http_status": 200, "url": url}
