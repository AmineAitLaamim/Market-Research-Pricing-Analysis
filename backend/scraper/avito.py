from __future__ import annotations

import json
import logging
import re
from typing import Any
from urllib.parse import parse_qs, quote_plus, urljoin, urlparse

from parsel import Selector

from .base import create_context, parse_price_string

logger = logging.getLogger(__name__)

BASE_URL = "https://www.avito.ma"
MAX_PAGES = 3


def _build_search_url(query: str, page: int = 1) -> str:
    """
    Build an Avito search URL.

    Avito (Next.js) uses SEO-friendly URL paths instead of search query params:
      https://www.avito.ma/fr/maroc/{keyword}--{ad_type}?o={page}

    The query-param format (recherche/?q=...) often fails with Playwright
    because Avito redirects or serves an empty Shell without the SSR state.
    """
    # Build a URL-safe slug from the query
    slug = query.strip().lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[-\s]+", "-", slug)
    # URL-encode with quote_plus then swap + for - to match Avito's format
    encoded_slug = quote_plus(slug).replace("+", "-")

    url = f"{BASE_URL}/fr/maroc/{encoded_slug}--%C3%A0_vendre"
    if page > 1:
        if "?" in url:
            url += f"&o={page}"
        else:
            url += f"?o={page}"
    return url


def _extract_ads_from_next_data(next_data: str, seen_urls: set[str]) -> list[dict[str, Any]]:
    """
    Extract ad listings from the Next.js __NEXT_DATA__ embedded JSON.
    This is the most reliable source since Avito is built on Next.js.
    """
    results: list[dict[str, Any]] = []

    try:
        parsed = json.loads(next_data)
    except json.JSONDecodeError:
        return results

    # Strategy A: Look in pageProps -> componentProps -> ads
    page_props = parsed.get("props", {}).get("pageProps", {})
    component_props = page_props.get("componentProps", {})
    ads_section = component_props.get("ads", {})

    raw_ads = None
    if isinstance(ads_section, dict):
        # Try common keys where ad listings are stored
        for key in ("ads", "results", "items", "listings"):
            candidate = ads_section.get(key)
            if isinstance(candidate, list):
                raw_ads = candidate
                break

    if not raw_ads:
        # Strategy B: Look directly in ads key at pageProps level
        ads_direct = page_props.get("ads", {})
        if isinstance(ads_direct, dict):
            for key in ("ads", "results", "items", "listings"):
                candidate = ads_direct.get(key)
                if isinstance(candidate, list):
                    raw_ads = candidate
                    break

    if not isinstance(raw_ads, list):
        return results

    for item in raw_ads:
        if not isinstance(item, dict):
            continue

        # Skip non-product entries (e.g. inline ads)
        list_id = item.get("listId") or item.get("id")
        if not list_id:
            continue

        title = item.get("subject") or item.get("title", "")
        if not title:
            continue

        # Extract price
        price = None
        price_raw = item.get("price")
        if isinstance(price_raw, dict):
            price = price_raw.get("value") or price_raw.get("amount")
        elif isinstance(price_raw, (int, float)):
            price = price_raw
        elif isinstance(price_raw, str):
            try:
                price = float(price_raw.replace(",", "").replace(" ", ""))
            except (ValueError, TypeError):
                pass

        if price is None or price <= 0:
            continue

        # Build URL if not present
        url = item.get("url", "")
        if not url:
            slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
            url = f"{BASE_URL}/fr/maroc/{slug}_{list_id}.htm"
        if not url.startswith("http"):
            url = urljoin(BASE_URL, url)

        if url in seen_urls:
            continue

        # Extract image URL
        image_url = None
        images = item.get("images") or item.get("medias") or []
        if isinstance(images, list) and images:
            first = images[0]
            if isinstance(first, dict):
                image_url = first.get("url") or first.get("src") or first.get("thumb")
            elif isinstance(first, str):
                image_url = first
        elif isinstance(images, dict):
            image_url = images.get("url") or images.get("src")

        # Seller name
        seller_name = None
        seller = item.get("seller") or item.get("owner") or {}
        if isinstance(seller, dict):
            seller_name = seller.get("name") or seller.get("displayName")

        # Category info
        category_text = None
        cat = item.get("category") or {}
        if isinstance(cat, dict):
            cat_name = cat.get("name", "")
            parent = cat.get("parent", {})
            if isinstance(parent, dict):
                parent_name = parent.get("name", "")
                category_text = f"{parent_name} - {cat_name}" if parent_name else cat_name
            else:
                category_text = cat_name

        seen_urls.add(url)
        results.append({
            "title": title.strip(),
            "price": float(price),
            "currency": "MAD",
            "url": url,
            "image_url": image_url or None,
            "platform": "avito",
            "rating": None,
            "seller_name": seller_name,
            "category": category_text,
        })

    return results


def extract_avito_results(html: str, query: str | None = None) -> list[dict[str, Any]]:
    """
    Extract ad listings from an Avito search results page.

    Strategy cascade:
      1. __NEXT_DATA__ SSR state (best: full structured data from Next.js)
      2. JSON-LD (structured data injected per-ad)
      3. CSS card parsing (fallback for when JS hasn't fully rendered)
    """
    selector = Selector(text=html)
    results: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    query_words = query.lower().split() if query else []

    # ── Strategy 1: __NEXT_DATA__ ───────────────────────────────────
    next_data = selector.css('script#__NEXT_DATA__::text').get()
    if next_data:
        results = _extract_ads_from_next_data(next_data, seen_urls)

    if results:
        logger.info(f"Avito __NEXT_DATA__ extracted {len(results)} items")
        return results

    # ── Strategy 2: JSON-LD ─────────────────────────────────────────
    scripts = selector.css('script[type="application/ld+json"]::text').getall()
    for script_text in scripts:
        try:
            data = json.loads(script_text)
            if not isinstance(data, dict):
                continue

            offers = data.get("offers")
            if not offers or not isinstance(offers, dict):
                continue

            title = data.get("name")
            if not title:
                continue

            price = offers.get("price")
            if price is None or float(price) <= 0:
                continue

            url = offers.get("url")
            if not url:
                continue

            # Relevance filter
            if query_words and not any(w in title.lower() for w in query_words):
                continue

            currency = offers.get("priceCurrency") or "MAD"
            images = data.get("image")
            image_url = images[0] if isinstance(images, list) and images else images

            if url in seen_urls:
                continue
            seen_urls.add(url)
            results.append({
                "title": title,
                "price": float(price),
                "currency": "MAD" if currency == "DH" else currency,
                "url": url,
                "image_url": image_url,
                "platform": "avito",
                "rating": None,
            })
        except Exception:
            continue

    if results:
        logger.info(f"Avito JSON-LD extracted {len(results)} items")
        return results

    # ── Strategy 3: CSS card parsing ────────────────────────────────
    # Card structure (from saved HTML samples):
    #   <a class="sc-1jge648-0 jZXrfL" href=".../product_12345678.htm">
    #     <p class="sc-1x0vz2r-0 iHApav" title="Product Title">...</p>
    #     <span class="sc-3286ebc5-2 PuYkS">3 900</span>
    #     <span class="sc-3286ebc5-5 eHXozK">DH</span>
    #   </a>

    for card in selector.css('a[href$=".htm"]'):
        url = card.attrib.get("href", "")
        if not url:
            continue
        if not url.startswith("http"):
            url = urljoin(BASE_URL, url)
        # Only keep product-detail links (they end with _<digits>.htm)
        if not re.search(r"_\d+\.htm$", url):
            continue
        if url in seen_urls:
            continue

        # ── Title ──
        title = card.css('p[title]::attr(title)').get()
        if not title:
            title = (
                card.css('p[class*="iHApav"]::text').get()
                or card.css("p.sc-1x0vz2r-0::text").get()
                or card.css("h3::text").get()
            )
        if not title:
            slug = url.split("/")[-1].replace(".htm", "")
            title = re.sub(r"_\d+$", "", slug).replace("_", " ")

        if not title or len(title.strip()) < 3:
            continue
        title = title.strip()

        # ── Price ──
        price_text = card.css('span[class*="PuYkS"]::text').get()
        if not price_text:
            price_text = card.xpath(
                './/*[contains(text(), "DH")]/parent::*//text()'
            ).get()
        if not price_text:
            price_text = card.xpath('.//*[contains(text(), "DH")]/text()').get()

        price = parse_price_string(price_text)
        if price is None or price <= 0:
            continue

        # ── Image ──
        image_url = (
            card.css('img[class*="jXTiJI"]::attr(src)').get()
            or card.css('img[class*="sc-1lb3x1r-3"]::attr(src)').get()
            or card.css("img::attr(data-src)").get()
        )
        # Skip avatar images
        if image_url and "avatar" in image_url:
            for img in card.css("img"):
                src = img.attrib.get("src", "")
                if src and "avatar" not in src and not src.startswith("data:"):
                    image_url = src
                    break

        seen_urls.add(url)
        results.append({
            "title": title,
            "price": price,
            "currency": "MAD",
            "url": url,
            "image_url": image_url,
            "platform": "avito",
            "rating": None,
        })

    logger.info(f"Avito CSS fallback extracted {len(results)} items")
    return results


def _extract_next_page_url(current_url: str, page_num: int) -> str:
    """Generate the next page URL. Avito uses o={page_num+1} for pagination."""
    base = current_url.rstrip("/")

    if "?" in base:
        if "o=" in base:
            return re.sub(r"o=\d+", f"o={page_num + 1}", base)
        return f"{base}&o={page_num + 1}"
    return f"{base}?o={page_num + 1}"


def scrape_avito(
    query_or_url: str, browser, progress_callback=None
) -> list[dict[str, Any]]:
    context = create_context(browser)
    page = context.new_page()
    results: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    try:
        if query_or_url.startswith("http"):
            base_search_url = query_or_url
            page_num_offset = 1
            try:
                from urllib.parse import urlparse
                parsed = urlparse(query_or_url)
                qs = parse_qs(parsed.query)
                o = qs.get("o", ["1"])[0]
                page_num_offset = int(o)
            except (ValueError, IndexError):
                page_num_offset = 1

            query = parse_qs(urlparse(query_or_url).query).get("q", [None])[0]
        else:
            base_search_url = _build_search_url(query_or_url)
            page_num_offset = 1
            query = query_or_url

        next_url = base_search_url

        for page_num in range(1, MAX_PAGES + 1):
            if progress_callback:
                progress_callback("avito", len(results))

            logger.info(f"Scraping Avito page {page_num}: {next_url}")
            page.goto(next_url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)

            page_results = extract_avito_results(page.content(), query=query)
            if not page_results:
                logger.warning(f"No results found on Avito page {page_num}")
                # Retry with longer wait on first page
                if page_num == 1:
                    page.wait_for_timeout(3000)
                    page_results = extract_avito_results(page.content(), query=query)

                if not page_results:
                    break

            for item in page_results:
                if item["url"] in seen_urls:
                    continue
                seen_urls.add(item["url"])
                results.append(item)

            next_url = _extract_next_page_url(base_search_url, page_num + page_num_offset - 1)

        return results
    finally:
        page.close()
        context.close()