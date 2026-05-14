# AliExpress Anti-CAPTCHA — Implementation Notes

## Problem

When scraping AliExpress, the bot detection system (**Akamai Bot Manager**) flags the
automated browser and displays a **slider CAPTCHA** — a bar the user must drag to
"verify" they are human. The session receives no product data.

### Root causes in the original code

| Issue | Why it matters |
|---|---|
| `headless=True` (Playwright default) | Headless Chromium leaks 30+ fingerprinting signals |
| Hand-rolled `_STEALTH_SCRIPT` (4–5 patches) | Akamai checks far more than `navigator.webdriver` |
| No `playwright-stealth` library | The library patches all major detection vectors automatically |
| No human-like interaction | Instant page load → data grab looks robotic |
| No CAPTCHA detection | Scraper returned empty results silently when blocked |

---

## Solution Overview

Three layers of defence were applied:

```
Layer 1 — playwright-stealth library  (patches 30+ browser signals)
Layer 2 — headed Chromium via Xvfb   (removes headless fingerprint entirely)
Layer 3 — human-like warmup           (random mouse moves + smooth scroll)
          + CAPTCHA detector           (log warning instead of silent empty result)
```

---

## Changes Made

### 1. `backend/pyproject.toml`

Added `playwright-stealth` as a project dependency:

```toml
"playwright==1.56.0",
"playwright-stealth==1.0.6",   # ← added
```

---

### 2. `backend/scraper/base.py`

**Removed** the hand-rolled `_STEALTH_SCRIPT` (only patched 4 signals).

**Added** `playwright-stealth` import and a new `apply_stealth(page)` helper:

```python
from playwright_stealth import stealth_sync

def apply_stealth(page: Page) -> None:
    """Apply playwright-stealth to a single page.

    Patches 30+ fingerprinting signals:
    navigator.webdriver, chrome runtime object, hairline feature,
    WebGL vendor/renderer, permission API, plugin array, etc.
    """
    stealth_sync(page)
```

**Added** `SCRAPER_HEADLESS` env-var support so headless mode can be toggled
without rebuilding the image:

```python
import os

_HEADLESS = os.environ.get("SCRAPER_HEADLESS", "true").lower() != "false"

_browser = _playwright.chromium.launch(
    headless=_HEADLESS,   # ← was hardcoded True
    args=[
        "--disable-blink-features=AutomationControlled",
        ...
    ],
)
```

---

### 3. `backend/scraper/aliexpress.py`

**Three additions:**

#### a) Apply stealth on every new page
```python
from .base import apply_stealth, create_context

page = context.new_page()
apply_stealth(page)   # ← patches all fingerprints before any navigation
```

#### b) CAPTCHA selector list + detector function
```python
_CAPTCHA_SELECTORS = [
    "#baxia-punish",       # Akamai slider overlay
    ".baxia-dialog",
    "[class*='slider']",
    "#nocaptcha",
    "[id*='captcha']",
]

def _is_captcha_page(page) -> bool:
    for selector in _CAPTCHA_SELECTORS:
        if page.locator(selector).count() > 0:
            return True
    html_snippet = page.content()[:4000].lower()
    return "slide" in html_snippet and "verify" in html_snippet
```

Called after each `page.goto()`:
```python
if _is_captcha_page(page):
    logger.warning("AliExpress CAPTCHA detected on page %d — ...", page_num)
    break
```

#### c) Human-like warmup
```python
def _human_warmup(page) -> None:
    # Three random mouse moves
    for _ in range(3):
        x = random.randint(200, vp["width"] - 200)
        y = random.randint(100, vp["height"] - 100)
        page.mouse.move(x, y)
        random_delay(0.2, 0.6)
    # Slow scroll down then back up
    page.evaluate("window.scrollBy({top: 400, behavior: 'smooth'})")
    random_delay(0.5, 1.2)
    page.evaluate("window.scrollBy({top: -200, behavior: 'smooth'})")
```

Also increased `timeout` from `30000` → `45000` ms and `random_delay` from
`(1, 3)` → `(2, 4)` seconds.

---

### 4. `backend/.env`

```env
# Set to false to run the browser with a visible window (reduces bot detection)
SCRAPER_HEADLESS=true
```

---

### 5. `docker/docker-compose.yml` — Xvfb virtual display

Running `headless=False` inside Docker crashes Chromium because there is no
display server. The fix is **Xvfb** (X Virtual Framebuffer): a fake screen that
Chromium renders into, available in the `mcr.microsoft.com/playwright/python`
base image with no extra install needed.

The `celery-worker` service was updated:

```yaml
celery-worker:
  command: >-
    sh -c "Xvfb :99 -screen 0 1280x720x24 -ac +extension GLX +render -noreset &
           sleep 1 &&
           celery -A config worker -l info"
  environment:
    - DISPLAY=:99            # ← points Chromium at the virtual screen
    - SCRAPER_HEADLESS=false # ← launches Chromium in headed (non-headless) mode
```

How it works:

```
Docker Container (celery-worker)
├── Xvfb :99          ← virtual screen (1280×720, 24-bit colour)
│     └── Chromium renders here — thinks it has a real monitor
└── Celery worker     ← Playwright launches Chromium with DISPLAY=:99
```

---

## Detection Risk Comparison

| Mode | Bot detection risk | Works in Docker |
|---|---|---|
| `headless=True`, no stealth | 🔴 Very High | ✅ Yes |
| `headless=True` + `playwright-stealth` | 🟡 Medium | ✅ Yes |
| `headless=False` without display | — | ❌ Crashes |
| `headless=False` + Xvfb + `playwright-stealth` | 🟢 Low | ✅ Yes |

---

## Escalation Path (if still blocked)

If the CAPTCHA still appears after these changes, the likely cause is the **IP
address** being flagged (Akamai maintains lists of datacenter IP ranges).

1. **Residential proxy** — set in `create_context()`:
   ```python
   context = browser.new_context(
       proxy={"server": "http://residential-proxy:port"},
       ...
   )
   ```
2. **CAPTCHA solving service** — integrate [2Captcha](https://2captcha.com/) or
   [CapSolver](https://www.capsolver.com/) (~$1 per 1 000 solves) as a last resort.

---

## Files Changed Summary

| File | What changed |
|---|---|
| `backend/pyproject.toml` | Added `playwright-stealth==1.0.6` |
| `backend/scraper/base.py` | Replaced `_STEALTH_SCRIPT` with `playwright-stealth`; added `apply_stealth()`; `SCRAPER_HEADLESS` env support |
| `backend/scraper/aliexpress.py` | `apply_stealth()` per page; `_human_warmup()`; `_is_captcha_page()` detector; longer timeouts/delays |
| `backend/.env` | Added `SCRAPER_HEADLESS=true` |
| `docker/docker-compose.yml` | `celery-worker` starts Xvfb, sets `DISPLAY=:99`, sets `SCRAPER_HEADLESS=false` |
