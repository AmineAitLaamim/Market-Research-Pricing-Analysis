from __future__ import annotations

import json
import logging
import re
from typing import Any
from urllib.parse import quote_plus, urljoin

from parsel import Selector

from .base import create_context, parse_price_string


logger = logging.getLogger(__name__)

BASE_URL = "https://www.avito.ma"
# Avito uses o=page_number for pagination. o=1 is page 1, o=2 is page 2, etc.
SEARCH_URL = f"{BASE_URL}/fr/maroc/recherche/?q={{query}}"
MAX_PAGES = 3


def extract_avito_results(html: str, query: str | None = None) -> list[dict[str, Any]]:
    selector = Selector(text=html)
    results: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    query_words = query.lower().split() if query else []

    # ── Strategy 1: JSON-LD (most structured and reliable) ──────────────
    # Avito injects structured data as <script type="application/ld+json">
    # when the page is rendered by Playwright. Each product gets its own
    # JSON-LD block with an "offers" object.
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

            # Relevance filter: at least one query word must appear in the title
            if query_words and not any(w in title.lower() for w in query_words):
                continue

            currency = offers.get("priceCurrency") or "MAD"
            images = data.get("image")
            image_url = images[0] if isinstance(images, list) and images else images

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

    # ── Strategy 2: CSS card extraction (fallback) ──────────────────────
    # When JSON-LD is missing (e.g. category browsing pages, or if Avito
    # changes its structured-data injection), we parse the rendered cards.
    #
    # Card structure (from saved HTML samples):
    #   <a class="sc-1jge648-0 ..." href=".../.htm">
    #     <p class="sc-1x0vz2r-0 iHApav" title="Product Title">...</p>
    #     <span class="sc-3286ebc5-2 PuYkS">3 900</span>
    #     <span class="sc-3286ebc5-5 eHXozK">DH</span>
    #     <img class="sc-1lb3x1r-3 jXTiJI" src="...">
    #   </a>

    # Primary card selector: <a> tags linking to .htm product pages
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
        # Best source: <p title="..."> attribute (always clean)
        title = card.css('p[title]::attr(title)').get()
        if not title:
            # Fallback: text of the title paragraph (class iHApav or sc-1x0vz2r-0)
            title = (
                card.css('p[class*="iHApav"]::text').get()
                or card.css('p.sc-1x0vz2r-0::text').get()
                or card.css('h3::text').get()
            )
        if not title:
            # Last resort: extract from URL slug
            slug = url.split("/")[-1].replace(".htm", "")
            title = re.sub(r"_\d+$", "", slug).replace("_", " ")

        if not title or len(title.strip()) < 3:
            continue
        title = title.strip()

        # ── Price ──
        # Primary: the PuYkS class spans contain just the digits
        price_text = card.css('span[class*="PuYkS"]::text').get()
        if not price_text:
            # Fallback: look for any element with "DH" nearby
            price_text = card.xpath(
                './/*[contains(text(), "DH")]/parent::*//text()'
            ).get()
        if not price_text:
            # Broader fallback: any text containing "DH"
            price_text = card.xpath(
                './/*[contains(text(), "DH")]/text()'
            ).get()

        price = parse_price_string(price_text)
        if price is None or price <= 0:
            continue

        # ── Image ──
        # Product images (not user avatars) use class jXTiJI / sc-1lb3x1r-3
        image_url = (
            card.css('img[class*="jXTiJI"]::attr(src)').get()
            or card.css('img[class*="sc-1lb3x1r-3"]::attr(src)').get()
            or card.css('img::attr(data-src)').get()
        )
        # Skip avatar images
        if image_url and "avatar" in image_url:
            # Try to find a non-avatar image
            for img in card.css('img'):
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
    # Page num starts from 1. Avito uses o=2 for page 2.
    # First, handle trailing slashes which might cause double slashes when appending
    base = current_url.rstrip('/')

    if "?" in base:
        if "o=" in base:
            return re.sub(r'o=\d+', f'o={page_num + 1}', base)
        else:
            return f"{base}&o={page_num + 1}"
    else:
        return f"{base}?o={page_num + 1}"


def scrape_avito(query_or_url: str, browser, progress_callback=None) -> list[dict[str, Any]]:
    context = create_context(browser)
    page = context.new_page()
    results: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    try:
        if query_or_url.startswith("http"):
            base_search_url = query_or_url
            from urllib.parse import parse_qs, urlparse
            query = parse_qs(urlparse(query_or_url).query).get('q', [None])[0]
        else:
            base_search_url = SEARCH_URL.format(query=quote_plus(query_or_url))
            query = query_or_url

        next_url = base_search_url

        for page_num in range(1, MAX_PAGES + 1):
            if progress_callback:
                progress_callback("avito", len(results))

            logger.info(f"Scraping Avito page {page_num}: {next_url}")
            # Use networkidle to ensure Next.js has rendered
            page.goto(next_url, wait_until="networkidle", timeout=30000)

            # Additional small wait for any client-side script execution
            page.wait_for_timeout(2000)

            page_results = extract_avito_results(page.content(), query=query)
            if not page_results:
                logger.warning(f"No results found on Avito page {page_num}")
                # Try one more time with a longer wait if first page is empty
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

            next_url = _extract_next_page_url(base_search_url, page_num)

        return results
    finally:
        page.close()
        context.close()
