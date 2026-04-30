import numpy as np
import pytest
from mining.pca import compute_pca

def test_compute_pca_n_ge_10():
    # Setup: n=12 samples, 5 features
    n = 12
    X = np.random.rand(n, 5)
    
    result = compute_pca(X, n)
    
    # Assertions
    assert result.shape == (n, 2)
    assert result.dtype == np.float64
    # Check that it's not all zeros (unless extremely unlikely)
    assert not np.all(result == 0)

def test_compute_pca_n_lt_10():
    # Setup: n=5 samples, 5 features
    n = 5
    X = np.random.rand(n, 5)
    
    result = compute_pca(X, n)
    
    # Assertions
    assert result.shape == (n, 2)
    assert result.dtype == np.float64
    assert np.all(result == 0)

def test_compute_pca_output_type():
    n = 10
    X = np.random.rand(n, 3)
    result = compute_pca(X, n)
    assert isinstance(result, np.ndarray)
