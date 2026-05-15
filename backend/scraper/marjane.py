from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import quote_plus, urljoin

from .base import apply_stealth, create_context
from .utils import clean_price, random_delay

logger = logging.getLogger(__name__)

BASE_URL = "https://www.marjane.ma"
SEARCH_URL = f"{BASE_URL}/search/{{query}}"
MAX_PAGES = 3
PRODUCT_LINK_SELECTOR = 'a[href*="/courses-en-ligne/"], a[href*="/product/"]'
PRODUCT_CARD_SELECTOR = 'aside[class*="product-card"], .product-card'
LOAD_MORE_TEXT_PATTERN = re.compile(r"(voir plus|afficher plus|charger plus|load more)", re.I)


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(value.split())
    return cleaned or None


def _build_search_url(query: str) -> str:
    return SEARCH_URL.format(query=quote_plus(query))


def _extract_price_and_currency(raw_text: str | None) -> tuple[float | None, str]:
    cleaned = _clean_text(raw_text)
    if not cleaned:
        return None, "MAD"

    currency = "MAD" if re.search(r"\b(?:dh|dhs|mad)\b", cleaned, re.I) else "MAD"
    price = clean_price(cleaned)
    return price, currency


def _extract_cards_from_page(page) -> list[dict[str, Any]]:
    return page.evaluate(
        """
        ({ cardSelector, linkSelector }) => {
          const cards = Array.from(document.querySelectorAll(cardSelector));
          return cards.map((card) => {
            const link =
              card.querySelector(linkSelector) ||
              card.closest(linkSelector);

            const titleNode =
              card.querySelector('[class*="title"]:not([class*="brand-title"])') ||
              card.querySelector('h2, h3, h4, p');

            const brandNode =
              card.querySelector('[class*="brand-title"], [class*="list-brand"]');

            const priceNode =
              card.querySelector('[class*="prices"]') ||
              card.querySelector('[class*="buy-block"]') ||
              card;

            const imageNode = card.querySelector("img");

            return {
              href: link ? link.getAttribute("href") : null,
              title: titleNode ? titleNode.textContent : null,
              brand: brandNode ? brandNode.textContent : null,
              price_text: priceNode ? priceNode.textContent : null,
              image_url: imageNode ? (imageNode.currentSrc || imageNode.src || imageNode.getAttribute("data-src")) : null,
            };
          });
        }
        """,
        {"cardSelector": PRODUCT_CARD_SELECTOR, "linkSelector": PRODUCT_LINK_SELECTOR},
    )


def _extract_results(page) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    for raw_item in _extract_cards_from_page(page):
        href = raw_item.get("href")
        title = _clean_text(raw_item.get("title"))
        brand = _clean_text(raw_item.get("brand"))
        price, currency = _extract_price_and_currency(raw_item.get("price_text"))
        image_url = raw_item.get("image_url")

        if not href or price is None:
            continue

        if not title:
            continue

        if brand and brand.lower() not in title.lower():
            title = f"{brand} {title}"

        if image_url and image_url.startswith("//"):
            image_url = "https:" + image_url

        results.append(
            {
                "title": title,
                "price": price,
                "currency": currency,
                "url": urljoin(BASE_URL, href),
                "image_url": image_url,
                "platform": "marjane",
                "rating": None,
            }
        )

    return results


def _click_load_more(page) -> bool:
    buttons = page.locator("button, a")
    count = min(buttons.count(), 50)

    for idx in range(count):
        try:
            button = buttons.nth(idx)
            text = _clean_text(button.inner_text(timeout=500))
            if not text or not LOAD_MORE_TEXT_PATTERN.search(text):
                continue

            if not button.is_visible():
                continue

            button.scroll_into_view_if_needed(timeout=1000)
            button.click(timeout=3000)
            return True
        except Exception:
            continue

    return False


def scrape_marjane(query_or_url: str, browser, progress_callback=None) -> list[dict[str, Any]]:
    context = create_context(browser)
    page = context.new_page()
    apply_stealth(page)
    results: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    try:
        url = query_or_url if query_or_url.startswith("http") else _build_search_url(query_or_url)

        logger.info("Scraping Marjane search: %s", url)
        page.goto(url, wait_until="networkidle", timeout=45000)
        random_delay(2, 4)

        try:
            page.wait_for_selector(PRODUCT_LINK_SELECTOR, timeout=15000)
        except Exception:
            logger.warning("No Marjane product links found for %s", url)
            return []

        for page_num in range(1, MAX_PAGES + 1):
            if progress_callback:
                progress_callback("marjane", len(results))

            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            random_delay(1, 2)

            page_results = _extract_results(page)
            if not page_results:
                break

            for item in page_results:
                if item["url"] in seen_urls:
                    continue
                seen_urls.add(item["url"])
                results.append(item)

            if page_num >= MAX_PAGES:
                break

            previous_count = len(seen_urls)
            if not _click_load_more(page):
                break

            random_delay(2, 4)
            if len(_extract_results(page)) <= previous_count:
                break

        return results
    finally:
        page.close()
        context.close()
