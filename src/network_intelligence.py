"""Summarize observable customer-terminal connectivity without labels."""

import pandas as pd


def terminal_network_summary(transactions: pd.DataFrame) -> pd.DataFrame:
    """Measure endpoint degree and concentration in the customer-terminal graph."""
    summary = (
        transactions.groupby(["Terminal_ID", "Merchant_ID"], as_index=False)
        .agg(
            Transaction_Count=("Transaction_ID", "size"),
            Distinct_Customers=("Customer_ID", "nunique"),
            Distinct_Days=("Timestamp", lambda values: pd.to_datetime(values).dt.date.nunique()),
            Total_Amount=("Amount", "sum"),
        )
    )
    summary["Customers_Per_Transaction"] = (
        summary["Distinct_Customers"] / summary["Transaction_Count"].clip(lower=1)
    ).round(4)
    return summary.sort_values(
        ["Distinct_Customers", "Transaction_Count"], ascending=False
    ).reset_index(drop=True)
