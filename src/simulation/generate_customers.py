"""Generate a small, reproducible customer profile table for TrustHold.

Learning scale: the default is intentionally small enough to inspect by eye.
All probabilities and profile values are fictional simulation assumptions.
"""

from pathlib import Path

import numpy as np
import pandas as pd


# Resolve the repository root from this file so the script works from any
# current working directory when run with ``python -m``.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = PROJECT_ROOT / "data" / "synthetic" / "customers.csv"

# A seed makes every random draw repeatable while these settings stay fixed.
SEED = 20260915
N_CUSTOMERS = 20  # Continues the count in the recovered local script.

# Each segment is paired by position with its fictional sampling probability.
SEGMENTS = ["Standard", "Premium", "Business"]
SEGMENT_PROBABILITIES = [0.70, 0.20, 0.10]

# These are medians, not arithmetic means, because the log-normal draw below
# uses the logarithm of each reference value as its underlying normal mean.
SEGMENT_MEDIAN_SPEND = {
    "Standard": 45.0,
    "Premium": 100.0,
    "Business": 180.0,
}
SEGMENT_MEDIAN_TRANSACTIONS_PER_DAY = {
    "Standard": 1.5,
    "Premium": 2.5,
    "Business": 4.0,
}
SPEND_LOG_SIGMA = 0.40
TRANSACTION_RATE_LOG_SIGMA = 0.30

# Region and KYC are customer descriptors. KYC risk is sampled independently
# from fraud ground truth; it must not act as a hidden fraud label.
REGIONS = ["Northeast", "South", "Midwest", "West"]
REGION_PROBABILITIES = [0.24, 0.36, 0.22, 0.18]
KYC_RISK_BANDS = ["Low", "Medium", "High"]
KYC_RISK_PROBABILITIES = [0.70, 0.25, 0.05]


def generate_customers(n_customers: int = N_CUSTOMERS, seed: int = SEED) -> pd.DataFrame:
    """Create customer attributes without generating transactions or fraud."""
    if n_customers < 1:
        raise ValueError("n_customers must be at least 1")

    # Use a fresh generator for each call, so repeated calls are identical.
    customer_rng = np.random.default_rng(seed)
    customer_ids = [f"C{i:06d}" for i in range(1, n_customers + 1)]
    segments = customer_rng.choice(
        SEGMENTS, size=n_customers, p=SEGMENT_PROBABILITIES
    )

    median_spend = [SEGMENT_MEDIAN_SPEND[segment] for segment in segments]
    typical_spend = customer_rng.lognormal(
        mean=np.log(median_spend), sigma=SPEND_LOG_SIGMA
    )

    median_daily_rate = [
        SEGMENT_MEDIAN_TRANSACTIONS_PER_DAY[segment] for segment in segments
    ]
    typical_transactions_per_day = customer_rng.lognormal(
        mean=np.log(median_daily_rate), sigma=TRANSACTION_RATE_LOG_SIGMA
    )

    # These attributes are drawn separately from segment, spend, and one
    # another; no fraud flag exists at this stage of the simulation.
    home_regions = customer_rng.choice(
        REGIONS, size=n_customers, p=REGION_PROBABILITIES
    )
    kyc_risk_bands = customer_rng.choice(
        KYC_RISK_BANDS, size=n_customers, p=KYC_RISK_PROBABILITIES
    )

    return pd.DataFrame(
        {
            "Customer_ID": customer_ids,
            "Segment": segments,
            "Typical_Spend": typical_spend.round(2),
            "Typical_Transactions_Per_Day": typical_transactions_per_day.round(2),
            "Home_Region": home_regions,
            "KYC_Risk_Band": kyc_risk_bands,
        }
    )


def main() -> None:
    """Generate the CSV and print summaries for an easy first inspection."""
    customers = generate_customers()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    customers.to_csv(OUTPUT_PATH, index=False)

    print(f"Generated {len(customers)} TrustHold customer profiles.")
    print(f"Saved to: {OUTPUT_PATH.relative_to(PROJECT_ROOT)}")
    print("\nCustomer sample:")
    print(customers.head(10).to_string(index=False))
    print("\nSegment profile summary:")
    print(
        customers.groupby("Segment")["Typical_Spend"]
        .agg(["count", "median", "min", "max"])
        .round(2)
        .to_string()
    )


if __name__ == "__main__":
    main()
