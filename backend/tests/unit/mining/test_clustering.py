import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from mining.clustering import adaptive_dbscan

def test_adaptive_dbscan_n_less_than_10():
    """Verify n < 10 returns None"""
    X = np.random.rand(5, 2)
    assert adaptive_dbscan(X, 5) is None
    assert adaptive_dbscan(X, 9) is None

@patch("mining.clustering.NearestNeighbors")
@patch("mining.clustering.DBSCAN")
def test_adaptive_dbscan_min_samples_formula(mock_dbscan_class, mock_nn_class):
    """Verify min_samples formula max(3, int(0.05 * n)) is used"""
    # Mock NearestNeighbors
    mock_nn = MagicMock()
    # distances should be shape (n, min_samples)
    mock_nn.kneighbors.return_value = (np.zeros((100, 5)), np.zeros((100, 5)))
    mock_nn_class.return_value = mock_nn

    # Mock DBSCAN
    mock_dbscan = MagicMock()
    mock_dbscan.fit_predict.return_value = np.zeros(100)
    mock_dbscan_class.return_value = mock_dbscan

    # Test n = 100 -> min_samples = max(3, int(100 * 0.05)) = 5
    X = np.random.rand(100, 2)
    adaptive_dbscan(X, 100)
    mock_nn_class.assert_called_with(n_neighbors=5)
    
    # Test n = 20 -> min_samples = max(3, int(20 * 0.05)) = max(3, 1) = 3
    mock_nn.kneighbors.return_value = (np.zeros((20, 3)), np.zeros((20, 3)))
    X2 = np.random.rand(20, 2)
    adaptive_dbscan(X2, 20)
    mock_nn_class.assert_called_with(n_neighbors=3)

def test_adaptive_dbscan_noise_points():
    """Verify noise points labeled -1 using a synthetic dataset"""
    # To make sure results are reproducible
    np.random.seed(42)
    
    # Create two tight clusters
    cluster1 = np.random.normal(loc=[0, 0], scale=0.1, size=(20, 2))
    cluster2 = np.random.normal(loc=[5, 5], scale=0.1, size=(20, 2))
    # Create one clear outlier (noise)
    outlier = np.array([[100, -100]])
    
    X = np.vstack([cluster1, cluster2, outlier])
    n = len(X)
    
    labels = adaptive_dbscan(X, n)
    
    # Check that it didn't return None
    assert labels is not None
    # Check shape
    assert len(labels) == n
    
    # The outlier is clearly far away and should be labeled -1
    assert labels[-1] == -1
    
    # Check that at least some points are clustered (label >= 0)
    assert np.any(labels[:-1] >= 0)
