import numpy as np

def compute_price_stats(items: list[dict], anomaly_flags: np.ndarray) -> dict:
    """
    Computes statistical metrics on the price_mad field of non-anomalous items.
    Returns: count, mean, median, std, variance, min, max, q1, q3, iqr
    """
    valid_prices = [item['price_mad'] for i, item in enumerate(items) if not anomaly_flags[i]]
    
    if not valid_prices:
        return {
            "count": 0, "mean": None, "median": None, "std": None,
            "variance": None, "min": None, "max": None,
            "q1": None, "q3": None, "iqr": None
        }
        
    prices = np.array(valid_prices)
    
    q1 = float(np.percentile(prices, 25))
    q3 = float(np.percentile(prices, 75))
    
    return {
        "count": len(prices),
        "mean": float(np.mean(prices)),
        "median": float(np.median(prices)),
        "std": float(np.std(prices)),
        "variance": float(np.var(prices)),
        "min": float(np.min(prices)),
        "max": float(np.max(prices)),
        "q1": q1,
        "q3": q3,
        "iqr": q1 - q3 if q1 > q3 else q3 - q1 # standard IQR is Q3 - Q1
    }
