# Quest of Trust

### A payments fraud strategy case study about loss, customer friction, and review capacity

**Quest of Trust** is a reproducible synthetic analytics portfolio project. Its **TrustHold** decision system simulates payment events, builds point-in-time risk signals, compares transparent rules with a logistic baseline, and evaluates four operating actions under fictional economics and limited review capacity.

> **Evidence boundary:** every customer, transaction, fraud label, dollar assumption, and reported outcome is synthetic. This project is an educational portfolio prototype, not a real-world performance claim or production control.

| Explore | What you will find |
|---|---|
| [Open the portfolio case study](https://yvonntsa.github.io/Quest-of-Trust/) | Findings, business meaning, methods, limitations, and the dashboard. |
| [Run the scenario dashboard](https://yvonntsa.github.io/Quest-of-Trust/dashboard.html) | Compare precomputed holdout outcomes across capacity and cost assumptions. |
| [Read the detailed case study](docs/portfolio_case_study.md) | Method, selected results, assumptions, caveats, and reproducibility. |
| [Use the three-minute walkthrough](docs/demo_talk_track.md) | Presentation script and answers to likely reviewer questions. |

## What the project asks

How should a payments business route an event when it must balance fraud loss, good-customer friction, payment margin, and finite investigator capacity?

TrustHold maps a risk score into four possible actions:

- **APPROVE** — preserve convenience and margin; accept modeled fraud loss if the event is fraudulent.
- **CHALLENGE** — add verification friction and a modeled per-event cost.
- **REVIEW** — use investigator capacity and an assumed recovery rate.
- **DECLINE** — stop the payment; risk losing a legitimate customer.

## Selected result from the published synthetic run

The portfolio run contains **22,903** events over 60 simulated days. The later holdout contains **6,923** events and **35 planted fraud events**. At the base assumptions and 25 reviews per day:

| Strategy | Fraud value captured | False declines | Legitimate challenges | Legitimate reviews | Modeled net cost |
|---|---:|---:|---:|---:|---:|
| Rules | 78.52% | 3 | 390 | 9 | −$4,859.65 |
| Logistic | 81.62% | 3 | 143 | 23 | −$5,847.42 |

In this run, Logistic captures an estimated 3.10 percentage points more fraud value than Rules and sends 247 fewer legitimate events to challenge. Its modeled net cost is lower under the project’s assumptions. **These figures are simulated, conditional results—not observed savings or a forecast.**

The generated Markdown report currently repeats the Rules PR-AUC in the scoreless Incumbent row. This README and portfolio page omit that invalid comparison; an incumbent with no continuous risk score has no applicable PR-AUC. See the case study for the reporting note.

## How it works

```text
Synthetic entities and events
        ↓
Four planted fraud scenarios ─── hidden labels stay separate
        ↓
12 timestamp-safe behavioral features
        ↓
Rules score + NumPy logistic baseline
        ↓
APPROVE / CHALLENGE / REVIEW / DECLINE
        ↓
Temporal holdout, finite review queue, economics, group diagnostics
        ↓
CSV + SQLite + SQL investigations + report + dashboard
```

The model is trained on earlier dates and evaluated on later dates. Features are created before the hidden fraud labels are joined for offline training/evaluation. The dashboard explores precomputed outcomes; it does not retrain a model or make live decisions.

## Run it locally

From PowerShell at the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m src.run_project
python sql/run_investigation.py
```

The default run creates 200 customers, 80 merchants, 120 terminals, and 60 days of activity. It writes inspectable CSV tables and a local SQLite database under `data/synthetic/run/`. SQLite is used as a simple, serverless analytical store for this local project.

To restore and verify the versioned synthetic CSV snapshot:

```powershell
python -m scripts.assemble_dataset
```

## Repository guide

- `src/simulation/` — fictional customers, entities, legitimate activity, and fraud injection.
- `src/features/` — point-in-time transaction behavior features.
- `src/rules/` and `src/models/` — readable rules and a NumPy logistic baseline.
- `src/decisions/` and `src/evaluation/` — actions, review capacity, economics, and metrics.
- `sql/` — six reproducible, label-free investigation queries.
- `data/synthetic/published_run/` — checksum-listed synthetic snapshot; truth labels are separate.
- `reports/` — generated case study and standalone interactive HTML dashboard.
- `docs/` — [roadmap](docs/roadmap.md), [data dictionary](docs/data_dictionary.md), [assumptions](docs/simulation_assumptions.md), [fraud scenarios](docs/fraud_scenarios.md), [governance](docs/model_governance.md), and [implementation walkthrough](docs/implementation_walkthrough.md).

## Limitations

- The data, prevalence, fraud scenarios, and unit economics are fictional.
- One holdout contains only 35 planted fraud events; results can change across seeds and scenarios.
- The simulator has one account per customer and no device, IP, login, or recovery-event network.
- Group diagnostics are descriptive, not fairness certification.
- Monitoring is a prototype; no real-time model service or payment control is deployed.

For a full interpretation of results and assumptions, start with the [portfolio case study](docs/portfolio_case_study.md). For a short presentation, use the [three-minute walkthrough](docs/demo_talk_track.md).

