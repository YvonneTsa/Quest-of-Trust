# Quest of Trust

### A payments fraud strategy case study about loss, customer friction, and review capacity

**Quest of Trust** is a reproducible synthetic fraud analytics project. Its **TrustHold** decision system simulates payment events, builds point-in-time risk signals, compares transparent rules with a logistic baseline, and evaluates four operating actions under fictional economics and limited review capacity.

> **Evidence boundary:** every customer, transaction, fraud label, dollar assumption, and reported outcome is synthetic. This project is an educational portfolio prototype, not a real-world performance claim or production control.

| Explore | What you will find |
|---|---|
| [Open the project site](https://yvonnetsa.github.io/Quest-of-Trust/) | Findings, business meaning, methods, limitations, and the dashboard. |
| [Run the scenario dashboard](https://yvonnetsa.github.io/Quest-of-Trust/dashboard.html) | Compare precomputed holdout outcomes across capacity and cost assumptions. |
| [Read the detailed case study](docs/portfolio_case_study.md) | Method, selected results, assumptions, caveats, and reproducibility. |
| [Use the three-minute walkthrough](docs/demo_talk_track.md) | Presentation script and answers to likely reviewer questions. |

## What the project asks

How should a payments business route an event when it must balance fraud loss, good-customer friction, payment margin, and finite investigator capacity?

TrustHold maps a risk score into four possible actions:

- **APPROVE** — preserve convenience and margin; accept modeled fraud loss if the event is fraudulent.
- **CHALLENGE** — add verification friction and a modeled per-event cost.
- **REVIEW** — use investigator capacity and an assumed recovery rate.
- **DECLINE** — stop the payment; risk losing a legitimate customer.

## Results across synthetic seeds

The default book contains **246,314** synthetic events over 60 days. The primary later-period test has **350 simulated fraud events per seed** and about 72,000–75,000 total events. Across **30** reproducible seeds, Logistic had lower modeled net cost than Rules in **30 of 30** runs. These ranges describe variation inside this simulator; they are not confidence intervals for real payment populations.

| Strategy | Fraud value captured, mean (range) | False declines, median (range) | Good payments challenged, median (range) | Good payments reviewed, median (range) | Modeled net cost, mean / median (range) |
|---|---:|---:|---:|---:|---:|
| Rules | 73.73% (68.29–81.25%) | 31 (19–52) | 5,139 (4,552–5,764) | 126 (88–155) | −$52,629 mean; −$52,948 median (−$58,036 to −$47,036) |
| Logistic | 77.51% (69.76–87.21%) | 0 (0–2) | 599 (181–930) | 19 (7–37) | −$67,853 mean; −$68,082 median (−$73,730 to −$60,293) |

Across paired runs, Logistic captured a median **3.66 percentage points** more fraud value (range **−1.86 to +14.31** points), challenged a median **4,464 fewer good payments** (3,988–5,342 fewer), and sent a median **108 fewer good payments to review** (65–138 fewer). Its median modeled-cost difference versus Rules was **−$15,502** per test period (range −$22,482 to −$11,208). The cost ranking repeated in 30/30 runs, while fraud-capture lift varied and was negative in some seeds. A negative modeled cost includes assumed margin from approved legitimate payments; it is not observed profit or savings.

The 30 paired runs show a consistent modeled-cost ranking inside this simulator, not real-world validity. The observed fraud-capture range also shows why the cost result should not be read as a guaranteed improvement in every outcome. Per-seed rows, summaries, paired differences, and full synthetic CSV table parts are included under `data/synthetic/published_run/`; the local SQLite database is rebuilt by the run command. The nested unseen-campaign check is reported separately for the default seed only and contains 175 fraud events; it is not a second 30-seed result.

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

The default run creates 2,000 customers, 800 merchants, 1,200 terminals, 60 days of activity, and 10 sampled campaigns for each of four fraud typologies. It evaluates the primary later-date comparison across 30 deterministic seeds by default and writes a separate default-seed nested campaign check, validation-split details, business sensitivity tables, CSV artifacts, and a local SQLite database under `data/synthetic/run/`. The review limit is 250 cases per day. SQLite is a local serverless analytical store.

To rebuild the versioned synthetic CSV snapshot after the run:

```powershell
python -m scripts.package_dataset
```

## Repository guide

- `src/simulation/` — fictional customers, entities, legitimate activity, and fraud injection.
- `src/features/` — point-in-time transaction behavior features.
- `src/rules/` and `src/models/` — readable rules and a NumPy logistic baseline.
- `src/decisions/` and `src/evaluation/` — actions, review capacity, economics, and metrics.
- `sql/` — six reproducible, label-free investigation queries.
- `data/synthetic/published_run/` — checksum-listed synthetic event, feature, and decision tables with planted labels stored separately.
- `data/synthetic/run/seed_stability_*.csv` — per-seed metrics, summary ranges, and paired strategy comparisons supporting the findings above.
- `reports/` — generated case study and standalone interactive HTML dashboard.
- `docs/evaluation_design.md` — fit, validation, temporal holdout, unseen-campaign holdout, and break-even methodology.
- `docs/` — [roadmap](docs/roadmap.md), [data dictionary](docs/data_dictionary.md), [assumptions](docs/simulation_assumptions.md), [fraud scenarios](docs/fraud_scenarios.md), [governance](docs/model_governance.md), and [implementation walkthrough](docs/implementation_walkthrough.md).

## Limitations

- The data, prevalence, fraud scenarios, and unit economics are fictional.
- Thirty deterministic seeds show variation under the same simulator assumptions; they are not confidence intervals and do not measure uncertainty in a real customer or transaction population.
- Each later-date test period has 350 simulated fraud cases. The separate default-seed campaign check withholds half the campaign identities and evaluates 175 later-phase cases; it is a one-seed diagnostic.
- Thresholds are selected on a campaign-stratified validation sample that is excluded from model fitting; the final temporal holdout remains untouched during selection.
- Thirty random seeds measure variation under the same simulator. They do not validate realism, statistical external validity, or real-world performance.
- Business break-even analysis varies challenge success, review recovery and cost, false-decline attrition, chargeback fee, legitimate-payment margin, and daily review capacity.
- The simulator has one account per customer and no device, IP, login, or recovery-event network.
- Group diagnostics are descriptive, not fairness certification.
- Monitoring is a prototype; no real-time model service or payment control is deployed.

For a full interpretation of results and assumptions, start with the [portfolio case study](docs/portfolio_case_study.md). For a short presentation, use the [three-minute walkthrough](docs/demo_talk_track.md).
