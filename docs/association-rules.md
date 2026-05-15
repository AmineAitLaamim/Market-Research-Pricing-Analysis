# Association Rules

This document describes how association rules are mined, persisted, exposed by the API, and rendered in the frontend.

---

## Purpose

Association rules help surface recurring relationships between categorical product attributes in a search result set.

Examples:
- products from one platform appearing frequently in a given price bucket
- used items being associated with lower price ranges
- short or long titles correlating with a category of offers

The project uses these rules as an exploratory insight layer in the search results page.

---

## Mining Implementation

Association rule mining is implemented in:

- `backend/mining/association.py`
- `backend/mining/preprocess.py`
- `backend/mining/pipeline.py`

### Dataset

The miner works on the one-hot encoded categorical matrix returned by `preprocess(raw_prices)`.

The encoded dataset includes categorical and derived bucket features such as:
- `platform`
- `condition`
- `price_bucket`
- `rating_bucket`
- `title_length_bucket`

### Guard Condition

The miner does not run when the encoded dataset is too small:

- if `len(X_encoded) < 30`, it returns `[]`

This prevents unstable and misleading rules on very small searches.

### Algorithms

The primary algorithm is FP-Growth:

```python
fpgrowth(X_encoded, min_support=min_support, use_colnames=True)
```

Rules are generated with:

```python
association_rules(freq_items, metric="confidence", min_threshold=min_confidence)
```

Apriori is also run with the same parameters for verification. The backend compares frequent-itemset counts from FP-Growth and Apriori in logs.

### Default Persisted Thresholds

When a search finishes, the mining pipeline persists rules using:

- `min_support=0.03`
- `min_confidence=0.5`

These defaults are used for the saved rule set attached to the completed search.

---

## API Behavior

Association rules are exposed at:

- `GET /api/search/<id>/rules/`

### Default Mode

If no threshold parameters are passed, the endpoint returns the rules already saved in the database for that search.

### Dynamic Threshold Mode

The endpoint also supports on-demand re-mining:

- `min_support`
- `min_confidence`

Example:

```text
/api/search/128/rules/?min_support=0.01&min_confidence=0.5
```

When either parameter is provided, the backend:
1. loads raw prices for that search
2. reruns preprocessing
3. reruns association mining with the requested thresholds
4. returns the recalculated rules directly in the response

This allows the frontend to explore different support thresholds without rerunning the whole search pipeline.

### Response Shape

Each rule is returned as:

```json
{
  "antecedent": ["platform_jumia"],
  "consequent": ["price_bucket_mid"],
  "support": 0.084,
  "confidence": 0.71,
  "lift": 1.64
}
```

---

## Frontend Behavior

The rules UI is implemented in:

- `frontend/src/components/AssociationRules.jsx`
- `frontend/src/pages/ResultsPage.jsx`
- `frontend/src/api/search.js`

### Layout

- the PCA section and the Association Rules section are stacked vertically
- the Association Rules card uses full width
- the rules table is rendered inside a scrollable window
- the table header stays sticky while scrolling

### Threshold Controls

Users can adjust minimum support with:
- a range slider
- a numeric input
- quick-pick buttons

Current support selection range:
- minimum: `0.1%`
- maximum: `50%`
- step: `0.1%`

The frontend converts the chosen percentage to a decimal before calling the API.

Example:
- `3%` in the UI becomes `min_support=0.03`

### Empty States

The rules card distinguishes between:
- fewer than `30` results: not enough data
- `30+` results but no qualifying rules: no rules met the thresholds

---

## Persistence Model

Persisted rules are stored in the `AssociationRule` model with:

- `search`
- `antecedent`
- `consequent`
- `support`
- `confidence`
- `lift`

This gives each completed search a saved baseline rule set while still allowing threshold-based recomputation through the API.

---

## Testing

Unit coverage for the miner is in:

- `backend/tests/unit/mining/test_association.py`

Covered cases:
- datasets with fewer than `30` rows return `[]`
- known boolean patterns produce at least one rule
- returned rules include all required keys

---

## Notes

- Dynamic threshold requests recompute rules from the raw search data and do not overwrite the persisted baseline rules.
- Lowering support usually increases the number of returned rules.
- If a search still returns no rules at low support, the categorical combinations in that search may simply not be strong enough under the confidence threshold.
