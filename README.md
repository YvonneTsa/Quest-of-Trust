# TrustHold — The Cost of Fraud

TrustHold is a reproducible synthetic payments-risk project about the cost of fraud decisions. It generates a digital-payments world, plants four documented fraud typologies, builds point-in-time behavioral signals, compares rules and a logistic-regression baseline, and evaluates **APPROVE / CHALLENGE / REVIEW / DECLINE** strategies under finite investigator capacity and explicit economics.

The objective is the overall business outcome: fraud loss, good-customer friction, review workload, and payment margin. The project does not optimize for accuracy alone. All outputs are synthetic and fictional; they are not evidence about a real company or customers.

## Run the complete project

From PowerShell at the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m src.run_project
```

The default run creates 200 customers, 80 merchants, 120 terminals, 60 days of baseline and injected events, and holds out the latest 30% of dates. The run uses only NumPy and pandas. Generated tables are saved as CSV and to a local SQLite database. No database server or downloaded dataset is required.

For a smaller walkthrough:

```powershell
python -m src.run_project --customers 20 --days 30
```

The generator rejects horizons too short to place fraud examples in both the training and holdout periods. Adjust counts with `--customers`, `--days`, `--merchants`, `--terminals`, and `--review-capacity`. Output location can be changed with `--output-dir`.

## Generated outputs

- `data/synthetic/run/*.csv` — customer, account, merchant, terminal, transaction, feature, decision, monitoring, and result tables.
- `data/synthetic/run/restricted/fraud_ground_truth.csv` — planted labels and typology metadata for offline evaluation only. It is generated locally, ignored by Git, and excluded from the SQLite database and public analysis tables.
- `data/synthetic/run/trusthold.sqlite` — local SQL investigation database containing observable transactions and derived features, strategy outputs, and aggregated metrics.
- `data/synthetic/run/capacity_sensitivity.csv`, `economic_sensitivity.csv`, and `impact_by_customer_group.csv` — scenario and customer-impact diagnostics.
- `reports/case_study.md` — generated held-out comparison plus capacity, economic, and group-impact tables, caveats, and interpretation.
- `reports/dashboard.html` — self-contained visual comparison of economic outcomes and daily observable volume.

## SQL investigation

After the full run, inspect the generated SQLite tables with:

```powershell
python sql/run_investigation.py
```

The `.sql` files explore daily volume, terminal concentration, rapid low-value events, amount deviation, and authentication/channel behavior. They intentionally do not reference the hidden labels.

## Repository guide

- `src/simulation/` — customer/entity and transaction generation plus fraud injection.
- `src/features/` — timestamp-ordered, lagged features.
- `src/rules/` — readable score and reason codes.
- `src/models/` — NumPy logistic-regression baseline.
- `src/decisions/` — four-action strategy and daily review capacity.
- `src/evaluation/` — PR-AUC and economic/customer-impact measures.
- `src/network_intelligence.py` — label-free customer-terminal graph connectivity summaries.
- `src/monitoring.py`, `src/storage.py`, `src/reporting.py` — rolling three-sigma monitoring, SQLite/CSV persistence, case study and dashboard.
- `docs/` — assumptions, data dictionary, fraud scenarios, governance, and teaching walkthrough.
- `sql/` — reproducible SQLite investigations.

## Method guardrails

- Fraud ground truth stays separate until after feature construction and is never a model input.
- Every rolling feature uses only events earlier than the current timestamp.
- The model evaluation uses a temporal holdout, not a random row split.
- KYC risk is independent of planted fraud and excluded from the model.
- Costs, fraud scenarios, populations, and intervention effectiveness are assumptions and are stress-tested.
- An anomaly is a signal to investigate, not proof that an event is fraudulent.
- No headline project results are prewritten: the case study is generated from each actual run and labels every result synthetic.

See [`docs/learning_build_guide.md`](docs/learning_build_guide.md) for the teaching sequence, [`docs/simulation_assumptions.md`](docs/simulation_assumptions.md) for parameter values, and [`docs/model_governance.md`](docs/model_governance.md) for leakage and evaluation controls. Power BI remains an optional portfolio presentation layer; the delivered HTML dashboard works locally without it.
The status of each original roadmap stage and the remaining prototype limits are recorded in [`docs/roadmap.md`](docs/roadmap.md).
