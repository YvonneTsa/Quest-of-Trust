"""Create observable, label-free daily monitoring summaries."""

import pandas as pd


def daily_monitoring(features: pd.DataFrame, scored: pd.DataFrame) -> pd.DataFrame:
    """Summarize operational signals without reading hidden fraud labels."""
    frame = features[["Timestamp", "Amount", "Auth_Soft_Decline"]].copy()
    frame["Date"] = pd.to_datetime(frame["Timestamp"]).dt.date.astype(str)
    frame["Model_Score"] = scored["Model_Score"].to_numpy()
    daily = (
        frame.groupby("Date", as_index=False)
        .agg(
            Transaction_Count=("Amount", "size"),
            Transaction_Value=("Amount", "sum"),
            Average_Amount=("Amount", "mean"),
            Soft_Decline_Rate=("Auth_Soft_Decline", "mean"),
            High_Risk_Score_Rate=("Model_Score", lambda values: (values >= 0.5).mean()),
        )
        .round(4)
    )
    for column, prefix in [("Transaction_Count", "Volume"), ("High_Risk_Score_Rate", "Risk_Score_Rate")]:
        history = daily[column].shift(1).rolling(window=14, min_periods=7)
        baseline_mean = history.mean()
        baseline_std = history.std(ddof=0).replace(0, float("nan"))
        daily[f"{prefix}_Prior_14d_ZScore"] = ((daily[column] - baseline_mean) / baseline_std).round(3)
    daily["Volume_3Sigma_Alert"] = (daily["Volume_Prior_14d_ZScore"].abs() >= 3).astype(int)
    daily["Risk_Score_3Sigma_Alert"] = (daily["Risk_Score_Rate_Prior_14d_ZScore"].abs() >= 3).astype(int)
    return daily
