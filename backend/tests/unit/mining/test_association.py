import pandas as pd

from mining.association import mine_association_rules


def test_mine_association_rules_returns_empty_when_n_less_than_30():
    X_encoded = pd.DataFrame(
        {
            "platform_jumia": [True, False, True],
            "condition_new": [True, True, False],
        }
    )

    assert mine_association_rules(X_encoded) == []


def test_mine_association_rules_finds_known_pattern():
    rows = []

    for _ in range(20):
        rows.append(
            {
                "platform_jumia": True,
                "condition_new": True,
                "condition_used": False,
                "platform_avito": False,
            }
        )

    for _ in range(10):
        rows.append(
            {
                "platform_jumia": True,
                "condition_new": False,
                "condition_used": True,
                "platform_avito": False,
            }
        )

    for _ in range(10):
        rows.append(
            {
                "platform_jumia": False,
                "condition_new": False,
                "condition_used": True,
                "platform_avito": True,
            }
        )

    X_encoded = pd.DataFrame(rows).astype(bool)

    rules = mine_association_rules(
        X_encoded,
        min_support=0.2,
        min_confidence=0.6,
    )

    assert rules
    assert any(
        rule["antecedents"] == ["condition_new"]
        and rule["consequents"] == ["platform_jumia"]
        for rule in rules
    )


def test_mine_association_rules_returns_required_rule_keys():
    rows = []

    for _ in range(18):
        rows.append(
            {
                "platform_jumia": True,
                "condition_new": True,
                "category_phone": True,
            }
        )

    for _ in range(12):
        rows.append(
            {
                "platform_jumia": False,
                "condition_new": False,
                "category_phone": True,
            }
        )

    X_encoded = pd.DataFrame(rows).astype(bool)

    rules = mine_association_rules(
        X_encoded,
        min_support=0.2,
        min_confidence=0.6,
    )

    assert rules
    assert set(rules[0].keys()) == {
        "antecedents",
        "consequents",
        "support",
        "confidence",
        "lift",
    }
