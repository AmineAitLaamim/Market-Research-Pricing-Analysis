import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors
from typing import Optional

def adaptive_dbscan(X_scaled: np.ndarray, n: int) -> Optional[np.ndarray]:
    """
    Adaptive DBSCAN clustering.
    eps is auto-computed from the 90th percentile of k-distances.
    Returns array of labels where -1 indicates noise.
    """
    if n < 10:
        return None

    min_samples = max(3, int(0.05 * n))
    
    # Compute eps using k-distance graph
    nn = NearestNeighbors(n_neighbors=min_samples)
    nn.fit(X_scaled)
    distances, _ = nn.kneighbors(X_scaled)
    
    # Get the distances to the k-th nearest neighbor (which is the last column)
    k_distances = distances[:, -1]
    
    # Calculate eps as the 75th percentile of these distances (tighter clusters)
    eps = float(np.percentile(k_distances, 75))
    
    # If the dataset contains many exact duplicates, k_distances might be 0.0!
    # A density radius of 0.0 will throw almost the entire dataset into noise (-1).
    if eps <= 0.0:
        eps = float(np.percentile(k_distances, 85))
        if eps <= 0.0:
            eps = 0.25 # Safe default fallback for StandardScaled data

    # Fit DBSCAN
    dbscan = DBSCAN(eps=eps, min_samples=min_samples)
    labels = dbscan.fit_predict(X_scaled)
    
    return labels
