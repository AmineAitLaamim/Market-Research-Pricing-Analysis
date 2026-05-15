# API Reference

This document provides a detailed reference for the Market Research & Pricing Analysis REST API and WebSocket protocols.

---

## Base URL
All REST API endpoints are relative to:
`http://<your-domain>/api/`

---

## Authentication
The API uses JWT (JSON Web Tokens). Most endpoints require the `Authorization` header.

**Header Format:**
`Authorization: Bearer <your_access_token>`

### Auth Endpoints
- `POST auth/register/`: Create a new user account.
- `POST auth/login/`: Obtain access and refresh tokens.
- `POST auth/logout/`: Revoke tokens.

---

## Search API

### `POST search/`
Initiates a new scraping and analysis task.

**Request Body:**
```json
{
  "query": "iphone 15",
  "platforms": ["avito", "jumia"]
}
```

**Response (201 Created):**
```json
{
  "id": 123,
  "query": "iphone 15",
  "platforms": ["avito", "jumia"],
  "status": "pending"
}
```
*Note: If an identical pending/processing search exists, it returns the existing search with `200 OK`.*

### `GET search/<id>/status/`
Check the progress of a specific search.

**Response:**
```json
{
  "id": 123,
  "status": "processing",
  "progress": 45,
  "message": "Scraping Jumia..."
}
```

### `GET search/<id>/results/`
Fetch the structured results for a completed search.

**Query Parameters:**
- `page`: Page number (default: 1).
- `platform`: Filter by platform (e.g., `avito`).
- `is_anomaly`: Filter by anomalies (`true`).
- `ordering`: Sort field (e.g., `price`, `-price`, `-analysis__deal_score`).

**Response:**
```json
{
  "count": 150,
  "next": "...",
  "previous": null,
  "results": [...],
  "meta": {
    "stats": { "avg": 8500, "min": 7200, "max": 12000 },
    "best_deal": { ... }
  }
}
```

### `GET search/<id>/pca/`
Fetch 2D visualization coordinates for the cluster map.

**Response (Array):**
```json
[
  {
    "id": 45,
    "title": "...",
    "pca_x": 1.23,
    "pca_y": -0.45,
    "cluster_kmeans": 1,
    "is_anomaly": false
  }
]
```

### `GET search/<id>/rules/`
Fetch association rules for a completed search.

By default, this endpoint returns the rules already persisted during the mining pipeline. It also supports on-demand re-mining when thresholds are provided.

**Query Parameters:**
- `min_support`: Optional float in `(0, 1]`. When present, the backend reruns association rule mining for this search with the provided support threshold.
- `min_confidence`: Optional float in `(0, 1]`. Defaults to `0.5` for on-demand mining when omitted.

**Behavior:**
- If neither parameter is provided, the endpoint returns saved rules from the database.
- If `min_support` or `min_confidence` is provided, the backend preprocesses the search's raw prices and reruns FP-Growth association mining on demand.
- If the encoded dataset contains fewer than `30` rows, the response is an empty array.

**Response (Array):**
```json
[
  {
    "antecedent": ["platform_jumia", "condition_new"],
    "consequent": ["price_bucket_mid"],
    "support": 0.084,
    "confidence": 0.71,
    "lift": 1.64
  }
]
```

---

## History & Analytics

### `GET search/analytics/`
Global dashboard metrics for the authenticated user.
- **Summary:** Total searches, total items, most searched keyword.
- **Price Trends:** Average price over time grouped by platform.
- **Top Cheap Products:** 5 cheapest items across all searches.

### `GET search/compare/?a={id1}&b={id2}`
Compares two searches with the same query conducted at different times.
- Returns `matched`, `new_items`, and `gone_items`.
- Provides summary delta (e.g., `avg_price_a` vs `avg_price_b`).

---

## Price Alerts

### `GET search/alerts/`
List all price drop notifications for the user.

### `PATCH search/alerts/<id>/read/`
Mark a specific alert as read.

### `PATCH search/alerts/read-all/`
Mark all unread alerts as read.

---

## WebSockets (Real-time)

### Search Progress WebSocket
**URL:** `ws://<your-domain>/ws/search/<task_id>/`

The frontend should connect to this socket immediately after creating a search. Authentication is not strictly required for this specific socket as the `task_id` acts as a unique token.

**Messages Received:**
```json
{
  "type": "progress_update",
  "status": "processing",
  "progress": 60,
  "message": "Analyzing data..."
}
```

### Price Alerts WebSocket
**URL:** `ws://<your-domain>/ws/alerts/?token=<jwt_token>`

Provides real-time notifications when a background task detects a price drop.
**Authentication:** This endpoint requires the user's JWT access token to be passed in the `token` query parameter, as native WebSocket APIs do not support setting custom `Authorization` headers. The backend ASGI middleware extracts this token to authenticate the connection.

**Messages Received:**
```json
{
  "type": "alert_message",
  "data": {
    "type": "new_alerts",
    "unread_count": 3
  }
}
```

```json
{
  "type": "search_complete",
  "status": "completed",
  "task_id": 123
}
```

---

## Exporting Data

### `GET export/csv/<id>/`
Download the results of search `<id>` as a CSV file.
- Requires authentication.
- Returns a `text/csv` attachment.

---

## Analytics API

### `GET analytics/products/?q={query}&limit={limit}`
Search the local database of previously scraped products.
- `q`: Search keyword.
- `limit`: Maximum number of results to return (default: 50).

### `GET analytics/top-drops/`
Get a list of the largest recent price drops across all user searches.

### `GET analytics/product-history/?url={url}`
Get the historical price trend for a specific product.

---

## Core Data Schemas

### `Search` Object
Represents a scraping job.
- `id` (Integer): Unique identifier.
- `query` (String): The search keyword.
- `platforms` (Array of Strings): Platforms searched (e.g., `["avito", "jumia", "marjane"]`).
- `status` (String): `pending`, `processing`, `completed`, or `failed`.
- `created_at` (Datetime): When the search was initiated.

### `RawPrice` Object
Represents a single product result from a scrape.
- `id` (Integer): Unique identifier.
- `platform` (String): Source platform.
- `title` (String): Product title.
- `price` (Decimal): Raw price on the platform.
- `currency` (String): Original currency.
- `exchange_rate` (Float): Rate used to convert to MAD.
- `url` (String): Link to the product.
- `image_url` (String, nullable): Product image.
- `seller_rating` (Float, nullable): Rating out of 5.0.
- `condition` (String, nullable): Item condition (`new`, `used`, etc.).
- `scraped_at` (Datetime): Timestamp of data extraction.

### `PriceAlert` Object
Represents a notification for a price drop.
- `id` (Integer): Unique identifier.
- `product_title` (String): Title of the product.
- `old_price` (Decimal): Previous price.
- `new_price` (Decimal): New, lower price.
- `drop_amount` (Decimal): Absolute difference.
- `drop_percent` (Decimal): Percentage drop.
- `platform` (String): Source platform.
- `product_url` (String): Link to the product.
- `search_query` (String): The search that triggered this alert.
- `is_read` (Boolean): Whether the user has acknowledged the alert.
- `created_at` (Datetime): When the drop was detected.

### `AssociationRule` Object
Represents one mined rule shown in the results page.
- `antecedent` (Array of Strings): Left-hand side itemset.
- `consequent` (Array of Strings): Right-hand side itemset.
- `support` (Float): Fraction of rows containing the full rule itemset.
- `confidence` (Float): Conditional probability of the consequent given the antecedent.
- `lift` (Float): Strength of association relative to independence.
