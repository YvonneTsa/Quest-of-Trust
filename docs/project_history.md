# TrustHold project history and build record

## Project identity

The current flagship is **TrustHold — The Cost of Fraud**. It evolved from the earlier FraudWatch / “Cost of Trust” concept. Its central question is how a digital-payments business should balance fraud loss, customer friction, review capacity, revenue, and trust across APPROVE, CHALLENGE, REVIEW, and DECLINE decisions.

The intended portfolio narrative connects actuarial science, analytics, audit/risk, fraud, and decision intelligence. The project is designed to show investigation, quantitative reasoning, control thinking, operational judgment, explainability, and communication—not only model selection.

## Recovered local state

The earlier project folder contained the expected directory layout and an untracked `src/simulation/generate_customers.py`. That saved script used seed `20260915`, 20 customers, segment sampling, and log-normal typical spend. It did not yet include a transaction-rate profile, region, KYC risk band, or a reusable function. The roadmap document described an earlier 10-customer version with seed `20240614`; this build preserves the actual saved script's 20-customer setting and records the discrepancy.

The prior local folder had empty `README.md`, `requirements.txt`, `.gitignore`, and project subfolders. It had no Git metadata. The matching GitHub repository, `YvonneTsa/The-Cost-of-Trust`, was also empty when inspected for this build.

## Decisions retained

- Build a synthetic environment with known, separately held fraud ground truth rather than relying only on a downloaded dataset.
- Keep fraud truth out of model inputs and keep all features point-in-time.
- Compare decisions on economic and operational outcomes, not accuracy alone.
- Treat all simulator settings as assumptions until supported or stress-tested.
- Build in small, inspectable steps while retaining the advanced end-to-end capstone structure.
- Distinguish simulated hypotheses and future targets from measured results.

## Current build

The local prototype now runs from customer profiles through entities, transactions, four fraud injections, point-in-time features, rules, a temporal logistic baseline, thresholded actions, finite review capacity, economics, sensitivity scenarios, customer-group diagnostics, SQL investigation, monitoring, and an interactive HTML dashboard. Generated case-study metrics are labeled as synthetic. A Power BI file and real production validation are not part of this build.
