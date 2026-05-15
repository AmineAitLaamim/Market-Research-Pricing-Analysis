from dataclasses import dataclass
from typing import List, TYPE_CHECKING
import numpy as np

from mining.association import mine_association_rules
from mining.preprocess import preprocess
from mining.pca import compute_pca

if TYPE_CHECKING:
    from apps.search.models import RawPrice, AnalysisResult


@dataclass
class PipelineResult:
    stats: dict
    best_deal_id: int | None
    analysis_results: List["AnalysisResult"]
    association_rules: list
    pca_points: list


def run_mining_pipeline(raw_prices: List["RawPrice"]) -> PipelineResult:
    """
    Run the full mining pipeline on scraped prices.
    Includes preprocessing, PCA for visualization, and placeholder for other mining tasks.
    """
    from apps.search.models import AnalysisResult, AssociationRule

    if not raw_prices:
        return PipelineResult({}, None, [], [], [])

    # 1. Preprocess data
    X_scaled_num, X_encoded, items = preprocess(raw_prices)

    if not items:
        return PipelineResult({}, None, [], [], [])

    # Combine numeric and categorical features for PCA
    X_combined = np.hstack([X_scaled_num, X_encoded.values])

    # 2. Compute PCA (dimensionality reduction for 2D visualization)
    n = len(items)
    pca_results = compute_pca(X_combined, n)

    # 3. Compute Deal Scores and Stats
    from mining.scoring import compute_deal_scores
    from mining.stats import compute_price_stats
    from mining.anomaly import isolation_forest_anomalies
    from mining.clustering import adaptive_dbscan
    
    # Run global anomaly detection
    prices_array = np.array([item['price_mad'] for item in items])
    anomaly_flags = isolation_forest_anomalies(prices_array, n)

    # Run DBSCAN Clustering
    dbscan_labels = adaptive_dbscan(X_combined, n)
    
    deal_scores = compute_deal_scores(items, anomaly_flags)
    stats_dict = compute_price_stats(items, anomaly_flags)
    mined_rules = mine_association_rules(
        X_encoded,
        min_support=0.03,
        min_confidence=0.5,
    )

    # 4. Build AnalysisResult objects
    # For now, we only populate PCA coordinates, Deal Score, Anomaly Flags, and DBSCAN labels.
    analysis_results = []
    association_rule_objects = []
    best_deal_id = None
    highest_score = -1.0

    for i, item in enumerate(items):
        ds = deal_scores[i]
        
        # Track the best deal
        if ds is not None and ds > highest_score:
            highest_score = ds
            best_deal_id = item["id"]

        analysis_results.append(
            AnalysisResult(
                raw_price_id=item["id"],
                pca_x=float(pca_results[i, 0]) if pca_results.shape[1] > 0 else None,
                pca_y=float(pca_results[i, 1]) if pca_results.shape[1] > 1 else None,
                deal_score=ds,
                is_anomaly=bool(anomaly_flags[i]),
                cluster_dbscan=int(dbscan_labels[i]) if dbscan_labels is not None else None
            )
        )

    if raw_prices:
        search = raw_prices[0].search
        association_rule_objects = [
            AssociationRule(
                search=search,
                antecedent=rule["antecedents"],
                consequent=rule["consequents"],
                support=rule["support"],
                confidence=rule["confidence"],
                lift=rule["lift"],
            )
            for rule in mined_rules
        ]

    return PipelineResult(
        stats=stats_dict,
        best_deal_id=best_deal_id,
        analysis_results=analysis_results,
        association_rules=association_rule_objects,
        pca_points=pca_results.tolist(),
    )


