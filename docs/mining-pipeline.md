# Data Mining Pipeline

This document explains the "Mining" stage of the search process, located in `backend/mining/`.

---

## Purpose

Raw scraped data from various platforms is often messy, inconsistent in currency, and contains noise. The mining pipeline transforms this raw data into structured insights that the frontend can visualize.

---

## The Pipeline Flow

The pipeline is orchestrated in `backend/mining/pipeline.py` via the `run_mining_pipeline(data)` function.

### 1. Preprocessing (`preprocess.py`)
- **Cleaning:** Removes HTML tags (if any), trims whitespace, and normalizes text to lowercase.
- **Numeric Extraction:** Extracts numerical values from price strings (e.g., "1.500 MAD" -> `1500.0`).
- **Currency Normalization:** Converts prices from various sources (EUR, USD) to MAD using current exchange rates (via `exchange_rate.py`).
- **Feature Engineering:** Creates derived features like `title_length`, `is_promotion`, or `platform_id`.

### 2. Dimensionality Reduction (PCA) (`pca.py`)
To visualize hundreds of products in a 2D scatter plot, we use **Principal Component Analysis (PCA)**.
- **Input:** A matrix of product features (Price, Platform, Normalized Title TF-IDF).
- **Process:** 
    1. Standardize features using `StandardScaler`.
    2. Apply PCA to reduce features to 2 components.
- **Output:** `x` and `y` coordinates for each product, which the frontend's `ClusterScatter` component renders.

### 3. Clustering (`clustering.py`)
- Uses **K-Means** to group similar products together.
- This helps users see "market segments" (e.g., high-end vs. budget variants of the same product).

### 4. Scoring & Best Deal Detection (`scoring.py`)
- Calculates a composite `deal_score` for non-anomalous items.
- **Formula:** `0.7 * price_score + 0.3 * rating_score`
    - `price_score = (max_price - price) / price_range`. If `price_range == 0`, defaults to `0.5`.
    - `rating_score = rating / 5.0`. Missing ratings (including `None` or `np.nan` from the scraper) default to `0.0` safely via a `math.isnan` guard to prevent JSON serialization crashes on the backend.
- Items flagged as anomalous receive a `deal_score` of `None`.
- The item with the highest non-null `deal_score` is flagged as the "Best Deal".

### 5. Price Statistics (`stats.py`)
- Computes comprehensive statistical metrics across all non-anomalous items.
- Calculates: `count`, `mean`, `median`, `std`, `variance`, `min`, `max`, `q1` (25th percentile), `q3` (75th percentile), and `iqr`.
- This data is directly used to render the frontend's Stats Cards grid.

---

## Integration with Celery

The mining pipeline is the second stage of the `run_search_pipeline` task:

```python
# backend/apps/search/tasks.py

@shared_task
def run_search_pipeline(query, user_id):
    # 1. Scrape
    raw_data = scrape_all(query)
    
    # 2. Mine
    analyzed_data = run_mining_pipeline(raw_data)
    
    # 3. Save
    save_results(analyzed_data, user_id)
```

---

## Key Symbols

- `MiningPipeline`: The main class managing the stages.
- `DataCleaner`: Handles regex-based cleaning of titles and prices.
- `PCARunner`: Wrapper around scikit-learn's PCA.
