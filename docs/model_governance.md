# Model governance and evaluation guardrails

- Keep `fraud_ground_truth.csv` out of public investigation inputs, feature creation, and live monitoring.
- Do not use fraud labels, event IDs, typologies, post-event outcomes, or KYC risk as baseline model features.
- Build rolling features in timestamp order and calculate prior counts before adding the current event.
- Hold out the latest 30% of dates; do not use random row splits for this changing behavior simulation.
- Repeat the primary rules-versus-logistic comparison across 30 deterministic seeds; publish paired cost and capture ranges, and label them as simulator variation rather than real-world confidence intervals. Keep the smaller campaign-identity check labeled as a single-seed diagnostic.
- Compare transparent rules with a simple logistic model and hybrid score. Accuracy is not a success criterion on a rare-event dataset.
- Report PR-AUC, fraud value captured, false declines, good-customer friction, review overflow, and economic cost.
- Keep the threshold candidate set and unit economics visible. Changing assumptions should cause the run to be repeated and recorded.
- Daily monitoring summaries use observable transaction volume, amount, auth soft-decline rate, and score rates without hidden labels.
- Three-sigma alerts compare each day with the previous 14 days (minimum seven prior days); they are screening signals and can be unstable with small or seasonal samples.
- Segment, KYC-band, and home-region impact tables are descriptive synthetic diagnostics, not proof of fairness or unfairness.
- Scaling the simulation to 350 simulated fraud events per later-date test period does not make its population representative evidence about any real customers, protected groups, company, or fraud strategy.

Before any real deployment, use approved data, assess fairness and customer impact, validate calibration and temporal stability, establish human oversight and appeals, document controls, and obtain accountable business and compliance review. This repository is a portfolio simulation, not a production decision service.
