from dataclasses import dataclass
from typing import List, TYPE_CHECKING
import numpy as np

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
    from apps.search.models import AnalysisResult

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

    # 3. Build AnalysisResult objects
    # For now, we only populate PCA coordinates.
    analysis_results = []
    for i, item in enumerate(items):
        analysis_results.append(
            AnalysisResult(
                raw_price_id=item["id"],
                pca_x=float(pca_results[i, 0]),
                pca_y=float(pca_results[i, 1]),
            )
        )

    return PipelineResult(
        stats={},
        best_deal_id=None,
        analysis_results=analysis_results,
        association_rules=[],
        pca_points=pca_results.tolist(),
    )
