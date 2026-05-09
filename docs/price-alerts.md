# Price Alert Notification System

## Overview

The Price Alert system automatically detects price drops whenever a user re-scrapes a keyword they have searched before. It requires **zero configuration** from the user — alerts are generated and displayed in real time via a bell icon in the navbar.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                            │
│                                                             │
│   Navbar                                                    │
│   └── AlertBell.jsx          ← bell icon + dropdown UI      │
│       └── useAlerts.js       ← polling hook (every 30s)     │
│           └── api/alerts.js  ← HTTP calls to backend        │
└─────────────────────────────┬───────────────────────────────┘
                              │ REST API
┌─────────────────────────────▼───────────────────────────────┐
│                         Backend                             │
│                                                             │
│   tasks.py                  ← Celery scrape pipeline        │
│   └── price_alerts.py       ← drop detection (called after  │
│       └── PriceAlert model    each completed scrape)        │
│                                                             │
│   views.py                  ← AlertListView                 │
│                                AlertMarkReadView            │
│                                AlertMarkAllReadView         │
└─────────────────────────────────────────────────────────────┘
```

---

## How It Works — Step by Step

### Step 1 — First scrape (baseline)

The user searches for a keyword (e.g. `"pc"`). The Celery task `run_search_pipeline` scrapes all requested platforms, saves `RawPrice` records to the database, and marks the search as `completed`.

At this point there is no previous search to compare against, so no alerts are created.

### Step 2 — Re-scrape the same keyword

The user searches for the same keyword again on a different date. The scrape pipeline runs again. Once it completes and the search is marked `completed`, the pipeline immediately calls:

```python
from .price_alerts import check_price_drops
check_price_drops(user=search.user, new_search=search)
```

### Step 3 — Drop detection (`price_alerts.py`)

`check_price_drops` does the following:

1. **Find previous search** — queries for the most recent completed search by the same user with the same query (excluding the current one).
2. **Fetch both price sets** — loads `RawPrice` objects for both the old and new search.
3. **Match products** — for each product in the new results:
   - **Exact match**: normalize both titles (lowercase, strip punctuation and extra whitespace) and compare.
   - **Fuzzy match fallback**: if no exact match, use `difflib.SequenceMatcher(None, old_title, new_title).ratio() > 0.85` to catch minor title variations (e.g. different casing, extra spaces, punctuation changes).
4. **Calculate drop**:
   ```
   old_price_MAD = float(old.price) × old.exchange_rate
   new_price_MAD = float(new.price) × new.exchange_rate
   drop_amount   = old_price_MAD - new_price_MAD
   drop_percent  = (drop_amount / old_price_MAD) × 100
   ```
5. **Filter noise** — skip if `drop_amount < 1 MAD` (prevents floating-point false positives).
6. **Upsert alert** — checks if an unread `PriceAlert` already exists for the same user + product title + query:
   - **If yes**: delete it and recreate it with updated values and a refreshed `created_at` timestamp.
   - **If no**: create a new `PriceAlert`.
7. **Never crash the scrape** — the entire function is wrapped in `try/except Exception` with structured logging. A failure here has zero impact on the scrape response.

### Step 4 — Bell updates in real time

The `useAlerts` hook in the frontend polls `GET /api/search/alerts/` every **30 seconds**. As soon as new alerts exist, the bell badge updates automatically.

---

## Data Model

### `PriceAlert`

| Field           | Type          | Description                                    |
|----------------|---------------|------------------------------------------------|
| `user`          | FK → User     | Owner of the alert                             |
| `product_title` | CharField     | Raw product title from the scrape              |
| `old_price`     | Decimal       | Price in MAD at previous scrape                |
| `new_price`     | Decimal       | Price in MAD at latest scrape                  |
| `drop_amount`   | Decimal       | `old_price - new_price` in MAD                 |
| `drop_percent`  | Decimal       | `(drop_amount / old_price) × 100`              |
| `platform`      | CharField     | e.g. `avito`, `jumia`                          |
| `product_url`   | URLField      | Direct link to the product listing             |
| `search_query`  | CharField     | The keyword that triggered the alert           |
| `is_read`       | BooleanField  | `False` until the user clicks the alert card   |
| `created_at`    | DateTimeField | Auto-set; refreshed on upsert                  |

---

## API Reference

All endpoints are under `/api/search/` and require authentication (`Authorization: Bearer <token>`).

### `GET /api/search/alerts/`

Returns all price alerts for the authenticated user, ordered by most recent first.

**Response:**
```json
{
  "unread_count": 3,
  "results": [
    {
      "id": 42,
      "product_title": "Lenovo IdeaPad 3 15.6\" Intel Core i5",
      "old_price": "4500.00",
      "new_price": "3999.00",
      "drop_amount": "501.00",
      "drop_percent": "11.1",
      "platform": "jumia",
      "product_url": "https://www.jumia.ma/...",
      "search_query": "pc",
      "is_read": false,
      "created_at": "2025-05-08T14:30:00Z"
    }
  ]
}
```

---

### `PATCH /api/search/alerts/{id}/read/`

Marks a single alert as read.

**Response:**
```json
{ "id": 42, "is_read": true }
```

**Errors:**
- `404` — alert not found or does not belong to the authenticated user.

---

### `PATCH /api/search/alerts/read-all/`

Marks all unread alerts for the authenticated user as read.

**Response:**
```json
{ "marked": 3 }
```

---

## Frontend Components

### `src/api/alerts.js`

Thin wrapper around the authenticated axios instance.

```js
alertsApi.getAlerts()          // GET  /api/search/alerts/
alertsApi.markAlertRead(id)    // PATCH /api/search/alerts/{id}/read/
alertsApi.markAllRead()        // PATCH /api/search/alerts/read-all/
```

---

### `src/hooks/useAlerts.js`

Custom React hook. Mount it once in any component that needs alert data.

```js
const { alerts, unreadCount, markRead, markAllRead, loading, refresh } = useAlerts()
```

| Return value    | Type       | Description                                      |
|----------------|------------|--------------------------------------------------|
| `alerts`        | Array      | Full list of `PriceAlert` objects                |
| `unreadCount`   | Number     | Count of alerts where `is_read === false`        |
| `markRead(id)`  | Function   | Optimistically marks one alert as read           |
| `markAllRead()` | Function   | Optimistically marks all alerts as read          |
| `loading`       | Boolean    | `true` during initial fetch                      |
| `refresh()`     | Function   | Manually re-fetches (e.g. after a new scrape)    |

The hook sets up a `setInterval` polling every **30 seconds** and clears it on unmount via `useEffect` cleanup.

---

### `src/components/AlertBell.jsx`

Standalone bell icon component. Place it anywhere in the layout.

**Behavior:**
- Shows a **terracotta red badge** (`#C1502E`) with the unread count when `unreadCount > 0`.
- Clicking the bell toggles the dropdown.
- Clicking outside the dropdown closes it (via `mousedown` listener on `document`).

**Dropdown contents:**
- Header: "Price drops" label + "Mark all as read" button.
- Scrollable list (max 380px height) of alert cards:
  - Green `TrendingDown` icon background (`#EAF3DE` / `#3B6D11`)
  - Product title (truncated with ellipsis)
  - Old price ~~strikethrough~~ → new price + green savings pill (`-X MAD · -Y%`)
  - Platform, keyword, and time-ago timestamp
  - "View" link opening the product URL in a new tab
  - Red unread dot for unread alerts
  - Unread card background: `#F5F4F0`; read: `#fff`
- Empty state when no alerts exist.
- Footer with "View all alerts →" link (navigates to `/alerts`).

---

## File Map

```
backend/
├── apps/search/
│   ├── models.py          ← PriceAlert model (appended at bottom)
│   ├── price_alerts.py    ← check_price_drops() detection function
│   ├── tasks.py           ← calls check_price_drops() after COMPLETED
│   ├── views.py           ← AlertListView, AlertMarkReadView, AlertMarkAllReadView
│   └── urls.py            ← /alerts/, /alerts/<pk>/read/, /alerts/read-all/
│
frontend/src/
├── api/
│   └── alerts.js          ← getAlerts, markAlertRead, markAllRead
├── hooks/
│   └── useAlerts.js       ← polling hook
└── components/
    ├── AlertBell.jsx       ← bell icon + dropdown
    └── Navbar.jsx          ← imports AlertBell, places it between History and username
```

---

## Design Decisions

| Decision | Rationale |
|---------|-----------|
| **Auto-detect, no config** | Users should not need to set up price alerts manually. The system infers intent from re-searching the same keyword. |
| **1 MAD minimum drop threshold** | Eliminates false positives caused by floating-point arithmetic in currency conversion. |
| **Upsert pattern (delete + recreate)** | Keeps only one unread alert per product per query, preventing inbox clutter on frequent re-scrapes. Refreshes `created_at` so the user always sees the latest comparison. |
| **`try/except` around entire function** | Alert generation is a non-critical side effect. A bug here must never surface to the user or fail the scrape response. |
| **30-second polling** | Simple and reliable without requiring WebSocket infrastructure for alerts specifically. |
| **Fuzzy matching at 0.85** | Conservative threshold — catches minor variations (e.g. `"Laptop HP 15"` vs `"Laptop HP 15-..."`) while avoiding false matches across different products. |

---

## Future Improvements

- [x] ~~Move `check_price_drops()` into a dedicated Celery async task~~ — done. `check_price_drops` is now a `@shared_task` dispatched with `.delay(search.id)` immediately after the scrape completes. It runs in the Celery worker process, retries up to 2 times on failure with a 30-second delay.
- [x] ~~Add a `/alerts` full page for browsing and filtering all historical alerts~~ — done. `AlertsPage.jsx` at `/alerts` with free-text search, platform filter, read/unread filter, and sort by newest / largest MAD drop / largest % drop.
- [ ] Support email notifications for significant price drops (e.g. > 20%).
- [ ] Allow users to set a minimum drop percentage threshold per keyword.
- [x] ~~Add WebSocket push for instant bell updates instead of 30-second polling~~ — done. `AlertConsumer` at `ws/alerts/` pushes `{ type: "new_alerts", unread_count: N }` to all open tabs for the user the moment the Celery task detects drops. `useAlerts` connects to this socket and calls `refresh()` on receipt.

