# Quest of Trust — 3-minute project walkthrough

## 0:00–0:30 — The business problem

“Quest of Trust is a synthetic payments-risk case study. I wanted to compare fraud strategies by their business consequences, not just by a model metric. Each payment event can be approved, challenged, sent to review, or declined. Every action trades off fraud loss, customer friction, margin, and limited investigator capacity.”

## 0:30–1:00 — The data and safeguards

“I generated a fictional 60-day payments world with 2,000 customers and planted four documented attack patterns. Each seed has 350 planted fraud events in its later-date holdout. The answer key stays separate from event features. Behavioral history is computed in timestamp order before the current event is added.”

## 1:00–1:45 — The comparison

“I compared transparent rules with a logistic baseline, then mapped their scores into approve, challenge, review, or decline actions under a daily review cap. Across 10 synthetic seeds, logistic captured 90.43% of fraud value on average versus 73.15% for rules. It had lower modeled net cost in all 10 runs.”

## 1:45–2:20 — The business interpretation

“The median paired cost difference was −$22,635 per holdout, with a range from −$25,345 to −$19,903. Logistic challenged a median 3,462 fewer legitimate payments, while sending 214 more legitimate payments to investigator review. Those are synthetic scenario outputs, not observed savings. The result depends on fictional challenge stop rates, recovery, customer value, and unit costs.”

## 2:20–2:45 — Show the interactive artifact

Open the live dashboard. Change daily review capacity and economic assumptions. Explain that these controls reveal precomputed holdout outcomes under different scenarios; they do not retrain the model or make live payment decisions.

## 2:45–3:00 — Close with limits and next step

“This is a reproducible project prototype, not a production fraud control. Ten seeds show how this simulator behaves under repeated random draws; they do not prove a real-world ranking or quantify statistical uncertainty for real customers. The next step would be validating the assumptions and thresholds against representative governed payment data.”

## Likely reviewer questions

**Why use a time-based holdout?** Fraud patterns and operations change over time. Training on earlier events and evaluating on later events better represents the forward-looking use case than a random event split.

**Why include a rules baseline?** It is auditable and makes an interpretable comparison point before adding model complexity.

**Why is the modeled cost negative?** Approved legitimate payment margin is represented as a negative cost. The total is an assumption-driven net-cost calculation, not realized profit.

**What is the biggest limitation?** The data, fraud scenarios, intervention probabilities, and unit economics are synthetic. More planted events and repeated seeds reduce simulation noise, but they do not make the scenarios representative of actual fraud.

**Why is SQLite used?** It keeps the local analytical project self-contained. The current workload does not justify operating a database server.
