# Learning-first end-to-end build guide

The capstone remains ambitious, but the workflow is staged. All runnable code belongs in `src/`; PowerShell runs commands but is not where Python statements are typed.

| Step | Concept and reason | TrustHold implementation | Inspect |
|---|---|---|---|
| 1 | Customer profile rows establish a controlled synthetic population. | `generate_customers.py` | `data/synthetic/customers.csv` |
| 2 | Linked entities give IDs and ownership relationships. | `generate_world.py` | customers/accounts/merchants/terminals CSVs |
| 3 | Poisson counts turn latent customer rates into integer activity. | `generate_legitimate_transactions` | baseline count and transaction CSV |
| 4 | Explicit injections create known evaluation truth. | `inject_fraud.py` | restricted truth table; keep out of investigation |
| 5 | Time-shifted features describe earlier behavior only. | `build_features.py` | feature table and `FEATURE_COLUMNS` |
| 6 | Rules make alert reasons inspectable before modeling. | `score_rules.py` | rule score and rule reasons |
| 7 | A time-ordered holdout tests future periods. | `logistic_baseline.py`, `run_project.py` | train/test dates and PR-AUC |
| 8 | Risk scores must become operating actions. | `decisions/policies.py` | strategy decisions and action counts |
| 9 | Review capacity changes which cases humans can see. | daily top-risk queue and spillover | overflow count by strategy |
| 10 | Cost makes friction and loss comparable in dollars. | `Economics`, `evaluate_policy` | strategy and assumption sensitivity tables |
| 11 | SQL aggregates patterns for investigation. | `sql/` | terminal, timing, velocity, and amount queries |
| 12 | Monitoring checks observable changes over time. | `monitoring.py` | daily CSV and dashboard trend |
| 13 | A case study communicates findings and limitations. | `reporting.py` | generated `reports/case_study.md` |

Run one command, inspect the printed outputs and generated files, then change only one setting at a time. Parameters should be explained and documented before scaling. The default is deliberately larger than the first 20-customer learning sample but remains local and reproducible; use `--customers 20 --days 30` for a smaller walkthrough.
