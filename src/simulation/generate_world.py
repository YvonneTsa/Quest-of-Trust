"""Create customer-linked accounts, merchants, terminals, and clean activity."""

import numpy as np
import pandas as pd

from src.config import SEED, START_DATE
from src.simulation.generate_customers import generate_customers


MERCHANT_CATEGORIES = ["Grocery", "Fuel", "Travel", "Digital", "Dining", "Retail"]
CHANNELS = ["card_present", "ecommerce", "mobile_wallet"]
AUTH_TYPES = ["chip_pin", "3ds", "wallet_biometric", "magstripe"]


def generate_entities(n_customers: int, n_merchants: int, n_terminals: int):
    """Return customer, account, merchant, and terminal tables."""
    rng = np.random.default_rng(SEED + 1)
    customers = generate_customers(n_customers)
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


def generate_legitimate_transactions(customers, accounts, merchants, terminals, days: int):
    """Generate baseline events; these are legitimate by construction."""
    rng = np.random.default_rng(SEED + 2)
    start = pd.Timestamp(START_DATE)
    terminal_merchant = terminals.set_index("Terminal_ID")["Merchant_ID"].to_dict()
    terminal_region = terminals.set_index("Terminal_ID")["Region"].to_dict()
    terminal_ids = terminals["Terminal_ID"].to_numpy()
    # Give each fictional customer a small set of habitual endpoints. This makes
    # later changes in customer-terminal connectivity meaningful and inspectable.
    terminals_by_region = {
        region: group["Terminal_ID"].to_numpy()
        for region, group in terminals.groupby("Region")
    }
    familiar_terminals = {}
    for customer in customers.itertuples(index=False):
        in_region = terminals_by_region.get(customer.Home_Region, terminal_ids)
        choices = in_region if len(in_region) else terminal_ids
        familiar_terminals[customer.Customer_ID] = rng.choice(
            choices, size=min(3, len(choices)), replace=False
        )
    customer_to_account = dict(zip(accounts["Customer_ID"], accounts["Account_ID"]))
    rows = []
    tx_counter = 0

    for customer in customers.itertuples(index=False):
        for day in range(days):
            event_count = rng.poisson(customer.Typical_Transactions_Per_Day)
            if event_count == 0:
                continue
            seconds = np.sort(rng.integers(0, 86400, size=event_count))
            for second in seconds:
                tx_counter += 1
                channel = rng.choice(CHANNELS, p=[0.52, 0.33, 0.15])
                if rng.random() < 0.05:
                    terminal_id = str(rng.choice(terminal_ids))
                else:
                    terminal_id = str(rng.choice(familiar_terminals[customer.Customer_ID]))
                amount = max(1.0, rng.lognormal(np.log(customer.Typical_Spend), 0.55))
                auth_type = rng.choice(AUTH_TYPES, p=[0.45, 0.28, 0.18, 0.09])
                auth_result = rng.choice(["approved", "soft_decline"], p=[0.985, 0.015])
                rows.append(
                    {
                        "Transaction_ID": f"X{tx_counter:09d}",
                        "Timestamp": start + pd.Timedelta(days=day, seconds=int(second)),
                        "Customer_ID": customer.Customer_ID,
                        "Account_ID": customer_to_account[customer.Customer_ID],
                        "Merchant_ID": terminal_merchant[terminal_id],
                        "Terminal_ID": terminal_id,
                        "Customer_Region": customer.Home_Region,
                        "Merchant_Region": terminal_region[terminal_id],
                        "Amount": round(float(amount), 2),
                        "Currency": "USD",
                        "Channel": channel,
                        "Auth_Type": auth_type,
                        "Auth_Result": auth_result,
                        "Incumbent_Decision": "APPROVE" if auth_result == "approved" else "CHALLENGE",
                    }
                )
    return pd.DataFrame(rows)
