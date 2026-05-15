from __future__ import annotations

import logging
import random
import re
from datetime import datetime
from typing import Any
from urllib.parse import quote_plus

from django.core.cache import cache

from .base import apply_stealth, create_context
from .utils import clean_price, random_delay

logger = logging.getLogger(__name__)

BASE_URL = "https://www.amazon.fr/s?k="
MAX_PAGES = 3

def _generate_queries(query: str) -> list[str]:
    """
    Generate related search queries to expand reach.
    Derived from user-provided expansion logic.
    """
    related = {
        "laptop": [
            "pc gamer", 
            "laptop",
            "ordinateur portable", 
            "macbook", 
            "macbook pro",
            "macbook air",
            "ordinateur hp",
            "ordinateur lenovo",
            "ultrabook",
            "chromebook",
            "pc portable asus",
            "ordinateur portable dell",
            "pc portable acer",
            "pc portable msi",
            "ordinateur portable etudiant",
            "ordinateur portable professionnel",
            "pc portable pas cher",
            "notebook pc",
            "ordinateur portable i7",
            "ordinateur portable rtx",
            "surface laptop",
            "microsoft surface",
            "huawei matebook",
            "xiaomi redmibook",
            "thinkpad",
            "lenovo ideapad",
            "lenovo yoga",
            "dell xps",
            "dell latitude",
            "dell inspiron",
            "hp pavilion",
            "hp omen",
            "acer predator",
            "acer swift",
            "acer aspire",
            "asus rog",
            "asus zenbook",
            "msi stealth",
            "apple mac",
            "pc portable i5",
            "pc portable i9",
            "pc portable ryzen 5",
            "pc portable ryzen 7",
            "pc portable ryzen 9",
            "pc portable 16 go ram",
            "pc portable 32 go ram",
            "pc portable ssd",
            "pc portable 1 to",
            "pc portable rtx 3060",
            "pc portable rtx 4070",
            "pc portable rtx 4090",
            "pc portable gtx 1660",
            "pc portable 144hz",
            "pc portable 120hz",
            "pc portable oled",
            "pc portable 4k",
            "pc portable full hd",
            "pc portable intel core",
            "pc portable amd",
        ]
    }
    query_lower = query.lower().strip()
    return related.get(query_lower, [query])


def _is_captcha_page(page) -> bool:
    """Detect Amazon's robot check / captcha page."""
    html = page.content().lower()
    return "robot check" in html or "captcha" in html or page.locator("#captchacharacters").count() > 0


def _human_warmup(page) -> None:
    """Perform random mouse movements and a slow scroll to mimic a human."""
    try:
        vp = page.viewport_size or {"width": 1280, "height": 720}
        # Three random mouse moves
        for _ in range(3):
            x = random.randint(200, vp["width"] - 200)
            y = random.randint(100, vp["height"] - 100)
            page.mouse.move(x, y)
            random_delay(0.2, 0.6)
        # Slow scroll down
        page.evaluate("window.scrollBy({top: 400, behavior: 'smooth'})")
        random_delay(0.5, 1.2)
        page.evaluate("window.scrollBy({top: -200, behavior: 'smooth'})")
        random_delay(0.3, 0.7)
    except Exception:
        pass


def scrape_amazon(
    query: str, browser, progress_callback=None
) -> list[dict[str, Any]]:
    context = create_context(browser)
    page = context.new_page()
    apply_stealth(page)
    results: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    # Expand query if it matches expansion keys
    queries = _generate_queries(query)

    try:
        for q in queries:
            if cache.get("STOP_SCRAPING"):
                logger.info(f"Scraping Amazon cancelled via cache for query: {q}")
                break

            formatted_query = quote_plus(q)
            
            for p_idx in range(1, MAX_PAGES + 1):
                if cache.get("STOP_SCRAPING"):
                    break
                
                if progress_callback:
                    progress_callback("amazon", len(results))

                url = f"{BASE_URL}{formatted_query}&page={p_idx}"
                logger.info(f"Scraping Amazon page {p_idx}: {url}")

                try:
                    # Navigation
                    page.goto(url, wait_until="networkidle", timeout=60000)
                    
                    # Human behavior
                    _human_warmup(page)

                    # Check for captcha
                    if _is_captcha_page(page):
                        logger.warning(f"Amazon CAPTCHA detected on page {p_idx}")
                        break

                    # Extra delay for dynamic content
                    random_delay(2, 4)

                    items = page.query_selector_all('div[data-component-type="s-search-result"]')
                    
                    if not items:
                        logger.warning(f"No results found on Amazon page {p_idx} for {q}")
                        break

                    for item in items:
                        try:
                            # Selectors
                            title_el = item.query_selector('h2 a span') or item.query_selector('h2 span')
                            price_el = item.query_selector('.a-price .a-offscreen') 
                            link_el = item.query_selector('h2 a') or item.query_selector('a.a-link-normal.s-no-outline')
                            img_el = item.query_selector('img.s-image')
                            rating_el = item.query_selector('i.a-icon-star-small span.a-icon-alt') or \
                                        item.query_selector('i.a-icon-star span.a-icon-alt')

                            if not title_el:
                                continue

                            title_text = title_el.inner_text().strip()
                            
                            # Price and Currency
                            price_val = None
                            currency = "EUR" # Base currency for amazon.fr
                            
                            if price_el:
                                raw_price = price_el.inner_text().strip()
                                # Amazon.fr prices often have € at the end or start
                                price_val = clean_price(raw_price)
                            
                            # Skip if no price found
                            if price_val is None:
                                continue

                            # URL
                            url_path = "N/A"
                            if link_el:
                                href = link_el.get_attribute("href")
                                if href:
                                    url_path = href if href.startswith('http') else "https://www.amazon.fr" + href
                            
                            if url_path == "N/A" or url_path in seen_urls:
                                continue
                            seen_urls.add(url_path)

                            # Image
                            image_url = None
                            if img_el:
                                image_url = img_el.get_attribute("src")

                            # Rating
                            rating = None
                            if rating_el:
                                rating_text = rating_el.inner_text()
                                # Matches 4.5 or 4,5
                                rating_match = re.search(r'(\d[,.]\d)', rating_text)
                                if rating_match:
                                    rating = float(rating_match.group(1).replace(',', '.'))

                            results.append({
                                "title": title_text,
                                "price": float(price_val),
                                "currency": currency,
                                "url": url_path,
                                "image_url": image_url,
                                "platform": "amazon",
                                "rating": rating,
                            })
                        except Exception:
                            logger.exception("Error parsing an individual Amazon item")
                            continue

                except Exception as e:
                    logger.error(f"Failed to navigate to Amazon page {p_idx}: {e}")
                    break
        
        return results
    finally:
        page.close()
        context.close()
