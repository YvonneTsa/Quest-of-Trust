"""Create customer-linked accounts, merchants, terminals, and clean activity."""

import numpy as np
import pandas as pd

from src.config import SEED, START_DATE
from src.simulation.generate_customers import generate_customers


MERCHANT_CATEGORIES = ["Grocery", "Fuel", "Travel", "Digital", "Dining", "Retail"]
CHANNELS = ["card_present", "ecommerce", "mobile_wallet"]
AUTH_TYPES = ["chip_pin", "3ds", "wallet_biometric", "magstripe"]


def generate_entities(n_customers: int, n_merchants: int, n_terminals: int, seed: int = SEED):
    """Return customer, account, merchant, and terminal tables."""
    rng = np.random.default_rng(seed + 1)
    customers = generate_customers(n_customers, seed=seed)
    customers["Created_At"] = pd.Timestamp(START_DATE) - pd.to_timedelta(
        rng.integers(30, 900, size=n_customers), unit="D"
    )
    customers["KYC_Risk_Band"] = customers["KYC_Risk_Band"].astype(str)

    accounts = pd.DataFrame(
        {
            "Account_ID": [f"A{i:07d}" for i in range(1, n_customers + 1)],
            "Customer_ID": customers["Customer_ID"],
            "Opened_At": customers["Created_At"],
            "Account_Type": rng.choice(["Debit", "Credit", "Prepaid"], n_customers, p=[0.52, 0.40, 0.08]),
            "Status": "active",
        }
    )
    merchants = pd.DataFrame(
        {
            "Merchant_ID": [f"M{i:05d}" for i in range(1, n_merchants + 1)],
            "Category": rng.choice(MERCHANT_CATEGORIES, n_merchants),
            "Region": rng.choice(["Northeast", "South", "Midwest", "West"], n_merchants),
            "Risk_Profile": rng.choice(["baseline", "elevated"], n_merchants, p=[0.92, 0.08]),
        }
    )
    terminal_merchant_ix = rng.integers(0, n_merchants, size=n_terminals)
    terminals = pd.DataFrame(
        {
            "Terminal_ID": [f"T{i:05d}" for i in range(1, n_terminals + 1)],
            "Merchant_ID": merchants.iloc[terminal_merchant_ix]["Merchant_ID"].to_numpy(),
            "Region": merchants.iloc[terminal_merchant_ix]["Region"].to_numpy(),
            "Terminal_Type": rng.choice(["physical", "online_gateway"], n_terminals, p=[0.62, 0.38]),
        }
    )
    return customers, accounts, merchants, terminals


def generate_legitimate_transactions(customers, accounts, merchants, terminals, days: int, seed: int = SEED):
    """Generate baseline events; these are legitimate by construction."""
    rng = np.random.default_rng(seed + 2)
    start = pd.Timestamp(START_DATE)
    terminal_ids = terminals["Terminal_ID"].to_numpy()
    # Give each fictional customer a small set of habitual endpoints. This makes
    # later changes in customer-terminal connectivity meaningful and inspectable.
    terminals_by_region = {
        region: group["Terminal_ID"].to_numpy()
        for region, group in terminals.groupby("Region")
    }
    customer_rows = list(customers.itertuples(index=False))
    familiar_indexes = np.zeros((len(customer_rows), 3), dtype=int)
    familiar_lengths = np.zeros(len(customer_rows), dtype=int)
    terminal_position = {str(terminal_id): i for i, terminal_id in enumerate(terminal_ids)}
    for position, customer in enumerate(customer_rows):
        in_region = terminals_by_region.get(customer.Home_Region, terminal_ids)
        choices = in_region if len(in_region) else terminal_ids
        selected = rng.choice(choices, size=min(3, len(choices)), replace=False)
        familiar_lengths[position] = len(selected)
        familiar_indexes[position, : len(selected)] = [terminal_position[str(item)] for item in selected]

    # Draw counts in one matrix, then generate the event columns as arrays. The
    # resulting event distributions and behavioral rules are the same, while
    # larger book sizes avoid constructing each row in nested Python loops.
    rates = customers["Typical_Transactions_Per_Day"].to_numpy(dtype=float)
    daily_counts = rng.poisson(rates[:, None], size=(len(customer_rows), days))
    event_count = int(daily_counts.sum())
    customer_ix = np.repeat(np.arange(len(customer_rows)), daily_counts.sum(axis=1))
    day_ix = np.repeat(np.tile(np.arange(days), len(customer_rows)), daily_counts.ravel())
    seconds = rng.integers(0, 86400, size=event_count)
    order = np.lexsort((seconds, day_ix, customer_ix))
    customer_ix = customer_ix[order]
    day_ix = day_ix[order]
    seconds = seconds[order]

    channel = rng.choice(CHANNELS, size=event_count, p=[0.52, 0.33, 0.15])
    global_terminal = rng.random(event_count) < 0.05
    familiar_choice = rng.integers(0, familiar_lengths[customer_ix])
    terminal_ix = familiar_indexes[customer_ix, familiar_choice]
    if global_terminal.any():
        terminal_ix[global_terminal] = rng.integers(0, len(terminal_ids), size=int(global_terminal.sum()))

    auth_type = rng.choice(AUTH_TYPES, size=event_count, p=[0.45, 0.28, 0.18, 0.09])
    auth_result = rng.choice(["approved", "soft_decline"], size=event_count, p=[0.985, 0.015])
    typical_spend = customers["Typical_Spend"].to_numpy(dtype=float)
    amount = np.maximum(1.0, rng.lognormal(np.log(typical_spend[customer_ix]), 0.55))
    customer_ids = customers["Customer_ID"].to_numpy()[customer_ix]
    account_ids = accounts["Account_ID"].to_numpy()[customer_ix]
    terminal_id_values = terminal_ids[terminal_ix]
    terminal_merchant = terminals["Merchant_ID"].to_numpy()[terminal_ix]
    terminal_region = terminals["Region"].to_numpy()[terminal_ix]
    event_timestamps = start + pd.to_timedelta(day_ix, unit="D") + pd.to_timedelta(seconds, unit="s")

    return pd.DataFrame(
        {
            "Transaction_ID": [f"X{i:09d}" for i in range(1, event_count + 1)],
            "Timestamp": event_timestamps,
            "Customer_ID": customer_ids,
            "Account_ID": account_ids,
            "Merchant_ID": terminal_merchant,
            "Terminal_ID": terminal_id_values,
            "Customer_Region": customers["Home_Region"].to_numpy()[customer_ix],
            "Merchant_Region": terminal_region,
            "Amount": np.round(amount, 2),
            "Currency": "USD",
            "Channel": channel,
            "Auth_Type": auth_type,
            "Auth_Result": auth_result,
            "Incumbent_Decision": np.where(auth_result == "approved", "APPROVE", "CHALLENGE"),
        }
    )
