# Product Intelligence Page

## Overview

The Product Intelligence page (`/analytics`) gives users deep market intelligence on any product they've previously scraped. It provides price history charts, trend analysis, buy/wait recommendations, similar product comparisons, and configurable price alert thresholds — all computed from the user's own scrape data.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                          Frontend                                │
│                                                                  │
│   AnalyticsPage.jsx             ← search state + recent grid     │
│   └── ProductDetail.jsx         ← full detail view               │
│       ├── PriceChart.jsx        ← Recharts LineChart             │
│       └── PriceCalendar.jsx     ← SVG heatmap (last 90 days)    │
│                                                                  │
│   api/analytics.js              ← HTTP calls                     │
└────────────────────┬─────────────────────────────────────────────┘
                     │ REST API
┌────────────────────▼─────────────────────────────────────────────┐
│                          Backend                                 │
│                                                                  │
│   analytics_views.py                                             │
│   ├── ProductSearchView         GET  /api/analytics/products/    │
│   ├── ProductHistoryView        GET  /api/analytics/product-history/ │
│   ├── SimilarProductsView       GET  /api/analytics/similar/     │
│   └── SetThresholdView          POST /api/analytics/threshold/   │
│                                                                  │
│   models.py                                                      │
│   ├── PriceThreshold            ← user-defined target prices     │
│   └── PriceAlert.is_threshold_alert  ← new field                 │
│                                                                  │
│   utils.py                      ← shared normalize_title()       │
│   price_alerts.py               ← updated with threshold check   │
└──────────────────────────────────────────────────────────────────┘
```

---

## How It Works

### Search State

1. User navigates to `/analytics`.
2. The page shows a centered search input and a "Recently tracked" grid (6 most recent unique products).
3. Typing 2+ characters triggers a debounced search (300ms) against `ProductSearchView`.
4. A dropdown shows matching products with title, platform badge, scrape count, and latest price.
5. Clicking a product or a recent card transitions to the detail state.

### Detail State

Once a product is selected, two API calls fire in parallel:
- `getProductHistory()` — returns all price data, summary stats, trend, recommendation, brackets, calendar data, scrape log, and threshold.
- `getSimilarProducts()` — returns up to 5 similar products from the user's history.

The detail view renders 9 sections described below.

---

## Data Model

### `PriceThreshold`

| Field             | Type          | Description                                    |
|-------------------|---------------|------------------------------------------------|
| `user`            | FK → User     | Owner                                          |
| `normalized_title`| CharField     | Lowercased, punctuation-stripped product title  |
| `platform`        | CharField     | e.g. `jumia`, `avito`                          |
| `threshold_mad`   | Decimal       | User's target price in MAD                     |
| `created_at`      | DateTimeField | Auto-set on creation                           |
| `updated_at`      | DateTimeField | Auto-updated on save                           |

**Constraint:** `unique_together = ['user', 'normalized_title', 'platform']`

### `PriceAlert.is_threshold_alert`

New boolean field (default `False`). When `True`, the alert was generated because the price hit the user's configured threshold, not just because it dropped compared to the previous scrape.

---

## API Reference

All endpoints require authentication (`Authorization: Bearer <token>`).

### `GET /api/analytics/products/?q={query}`

Search previously scraped products by title.

| Param | Required | Description |
|-------|----------|-------------|
| `q`   | No       | Search string (min 2 chars). If empty or <2 chars, returns 6 most recently scraped unique products. |

**Response** (array, max 10 items):
```json
[
  {
    "title": "DELL Optiplex 3020 MT Intel Celeron",
    "normalized_title": "dell optiplex 3020 mt intel celeron",
    "platform": "jumia",
    "scrape_count": 5,
    "latest_price_mad": 420.00,
    "last_scraped": "2025-05-08T14:30:00Z"
  }
]
```

**Deduplication logic:**
- Products are grouped by `(normalized_title, platform)`.
- The displayed title is the most common raw title variant (statistical mode).

---

### `GET /api/analytics/product-history/?title={normalized_title}&platform={platform}`

Full market intelligence for a single product.

| Param      | Required | Description |
|------------|----------|-------------|
| `title`    | Yes      | Normalized title string |
| `platform` | Yes      | Platform name |

**Response shape:**
```json
{
  "title": "DELL Optiplex 3020 MT Intel Celeron",
  "normalized_title": "dell optiplex 3020 mt intel celeron",
  "platform": "jumia",
  "trend": "dropping",
  "recommendation": {
    "verdict": "buy_now",
    "reason": "Current price is within 5% of the all-time low."
  },
  "summary": {
    "current_price": 299.00,
    "lowest_price": 280.00,
    "lowest_price_date": "2025-04-15",
    "highest_price": 450.00,
    "highest_price_date": "2025-03-01",
    "avg_price": 365.00,
    "total_scrapes": 8,
    "first_seen": "2025-03-01",
    "last_seen": "2025-05-08",
    "price_change_overall": -151.00,
    "price_change_percent": -33.6,
    "volatility": 52.30,
    "days_tracked": 68
  },
  "price_history": [
    { "date": "2025-03-01", "price_mad": 450.00 }
  ],
  "price_brackets": [
    { "label": "Under 337 MAD", "count": 3, "percent": 37.5 },
    { "label": "337–393 MAD", "count": 2, "percent": 25.0 },
    { "label": "Over 393 MAD", "count": 3, "percent": 37.5 }
  ],
  "scrape_log": [
    { "date": "2025-05-08", "price_mad": 299.00, "search_query": "pc", "product_url": "https://..." }
  ],
  "calendar_data": [
    { "date": "2025-05-08", "price_mad": 299.00, "is_lowest": false, "is_highest": false }
  ],
  "threshold": { "threshold_mad": 280.00 }
}
```

#### Trend Detection

| Trend          | Condition |
|----------------|-----------|
| `dropping`     | Last 3 prices each lower than the previous |
| `rising`       | Last 3 prices each higher than the previous |
| `stable`       | Coefficient of variation (std/mean) < 0.02 |
| `fluctuating`  | Anything else |
| `uncertain`    | Fewer than 3 scrapes |

#### Recommendation Engine

Evaluated in priority order:

| Verdict     | Condition |
|-------------|-----------|
| `uncertain` | Total scrapes < 3 |
| `buy_now`   | Current price ≤ lowest × 1.05 AND trend is dropping or stable |
| `good_deal` | Current price ≤ average × 0.90 |
| `wait`      | Trend is rising AND current price > average |
| `wait`      | Trend is dropping AND current price > lowest × 1.10 |
| `neutral`   | Default fallback |

#### Price Brackets

- The min–max range is split into 3 equal segments.
- For each segment, the count and percentage of scrape entries falling within it are computed.

---

### `GET /api/analytics/similar/?title={normalized_title}&platform={platform}`

Find similar products in the user's scrape history.

| Param      | Required | Description |
|------------|----------|-------------|
| `title`    | Yes      | Normalized title of the query product |
| `platform` | No       | Platform name |

**Response** (array, max 5 items, sorted by similarity desc):
```json
[
  {
    "title": "DELL Optiplex 3010 Intel Core i3",
    "normalized_title": "dell optiplex 3010 intel core i3",
    "platform": "jumia",
    "latest_price_mad": 399.00,
    "price_diff_mad": 100.00,
    "price_diff_direction": "more_expensive",
    "scrape_count": 3
  }
]
```

**Matching logic:**
- Uses `difflib.SequenceMatcher` with a threshold of `> 0.45` (intentionally lower than the 0.85 used in price alerts to surface broader comparisons).
- `price_diff_direction` is `"cheaper"`, `"more_expensive"`, or `"same"` relative to the query product's current price.

---

### `POST /api/analytics/threshold/`

Set or update a price alert threshold for a product.

**Request body:**
```json
{
  "normalized_title": "dell optiplex 3020 mt intel celeron",
  "platform": "jumia",
  "threshold_mad": 280.00
}
```

**Response:**
```json
{
  "normalized_title": "dell optiplex 3020 mt intel celeron",
  "platform": "jumia",
  "threshold_mad": 280.00,
  "created": true
}
```

**Validation:** `threshold_mad` must be a positive number.

**Behavior:** Uses `update_or_create` — if a threshold already exists for the same user + title + platform, it updates the value.

---

## Threshold Alert Integration

When `check_price_drops` runs after a scrape completes:

1. For each matched product where the new price is lower than the old price:
   - Look up `PriceThreshold` for the user + normalized title + platform.
   - If a threshold exists and `new_price_mad ≤ threshold_mad`:
     - Create a `PriceAlert` with `is_threshold_alert=True`.
     - This alert appears in the bell dropdown alongside regular drop alerts.

This means users get notified automatically when a product hits their target price — no need to manually check.

---

## Frontend Components

### `AnalyticsPage.jsx`

Two-state page controlled by `selectedProduct`:
- **`null`** → Search state (centered search input + recently tracked grid)
- **Object** → Detail state (renders `ProductDetail`)

### `ProductDetail.jsx`

Receives `{ product, onBack }` props. On mount, calls both `getProductHistory` and `getSimilarProducts` in parallel via `Promise.all`.

Renders 9 sections:

| Section | Description |
|---------|-------------|
| **A — Header** | Back arrow, product title + platform badge, "Scrape now" button |
| **B — Recommendation** | Color-coded card with icon, verdict label, and reason text |
| **C — Metric cards** | 5 cards: current price, all-time low, all-time high, average, days tracked |
| **D — Trend pill** | Full-width pill with icon + trend label |
| **E — Price chart** | Recharts `LineChart` with custom dots, avg reference line, threshold reference line |
| **F — Calendar + Brackets** | Two-column: SVG heatmap (left), horizontal bar distribution (right) |
| **G — Similar products** | Horizontally scrolling card row with price diff indicators |
| **H — Scrape log** | Alternating-row table: date, price, keyword pill, external link |
| **I — Threshold setter** | Input + save button, pre-filled if threshold exists |

### `PriceChart.jsx`

- Recharts `LineChart` with `#C1502E` line, strokeWidth 2.
- Custom dots: green (`#3B6D11`) for all-time low, red (`#A32D2D`) for all-time high, accent for normal.
- Dashed reference line at average price (labeled "avg").
- Dashed reference line at threshold (labeled "your target") if set.
- Custom tooltip with date, price, and "All-time low/high" badge.
- Single data point → shows message instead of chart.

### `PriceCalendar.jsx`

- Inline SVG rendering last 90 days as a 7-row grid of 10×10px squares.
- Days without scrapes: muted background.
- Days with scrapes: green color scale (darker = cheaper price, inverted logic — cheaper is better).
- Month labels above columns.
- Tooltip via `<title>` attribute on each `<rect>`.
- Legend bar below: "Higher price" (light) → "Lower price" (dark).

---

## File Map

```
backend/
├── apps/search/
│   ├── models.py              ← PriceThreshold + PriceAlert.is_threshold_alert
│   ├── utils.py               ← normalize_title() shared utility
│   ├── price_alerts.py        ← threshold check added after drop detection
│   ├── analytics_views.py     ← ProductSearch, ProductHistory, Similar, SetThreshold
│   └── analytics_urls.py      ← /api/analytics/* routes
│
├── config/
│   └── urls.py                ← includes analytics_urls
│
frontend/src/
├── api/
│   └── analytics.js           ← searchProducts, getProductHistory, getSimilarProducts, setThreshold
├── pages/
│   └── AnalyticsPage.jsx      ← search + detail states
├── components/
│   ├── Navbar.jsx             ← added Analytics nav link
│   ├── SearchForm.jsx         ← added initialQuery prop
│   └── analytics/
│       ├── ProductDetail.jsx  ← full detail view (9 sections)
│       ├── PriceChart.jsx     ← Recharts line chart
│       └── PriceCalendar.jsx  ← SVG heatmap
```

---

## Shared Utility: `normalize_title()`

Located in `backend/apps/search/utils.py`. Used across:
- `price_alerts.py` — matching products between scrapes
- `analytics_views.py` — deduplicating and looking up products

```python
def normalize_title(title: str) -> str:
    title = title.lower()
    title = re.sub(r'[^\w\s]', '', title)
    title = re.sub(r'\s+', ' ', title).strip()
    return title
```

---

## Design Decisions

| Decision | Rationale |
|---------|-----------|
| **Separate `analytics_urls.py`** | Keeps the analytics routes cleanly separated from the core search CRUD routes. Mounted at `/api/analytics/` in the main URL config. |
| **Similarity threshold at 0.45** | Much lower than the 0.85 used in price alerts. The goal here is broader discovery ("what else looks like this product?"), not strict matching. |
| **3 price brackets** | Simple enough to parse at a glance. Auto-computed from the data's own min/max range, so they adapt to any product. |
| **Recommendation priority order** | `buy_now` is checked before `good_deal` because being near the all-time low is a stronger signal than just being below average. `wait` is checked before `neutral` to avoid false "no signal" verdicts when there is a clear directional trend. |
| **Coefficient of variation < 0.02 for "stable"** | A very tight threshold — the price must barely move relative to its mean to qualify as stable. This prevents mislabeling products with minor fluctuations. |
| **Calendar heatmap (inverted green)** | Cheaper = darker green. This is intentional — a darker cell is a "better deal day", which is the metric users care about most. |
| **`update_or_create` for thresholds** | One threshold per user per product per platform. Users don't need to manage multiple thresholds — they just set the number and it updates silently. |

---

## SearchPage Query Param Pre-fill

Clicking "Scrape now" in the analytics detail navigates to `/search?q={keyword}`. The `SearchPage` reads this param on mount via `useSearchParams()` and passes it as `initialQuery` to `SearchForm`, which pre-fills the search input.

This creates a seamless flow: **Analytics → "price is dropping, scrape now" → Search page pre-filled → one-click scrape**.
