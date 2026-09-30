# Quest of Trust — 3-minute portfolio walkthrough

## 0:00–0:30 — The business problem

“Quest of Trust is a synthetic payments-risk case study. I wanted to compare fraud strategies by their business consequences, not just by a model metric. Each payment event can be approved, challenged, sent to review, or declined. Every action trades off fraud loss, customer friction, margin, and limited investigator capacity.”

## 0:30–1:00 — The data and safeguards

“I generated a fictional 60-day payments world and planted four documented attack patterns. The answer key stays separate from event features. Behavioral history is computed in timestamp order before the current event is added, and the latest dates are held out to mimic future evaluation.”

## 1:00–1:45 — The comparison

“I compared transparent rules with a logistic baseline, then mapped their scores into four actions under a daily review cap. In the 6,923-event holdout, 35 events are planted fraud. Under the simulator’s base assumptions, logistic captures an estimated 81.62% of fraud value versus 78.52% for rules. It also produces 247 fewer legitimate challenges, with the same three false declines.”

## 1:45–2:20 — The business interpretation

“The logistic strategy has the lowest modeled net cost in this run: −$5,847.42. That is a conditional simulation output, not observed savings. It depends on fictional challenge stop rates, review recovery, customer value, and cost assumptions. The point is the decision framework: model ranking, customer friction, operations, and economics need to be considered together.”

## 2:20–2:45 — Show the interactive artifact

Open the live dashboard. Change daily review capacity and economic assumptions. Explain that these controls reveal precomputed holdout outcomes under different scenarios; they do not retrain the model or make live payment decisions.

## 2:45–3:00 — Close with limits and next step

“This is a reproducible portfolio prototype, not a production fraud control. The next validation step would be to correct a PR-AUC reporting defect, test across multiple temporal windows and simulation seeds, and only then assess representative governed data. I’ve documented the assumptions and kept the full code and data artifacts inspectable.”

## Likely reviewer questions

**Why use a time-based holdout?** Fraud patterns and operations change over time. Training on earlier events and evaluating on later events better represents the forward-looking use case than a random event split.

**Why include a rules baseline?** It is auditable and makes an interpretable comparison point before adding model complexity.

**Why is the modeled cost negative?** Approved legitimate payment margin is represented as a negative cost. The total is an assumption-driven net-cost calculation, not realized profit.

**What is the biggest limitation?** The data, fraud scenarios, intervention probabilities, and unit economics are synthetic; the holdout also contains only 35 planted fraud events.

**Why is SQLite used?** It keeps the local analytical project self-contained. The current workload does not justify operating a database server.

