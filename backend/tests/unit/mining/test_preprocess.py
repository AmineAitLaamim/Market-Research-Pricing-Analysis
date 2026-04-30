from dataclasses import dataclass
from typing import Optional
import pytest
import numpy as np
import pandas as pd
from mining.preprocess import preprocess, build_preprocessing_pipeline

# Use dataclass to mock RawPrice from Django models without needing database
@dataclass
class MockRawPrice:
    id: int
    url: str
    price: str
    exchange_rate: float
    platform: str
    seller_rating: Optional[float] = None
    condition: Optional[str] = None

def test_pipeline_removes_duplicates_and_invalid_prices():
    """Ensure duplicate URLs are ignored (keep first), and zero/null prices dropped."""
    mock_data = [
        MockRawPrice(id=1, url="http://test.com/1", price="100.00", exchange_rate=1.0, platform="jumia"),
        # Duplicate URL:
        MockRawPrice(id=2, url="http://test.com/1", price="50.00", exchange_rate=1.0, platform="jumia"),
        # Zero price:
        MockRawPrice(id=3, url="http://test.com/2", price="0.00", exchange_rate=1.0, platform="jumia"),
        # Invalid price string:
        MockRawPrice(id=4, url="http://test.com/3", price="N/A", exchange_rate=1.0, platform="jumia"),
    ]
    
    X_scaled, X_encoded, items = preprocess(mock_data)
    
    assert len(items) == 1
    assert items[0]['id'] == 1
    assert X_scaled.shape[0] == 1
    assert X_encoded.shape[0] == 1

def test_pipeline_imputes_missing_values():
    """Ensure missing seller_rating and condition are imputed so no NaNs exist."""
    mock_data = [
        MockRawPrice(id=1, url="http://test.com/1", price="100.00", exchange_rate=1.0, platform="jumia", seller_rating=4.5, condition="new"),
        MockRawPrice(id=2, url="http://test.com/2", price="200.00", exchange_rate=1.0, platform="jumia", seller_rating=None, condition=None),
        MockRawPrice(id=3, url="http://test.com/3", price="300.00", exchange_rate=1.0, platform="jumia", seller_rating=3.0, condition="used"),
    ]
    
    X_scaled, X_encoded, items = preprocess(mock_data)
    
    assert len(items) == 3
    # Check that scaled data has no NaNs
    assert not np.isnan(X_scaled).any()
    # Check encoded data has no NaNs
    assert not X_encoded.isna().any().any()
    
    # Check boolean values in X_encoded
    assert all(X_encoded.dtypes == bool)

def test_pipeline_scales_prices_correctly():
    """Ensure price_mad calculation works and is scaled."""
    mock_data = [
        MockRawPrice(id=1, url="http://test.com/1", price="10.00", exchange_rate=10.0, platform="amazon"),  # 100 MAD
        MockRawPrice(id=2, url="http://test.com/2", price="200.00", exchange_rate=1.0, platform="jumia"),  # 200 MAD
        MockRawPrice(id=3, url="http://test.com/3", price="30.00", exchange_rate=10.0, platform="amazon"), # 300 MAD
    ]
    
    X_scaled, X_encoded, items = preprocess(mock_data)
    
    # Extract calculated MAD prices
    prices_mad = [item['price_mad'] for item in items]
    assert prices_mad == [100.0, 200.0, 300.0]
    
    # Since prices are linearly spaced, mean is 200, std is ~81.65 (population)
    # StandardScaler uses population std (ddof=0)
    assert np.isclose(X_scaled[0, 0], -1.22474487)
    assert np.isclose(X_scaled[1, 0], 0.0)
    assert np.isclose(X_scaled[2, 0], 1.22474487)

def test_empty_input():
    """Ensure empty list is handled safely."""
    X_scaled, X_encoded, items = preprocess([])
    
    assert items == []
    assert X_scaled.shape == (0,)
    assert X_encoded.empty
