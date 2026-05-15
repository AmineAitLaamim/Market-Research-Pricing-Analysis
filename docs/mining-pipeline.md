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
- **Feature Engineering:** Creates derived features used by both scoring and association mining, including `title_length`, `price_bucket`, `rating_bucket`, and `title_length_bucket`.

### 2. Dimensionality Reduction (PCA) (`pca.py`)
To visualize hundreds of products in a 2D scatter plot, we use **Principal Component Analysis (PCA)**.
- **Input:** A matrix of product features combining scaled numeric features (Price, Rating) and one-hot encoded categorical features (Platform, Condition).
- **Process:** 
    1. Standardize features using Scikit-Learn's `StandardScaler` and `SimpleImputer`.
    2. Encode categorical fields with `OneHotEncoder`.
    3. Combine matrices into a single dataset.
    4. Apply PCA to reduce features to exactly 2 components (`pca_x` and `pca_y`).
- **Output:** Coordinates for each product, allowing the frontend's `ClusterScatter` component to render a 2D topographical map of the market.

### 3. Global Anomaly Detection (`anomaly.py`)
- Uses the **Isolation Forest** algorithm from Scikit-Learn to detect outliers (e.g., highly mispriced or fake listings) across the entire scraped dataset.
- **Adaptive Contamination:** The expected proportion of anomalies ("contamination") scales dynamically based on the dataset size (`n`).
  - For small datasets (`n < 20`), it is highly sensitive (`1.0 / n`).
  - For larger datasets, it scales smoothly: `min(0.05, max(0.02, 5.0 / n))`, ensuring the proportion remains between 2% and 5%.
  - It handles edge cases by strictly capping contamination at `0.5` to adhere to the algorithm's constraints.
- **Execution:** Runs consistently regardless of the dataset size (no arbitrary minimum `N` guards).
- **Output:** A boolean mapping where `True` marks an anomaly. These items are subsequently excluded from "Best Deal" scoring and statistical aggregations to prevent skewing.

### 4. Clustering (`clustering.py`)
- Uses **Adaptive DBSCAN (Density-Based Spatial Clustering of Applications with Noise)** to group dense regions of products together.
- **Dynamic Parameters:** 
  - `min_samples` is dynamically scaled based on the dataset size: `max(3, int(0.05 * n))`.
  - `eps` is auto-computed using a K-Distance graph by selecting the 90th percentile of distances to the K-th nearest neighbor.
- **Execution:** Runs only for datasets with at least 10 items to prevent mathematically unsound clusters.
- **Output:** Assigns a cluster ID to each item. Items that fall outside of dense regions are labeled as `-1` (noise) and saved as `cluster_dbscan` in the database.

### 5. Scoring & Best Deal Detection (`scoring.py`)
- Calculates a composite `deal_score` for non-anomalous items.
- **Formula:** `0.7 * price_score + 0.3 * rating_score`
    - `price_score = (max_price - price) / price_range`. If `price_range == 0`, defaults to `0.5`.
    - `rating_score = rating / 5.0`. Missing ratings (including `None` or `np.nan` from the scraper) default to `0.0` safely via a `math.isnan` guard to prevent JSON serialization crashes on the backend.
- Items flagged as anomalous receive a `deal_score` of `None`.
- The item with the highest non-null `deal_score` is flagged as the "Best Deal".

### 6. Price Statistics (`stats.py`)
- Computes comprehensive statistical metrics across all non-anomalous items.
- Calculates: `count`, `mean`, `median`, `std`, `variance`, `min`, `max`, `q1` (25th percentile), `q3` (75th percentile), and `iqr`.
- This data is directly used to render the frontend's Stats Cards grid.

### 7. Association Rule Mining (`association.py`)
- Uses `mlxtend` to mine item associations from the one-hot encoded categorical dataset returned by `preprocess.py`.
- **Guard:** The miner returns `[]` when `len(X_encoded) < 30`.
- **Primary algorithm:** FP-Growth via `fpgrowth(X_encoded, min_support=..., use_colnames=True)`.
- **Rule generation:** `association_rules(freq_items, metric="confidence", min_threshold=min_confidence)`.
- **Verification:** Apriori is run with the same parameters and the FP-Growth vs Apriori frequent-itemset counts are compared in logs.
- **Default pipeline thresholds:** The search pipeline persists rules using `min_support=0.03` and `min_confidence=0.5`.
- **Dynamic thresholds:** The API can rerun association mining on demand for a saved search when the frontend passes a custom `min_support` or `min_confidence`.
- **Output shape:** Each rule is normalized to:
  - `antecedents`
  - `consequents`
  - `support`
  - `confidence`
  - `lift`

### 8. Pipeline Result Output
The final step of the pipeline constructs a structured `PipelineResult` object containing:
- `stats`: The statistical dictionary.
- `best_deal_id`: The database ID of the best product found.
- `analysis_results`: A list of analysis objects mapping `pca_x`, `pca_y`, `deal_score`, and `is_anomaly` directly back to the `RawPrice` database records.
- `association_rules`: A list of `AssociationRule` model objects ready to persist.
- `pca_points`: The raw 2D array of coordinates.

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

## Key Modules

- `pipeline.py`: Orchestrates preprocessing, PCA, anomaly detection, clustering, scoring, stats, and association rules.
- `preprocess.py`: Produces numeric matrices, encoded categorical features, and normalized item dictionaries.
- `association.py`: Encapsulates FP-Growth, Apriori verification, and rule serialization.
- `pca.py`: Wrapper around scikit-learn PCA for 2D visualization coordinates.
