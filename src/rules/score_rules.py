"""A readable baseline risk score; each signal contributes a visible reason."""

import numpy as np
import pandas as pd


def score_rules(features: pd.DataFrame) -> pd.DataFrame:
    scored = features.copy()
    score = pd.Series(0, index=scored.index, dtype="int64")
    reasons = pd.Series("", index=scored.index, dtype="object")

    def add(mask, points, label):
        nonlocal score
        matched = mask.fillna(False).to_numpy(dtype=bool)
        score += pd.Series(matched.astype("int64") * points, index=scored.index)
        existing = reasons.loc[matched].to_numpy(dtype=object)
        reasons.loc[matched] = np.where(existing == "", label, existing + ";" + label)

    add(scored["Amount_To_Typical_Spend"] >= 3, 30, "amount_vs_profile")
    add(scored["Amount_To_Typical_Spend"] >= 6, 25, "extreme_amount_vs_profile")
    add(scored["Tx_Count_Prior_24h"] >= 5, 25, "customer_velocity")
    add(scored["Tx_Count_Prior_24h"] >= 10, 20, "high_customer_velocity")
    add(scored["Customer_Terminal_Prior_Count"] == 0, 15, "new_customer_terminal_pair")
    add(scored["Terminal_Prior_Distinct_Customers"] >= 8, 18, "terminal_customer_network_burst")
    add(
        (scored["Amount"] <= 5) & (scored["Tx_Count_Prior_24h"] >= 2),
        35,
        "low_value_testing_velocity",
    )
    add(
        (scored["Is_Ecommerce"] == 1)
        & (scored["Is_Magstripe"] == 1)
        & (scored["Is_Night"] == 1),
        20,
        "ecommerce_authentication_shift",
    )
    add(scored["Is_Night"] == 1, 8, "night_activity")
    add(scored["Auth_Soft_Decline"] == 1, 8, "authentication_soft_decline")
    add(scored["Region_Mismatch"] == 1, 12, "home_region_mismatch")
    scored["Rule_Score"] = score.clip(upper=100)
    scored["Rule_Reasons"] = reasons
    return scored
