"""A NumPy-only logistic regression baseline with a time-ordered holdout."""

import numpy as np
import pandas as pd

from src.features.build_features import FEATURE_COLUMNS


class LogisticBaseline:
    """Weighted logistic regression fitted with full-batch gradient descent."""

    def __init__(self, learning_rate=0.08, epochs=1200, l2=0.001):
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.l2 = l2

    def fit(self, frame: pd.DataFrame):
        x = frame[FEATURE_COLUMNS].to_numpy(dtype=float)
        y = frame["Fraud_Label"].to_numpy(dtype=float)
        self.mean_ = x.mean(axis=0)
        self.scale_ = x.std(axis=0)
        self.scale_[self.scale_ == 0] = 1.0
        z = np.clip((x - self.mean_) / self.scale_, -8, 8)
        self.weights_ = np.zeros(z.shape[1], dtype=float)
        self.intercept_ = 0.0
        positives = max(1.0, y.sum())
        negatives = max(1.0, len(y) - positives)
        sample_weight = np.where(y == 1, min(negatives / positives, 12.0), 1.0)
        sample_weight /= sample_weight.mean()
        for _ in range(self.epochs):
            linear = np.clip(z @ self.weights_ + self.intercept_, -30, 30)
            probability = 1.0 / (1.0 + np.exp(-linear))
            error = (probability - y) * sample_weight
            self.weights_ -= self.learning_rate * ((z.T @ error) / len(y) + self.l2 * self.weights_)
            self.intercept_ -= self.learning_rate * error.mean()
        return self

    def predict_proba(self, frame: pd.DataFrame):
        x = frame[FEATURE_COLUMNS].to_numpy(dtype=float)
        z = np.clip((x - self.mean_) / self.scale_, -8, 8)
        linear = np.clip(z @ self.weights_ + self.intercept_, -30, 30)
        return 1.0 / (1.0 + np.exp(-linear))

    def coefficients(self):
        return pd.DataFrame({"Feature": FEATURE_COLUMNS, "Coefficient": self.weights_})
