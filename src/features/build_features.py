"""Build behavioral features using only information known by each event time."""

import numpy as np
import pandas as pd


FEATURE_COLUMNS = [
    "Amount_To_Typical_Spend",
    "Tx_Count_Prior_24h",
    "Terminal_Prior_Tx_Count",
    "Terminal_Prior_Distinct_Customers",
    "Customer_Terminal_Prior_Count",
    "Is_Night",
    "Is_Weekend",
    "Auth_Soft_Decline",
    "Is_Ecommerce",
    "Is_Magstripe",
    "Is_Mobile_Wallet",
    "Region_Mismatch",
]


def build_features(transactions: pd.DataFrame, customers: pd.DataFrame) -> pd.DataFrame:
    """Return events sorted by time with lagged counts and customer context."""
    frame = transactions.sort_values(["Timestamp", "Transaction_ID"], kind="stable").copy()
    spend_map = customers.set_index("Customer_ID")["Typical_Spend"]
    frame["Typical_Spend"] = frame["Customer_ID"].map(spend_map)
    frame["Amount_To_Typical_Spend"] = frame["Amount"] / frame["Typical_Spend"].clip(lower=1)
    timestamps = pd.to_datetime(frame["Timestamp"])
    frame["Is_Night"] = ((timestamps.dt.hour < 5) | (timestamps.dt.hour >= 23)).astype(int)
    frame["Is_Weekend"] = (timestamps.dt.dayofweek >= 5).astype(int)
    frame["Auth_Soft_Decline"] = (frame["Auth_Result"] == "soft_decline").astype(int)
    frame["Is_Ecommerce"] = (frame["Channel"] == "ecommerce").astype(int)
    frame["Is_Magstripe"] = (frame["Auth_Type"] == "magstripe").astype(int)
    frame["Is_Mobile_Wallet"] = (frame["Channel"] == "mobile_wallet").astype(int)
    frame["Region_Mismatch"] = (frame["Customer_Region"] != frame["Merchant_Region"]).astype(int)

    # Histories are computed from the sorted event order. For the rolling
    # customer count, searchsorted finds the inclusive 24-hour lower bound and
    # the event's position excludes the current event while including earlier
    # events at the same timestamp, matching the original streaming logic.
    timestamp_values = timestamps.to_numpy(dtype="datetime64[ns]")
    prior_24h = np.zeros(len(frame), dtype=np.int64)
    for positions in frame.groupby("Customer_ID", sort=False).indices.values():
        customer_times = timestamp_values[positions]
        left_edge = np.searchsorted(
            customer_times,
            customer_times - np.timedelta64(24, "h"),
            side="left",
        )
        prior_24h[positions] = np.arange(len(positions)) - left_edge
    frame["Tx_Count_Prior_24h"] = prior_24h

    frame["Terminal_Prior_Tx_Count"] = frame.groupby(
        "Terminal_ID", sort=False
    ).cumcount()
    first_customer_at_terminal = ~frame.duplicated(
        ["Terminal_ID", "Customer_ID"], keep="first"
    )
    first_customer_indicator = first_customer_at_terminal.astype("int64")
    frame["Terminal_Prior_Distinct_Customers"] = (
        first_customer_indicator.groupby(frame["Terminal_ID"], sort=False).cumsum()
        - first_customer_indicator
    )
    frame["Customer_Terminal_Prior_Count"] = frame.groupby(
        ["Customer_ID", "Terminal_ID"], sort=False
    ).cumcount()
    frame[FEATURE_COLUMNS] = frame[FEATURE_COLUMNS].replace([np.inf, -np.inf], np.nan).fillna(0)
    return frame
