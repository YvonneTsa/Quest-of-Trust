"""Metrics that describe fraud capture and business impact, not accuracy alone."""

import numpy as np
import pandas as pd


def average_precision(labels, scores) -> float:
    """Area under the precision-recall step curve, implemented with NumPy."""
    y = np.asarray(labels, dtype=int)
    s = np.asarray(scores, dtype=float)
    positives = int(y.sum())
    if positives == 0:
        return 0.0
    order = np.argsort(-s, kind="stable")
    sorted_y = y[order]
    precision_at_k = np.cumsum(sorted_y) / np.arange(1, len(y) + 1)
    return float((precision_at_k * sorted_y).sum() / positives)


def action_counts(frame: pd.DataFrame) -> pd.DataFrame:
    counts = frame["Decision"].value_counts().reindex(
        ["APPROVE", "CHALLENGE", "REVIEW", "DECLINE"], fill_value=0
    )
    return counts.rename_axis("Decision").reset_index(name="Count")
