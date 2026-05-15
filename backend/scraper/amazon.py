from __future__ import annotations

import logging
import random
import re
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Callable
from urllib.parse import quote_plus

from django.core.cache import cache

from .base import apply_stealth, create_context
from .utils import clean_price, random_delay

logger = logging.getLogger(__name__)

BASE_URL = "https://www.amazon.fr/s?k="
MAX_PAGES = 3
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2.0  # seconds; doubles on each retry


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class AmazonProduct:
    title: str
    price: float
    currency: str
    url: str
    platform: str = "amazon"
    image_url: str | None = None
    rating: float | None = None
    review_count: int | None = None
    asin: str | None = None
    is_prime: bool = False
    scraped_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Query expansion
# ---------------------------------------------------------------------------

_RELATED_QUERIES: dict[str, list[str]] = {
    "laptop": [
        "pc gamer", "laptop", "ordinateur portable", "macbook", "macbook pro",
        "macbook air", "ordinateur hp", "ordinateur lenovo", "ultrabook",
        "chromebook", "pc portable asus", "ordinateur portable dell",
        "pc portable acer", "pc portable msi", "ordinateur portable etudiant",
        "ordinateur portable professionnel", "pc portable pas cher", "notebook pc",
        "ordinateur portable i7", "ordinateur portable rtx", "surface laptop",
        "microsoft surface", "huawei matebook", "xiaomi redmibook", "thinkpad",
        "lenovo ideapad", "lenovo yoga", "dell xps", "dell latitude", "dell inspiron",
        "hp pavilion", "hp omen", "acer predator", "acer swift", "acer aspire",
        "asus rog", "asus zenbook", "msi stealth", "apple mac",
        "pc portable i5", "pc portable i9", "pc portable ryzen 5",
        "pc portable ryzen 7", "pc portable ryzen 9", "pc portable 16 go ram",
        "pc portable 32 go ram", "pc portable ssd", "pc portable 1 to",
        "pc portable rtx 3060", "pc portable rtx 4070", "pc portable rtx 4090",
        "pc portable gtx 1660", "pc portable 144hz", "pc portable 120hz",
        "pc portable oled", "pc portable 4k", "pc portable full hd",
        "pc portable intel core", "pc portable amd",
    ],
}


def _generate_queries(query: str) -> list[str]:
    """Return expanded query list, or the raw query if no expansion is defined."""
    return _RELATED_QUERIES.get(query.lower().strip(), [query])


# ---------------------------------------------------------------------------
# CAPTCHA / bot-wall detection
# ---------------------------------------------------------------------------

_CAPTCHA_SELECTORS = [
    "#captchacharacters",
    "form[action='/errors/validateCaptcha']",
    "input[name='captcha_characters']",
    "img[src*='captcha']",
]
_CAPTCHA_TEXTS = ("robot check", "enter the characters you see below")


def _is_captcha_page(page) -> bool:
    for selector in _CAPTCHA_SELECTORS:
        try:
            if page.locator(selector).count() > 0:
                return True
        except Exception:
            pass
    try:
        content = page.content().lower()
        if any(t in content for t in _CAPTCHA_TEXTS):
            return True
    except Exception:
        pass
    return False


def _is_empty_results_page(page) -> bool:
    """Detect 'no results' pages to avoid wasting retries."""
    try:
        content = page.content().lower()
        no_result_phrases = (
            "aucun résultat",
            "no results for",
            "did not match any products",
        )
        return any(p in content for p in no_result_phrases)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Human-like behaviour helpers
# ---------------------------------------------------------------------------

def _human_warmup(page) -> None:
    """Random mouse movements + smooth scroll to mimic a real user."""
    try:
        vp = page.viewport_size or {"width": 1280, "height": 720}
        for _ in range(random.randint(3, 6)):
            x = random.randint(100, vp["width"] - 100)
            y = random.randint(100, vp["height"] - 100)
            page.mouse.move(x, y, steps=random.randint(10, 25))
            random_delay(0.05, 0.3)

        # Scroll down then partially back up (mimics reading)
        scroll_amount = random.randint(400, 700)
        page.evaluate(f"window.scrollBy({{top: {scroll_amount}, behavior: 'smooth'}})")
        random_delay(0.6, 1.2)
        page.evaluate(f"window.scrollBy({{top: -{random.randint(100, 300)}, behavior: 'smooth'}})")
        random_delay(0.2, 0.6)
    except Exception:
        pass


def _rotate_viewport(context) -> None:
    """
    Slightly vary the viewport on each context to reduce browser fingerprint
    consistency across requests.
    """
    try:
        width = random.choice([1280, 1366, 1440, 1536, 1920])
        height = random.choice([720, 768, 800, 864, 1080])
        context.set_viewport_size({"width": width, "height": height})
    except Exception:
        pass


# ---------------------------------------------------------------------------
# ASIN extraction
# ---------------------------------------------------------------------------

_ASIN_RE = re.compile(r"/dp/([A-Z0-9]{10})")


def _extract_asin(url: str) -> str | None:
    m = _ASIN_RE.search(url)
    return m.group(1) if m else None


# ---------------------------------------------------------------------------
# Per-item parsing
# ---------------------------------------------------------------------------

def _parse_item(item) -> AmazonProduct | None:
    """
    Extract all relevant fields from a single search-result card.
    Returns None if the item is unusable (no title, no price, no URL).
    """
    try:
        # --- Title ---
        title_el = (
            item.query_selector("h2 a span")
            or item.query_selector("h2 span")
        )
        if not title_el:
            return None
        title_text = title_el.inner_text().strip()
        if not title_text:
            return None

        # --- Price ---
        price_el = item.query_selector(".a-price .a-offscreen")
        if not price_el:
            return None
        price_val = clean_price(price_el.inner_text().strip())
        if price_val is None:
            return None

        # --- URL ---
        link_el = (
            item.query_selector("h2 a")
            or item.query_selector("a.a-link-normal.s-no-outline")
        )
        if not link_el:
            return None
        href = link_el.get_attribute("href") or ""
        if not href:
            return None
        full_url = href if href.startswith("http") else f"https://www.amazon.fr{href}"

        # --- Image ---
        img_el = item.query_selector("img.s-image")
        image_url = img_el.get_attribute("src") if img_el else None

        # --- Rating ---
        rating: float | None = None
        rating_el = (
            item.query_selector("i.a-icon-star-small span.a-icon-alt")
            or item.query_selector("i.a-icon-star span.a-icon-alt")
        )
        if rating_el:
            m = re.search(r"(\d[,.]\d)", rating_el.inner_text())
            if m:
                rating = float(m.group(1).replace(",", "."))

        # --- Review count ---
        review_count: int | None = None
        review_el = item.query_selector("span.a-size-base.s-underline-text")
        if review_el:
            raw = review_el.inner_text().replace("\xa0", "").replace(",", "").replace(".", "").strip()
            if raw.isdigit():
                review_count = int(raw)

        # --- Prime badge ---
        is_prime = item.query_selector("i.a-icon-prime") is not None

        # --- ASIN ---
        asin = _extract_asin(full_url)

        return AmazonProduct(
            title=title_text,
            price=float(price_val),
            currency="EUR",
            url=full_url,
            image_url=image_url,
            rating=rating,
            review_count=review_count,
            is_prime=is_prime,
            asin=asin,
        )

    except Exception:
        logger.exception("Error parsing an individual Amazon item")
        return None


# ---------------------------------------------------------------------------
# Page-level scraping with retry
# ---------------------------------------------------------------------------

def _scrape_page_with_retry(
    page,
    url: str,
    page_index: int,
    max_retries: int = MAX_RETRIES,
) -> list | None:
    """
    Navigate to `url`, detect CAPTCHA / empty pages, and return raw item
    elements. Returns None if the page should be skipped entirely (CAPTCHA
    or unrecoverable error). Returns [] for a legitimate empty page (last
    page of results).
    """
    for attempt in range(1, max_retries + 1):
        try:
            page.goto(url, wait_until="networkidle", timeout=60_000)
            _human_warmup(page)

            if _is_captcha_page(page):
                logger.warning(
                    f"[Page {page_index}] CAPTCHA detected (attempt {attempt}). "
                    "Consider running with SCRAPER_HEADLESS=false or rotating proxies."
                )
                # Back-off and retry — sometimes a simple reload clears it
                if attempt < max_retries:
                    time.sleep(RETRY_BACKOFF_BASE ** attempt + random.uniform(1, 3))
                    page.reload(wait_until="networkidle", timeout=60_000)
                    continue
                return None  # Give up on this page

            if _is_empty_results_page(page):
                logger.info(f"[Page {page_index}] No results — stopping pagination.")
                return []

            random_delay(2, 4)

            try:
                page.wait_for_selector(
                    'div[data-component-type="s-search-result"]',
                    timeout=8_000,
                )
            except Exception:
                pass  # Continue even if the selector times out

            items = page.query_selector_all('div[data-component-type="s-search-result"]')
            if not items:
                logger.warning(f"[Page {page_index}] Selector matched 0 items.")
                if attempt < max_retries:
                    time.sleep(RETRY_BACKOFF_BASE ** attempt)
                    continue
                return []

            return items

        except Exception as e:
            logger.error(f"[Page {page_index}] Navigation error (attempt {attempt}): {e}")
            if attempt < max_retries:
                time.sleep(RETRY_BACKOFF_BASE ** attempt + random.uniform(0.5, 2))
            else:
                return None

    return None


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def scrape_amazon(
    query: str,
    browser,
    progress_callback: Callable[[str, int], None] | None = None,
) -> list[dict[str, Any]]:
    """
    Scrape Amazon.fr for `query` and return a list of product dicts.

    Args:
        query:             Search term. Expanded automatically for known categories.
        browser:           Playwright browser instance.
        progress_callback: Optional callable(source: str, count: int) for live updates.

    Returns:
        List of product dicts (see AmazonProduct.to_dict()).
    """
    context = create_context(browser)
    _rotate_viewport(context)
    page = context.new_page()
    apply_stealth(page)

    results: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    seen_asins: set[str] = set()

    queries = _generate_queries(query)
    logger.info(f"Starting Amazon scrape for '{query}' — {len(queries)} sub-queries, up to {MAX_PAGES} pages each.")

    try:
        for q in queries:
            if cache.get("STOP_SCRAPING"):
                logger.info(f"Scraping cancelled (cache flag) — stopping at query: {q!r}")
                break

            formatted_query = quote_plus(q)

            for p_idx in range(1, MAX_PAGES + 1):
                if cache.get("STOP_SCRAPING"):
                    break

                if progress_callback:
                    progress_callback("amazon", len(results))

                url = f"{BASE_URL}{formatted_query}&page={p_idx}"
                logger.info(f"[{q!r}] Page {p_idx}: {url}")

                items = _scrape_page_with_retry(page, url, p_idx)

                if items is None:
                    # Unrecoverable error or persistent CAPTCHA — skip remaining pages
                    logger.warning(f"[{q!r}] Skipping remaining pages after failure on page {p_idx}.")
                    break

                if not items:
                    # Legitimate end of results
                    break

                page_hits = 0
                for item in items:
                    product = _parse_item(item)
                    if product is None:
                        continue

                    # Deduplicate by ASIN first, then URL
                    if product.asin and product.asin in seen_asins:
                        continue
                    if product.url in seen_urls:
                        continue

                    if product.asin:
                        seen_asins.add(product.asin)
                    seen_urls.add(product.url)

                    results.append(product.to_dict())
                    page_hits += 1

                logger.info(f"[{q!r}] Page {p_idx}: +{page_hits} products (total {len(results)})")

                # Polite inter-page delay
                random_delay(1.5, 3.5)

        logger.info(f"Amazon scrape complete — {len(results)} unique products collected.")
        return results

    finally:
        page.close()
        context.close()