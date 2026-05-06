import numpy as np
import pytest
from backend.mining.pca import compute_pca

def test_compute_pca_small_n():
    n = 5
    X = np.random.rand(n, 4)
    result = compute_pca(X, n)
    assert result.shape == (n, 2)
    assert np.all(result == 0)

def test_compute_pca_enough_n():
    n = 15
    X = np.random.rand(n, 4)
    result = compute_pca(X, n)
    assert result.shape == (n, 2)
    # Check that it's not all zeros
    assert not np.all(result == 0)

def test_compute_pca_reproducibility():
    n = 15
    X = np.random.rand(n, 4)
    result1 = compute_pca(X, n)
    result2 = compute_pca(X, n)
    np.testing.assert_array_almost_equal(result1, result2)
