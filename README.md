# TrustHold — The Cost of Fraud

TrustHold is a synthetic digital-payments fraud strategy project. It studies how a payments business can balance fraud loss, customer friction, investigator capacity, and revenue when choosing to **APPROVE**, **CHALLENGE**, **REVIEW**, or **DECLINE** a transaction.

The goal is to compare business outcomes, not to maximize model accuracy. No results in this repository should be described as real-world findings: simulated parameters are documented assumptions, and conclusions will be added only after analysis of generated data.

## Current milestone

The first build milestone generates a reproducible customer profile table with segment, typical spend, typical transaction rate, home region, and KYC risk band. The generator currently uses a 20-customer learning sample, continuing the saved script discovered during project recovery. The roadmap document described a 10-customer sample at an earlier point; the active count is an explicit setting in the code.

## Run it

From the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m src.simulation.generate_customers
```

The script creates `data/synthetic/customers.csv` and prints a small profile summary. To change the learning sample or random seed, edit the clearly named settings near the top of `src/simulation/generate_customers.py`.

## Repository map

- `src/simulation/` — reusable synthetic-data generation code.
- `data/synthetic/` — generated, non-sensitive example data.
- `docs/` — assumptions, project history, and teaching walkthroughs.
- `notebooks/` — later exploratory analysis.
- `sql/` — later investigation queries.
- `reports/` — later business-facing outputs.
- `tests/` — reserved for future automated checks.

## Learning-first build protocol

Each milestone explains the concept and reason, introduces syntax with a small example, states where code belongs, applies it to TrustHold, inspects the output, records assumptions, and connects the work to fraud/risk practice. See [`docs/customer_simulation_walkthrough.md`](docs/customer_simulation_walkthrough.md) and [`docs/simulation_assumptions.md`](docs/simulation_assumptions.md).

## Roadmap

1. Customer simulation — in progress; initial profile table implemented.
2. Accounts, merchants, and terminals.
3. Legitimate transaction generation.
4. Fraud-event injection with separately held ground truth.
5. Storage and SQL investigation.
6. Point-in-time behavioral features, rules, and model comparisons.
7. Decision policy, review capacity, and fraud economics.
8. Network intelligence, monitoring, and portfolio case study.

See [`docs/project_history.md`](docs/project_history.md) for the recovered project context and [`docs/simulation_assumptions.md`](docs/simulation_assumptions.md) for assumptions. Later stages remain planned; no model results or case-study metrics are claimed yet.
