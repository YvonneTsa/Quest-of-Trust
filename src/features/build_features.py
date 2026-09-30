"""Build behavioral features using only information known by each event time."""

from collections import defaultdict, deque

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

    # Histories are updated only after the current row's features are calculated.
    customer_times = defaultdict(deque)
    terminal_counts = defaultdict(int)
    terminal_customers = defaultdict(set)
    pair_counts = defaultdict(int)
    prior_24h, terminal_prior, terminal_customer_prior, pair_prior = [], [], [], []
    for row in frame.itertuples(index=False):
        now = pd.Timestamp(row.Timestamp)
        customer_history = customer_times[row.Customer_ID]
        cutoff = now - pd.Timedelta(hours=24)
        while customer_history and customer_history[0] < cutoff:
            customer_history.popleft()
        prior_24h.append(len(customer_history))
        terminal_prior.append(terminal_counts[row.Terminal_ID])
        terminal_customer_prior.append(len(terminal_customers[row.Terminal_ID]))
        pair_key = (row.Customer_ID, row.Terminal_ID)
        pair_prior.append(pair_counts[pair_key])
        customer_history.append(now)
        terminal_counts[row.Terminal_ID] += 1
        terminal_customers[row.Terminal_ID].add(row.Customer_ID)
        pair_counts[pair_key] += 1

    frame["Tx_Count_Prior_24h"] = prior_24h
    frame["Terminal_Prior_Tx_Count"] = terminal_prior
    frame["Terminal_Prior_Distinct_Customers"] = terminal_customer_prior
    frame["Customer_Terminal_Prior_Count"] = pair_prior
    frame[FEATURE_COLUMNS] = frame[FEATURE_COLUMNS].replace([np.inf, -np.inf], np.nan).fillna(0)
    return frame
