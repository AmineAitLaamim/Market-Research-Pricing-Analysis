import numpy as np
from sklearn.decomposition import PCA

def compute_pca(X_scaled: np.ndarray, n: int) -> np.ndarray:
    """
    Reduce feature space to 2 principal components for 2D scatter visualization.
    Only runs if n >= 10.
    
    Args:
        X_scaled: Scaled feature matrix of shape (n, features)
        n: Number of samples
        
    Returns:
        np.ndarray of shape (n, 2)
    """
    if n < 10:
        return np.zeros((n, 2), dtype=np.float64)
    
    pca = PCA(n_components=2, random_state=42)
    return pca.fit_transform(X_scaled)
