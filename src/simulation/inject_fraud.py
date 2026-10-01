"""Inject transparent synthetic attack events and keep their truth table separate."""

import numpy as np
import pandas as pd

from src.config import FRAUD_CAMPAIGNS_PER_TYPOLOGY, SEED


def inject_fraud(
    transactions,
    customers,
    terminals,
    days: int,
    seed: int = SEED,
    campaigns_per_typology: int = FRAUD_CAMPAIGNS_PER_TYPOLOGY,
):
    """Add four typologies after the baseline period and return hidden truth."""
    if campaigns_per_typology < 1:
        raise ValueError("campaigns_per_typology must be at least 1")
    rng = np.random.default_rng(seed + 3)
    if transactions.empty:
        return transactions, pd.DataFrame(columns=["Transaction_ID", "Event_ID", "Typology"])

    start = transactions["Timestamp"].min().normalize()
    crisis_day = max(1, int(days * 0.58))
    crisis_start = start + pd.Timedelta(days=crisis_day)
    truth_rows, fraud_rows = [], []
    next_id = len(transactions) + 1
    event_number = 0

    def add_event(typology, customer_ids, terminal_id, count, amount_range, cadence_seconds, phase):
        nonlocal next_id, event_number
        event_number += 1
        event_id = f"F{event_number:04d}"
        first_second = int(rng.integers(0, 86400))
        phase_offset = 0 if phase == 1 else max(1, (days - crisis_day) // 2)
        event_start = crisis_start + pd.Timedelta(days=phase_offset)
        for i in range(count):
            customer_id = str(rng.choice(customer_ids))
            customer = customers.loc[customers["Customer_ID"] == customer_id].iloc[0]
            terminal = terminals.loc[terminals["Terminal_ID"] == terminal_id].iloc[0]
            tx_id = f"X{next_id:09d}"
            next_id += 1
            low, high = amount_range
            amount = float(rng.uniform(low, high))
            timestamp = event_start + pd.Timedelta(seconds=first_second + cadence_seconds * i)
            fraud_rows.append(
                {
                    "Transaction_ID": tx_id,
                    "Timestamp": timestamp,
                    "Customer_ID": customer_id,
                    "Account_ID": f"A{int(customer_id[1:]):07d}",
                    "Merchant_ID": str(terminals.loc[terminals["Terminal_ID"] == terminal_id, "Merchant_ID"].iloc[0]),
                    "Terminal_ID": terminal_id,
                    "Customer_Region": customer["Home_Region"],
                    "Merchant_Region": terminal["Region"],
                    "Amount": round(amount, 2),
                    "Currency": "USD",
                    "Channel": rng.choice(["ecommerce", "mobile_wallet", "card_present"]),
                    "Auth_Type": rng.choice(["3ds", "magstripe", "chip_pin"]),
                    "Auth_Result": rng.choice(["approved", "soft_decline"], p=[0.82, 0.18]),
                    "Incumbent_Decision": "APPROVE",
                }
            )
            truth_rows.append(
                {
                    "Transaction_ID": tx_id,
                    "Event_ID": event_id,
                    "Typology": typology,
                    "Crisis_Start": crisis_start,
                    "Event_Start": event_start,
                    "Affected_Customer_ID": customer_id,
                    "Compromised_Terminal_ID": terminal_id,
                }
            )

    customers_ids = customers["Customer_ID"].to_numpy()
    terminal_ids = terminals["Terminal_ID"].to_numpy()

    for _ in range(campaigns_per_typology):
        # A terminal compromise creates a burst across several otherwise unrelated accounts.
        compromised_terminal = str(rng.choice(terminal_ids))
        ring_customers = rng.choice(customers_ids, size=min(8, len(customers_ids)), replace=False)
        add_event("terminal_compromise", ring_customers, compromised_terminal, 16, (35, 420), 900, 1)
        add_event("terminal_compromise", ring_customers, compromised_terminal, 16, (35, 420), 900, 2)

        # Card testing is represented by short low-value sequences at a shared endpoint.
        testing_terminal = str(rng.choice(terminal_ids))
        testers = rng.choice(customers_ids, size=min(4, len(customers_ids)), replace=False)
        add_event("card_testing", testers, testing_terminal, 12, (0.5, 5.0), 45, 1)
        add_event("card_testing", testers, testing_terminal, 12, (0.5, 5.0), 45, 2)

        # Compromised credentials produce behaviorally unusual higher-value activity.
        credential_customer = str(rng.choice(customers_ids))
        credential_terminal = str(rng.choice(terminal_ids))
        add_event("credential_compromise", [credential_customer], credential_terminal, 4, (180, 900), 1800, 1)
        add_event("credential_compromise", [credential_customer], credential_terminal, 4, (180, 900), 1800, 2)

        # ATO adds a rapid, shifted channel/authentication pattern for one account.
        ato_customer = str(rng.choice(customers_ids))
        ato_terminal = str(rng.choice(terminal_ids))
        add_event("account_takeover", [ato_customer], ato_terminal, 3, (120, 700), 1200, 1)
        add_event("account_takeover", [ato_customer], ato_terminal, 3, (120, 700), 1200, 2)

    fraud = pd.DataFrame(fraud_rows)
    combined = pd.concat([transactions, fraud], ignore_index=True).sort_values(
        ["Timestamp", "Transaction_ID"], kind="stable"
    ).reset_index(drop=True)
    truth = pd.DataFrame(truth_rows).sort_values("Transaction_ID").reset_index(drop=True)
    return combined, truth
