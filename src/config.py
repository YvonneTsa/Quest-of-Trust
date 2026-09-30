"""Central, inspectable assumptions for the TrustHold simulation."""

from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "synthetic" / "run"
SEED = 20260915
START_DATE = "2026-01-01"
SIMULATION_DAYS = 60
N_CUSTOMERS = 200
N_MERCHANTS = 80
N_TERMINALS = 120


@dataclass(frozen=True)
class Economics:
    """Fictional unit costs, kept in one place for sensitivity analysis."""

    interchange_margin_rate: float = 0.011
    chargeback_fee: float = 25.0
    challenge_cost: float = 0.40
    challenge_fraud_stop_probability: float = 0.80
    false_decline_probability_of_attrition: float = 0.05
    customer_lifetime_value: float = 500.0
    review_cost: float = 4.50
    review_fraud_recovery_probability: float = 0.90
    review_capacity_per_day: int = 25


ECONOMICS = Economics()
