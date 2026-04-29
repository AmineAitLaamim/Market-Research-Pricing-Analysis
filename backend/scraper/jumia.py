from __future__ import annotations

from typing import Any
from urllib.parse import quote_plus, urljoin

from parsel import Selector

from .base import create_context, parse_price_string


BASE_URL = "https://www.jumia.ma"
SEARCH_URL = f"{BASE_URL}/catalog/?q={{query}}"
PRODUCT_CARD_SELECTOR = "article.prd, .c-product-item"
MAX_PAGES = 3


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(value.split())
    return cleaned or None


def _parse_price(price_text: str | None) -> tuple[float | None, str | None]:
    cleaned = _clean_text(price_text)
    if not cleaned:
        return None, None

    currency = "MAD" if "DH" in cleaned.upper() else None
    price = parse_price_string(cleaned)
    return price, currency


def _parse_rating(rating_text: str | None) -> float | None:
    cleaned = _clean_text(rating_text)
    if not cleaned:
        return None

    # Handle "4.5 out of 5" or "4.5 / 5"
    token = cleaned.split(" out")[0].split("/")[0].split("sur")[0].strip()
    try:
        return float(token)
    except ValueError:
        return None


def extract_jumia_results(html: str) -> list[dict[str, Any]]:
    selector = Selector(text=html)
    results: list[dict[str, Any]] = []

    for card in selector.css(PRODUCT_CARD_SELECTOR):
        title = _clean_text(card.css(".info .name::text, .name::text").get())
        raw_price = card.css(".prc::text").get()
        price, currency = _parse_price(raw_price)
        url = card.css("a.core::attr(href), a::attr(href)").get()
        rating_text = (
            card.css(".stars::attr(aria-label)").get()
            or card.css(".stars._s::attr(aria-label)").get()
            or card.css(".rev::text").get()
        )
        rating = _parse_rating(rating_text)

        if not title or not url or price is None:
            continue

        results.append(
            {
                "title": title,
                "price": price,
                "currency": currency or "MAD",
                "url": urljoin(BASE_URL, url),
                "platform": "jumia",
                "rating": rating,
            }
        )

    return results


def _extract_next_page_url(page) -> str | None:
    # Try multiple aria-labels for different site languages
    selector = 'a[aria-label="Next Page"], a[aria-label="Page suivante"]'
    try:
        # Use a short timeout because if it's not there after cards load, it doesn't exist
        next_href = page.locator(selector).first.get_attribute("href", timeout=2000)
        if next_href:
            return urljoin(BASE_URL, next_href)
    except Exception:
        pass
    return None


def scrape_jumia(query_or_url: str, browser, progress_callback=None) -> list[dict[str, Any]]:
    context = create_context(browser)
    page = context.new_page()
    results: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    try:
        if query_or_url.startswith("http"):
            next_url = query_or_url
        else:
            next_url = SEARCH_URL.format(query=quote_plus(query_or_url))

        for page_num in range(1, MAX_PAGES + 1):
            if progress_callback:
                progress_callback("jumia", len(results))
            
            page.goto(next_url, wait_until="domcontentloaded")
            
            # Wait for either products or an empty state
            try:
                page.wait_for_selector(PRODUCT_CARD_SELECTOR, timeout=10000)
            except Exception:
                # Might be an empty results page
                break

            for item in extract_jumia_results(page.content()):
                if item["url"] in seen_urls:
                    continue
                seen_urls.add(item["url"])
                results.append(item)

            next_url = _extract_next_page_url(page)
            if not next_url:
                break

        return results
    finally:
        page.close()
        context.close()
