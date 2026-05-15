import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from mining.anomaly import isolation_forest_anomalies

@patch("mining.anomaly.IsolationForest")
def test_isolation_forest_anomalies_n_5(mock_iforest):
    """Test n=5 contamination formula (-> 1/5 = 0.2)"""
    mock_model = MagicMock()
    mock_model.fit_predict.return_value = np.array([1, 1, 1, 1, -1])
    mock_iforest.return_value = mock_model

    prices = np.array([100, 105, 95, 102, 1000])
    n = 5
    
    result = isolation_forest_anomalies(prices, n)
    
    # Verify contamination is 0.2
    mock_iforest.assert_called_once_with(contamination=0.2, random_state=42)
    mock_model.fit_predict.assert_called_once()
    
    # Verify output is bool array of length n
    assert isinstance(result, np.ndarray)
    assert result.dtype == bool
    assert len(result) == n
    assert result[4] == True
    assert result[0] == False

@patch("mining.anomaly.IsolationForest")
def test_isolation_forest_anomalies_n_20(mock_iforest):
    """Test n=20 contamination formula (-> min(0.05, max(0.02, 5.0/20=0.25)) = 0.05)"""
    mock_model = MagicMock()
    mock_model.fit_predict.return_value = np.ones(20)
    mock_iforest.return_value = mock_model

    prices = np.random.rand(20) * 100
    n = 20
    
    result = isolation_forest_anomalies(prices, n)
    
    mock_iforest.assert_called_once_with(contamination=0.05, random_state=42)
    assert isinstance(result, np.ndarray)
    assert result.dtype == bool
    assert len(result) == n

@patch("mining.anomaly.IsolationForest")
def test_isolation_forest_anomalies_n_100(mock_iforest):
    """Test n=100 contamination formula (-> min(0.05, max(0.02, 5.0/100=0.05)) = 0.05)"""
    mock_model = MagicMock()
    mock_model.fit_predict.return_value = np.ones(100)
    mock_iforest.return_value = mock_model

    prices = np.random.rand(100) * 100
    n = 100
    
    result = isolation_forest_anomalies(prices, n)
    
    mock_iforest.assert_called_once_with(contamination=0.05, random_state=42)
    assert isinstance(result, np.ndarray)
    assert result.dtype == bool
    assert len(result) == n

@patch("mining.anomaly.IsolationForest")
def test_isolation_forest_anomalies_n_250(mock_iforest):
    """Test n=250 contamination formula (-> min(0.05, max(0.02, 5.0/250=0.02)) = 0.02)"""
    mock_model = MagicMock()
    mock_model.fit_predict.return_value = np.ones(250)
    mock_iforest.return_value = mock_model

    prices = np.random.rand(250) * 100
    n = 250
    
    result = isolation_forest_anomalies(prices, n)
    
    mock_iforest.assert_called_once_with(contamination=0.02, random_state=42)
    assert isinstance(result, np.ndarray)
    assert result.dtype == bool
    assert len(result) == n
