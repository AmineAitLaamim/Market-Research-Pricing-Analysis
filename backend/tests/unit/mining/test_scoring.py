import numpy as np
from mining.scoring import compute_deal_scores

def test_zero_range_guard():
    # All prices are the same, so range = 0
    clean_items = [
        {"price_mad": 100.0, "rating": 5.0},
        {"price_mad": 100.0, "rating": 4.0},
    ]
    anomaly_flags = np.array([False, False])
    
    scores = compute_deal_scores(clean_items, anomaly_flags)
    
    # price_score should be 0.5 for both
    # Item 0: 0.7 * 0.5 + 0.3 * (5.0/5.0) = 0.35 + 0.3 = 0.65
    # Item 1: 0.7 * 0.5 + 0.3 * (4.0/5.0) = 0.35 + 0.24 = 0.59
    assert len(scores) == 2
    assert abs(scores[0] - 0.65) < 1e-6
    assert abs(scores[1] - 0.59) < 1e-6

def test_anomaly_exclusion():
    # Item 1 is an anomaly
    clean_items = [
        {"price_mad": 100.0, "rating": 4.0},
        {"price_mad": 1000.0, "rating": 5.0},
    ]
    anomaly_flags = np.array([False, True])
    
    scores = compute_deal_scores(clean_items, anomaly_flags)
    
    assert len(scores) == 2
    # Item 0 is the only valid item, so max=min=100 -> range 0 -> price_score 0.5
    # deal_score = 0.7 * 0.5 + 0.3 * (4.0/5.0) = 0.35 + 0.24 = 0.59
    assert abs(scores[0] - 0.59) < 1e-6
    # Item 1 is anomalous -> None
    assert scores[1] is None

def test_null_rating_defaults_to_zero():
    clean_items = [
        {"price_mad": 100.0, "rating": None},
    ]
    anomaly_flags = np.array([False])
    
    scores = compute_deal_scores(clean_items, anomaly_flags)
    
    assert len(scores) == 1
    # price_score = 0.5, rating_score = 0.0
    # deal_score = 0.7 * 0.5 + 0.3 * 0 = 0.35
    assert abs(scores[0] - 0.35) < 1e-6

def test_formula_correctness():
    # Max price: 200, Min price: 100, Range: 100
    clean_items = [
        {"price_mad": 100.0, "rating": 5.0},   # price_score: (200-100)/100 = 1.0, rating_score: 1.0
        {"price_mad": 150.0, "rating": 2.5},   # price_score: (200-150)/100 = 0.5, rating_score: 0.5
        {"price_mad": 200.0, "rating": 0.0},   # price_score: (200-200)/100 = 0.0, rating_score: 0.0
    ]
    anomaly_flags = np.array([False, False, False])
    
    scores = compute_deal_scores(clean_items, anomaly_flags)
    
    assert len(scores) == 3
    # Item 0: 0.7 * 1.0 + 0.3 * 1.0 = 1.0
    assert abs(scores[0] - 1.0) < 1e-6
    # Item 1: 0.7 * 0.5 + 0.3 * 0.5 = 0.35 + 0.15 = 0.5
    assert abs(scores[1] - 0.5) < 1e-6
    # Item 2: 0.7 * 0.0 + 0.3 * 0.0 = 0.0
    assert abs(scores[2] - 0.0) < 1e-6
