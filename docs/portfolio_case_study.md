# Quest of Trust — Fraud Strategy Case Study

## Executive summary

Quest of Trust is a synthetic payments-fraud analytics project. Its TrustHold decision system compares four authorization actions—approve, challenge, review, and decline—against modeled fraud loss, legitimate-payment friction, payment contribution, and investigator capacity.

The simulation covers 22,903 payment transactions over 60 days. Its later holdout contains 6,923 transactions and 35 planted fraud events. Under the project's fictional base economics and a review limit of 25 cases per day, the logistic strategy captures an estimated 81.62% of holdout fraud value, records three false declines, and produces a modeled net economic cost of −$5,847.42. The rules strategy captures 78.52%, records three false declines, and produces a modeled cost of −$4,859.65.

These are outputs of the simulator—not observed business savings, a real fraud rate, or evidence that the system is ready to make production decisions.

## Business question

How should a payments business route an event when it must balance fraud loss against legitimate-customer friction and a finite review queue?

The project makes the decision explicit:

| Action | Operating interpretation |
|---|---|
| Approve | Preserve convenience and payment margin; accept modeled fraud loss if the event is fraudulent. |
| Challenge | Add customer verification with an assumed stop rate and per-event cost. |
| Review | Spend investigator capacity; apply an assumed recovery rate and review cost. |
| Decline | Stop the event; incur an assumed customer-attrition cost if it was legitimate. |

## Method

1. Generate fictional customers, accounts, merchants, terminals, and legitimate transactions from a fixed seed.
2. Inject four documented fraud scenarios and keep their labels in a separate truth file.
3. Create 12 timestamp-safe behavioral signals using only information available before each event.
4. Score events with a transparent rules baseline and a NumPy logistic-regression baseline.
5. Choose action thresholds using the earlier training period, apply daily review capacity, and evaluate on later dates.
6. Compare costs, fraud-value capture, false declines, workload, capacity sensitivity, and customer-group diagnostics.
7. Save inspectable CSV tables and SQLite investigations; render a report and interactive standalone dashboard.

## Holdout fraud and operating results

| Strategy | Est. fraud value captured | False declines | Legitimate payments challenged | Legitimate payments reviewed | Cases over capacity | Modeled net cost |
|---|---:|---:|---:|---:|---:|---:|
| Incumbent | 0.00% | 0 | 97 | 0 | 0 | $385.41 |
| Rules | 78.52% | 3 | 390 | 9 | 0 | −$4,859.65 |
| Logistic | 81.62% | 3 | 143 | 23 | 0 | −$5,847.42 |
| Rules + logistic | 81.08% | 3 | 394 | 12 | 0 | −$5,053.89 |

At the stated assumptions, logistic increases estimated fraud-value capture by 3.10 percentage points versus rules while challenging 247 fewer legitimate payments. It sends 14 more legitimate payments to manual review; both strategies produce three false declines. Logistic has the lowest modeled net cost in this run. These differences depend on the simulation, the small holdout fraud count, and the assumed unit economics.

## What the result means—and does not mean

The analysis demonstrates how a payments-fraud team can compare detection strategies using business outcomes: estimated fraud loss captured, legitimate-payment friction, false declines, investigator workload, and modeled net cost. It does not establish expected performance or profitability for a real authorization policy. Challenge effectiveness, review recovery, customer lifetime value, chargeback costs, and the simulated population are fictional assumptions.

The case-study output currently contains a PR-AUC value in the scoreless Incumbent row due to a metric-mapping defect in the report pipeline. This strategy comparison does not use that value; an incumbent with no continuous risk score has no applicable PR-AUC. The project should correct that reporting defect before treating its generated case-study table as final.

## Scope and limitations

- Synthetic population and planted labels; no real customer or processor data.
- One account per customer and no device, IP, login, or account-recovery event model.
- One temporal holdout with 35 planted fraud events; results can vary with seed and scenario design.
- Cost and intervention effectiveness values are not calibrated to a real business.
- The model is a teaching baseline, not a production service or payment-time control.
- Customer-group rates are descriptive diagnostics, not a fairness certification.
- Monitoring is a prototype based on simple trailing statistical thresholds.
- Dashboard outcomes are precomputed; changing selectors changes scenario views, not the trained scoring model.

## Reproducibility

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m src.run_project
python sql/run_investigation.py
```

See the [project README](../README.md), [roadmap](roadmap.md), [implementation walkthrough](implementation_walkthrough.md), [data dictionary](data_dictionary.md), [simulation assumptions](simulation_assumptions.md), [fraud scenarios](fraud_scenarios.md), and [model governance notes](model_governance.md).

