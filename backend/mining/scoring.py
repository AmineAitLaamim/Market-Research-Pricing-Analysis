import numpy as np

def compute_deal_scores(clean_items: list[dict], anomaly_flags: np.ndarray) -> list[float | None]:
    """
    Compute a composite deal score for each non-anomalous item.
    Returns a list of scores aligned with clean_items.
    Anomalous items receive a score of None.
    
    The score is calculated as:
    deal_score = 0.7 * price_score + 0.3 * rating_score
    """
    if not clean_items:
        return []

    # Identify non-anomalous items and extract their prices
    valid_prices = []
    for i, item in enumerate(clean_items):
        if not anomaly_flags[i]:
            valid_prices.append(item['price_mad'])

    # Determine max and min prices among non-anomalous items
    if valid_prices:
        max_price = max(valid_prices)
        min_price = min(valid_prices)
        price_range = max_price - min_price
    else:
        max_price = 0
        min_price = 0
        price_range = 0

    scores = []
    for i, item in enumerate(clean_items):
        if anomaly_flags[i]:
            scores.append(None)
            continue

        # Price Score
        price = item['price_mad']
        if price_range == 0:
            price_score = 0.5
        else:
            price_score = (max_price - price) / price_range

        # Rating Score
        rating = item.get('rating')
        if rating is None:
            rating = item.get('seller_rating')
        if rating is None:
            rating = 0.0
            
        rating_score = float(rating) / 5.0

        # Composite Deal Score
        deal_score = 0.7 * price_score + 0.3 * rating_score
        scores.append(deal_score)

    return scores
