from __future__ import annotations

import logging
from typing import Any

import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules, fpgrowth


logger = logging.getLogger(__name__)


def mine_association_rules(
    X_encoded: pd.DataFrame,
    min_support: float = 0.05,
    min_confidence: float = 0.6,
) -> list[dict[str, Any]]:
    """
    Mine association rules from a one-hot encoded boolean DataFrame.

    Uses FP-Growth for the returned result set and Apriori as a verification pass.
    Returns an empty list when there are fewer than 30 rows.
    """
    if len(X_encoded) < 30:
        return []

    if X_encoded.empty:
        return []

    encoded = X_encoded.astype(bool)

    freq_items_fp = fpgrowth(
        encoded,
        min_support=min_support,
        use_colnames=True,
    )
    freq_items_ap = apriori(
        encoded,
        min_support=min_support,
        use_colnames=True,
    )

    logger.info(
        "Association mining itemset counts: fp_growth=%d apriori=%d",
        len(freq_items_fp),
        len(freq_items_ap),
    )

    if freq_items_fp.empty:
        return []

    rules_df = association_rules(
        freq_items_fp,
        metric="confidence",
        min_threshold=min_confidence,
    )

    if rules_df.empty:
        return []

    rules_df = rules_df.sort_values(
        by=["lift", "confidence", "support"],
        ascending=[False, False, False],
    )

    results: list[dict[str, Any]] = []
    for _, row in rules_df.iterrows():
        results.append(
            {
                "antecedents": sorted(str(item) for item in row["antecedents"]),
                "consequents": sorted(str(item) for item in row["consequents"]),
                "support": float(row["support"]),
                "confidence": float(row["confidence"]),
                "lift": float(row["lift"]),
            }
        )

    return results
