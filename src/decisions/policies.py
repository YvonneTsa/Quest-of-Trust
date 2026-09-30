"""Translate risk scores into four operating actions under review limits."""

import pandas as pd

from src.config import ECONOMICS


THRESHOLD_CANDIDATES = [
    (0.20, 0.50, 0.80),
    (0.30, 0.60, 0.90),
    (0.40, 0.70, 0.95),
    (0.50, 0.80, 0.97),
]


def apply_policy(frame: pd.DataFrame, score_column: str, thresholds, capacity=None):
    """Apply score bands and route only the daily highest-risk cases to review."""
    challenge_at, review_at, decline_at = thresholds
    out = frame.copy()
    score = out[score_column].astype(float)
    out["Decision"] = "APPROVE"
    out.loc[score >= challenge_at, "Decision"] = "CHALLENGE"
    out.loc[score >= review_at, "Decision"] = "REVIEW"
    out.loc[score >= decline_at, "Decision"] = "DECLINE"

    daily_capacity = ECONOMICS.review_capacity_per_day if capacity is None else capacity
    out["Capacity_Overflow"] = 0
    out["Decision_Date"] = pd.to_datetime(out["Timestamp"]).dt.date.astype(str)
    for _, indexes in out.loc[out["Decision"] == "REVIEW"].groupby("Decision_Date").groups.items():
        ordered = out.loc[indexes].sort_values(score_column, ascending=False, kind="stable")
        spill = ordered.index[daily_capacity:]
        out.loc[spill, "Decision"] = "CHALLENGE"
        out.loc[spill, "Capacity_Overflow"] = 1
    return out


def policy_costs(frame: pd.DataFrame, economics=ECONOMICS) -> pd.Series:
    """Per-event dollar cost under documented fictional economics."""
    econ = economics
    fraud = frame["Fraud_Label"].astype(bool)
    amount = frame["Amount"].astype(float)
    decision = frame["Decision"]
    costs = pd.Series(0.0, index=frame.index)

    costs.loc[fraud & (decision == "APPROVE")] = amount.loc[fraud & (decision == "APPROVE")] + econ.chargeback_fee
    costs.loc[fraud & (decision == "CHALLENGE")] = (
        amount.loc[fraud & (decision == "CHALLENGE")] * (1 - econ.challenge_fraud_stop_probability)
        + econ.challenge_cost
    )
    costs.loc[fraud & (decision == "REVIEW")] = (
        amount.loc[fraud & (decision == "REVIEW")] * (1 - econ.review_fraud_recovery_probability)
        + econ.review_cost
    )
    costs.loc[fraud & (decision == "DECLINE")] = 0.0

    legitimate = ~fraud
    costs.loc[legitimate & (decision == "APPROVE")] = -amount.loc[legitimate & (decision == "APPROVE")] * econ.interchange_margin_rate
    costs.loc[legitimate & (decision == "CHALLENGE")] = econ.challenge_cost
    costs.loc[legitimate & (decision == "REVIEW")] = econ.review_cost
    costs.loc[legitimate & (decision == "DECLINE")] = (
        econ.false_decline_probability_of_attrition * econ.customer_lifetime_value
        + amount.loc[legitimate & (decision == "DECLINE")] * econ.interchange_margin_rate
    )
    return costs


def evaluate_policy(frame: pd.DataFrame, strategy: str, economics=ECONOMICS) -> dict:
    """Summarize capture, customer friction, capacity, and net economic cost."""
    labeled = frame.copy()
    fraud = labeled["Fraud_Label"].astype(bool)
    legitimate = ~fraud
    total_fraud_value = float(labeled.loc[fraud, "Amount"].sum())
    intervention = labeled["Decision"] != "APPROVE"
    costs = policy_costs(labeled, economics)
    capture_fraction = {"APPROVE": 0.0, "CHALLENGE": 0.80, "REVIEW": 0.90, "DECLINE": 1.0}
    captured_value = sum(
        float(labeled.loc[fraud & (labeled["Decision"] == action), "Amount"].sum()) * capture_fraction[action]
        for action in capture_fraction
    )
    fraud_losses = float(costs.loc[fraud].sum())
    return {
        "Strategy": strategy,
        "Transactions": int(len(labeled)),
        "Fraud_Transactions": int(fraud.sum()),
        "Fraud_Value": round(total_fraud_value, 2),
        "Fraud_Value_Captured_Pct": round(100 * captured_value / total_fraud_value, 2) if total_fraud_value else 0.0,
        "Fraud_Loss_After_Intervention": round(fraud_losses, 2),
        "Precision_Among_Interventions": round(float((fraud & intervention).sum() / max(1, intervention.sum())), 4),
        "Fraud_Recall": round(float((fraud & intervention).sum() / max(1, fraud.sum())), 4),
        "Legitimate_Challenge_Count": int((legitimate & (labeled["Decision"] == "CHALLENGE")).sum()),
        "Legitimate_Review_Count": int((legitimate & (labeled["Decision"] == "REVIEW")).sum()),
        "False_Declines": int((legitimate & (labeled["Decision"] == "DECLINE")).sum()),
        "Review_Overflow_Count": int(labeled["Capacity_Overflow"].sum()),
        "Net_Economic_Cost": round(float(costs.sum()), 2),
    }
