from __future__ import annotations

import json
import logging
import re
from typing import Any
from urllib.parse import quote_plus, urljoin

from parsel import Selector

from .base import create_context, parse_price_string

logger = logging.getLogger(__name__)

BASE_URL = "https://www.aliexpress.com"
MAX_PAGES = 3


def _build_search_url(query: str, page: int = 1) -> str:
    """
    Build an AliExpress search URL.
    """
    # AliExpress search URL format
    encoded_query = quote_plus(query)
    url = f"{BASE_URL}/w/wholesale-{encoded_query}.html"
    if page > 1:
        url += f"?page={page}"
    return url


def extract_aliexpress_results(html: str, query: str | None = None) -> list[dict[str, Any]]:
    """
    Extract product listings from an AliExpress search results page.
    Primary strategy: Parse the embedded _init_data_ JSON.
    """
    results: list[dict[str, Any]] = []
    
    # Extract the JSON object from the script tag
    # The JSON is delimited by /*!-->init-data-start--*/ and /*!-->init-data-end--*/
    # but we can also use a regex for window._dida_config_._init_data_
    match = re.search(r'window\._dida_config_\._init_data_=\s*({.*?})/\*!-->init-data-end--\*/', html, re.DOTALL)
    if not match:
        # Try a more general regex if the delimiter is missing
        match = re.search(r'window\._dida_config_\._init_data_=\s*({.*?});', html, re.DOTALL)
    
    if not match:
        logger.warning("Could not find AliExpress _init_data_ in HTML")
        return results

    content = match.group(1).strip()
    
    # Fix unquoted keys if necessary (AliExpress often leaves 'data' unquoted)
    if content.startswith('{ data:'):
        content = content.replace('{ data:', '{"data":', 1)
    
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        logger.exception("Failed to parse AliExpress _init_data_ JSON")
        return results

    # Navigate to the item list
    # Path found: data.data.root.fields.mods.itemList.content
    try:
        fields = data.get("data", {}).get("data", {}).get("root", {}).get("fields", {})
        mods = fields.get("mods", {})
        item_list = mods.get("itemList", {})
        items = item_list.get("content", [])
    except Exception:
        logger.exception("Error traversing AliExpress JSON structure")
        return results

    if not isinstance(items, list):
        return results

    for item in items:
        try:
            # Skip non-product items
            if item.get("itemType") != "productV3" and "productId" not in item:
                continue

            product_id = item.get("productId")
            if not product_id:
                continue

            title = item.get("title", {}).get("displayTitle")
            if not title:
                continue

            # Prices
            prices = item.get("prices", {})
            sale_price = prices.get("salePrice", {})
            
            price = sale_price.get("minPrice")
            currency = sale_price.get("currencyCode") or "USD"

            if price is None:
                # Fallback to formatted price parsing
                formatted = sale_price.get("formattedPrice")
                if formatted:
                    price = parse_price_string(formatted)
            
            if price is None:
                continue

            # Image
            image_url = item.get("image", {}).get("imgUrl")
            if image_url and image_url.startswith("//"):
                image_url = "https:" + image_url

            # Rating
            rating = item.get("evaluation", {}).get("starRating")
            
            # URL
            url = f"{BASE_URL}/item/{product_id}.html"

            results.append({
                "title": title.strip(),
                "price": float(price),
                "currency": currency,
                "url": url,
                "image_url": image_url,
                "platform": "aliexpress",
                "rating": float(rating) if rating is not None else None,
            })
        except Exception:
            logger.exception("Error parsing an individual AliExpress item")
            continue

    return results


def scrape_aliexpress(
    query_or_url: str, browser, progress_callback=None
) -> list[dict[str, Any]]:
    context = create_context(browser)
    page = context.new_page()
    results: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    try:
        if query_or_url.startswith("http"):
            next_url = query_or_url
        else:
            next_url = _build_search_url(query_or_url)

        for page_num in range(1, MAX_PAGES + 1):
            if progress_callback:
                progress_callback("aliexpress", len(results))

            logger.info(f"Scraping AliExpress page {page_num}: {next_url}")
            
            # AliExpress might need a real user agent or specific headers
            # but we'll start with default Playwright settings
            page.goto(next_url, wait_until="networkidle", timeout=30000)
            
            # Wait a bit for any dynamic content/redirects
            page.wait_for_timeout(2000)

            page_results = extract_aliexpress_results(page.content(), query=query_or_url)
            if not page_results:
                logger.warning(f"No results found on AliExpress page {page_num}")
                break

            for item in page_results:
                if item["url"] in seen_urls:
                    continue
                seen_urls.add(item["url"])
                results.append(item)

            # Pagination URL
            if query_or_url.startswith("http"):
                # If we started with a URL, we don't easily know how to paginate
                break
            else:
                next_url = _build_search_url(query_or_url, page=page_num + 1)

        return results
    finally:
        page.close()
        context.close()
