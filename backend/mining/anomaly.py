import numpy as np
from sklearn.ensemble import IsolationForest

def isolation_forest_anomalies(prices: np.ndarray, n: int) -> np.ndarray:
    """
    Global anomaly detection with adaptive contamination using Isolation Forest.
    Returns a boolean array where True indicates an anomaly.
    """
    contamination = 1.0 / n if n < 20 else min(0.05, max(0.02, 5.0 / n))
    
    # Scikit-learn's IsolationForest contamination parameter must be in the range (0.0, 0.5].
    if contamination > 0.5:
        contamination = 0.5

    model = IsolationForest(contamination=contamination, random_state=42)
    predictions = model.fit_predict(prices.reshape(-1, 1))
    
    return predictions == -1
