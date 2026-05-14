# Avito Anti-Bot Detection — Implementation Notes

## Problem

Avito.ma is a **Next.js** site with server-side rendering. When scraping it with
a headless Playwright browser, the bot detection may return an access-denied /
robot-check page instead of product listings. This caused the scraper to silently
return empty results with no actionable log message.

### Root causes in the original code

| Issue | Why it matters |
|---|---|
| `headless=True` (Playwright default) | Headless Chromium leaks 30+ fingerprinting signals |
| No `playwright-stealth` | `navigator.webdriver` and other signals expose the bot |
| No human-like interaction | Instant `goto` → data grab looks robotic |
| No block-page detection | Returned empty results silently when blocked |
| Short timeout (`30 000 ms`) | Next.js SSR pages can be slow on first load |
| Short delay (`1–3 s`) | Not enough settle time for lazy-loaded JS content |

---

## Solution — Same 3-Layer Approach as AliExpress

```
Layer 1 — playwright-stealth      (patches 30+ browser fingerprinting signals)
Layer 2 — headed Chromium/Xvfb   (applied project-wide via docker-compose)
Layer 3 — _human_warmup()         (random mouse moves + smooth scroll)
          + _is_blocked_page()    (clear warning log instead of silent empty)
```

> **Note:** Layers 1 and 2 were already set up project-wide (in `base.py` and
> `docker-compose.yml`) during the AliExpress fix. Only Layer 3 needed to be
> added to `avito.py` specifically.

---

## Changes Made

### `backend/scraper/avito.py`

#### a) Import `apply_stealth`

```python
# Before
from .base import create_context

# After
from .base import apply_stealth, create_context
```

#### b) Block-page selector list

Avito does not use a branded CAPTCHA like Akamai; it shows generic
access-denied or robot-check pages:

```python
_BLOCK_SELECTORS = [
    "#captcha",
    "[class*='captcha']",
    "[id*='captcha']",
    ".robot-check",
    "[class*='blocked']",
]
```

#### c) `_is_blocked_page()` detector

```python
def _is_blocked_page(page) -> bool:
    """Return True if Avito is showing a CAPTCHA or access-denied page."""
    for selector in _BLOCK_SELECTORS:
        try:
            if page.locator(selector).count() > 0:
                return True
        except Exception:
            pass
    html_snippet = page.content()[:4000].lower()
    return any(kw in html_snippet for kw in ("robot", "captcha", "access denied", "accès refusé"))
```

#### d) `_human_warmup()` — random mouse + scroll

```python
def _human_warmup(page) -> None:
    """Random mouse moves + smooth scroll to mimic a human visitor."""
    vp = page.viewport_size or {"width": 1280, "height": 720}
    for _ in range(3):
        x = random.randint(200, vp["width"] - 200)
        y = random.randint(100, vp["height"] - 100)
        page.mouse.move(x, y)
        random_delay(0.2, 0.6)
    page.evaluate("window.scrollBy({top: 500, behavior: 'smooth'})")
    random_delay(0.5, 1.2)
    page.evaluate("window.scrollBy({top: -200, behavior: 'smooth'})")
    random_delay(0.3, 0.7)
```

#### e) Apply stealth on every page + updated scrape loop

```python
page = context.new_page()
apply_stealth(page)   # ← patches all fingerprints before any navigation
```

Old loop:
```python
page.goto(next_url, wait_until="networkidle", timeout=30000)
random_delay(1, 3)
page_results = extract_avito_results(...)
```

New loop:
```python
page.goto(next_url, wait_until="networkidle", timeout=45000)  # longer timeout
_human_warmup(page)                                            # mouse + scroll

if _is_blocked_page(page):
    logger.warning("Avito bot-check detected on page %d — ...", page_num)
    break

random_delay(2, 4)                                             # longer settle delay
page_results = extract_avito_results(...)
```

---

## Avito-Specific Notes

### Why Avito is different from AliExpress

| Aspect | AliExpress | Avito.ma |
|---|---|---|
| Bot system | Akamai Bot Manager | Generic / custom |
| Block type | Slider CAPTCHA (`#baxia-punish`) | Robot-check / access-denied page |
| Detection signal | DOM selector + `slide`+`verify` keywords | DOM selector + `robot`/`captcha`/`access denied` keywords |
| Tech stack | Custom React | Next.js (SSR — `__NEXT_DATA__` embedded) |

### Extraction strategy cascade (unchanged)

Avito embeds full structured data in the page via Next.js SSR. The extractor
tries three strategies in order:

```
1. __NEXT_DATA__  — best: full structured JSON (title, price, images, seller)
2. JSON-LD        — fallback: per-ad structured data
3. CSS card parse — last resort: raw DOM scraping
```

The bot-block detection is checked **before** extraction so that none of these
strategies run against an empty/wrong page.

---

## Files Changed Summary

| File | What changed |
|---|---|
| `backend/scraper/avito.py` | `apply_stealth()` per page; `_human_warmup()`; `_is_blocked_page()`; longer timeout (`45 000 ms`); longer settle delay (`2–4 s`) |

> `pyproject.toml`, `base.py`, `.env`, and `docker-compose.yml` were already
> updated during the AliExpress fix and apply to **all scrapers** automatically.
> See [`aliexpress-anti-captcha.md`](./aliexpress-anti-captcha.md) for those changes.
