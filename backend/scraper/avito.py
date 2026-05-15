from __future__ import annotations

import json
import logging
import random
import re
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Callable
from urllib.parse import parse_qs, quote_plus, urljoin, urlparse

from parsel import Selector

from .base import apply_stealth, create_context
from .utils import clean_price, random_delay

logger = logging.getLogger(__name__)

BASE_URL = "https://www.avito.ma"
MAX_PAGES = 3
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2.0  # seconds; doubles each retry


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class AvitoProduct:
    title: str
    price: float
    currency: str
    url: str
    platform: str = "avito"
    image_url: str | None = None
    rating: float | None = None
    seller_name: str | None = None
    seller_type: str | None = None       # "pro" | "private" | None
    category: str | None = None
    location: str | None = None          # city / region from the listing
    listing_id: str | None = None        # Avito's internal numeric ID
    publication_date: str | None = None  # ISO date string when available
    scraped_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------

_LISTING_ID_RE = re.compile(r"_(\d+)\.htm$")


def _build_search_url(query: str, page: int = 1) -> str:
    """
    Build an Avito SEO-friendly search URL.

    Avito (Next.js) uses path-based slugs instead of ?q= query params:
      https://www.avito.ma/fr/maroc/{slug}--%C3%A0_vendre?o={page}
    """
    slug = query.strip().lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[-\s]+", "-", slug)
    encoded = quote_plus(slug).replace("+", "-")
    url = f"{BASE_URL}/fr/maroc/{encoded}--%C3%A0_vendre"
    if page > 1:
        url += f"?o={page}"
    return url


def _paginate_url(base_url: str, page_num: int) -> str:
    """Inject / replace the `o` pagination param in a URL."""
    if "o=" in base_url:
        return re.sub(r"o=\d+", f"o={page_num}", base_url)
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}o={page_num}"


def _extract_listing_id(url: str) -> str | None:
    m = _LISTING_ID_RE.search(url)
    return m.group(1) if m else None


def _normalise_url(raw: str) -> str:
    return raw if raw.startswith("http") else urljoin(BASE_URL, raw)


# ---------------------------------------------------------------------------
# Bot / CAPTCHA detection
# ---------------------------------------------------------------------------

_BLOCK_SELECTORS = [
    "#captcha",
    "[class*='captcha']",
    "[id*='captcha']",
    ".robot-check",
    "[class*='blocked']",
]
_BLOCK_KEYWORDS = ("robot", "captcha", "access denied", "accès refusé", "تحقق")


def _is_blocked_page(page) -> bool:
    for selector in _BLOCK_SELECTORS:
        try:
            if page.locator(selector).count() > 0:
                return True
        except Exception:
            pass
    try:
        snippet = page.content()[:5000].lower()
        return any(kw in snippet for kw in _BLOCK_KEYWORDS)
    except Exception:
        return False


def _is_empty_results_page(html: str) -> bool:
    low = html[:8000].lower()
    empty_signals = (
        "aucune annonce",
        "aucun résultat",
        "no results",
        "0 annonce",
    )
    return any(s in low for s in empty_signals)


# ---------------------------------------------------------------------------
# Human-like behaviour
# ---------------------------------------------------------------------------

def _human_warmup(page) -> None:
    """Random mouse movements + two-phase smooth scroll."""
    try:
        vp = page.viewport_size or {"width": 1280, "height": 720}
        for _ in range(random.randint(3, 6)):
            x = random.randint(100, vp["width"] - 100)
            y = random.randint(100, vp["height"] - 100)
            page.mouse.move(x, y, steps=random.randint(8, 20))
            random_delay(0.05, 0.25)
        scroll_down = random.randint(400, 750)
        page.evaluate(f"window.scrollBy({{top: {scroll_down}, behavior: 'smooth'}})")
        random_delay(0.6, 1.2)
        page.evaluate(f"window.scrollBy({{top: -{random.randint(100, 300)}, behavior: 'smooth'}})")
        random_delay(0.2, 0.6)
    except Exception:
        pass


def _rotate_viewport(context) -> None:
    try:
        w = random.choice([1280, 1366, 1440, 1536, 1920])
        h = random.choice([720, 768, 800, 864, 1080])
        context.set_viewport_size({"width": w, "height": h})
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Extraction — Strategy 1: __NEXT_DATA__
# ---------------------------------------------------------------------------

def _extract_from_next_data(
    next_data_text: str,
    seen_urls: set[str],
    seen_ids: set[str],
) -> list[AvitoProduct]:
    results: list[AvitoProduct] = []
    try:
        parsed = json.loads(next_data_text)
    except json.JSONDecodeError:
        return results

    page_props = parsed.get("props", {}).get("pageProps", {})

    # Traverse common Next.js data shapes to find the listings array
    raw_ads: list | None = None
    search_paths = [
        ["componentProps", "ads", "ads"],
        ["componentProps", "ads", "results"],
        ["componentProps", "ads", "items"],
        ["ads", "ads"],
        ["ads", "results"],
        ["ads", "items"],
        ["listings"],
        ["results"],
    ]
    for path in search_paths:
        node = page_props
        for key in path:
            node = node.get(key) if isinstance(node, dict) else None
            if node is None:
                break
        if isinstance(node, list) and node:
            raw_ads = node
            break

    if not raw_ads:
        return results

    for item in raw_ads:
        if not isinstance(item, dict):
            continue

        # Skip non-product / injected ad entries
        list_id = str(item.get("listId") or item.get("id") or "")
        if not list_id:
            continue
        if list_id in seen_ids:
            continue

        title = (item.get("subject") or item.get("title") or "").strip()
        if not title:
            continue

        # Price
        price: float | None = None
        price_raw = item.get("price")
        if isinstance(price_raw, dict):
            price = price_raw.get("value") or price_raw.get("amount")
        elif isinstance(price_raw, (int, float)):
            price = float(price_raw)
        elif isinstance(price_raw, str):
            price = clean_price(price_raw)
        if price is None or price <= 0:
            continue

        # URL
        url_raw = item.get("url") or ""
        if not url_raw:
            slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
            url_raw = f"/fr/maroc/{slug}_{list_id}.htm"
        url = _normalise_url(url_raw)
        if url in seen_urls:
            continue

        # Image — prefer highest-resolution variant
        image_url: str | None = None
        images = item.get("images") or item.get("medias") or []
        if isinstance(images, list) and images:
            first = images[0]
            if isinstance(first, dict):
                image_url = (
                    first.get("url")
                    or first.get("src")
                    or first.get("thumb")
                )
            elif isinstance(first, str):
                image_url = first
        elif isinstance(images, dict):
            image_url = images.get("url") or images.get("src")

        # Seller
        seller_name: str | None = None
        seller_type: str | None = None
        seller = item.get("seller") or item.get("owner") or {}
        if isinstance(seller, dict):
            seller_name = seller.get("name") or seller.get("displayName")
            store = seller.get("store") or {}
            if isinstance(store, dict) and store:
                seller_type = "pro"
            else:
                seller_type = seller.get("type")  # some schemas expose this

        # Category
        category_text: str | None = None
        cat = item.get("category") or {}
        if isinstance(cat, dict):
            cat_name = cat.get("name", "")
            parent = cat.get("parent") or {}
            parent_name = parent.get("name", "") if isinstance(parent, dict) else ""
            category_text = f"{parent_name} - {cat_name}" if parent_name else cat_name or None

        # Location
        location: str | None = None
        loc = item.get("location") or item.get("city") or {}
        if isinstance(loc, dict):
            location = loc.get("name") or loc.get("label")
        elif isinstance(loc, str):
            location = loc

        # Publication date
        pub_date: str | None = None
        raw_date = item.get("firstPublicationDate") or item.get("publicationDate")
        if raw_date:
            pub_date = str(raw_date)

        seen_ids.add(list_id)
        seen_urls.add(url)
        results.append(AvitoProduct(
            title=title,
            price=float(price),
            currency="MAD",
            url=url,
            image_url=image_url,
            seller_name=seller_name,
            seller_type=seller_type,
            category=category_text,
            location=location,
            listing_id=list_id,
            publication_date=pub_date,
        ))

    return results


# ---------------------------------------------------------------------------
# Extraction — Strategy 2: JSON-LD
# ---------------------------------------------------------------------------

def _extract_from_json_ld(
    selector: Selector,
    seen_urls: set[str],
    query_words: list[str],
) -> list[AvitoProduct]:
    results: list[AvitoProduct] = []
    for script_text in selector.css('script[type="application/ld+json"]::text').getall():
        try:
            data = json.loads(script_text)
            if not isinstance(data, dict):
                continue

            offers = data.get("offers")
            if not isinstance(offers, dict):
                continue

            title = (data.get("name") or "").strip()
            if not title:
                continue

            price_raw = offers.get("price")
            if price_raw is None:
                continue
            price = float(price_raw)
            if price <= 0:
                continue

            url = offers.get("url") or ""
            if not url or url in seen_urls:
                continue

            # Relevance filter — skip listings that share no words with query
            if query_words and not any(w in title.lower() for w in query_words):
                continue

            raw_currency = offers.get("priceCurrency") or "MAD"
            currency = "MAD" if raw_currency in ("DH", "MAD") else raw_currency

            images = data.get("image")
            image_url = images[0] if isinstance(images, list) and images else (
                images if isinstance(images, str) else None
            )

            listing_id = _extract_listing_id(url)
            seen_urls.add(url)
            results.append(AvitoProduct(
                title=title,
                price=price,
                currency=currency,
                url=url,
                image_url=image_url,
                listing_id=listing_id,
            ))
        except Exception:
            continue
    return results


# ---------------------------------------------------------------------------
# Extraction — Strategy 3: CSS card parsing
# ---------------------------------------------------------------------------

_PRODUCT_URL_RE = re.compile(r"_\d+\.htm$")

# Known Avito obfuscated class fragments (update as needed)
_PRICE_CLASS_HINTS = ("PuYkS", "sc-3286ebc5-2", "price")
_TITLE_CLASS_HINTS = ("iHApav", "sc-1x0vz2r-0")
_IMG_CLASS_HINTS = ("jXTiJI", "sc-1lb3x1r-3")


def _css_hint(*fragments: str) -> str:
    """Build a CSS selector that matches any of the given class fragments."""
    return ", ".join(f'[class*="{f}"]' for f in fragments)


def _extract_from_css(
    selector: Selector,
    seen_urls: set[str],
) -> list[AvitoProduct]:
    results: list[AvitoProduct] = []

    for card in selector.css('a[href$=".htm"]'):
        url_raw = card.attrib.get("href", "")
        if not url_raw or not _PRODUCT_URL_RE.search(url_raw):
            continue
        url = _normalise_url(url_raw)
        if url in seen_urls:
            continue

        # Title — prefer explicit title attribute, fall back to class hints
        title = card.css("p[title]::attr(title)").get()
        if not title:
            for hint in _TITLE_CLASS_HINTS:
                title = card.css(f'[class*="{hint}"]::text').get()
                if title:
                    break
        if not title:
            title = card.css("h3::text, h2::text").get()
        if not title:
            # Derive a readable title from the URL slug
            slug = url_raw.split("/")[-1].replace(".htm", "")
            title = re.sub(r"_\d+$", "", slug).replace("_", " ")
        title = (title or "").strip()
        if len(title) < 3:
            continue

        # Price
        price_text: str | None = None
        for hint in _PRICE_CLASS_HINTS:
            price_text = card.css(f'[class*="{hint}"]::text').get()
            if price_text:
                break
        if not price_text:
            # XPath fallback: look for a node near "DH"
            price_text = card.xpath(
                './/*[contains(text(),"DH")]/preceding-sibling::*[1]/text() | '
                './/*[contains(text(),"DH")]/parent::*/text()'
            ).get()
        price = clean_price(price_text)
        if price is None or price <= 0:
            continue

        # Image — skip avatar / data-URI placeholders
        image_url: str | None = None
        for img in card.css("img"):
            src = img.attrib.get("src") or img.attrib.get("data-src") or ""
            if src and "avatar" not in src and not src.startswith("data:"):
                image_url = src
                break

        listing_id = _extract_listing_id(url)

        seen_urls.add(url)
        results.append(AvitoProduct(
            title=title,
            price=price,
            currency="MAD",
            url=url,
            image_url=image_url,
            listing_id=listing_id,
        ))

    return results


# ---------------------------------------------------------------------------
# Orchestrated extraction (strategy cascade)
# ---------------------------------------------------------------------------

def extract_avito_results(
    html: str,
    query: str | None = None,
    seen_urls: set[str] | None = None,
    seen_ids: set[str] | None = None,
) -> list[AvitoProduct]:
    """
    Extract listings from a rendered Avito search-results page.

    Strategy cascade (highest fidelity → lowest):
      1. __NEXT_DATA__ SSR JSON  — richest, most fields
      2. JSON-LD structured data — reliable but one listing per script block
      3. CSS card parsing        — last resort; fragile against class obfuscation

    Args:
        html:      Full page HTML string.
        query:     Original search query (used for relevance filtering in JSON-LD).
        seen_urls: Shared dedup set (mutated in-place).
        seen_ids:  Shared dedup set for Avito listing IDs (mutated in-place).
    """
    if seen_urls is None:
        seen_urls = set()
    if seen_ids is None:
        seen_ids = set()

    selector = Selector(text=html)
    query_words = query.lower().split() if query else []

    # Strategy 1 — __NEXT_DATA__
    next_data = selector.css("script#__NEXT_DATA__::text").get()
    if next_data:
        products = _extract_from_next_data(next_data, seen_urls, seen_ids)
        if products:
            logger.info(f"Avito __NEXT_DATA__: {len(products)} listings")
            return products

    # Strategy 2 — JSON-LD
    products = _extract_from_json_ld(selector, seen_urls, query_words)
    if products:
        logger.info(f"Avito JSON-LD: {len(products)} listings")
        return products

    # Strategy 3 — CSS cards
    products = _extract_from_css(selector, seen_urls)
    logger.info(f"Avito CSS fallback: {len(products)} listings")
    return products


# ---------------------------------------------------------------------------
# Page-level navigation with retry + backoff
# ---------------------------------------------------------------------------

def _navigate_with_retry(
    page,
    url: str,
    page_num: int,
    max_retries: int = MAX_RETRIES,
) -> str | None:
    """
    Navigate to `url`, apply human warmup, and return the page HTML.

    Returns:
        HTML string on success.
        None if the page is blocked or all retries are exhausted.
    """
    for attempt in range(1, max_retries + 1):
        try:
            page.goto(url, wait_until="networkidle", timeout=50_000)
            _human_warmup(page)

            if _is_blocked_page(page):
                logger.warning(
                    f"[Page {page_num}] Bot-block detected (attempt {attempt}). "
                    "Consider SCRAPER_HEADLESS=false or a residential proxy."
                )
                if attempt < max_retries:
                    wait = RETRY_BACKOFF_BASE ** attempt + random.uniform(1, 3)
                    logger.info(f"[Page {page_num}] Waiting {wait:.1f}s before retry…")
                    time.sleep(wait)
                    page.reload(wait_until="networkidle", timeout=50_000)
                    continue
                return None

            # Extra settle time for Next.js hydration
            random_delay(2, 4)

            html = page.content()

            if _is_empty_results_page(html):
                logger.info(f"[Page {page_num}] Empty results page — stopping pagination.")
                return ""  # Caller interprets "" as "stop, don't retry"

            return html

        except Exception as e:
            logger.error(f"[Page {page_num}] Navigation error (attempt {attempt}): {e}")
            if attempt < max_retries:
                time.sleep(RETRY_BACKOFF_BASE ** attempt + random.uniform(0.5, 2))
            else:
                return None

    return None


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def scrape_avito(
    query_or_url: str,
    browser,
    progress_callback: Callable[[str, int], None] | None = None,
) -> list[dict[str, Any]]:
    """
    Scrape Avito.ma for `query_or_url` and return a list of product dicts.

    Args:
        query_or_url:      Either a plain search term or a full Avito search URL.
        browser:           Playwright browser instance.
        progress_callback: Optional callable(source: str, count: int).

    Returns:
        List of product dicts (see AvitoProduct.to_dict()).
    """
    context = create_context(browser)
    _rotate_viewport(context)
    page = context.new_page()
    apply_stealth(page)

    results: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    seen_ids: set[str] = set()

    # Resolve starting URL and query string
    if query_or_url.startswith("http"):
        parsed = urlparse(query_or_url)
        qs = parse_qs(parsed.query)
        start_page = int(qs.get("o", ["1"])[0])
        query = qs.get("q", [None])[0]
        base_search_url = query_or_url
    else:
        query = query_or_url
        start_page = 1
        base_search_url = _build_search_url(query, page=1)

    logger.info(
        f"Starting Avito scrape for {query!r} — "
        f"up to {MAX_PAGES} pages from page {start_page}."
    )

    try:
        for page_num in range(start_page, start_page + MAX_PAGES):
            if progress_callback:
                progress_callback("avito", len(results))

            url = _paginate_url(base_search_url, page_num) if page_num > 1 else base_search_url
            logger.info(f"[Page {page_num}] {url}")

            html = _navigate_with_retry(page, url, page_num)

            if html is None:
                # Unrecoverable (persistent block or network failure)
                logger.warning(f"[Page {page_num}] Giving up — stopping scrape.")
                break

            if html == "":
                # Clean end of results
                break

            page_products = extract_avito_results(
                html,
                query=query,
                seen_urls=seen_urls,
                seen_ids=seen_ids,
            )

            # First-page retry with longer wait if extraction yielded nothing
            if not page_products and page_num == start_page:
                logger.info("[Page 1] No results on first attempt — waiting and retrying extraction.")
                page.wait_for_timeout(4000)
                page_products = extract_avito_results(
                    page.content(),
                    query=query,
                    seen_urls=seen_urls,
                    seen_ids=seen_ids,
                )

            if not page_products:
                logger.warning(f"[Page {page_num}] No products extracted — stopping.")
                break

            page_hits = 0
            for product in page_products:
                # seen_urls / seen_ids already updated inside extract_avito_results
                results.append(product.to_dict())
                page_hits += 1

            logger.info(
                f"[Page {page_num}] +{page_hits} products "
                f"(running total: {len(results)})"
            )

            # Polite inter-page pause
            random_delay(1.5, 3.5)

        logger.info(f"Avito scrape complete — {len(results)} unique listings collected.")
        return results

    finally:
        page.close()
        context.close()